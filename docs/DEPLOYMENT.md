# 🚀 Guia de Deploy - Portal Cativo Wi-Fi

Guia completo para deploy em produção do Portal Cativo.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Deploy Rápido](#deploy-rápido)
3. [Configuração SSL](#configuração-ssl)
4. [Backup Automático](#backup-automático)
5. [Monitoramento](#monitoramento)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Pré-requisitos

### Servidor
- Ubuntu 20.04+ / Debian 11+ / Rocky Linux 8+
- 2 CPU cores mínimo
- 2GB RAM mínimo (4GB recomendado)
- 20GB disco livre
- Acesso root ou sudo

### Software
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Rede
- Porta 80 (HTTP)
- Porta 443 (HTTPS)
- Domínio configurado (para SSL)

---

## 🚀 Deploy Rápido

### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout e login para aplicar grupo docker
```

### 2. Clonar Repositório

```bash
cd /opt
sudo git clone https://github.com/sua-prefeitura/wifi-portal.git
cd wifi-portal
sudo chown -R $USER:$USER .
```

### 3. Configurar Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.prod.example .env.local

# Gerar credenciais seguras
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"

# Editar arquivo
nano .env.local
```

**Configurar no .env.local:**
```bash
# Flask
SECRET_KEY=<chave-gerada-acima>
FLASK_ENV=production

# Database
DATABASE_URL=postgresql://portal_user:<senha-forte>@postgres:5432/wifi_portal

# Encryption
ENCRYPTION_KEY=<chave-fernet-gerada-acima>

# Admin
ADMIN_DEFAULT_PASSWORD=<senha-forte-admin>

# Email (opcional - para recuperação de senha)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_FROM=noreply@prefeitura.gov.br

# Rate Limiting
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URL=redis://redis:6379/0
```

### 4. Iniciar Sistema

```bash
# Build e iniciar
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar status
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Aplicar Migrations

```bash
# Aguardar containers iniciarem
sleep 30

# Aplicar migrations
docker-compose -f docker-compose.prod.yml exec app flask db upgrade

# Verificar
docker-compose -f docker-compose.prod.yml exec app flask db current
```

### 6. Teste Inicial

```bash
# Health check
curl http://localhost/health

# Acessar admin
# http://seu-servidor/admin/login
# Usuario: admin
# Senha: <ADMIN_DEFAULT_PASSWORD do .env.local>
```

---

## 🔒 Configuração SSL

### Opção 1: Let's Encrypt (Recomendado)

```bash
# Executar script automático
chmod +x deploy/setup-ssl.sh
sudo ./deploy/setup-ssl.sh wifi.prefeitura.com.br

# Renovação automática (já configurada no script)
# Certbot renova automaticamente 30 dias antes do vencimento
```

### Opção 2: Certificado Próprio

```bash
# Copiar certificados para deploy/ssl/
sudo cp seu-cert.crt deploy/ssl/cert.pem
sudo cp sua-chave.key deploy/ssl/privkey.pem
sudo cp chain.crt deploy/ssl/chain.pem

# Ajustar permissões
sudo chmod 644 deploy/ssl/*.pem

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Verificar SSL

```bash
# Testar HTTPS
curl https://wifi.prefeitura.com.br/health

# Verificar certificado
openssl s_client -connect wifi.prefeitura.com.br:443 -servername wifi.prefeitura.com.br
```

---

## 💾 Backup Automático

### Configurar Backup Diário

```bash
# Dar permissão aos scripts
chmod +x scripts/backup/*.sh

# Criar diretório de backups
sudo mkdir -p /backups
sudo chown $USER:$USER /backups

# Testar backup manualmente
./scripts/backup/backup_postgres.sh

# Verificar arquivo criado
ls -lh /backups/
```

### Agendar com Cron

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 02:00)
0 2 * * * /opt/wifi-portal/scripts/backup/backup_postgres.sh >> /var/log/wifi-backup.log 2>&1

# Adicionar linha (limpeza de logs antigos - semanal)
0 3 * * 0 /opt/wifi-portal/scripts/backup/cleanup-old-backups.sh >> /var/log/wifi-backup.log 2>&1
```

### Testar Restore

```bash
# Listar backups disponíveis
ls -lh /backups/

# Restaurar backup
./scripts/backup/restore_postgres.sh /backups/wifi_portal_20260203_020000.sql.gz

# Confirmar restauração
docker-compose -f docker-compose.prod.yml exec postgres psql -U portal_user -d wifi_portal -c "SELECT COUNT(*) FROM access_logs;"
```

---

## 📊 Monitoramento

### Health Checks

```bash
# Endpoint de saúde
curl http://localhost/health

# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f app

# Logs de erro apenas
docker-compose -f docker-compose.prod.yml logs app | grep ERROR
```

### Métricas

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h
docker system df

# Conexões PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U portal_user -d wifi_portal -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Cache Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO stats
```

### Logs

```bash
# Logs da aplicação
docker-compose -f docker-compose.prod.yml logs -f app

# Logs do Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Logs do PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f postgres

# Logs de segurança (dentro do container)
docker-compose -f docker-compose.prod.yml exec app tail -f logs/security.log
```

---

## 🔧 Manutenção

### Atualizar Sistema

```bash
# 1. Fazer backup
./scripts/backup/backup_postgres.sh

# 2. Parar containers
docker-compose -f docker-compose.prod.yml down

# 3. Atualizar código
git pull origin main

# 4. Rebuild e reiniciar
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Aplicar migrations
docker-compose -f docker-compose.prod.yml exec app flask db upgrade

# 6. Verificar
curl http://localhost/health
```

### Limpar Sistema

```bash
# Limpar containers parados
docker container prune -f

# Limpar imagens não utilizadas
docker image prune -a -f

# Limpar volumes órfãos
docker volume prune -f

# Limpar logs antigos (>30 dias)
find /var/lib/docker/containers -name "*.log" -mtime +30 -delete
```

### Restart de Serviços

```bash
# Restart app apenas
docker-compose -f docker-compose.prod.yml restart app

# Restart nginx apenas
docker-compose -f docker-compose.prod.yml restart nginx

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres

# Restart completo
docker-compose -f docker-compose.prod.yml restart
```

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose -f docker-compose.prod.yml logs app

# Verificar configuração
docker-compose -f docker-compose.prod.yml config

# Rebuild forçado
docker-compose -f docker-compose.prod.yml build --no-cache app
docker-compose -f docker-compose.prod.yml up -d app
```

### Erro de conexão PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker-compose -f docker-compose.prod.yml ps postgres

# Testar conexão
docker-compose -f docker-compose.prod.yml exec postgres psql -U portal_user -d wifi_portal

# Ver logs do PostgreSQL
docker-compose -f docker-compose.prod.yml logs postgres

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml exec app printenv | grep DATABASE
```

### Erro 500 na aplicação

```bash
# Ver logs de erro
docker-compose -f docker-compose.prod.yml logs app | grep -i error

# Verificar migrations
docker-compose -f docker-compose.prod.yml exec app flask db current

# Testar manualmente
docker-compose -f docker-compose.prod.yml exec app python -c "
from app_simple import app, db
with app.app_context():
    print('DB connected!', db.engine.url)
"
```

### Performance lenta

```bash
# Verificar uso de recursos
docker stats

# Verificar queries lentas PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U portal_user -d wifi_portal -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Limpar cache Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Vacuum PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres vacuumdb -U portal_user -d wifi_portal -v -f
```

---

## 🔐 Segurança em Produção

### Firewall

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Verificar
sudo ufw status
```

### Fail2Ban (Opcional)

```bash
# Instalar
sudo apt install fail2ban -y

# Criar configuração para nginx
sudo nano /etc/fail2ban/jail.d/nginx.conf
```

```ini
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600
```

### Auditar Logs

```bash
# Verificar tentativas de login falhadas
docker-compose -f docker-compose.prod.yml exec app grep "LOGIN_FAILED" logs/security.log

# Verificar IPs bloqueados por rate limit
docker-compose -f docker-compose.prod.yml exec app grep "RATE_LIMIT_EXCEEDED" logs/security.log

# Exportar relatório de segurança
docker-compose -f docker-compose.prod.yml exec app python -c "
from app_simple import app
from app.security import generate_security_report
with app.app_context():
    print(generate_security_report())
" > security-report.txt
```

---

## 📞 Suporte

Ver [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) para mais problemas comuns.

**Issues:** https://github.com/sua-prefeitura/wifi-portal/issues
