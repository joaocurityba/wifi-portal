#!/usr/bin/env python3
"""
Teste de redirecionamento automático
"""

import requests
from app_simple import app

def test_admin_redirect():
    """Testa o redirecionamento automático da rota /admin"""
    with app.test_client() as client:
        # Testa acesso à rota /admin sem login
        response = client.get('/admin')
        
        print(f"Status Code: {response.status_code}")
        print(f"Location: {response.location}")
        print(f"Data: {response.data.decode('utf-8')}")
        
        # Verifica se houve redirecionamento
        if response.status_code == 302:
            if 'admin/login' in response.location:
                print("✅ REDIRECIONAMENTO FUNCIONANDO CORRETAMENTE!")
                print(f"Redirecionou para: {response.location}")
            else:
                print("❌ Redirecionamento incorreto")
                print(f"Redirecionou para: {response.location}")
        else:
            print("❌ Nenhum redirecionamento ocorreu")
            print("Conteúdo retornado:")
            print(response.data.decode('utf-8'))

if __name__ == '__main__':
    test_admin_redirect()