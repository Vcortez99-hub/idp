# 🤖 Deploy Automático no Fly.io com GitHub Actions

## 📋 O que foi configurado

✅ **GitHub Actions Workflow** - Deploy automático a cada push
✅ **Branch: master** - Deploy só quando push na branch principal
✅ **Deploy manual** - Possibilidade de fazer deploy pela interface do GitHub

---

## 🚀 Setup Rápido (3 passos)

### **Passo 1: Gerar token do Fly.io**

No terminal, execute:

```bash
fly auth token
```

Isso vai gerar um token como:
```
FlyV1 fm2_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copie esse token!** Você vai precisar dele no próximo passo.

---

### **Passo 2: Adicionar token no GitHub**

1. Acesse seu repositório no GitHub: https://github.com/Vcortez99-hub/idp

2. Vá em **Settings** (Configurações) → **Secrets and variables** → **Actions**

3. Clique em **New repository secret**

4. Configure:
   - **Name:** `FLY_API_TOKEN`
   - **Secret:** Cole o token que você copiou no Passo 1

5. Clique em **Add secret**

---

### **Passo 3: Fazer commit e push**

```bash
git add .github/workflows/fly-deploy.yml
git commit -m "CI/CD: Adiciona deploy automático no Fly.io"
git push
```

**Pronto!** 🎉 O deploy vai começar automaticamente!

---

## 🔄 Como funciona

### **Deploy Automático**

Sempre que você fizer `git push` na branch `master`:

```bash
git add .
git commit -m "Minha alteração"
git push
```

**O que acontece:**
1. ✅ GitHub detecta o push
2. ✅ GitHub Actions inicia workflow
3. ✅ Faz checkout do código
4. ✅ Instala Fly CLI
5. ✅ Faz deploy no Fly.io
6. ✅ App atualizado em ~5-8 minutos

---

### **Deploy Manual**

Se quiser fazer deploy sem push:

1. Vá em **Actions** no GitHub
2. Selecione **Deploy to Fly.io**
3. Clique em **Run workflow**
4. Escolha a branch e clique em **Run workflow**

---

## 📊 Monitoramento

### **Ver status do deploy:**

**GitHub:**
- Acesse: https://github.com/Vcortez99-hub/idp/actions
- Veja progresso em tempo real

**Fly.io:**
```bash
fly logs
```

---

## 🛠️ Arquivo de Workflow

**Localização:** `.github/workflows/fly-deploy.yml`

```yaml
name: Deploy to Fly.io

on:
  push:
    branches:
      - master  # Deploy automático no push
  workflow_dispatch:  # Deploy manual

jobs:
  deploy:
    name: Deploy app
    runs-on: ubuntu-latest

    steps:
      - name: Checkout código
        uses: actions/checkout@v4

      - name: Setup Fly.io CLI
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy para Fly.io
        run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

---

## 🎯 Fluxo de Trabalho Completo

### **Desenvolvimento local:**

```bash
# 1. Faça suas alterações
code app.py

# 2. Teste localmente
python app.py

# 3. Commit
git add .
git commit -m "Feature: Nova funcionalidade"

# 4. Push (dispara deploy automático)
git push

# 5. Aguarde ~5-8 min
# Deploy acontece automaticamente!
```

### **Verificar deploy:**

```bash
# Ver logs em tempo real
fly logs

# Ver status da app
fly status

# Acessar app
open https://idp-classifier.fly.dev
```

---

## 🔧 Troubleshooting

### **Deploy falhou?**

**1. Verifique logs no GitHub:**
- https://github.com/Vcortez99-hub/idp/actions
- Clique no workflow que falhou
- Veja o erro detalhado

**2. Verifique token:**
```bash
# Gere novo token se necessário
fly auth token

# Atualize no GitHub
# Settings → Secrets → FLY_API_TOKEN → Update
```

**3. Deploy manual como fallback:**
```bash
fly deploy
```

---

### **Token expirou?**

Se aparecer erro de autenticação:

```bash
# 1. Gere novo token
fly auth token

# 2. Atualize no GitHub
# Settings → Secrets → FLY_API_TOKEN → Update
```

---

### **Build muito lento?**

O build remoto (`--remote-only`) é feito nos servidores do Fly.io (mais rápido que GitHub Actions).

**Tempo normal:**
- Build inicial: ~8-10 min
- Builds subsequentes (cache): ~5-6 min

---

## 🚦 Status Badges (Opcional)

Adicione badge de status no README.md:

```markdown
[![Deploy to Fly.io](https://github.com/Vcortez99-hub/idp/actions/workflows/fly-deploy.yml/badge.svg)](https://github.com/Vcortez99-hub/idp/actions/workflows/fly-deploy.yml)
```

Mostra status do último deploy: ✅ ou ❌

---

## 🎨 Personalizações

### **Deploy só em tags (releases):**

```yaml
on:
  push:
    tags:
      - 'v*'  # Deploy quando criar tag v1.0, v2.0, etc
```

### **Deploy em múltiplas branches:**

```yaml
on:
  push:
    branches:
      - master
      - develop
      - production
```

### **Notificações no Slack/Discord:**

Adicione step de notificação após deploy:

```yaml
- name: Notificar sucesso
  if: success()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
    -d '{"text":"✅ Deploy concluído!"}'
```

---

## 📈 Vantagens do Deploy Automático

| Antes (Manual) | Agora (Automático) |
|----------------|-------------------|
| `git push` | `git push` |
| `fly deploy` (manual) | ✅ **Automático!** |
| Aguardar 5-8 min | Faz outra coisa enquanto deploya |
| Pode esquecer | **Nunca esquece!** |
| Um deploy por vez | Fila automática |

---

## ✅ Checklist Final

- [x] Workflow criado (`.github/workflows/fly-deploy.yml`)
- [ ] Token gerado (`fly auth token`)
- [ ] Token adicionado no GitHub (`FLY_API_TOKEN`)
- [ ] Primeiro push feito
- [ ] Deploy verificado (GitHub Actions)
- [ ] App funcionando (Fly.io)

---

## 📚 Links Úteis

- **GitHub Actions:** https://github.com/Vcortez99-hub/idp/actions
- **Fly.io Dashboard:** https://fly.io/dashboard
- **Fly.io Docs:** https://fly.io/docs/app-guides/continuous-deployment-with-github-actions/

---

**Configurado em:** 25/10/2025
**Arquivo:** `.github/workflows/fly-deploy.yml`
**Tempo médio de deploy:** 5-8 minutos

🎉 **Agora todo push na master faz deploy automático!**
