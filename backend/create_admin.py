"""
创建初始管理员账号脚本
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.utils.auth import get_password_hash
import uuid


async def create_admin_user():
    """创建管理员用户"""
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
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
            select(User).where(User.employee_id == "ADMIN001")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("❌ 管理员账号已存在")
            print(f"   员工ID: {existing_admin.employee_id}")
            print(f"   姓名: {existing_admin.name}")
            print(f"   是否KOL: {existing_admin.is_kol}")
            
            # 询问是否重置密码
            reset = input("\n是否重置管理员密码？(y/n): ").strip().lower()
            if reset == 'y':
                password = input("请输入新密码: ").strip()
                if not password:
                    print("❌ 密码不能为空")
                    return
                
                existing_admin.password_hash = get_password_hash(password)
                await session.commit()
                print("✅ 管理员密码已重置")
            return
        
        # 获取管理员信息
        print("=== 创建初始管理员账号 ===\n")
        
        employee_id = input("请输入员工ID (默认: ADMIN001): ").strip() or "ADMIN001"
        name = input("请输入姓名 (默认: 系统管理员): ").strip() or "系统管理员"
        department = input("请输入部门 (默认: 技术部): ").strip() or "技术部"
        position = input("请输入岗位 (默认: 系统管理员): ").strip() or "系统管理员"
        password = input("请输入密码: ").strip()
        
        if not password:
            print("❌ 密码不能为空")
            return
        
        # 创建管理员用户
        admin_user = User(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            name=name,
            department=department,
            position=position,
            password_hash=get_password_hash(password),
            is_kol=True  # 管理员默认具有KOL权限
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print("\n✅ 管理员账号创建成功！")
        print(f"   用户ID: {admin_user.id}")
        print(f"   员工ID: {admin_user.employee_id}")
        print(f"   姓名: {admin_user.name}")
        print(f"   部门: {admin_user.department}")
        print(f"   岗位: {admin_user.position}")
        print(f"   是否KOL: {admin_user.is_kol}")
        print(f"\n请使用以下信息登录：")
        print(f"   员工ID: {admin_user.employee_id}")
        print(f"   密码: ******")
    
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 创建管理员账号失败: {str(e)}")
        sys.exit(1)
