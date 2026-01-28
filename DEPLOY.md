# Guia de Deploy Seguro - Portal Cautivo

Este guia detalha como implantar o Portal Cautivo Flask em ambiente de produção com todas as configurações de segurança.

## 🚀 Pré-requisitos

- Python 3.8+
- OpenSSL (para HTTPS)
- Permissões de administrador (para configurações de segurança)

## 📦 Instalação

### 1. Clonar e Configurar

```bash
# Clone o repositório
git clone <seu-repositorio>
cd wifi-portal

# Instale dependências
pip install -r requirements.txt

# Execute o script de configuração de segurança
python setup_security.py
```

### 2. Configurar Variáveis de Ambiente

O script `setup_security.py` cria automaticamente o arquivo `.env.local` com configurações seguras. Para produção, ajuste:

```bash
# Edite o arquivo .env.local
nano .env.local

# Altere estas configurações críticas:
SECRET_KEY=sua-chave-secreta-muito-forte-aqui
DEBUG=False
ALLOWED_HOSTS=seuservidor.com,portal.para.br
```

### 3. Segurança de Arquivos

```bash
# Defina permissões seguras
chmod 750 data/
chmod 640 data/*.csv
chmod 600 ssl/*.key
chmod 600 .env.local

# No Linux/Unix, proteja ainda mais
sudo chown -R www-data:www-data data/
sudo chown -R www-data:www-data ssl/
```

## 🔒 Configurações de Segurança

### HTTPS/SSL

#### Opção 1: Certificado Auto-assinado (Desenvolvimento)
```bash
# O script setup_security.py já gera certificados
# Para usar: python run_secure.py
```

#### Opção 2: Certificado Let's Encrypt (Produção)
```bash
# Instale certbot
sudo apt install certbot

# Obtenha certificado
sudo certbot certonly --standalone -d seu-dominio.com

# Atualize o .env.local
SSL_CERT_PATH=/etc/letsencrypt/live/seu-dominio.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/seu-dominio.com/privkey.pem
```

### Firewall

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (se usar)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 🚀 Deploy em Produção

### Opção 1: Gunicorn + Nginx (Recomendado)

#### 1. Instalar Gunicorn
```bash
pip install gunicorn
```

#### 2. Configurar Gunicorn
```bash
# Crie arquivo gunicorn.conf.py
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
EOF
```

#### 3. Configurar Nginx
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /path/to/ssl/portal_cautivo.crt;
    ssl_certificate_key /path/to/ssl/portal_cautivo.key;

    # Configurações de segurança
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 4. Iniciar Serviços
```bash
# Inicie Gunicorn
gunicorn -c gunicorn.conf.py app_simple:app

# Reinicie Nginx
sudo systemctl restart nginx
```

### Opção 2: Systemd Service

#### 1. Criar Service
```bash
sudo nano /etc/systemd/system/portal-cautivo.service
```

```ini
[Unit]
Description=Portal Cautivo Flask
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/wifi-portal
Environment="PATH=/path/to/wifi-portal/venv/bin"
ExecStart=/path/to/wifi-portal/venv/bin/python run_secure.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 2. Ativar Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable portal-cautivo
sudo systemctl start portal-cautivo
```

## 🔐 Configurações do MikroTik

### Hotspot Configuration
```bash
# Configure o hotspot
/ip hotspot profile set [profile-name] \
    login-url=https://seu-dominio.com/login \
    use-radius=no

# Configure DNS para redirecionamento
/ip dns static add \
    name=portal.seu-dominio.com \
    address=seu-ip-publico
```

### Firewall Rules
```bash
# Permitir tráfego para o portal
/ip firewall filter add \
    chain=forward \
    action=accept \
    dst-address=seu-ip-servidor \
    protocol=tcp \
    dst-port=443

# Bloquear tráfego direto (forçar hotspot)
/ip firewall filter add \
    chain=forward \
    action=drop \
    out-interface=hotspot-interface \
    connection-state=new
```

## 📊 Monitoramento

### Logs
```bash
# Monitorar logs em tempo real
tail -f logs/app.log
tail -f logs/security.log
tail -f logs/security_events.log

# Analisar eventos de segurança
grep "SECURITY" logs/security_events.log
```

### Métricas de Performance
```bash
# Monitorar uso de memória e CPU
htop

# Monitorar conexões
netstat -tulpn | grep :5000

# Testar performance
ab -n 1000 -c 100 https://seu-dominio.com/login
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Permissão
```bash
# Solução
sudo chown -R www-data:www-data /path/to/wifi-portal
sudo chmod -R 755 /path/to/wifi-portal
```

#### 2. Erro de SSL
```bash
# Verifique certificado
openssl x509 -in ssl/portal_cautivo.crt -text -noout

# Regenere certificado se necessário
python setup_security.py
```

#### 3. Erro de Banco de Dados
```bash
# Verifique arquivos CSV
ls -la data/
head -5 data/users.csv
```

#### 4. Erro de Conexão
```bash
# Teste conexão local
curl -k https://localhost:5000/login

# Teste conexão externa
curl -k https://seu-dominio.com/login
```

### Comandos Úteis

```bash
# Verificar status da aplicação
sudo systemctl status portal-cautivo

# Reiniciar aplicação
sudo systemctl restart portal-cautivo

# Ver logs do systemd
sudo journalctl -u portal-cautivo -f

# Testar configuração
python -c "from app_simple import app; print('OK')"
```

## 🛡️ Boas Práticas de Segurança

### 1. Atualizações
```bash
# Mantenha o sistema atualizado
sudo apt update && sudo apt upgrade -y

# Atualize dependências Python
pip install --upgrade -r requirements.txt
```

### 2. Backups
```bash
# Script de backup automatizado
python backup.py

# Backup manual
tar -czf backup_$(date +%Y%m%d).tar.gz data/ ssl/ logs/
```

### 3. Monitoramento de Segurança
```bash
# Monitorar tentativas de login
grep "admin_login_failed" logs/security_events.log

# Monitorar acessos suspeitos
grep "suspicious" logs/security_events.log
```

### 4. Auditoria
```bash
# Verifique integridade dos arquivos
find . -name "*.py" -exec md5sum {} \; > checksums.txt

# Compare com versão anterior
diff checksums.txt checksums.old.txt
```

## 📈 Escalabilidade

### Load Balancing
Para alto tráfego, considere:
- Múltiplos servidores Flask
- Load balancer (HAProxy, Nginx)
- Banco de dados PostgreSQL
- Redis para cache e sessões

### Cache
```bash
# Instalar Redis
sudo apt install redis-server

# Configurar cache na aplicação
# (Implementar no futuro)
```

## 🆘 Suporte

### Documentação
- [README.md](README.md) - Documentação principal
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribuições
- [security.py](security.py) - Documentação de segurança

### Logs de Erro
Todos os erros são registrados em:
- `logs/app.log` - Logs da aplicação
- `logs/security.log` - Logs de segurança
- `logs/security_events.log` - Eventos de segurança

### Comunicação
Para suporte:
1. Verifique os logs
2. Teste a aplicação localmente
3. Consulte este guia
4. Abra issue no repositório

---

**⚠️ Atenção**: Este guia assume conhecimentos básicos de administração de sistemas Linux e redes. Sempre teste em ambiente de desenvolvimento antes de aplicar em produção.