# Portal Cautivo Flask - Wi-Fi Público Municipal

Aplicação backend Flask para portal cativo integrado ao MikroTik Hotspot, destinada a Wi-Fi público municipal.

## 🚀 Funcionalidades

- ✅ **Portal cativo** com formulário de cadastro
- ✅ **Integração MikroTik** (captura de parâmetros IP, MAC, link-orig)
- ✅ **Registro de acessos** em CSV (sem banco de dados)
- ✅ **Validação de formulário** (nome, telefone, termos de uso)
- ✅ **Proteção CSRF** e sanitização de inputs
- ✅ **Design responsivo** para dispositivos móveis
- ✅ **Painel administrativo** para visualização de registros
- ✅ **Termos de uso** integrados
- ✅ **Login administrativo** seguro
- ✅ **Recuperação de senha** por email
- ✅ **Edição de perfil** administrativo

## 📁 Estrutura de Arquivos

```
loginwifi/
├── app_simple.py           # Aplicação principal Flask
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── .gitignore             # Arquivos ignorados pelo Git
├── .env                   # Variáveis de ambiente (exemplo)
├── LICENSE                # Licença MIT
├── CONTRIBUTING.md        # Diretrizes de contribuição
├── data/                  # Dados
│   ├── access_log.csv     # Registros de acesso
│   └── users.csv          # Usuários administrativos
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── style.css      # Estilos responsivos
│   └── js/
│       └── main.js        # Scripts principais
└── templates/             # Templates HTML
    ├── login.html         # Página principal do portal
    ├── termos.html        # Página de termos de uso
    ├── admin.html         # Página de administração
    ├── admin_login.html   # Login administrativo
    ├── admin_profile.html # Perfil administrativo
    ├── reset_password.html # Recuperação de senha
    └── reset_form.html    # Formulário de redefinição
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

- **Hash de senhas**: Utiliza Werkzeug para hash seguro de senhas
- **Sessões seguras**: Chave secreta configurável
- **CSRF Protection**: Proteção contra ataques CSRF
- **Input Sanitization**: Todos os inputs são sanitizados para prevenir XSS
- **Validação robusta**: Validação server-side de todos os campos
- **Redirecionamento seguro**: Redirecionamento automático para login quando não autenticado

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

## 🚀 Produção

### HTTPS

Para uso em produção com HTTPS:

1. Configure um proxy reverso (nginx, Apache)
2. Configure certificado SSL/TLS
3. Atualize a URL no MikroTik para usar HTTPS

### Variáveis de Ambiente

Configure variáveis de ambiente via `.env.local`:

```bash
SECRET_KEY=sua-secret-key-segura
DEBUG=False
CSV_FILE=data/access_log.csv
```

### Segurança em Produção

1. **Altere credenciais padrão**:
   - Modifique usuário e senha padrão
   - Gere uma nova SECRET_KEY

2. **Proteja arquivos sensíveis**:
   - Configure permissões adequadas
   - Não exponha diretório `data/`

3. **Monitoramento**:
   - Configure logs adequados
   - Monitore acesso ao painel admin

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

## 🐛 Troubleshooting

### Erro de permissão no CSV

Certifique-se que o diretório `data/` tem permissão de escrita:

```bash
chmod 755 data/
```

### Conexão com MikroTik

Verifique:
1. O MikroTik pode acessar o servidor Flask
2. A porta 5000 está aberta no firewall
3. A URL de login está correta no profile do hotspot

### Depuração

Para habilitar modo debug:

```python
# Em app_simple.py, altere a última linha:
app.run(host='0.0.0.0', port=5000, debug=True)
```

### Problemas comuns

**"Nenhum registro encontrado"**
- Verifique se o arquivo `data/access_log.csv` existe
- Confira as permissões de escrita

**"Usuário ou senha incorretos"**
- Verifique credenciais padrão: admin/admin123
- Confira se o arquivo `data/users.csv` foi criado

**"Token inválido ou expirado"**
- Tokens de recuperação expiram em 1 hora
- Gere um novo token de recuperação

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