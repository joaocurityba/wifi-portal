# Contribuindo com o Portal Cativo Municipal

Agradecemos pelo interesse em contribuir com o Portal Cativo Municipal! Este documento contém informações importantes para contribuidores.

## Como Contribuir

### 1. Fork do Projeto
- Clique em "Fork" no canto superior direito do repositório
- Clone o fork para sua máquina local

```bash
git clone https://github.com/seu-usuario/wifi-portal.git
cd wifi-portal-teste
```

### 2. Configuração do Ambiente

#### Requisitos
**Opção 1: Desenvolvimento Local (Tradicional)**
- Python 3.9+
- pip
- Git
- Redis (opcional, para testes completos)

**Opção 2: Desenvolvimento com Docker (Recomendado)**
- Docker
- Docker Compose
- Git

#### Instalação de Dependências
```bash
# Clonar repositório
git clone https://github.com/seu-usuario/wifi-portal.git
cd wifi-portal-teste

# Criar virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # se existir

# Instalar Gunicorn (não está em requirements.txt para dev)
pip install gunicorn
```

#### Configuração de Variáveis de Ambiente
```bash
# Copiar template
cp .env.template .env.local

# Editar para desenvolvimento
nano .env.local

# Mínimo para desenvolvimento:
DEBUG=True
SECRET_KEY=dev-key-change-me
ALLOWED_HOSTS=localhost,127.0.0.1
ADMIN_PASSWORD=admin123
```

### 3. Diretrizes de Código

#### Estilo de Código
- Siga o padrão PEP 8
- Use docstrings para funções e classes
- Comentários em português para lógica complexa

#### Nomenclatura
- **Variáveis**: `snake_case`
- **Funções**: `snake_case`
- **Classes**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`

#### Exemplos de Código

```python
def validar_email(email: str) -> bool:
    """
    Valida o formato de um endereço de email.
    
    Args:
        email (str): Endereço de email a ser validado
        
    Returns:
        bool: True se o email for válido, False caso contrário
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None
```

### 4. Testes

#### Rodando Testes Localmente
```bash
# Verificar sintaxe
python -m py_compile app_simple.py security.py data_manager.py

# Rodar testes existentes
python test_portal.py
python test_redirect.py

# Com pytest (se instalado)
pip install pytest pytest-flask
pytest -v

# Ver cobertura
pip install pytest-cov
pytest --cov=. --cov-report=html
# Abrir htmlcov/index.html no navegador
```

#### Antes de Fazer Pull Request
- [ ] Código foi testado localmente
- [ ] `python -c "from wsgi import app; print(app)"` funciona
- [ ] Sem imports não utilizados
- [ ] Sem dados sensíveis em commits
- [ ] Sem `.env.local` commitado
- [ ] Documentação foi atualizada (se necessário)

### 5. Processo de Pull Request

#### Antes de Enviar
1. **Teste localmente** - Certifique-se de que tudo funciona
2. **Verifique lint** - Use ferramentas de lint se disponíveis
3. **Atualize documentação** - Atualize README.md se necessário
4. **Commit significativo** - Use mensagens de commit descritivas

#### Mensagens de Commit
Use o formato:
```
Tipo: Descrição curta da mudança

Descrição detalhada da mudança (se necessário)
- Ponto 1
- Ponto 2
- Ponto 3
```

**Tipos de commit:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Alterações na documentação
- `style`: Alterações de formatação
- `refactor`: Refatoração
- `test`: Adição ou alteração de testes
- `chore`: Manutenção

#### Exemplo de Pull Request
```markdown
## Resumo da mudança
Breve descrição do que foi alterado.

## Motivação
Por que essa mudança foi necessária?

## Testes realizados
- [ ] Teste 1
- [ ] Teste 2
- [ ] Teste 3

## Checklist
- [ ] Código segue o estilo do projeto
- [ ] Alterações foram testadas
- [ ] Documentação foi atualizada
```

### 6. Segurança (MUITO IMPORTANTE)

#### Nunca Commitar Estes Arquivos
```
.env.local                # CONTÉM SENHAS E CHAVES!
*.key                     # Chaves privadas
*.pem                     # Certificados
data/users.csv           # Dados de usuários
data/access_log*         # Logs com dados sensíveis
.venv/                   # Virtual environment
__pycache__/             # Cache
```

**Está em .gitignore?**
```bash
grep "\.env\.local" .gitignore  # Deve aparecer
```

#### Código Seguro

**❌ Nunca faça:**
```python
password = "minha-senha"  # Hardcoded!
SECRET_KEY = "minha-chave"  # Hardcoded!
```

**✅ Sempre faça:**
```python
import os
password = os.environ.get('ADMIN_PASSWORD')
secret = os.environ.get('SECRET_KEY')

# Hash de senhas
from werkzeug.security import generate_password_hash
hash_seguro = generate_password_hash(user_password, method='pbkdf2')

# Validação
def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize(input_str: str) -> str:
    return re.sub(r'[<>\"\'%]', '', input_str).strip()
```

---

### 7. Desenvolvimento Local (Rodando Localmente)

#### Iniciar a Aplicação
```bash
# Ativar virtual environment
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Executar em desenvolvimento (debug mode)
python app_simple.py

# Acessar em http://localhost:5000
# Logs são mostrados no terminal
```

#### Com Docker (Alternativa)
```bash
# Buildar e iniciar (inclui Redis)
docker-compose up -d

# Acessar em http://localhost:5000
docker-compose logs -f app  # Ver logs

# Parar
docker-compose down
```

#### Troubleshooting Desenvolvimento
```bash
# Erro de porta em uso
lsof -i :5000  # ver quem está usando
# Mudar em app_simple.py: app.run(port=5001)

# Erro de imports
python -c "from wsgi import app; print(app)"

# Limpar cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

### 7. Relatórios de Bug

#### Como Reportar
1. **Busque por duplicatas** - Verifique se o bug já foi reportado
2. **Crie um issue** - Use o template de bug report
3. **Forneça detalhes** - Inclua:
   - Versão do Python
   - Sistema operacional
   - Passos para reproduzir
   - Mensagem de erro completa

#### Template de Bug Report
```markdown
## Descrição do Bug
Descrição clara do que está acontecendo.

## Passos para Reproduzir
1. Vá para '...'
2. Clique em '....'
3. Role até '....'
4. Veja o erro

## Comportamento Esperado
Descrição do que deveria acontecer.

## Ambiente
- Sistema Operacional: [ex: Windows 10, Ubuntu 20.04]
- Python: [ex: 3.9.7]
- Versão do Projeto: [ex: 1.0.0]

## Logs de Erro
Cole aqui qualquer log ou stack trace relevante.
```

### 8. Solicitações de Funcionalidades

#### Como Solicitar
1. **Verifique necessidade** - Busque por issues similares
2. **Crie um issue** - Use o template de feature request
3. **Descreva o problema** - Explique o que falta e por quê

#### Template de Feature Request
```markdown
## Descrição da Funcionalidade
Descrição clara do que você gostaria de ver adicionado.

## Motivação
Explique por que essa funcionalidade é necessária.

## Alternativas Consideradas
Descreva alternativas que você já considerou.

## Implementação Proposta
Se possível, descreva como você imagina que a implementação deveria ser.
```

### 9. Comunicação

#### Canais de Comunicação
- **Issues**: Para bugs e solicitações de funcionalidades
- **Pull Requests**: Para contribuições de código
- **Discussions**: Para dúvidas e discussões gerais

#### Código de Conduta
- Seja respeitoso com outros contribuidores
- Seja claro e objetivo na comunicação
- Ajude outros contribuidores quando possível
- Respeite o tempo e opinião dos mantenedores

### 10. Reconhecimento

#### Como Agradecemos
- Menção nos commits
- Agradecimento no README
- Resposta rápida aos PRs
- Feedback construtivo

## Contato

Para dúvidas sobre contribuição:
- Abra uma issue
- Envie um email para: [seu-email@dominio.com]

## Agradecimentos

Agradecemos a todos os contribuidores que ajudam a melhorar este projeto!

---

**Última atualização**: Janeiro 2025
**Versão**: 1.0.0