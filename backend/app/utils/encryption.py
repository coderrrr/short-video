"""
数据加密工具
提供敏感数据加密和解密功能
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging

logger = logging.getLogger(__name__)


class DataEncryptor:
    """数据加密器"""
    
    def __init__(self, key: str = None):
        """
        初始化加密器
        
        Args:
            key: 加密密钥（如果不提供，将从环境变量读取）
        """
        if key is None:
            key = os.getenv('ENCRYPTION_KEY', 'default-encryption-key-change-in-production')
        
        # 使用PBKDF2派生密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'enterprise-video-platform-salt',
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        
        self.cipher = Fernet(derived_key)
    
    def encrypt(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 明文数据
            
        Returns:
            加密后的数据（Base64编码）
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            
        Returns:
            明文数据
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        加密字典中的指定字段
        
        Args:
            data: 数据字典
            fields: 需要加密的字段列表
            
        Returns:
            加密后的字典
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        解密字典中的指定字段
        
        Args:
            data: 数据字典
            fields: 需要解密的字段列表
            
        Returns:
            解密后的字典
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except Exception:
                    # 如果解密失败，保持原值
                    pass
        return result


# 全局加密器实例
encryptor = DataEncryptor()


def encrypt_sensitive_field(value: str) -> str:
    """
    加密敏感字段
    
    Args:
        value: 明文值
        
    Returns:
        加密后的值
    """
    return encryptor.encrypt(value)


def decrypt_sensitive_field(encrypted_value: str) -> str:
    """
    解密敏感字段
    
    Args:
        encrypted_value: 加密的值
        
    Returns:
        明文值
    """
    return encryptor.decrypt(encrypted_value)


class FieldEncryptionMixin:
    """
    字段加密混入类
    用于SQLAlchemy模型
    """
    
    # 子类需要定义需要加密的字段
    _encrypted_fields = []
    
    def encrypt_fields(self):
        """加密指定字段"""
        for field in self._encrypted_fields:
            value = getattr(self, field, None)
            if value and not value.startswith('enc:'):
                encrypted = encrypt_sensitive_field(value)
                setattr(self, field, f'enc:{encrypted}')
    
    def decrypt_fields(self):
        """解密指定字段"""
        for field in self._encrypted_fields:
            value = getattr(self, field, None)
            if value and value.startswith('enc:'):
                encrypted = value[4:]  # 移除 'enc:' 前缀
                decrypted = decrypt_sensitive_field(encrypted)
                setattr(self, field, decrypted)
    
    def to_dict_with_decryption(self) -> dict:
        """转换为字典并解密敏感字段"""
        self.decrypt_fields()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
