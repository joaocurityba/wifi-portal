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
- ✅ **Recuperação de senha** via email SMTP
- ✅ **Rate limiting** com Redis (opcional)
- ✅ **Criptografia** de dados sensíveis
- ✅ **Logs** avançados e segurança

**Nota**: Ver [LIMITATIONS.md](LIMITATIONS.md) para limitações conhecidas e [DEPLOY.md](DEPLOY.md) para deployment em produção.

## 📁 Estrutura de Arquivos

```
wifi-portal-teste/
├── app_simple.py           # Aplicação principal Flask
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── .gitignore             # Arquivos ignorados pelo Git
├── .env.local             # Variáveis de ambiente (configurado)
├── .env_example           # Exemplo de variáveis de ambiente
├── LICENSE                # Licença MIT
├── CONTRIBUTING.md        # Diretrizes de contribuição
├── data/                  # Dados
│   ├── access_log.csv     # Registros de acesso
│   ├── access_log_encrypted.json # Registros criptografados
│   └── users.csv          # Usuários administrativos
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

- Python 3.8+
- pip

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar ambiente

```bash
# Copie o arquivo de exemplo
cp .env .env.local

# Edite as variáveis de ambiente conforme necessário
# (opcional para desenvolvimento)
```

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

## 🔒 Segurança

- **Criptografia de PII**: Nome, email, telefone, data nascimento são criptografados com Fernet (PBKDF2)
- **Hash de senhas**: Utiliza Werkzeug PBKDF2 para hash seguro de senhas
- **Sessões seguras**: Chave secreta única por ambiente, cookies HTTP-only
- **CSRF Protection**: Tokens CSRF em painel admin (em desenvolvimento para formulário público)
- **Input Sanitization**: Sanitização de todos os inputs para prevenir XSS
- **Rate Limiting**: Limite de 5 tentativas/hora para admin login, 100/min global
- **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, CSP
- **File Locking**: Atomic writes para integridade de dados em concurrent access
- **Validação robusta**: Server-side validation de email, telefone, data de nascimento

⚠️ **Veja [LIMITATIONS.md](LIMITATIONS.md)** para features incompletas (email, CSRF no formulário público, etc)

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

## 🚀 Deploy em Produção

Para instruções detalhadas de deployment em Ubuntu 20.04+ com Gunicorn, Nginx, Systemd e Let's Encrypt, ver:

👉 **[DEPLOY.md](DEPLOY.md)** - Guia completo de deploy manual (15 passos)

**Quick Summary:**
- Python 3.9+ + venv
- Gunicorn (4 workers) + Nginx reverse proxy
- Systemd service com auto-restart
- Let's Encrypt para SSL/TLS
- Logrotate (90 dias de retenção)
- File-locking atomático para integridade de dados

**Pré-requisitos:**
- Servidor Ubuntu 20.04+
- Domínio ou IP público
- Acesso SSH com sudo

**Tempo estimado:** 45-60 minutos

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
**Versão**: 1.0.0  
**Última atualização**: Janeiro 2025