#!/usr/bin/env python3
"""
Script de Inicialização Segura para Portal Cautivo
Configura HTTPS, logging avançado e monitoramento
"""

import os
import sys
import ssl
import logging
from pathlib import Path
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa a aplicação
from app_simple import app

def configurar_logging():
    """Configura logging avançado"""
    # Cria diretório de logs
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
            logging.FileHandler(log_dir / 'security.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Configura logger de segurança
    security_logger = logging.getLogger('security')
    security_handler = logging.FileHandler(log_dir / 'security_events.log', encoding='utf-8')
    security_handler.setFormatter(logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    ))
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def verificar_seguranca():
    """Verifica requisitos de segurança"""
    logger = configurar_logging()
    
    # Verifica SECRET_KEY
    secret_key = app.config.get('SECRET_KEY', '')
    if len(secret_key) < 32:
        logger.warning("SECRET_KEY muito curta. Use uma chave de pelo menos 32 caracteres.")
        return False
    
    # Verifica arquivos críticos
    critical_files = [
        'data/users.csv',
        'ssl/portal_cautivo.crt',
        'ssl/portal_cautivo.key'
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            logger.warning(f"Arquivo crítico ausente: {file_path}")
    
    # Verifica permissões (Linux/Unix)
    if os.name != 'nt':
        import stat
        try:
            key_file = Path('ssl/portal_cautivo.key')
            if key_file.exists():
                file_stat = key_file.stat()
                if file_stat.st_mode & stat.S_IRWXG or file_stat.st_mode & stat.S_IRWXO:
                    logger.warning("Chave SSL com permissões muito abertas. Use chmod 600.")
        except:
            pass
    
    logger.info("Verificação de segurança concluída")
    return True

def criar_contexto_ssl():
    """Cria contexto SSL para HTTPS"""
    try:
        ssl_dir = Path('ssl')
        cert_file = ssl_dir / 'portal_cautivo.crt'
        key_file = ssl_dir / 'portal_cautivo.key'
        
        if cert_file.exists() and key_file.exists():
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(cert_file), str(key_file))
            return context
        else:
            print("⚠️  Certificado SSL não encontrado. Iniciando em HTTP...")
            return None
    except Exception as e:
        print(f"⚠️  Erro ao carregar SSL: {e}. Iniciando em HTTP...")
        return None

def iniciar_aplicacao():
    """Inicia a aplicação com configurações seguras"""
    logger = configurar_logging()
    
    # Verifica segurança
    if not verificar_seguranca():
        print("⚠️  Avisos de segurança detectados. Consulte os logs para detalhes.")
    
    # Configurações de host e porta
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    # Cria contexto SSL
    ssl_context = criar_contexto_ssl()
    
    # Configurações de debug
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Iniciando Portal Cautivo em {host}:{port}")
    if ssl_context:
        logger.info("HTTPS habilitado")
    else:
        logger.warning("HTTPS desabilitado - use apenas para desenvolvimento")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            ssl_context=ssl_context,
            threaded=True,  # Permite múltiplas requisições simultâneas
            use_reloader=False  # Desativa reloader em produção
        )
    except KeyboardInterrupt:
        logger.info("Aplicação encerrada pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        raise

if __name__ == '__main__':
    iniciar_aplicacao()