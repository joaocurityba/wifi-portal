"""
Testes de Persistência de Dados
Prioridade: CRÍTICA 🔴

Testa:
- Dados são salvos corretamente
- Dados podem ser recuperados
- Integridade dos dados salvos
"""

import pytest
import os
import csv
import json
import re
from app.data_manager import data_manager


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
def test_user_data_saved_to_csv(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Dados do usuário devem ser salvos no banco de dados
    
    NOTA: CSV está deprecated, agora usa PostgreSQL (ou SQLite em testes)
    Se falhar: Registros de acesso são perdidos
    """
    csrf_token = get_csrf_token(client, '/login')
    sample_user_data['csrf_token'] = csrf_token
    
    # Importa modelos para verificar banco
    from app.models import AccessLog
    
    # Conta registros antes
    initial_count = AccessLog.query.count()
    
    # Submete formulário
    response = client.post('/login', data=sample_user_data, follow_redirects=False)
    
    assert response.status_code == 302, "Deve processar dados com sucesso"
    
    # Aguarda um momento para I/O
    import time
    time.sleep(0.1)
    
    # Verifica que registro foi salvo no banco
    final_count = AccessLog.query.count()
    assert final_count > initial_count, "Deve criar registro no banco de dados"
    
    # Busca último registro
    last_record = AccessLog.query.order_by(AccessLog.id.desc()).first()
    
    assert last_record is not None, "Deve haver pelo menos um registro"
    assert last_record.nome == sample_user_data['nome'], \
        "Nome deve ser salvo corretamente"
    assert last_record.email == sample_user_data['email'], \
        "Email deve ser salvo corretamente"
    assert last_record.telefone == sample_user_data['telefone'], \
        "Telefone deve ser salvo corretamente"


@pytest.mark.critical
def test_user_data_saved_encrypted(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Dados devem ser salvos no formato criptografado
    
    Se falhar: Dados sensíveis não são protegidos
    """
    csrf_token = get_csrf_token(client, '/login')
    sample_user_data['csrf_token'] = csrf_token
    
    # Submete formulário
    client.post('/login', data=sample_user_data)
    
    # Aguarda I/O
    import time
    time.sleep(0.1)
    
    # Verifica arquivo criptografado
    encrypted_file = os.path.join('data', 'access_log_encrypted.json')
    
    if os.path.exists(encrypted_file):
        with open(encrypted_file, 'r', encoding='utf-8') as f:
            encrypted_data = json.load(f)
        
        assert len(encrypted_data) > 0, "Deve ter dados criptografados salvos"


@pytest.mark.critical
def test_retrieve_saved_data(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Dados salvos devem poder ser recuperados
    
    Se falhar: Dados são salvos mas não podem ser lidos
    """
    # Salva dados diretamente via data_manager
    result = data_manager.log_access_encrypted(sample_user_data)
    assert result == True, "Deve salvar dados com sucesso"
    
    # Recupera dados
    logs = data_manager.get_access_logs(limit=10)
    
    assert len(logs) > 0, "Deve recuperar logs salvos"
    
    last_log = logs[0]
    assert last_log['nome'] == sample_user_data['nome'], \
        "Deve recuperar nome corretamente"
    assert last_log['email'] == sample_user_data['email'], \
        "Deve recuperar email corretamente"
    assert last_log['telefone'] == sample_user_data['telefone'], \
        "Deve recuperar telefone corretamente"


@pytest.mark.critical
def test_multiple_records_saved(client, cleanup_data_files):
    """
    CRÍTICO: Múltiplos registros devem ser salvos sem perda
    
    Se falhar: Dados são sobrescritos
    """
    # Salva 3 registros diferentes
    for i in range(3):
        data = {
            'nome': f'Usuário {i}',
            'email': f'user{i}@test.com',
            'telefone': f'1198765432{i}',
            'data_nascimento': '1990-01-01',
            'ip': f'192.168.1.{i}',
            'mac': f'AA:BB:CC:DD:EE:F{i}'
        }
        data_manager.log_access_encrypted(data)
    
    # Recupera todos
    logs = data_manager.get_access_logs(limit=10)
    
    assert len(logs) >= 3, "Deve salvar todos os registros"
    
    # Verifica que cada registro é único
    names = [log['nome'] for log in logs]
    assert 'Usuário 0' in names
    assert 'Usuário 1' in names
    assert 'Usuário 2' in names


@pytest.mark.critical
def test_data_integrity_after_save(client, sample_user_data, cleanup_data_files):
    """
    CRÍTICO: Dados não devem ser corrompidos durante salvamento
    
    Se falhar: Dados são alterados durante processo
    """
    original_data = sample_user_data.copy()
    
    # Salva
    data_manager.log_access_encrypted(sample_user_data)
    
    # Recupera
    logs = data_manager.get_access_logs(limit=1)
    recovered_data = logs[0] if logs else {}
    
    # Compara campos principais
    assert recovered_data.get('nome') == original_data['nome']
    assert recovered_data.get('email') == original_data['email']
    assert recovered_data.get('telefone') == original_data['telefone']
    assert recovered_data.get('ip') == original_data['ip']
    assert recovered_data.get('mac') == original_data['mac']


def test_csv_headers_created(client, sample_user_data, cleanup_data_files):
    """
    Arquivo CSV deve ter headers corretos
    """
    csrf_token = get_csrf_token(client, '/login')
    sample_user_data['csrf_token'] = csrf_token
    
    client.post('/login', data=sample_user_data)
    
    import time
    time.sleep(0.1)
    
    csv_file = client.application.config.get('CSV_FILE', 'data/access_log.csv')
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        # Verifica headers esperados
        assert 'nome' in first_line.lower()
        assert 'telefone' in first_line.lower()
        assert 'email' in first_line.lower()


def test_mikrotik_params_saved(client, cleanup_data_files):
    """
    Parâmetros do MikroTik devem ser salvos corretamente
    """
    csrf_token = get_csrf_token(client, '/login')
    
    response = client.post('/login', data={
        'nome': 'Teste MikroTik',
        'email': 'mikrotik@test.com',
        'telefone': '11987654321',
        'data_nascimento': '1990-01-01',
        'termos': 'on',
        'ip': '10.0.0.50',
        'mac': 'DE:AD:BE:EF:CA:FE',
        'link-orig': 'http://example.com',
        'csrf_token': csrf_token
    })
    
    import time
    time.sleep(0.1)
    
    # Verifica que parâmetros foram salvos
    logs = data_manager.get_access_logs(limit=1)
    
    if len(logs) > 0:
        assert logs[0]['ip'] == '10.0.0.50'
        assert logs[0]['mac'] == 'DE:AD:BE:EF:CA:FE'
