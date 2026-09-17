# -*- coding: utf-8 -*-
"""
MySQL数据库配置模块
支持环境变量读取和敏感信息加密存储
"""
import os
import base64
import hashlib
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from dotenv import load_dotenv

_ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(_ROOT_DIR / "backend" / ".env", override=False)

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类，支持加密存储敏感信息"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._encryption_key = None
        self._cipher = None
        
        self._load_config()
    
    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """从密码生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _load_config(self):
        """加载配置"""
        self.host = os.getenv('DATABASE_HOST', 'localhost')
        self.port = int(os.getenv('DATABASE_PORT', 3306))
        self.user = os.getenv('DATABASE_USER', 'root')
        self.database = os.getenv('DATABASE_NAME', 'health_diet_db')
        
        password = os.getenv('DATABASE_PASSWORD', '')
        self.password = self._decrypt_password(password) if password else ''
        
        self.charset = os.getenv('DATABASE_CHARSET', 'utf8mb4')
        
        self.pool_size = int(os.getenv('DATABASE_POOL_SIZE', 5))
        self.max_overflow = int(os.getenv('DATABASE_MAX_OVERFLOW', 10))
        self.pool_timeout = int(os.getenv('DATABASE_POOL_TIMEOUT', 30))
        self.pool_recycle = int(os.getenv('DATABASE_POOL_RECYCLE', 3600))
        
        self.connect_timeout = int(os.getenv('DATABASE_CONNECT_TIMEOUT', 10))
        self.read_timeout = int(os.getenv('DATABASE_READ_TIMEOUT', 30))
        self.write_timeout = int(os.getenv('DATABASE_WRITE_TIMEOUT', 30))
        
        self.auto_reconnect = os.getenv('DATABASE_AUTO_RECONNECT', 'true').lower() == 'true'
        self.max_reconnect_attempts = int(os.getenv('DATABASE_MAX_RECONNECT_ATTEMPTS', 3))
        self.reconnect_delay = int(os.getenv('DATABASE_RECONNECT_DELAY', 1))
        
        self.use_ssl = os.getenv('DATABASE_USE_SSL', 'false').lower() == 'true'
        self.ssl_ca = os.getenv('DATABASE_SSL_CA', '')
        self.ssl_cert = os.getenv('DATABASE_SSL_CERT', '')
        self.ssl_key = os.getenv('DATABASE_SSL_KEY', '')
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """解密密码"""
        if not encrypted_password:
            return ''
        
        try:
            if encrypted_password.startswith('ENC:'):
                encrypted_data = encrypted_password[4:]
                salt = os.getenv('DATABASE_ENCRYPTION_SALT', '').encode()
                if not salt:
                    logger.warning("未设置加密盐，无法解密密码")
                    return encrypted_password
                
                key = self._generate_key_from_password(
                    os.getenv('DATABASE_ENCRYPTION_KEY', 'default_key'),
                    salt
                )
                cipher = Fernet(key)
                decrypted = cipher.decrypt(encrypted_data.encode())
                return decrypted.decode()
            else:
                return encrypted_password
        except Exception as e:
            logger.error(f"密码解密失败: {e}")
            return encrypted_password
    
    def encrypt_password(self, password: str) -> str:
        """加密密码"""
        if not password:
            return ''
        
        try:
            salt = os.getenv('DATABASE_ENCRYPTION_SALT', '').encode()
            if not salt:
                logger.warning("未设置加密盐，无法加密密码")
                return password
            
            key = self._generate_key_from_password(
                os.getenv('DATABASE_ENCRYPTION_KEY', 'default_key'),
                salt
            )
            cipher = Fernet(key)
            encrypted = cipher.encrypt(password.encode())
            return f'ENC:{encrypted.decode()}'
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            return password
    
    def get_connection_params(self) -> dict:
        """获取连接参数"""
        params = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'connect_timeout': self.connect_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout,
        }
        
        if self.use_ssl:
            ssl_config = {}
            if self.ssl_ca:
                ssl_config['ca'] = self.ssl_ca
            if self.ssl_cert:
                ssl_config['cert'] = self.ssl_cert
            if self.ssl_key:
                ssl_config['key'] = self.ssl_key
            params['ssl'] = ssl_config if ssl_config else None
        
        return params
    
    def get_pool_config(self) -> dict:
        """获取连接池配置"""
        return {
            'maxconnections': self.pool_size,
            'maxcached': self.pool_size,
            'maxshared': self.pool_size,
            'maxusage': None,
            'blocking': True,
            'setsession': None,
            'ping': 1,
            'reset': True,
        }
    
    def validate_config(self) -> tuple[bool, str]:
        """验证配置"""
        if not self.host:
            return False, "数据库主机地址不能为空"
        
        if not self.user:
            return False, "数据库用户名不能为空"
        
        if not self.database:
            return False, "数据库名称不能为空"
        
        if self.port < 1 or self.port > 65535:
            return False, f"无效的端口号: {self.port}"
        
        if self.pool_size < 1:
            return False, f"连接池大小必须大于0: {self.pool_size}"
        
        return True, "配置验证通过"
    
    def __repr__(self) -> str:
        """安全的配置表示（隐藏密码）"""
        return (f"DatabaseConfig(host={self.host}, port={self.port}, "
                f"user={self.user}, database={self.database}, "
                f"pool_size={self.pool_size})")


_config_instance: Optional[DatabaseConfig] = None


def get_config() -> DatabaseConfig:
    """获取数据库配置单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = DatabaseConfig()
    return _config_instance


def reload_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = DatabaseConfig()
