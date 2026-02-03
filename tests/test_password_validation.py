"""
Testes de Validação de Senha Forte
Prioridade: ALTA 🔴

Testa:
- Validação de força de senha
- Requisitos de segurança
- Caracteres especiais, maiúsculas, números
"""

import pytest
from app.security import security_manager


@pytest.mark.critical
@pytest.mark.security
def test_password_too_short():
    """
    CRÍTICO: Senha com menos de 8 caracteres deve falhar
    """
    valid, message = security_manager.validate_strong_password('Abc123!')
    
    assert valid == False
    assert '8 caracteres' in message.lower() or '8' in message


@pytest.mark.critical
@pytest.mark.security
def test_password_without_uppercase():
    """
    CRÍTICO: Senha sem maiúsculas deve falhar
    """
    valid, message = security_manager.validate_strong_password('abcd1234!')
    
    assert valid == False
    assert 'maiúscula' in message.lower() or 'uppercase' in message.lower()


@pytest.mark.critical
@pytest.mark.security
def test_password_without_lowercase():
    """
    CRÍTICO: Senha sem minúsculas deve falhar
    """
    valid, message = security_manager.validate_strong_password('ABCD1234!')
    
    assert valid == False
    assert 'minúscula' in message.lower() or 'lowercase' in message.lower()


@pytest.mark.critical
@pytest.mark.security
def test_password_without_number():
    """
    CRÍTICO: Senha sem números deve falhar
    """
    valid, message = security_manager.validate_strong_password('Abcdefgh!')
    
    assert valid == False
    assert 'número' in message.lower() or 'digit' in message.lower()


@pytest.mark.critical
@pytest.mark.security
def test_password_without_special_char():
    """
    CRÍTICO: Senha sem caracteres especiais deve falhar
    """
    valid, message = security_manager.validate_strong_password('Abcd1234')
    
    assert valid == False
    assert 'especial' in message.lower() or 'special' in message.lower()


@pytest.mark.critical
@pytest.mark.security
def test_password_valid_strong():
    """
    CRÍTICO: Senha forte válida deve passar
    """
    valid, message = security_manager.validate_strong_password('Senha@123')
    
    assert valid == True
    assert 'válida' in message.lower() or 'valid' in message.lower()


@pytest.mark.security
def test_password_with_all_requirements():
    """
    Senha com todos os requisitos deve passar
    """
    passwords = [
        'MyP@ssw0rd',
        'Test@2026!',
        'Secure#Pass1',
        'Admin$2026',
        'Portal@WiFi9'
    ]
    
    for password in passwords:
        valid, message = security_manager.validate_strong_password(password)
        assert valid == True, f"Senha '{password}' deveria ser válida: {message}"


@pytest.mark.security
def test_password_edge_cases():
    """
    Casos extremos de senha
    """
    # Exatamente 8 caracteres com todos requisitos
    valid, _ = security_manager.validate_strong_password('Teste@1a')
    assert valid == True
    
    # Senha muito longa mas válida
    valid, _ = security_manager.validate_strong_password('A' * 100 + 'a1@')
    assert valid == True
    
    # Senha vazia
    valid, _ = security_manager.validate_strong_password('')
    assert valid == False
    
    # Senha só com espaços
    valid, _ = security_manager.validate_strong_password('        ')
    assert valid == False


@pytest.mark.security
def test_password_with_unicode_characters():
    """
    Senha com caracteres unicode
    """
    valid, _ = security_manager.validate_strong_password('Sénha@123')
    # Deve validar (acentos são permitidos)
    assert valid == True


@pytest.mark.security
def test_password_common_patterns_rejected():
    """
    Padrões comuns fracos devem falhar
    """
    weak_passwords = [
        'password',
        '12345678',
        'abcdefgh',
        'ABCDEFGH',
        'Password',
        '12345678!',
    ]
    
    for password in weak_passwords:
        valid, _ = security_manager.validate_strong_password(password)
        # Deve falhar por falta de algum requisito
        assert valid == False, f"'{password}' não deveria ser aceita"


@pytest.mark.security
def test_validate_strong_password_function_exists():
    """
    Função de validação deve existir
    """
    assert hasattr(security_manager, 'validate_strong_password')
    assert callable(security_manager.validate_strong_password)


@pytest.mark.security
def test_password_validation_returns_tuple():
    """
    Validação deve retornar tupla (bool, str)
    """
    result = security_manager.validate_strong_password('Test@123')
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], str)
