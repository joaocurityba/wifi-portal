#!/bin/bash
# Backup automatizado do PostgreSQL para WiFi Portal
# Salva em /backups com rotação de 30 dias
# 
# Uso: ./backup_postgres.sh
# Adicionar ao cron: 0 2 * * * /opt/wifi-portal/backup_postgres.sh

set -e

# Configurações
BACKUP_DIR="/backups"
CONTAINER_NAME="wifi-portal-postgres"
DB_USER="portal_user"
DB_NAME="wifi_portal"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/wifi_portal_${DATE}.sql.gz"

# Cria diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup do PostgreSQL..."

# Executa pg_dump dentro do container e compacta
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verifica se o backup foi criado
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup concluído: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ERRO: Backup falhou!"
    exit 1
fi

# Remove backups antigos (mantém últimos 30 dias)
echo "[$(date)] Removendo backups com mais de $RETENTION_DAYS dias..."
find "$BACKUP_DIR" -name "wifi_portal_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Lista backups existentes
echo "[$(date)] Backups disponíveis:"
ls -lh "$BACKUP_DIR"/wifi_portal_*.sql.gz 2>/dev/null || echo "Nenhum backup encontrado"

echo "[$(date)] Processo de backup finalizado!"
