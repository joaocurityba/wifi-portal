# 🔧 Troubleshooting Operacional

Guia rápido para diagnosticar e corrigir incidentes de produção sem alterar código da aplicação.

---

## 1) Diagnóstico inicial (sempre começar aqui)

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=120 app
docker compose -f docker-compose.prod.yml logs --tail=120 nginx
curl -i http://localhost/healthz
```

Se necessário, use `docker-compose` no lugar de `docker compose`.

---

## 2) App não sobe / fica reiniciando

### Sintomas
- `app` em `Restarting`
- `Exit 1`

### Verificações

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 app
docker compose -f docker-compose.prod.yml exec app env | egrep 'SECRET_KEY|DATABASE_URL|REDIS_URL|SMTP_'
```

### Causas comuns e ação

- Variáveis obrigatórias ausentes no `.env.local`
  - Corrigir `.env.local` e subir novamente:
  ```bash
  docker compose -f docker-compose.prod.yml up -d --build app
  ```
- Falha de conexão com banco/redis
  - Validar `postgres` e `redis` (seção 3)

---

## 3) Falha de conexão com PostgreSQL ou Redis

### PostgreSQL

```bash
docker compose -f docker-compose.prod.yml ps postgres
docker compose -f docker-compose.prod.yml logs --tail=150 postgres
docker compose -f docker-compose.prod.yml exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Checar consistência entre:
- `POSTGRES_PASSWORD`
- senha presente em `DATABASE_URL`

### Redis

```bash
docker compose -f docker-compose.prod.yml ps redis
docker compose -f docker-compose.prod.yml logs --tail=150 redis
docker compose -f docker-compose.prod.yml exec redis sh -c 'redis-cli -a "$REDIS_PASSWORD" ping'
```

Resposta esperada: `PONG`.

---

## 4) Health check falhando

Endpoint correto do projeto: **`/healthz`**.

### Testes

```bash
curl -i http://localhost/healthz
docker compose -f docker-compose.prod.yml exec app curl -i http://localhost:5000/healthz
```

Se no host retornar erro e no container funcionar, o problema está no `nginx`/roteamento.

---

## 5) Nginx falha ao iniciar (SSL)

### Sintoma comum
Erro relacionado a certificado em `/etc/letsencrypt/live/...`.

### Verificações

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 nginx
grep -n "DOMAIN_NAME" deploy/nginx.docker.prod.conf
```

### Ações

1. Garantir que o domínio já esteja configurado no DNS
2. Executar script SSL:

```bash
chmod +x deploy/setup-ssl.sh
sudo bash deploy/setup-ssl.sh seu-dominio.com admin@seu-dominio.com
```

3. Revalidar:

```bash
curl -I https://seu-dominio.com/healthz
```

---

## 6) Erro em migrations

### Comando recomendado

```bash
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db upgrade
```

### Diagnóstico

```bash
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db current
docker compose -f docker-compose.prod.yml logs --tail=200 app
```

---

## 7) Não consigo acessar admin

### Primeiro deploy
- Usuário: `admin`
- Senha inicial: `admin123`

Após login, alterar senha em `/admin/profile`.

### Se credencial não funcionar

```bash
docker compose -f docker-compose.prod.yml logs --tail=200 app | grep -i admin
docker compose -f docker-compose.prod.yml exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, username, email, created_at FROM users;"'
```

---

## 8) Recuperação de senha por email não envia

### Verificações

```bash
docker compose -f docker-compose.prod.yml exec app env | egrep 'SMTP_|FROM_'
docker compose -f docker-compose.prod.yml logs --tail=200 app | grep -i smtp
```

Campos críticos:
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USER` (ou `SMTP_USERNAME`)
- `SMTP_PASSWORD`
- `SMTP_FROM` (ou `FROM_EMAIL`)

---

## 9) Backup falha

### Linux (`backup_postgres.sh`)

```bash
chmod +x scripts/backup/*.sh
./scripts/backup/backup_postgres.sh
```

Se falhar:

```bash
docker ps --filter "name=wifi-portal-postgres"
ls -ld /backups
```

### Windows (`backup_postgres.ps1`)

```powershell
.\scripts\backup\backup_postgres.ps1
```

Verificar:
- Docker Desktop em execução
- container `wifi-portal-postgres` ativo
- 7-Zip disponível em `C:\Program Files\7-Zip\7z.exe`

---

## 10) Comandos de observabilidade úteis

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml top app
docker stats --no-stream
df -h
docker system df
```

---

## 11) Checklist de restauração de serviço

1. `docker compose -f docker-compose.prod.yml ps`
2. `curl -f http://localhost/healthz`
3. Login admin validado
4. Logs sem erro crítico recorrente
5. Backup mais recente confirmado
