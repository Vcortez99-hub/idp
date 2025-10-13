# Classificador de Documentos Jurídicos

Aplicação completa com backend Flask e frontend web para classificar documentos jurídicos brasileiros usando OpenAI Vision (GPT-4o-mini).

## Funcionalidades
- Upload múltiplo (arrasta e solta)
- 11 categorias de documentos
- Suporte a PDF, PNG, JPEG
- Download ZIP organizado
- Relatório em TXT
- Contador de custos em tempo real
- Interface responsiva

## Execução Local
1. Instale Python 3.8+
2. No Windows: execute `start.bat`. No Linux/Mac: `bash start.sh`
3. Abra `index.html` no navegador.
4. Informe sua chave OpenAI e envie arquivos.

## Dependências
Veja `requirements.txt`.

## Endpoints
- `POST /api/upload` — recebe arquivos e retorna `session_id`
- `POST /api/classify` — classifica documentos da sessão
- `POST /api/download` — retorna ZIP com organização e relatório
- `GET /api/health` — status do servidor

## Deploy
Consulte `DEPLOY_RENDER.md` para backend no Render e frontend no Netlify.

## Testes
Consulte `TESTE.md`.