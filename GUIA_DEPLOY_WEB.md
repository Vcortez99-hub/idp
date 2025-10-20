# 🚀 Guia Completo: Deploy Web com OCR Funcional

## 📋 Opções de Hospedagem Recomendadas

### 1️⃣ **Render.com (RECOMENDADO - Gratuito)**
- ✅ Suporte nativo a Tesseract OCR
- ✅ Deploy automático via GitHub
- ✅ SSL/HTTPS incluído
- ✅ Plano gratuito disponível
- ⚠️ Limites: 512MB RAM, 0.1 CPU (suficiente para OCR)

### 2️⃣ **Railway.app**
- ✅ Fácil configuração
- ✅ Integração GitHub
- ✅ $5/mês de crédito grátis
- ✅ Boa para produção

### 3️⃣ **AWS EC2 / DigitalOcean**
- ✅ Controle total
- ✅ Escalabilidade
- ⚠️ Requer configuração manual
- 💰 A partir de $5/mês

---

## 🎯 Deploy no Render.com (Passo a Passo)

### **Passo 1: Criar arquivo Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema (Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache de layer)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p uploads temp_files

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
```

### **Passo 2: Criar arquivo render.yaml**

```yaml
# render.yaml
services:
  - type: web
    name: classificador-documentos
    env: docker
    region: oregon
    plan: free
    healthCheckPath: /
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: TESSDATA_PREFIX
        value: /usr/share/tesseract-ocr/5/tessdata
```

### **Passo 3: Ajustar app.py para produção**

Adicione no início do arquivo `app.py`:

```python
import os

# Configuração para produção
if os.environ.get('RENDER'):
    # Detecta se está no Render
    UPLOAD_FOLDER = '/tmp/uploads'
    TEMP_FOLDER = '/tmp/temp_files'
else:
    # Desenvolvimento local
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp_files')

# Criar diretórios se não existirem
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
```

### **Passo 4: Criar .dockerignore**

```
# .dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.env
.git
.gitignore
*.md
learning_data.db
uploads/
temp_files/
```

### **Passo 5: Deploy no Render**

1. **Criar conta** no [Render.com](https://render.com)

2. **Conectar GitHub**:
   - Faça push do código para GitHub
   - Inclua: `Dockerfile`, `render.yaml`, `requirements.txt`, `app.py`

3. **Criar Web Service**:
   - Dashboard → New → Web Service
   - Conecte seu repositório GitHub
   - Render detectará automaticamente o Dockerfile

4. **Configurar variáveis de ambiente** (opcional):
   ```
   OPENAI_API_KEY=sk-xxx (se usar IA)
   FLASK_ENV=production
   ```

5. **Deploy**:
   - Clique em "Create Web Service"
   - Aguarde 5-10 minutos (instalação do Tesseract)
   - URL pública será gerada: `https://seu-app.onrender.com`

---

## 🐳 Deploy com Docker (Servidor Próprio)

### **Opção 1: Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./learning_data.db:/app/learning_data.db
      - uploads:/tmp/uploads
    environment:
      - FLASK_ENV=production
      - TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
    restart: unless-stopped

volumes:
  uploads:
```

**Comandos**:
```bash
# Buildar imagem
docker-compose build

# Iniciar aplicação
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### **Opção 2: Docker Run**

```bash
# Build
docker build -t classificador-docs .

# Run
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/learning_data.db:/app/learning_data.db \
  --name classificador \
  classificador-docs
```

---

## ☁️ Deploy na AWS EC2

### **Passo 1: Lançar instância EC2**

```bash
# Tipo: t2.micro (1 GB RAM)
# OS: Ubuntu 22.04 LTS
# Portas abertas: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### **Passo 2: Conectar via SSH e configurar**

```bash
# Conectar
ssh -i sua-chave.pem ubuntu@seu-ip

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clonar repositório
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# Iniciar aplicação
docker-compose up -d
```

### **Passo 3: Configurar Nginx (proxy reverso)**

```bash
# Instalar Nginx
sudo apt install nginx -y

# Criar configuração
sudo nano /etc/nginx/sites-available/classificador
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout para OCR longo
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/classificador /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL gratuito com Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu-dominio.com
```

---

## 🔧 Configurações de Produção

### **1. Aumentar limite de upload**

No `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### **2. Configurar CORS (se frontend separado)**

```python
from flask_cors import CORS

CORS(app, origins=[
    'https://seu-frontend.com',
    'https://seu-dominio.com'
])
```

### **3. Variáveis de ambiente**

Crie arquivo `.env`:
```bash
FLASK_ENV=production
OPENAI_API_KEY=sk-xxx
DATABASE_PATH=/app/learning_data.db
UPLOAD_FOLDER=/tmp/uploads
```

### **4. Persistência do banco de dados**

Para evitar perder dados em redeploys:

**Render.com**: Use volume persistente
```yaml
# render.yaml
services:
  - type: web
    ...
    disk:
      name: learning-data
      mountPath: /app/data
      sizeGB: 1
```

Ajuste `learning_system.py`:
```python
DB_PATH = '/app/data/learning_data.db'
```

---

## 🧪 Testar OCR em Produção

### **Verificar se Tesseract está instalado**

```bash
# Dentro do container
docker exec -it <container-id> tesseract --version
docker exec -it <container-id> tesseract --list-langs
```

**Output esperado**:
```
tesseract 5.x.x
List of available languages:
eng
fra
por
```

### **Teste via API**

```bash
curl -X POST https://seu-app.onrender.com/api/upload \
  -F "files[]=@documento_teste.pdf"
```

---

## 📊 Monitoramento e Logs

### **Render.com**
- Dashboard → Logs (tempo real)
- Métricas de CPU/RAM

### **Docker**
```bash
# Logs em tempo real
docker logs -f classificador

# Últimas 100 linhas
docker logs --tail 100 classificador
```

### **AWS EC2**
```bash
# Logs do Gunicorn
docker-compose logs -f web

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## ⚡ Otimizações de Performance

### **1. Workers do Gunicorn**

```bash
# Fórmula: (2 x CPU cores) + 1
# t2.micro = 1 core → 3 workers

gunicorn --workers 3 --threads 2 --timeout 120 app:app
```

### **2. Cache de OCR (futuro)**

Para PDFs grandes que são processados múltiplas vezes:
```python
import hashlib

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# Armazenar resultado OCR em cache usando hash do arquivo
```

### **3. Compressão de resposta**

```python
from flask_compress import Compress
Compress(app)
```

---

## 🛡️ Segurança

### **1. Rate Limiting**

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_files():
    ...
```

### **2. Validação de arquivos**

```python
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### **3. Sanitização de nomes de arquivo**

```python
from werkzeug.utils import secure_filename

filename = secure_filename(file.filename)
```

---

## ✅ Checklist Final de Deploy

- [ ] Dockerfile criado com Tesseract OCR
- [ ] render.yaml configurado (se Render)
- [ ] requirements.txt atualizado
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados persistente configurado
- [ ] CORS configurado (se necessário)
- [ ] SSL/HTTPS ativo
- [ ] Logs de produção funcionando
- [ ] Teste de upload de PDF realizado
- [ ] Teste de OCR em português/francês/inglês
- [ ] Feedback (like/dislike) funcional

---

## 🎯 Recomendação Final

**Para começar rapidamente**: Use **Render.com**
- Deploy em 10 minutos
- OCR funciona nativamente
- SSL incluído
- Plano gratuito suficiente para testes

**Para produção de longo prazo**: Use **AWS EC2 + Docker + Nginx**
- Controle total
- Escalabilidade
- Custo previsível (~$5-10/mês)

---

## 📞 Problemas Comuns

### **"Tesseract not found"**
```dockerfile
# Adicionar no Dockerfile
RUN apt-get install -y tesseract-ocr tesseract-ocr-por
```

### **"OpenCV error"**
```dockerfile
# Adicionar no Dockerfile
RUN apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### **"Timeout ao processar PDF"**
```python
# Aumentar timeout no Gunicorn
CMD ["gunicorn", "--timeout", "300", "app:app"]
```

### **"Banco de dados zerado após redeploy"**
```yaml
# Configurar volume persistente no render.yaml
disk:
  name: learning-data
  mountPath: /app/data
```

---

**🚀 Pronto! Sua aplicação estará acessível na web com OCR totalmente funcional!**
