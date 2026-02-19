# 🌐 Portal Cativo Wi-Fi Municipal

Portal cativo para Wi-Fi público com Flask, PostgreSQL, Redis, Docker e painel administrativo.

---

## 📌 Visão Geral

- Coleta consentimento e dados básicos de acesso no portal público (`/login`)
- Disponibiliza painel administrativo (`/admin`) com estatísticas e busca
- Registra logs com foco em segurança e auditoria
- Executa em containers com Nginx + Gunicorn + PostgreSQL + Redis

---

## 🧱 Arquitetura de Produção

- `nginx` (TLS + reverse proxy)
- `app` (Gunicorn servindo `app_simple:app`)
- `postgres` (persistência)
- `redis` (rate limiting/storage do limiter)
- `certbot` (renovação automática de certificado, compose produção)

Endpoint de saúde usado no projeto: **`/healthz`**.

---

## ✅ Requisitos

- Docker 20.10+
- Docker Compose (plugin `docker compose` ou binário `docker-compose`)
- Linux para produção (Ubuntu/Debian/Rocky recomendados)

---

## 🚀 Deploy Rápido (Produção)

1. Clonar o repositório

```bash
git clone https://github.com/sua-organizacao/wifi-portal.git
cd wifi-portal
```

2. Criar arquivo de ambiente de produção

```bash
cp .env.prod.example .env.local
```

3. Editar `.env.local` e trocar todos os valores `TROCAR_POR_*`

4. Subir stack de produção

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

5. Aplicar migrations

```bash
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db upgrade
```

6. Validar saúde

```bash
curl -f http://localhost/healthz
```

> Se seu ambiente usa `docker-compose`, substitua `docker compose` por `docker-compose` nos comandos.

Guia completo: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🔐 Primeiro Acesso Admin

Comportamento atual da aplicação:

- Usuário padrão: `admin`
- Senha inicial padrão: `admin123`

Essa credencial é criada automaticamente quando não existe usuário na tabela `users`.

**Ação obrigatória em produção:** após o primeiro login, altere a senha em `/admin/profile`.

---

## ⚙️ Variáveis de Ambiente

### Obrigatórias para produção (`.env.local`)

- `SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_PASSWORD`

### Utilizadas pela aplicação

- `DEBUG`
- `SESSION_TIMEOUT`
- `MAX_LOGIN_ATTEMPTS`
- `ALLOWED_HOSTS`
- SMTP: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`/`SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM`, `FROM_EMAIL`, `FROM_NAME`

### Observações importantes

- O `docker-compose.prod.yml` injeta `REDIS_URL` automaticamente no container da aplicação.
- O endpoint de saúde esperado pelos health checks é `http://localhost:5000/healthz` dentro do container `app`.

---

## 🗂️ Operação

### Status e logs

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Reinício de serviços

```bash
docker compose -f docker-compose.prod.yml restart app
docker compose -f docker-compose.prod.yml restart nginx
docker compose -f docker-compose.prod.yml restart
```

### Migrações

```bash
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db current
docker compose -f docker-compose.prod.yml exec app flask --app wsgi:app db upgrade
```

---

## 💾 Backup e Restore

Scripts disponíveis:

- Linux: `scripts/backup/backup_postgres.sh`
- Linux (restore): `scripts/backup/restore_postgres.sh`
- Windows: `scripts/backup/backup_postgres.ps1`

Exemplo Linux:

```bash
chmod +x scripts/backup/*.sh
./scripts/backup/backup_postgres.sh
./scripts/backup/restore_postgres.sh /backups/wifi_portal_YYYYMMDD_HHMMSS.sql.gz
```

Mais detalhes: [scripts/README.md](scripts/README.md)

---

## 🧪 Testes

```bash
pytest
pytest --cov=. --cov-report=html
```

---

## 📚 Documentação

- Deploy: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Troubleshooting: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Contribuição: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 📄 Licença

MIT. Ver [LICENSE](LICENSE).
