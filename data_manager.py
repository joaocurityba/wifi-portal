#!/usr/bin/env python3
"""
Gerenciador de Dados Criptografado para Portal Cautivo
Implementa armazenamento seguro de dados sensíveis com criptografia
"""

import os
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from security import security_manager
from app.locks import file_lock, atomic_write_json, append_safe_json

logger = logging.getLogger(__name__)

class EncryptedDataManager:
    """Gerenciador de dados com criptografia avançada"""
    
    def __init__(self, app=None):
        self.app = app
        self.data_dir = 'data'
        self.access_log_file = 'access_log_encrypted.json'
        self.users_file = 'users_encrypted.json'
        
    def init_app(self, app):
        """Inicializa com a aplicação Flask"""
        self.app = app
        self.data_dir = app.config.get('CSV_FILE', 'data').replace('access_log.csv', '')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criptografa campos sensíveis no dicionário de dados"""
        sensitive_fields = ['nome', 'email', 'telefone', 'data_nascimento']
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = security_manager.encrypt_data(encrypted_data[field])
                
        # Adiciona hash para consultas rápidas (não criptografado)
        if 'ip' in encrypted_data:
            encrypted_data['ip_hash'] = security_manager.hash_sensitive_data(encrypted_data['ip'])
        if 'mac' in encrypted_data:
            encrypted_data['mac_hash'] = security_manager.hash_sensitive_data(encrypted_data['mac'])
            
        return encrypted_data
        
    def decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Descriptografa campos sensíveis no dicionário de dados"""
        sensitive_fields = ['nome', 'email', 'telefone', 'data_nascimento']
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = security_manager.decrypt_data(decrypted_data[field])
                
        # Remove campos de hash
        decrypted_data.pop('ip_hash', None)
        decrypted_data.pop('mac_hash', None)
        
        return decrypted_data
        
    def log_access_encrypted(self, data: Dict[str, Any]) -> bool:
        """Registra acesso com criptografia (atomicamente)"""
        try:
            # Adiciona timestamp
            data['timestamp'] = datetime.now().isoformat()
            data['access_id'] = security_manager.hash_sensitive_data(f"{data.get('ip', '')}_{data.get('mac', '')}_{data['timestamp']}")
            
            # Criptografa dados sensíveis
            encrypted_data = self.encrypt_sensitive_fields(data)
            
            # Salva no arquivo JSON com file-locking atomicamente
            file_path = os.path.join(self.data_dir, self.access_log_file)
            
            # Usa lock e append seguro para JSON
            with file_lock(file_path):
                existing_data = []
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Arquivo de log corrompido, criando novo")
                
                # Adiciona novo registro
                existing_data.append(encrypted_data)
                
                # Salva atomicamente
                atomic_write_json(file_path, existing_data, indent=2)
                
            logger.info(f"Acesso registrado: {data.get('access_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {e}")
            return False
            
    def get_access_logs(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Obtém logs de acesso descriptografados"""
        try:
            file_path = os.path.join(self.data_dir, self.access_log_file)
            
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
                
            # Descriptografa e limita resultados
            decrypted_data = []
            for record in reversed(encrypted_data[-limit:]):  # Últimos registros primeiro
                decrypted_data.append(self.decrypt_sensitive_fields(record))
                
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Erro ao ler logs de acesso: {e}")
            return []
            
    def search_access_logs(self, search_term: str, field: str = 'nome') -> List[Dict[str, Any]]:
        """Busca em logs de acesso (busca em texto descriptografado)"""
        try:
            all_logs = self.get_access_logs()
            results = []
            
            search_term = search_term.lower()
            
            for log in all_logs:
                if field in log and log[field] and search_term in log[field].lower():
                    results.append(log)
                    
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar logs: {e}")
            return []
            
    def get_user_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de uso"""
        try:
            logs = self.get_access_logs()
            
            stats = {
                'total_accesses': len(logs),
                'unique_ips': len(set(log.get('ip', '') for log in logs if log.get('ip'))),
                'unique_macs': len(set(log.get('mac', '') for log in logs if log.get('mac'))),
                'today_accesses': 0,
                'this_week_accesses': 0
            }
            
            today = datetime.now().date()
            
            for log in logs:
                if 'timestamp' in log:
                    log_date = datetime.fromisoformat(log['timestamp']).date()
                    
                    if log_date == today:
                        stats['today_accesses'] += 1
                        
                    if today - log_date <= timedelta(days=7):
                        stats['this_week_accesses'] += 1
                        
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {'error': str(e)}

# Instância global do gerenciador de dados
data_manager = EncryptedDataManager()