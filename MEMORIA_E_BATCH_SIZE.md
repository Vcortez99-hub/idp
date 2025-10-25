# 🧠 Configuração de Memória e Batch Size - Fly.io

## 📊 Situação Atual

**Erro recebido:**
```
Out of memory: Killed process 659 (gunicorn)
total-vm: 812MB
anon-rss: 272MB (memória real usada)
Limite atual: 512MB
```

**Problema:** OCR com Tesseract + OpenCV + PIL consome muita memória ao processar múltiplos documentos.

---

## 🎯 Quantidade Ideal de Arquivos por Configuração de RAM

### **512MB RAM (FREE - Atual)** ⚠️
- **Máximo recomendado:** 2-3 arquivos pequenos (< 5MB cada)
- **Máximo absoluto:** 5 arquivos (risco de OOM)
- **Status:** **NÃO RECOMENDADO para produção**
- **Custo:** Grátis

**Limitações:**
- Gunicorn (2 workers) = ~100MB base
- Python + Flask + libs = ~80MB
- OCR por arquivo = ~40-60MB
- Sobram apenas ~200MB livres para processamento

### **1GB RAM (RECOMENDADO)** ✅
- **Máximo recomendado:** 10-15 arquivos por batch
- **Máximo absoluto:** 20 arquivos
- **Status:** **IDEAL para uso normal**
- **Custo:** ~$5/mês ($0.0000022/s)

**Capacidade:**
- Sistema base = ~180MB
- Disponível para OCR = ~820MB
- Pode processar ~15 arquivos simultaneamente com segurança

### **2GB RAM (PRODUÇÃO PESADA)** 🚀
- **Máximo recomendado:** 30-40 arquivos por batch
- **Máximo absoluto:** 50 arquivos
- **Status:** Para uso intensivo
- **Custo:** ~$10/mês

---

## 🔧 Opção 1: Aumentar RAM para 1GB (RECOMENDADO)

### **Passo 1: Aumentar memória**

```bash
fly scale memory 1024 -a idp-evizeq
```

### **Passo 2: Verificar mudança**

```bash
fly status -a idp-evizeq
```

Deve mostrar:
```
Memory: 1024 MB
```

### **Passo 3: Fazer redeploy**

```bash
fly deploy --remote-only -a idp-evizeq
```

**Custo:** ~$5/mês (muito acessível para produção)

---

## 🛠️ Opção 2: Manter 512MB e Limitar Batch Size

Se quiser continuar no free tier, precisamos limitar uploads:

### **Alterações necessárias:**

1. **Limitar número de arquivos no frontend** (index.html)
2. **Adicionar validação no backend** (app.py)
3. **Mostrar aviso claro ao usuário**

### **Implementação:**

```javascript
// Em index.html - adicionar validação
document.getElementById('file').addEventListener('change', function(e) {
    if (e.target.files.length > 3) {
        alert('⚠️ No plano Free, limite de 3 arquivos por vez.\nPara processar mais, considere upgrade para 1GB RAM.');
        e.target.value = '';
    }
});
```

```python
# Em app.py - adicionar validação
@app.route('/api/classify', methods=['POST'])
def classify_documents():
    files = request.files.getlist('files')

    # Limitar batch size no free tier
    if os.getenv('FLY_MEMORY_MB', '512') == '512' and len(files) > 3:
        return jsonify({
            'error': 'Limite de 3 arquivos no plano Free. Upgrade para 1GB RAM para processar mais.'
        }), 400
```

---

## 📈 Comparação de Custos

| RAM | Custo/mês | Arquivos/batch | Status |
|-----|-----------|----------------|---------|
| **512MB** | Grátis | 2-3 | ⚠️ Instável |
| **1GB** | ~$5 | 10-15 | ✅ **Recomendado** |
| **2GB** | ~$10 | 30-40 | 🚀 Produção |

---

## 🎯 RECOMENDAÇÃO FINAL

### **Para produção: Upgrade para 1GB**

```bash
fly scale memory 1024 -a idp-evizeq
fly deploy --remote-only -a idp-evizeq
```

**Motivos:**
1. **$5/mês é muito acessível** (R$25-30/mês)
2. **512MB é insuficiente** para OCR com múltiplos arquivos
3. **Melhor experiência do usuário** (10-15 arquivos por vez)
4. **Sem risco de crashes** em produção

### **Para desenvolvimento/testes: Limitar batch size**

Manter 512MB mas adicionar:
- Limite de 3 arquivos no frontend
- Validação no backend
- Aviso claro ao usuário

---

## 📝 Próximos Passos

**Escolha uma opção:**

### ✅ Opção A: Upgrade (Recomendado)
```bash
fly scale memory 1024 -a idp-evizeq
fly deploy --remote-only -a idp-evizeq
fly open  # Testar aplicação
```

### ⚠️ Opção B: Manter Free + Limitar
- Modificar index.html (validação frontend)
- Modificar app.py (validação backend)
- Commit e redeploy

---

## ❓ FAQ

**Q: Por que 512MB não é suficiente?**
A: Tesseract OCR + OpenCV + PIL consomem ~40-60MB por arquivo. Com 2 workers do gunicorn processando simultaneamente, facilmente ultrapassa 512MB.

**Q: 1GB resolve definitivamente?**
A: Sim, para uso normal (10-15 arquivos). Para processamento massivo (30+ arquivos), considere 2GB.

**Q: Posso testar antes de pagar?**
A: Sim! Fly.io oferece trial. Você pode testar 1GB e voltar para 512MB depois.

---

**Recomendação:** Use **1GB RAM** ($5/mês) para produção estável. É o melhor custo-benefício.
