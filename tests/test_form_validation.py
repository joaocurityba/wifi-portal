"""
Testes de Validação de Formulários
Prioridade: CRÍTICA 🔴

Testa:
- Validação de campos obrigatórios
- Validação de formato de dados
- Regras de negócio (idade mínima, termos)
"""

import pytest
import re
from app_simple import validate_email


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
def test_login_requires_all_fields(client):
    """
    CRÍTICO: Formulário deve rejeitar dados incompletos
    
    Se falhar: Dados inválidos entram no sistema
    """
    csrf_token = get_csrf_token(client, '/login')
    
    # Envia apenas nome (falta email e termos)
    response = client.post('/login', data={
        'nome': 'Teste Incompleto',
        'csrf_token': csrf_token
    })
    
    # Deve retornar erro (não redirecionar)
    assert response.status_code == 200, "Deve retornar ao formulário com erro"
    # Mensagem pode estar em minúsculas no HTML
    assert (b'por favor, informe' in response.data.lower() or 
            b'informe' in response.data.lower()), \
        "Deve exibir mensagem de campos obrigatórios"


@pytest.mark.critical
def test_login_requires_terms_acceptance(client):
    """
    CRÍTICO: Deve exigir aceitação dos termos de uso
    
    Se falhar: Problemas legais com LGPD
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'Usuário Teste',
        'email': 'test@test.com',
        # termos não enviado (não marcado)
        'csrf_token': csrf_token
    })
    
    assert b'termos' in response.data.lower(), \
        "Deve exibir mensagem sobre termos de uso"


@pytest.mark.critical
def test_email_validation():
    """
    CRÍTICO: Validação de formato de email
    """
    # Emails válidos
    assert validate_email("usuario@example.com") == True
    assert validate_email("user.name@domain.com.br") == True
    assert validate_email("user+tag@example.com") == True
    
    # Emails inválidos
    assert validate_email("invalid-email") == False
    assert validate_email("@example.com") == False
    assert validate_email("user@") == False
    assert validate_email("user@.com") == False
    assert validate_email("") == False
    assert validate_email(None) == False


def test_login_rejects_invalid_email(client):
    """
    Email inválido deve ser rejeitado
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'Usuário Teste',
        'email': 'email-invalido',  # Sem @
        'termos': 'on',
        'csrf_token': csrf_token
    })
    
    assert b'email' in response.data.lower()


def test_login_rejects_short_name(client):
    """
    Nome muito curto deve ser rejeitado
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'AB',  # Menos de 3 caracteres
        'email': 'test@test.com',
        'termos': 'on',
        'csrf_token': csrf_token
    })
    
    assert b'3 caracteres' in response.data.lower()


def test_login_with_complete_valid_data(client, sample_user_data):
    """
    Dados completos e válidos devem ser aceitos
    """
    csrf_token = get_csrf_token(client, '/login')
    sample_user_data['csrf_token'] = csrf_token
    
    response = client.post('/login', data=sample_user_data, follow_redirects=False)
    
    # Deve redirecionar (sucesso)
    assert response.status_code == 302, "Dados válidos devem ser aceitos"
