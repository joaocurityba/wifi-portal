"""
Testes de Validação de Formulários
Prioridade: CRÍTICA 🔴

Testa:
- Validação de campos obrigatórios
- Validação de formato de dados
- Regras de negócio (idade mínima, termos)
"""

import pytest
from datetime import date, timedelta
import re
from app_simple import validate_email, validate_phone, validate_birth_date


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
    
    # Envia apenas nome (falta email, telefone, data_nascimento, termos)
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
def test_login_rejects_underage(client):
    """
    CRÍTICO: Deve bloquear menores de 13 anos
    
    Se falhar: Problemas legais com registro de menores
    """
    csrf_token = get_csrf_token(client, '/login')
    
    # Data de nascimento = 10 anos atrás (menor de idade)
    birth_date = (date.today() - timedelta(days=10*365)).strftime('%Y-%m-%d')
    
    response = client.post('/login', data={
        'nome': 'Criança Teste',
        'email': 'crianca@test.com',
        'telefone': '11987654321',
        'data_nascimento': birth_date,
        'termos': 'on',
        'csrf_token': csrf_token
    })
    
    assert b'13 anos' in response.data.lower(), \
        "Deve exibir mensagem sobre idade mínima"


@pytest.mark.critical
def test_login_accepts_valid_age(client):
    """
    CRÍTICO: Deve aceitar usuários com 13+ anos
    """
    csrf_token = get_csrf_token(client, '/login')
    
    # 20 anos atrás (adulto)
    birth_date = (date.today() - timedelta(days=20*365)).strftime('%Y-%m-%d')
    
    response = client.post('/login', data={
        'nome': 'Usuário Adulto',
        'email': 'adulto@test.com',
        'telefone': '11987654321',
        'data_nascimento': birth_date,
        'termos': 'on',
        'ip': '192.168.1.100',
        'mac': 'AA:BB:CC:DD:EE:FF',
        'csrf_token': csrf_token
    }, follow_redirects=False)
    
    # Deve redirecionar (sucesso)
    assert response.status_code == 302, "Deve aceitar usuário com idade válida"


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
        'telefone': '11987654321',
        'data_nascimento': '1990-01-01',
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


@pytest.mark.critical
def test_phone_validation():
    """
    CRÍTICO: Validação de formato de telefone
    """
    # Telefones válidos
    assert validate_phone("11987654321") == True
    assert validate_phone("(11) 98765-4321") == True
    assert validate_phone("1198765-4321") == True
    assert validate_phone("11 98765-4321") == True
    
    # Telefones inválidos
    assert validate_phone("123") == False  # Muito curto
    assert validate_phone("") == False
    assert validate_phone(None) == False
    assert validate_phone("12345678901234567890") == False  # Muito longo


@pytest.mark.critical
def test_birth_date_validation():
    """
    CRÍTICO: Validação de data de nascimento
    """
    # Datas válidas (13+ anos) - adiciona dias extras para evitar problemas com ano bissexto
    valid_date = (date.today() - timedelta(days=13*365 + 10)).strftime('%Y-%m-%d')
    assert validate_birth_date(valid_date) == True
    
    old_date = (date.today() - timedelta(days=80*365)).strftime('%Y-%m-%d')
    assert validate_birth_date(old_date) == True
    
    # Datas inválidas
    future_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    assert validate_birth_date(future_date) == False
    
    young_date = (date.today() - timedelta(days=12*365)).strftime('%Y-%m-%d')
    assert validate_birth_date(young_date) == False
    
    assert validate_birth_date("") == False
    assert validate_birth_date(None) == False
    assert validate_birth_date("invalid-date") == False


def test_login_rejects_invalid_email(client):
    """
    Email inválido deve ser rejeitado
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'Usuário Teste',
        'email': 'email-invalido',  # Sem @
        'telefone': '11987654321',
        'data_nascimento': '1990-01-01',
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
        'telefone': '11987654321',
        'data_nascimento': '1990-01-01',
        'termos': 'on',
        'csrf_token': csrf_token
    })
    
    assert b'3 caracteres' in response.data.lower()


def test_login_rejects_invalid_phone(client):
    """
    Telefone inválido deve ser rejeitado
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'Usuário Teste',
        'email': 'test@test.com',
        'telefone': '123',  # Muito curto
        'data_nascimento': '1990-01-01',
        'termos': 'on',
        'csrf_token': csrf_token
    })
    
    assert b'telefone' in response.data.lower()


def test_login_with_complete_valid_data(client, sample_user_data):
    """
    Dados completos e válidos devem ser aceitos
    """
    csrf_token = get_csrf_token(client, '/login')
    sample_user_data['csrf_token'] = csrf_token
    
    response = client.post('/login', data=sample_user_data, follow_redirects=False)
    
    # Deve redirecionar (sucesso)
    assert response.status_code == 302, "Dados válidos devem ser aceitos"
