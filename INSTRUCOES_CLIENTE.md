# 🚀 INSTRUÇÕES PARA A CLIENTE - Limpar Cache

## ✅ O SISTEMA ESTÁ ATUALIZADO NO SERVIDOR!

**URL:** https://classificador-documentacao.onrender.com

**Status:** ✅ Versão 2.0.1-fixed deployada com sucesso!

---

## 🧹 SOLUÇÃO: Limpar Cache do Navegador

### Opção 1: Hard Refresh (MAIS RÁPIDO) ⚡

**Windows:**
1. Abra o site: https://classificador-documentacao.onrender.com
2. Pressione: **Ctrl + Shift + R**
3. OU: **Ctrl + F5**

**Mac:**
1. Abra o site: https://classificador-documentacao.onrender.com
2. Pressione: **Cmd + Shift + R**

### Opção 2: Limpar Cache Completo 🗑️

**Chrome/Edge:**
1. Pressione **Ctrl + Shift + Delete**
2. Selecione:
   - ✅ Imagens e arquivos em cache
   - ✅ Cookies e outros dados do site (opcional)
3. Período: **Última hora**
4. Clique em **Limpar dados**
5. Recarregue a página

**Firefox:**
1. Pressione **Ctrl + Shift + Delete**
2. Selecione:
   - ✅ Cache
   - ✅ Cookies (opcional)
3. Intervalo: **Última hora**
4. Clique em **Limpar agora**
5. Recarregue a página

**Safari (Mac):**
1. Menu **Develop** → **Empty Caches**
2. OU pressione: **Cmd + Option + E**
3. Recarregue a página

### Opção 3: Modo Anônimo (TEMPORÁRIO) 🕵️

1. Abra uma **janela anônima/privada**:
   - Chrome/Edge: **Ctrl + Shift + N**
   - Firefox: **Ctrl + Shift + P**
   - Safari: **Cmd + Shift + N**
2. Acesse: https://classificador-documentacao.onrender.com
3. Teste o sistema

> ⚠️ **Nota:** Modo anônimo é temporário. Para uso normal, faça o Hard Refresh.

---

## ✅ Como Verificar que Está na Versão Correta:

### Teste 1: Upload de Bulletin de Salaire
1. Faça upload de: `bulletin-de-salaire_07_2025.pdf`
2. Clique em "Classificar Documentos"
3. **Resultado esperado:**
   - ✅ Categoria: **"Holerite Francês"** ou **"Bulletin Salaire"**
   - ✅ Confiança OCR: **80% ou mais** (NÃO 0%)
   - ✅ Nome sugerido: **"Bulletin_de_salaire_Juillet_2025.pdf"**

### Teste 2: Verificar Headers (Técnico)
1. Pressione **F12** (DevTools)
2. Aba **Network**
3. Recarregue a página
4. Clique na primeira requisição (/)
5. Aba **Headers** → **Response Headers**
6. Procure por:
   ```
   X-App-Version: 2.0.1-fixed
   Cache-Control: no-cache, no-store, must-revalidate
   ```

---

## 🆘 Se AINDA não funcionar:

### 1. Desabilitar extensões do navegador:
- AdBlock, uBlock, Privacy Badger, etc podem interferir
- Teste em modo anônimo primeiro

### 2. Limpar DNS cache:
**Windows:**
```cmd
ipconfig /flushdns
```

**Mac/Linux:**
```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 3. Tentar outro navegador:
- Se usa Chrome, teste no Firefox
- Se usa Edge, teste no Chrome

### 4. Verificar conexão:
- Não usar VPN
- Não usar proxy corporativo
- Usar rede Wi-Fi/4G normal

---

## 📞 Suporte:

Se após seguir TODOS os passos acima ainda não funcionar:
1. Tire um print da tela mostrando o problema
2. Pressione F12 → Console → Copie erros (se houver)
3. Informe qual navegador e sistema operacional está usando

---

## ✨ Versão Atual do Sistema:

- **Versão:** 2.0.1-fixed
- **Commit:** 39b4e6a
- **OCR:** ✅ Funcionando
- **Função duplicada:** ✅ Removida
- **Deploy:** ✅ 23/10/2025
- **Status:** 🟢 ONLINE

**URL:** https://classificador-documentacao.onrender.com

