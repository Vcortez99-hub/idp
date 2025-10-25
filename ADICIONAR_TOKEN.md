# 🔑 Adicionar Token do Fly.io no GitHub

## ✅ Seu token (já gerado):

```
FlyV1 fm2_lJPECAAAAAAACqYxxBCiQJbjpEOtMkaG2UO8vs4RwrVodHRwczovL2FwaS5mbHkuaW8vdjGWAJLOABQrWR8Lk7lodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDytxggjaEIEwLmhT5Ku1dpGOVbTf+MnVNQNOSU+gXm54Hm0fL0h3G8lMbLF2nx/hnVau9bYnH+6zYt7fV/ETuwzJzZuughs/V5DF9r8aGghJRJHY/iV+W2Ki9q10i+PAySnkycp2LwEgMSDp2UH5baG+P36i7r++3VaduGjjBrkzDOcNnDAQKE7kf8WqQ2SlAORgc4AqY25HwWRgqdidWlsZGVyH6J3Zx8BxCDPlYI5R14W6eETSvrbN1fazuF1WMnTs+3wwTWHZPXaqg==,fm2_lJPETuwzJzZuughs/V5DF9r8aGghJRJHY/iV+W2Ki9q10i+PAySnkycp2LwEgMSDp2UH5baG+P36i7r++3VaduGjjBrkzDOcNnDAQKE7kf8WqcQQxweVT2b5W86ahNv9AJwXlcO5aHR0cHM6Ly9hcGkuZmx5LmlvL2FhYS92MZgEks5o/RgYzwAAAAEk9TY2F84AE1/UCpHOABNf1AzEEP4du0Fz0rA3XhqLCCvsW2jEIKuofEOkH4PSoN3gKrabl+jba86eI7qjdRnoOw1K3T6k
```

---

## 📝 Passo a Passo

### **1. Acesse as configurações do repositório**

Clique aqui: 👉 https://github.com/Vcortez99-hub/idp/settings/secrets/actions

Ou navegue manualmente:
1. Vá em https://github.com/Vcortez99-hub/idp
2. Clique em **Settings** (no topo da página)
3. No menu lateral, clique em **Secrets and variables** → **Actions**

---

### **2. Criar novo secret**

1. Clique no botão verde **New repository secret**

2. Preencha os campos:

   **Name:** (copie exatamente)
   ```
   FLY_API_TOKEN
   ```

   **Secret:** (copie todo o token abaixo)
   ```
   FlyV1 fm2_lJPECAAAAAAACqYxxBCiQJbjpEOtMkaG2UO8vs4RwrVodHRwczovL2FwaS5mbHkuaW8vdjGWAJLOABQrWR8Lk7lodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDytxggjaEIEwLmhT5Ku1dpGOVbTf+MnVNQNOSU+gXm54Hm0fL0h3G8lMbLF2nx/hnVau9bYnH+6zYt7fV/ETuwzJzZuughs/V5DF9r8aGghJRJHY/iV+W2Ki9q10i+PAySnkycp2LwEgMSDp2UH5baG+P36i7r++3VaduGjjBrkzDOcNnDAQKE7kf8WqQ2SlAORgc4AqY25HwWRgqdidWlsZGVyH6J3Zx8BxCDPlYI5R14W6eETSvrbN1fazuF1WMnTs+3wwTWHZPXaqg==,fm2_lJPETuwzJzZuughs/V5DF9r8aGghJRJHY/iV+W2Ki9q10i+PAySnkycp2LwEgMSDp2UH5baG+P36i7r++3VaduGjjBrkzDOcNnDAQKE7kf8WqcQQxweVT2b5W86ahNv9AJwXlcO5aHR0cHM6Ly9hcGkuZmx5LmlvL2FhYS92MZgEks5o/RgYzwAAAAEk9TY2F84AE1/UCpHOABNf1AzEEP4du0Fz0rA3XhqLCCvsW2jEIKuofEOkH4PSoN3gKrabl+jba86eI7qjdRnoOw1K3T6k
   ```

3. Clique em **Add secret**

---

### **3. Verificar se foi adicionado**

Você deve ver:
```
FLY_API_TOKEN
```

na lista de secrets, com a indicação "Updated X seconds ago"

---

### **4. Testar o deploy automático**

Faça qualquer alteração e push:

```bash
echo "# Deploy automático ativado!" >> README.md
git add .
git commit -m "test: Ativa deploy automático"
git push
```

---

### **5. Acompanhar o deploy**

Acesse: https://github.com/Vcortez99-hub/idp/actions

Você verá o workflow **"Deploy to Fly.io"** rodando! 🚀

---

## ✅ Checklist

- [ ] Acessei https://github.com/Vcortez99-hub/idp/settings/secrets/actions
- [ ] Cliquei em "New repository secret"
- [ ] Nome: `FLY_API_TOKEN`
- [ ] Secret: Token completo copiado
- [ ] Cliquei em "Add secret"
- [ ] Fiz push para testar
- [ ] Deploy começou automaticamente!

---

## 🎉 Pronto!

Agora todo `git push` fará deploy automático no Fly.io!

**Tempo de deploy:** 5-8 minutos
**Status em tempo real:** https://github.com/Vcortez99-hub/idp/actions
