"""
Testes de Segurança do Painel Administrativo
Prioridade: CRÍTICA 🔴

Testa:
- Proteção de rotas administrativas
- Autenticação de admin
- Controle de acesso
"""

import pytest
import re


def get_csrf_token(client, url='/login'):
    """Helper para obter token CSRF de uma página"""
    response = client.get(url)
    data = response.data.decode('utf-8')
    
    # Extrai o token do HTML
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', data)
    if match:
        return match.group(1)
    
    # Se não encontrar no HTML, tenta pegar da sessão
    with client.session_transaction() as sess:
        return sess.get('csrf_token', '')


@pytest.mark.critical
@pytest.mark.security
def test_admin_route_requires_login(client):
    """
    CRÍTICO: Painel admin deve bloquear acesso não autenticado
    
    Se falhar: Invasor pode acessar dados de TODOS os usuários
    """
    response = client.get('/admin')
    
    # Deve redirecionar para login
    assert response.status_code == 302, "Admin deve redirecionar usuário não autenticado"
    assert '/admin/login' in response.location, "Deve redirecionar para página de login admin"


@pytest.mark.critical
@pytest.mark.security
def test_admin_login_with_valid_credentials(client):
    """
    CRÍTICO: Admin deve conseguir fazer login com credenciais válidas
    
    Se falhar: Admin legítimo não consegue acessar painel
    """
    # Obtém token CSRF
    csrf_token = get_csrf_token(client, '/admin/login')
    
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }, follow_redirects=False)
    
    # Deve redirecionar após login bem-sucedido
    assert response.status_code == 302, "Deve redirecionar após login"
    
    # Verifica que sessão foi criada
    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') == True, "Sessão deve marcar admin como logado"
        assert sess.get('username') == 'admin', "Username deve estar na sessão"


@pytest.mark.critical
@pytest.mark.security
def test_admin_login_with_invalid_credentials(client):
    """
    CRÍTICO: Credenciais inválidas devem ser rejeitadas
    
    Se falhar: Atacante pode acessar com senha errada
    """
    csrf_token = get_csrf_token(client, '/admin/login')
    
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'senha_errada_123',
        'csrf_token': csrf_token
    })
    
    # Verifica que sessão NÃO foi criada
    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') != True, "Não deve criar sessão com senha errada"
    
    # Verifica que há mensagem de erro
    assert response.status_code == 200, "Deve retornar à página de login"


@pytest.mark.critical
@pytest.mark.security
def test_admin_logout_clears_session(client):
    """
    CRÍTICO: Logout deve limpar sessão completamente
    
    Se falhar: Sessão permanece ativa após logout
    """
    # Faz login primeiro
    csrf_token = get_csrf_token(client, '/admin/login')
    client.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    })
    
    # Verifica que está logado
    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') == True
    
    # Faz logout
    client.get('/admin/logout')
    
    # Verifica que sessão foi limpa
    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') is None, "Logout deve remover flag de login"
        assert sess.get('username') is None, "Logout deve remover username"


@pytest.mark.critical
@pytest.mark.security
def test_admin_route_accessible_when_authenticated(authenticated_client):
    """
    CRÍTICO: Admin autenticado deve acessar painel
    
    Se falhar: Admin não consegue usar o sistema
    """
    response = authenticated_client.get('/admin')
    
    assert response.status_code == 200, "Admin autenticado deve acessar painel"
    assert b'admin.html' in response.data or b'registros' in response.data.lower(), \
        "Deve exibir conteúdo do painel admin"


@pytest.mark.security
def test_admin_profile_requires_authentication(client):
    """
    Rota de perfil deve exigir autenticação
    """
    response = client.get('/admin/profile')
    
    assert response.status_code == 302, "Deve redirecionar usuário não autenticado"
    assert '/admin/login' in response.location


@pytest.mark.security
def test_admin_login_with_empty_credentials(client):
    """
    Credenciais vazias devem ser rejeitadas
    """
    csrf_token = get_csrf_token(client, '/admin/login')
    
    response = client.post('/admin/login', data={
        'username': '',
        'password': '',
        'csrf_token': csrf_token
    })
    
    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') != True, "Credenciais vazias não devem autenticar"
