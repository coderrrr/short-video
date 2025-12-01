"""
数据库连接管理
提供数据库连接池和会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 创建异步数据库引擎
# 使用连接池提高性能
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境下打印SQL语句
    # 异步引擎使用默认的AsyncAdaptedQueuePool
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=3600,  # 连接回收时间（秒）
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    
    使用示例:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库
    注意：表结构由 database/create_tables.sql 脚本创建
    """
    # from app.models.base import Base
    
    # async with engine.begin() as conn:
    #     # 在开发环境下可以使用 drop_all 重建表
    #     # await conn.run_sync(Base.metadata.drop_all)
    #     # 注释掉自动创建表，改用 SQL 脚本管理
    #     # await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库初始化完成（表结构由 SQL 脚本管理）")


async def close_db():
    """
    关闭数据库连接
    应用关闭时调用
    """
    await engine.dispose()
    logger.info("数据库连接已关闭")


async def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True，否则返回False
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
