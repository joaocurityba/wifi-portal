# PowerShell script for PostgreSQL backup on Windows
# Backup automatizado do PostgreSQL para WiFi Portal
# Salva em C:\backups com rotação de 30 dias
# 
# Uso: .\backup_postgres.ps1
# Agendar no Windows: Task Scheduler diariamente às 02:00

$ErrorActionPreference = "Stop"

# Configurações
$BACKUP_DIR = "C:\backups"
$CONTAINER_NAME = "wifi-portal-postgres"
$DB_USER = "portal_user"
$DB_NAME = "wifi_portal"
$RETENTION_DAYS = 30
$DATE = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = "$BACKUP_DIR\wifi_portal_$DATE.sql.gz"

# Cria diretório de backup se não existir
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
}

Write-Host "[$((Get-Date))] Iniciando backup do PostgreSQL..."

try {
    # Executa pg_dump dentro do container
    $dumpOutput = docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME
    
    # Compacta e salva
    $dumpOutput | & "C:\Program Files\7-Zip\7z.exe" a -si $BACKUP_FILE -tgzip
    
    if (Test-Path $BACKUP_FILE) {
        $SIZE = (Get-Item $BACKUP_FILE).Length / 1MB
        Write-Host "[$((Get-Date))] Backup concluído: $BACKUP_FILE ($([math]::Round($SIZE, 2)) MB)"
    } else {
        throw "Backup falhou - arquivo não criado"
    }
    
    # Remove backups antigos
    Write-Host "[$((Get-Date))] Removendo backups com mais de $RETENTION_DAYS dias..."
    Get-ChildItem $BACKUP_DIR -Filter "wifi_portal_*.sql.gz" | 
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RETENTION_DAYS) } | 
        Remove-Item -Force
    
    # Lista backups existentes
    Write-Host "[$((Get-Date))] Backups disponíveis:"
    Get-ChildItem $BACKUP_DIR -Filter "wifi_portal_*.sql.gz" | 
        Format-Table Name, Length, LastWriteTime -AutoSize
    
    Write-Host "[$((Get-Date))] Processo de backup finalizado!"
    
} catch {
    Write-Host "[$((Get-Date))] ERRO: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
