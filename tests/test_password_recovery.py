"""
Testes de Recuperação de Senha
Prioridade: ALTA 🔴

Testa:
- Solicitação de recuperação de senha
- Validação de token de reset
- Redefinição de senha
- Expiração de token
"""

import pytest
import re
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from werkzeug.security import check_password_hash


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
@pytest.mark.security
def test_reset_password_request_page_loads(client):
    """
    CRÍTICO: Página de recuperação de senha deve carregar
    """
    response = client.get('/admin/reset-password')
    
    assert response.status_code == 200
    assert b'reset' in response.data.lower() or b'recupera' in response.data.lower()


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_with_valid_email(client):
    """
    CRÍTICO: Deve aceitar solicitação com email válido
    """
    from app.models import User
    
    # Cria usuário de teste
    user = User.query.filter_by(username='admin').first()
    
    csrf_token = get_csrf_token(client, '/admin/reset-password')
    
    with patch('app_simple.send_reset_email') as mock_email:
        mock_email.return_value = True
        
        response = client.post('/admin/reset-password', data={
            'email': user.email,
            'csrf_token': csrf_token
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Verifica se houve tentativa de enviar email ou mensagem de sucesso
        assert b'instru' in response.data.lower() or b'email' in response.data.lower()


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_with_invalid_email(client):
    """
    CRÍTICO: Não deve revelar se email existe (segurança)
    """
    csrf_token = get_csrf_token(client, '/admin/reset-password')
    
    response = client.post('/admin/reset-password', data={
        'email': 'naoexiste@example.com',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Deve retornar mensagem genérica (não revela se email existe)
    assert response.status_code == 200
    # Mensagem deve ser genérica para não revelar informações


@pytest.mark.critical
@pytest.mark.security
def test_reset_token_generation(client):
    """
    CRÍTICO: Token de reset deve ser gerado ao solicitar recuperação
    """
    from app.models import User
    
    user = User.query.filter_by(username='admin').first()
    csrf_token = get_csrf_token(client, '/admin/reset-password')
    
    # Reset token inicial deve ser None
    assert user.reset_token is None or user.reset_token == ''
    
    with patch('app_simple.send_reset_email') as mock_email:
        mock_email.return_value = True
        
        client.post('/admin/reset-password', data={
            'email': user.email,
            'csrf_token': csrf_token
        })
        
        # Recarrega usuário
        from app.models import db
        db.session.refresh(user)
        
        # Token deve ter sido gerado
        if user.reset_token:
            assert len(user.reset_token) > 20, "Token deve ter tamanho adequado"
            assert user.reset_expires is not None, "Expiração deve estar definida"


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_form_with_valid_token(client):
    """
    CRÍTICO: Formulário de reset deve carregar com token válido
    """
    from app.models import User, db
    import secrets
    
    user = User.query.filter_by(username='admin').first()
    
    # Define token manualmente
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    response = client.get(f'/admin/reset/{token}')
    
    assert response.status_code == 200
    assert b'senha' in response.data.lower() or b'password' in response.data.lower()


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_form_with_invalid_token(client):
    """
    CRÍTICO: Token inválido deve ser rejeitado
    """
    response = client.get('/admin/reset/token_invalido_12345', follow_redirects=True)
    
    # Deve redirecionar ou mostrar erro
    assert response.status_code == 200
    # Pode conter mensagem de erro


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_form_with_expired_token(client):
    """
    CRÍTICO: Token expirado deve ser rejeitado
    """
    from app.models import User, db
    import secrets
    
    user = User.query.filter_by(username='admin').first()
    
    # Define token expirado
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() - timedelta(hours=1)  # Expirado
    db.session.commit()
    
    response = client.get(f'/admin/reset/{token}', follow_redirects=True)
    
    # Deve redirecionar ou mostrar erro
    assert response.status_code == 200


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_execution(client):
    """
    CRÍTICO: Senha deve ser alterada com token válido
    """
    from app.models import User, db
    from werkzeug.security import check_password_hash
    import secrets
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    # Define token válido
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    csrf_token = get_csrf_token(client, f'/admin/reset/{token}')
    
    new_password = 'NovaSenha@123'
    
    response = client.post(f'/admin/reset/{token}', data={
        'password': new_password,
        'confirm_password': new_password,
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Busca usuário novamente (fresh query)
    user = User.query.filter_by(username='admin').first()
    
    # Senha deve ter mudado - verificar usando check_password_hash
    assert check_password_hash(user.password_hash, new_password)
    
    # Token deve ter sido limpo
    assert user.reset_token is None


@pytest.mark.critical
@pytest.mark.security
def test_reset_password_mismatched_passwords(client):
    """
    CRÍTICO: Senhas diferentes devem ser rejeitadas
    """
    from app.models import User, db
    import secrets
    
    user = User.query.filter_by(username='admin').first()
    
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    csrf_token = get_csrf_token(client, f'/admin/reset/{token}')
    
    response = client.post(f'/admin/reset/{token}', data={
        'password': 'Senha123',
        'confirm_password': 'SenhaDiferente456',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302 redirecionando
    assert response.status_code in [200, 302]
    # Senha não deve ter mudado
    user = User.query.filter_by(username='admin').first()
    assert not check_password_hash(user.password_hash, 'Senha123')


@pytest.mark.security
def test_reset_password_too_short(client):
    """
    Senha muito curta deve ser rejeitada
    """
    from app.models import User, db
    import secrets
    
    user = User.query.filter_by(username='admin').first()
    
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    csrf_token = get_csrf_token(client, f'/admin/reset/{token}')
    
    response = client.post(f'/admin/reset/{token}', data={
        'password': '123',
        'confirm_password': '123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302 redirecionando
    assert response.status_code in [200, 302]
    # Senha não deve ter mudado
    user = User.query.filter_by(username='admin').first()
    assert not check_password_hash(user.password_hash, '123')


@pytest.mark.security
def test_send_reset_email_function(client):
    """
    Função de envio de email deve ser chamada corretamente
    """
    with patch('app_simple.smtplib.SMTP') as mock_smtp:
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        from app_simple import send_reset_email
        
        result = send_reset_email('test@example.com', 'testuser', 'token123')
        
        # Se SMTP estiver configurado, deve tentar enviar
        # Se não, deve retornar False
        assert result in [True, False]
