#!/usr/bin/env python3
"""
Script de teste automatizado para o Portal Cautivo
Simula acesso real com parâmetros MikroTik
"""

import requests
import time
import csv
import os

def test_portal_cautivo():
    """Testa o portal cativo com simulação completa"""
    
    # Configurações do teste
    BASE_URL = "http://localhost:5000"
    TEST_DATA = {
        'nome': 'Teste Usuário',
        'telefone': '(11) 98765-4321',
        'termos': 'on'
    }
    
    # Parâmetros MikroTik simulados
    MIKROTIK_PARAMS = {
        'ip': '192.168.88.100',
        'mac': 'AA:BB:CC:DD:EE:FF', 
        'link-orig': 'http://google.com'
    }
    
    print("🧪 Iniciando teste do Portal Cautivo...")
    print(f"📡 Parâmetros MikroTik: {MIKROTIK_PARAMS}")
    
    try:
        # Etapa 1: Simular acesso GET com parâmetros MikroTik
        print("\n1️⃣ Simulando acesso GET com parâmetros MikroTik...")
        get_url = f"{BASE_URL}/login"
        response = requests.get(get_url, params=MIKROTIK_PARAMS)
        
        if response.status_code == 200:
            print("✅ GET realizado com sucesso")
        else:
            print(f"❌ Erro no GET: {response.status_code}")
            return False
        
        # Etapa 2: Enviar formulário POST
        print("\n2️⃣ Enviando formulário POST...")
        post_data = {
            **TEST_DATA,
            **MIKROTIK_PARAMS  # Adiciona parâmetros MikroTik ao POST
        }
        
        response = requests.post(f"{BASE_URL}/login", data=post_data)
        
        if response.status_code == 200:
            print("✅ POST realizado com sucesso")
        elif response.status_code == 302:
            print("✅ Redirecionamento realizado (código 302)")
        else:
            print(f"❌ Erro no POST: {response.status_code}")
            return False
        
        # Etapa 3: Verificar registro no CSV
        print("\n3️⃣ Verificando registro no CSV...")
        if verificar_csv(MIKROTIK_PARAMS, TEST_DATA):
            print("✅ Dados gravados corretamente no CSV")
            return True
        else:
            print("❌ Dados não encontrados no CSV")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Servidor não está rodando em localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def verificar_csv(mikrotik_params, test_data):
    """Verifica se os dados foram gravados corretamente no CSV"""
    
    csv_file = "data/access_log.csv"
    
    if not os.path.exists(csv_file):
        print("❌ Arquivo CSV não encontrado")
        return False
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        registros = list(reader)
    
    if not registros:
        print("❌ Nenhum registro encontrado no CSV")
        return False
    
    # Verifica o último registro
    ultimo_registro = registros[-1]
    
    print(f"📋 Último registro no CSV:")
    print(f"   Nome: {ultimo_registro.get('nome', 'N/A')}")
    print(f"   Telefone: {ultimo_registro.get('telefone', 'N/A')}")
    print(f"   IP: {ultimo_registro.get('ip', 'N/A')}")
    print(f"   MAC: {ultimo_registro.get('mac', 'N/A')}")
    print(f"   User Agent: {ultimo_registro.get('user_agent', 'N/A')}")
    print(f"   Data/Hora: {ultimo_registro.get('data_hora', 'N/A')}")
    
    # Verifica se os dados correspondem
    checks = [
        ultimo_registro.get('nome') == test_data['nome'],
        ultimo_registro.get('telefone') == test_data['telefone'],
        ultimo_registro.get('ip') == mikrotik_params['ip'],
        ultimo_registro.get('mac') == mikrotik_params['mac']
    ]
    
    return all(checks)

if __name__ == "__main__":
    success = test_portal_cautivo()
    if success:
        print("\n🎉 Teste concluído com sucesso!")
    else:
        print("\n💥 Teste falhou!")