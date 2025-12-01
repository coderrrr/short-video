"""
认证和授权工具
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.user_schemas import TokenData

# HTTP Bearer认证
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        TokenData对象
        
    Raises:
        HTTPException: 令牌无效时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        employee_id: str = payload.get("employee_id")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, employee_id=employee_id)
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 用户未认证或不存在时抛出
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    # 从数据库查询用户
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户（可扩展添加用户状态检查）
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前活跃用户对象
    """
    # 这里可以添加用户状态检查，如是否被禁用等
    return current_user


async def require_kol(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    要求当前用户为KOL
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前KOL用户对象
        
    Raises:
        HTTPException: 用户不是KOL时抛出
    """
    if not current_user.is_kol:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要KOL权限"
        )
    
    return current_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        密码是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希密码
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')



async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    要求当前用户为管理员
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前管理员用户对象
        
    Raises:
        HTTPException: 用户不是管理员时抛出
    """
    # 检查用户是否有管理员权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user
