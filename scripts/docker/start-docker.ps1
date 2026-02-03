# Script para iniciar WiFi Portal com Docker

Write-Host "🐳 WiFi Portal - Iniciando com Docker" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Parar containers existentes
Write-Host "⏹️  Parando containers existentes..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Construir e iniciar
Write-Host "🔨 Construindo imagens..." -ForegroundColor Yellow
docker-compose build --no-cache

Write-Host "`n🚀 Iniciando containers..." -ForegroundColor Yellow
docker-compose up -d

# Aguardar containers iniciarem
Write-Host "`n⏳ Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status
Write-Host "`n📊 Status dos Containers:" -ForegroundColor Green
docker-compose ps

# Verificar logs
Write-Host "`n📝 Últimas linhas dos logs:" -ForegroundColor Green
docker-compose logs --tail=20

Write-Host "`n✅ Aplicação disponível em:" -ForegroundColor Green
Write-Host "   🌐 http://localhost" -ForegroundColor White
Write-Host "   🔐 Admin: http://localhost/admin/login" -ForegroundColor White
Write-Host "`n   Username: admin" -ForegroundColor Gray
Write-Host "   Password: admin123" -ForegroundColor Gray

Write-Host "`n📋 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f app     # Ver logs em tempo real" -ForegroundColor White
Write-Host "   docker-compose ps              # Ver status" -ForegroundColor White
Write-Host "   docker-compose down            # Parar tudo" -ForegroundColor White
Write-Host "   docker-compose restart app     # Reiniciar app" -ForegroundColor White
