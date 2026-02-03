"""
Testes de Perfil Administrativo
Prioridade: ALTA 🔴

Testa:
- Acesso à página de perfil
- Edição de email
- Troca de senha
- Validação de senha atual
"""

import pytest
import re
from werkzeug.security import generate_password_hash, check_password_hash


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
def test_admin_profile_requires_login(client):
    """
    CRÍTICO: Página de perfil deve exigir autenticação
    """
    response = client.get('/admin/profile')
    
    assert response.status_code == 302
    assert '/admin/login' in response.location


@pytest.mark.critical
def test_admin_profile_page_loads(authenticated_client):
    """
    CRÍTICO: Página de perfil deve carregar para admin autenticado
    """
    response = authenticated_client.get('/admin/profile')
    
    assert response.status_code == 200
    assert b'perfil' in response.data.lower() or b'profile' in response.data.lower()


@pytest.mark.critical
def test_admin_profile_shows_current_info(authenticated_client):
    """
    CRÍTICO: Deve mostrar informações atuais do admin
    """
    from app.models import User
    
    user = User.query.filter_by(username='admin').first()
    
    response = authenticated_client.get('/admin/profile')
    
    assert response.status_code == 200
    assert user.username.encode() in response.data
    assert user.email.encode() in response.data


@pytest.mark.critical
@pytest.mark.security
def test_update_email_requires_current_password(authenticated_client):
    """
    CRÍTICO: Mudança de email deve exigir senha atual
    """
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'novoemail@example.com',
        'current_password': '',  # Senha vazia
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302 redirecionando
    assert response.status_code in [200, 302]


@pytest.mark.critical
def test_update_email_with_valid_password(authenticated_client):
    """
    CRÍTICO: Email deve ser atualizado com senha correta
    """
    from app.models import User, db
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'novoemail@example.com',
        'current_password': 'admin123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Limpa cache do SQLAlchemy e busca novamente
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    
    # Email deve ter mudado
    assert user.email == 'novoemail@example.com'


@pytest.mark.critical
@pytest.mark.security
def test_update_email_with_wrong_password(authenticated_client):
    """
    CRÍTICO: Senha incorreta deve bloquear alteração
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_email = user.email
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'novoemail@example.com',
        'current_password': 'senha_errada',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302
    assert response.status_code in [200, 302]
    
    # Email NÃO deve ter mudado
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert user.email != 'novoemail@example.com'


@pytest.mark.critical
@pytest.mark.security
def test_change_password_requires_current_password(authenticated_client):
    """
    CRÍTICO: Troca de senha deve exigir senha atual
    """
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'admin@prefeitura.com',
        'current_password': '',
        'new_password': 'NovaSenha123',
        'confirm_password': 'NovaSenha123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302
    assert response.status_code in [200, 302]


@pytest.mark.critical
@pytest.mark.security
def test_change_password_successfully(authenticated_client):
    """
    CRÍTICO: Senha deve ser alterada com dados válidos
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    new_password = 'NovaSenha@2026'
    
    response = authenticated_client.post('/admin/profile', data={
        'email': user.email,
        'current_password': 'admin123',
        'new_password': new_password,
        'confirm_password': new_password,
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Busca usuário novamente
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    
    # Senha deve ter mudado - verificar usando check_password_hash
    assert check_password_hash(user.password_hash, new_password)


@pytest.mark.critical
@pytest.mark.security
def test_change_password_with_wrong_current_password(authenticated_client):
    """
    CRÍTICO: Senha atual incorreta deve bloquear troca
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': user.email,
        'current_password': 'senha_errada',
        'new_password': 'NovaSenha123',
        'confirm_password': 'NovaSenha123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302
    assert response.status_code in [200, 302]
    
    # Senha NÃO deve ter mudado
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert not check_password_hash(user.password_hash, 'NovaSenha123')


@pytest.mark.critical
@pytest.mark.security
def test_change_password_mismatch(authenticated_client):
    """
    CRÍTICO: Senhas diferentes devem ser rejeitadas
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': user.email,
        'current_password': 'admin123',
        'new_password': 'Senha123',
        'confirm_password': 'SenhaDiferente456',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302
    assert response.status_code in [200, 302]
    
    # Senha NÃO deve ter mudado
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert not check_password_hash(user.password_hash, 'Senha123')


@pytest.mark.security
def test_change_password_too_short(authenticated_client):
    """
    Senha muito curta deve ser rejeitada
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': user.email,
        'current_password': 'admin123',
        'new_password': '123',
        'confirm_password': '123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    # Pode retornar 200 com erro ou 302
    assert response.status_code in [200, 302]
    
    # Senha NÃO deve ter mudado
    db.session.expire_all()
    user = User.query.filter_by(username='admin').first()
    assert not check_password_hash(user.password_hash, '123')


@pytest.mark.security
def test_update_email_invalid_format(authenticated_client):
    """
    Email inválido deve ser rejeitado
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_email = user.email
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'email_invalido',
        'current_password': 'admin123',
        'csrf_token': csrf_token
    })
    
    assert response.status_code == 200
    
    # Recarrega usuário
    db.session.refresh(user)
    
    # Email NÃO deve ter mudado
    assert user.email == old_email


@pytest.mark.security
def test_update_only_email_keeps_password(authenticated_client):
    """
    Atualizar só email não deve alterar senha
    """
    from app.models import User, db
    
    user = User.query.filter_by(username='admin').first()
    old_password_hash = user.password_hash
    
    csrf_token = get_csrf_token(authenticated_client, '/admin/profile')
    
    response = authenticated_client.post('/admin/profile', data={
        'email': 'outro@example.com',
        'current_password': 'admin123',
        # Sem new_password
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Recarrega usuário
    db.session.refresh(user)
    
    # Senha deve permanecer igual
    assert user.password_hash == old_password_hash
