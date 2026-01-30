# Portal Cautivo Flask - Wi-Fi Público Municipal

Aplicação backend Flask para portal cativo integrado ao MikroTik Hotspot, destinada a Wi-Fi público municipal.

## 🚀 Funcionalidades

- ✅ **Portal cativo** com formulário de cadastro
- ✅ **Integração MikroTik** (captura de parâmetros IP, MAC, link-orig)
- ✅ **Registro de acessos** em CSV com criptografia de dados sensíveis
- ✅ **Validação de formulário** (nome, telefone, termos de uso, validação de idade)
- ✅ **Proteção CSRF** em painel admin e portal público
- ✅ **Design responsivo** para dispositivos móveis
- ✅ **Painel administrativo** seguro para visualização e busca de registros
- ✅ **Termos de uso** integrados
- ✅ **Login administrativo** com rate limiting e proteção
- ✅ **Edição de perfil** administrativo
- ✅ **Recuperação de senha** com tokens de reset
- ✅ **Rate limiting** integrado (com Redis opcional)
- ✅ **Criptografia avançada** (Fernet + PBKDF2) de dados sensíveis
- ✅ **Logs de segurança** e auditoria
- ✅ **Docker Compose** para deployment rápido

**Nota**: Ver [LIMITATIONS.md](LIMITATIONS.md) para limitações conhecidas e [DEPLOY.md](DEPLOY.md) para deployment em produção.

## 📁 Estrutura de Arquivos

```
wifi-portal-teste/
├── app_simple.py           # Aplicação principal Flask
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── .gitignore             # Arquivos ignorados pelo Git
├── .env.local             # Variáveis de ambiente (não commitar!)
├── .env.template          # Template de variáveis de ambiente
├── .env_example           # Exemplo antigo (não use)
├── LICENSE                # Licença MIT
├── CONTRIBUTING.md        # Diretrizes de contribuição
├── data/                  # Dados
│   ├── access_log.csv     # Registros de acesso (CSV legível)
│   ├── access_log_encrypted.json # Registros com criptografia
│   └── users.csv          # Usuários administrativos (hash de senha)
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── style.css      # Estilos responsivos
│   └── js/
│       └── main.js        # Scripts principais
├── templates/             # Templates HTML
│   ├── login.html         # Página principal do portal
│   ├── termos.html        # Página de termos de uso
│   ├── admin.html         # Página de administração
│   ├── admin_login.html   # Login administrativo
│   ├── admin_profile.html # Perfil administrativo
│   ├── reset_password.html # Recuperação de senha
│   └── reset_form.html    # Formulário de redefinição
├── deploy/                # Arquivos de deploy
│   ├── gunicorn.conf.py   # Configuração Gunicorn
│   ├── nginx.portal_cautivo.conf # Configuração Nginx
│   ├── portal.service     # Systemd service
│   ├── logrotate.conf     # Rotação de logs
│   └── checklist.sh       # Script de verificação
├── logs/                  # Logs da aplicação
└── security.py            # Módulo de segurança
```

## 🛠️ Instalação e Configuração

### Requisitos

#### Opção 1: Execução Direta (Linux/Mac/Windows)
- Python 3.9+
- pip
- Redis (opcional, recomendado para produção)

#### Opção 2: Docker Compose (Recomendado)
- Docker 20.10+
- Docker Compose 1.29+

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar ambiente

```bash
# Copiar template de variáveis de ambiente
cp .env.template .env.local

# IMPORTANTE: Editar e configurar valores para seu ambiente
nano .env.local
```

**Variáveis essenciais em `.env.local`:**
- `SECRET_KEY` - Chave secreta única (gerar com: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `ALLOWED_HOSTS` - Seu domínio ou IP (ex: `seu-dominio.com` ou `192.168.1.100`)
- `DEBUG` - `False` em produção, `True` em desenvolvimento
- `ADMIN_PASSWORD` - Senha do usuário admin padrão (alterar após primeiro login)

### 3. Executar a aplicação

```bash
python app_simple.py
```

A aplicação será iniciada em `http://localhost:5000`

## 🔧 Configuração no MikroTik Hotspot

### Configurar o Hotspot

No MikroTik, configure o hotspot com a URL de login:

```bash
/ip hotspot profile set [profile-name] login-url=http://seuservidor:5000/login
```

Ou via WinBox:
1. Acesse IP > Hotspot
2. Selecione seu profile
3. Configure "Login URL" como: `http://seuservidor:5000/login`

### Parâmetros enviados pelo MikroTik

O MikroTik envia automaticamente os seguintes parâmetros:
- `ip` - Endereço IP do cliente
- `mac` - Endereço MAC do cliente  
- `link-orig` - URL original que o cliente tentou acessar

## 📱 Uso

### Portal de Login Público

1. Usuário conecta-se à rede Wi-Fi
2. É redirecionado automaticamente para o portal cativo
3. Preenche os campos obrigatórios:
   - Nome completo
   - Email
   - Data de nascimento
   - Telefone celular
   - Aceita os termos de uso
4. Clica em "Acessar Internet"
5. É redirecionado para a URL original ou Google

### Área Administrativa

#### Login Administrativo
- **URL**: `http://localhost:5000/admin/login`
- **Usuário padrão**: `admin`
- **Senha padrão**: `admin123`

#### Páginas Administrativas
- **Painel**: `http://localhost:5000/admin` - Visualização de registros
- **Perfil**: `http://localhost:5000/admin/profile` - Edição de perfil
- **Recuperação**: `http://localhost:5000/admin/reset-password` - Recuperação de senha

## � Email e Recuperação de Senha

A funcionalidade de recuperação de senha pode enviar emails via SMTP (opcional).

**Se quiser ativar email SMTP, configure em `.env.local`:**

```bash
# Gmail (exemplo)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app  # Use "Senha de app" se 2FA ativado
SMTP_USE_TLS=True
FROM_EMAIL=seu-email@gmail.com
FROM_NAME=Wi-Fi Portal Admin
```

**Obs:** Se não configurar SMTP, a recuperação de senha mostrará o link na tela (apenas para desenvolvimento).

---

## 🔒 Segurança

**Features implementadas:**
- ✅ **Criptografia Fernet** (PBKDF2-SHA256) para dados sensíveis (nome, email, telefone, data nascimento)
- ✅ **Hash de senhas** com Werkzeug (PBKDF2) 
- ✅ **Proteção CSRF** em todas as rotas POST
- ✅ **Rate limiting** (5 tentativas/hora admin, 100/min global)
- ✅ **Headers de segurança** (HSTS, CSP, X-Frame-Options, etc)
- ✅ **Validação server-side** de todos os inputs
- ✅ **Sanitização HTML** para prevenir XSS
- ✅ **File-locking atômico** para integridade de dados (concurrent access)
- ✅ **Logs de segurança** com audit trail

⚠️ **Veja [LIMITATIONS.md](LIMITATIONS.md)** para features não implementadas e recomendações de escala

## 🎨 Personalização

### Estilos

Edite `static/css/style.css` para alterar o design do portal.

### Textos

Edite os templates HTML em `templates/` para alterar textos e mensagens.

### Validação

Modifique as funções de validação em `app_simple.py`:
- `validate_phone()` - Validação de telefone
- `validate_email()` - Validação de email
- `validate_birth_date()` - Validação de data de nascimento
- `sanitize_input()` - Sanitização de inputs

## � Quick Start com Docker Compose

Para rodar a aplicação rapidamente com Docker (inclui Redis):

```bash
# Buildar e iniciar
docker-compose up -d

# A aplicação estará em http://localhost:5000
# Redis estará em localhost:6379

# Ver logs
docker-compose logs -f app

# Parar
docker-compose down

# Limpar volumes (dados)
docker-compose down -v
```

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **MUDE IMEDIATAMENTE após primeiro login!**

---

## 🚀 Deploy em Produção (Ubuntu Server)

**LEIA COMPLETAMENTE**: Este é o guia essencial para deployar em produção seguro.

### Opção 1: Deploy Manual (Recomendado)

Para instruções detalhadas passo-a-passo:

👉 **[DEPLOY.md](DEPLOY.md)** - Guia completo (15 passos, ~45-60 minutos)

**O que será configurado:**
- Python 3.9+ com virtual environment
- Gunicorn (porta 8003) como WSGI application server
- Nginx como reverse proxy + SSL/TLS termination
- Let's Encrypt para certificados HTTPS automáticos
- Systemd service para auto-restart
- Logrotate para rotação de logs (90 dias)
- Redis para rate limiting distribuído (opcional)
- UFW firewall configurado

**Pré-requisitos:**
- Ubuntu 20.04 ou superior
- Domínio DNS apontando para o servidor (ou IP público)
- Acesso SSH com permissão `sudo`
- ~2GB RAM mínimo
- ~5GB disco mínimo

### Opção 2: Deploy com Docker em Produção

```bash
# Build da imagem
docker build -t wifi-portal:latest .

# Push para registry (DockerHub, ECR, etc)
docker push seu-registry/wifi-portal:latest

# Deploy em seu orquestrador:
# - Docker Swarm
# - Kubernetes
# - AWS ECS
# - DigitalOcean App Platform
# - etc
```

### Opção 3: Plataformas Gerenciadas

- **Railway.app**, **Render**, **Heroku**: `git push` automático
- **AWS EC2**: Usar manual deployment
- **Azure App Service**: Suporta containers
- **DigitalOcean**: App Platform com Docker

**Qualquer que seja a opção:**
1. ✅ Altere a senha admin padrão imediatamente
2. ✅ Gere SECRET_KEY e ENCRYPTION_SALT únicos
3. ✅ Configure HTTPS/SSL
4. ✅ Ative rate limiting (com Redis se possível)
5. ✅ Configure backups automáticos dos dados

## 📊 Dados e Registros

### Formato do CSV

Os registros são armazenados em CSV com os seguintes campos:
- `nome` - Nome completo do usuário
- `telefone` - Telefone celular
- `ip` - Endereço IP do cliente
- `mac` - Endereço MAC do cliente
- `user_agent` - User agent do navegador
- `data` - Data do acesso (YYYY-MM-DD)
- `hora` - Hora do acesso (HH:MM:SS)
- `email` - Email do usuário
- `data_nascimento` - Data de nascimento

### Backup

Para backup dos dados:

```bash
# Copie o arquivo de registros
cp data/access_log.csv backup/access_log_$(date +%Y%m%d).csv

# Copie o arquivo de usuários
cp data/users.csv backup/users_$(date +%Y%m%d).csv
```

## 🆘 Troubleshooting

Para soluções de problemas comuns em deployment:

👉 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Guia de diagnóstico e resolução

**Problemas cobertos:**
- Systemd service não inicia
- Nginx retorna 502 Bad Gateway
- SSL certificate errors
- Permission denied em data/logs
- Logs não são criados
- Aplicação travando/lenta
- E muito mais...

**Desenvolvimento local:**

```bash
# Teste rápido
python3 -c "from wsgi import app; print(app)"

# Rodar localmente (desenvolvimento apenas)
python app_simple.py
# Acessa http://localhost:5000
```

## 🧪 Testes

### Testes de redirecionamento

```bash
# Teste o redirecionamento automático
python test_redirect.py
```

### Testes de integração

```bash
# Teste a aplicação completa
python test_portal.py
```

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para mais informações.

### Como contribuir

1. Fork do projeto
2. Crie uma branch: `git checkout -b feature/nome-feature`
3. Faça commit das suas alterações: `git commit -m 'Adiciona feature X'`
4. Push para a branch: `git push origin feature/nome-feature`
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- Comunidade Flask
- Equipe do MikroTik
- Contribuidores e testadores

---

**Desenvolvido para Wi-Fi público municipal**  
**Versão**: 2.0 (Criptografia avançada, Docker, Rate limiting com Redis)  
**Última atualização**: Janeiro 2026  
**Status**: Pronto para produção