from flask import Flask, request, jsonify, send_file
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
from PIL import Image
import re
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

DOCUMENT_TYPES = {
    'holerite': 'Holerites',
    'certidao_nascimento': 'Certidões de Nascimento',
    'comprovante_residencia': 'Comprovantes de Residência',
    'rg': 'RG',
    'cpf': 'CPF',
    'cnh': 'CNH',
    'ctps': 'CTPS',
    'contrato': 'Contratos',
    'procuracao': 'Procurações',
    'peticao': 'Petições',
    'sentenca': 'Sentenças',
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
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar categorias: {e}")
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text_from_file(file_path):
    """Extrai texto de arquivos PDF ou imagens usando OCR"""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            # Extração de texto de PDF
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
            
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            # OCR para imagens
            try:
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image, lang='por')
                return text.strip()
            except Exception as ocr_error:
                print(f"Erro no OCR: {ocr_error}")
                return ""
        
        return ""
    except Exception as e:
        print(f"Erro ao extrair texto de {file_path}: {e}")
        return ""

def classify_offline_fallback(file_path, categories):
    """Classificação offline baseada no conteúdo do arquivo"""
    
    # Primeiro tenta extrair texto do arquivo
    content = extract_text_from_file(file_path)
    
    # Se conseguiu extrair texto, classifica baseado no conteúdo
    if content:
        content_lower = content.lower()
        
        # Padrões para identificação por conteúdo
        content_patterns = {
            'cnh': [
                'carteira nacional de habilitacao', 'cnh', 'condutor', 'categoria', 'validade',
                'detran', 'habilitacao', 'motorista', 'veiculo automotor', 'permissao'
            ],
            'rg': [
                'registro geral', 'carteira de identidade', 'secretaria de seguranca',
                'identidade', 'filiacao', 'naturalidade', 'estado civil', 'profissao'
            ],
            'cpf': [
                'cadastro de pessoa fisica', 'receita federal', 'cpf', 'situacao cadastral',
                'comprovante de inscricao', 'regularidade fiscal'
            ],
            'holerite': [
                'demonstrativo de pagamento', 'holerite', 'salario', 'vencimentos',
                'descontos', 'liquido', 'inss', 'irrf', 'fgts', 'folha de pagamento'
            ],
            'comprovante_residencia': [
                'comprovante de residencia', 'conta de luz', 'conta de agua', 'conta de gas',
                'telefone', 'internet', 'endereco', 'consumo', 'vencimento', 'fatura'
            ],
            'certidao_nascimento': [
                'certidao de nascimento', 'cartorio', 'registro civil', 'nascimento',
                'filiacao', 'data de nascimento', 'naturalidade'
            ],
            'ctps': [
                'carteira de trabalho', 'ctps', 'previdencia social', 'trabalho',
                'empregador', 'admissao', 'funcao', 'salario contratual'
            ],
            'contrato': [
                'contrato', 'acordo', 'clausulas', 'partes contratantes', 'objeto',
                'prazo', 'valor', 'condicoes', 'termo', 'aditivo'
            ],
            'procuracao': [
                'procuracao', 'mandato', 'outorgante', 'outorgado', 'poderes',
                'representacao', 'substabelecer', 'revogar'
            ],
            'peticao': [
                'peticao inicial', 'excelentissimo', 'meritissimo', 'juiz', 'vara',
                'requer', 'direito', 'pedido', 'fundamentacao', 'recurso'
            ],
            'sentenca': [
                'sentenca', 'acordao', 'decisao', 'julgamento', 'tribunal',
                'relator', 'ementa', 'dispositivo', 'julgo', 'condeno'
            ]
        }
        
        # Verifica padrões no conteúdo
        for category, keywords in content_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            # Se encontrar pelo menos 2 palavras-chave da categoria
            if matches >= 2:
                return {
                    'category': category,
                    'category_name': categories.get(category, category.title()),
                    'cost': 0.0,
                    'method': 'offline_content_analysis',
                    'confidence': min(matches / len(keywords), 1.0)
                }
        
        # Verifica padrões para notas fiscais e documentos comerciais
        commercial_keywords = [
            'nota fiscal', 'nf-e', 'danfe', 'cnpj', 'inscricao estadual',
            'icms', 'ipi', 'valor total', 'destinatario', 'emitente',
            'cupom fiscal', 'fatura', 'boleto', 'cobranca', 'invoice'
        ]
        
        commercial_matches = sum(1 for keyword in commercial_keywords if keyword in content_lower)
        if commercial_matches >= 2:
            return {
                'category': 'outros',
                'category_name': 'Notas Fiscais e Documentos Comerciais',
                'cost': 0.0,
                'method': 'offline_content_analysis',
                'confidence': min(commercial_matches / len(commercial_keywords), 1.0)
            }
    
    # Se não conseguiu extrair texto ou não encontrou padrões, usa o nome do arquivo como fallback
    filename = os.path.basename(file_path)
    filename_lower = filename.lower()
    
    # Padrões para identificação por nome (fallback)
    filename_patterns = {
        'cnh': ['cnh', 'carteira', 'habilitacao', 'motorista', 'condutor'],
        'rg': ['rg', 'registro', 'identidade', 'cedula'],
        'cpf': ['cpf', 'receita', 'federal', 'cadastro'],
        'holerite': ['holerite', 'salario', 'folha', 'pagamento', 'contracheque'],
        'comprovante_residencia': ['comprovante', 'residencia', 'endereco', 'conta', 'luz', 'agua'],
        'certidao_nascimento': ['certidao', 'nascimento', 'cartorio', 'civil'],
        'ctps': ['ctps', 'trabalho', 'previdencia', 'carteira'],
        'contrato': ['contrato', 'acordo', 'termo', 'aditivo'],
        'procuracao': ['procuracao', 'mandato', 'representacao'],
        'peticao': ['peticao', 'inicial', 'recurso', 'defesa'],
        'sentenca': ['sentenca', 'decisao', 'julgamento', 'acordao'],
        'outros': ['nota', 'fiscal', 'nf', 'nfe', 'cupom', 'fatura', 'boleto']
    }
    
    # Verifica padrões no nome do arquivo
    for category, keywords in filename_patterns.items():
        if any(keyword in filename_lower for keyword in keywords):
            if category == 'outros' and any(word in filename_lower for word in ['nota', 'fiscal', 'nf', 'nfe']):
                return {
                    'category': 'outros',
                    'category_name': 'Notas Fiscais e Documentos Comerciais',
                    'cost': 0.0,
                    'method': 'offline_filename_fallback',
                    'confidence': 0.5
                }
            return {
                'category': category,
                'category_name': categories.get(category, category.title()),
                'cost': 0.0,
                'method': 'offline_filename_fallback',
                'confidence': 0.5
            }
    
    # Fallback final
    return {
        'category': 'outros',
        'category_name': categories.get('outros', 'Outros Documentos'),
        'cost': 0.0,
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

def classify_document(file_path, api_key, categories=None):
    """Classifica um documento usando GPT-4o"""
    try:
        # Usa categorias padrão se não fornecidas
        if categories is None:
            categories = DOCUMENT_TYPES
        
        # Codifica a imagem
        image_data = encode_image(file_path)
        
        # Determina o tipo MIME
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # Cria lista de categorias para o prompt
        categories_list = '\n'.join([f"- {key}: {name}" for key, name in categories.items()])
        
        # Prompt otimizado para classificação
        prompt = f"""Analise este documento brasileiro e classifique-o em uma das categorias abaixo.

CATEGORIAS DISPONÍVEIS:
{categories_list}

INSTRUÇÕES:
1. Examine cuidadosamente o documento
2. Identifique elementos como: cabeçalhos, logos, campos específicos, layout
3. Responda APENAS com a chave da categoria (ex: "rg", "cnh", "holerite")
4. Se não conseguir identificar com certeza, use "outros"

EXEMPLOS:
- Documento com foto e "CARTEIRA NACIONAL DE HABILITAÇÃO" → cnh
- Documento com "REGISTRO GERAL" ou "RG" → rg
- Documento com salário e descontos → holerite
- Documento com endereço e comprovação de residência → comprovante_residencia

Responda apenas com a chave da categoria:"""

        # Faz a chamada para a API com tratamento de erro robusto
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=50,
                temperature=0.1,
                timeout=30  # Timeout de 30 segundos
            )
            
            # Extrai a categoria da resposta
            category = response.choices[0].message.content.strip().lower()
            
            # Valida se a categoria existe
            if category not in categories:
                category = 'outros'
            
            # Calcula o custo aproximado
            cost = 0.01  # Custo estimado por classificação
            
            return {
                'category': category,
                'category_name': categories[category],
                'cost': cost,
                'method': 'openai_api'
            }
            
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"Erro detalhado na API OpenAI: {error_msg}")
            print(f"Tipo do erro: {type(api_error).__name__}")
            
            # Verifica se é erro de autenticação
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                print("ERRO: Chave da API OpenAI inválida ou não configurada!")
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                print("ERRO: Problema de conexão com a API OpenAI")
            
            print(f"Usando classificação offline para: {os.path.basename(file_path)}")
            # Usa classificação offline como fallback
            return classify_offline_fallback(file_path, categories)
        
    except Exception as e:
        print(f"Erro na classificação: {str(e)}")
        return 'outros', categories.get('outros', 'Outros Documentos'), 0.0

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Recebe múltiplos arquivos para upload"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    files = request.files.getlist('files[]')
    api_key = request.form.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'Chave API não fornecida'}), 400
    
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
        total_cost = 0.0
        
        for filename in os.listdir(session_folder):
            file_path = os.path.join(session_folder, filename)
            if os.path.isfile(file_path):
                try:
                    if use_offline_mode:
                        # Usa classificação offline
                        classification = classify_offline_fallback(file_path, categories)
                    else:
                        # Usa API OpenAI
                        classification = classify_document(file_path, api_key, categories)
                    
                    results.append({
                        'filename': filename,
                        'category': classification['category'],
                        'category_name': classification['category_name']
                    })
                    total_cost += classification['cost']
                except Exception as e:
                    print(f"Erro ao classificar {filename}: {str(e)}")
                    results.append({
                        'filename': filename,
                        'category': 'outros',
                        'category_name': categories.get('outros', 'Outros Documentos')
                    })
        
        return jsonify({
            'results': results,
            'total_files': len(results),
            'total_cost': total_cost
        })
    
    except Exception as e:
        print(f"Erro na classificação: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_organized():
    """Cria e retorna um ZIP com documentos organizados em pastas"""
    data = request.json
    session_id = data.get('session_id')
    classifications = data.get('classifications')
    
    if not session_id or not classifications:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    
    # Cria ZIP em memória
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Organiza arquivos por categoria
        for item in classifications:
            filename = item['filename']
            category_name = item['category_name']
            
            source_path = os.path.join(session_folder, filename)
            
            if os.path.exists(source_path):
                # Adiciona arquivo no ZIP dentro da pasta da categoria
                zip_path = os.path.join(category_name, filename)
                zip_file.write(source_path, zip_path)
        
        # Adiciona relatório
        report = generate_report(classifications, data.get('total_cost', 0))
        zip_file.writestr('RELATORIO.txt', report)
    
    zip_buffer.seek(0)
    
    # Limpa arquivos da sessão
    try:
        shutil.rmtree(session_folder)
    except:
        pass
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'documentos_organizados_{session_id}.zip'
    )

def generate_report(classifications, total_cost):
    """Gera relatório textual da classificação"""
    report = f"""RELATÓRIO DE CLASSIFICAÇÃO DE DOCUMENTOS
===============================================
Total de documentos processados: {len(classifications)}
Custo total: ${total_cost:.4f} USD (≈ R$ {total_cost * 5.5:.2f})
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
        data = request.get_json()
        categories = data.get('categories')
        
        if not categories:
            return jsonify({'error': 'Categorias não fornecidas'}), 400
        
        # Garante que a categoria 'outros' sempre existe
        if 'outros' not in categories:
            categories['outros'] = 'Outros Documentos'
        
        success = save_categories(categories)
        
        if success:
            return jsonify({'message': 'Categorias salvas com sucesso', 'categories': categories})
        else:
            return jsonify({'error': 'Erro ao salvar categorias'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/')
def index():
    """Serve a página frontend"""
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)