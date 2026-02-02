# 🚀 Guia Completo de Deploy em Produção

Guia passo a passo para implantar o Portal Cativo em **Ubuntu Server 20.04+** com Docker, SSL e alta disponibilidade.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Servidor](#preparação-do-servidor)
3. [Instalação do Docker](#instalação-do-docker)
4. [Clone e Configuração](#clone-e-configuração)
5. [Configuração de Variáveis](#configuração-de-variáveis)
6. [Setup SSL (Let's Encrypt)](#setup-ssl-lets-encrypt)
7. [Deploy da Aplicação](#deploy-da-aplicação)
8. [Configuração de Firewall](#configuração-de-firewall)
9. [Verificação e Testes](#verificação-e-testes)
10. [Backup Automático](#backup-automático)
11. [Monitoramento](#monitoramento)
12. [Manutenção](#manutenção)

---

## 📌 Pré-requisitos

### **Hardware Recomendado**
- **CPU:** 2 cores (mínimo 1 core)
- **RAM:** 4GB (mínimo 2GB)
- **Disco:** 20GB SSD
- **Rede:** 100Mbps

### **Software**
- Ubuntu Server 20.04 LTS ou 22.04 LTS
- Acesso SSH com sudo
- Domínio configurado (ex: wifi.prefeitura.com.br)
- DNS apontando para IP do servidor

### **Portas Necessárias**
- `22` - SSH
- `80` - HTTP (redirect para HTTPS)
- `443` - HTTPS

---

## 1️⃣ Preparação do Servidor

### **Conectar via SSH**

```bash
ssh usuario@IP_DO_SERVIDOR
```

### **Atualizar Sistema**

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar utilitários básicos
sudo apt install -y curl wget git nano htop ufw
```

### **Configurar Timezone**

```bash
# Listar timezones
timedatectl list-timezones | grep Sao_Paulo

# Configurar timezone (exemplo: São Paulo)
sudo timedatectl set-timezone America/Sao_Paulo

# Verificar
timedatectl
```

### **Configurar Hostname (Opcional)**

```bash
# Definir hostname
sudo hostnamectl set-hostname wifi-portal

# Editar /etc/hosts
sudo nano /etc/hosts
# Adicionar:
# 127.0.0.1 wifi-portal
```

---

## 2️⃣ Instalação do Docker

### **Remover Versões Antigas (se existir)**

```bash
sudo apt remove docker docker-engine docker.io containerd runc -y
```

### **Instalar Docker (Método Oficial)**

```bash
# Baixar script de instalação
curl -fsSL https://get.docker.com -o get-docker.sh

# Executar instalação
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Habilitar docker no boot
sudo systemctl enable docker
sudo systemctl start docker
```

### **Instalar Docker Compose**

```bash
# Método 1: Via apt (Ubuntu 22.04+)
sudo apt install docker-compose-plugin -y

# Método 2: Via curl (Ubuntu 20.04)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### **Verificar Instalação**

```bash
# Verificar Docker
docker --version
# Saída esperada: Docker version 24.0.x

# Verificar Docker Compose
docker-compose --version
# Saída esperada: Docker Compose version v2.x.x

# Testar Docker (sem sudo)
# IMPORTANTE: Relogar ou executar: newgrp docker
docker run hello-world
```

---

## 3️⃣ Clone e Configuração

### **Criar Diretório de Trabalho**

```bash
# Criar diretório para aplicação
sudo mkdir -p /var/www
sudo chown -R $USER:$USER /var/www
cd /var/www
```

### **Clonar Repositório**

```bash
# Opção 1: HTTPS
git clone https://github.com/seu-usuario/wifi-portal.git wifi-portal

# Opção 2: SSH (se configurou chave SSH)
git clone git@github.com:seu-usuario/wifi-portal.git wifi-portal

# Entrar no diretório
cd wifi-portal
```

### **Verificar Estrutura**

```bash
ls -la
# Deve mostrar: docker-compose.prod.yml, deploy/, app_simple.py, etc.
```

---

## 4️⃣ Configuração de Variáveis

### **Copiar Template**

```bash
cp .env.prod .env.local
```

### **Gerar SECRET_KEY**

```bash
# Gerar chave segura
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Saída (exemplo):
# nci7Rts0gViQn9h56H7v_P25BTJhTrQcSDmJMQYjhCSjT4Hw-eA4RWn_ZldsDYbg0_o0XcJ8IST5Eb3FbBHM5g
```

### **Gerar Senha do Redis**

```bash
# Gerar senha forte
openssl rand -base64 32

# Saída (exemplo):
# 8K+mZ5nQ7rY3pL6wN2vX9tH4jC1sD8fE
```

### **Editar .env.local**

```bash
nano .env.local
```

**Preencher com seus dados:**

```bash
# Portal Cautivo - Variáveis de Produção

# ============================================
# SEGURANÇA - OBRIGATÓRIO ALTERAR
# ============================================

# SECRET_KEY - Gere uma nova com: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=COLE_A_CHAVE_GERADA_AQUI

# Modo debug (SEMPRE False em produção)
DEBUG=False
FLASK_ENV=production

# ============================================
# REDIS
# ============================================

# Senha do Redis - Gere com: openssl rand -base64 32
REDIS_PASSWORD=COLE_A_SENHA_GERADA_AQUI
REDIS_URL=redis://:COLE_A_MESMA_SENHA_AQUI@redis:6379/0

# ============================================
# DOMÍNIO
# ============================================

# Substitua pelo seu domínio
ALLOWED_HOSTS=wifi.prefeitura.com.br,www.wifi.prefeitura.com.br

# ============================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================

MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT=1800
RATE_LIMIT_ENABLED=True
CSRF_PROTECTION=True
SECURE_HEADERS=True

# ============================================
# LOGGING
# ============================================

LOG_LEVEL=INFO
LOG_FILE=data/security.log

# ============================================
# ARQUIVOS
# ============================================

CSV_FILE=data/access_log.csv
USERS_FILE=data/users.csv
```

**Salvar:** `Ctrl+O`, Enter, `Ctrl+X`

### **Verificar Permissões**

```bash
# .env.local deve ter permissões restritas
chmod 600 .env.local

# Verificar
ls -la .env.local
# Saída: -rw------- 1 usuario usuario ... .env.local
```

---

## 5️⃣ Setup SSL (Let's Encrypt)

### **Verificar DNS**

```bash
# Verificar se domínio aponta para o servidor
dig +short wifi.prefeitura.com.br

# Deve retornar o IP do servidor
# Se não retornar, configure o DNS e aguarde propagação (até 48h)
```

### **Criar Diretórios Necessários**

```bash
# Criar diretórios para certificados
sudo mkdir -p /etc/letsencrypt
sudo mkdir -p certbot/www
mkdir -p logs/nginx
```

### **Executar Script de Setup SSL**

```bash
# Dar permissão de execução
chmod +x deploy/setup-ssl.sh

# Executar script
# Sintaxe: sudo bash deploy/setup-ssl.sh SEU_DOMINIO SEU_EMAIL
sudo bash deploy/setup-ssl.sh wifi.prefeitura.com.br admin@prefeitura.com.br
```

**O que o script faz:**
1. ✅ Cria diretórios necessários
2. ✅ Configura Nginx para o domínio
3. ✅ Sobe containers em modo HTTP
4. ✅ Obtém certificados Let's Encrypt
5. ✅ Reconfigura Nginx para HTTPS
6. ✅ Sobe todos os containers
7. ✅ Configura renovação automática

**Saída esperada:**

```
🚀 Configurando SSL para wifi.prefeitura.com.br...
📧 Email: admin@prefeitura.com.br
📁 Criando diretórios...
🔧 Configurando Nginx...
🌐 Subindo containers em modo HTTP (para validação)...
🔐 Obtendo certificados SSL do Let's Encrypt...
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Successfully received certificate.
♻️  Reiniciando Nginx com SSL...
🚀 Subindo todos os containers...
✅ SSL configurado com sucesso!
🌐 Acesse: https://wifi.prefeitura.com.br
```

---

## 6️⃣ Deploy da Aplicação

### **Método Automático (Recomendado)**

Se executou o script SSL acima, a aplicação já está rodando!

### **Método Manual**

```bash
# Subir containers em produção
docker-compose -f docker-compose.prod.yml up -d --build

# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Pressione Ctrl+C para sair dos logs
```

### **Verificar Status dos Containers**

```bash
# Ver containers rodando
docker-compose -f docker-compose.prod.yml ps

# Saída esperada:
# NAME                  STATUS          PORTS
# wifi-portal-app       Up (healthy)    5000/tcp
# wifi-portal-nginx     Up (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# wifi-portal-redis     Up (healthy)    6379/tcp
# wifi-portal-certbot   Up              -
```

---

## 7️⃣ Configuração de Firewall

### **Configurar UFW**

```bash
# Permitir SSH (IMPORTANTE FAZER PRIMEIRO!)
sudo ufw allow 22/tcp

# Permitir HTTP e HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Habilitar firewall
sudo ufw enable

# Verificar status
sudo ufw status verbose
```

**Saída esperada:**

```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

### **Configuração Avançada (Opcional)**

```bash
# Limitar tentativas SSH (proteção contra brute force)
sudo ufw limit 22/tcp

# Permitir apenas IPs específicos para SSH
sudo ufw delete allow 22/tcp
sudo ufw allow from IP_DO_SEU_ESCRITORIO to any port 22

# Verificar
sudo ufw status numbered
```

---

## 8️⃣ Verificação e Testes

### **Testar Health Check**

```bash
# Teste local
curl -I http://localhost/healthz

# Teste externo
curl -I https://wifi.prefeitura.com.br/healthz

# Saída esperada:
# HTTP/2 200
# {"service":"wifi-portal","status":"healthy"}
```

### **Testar Portal Público**

```bash
# Abrir no navegador
https://wifi.prefeitura.com.br/login

# Ou via curl
curl -I https://wifi.prefeitura.com.br/login
# Saída esperada: HTTP/2 200
```

### **Testar Painel Admin**

```bash
# URL
https://wifi.prefeitura.com.br/admin/login

# Credenciais padrão (MUDE IMEDIATAMENTE!)
# Usuário: admin
# Senha: admin123
```

### **Verificar Certificado SSL**

```bash
# Ver detalhes do certificado
openssl s_client -connect wifi.prefeitura.com.br:443 -servername wifi.prefeitura.com.br < /dev/null | openssl x509 -noout -dates

# Ou online
# https://www.ssllabs.com/ssltest/analyze.html?d=wifi.prefeitura.com.br
```

### **Testar Rate Limiting**

```bash
# Fazer múltiplas requisições
for i in {1..150}; do curl -s -o /dev/null -w "%{http_code}\n" https://wifi.prefeitura.com.br/login; done

# Deve retornar 200 até ~100 requisições, depois 429 (Too Many Requests)
```

---

## 9️⃣ Backup Automático

### **Criar Script de Backup**

```bash
# Criar script
sudo nano /usr/local/bin/backup-wifi-portal.sh
```

**Conteúdo:**

```bash
#!/bin/bash
# Backup automático do Portal Cativo

# Variáveis
APP_DIR="/var/www/wifi-portal"
BACKUP_DIR="/backup/wifi-portal"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Fazer backup
cd $APP_DIR
tar -czf $BACKUP_DIR/wifi-portal_$DATE.tar.gz \
    data/ \
    uploads/ \
    .env.local \
    logs/nginx/

# Remover backups antigos
find $BACKUP_DIR -name "wifi-portal_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log
echo "$(date): Backup criado: wifi-portal_$DATE.tar.gz" >> /var/log/wifi-portal-backup.log
```

**Salvar e dar permissão:**

```bash
sudo chmod +x /usr/local/bin/backup-wifi-portal.sh
```

### **Configurar Cron**

```bash
# Editar crontab
sudo crontab -e

# Adicionar linha (backup diário às 2h da manhã)
0 2 * * * /usr/local/bin/backup-wifi-portal.sh

# Salvar e sair
```

### **Testar Backup Manual**

```bash
sudo /usr/local/bin/backup-wifi-portal.sh

# Verificar
ls -lh /backup/wifi-portal/
```

---

## 🔟 Monitoramento

### **Health Checks Automáticos**

```bash
# Criar script de monitoramento
sudo nano /usr/local/bin/check-wifi-portal.sh
```

**Conteúdo:**

```bash
#!/bin/bash
# Verificação de saúde do Portal Cativo

HEALTH_URL="https://wifi.prefeitura.com.br/healthz"
LOG_FILE="/var/log/wifi-portal-health.log"

# Fazer requisição
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $HTTP_CODE -eq 200 ]; then
    echo "$(date): OK - Portal funcionando" >> $LOG_FILE
else
    echo "$(date): ERRO - Portal retornou $HTTP_CODE" >> $LOG_FILE
    # Opcional: Enviar alerta
    # mail -s "Portal Offline" admin@prefeitura.com.br < /dev/null
fi
```

**Configurar:**

```bash
sudo chmod +x /usr/local/bin/check-wifi-portal.sh

# Adicionar ao cron (verificar a cada 5 minutos)
sudo crontab -e
# Adicionar:
*/5 * * * * /usr/local/bin/check-wifi-portal.sh
```

### **Monitorar Recursos**

```bash
# Ver uso de recursos em tempo real
docker stats

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Ver logs de um serviço específico
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f redis
```

---

## 1️⃣1️⃣ Manutenção

### **Atualizar Aplicação**

```bash
cd /var/www/wifi-portal

# Backup antes de atualizar
sudo /usr/local/bin/backup-wifi-portal.sh

# Puxar atualizações
git pull

# Rebuild e restart
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar
docker-compose -f docker-compose.prod.yml ps
curl https://wifi.prefeitura.com.br/healthz
```

### **Ver Logs**

```bash
# Logs de todos os containers
docker-compose -f docker-compose.prod.yml logs -f

# Logs apenas do app
docker-compose -f docker-compose.prod.yml logs -f app

# Últimas 100 linhas
docker-compose -f docker-compose.prod.yml logs --tail=100

# Logs do sistema
tail -f /var/log/syslog
```

### **Reiniciar Containers**

```bash
# Reiniciar todos
docker-compose -f docker-compose.prod.yml restart

# Reiniciar apenas um
docker-compose -f docker-compose.prod.yml restart app
docker-compose -f docker-compose.prod.yml restart nginx
```

### **Limpar Docker**

```bash
# Remover containers parados
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Remover volumes não usados (CUIDADO!)
docker volume prune -f

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes -f
```

### **Renovar Certificado SSL (Manual)**

```bash
# Renovar certificado
docker-compose -f docker-compose.prod.yml exec certbot certbot renew

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Verificar validade
openssl s_client -connect wifi.prefeitura.com.br:443 -servername wifi.prefeitura.com.br < /dev/null | openssl x509 -noout -dates
```

---

## 📊 Comandos Úteis

### **Quick Reference**

```bash
# Status geral
docker-compose -f docker-compose.prod.yml ps

# Subir
docker-compose -f docker-compose.prod.yml up -d

# Parar
docker-compose -f docker-compose.prod.yml down

# Rebuild
docker-compose -f docker-compose.prod.yml up -d --build

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl https://wifi.prefeitura.com.br/healthz

# Backup
sudo /usr/local/bin/backup-wifi-portal.sh

# Reiniciar
docker-compose -f docker-compose.prod.yml restart
```

---

## ⚠️ Segurança Pós-Deploy

### **Checklist de Segurança**

```bash
# 1. Verificar .env.local não está no Git
git ls-files .env.local
# Deve retornar vazio

# 2. Verificar permissões
ls -la .env.local
# Deve ser: -rw------- (600)

# 3. Verificar firewall
sudo ufw status
# Deve mostrar: Status: active

# 4. Verificar SSL
curl -I https://wifi.prefeitura.com.br
# Deve retornar: HTTP/2 200

# 5. Verificar health checks
docker-compose -f docker-compose.prod.yml ps
# Todos devem estar: Up (healthy)
```

### **Alterar Senha Admin**

```bash
# Conectar ao container
docker-compose -f docker-compose.prod.yml exec app bash

# Abrir Python
python

# Executar
from werkzeug.security import generate_password_hash
print(generate_password_hash('SUA_NOVA_SENHA_FORTE'))
# Copiar o hash gerado

# Editar data/users.csv e substituir o hash da senha
exit()
exit

# Reiniciar app
docker-compose -f docker-compose.prod.yml restart app
```

---

## 🆘 Troubleshooting Rápido

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING-NEW.md) para soluções completas.

| Problema | Solução Rápida |
|----------|----------------|
| Containers não sobem | `docker-compose -f docker-compose.prod.yml logs` |
| SSL não funciona | Verificar DNS e executar script novamente |
| 502 Bad Gateway | `docker-compose -f docker-compose.prod.yml restart app` |
| Health check falha | Verificar `/healthz` no navegador |
| Muito lento | `docker stats` para ver recursos |

---

## ✅ Próximos Passos

Após deploy bem-sucedido:

1. ✅ Configurar MikroTik para redirecionar para o portal
2. ✅ Testar fluxo completo de autenticação
3. ✅ Configurar backup externo (S3, etc)
4. ✅ Configurar monitoramento avançado (Prometheus, Grafana)
5. ✅ Treinar equipe de suporte

---

<p align="center">
  <strong>Portal Cativo pronto para produção! 🎉</strong>
</p>
