# 🤝 Guia de Contribuição

Obrigado por considerar contribuir com o **Portal Cativo WiFi**! Este documento fornece diretrizes para contribuir com o projeto.

---

## 📋 Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Posso Contribuir?](#como-posso-contribuir)
3. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
4. [Padrões de Código](#padrões-de-código)
5. [Workflow de Contribuição](#workflow-de-contribuição)
6. [Commits e Mensagens](#commits-e-mensagens)
7. [Pull Requests](#pull-requests)
8. [Testes](#testes)
9. [Documentação](#documentação)
10. [Revisão de Código](#revisão-de-código)

---

## 📜 Código de Conduta

### **Nossos Valores**

- **Respeito:** Trate todos com dignidade e profissionalismo
- **Colaboração:** Trabalhe em conjunto, compartilhe conhecimento
- **Qualidade:** Escreva código limpo, testado e documentado
- **Transparência:** Comunique-se claramente sobre mudanças

### **Comportamento Esperado**

✅ Usar linguagem acolhedora e inclusiva  
✅ Respeitar opiniões e experiências diferentes  
✅ Aceitar críticas construtivas  
✅ Focar no que é melhor para a comunidade  
✅ Mostrar empatia com outros membros

### **Comportamento Inaceitável**

❌ Linguagem ou imagens sexualizadas  
❌ Ataques pessoais ou políticos  
❌ Assédio público ou privado  
❌ Publicar informações privadas de terceiros  
❌ Conduta não profissional

---

## 💡 Como Posso Contribuir?

### **Reportar Bugs**

Encontrou um bug? Ajude-nos a melhorar!

1. **Verifique** se já existe uma issue aberta
2. **Crie** uma nova issue com:
   - Título claro e descritivo
   - Passos para reproduzir
   - Comportamento esperado vs observado
   - Screenshots (se aplicável)
   - Ambiente (OS, versão do Docker, etc)

**Template de Bug Report:**

```markdown
### Descrição
[Descrição clara do problema]

### Passos para Reproduzir
1. Acesse '...'
2. Clique em '...'
3. Veja o erro

### Comportamento Esperado
[O que deveria acontecer]

### Comportamento Observado
[O que aconteceu de fato]

### Ambiente
- OS: Ubuntu 22.04
- Docker: 24.0.7
- Navegador: Chrome 120

### Logs
```
[Cole os logs relevantes aqui]
```
```

### **Sugerir Melhorias**

Tem uma ideia? Compartilhe!

1. **Verifique** o roadmap e issues existentes
2. **Abra** uma issue com tag `enhancement`
3. **Descreva**:
   - Problema que a feature resolve
   - Solução proposta
   - Alternativas consideradas
   - Impacto em funcionalidades existentes

### **Contribuir com Código**

Pronto para codar? Siga o [Workflow de Contribuição](#workflow-de-contribuição)!

### **Melhorar Documentação**

Documentação é crucial! Você pode:

- Corrigir erros de digitação
- Melhorar explicações
- Adicionar exemplos
- Traduzir conteúdo
- Criar tutoriais

---

## 🛠️ Ambiente de Desenvolvimento

### **Pré-requisitos**

- Python 3.9+
- Docker 24.0+
- Docker Compose 2.0+
- Git

### **Setup Inicial**

```bash
# 1. Fork o repositório no GitHub

# 2. Clone seu fork
git clone https://github.com/SEU_USUARIO/wifi-portal.git
cd wifi-portal

# 3. Adicione upstream
git remote add upstream https://github.com/REPO_ORIGINAL/wifi-portal.git

# 4. Crie .env.local
cp .env.prod .env.local
# Edite conforme necessário

# 5. Suba ambiente de desenvolvimento
docker-compose up -d

# 6. Verifique
curl http://localhost/healthz
```

### **Desenvolvimento Local (sem Docker)**

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Subir Redis
docker run -d -p 6379:6379 redis:7-alpine

# 4. Executar aplicação
python app_simple.py

# Acesse: http://localhost:5000
```

### **Ferramentas de Desenvolvimento**

```bash
# Instalar ferramentas de lint e formatação
pip install -r requirements-dev.txt

# Ferramentas incluídas:
# - pytest: Testes
# - black: Formatação de código
# - flake8: Linting
# - mypy: Type checking
# - pylint: Análise estática
```

---

## 📝 Padrões de Código

### **Python**

#### **PEP 8 - Style Guide**

```python
# ✅ BOM
def calculate_user_age(birth_year: int) -> int:
    """
    Calcula a idade do usuário baseado no ano de nascimento.
    
    Args:
        birth_year: Ano de nascimento (YYYY)
        
    Returns:
        Idade em anos
    """
    from datetime import datetime
    current_year = datetime.now().year
    return current_year - birth_year

# ❌ RUIM
def calc(y):
    from datetime import datetime
    return datetime.now().year-y
```

#### **Formatação com Black**

```bash
# Formatar todos os arquivos
black .

# Verificar sem modificar
black --check .

# Formatar arquivo específico
black app_simple.py
```

#### **Linting com Flake8**

```bash
# Verificar código
flake8 .

# Ignorar diretórios
flake8 --exclude=venv,__pycache__,.git

# Configuração em .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = venv, __pycache__, .git, data, uploads
```

#### **Type Hints**

```python
# ✅ Use type hints
from typing import Dict, List, Optional

def get_user_data(user_id: int) -> Optional[Dict[str, str]]:
    """Retorna dados do usuário ou None se não encontrado."""
    pass

def process_users(users: List[str]) -> int:
    """Processa lista de usuários e retorna quantidade."""
    return len(users)

# ❌ Evite código sem tipos
def get_user(id):
    pass
```

#### **Docstrings**

```python
# ✅ Google Style Docstrings
def authenticate_user(username: str, password: str) -> bool:
    """
    Autentica usuário verificando credenciais.

    Args:
        username: Nome de usuário
        password: Senha em texto plano

    Returns:
        True se autenticado, False caso contrário

    Raises:
        ValueError: Se username ou password estiverem vazios
        
    Example:
        >>> authenticate_user("admin", "password123")
        True
    """
    if not username or not password:
        raise ValueError("Username e password são obrigatórios")
    # ... lógica de autenticação
```

### **JavaScript**

```javascript
// ✅ Use const/let, nunca var
const API_URL = '/api/users';
let userCount = 0;

// ✅ Arrow functions
const calculateTotal = (items) => items.reduce((sum, item) => sum + item.price, 0);

// ✅ Template literals
const greeting = `Olá, ${userName}!`;

// ✅ Async/await
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        return await response.json();
    } catch (error) {
        console.error('Erro ao buscar usuário:', error);
        throw error;
    }
}
```

### **HTML/CSS**

```html
<!-- ✅ Semântica correta -->
<main class="portal-container">
    <section class="login-section">
        <h1>Portal de Acesso WiFi</h1>
        <form id="loginForm" class="login-form">
            <label for="username">Usuário:</label>
            <input type="text" id="username" name="username" required>
            <button type="submit" class="btn btn-primary">Entrar</button>
        </form>
    </section>
</main>
```

```css
/* ✅ BEM Naming */
.login-form {}
.login-form__input {}
.login-form__button--primary {}

/* ✅ Mobile-first */
.container {
    width: 100%;
    padding: 1rem;
}

@media (min-width: 768px) {
    .container {
        max-width: 720px;
    }
}
```

---

## 🔄 Workflow de Contribuição

### **1. Criar Branch**

```bash
# Atualizar main
git checkout main
git pull upstream main

# Criar branch descritiva
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
# ou
git checkout -b docs/atualizar-readme
```

**Convenção de Nomes:**

- `feature/` - Nova funcionalidade
- `fix/` - Correção de bug
- `docs/` - Documentação
- `refactor/` - Refatoração
- `test/` - Adição de testes
- `chore/` - Manutenção (deps, config, etc)

### **2. Desenvolver**

```bash
# Fazer alterações
nano app/security.py

# Testar localmente
docker-compose up -d
pytest

# Adicionar ao stage
git add app/security.py

# Commit (ver seção de commits)
git commit -m "feat: adicionar autenticação 2FA"
```

### **3. Manter Atualizado**

```bash
# Puxar atualizações do upstream
git fetch upstream
git rebase upstream/main

# Se houver conflitos, resolva e continue
git add .
git rebase --continue
```

### **4. Push**

```bash
# Push para seu fork
git push origin feature/nome-da-feature
```

### **5. Abrir Pull Request**

1. Vá ao GitHub
2. Clique em "New Pull Request"
3. Preencha o template (ver seção PR)
4. Aguarde revisão

---

## 💬 Commits e Mensagens

### **Conventional Commits**

Usamos o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (não altera lógica)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção
- `perf`: Performance
- `ci`: CI/CD
- `build`: Build system

**Exemplos:**

```bash
# ✅ Simples
git commit -m "feat: adicionar rate limiting por IP"

# ✅ Com scope
git commit -m "fix(auth): corrigir validação de senha"

# ✅ Com body
git commit -m "feat(api): adicionar endpoint de estatísticas

Adiciona novo endpoint /api/stats que retorna:
- Total de usuários autenticados
- Média de tempo de sessão
- Top 10 dispositivos

Closes #42"

# ✅ Breaking change
git commit -m "feat!: migrar de CSV para PostgreSQL

BREAKING CHANGE: Formato de armazenamento alterado.
Ver MIGRATION.md para instruções de migração."
```

**Regras:**

- ✅ Primeira linha ≤ 72 caracteres
- ✅ Use imperativo ("adicionar" não "adicionado")
- ✅ Não termine com ponto
- ✅ Body opcional (explica "o quê" e "por quê")
- ✅ Footer opcional (referências, breaking changes)

---

## 🔀 Pull Requests

### **Template de PR**

```markdown
## Descrição
[Descrição clara das mudanças]

## Tipo de Mudança
- [ ] Bug fix (correção que resolve uma issue)
- [ ] Nova feature (adiciona funcionalidade)
- [ ] Breaking change (altera comportamento existente)
- [ ] Documentação

## Motivação
[Por que essa mudança é necessária?]

## Como Testar
1. Subir ambiente: `docker-compose up -d`
2. Acessar: `http://localhost/login`
3. Testar funcionalidade X
4. Verificar resultado Y

## Checklist
- [ ] Código segue padrões do projeto
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Nenhum warning de linter
- [ ] Testado localmente
- [ ] Commits seguem Conventional Commits

## Screenshots (se aplicável)
[Cole screenshots aqui]

## Issues Relacionadas
Closes #123
Relacionado a #456
```

### **Processo de Revisão**

1. **Automated Checks:** CI roda testes automaticamente
2. **Code Review:** Mantenedor revisa o código
3. **Feedback:** Discussão e ajustes
4. **Aprovação:** PR aprovado
5. **Merge:** Código integrado ao main

### **Respondendo Feedback**

```bash
# Fazer alterações solicitadas
nano app_simple.py

# Commit
git add .
git commit -m "fix: corrigir validação conforme review"

# Push (atualiza PR automaticamente)
git push origin feature/nome-da-feature
```

---

## 🧪 Testes

### **Executar Testes**

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=app --cov-report=html

# Teste específico
pytest test_portal.py::test_login

# Ver relatório
open htmlcov/index.html
```

### **Escrever Testes**

```python
# test_auth.py
import pytest
from app.security import SecurityManager

def test_password_hashing():
    """Testa hash de senha."""
    security = SecurityManager('test-key')
    password = 'senha123'
    
    # Hash
    hashed = security.hash_password(password)
    
    # Verificar
    assert security.verify_password(password, hashed) is True
    assert security.verify_password('errada', hashed) is False

def test_rate_limiting():
    """Testa rate limiting."""
    # ... implementação
    
@pytest.fixture
def client():
    """Cliente de teste Flask."""
    from app_simple import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    """Testa página de login."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Portal WiFi' in response.data
```

### **Cobertura Mínima**

- **Geral:** 80%
- **Módulos críticos (security.py):** 90%
- **Novas features:** 100%

---

## 📚 Documentação

### **O Que Documentar**

- ✅ Novas funcionalidades
- ✅ Mudanças em APIs
- ✅ Configurações adicionadas
- ✅ Dependências novas
- ✅ Processos de deploy alterados

### **Onde Documentar**

- **README.md:** Visão geral, quick start
- **DEPLOY.md:** Instruções de deploy
- **CONTRIBUTING.md:** Este arquivo
- **TROUBLESHOOTING.md:** Problemas comuns
- **Docstrings:** Funções e classes
- **Comments:** Lógica complexa no código

### **Exemplo de Boa Documentação**

```python
class RateLimiter:
    """
    Controla taxa de requisições por IP usando Redis.
    
    Implementa sliding window com limite de 100 req/min.
    
    Attributes:
        redis_client: Conexão com Redis
        window_size: Tamanho da janela em segundos (default: 60)
        max_requests: Máximo de requisições permitidas (default: 100)
        
    Example:
        >>> limiter = RateLimiter(redis_client)
        >>> if limiter.is_allowed('192.168.1.1'):
        ...     # Processar requisição
        ...     pass
        >>> else:
        ...     # Retornar 429 Too Many Requests
        ...     pass
    """
    
    def __init__(self, redis_client, window_size=60, max_requests=100):
        """Inicializa rate limiter."""
        self.redis = redis_client
        self.window = window_size
        self.max = max_requests
```

---

## 👀 Revisão de Código

### **Como Revisor**

#### **O Que Verificar**

- [ ] Código segue padrões do projeto
- [ ] Lógica está correta
- [ ] Testes adequados incluídos
- [ ] Documentação atualizada
- [ ] Sem problemas de segurança
- [ ] Performance não degradou
- [ ] Não quebra funcionalidades existentes

#### **Como Dar Feedback**

**✅ Feedback Construtivo:**

```
Ótima implementação do cache! 

Sugestão: poderíamos adicionar TTL configurável?

```python
def get_cached_data(key, ttl=3600):
    ...
```

Isso daria mais flexibilidade.
```

**❌ Feedback Destrutivo:**

```
Isso está errado. Refaça.
```

### **Como Autor**

#### **Antes de Submeter**

```bash
# 1. Formatar código
black .

# 2. Verificar lint
flake8 .

# 3. Executar testes
pytest

# 4. Verificar cobertura
pytest --cov=app

# 5. Build local
docker-compose up -d --build

# 6. Testar manualmente
curl http://localhost/healthz
```

#### **Respondendo Revisão**

- ✅ Agradeça o feedback
- ✅ Faça perguntas se não entender
- ✅ Explique decisões de design
- ✅ Implemente sugestões ou explique por que não
- ✅ Seja profissional e respeitoso

---

## 🏷️ Issues e Labels

### **Labels Padrão**

- `bug` - Algo não está funcionando
- `enhancement` - Nova funcionalidade
- `documentation` - Melhorias na documentação
- `good first issue` - Bom para iniciantes
- `help wanted` - Precisa de ajuda
- `question` - Pergunta ou discussão
- `wontfix` - Não será implementado
- `duplicate` - Issue duplicada
- `priority:high` - Alta prioridade
- `priority:low` - Baixa prioridade

---

## 🎯 Prioridades

### **High Priority**

- 🔴 Bugs de segurança
- 🔴 Perda de dados
- 🔴 Aplicação quebrada

### **Medium Priority**

- 🟡 Features planejadas
- 🟡 Melhorias de performance
- 🟡 Refatorações

### **Low Priority**

- 🟢 Nice to have
- 🟢 Documentação
- 🟢 Testes adicionais

---

## 📞 Contato

- **Issues:** [GitHub Issues](https://github.com/seu-repo/wifi-portal/issues)
- **Discussions:** [GitHub Discussions](https://github.com/seu-repo/wifi-portal/discussions)
- **Email:** devteam@prefeitura.com.br

---

## 🎉 Reconhecimentos

Contribuidores são reconhecidos:

- README.md (seção Contributors)
- Releases notes
- Changelog

### **Hall of Fame**

Contribuidores top:

1. @usuario1 - 50 commits
2. @usuario2 - 30 commits
3. @usuario3 - 20 commits

---

## 📖 Recursos Adicionais

- [Python PEP 8](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)

---

<p align="center">
  <strong>Obrigado por contribuir! 🙏</strong><br>
  Juntos tornamos o Portal Cativo melhor para todos.
</p>
