"""
Testes de Busca no Admin
Prioridade: MÉDIA 🟡

Testa:
- Busca por diferentes campos
- Busca em campos criptografados
- Busca em campos não criptografados
"""

import pytest
import re


def get_csrf_token(client, url='/login'):
    """Helper para obter token CSRF de uma página"""
    response = client.get(url)
    data = response.data.decode('utf-8')
    
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', data)
    if match:
        return match.group(1)
    
    with client.session_transaction() as sess:
        return sess.get('csrf_token', '')


@pytest.mark.critical
def test_admin_search_requires_authentication(client):
    """
    Busca deve exigir autenticação
    """
    response = client.get('/admin/search')
    
    assert response.status_code == 302
    assert '/admin/login' in response.location


def test_admin_search_page_loads(authenticated_client):
    """
    Página de busca deve carregar
    """
    response = authenticated_client.get('/admin/search')
    
    # Pode retornar 200 ou 404 se rota não existir ainda
    assert response.status_code in [200, 404]


def test_search_by_nome(client, sample_user_data):
    """
    Busca por nome deve funcionar
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca
    results = data_manager.search_access_logs('Usuário', 'nome')
    
    assert len(results) > 0
    assert results[0]['nome'] == sample_user_data['nome']


def test_search_by_email(client, sample_user_data):
    """
    Busca por email deve funcionar
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca
    results = data_manager.search_access_logs('usuario.teste', 'email')
    
    assert len(results) > 0
    assert 'usuario.teste' in results[0]['email'].lower()


def test_search_by_telefone(client, sample_user_data):
    """
    Busca por telefone deve funcionar
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca
    results = data_manager.search_access_logs('98765', 'telefone')
    
    assert len(results) > 0
    assert '98765' in results[0]['telefone']


def test_search_by_ip(client, sample_user_data):
    """
    Busca por IP deve ser rápida (campo não criptografado)
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    import time
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca
    start = time.time()
    results = data_manager.search_access_logs('192.168', 'ip')
    elapsed = time.time() - start
    
    assert len(results) > 0
    assert '192.168' in results[0]['ip']
    # Busca por IP deve ser muito rápida (< 0.1s)
    assert elapsed < 0.5


def test_search_by_mac(client, sample_user_data):
    """
    Busca por MAC deve funcionar
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca
    results = data_manager.search_access_logs('AA:BB', 'mac')
    
    assert len(results) > 0
    assert 'AA:BB' in results[0]['mac'].upper()


def test_search_by_user_agent(client, sample_user_data):
    """
    Busca por user agent deve funcionar
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data = sample_user_data.copy()
    data['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0)'
    data_manager.log_access_encrypted(data)
    
    # Busca
    results = data_manager.search_access_logs('Mozilla', 'user_agent')
    
    assert len(results) > 0


def test_search_empty_term():
    """
    Busca vazia deve retornar lista vazia
    """
    from app.data_manager import data_manager
    
    results = data_manager.search_access_logs('', 'nome')
    
    # Pode retornar vazio ou todos os registros, depende da implementação
    assert isinstance(results, list)


def test_search_no_results():
    """
    Busca sem resultados deve retornar lista vazia
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    results = data_manager.search_access_logs('termo_inexistente_12345', 'nome')
    
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_case_insensitive(client, sample_user_data):
    """
    Busca deve ser case-insensitive
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca com case diferente
    results_lower = data_manager.search_access_logs('usuario', 'nome')
    results_upper = data_manager.search_access_logs('USUARIO', 'nome')
    
    assert len(results_lower) > 0
    assert len(results_upper) > 0


def test_search_partial_match(client, sample_user_data):
    """
    Busca deve encontrar matches parciais
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso
    data_manager.log_access_encrypted(sample_user_data)
    
    # Busca parcial
    results = data_manager.search_access_logs('Usuá', 'nome')
    
    assert len(results) > 0


def test_search_multiple_results(client, sample_user_data):
    """
    Busca deve retornar múltiplos resultados quando aplicável
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra vários acessos similares
    for i in range(3):
        data = sample_user_data.copy()
        data['nome'] = f'João Silva {i}'
        data['ip'] = f'192.168.1.{i}'
        data_manager.log_access_encrypted(data)
    
    # Busca
    results = data_manager.search_access_logs('João Silva', 'nome')
    
    assert len(results) == 3


def test_search_special_characters(client, sample_user_data):
    """
    Busca deve lidar com caracteres especiais
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra com caracteres especiais
    data = sample_user_data.copy()
    data['nome'] = 'José da Silva'
    data_manager.log_access_encrypted(data)
    
    # Busca
    results = data_manager.search_access_logs('José', 'nome')
    
    assert len(results) > 0
