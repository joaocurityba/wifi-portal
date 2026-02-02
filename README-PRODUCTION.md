# 🚀 Guia de Deploy em Produção com Docker + SSL

## 📋 Pré-requisitos

1. Servidor Linux (Ubuntu 20.04+ recomendado)
2. Docker e Docker Compose instalados
3. Domínio configurado apontando para o IP do servidor
4. Portas 80 e 443 abertas no firewall

## 🔧 Instalação Rápida

### 1. Instalar Docker (se necessário)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin -y
```

### 2. Clonar o repositório

```bash
cd /var/www
git clone <seu-repo> wifi-portal
cd wifi-portal
```

### 3. Configurar variáveis de ambiente

```bash
# Copiar template
cp .env.prod .env.local

# Gerar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Editar .env.local e preencher:
nano .env.local
# - SECRET_KEY (cole a chave gerada acima)
# - REDIS_PASSWORD (senha forte)
# - ALLOWED_HOSTS (seu-dominio.com)
```

### 4. Configurar SSL

```bash
# Dar permissão de execução
chmod +x deploy/setup-ssl.sh

# Executar script (substitua seu-dominio.com)
sudo bash deploy/setup-ssl.sh seu-dominio.com admin@seu-dominio.com
```

O script vai:
- ✅ Criar diretórios necessários
- ✅ Configurar Nginx
- ✅ Obter certificados Let's Encrypt
- ✅ Subir todos os containers
- ✅ Configurar renovação automática

### 5. Verificar

```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Verificar containers
docker-compose -f docker-compose.prod.yml ps

# Testar HTTPS
curl -I https://seu-dominio.com
```

## 📁 Estrutura de Arquivos

```
deploy/
├── nginx.docker.conf           # Nginx para DEV (HTTP apenas)
├── nginx.docker.prod.conf      # Nginx para PROD (HTTPS)
├── nginx.portal_cautivo.conf   # Nginx para PROD sem Docker
├── gunicorn.conf.py           # Config do Gunicorn
├── setup-ssl.sh               # Script de setup SSL
└── portal.service             # Systemd service (sem Docker)

docker-compose.yml              # Para desenvolvimento
docker-compose.prod.yml         # Para produção com SSL
.env.local                      # Variáveis de ambiente (não commitar!)
.env.prod                       # Template de variáveis
```

## 🔒 Segurança

### Antes de subir para produção:

1. ✅ **Mudar senha admin**
   - Edite [app_simple.py](app_simple.py#L107)
   - Ou conecte via shell e crie novo usuário

2. ✅ **Gerar SECRET_KEY única**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. ✅ **Configurar senha do Redis**
   - Já configurado em docker-compose.prod.yml
   - Defina REDIS_PASSWORD no .env.local

4. ✅ **Configurar firewall**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

## 🔄 Manutenção

### Atualizar aplicação

```bash
cd /var/www/wifi-portal
git pull
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Ver logs

```bash
# Todos
docker-compose -f docker-compose.prod.yml logs -f

# Apenas app
docker-compose -f docker-compose.prod.yml logs -f app

# Apenas nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Backup

```bash
# Backup manual
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/ .env.local

# Automatizar (cron)
crontab -e
# Adicione:
0 2 * * * cd /var/www/wifi-portal && tar -czf /backup/wifi-portal-$(date +\%Y\%m\%d).tar.gz data/ uploads/ .env.local
```

### Renovação SSL (automática)

Os certificados são renovados automaticamente pelo container `certbot`.
Para renovar manualmente:

```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

## 🆘 Troubleshooting

### Certificado SSL não funciona

```bash
# Verificar se o domínio aponta para o servidor
dig +short seu-dominio.com

# Ver logs do certbot
docker-compose -f docker-compose.prod.yml logs certbot

# Renovar manualmente
sudo certbot renew --force-renewal
```

### App não inicia

```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs app

# Entrar no container
docker-compose -f docker-compose.prod.yml exec app sh

# Verificar variáveis
docker-compose -f docker-compose.prod.yml exec app env
```

### Nginx 502 Bad Gateway

```bash
# Verificar se app está rodando
docker-compose -f docker-compose.prod.yml ps

# Ver logs do app
docker-compose -f docker-compose.prod.yml logs app

# Reiniciar
docker-compose -f docker-compose.prod.yml restart app nginx
```

### Health checks falhando

```bash
# Testar endpoint manualmente
curl http://localhost/healthz

# Ver status dos containers
docker-compose -f docker-compose.prod.yml ps

# Ver logs de healthcheck
docker inspect wifi-portal-app | grep -A 10 Health
```

## 📊 Monitoramento

### Verificar health status

```bash
# Status geral
docker-compose -f docker-compose.prod.yml ps

# Health de um container específico
docker inspect --format='{{json .State.Health}}' wifi-portal-app | jq
```

### Verificar recursos

```bash
# Uso de CPU/Memória
docker stats

# Espaço em disco
df -h
du -sh data/ logs/ uploads/
```

## 📞 Suporte

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para mais detalhes sobre problemas comuns.

## 🎯 Quick Commands

```bash
# Subir produção
docker-compose -f docker-compose.prod.yml up -d

# Parar produção
docker-compose -f docker-compose.prod.yml down

# Rebuild e restart
docker-compose -f docker-compose.prod.yml up -d --build

# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Backup rápido
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/
```
