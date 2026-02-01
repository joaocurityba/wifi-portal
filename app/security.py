#!/usr/bin/env python3
"""
Módulo de Segurança Avançada para Portal Cautivo
Implementa criptografia, rate limiting, validação avançada e headers de segurança
"""

import os
import csv
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any
from flask import request, session, flash, redirect, url_for, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    """Gerenciador de segurança avançada"""
    
    def __init__(self, app=None):
        self.app = app
        self.limiter = None
        self.cipher_suite = None
        # Não chama setup_encryption aqui, será chamado no init_app
        
    def init_app(self, app):
        """Inicializa o gerenciador de segurança com a aplicação Flask"""
        self.app = app
        self.setup_limiter()
        self.setup_encryption()
        self.setup_headers()
        
    def setup_limiter(self):
        """Configura o rate limiting"""
        storage_uri = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        if REDIS_AVAILABLE:
            try:
                self.limiter = Limiter(
                    app=self.app,
                    key_func=get_remote_address,
                    storage_uri=storage_uri,
                    default_limits=["1000 per hour", "100 per minute"]
                )
                logger.info("Rate limiting configured with Redis")
            except Exception as e:
                logger.warning(f"Redis not available, falling back to in-memory: {e}")
                self.limiter = Limiter(
                    app=self.app,
                    key_func=get_remote_address,
                    default_limits=["1000 per hour", "100 per minute"]
                )
        else:
            logger.warning("Redis not available, using in-memory storage")
            self.limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                default_limits=["1000 per hour", "100 per minute"]
            )
        
    def setup_encryption(self):
        """Configura a criptografia para dados sensíveis"""
        # Gera chave de criptografia baseada na SECRET_KEY
        secret_key = self.app.config.get('SECRET_KEY', 'fallback-key')
        password = secret_key.encode()
        salt = b'salt_123_portal_cautivo'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)
        
    def setup_headers(self):
        """Configura headers de segurança"""
        @self.app.after_request
        def set_security_headers(response):
            # Headers de segurança
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # Prevenção de cache para páginas sensíveis
            if request.endpoint in ['admin', 'admin_profile', 'admin_login']:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                
            return response
            
    def encrypt_data(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        if not data:
            return ''
        try:
            encrypted = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            return data
            
    def decrypt_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis"""
        if not encrypted_data:
            return ''
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            return encrypted_data
            
    def hash_sensitive_data(self, data: str) -> str:
        """Gera hash SHA-256 para dados sensíveis (para consultas)"""
        if not data:
            return ''
        return hashlib.sha256(data.encode()).hexdigest()
        
    def validate_strong_password(self, password: str) -> tuple[bool, str]:
        """Valida força da senha"""
        if len(password) < 8:
            return False, "A senha deve ter pelo menos 8 caracteres"
        
        if not re.search(r'[A-Z]', password):
            return False, "A senha deve conter pelo menos uma letra maiúscula"
            
        if not re.search(r'[a-z]', password):
            return False, "A senha deve conter pelo menos uma letra minúscula"
            
        if not re.search(r'\d', password):
            return False, "A senha deve conter pelo menos um número"
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "A senha deve conter pelo menos um caractere especial"
            
        return True, "Senha válida"
        
    def sanitize_input_advanced(self, text: str, max_length: int = 255) -> str:
        """Sanitização avançada de inputs"""
        if not text:
            return ''
            
        # Remove caracteres perigosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\\', '\x00', '\n', '\r', '\t']
        for char in dangerous_chars:
            text = text.replace(char, '')
            
        # Limita comprimento
        text = text[:max_length]
        
        # Remove múltiplos espaços
        text = ' '.join(text.split())
        
        return text.strip()
        
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Registra eventos de segurança"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'ip': get_remote_address(),
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'details': details
        }
        logger.warning(f"SECURITY: {event_type} - {log_data}")

# Instância global do gerenciador de segurança
security_manager = SecurityManager()

def require_admin(f):
    """Decorator para proteger rotas administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            security_manager.log_security_event('unauthorized_admin_access', {
                'endpoint': request.endpoint,
                'path': request.path
            })
            flash('Acesso não autorizado. Faça login para continuar.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_admin(f):
    """Decorator para aplicar rate limiting em rotas administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Aplica rate limiting mais restrito para admin
        if security_manager.limiter:
            # Verifica limite personalizado para login admin
            key = f"admin_login_{get_remote_address()}"
            current = security_manager.limiter.storage.get(key)
            if current and current >= 5:  # 5 tentativas por hora
                security_manager.log_security_event('rate_limit_exceeded', {
                    'key': key,
                    'attempts': current
                })
                flash('Muitas tentativas de login. Tente novamente mais tarde.', 'error')
                return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token():
    """Valida token CSRF"""
    token = session.get('csrf_token')
    form_token = request.form.get('csrf_token')
    
    if not token or not form_token or token != form_token:
        security_manager.log_security_event('csrf_token_invalid', {
            'session_token': token is not None,
            'form_token': form_token is not None
        })
        flash('Token de segurança inválido. Por favor, tente novamente.', 'error')
        return False
    return True

def require_csrf_token(f):
    """Decorator para enforçar validação de CSRF token em POST requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            if not validate_csrf_token():
                security_manager.log_security_event('csrf_validation_failed', {
                    'endpoint': request.endpoint,
                    'method': request.method
                })
                return redirect(request.referrer or url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_csrf_token():
    """Gera token CSRF"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']