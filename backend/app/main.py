"""
FastAPI 主应用入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os

from app.database import init_db, close_db, check_db_connection, get_db
from app.api import users, contents, comments, shares, playback, downloads, reports, learning, analytics, gamification, notifications, admin_contents, admin_tags, admin_analytics, admin_upload, files
from app.utils.cache import init_cache
from app.utils.rate_limiter import init_rate_limiter, rate_limit_middleware
from app.utils.security import security_middleware
from app.utils.performance import performance_middleware, get_performance_stats

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    await init_db()
    
    # 初始化缓存（开发环境使用内存缓存）
    init_cache()
    logger.info("缓存系统已初始化")
    
    # 初始化限流器
    init_rate_limiter(max_requests=100, window_seconds=60)
    logger.info("限流器已初始化")
    
    logger.info("应用启动完成")
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")
    await close_db()
    logger.info("应用已关闭")


app = FastAPI(
    title="企业内部短视频平台 API",
    description="企业内部短视频平台后端服务",
    version="0.1.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩中间件（提高传输效率）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 性能监控中间件
app.middleware("http")(performance_middleware)

# 安全中间件
app.middleware("http")(security_middleware)

# 限流中间件
app.middleware("http")(rate_limit_middleware)

# 挂载静态文件目录（用于访问上传的视频和图片）
storage_path = "storage"
if not os.path.exists(storage_path):
    os.makedirs(storage_path, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")


@app.get("/")
async def root():
    """健康检查端点"""
    return {"status": "ok", "message": "企业内部短视频平台 API"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """健康检查"""
    db_status = await check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }


@app.get("/metrics/performance")
async def performance_metrics():
    """性能指标"""
    return get_performance_stats()


# 注册路由
app.include_router(users.router)
app.include_router(contents.router)
app.include_router(comments.router)
app.include_router(shares.router)
app.include_router(playback.router)
app.include_router(downloads.router)
app.include_router(reports.router)
app.include_router(learning.router)
app.include_router(analytics.router)
app.include_router(gamification.router)
app.include_router(notifications.router)
app.include_router(files.router)
app.include_router(admin_contents.router)
app.include_router(admin_upload.router)

# 导入审核管理路由
from app.api import reviews
app.include_router(reviews.router)

# 导入管理后台标签和分类管理路由
app.include_router(admin_tags.router)
app.include_router(admin_tags.category_router)
app.include_router(admin_tags.kol_router)

# 导入管理后台数据分析路由
app.include_router(admin_analytics.router)
