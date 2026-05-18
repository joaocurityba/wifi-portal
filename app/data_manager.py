#!/usr/bin/env python3
"""
Gerenciador de Dados para Portal Cautivo com PostgreSQL
Implementa armazenamento seguro de dados sensíveis com criptografia em banco de dados
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, func, desc
from app.security import security_manager

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None

logger = logging.getLogger(__name__)
try:
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo") if ZoneInfo else timezone(timedelta(hours=-3))
except Exception:
    SAO_PAULO_TZ = timezone(timedelta(hours=-3))

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
                controller_type=data.get('controller_type', 'unifi'),
                controller_site=data.get('controller_site'),
                ap_mac=data.get('ap_mac'),
                gateway_mac=data.get('gateway_mac'),
                vlan_id=data.get('vlan_id'),
                ssid=data.get('ssid'),
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

    def get_access_logs_page(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Obtém uma página de logs de acesso com total real do banco."""
        try:
            page = max(int(page or 1), 1)
            per_page = min(max(int(per_page or 50), 1), 200)

            query = self.AccessLog.query.order_by(
                desc(self.AccessLog.timestamp),
                desc(self.AccessLog.id)
            )
            total = query.order_by(None).count()
            total_pages = max((total + per_page - 1) // per_page, 1)
            if page > total_pages:
                page = total_pages

            offset = (page - 1) * per_page
            logs = query.offset(offset).limit(per_page).all()
            items = [log.to_dict(decrypt=True) for log in logs]

            start_index = offset + 1 if total else 0
            end_index = offset + len(items) if total else 0

            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None,
                'start_index': start_index,
                'end_index': end_index,
            }

        except Exception as e:
            logger.error(f"Erro ao paginar logs de acesso: {e}")
            return {
                'items': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_index': 0,
                'end_index': 0,
                'error': str(e),
            }
            
    def search_access_logs(self, search_term: str, field: str = 'nome') -> List[Dict[str, Any]]:
        """
        Busca em logs de acesso.
        
        NOTA: Para campos encriptados, precisa descriptografar todos os registros primeiro
        (não há como fazer LIKE em campos encriptados diretamente no banco)
        """
        try:
            # Para campos não encriptados (ip, mac, user_agent), pode fazer busca direta
            if field in ['ip', 'mac', 'user_agent', 'controller_type', 'controller_site', 'ssid']:
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
                elif field == 'controller_type':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.controller_type.ilike(f'%{search_term}%')
                    ).order_by(desc(self.AccessLog.timestamp)).limit(1000).all()
                elif field == 'controller_site':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.controller_site.ilike(f'%{search_term}%')
                    ).order_by(desc(self.AccessLog.timestamp)).limit(1000).all()
                elif field == 'ssid':
                    logs = self.AccessLog.query.filter(
                        self.AccessLog.ssid.ilike(f'%{search_term}%')
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
            today_local = datetime.now(SAO_PAULO_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
            today_start = today_local.astimezone(timezone.utc).replace(tzinfo=None)
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
