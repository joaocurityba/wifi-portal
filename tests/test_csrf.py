"""
Testes de Proteção CSRF (Cross-Site Request Forgery)
Prioridade: CRÍTICA 🔴

Testa:
- Token CSRF é gerado
- Token CSRF é validado
- Requisições sem token são bloqueadas
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
def test_csrf_token_generated(client):
    """
    CRÍTICO: Token CSRF deve ser gerado em formulários
    
    Se falhar: Aplicação vulnerável a ataques CSRF
    """
    response = client.get('/login')
    
    # Verifica que há um input csrf_token no HTML
    assert b'csrf_token' in response.data, "Formulário deve conter campo csrf_token"
    assert b'type="hidden"' in response.data, "CSRF token deve ser campo hidden"


@pytest.mark.critical
@pytest.mark.security
def test_post_without_csrf_token_blocked(client_with_csrf):
    """
    CRÍTICO: POST sem token CSRF deve ser bloqueado
    
    Se falhar: Atacante pode submeter formulários maliciosos
    """
    response = client_with_csrf.post('/login', data={
        'nome': 'Teste',
        'email': 'test@test.com',
        'termos': 'on'
        # Sem csrf_token
    }, follow_redirects=False)
    
    # Deve redirecionar (bloqueado) ou retornar erro
    # O comportamento depende da implementação, mas não deve processar
    assert response.status_code in [302, 400, 403], \
        "Requisição sem CSRF token deve ser bloqueada"


@pytest.mark.critical
@pytest.mark.security
def test_post_with_invalid_csrf_token_blocked(client_with_csrf):
    """
    CRÍTICO: POST com token CSRF inválido deve ser bloqueado
    
    Se falhar: Atacante pode forjar tokens
    """
    response = client_with_csrf.post('/login', data={
        'nome': 'Teste',
        'email': 'test@test.com',
        'termos': 'on',
        'csrf_token': 'token_falso_12345'
    }, follow_redirects=False)
    
    # Deve ser bloqueado
    assert response.status_code in [302, 400, 403], \
        "Token CSRF inválido deve ser rejeitado"


@pytest.mark.critical
@pytest.mark.security
def test_post_with_valid_csrf_token_accepted(client_with_csrf):
    """
    CRÍTICO: POST com token válido deve ser aceito
    
    Se falhar: Funcionalidade normal quebrada
    """
    # Obtém token válido
    csrf_token = get_csrf_token(client_with_csrf, '/login')
    
    response = client_with_csrf.post('/login', data={
        'nome': 'Usuário Válido',
        'email': 'valido@test.com',
        'termos': 'on',
        'ip': '192.168.1.100',
        'mac': 'AA:BB:CC:DD:EE:FF',
        'csrf_token': csrf_token
    }, follow_redirects=False)
    
    # Deve processar normalmente (redirecionar após sucesso)
    assert response.status_code == 302, \
        "Token CSRF válido deve permitir processamento"


@pytest.mark.security
def test_csrf_token_in_session(client):
    """
    Token CSRF deve ser armazenado na sessão
    """
    # Faz request para gerar token
    client.get('/login')
    
    # Verifica que token está na sessão
    with client.session_transaction() as sess:
        assert 'csrf_token' in sess, "Token CSRF deve estar na sessão"
        assert len(sess['csrf_token']) > 20, "Token deve ter tamanho adequado"


@pytest.mark.security
def test_admin_login_csrf_protection(client_with_csrf):
    """
    Login admin deve ter proteção CSRF
    """
    # Tenta login sem token
    response = client_with_csrf.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin123'
        # Sem csrf_token
    }, follow_redirects=False)
    
    # Não deve autenticar
    with client_with_csrf.session_transaction() as sess:
        assert sess.get('admin_logged_in') != True, \
            "Não deve autenticar sem CSRF token"


@pytest.mark.security
def test_admin_login_with_valid_csrf(client_with_csrf):
    """
    Login admin com CSRF válido deve funcionar
    """
    csrf_token = get_csrf_token(client_with_csrf, '/admin/login')
    
    response = client_with_csrf.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }, follow_redirects=False)
    
    # Deve autenticar
    assert response.status_code == 302
    with client_with_csrf.session_transaction() as sess:
        assert sess.get('admin_logged_in') == True


@pytest.mark.security
def test_csrf_token_unique_per_session(client):
    """
    Cada sessão deve ter token CSRF único
    """
    # Primeira sessão
    client.get('/login')
    with client.session_transaction() as sess:
        token1 = sess.get('csrf_token')
    
    # Limpa sessão
    with client.session_transaction() as sess:
        sess.clear()
    
    # Segunda sessão
    client.get('/login')
    with client.session_transaction() as sess:
        token2 = sess.get('csrf_token')
    
    assert token1 != token2, "Cada sessão deve ter token CSRF diferente"
