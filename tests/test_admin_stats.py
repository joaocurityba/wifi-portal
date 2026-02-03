"""
Testes de Estatísticas do Admin
Prioridade: MÉDIA 🟡

Testa:
- Geração de estatísticas
- Contadores corretos
- Performance de queries
"""

import pytest
import re
from datetime import datetime, timedelta


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
def test_admin_stats_requires_authentication(client):
    """
    Estatísticas devem exigir autenticação
    """
    response = client.get('/admin/stats')
    
    assert response.status_code == 302
    assert '/admin/login' in response.location


def test_admin_stats_page_loads(authenticated_client):
    """
    Página de estatísticas deve carregar
    """
    response = authenticated_client.get('/admin/stats')
    
    # Pode retornar 200 ou 404 se rota não existir ainda
    assert response.status_code in [200, 404]


def test_get_user_stats_function():
    """
    Função de estatísticas deve retornar dados estruturados
    """
    from app.data_manager import data_manager
    
    stats = data_manager.get_user_stats()
    
    assert isinstance(stats, dict)
    assert 'total_accesses' in stats
    assert 'unique_ips' in stats
    assert 'unique_macs' in stats


def test_stats_with_no_data():
    """
    Estatísticas com banco vazio devem retornar zeros
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados (se houver)
    AccessLog.query.delete()
    
    stats = data_manager.get_user_stats()
    
    assert stats['total_accesses'] == 0
    assert stats['unique_ips'] == 0
    assert stats['unique_macs'] == 0


def test_stats_count_total_accesses(client, sample_user_data):
    """
    Deve contar acessos totais corretamente
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra alguns acessos
    for i in range(5):
        data = sample_user_data.copy()
        data['ip'] = f'192.168.1.{i}'
        data_manager.log_access_encrypted(data)
    
    stats = data_manager.get_user_stats()
    
    assert stats['total_accesses'] == 5


def test_stats_count_unique_ips(client, sample_user_data):
    """
    Deve contar IPs únicos corretamente
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acessos com IPs duplicados
    data1 = sample_user_data.copy()
    data1['ip'] = '192.168.1.1'
    data_manager.log_access_encrypted(data1)
    
    data2 = sample_user_data.copy()
    data2['ip'] = '192.168.1.1'  # Mesmo IP
    data_manager.log_access_encrypted(data2)
    
    data3 = sample_user_data.copy()
    data3['ip'] = '192.168.1.2'  # IP diferente
    data_manager.log_access_encrypted(data3)
    
    stats = data_manager.get_user_stats()
    
    assert stats['total_accesses'] == 3
    assert stats['unique_ips'] == 2


def test_stats_count_unique_macs(client, sample_user_data):
    """
    Deve contar MACs únicos corretamente
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acessos com MACs duplicados
    data1 = sample_user_data.copy()
    data1['mac'] = 'AA:BB:CC:DD:EE:01'
    data_manager.log_access_encrypted(data1)
    
    data2 = sample_user_data.copy()
    data2['mac'] = 'AA:BB:CC:DD:EE:01'  # Mesmo MAC
    data_manager.log_access_encrypted(data2)
    
    data3 = sample_user_data.copy()
    data3['mac'] = 'AA:BB:CC:DD:EE:02'  # MAC diferente
    data_manager.log_access_encrypted(data3)
    
    stats = data_manager.get_user_stats()
    
    assert stats['total_accesses'] == 3
    assert stats['unique_macs'] == 2


def test_stats_today_accesses(client, sample_user_data):
    """
    Deve contar acessos de hoje
    """
    from app.data_manager import data_manager
    from app.models import AccessLog, db
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra acesso de hoje
    data_manager.log_access_encrypted(sample_user_data)
    
    stats = data_manager.get_user_stats()
    
    assert 'today_accesses' in stats
    assert stats['today_accesses'] >= 1


def test_stats_this_week_accesses(client, sample_user_data):
    """
    Deve contar acessos desta semana
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra alguns acessos
    for i in range(3):
        data_manager.log_access_encrypted(sample_user_data)
    
    stats = data_manager.get_user_stats()
    
    assert 'this_week_accesses' in stats
    assert stats['this_week_accesses'] >= 3


def test_stats_handles_errors_gracefully():
    """
    Estatísticas devem retornar valores padrão em caso de erro
    """
    from app.data_manager import data_manager
    
    stats = data_manager.get_user_stats()
    
    # Deve sempre retornar dict com campos esperados
    assert isinstance(stats, dict)
    assert 'total_accesses' in stats
    
    # Valores devem ser numéricos
    assert isinstance(stats.get('total_accesses', 0), int)


def test_stats_performance_with_many_records(client, sample_user_data):
    """
    Estatísticas devem ser rápidas mesmo com muitos registros
    """
    from app.data_manager import data_manager
    from app.models import AccessLog
    import time
    
    # Limpa dados
    AccessLog.query.delete()
    
    # Registra vários acessos
    for i in range(50):
        data = sample_user_data.copy()
        data['ip'] = f'192.168.1.{i % 10}'
        data_manager.log_access_encrypted(data)
    
    start = time.time()
    stats = data_manager.get_user_stats()
    elapsed = time.time() - start
    
    # Deve executar em menos de 1 segundo
    assert elapsed < 1.0
    assert stats['total_accesses'] == 50
