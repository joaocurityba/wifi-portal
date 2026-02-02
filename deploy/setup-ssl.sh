#!/bin/bash
# Script para configurar SSL com Let's Encrypt no Docker
# Usage: sudo bash deploy/setup-ssl.sh seu-dominio.com

set -e

DOMAIN=$1
EMAIL=${2:-admin@${DOMAIN}}

if [ -z "$DOMAIN" ]; then
    echo "❌ Erro: Domínio não fornecido"
    echo "Usage: sudo bash $0 seu-dominio.com [email@example.com]"
    exit 1
fi

echo "🚀 Configurando SSL para $DOMAIN..."
echo "📧 Email: $EMAIL"

# 1. Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p certbot/www
mkdir -p logs/nginx

# 2. Substituir DOMAIN_NAME no nginx config
echo "🔧 Configurando Nginx..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/DOMAIN_NAME/$DOMAIN/g" deploy/nginx.docker.prod.conf
    sed -i '' "s/server_name _;/server_name $DOMAIN www.$DOMAIN;/g" deploy/nginx.docker.prod.conf
else
    # Linux
    sed -i "s/DOMAIN_NAME/$DOMAIN/g" deploy/nginx.docker.prod.conf
    sed -i "s/server_name _;/server_name $DOMAIN www.$DOMAIN;/g" deploy/nginx.docker.prod.conf
fi

# 3. Primeiro, subir apenas HTTP para validação Let's Encrypt
echo "🌐 Subindo containers em modo HTTP (para validação)..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Aguardar nginx iniciar
sleep 5

# 4. Obter certificados SSL
echo "🔐 Obtendo certificados SSL do Let's Encrypt..."
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# 5. Reiniciar Nginx com SSL
echo "♻️  Reiniciando Nginx com SSL..."
docker-compose -f docker-compose.prod.yml restart nginx

# 6. Subir todos os containers
echo "🚀 Subindo todos os containers..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ SSL configurado com sucesso!"
echo "🌐 Acesse: https://$DOMAIN"
echo ""
echo "📋 Próximos passos:"
echo "   1. Verifique se está funcionando: curl -I https://$DOMAIN"
echo "   2. Configure renovação automática (já está configurada via container certbot)"
echo "   3. Teste o site no navegador"
echo ""
echo "🔄 Renovação automática: Os certificados serão renovados automaticamente a cada 12h"