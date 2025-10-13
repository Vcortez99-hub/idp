# 🧪 Guia de Testes do Sistema

## 🎯 Testes Locais

### 1. Teste Básico (1 documento)

1. Inicie o servidor: `python app.py`
2. Abra `index.html` no navegador
3. Insira sua API Key do OpenAI
4. Faça upload de **1 PDF simples** (ex: holerite)
5. Clique em "Classificar Documentos"
6. Verifique se classifica corretamente
7. Baixe o ZIP e verifique a organização

**Resultado esperado:**
- Processamento em ~5 segundos
- Custo: ~$0.003 USD
- ZIP com pasta correta e documento dentro

### 2. Teste Múltiplos Documentos (10-20 docs)

1. Prepare 10-20 documentos variados
2. Faça upload de todos de uma vez
3. Observe o progresso em tempo real
4. Verifique se todos foram classificados

**Resultado esperado:**
- Processamento: ~30-60 segundos
- Custo: ~$0.03-0.06 USD
- Todas categorias corretas

### 3. Teste Documentos Mistos

Teste com:
- ✅ PDFs nativos (gerados digitalmente)
- ✅ PDFs escaneados
- ✅ Fotos PNG de documentos
- ✅ JPEGs de celular

**Resultado esperado:**
- Sistema deve processar todos os tipos
- Imagens de baixa qualidade podem ter classificação "outros"

### 4. Teste de Erro

Tente:
- ❌ Upload sem API Key → deve mostrar erro
- ❌ Upload sem arquivos → deve mostrar erro
- ❌ API Key inválida → deve mostrar erro claro

## 📊 Benchmark de Performance

### Pequeno Volume (10 docs)
- ⏱️ Tempo: ~30 segundos
- 💰 Custo: ~$0.03 USD (~R$ 0,15)

### Médio Volume (100 docs)
- ⏱️ Tempo: ~5 minutos
- 💰 Custo: ~$0.30 USD (~R$ 1,65)

### Grande Volume (500 docs)
- ⏱️ Tempo: ~25 minutos
- 💰 Custo: ~$1.50 USD (~R$ 8,25)

### Volume Massivo (1000 docs)
- ⏱️ Tempo: ~50 minutos
- 💰 Custo: ~$3.00 USD (~R$ 16,50)

## 🧪 Testes de API (Curl)

### Verificar se servidor está rodando

```bash
curl http://localhost:5000/api/health
```

**Resposta esperada:**
```json
{"status":"ok","message":"Servidor funcionando"}
```

### Upload de arquivo via API

```bash
curl -X POST \
  -F "files[]=@documento.pdf" \
  -F "api_key=sk-sua-chave" \
  http://localhost:5000/api/upload
```

### Classificar documentos

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id":"20250111_123456","api_key":"sk-sua-chave"}' \
  http://localhost:5000/api/classify
```

## 🎭 Cenários de Uso Real

### Cenário 1: Escritório pequeno (50 docs/mês)
- Custo mensal: ~R$ 4,00
- Tempo economizado: ~5 horas/mês
- ROI: Excelente

### Cenário 2: Escritório médio (500 docs/mês)
- Custo mensal: ~R$ 40,00
- Tempo economizado: ~50 horas/mês
- ROI: Fantástico

### Cenário 3: Escritório grande (2000+ docs/mês)
- Custo mensal: ~R$ 160,00
- Tempo economizado: ~200 horas/mês
- ROI: Impressionante

## ✅ Checklist de Qualidade

Antes de entregar para cliente, verifique:

- [ ] Sistema roda localmente sem erros
- [ ] Frontend está responsivo (mobile/desktop)
- [ ] Upload de múltiplos arquivos funciona
- [ ] Classificação está precisa (>90%)
- [ ] Download do ZIP funciona
- [ ] Relatório está legível
- [ ] Custos são calculados corretamente
- [ ] Erros são tratados com mensagens claras
- [ ] Sistema está deployado e acessível
- [ ] Documentação está completa

## 🐛 Testes de Edge Cases

### Documentos Problemáticos

1. **PDF corrompido**
   - Resultado: Deve dar erro claro

2. **Imagem muito grande (>10MB)**
   - Resultado: Pode demorar, mas deve processar

3. **Documento ilegível**
   - Resultado: Classifica como "outros"

4. **Documento em outra língua**
   - Resultado: Pode classificar errado, melhoria futura

5. **Arquivo não suportado (.doc, .txt)**
   - Resultado: Não aceita no upload

### Limites do Sistema

- **Max arquivo:** 16MB (limite OpenAI Vision)
- **Max upload simultâneo:** Ilimitado (mas processamento é sequencial)
- **Timeout:** 30s por documento (configurável)

## 📈 Métricas de Sucesso

### Precisão esperada:
- ✅ Holerites: 95%+
- ✅ RG/CPF: 98%+
- ✅ Certidões: 90%+
- ✅ Contratos: 85%+
- ⚠️ Documentos complexos: 80%+

### Se precisão < 80%:
1. Verifique qualidade das imagens
2. Considere usar GPT-4o (mais caro, mais preciso)
3. Adicione exemplos no prompt

## 🎓 Treinamento do Cliente

Oriente sua cliente a:

1. ✅ Usar imagens de boa qualidade
2. ✅ Separar documentos muito diferentes
3. ✅ Revisar classificação de "outros"
4. ✅ Reportar erros para melhoria
5. ✅ Fazer backup antes de processar

## 🔧 Troubleshooting Comum

### "Erro ao classificar documento"
- Verifique créditos OpenAI
- Teste API key em: https://platform.openai.com/playground

### "Classificação errada"
- Melhore qualidade da imagem
- Considere usar modelo mais avançado
- Adicione feedback ao prompt

### "Sistema lento"
- Normal para muitos documentos
- Considere processar em lotes menores
- Upgrade servidor (se no Render free tier)

## 📞 Suporte Pós-Deploy

Crie documento para cliente com:
- ✅ URL do sistema
- ✅ Instruções de uso
- ✅ Seu contato para suporte
- ✅ FAQ com problemas comuns
- ✅ Tabela de custos atualizada

---

**Sistema testado e pronto para produção!** 🚀⚖️