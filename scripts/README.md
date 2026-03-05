# Scripts do WiFi Portal

Esta pasta contém scripts auxiliares para operação e manutenção do sistema.

## 📁 Estrutura

### `backup/`
Scripts para backup e restore do banco de dados PostgreSQL.

- **`backup_postgres.ps1`** - Backup automatizado (Windows)
  - Uso: `.\scripts\backup\backup_postgres.ps1`
  - Agenda no Task Scheduler para executar diariamente
  - Salva backups em `C:\backups`
  - Rotação automática de 30 dias

- **`backup_postgres.sh`** - Backup automatizado (Linux)
  - Uso: `./scripts/backup/backup_postgres.sh`
  - Adicionar ao cron: `0 2 * * * /opt/wifi-portal/scripts/backup/backup_postgres.sh`
  - Salva backups em `/backups`
  - Rotação automática de 30 dias

- **`restore_postgres.sh`** - Restauração de backup (Linux)
  - Uso: `./scripts/backup/restore_postgres.sh <arquivo_backup.sql.gz>`
  - Exemplo: `./scripts/backup/restore_postgres.sh /backups/wifi_portal_20260203_020000.sql.gz`

### `docker/`
Scripts para gerenciamento de containers Docker.

- **`start-docker.ps1`** - Inicialização completa com Docker (Windows)
  - Uso: `.\scripts\docker\start-docker.ps1`
  - Para containers existentes
  - Reconstrói imagens
  - Inicia todos os serviços
  - Exibe status e logs

### `testing/` (opcional)
Scripts de teste manual e desenvolvimento.

- **`test_portal.py`** - Teste manual do portal (se existir)
- **`test_redirect.py`** - Teste manual de redirecionamento (se existir)

## 🚀 Exemplos de Uso

### Backup Diário Automático (Linux)
```bash
# Adicionar ao crontab
crontab -e

# Adicionar linha:
0 2 * * * /opt/wifi-portal/scripts/backup/backup_postgres.sh >> /var/log/wifi-portal-backup.log 2>&1
```

### Backup Manual (Windows)
```powershell
# Executar PowerShell como Administrador
cd C:\wifi-portal
.\scripts\backup\backup_postgres.ps1
```

### Iniciar Sistema com Docker
```powershell
# Windows
.\scripts\docker\start-docker.ps1

# Linux
docker-compose up -d
```

### Restaurar Backup
```bash
# Linux
./scripts/backup/restore_postgres.sh /backups/wifi_portal_20260203_020000.sql.gz
```

## ⚠️ Notas Importantes

1. **Permissões Linux**: Certifique-se de dar permissão de execução aos scripts `.sh`
   ```bash
   chmod +x scripts/backup/*.sh
   ```

2. **Task Scheduler (Windows)**: Configure no Agendador de Tarefas para backups automáticos

3. **Volumes Docker**: Os scripts de backup trabalham com containers Docker em execução

4. **Segurança**: Backups contêm dados sensíveis - armazene com segurança

## 📝 Manutenção

- Verifique logs de backup regularmente
- Teste restauração periodicamente
- Monitore espaço em disco para backups
- Ajuste RETENTION_DAYS conforme necessário
