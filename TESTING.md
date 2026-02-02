# 🧪 Guia Rápido - Rodar os Testes

## ⚡ Início Rápido (3 passos)

### 1️⃣ Instalar Dependências de Teste
```powershell
pip install -r requirements-dev.txt
```

### 2️⃣ Rodar os Testes
```powershell
pytest -v
```

### 3️⃣ Ver Resultado
✅ Se todos passarem = Aplicação segura!
❌ Se algum falhar = NÃO faça deploy, corrija primeiro

---

## 📋 Comandos Úteis

### **Rodar todos os testes**
```powershell
pytest
```

### **Rodar com detalhes**
```powershell
pytest -v
```

### **Rodar apenas testes críticos**
```powershell
pytest -m critical -v
```

### **Rodar apenas testes de segurança**
```powershell
pytest -m security -v
```

### **Rodar arquivo específico**
```powershell
pytest tests/test_admin_security.py -v
pytest tests/test_encryption.py -v
pytest tests/test_form_validation.py -v
pytest tests/test_csrf.py -v
pytest tests/test_data_persistence.py -v
```

### **Rodar com cobertura**
```powershell
pytest --cov=app --cov=app_simple --cov-report=html
```

---

## 🎯 O que Cada Teste Valida

### 🔐 **test_admin_security.py** (8 testes)
Garante que apenas admins autorizados acessam o painel

### 🔒 **test_encryption.py** (9 testes)
Garante que dados pessoais são criptografados (LGPD)

### ✅ **test_form_validation.py** (12 testes)
Garante que apenas dados válidos entram no sistema

### 🛡️ **test_csrf.py** (9 testes)
Protege contra ataques CSRF

### 💾 **test_data_persistence.py** (8 testes)
Garante que dados são salvos e recuperados corretamente

---

## 📊 Interpretando Resultados

```
tests/test_admin_security.py::test_admin_route_requires_login PASSED
tests/test_admin_security.py::test_admin_login_with_valid_credentials PASSED
...
======================== 46 passed in 2.35s ========================
```

✅ **PASSED** = Tudo OK!
❌ **FAILED** = Problema encontrado - corrija antes de deploy
⚠️ **SKIPPED** = Teste pulado

---

## ⚠️ Regra de Ouro

**Se QUALQUER teste CRÍTICO falhar:**
- ❌ NÃO faça commit
- ❌ NÃO faça deploy
- ❌ NÃO ignore o erro
- ✅ CORRIJA o problema primeiro!

---

## 🆘 Problemas Comuns

### "ModuleNotFoundError: No module named 'pytest'"
```powershell
pip install pytest pytest-flask
```

### Testes falhando por diretório
```powershell
# Rode da raiz do projeto
cd c:\Users\PC\Desktop\wifi-portal\wifi-portal-teste
pytest
```

---

## 📞 Mais Informações

Ver `tests/README.md` para documentação completa
