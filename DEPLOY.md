# Portal Cativo - Guia de Deploy em Produção

Guia completo para implantar o Portal Cativo Flask em **Ubuntu 20.04+** com opções de **Docker Compose** ou **deployment manual**.

## 🚀 Opção Rápida: Docker Compose (Recomendado)

Se você tem **Docker e Docker Compose** instalados, a forma mais rápida é:

```bash
# 1. Clonar repositório
git clone <seu-repositorio-github> wifi-portal-teste
cd wifi-portal-teste

# 2. Configurar variáveis de ambiente
cp .env.template .env.local
nano .env.local  # Editar SECRET_KEY, ALLOWED_HOSTS, etc

# 3. Iniciar com Docker Compose
docker-compose up -d

# 4. Aplicação está rodando em http://localhost:5000
# Para produção: configure Nginx como reverse proxy (veja seção "Configurar Nginx" abaixo)
```

✅ Instala Redis + App automaticamente  
✅ Zero problemas de dependências  
✅ Perfeito para desenvolvimento e pequena produção  

**Quer deployment manual?** Siga para "Visão Geral" abaixo.

---

## 📋 Visão Geral (Deploy Manual)

Este guia cobre deployment em **Ubuntu 20.04+** com:
- **Gunicorn** WSGI server (porta 8003)
- **Nginx** reverse proxy + SSL termination
- **Systemd** service para orquestração e auto-restart
- **Let's Encrypt** para certificados HTTPS
- **Redis** (opcional) para rate limiting distribuído
- **File-locking atômico** para integridade de dados
- **Logrotate** com retenção de 90 dias
- **Firewall UFW** configurado

**Estrutura do deployment:**
```
Nginx (porta 443 HTTPS)
  ↓
Gunicorn (porta 8003, localhost apenas)
  ↓
Flask App (app_simple.py via wsgi.py)
  ↓
Dados (CSV/JSON criptografados em /var/www/wifi-portal-teste/data/)
```

**Tempo estimado:** 45-60 minutos em primeira vez.

---

## 🚀 Pré-requisitos (Deploy Manual)

Escolha UMA das opções abaixo:

### Opção A: Docker Compose (Recomendado)
```
- Docker 20.10+
- Docker Compose 1.29+
- Git
```

### Opção B: Deploy Manual (Ubuntu 20.04+)
```bash
# Verificar Python versão
python3 --version  # deve ser 3.9+

# Ter acesso SSH com sudo
# Domínio configurado ou IP público
# Apenas isso é necessário - vamos instalar o resto
```

---

## 🔧 Passo a Passo de Deploy (15 passos)

### Passo 1: Preparar Servidor e Clonar Repositório

```bash
# Update sistema
sudo apt update && sudo apt upgrade -y

# Criar diretório da aplicação
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www

# Clonar repositório
git clone <seu-repositorio-github> wifi-portal-teste
cd wifi-portal-teste

# Verificar estrutura
ls -la
# Deve mostrar: app_simple.py, wsgi.py, requirements.txt, deploy/, etc
```

### Passo 2: Criar Virtual Environment Python

```bash
# Criar venv
python3 -m venv .venv
source .venv/bin/activate

# Atualizar pip
pip install --upgrade pip setuptools wheel
```

### Passo 3: Instalar Dependências Python

```bash
# Instalar dependências do requirements.txt
pip install -r requirements.txt

# Instalar Gunicorn (não está em requirements.txt)
pip install gunicorn>=21.0.0

# Verificar que importa sem erros
python -c "from wsgi import app; print('✓ Aplicação carrega OK')"

# Se erro acima falhar, verificar arquivo .env.local em Passo 4
```

### Passo 4: Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.template .env.local

# Editar com seus valores
nano .env.local
```

**Valores críticos a alterar em `.env.local`:**

```bash
# Gerar SECRET_KEY único
python -c "import secrets; print(secrets.token_hex(32))"
# Copiar resultado INTEIRO e colar em SECRET_KEY=

# DEBUG deve ser False em produção
DEBUG=False

# Seu domínio ou IP público
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Admin password (mude IMEDIATAMENTE após primeiro login!)
ADMIN_PASSWORD=mude_na_primeira_acessao

# RECOMENDADO: Redis para rate limiting distribuído  
REDIS_URL=redis://localhost:6379/0

# OPCIONAL: Email para recuperação de senha
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# etc...
```

**Proteger arquivo:**

```bash
chmod 600 .env.local

# Verificar que .env.local está em .gitignore
grep "\.env\.local" .gitignore
```

### Passo 4.5: Instalar e Configurar Redis (Recomendado)

Redis é necessário para rate limiting distribuído e melhor performance:

```bash
# Instalar Redis
sudo apt install redis-server -y

# Iniciar e ativar no boot
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Testar que está rodando
redis-cli ping  # deve responder: PONG

# Verificar porta
sudo ss -tulpn | grep 6379
```

Se Redis falhar, aplicação continua com rate limiting in-memory (fallback automático).

### Passo 5: Criar Estrutura de Diretórios

```bash
# Criar diretórios de dados e logs
mkdir -p /var/www/wifi-portal-teste/logs /var/www/wifi-portal-teste/data

# Verificar
ls -la /var/www/wifi-portal-teste/
```

### Passo 6: Instalar e Configurar Nginx

```bash
# Instalar Nginx
sudo apt install nginx -y

# Copiar configuração exemplar
sudo cp deploy/nginx.portal_cautivo.conf /etc/nginx/sites-available/wifi-portal-teste

# Editar para seu domínio
sudo nano /etc/nginx/sites-available/wifi-portal-teste
# Substituir "seu-dominio.com" pelo seu domínio real
```

**Ativar site:**

```bash
# Criar symlink
sudo ln -sf /etc/nginx/sites-available/wifi-portal-teste /etc/nginx/sites-enabled/

# Desabilitar site padrão (se existir)
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t
# Deve mostrar: "syntax is ok" e "test is successful"

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar status
sudo systemctl status nginx
```

### Passo 7: Obter Certificado SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado (seu domínio deve estar apontando para este IP)
sudo certbot certonly --standalone -d seu-dominio.com

# Testar renovação automática (não renova, apenas testa)
sudo certbot renew --dry-run

# Ativar timer de renovação automática
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

**Verificar certificado:**

```bash
sudo certbot certificates
```

### Passo 8: Definir Permissões de Arquivos

```bash
# Transferir propriedade para www-data (usuário do Nginx/Gunicorn)
sudo chown -R www-data:www-data /var/www/wifi-portal-teste

# Definir permissões corretas
sudo chmod 750 /var/www/wifi-portal-teste
sudo chmod 750 /var/www/wifi-portal-teste/data
sudo chmod 750 /var/www/wifi-portal-teste/logs
sudo chmod 600 /var/www/wifi-portal-teste/.env.local

# Verificar
ls -ld /var/www/wifi-portal-teste
ls -la /var/www/wifi-portal-teste/.env.local
```

### Passo 9: Instalar Systemd Service

```bash
# Copiar arquivo de serviço
sudo cp deploy/portal.service /etc/systemd/system/portal-cautivo.service

# Recarregar systemd daemon
sudo systemctl daemon-reload

# Ativar serviço para iniciar automaticamente no boot
sudo systemctl enable portal-cautivo

# Iniciar serviço
sudo systemctl start portal-cautivo

# Verificar status (deve estar "active (running)")
sudo systemctl status portal-cautivo
```

**Se tiver erro, verificar logs:**

```bash
sudo journalctl -u portal-cautivo -n 30
```

### Passo 10: Configurar Logrotate (90 dias)

```bash
# Copiar configuração
sudo cp deploy/logrotate.conf /etc/logrotate.d/wifi-portal

# Testar (dry-run, não faz mudanças)
sudo logrotate -d /etc/logrotate.d/wifi-portal

# Logrotate é executado automaticamente pelo system (cron diário)
```

### Passo 11: Configurar Firewall

```bash
# Ativar UFW (Uncomplicated Firewall)
sudo ufw enable

# Permitir SSH, HTTP e HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redireciona para HTTPS)
sudo ufw allow 443/tcp  # HTTPS

# Verificar status
sudo ufw status
```

### Passo 12: Testar Aplicação

```bash
# Teste 1: Gunicorn está respondendo?
curl -s http://127.0.0.1:8003/login | head -20

# Teste 2: Nginx está respondendo (aguarde alguns segundos)?
sleep 3
curl -s https://seu-dominio.com/login | head -20

# Teste 3: No navegador
# Abra: https://seu-dominio.com/login
# Deve ver o formulário de login
# Credenciais padrão: admin / admin123
```

### Passo 13: Mudar Credenciais Padrão (OBRIGATÓRIO)

```bash
# CRÍTICO: Senha padrão é admin123, deve ser alterada IMEDIATAMENTE!

# Acessar painel admin
# https://seu-dominio.com/admin
# Login com: admin / admin123
# Clicar em "Perfil"
# Alterar senha para algo FORTE (mínimo 12 caracteres, misturado)
# Clicar "Salvar"
# Fazer logout e login novamente com nova senha
```

### Passo 14: Verificar Logs e Status

```bash
# Ver logs em tempo real
sudo journalctl -u portal-cautivo -f

# Em outro terminal, fazer requisição
curl https://seu-dominio.com/login

# Deveria aparecer linha de log mostrando a requisição
```

### Passo 15: Resumo de Verificação

```bash
# Verificar que tudo está rodando
sudo systemctl status portal-cautivo
sudo systemctl status nginx
redis-cli ping  # se instalou redis

# Verificar permissões
ls -la /var/www/wifi-portal-teste/.env.local

# Verificar dados
ls -la /var/www/wifi-portal-teste/data/
ls -la /var/www/wifi-portal-teste/logs/
```

Se tudo passou ✅, aplicação está pronta para produção!

---

## 🔐 Segurança: Alterações Obrigatórias

### 1. ✅ Mudar Credenciais Padrão

Após o primeiro login, **IMEDIATAMENTE**:

```bash
# Acessar https://seu-dominio.com/admin
# Alterar senha de admin123 para algo forte
# Salvar novo .env.local com ADMIN_PASSWORD se quiser redefini-lo via env
```

### 2. ✅ Verificar `.env.local`

```bash
# Confirmar que está fora do repositório (não versionado)
cd /var/www/wifi-portal-teste
cat .gitignore | grep env.local  # deve estar lá

# Verificar que contém valores únicos
sudo cat /var/www/wifi-portal-teste/.env.local | grep -E "^(SECRET_KEY|ENCRYPTION_SALT)="

# Cada ambiente DEVE ter SECRET_KEY e ENCRYPTION_SALT diferentes
```

### 3. ✅ Revisar Permissões de Arquivos Sensíveis

```bash
# .env.local deve ser -rw------- (600)
ls -la /var/www/wifi-portal-teste/.env.local

# data/ deve ser d-rwxr-x--- (750)
ls -ld /var/www/wifi-portal-teste/data

# Verificar owner
ls -la /var/www/wifi-portal-teste/ | grep -E "(data|logs|.env.local)"

# Tudo deve ser www-data:www-data
```

### 4. ✅ Verificar HTTPS está Ativo

```bash
# Acessar https://seu-dominio.com (com 's' em https)
# Certificado deve ser válido (Let's Encrypt)

# Teste CLI
curl -v https://seu-dominio.com/login 2>&1 | grep -i certificate
```

### 5. ✅ Verificar Headers de Segurança

```bash
# Nginx deve incluir:
curl -I https://seu-dominio.com | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"

# Saída deve mostrar estes headers
```

---

## 🔄 Operações Diárias

### Ver Status da Aplicação

```bash
sudo systemctl status portal-cautivo
```

### Restart da Aplicação (se necessário)

```bash
sudo systemctl restart portal-cautivo

# Aguarde 2-3 segundos
sleep 3
sudo systemctl status portal-cautivo
```

### Ver Logs em Tempo Real

```bash
# Logs do systemd
sudo journalctl -u portal-cautivo -f

# Logs da aplicação
tail -f /var/www/wifi-portal-teste/logs/app.log
tail -f /var/www/wifi-portal-teste/logs/security_events.log
```

### Monitorar Performance

```bash
# Conexões ativas na porta 8000 (Gunicorn)
netstat -tulpn 2>/dev/null | grep 8003

# Ou com ss
ss -tulpn | grep 8003

# Uso de memória
free -h

# Uso de CPU
top -b -n 1 | head -15

# Espaço em disco (importante para data/logs)
df -h /var/www/wifi-portal-teste
```

### Ver Estatísticas de Acesso

```bash
# Últimas 10 conexões
tail -10 /var/www/wifi-portal-teste/data/access_log.csv

# Contar acessos por dia (se tiver access_log)
cut -d',' -f6 /var/www/wifi-portal-teste/data/access_log.csv | sort | uniq -c
```

---

## 🆘 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'app_simple'"

```bash
# Verificar se .venv é activado
which python  # deve mostrar /var/www/wifi-portal-teste/.venv/bin/python

# Verificar que wsgi.py importa corretamente
source /var/www/wifi-portal-teste/.venv/bin/activate
python -c "from wsgi import app; print('OK')"

# Se ainda falhar, reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: "Permission denied" ao escrever em `data/`

```bash
# Problema: dados/logs não podem ser criados
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/data
sudo chown -R www-data:www-data /var/www/wifi-portal-teste/logs
sudo chmod 750 /var/www/wifi-portal-teste/data
sudo chmod 750 /var/www/wifi-portal-teste/logs

# Reiniciar
sudo systemctl restart portal-cautivo
```

### Nginx retorna "502 Bad Gateway"

```bash
# Gunicorn pode não estar rodando
sudo systemctl status portal-cautivo

# Ver erro específico
sudo journalctl -u portal-cautivo -n 20

# Reiniciar Gunicorn
sudo systemctl restart portal-cautivo

# Testar localmente
curl http://127.0.0.1:8000/login

# Verificar arquivo Nginx
sudo nginx -t
```

### SSL Certificate Error

```bash
# Ver certificados atuais
sudo certbot certificates

# Renovar manualmente (se próximo do vencimento)
sudo certbot renew --force-renewal

# Testar renovação automática (dry-run)
sudo certbot renew --dry-run

# Se der erro, ver log
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Aplicação muito lenta ou travando

```bash
# Verificar acessos simultâneos
ps aux | grep gunicorn | wc -l

# Ver uso de memória
top -p $(pgrep -f gunicorn | tr '\n' ',')

# Aumentar workers em /etc/systemd/system/portal-cautivo.service
# Aumentar timeout em deploy/gunicorn.conf.py
# Considerar Redis para cache

# Reiniciar após mudanças
sudo systemctl daemon-reload
sudo systemctl restart portal-cautivo
```

### Logrotate não está funcionando

```bash
# Testar configuração
sudo logrotate -d /etc/logrotate.d/wifi-portal-teste

# Forçar rotação (se necessário)
sudo logrotate -f /etc/logrotate.d/wifi-portal-teste

# Verificar que logs foram rotacionados
ls -la /var/www/wifi-portal-teste/logs/
```

---

## 📊 Monitoramento (Opcional)

### Instalar e Usar Htop para Monitorar em Tempo Real

```bash
sudo apt install htop -y
htop  # monitora recursos
# Pressione 'q' para sair
```

### Backup Automático Diário

```bash
# Criar script de backup
cat > /home/ubuntu/backup-wifi-portal.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/mnt/backup"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/wifi-portal-teste_$DATE.tar.gz /var/www/wifi-portal-teste/data /var/www/wifi-portal-teste/ssl
echo "Backup created: $BACKUP_DIR/wifi-portal_$DATE.tar.gz"
EOF

# Dar permissão
chmod +x /home/ubuntu/backup-wifi-portal.sh

# Adicionar ao crontab (executa diariamente às 2h)
sudo crontab -e
# Adicionar linha:
# 0 2 * * * /home/ubuntu/backup-wifi-portal.sh
```

### Email de Alertas (Opcional)

Se quiser receber alertas quando a aplicação cai:

```bash
# Criar script de verificação
cat > /home/ubuntu/check-portal.sh << 'EOF'
#!/bin/bash
if ! curl -sf https://seu-dominio.com/login > /dev/null; then
  echo "Portal está offline!" | mail -s "ALERTA: Portal Cautivo Offline" seu-email@example.com
  systemctl restart portal-cautivo
fi
EOF

# Adicionar ao crontab (verifica a cada 5 minutos)
sudo crontab -e
# */5 * * * * /home/ubuntu/check-portal.sh
```

---

## ✅ Checklist Final Antes de Produção

- [ ] Python 3.9+ instalado (`python3 --version`)
- [ ] Virtual environment criado e ativado
- [ ] `requirements.txt` instalado (`pip list | grep Flask`)
- [ ] `.env.local` criado e preenchido (não no git)
- [ ] `SECRET_KEY` gerado e único
- [ ] `ENCRYPTION_SALT` gerado e único
- [ ] Diretórios `data/`, `logs/`, `ssl/` criados com permissões corretas
- [ ] Nginx instalado e configurado
- [ ] SSL certificate obtido (Let's Encrypt)
- [ ] Systemd service instalado e habilitado
- [ ] Logrotate configurado (90 dias de retenção)
- [ ] Firewall configurado (portas 22, 80, 443 abertas)
- [ ] Acesso HTTPS bem-sucedido (https://seu-dominio.com)
- [ ] Admin password alterado de `admin123`
- [ ] Certificado é válido e vai renovar automaticamente
- [ ] Headers de segurança presentes (HSTS, CSP, etc)
- [ ] Logs estão sendo gerados (`tail -f /var/www/wifi-portal/logs/app.log`)
- [ ] Logrotate está funcionando (verifica dia 1 de cada mês)
- [ ] Backup automático configurado (opcional)

---

## 📝 Notas Importantes

### Data/Logs Location

Arquivos de dados e logs estão em `/var/www/wifi-portal/`:

```bash
/var/www/wifi-portal/
├── data/
│   ├── access_log.csv           # Log de acessos ao portal
│   ├── access_log_encrypted.json # Log com dados criptografados
│   └── users.csv                # Usuários do painel admin
├── logs/
│   ├── app.log                  # Logs da aplicação
│   ├── security_events.log      # Eventos de segurança
│   └── security.log             # Log de segurança geral
└── ssl/
    └── (certificados Let's Encrypt gerenciados por Certbot)
```

### 90-Day Log Retention

Logrotate rotaciona logs diariamente e mantém últimos **90 dias**:

```bash
# Ver configuração
cat /etc/logrotate.d/wifi-portal

# Logs são mantidos em:
# /var/www/wifi-portal/logs/app.log
# /var/www/wifi-portal/logs/app.log.1
# /var/www/wifi-portal/logs/app.log.2
# ... até app.log.90
```

---

## 🆘 Suporte

Se encontrar problemas:

1. **Verifique os logs:**
   ```bash
   sudo journalctl -u portal-cautivo -f
   tail -f /var/www/wifi-portal/logs/app.log
   ```

2. **Teste a aplicação localmente:**
   ```bash
   source /var/www/wifi-portal/.venv/bin/activate
   python -c "from wsgi import app; app.run()"
   ```

3. **Consulte este guia novamente** (seção Troubleshooting)

4. **Abra issue no repositório** com:
   - Versão do SO (`uname -a`)
   - Saída do comando problemático
   - Trecho dos logs
   - Contexto do que você estava tentando fazer

---

**Stack Deployment:** Python 3.9+ | Flask 2.3+ | Gunicorn 21+ | Nginx | Systemd | Let's Encrypt | Ubuntu 20.04+

**Última atualização:** Janeiro 2026
