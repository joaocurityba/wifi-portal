# Portal Cativo - Limitações Atuais

**Data:** Janeiro 2026  
**Versão:** 2.0

Este documento lista o que funciona bem e o que pode ser melhorado ou escalado.

---

## ✅ Implementado e Funcionando Bem

- ✅ **Criptografia avançada**: Fernet (PBKDF2-SHA256) para dados sensíveis
- ✅ **Hash de senhas**: Werkzeug PBKDF2
- ✅ **Proteção CSRF**: Em todas rotas POST
- ✅ **Rate limiting**: Integrado com fallback Redis
- ✅ **Validação server-side**: Robusto (email, telefone, data nascimento)
- ✅ **Sanitização HTML**: Previne XSS
- ✅ **File-locking atômico**: Integridade de dados (Unix/Linux)
- ✅ **Logs de segurança**: Audit trail
- ✅ **Docker Compose**: Deployment rápido
- ✅ **Recuperação de senha**: Com tokens
- ✅ **Systemd service**: Auto-restart
- ✅ **Nginx + Let's Encrypt**: HTTPS automático

---

## ⚠️ Limitações e Recomendações

### 1. Armazenamento em Arquivos (Não é Banco de Dados)

**Status:** Funciona, mas tem limites

**O que funciona:**
- CSV/JSON com criptografia
- File-locking atômico para concurrent access
- Até ~10.000 registros OK

**Limitações:**
- Sem índices = busca linear (lento com >10k registros)
- Sem transações = risco de race conditions sob alto tráfego
- Sem replicação = sem alta disponibilidade

**Quando migrar para PostgreSQL:**
```
<10k registros: CSV está OK ✅
10k-100k: Considerar PostgreSQL ⚠️
>100k: PostgreSQL obrigatório ❌
```

**Como fazer migração:**
```bash
# Arquivar logs antigos periodicamente
cd /var/www/wifi-portal-teste/data
tar -czf access_log_archive_$(date +%Y%m).tar.gz access_log*.csv access_log*.json
```

**Prioridade:** Média (escale conforme necessário)

---

### 2. Rate Limiting com Redis (Opcional)

**Status:** ✅ Implementado com fallback automático

**Com Redis (recomendado em produção):**
- Limites persistentes entre restarts
- Escalável horizontalmente
- Verdadeiro rate limiting distribuído

**Sem Redis (fallback in-memory):**
- Limites por worker (com 4 workers, bypass 5x possível)
- Reset ao reiniciar
- OK apenas para desenvolvimento

**Instalação em produção:**
```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
# Em .env.local: REDIS_URL=redis://localhost:6379/0
```

**Prioridade:** Média (importante para produção)

---

### 3. Email/SMTP (Implementado com Fallback)

**Status:** ✅ Implementado

**O que funciona:**
- Recuperação de senha com tokens
- Se SMTP configurado, pode enviar emails
- Se SMTP não disponível, mostra link na tela (dev only)

**Para ativar email:**
```bash
# Em .env.local
SMTP_SERVER=smtp.seu-provedor.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@example.com
SMTP_PASSWORD=senha-app
SMTP_USE_TLS=True
FROM_EMAIL=seu-email@example.com
```

**Prioridade:** Média

---

### 4. Sem Testes Automatizados

**Status:** ⚠️ Estrutura existe, sem cobertura

**O que existe:**
- `test_portal.py` e `test_redirect.py`
- Executáveis

**O que falta:**
- Cobertura de segurança e criptografia
- Cobertura de validação de dados
- Testes de integração

**Como rodar:**
```bash
python test_portal.py
python test_redirect.py

# Com pytest:
pip install pytest
pytest -v
```

**Prioridade:** Média (importante antes de mudanças de código)

---

### 5. Sem Health Checks / Monitoramento

**Status:** ❌ Não implementado

**Necessário para:**
- Load balancers
- Kubernetes
- Escalabilidade automática

**Verificação manual:**
```bash
# Testar que aplicação está viva
curl https://seu-dominio.com/login

# Ver status
sudo systemctl status portal-cautivo
redis-cli ping  # Se usar Redis
```

**Prioridade:** Baixa (só precisa se escalar)

---

### 6. Logs Locais (Sem Agregação Centralizada)

**Status:** ⚠️ Funcional mas manual

**O que funciona:**
- Logs em `/var/www/wifi-portal-teste/logs/`
- Rotacionados diariamente (90 dias retenção)
- Via systemd journal

**O que não funciona:**
- Sem Elasticsearch/Splunk
- Sem Sentry para error tracking
- Sem dashboards
- Sem alertas automáticos

**Monitoramento manual:**
```bash
# Ver logs
tail -100 /var/www/wifi-portal-teste/logs/app.log
grep -i error /var/www/wifi-portal-teste/logs/app.log

# Em tempo real
sudo journalctl -u portal-cautivo -f
```

**Prioridade:** Baixa (OK para operação manual)

---

### 7. Sem Backup Automático

**Status:** ⚠️ Manual apenas

**IMPORTANTE:** Implementar backups!

**Script recomendado:**
```bash
#!/bin/bash
# /home/ubuntu/backup-portal.sh
BACKUP_DIR="/mnt/backup"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

tar -czf $BACKUP_DIR/portal_$DATE.tar.gz \
  /var/www/wifi-portal-teste/data/ \
  /var/www/wifi-portal-teste/.env.local

# Manter últimos 30 backups
find $BACKUP_DIR -name "portal_*" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/portal_$DATE.tar.gz"
```

**Adicionar ao crontab:**
```bash
chmod +x /home/ubuntu/backup-portal.sh

# Executar diariamente às 2h
sudo crontab -e
# Adicionar: 0 2 * * * /home/ubuntu/backup-portal.sh
```

**Prioridade:** ALTA (dados são críticos!)

---

## 📊 Recomendações por Escala

### Pequeno (<100 usuários/dia)
```
✅ Usar configuração atual
✅ CSV adequado
⚠️ Adicionar backups manuais
⚠️ Monitorar logs periodicamente
```

### Médio (100-1000 usuários/dia)
```
✅ Manter CSV ou considerar PostgreSQL
✅ Instalar Redis (IMPORTANTE)
✅ Implementar email SMTP
✅ Backups automáticos
✅ Monitoramento básico
```

### Grande (>1000 usuários/dia)
```
❌ CSV não é adequado
✅ Migrar para PostgreSQL obrigatoriamente
✅ Redis distribuído
✅ Elasticsearch para logs
✅ Múltiplos servidores + load balancer
✅ Monitoramento centralizado (Prometheus + Grafana)
✅ Alertas automáticos
```

---

## 🔮 Melhorias Planejadas (Futura)

- Dashboard admin com gráficos
- Integração MikroTik completa
- 2FA (Two-Factor Authentication)
- LDAP/AD para autenticação corporativa
- API REST para integração
- Testes automatizados completos
- Data export (Excel/PDF)
- Multi-tenancy
- Sentry integration

---

## 🆘 Como Reportar Problemas

1. Abra issue no repositório
2. Inclua: contexto, logs, versão do Ubuntu
3. Descreva o que você está tentando fazer

---

**Última atualização:** Janeiro 2026  
**Status:** Pronto para produção (pequeno-médio volume)
