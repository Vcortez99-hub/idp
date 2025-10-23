# -*- coding: utf-8 -*-
import sys
import io as io_module

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io_module.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io_module.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import base64
import zipfile
import io
from openai import OpenAI
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime
import PyPDF2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import re
import json
from learning_system import IntelligentLearningSystem

app = Flask(__name__)
CORS(app)

# Configuração de upload
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Inicializa o sistema de aprendizado inteligente
learning_system = IntelligentLearningSystem()

# Configuração de pastas para produção
if os.environ.get('RENDER'):
    # Ambiente de produção no Render
    UPLOAD_FOLDER = '/tmp/uploads'
    PROCESSED_FOLDER = '/tmp/processed'
else:
    # Desenvolvimento local
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DOCUMENT_TYPES = {
    'holerite': 'Holerites',
    'certidao_nascimento': 'Certidões de Nascimento',
    'comprovante_residencia': 'Comprovantes de Residência',
    'rg': 'Identidade',
    'cpf': 'CPF',
    'cnh': 'CNH',
    'ctps': 'CTPS',
    'contrato': 'Contratos',
    'procuracao': 'Procurações',
    'peticao': 'Petições',
    'sentenca': 'Sentenças',
    # Documentos específicos para migração francesa
    'titre_sejour': 'Título de Permanência',
    'visa_frances': 'Visto Francês',
    'carte_resident': 'Cartão de Residente',
    'attestation_hebergement': 'Atestado de Hospedagem',
    'justificatif_domicile': 'Comprovante de Domicílio',
    'bulletin_salaire': 'Holerite Francês',
    'contrat_travail': 'Contrato de Trabalho',
    'attestation_employeur': 'Atestado do Empregador',
    'avis_imposition': 'Aviso de Impostos',
    'certificat_scolarite': 'Certificado Escolar',
    'diplome_francais': 'Diploma Francês',
    'acte_naissance_traduit': 'Certidão de Nascimento Traduzida',
    'casier_judiciaire': 'Antecedentes Criminais',
    'certificat_medical': 'Certificado Médico',
    'assurance_maladie': 'Seguro Saúde',
    'liste_documents': 'Lista de Documentos',
    # Documentos jurídicos franceses específicos
    'tableau_vie_commune': 'Quadro de Vida em Comum',
    'refere_suspension': 'Referência de Suspensão',
    'accuse_depot': 'Comprovante de Depósito',
    'accuse_reception': 'Comprovante de Recebimento',
    'requete_tribunal': 'Petição ao Tribunal',
    'lettre_recommandee': 'Carta Registrada',
    'document_tribunal': 'Documento do Tribunal',
    'procedure_administrative': 'Procedimento Administrativo',
    'recours_administratif': 'Recurso Administrativo',
    # Documentos específicos adicionais
    'attestation_honneur': 'Declaração de Honra',
    'attestation_depot': 'Atestado de Depósito',
    'passeport': 'Passaporte',
    'conta_telefone': 'Conta de Telefone',
    'outros': 'Outros Documentos'
}

def load_categories():
    """Carrega categorias do arquivo JSON ou retorna as padrões"""
    try:
        with open('categories.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return DOCUMENT_TYPES.copy()
    except json.JSONDecodeError:
        return DOCUMENT_TYPES.copy()

def save_categories(categories):
    """Salva categorias no arquivo JSON"""
    try:
        print(f"Tentando salvar categorias: {categories}")
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        print("Categorias salvas com sucesso no arquivo categories.json")
        return True
    except Exception as e:
        print(f"Erro ao salvar categorias: {e}")
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def preprocess_image_for_ocr(image):
    """Pré-processa imagem para melhorar precisão do OCR"""
    try:
        # Converte PIL Image para numpy array (OpenCV)
        img_array = np.array(image)

        # Converte para escala de cinza se necessário
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # 1. Redimensiona se a imagem for muito pequena (melhora OCR)
        height, width = gray.shape
        if height < 1000 or width < 1000:
            scale_factor = 2.0
            gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            print(f"  Imagem redimensionada: {width}x{height} → {gray.shape[1]}x{gray.shape[0]}")

        # 2. Remoção de ruído com filtro bilateral (preserva bordas)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 3. Correção de inclinação (deskew)
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 0.5:  # Só corrige se inclinação for significativa
                (h, w) = denoised.shape
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h),
                                         flags=cv2.INTER_CUBIC,
                                         borderMode=cv2.BORDER_REPLICATE)
                print(f"  Correção de inclinação aplicada: {angle:.2f}°")

        # 4. Binarização adaptativa (Otsu's method + adaptativa)
        # Primeiro tenta Otsu
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Se Otsu não funcionar bem, usa binarização adaptativa
        adaptive = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 11, 2)

        # Usa a que tiver mais pixels brancos (geralmente melhor para documentos)
        if np.sum(binary == 255) < np.sum(adaptive == 255):
            binary = adaptive
            print("  Binarização adaptativa aplicada")
        else:
            print("  Binarização Otsu aplicada")

        # 5. Morfologia para limpar ruídos pequenos
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

        # 6. Aumenta contraste final
        processed = cv2.convertScaleAbs(processed, alpha=1.2, beta=10)

        # Converte de volta para PIL Image
        return Image.fromarray(processed)

    except Exception as e:
        print(f"  Erro no pré-processamento, usando imagem original: {e}")
        return image

def extract_month_year_from_bulletin(text):
    """Extrai mês e ano de um bulletin de salaire francês"""
    if not text:
        return None, None

    text_lower = text.lower()

    # Mapeamento de meses em francês
    meses_fr = {
        'janvier': '01', 'jan': '01',
        'février': '02', 'fevrier': '02', 'fev': '02', 'fév': '02',
        'mars': '03', 'mar': '03',
        'avril': '04', 'avr': '04',
        'mai': '05',
        'juin': '06',
        'juillet': '07', 'juil': '07',
        'août': '08', 'aout': '08',
        'septembre': '09', 'sept': '09', 'sep': '09',
        'octobre': '10', 'oct': '10',
        'novembre': '11', 'nov': '11',
        'décembre': '12', 'decembre': '12', 'dec': '12', 'déc': '12'
    }

    # Procura por padrão "Période : Mês Ano" ou "Période: Mês Ano"
    import re

    # Padrão 1: "Période : Juillet 2025" ou "période: juillet 2025"
    match = re.search(r'période\s*[:：]\s*([a-zéèêâû]+)\s+(\d{4})', text_lower)
    if match:
        mes_texto = match.group(1).strip()
        ano = match.group(2)
        mes_num = meses_fr.get(mes_texto)
        if mes_num:
            return mes_num, ano

    # Padrão 2: "07/2025" ou "07 2025"
    match = re.search(r'(\d{2})[/\s-](\d{4})', text)
    if match:
        return match.group(1), match.group(2)

    # Padrão 3: Mês por extenso seguido de ano
    for mes_nome, mes_num in meses_fr.items():
        pattern = rf'{mes_nome}\s+(\d{{4}})'
        match = re.search(pattern, text_lower)
        if match:
            return mes_num, match.group(1)

    return None, None

def extract_text_from_file(file_path):
    """Extrai texto de arquivos PDF ou imagens usando OCR com melhor logging"""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        
        if file_extension == '.pdf':
            # Extração otimizada de texto de PDF com suporte a OCR para PDFs com imagens
            print(f"Extraindo texto de PDF: {filename}")
            text = ""
            has_images = False
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"  PDF com {total_pages} páginas")
                
                # Limita a extração para PDFs muito grandes (mais de 10 páginas)
                max_pages = min(10, total_pages) if total_pages > 10 else total_pages
                if max_pages < total_pages:
                    print(f"  Limitando extração às primeiras {max_pages} páginas para otimização")
                
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"

                    # Verifica se a página tem imagens (indicativo de PDF escaneado)
                    if '/XObject' in page.get('/Resources', {}):
                        xobjects = page['/Resources']['/XObject'].get_object()
                        for obj in xobjects:
                            if xobjects[obj]['/Subtype'] == '/Image':
                                has_images = True
                                break

                    if page_num < 3:  # Log detalhado apenas para as primeiras páginas
                        print(f"  Página {page_num + 1}: {len(page_text)} caracteres extraídos")
            
            extracted_text = text.strip()
            
            # Se o PDF tem pouco texto mas tem imagens, aplica OCR em TODAS as páginas
            if (len(extracted_text) < 100 and has_images) or (has_images and len(extracted_text.split()) < 20):
                print(f"  PDF parece ser escaneado (pouco texto: {len(extracted_text)} chars), aplicando OCR em todas as páginas...")
                try:
                    import fitz  # PyMuPDF para converter PDF em imagem

                    # Processa TODAS as páginas do PDF com OCR
                    pdf_document = fitz.open(file_path)
                    total_ocr_text = ""
                    pages_to_process = min(len(pdf_document), max_pages)  # Respeita max_pages

                    for page_num in range(pages_to_process):
                        page = pdf_document[page_num]
                        # Aumenta resolução para melhor OCR (matriz 2x2)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_data = pix.tobytes("png")

                        # Converte bytes em imagem PIL
                        from io import BytesIO
                        image = Image.open(BytesIO(img_data))

                        # Pré-processa a imagem
                        print(f"  Pré-processando página {page_num + 1}...")
                        processed_image = preprocess_image_for_ocr(image)

                        # Aplica OCR com configuração otimizada
                        try:
                            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
                            page_ocr_text = pytesseract.image_to_string(processed_image, lang='por+fra+eng', config=custom_config)
                            total_ocr_text += page_ocr_text + "\n"
                            print(f"  Página {page_num + 1}: {len(page_ocr_text)} caracteres extraídos via OCR")
                        except Exception as ocr_error:
                            print(f"  Erro no OCR da página {page_num + 1}: {ocr_error}")

                    pdf_document.close()

                    if len(total_ocr_text.strip()) > len(extracted_text):
                        extracted_text = total_ocr_text.strip()
                        print(f"  Usando texto do OCR completo: {len(extracted_text)} caracteres")

                except ImportError:
                    print(f"  PyMuPDF não disponível, tentando com pdf2image...")
                    try:
                        from pdf2image import convert_from_path

                        # Converte todas as páginas em imagens
                        images = convert_from_path(file_path, dpi=300)
                        total_ocr_text = ""

                        for idx, image in enumerate(images):
                            if idx >= max_pages:
                                break
                            # Pré-processa
                            processed_image = preprocess_image_for_ocr(image)
                            # Aplica OCR
                            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
                            page_ocr_text = pytesseract.image_to_string(processed_image, lang='por+fra+eng', config=custom_config)
                            total_ocr_text += page_ocr_text + "\n"
                            print(f"  Página {idx + 1}: {len(page_ocr_text)} caracteres via OCR")

                        if len(total_ocr_text.strip()) > len(extracted_text):
                            extracted_text = total_ocr_text.strip()
                            print(f"  Usando texto do OCR completo: {len(extracted_text)} caracteres")
                    except Exception as pdf2img_error:
                        print(f"  Erro com pdf2image: {pdf2img_error}")
                        print(f"  Usando texto extraído diretamente: {len(extracted_text)} caracteres")
                except Exception as e:
                    print(f"  Erro ao aplicar OCR no PDF: {e}")
            
            print(f"Total extraído do PDF: {len(extracted_text)} caracteres")
            return extracted_text
            
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            # OCR para imagens com pré-processamento
            print(f"Aplicando OCR em imagem: {filename}")
            try:
                image = Image.open(file_path)
                print(f"  Dimensões da imagem original: {image.size}")

                # Pré-processa a imagem para melhorar OCR
                print("  Iniciando pré-processamento da imagem...")
                processed_image = preprocess_image_for_ocr(image)

                # Configuração otimizada do Tesseract
                # --oem 3: usa LSTM OCR Engine (mais preciso)
                # --psm 6: assume um bloco uniforme de texto
                # preserve_interword_spaces: mantém espaços entre palavras
                custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

                # Tenta com múltiplos idiomas simultaneamente
                try:
                    text = pytesseract.image_to_string(processed_image, lang='por+fra+eng', config=custom_config)
                    print(f"  OCR multi-idioma: {len(text)} caracteres extraídos")
                except Exception as e:
                    print(f"  Erro com multi-idioma: {e}, tentando apenas português...")
                    try:
                        text = pytesseract.image_to_string(processed_image, lang='por', config=custom_config)
                        print(f"  OCR português: {len(text)} caracteres extraídos")
                    except:
                        print("  Português não disponível, usando inglês para OCR")
                        text = pytesseract.image_to_string(processed_image, lang='eng', config=custom_config)
                        print(f"  OCR inglês: {len(text)} caracteres extraídos")

                extracted_text = text.strip()
                if extracted_text:
                    print(f"  Texto extraído com sucesso: {len(extracted_text)} caracteres")
                    # Mostra uma amostra do texto extraído para debug
                    sample = extracted_text[:100].replace('\n', ' ')
                    print(f"  Amostra: {sample}...")
                else:
                    print("  Nenhum texto foi extraído da imagem")

                return extracted_text

            except Exception as ocr_error:
                print(f"Erro no OCR para {filename}: {ocr_error}")
                return ""
        
        print(f"Formato não suportado para extração: {file_extension}")
        return ""
        
    except Exception as e:
        print(f"Erro ao extrair texto de {file_path}: {e}")
        return ""

def separate_documents_from_pdf(file_path):
    """Separa um PDF em documentos individuais por página"""
    try:
        documents = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                # Extrai texto da página
                page_text = page.extract_text().strip()
                
                if page_text:  # Só inclui páginas com texto
                    documents.append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'filename': f"{os.path.splitext(os.path.basename(file_path))[0]}_pagina_{page_num + 1}.pdf"
                    })
        
        return documents
    except Exception as e:
        print(f"Erro ao separar PDF {file_path}: {e}")
        return []

def detect_document_boundaries(text):
    """Detecta possíveis limites entre documentos em um texto"""
    # Padrões que indicam início de novo documento
    document_markers = [
        r'REPÚBLICA FEDERATIVA DO BRASIL',
        r'CERTIDÃO DE NASCIMENTO',
        r'CARTEIRA DE TRABALHO',
        r'CARTEIRA NACIONAL DE HABILITAÇÃO',
        r'REGISTRO GERAL',
        r'CADASTRO DE PESSOA FÍSICA',
        r'COMPROVANTE DE RESIDÊNCIA',
        r'HOLERITE',
        r'FOLHA DE PAGAMENTO',
        r'CONTRATO',
        r'PROCURAÇÃO',
        r'PETIÇÃO INICIAL',
        r'SENTENÇA',
        r'NOTA FISCAL'
    ]
    
    import re
    boundaries = [0]  # Sempre começa no início
    
    for marker in document_markers:
        matches = re.finditer(marker, text, re.IGNORECASE)
        for match in matches:
            pos = match.start()
            if pos > 100:  # Evita detectar o mesmo documento
                boundaries.append(pos)
    
    boundaries = sorted(list(set(boundaries)))  # Remove duplicatas e ordena
    return boundaries


def classify_offline_fallback(file_path, categories=None, text=None):
    """Classificação offline usando padrões de nome de arquivo e conteúdo OCR"""
    if categories is None:
        categories = DOCUMENT_TYPES

    # Extrai texto se não foi fornecido
    if text is None:
        text = extract_text_from_file(file_path)

    filename = os.path.basename(file_path) if os.path.isfile(file_path) else file_path
    filename_lower = filename.lower()
    text_lower = text.lower() if text else ""

    print(f"  [Offline] Analisando: {filename}")
    print(f"  [Offline] Texto disponível: {len(text)} caracteres")
    
    # Padrões expandidos e unificados para classificação
    filename_patterns = {
        # Documentos de Identidade
        'rg': ['rg', 'identidade', 'carteira_identidade', 'cedula'],
        'cpf': ['cpf', 'cadastro_pessoa_fisica'],
        'cnh': ['cnh', 'carteira_habilitacao', 'habilitacao'],
        'passaporte': ['passaporte', 'passport'],
        
        # Certidões
        'certidao_nascimento': ['certidao', 'nascimento', 'birth'],
        'certidao_casamento': ['certidao', 'casamento', 'marriage'],
        'certidao_obito': ['certidao', 'obito', 'death'],
        'certidao_antecedentes': ['certidao', 'antecedentes', 'criminal'],
        
        # Documentos de Trabalho
        'holerite': ['holerite', 'folha', 'pagamento', 'salario'],
        'certificado_trabalho': ['certificado', 'trabalho', 'emprego'],
        'comprovante_renda': ['comprovante', 'renda', 'rendimento'],
        'declaracao_imposto': ['declaracao', 'imposto', 'renda', 'receita'],
        
        # Documentos Escolares
        'diploma': ['diploma', 'graduacao', 'formatura'],
        'certificado_escolar': ['certificado', 'escolar', 'curso'],
        'historico_escolar': ['historico', 'escolar', 'notas'],
        'comprovante_matricula': ['comprovante', 'matricula', 'escola'],
        
        # Documentos Médicos
        'atestado_medico': ['atestado', 'medico', 'saude'],
        'laudo_medico': ['laudo', 'medico', 'exame'],
        'comprovante_vacinacao': ['comprovante', 'vacinacao', 'vacina'],
        'cartao_vacinacao': ['cartao', 'vacinacao', 'vacina'],
        
        # Documentos Bancários
        'comprovante_bancario': ['comprovante', 'bancario', 'banco'],
        'extrato_bancario': ['extrato', 'bancario', 'conta'],
        'comprovante_transferencia': ['comprovante', 'transferencia', 'ted', 'doc'],
        'comprovante_deposito': ['comprovante', 'deposito'],
        
        # Comprovantes de Residência e Contas
        'comprovante_residencia': ['comprovante', 'residencia', 'endereco'],
        'conta_luz': ['conta', 'luz', 'energia', 'eletrica', 'cemig', 'copel', 'celpe'],
        'conta_agua': ['conta', 'agua', 'saneamento', 'sabesp', 'cedae'],
        'conta_gas': ['conta', 'gas', 'comgas', 'naturgy'],
        'conta_telefone': ['conta', 'telefone', 'celular', 'tim', 'vivo', 'claro', 'oi', 'nextel', 'algar', 'telefonica', 'fatura', 'mobile', 'fixo', 'linha'],
        
        # Comprovantes de Pagamento
        'comprovante_pagamento': ['comprovante', 'pagamento'],
        'recibo': ['recibo', 'pagamento'],
        'nota_fiscal': ['nota', 'fiscal', 'nf', 'nfe'],
        'boleto': ['boleto', 'cobranca'],
        'comprovante_quitacao': ['comprovante', 'quitacao'],
        
        # Documentos Legais
        'autorizacao': ['autorizacao', 'permissao'],
        'procuracao': ['procuracao', 'mandato', 'representacao'],
        'declaracao': ['declaracao'],
        'licenca': ['licenca', 'alvara'],
        'alvara': ['alvara', 'funcionamento'],
        'permissao': ['permissao'],
        
        # Documentos Jurídicos
        'contrato': ['contrato', 'acordo', 'contract', 'termo'],
        'peticao': ['peticao', 'inicial', 'recurso', 'defesa'],
        'sentenca': ['sentenca', 'decisao', 'julgamento', 'acordao'],
        
        # Outros
        'atestado': ['atestado'],
        'certificado': ['certificado'],
        'credencial': ['credencial'],
        'carteirinha': ['carteirinha'],
        'cartao': ['cartao'],
        'comprovante_isencao': ['comprovante', 'isencao'],
        
        # Documentos específicos para migração francesa
        'titre_sejour': ['titre', 'sejour', 'residence'],
        'visa_frances': ['visa', 'visto', 'schengen'],
        'carte_resident': ['carte', 'resident', 'permanente'],
        'attestation_hebergement': ['attestation', 'hebergement', 'logement'],
        'justificatif_domicile': ['justificatif', 'domicile', 'residence'],
        'bulletin_salaire': ['bulletin-de-salaire', 'bulletin_salaire', 'bulletin', 'salaire', 'paie', 'fiche-de-paie'],
        'contrat_travail': ['contrat', 'travail', 'emploi'],
        'attestation_employeur': ['attestation', 'employeur', 'travail'],
        'avis_imposition': ['avis', 'imposition', 'impot'],
        'certificat_scolarite': ['certificat', 'scolarite', 'etudiant'],
        'diplome_francais': ['diplome', 'universite', 'formation'],
        'acte_naissance_traduit': ['acte', 'naissance', 'traduit'],
        'casier_judiciaire': ['casier', 'judiciaire', 'penal'],
        'certificat_medical': ['certificat', 'medical', 'sante'],
        'assurance_maladie': ['assurance', 'maladie', 'securite', 'sociale'],
        'liste_documents': ['lista', 'documentos', 'regularizacao', 'regularisation'],
        
        # Documentos jurídicos franceses específicos
        'tableau_vie_commune': ['tableau', 'vie', 'commune', 'justificatifs', 'conjoint'],
        'refere_suspension': ['refere', 'suspension', 'tribunal', 'administratif'],
        'accuse_depot': ['accuse', 'depot', 'recommande', 'envoi'],
        'accuse_reception': ['accuse', 'reception', 'requete', 'depot'],
        'requete_tribunal': ['requete', 'tribunal', 'administratif', 'petition'],
        'lettre_recommandee': ['lettre', 'recommandee', 'poste', 'envoi'],
        'document_tribunal': ['tribunal', 'administratif', 'juridique', 'judiciaire'],
        'procedure_administrative': ['procedure', 'administrative', 'demarche'],
        'recours_administratif': ['recours', 'administratif', 'contestation'],
        
        # Documentos específicos adicionais
        'attestation_honneur': ['attestation', 'honneur', 'lhonneur', 'sur_lhonneur', 'epoux', 'requerante'],
        'attestation_depot': ['attestation', 'depot', 'de_depot'],
        'passeport': ['passeport', 'passport'],

        'outros': []  # Removido padrões genéricos para evitar false positives
    }
    
    # Classificação baseada no nome do arquivo com confiança alta
    for category, keywords in filename_patterns.items():
        if any(keyword in filename_lower for keyword in keywords):
            # Tratamento especial para notas fiscais
            if category == 'outros' and any(word in filename_lower for word in ['nota', 'fiscal', 'nf', 'nfe']):
                return {
                    'category': 'nota_fiscal',
                    'category_name': 'Notas Fiscais e Documentos Comerciais',
                    'method': 'offline_filename',
                    'confidence': 0.8
                }
            return {
                'category': category,
                'category_name': categories.get(category, category.title()),
                'method': 'offline_filename',
                'confidence': 0.8
            }
    
    # Classificação baseada no conteúdo OCR com padrões mais específicos
    if text_lower:
        content_patterns = {
            'rg': [
                'registro geral', 
                'carteira de identidade', 
                'secretaria de segurança pública',
                'instituto de identificação',
                'rg nº',
                'carteira identidade',
                'documento de identidade'
            ],
            'cpf': ['cadastro de pessoa física', 'receita federal do brasil', 'cpf nº', 'situação cadastral'],
            'cnh': ['carteira nacional de habilitação', 'detran', 'categoria a', 'categoria b', 'categoria c', 'categoria d', 'categoria e'],
            'passaporte': ['passaporte brasileiro', 'passport', 'ministério das relações exteriores', 'polícia federal'],
            'certidao_nascimento': ['certidão de nascimento', 'registro civil das pessoas naturais', 'nasceu no dia', 'filho de'],
            'certidao_casamento': ['certidão de casamento', 'registro civil das pessoas naturais', 'casaram-se', 'contraíram matrimônio'],
            'certidao_obito': ['certidão de óbito', 'registro civil das pessoas naturais', 'faleceu', 'causa da morte'],
            'holerite': ['demonstrativo de pagamento', 'folha de pagamento', 'salário base', 'desconto inss', 'salário líquido'],
            'comprovante_bancario': ['comprovante de operação bancária', 'agência', 'conta corrente', 'saldo disponível'],
            'extrato_bancario': ['extrato de conta corrente', 'movimentação bancária', 'saldo anterior', 'saldo atual'],
            'conta_telefone': [
                'fatura de telefone', 'conta de telefone', 'fatura celular', 'conta celular',
                'tim', 'vivo', 'claro', 'oi', 'nextel', 'algar', 'telefônica',
                'linha telefônica', 'plano pós-pago', 'plano pré-pago', 'serviços de telecomunicações',
                'valor da fatura', 'vencimento da fatura', 'número da linha', 'consumo de dados',
                'chamadas realizadas', 'sms enviados', 'internet móvel', 'roaming',
                'anatel', 'agência nacional de telecomunicações', 'código de área',
                'fatura detalhada', 'resumo da conta', 'débito automático'
            ],
            'nota_fiscal': ['nota fiscal eletrônica', 'cnpj', 'valor total da nota', 'icms', 'danfe'],
            'atestado': ['atestado médico', 'cid-10', 'afastamento por', 'dias de repouso'],
            'certificado': ['certificado de conclusão', 'carga horária', 'aprovado com', 'instituição de ensino'],
            'diploma': ['diploma de graduação', 'universidade', 'bacharel em', 'licenciado em', 'tecnólogo em'],
            'carta': ['prezado senhor', 'prezada senhora', 'atenciosamente', 'cordialmente', 'respeitosamente'],
            
            # Padrões para documentos de migração francesa
            'titre_sejour': [
                'titre de séjour', 'carte de séjour', 'préfecture', 'ofii', 
                'autorisation de séjour', 'récépissé de demande', 'renouvellement'
            ],
            'visa_frances': [
                'visa', 'consulat de france', 'schengen', 'entrée en france',
                'ambassade de france', 'visa de long séjour', 'vls-ts'
            ],
            'carte_resident': [
                'carte de résident', 'résident permanent', 'carte de résident permanent',
                'titre de séjour de 10 ans', 'résident de longue durée'
            ],
            'attestation_hebergement': [
                'attestation d\'hébergement', 'héberge', 'domicile chez',
                'certifie héberger', 'logement gratuit', 'hébergement à titre gratuit'
            ],
            'justificatif_domicile': [
                'justificatif de domicile', 'facture edf', 'facture gdf', 'facture eau',
                'quittance de loyer', 'taxe d\'habitation', 'facture téléphone'
            ],
            'bulletin_salaire': [
                'bulletin de salaire', 'bulletin de paie', 'fiche de paie',
                'salaire brut', 'salaire net', 'cotisations sociales', 'urssaf',
                'période :', 'période:', 'employeur', 'salarié', 'net à payer'
            ],
            'contrat_travail': [
                'contrat de travail', 'cdi', 'cdd', 'contrat à durée indéterminée',
                'contrat à durée déterminée', 'employeur', 'salarié'
            ],
            'attestation_employeur': [
                'attestation employeur', 'certificat de travail', 'attestation de salaire',
                'emploi depuis', 'fonction occupée', 'rémunération mensuelle'
            ],
            'avis_imposition': [
                'avis d\'imposition', 'impôt sur le revenu', 'revenu fiscal de référence',
                'direction générale des finances publiques', 'dgfip', 'revenus déclarés'
            ],
            'certificat_scolarite': [
                'certificat de scolarité', 'attestation de scolarité', 'étudiant inscrit',
                'année scolaire', 'établissement scolaire', 'université'
            ],
            'diplome_francais': [
                'diplôme', 'université', 'licence', 'master', 'doctorat',
                'baccalauréat', 'bts', 'dut', 'académie', 'ministère de l\'éducation'
            ],
            'acte_naissance_traduit': [
                'acte de naissance', 'traduction certifiée', 'traducteur assermenté',
                'né le', 'lieu de naissance', 'état civil', 'extrait de naissance'
            ],
            'casier_judiciaire': [
                'casier judiciaire', 'bulletin n°3', 'extrait de casier judiciaire',
                'ministère de la justice', 'condamnations', 'vierge'
            ],
            'certificat_medical': [
                'certificat médical', 'médecin', 'examen médical', 'aptitude physique',
                'visite médicale', 'ofii médical', 'tuberculose'
            ],
            'assurance_maladie': [
                'assurance maladie', 'sécurité sociale', 'carte vitale', 'cpam',
                'attestation de droits', 'numéro de sécurité sociale', 'mutuelle'
            ],
            'liste_documents': [
                'lista de documentos', 'liste des documents', 'regularização', 'regularisation',
                'dossier de demande', 'pièces à fournir', 'documents requis', 'checklist'
            ],
            
            # Padrões para documentos jurídicos franceses específicos
            'tableau_vie_commune': [
                'tableau détaillé des justificatifs', 'justificatifs de vie commune',
                'vie commune', 'conjoint', 'concubinage', 'pacs', 'mariage',
                'madame', 'monsieur', 'et son conjoint', 'et sa conjointe'
            ],
            'refere_suspension': [
                'référé suspension', 'tribunal administratif', 'requête en référé',
                'suspension de l\'exécution', 'mesures d\'urgence', 'référé-suspension',
                'tribunal administratif de', 'demande de suspension'
            ],
            'accuse_depot': [
                'accusé de dépôt', 'envoi recommandé', 'lettre recommandée',
                'la poste', 'dépôt d\'un envoi', 'recommandé avec accusé',
                'numéro de suivi', 'preuve de dépôt'
            ],
            'accuse_reception': [
                'accusé de réception', 'réception d\'un dépôt', 'dépôt de requête',
                'comprovante de recebimento', 'requerimento apresentado',
                'réception de la demande', 'enregistrement de la requête'
            ],
            'requete_tribunal': [
                'requête', 'tribunal administratif', 'demande au tribunal',
                'pétition', 'recours contentieux', 'contentieux administratif',
                'juridiction administrative', 'instance administrative'
            ],
            'lettre_recommandee': [
                'lettre recommandée', 'envoi recommandé', 'courrier recommandé',
                'accusé de réception postal', 'la poste française',
                'service postal', 'recommandé ar'
            ],
            'document_tribunal': [
                'tribunal', 'juridiction', 'cour administrative', 'instance judiciaire',
                'procédure judiciaire', 'acte judiciaire', 'décision de justice'
            ],
            'procedure_administrative': [
                'procédure administrative', 'démarche administrative', 'formalité administrative',
                'administration française', 'service public', 'démarche officielle'
            ],
            'recours_administratif': [
                'recours administratif', 'contestation administrative', 'recours gracieux',
                'recours hiérarchique', 'opposition administrative', 'révision administrative'
            ],
            
            # Documentos específicos adicionais
            'attestation_honneur': [
                'attestation sur l\'honneur', 'attestation d\'honneur', 'sur l\'honneur',
                'je soussigné', 'atteste sur l\'honneur', 'certifie sur l\'honneur',
                'déclare sur l\'honneur', 'époux', 'épouse', 'requérante'
            ],
            'attestation_depot': [
                'attestation de dépôt', 'attestation dépôt', 'dépôt de dossier',
                'accusé de dépôt', 'confirmation de dépôt', 'récépissé de dépôt'
            ],
            'bulletin_salaire': [
                'bulletin de salaire', 'bulletin de paie', 'fiche de paie',
                'salaire brut', 'salaire net', 'cotisations sociales',
                'employeur', 'salarié', 'période de paie', 'rémunération'
            ],
            'passeport': [
                'passeport', 'passport', 'république française', 'ministère des affaires étrangères',
                'document de voyage', 'identité française', 'nationalité française',
                'passeport français', 'passeport biométrique'
            ]
        }
        
        # Sistema de pontuação mais rigoroso com priorização de documentos jurídicos e específicos
        legal_categories = [
            'tableau_vie_commune', 'refere_suspension', 'accuse_depot', 'accuse_reception',
            'requete_tribunal', 'lettre_recommandee', 'document_tribunal', 
            'procedure_administrative', 'recours_administratif'
        ]
        
        # Categorias específicas com alta prioridade
        specific_categories = [
            'attestation_honneur', 'attestation_depot', 'bulletin_salaire', 'passeport'
        ]
        
        # Primeiro, verifica documentos jurídicos franceses (alta prioridade)
        for category in legal_categories:
            if category in content_patterns:
                patterns = content_patterns[category]
                matches = sum(1 for pattern in patterns if pattern in text_lower)
                if matches >= 1:  # Apenas 1 padrão necessário para documentos jurídicos
                    return {
                        'category': category,
                        'category_name': categories.get(category, category.title()),
                        'method': 'offline_content_legal',
                        'confidence': min(0.9, 0.7 + (matches * 0.1))
                    }
        
        # Segundo, verifica documentos específicos (alta prioridade)
        for category in specific_categories:
            if category in content_patterns:
                patterns = content_patterns[category]
                matches = sum(1 for pattern in patterns if pattern in text_lower)
                if matches >= 1:  # Apenas 1 padrão necessário para documentos específicos
                    return {
                        'category': category,
                        'category_name': categories.get(category, category.title()),
                        'method': 'offline_content_specific',
                        'confidence': min(0.9, 0.7 + (matches * 0.1))
                    }
        
        # Depois, verifica outras categorias com regras específicas
        for category, patterns in content_patterns.items():
            if category in legal_categories or category in specific_categories:
                continue  # Já verificado acima
                
            matches = sum(1 for pattern in patterns if pattern in text_lower)
            if matches > 0:
                # Para RG, exige pelo menos 3 padrões correspondentes (mais restritivo)
                if category == 'rg' and matches >= 3:
                    # Verificação adicional: evita RG se contém termos jurídicos ou específicos
                    legal_terms = ['tribunal', 'attestation', 'accusé', 'requête', 'dépôt', 'passeport', 'bulletin', 'salaire']
                    if not any(term in text_lower for term in legal_terms):
                        return {
                            'category': category,
                            'category_name': categories.get(category, category.title()),
                            'method': 'offline_content',
                            'confidence': min(0.7, 0.4 + (matches * 0.08))  # Confiança reduzida
                        }
                # Para outras categorias não jurídicas, 1 padrão é suficiente
                elif category != 'rg':
                    return {
                        'category': category,
                        'category_name': categories.get(category, category.title()),
                        'method': 'offline_content',
                        'confidence': min(0.8, 0.6 + (matches * 0.1))
                    }
    
    # Fallback final
    return {
        'category': 'outros',
        'category_name': categories.get('outros', 'Outros Documentos'),
        'method': 'offline_fallback',
        'confidence': 0.1
    }

def test_openai_connection(api_key):
    """Testa a conexão com a API OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        # Faz uma chamada simples para testar a conexão
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1,
            timeout=10
        )
        return True, "Conexão OK"
    except Exception as e:
        return False, str(e)

def classify_document_hybrid(file_path, api_key, categories=None):
    """Classificação híbrida melhorada: combina assertividade de regras e IA"""
    if categories is None:
        categories = load_categories()

    filename = os.path.basename(file_path)

    # 1. PRIMEIRO: Extrai texto usando OCR (sempre executa)
    print(f"Extraindo texto via OCR de: {filename}")
    text_content = extract_text_from_file(file_path)

    # 2. Detecção aprimorada para documentos franceses específicos
    text_lower = text_content.lower() if text_content else ""
    filename_lower = filename.lower()

    # Padrões específicos dos documentos reais da pasta "Documentos Anne"
    enhanced_patterns = {
        'bulletin_salaire': ['bulletin', 'salaire', 'cotisations', 'brut', 'net à payer', 'employeur', 'salarié'],
        'passaporte': ['passport', 'passeport', 'república federativa', 'passaporte', 'federal republic'],
        'comprovante_residencia': ['edf', 'electricité de france', 'kwh', 'facture', 'abonnement'],
        'contrato': ['contrat', 'pédagogique', 'formation', 'stage', 'convention'],
        'lista_documents': ['liste', 'documents', 'pièces à fournir', 'membre de famille'],
        'attestation_hebergement': ['attestation', 'hébergement', 'certifie'],
        'facture': ['facture', 'invoice', 'montant', 'ttc', 'commande'],
        'outros': []  # Categoria padrão
    }

    # Detecção forte baseada em padrões dos documentos reais
    strong_match_category = None
    strong_match_confidence = 0.0

    for category, patterns in enhanced_patterns.items():
        if category == 'outros':
            continue
        matches = sum(1 for pattern in patterns if pattern in text_lower or pattern in filename_lower)
        if matches >= 2:  # Pelo menos 2 padrões encontrados
            confidence = min(0.95, 0.60 + (matches * 0.10))
            if confidence > strong_match_confidence:
                strong_match_category = category
                strong_match_confidence = confidence

    # 3. Classificação baseada em regras com texto OCR
    rule_result = classify_offline_fallback(file_path, categories)
    print(f"Regras classificaram como: {rule_result['category']} (confiança: {rule_result['confidence']})")

    # Sobrescreve com detecção forte se encontrada
    if strong_match_category:
        print(f"Padrões aprimorados detectaram: {strong_match_category} (confiança: {strong_match_confidence})")
        rule_result['category'] = strong_match_category
        rule_result['category_name'] = categories.get(strong_match_category, 'Outros Documentos')
        rule_result['confidence'] = strong_match_confidence

    # 4. Verifica sistema de aprendizado
    learned_category, learned_confidence = learning_system.get_intelligent_classification(filename, text_content)
    if learned_category:
        print(f"Sistema aprendido sugere: {learned_category} (confiança: {learned_confidence})")

    # Valida semanticamente o resultado das regras
    semantic_validation = validate_classification_semantically(rule_result['category'], text_content)
    rule_result['confidence'] = min(0.98, rule_result['confidence'] * semantic_validation)

    # REGRA CRÍTICA 1: Se classificou como "outros", assertividade = N/A
    if rule_result['category'] == 'outros':
        rule_result['confidence'] = 'N/A'
        print(f"Categoria 'outros' detectada, assertividade definida como N/A")

    # REGRA CRÍTICA 2: Se classificou em categoria específica, confiança mínima de 30%
    elif isinstance(rule_result['confidence'], (int, float)) and rule_result['confidence'] == 0.0:
        rule_result['confidence'] = 0.30
        print(f"Confiança 0% corrigida para mínimo de 30% (categoria específica: {rule_result['category']})")

    # 4. LÓGICA OTIMIZADA: Usa IA apenas quando realmente necessário
    confidence_threshold = 0.70
    use_ai_threshold = 0.85  # Só chama IA se confiança for menor que isso

    # Tratamento especial para confiança N/A (categoria "outros")
    if rule_result['confidence'] == 'N/A':
        learning_system.record_classification(filename, rule_result['category'], 0, text_content)
        return {
            'category': rule_result['category'],
            'category_name': rule_result['category_name'],
            'method': 'rules_outros_category',
            'confidence': 'N/A'
        }

    if rule_result['category'] != 'outros' and isinstance(rule_result['confidence'], (int, float)) and rule_result['confidence'] >= use_ai_threshold:
        # Alta confiança nas regras, não precisa de IA
        print(f"Alta confiança nas regras ({rule_result['confidence']:.2f}), pulando IA para economizar")
        learning_system.record_classification(filename, rule_result['category'], rule_result['confidence'], text_content)
        return {
            'category': rule_result['category'],
            'category_name': rule_result['category_name'],
            'method': 'rules_high_confidence_no_ai',
            'confidence': rule_result['confidence']
        }

    if rule_result['category'] != 'outros' and rule_result['confidence'] >= confidence_threshold:
        # Aplica IA apenas para validação cruzada com threshold mais alto
        if api_key:
            try:
                print(f"Validando com IA a classificação por regras: {rule_result['category']}")
                ai_result = classify_with_ai(file_path, api_key, categories)
                print(f"IA classificou como: {ai_result['category']} (confiança: {ai_result['confidence']})")
                
                # Consenso forte: ambos concordam com alta confiança
                if (ai_result['category'] == rule_result['category'] and 
                    ai_result['confidence'] >= 0.7 and rule_result['confidence'] >= 0.7):
                    final_confidence = min(0.98, (rule_result['confidence'] + ai_result['confidence']) / 2 + 0.2)
                    learning_system.record_classification(filename, rule_result['category'], final_confidence, text_content)
                    return {
                        'category': rule_result['category'],
                        'category_name': rule_result['category_name'],
                        'method': 'hybrid_strong_consensus',
                        'confidence': final_confidence
                    }
                
                # Discordância: analisa qual tem maior confiança e contexto
                elif ai_result['category'] != rule_result['category']:
                    # Se ambos têm alta confiança mas discordam, prioriza o método mais específico
                    if (ai_result['confidence'] >= 0.8 and rule_result['confidence'] >= 0.8):
                        # Verifica se há padrões específicos no conteúdo que favoreçam uma classificação
                        text_lower = text_content.lower() if text_content else ""
                        
                        # Padrões de alta especificidade para desempate
                        specific_patterns = {
                            'passaporte': ['república federativa', 'federal republic', 'passport'],
                            'rg': ['registro geral', 'carteira de identidade'],
                            'cpf': ['cadastro de pessoa física', 'receita federal'],
                            'cnh': ['carteira nacional de habilitação', 'detran'],
                            'conta_luz': ['kwh', 'energia elétrica', 'distribuidora'],
                            'conta_agua': ['m³', 'saneamento básico'],
                            'extrato_bancario': ['saldo anterior', 'saldo atual', 'conta corrente'],
                            'nota_fiscal': ['cnpj', 'nota fiscal eletrônica', 'chave de acesso']
                        }
                        
                        rule_specificity = sum(1 for pattern in specific_patterns.get(rule_result['category'], []) 
                                             if pattern in text_lower)
                        ai_specificity = sum(1 for pattern in specific_patterns.get(ai_result['category'], []) 
                                           if pattern in text_lower)
                        
                        if rule_specificity > ai_specificity:
                            chosen_result = rule_result
                            method = 'hybrid_rules_high_specificity'
                        elif ai_specificity > rule_specificity:
                            chosen_result = ai_result
                            method = 'hybrid_ai_high_specificity'
                        else:
                            # Em caso de empate, prioriza o com maior confiança
                            chosen_result = rule_result if rule_result['confidence'] >= ai_result['confidence'] else ai_result
                            method = 'hybrid_confidence_priority'
                        
                        learning_system.record_classification(filename, chosen_result['category'], chosen_result['confidence'], text_content)
                        return {
                            'category': chosen_result['category'],
                            'category_name': chosen_result['category_name'],
                            'method': method,
                            'confidence': chosen_result['confidence']
                        }
                
                # IA retornou "outros" mas regras foram específicas
                if ai_result['category'] == 'outros' and rule_result['confidence'] >= confidence_threshold:
                    learning_system.record_classification(filename, rule_result['category'], rule_result['confidence'], text_content)
                    return {
                        'category': rule_result['category'],
                        'category_name': rule_result['category_name'],
                        'method': 'hybrid_rules_over_ai_outros',
                        'confidence': rule_result['confidence']
                    }
                    
            except Exception as e:
                print(f"Erro na IA, mantendo classificação por regras: {str(e)}")
        
        # Validação com sistema aprendido
        if learned_category and learned_category == rule_result['category'] and learned_confidence > 0.7:
            final_confidence = min(0.92, (rule_result['confidence'] + learned_confidence) / 2 + 0.15)
            learning_system.record_classification(filename, rule_result['category'], final_confidence, text_content)
            return {
                'category': rule_result['category'],
                'category_name': rule_result['category_name'],
                'method': 'hybrid_rules_learning_consensus',
                'confidence': final_confidence
            }
        
        # Usa regras com alta confiança
        learning_system.record_classification(filename, rule_result['category'], rule_result['confidence'], text_content)
        return {
            'category': rule_result['category'],
            'category_name': rule_result['category_name'],
            'method': 'rules_high_confidence',
            'confidence': rule_result['confidence']
        }
    
    # 5. Se regras retornaram "outros", aplica IA com mais peso
    if api_key:
        try:
            print(f"Regras incertas, aplicando IA para documento: {filename}")
            ai_result = classify_with_ai(file_path, api_key, categories)
            print(f"IA classificou como: {ai_result['category']} (confiança: {ai_result['confidence']})")
            
            # Se IA encontrou categoria específica, usa ela
            if ai_result['category'] != 'outros' and ai_result['confidence'] >= 0.6:
                # Verifica consenso com sistema aprendido
                if learned_category and learned_category == ai_result['category'] and learned_confidence > 0.5:
                    final_confidence = min(0.9, (ai_result['confidence'] + learned_confidence) / 2 + 0.1)
                    learning_system.record_classification(filename, ai_result['category'], final_confidence, text_content)
                    return {
                        'category': ai_result['category'],
                        'category_name': ai_result['category_name'],
                        'method': 'hybrid_ai_learning_consensus',
                        'confidence': final_confidence
                    }
                
                # Usa IA
                learning_system.record_classification(filename, ai_result['category'], ai_result['confidence'], text_content)
                return {
                    'category': ai_result['category'],
                    'category_name': ai_result['category_name'],
                    'method': 'ai_specific_category',
                    'confidence': ai_result['confidence']
                }
            
        except Exception as e:
            print(f"Erro na IA: {str(e)}")
    
    # 6. Fallback: usa sistema aprendido se disponível
    if learned_category and learned_confidence > 0.6:
        learning_system.record_classification(filename, learned_category, learned_confidence, text_content)
        return {
            'category': learned_category,
            'category_name': categories.get(learned_category, learned_category),
            'method': 'learning_fallback',
            'confidence': learned_confidence
        }
    
    # 7. Último recurso: classificação por regras (mesmo que seja "outros")
    learning_system.record_classification(filename, rule_result['category'], rule_result['confidence'], text_content)
    return rule_result

def classify_with_ai(file_path, api_key, categories):
    """Classificação usando apenas IA (função auxiliar)"""
    filename = os.path.basename(file_path)
    text_content = extract_text_from_file(file_path)
    
    client = OpenAI(api_key=api_key)
    
    # Lista de categorias disponíveis
    categories_list = list(categories.keys())
    categories_description = "\n".join([f"- {k}: {v}" for k, v in categories.items()])
    
    # Prepara o conteúdo para análise da IA com prompt melhorado
    if text_content and len(text_content.strip()) >= 10:
        document_info = f"Conteúdo do documento:\n{text_content[:2000]}"
    else:
        document_info = f"Nome do arquivo: {filename}\nConteúdo extraído: {text_content if text_content else 'Não foi possível extrair texto do documento'}"
    
    # Exemplos few-shot para melhorar precisão
    few_shot_examples = """
EXEMPLOS DE CLASSIFICAÇÃO:

Exemplo 1:
Conteúdo: "REGISTRO GERAL - RG Nº 12.345.678-9 NOME: João Silva FILIAÇÃO: Maria Silva e José Silva NATURALIDADE: São Paulo-SP SECRETARIA DE SEGURANÇA PÚBLICA"
Categoria: rg

Exemplo 2:
Conteúdo: "CEMIG - Companhia Energética de Minas Gerais / Conta de Energia Elétrica / Consumo: 250 kWh / Valor: R$ 180,50 / Endereço: Rua das Flores, 123"
Categoria: conta_luz

Exemplo 3:
Conteúdo: "BULLETIN DE SALAIRE / Employeur: ABC France SARL / Salarié: Pierre Dupont / Salaire brut: 2.500,00 EUR / Cotisations sociales: 450,00 EUR / Salaire net: 2.050,00 EUR"
Categoria: bulletin_salaire

Exemplo 4:
Conteúdo: "TRIBUNAL ADMINISTRATIF / Requête en référé suspension / Demandeur: Madame Silva / Contre: Préfecture de Paris / Objet: Contestation refus titre de séjour"
Categoria: refere_suspension

Exemplo 5:
Conteúdo: "ATTESTATION SUR L'HONNEUR / Je soussigné Monsieur Silva, atteste sur l'honneur héberger mon épouse Madame Silva à titre gratuit / Fait à Paris, le 15/01/2024"
Categoria: attestation_honneur
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # Mudado para gpt-4o (mais preciso que mini)
        messages=[
            {
                "role": "system",
                "content": f"""Você é um especialista em classificação de documentos brasileiros e franceses com anos de experiência.

CATEGORIAS DISPONÍVEIS:
{categories_description}

{few_shot_examples}

PROCESSO DE ANÁLISE (Chain-of-Thought):
1. Leia o conteúdo do documento cuidadosamente
2. Identifique palavras-chave, números de registro, órgãos emissores
3. Analise o contexto: é um documento de identidade? comprovante? documento jurídico?
4. Compare com os exemplos fornecidos
5. Se houver múltiplas possibilidades, escolha a MAIS ESPECÍFICA
6. Apenas use 'outros' se realmente não se encaixar em nenhuma categoria

REGRAS IMPORTANTES:
- Documentos em francês com termos jurídicos (tribunal, préfecture, requête) → categorias jurídicas francesas
- Contas com consumo em kWh → conta_luz
- Contas com m³ de água → conta_agua
- Bulletins de salaire (França) → bulletin_salaire
- Attestations sur l'honneur → attestation_honneur
- RG sempre tem "Registro Geral" ou número no formato XX.XXX.XXX-X
- CPF tem formato XXX.XXX.XXX-XX

Responda APENAS com a categoria (chave), sem explicações."""
            },
            {
                "role": "user",
                "content": f"Classifique este documento:\n\n{document_info}"
            }
        ],
        max_tokens=50,
        temperature=0.1  # Baixa temperatura mas não zero (permite alguma criatividade)
    )
    
    category = response.choices[0].message.content.strip().lower()
    
    # Valida se a categoria retornada existe
    if category not in categories:
        category = 'outros'
    
    # Calcula confiança baseada na qualidade do conteúdo
    confidence = 0.8  # Confiança padrão da IA
    if text_content and len(text_content.strip()) >= 50:
        confidence = 0.9  # Mais confiança com mais texto
    elif not text_content or len(text_content.strip()) < 10:
        confidence = 0.5  # Menos confiança sem texto
    
    return {
        'category': category,
        'category_name': categories[category],
        'method': 'openai_api',
        'confidence': confidence
    }

def classify_document(file_path, api_key, categories=None):
    """Função principal de classificação - agora usa o sistema híbrido"""
    return classify_document_hybrid(file_path, api_key, categories)


def classify_with_openai_api(filename, text_content, api_key, categories):
    """Classifica documento usando a API OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        
        # Prepara informações do documento
        document_info = f"Nome do arquivo: {filename}"
        if text_content:
            document_info += f"\n\nConteúdo extraído:\n{text_content[:2000]}"  # Limita o texto
        
        # Lista de categorias para o prompt
        categories_list = "\n".join([f'- "{name}" → {key}' for key, name in categories.items()])
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""Você é um especialista em classificação de documentos. 
                    Analise o documento fornecido e classifique-o em uma das seguintes categorias:
                    
                    {categories_list}
                    
                    Responda APENAS com o nome da categoria (chave), sem explicações adicionais.
                    Se não conseguir identificar claramente, use 'outros'."""
                },
                {
                    "role": "user", 
                    "content": f"Classifique este documento:\n\n{document_info}"
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip().lower()
        
        # Valida se a categoria retornada existe
        if category not in categories:
            category = 'outros'
        
        # Registra a classificação no sistema de aprendizado
        api_confidence = 1.0  # Confiança padrão da API
        learning_system.record_classification(filename, category, api_confidence, text_content)
        
        return {
            'category': category,
            'category_name': categories[category],
            'method': 'openai_api',
            'confidence': api_confidence
        }
        
    except Exception as api_error:
        error_msg = str(api_error)
        print(f"Erro detalhado na API OpenAI: {error_msg}")
        print(f"Tipo do erro: {type(api_error).__name__}")
        print(f"Arquivo sendo processado: {file_path}")
        
        # Verifica se é erro de autenticação
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            print("ERRO: Chave da API OpenAI inválida ou não configurada!")
        
        # Usa fallback offline em caso de erro
        print(f"Usando classificação offline para: {os.path.basename(file_path)}")
        result = classify_offline_fallback(file_path, categories)
        
        # Registra a classificação offline no sistema de aprendizado
        offline_confidence = 0.5  # Confiança menor para classificação offline
        learning_system.record_classification(filename, result['category'], offline_confidence, text_content)
        
        return result

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Recebe feedback do usuário para melhorar a classificação"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        category = data.get('category')
        is_positive = data.get('is_positive')
        session_id = data.get('session_id')

        if not filename or not category or is_positive is None:
            return jsonify({'error': 'Filename, category e is_positive são obrigatórios'}), 400

        print(f"Feedback recebido: {filename} -> {category} -> {'Positivo' if is_positive else 'Negativo'}")

        # Registra o feedback no sistema de aprendizado
        if is_positive:
            # Feedback positivo: reforça a classificação atual
            learning_system.record_positive_feedback(filename, category)
        else:
            # Feedback negativo: marca para revisão
            learning_system.record_negative_feedback(filename, category)

        return jsonify({
            'success': True,
            'message': f'Feedback {"positivo" if is_positive else "negativo"} registrado com sucesso.'
        })

    except Exception as e:
        print(f"Erro ao processar feedback: {e}")
        return jsonify({'error': f'Erro ao processar feedback: {str(e)}'}), 500

@app.route('/dashboard')
def dashboard():
    """Página do dashboard de aprendizado inteligente"""
    return render_template('dashboard.html')

@app.route('/api/performance', methods=['GET'])
def get_performance_report():
    """Retorna relatório de performance do sistema de aprendizado"""
    try:
        report = learning_system.get_performance_report()
        return jsonify(report)
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'}), 500

def extract_semantic_features(text_content):
    """Extrai features semânticas do conteúdo para validação"""
    features = {
        'has_cpf': bool(re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text_content)),
        'has_rg': bool(re.search(r'\d{1,2}\.\d{3}\.\d{3}-\d{1,2}', text_content)),
        'has_cnpj': bool(re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text_content)),
        'has_cep': bool(re.search(r'\d{5}-?\d{3}', text_content)),
        'has_money': bool(re.search(r'R\$\s*\d+[,.]?\d*', text_content)),
        'has_kwh': 'kwh' in text_content.lower(),
        'has_m3': 'm³' in text_content.lower() or 'm3' in text_content.lower(),
        'has_tribunal': 'tribunal' in text_content.lower(),
        'has_attestation': 'attestation' in text_content.lower(),
        'has_salaire': 'salaire' in text_content.lower() or 'bulletin' in text_content.lower(),
        'language': 'french' if any(word in text_content.lower() for word in ['monsieur', 'madame', 'attestation', 'tribunal']) else 'portuguese'
    }
    return features

def validate_classification_semantically(category, text_content):
    """Valida se a classificação faz sentido semanticamente com o conteúdo"""
    if not text_content or len(text_content) < 10:
        return 0.5  # Confiança neutra sem conteúdo

    features = extract_semantic_features(text_content)
    text_lower = text_content.lower()

    # Validações específicas por categoria
    validations = {
        'rg': features['has_rg'] or 'registro geral' in text_lower or 'identidade' in text_lower,
        'cpf': features['has_cpf'] or 'cadastro de pessoa' in text_lower,
        'conta_luz': features['has_kwh'] or 'energia' in text_lower or 'cemig' in text_lower,
        'conta_agua': features['has_m3'] or 'saneamento' in text_lower or 'sabesp' in text_lower,
        'bulletin_salaire': features['has_salaire'] and features['language'] == 'french',
        'attestation_honneur': features['has_attestation'] and 'honneur' in text_lower,
        'refere_suspension': features['has_tribunal'] and 'référé' in text_lower,
        'extrato_bancario': 'saldo' in text_lower or 'extrato' in text_lower,
        'nota_fiscal': features['has_cnpj'] or 'nota fiscal' in text_lower,
    }

    # Retorna confiança boost se validação passou
    if category in validations:
        return 1.3 if validations[category] else 0.6

    return 1.0  # Confiança neutra para outras categorias

def classify_offline_fallback(file_path, categories):
    """Classificação offline robusta baseada em padrões do nome do arquivo e conteúdo"""
    filename = os.path.basename(file_path).lower()
    filename_lower = filename

    # Extrai texto do arquivo para análise adicional
    text_content = extract_text_from_file(file_path).lower()

    # Padrões consolidados e otimizados de classificação
    filename_patterns = {
        # Documentos de Identidade
        'rg': ['rg', 'identidade', 'carteira', 'id_', 'identity', 'registro_geral', 'id-', 'id.'],
        'cpf': ['cpf', 'cadastro_pessoa_fisica'],
        'cnh': ['cnh', 'habilitacao', 'carteira_nacional', 'driver', 'license'],
        'passaporte': ['passaporte', 'passport', 'idfra', 'idfraben'],
        
        # Certidões
        'certidao_nascimento': ['nascimento', 'certidao_nascimento', 'birth', 'certificate_birth'],
        'certidao_casamento': ['casamento', 'certidao_casamento', 'marriage', 'certificate_marriage'],
        'certidao_obito': ['obito', 'certidao_obito', 'death', 'certificate_death'],
        
        # Documentos Trabalhistas
        'contracheque': ['contracheque', 'holerite', 'payroll', 'salario', 'folha_pagamento'],
        'ctps': ['ctps', 'carteira_trabalho', 'trabalho'],
        'contrato_trabalho': ['contrato_trabalho', 'admissao', 'contrato_emprego'],
        
        # Comprovantes de Residência
        'comprovante_residencia': ['comprovante_residencia', 'endereco', 'address', 'comprovante_endereco'],
        'conta_luz': ['luz', 'energia', 'cemig', 'cpfl', 'eletrica', 'electric', 'energia_eletrica'],
        'conta_agua': ['agua', 'saneamento', 'sabesp', 'copasa', 'hidrica'],
        'conta_gas': ['gas', 'comgas', 'naturgy', 'gasosa'],
        'conta_telefone': ['telefone', 'celular', 'vivo', 'tim', 'claro', 'oi', 'mobile', 'phone'],
        'iptu': ['iptu', 'predial', 'territorial', 'imposto_predial'],
        
        # Documentos Bancários (consolidados)
        'extrato_bancario': ['extrato', 'banco', 'bank', 'statement', 'bancario', 'conta_corrente'],
        'comprovante_bancario': ['comprovante_bancario', 'comprovante_banco', 'bank_proof'],
        'comprovante_transferencia': ['transferencia', 'ted', 'doc', 'pix', 'transfer'],
        'comprovante_deposito': ['deposito', 'deposit', 'comprovante_deposito'],
        
        # Documentos Educacionais
        'diploma': ['diploma', 'graduation', 'formatura', 'graduacao'],
        'certificado': ['certificado', 'certificate', 'cert', 'certificat', 'certificacao'],
        'historico_escolar': ['historico', 'escolar', 'transcript', 'academic'],
        'declaracao_escolar': ['declaracao_escolar', 'matricula', 'enrollment'],
        
        # Documentos Médicos (consolidados)
        'atestado_medico': ['atestado', 'medico', 'medical', 'saude', 'health', 'atestado_medico'],
        'laudo_medico': ['laudo', 'laudo_medico', 'medical_report', 'exame', 'resultado'],
        'comprovante_vacinacao': ['comprovante_vacinacao', 'vacina', 'vaccination', 'cartao_vacinacao'],
        
        # Comprovantes de Pagamento
        'comprovante_pagamento': ['comprovante_pagamento', 'payment_proof'],
        'recibo': ['recibo', 'pagamento', 'receipt'],
        'nota_fiscal': ['nota', 'fiscal', 'nf', 'nfe', 'invoice'],
        'boleto': ['boleto', 'cobranca', 'billing'],
        'comprovante_quitacao': ['comprovante_quitacao', 'quitacao', 'paid_off'],
        
        # Documentos Legais (consolidados)
        'autorizacao': ['autorizacao', 'authorization'],
        'procuracao': ['procuracao', 'mandato', 'representacao', 'power_attorney'],
        'declaracao': ['declaracao', 'declaration'],
        'licenca': ['licenca', 'license_permit'],
        'alvara': ['alvara', 'funcionamento', 'permit'],
        'permissao': ['permissao', 'permission'],
        
        # Documentos Jurídicos
        'contrato': ['contrato', 'acordo', 'contract', 'termo', 'agreement'],
        'peticao': ['peticao', 'inicial', 'recurso', 'defesa', 'petition'],
        'sentenca': ['sentenca', 'decisao', 'julgamento', 'acordao', 'judgment'],
        
        # Correspondências
        'carta': ['carta', 'letter', 'correspondencia', 'missiva', 'comunicacao'],
        
        # Outros (consolidados)
        'credencial': ['credencial', 'credential'],
        'carteirinha': ['carteirinha', 'card_id'],
        'cartao': ['cartao', 'card'],
        'comprovante_isencao': ['comprovante_isencao', 'isencao', 'exemption']
    }
    
    # Primeiro verifica o nome do arquivo
    for category, keywords in filename_patterns.items():
        if any(keyword in filename_lower for keyword in keywords):
            # Tratamento especial para notas fiscais
            if category == 'outros' and any(word in filename_lower for word in ['nota', 'fiscal', 'nf', 'nfe']):
                return {
                    'category': 'nota_fiscal',
                    'category_name': categories.get('nota_fiscal', 'Notas Fiscais'),
                    'method': 'offline_filename_fallback',
                    'confidence': 0.8
                }
            return {
                'category': category,
                'category_name': categories.get(category, category.title()),
                'method': 'offline_filename_fallback',
                'confidence': 0.8
            }
    
    # Se não encontrou no nome, verifica o conteúdo do texto com validação aprimorada
    if text_content:
        # Contador de matches para determinar confiança
        category_matches = {}
        
        for category, keywords in filename_patterns.items():
            match_count = sum(1 for keyword in keywords if keyword in text_content)
            if match_count > 0:
                category_matches[category] = match_count
        
        # Se encontrou matches, escolhe o com maior número de correspondências
        if category_matches:
            best_category = max(category_matches, key=category_matches.get)
            match_count = category_matches[best_category]
            
            # Ajusta confiança baseada no número de matches
            confidence = min(0.9, 0.5 + (match_count * 0.1))

            # Valida semanticamente
            semantic_boost = validate_classification_semantically(best_category, text_content)
            final_confidence = min(0.95, confidence * semantic_boost)

            return {
                'category': best_category,
                'category_name': categories.get(best_category, best_category.title()),
                'method': 'offline_content_fallback_validated',
                'confidence': final_confidence
            }
        
        # Padrões específicos no conteúdo com validação rigorosa
        content_patterns = {
            'passaporte': ['idfra', 'passport', 'república federativa', 'federal republic'],
            'rg': ['registro geral', 'carteira de identidade', 'identity card'],
            'cpf': ['cadastro de pessoa física', 'receita federal'],
            'cnh': ['carteira nacional de habilitação', 'driver license'],
            'conta_luz': ['kwh', 'energia elétrica', 'cemig', 'cpfl', 'eletropaulo'],
            'conta_agua': ['m³', 'metros cúbicos', 'sabesp', 'copasa', 'saneamento'],
            'conta_telefone': ['minutos', 'dados móveis', 'vivo', 'tim', 'claro', 'oi'],
            'extrato_bancario': ['saldo anterior', 'saldo atual', 'extrato de conta'],
            'nota_fiscal': ['cnpj', 'nota fiscal eletrônica', 'chave de acesso']
        }
        
        for category, patterns in content_patterns.items():
            pattern_matches = sum(1 for pattern in patterns if pattern in text_content)
            if pattern_matches >= 2:  # Requer pelo menos 2 padrões para alta confiança
                return {
                    'category': category,
                    'category_name': categories.get(category, category.title()),
                    'method': 'offline_content_pattern',
                    'confidence': 0.85
                }
            elif pattern_matches == 1:  # 1 padrão = confiança média
                return {
                    'category': category,
                    'category_name': categories.get(category, category.title()),
                    'method': 'offline_content_pattern',
                    'confidence': 0.65
                }
    
    # Fallback final com confiança muito baixa
    return {
        'category': 'outros',
        'category_name': categories.get('outros', 'Outros Documentos'),
        'method': 'offline_fallback',
        'confidence': 0.05
    }

def upload_files():
    """Endpoint para upload de arquivos"""
    if 'files' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Criar pasta da sessão
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    results = []
    
    for file in files:
        if file and file.filename != '':
            # Salvar arquivo
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_folder, filename)
            file.save(file_path)
            
            # Classificar documento
            classification_result = classify_document(file_path)
            
            results.append({
                'filename': filename,
                'category': classification_result['category'],
                'category_name': classification_result['category_name']
            })
    
    return jsonify({
        'session_id': session_id,
        'results': results
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Recebe múltiplos arquivos para upload"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    files = request.files.getlist('files[]')
    api_key = request.form.get('api_key', '')  # API key opcional

    # Cria pasta única para esta sessão
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(session_folder, filename)
            file.save(filepath)
            uploaded_files.append({
                'name': filename,
                'path': filepath
            })
    
    return jsonify({
        'session_id': session_id,
        'files': uploaded_files,
        'count': len(uploaded_files)
    })

@app.route('/api/classify', methods=['POST'])
def classify_documents():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        api_key = data.get('api_key')
        categories = data.get('categories', DOCUMENT_TYPES)
        
        if not session_id:
            return jsonify({'error': 'Session ID é obrigatório'}), 400
        
        # Se não há API key, usa modo offline
        if not api_key:
            print("Modo offline ativado - sem API key fornecida")
            use_offline_mode = True
        else:
            # Testa a conexão com a API OpenAI primeiro
            connection_ok, connection_msg = test_openai_connection(api_key)
            if not connection_ok:
                print(f"Falha no teste de conexão: {connection_msg}")
                print("Ativando modo offline como fallback")
                use_offline_mode = True
            else:
                use_offline_mode = False
        
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        if not os.path.exists(session_folder):
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        results = []
        total_files = len([f for f in os.listdir(session_folder) if os.path.isfile(os.path.join(session_folder, f))])
        processed_count = 0
        
        print(f"Iniciando classificação de {total_files} arquivos...")
        
        for filename in os.listdir(session_folder):
            file_path = os.path.join(session_folder, filename)
            if os.path.isfile(file_path):
                processed_count += 1
                print(f"Processando arquivo {processed_count}/{total_files}: {filename}")
                
                try:
                    # PRIMEIRO: Extrai texto via OCR (sempre)
                    print(f"  Extraindo texto via OCR...")
                    text_content = extract_text_from_file(file_path)
                    print(f"  OCR extraiu {len(text_content)} caracteres")

                    if use_offline_mode:
                        # Usa classificação offline COM texto OCR
                        classification = classify_offline_fallback(file_path, categories, text_content)
                    else:
                        # Usa API OpenAI
                        classification = classify_document(file_path, api_key, categories)
                    ocr_confidence = min(1.0, len(text_content) / 500) if text_content else 0.0

                    # Se for bulletin de salaire, extrai mês e ano para renomear
                    suggested_filename = filename
                    if classification['category'] == 'bulletin_salaire':
                        mes, ano = extract_month_year_from_bulletin(text_content)
                        if mes and ano:
                            # Nomes dos meses em francês para exibição
                            meses_nome = {
                                '01': 'Janvier', '02': 'Février', '03': 'Mars', '04': 'Avril',
                                '05': 'Mai', '06': 'Juin', '07': 'Juillet', '08': 'Août',
                                '09': 'Septembre', '10': 'Octobre', '11': 'Novembre', '12': 'Décembre'
                            }
                            mes_nome = meses_nome.get(mes, mes)
                            suggested_filename = f"Bulletin_de_salaire_{mes_nome}_{ano}.pdf"
                            print(f"  → Nome sugerido: {suggested_filename}")

                    results.append({
                        'filename': filename,
                        'suggested_filename': suggested_filename,
                        'category': classification['category'],
                        'category_name': classification['category_name'],
                        'confidence': classification.get('confidence', 0.0),
                        'method': classification.get('method', 'unknown'),
                        'ocr_confidence': round(ocr_confidence, 2),
                        'used_ai': 'ai' in classification.get('method', '').lower() or 'openai' in classification.get('method', '').lower()
                    })
                    
                    print(f"  ✓ {filename} classificado como: {classification['category_name']} (confiança: {classification.get('confidence', 'N/A')})")
                    
                except Exception as e:
                    print(f"  ✗ Erro ao classificar {filename}: {str(e)}")
                    results.append({
                        'filename': filename,
                        'category': 'outros',
                        'category_name': categories.get('outros', 'Outros Documentos')
                    })
        
        print(f"Classificação concluída! {len(results)} arquivos processados.")
        
        return jsonify({
            'results': results,
            'total_files': len(results)
        })
    
    except Exception as e:
        print(f"Erro na classificação: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_organized():
    """Cria e retorna um ZIP com documentos organizados em pastas"""
    try:
        data = request.json
        print(f"Dados recebidos no download: {data}")

        session_id = data.get('session_id')
        classifications = data.get('classifications')

        print(f"Download solicitado - Session: {session_id}, Classifications recebidas: {classifications}")

        if not session_id:
            print(f"Erro: session_id não fornecido")
            return jsonify({'error': 'session_id é obrigatório'}), 400

        if not classifications or not isinstance(classifications, list) or len(classifications) == 0:
            print(f"Erro: classifications inválido ou vazio - Tipo: {type(classifications)}, Conteúdo: {classifications}")
            return jsonify({'error': 'classifications deve ser uma lista não vazia'}), 400
    
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)

        if not os.path.exists(session_folder):
            print(f"Erro: Pasta da sessão não encontrada: {session_folder}")
            return jsonify({'error': 'Sessão não encontrada ou já foi processada'}), 404

        # Cria ZIP em memória
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Organiza arquivos por categoria
            for item in classifications:
                filename = item['filename']
                category_name = item['category_name']
                suggested_filename = item.get('suggested_filename', filename)

                source_path = os.path.join(session_folder, filename)

                if os.path.exists(source_path):
                    # Usa nome sugerido se disponível
                    final_filename = suggested_filename if suggested_filename else filename
                    # Adiciona arquivo no ZIP dentro da pasta da categoria
                    zip_path = os.path.join(category_name, final_filename)
                    zip_file.write(source_path, zip_path)
                    if suggested_filename != filename:
                        print(f"  Adicionado ao ZIP: {zip_path} (renomeado de {filename})")
                    else:
                        print(f"  Adicionado ao ZIP: {zip_path}")
                else:
                    print(f"  Arquivo não encontrado: {source_path}")

            # Adiciona relatório
            report = generate_report(classifications)
            zip_file.writestr('RELATORIO.txt', report)
            print("  Relatório adicionado ao ZIP")

        zip_buffer.seek(0)
        print(f"ZIP criado com sucesso! Tamanho: {zip_buffer.getbuffer().nbytes} bytes")

        # Limpa arquivos da sessão
        try:
            shutil.rmtree(session_folder)
            print(f"Pasta da sessão removida: {session_folder}")
        except Exception as e:
            print(f"Erro ao remover pasta da sessão: {e}")

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'documentos_organizados_{session_id}.zip'
        )

    except Exception as e:
        print(f"Erro ao gerar ZIP: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro ao gerar arquivo ZIP: {str(e)}'}), 500

def generate_report(classifications):
    """Gera relatório textual da classificação"""
    report = f"""RELATÓRIO DE CLASSIFICAÇÃO DE DOCUMENTOS
===============================================
Total de documentos processados: {len(classifications)}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

"""
    
    # Agrupa por categoria
    by_category = {}
    for item in classifications:
        category = item['category_name']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(item['filename'])
    
    for category, files in by_category.items():
        report += f"\n{category} ({len(files)} documento(s)):\n"
        for filename in files:
            report += f"  - {filename}\n"
    
    report += "\n===============================================\n"
    report += "Os documentos foram organizados automaticamente em pastas.\n"
    report += "Cada pasta corresponde a uma categoria de documento.\n"
    
    return report

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica se o servidor está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Servidor funcionando'})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Retorna as categorias atuais"""
    categories = load_categories()
    return jsonify({'categories': categories})

@app.route('/api/categories', methods=['POST'])
def save_categories_endpoint():
    """Salva categorias personalizadas"""
    try:
        print("=== ENDPOINT SAVE CATEGORIES CHAMADO ===")
        data = request.get_json()
        print(f"Dados recebidos: {data}")
        categories = data.get('categories')
        print(f"Categorias extraídas: {categories}")
        
        if not categories:
            print("ERRO: Categorias não fornecidas")
            return jsonify({'error': 'Categorias não fornecidas'}), 400
        
        # Garante que a categoria 'outros' sempre existe
        if 'outros' not in categories:
            categories['outros'] = 'Outros Documentos'
        
        print("Chamando função save_categories...")
        success = save_categories(categories)
        print(f"Resultado do salvamento: {success}")
        
        if success:
            print("Categorias salvas com sucesso!")
            return jsonify({'message': 'Categorias salvas com sucesso', 'categories': categories})
        else:
            print("ERRO: Falha ao salvar categorias")
            return jsonify({'error': 'Erro ao salvar categorias'}), 500
            
    except Exception as e:
        print(f"ERRO CRÍTICO no endpoint: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/separate-documents', methods=['POST'])
def separate_documents():
    """Endpoint para separar múltiplos documentos de um arquivo"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nome do arquivo vazio'}), 400
        
        # Salva o arquivo temporariamente
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_extension = os.path.splitext(filename)[1].lower()
        separated_docs = []
        
        if file_extension == '.pdf':
            # Separa PDF por páginas
            separated_docs = separate_documents_from_pdf(file_path)
            
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            # Para imagens, extrai texto e tenta detectar múltiplos documentos
            full_text = extract_text_from_file(file_path)
            if full_text:
                boundaries = detect_document_boundaries(full_text)
                
                if len(boundaries) > 1:
                    # Múltiplos documentos detectados
                    for i in range(len(boundaries)):
                        start = boundaries[i]
                        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(full_text)
                        doc_text = full_text[start:end].strip()
                        
                        if doc_text:
                            separated_docs.append({
                                'document_number': i + 1,
                                'text': doc_text,
                                'filename': f"{os.path.splitext(filename)[0]}_documento_{i + 1}.txt"
                            })
                else:
                    # Apenas um documento
                    separated_docs.append({
                        'document_number': 1,
                        'text': full_text,
                        'filename': f"{os.path.splitext(filename)[0]}_documento_1.txt"
                    })
        
        # Remove arquivo temporário
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'original_filename': filename,
            'documents_found': len(separated_docs),
            'documents': separated_docs
        })
        
    except Exception as e:
        print(f"Erro ao separar documentos: {e}")
        return jsonify({'error': f'Erro ao separar documentos: {str(e)}'}), 500

@app.route('/')
def index():
    """Serve a página frontend"""
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)