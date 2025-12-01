"""
性能监控工具
提供API响应时间监控、慢查询检测和性能分析
"""
import time
import logging
from typing import Callable
from functools import wraps
from fastapi import Request
import asyncio

logger = logging.getLogger(__name__)

# 性能统计
_performance_stats = {
    "total_requests": 0,
    "slow_requests": 0,
    "average_response_time": 0.0,
    "endpoints": {}
}


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, slow_threshold: float = 1.0):
        """
        初始化性能监控器
        
        Args:
            slow_threshold: 慢请求阈值（秒）
        """
        self.slow_threshold = slow_threshold
    
    async def track_request(self, request: Request, call_next):
        """
        跟踪请求性能
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件
            
        Returns:
            响应对象
        """
        start_time = time.time()
        
        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        duration = time.time() - start_time
        
        # 记录性能数据
        endpoint = f"{request.method} {request.url.path}"
        self._record_performance(endpoint, duration)
        
        # 添加响应时间头
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # 记录慢请求
        if duration > self.slow_threshold:
            logger.warning(
                f"慢请求检测: {endpoint} 耗时 {duration:.3f}秒"
            )
            _performance_stats["slow_requests"] += 1
        
        return response
    
    def _record_performance(self, endpoint: str, duration: float):
        """记录性能数据"""
        _performance_stats["total_requests"] += 1
        
        if endpoint not in _performance_stats["endpoints"]:
            _performance_stats["endpoints"][endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }
        
        stats = _performance_stats["endpoints"][endpoint]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        
        # 更新全局平均响应时间
        total_time = sum(
            ep["total_time"] 
            for ep in _performance_stats["endpoints"].values()
        )
        _performance_stats["average_response_time"] = (
            total_time / _performance_stats["total_requests"]
        )


# 全局性能监控器
performance_monitor = PerformanceMonitor()


async def performance_middleware(request: Request, call_next):
    """
    性能监控中间件
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件
        
    Returns:
        响应对象
    """
    return await performance_monitor.track_request(request, call_next)


def get_performance_stats() -> dict:
    """
    获取性能统计数据
    
    Returns:
        性能统计字典
    """
    return _performance_stats.copy()


def reset_performance_stats():
    """重置性能统计"""
    global _performance_stats
    _performance_stats = {
        "total_requests": 0,
        "slow_requests": 0,
        "average_response_time": 0.0,
        "endpoints": {}
    }


def monitor_performance(threshold: float = 1.0):
    """
    性能监控装饰器
    
    Args:
        threshold: 慢操作阈值（秒）
        
    使用示例:
        @monitor_performance(threshold=0.5)
        async def expensive_operation():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                
                if duration > threshold:
                    logger.warning(
                        f"慢操作检测: {func.__name__} 耗时 {duration:.3f}秒"
                    )
        
        return wrapper
    return decorator


class QueryPerformanceTracker:
    """数据库查询性能跟踪器"""
    
    def __init__(self, slow_query_threshold: float = 0.5):
        """
        初始化查询性能跟踪器
        
        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries = []
    
    async def track_query(self, query_func: Callable, query_name: str = ""):
        """
        跟踪查询性能
        
        Args:
            query_func: 查询函数
            query_name: 查询名称
            
        Returns:
            查询结果
        """
        start_time = time.time()
        
        try:
            result = await query_func()
            return result
        finally:
            duration = time.time() - start_time
            
            if duration > self.slow_query_threshold:
                slow_query_info = {
                    "name": query_name or query_func.__name__,
                    "duration": duration,
                    "timestamp": time.time()
                }
                self.slow_queries.append(slow_query_info)
                
                logger.warning(
                    f"慢查询检测: {slow_query_info['name']} "
                    f"耗时 {duration:.3f}秒"
                )
    
    def get_slow_queries(self, limit: int = 10) -> list:
        """
        获取慢查询列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            慢查询列表
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True
        )[:limit]
    
    def clear_slow_queries(self):
        """清除慢查询记录"""
        self.slow_queries.clear()


# 全局查询性能跟踪器
query_tracker = QueryPerformanceTracker()


class ConcurrencyLimiter:
    """并发限制器"""
    
    def __init__(self, max_concurrent: int = 100):
        """
        初始化并发限制器
        
        Args:
            max_concurrent: 最大并发数
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        """进入上下文"""
        await self.semaphore.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.semaphore.release()


def limit_concurrency(max_concurrent: int = 100):
    """
    并发限制装饰器
    
    Args:
        max_concurrent: 最大并发数
        
    使用示例:
        @limit_concurrency(max_concurrent=10)
        async def process_video():
            pass
    """
    limiter = ConcurrencyLimiter(max_concurrent)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with limiter:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
