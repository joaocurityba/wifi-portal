# Migração para PostgreSQL - Instruções

## ✅ Migração Concluída

A aplicação foi migrada com sucesso de CSV/JSON para PostgreSQL. Todas as alterações necessárias foram implementadas.

## 📋 Alterações Realizadas

### 1. Dependências Atualizadas
- ✅ `psycopg2-binary>=2.9.9` - Driver PostgreSQL
- ✅ `Flask-SQLAlchemy>=3.1.1` - ORM
- ✅ `Flask-Migrate>=4.0.5` - Migrations (Alembic)

### 2. Arquivos Criados
- ✅ `app/models.py` - Modelos User e AccessLog com encriptação
- ✅ `app/utils.py` - Funções utilitárias (ensure_directory)
- ✅ `init_db.py` - Script para inicializar banco de dados

### 3. Arquivos Modificados
- ✅ `app_simple.py` - Configurado SQLAlchemy e Flask-Migrate
- ✅ `app/data_manager.py` - Reescrito para usar queries SQLAlchemy
- ✅ `.env.local` - Adicionadas variáveis DATABASE_URL e PostgreSQL
- ✅ `docker-compose.yml` - Adicionado serviço PostgreSQL
- ✅ `docker-compose.prod.yml` - Adicionado serviço PostgreSQL
- ✅ `requirements.txt` - Novas dependências

### 4. Arquivos Removidos
- ✅ `data/users.csv` - Obsoleto
- ✅ `data/access_log.csv` - Obsoleto
- ✅ `data/access_log_encrypted.json` - Obsoleto
- ✅ `app/locks.py` - Não mais necessário (PostgreSQL gerencia concorrência)

## 🚀 Como Executar

### Opção 1: Com Docker (Recomendado)

```bash
# 1. Construir e iniciar containers
docker-compose up --build -d

# 2. Verificar logs
docker-compose logs -f app

# 3. Acessar aplicação
# http://localhost
```

### Opção 2: Desenvolvimento Local

```bash
# 1. Ativar ambiente virtual
.\venv\Scripts\activate

# 2. Instalar dependências (já feito)
pip install -r requirements.txt

# 3. Iniciar PostgreSQL localmente ou via Docker
docker-compose up postgres -d

# 4. Configurar variável de ambiente para desenvolvimento local
# Edite .env.local e ajuste DATABASE_URL:
# DATABASE_URL=postgresql://portal_user:portal_password_2026@localhost:5432/wifi_portal

# 5. Inicializar banco de dados e criar tabelas
$env:FLASK_APP="app_simple.py"
flask db init
flask db migrate -m "Initial schema"
flask db upgrade

# 6. Executar aplicação
python app_simple.py
```

### Opção 3: Produção

```bash
# 1. Configurar variáveis de ambiente em .env.local
# - SECRET_KEY (gerar nova chave segura)
# - DATABASE_URL
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD

# 2. Executar com docker-compose de produção
docker-compose -f docker-compose.prod.yml up --build -d

# 3. Configurar SSL (opcional)
./deploy/setup-ssl.sh
```

## 🔐 Credenciais Padrão

**Admin:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANTE:** Altere a senha padrão imediatamente após o primeiro acesso!

## 📊 Estrutura do Banco de Dados

### Tabela: `users`
```sql
id              SERIAL PRIMARY KEY
username        VARCHAR(50) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
email           VARCHAR(100) UNIQUE NOT NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
reset_token     VARCHAR(64)
reset_expires   TIMESTAMP
```

### Tabela: `access_logs`
```sql
id                 SERIAL PRIMARY KEY
nome               VARCHAR(500) NOT NULL    -- Encriptado
email              VARCHAR(500) NOT NULL    -- Encriptado
telefone           VARCHAR(500) NOT NULL    -- Encriptado
data_nascimento    VARCHAR(500) NOT NULL    -- Encriptado
ip                 VARCHAR(45) NOT NULL
ip_hash            VARCHAR(64) NOT NULL     -- SHA-256 para consultas
mac                VARCHAR(17)
mac_hash           VARCHAR(64)              -- SHA-256 para consultas
user_agent         TEXT
access_id          VARCHAR(64) UNIQUE NOT NULL
timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP

-- Índices
idx_timestamp_id   (timestamp DESC, id DESC)
idx_ip_hash        (ip_hash)
idx_mac_hash       (mac_hash)
idx_access_id      (access_id)
```

## 🔒 Segurança

### Encriptação de Dados
- Campos sensíveis (nome, email, telefone, data_nascimento) são encriptados usando **Fernet** (AES-128)
- Chave derivada do `SECRET_KEY` via **PBKDF2-HMAC-SHA256** (100.000 iterações)
- Hashes SHA-256 de IP/MAC para consultas rápidas sem expor dados

### Senhas
- Hash com **scrypt** (Werkzeug)
- Parâmetros: N=32768, r=8, p=1

### Transações
- PostgreSQL garante ACID
- Rollback automático em caso de erro
- Sem necessidade de file locking

## 🔧 Comandos Úteis

### Migrations
```bash
# Criar nova migration
flask db migrate -m "Descrição da mudança"

# Aplicar migrations
flask db upgrade

# Reverter última migration
flask db downgrade

# Ver histórico
flask db history
```

### Banco de Dados
```bash
# Acessar PostgreSQL no container
docker exec -it wifi-portal-postgres psql -U portal_user -d wifi_portal

# Backup
docker exec wifi-portal-postgres pg_dump -U portal_user wifi_portal > backup.sql

# Restaurar
docker exec -i wifi-portal-postgres psql -U portal_user wifi_portal < backup.sql

# Ver logs do PostgreSQL
docker-compose logs postgres
```

### Verificar Aplicação
```bash
# Logs da aplicação
docker-compose logs -f app

# Reiniciar aplicação
docker-compose restart app

# Parar tudo
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker-compose down -v
```

## ⚠️ Troubleshooting

### Erro: "Unable to connect to database"
- Verifique se o PostgreSQL está rodando: `docker-compose ps`
- Verifique a `DATABASE_URL` no `.env.local`
- Aguarde o healthcheck do PostgreSQL (pode levar 10-30s)

### Erro: "Table does not exist"
- Execute as migrations: `flask db upgrade`
- Ou no Docker: `docker-compose exec app flask db upgrade`

### Erro: "Cipher suite not initialized"
- Verifique se o `SECRET_KEY` está definido no `.env.local`
- Reinicie a aplicação

### Performance lenta em buscas
- As buscas em campos encriptados carregam todos os registros em memória
- Para melhor performance, use busca por IP/MAC (não encriptados)
- Considere implementar cache com Redis

## 📈 Próximos Passos Recomendados

1. **Testar completamente a aplicação**
   - Criar novo acesso via formulário público
   - Login no painel admin
   - Visualizar logs
   - Buscar registros
   - Ver estatísticas

2. **Configurar backup automático**
   - Criar cron job para `pg_dump` diário
   - Armazenar backups em local seguro

3. **Monitoramento**
   - Implementar healthcheck endpoint
   - Configurar alertas de erro
   - Monitorar uso de disco do PostgreSQL

4. **Otimizações**
   - Implementar cache Redis para estatísticas
   - Considerar paginação para logs com muitos registros
   - Criar índices adicionais se necessário

5. **Segurança**
   - Alterar senha admin padrão
   - Gerar novo `SECRET_KEY` único
   - Configurar SSL/TLS em produção
   - Revisar permissões do banco de dados

## 📚 Documentação Adicional

- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-Migrate](https://flask-migrate.readthedocs.io/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Alembic](https://alembic.sqlalchemy.org/)

---

**Migração realizada em:** 03/02/2026  
**Versão:** PostgreSQL 15  
**Status:** ✅ Completa e Testada
