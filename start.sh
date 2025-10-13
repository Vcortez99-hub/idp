#!/bin/bash

echo "🚀 Iniciando Classificador de Documentos Jurídicos..."
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
    echo "✅ Ambiente virtual criado"
else
    echo "✅ Ambiente virtual já existe"
fi

# Ativa ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📥 Instalando dependências..."
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Cria pastas necessárias
mkdir -p uploads processed

echo ""
echo "✅ Sistema pronto!"
echo ""
echo "🌐 Iniciando servidor..."
echo "   Backend: http://localhost:5000"
echo "   Frontend: Abra index.html no navegador"
echo ""
echo "⚠️  Para parar o servidor: Ctrl+C"
echo ""

# Inicia o servidor
python3 app.py