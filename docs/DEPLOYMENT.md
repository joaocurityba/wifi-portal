# 🚀 Deploy em Produção

Runbook operacional para subir o Portal Cativo em produção usando Docker.

---

## 1) Pré-requisitos

### Infra
- Linux com acesso root/sudo
- 2 vCPU / 2 GB RAM (mínimo)
- DNS do domínio apontando para o IP público do servidor
- Portas abertas: `80/tcp` e `443/tcp`

### Software
- Docker 20.10+
- Docker Compose plugin (`docker compose`) ou `docker-compose`
- Git

---

## 2) Preparação do servidor

Exemplo Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Faça logout/login após adicionar seu usuário ao grupo `docker`.

---

## 3) Checkout do projeto

```bash
cd /opt
sudo git clone https://github.com/sua-organizacao/wifi-portal.git
sudo chown -R $USER:$USER wifi-portal
cd wifi-portal
```

---

## 4) Configurar ambiente (`.env.local`)

```bash
cp .env.prod.example .env.local
```

Gere segredos fortes:

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))"
```

Edite `.env.local` e valide no mínimo:

- `SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL` (com a mesma senha do `POSTGRES_PASSWORD`)
- `REDIS_PASSWORD`
- SMTP (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`/`SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`)

---

## 5) Subir stack de produção

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Se seu host usa o binário legado, troque `docker compose` por `docker-compose`.

---

## 6) Aplicar migrations

```bash
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db upgrade
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db current
```

---

## 7) Verificações pós-deploy

```bash
curl -f http://localhost/healthz
docker compose -f docker-compose.prod.yml logs --tail=100 app
docker compose -f docker-compose.prod.yml logs --tail=100 nginx
```

Validações esperadas:

- Endpoint `/healthz` retorna HTTP `200`
- Containers `app`, `postgres`, `redis`, `nginx` em estado `Up`
- Sem erros recorrentes nos logs

---

## 8) Credencial inicial de administrador

Comportamento atual do sistema (primeira execução sem usuários):

- Usuário: `admin`
- Senha inicial: `admin123`

Após o primeiro login, altere imediatamente em `/admin/profile`.

---

## 9) SSL/TLS (Let's Encrypt)

O projeto inclui o script `deploy/setup-ssl.sh` para:

1. substituir `DOMAIN_NAME` em `deploy/nginx.docker.prod.conf`
2. solicitar certificado
3. reiniciar Nginx e subir stack completa

Execução:

```bash
chmod +x deploy/setup-ssl.sh
sudo bash deploy/setup-ssl.sh seu-dominio.com admin@seu-dominio.com
```

Validação:

```bash
curl -I https://seu-dominio.com/healthz
openssl s_client -connect seu-dominio.com:443 -servername seu-dominio.com </dev/null 2>/dev/null | openssl x509 -noout -dates
```

---

## 10) Operação diária

### Logs e status

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart

```bash
docker compose -f docker-compose.prod.yml restart app
docker compose -f docker-compose.prod.yml restart nginx
docker compose -f docker-compose.prod.yml restart
```

### Upgrade da aplicação

```bash
./scripts/backup/backup_postgres.sh
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db upgrade
curl -f http://localhost/healthz
```

---

## 11) Backup e restore

### Backup (Linux)

```bash
chmod +x scripts/backup/*.sh
./scripts/backup/backup_postgres.sh
```

### Agendamento (cron)

```bash
crontab -e
```

Exemplo diário às 02:00:

```cron
0 2 * * * /opt/wifi-portal/scripts/backup/backup_postgres.sh >> /var/log/wifi-portal-backup.log 2>&1
```

### Restore (Linux)

```bash
./scripts/backup/restore_postgres.sh /backups/wifi_portal_YYYYMMDD_HHMMSS.sql.gz
```

---

## 12) Hardening mínimo recomendado

- Bloquear acesso externo às portas de banco/redis via firewall
- Manter apenas `22`, `80`, `443` expostas no host
- Rotacionar segredos periodicamente
- Monitorar logs de `app` e `nginx`
- Testar restore de backup periodicamente

---

## 13) Comandos rápidos de diagnóstico

```bash
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=200 app
docker compose -f docker-compose.prod.yml exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose -f docker-compose.prod.yml exec redis sh -c 'redis-cli -a "$REDIS_PASSWORD" ping'
```

Para problemas comuns, consulte [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md).
