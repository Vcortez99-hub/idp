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
    'ctps': 'CTPS',
    'contrato': 'Contratos',
    'procuracao': 'Procurações',
    'peticao': 'Petições',
    'sentenca': 'Sentenças',
    'passaporte': 'Passaportes',
    'outros': 'Outros Documentos'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def classify_document(file_path, api_key):
    """Classifica um documento usando GPT-4o-mini Vision com melhor assertividade"""
    client = OpenAI(api_key=api_key)

    # Determina o tipo de arquivo
    file_extension = file_path.rsplit('.', 1)[1].lower()

    # Codifica a imagem em base64
    base64_image = encode_image(file_path)

    # Define o MIME type
    mime_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    mime_type = mime_types.get(file_extension, 'image/jpeg')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Você é um assistente especializado em classificar documentos brasileiros e internacionais.
Analise este documento e classifique-o em UMA das seguintes categorias com sua confiança:

CATEGORIAS ESPECÍFICAS:
- holerite: Contracheques/recibos de pagamento (incluindo "bulletin de salaire" francês, payslip inglês)
- certidao_nascimento: Certidões de nascimento (brasileiras ou internacionais)
- comprovante_residencia: Contas de luz, água, telefone, contratos de aluguel, comprovantes de endereço
- rg: Registro Geral, carteira de identidade (RG brasileiro, CNI, carte d'identité)
- cpf: Cadastro de Pessoa Física brasileiro
- ctps: Carteira de Trabalho brasileira
- contrato: Contratos diversos (trabalho, prestação de serviços, pedagógico, stage/estágio)
- procuracao: Procurações
- peticao: Petições iniciais, contestações, recursos
- sentenca: Sentenças, decisões judiciais
- passaporte: Passaportes brasileiros ou internacionais
- outros: SOMENTE documentos que NÃO se encaixam em nenhuma categoria acima (faturas comerciais, formulários genéricos, listas, etc)

INSTRUÇÕES CRÍTICAS:
1. Se for holerite/payslip em qualquer idioma (português, francês, inglês), classifique como "holerite"
2. Se for passaporte, classifique como "passaporte"
3. NUNCA retorne confiança 0% se classificou em alguma categoria específica
4. Se classificou como "outros", a confiança deve ser "N/A"
5. Para categorias específicas, a confiança mínima deve ser 30%

Responda APENAS no formato JSON:
{{"category": "categoria", "confidence": "XX%" ou "N/A"}}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )

        result_text = response.choices[0].message.content.strip()

        # Parse do JSON retornado
        import json
        try:
            result_json = json.loads(result_text)
            category = result_json.get('category', 'outros').lower()
            confidence = result_json.get('confidence', 'N/A')
        except:
            # Fallback se não retornar JSON válido
            category = result_text.lower()
            confidence = 'N/A' if category == 'outros' else '50%'

        # Validações de assertividade
        if category not in DOCUMENT_TYPES:
            category = 'outros'
            confidence = 'N/A'

        # Se classificou como categoria específica mas retornou 0%, corrige para mínimo
        if category != 'outros' and confidence == '0%':
            confidence = '30%'

        # Se classificou como "outros", sempre retorna N/A
        if category == 'outros':
            confidence = 'N/A'

        # Calcula custo aproximado
        total_tokens = response.usage.total_tokens
        cost = total_tokens * 0.00000015  # Preço aproximado do GPT-4o-mini

        return {
            'category': category,
            'category_name': DOCUMENT_TYPES.get(category, DOCUMENT_TYPES['outros']),
            'confidence': confidence,
            'tokens': total_tokens,
            'cost': cost
        }

    except Exception as e:
        print(f"Erro ao classificar documento: {str(e)}")
        return {
            'category': 'outros',
            'category_name': DOCUMENT_TYPES['outros'],
            'confidence': 'N/A',
            'tokens': 0,
            'cost': 0,
            'error': str(e)
        }

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
    """Classifica todos os documentos de uma sessão"""
    data = request.json
    session_id = data.get('session_id')
    api_key = data.get('api_key')
    
    if not session_id or not api_key:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    
    if not os.path.exists(session_folder):
        return jsonify({'error': 'Sessão não encontrada'}), 404
    
    # Processa todos os arquivos
    results = []
    total_cost = 0
    
    for filename in os.listdir(session_folder):
        filepath = os.path.join(session_folder, filename)
        
        if os.path.isfile(filepath):
            classification = classify_document(filepath, api_key)
            
            result = {
                'filename': filename,
                'category': classification['category'],
                'category_name': classification['category_name'],
                'confidence': classification.get('confidence', 'N/A'),
                'cost': classification['cost']
            }

            if 'error' in classification:
                result['error'] = classification['error']

            results.append(result)
            total_cost += classification['cost']
    
    return jsonify({
        'results': results,
        'total_cost': total_cost,
        'total_files': len(results)
    })

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)