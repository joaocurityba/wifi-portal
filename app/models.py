"""
SQLAlchemy models for WiFi Portal Application.
Defines User and AccessLog tables with encryption for sensitive data.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Text, DateTime, Integer, Index, event
from sqlalchemy.types import TypeDecorator
import hashlib

db = SQLAlchemy()

# Global cipher suite reference (will be set from security_manager)
_cipher_suite = None

def set_encryption_cipher(cipher):
    """Set the global cipher suite for encryption."""
    global _cipher_suite
    _cipher_suite = cipher
    import logging
    logging.getLogger(__name__).info(f"Encryption cipher configured: {cipher is not None}")


class EncryptedString(TypeDecorator):
    """
    Custom SQLAlchemy type for encrypted string fields.
    Automatically encrypts data on write and decrypts on read.
    """
    impl = String
    cache_ok = True
    
    def __init__(self, length=255, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = length
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        import logging
        logger = logging.getLogger(__name__)
        
        if value is None:
            return None
        if _cipher_suite is None:
            logger.warning(f"Cipher suite is None! Cannot encrypt: {value[:20]}...")
            return value
        try:
            encrypted = _cipher_suite.encrypt(value.encode())
            logger.debug(f"Encrypted {len(value)} chars to {len(encrypted.decode())} chars")
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return value
    
    def process_result_value(self, value, dialect):
        """Decrypt value when reading from database."""
        if value is None:
            return None
        if _cipher_suite is None:
            return value
        try:
            decrypted = _cipher_suite.decrypt(value.encode())
            return decrypted.decode()
        except Exception:
            # If decryption fails, return as-is
            return value


class User(db.Model):
    """Admin user model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(255), nullable=False)
    email = db.Column(String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    reset_token = db.Column(String(64), nullable=True)
    reset_expires = db.Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reset_token': self.reset_token,
            'reset_expires': self.reset_expires.isoformat() if self.reset_expires else None
        }


class AccessLog(db.Model):
    """Access log model for tracking user portal access."""
    __tablename__ = 'access_logs'
    
    id = db.Column(Integer, primary_key=True)
    
    # Encrypted sensitive fields
    nome = db.Column(EncryptedString(500), nullable=False)  # Will be encrypted
    email = db.Column(EncryptedString(500), nullable=False)  # Will be encrypted
    
    # Non-encrypted fields
    ip = db.Column(String(45), nullable=True, default='0.0.0.0')  # IPv4 or IPv6
    ip_hash = db.Column(String(64), nullable=True, index=True)  # SHA-256 hash for queries
    mac = db.Column(String(17), nullable=True)
    mac_hash = db.Column(String(64), nullable=True, index=True)  # SHA-256 hash for queries
    user_agent = db.Column(Text, nullable=True)
    
    # Metadata
    access_id = db.Column(String(64), unique=True, nullable=False, index=True)
    timestamp = db.Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Composite index for efficient pagination
    __table_args__ = (
        Index('idx_timestamp_id', 'timestamp', 'id'),
    )
    
    def __repr__(self):
        return f'<AccessLog {self.access_id} at {self.timestamp}>'
    
    def to_dict(self, decrypt=False):
        """
        Convert access log to dictionary.
        
        Args:
            decrypt: If True, returns decrypted sensitive fields
        """
        return {
            'nome': self.nome if decrypt else '[encrypted]',
            'email': self.email if decrypt else '[encrypted]',
            'ip': self.ip,
            'ip_hash': self.ip_hash,
            'mac': self.mac,
            'mac_hash': self.mac_hash,
            'user_agent': self.user_agent,
            'access_id': self.access_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data': self.timestamp.strftime('%Y-%m-%d') if self.timestamp else None,
            'hora': self.timestamp.strftime('%H:%M:%S') if self.timestamp else None,
        }
    
    @staticmethod
    def hash_value(value):
        """Generate SHA-256 hash of a value for indexing."""
        if not value:
            return None
        return hashlib.sha256(value.encode()).hexdigest()
    
    @staticmethod
    def generate_access_id():
        """Generate unique access ID."""
        import secrets
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(8)
        return f"{timestamp}_{random_part}"
