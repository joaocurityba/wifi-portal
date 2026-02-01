# Portal Cativo - Troubleshooting Guide

Guia de diagnóstico e resolução dos problemas mais comuns em deploy.

---

## 🔍 Diagnóstico Rápido

### Checklist de 5 Passos

```bash
# 1. Aplicação está rodando?
sudo systemctl status portal-cautivo

# 2. Gunicorn está respondendo localmente?
curl -s http://127.0.0.1:8003/login | head -20

# 3. Nginx está rodando?
sudo systemctl status nginx

# 4. Https está funcionando?
curl -s -k https://seu-dominio.com/login | head -20

# 5. Certificado SSL está válido?
sudo certbot certificates | grep seu-dominio.com
```

Se algum fail, vá para seção correspondente abaixo.

---

## ❌ Erro: "ModuleNotFoundError" ou Aplicação não inicia

### Sintomas
```
ModuleNotFoundError: No module named 'flask'
ModuleNotFoundError: No module named 'app_simple'
ImportError: cannot import name 'app'
```

### Diagnóstico

```bash
# 1. Virtual environment está ativado?
echo $VIRTUAL_ENV
# Deve mostrar: /var/www/wifi-portal-teste/.venv

# 2. Arquivo .env.local existe?
ls -la /var/www/wifi-portal-teste/.env.local

# 3. Aplicação consegue ser importada?
cd /var/www/wifi-portal-teste
source .venv/bin/activate
python -c "from wsgi import app; print('✓ OK')"
```

### Causas Comuns e Soluções

#### Erro: `.env.local` não encontrado

```bash
# Criar .env.local
cd /var/www/wifi-portal-teste
cp .env.template .env.local

# Editar e preencher valores obrigatórios
nano .env.local

# Permissões
chmod 600 .env.local

# Reiniciar
sudo systemctl restart portal-cautivo
```

#### Erro: Dependências não instaladas

```bash
# Reinstalar dependências
cd /var/www/wifi-portal-teste
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn>=21.0.0

# Verificar
pip list | grep -E "Flask|Werkzeug|gunicorn"
```

#### Erro: Virtual environment não criado

```bash
# Criar venv
cd /var/www/wifi-portal-teste
python3 -m venv .venv

# Ativar e instalar
source .venv/bin/activate
pip install -r requirements.txt

# Reiniciar service
sudo systemctl restart portal-cautivo
```

---

## ❌ Erro: "Gunicorn não consegue ligar na porta 8003"

### Sintomas
```
Address already in use: ('127.0.0.1', 8003)
[Errno 98] Address already in use
```

### Solução

```bash
# Ver o que está usando porta 8003
sudo lsof -i :8003
# ou
sudo ss -tulpn | grep 8003

# Matar processo antigo (se necessário)
sudo kill -9 <PID>

# Aguardar 5 segundos e reiniciar
sleep 5
sudo systemctl restart portal-cautivo

# Verificar que agora está rodando
sudo systemctl status portal-cautivo
```

---

## ❌ Erro: "Permission denied" ao escrever em data/ ou logs/

### Sintomas
```
PermissionError: [Errno 13] Permission denied: 'data/access_log.csv'
```

### Solução

```bash
# Mudar ownership para www-data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/logs

# Definir permissões corretas
sudo chmod 750 /var/www/wifi-portal-teste/data
sudo chmod 750 /var/www/wifi-portal-teste/logs

# Reiniciar
sudo systemctl restart portal-cautivo

# Verificar
ls -la /var/www/wifi-portal-teste/data/
```

---

# Deve ser:
# ExecStart=/var/www/wifi-portal-teste/.venv/bin/python -m gunicorn -c deploy/gunicorn.conf.py wsgi:app

# Se não tiver .venv no path, reinstalar:
cd /var/www/wifi-portal-teste
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Recarregar systemd
sudo systemctl daemon-reload
sudo systemctl restart portal-cautivo
```

#### 1.2: .env.local não encontrado

**Erro:**
```
FileNotFoundError: [Errno 2] No such file or directory: '.env.local'
```

**Solução:**
```bash
# Criar .env.local
cd /var/www/wifi-portal-teste
cp .env.template .env.local
nano .env.local  # preencher valores

# Permissões corretas
chmod 600 .env.local

# Reiniciar
sudo systemctl restart portal-cautivo
```

#### 1.3: Gunicorn não pode ligar na porta

**Erro:**
```
Address already in use: ('127.0.0.1', 8003)
```

**Solução:**
```bash
# Ver o que está usando porta 8003
sudo lsof -i :8003

# Matar processo antigo
sudo kill -9 <PID>

# Ou mudar porta em deploy/gunicorn.conf.py
sudo nano deploy/gunicorn.conf.py
# bind = "127.0.0.1:8001"  # mudar para 8001

# E atualizar nginx também
sudo nano /etc/nginx/sites-available/wifi-portal-teste
# proxy_pass http://127.0.0.1:8001;

# Recarregar
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl restart portal-cautivo
```

#### 1.4: Permissão negada ao escrever em data/

**Erro:**
```
PermissionError: [Errno 13] Permission denied: 'data/access_log.csv'
```

**Solução:**
```bash
# Mudar ownership para www-data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/logs

# Verificar permissões
ls -la /var/www/wifi-portal-teste/data/
# Deve mostrar: drwxr-x--- www-data www-data

# Se ainda não funcionar, expandir permissões temporariamente
sudo chmod 777 /var/www/wifi-portal-teste/data
sudo systemctl restart portal-cautivo

# Depois restaurar segurança
sudo chmod 750 /var/www/wifi-portal-teste/data
```

---

## ❌ Erro: "Redis Connection Refused"

### Sintomas
```
ConnectionRefusedError: [Errno 111] Connection refused
redis.exceptions.ConnectionError: Error -2 connecting to localhost:6379
```

### Diagnóstico

```bash
# Redis está rodando?
sudo systemctl status redis-server

# Redis responde?
redis-cli ping
# Deve responder: PONG

# Ver porta
sudo ss -tulpn | grep 6379
```

### Solução

```bash
# Se não está instalado:
sudo apt install redis-server -y

# Ativar e iniciar
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Testar
redis-cli ping

# Se ainda falhar:
sudo journalctl -u redis-server -n 20

# Ou simplesmente remover REDIS_URL do .env.local para usar fallback in-memory
nano /var/www/wifi-portal-teste/.env.local
# Comentar: # REDIS_URL=redis://localhost:6379/0

sudo systemctl restart portal-cautivo
```

---

## ❌ Erro: "Docker Compose não inicia"

### Sintomas
```
ERROR: Service 'app' failed to build
ERROR: The image for the service you're trying to recreate has been removed
```

### Solução

```bash
# Limpar imagens antigas
docker-compose down -v

# Rebuildar
docker-compose build --no-cache

# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f app
```

### Se a porta 5000 já estiver em uso

```bash
# Ver o que está usando
sudo lsof -i :5000

# Ou mudar porta em docker-compose.yml
nano docker-compose.yml
# Mudar: "5000:5000" para "5001:5000"

docker-compose restart
```

---

### Sintomas
```
502 Bad Gateway
nginx/1.18.0
```

### Diagnóstico

```bash
# 1. Gunicorn está rodando?
sudo systemctl status portal-cautivo
ps aux | grep gunicorn

# 2. Gunicorn está respondendo localmente?
curl -v http://127.0.0.1:8003/login

# 3. Nginx config está ok?
sudo nginx -t

# 4. Ver erro no nginx
sudo tail -30 /var/log/nginx/wifi-portal-teste_error.log
sudo tail -30 /var/log/nginx/error.log
```

### Causas Comuns e Soluções

#### 2.1: Gunicorn caiu ou não está respondendo

**Solução:**
```bash
# Reiniciar
sudo systemctl restart portal-cautivo
sleep 3

# Verificar se levantou
sudo systemctl status portal-cautivo
curl -v http://127.0.0.1:8003/login

# Se continuar caindo, ver logs
sudo journalctl -u portal-cautivo -f
```

#### 2.2: Nginx não consegue conectar em Gunicorn

**Erro em nginx error.log:**
```
connect() failed (111: Connection refused)
upstream timed out (110: Connection timed out)
```

**Solução:**
```bash
# Verificar que proxy_pass no nginx está correto
sudo cat /etc/nginx/sites-available/wifi-portal-teste | grep proxy_pass
# Deve ser: proxy_pass http://127.0.0.1:8003;

# Testar conexão manualmente
curl -v http://127.0.0.1:8003/

# Se não funciona, porta pode estar errada
# Verificar gunicorn.conf.py
cat deploy/gunicorn.conf.py | grep bind
```

#### 2.3: Timeout entre Nginx e Gunicorn

**Erro em nginx error.log:**
```
upstream timed out (110: Connection timed out)
```

**Solução:**
```bash
# Aumentar timeout em nginx
sudo nano /etc/nginx/sites-available/wifi-portal-teste

# Adicionar ou atualizar:
proxy_connect_timeout 30s;
proxy_send_timeout 30s;
proxy_read_timeout 30s;

# Testar
sudo nginx -t
sudo systemctl restart nginx
```

#### 2.4: Gunicorn workers travando

**Solução:**
```bash
# Ver workers
ps aux | grep gunicorn | grep -v grep

# Se há muitos processos ou alguns "defunct", reiniciar
sudo systemctl restart portal-cautivo

# Se continua travando:
# 1. Aumentar workers em deploy/gunicorn.conf.py
# 2. Aumentar timeout
# 3. Ver logs para identif memory leak

# Ver uso de memória
top -p $(pgrep -f gunicorn | tr '\n' ',' | sed 's/,$//')
```

---

## ❌ Erro: "SSL Certificate Error"

### Sintomas
```
NET::ERR_CERT_AUTHORITY_INVALID
SSL certificate problem
```

### Diagnóstico

```bash
# Checar certificado
sudo certbot certificates

# Testar SSL
openssl s_client -connect seu-dominio.com:443

# Ver data de expiração
echo | openssl s_client -servername seu-dominio.com -connect seu-dominio.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Causas Comuns e Soluções

#### 3.1: Certificado expirado

**Solução:**
```bash
# Renovar manualmente
sudo certbot renew --force-renewal

# Testar renovação automática
sudo certbot renew --dry-run

# Verificar que certbot.timer está ativo
sudo systemctl status certbot.timer
```

#### 3.2: Domínio não aponta para este servidor

**Erro ao obter certificado:**
```
Certbot failed to authenticate
```

**Solução:**
```bash
# Verificar DNS
nslookup seu-dominio.com
dig seu-dominio.com

# Deve retornar IP deste servidor

# Se não, atualizar DNS no registrador:
# A seu-dominio.com -> seu-ip-publico

# Aguardar propagação (até 48h)
# Depois tentar novamente
sudo certbot certonly --standalone -d seu-dominio.com
```

#### 3.3: Nginx não está usando certificado correto

**Solução:**
```bash
# Verificar configuração nginx
sudo cat /etc/nginx/sites-available/wifi-portal-teste | grep ssl_certificate

# Deve apontar para:
# ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.key;

# Se caminhos estiverem errados, editar
sudo nano /etc/nginx/sites-available/wifi-portal-teste

# Testar e recarregar
sudo nginx -t
sudo systemctl restart nginx
```

---

## ❌ Erro: "Connection Refused / Cannot Connect"

### Sintomas
```
curl: (7) Failed to connect
Connection refused
```

### Diagnóstico

```bash
# 1. Servidor web está rodando?
sudo systemctl status nginx
sudo systemctl status portal-cautivo

# 2. Porta 443 está aberta?
sudo ufw status
ss -tulpn | grep 443

# 3. Firewall permite?
sudo iptables -L -n | grep 443
```

### Causas Comuns e Soluções

#### 4.1: Nginx não está rodando

**Solução:**
```bash
sudo systemctl start nginx
sudo systemctl status nginx

# Se der erro, verificar configuração
sudo nginx -t
```

#### 4.2: Porta bloqueada por firewall

**Solução:**
```bash
# Verificar regras
sudo ufw status
sudo ufw status numbered

# Se 443 não está permitida, adicionar
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# Recarregar
sudo ufw reload
```

#### 4.3: Domínio não aponta para servidor

**Solução:**
```bash
# Testar DNS
nslookup seu-dominio.com
dig seu-dominio.com A

# Se não retornar seu IP, atualizar DNS no registrador
# Aguardar propagação (até 48h)
# Testar com:
curl -I https://seu-dominio.com
```

---

## ❌ Erro: "Permission Denied" ao Escrever Dados

### Sintomas
```
PermissionError: [Errno 13] Permission denied: 'data/access_log.csv'
PermissionError: [Errno 13] Permission denied: 'logs/app.log'
```

### Diagnóstico

```bash
# Verificar owner
ls -la /var/www/wifi-portal-teste/data/
ls -la /var/www/wifi-portal-teste/logs/

# Deve ser: www-data www-data

# Verificar permissões
stat /var/www/wifi-portal-teste/data/
```

### Solução

```bash
# Corrigir ownership
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/logs

# Corrigir permissões
sudo chmod 750 /var/www/wifi-portal-teste/data
sudo chmod 750 /var/www/wifi-portal-teste/logs

# Criar arquivos se não existirem
sudo -u www-data touch /var/www/wifi-portal-teste/data/access_log.csv
sudo -u www-data touch /var/www/wifi-portal-teste/logs/app.log

# Restart
sudo systemctl restart portal-cautivo

# Verificar
curl -s -k https://seu-dominio.com/login  # deve funcionar
tail -f /var/www/wifi-portal/logs/app.log  # deve ter novos logs
```

---

## ❌ Erro: "Too Many Login Attempts"

### Sintomas
```
Muitas tentativas de login. Tente novamente mais tarde.
```

### Causa

Rate limiting foi acionado após 5 tentativas de login em 1 hora.

### Solução

```bash
# Aguardar 1 hora (limite reseta)
# Ou

# Reiniciar aplicação (reseta memória de tentativas)
sudo systemctl restart portal-cautivo

# Ou

# Aumentar limite em security.py
# rate_limit_admin decorator (linha ~190)
# Aumentar "5" para número maior

# E redeploy
```

---

## ❌ Erro: "Logs Não São Criados"

### Sintomas
```
tail: cannot open 'logs/app.log' for reading: No such file or directory
```

### Diagnóstico

```bash
# Verificar se diretório logs existe
ls -la /var/www/wifi-portal/ | grep logs

# Se não existe, criar
mkdir -p /var/www/wifi-portal/logs
sudo chown www-data:www-data /var/www/wifi-portal/logs
sudo chmod 750 /var/www/wifi-portal/logs
```

### Solução

```bash
# Se logs estão em outro lugar
find /var/www/wifi-portal -name "*.log" 2>/dev/null

# Ou ver onde logging está configurado
grep -r "FileHandler" /var/www/wifi-portal/*.py

# Criar arquivo de log manualmente
sudo -u www-data touch /var/www/wifi-portal/logs/app.log

# Restart
sudo systemctl restart portal-cautivo
```

---

## ❌ Erro: "Logrotate Não Está Funcionando"

### Sintomas
```
/var/www/wifi-portal/logs/app.log
/var/www/wifi-portal/logs/app.log.1
/var/www/wifi-portal/logs/app.log.2
... não aparecem após 1+ dias
```

### Diagnóstico

```bash
# Testar configuração (dry-run)
sudo logrotate -d /etc/logrotate.d/wifi-portal

# Ver se arquivo existe
ls -la /etc/logrotate.d/wifi-portal

# Ver logs do logrotate
grep logrotate /var/log/syslog  # Ubuntu
grep logrotate /var/log/messages  # CentOS
```

### Solução

```bash
# Forçar rotação (se necessário para teste)
sudo logrotate -f /etc/logrotate.d/wifi-portal

# Verificar resultado
ls -la /var/www/wifi-portal/logs/

# Se arquivo de config está errado, corrigir
sudo nano /etc/logrotate.d/wifi-portal

# Exemplo correto:
# /var/www/wifi-portal/logs/*.log {
#     daily
#     rotate 90
#     compress
#     missingok
#     notifempty
#     create 0640 www-data www-data
# }

# Recarregar
sudo systemctl restart logrotate  # ou restart cron
```

---

## ❌ Erro: "Admin Password Não Funciona"

### Sintomas
```
Login: admin
Senha: admin123
→ "Usuário ou senha incorretos"
```

### Solução

```bash
# 1. Verificar que users.csv existe
ls -la /var/www/wifi-portal/data/users.csv

# 2. Se não existe, será criado automaticamente na primeira acessão
#    Aguarde e tente novamente

# 3. Se exists, resetar password manualmente
cd /var/www/wifi-portal
source .venv/bin/activate

python3 << 'EOF'
import csv
from werkzeug.security import generate_password_hash

users_file = 'data/users.csv'
users = []

# Ler users
with open(users_file, 'r') as f:
    reader = csv.DictReader(f)
    users = list(reader)

# Encontrar admin e resetar
for user in users:
    if user['username'] == 'admin':
        user['password_hash'] = generate_password_hash('admin123')
        print(f"Admin password reset para admin123")

# Escrever
with open(users_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['username', 'password_hash', 'email', 'created_at', 'reset_token', 'reset_expires'])
    writer.writeheader()
    writer.writerows(users)

print("✓ Password resetado")
EOF

# 4. Restart
sudo systemctl restart portal-cautivo

# 5. Tentar login novamente
```

---

## ❌ Erro: "Aplicação Muito Lenta"

### Sintomas
```
Respostas demoram >5s
Timeouts frequentes
```

### Diagnóstico

```bash
# 1. Ver uso de memória
top -p $(pgrep -f gunicorn | tr '\n' ',' | sed 's/,$//')

# 2. Ver uso de CPU
top -b -n 1 | head -10

# 3. Ver conexões ativas
ss -tulpn | grep 8003

# 4. Ver acessos/segundo nos logs
tail -100 /var/www/wifi-portal/logs/app.log | grep "POST\|GET" | wc -l
```

### Soluções

```bash
# 1. Aumentar workers (se CPU < 80%)
sudo nano deploy/gunicorn.conf.py
# workers = 8  # aumentar de 4

# 2. Aumentar timeout (se conexão lenta)
# timeout = 60  # aumentar de 30

# 3. Implementar Redis cache (futuro)

# 4. Revisar queries em CSV (se dataset grande)
# Considerar PostgreSQL

# 5. Restart
sudo systemctl daemon-reload
sudo systemctl restart portal-cautivo
```

---

## ❌ Erro: "Dados Corrompidos / CSV Inválido"

### Sintomas
```
Error reading CSV: _csv.Error: unexpected end of data
```

### Diagnóstico

```bash
# Verificar arquivo
file /var/www/wifi-portal/data/access_log.csv

# Tentar ler
head -5 /var/www/wifi-portal/data/access_log.csv

# Verificar com Python
python3 -c "import csv; list(csv.DictReader(open('data/access_log.csv')))"
```

### Solução

```bash
# 1. Backup do arquivo corrompido
sudo cp /var/www/wifi-portal/data/access_log.csv /var/www/wifi-portal/data/access_log.csv.bak

# 2. Criar novo arquivo vazio (vai reconstruir headers)
sudo -u www-data touch /var/www/wifi-portal/data/access_log.csv

# 3. Se had dados válidos em .bak, recuperar
# (manual: grep e import)

# 4. Reiniciar
sudo systemctl restart portal-cautivo

# 5. Em futuro, usar app/locks.py para evitar corrupção
```

---

## 📞 Quando Nada Funciona

### Passo 1: Coletar Informações

```bash
# Versão do SO
uname -a

# Versão Python
python3 --version

# Status dos serviços
sudo systemctl status portal-cautivo
sudo systemctl status nginx

# Últimos 50 linhas de logs
sudo journalctl -u portal-cautivo -n 50
sudo tail -50 /var/log/nginx/wifi-portal_error.log

# Testar conectividade
curl -v https://seu-dominio.com/login 2>&1 | head -30
```

### Passo 2: Abrir Issue no Repositório

Criar issue com:

```markdown
## Erro: [Descrever o erro]

### Ambiente
- SO: ubuntu 20.04
- Python: 3.9.2
- Stack: Gunicorn 21.0 + Nginx 1.18

### Passo para Reproduzir
1. ...
2. ...

### Logs
```
<colar saída de journalctl -u portal-cautivo>
```

### Resultado Esperado
...

### Resultado Atual
...
```

---

**Última atualização:** Janeiro 2026
