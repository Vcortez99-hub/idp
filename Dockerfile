# Dockerfile otimizado para VPS
FROM python:3.11-slim

# Variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Instalar dependências do sistema em uma única camada
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (aproveita cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Criar diretórios
RUN mkdir -p /tmp/uploads /tmp/temp_files /tmp/processed /app/data

# Expor porta
EXPOSE 8080

# Inicialização otimizada para 1GB RAM
# 1 worker = ~300-400MB, total com sistema = ~600-800MB
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} \
    --workers 1 \
    --threads 2 \
    --worker-class sync \
    --timeout 600 \
    --max-requests 100 \
    --max-requests-jitter 10 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
