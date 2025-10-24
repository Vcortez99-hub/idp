# 🚀 Deploy no Fly.io - Guia Completo

## Por que Fly.io?

✅ **3 VMs gratuitas** (256MB RAM cada)
✅ **CPU muito mais rápida** que Render free tier
✅ **Escala automaticamente** sob carga
✅ **Region São Paulo (GRU)** - baixíssima latência
✅ **Volume persistente** para banco de dados
✅ **Sem cold start** - sempre online

---

## 📋 Pré-requisitos

1. **Conta no Fly.io** (gratuita)
   - Acesse: https://fly.io/signup
   - Você receberá 3 VMs free tier (256MB cada)

2. **Fly CLI instalado**
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

   # macOS/Linux
   curl -L https://fly.io/install.sh | sh
   ```

3. **Login no Fly.io**
   ```bash
   fly auth login
   ```

---

## 🎯 Deploy Passo a Passo

### 1. Criar volume persistente (banco de dados)

```bash
fly volumes create idp_data --region gru --size 1
```

### 2. Fazer deploy da aplicação

```bash
# Deploy inicial (cria app e faz primeiro build)
fly deploy

# OU, se quiser escolher nome customizado:
fly launch --name seu-app-idp
```

### 3. Verificar status

```bash
# Ver status da aplicação
fly status

# Ver logs em tempo real
fly logs

# Ver métricas
fly dashboard
```

### 4. Acessar a aplicação

Após deploy, sua aplicação estará disponível em:
```
https://idp-classifier.fly.dev
```

---

## 🔧 Comandos Úteis

### Deploy e Atualização

```bash
# Deploy com rebuild completo
fly deploy

# Deploy forçando rebuild (sem cache)
fly deploy --no-cache

# Deploy com logs em tempo real
fly deploy --detach=false
```

### Monitoramento

```bash
# Ver logs em tempo real
fly logs

# Ver logs das últimas 200 linhas
fly logs -a idp-classifier -n 200

# Ver status detalhado
fly status --all
```

### Escalamento

```bash
# Escalar para 512MB RAM (recomendado para OCR pesado)
fly scale memory 512

# Escalar para 2 VMs (alta disponibilidade)
fly scale count 2

# Voltar para 1 VM (free tier)
fly scale count 1
```

### SSH e Debug

```bash
# Acessar shell dentro do container
fly ssh console

# Ver configuração atual
fly config show

# Reiniciar aplicação
fly apps restart idp-classifier
```

### Volumes (Banco de Dados)

```bash
# Listar volumes
fly volumes list

# Ver detalhes do volume
fly volumes show idp_data

# Fazer snapshot do volume
fly volumes snapshots create idp_data
```

---

## 📊 Configuração Atual

**Arquivo: [fly.toml](fly.toml)**

```toml
app = "idp-classifier"
primary_region = "gru"  # São Paulo

[vm]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512  # Pode ser 256 no free tier

[[mounts]]
  source = "idp_data"
  destination = "/app/data"
```

---

## 🆚 Fly.io vs Render

| Recurso | Fly.io Free | Render Free |
|---------|-------------|-------------|
| **RAM** | 256MB x 3 VMs | 512MB |
| **CPU** | ⚡ Rápida (shared) | 🐌 Lenta (0.1 CPU) |
| **Timeout** | Sem limite | 15min max |
| **Cold Start** | Não | Sim (~1min) |
| **Region Brasil** | ✅ GRU (São Paulo) | ❌ EUA apenas |
| **Volume Persistente** | 3GB free | ❌ Ephemeral |
| **Build Time** | ~5 min | ~10 min |

---

## 🔥 Performance Esperada

**Render Free Tier:**
- 13 arquivos com OCR: **5-8 minutos**
- CPU: 0.1 vCPU compartilhada
- Travava no pré-processamento de imagens

**Fly.io Free Tier:**
- 13 arquivos com OCR: **1-2 minutos** ⚡
- CPU: 1 vCPU compartilhada (muito mais rápida)
- Processamento fluido e estável

---

## 🐛 Troubleshooting

### Deploy falhou?

```bash
# Ver logs do build
fly logs --app idp-classifier

# Tentar deploy novamente sem cache
fly deploy --no-cache
```

### Aplicação não responde?

```bash
# Verificar health checks
fly checks list

# Ver status
fly status

# Reiniciar
fly apps restart
```

### Espaço em disco cheio?

```bash
# Ver uso do volume
fly ssh console -C "df -h /app/data"

# Limpar uploads antigos
fly ssh console -C "rm -rf /tmp/uploads/*"
```

### OCR muito lento?

```bash
# Aumentar RAM para 512MB
fly scale memory 512

# Ou escalar para 2 VMs
fly scale count 2
```

---

## 💰 Custos (Plano Gratuito)

**Recursos incluídos FREE:**
- ✅ 3 VMs (256MB cada)
- ✅ 3GB volumes persistentes
- ✅ 160GB bandwidth/mês
- ✅ Certificado SSL automático
- ✅ Deploy ilimitado

**Upgrade recomendado (opcional):**
- 512MB RAM: ~$2/mês por VM
- 1GB RAM: ~$4/mês por VM

---

## 📚 Links Úteis

- **Dashboard:** https://fly.io/dashboard
- **Documentação:** https://fly.io/docs
- **Status:** https://status.fly.io
- **Comunidade:** https://community.fly.io
- **Pricing:** https://fly.io/docs/about/pricing

---

## ✅ Checklist de Deploy

- [ ] Fly CLI instalado (`fly version`)
- [ ] Login realizado (`fly auth login`)
- [ ] Volume criado (`fly volumes create idp_data --region gru --size 1`)
- [ ] Deploy executado (`fly deploy`)
- [ ] Health check OK (`fly checks list`)
- [ ] Teste da aplicação (`curl https://seu-app.fly.dev/api/health`)
- [ ] Logs monitorados (`fly logs`)

---

🎉 **Pronto!** Sua aplicação está rodando no Fly.io com performance **5-10x melhor** que o Render!
