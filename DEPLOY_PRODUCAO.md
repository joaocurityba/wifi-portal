# 🚀 Guia Rápido de Deploy em Produção

## ⚠️ Checklist PRÉ-DEPLOY

### 1. Preparar Ambiente de Produção

```bash
# No servidor de produção
cd /opt
git clone <seu-repositorio> wifi-portal
cd wifi-portal
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.prod.example .env.prod

# Gerar credenciais fortes
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))"

# Editar .env.prod com as credenciais geradas
nano .env.prod
```

**IMPORTANTE:** Substituir TODOS os valores `TROCAR_POR_*`

### 3. Configurar SSL/TLS (Let's Encrypt)

```bash
# Criar diretório para certbot
mkdir -p certbot/www

# Obter certificado (substitua pelo seu domínio)
docker-compose -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@prefeitura.com.br \
  --agree-tos \
  --no-eff-email \
  -d wifi.prefeitura.com.br
```

### 4. Ajustar docker-compose.prod.yml

Verificar se `.env.prod` está sendo usado:

```yaml
# docker-compose.prod.yml
services:
  app:
    env_file:
      - .env.prod  # ← Confirmar que aponta para .env.prod
```

### 5. Iniciar Containers

```bash
# Build e start
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar status
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f app
```

### 6. Aplicar Migrations

```bash
# Aguardar containers iniciarem (20-30 segundos)
sleep 30

# Aplicar migrations
docker-compose -f docker-compose.prod.yml exec app flask db upgrade

# Criar usuário admin
docker-compose -f docker-compose.prod.yml exec app python -c "
from app_simple import app, db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        username='admin',
        password_hash=generate_password_hash('TROCAR_ESTA_SENHA'),
        email='admin@prefeitura.com.br'
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin criado!')
"
```

### 7. Configurar Backup Automático

```bash
# Copiar script de backup
chmod +x backup_postgres.sh

# Criar diretório de backups
mkdir -p /backups

# Adicionar ao cron (diariamente às 02:00)
crontab -e

# Adicionar linha:
0 2 * * * /opt/wifi-portal/backup_postgres.sh >> /var/log/backup-wifi-portal.log 2>&1
```

### 8. Configurar Firewall

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Ou iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 9. Verificação Final

```bash
# Health check
curl http://wifi.prefeitura.com.br/healthz

# SSL (após configurar)
curl https://wifi.prefeitura.com.br/healthz

# Logs
docker-compose -f docker-compose.prod.yml logs --tail=100 app | grep ERROR
```

---

## 🔍 Verificações Pós-Deploy

### Container Status
```bash
docker-compose -f docker-compose.prod.yml ps

# Todos devem estar "Up" e "healthy"
```

### Database
```bash
# Conectar ao PostgreSQL
docker exec -it wifi-portal-postgres psql -U portal_user -d wifi_portal

# Verificar tabelas
\dt

# Verificar admin
SELECT username, email FROM users;

# Sair
\q
```

### Redis
```bash
# Testar conexão (use a senha do .env.prod)
docker exec wifi-portal-redis redis-cli -a SUA_SENHA_REDIS ping

# Ver chaves
docker exec wifi-portal-redis redis-cli -a SUA_SENHA_REDIS --no-auth-warning KEYS "*"
```

### Nginx
```bash
# Testar config
docker exec wifi-portal-nginx nginx -t

# Recarregar (se fizer mudanças)
docker exec wifi-portal-nginx nginx -s reload
```

---

## 🔒 Segurança Pós-Deploy

### 1. Trocar Senha do Admin
```
Acesse: https://wifi.prefeitura.com.br/admin/login
Login: admin
Senha: (a que você definiu)

Depois: Admin → Alterar Senha
```

### 2. Verificar Credenciais
```bash
# Confirmar que .env.prod NÃO está no Git
git status | grep .env.prod  # Não deve aparecer

# Confirmar permissões
chmod 600 .env.prod
```

### 3. Monitoramento
```bash
# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Ver apenas erros
docker-compose -f docker-compose.prod.yml logs | grep -i error
```

---

## 🔄 Atualizações Futuras

```bash
# Pull código atualizado
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml up -d --build

# Aplicar migrations (se houver)
docker-compose -f docker-compose.prod.yml exec app flask db upgrade

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f app
```

---

## 🆘 Troubleshooting

### Container não inicia
```bash
# Ver logs completos
docker-compose -f docker-compose.prod.yml logs app

# Ver logs do sistema
journalctl -u docker.service -n 100
```

### Banco de dados com erro
```bash
# Verificar conexão
docker exec wifi-portal-postgres pg_isready -U portal_user

# Ver logs
docker logs wifi-portal-postgres
```

### Redis não conecta
```bash
# Verificar se está rodando
docker exec wifi-portal-redis redis-cli -a SUA_SENHA ping

# Ver logs
docker logs wifi-portal-redis
```

### SSL não funciona
```bash
# Verificar certificados
ls -la /etc/letsencrypt/live/wifi.prefeitura.com.br/

# Renovar manualmente
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

---

## 📞 Suporte

**Logs importantes:**
- Aplicação: `/opt/wifi-portal/logs/`
- Nginx: `/opt/wifi-portal/logs/nginx/`
- Backups: `/backups/`

**Comandos úteis:**
```bash
# Status geral
docker-compose -f docker-compose.prod.yml ps

# Restart serviço
docker-compose -f docker-compose.prod.yml restart app

# Restart completo
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Backup manual
/opt/wifi-portal/backup_postgres.sh
```
