# 🌐 Portal Cativo - Wi-Fi Público Municipal

Sistema completo de portal cativo para Wi-Fi público integrado ao MikroTik, desenvolvido em Flask com foco em segurança, escalabilidade e facilidade de manutenção.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Início Rápido](#início-rápido)
- [Arquitetura](#arquitetura)
- [Documentação](#documentação)
- [Desenvolvimento](#desenvolvimento)
- [Produção](#produção)
- [Segurança](#segurança)
- [Suporte](#suporte)
- [Licença](#licença)

---

## 🎯 Visão Geral

O Portal Cativo é uma solução completa para autenticação de usuários em redes Wi-Fi públicas, especialmente desenvolvida para integração com MikroTik Hotspot. Ideal para prefeituras, bibliotecas, praças e espaços públicos que oferecem acesso gratuito à internet.

### **Características Principais:**
- 🔐 Autenticação de usuários com validação de dados
- 📊 Painel administrativo com estatísticas e busca
- 🔒 Segurança avançada (CSRF, Rate Limiting, Criptografia)
- 🐳 Deploy simplificado com Docker
- 🔄 Alta disponibilidade com health checks
- 📱 Interface responsiva para dispositivos móveis

---

## ✨ Funcionalidades

### **Portal Público**
- ✅ Formulário de cadastro com validação de dados
- ✅ Integração completa com MikroTik (IP, MAC, link-orig)
- ✅ Validação de idade (mínimo 13 anos)
- ✅ Validação de telefone e email
- ✅ Termos de uso obrigatórios
- ✅ Proteção CSRF
- ✅ Design responsivo

### **Painel Administrativo**
- ✅ Login seguro com rate limiting
- ✅ Visualização de registros de acesso
- ✅ Busca por nome, telefone, CPF, IP ou MAC
- ✅ Estatísticas de uso
- ✅ Exportação de dados
- ✅ Edição de perfil
- ✅ Recuperação de senha
- ✅ Logs de segurança

### **Segurança**
- ✅ Criptografia de dados sensíveis (Fernet + PBKDF2)
- ✅ Rate limiting (100 req/min, 1000 req/hora)
- ✅ Proteção CSRF em todas as rotas
- ✅ Headers de segurança (HSTS, CSP, X-Frame-Options)
- ✅ Validação e sanitização de inputs
- ✅ Logs de auditoria
- ✅ Session timeout configurável

### **Infraestrutura**
- ✅ Docker Compose para dev e prod
- ✅ Health checks automáticos
- ✅ Redis para cache e rate limiting
- ✅ Nginx como reverse proxy
- ✅ SSL/TLS com Let's Encrypt
- ✅ Logs estruturados
- ✅ Renovação automática de certificados

---

## 🔧 Requisitos

### **Para Desenvolvimento:**
- Docker 20.10+
- Docker Compose 1.29+
- Git

### **Para Produção (Ubuntu Server):**
- Ubuntu 20.04+ (LTS recomendado)
- Docker 20.10+
- Docker Compose 1.29+
- Domínio configurado (para SSL)
- 2GB RAM mínimo (4GB recomendado)
- 20GB disco
- Portas 80 e 443 abertas

### **Stack Tecnológica:**
- **Backend:** Python 3.9+, Flask 2.3+
- **WSGI:** Gunicorn 21.0+
- **Proxy:** Nginx (Alpine)
- **Cache:** Redis 7.0+
- **Criptografia:** Cryptography 41.0+
- **Rate Limiting:** Flask-Limiter 3.5+

---

## 🚀 Início Rápido

### **Desenvolvimento Local (5 minutos)**

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/wifi-portal.git
cd wifi-portal

# 2. Copiar variáveis de ambiente
cp .env.prod .env.local

# 3. Gerar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# Cole a saída no .env.local

# 4. Subir ambiente
docker-compose up -d

# 5. Acessar
# Portal: http://localhost/login
# Admin: http://localhost/admin/login
# Health: http://localhost/healthz
```

**Credenciais padrão:** `admin` / `admin123` ⚠️ **MUDE EM PRODUÇÃO!**

### **Verificar Status**

```bash
# Ver containers
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar ambiente
docker-compose down
```

---

## 🏗️ Arquitetura

### **Diagrama de Componentes**

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET / USUÁRIOS                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │  MikroTik      │
            │  Hotspot       │
            └────────┬───────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Nginx Container     │
         │   (Reverse Proxy)     │
         │   Porta: 80, 443      │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Flask App           │
         │   (Gunicorn)          │
         │   Porta: 5000         │
         └───────┬───────────────┘
                 │
                 ├──────────────────┐
                 │                  │
                 ▼                  ▼
      ┌──────────────────┐  ┌──────────────┐
      │  Redis           │  │  Data        │
      │  (Rate Limiting) │  │  (CSV/JSON)  │
      └──────────────────┘  └──────────────┘
```

### **Fluxo de Requisição**

1. **Usuário** conecta ao Wi-Fi → MikroTik redireciona para portal
2. **Nginx** recebe requisição (HTTPS) → proxy para app
3. **Flask App** processa → valida dados → registra acesso
4. **Redis** controla rate limiting
5. **MikroTik** libera acesso após validação

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [DEPLOY.md](DEPLOY-NEW.md) | **Guia completo de deploy em produção** |
| [CONTRIBUTING.md](CONTRIBUTING-NEW.md) | Como contribuir com o projeto |
| [LIMITATIONS.md](LIMITATIONS-NEW.md) | Limitações conhecidas e roadmap |
| [TROUBLESHOOTING.md](TROUBLESHOOTING-NEW.md) | Solução de problemas comuns |

---

## 💻 Desenvolvimento

### **Estrutura do Projeto**

```
wifi-portal/
├── app_simple.py              # Aplicação Flask principal
├── wsgi.py                    # Entry point para Gunicorn
├── requirements.txt           # Dependências Python
├── Dockerfile                 # Build da aplicação
├── docker-compose.yml         # Ambiente desenvolvimento
├── docker-compose.prod.yml    # Ambiente produção
├── .env.prod                  # Template de variáveis
├── .env.local                 # Variáveis locais (não commitar!)
│
├── app/                       # Módulos da aplicação
│   ├── security.py           # Gerenciamento de segurança
│   ├── data_manager.py       # Gerenciamento de dados
│   └── locks.py              # File locking
│
├── deploy/                    # Arquivos de deploy
│   ├── nginx.docker.conf     # Nginx para dev
│   ├── nginx.docker.prod.conf# Nginx para prod (SSL)
│   ├── gunicorn.conf.py      # Config Gunicorn
│   ├── setup-ssl.sh          # Script setup SSL
│   └── portal.service        # Systemd service
│
├── templates/                 # Templates HTML
│   ├── login.html            # Portal público
│   ├── admin.html            # Painel admin
│   ├── admin_login.html      # Login admin
│   └── termos.html           # Termos de uso
│
├── static/                    # Arquivos estáticos
│   ├── css/style.css         # Estilos
│   └── js/main.js            # JavaScript
│
└── data/                      # Dados (persistente)
    ├── access_log.csv        # Registros em CSV
    ├── access_log_encrypted.json # Registros criptografados
    └── users.csv             # Usuários admin
```

### **Variáveis de Ambiente**

```bash
# Segurança
SECRET_KEY=<gerar-com-secrets>
DEBUG=False
FLASK_ENV=production

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=<senha-forte>

# Configurações
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT=1800
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
```

### **Desenvolvimento Local**

```bash
# Modo dev (hot reload)
docker-compose up

# Rebuild
docker-compose up --build

# Ver logs específicos
docker-compose logs -f app
docker-compose logs -f nginx
docker-compose logs -f redis

# Executar comandos no container
docker-compose exec app bash
docker-compose exec app python -c "import app_simple"

# Limpar tudo
docker-compose down -v
```

### **Testes**

```bash
# Rodar testes
docker-compose exec app python -m pytest

# Test de carga
ab -n 1000 -c 10 http://localhost/login

# Health check
curl http://localhost/healthz
```

---

## 🌐 Produção

### **Deploy Rápido (Ubuntu Server)**

```bash
# 1. Preparar servidor
sudo apt update && sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker $USER

# 2. Clonar e configurar
git clone https://github.com/seu-usuario/wifi-portal.git /var/www/wifi-portal
cd /var/www/wifi-portal
cp .env.prod .env.local
nano .env.local  # Configurar variáveis

# 3. Setup SSL
chmod +x deploy/setup-ssl.sh
sudo bash deploy/setup-ssl.sh seu-dominio.com admin@seu-dominio.com

# 4. Pronto!
# https://seu-dominio.com
```

Ver [DEPLOY.md](DEPLOY-NEW.md) para guia completo.

### **Manutenção**

```bash
# Atualizar aplicação
cd /var/www/wifi-portal
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/ .env.local

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Reiniciar
docker-compose -f docker-compose.prod.yml restart

# Health check
curl https://seu-dominio.com/healthz
```

---

## 🔒 Segurança

### **Checklist de Segurança**

- [ ] SECRET_KEY única e forte
- [ ] REDIS_PASSWORD configurada
- [ ] Senha admin alterada
- [ ] SSL/TLS configurado
- [ ] Firewall ativo (UFW)
- [ ] Backup automático
- [ ] Logs monitorados
- [ ] Atualizações regulares
- [ ] .env.local fora do Git

### **Boas Práticas**

1. **Nunca** commite `.env.local`
2. **Sempre** use HTTPS em produção
3. **Monitore** logs de segurança
4. **Faça backup** diário dos dados
5. **Mantenha** dependências atualizadas
6. **Teste** em staging antes de produção
7. **Use** senhas fortes e únicas

---

## 🆘 Suporte

### **Problemas Comuns**

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING-NEW.md) para soluções detalhadas.

### **Reportar Bugs**

1. Verifique [Issues existentes](https://github.com/seu-usuario/wifi-portal/issues)
2. Crie novo issue com:
   - Descrição do problema
   - Passos para reproduzir
   - Logs relevantes
   - Ambiente (dev/prod, versão)

### **Comunidade**

- 📧 Email: suporte@prefeitura.com.br
- 💬 Discord: [Link do servidor]
- 📝 Wiki: [Link da wiki]

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Ver [CONTRIBUTING.md](CONTRIBUTING-NEW.md) para diretrizes.

```bash
# Fork → Clone → Branch → Commit → Push → Pull Request
git checkout -b feature/nova-funcionalidade
git commit -m "feat: adiciona nova funcionalidade"
git push origin feature/nova-funcionalidade
```

---

## 📊 Roadmap

- [ ] Dashboard com gráficos em tempo real
- [ ] Exportação em múltiplos formatos
- [ ] Autenticação via redes sociais
- [ ] Notificações por email/SMS
- [ ] API REST para integração
- [ ] Multi-tenancy
- [ ] Dark mode

Ver [LIMITATIONS.md](LIMITATIONS-NEW.md) para detalhes.

---

## 📄 Licença

Este projeto está sob a licença MIT. Ver [LICENSE](LICENSE) para detalhes.

---

## 👥 Autores

- **Prefeitura Municipal** - Desenvolvimento inicial
- **Comunidade** - Contribuições e melhorias

Ver [contributors](https://github.com/seu-usuario/wifi-portal/graphs/contributors) para lista completa.

---

## 🙏 Agradecimentos

- Comunidade Flask
- Projeto MikroTik
- Contribuidores open source

---

<p align="center">
  Feito com ❤️ para Wi-Fi público e gratuito
</p>
