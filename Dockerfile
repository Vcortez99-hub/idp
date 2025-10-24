# Dockerfile otimizado para Fly.io / Render.com
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Atualizar repositórios primeiro
RUN apt-get update

# Instalar Tesseract OCR e pacotes de idioma
RUN apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    tesseract-ocr-fra

# Instalar dependências do OpenCV (CORRIGIDO: libgl1 ao invés de libgl1-mesa-glx)
RUN apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0

# Instalar poppler-utils para PDF e curl para healthcheck
RUN apt-get install -y --no-install-recommends \
    poppler-utils \
    curl

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
RUN mkdir -p /tmp/uploads /tmp/temp_files /tmp/processed /app/data && \
    chmod 755 /tmp/uploads /tmp/temp_files /tmp/processed /app/data

# Expor porta (usa variável de ambiente PORT, padrão 8080)
EXPOSE 8080

# Healthcheck para Fly.io
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

# Comando de inicialização (timeout 600s para OCR pesado)
# Usa PORT do ambiente (Fly.io usa 8080, Render usa 5000)
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 2 --timeout 600 --access-logfile - --error-logfile - app:app
