#!/bin/bash
# Script de restore do PostgreSQL para WiFi Portal
#
# Uso: ./restore_postgres.sh <arquivo_backup.sql.gz>
# Exemplo: ./restore_postgres.sh /backups/wifi_portal_20260203_020000.sql.gz

set -e

# Configurações
CONTAINER_NAME="wifi-portal-postgres"
DB_USER="portal_user"
DB_NAME="wifi_portal"

# Verifica se foi passado um arquivo
if [ -z "$1" ]; then
    echo "Erro: Informe o arquivo de backup"
    echo "Uso: $0 <arquivo_backup.sql.gz>"
    echo ""
    echo "Backups disponíveis:"
    ls -lh /backups/wifi_portal_*.sql.gz 2>/dev/null || echo "Nenhum backup encontrado"
    exit 1
fi

BACKUP_FILE="$1"

# Verifica se o arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Erro: Arquivo não encontrado: $BACKUP_FILE"
    exit 1
fi

echo "========================================="
echo "ATENÇÃO: Este processo irá:"
echo "1. Parar a aplicação"
echo "2. APAGAR todos os dados atuais do banco"
echo "3. Restaurar dados do backup: $BACKUP_FILE"
echo "========================================="
read -p "Deseja continuar? (digite 'SIM' para confirmar): " CONFIRM

if [ "$CONFIRM" != "SIM" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo "[$(date)] Parando aplicação..."
docker-compose stop app

echo "[$(date)] Deletando banco de dados atual..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "[$(date)] Criando novo banco de dados..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "[$(date)] Restaurando backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

echo "[$(date)] Iniciando aplicação..."
docker-compose start app

echo "[$(date)] Restore concluído com sucesso!"
echo "[$(date)] Verificando dados..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "\
    SELECT 'Users: ' || COUNT(*) FROM users UNION ALL \
    SELECT 'Access Logs: ' || COUNT(*) FROM access_logs;"
