@echo off
setlocal
echo 🚀 Iniciando Classificador de Documentos Jurídicos...

REM Verifica Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
  echo ❌ Python não encontrado. Instale Python 3.8+
  exit /b 1
)

echo ✅ Python encontrado

REM Cria venv se não existir
IF NOT EXIST venv (
  echo 📦 Criando ambiente virtual...
  python -m venv venv
)

echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate

echo 📥 Instalando dependências...
pip install -q -r requirements.txt
IF ERRORLEVEL 1 (
  echo ❌ Erro ao instalar dependências
  exit /b 1
)

IF NOT EXIST uploads mkdir uploads
IF NOT EXIST processed mkdir processed

echo ✅ Sistema pronto!
echo 🌐 Backend: http://localhost:5000
echo Abra index.html no navegador

python app.py