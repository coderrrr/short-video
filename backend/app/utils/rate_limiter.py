"""
API限流工具
防止API滥用和DDoS攻击
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

# 内存存储（开发环境）
_rate_limit_store = {}


class RateLimiter:
    """限流器"""
    
    def __init__(
        self,
        redis_client=None,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        """
        初始化限流器
        
        Args:
            redis_client: Redis客户端（可选）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def check_rate_limit(self, key: str) -> bool:
        """
        检查是否超过限流
        
        Args:
            key: 限流键（通常是用户ID或IP）
            
        Returns:
            是否允许请求
        """
        try:
            if self.use_redis:
                return await self._check_redis(key)
            else:
                return await self._check_memory(key)
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            # 失败时允许请求
            return True
    
    async def _check_redis(self, key: str) -> bool:
        """使用Redis检查限流"""
        current_time = datetime.now().timestamp()
        window_start = current_time - self.window_seconds
        
        # 使用Redis sorted set存储请求时间戳
        pipe = self.redis.pipeline()
        
        # 移除窗口外的记录
        pipe.zremrangebyscore(key, 0, window_start)
        
        # 添加当前请求
        pipe.zadd(key, {str(current_time): current_time})
        
        # 获取窗口内的请求数
        pipe.zcard(key)
        
        # 设置过期时间
        pipe.expire(key, self.window_seconds)
        
        results = await pipe.execute()
        request_count = results[2]
        
        return request_count <= self.max_requests
    
    async def _check_memory(self, key: str) -> bool:
        """使用内存检查限流"""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.window_seconds)
        
        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        
        # 移除窗口外的记录
        _rate_limit_store[key] = [
            t for t in _rate_limit_store[key]
            if t > window_start
        ]
        
        # 添加当前请求
        _rate_limit_store[key].append(current_time)
        
        # 检查是否超限
        return len(_rate_limit_store[key]) <= self.max_requests
    
    async def get_remaining(self, key: str) -> int:
        """
        获取剩余请求数
        
        Args:
            key: 限流键
            
        Returns:
            剩余请求数
        """
        try:
            if self.use_redis:
                current_time = datetime.now().timestamp()
                window_start = current_time - self.window_seconds
                count = await self.redis.zcount(key, window_start, current_time)
                return max(0, self.max_requests - count)
            else:
                current_time = datetime.now()
                window_start = current_time - timedelta(seconds=self.window_seconds)
                
                if key not in _rate_limit_store:
                    return self.max_requests
                
                valid_requests = [
                    t for t in _rate_limit_store[key]
                    if t > window_start
                ]
                return max(0, self.max_requests - len(valid_requests))
        except Exception as e:
            logger.error(f"获取剩余请求数失败: {e}")
            return self.max_requests


# 全局限流器实例
rate_limiter = RateLimiter()


def init_rate_limiter(redis_client=None, max_requests: int = 100, window_seconds: int = 60):
    """
    初始化限流器
    
    Args:
        redis_client: Redis客户端
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
    """
    global rate_limiter
    rate_limiter = RateLimiter(redis_client, max_requests, window_seconds)


async def rate_limit_middleware(request: Request, call_next):
    """
    限流中间件
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件
        
    Returns:
        响应对象
    """
    # 获取客户端标识（IP或用户ID）
    client_id = request.client.host if request.client else "unknown"
    
    # 如果有用户认证，使用用户ID
    if hasattr(request.state, "user_id"):
        client_id = request.state.user_id
    
    # 检查限流
    allowed = await rate_limiter.check_rate_limit(f"rate_limit:{client_id}")
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试"
        )
    
    # 获取剩余请求数
    remaining = await rate_limiter.get_remaining(f"rate_limit:{client_id}")
    
    response = await call_next(request)
    
    # 添加限流信息到响应头
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(rate_limiter.window_seconds)
    
    return response


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    限流装饰器
    
    Args:
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
        
    使用示例:
        @app.post("/api/upload")
        @rate_limit(max_requests=10, window_seconds=60)
        async def upload_video():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取request对象
            request = kwargs.get('request')
            if not request:
                # 尝试从args中获取
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                client_id = request.client.host if request.client else "unknown"
                if hasattr(request.state, "user_id"):
                    client_id = request.state.user_id
                
                limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
                allowed = await limiter.check_rate_limit(f"rate_limit:{client_id}")
                
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="请求过于频繁，请稍后再试"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
