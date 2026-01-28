#!/usr/bin/env python3
"""
Script de Configuração de Segurança para Portal Cautivo
Configura ambiente seguro e gera certificados auto-assinados
"""

import os
import sys
import subprocess
import secrets
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def gerar_chave_segura():
    """Gera uma chave secreta segura"""
    return secrets.token_urlsafe(64)

def criar_diretorios_seguranca():
    """Cria diretórios necessários com permissões seguras"""
    dirs = ['data', 'logs', 'ssl', 'backups']
    
    for dir_name in dirs:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        
        # Define permissões seguras (Linux/Unix)
        if os.name != 'nt':  # Não Windows
            os.chmod(path, 0o750)
            
    logger.info("Diretórios de segurança criados")

def gerar_certificado_ssl():
    """Gera certificado SSL auto-assinado para desenvolvimento"""
    try:
        ssl_dir = Path('ssl')
        cert_file = ssl_dir / 'portal_cautivo.crt'
        key_file = ssl_dir / 'portal_cautivo.key'
        
        if cert_file.exists() and key_file.exists():
            logger.info("Certificado SSL já existe")
            return
            
        # Comando OpenSSL para gerar certificado auto-assinado
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', str(key_file),
            '-out', str(cert_file), '-days', '365', '-nodes', '-subj',
            '/C=BR/ST=SP/L=Sao Paulo/O=Prefeitura/CN=localhost'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Define permissões seguras para chave privada
        if os.name != 'nt':
            os.chmod(key_file, 0o600)
            
        logger.info("Certificado SSL gerado com sucesso")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao gerar certificado SSL: {e}")
        logger.warning("Continuando sem HTTPS (apenas para desenvolvimento)")
    except FileNotFoundError:
        logger.warning("OpenSSL não encontrado. Instale OpenSSL para gerar certificados SSL")

def criar_arquivo_env():
    """Cria arquivo .env.local com configurações seguras"""
    env_content = f"""# Portal Cautivo Flask - Configurações de Produção
# Variáveis de ambiente para ambiente de produção

# Chave secreta para sessões e segurança da aplicação
SECRET_KEY={gerar_chave_segura()}

# Modo debug - SEMPRE False em produção
DEBUG=False

# Configurações de arquivos e diretórios
CSV_FILE=data/access_log.csv
USERS_FILE=data/users.csv

# Configurações de segurança
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT=1800
ALLOWED_HOSTS=localhost,127.0.0.1

# Configurações de logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Configurações de segurança avançada
RATE_LIMIT_ENABLED=True
RATE_LIMIT_STORAGE_URL=memory://
CSRF_PROTECTION=True
SECURE_HEADERS=True

# Configurações de HTTPS
SSL_CERT_PATH=ssl/portal_cautivo.crt
SSL_KEY_PATH=ssl/portal_cautivo.key

# Configurações de banco de dados (para futuro)
# DATABASE_URL=sqlite:///data/portal_cautivo.db
# DATABASE_URL=postgresql://user:password@localhost/portal_cautivo

# Configurações de email (para produção)
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=seu-email@prefeitura.com.br
# SMTP_PASSWORD=sua-senha-app
# SMTP_USE_TLS=True

# Configurações de cache (para futuro)
# CACHE_TYPE=redis
# CACHE_REDIS_URL=redis://localhost:6379/0

# Configurações de monitoramento (para futuro)
# SENTRY_DSN=https://sua-chave@sentry.io/projeto
# METRICS_ENABLED=True
"""
    
    env_file = Path('.env.local')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info("Arquivo .env.local criado com configurações seguras")
    else:
        logger.info("Arquivo .env.local já existe")

def instalar_dependencias():
    """Instala dependências de segurança"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        logger.info("Dependências instaladas com sucesso")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar dependências: {e}")

def criar_script_deploy():
    """Cria script de deploy seguro"""
    deploy_content = '''#!/bin/bash
# Script de Deploy Seguro para Portal Cautivo

set -e

echo "🚀 Iniciando deploy seguro do Portal Cautivo..."

# Verifica se está no ambiente correto
if [ "$EUID" -eq 0 ]; then
    echo "❌ Não execute como root. Use um usuário com permissões adequadas."
    exit 1
fi

# Cria ambiente virtual (opcional)
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
source venv/bin/activate

# Instala dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Configura permissões
echo "🔒 Configurando permissões..."
chmod 750 data/
chmod 640 data/*.csv 2>/dev/null || true
chmod 600 ssl/*.key 2>/dev/null || true

# Testa aplicação
echo "🧪 Testando aplicação..."
python3 -c "from app_simple import app; print('✅ Aplicação carregada com sucesso')"

echo "✅ Deploy concluído com sucesso!"
echo ""
echo "Para iniciar a aplicação:"
echo "  source venv/bin/activate"
echo "  python3 app_simple.py"
'''
    
    deploy_file = Path('deploy.sh')
    with open(deploy_file, 'w') as f:
        f.write(deploy_content)
    
    # Torna executável
    if os.name != 'nt':
        os.chmod(deploy_file, 0o755)
        
    logger.info("Script de deploy criado")

def criar_script_backup():
    """Cria script de backup automatizado"""
    backup_content = '''#!/usr/bin/env python3
"""
Script de Backup Automatizado para Portal Cautivo
Realiza backup dos dados e logs
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def criar_backup():
    """Cria backup dos dados críticos"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f"backup_{timestamp}.zip"
    
    with zipfile.ZipFile(backup_file, 'w') as backup_zip:
        # Arquivos de dados
        for file_path in ["data/access_log.csv", "data/users.csv", "data/access_log_encrypted.json"]:
            if Path(file_path).exists():
                backup_zip.write(file_path, arcname=Path(file_path).name)
        
        # Logs
        logs_dir = Path("logs")
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                backup_zip.write(log_file, arcname=f"logs/{log_file.name}")
    
    print(f"✅ Backup criado: {backup_file}")
    
    # Mantém apenas os últimos 10 backups
    backups = sorted(backup_dir.glob("backup_*.zip"))
    for old_backup in backups[:-10]:
        old_backup.unlink()
        print(f"🗑️  Backup antigo removido: {old_backup}")

if __name__ == "__main__":
    criar_backup()
'''
    
    backup_file = Path('backup.py')
    with open(backup_file, 'w') as f:
        f.write(backup_content)
        
    logger.info("Script de backup criado")

def main():
    """Função principal de configuração"""
    print("🔒 Configurando ambiente seguro para Portal Cautivo...")
    print("=" * 60)
    
    # Passos de configuração
    criar_diretorios_seguranca()
    criar_arquivo_env()
    gerar_certificado_ssl()
    criar_script_deploy()
    criar_script_backup()
    
    print("\n✅ Configuração de segurança concluída!")
    print("\nPróximos passos:")
    print("1. Instale as dependências: pip install -r requirements.txt")
    print("2. Inicie a aplicação: python app_simple.py")
    print("3. Acesse o painel admin: http://localhost:5000/admin/login")
    print("   - Usuário: admin")
    print("   - Senha: admin123 (ALTERE IMEDIATAMENTE!)")
    print("\n⚠️  Lembre-se de:")
    print("- Alterar as credenciais padrão")
    print("- Configurar HTTPS em produção")
    print("- Realizar backups regulares")
    print("- Monitorar logs de segurança")

if __name__ == "__main__":
    main()