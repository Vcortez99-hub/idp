# GUIA: Forçar Redeploy no Render e Limpar Cache

## ✅ Verificar versão atual do deploy:

### 1. Testar endpoint de health:
```bash
curl https://seu-app.onrender.com/api/health
```

**Resposta esperada (versão correta):**
```json
{
  "status": "ok",
  "message": "Servidor funcionando",
  "version": "2.0.1-fixed",
  "commit": "39b4e6a",
  "ocr_enabled": true,
  "duplicate_function_removed": true
}
```

**Se retornar apenas `{"status": "ok"}` = versão ANTIGA**

---

## 🔄 Forçar Redeploy no Render:

### Método 1: Via Dashboard (Recomendado)
1. Acesse: https://dashboard.render.com
2. Selecione seu serviço "classificador-documentos-idp"
3. Clique em **"Manual Deploy"** → **"Deploy latest commit"**
4. Aguarde o build completar (~5-10 minutos)

### Método 2: Via Commit Vazio (Forçado)
```bash
git commit --allow-empty -m "Force redeploy to Render"
git push origin master
```

### Método 3: Clear Build Cache + Redeploy
1. Dashboard Render → Settings
2. Clique em **"Clear build cache"**
3. Depois clique em **"Manual Deploy"**

---

## 🧹 Limpar Cache do Navegador:

### Para usuários acessando de outro computador:

**Chrome/Edge:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Imagens e arquivos em cache"
3. Clique em "Limpar dados"
4. OU: Abra DevTools (F12) → Network → Marque "Disable cache"

**Firefox:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Cache"
3. Clique em "Limpar agora"

**Safari:**
1. Develop → Empty Caches
2. OU: `Cmd + Option + E`

**Hard Refresh (todos os navegadores):**
- Windows: `Ctrl + F5` ou `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

---

## 🔍 Verificar que está na versão correta:

### 1. Abra DevTools (F12) → Network
### 2. Recarregue a página
### 3. Veja os headers da resposta de `/`:
```
X-App-Version: 2.0.1-fixed
Cache-Control: no-cache, no-store, must-revalidate
```

### 4. Teste classificação de bulletin-de-salaire:
- Upload: `bulletin-de-salaire_07_2025.pdf`
- Categoria esperada: **"Holerite Francês (Bulletin Salaire)"**
- Confiança esperada: **80%+** (NÃO 0%)
- Nome sugerido: **"Bulletin_de_salaire_Juillet_2025.pdf"**

---

## 📊 Logs do Render:

Para verificar se o deploy foi bem-sucedido:
1. Dashboard → Logs
2. Procure por: `"Debugger is active!"` e `"Running on"`
3. Teste: `curl https://seu-app.onrender.com/api/health`

---

## ⚠️ Se ainda não funcionar:

1. **Verificar arquivo correto no GitHub:**
   - https://github.com/Vcortez99-hub/idp/blob/master/app.py
   - Procure pela linha 480: `def classify_offline_fallback(file_path, categories=None, text=None):`
   - Verifique que NÃO existe linha 1390 com função duplicada

2. **Forçar rebuild completo:**
   ```bash
   # Fazer um change mínimo no Dockerfile
   echo "# Force rebuild $(date)" >> Dockerfile
   git add Dockerfile
   git commit -m "Force rebuild"
   git push origin master
   ```

3. **Verificar variáveis de ambiente no Render:**
   - Settings → Environment
   - Adicione: `FORCE_RELOAD=true`
