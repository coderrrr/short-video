"""
快速创建默认管理员账号
员工ID: ADMIN001
密码: admin123
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.utils.auth import get_password_hash
import uuid


async def create_default_admin():
    """创建默认管理员用户"""
    
    # 默认管理员信息
    DEFAULT_EMPLOYEE_ID = "ADMIN001"
    DEFAULT_PASSWORD = "admin123"
    DEFAULT_NAME = "系统管理员"
    DEFAULT_DEPARTMENT = "技术部"
    DEFAULT_POSITION = "系统管理员"
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 检查管理员是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.employee_id == DEFAULT_EMPLOYEE_ID)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"⚠️  管理员账号已存在: {DEFAULT_EMPLOYEE_ID}")
            print(f"   如需重置密码，请使用 create_admin.py 脚本")
            return
        
        # 创建管理员用户
        admin_user = User(
            id=str(uuid.uuid4()),
            employee_id=DEFAULT_EMPLOYEE_ID,
            name=DEFAULT_NAME,
            department=DEFAULT_DEPARTMENT,
            position=DEFAULT_POSITION,
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            is_kol=True,  # 管理员默认具有KOL权限
            is_admin=True  # 设置为管理员
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print("✅ 默认管理员账号创建成功！")
        print(f"\n登录信息：")
        print(f"   员工ID: {DEFAULT_EMPLOYEE_ID}")
        print(f"   密码: {DEFAULT_PASSWORD}")
        print(f"\n⚠️  请在首次登录后立即修改密码！")
    
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_default_admin())
    except Exception as e:
        print(f"❌ 创建管理员账号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
