# 🌐 Portal Cativo Wi-Fi Municipal

Sistema completo de portal cativo para Wi-Fi público integrado ao MikroTik, desenvolvido em Flask com PostgreSQL, Docker e foco em segurança.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-95%2F103%20passing-brightgreen.svg)](#testes)
[![Coverage](https://img.shields.io/badge/Coverage-80%25-green.svg)](#cobertura-de-testes)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Instalação Rápida](#-instalação-rápida)
- [Configuração](#-configuração)
- [Arquitetura](#-arquitetura)
- [Segurança](#-segurança)
- [Testes](#-testes)
- [Deploy em Produção](#-deploy-em-produção)
- [Scripts Disponíveis](#-scripts-disponíveis)
- [Manutenção](#-manutenção)
- [Limitações](#-limitações-conhecidas)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 Visão Geral

Portal Cativo completo para autenticação de usuários em redes Wi-Fi públicas municipais, integrado com **MikroTik Hotspot**. Ideal para prefeituras, bibliotecas, praças e espaços públicos.

### **Por que usar este portal?**

✅ **Pronto para produção** - 80% de cobertura de testes, segurança robusta  
✅ **Fácil deploy** - Docker Compose com 1 comando  
✅ **Seguro** - CSRF, rate limiting, criptografia de dados sensíveis  
✅ **Escalável** - PostgreSQL, Redis, Nginx, health checks  
✅ **Administrável** - Painel admin com estatísticas e busca  

---

## ✨ Funcionalidades

### Portal Público
- 📝 Formulário de cadastro com validação (nome, email, telefone, data nascimento)
- 🔗 Integração MikroTik (captura IP, MAC, link-orig, username)
- ✅ Validação de idade mínima (13 anos)
- 📱 Interface responsiva (mobile-first)
- 🛡️ Proteção CSRF em todos os formulários
- ⏱️ Rate limiting (10 req/min por IP)
- 📜 Aceite de termos de uso obrigatório

### Painel Administrativo
- 🔐 Login seguro com senha forte (8+ chars, maiúscula, número, especial)
- 📊 Dashboard com estatísticas (total acessos, IPs únicos, MACs únicos)
- 🔍 Busca avançada em logs (por nome, email, telefone, IP, MAC, user agent)
- 👤 Perfil do admin (trocar email, senha)
- 📈 Métricas por período (hoje, semana, mês)
- 🔒 Recuperação de senha via email

### Segurança
- 🔐 **CSRF Protection** - Tokens em todos os formulários POST
- 🚦 **Rate Limiting** - Redis-based, configurável por rota
- 🔒 **Criptografia** - Fernet para dados PII (nome, email, telefone)
- 🔑 **Senhas** - Hashing com PBKDF2-HMAC-SHA256
- 🛡️ **Headers** - Secure headers (X-Frame-Options, CSP)
- 📝 **Logging** - Auditoria completa de eventos de segurança

---

## 🚀 Instalação Rápida

### Requisitos
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM mínimo
- 10GB espaço em disco

### 1. Clone o repositório
```bash
git clone https://github.com/sua-prefeitura/wifi-portal.git
cd wifi-portal
```

### 2. Configure variáveis de ambiente
```bash
cp .env.prod.example .env.local
nano .env.local  # Edite as credenciais
```

### 3. Inicie com Docker
```bash
# Desenvolvimento
docker-compose up -d

# Produção
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Acesse o sistema
- **Portal público:** http://localhost
- **Painel admin:** http://localhost/admin/login
  - Usuário: `admin`
  - Senha: definida em `ADMIN_DEFAULT_PASSWORD`

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env.local)

```bash
# Flask
SECRET_KEY=sua-chave-secreta-aqui-256-bits
FLASK_ENV=production

# Banco de Dados
DATABASE_URL=postgresql://portal_user:senha@postgres:5432/wifi_portal

# Redis (Rate Limiting)
REDIS_URL=redis://redis:6379/0

# Segurança
ENCRYPTION_KEY=chave-fernet-base64-aqui==
ADMIN_DEFAULT_PASSWORD=SenhaForte@2026

# Email (Recuperação de Senha)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_FROM=noreply@prefeitura.gov.br

# Rate Limiting
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URL=redis://redis:6379/0
```

### Gerar Credenciais Seguras

```bash
# Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Gerar ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Integração MikroTik

Configure o Hotspot no MikroTik:

```
/ip hotspot profile
set default login-by=http-chap,http-pap
set default html-directory=hotspot

# Apontar para seu portal
/ip hotspot
set [find] html-directory-override=http://seu-servidor/login
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIO                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    NGINX (Reverse Proxy)                     │
│                 • SSL/TLS Termination                        │
│                 • Static Files                               │
│                 • Load Balancing                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK APP (Gunicorn + gevent)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app_simple.py                                       │   │
│  │  • Rotas públicas (/login, /termos)                 │   │
│  │  • Rotas admin (/admin/*, /admin/profile)           │   │
│  │  • Middlewares (CSRF, Rate Limit)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app/security.py                                     │   │
│  │  • CSRF Protection                                   │   │
│  │  • Password Validation                               │   │
│  │  • Security Logging                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app/models.py                                       │   │
│  │  • User (SQLAlchemy)                                 │   │
│  │  • AccessLog (com campos criptografados)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────┬─────────────────────────────┬─────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────┐
│   PostgreSQL 15         │   │      Redis 7                │
│   • Users               │   │   • Rate Limiting           │
│   • AccessLog           │   │   • Session Storage         │
│   • Encrypted PII       │   │   • Cache                   │
└─────────────────────────┘   └─────────────────────────────┘
```

### Stack Tecnológica

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| **Backend** | Python | 3.11+ |
| **Framework** | Flask | 3.1.2 |
| **WSGI Server** | Gunicorn | 25.0.1 |
| **Database** | PostgreSQL | 15-alpine |
| **ORM** | SQLAlchemy | 2.0.46 |
| **Cache/Rate Limit** | Redis | 7-alpine |
| **Reverse Proxy** | Nginx | alpine |
| **Criptografia** | Fernet (cryptography) | 46.0.4 |
| **Containerização** | Docker | 20.10+ |

---

## 🔒 Segurança

### Características de Segurança Implementadas

#### 1. Proteção CSRF
- Tokens únicos por sessão
- Validação em todos os POST requests
- Auto-renovação de tokens

#### 2. Rate Limiting
```python
# Configuração padrão
/login         -> 10 req/minuto
/admin/login   -> 5 req/minuto
/admin/*       -> 30 req/minuto
```

#### 3. Criptografia de Dados
```python
# Campos criptografados (Fernet)
- nome
- email  
- telefone

# Campos hasheados
- MAC address (SHA256)
- IP address (SHA256)
```

#### 4. Senhas Seguras
- Mínimo 8 caracteres
- Pelo menos 1 maiúscula
- Pelo menos 1 número
- Pelo menos 1 caractere especial
- Hashing PBKDF2-HMAC-SHA256

#### 5. Headers de Segurança
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### Credenciais Padrão

⚠️ **IMPORTANTE:** Altere TODAS as credenciais antes de produção!

```bash
# Admin
Usuario: admin
Senha: definida em ADMIN_DEFAULT_PASSWORD (.env.local)

# PostgreSQL
Usuario: portal_user
Senha: definida em DATABASE_URL

# Redis
Senha: nenhuma (acessível apenas internamente)
```

**Trocar credenciais:**
```bash
# 1. Fazer backup
./scripts/backup/backup_postgres.sh

# 2. Editar .env.local
nano .env.local

# 3. Recriar containers
docker-compose down
docker-compose up -d

# 4. Trocar senha admin via painel
# Login -> Perfil -> Alterar Senha
```

---

## 🧪 Testes

### Executar Testes

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html

# Testes específicos
pytest tests/test_admin_security.py -v
pytest tests/test_csrf.py -v
```

### Resultados Atuais

```
📊 Status: 95/103 testes passando (92%)
📈 Cobertura: 80% (1863 linhas)

Detalhe por módulo:
├── app/data_manager.py     91% ✅
├── app/security.py          90% ✅
├── app/models.py            86% ✅
├── app_simple.py            59% 🟡
└── app/utils.py             53% 🟡
```

### Categorias de Testes

- ✅ **Segurança** (20 testes) - CSRF, autenticação, rate limiting
- ✅ **Criptografia** (8 testes) - Fernet, hashing
- ✅ **Validação** (12 testes) - Formulários, senhas, dados
- ✅ **Admin** (35 testes) - Login, perfil, stats, busca
- ✅ **Persistência** (7 testes) - Database, migrations
- ✅ **Recuperação de Senha** (13 testes) - Tokens, email, reset

---

## 🚀 Deploy em Produção

### Checklist Pré-Deploy

- [ ] Trocar SECRET_KEY
- [ ] Trocar ENCRYPTION_KEY  
- [ ] Trocar senha do PostgreSQL
- [ ] Trocar senha admin
- [ ] Configurar SMTP para emails
- [ ] Configurar SSL/TLS (certificado)
- [ ] Ajustar limites de rate limiting
- [ ] Configurar backup automático
- [ ] Configurar firewall
- [ ] Testar recuperação de backup

### Deploy Docker (Produção)

```bash
# 1. Clonar repositório
git clone https://github.com/sua-prefeitura/wifi-portal.git
cd wifi-portal

# 2. Configurar .env.local
cp .env.prod.example .env.local
nano .env.local  # Editar credenciais

# 3. Build e start
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verificar saúde
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/health

# 5. Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Configurar SSL (Let's Encrypt)

```bash
# Executar script de setup SSL
chmod +x deploy/setup-ssl.sh
./deploy/setup-ssl.sh seu-dominio.com.br
```

### Backup Automático

```bash
# Dar permissão aos scripts
chmod +x scripts/backup/*.sh

# Testar backup manualmente
./scripts/backup/backup_postgres.sh

# Configurar cron (diário às 02:00)
crontab -e
# Adicionar:
0 2 * * * /opt/wifi-portal/scripts/backup/backup_postgres.sh >> /var/log/wifi-backup.log 2>&1
```

### Monitoramento

```bash
# Health check
curl http://localhost/health

# Ver logs
docker-compose logs -f app

# Status dos containers
docker-compose ps

# Métricas
docker stats
```

**Documentação completa:** Ver [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🛠️ Scripts Disponíveis

### Backup e Restore

```bash
# Backup (Linux)
./scripts/backup/backup_postgres.sh

# Backup (Windows)
.\scripts\backup\backup_postgres.ps1

# Restore
./scripts/backup/restore_postgres.sh /backups/arquivo.sql.gz
```

### Docker

```bash
# Iniciar sistema (Windows)
.\scripts\docker\start-docker.ps1

# Parar sistema
docker-compose down

# Rebuild completo
docker-compose build --no-cache
docker-compose up -d
```

### Banco de Dados

```bash
# Executar migrations
docker-compose exec app flask db upgrade

# Criar migration
docker-compose exec app flask db revision -m "descrição"

# Inicializar DB
docker-compose exec app python init_db.py
```

**Documentação completa:** Ver [scripts/README.md](scripts/README.md)

---

## 🔧 Manutenção

### Rotinas Recomendadas

#### Diário
- ✅ Verificar logs de erro
- ✅ Monitorar espaço em disco
- ✅ Verificar backup automático executou

#### Semanal
- ✅ Testar restauração de backup
- ✅ Revisar logs de segurança
- ✅ Verificar performance do banco

#### Mensal
- ✅ Atualizar dependências (segurança)
- ✅ Limpar logs antigos (logrotate)
- ✅ Revisar estatísticas de uso
- ✅ Testar fluxo completo (ponta a ponta)

### Comandos Úteis

```bash
# Limpar logs antigos
docker-compose exec app find /app/logs -name "*.log" -mtime +30 -delete

# Vacuum PostgreSQL
docker-compose exec postgres vacuumdb -U portal_user -d wifi_portal -v

# Rebuild índices
docker-compose exec postgres reindexdb -U portal_user -d wifi_portal

# Ver uso de disco
docker system df
docker system prune -a  # Limpar não utilizados
```

---

## ⚠️ Limitações Conhecidas

### Escalabilidade
- **Single container** - Não configurado para múltiplas instâncias (sem Redis session store)
- **Uploads locais** - Arquivos salvos em volume Docker (não distribuído)
- **SMTP síncrono** - Envio de emails bloqueia thread (considerar Celery/RQ)

### Funcionalidades
- ❌ **Sem dashboard gráfico** - Estatísticas básicas apenas
- ❌ **Sem exportação de dados** - Apenas via SQL
- ❌ **Sem API REST** - Apenas interface web
- ❌ **Sem 2FA** - Apenas senha simples

### Integrações
- ✅ **MikroTik Hotspot** - Suportado
- ❌ **UniFi** - Não testado
- ❌ **pfSense** - Não testado
- ❌ **RADIUS** - Não implementado

### Próximas Melhorias

**v2.0 (Planejado):**
- [ ] API REST completa
- [ ] Dashboard com gráficos (Chart.js)
- [ ] Exportação CSV/Excel
- [ ] Autenticação 2FA (TOTP)
- [ ] Multi-tenancy (várias localidades)
- [ ] Celery para tarefas assíncronas
- [ ] Prometheus + Grafana
- [ ] Kubernetes manifests

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Desenvolvimento Local

```bash
# Clone e entre na pasta
git clone https://github.com/sua-prefeitura/wifi-portal.git
cd wifi-portal

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements-dev.txt

# Configure .env.local
cp .env.prod.example .env.local

# Execute testes
pytest --cov

# Rode localmente
flask run --debug
```

### Padrões de Código

- Python 3.11+
- PEP 8 (formatação)
- Type hints onde possível
- Docstrings em funções públicas
- Testes para novas features
- Cobertura mínima 80%

Ver: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 📞 Suporte

### Problemas Comuns

**1. Container não inicia**
```bash
# Verificar logs
docker-compose logs app

# Verificar saúde
docker-compose ps
```

**2. Erro de conexão com PostgreSQL**
```bash
# Verificar se container está rodando
docker-compose ps postgres

# Testar conexão
docker-compose exec postgres psql -U portal_user -d wifi_portal
```

**3. Rate limit muito agressivo**
```bash
# Ajustar em .env.local
RATELIMIT_ENABLED=false  # Desabilitar temporariamente

# Ou aumentar limites em app_simple.py
```

**Documentação completa:** Ver [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

### Reportar Bugs

Abra uma issue no GitHub com:
- Descrição do problema
- Passos para reproduzir
- Logs relevantes
- Versão do sistema

---

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- Flask Team - Framework web
- PostgreSQL Team - Banco de dados
- MikroTik - Integração Hotspot
- Comunidade Open Source

---

**Desenvolvido com ❤️ para Wi-Fi Público Municipal**

**Versão:** 1.0.0  
**Última atualização:** Fevereiro 2026
