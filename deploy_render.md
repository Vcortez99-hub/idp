# 🚀 Deploy no Render.com (Gratuito)

## Por que Render?
- ✅ Gratuito (tier free)
- ✅ Deploy automático
- ✅ HTTPS incluso
- ✅ Fácil de usar
- ✅ Zero configuração de servidor

## 📋 Passo a Passo

### 1. Preparar arquivos

Adicione ao seu projeto o arquivo `gunicorn` no `requirements.txt`:

```text
flask==3.0.0
flask-cors==4.0.0
openai==1.12.0
werkzeug==3.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
```

### 2. Criar conta no Render

1. Acesse: https://render.com
2. Clique em "Get Started for Free"
3. Faça login com GitHub (recomendado)

### 3. Preparar repositório GitHub

```bash
# No seu computador, dentro da pasta do projeto:
git init
git add .
git commit -m "Initial commit"

# Crie um repositório no GitHub e depois:
git remote add origin https://github.com/seu-usuario/classificador-docs.git
git branch -M main
git push -u origin main
```

### 4. Deploy no Render

1. No dashboard do Render, clique em **"New +"**
2. Selecione **"Web Service"**
3. Conecte sua conta GitHub
4. Selecione o repositório `classificador-docs`
5. Configure:

**Configurações:**
```
Name: classificador-documentos
Region: Oregon (US West)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Instance Type: Free
```

6. Clique em **"Create Web Service"**

### 5. Aguarde o deploy

- O Render vai instalar as dependências (2-3 minutos)
- Quando terminar, sua URL estará disponível: `https://classificador-documentos.onrender.com`

### 6. Atualizar o Frontend

No `index.html`, altere a linha:

```javascript
// De:
const API_URL = 'http://localhost:5000/api';

// Para:
const API_URL = 'https://classificador-documentos.onrender.com/api';
// (Use a URL que o Render gerou para você)
```

### 7. Hospedar o Frontend

**Opção A: No mesmo Render (Estático)**

1. Crie novo "Static Site" no Render
2. Configure:
   - Build Command: (deixe vazio)
   - Publish Directory: `.`
3. Upload do `index.html`

**Opção B: Netlify (Recomendado para frontend)**

1. Acesse https://netlify.com
2. Arraste o `index.html` para upload
3. Pronto! URL gerada automaticamente

**Opção C: GitHub Pages (Gratuito)**

```bash
# No repositório GitHub:
# Settings → Pages → Source: main branch
# Seu site estará em: https://seu-usuario.github.io/classificador-docs
```

## 🔧 Configurações Avançadas

### Adicionar domínio personalizado

1. No Render dashboard, vá em Settings
2. Custom Domain → Add Custom Domain
3. Configure DNS conforme instruções

### Variáveis de ambiente (opcional)

Se quiser configurar API key padrão:

1. No Render, vá em Environment
2. Adicione: `OPENAI_API_KEY` = `sk-sua-chave`
3. Redeploy

### Aumentar timeout (para muitos documentos)

No `app.py`, adicione antes do `app.run()`:

```python
if __name__ == '__main__':
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    app.run(debug=False, host='0.0.0.0', port=5000)
```

## 🐛 Troubleshooting

### Erro de Build

Se falhar o build:
1. Verifique `requirements.txt` (sem espaços extras)
2. Certifique-se que está usando Python 3.8+

### Erro 502 Bad Gateway

- App está iniciando (aguarde 1-2 minutos)
- Verifique logs no dashboard do Render

### Erro de CORS

Certifique-se que o backend tem:
```python
from flask_cors import CORS
CORS(app)
```

### App "dorme" no plano free

O tier gratuito do Render "dorme" após 15 minutos de inatividade.
- Primeira requisição pode demorar 30s-1min
- Considere upgrade para $7/mês se precisar disponibilidade 24/7

## 💰 Custos

### Render Free Tier:
- ✅ GRATUITO para sempre
- 750 horas/mês (suficiente para 1 app)
- App "dorme" após inatividade
- Deploy automático

### Render Paid ($7/mês):
- ✅ Sempre ativo (sem "sono")
- ✅ Mais recursos computacionais
- ✅ Suporte prioritário

## 🎯 URLs Finais

Após deploy completo, você terá:

```
Backend (API): https://classificador-documentos.onrender.com
Frontend (Web): https://seu-site.netlify.app
```

Compartilhe a URL do frontend com sua cliente! 🎉

## 🔄 Atualizações Futuras

Qualquer push para o GitHub atualiza automaticamente:

```bash
git add .
git commit -m "Nova feature"
git push origin main
```

O Render fará redeploy automático em ~2 minutos.

---

**Pronto para produção!** ⚖️✨