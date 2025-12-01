"""
缓存工具模块
提供Redis缓存和内存缓存功能
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import asyncio
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# 内存缓存（开发环境使用）
_memory_cache = {}


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client=None):
        """
        初始化缓存管理器
        
        Args:
            redis_client: Redis客户端实例（可选）
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        try:
            if self.use_redis:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            else:
                # 使用内存缓存
                if key in _memory_cache:
                    return _memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            if self.use_redis:
                serialized = json.dumps(value, ensure_ascii=False)
                if expire:
                    await self.redis.setex(key, expire, serialized)
                else:
                    await self.redis.set(key, serialized)
            else:
                # 使用内存缓存
                _memory_cache[key] = value
                if expire:
                    # 简单的过期处理
                    asyncio.create_task(self._expire_memory_cache(key, expire))
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            if self.use_redis:
                await self.redis.delete(key)
            else:
                if key in _memory_cache:
                    del _memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 键模式（如 "user:*"）
            
        Returns:
            删除的键数量
        """
        try:
            if self.use_redis:
                keys = await self.redis.keys(pattern)
                if keys:
                    return await self.redis.delete(*keys)
                return 0
            else:
                # 内存缓存简单匹配
                import fnmatch
                keys_to_delete = [
                    k for k in _memory_cache.keys() 
                    if fnmatch.fnmatch(k, pattern)
                ]
                for key in keys_to_delete:
                    del _memory_cache[key]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"清除缓存模式失败: {e}")
            return 0
    
    async def _expire_memory_cache(self, key: str, seconds: int):
        """内存缓存过期处理"""
        await asyncio.sleep(seconds)
        if key in _memory_cache:
            del _memory_cache[key]


# 全局缓存管理器实例
cache_manager = CacheManager()


def init_cache(redis_client=None):
    """
    初始化缓存管理器
    
    Args:
        redis_client: Redis客户端实例
    """
    global cache_manager
    cache_manager = CacheManager(redis_client)


def cache_key(*args, **kwargs) -> str:
    """
    生成缓存键
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        缓存键字符串
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    prefix: str,
    expire: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        expire: 过期时间（秒）
        key_builder: 自定义键生成函数
        
    使用示例:
        @cached(prefix="user", expire=600)
        async def get_user(user_id: str):
            return await db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_builder:
                key = f"{prefix}:{key_builder(*args, **kwargs)}"
            else:
                key = f"{prefix}:{cache_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_value = await cache_manager.get(key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {key}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache_manager.set(key, result, expire)
                logger.debug(f"缓存设置: {key}")
            
            return result
        return wrapper
    return decorator


async def invalidate_cache(prefix: str, *args, **kwargs):
    """
    使缓存失效
    
    Args:
        prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数
    """
    key = f"{prefix}:{cache_key(*args, **kwargs)}"
    await cache_manager.delete(key)


async def invalidate_pattern(pattern: str):
    """
    使匹配模式的缓存失效
    
    Args:
        pattern: 键模式
    """
    await cache_manager.clear_pattern(pattern)
