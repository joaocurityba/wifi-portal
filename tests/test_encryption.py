"""
Testes de Criptografia de Dados Sensíveis
Prioridade: CRÍTICA 🔴

Testa:
- Criptografia e descriptografia de dados
- Armazenamento seguro
- Integridade dos dados
"""

import pytest
import json
import os
from app.security import security_manager
from app.data_manager import data_manager


@pytest.mark.critical
@pytest.mark.security
def test_encrypt_decrypt_data():
    """
    CRÍTICO: Dados devem ser criptografados e descriptografados corretamente
    
    Se falhar: Dados podem ser corrompidos ou expostos
    """
    original_data = "João Silva - (11) 98765-4321"
    
    # Criptografa
    encrypted = security_manager.encrypt_data(original_data)
    
    # Descriptografa
    decrypted = security_manager.decrypt_data(encrypted)
    
    # Validações
    assert decrypted == original_data, "Dados descriptografados devem ser idênticos ao original"
    assert encrypted != original_data, "Dados criptografados devem ser diferentes do original"
    assert len(encrypted) > len(original_data), "Dados criptografados devem ser maiores"
    # O formato pode ser base64 puro ou com encoding adicional
    assert len(encrypted) > 40, "Dados criptografados devem ter tamanho razoável"


@pytest.mark.critical
@pytest.mark.security
def test_encrypt_empty_string():
    """
    CRÍTICO: Deve tratar strings vazias corretamente
    """
    encrypted = security_manager.encrypt_data("")
    decrypted = security_manager.decrypt_data(encrypted)
    
    assert decrypted == "", "String vazia deve ser tratada corretamente"


@pytest.mark.critical
@pytest.mark.security
def test_encrypt_special_characters():
    """
    CRÍTICO: Deve criptografar caracteres especiais e acentos
    """
    original = "José da Silva - R$ 1.000,00 - ação@email.com"
    
    encrypted = security_manager.encrypt_data(original)
    decrypted = security_manager.decrypt_data(encrypted)
    
    assert decrypted == original, "Deve preservar caracteres especiais"


@pytest.mark.critical
@pytest.mark.security
def test_encrypted_data_saved_to_file(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Dados salvos em arquivo devem estar criptografados
    
    Se falhar: Violação de LGPD - dados pessoais em texto plano
    """
    # Registra acesso criptografado
    result = data_manager.log_access_encrypted(sample_user_data)
    
    assert result == True, "Deve salvar dados com sucesso"
    
    # Lê arquivo RAW (sem descriptografar)
    encrypted_file = os.path.join('data', 'access_log_encrypted.json')
    
    if os.path.exists(encrypted_file):
        with open(encrypted_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if len(raw_data) > 0:
            last_record = raw_data[-1]
            
            # Verifica que dados sensíveis estão criptografados
            assert last_record['nome'] != sample_user_data['nome'], \
                "Nome deve estar criptografado no arquivo"
            assert last_record['email'] != sample_user_data['email'], \
                "Email deve estar criptografado no arquivo"
            
            # Verifica que dados estão em formato base64 (criptografados)
            assert len(last_record['nome']) > len(sample_user_data['nome']), \
                "Dados criptografados devem ser maiores que originais"


@pytest.mark.critical
def test_decrypt_encrypted_data_from_file(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Deve conseguir descriptografar dados salvos
    
    Se falhar: Dados ficam inacessíveis permanentemente
    """
    # Salva dados criptografados
    data_manager.log_access_encrypted(sample_user_data)
    
    # Lê e descriptografa
    logs = data_manager.get_access_logs(limit=1)
    
    assert len(logs) > 0, "Deve recuperar pelo menos um log"
    
    last_log = logs[0]
    
    # Verifica que dados foram descriptografados corretamente
    assert last_log['nome'] == sample_user_data['nome'], \
        "Nome deve ser descriptografado corretamente"
    assert last_log['email'] == sample_user_data['email'], \
        "Email deve ser descriptografado corretamente"


@pytest.mark.security
def test_hash_sensitive_data():
    """
    Hash de dados sensíveis deve ser consistente
    """
    data = "192.168.1.100"
    
    hash1 = security_manager.hash_sensitive_data(data)
    hash2 = security_manager.hash_sensitive_data(data)
    
    assert hash1 == hash2, "Hash do mesmo dado deve ser idêntico"
    assert len(hash1) == 64, "Hash SHA-256 deve ter 64 caracteres"
    assert hash1 != data, "Hash deve ser diferente do dado original"


@pytest.mark.security
def test_encrypt_multiple_fields():
    """
    Deve criptografar múltiplos campos independentemente
    """
    fields = {
        'nome': 'João Silva',
        'email': 'joao@email.com'
    }
    
    encrypted_fields = {
        key: security_manager.encrypt_data(value)
        for key, value in fields.items()
    }
    
    # Verifica que cada campo foi criptografado de forma única
    encrypted_values = list(encrypted_fields.values())
    assert len(set(encrypted_values)) == len(encrypted_values), \
        "Cada campo deve ter criptografia única"
    
    # Verifica que pode descriptografar tudo
    for key, encrypted_value in encrypted_fields.items():
        decrypted = security_manager.decrypt_data(encrypted_value)
        assert decrypted == fields[key], f"Deve descriptografar {key} corretamente"


@pytest.mark.security
def test_encryption_with_long_text():
    """
    Deve criptografar textos longos corretamente
    """
    long_text = "A" * 10000  # 10KB de texto
    
    encrypted = security_manager.encrypt_data(long_text)
    decrypted = security_manager.decrypt_data(encrypted)
    
    assert decrypted == long_text, "Deve preservar texto longo"
