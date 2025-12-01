"""
安全工具模块
提供SQL注入防护、XSS防护、CSRF防护和数据加密功能
"""
import re
import html
import secrets
from typing import Optional, Any
from fastapi import Request, HTTPException, status
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """安全验证器"""
    
    # SQL注入危险关键词
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('|\"|\`)",
    ]
    
    # XSS危险标签和属性
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"javascript:",
        r"on\w+\s*=",
        r"<embed[^>]*>",
        r"<object[^>]*>",
    ]
    
    @classmethod
    def validate_sql_injection(cls, value: str) -> bool:
        """
        检测SQL注入
        
        Args:
            value: 要检测的字符串
            
        Returns:
            是否安全（True表示安全）
        """
        if not value:
            return True
        
        value_upper = value.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"检测到SQL注入尝试: {value}")
                return False
        
        return True
    
    @classmethod
    def sanitize_sql_input(cls, value: str) -> str:
        """
        清理SQL输入
        
        Args:
            value: 输入字符串
            
        Returns:
            清理后的字符串
        """
        if not value:
            return value
        
        # 移除危险字符
        value = value.replace("'", "''")  # 转义单引号
        value = value.replace(";", "")    # 移除分号
        value = value.replace("--", "")   # 移除注释
        
        return value
    
    @classmethod
    def validate_xss(cls, value: str) -> bool:
        """
        检测XSS攻击
        
        Args:
            value: 要检测的字符串
            
        Returns:
            是否安全（True表示安全）
        """
        if not value:
            return True
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"检测到XSS攻击尝试: {value}")
                return False
        
        return True
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """
        清理HTML内容，防止XSS
        
        Args:
            value: HTML字符串
            
        Returns:
            清理后的字符串
        """
        if not value:
            return value
        
        # HTML实体编码
        return html.escape(value)
    
    @classmethod
    def validate_file_path(cls, path: str) -> bool:
        """
        验证文件路径，防止路径遍历攻击
        
        Args:
            path: 文件路径
            
        Returns:
            是否安全
        """
        if not path:
            return False
        
        # 检测路径遍历
        dangerous_patterns = [
            "..",
            "~",
            "/etc/",
            "/root/",
            "\\\\",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in path:
                logger.warning(f"检测到路径遍历尝试: {path}")
                return False
        
        return True


class CSRFProtection:
    """CSRF防护"""
    
    @staticmethod
    def generate_token() -> str:
        """
        生成CSRF令牌
        
        Returns:
            CSRF令牌
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(request_token: str, session_token: str) -> bool:
        """
        验证CSRF令牌
        
        Args:
            request_token: 请求中的令牌
            session_token: 会话中的令牌
            
        Returns:
            是否有效
        """
        if not request_token or not session_token:
            return False
        
        return secrets.compare_digest(request_token, session_token)


class DataEncryption:
    """数据加密"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """
        哈希密码
        
        Args:
            password: 明文密码
            salt: 盐值（可选）
            
        Returns:
            (哈希值, 盐值)
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        import hashlib
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )
        
        return hashed.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希值
            salt: 盐值
            
        Returns:
            是否匹配
        """
        new_hash, _ = DataEncryption.hash_password(password, salt)
        return secrets.compare_digest(new_hash, hashed)
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: str) -> str:
        """
        加密敏感数据
        
        Args:
            data: 明文数据
            key: 加密密钥
            
        Returns:
            加密后的数据
        """
        # 简单的HMAC加密（生产环境应使用AES等更强的加密）
        return hmac.new(
            key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """
        遮蔽敏感数据
        
        Args:
            data: 原始数据
            mask_char: 遮蔽字符
            visible_chars: 可见字符数
            
        Returns:
            遮蔽后的数据
        """
        if not data or len(data) <= visible_chars:
            return data
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)


async def security_middleware(request: Request, call_next):
    """
    安全中间件
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件
        
    Returns:
        响应对象
    """
    # 添加安全响应头
    response = await call_next(request)
    
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    
    # 防止MIME类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS防护
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # 内容安全策略
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # HTTPS严格传输安全
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


def validate_input(
    sql_injection: bool = True,
    xss: bool = True,
    path_traversal: bool = False
):
    """
    输入验证装饰器
    
    Args:
        sql_injection: 是否检查SQL注入
        xss: 是否检查XSS
        path_traversal: 是否检查路径遍历
        
    使用示例:
        @app.post("/api/comment")
        @validate_input(sql_injection=True, xss=True)
        async def create_comment(text: str):
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 验证所有字符串参数
            for key, value in kwargs.items():
                if isinstance(value, str):
                    if sql_injection and not SecurityValidator.validate_sql_injection(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="检测到非法输入"
                        )
                    
                    if xss and not SecurityValidator.validate_xss(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="检测到非法输入"
                        )
                    
                    if path_traversal and not SecurityValidator.validate_file_path(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="非法文件路径"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
