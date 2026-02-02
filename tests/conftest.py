"""
Configurações e fixtures compartilhadas para testes pytest
"""

import pytest
import os
import sys
import tempfile
import shutil
from datetime import datetime
from unittest.mock import MagicMock, patch

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock do Redis ANTES de importar a aplicação
sys.modules['redis'] = MagicMock()

from app_simple import app, create_default_user
from app.security import security_manager
from app.data_manager import data_manager


@pytest.fixture
def client():
    """Fixture que fornece um cliente de teste Flask"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Desabilita CSRF para testes que não precisam
    app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    
    # Desabilita rate limiting nos testes (não precisa de Redis)
    os.environ['RATELIMIT_ENABLED'] = 'false'
    
    # Usa diretórios temporários para dados de teste
    test_data_dir = tempfile.mkdtemp()
    app.config['CSV_FILE'] = os.path.join(test_data_dir, 'access_log.csv')
    
    # Reconfigura limiter para usar memória ao invés de Redis
    from app.security import security_manager
    security_manager.limiter.enabled = False
    
    with app.test_client() as client:
        with app.app_context():
            create_default_user()
            yield client
    
    # Cleanup - remove diretório temporário
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)


@pytest.fixture
def client_with_csrf():
    """Fixture que fornece um cliente de teste Flask COM CSRF habilitado"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    
    # Desabilita rate limiting nos testes
    os.environ['RATELIMIT_ENABLED'] = 'false'
    
    # Usa diretórios temporários para dados de teste
    test_data_dir = tempfile.mkdtemp()
    app.config['CSV_FILE'] = os.path.join(test_data_dir, 'access_log.csv')
    
    # Desabilita limiter
    from app.security import security_manager
    security_manager.limiter.enabled = False
    
    with app.test_client() as client:
        with app.app_context():
            create_default_user()
            yield client
    
    # Cleanup
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)


@pytest.fixture
def authenticated_client(client):
    """Fixture que fornece um cliente já autenticado como admin"""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['username'] = 'admin'
    return client


def get_csrf_token(client, url='/login'):
    """Helper para obter token CSRF de uma página"""
    response = client.get(url)
    data = response.data.decode('utf-8')
    
    # Extrai o token do HTML
    import re
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', data)
    if match:
        return match.group(1)
    
    # Se não encontrar no HTML, tenta pegar da sessão
    with client.session_transaction() as sess:
        return sess.get('csrf_token', '')


@pytest.fixture
def sample_user_data():
    """Fixture com dados de usuário válidos para testes"""
    return {
        'nome': 'Usuário Teste',
        'email': 'usuario.teste@example.com',
        'telefone': '(11) 98765-4321',
        'data_nascimento': '1990-01-01',
        'termos': 'on',
        'ip': '192.168.88.100',
        'mac': 'AA:BB:CC:DD:EE:FF',
        'link-orig': 'http://google.com'
    }


@pytest.fixture
def cleanup_data_files():
    """Fixture para limpar arquivos de dados após testes"""
    yield
    
    # Cleanup após o teste
    test_files = [
        'data/access_log.csv',
        'data/access_log_encrypted.json',
        'data/users.csv'
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
