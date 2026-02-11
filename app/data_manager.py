#!/usr/bin/env python3
"""
Gerenciador de Dados para Portal Cautivo com PostgreSQL
Implementa armazenamento seguro de dados sensíveis com criptografia em banco de dados
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, func, desc
from app.security import security_manager

logger = logging.getLogger(__name__)

class EncryptedDataManager:
    """Gerenciador de dados com criptografia avançada usando PostgreSQL"""
    
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.User = None
        self.AccessLog = None
        
    def init_app(self, app):
        """Inicializa com a aplicação Flask"""
        self.app = app
        # Importa modelos aqui para evitar importação circular
        from app.models import db, User, AccessLog
        self.db = db
        self.User = User
        self.AccessLog = AccessLog
        
        # Configura cipher suite para encriptação dos campos
        self._setup_encryption()
        
    def _setup_encryption(self):
        """Configura encriptação para os campos sensíveis"""
        # A encriptação agora é gerenciada pelo TypeDecorator nos models
        # Mas precisamos garantir que o cipher_suite está disponível
        pass
        
    def log_access_encrypted(self, data: Dict[str, Any]) -> bool:
        """Registra acesso com criptografia no banco de dados"""
        try:
            # Valores padrão para campos obrigatórios
            ip = data.get('ip') or '0.0.0.0'
            mac = data.get('mac') or ''
            
            # Cria novo registro de acesso
            access_log = self.AccessLog(
                nome=data.get('nome', ''),
                email=data.get('email', ''),
                ip=ip,
                ip_hash=self.AccessLog.hash_value(ip) if ip else None,
                mac=mac if mac else None,
                mac_hash=self.AccessLog.hash_value(mac) if mac else None,
                user_agent=data.get('user_agent'),
                access_id=self.AccessLog.generate_access_id(),
                timestamp=datetime.utcnow()
            )
            
            self.db.session.add(access_log)
            self.db.session.commit()
            
            logger.info(f"Acesso registrado: {access_log.access_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar acesso: {e}")
            self.db.session.rollback()
            return False
            
    def get_access_logs(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Obtém logs de acesso do banco de dados"""
        try:
            # Query com ordenação e limite
            logs = self.AccessLog.query.order_by(
                desc(self.AccessLog.timestamp),
                desc(self.AccessLog.id)
            ).limit(limit).all()
            
            # Converte para dicionários (dados já serão descriptografados pelo TypeDecorator)
            return [log.to_dict(decrypt=True) for log in logs]
            
        except Exception as e:
            logger.error(f"Erro ao ler logs de acesso: {e}")
            return []
            
    def search_access_logs(self, search_term: str, field: str = 'nome') -> List[Dict[str, Any]]:
        """
        Busca em logs de acesso.
        
        NOTA: Para campos encriptados, precisa descriptografar todos os registros primeiro
        (não há como fazer LIKE em campos encriptados diretamente no banco)
        """
        try:
            # Para campos não encriptados (ip, mac, user_agent), pode fazer busca direta
            if field in ['ip', 'mac', 'user_agent']:
                if field == 'ip':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.ip.ilike(f'%{search_term}%')
                    ).order_by(desc(self.AccessLog.timestamp)).limit(1000).all()
                elif field == 'mac':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.mac.ilike(f'%{search_term}%')
                    ).order_by(desc(self.AccessLog.timestamp)).limit(1000).all()
                elif field == 'user_agent':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.user_agent.ilike(f'%{search_term}%')
                    ).order_by(desc(self.AccessLog.timestamp)).limit(1000).all()
                
                return [log.to_dict(decrypt=True) for log in logs]
            
            # Para campos encriptados (nome, email),
            # precisa carregar todos e filtrar em memória
            all_logs = self.get_access_logs(limit=10000)
            results = []
            
            search_term_lower = search_term.lower()
            
            for log in all_logs:
                if field in log and log[field] and search_term_lower in str(log[field]).lower():
                    results.append(log)
                    
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar logs: {e}")
            return []
            
    def get_user_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de uso do banco de dados"""
        try:
            # Total de acessos
            total_accesses = self.db.session.query(func.count(self.AccessLog.id)).scalar()
            
            # IPs únicos
            unique_ips = self.db.session.query(
                func.count(func.distinct(self.AccessLog.ip_hash))
            ).scalar()
            
            # MACs únicos
            unique_macs = self.db.session.query(
                func.count(func.distinct(self.AccessLog.mac_hash))
            ).filter(self.AccessLog.mac_hash.isnot(None)).scalar()
            
            # Acessos hoje
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_accesses = self.db.session.query(
                func.count(self.AccessLog.id)
            ).filter(self.AccessLog.timestamp >= today_start).scalar()
            
            # Acessos esta semana
            week_start = today_start - timedelta(days=today_start.weekday())
            this_week_accesses = self.db.session.query(
                func.count(self.AccessLog.id)
            ).filter(self.AccessLog.timestamp >= week_start).scalar()
            
            stats = {
                'total_accesses': total_accesses or 0,
                'unique_ips': unique_ips or 0,
                'unique_macs': unique_macs or 0,
                'today_accesses': today_accesses or 0,
                'this_week_accesses': this_week_accesses or 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {
                'total_accesses': 0,
                'unique_ips': 0,
                'unique_macs': 0,
                'today_accesses': 0,
                'this_week_accesses': 0,
                'error': str(e)
            }

# Instância global do gerenciador de dados
data_manager = EncryptedDataManager()
