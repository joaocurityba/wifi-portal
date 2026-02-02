# 🧪 Suite de Testes - Portal Cautivo Wi-Fi

## 📋 Visão Geral

Esta pasta contém os testes automatizados críticos para o Portal Cautivo Wi-Fi.

### **Testes Implementados (5 Críticos)**

| Arquivo | Prioridade | Testes | Cobre |
|---------|-----------|--------|-------|
| `test_admin_security.py` | 🔴 CRÍTICA | 8 | Proteção do painel admin |
| `test_encryption.py` | 🔴 CRÍTICA | 9 | Criptografia de dados sensíveis |
| `test_form_validation.py` | 🔴 CRÍTICA | 12 | Validação de formulários |
| `test_csrf.py` | 🔴 CRÍTICA | 9 | Proteção CSRF |
| `test_data_persistence.py` | 🔴 CRÍTICA | 8 | Salvamento de dados |

**Total: 46 testes críticos**

---

## 🚀 Como Rodar os Testes

### **Pré-requisitos**

```bash
# Instala dependências de teste
pip install -r requirements-dev.txt

# Ou instala manualmente
pip install pytest pytest-flask
```

### **Executar Todos os Testes**

```bash
# Roda todos os testes
pytest

# Roda com verbose (mostra cada teste)
pytest -v

# Roda com output detalhado
pytest -vv
```

### **Executar Testes Específicos**

```bash
# Roda apenas testes de segurança admin
pytest tests/test_admin_security.py -v

# Roda apenas testes de criptografia
pytest tests/test_encryption.py -v

# Roda apenas testes críticos (marcados)
pytest -m critical -v

# Roda apenas testes de segurança
pytest -m security -v
```

### **Executar com Cobertura**

```bash
# Instala pytest-cov
pip install pytest-cov

# Roda com relatório de cobertura
pytest --cov=app --cov=app_simple --cov-report=html

# Abre relatório no navegador
start htmlcov/index.html  # Windows
```

---

## 📊 Interpretando os Resultados

### **Saída Normal**

```
tests/test_admin_security.py::test_admin_route_requires_login PASSED    [ 12%]
tests/test_admin_security.py::test_admin_login_with_valid_credentials PASSED [ 25%]
...

======================== 46 passed in 2.35s ========================
```

✅ **PASSED** = Teste passou (tudo funcionando)  
❌ **FAILED** = Teste falhou (problema detectado)  
⚠️ **SKIPPED** = Teste pulado

### **Se um Teste Falhar**

```
FAILED tests/test_encryption.py::test_encrypt_decrypt_data - AssertionError: ...
```

1. **Leia a mensagem de erro** - indica o que quebrou
2. **Verifique o arquivo** mencionado
3. **Corrija o problema** no código fonte
4. **Rode novamente** o teste

---

## 🎯 O que Cada Teste Valida

### **1. test_admin_security.py**
- ✅ Painel admin bloqueia acesso não autenticado
- ✅ Login funciona com credenciais válidas
- ✅ Login rejeita credenciais inválidas
- ✅ Logout limpa sessão
- ✅ Admin autenticado acessa painel

**Se falhar:** Vulnerabilidade de segurança - invasor pode acessar dados

### **2. test_encryption.py**
- ✅ Dados são criptografados corretamente
- ✅ Dados são descriptografados sem perda
- ✅ Dados salvos em arquivo estão criptografados
- ✅ Caracteres especiais são preservados
- ✅ Hash de dados funciona

**Se falhar:** Violação de LGPD - dados pessoais expostos

### **3. test_form_validation.py**
- ✅ Campos obrigatórios são validados
- ✅ Menores de 13 anos são bloqueados
- ✅ Termos de uso são obrigatórios
- ✅ Email é validado
- ✅ Telefone é validado
- ✅ Data de nascimento é validada

**Se falhar:** Dados inválidos entram no sistema

### **4. test_csrf.py**
- ✅ Token CSRF é gerado
- ✅ Requisições sem token são bloqueadas
- ✅ Token inválido é rejeitado
- ✅ Token válido permite acesso
- ✅ Admin tem proteção CSRF

**Se falhar:** Vulnerável a ataques CSRF

### **5. test_data_persistence.py**
- ✅ Dados são salvos no CSV
- ✅ Dados são salvos criptografados
- ✅ Dados podem ser recuperados
- ✅ Múltiplos registros são preservados
- ✅ Integridade dos dados é mantida

**Se falhar:** Perda de dados de usuários

---

## 🔧 Configuração

### **pytest.ini**
Configurações globais do pytest (raiz do projeto)

### **conftest.py**
Fixtures compartilhadas entre todos os testes:
- `client` - Cliente Flask para testes
- `client_with_csrf` - Cliente com CSRF habilitado
- `authenticated_client` - Cliente já autenticado como admin
- `sample_user_data` - Dados de exemplo
- `get_csrf_token()` - Helper para obter token CSRF

---

## 🎓 Boas Práticas

### **Sempre rode os testes:**
- ✅ Antes de fazer commit
- ✅ Antes de fazer deploy
- ✅ Após fazer mudanças no código
- ✅ Após pull de código novo

### **Se um teste falhar:**
- ❌ **NÃO** faça deploy
- ❌ **NÃO** ignore o erro
- ✅ **CORRIJA** o problema antes de continuar

### **Mantenha os testes atualizados:**
- Adicione testes para novas funcionalidades
- Atualize testes quando mudar comportamento
- Documente testes complexos

---

## 📈 Próximos Passos

### **Expandir Cobertura**
Depois dos testes críticos, adicionar:
- `test_rate_limiting.py` - Rate limiting
- `test_session.py` - Gerenciamento de sessão
- `test_password_recovery.py` - Recuperação de senha
- `test_admin_routes.py` - Rotas administrativas
- `test_mikrotik.py` - Integração MikroTik

### **Integração Contínua (CI/CD)**
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-dev.txt
      - run: pytest -v
```

---

## 🆘 Troubleshooting

### **Erro: "ModuleNotFoundError: No module named 'pytest'"**
```bash
pip install pytest pytest-flask
```

### **Erro: "fixture 'client' not found"**
```bash
# Certifique-se de rodar pytest da raiz do projeto
cd /caminho/para/wifi-portal
pytest
```

### **Erro: Testes de CSRF falhando**
```bash
# Alguns testes desabilitam CSRF, outros habilitam
# Use a fixture correta: client_with_csrf
```

### **Erro: "No such file or directory: 'data/...'"**
```bash
# Fixtures criam diretórios temporários automaticamente
# Certifique-se de que a fixture cleanup_data_files está sendo usada
```

---

## 📞 Suporte

Para dúvidas sobre os testes:
1. Leia a documentação de cada teste (docstrings)
2. Verifique este README
3. Consulte documentação do pytest: https://docs.pytest.org/

---

**Última atualização:** Fevereiro 2026  
**Versão:** 1.0  
**Autor:** Equipe Portal Cautivo
