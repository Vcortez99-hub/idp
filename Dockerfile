# Dockerfile otimizado para Render.com
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Atualizar repositórios primeiro
RUN apt-get update

# Instalar Tesseract OCR e pacotes de idioma
RUN apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    tesseract-ocr-fra

# Instalar dependências do OpenCV e sistema
RUN apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0

# Instalar poppler-utils para PDF
RUN apt-get install -y --no-install-recommends \
    poppler-utils

# Limpar cache do apt
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (aproveita cache do Docker)
COPY requirements.txt .

# Atualizar pip e instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /tmp/uploads /tmp/temp_files /app/data

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
