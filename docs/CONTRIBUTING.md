# 🤝 Guia de Contribuição

Obrigado por contribuir com o Portal Cativo Wi-Fi!

---

## 🚀 Início Rápido

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/seu-usuario/wifi-portal.git
cd wifi-portal
```

### 2. Configurar Ambiente Local

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements-dev.txt

# Configurar .env.local
cp .env.prod.example .env.local
```

### 3. Executar Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html

# Ver relatório
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### 4. Fazer Mudanças

```bash
# Criar branch
git checkout -b feature/minha-feature

# Fazer mudanças...

# Testar
pytest

# Commit
git add .
git commit -m "feat: adiciona minha feature"

# Push
git push origin feature/minha-feature
```

### 5. Abrir Pull Request

- Vá para seu fork no GitHub
- Clique em "New Pull Request"
- Preencha descrição detalhada
- Aguarde review

---

## 📝 Padrões de Código

### Python
- **PEP 8** para formatação
- **Type hints** quando possível
- **Docstrings** em funções públicas
- **Nomes descritivos** para variáveis

```python
# ✅ Bom
def validate_user_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a ser validado
        
    Returns:
        True se válido, False caso contrário
    """
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

# ❌ Evitar
def val(e):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', e) is not None
```

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: adiciona busca por MAC address
fix: corrige validação de telefone
docs: atualiza README com instruções SSL
test: adiciona testes para admin profile
refactor: reorganiza estrutura de pastas
perf: otimiza query de estatísticas
```

### Testes

- **Teste toda nova funcionalidade**
- **Mantenha cobertura >80%**
- **Use fixtures do pytest**
- **Nomes descritivos**

```python
def test_admin_login_with_valid_credentials(client):
    """Admin deve conseguir fazer login com credenciais corretas"""
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': get_csrf_token(client)
    })
    
    assert response.status_code == 302
    assert b'admin' in response.data
```

---

## 🐛 Reportar Bugs

### Antes de Reportar
- Busque issues existentes
- Teste na versão mais recente
- Reproduza o problema

### Template de Issue

```markdown
**Descrição**
Descrição clara e concisa do bug.

**Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Veja erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente**
- OS: [ex: Ubuntu 22.04]
- Docker: [ex: 20.10.22]
- Versão: [ex: 1.0.0]

**Logs**
```
Cole logs relevantes aqui
```
```

---

## ✨ Sugerir Features

### Template de Feature Request

```markdown
**Problema que resolve**
Descrição clara do problema.

**Solução proposta**
Como você imagina que deveria funcionar.

**Alternativas consideradas**
Outras soluções que você pensou.

**Contexto adicional**
Qualquer outro contexto.
```

---

## 📚 Áreas de Contribuição

### Código
- Novas funcionalidades
- Correção de bugs
- Otimizações de performance
- Melhorias de segurança

### Documentação
- Melhorar README
- Adicionar tutoriais
- Traduzir documentação
- Corrigir typos

### Testes
- Aumentar cobertura
- Testes de integração
- Testes de performance
- Testes de segurança

### Design
- Melhorar UI/UX
- Responsividade
- Acessibilidade
- Temas/cores

---

## ❓ Dúvidas

- **Issues:** https://github.com/sua-prefeitura/wifi-portal/issues
- **Discussions:** https://github.com/sua-prefeitura/wifi-portal/discussions

---

**Obrigado por contribuir! 🙏**
