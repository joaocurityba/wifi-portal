# 🔧 Guia de Troubleshooting

Soluções para problemas comuns no Portal Cativo WiFi. Use este guia para diagnosticar e resolver issues rapidamente.

---

## 📋 Índice

1. [Quick Diagnostic](#quick-diagnostic)
2. [Problemas de Containers](#problemas-de-containers)
3. [Problemas de SSL](#problemas-de-ssl)
4. [Problemas de Health Check](#problemas-de-health-check)
5. [Problemas de Autenticação](#problemas-de-autenticação)
6. [Problemas de Rede](#problemas-de-rede)
7. [Problemas de Performance](#problemas-de-performance)
8. [Problemas de Armazenamento](#problemas-de-armazenamento)
9. [Problemas de Redis](#problemas-de-redis)
10. [Análise de Logs](#análise-de-logs)
11. [Comandos Úteis](#comandos-úteis)

---

## 🚨 Quick Diagnostic

### **Checklist Rápido**

Execute estes comandos para diagnóstico inicial:

```bash
# 1. Status dos containers
docker-compose -f docker-compose.prod.yml ps

# 2. Health checks
curl -I https://wifi.prefeitura.com.br/healthz

# 3. Logs recentes
docker-compose -f docker-compose.prod.yml logs --tail=50

# 4. Uso de recursos
docker stats --no-stream

# 5. Espaço em disco
df -h

# 6. Processos
ps aux | grep gunicorn
```

**O que verificar:**

| Check | Esperado | Se falhar |
|-------|----------|-----------|
| Containers | All "Up (healthy)" | Ver [Problemas de Containers](#problemas-de-containers) |
| Health check | HTTP 200 | Ver [Problemas de Health Check](#problemas-de-health-check) |
| Logs | Sem "ERROR" | Ver [Análise de Logs](#análise-de-logs) |
| CPU | < 70% | Ver [Performance](#problemas-de-performance) |
| Disco | < 80% | Ver [Armazenamento](#problemas-de-armazenamento) |

---

## 🐳 Problemas de Containers

### **Containers não sobem**

**Sintoma:**
```bash
docker-compose -f docker-compose.prod.yml ps
# Mostra: Exit 1 ou Restarting
```

**Diagnóstico:**

```bash
# Ver logs do container com problema
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml logs nginx
docker-compose -f docker-compose.prod.yml logs redis
```

**Soluções:**

#### **1. Porta já em uso**

**Erro:**
```
Error starting userland proxy: listen tcp 0.0.0.0:443: bind: address already in use
```

**Solução:**
```bash
# Identificar processo usando porta 443
sudo lsof -i :443

# Parar processo
sudo kill -9 PID

# Ou parar serviço
sudo systemctl stop nginx  # Se nginx instalado no host
sudo systemctl stop apache2  # Se Apache instalado

# Subir containers novamente
docker-compose -f docker-compose.prod.yml up -d
```

#### **2. .env.local faltando**

**Erro:**
```
KeyError: 'SECRET_KEY'
```

**Solução:**
```bash
# Verificar se .env.local existe
ls -la .env.local

# Se não existir, criar
cp .env.prod .env.local

# Gerar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Editar .env.local e colar a chave
nano .env.local

# Reiniciar
docker-compose -f docker-compose.prod.yml up -d --build
```

#### **3. Permissões de arquivos**

**Erro:**
```
PermissionError: [Errno 13] Permission denied: 'data/users.csv'
```

**Solução:**
```bash
# Corrigir permissões
sudo chown -R $USER:$USER data/ uploads/ logs/
chmod -R 755 data/ uploads/ logs/

# Reiniciar
docker-compose -f docker-compose.prod.yml restart app
```

#### **4. Erro de build**

**Erro:**
```
ERROR: failed to solve: error from sender: open Dockerfile: no such file or directory
```

**Solução:**
```bash
# Verificar se está no diretório correto
pwd
# Deve ser: /var/www/wifi-portal

# Verificar se Dockerfile existe
ls -la Dockerfile

# Se estiver em lugar errado
cd /var/www/wifi-portal

# Rebuild
docker-compose -f docker-compose.prod.yml up -d --build
```

---

### **Container em restart loop**

**Sintoma:**
```bash
docker-compose -f docker-compose.prod.yml ps
# STATUS: Restarting (1) 3 seconds ago
```

**Diagnóstico:**

```bash
# Ver últimas 100 linhas de log
docker-compose -f docker-compose.prod.yml logs --tail=100 app

# Ver tentativas de restart
docker events --filter 'container=wifi-portal-app'
```

**Causas Comuns:**

1. **App crashando na inicialização**
   ```bash
   # Ver traceback completo
   docker-compose -f docker-compose.prod.yml logs app | grep -A 50 "Traceback"
   ```

2. **Health check falhando**
   ```bash
   # Testar health check manualmente
   docker-compose -f docker-compose.prod.yml exec app curl localhost:5000/healthz
   ```

3. **Dependência não disponível (Redis)**
   ```bash
   # Verificar Redis
   docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
   # Deve retornar: PONG
   ```

**Solução:**
```bash
# Parar todos os containers
docker-compose -f docker-compose.prod.yml down

# Limpar volumes (CUIDADO: perde dados)
docker volume prune

# Subir novamente
docker-compose -f docker-compose.prod.yml up -d --build

# Acompanhar logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔐 Problemas de SSL

### **Certificado SSL não funciona**

**Sintoma:**
```
Your connection is not private
NET::ERR_CERT_DATE_INVALID
```

**Diagnóstico:**

```bash
# Verificar certificado
openssl s_client -connect wifi.prefeitura.com.br:443 -servername wifi.prefeitura.com.br < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Deve mostrar:
# notBefore=...
# notAfter=...
```

**Soluções:**

#### **1. Certificado expirado**

**Solução:**
```bash
# Renovar certificado
docker-compose -f docker-compose.prod.yml exec certbot certbot renew --force-renewal

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Verificar
curl -I https://wifi.prefeitura.com.br/healthz
```

#### **2. Certificado não foi criado**

**Erro:**
```
ssl_certificate "/etc/letsencrypt/live/wifi.prefeitura.com.br/fullchain.pem" failed
```

**Solução:**
```bash
# Executar script de SSL novamente
sudo bash deploy/setup-ssl.sh wifi.prefeitura.com.br admin@prefeitura.com.br

# Ou manualmente
docker-compose -f docker-compose.prod.yml up -d certbot
docker-compose -f docker-compose.prod.yml exec certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@prefeitura.com.br \
  --agree-tos \
  --no-eff-email \
  -d wifi.prefeitura.com.br
```

#### **3. DNS não aponta para servidor**

**Solução:**
```bash
# Verificar DNS
dig +short wifi.prefeitura.com.br

# Deve retornar o IP do servidor
# Se não retornar, configurar DNS e aguardar propagação

# Verificar propagação em: https://dnschecker.org
```

---

### **Renovação automática não funciona**

**Problema:**
Certificado expira e não renova automaticamente.

**Diagnóstico:**

```bash
# Verificar cron do certbot
docker-compose -f docker-compose.prod.yml exec certbot cat /etc/cron.d/certbot

# Ver logs de renovação
docker-compose -f docker-compose.prod.yml logs certbot | grep renew
```

**Solução:**

```bash
# Testar renovação dry-run
docker-compose -f docker-compose.prod.yml exec certbot certbot renew --dry-run

# Se funcionar, configurar cron no host
sudo crontab -e
# Adicionar:
0 3 * * * cd /var/www/wifi-portal && docker-compose -f docker-compose.prod.yml exec certbot certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

---

## ❤️ Problemas de Health Check

### **Health check falha constantemente**

**Sintoma:**
```bash
docker-compose -f docker-compose.prod.yml ps
# STATUS: Up (unhealthy)
```

**Diagnóstico:**

```bash
# Testar health check manualmente
curl http://localhost/healthz

# Dentro do container
docker-compose -f docker-compose.prod.yml exec app curl localhost:5000/healthz

# Ver logs do health check
docker inspect wifi-portal-app --format='{{json .State.Health}}' | jq
```

**Soluções:**

#### **1. Endpoint /healthz não existe**

**Erro:**
```
404 Not Found
```

**Solução:**
```bash
# Verificar se rota existe no código
docker-compose -f docker-compose.prod.yml exec app grep -n "healthz" app_simple.py

# Se não existir, adicionar no app_simple.py:
@app.route('/healthz')
def healthz():
    return jsonify({"status": "healthy", "service": "wifi-portal"}), 200

# Rebuild
docker-compose -f docker-compose.prod.yml up -d --build
```

#### **2. App não está respondendo**

**Erro:**
```
curl: (7) Failed to connect to localhost port 5000
```

**Solução:**
```bash
# Ver se gunicorn está rodando
docker-compose -f docker-compose.prod.yml exec app ps aux | grep gunicorn

# Ver logs do app
docker-compose -f docker-compose.prod.yml logs app

# Reiniciar
docker-compose -f docker-compose.prod.yml restart app
```

#### **3. Timeout muito curto**

**Problema:**
Health check timeout antes da resposta.

**Solução:**

Editar `docker-compose.prod.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/healthz"]
  interval: 30s
  timeout: 10s  # Aumentar de 3s para 10s
  retries: 3
  start_period: 40s  # Aumentar período inicial
```

```bash
# Aplicar mudanças
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔑 Problemas de Autenticação

### **Não consegue fazer login (credenciais corretas)**

**Sintoma:**
```
Login falha mesmo com senha correta
```

**Diagnóstico:**

```bash
# Verificar se users.csv existe
docker-compose -f docker-compose.prod.yml exec app ls -la data/users.csv

# Ver conteúdo (sem revelar senhas completas)
docker-compose -f docker-compose.prod.yml exec app head data/users.csv
```

**Soluções:**

#### **1. Arquivo users.csv corrompido**

**Solução:**
```bash
# Fazer backup
docker-compose -f docker-compose.prod.yml exec app cp data/users.csv data/users.csv.bak

# Verificar integridade
docker-compose -f docker-compose.prod.yml exec app cat data/users.csv

# Se corrompido, recriar
docker-compose -f docker-compose.prod.yml exec app python3 << 'EOF'
from werkzeug.security import generate_password_hash
import csv
from datetime import datetime

users = [
    ['admin', generate_password_hash('admin123'), 'admin', datetime.now().isoformat()]
]

with open('data/users.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['username', 'password_hash', 'role', 'created_at'])
    writer.writerows(users)
EOF

# Reiniciar app
docker-compose -f docker-compose.prod.yml restart app
```

#### **2. CSRF token inválido**

**Erro no log:**
```
The CSRF token is missing
```

**Solução:**
```bash
# Limpar cookies do navegador
# Ou modo anônimo

# Verificar SECRET_KEY está configurada
docker-compose -f docker-compose.prod.yml exec app env | grep SECRET_KEY

# Se vazia, configurar em .env.local
nano .env.local
# SECRET_KEY=sua-chave-aqui

# Reiniciar
docker-compose -f docker-compose.prod.yml restart app
```

---

### **Rate limit bloqueando admin**

**Sintoma:**
```
429 Too Many Requests
Muitas tentativas. Tente novamente em X segundos.
```

**Solução:**

```bash
# Opção 1: Limpar rate limit no Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Dentro do redis-cli:
KEYS *192.168.1.100*  # Substitua pelo IP do admin
DEL rate_limit:192.168.1.100
exit

# Opção 2: Aguardar 1 hora (timeout padrão)

# Opção 3: Desabilitar rate limit temporariamente
# Editar .env.local:
RATE_LIMIT_ENABLED=False

# Reiniciar app
docker-compose -f docker-compose.prod.yml restart app
```

---

## 🌐 Problemas de Rede

### **502 Bad Gateway**

**Sintoma:**
```
nginx/1.25.0 502 Bad Gateway
```

**Diagnóstico:**

```bash
# Ver logs nginx
docker-compose -f docker-compose.prod.yml logs nginx | tail -50

# Ver logs app
docker-compose -f docker-compose.prod.yml logs app | tail -50

# Testar conexão nginx → app
docker-compose -f docker-compose.prod.yml exec nginx curl http://app:5000/healthz
```

**Soluções:**

#### **1. App não está respondendo**

**Solução:**
```bash
# Reiniciar app
docker-compose -f docker-compose.prod.yml restart app

# Aguardar 10 segundos
sleep 10

# Testar
curl https://wifi.prefeitura.com.br/healthz
```

#### **2. Timeout nginx → app**

**Solução:**

Editar `deploy/nginx.docker.prod.conf`:

```nginx
location / {
    proxy_pass http://app:5000;
    proxy_connect_timeout 60s;  # Aumentar
    proxy_read_timeout 60s;     # Aumentar
    proxy_send_timeout 60s;     # Aumentar
}
```

```bash
# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

---

### **Redirecionamento não funciona (MikroTik)**

**Problema:**
Usuário não é redirecionado para o portal.

**Diagnóstico:**

```bash
# Testar DNS do portal
dig +short wifi.prefeitura.com.br

# Testar HTTP (deve redirecionar para HTTPS)
curl -I http://wifi.prefeitura.com.br

# Verificar configuração MikroTik (via SSH)
ssh admin@IP_MIKROTIK
/ip hotspot profile print detail
```

**Solução:**

No MikroTik:

```
/ip hotspot profile
set [find] login-by=http-chap,http-pap,cookie
set [find] http-proxy=0.0.0.0:0
set [find] use-radius=no

/ip hotspot
set [find] address-pool=hs-pool
set [find] profile=hsprof1
set [find] idle-timeout=5m

# IMPORTANTE: Configurar Login URL
/ip hotspot profile
set [find] html-directory=hotspot
set [find] login-by=http-chap
set [find] http-proxy=0.0.0.0:0
set [find] login-by=cookie,http-chap

# Mudar URL de login
set [find] use-radius=no
set [find] http-cookie-lifetime=1d
```

---

## ⚡ Problemas de Performance

### **Aplicação muito lenta**

**Sintoma:**
Páginas demoram >5 segundos para carregar.

**Diagnóstico:**

```bash
# Ver uso de recursos
docker stats --no-stream

# Ver processos dentro do container
docker-compose -f docker-compose.prod.yml exec app top

# Testar latência
curl -w "@-" -o /dev/null -s https://wifi.prefeitura.com.br/login << 'EOF'
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
EOF
```

**Soluções:**

#### **1. CPU em 100%**

**Solução:**
```bash
# Aumentar workers do Gunicorn
# Editar wsgi.py ou docker-compose.prod.yml

# Calcular workers ideais
python3 -c "import multiprocessing; print((multiprocessing.cpu_count() * 2) + 1)"

# Aplicar (exemplo: 9 workers para 4 CPUs)
docker-compose -f docker-compose.prod.yml exec app gunicorn wsgi:app \
  --workers 9 \
  --bind 0.0.0.0:5000 \
  --reload
```

#### **2. Memória esgotada**

**Solução:**
```bash
# Ver uso de memória
free -h

# Limpar cache
sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches

# Adicionar swap (se não tiver)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### **3. I/O de disco lento**

**Problema:**
CSV muito grande.

**Solução:**
```bash
# Ver tamanho dos arquivos
du -sh data/*

# Se access_log.csv > 100MB, rotacionar
cd data
timestamp=$(date +%Y%m%d_%H%M%S)
mv access_log.csv access_log_${timestamp}.csv
touch access_log.csv

# Comprimir antigos
gzip access_log_*.csv

# Reiniciar app
docker-compose -f docker-compose.prod.yml restart app
```

---

### **Redis lento**

**Diagnóstico:**

```bash
# Conectar ao Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Ver estatísticas
INFO stats

# Ver latência
PING
# Deve retornar PONG instantaneamente

# Ver memória
INFO memory
```

**Soluções:**

#### **1. Redis com muitas keys**

```bash
# Dentro do redis-cli
DBSIZE
# Se > 1 milhão, considerar flush

# Flush (CUIDADO: perde todos os dados)
FLUSHDB

# Ou configurar expiração automática
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru
```

---

## 💾 Problemas de Armazenamento

### **Disco cheio**

**Sintoma:**
```
OSError: [Errno 28] No space left on device
```

**Diagnóstico:**

```bash
# Ver uso de disco
df -h

# Ver maiores diretórios
du -h /var/www/wifi-portal | sort -hr | head -20

# Ver maiores arquivos
find /var/www/wifi-portal -type f -size +100M -exec ls -lh {} \;
```

**Soluções:**

```bash
# Limpar logs do Docker
docker system prune -a --volumes -f

# Limpar logs da aplicação
cd /var/www/wifi-portal
find logs/ -name "*.log" -mtime +7 -delete

# Rotacionar access_log.csv
cd data
for file in access_log_*.csv; do
    gzip "$file"
done

# Mover backups antigos
find /backup -name "*.tar.gz" -mtime +30 -delete

# Se necessário, aumentar disco
# (depende do provedor de cloud)
```

---

### **Arquivo corrompido**

**Sintoma:**
```
csv.Error: line contains NULL byte
```

**Solução:**

```bash
# Fazer backup
cp data/users.csv data/users.csv.corrupt

# Tentar recuperar
strings data/users.csv.corrupt > data/users.csv

# Verificar
cat data/users.csv

# Se não funcionar, restaurar do backup
cp /backup/wifi-portal_LATEST.tar.gz .
tar -xzf wifi-portal_LATEST.tar.gz
cp backup/data/users.csv data/

# Reiniciar
docker-compose -f docker-compose.prod.yml restart app
```

---

## 🔴 Problemas de Redis

### **Redis não conecta**

**Erro:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Diagnóstico:**

```bash
# Ver se Redis está rodando
docker-compose -f docker-compose.prod.yml ps redis

# Testar conexão
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Ver porta
docker-compose -f docker-compose.prod.yml exec redis netstat -tuln | grep 6379
```

**Soluções:**

#### **1. Redis parado**

```bash
# Iniciar Redis
docker-compose -f docker-compose.prod.yml up -d redis

# Verificar logs
docker-compose -f docker-compose.prod.yml logs redis
```

#### **2. Senha incorreta**

**Erro:**
```
NOAUTH Authentication required
```

**Solução:**
```bash
# Verificar senha em .env.local
grep REDIS_PASSWORD .env.local

# Verificar senha em docker-compose.prod.yml
grep REDIS_PASSWORD docker-compose.prod.yml

# Se diferentes, corrigir e reiniciar
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📊 Análise de Logs

### **Encontrar erros nos logs**

```bash
# Erros de todas as aplicações
docker-compose -f docker-compose.prod.yml logs | grep -i error

# Erros apenas do app
docker-compose -f docker-compose.prod.yml logs app | grep -i error

# Últimas 100 linhas com erro
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i "error\|exception\|failed"

# Exportar logs para análise
docker-compose -f docker-compose.prod.yml logs > /tmp/portal-logs.txt
```

### **Logs em tempo real**

```bash
# Todos os containers
docker-compose -f docker-compose.prod.yml logs -f

# Apenas app
docker-compose -f docker-compose.prod.yml logs -f app

# Com timestamp
docker-compose -f docker-compose.prod.yml logs -f -t

# Filtrar por padrão
docker-compose -f docker-compose.prod.yml logs -f | grep "192.168.1.100"
```

### **Analisar logs do Nginx**

```bash
# Access log
docker-compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/access.log | tail -100

# Error log
docker-compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/error.log | tail -100

# Top 10 IPs
docker-compose -f docker-compose.prod.yml exec nginx awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# Top 10 URLs
docker-compose -f docker-compose.prod.yml exec nginx awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10
```

---

## 🛠️ Comandos Úteis

### **Restart Completo**

```bash
# Parar tudo
docker-compose -f docker-compose.prod.yml down

# Limpar (CUIDADO: perde dados não persistidos)
docker system prune -f

# Subir novamente
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar
docker-compose -f docker-compose.prod.yml ps
curl https://wifi.prefeitura.com.br/healthz
```

### **Resetar Aplicação (Factory Reset)**

**⚠️ ATENÇÃO: Isso apaga TODOS OS DADOS!**

```bash
# Backup primeiro!
sudo /usr/local/bin/backup-wifi-portal.sh

# Parar containers
docker-compose -f docker-compose.prod.yml down -v

# Remover dados
rm -rf data/* uploads/* logs/nginx/*

# Recriar estrutura
mkdir -p data uploads logs/nginx
touch data/users.csv data/access_log.csv

# Criar usuário admin
docker-compose -f docker-compose.prod.yml run --rm app python3 << 'EOF'
from werkzeug.security import generate_password_hash
import csv
from datetime import datetime

users = [['admin', generate_password_hash('admin123'), 'admin', datetime.now().isoformat()]]
with open('data/users.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['username', 'password_hash', 'role', 'created_at'])
    writer.writerows(users)
EOF

# Subir
docker-compose -f docker-compose.prod.yml up -d --build
```

### **Backup Manual**

```bash
# Criar backup
timestamp=$(date +%Y%m%d_%H%M%S)
tar -czf wifi-portal-backup-${timestamp}.tar.gz \
    data/ \
    uploads/ \
    .env.local \
    logs/nginx/

# Verificar
ls -lh wifi-portal-backup-*.tar.gz

# Restaurar
tar -xzf wifi-portal-backup-TIMESTAMP.tar.gz
docker-compose -f docker-compose.prod.yml restart
```

### **Ver Métricas**

```bash
# Requisições por segundo
docker-compose -f docker-compose.prod.yml logs nginx | grep -oP '\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2}' | uniq -c

# Tempo médio de resposta
docker-compose -f docker-compose.prod.yml logs app | grep -oP 'response_time=\K[\d.]+' | awk '{sum+=$1; count++} END {print "Média:", sum/count, "ms"}'

# Erros 5xx
docker-compose -f docker-compose.prod.yml logs nginx | grep ' 5[0-9][0-9] ' | wc -l
```

---

## 🆘 Quando Pedir Ajuda

Se após tentar as soluções acima o problema persistir:

### **1. Coletar Informações**

```bash
# Script de diagnóstico completo
cat > /tmp/diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== DIAGNÓSTICO COMPLETO ==="
echo
echo "Data/Hora: $(date)"
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo
echo "=== DOCKER ==="
docker --version
docker-compose --version
echo
echo "=== CONTAINERS ==="
docker-compose -f docker-compose.prod.yml ps
echo
echo "=== RECURSOS ==="
free -h
df -h
docker stats --no-stream
echo
echo "=== LOGS (últimas 50 linhas) ==="
docker-compose -f docker-compose.prod.yml logs --tail=50
echo
echo "=== HEALTH CHECKS ==="
curl -I http://localhost/healthz 2>&1
curl -I https://wifi.prefeitura.com.br/healthz 2>&1
EOF

chmod +x /tmp/diagnostic.sh
bash /tmp/diagnostic.sh > /tmp/diagnostic-output.txt 2>&1

# Enviar diagnostic-output.txt para o suporte
```

### **2. Abrir Issue no GitHub**

Template:

```markdown
## Descrição do Problema
[Descreva claramente]

## Comportamento Esperado
[O que deveria acontecer]

## Comportamento Observado
[O que está acontecendo]

## Passos para Reproduzir
1. ...
2. ...
3. ...

## Ambiente
- OS: Ubuntu 22.04
- Docker: 24.0.7
- Compose: 2.21.0

## Logs
```
[Cole o conteúdo de diagnostic-output.txt]
```

## Já Tentei
- [x] Reiniciar containers
- [x] Verificar logs
- [ ] ...
```

---

<p align="center">
  <strong>Se nada funcionar, pode ser um bug! Reporte em GitHub Issues. 🐛</strong>
</p>
