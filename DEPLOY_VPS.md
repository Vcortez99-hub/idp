# Deploy na VPS - Classificador de Documentos

## Requisitos da VPS
- Ubuntu 20.04+ ou Debian 11+
- 1GB RAM mínimo (2GB recomendado)
- Python 3.11+
- 10GB de espaço livre

## Instalação Rápida

### 1. Conectar na VPS
```bash
ssh usuario@seu-servidor.com
```

### 2. Instalar Tesseract OCR
```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng tesseract-ocr-fra
sudo apt install -y poppler-utils libgl1 libglib2.0-0
```

### 3. Instalar Python e dependências
```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### 4. Clonar/Upload do projeto
```bash
# Opção 1: Via Git
git clone https://github.com/SEU-USUARIO/IDP.git
cd IDP

# Opção 2: Via SCP (do seu PC)
# scp -r /caminho/local/IDP usuario@servidor:/home/usuario/
```

### 5. Criar ambiente virtual e instalar dependências
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Criar diretórios necessários
```bash
mkdir -p uploads temp_files processed data
chmod 755 uploads temp_files processed data
```

### 7. Testar localmente
```bash
python app.py
# Acesse: http://IP-DA-VPS:5000
```

### 8. Configurar como serviço (systemd)

Criar arquivo `/etc/systemd/system/idp-classifier.service`:

```ini
[Unit]
Description=IDP Classifier
After=network.target

[Service]
User=seu-usuario
WorkingDirectory=/home/seu-usuario/IDP
Environment="PATH=/home/seu-usuario/IDP/venv/bin"
ExecStart=/home/seu-usuario/IDP/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 2 --timeout 600 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable idp-classifier
sudo systemctl start idp-classifier
sudo systemctl status idp-classifier
```

### 9. Configurar Nginx (proxy reverso)

Instalar Nginx:
```bash
sudo apt install -y nginx
```

Criar configuração `/etc/nginx/sites-available/idp-classifier`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;  # ou IP da VPS

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

Ativar configuração:
```bash
sudo ln -s /etc/nginx/sites-available/idp-classifier /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Configurar SSL (HTTPS) - Opcional mas recomendado

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

## Acesso

- HTTP: `http://seu-dominio.com` ou `http://IP-DA-VPS`
- HTTPS: `https://seu-dominio.com` (após configurar SSL)

## Comandos Úteis

```bash
# Ver logs do serviço
sudo journalctl -u idp-classifier -f

# Reiniciar serviço
sudo systemctl restart idp-classifier

# Parar serviço
sudo systemctl stop idp-classifier

# Verificar status
sudo systemctl status idp-classifier
```

## Troubleshooting

### Erro de permissão
```bash
sudo chown -R seu-usuario:seu-usuario /home/seu-usuario/IDP
chmod 755 uploads temp_files processed data
```

### OCR não funciona
```bash
tesseract --version  # Verificar instalação
tesseract --list-langs  # Verificar idiomas
```

### Erro de memória
Aumentar workers/threads no gunicorn:
```bash
# Editar /etc/systemd/system/idp-classifier.service
ExecStart=... --workers 1 --threads 1 ...
sudo systemctl daemon-reload
sudo systemctl restart idp-classifier
```
