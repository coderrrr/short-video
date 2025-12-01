"""
标签和分类管理服务
"""
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select, delete
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import HTTPException

from app.models.tag import Tag
from app.models.content_tag import ContentTag
from app.models.content import Content
from app.schemas.tag_schemas import (
    TagCreate, TagUpdate, TagResponse, TagTreeNode,
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode
)


class TagService:
    """标签服务"""
    
    @staticmethod
    async def create_tag(db: AsyncSession, tag_data: TagCreate) -> Tag:
        """
        创建标签
        
        需求：47.1 - 实现标签CRUD接口
        """
        # 验证父标签是否存在
        if tag_data.parent_id:
            result = await db.execute(select(Tag).filter(Tag.id == tag_data.parent_id))
            parent = result.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=404, detail="父标签不存在")
        
        # 检查同名标签
        result = await db.execute(
            select(Tag).filter(
                Tag.name == tag_data.name,
                Tag.category == tag_data.category
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        
        # 创建标签
        tag = Tag(
            id=str(uuid4()),
            name=tag_data.name,
            category=tag_data.category,
            parent_id=tag_data.parent_id
        )
        
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    @staticmethod
    async def get_tag(db: AsyncSession, tag_id: str) -> Optional[Tag]:
        """获取标签详情"""
        result = await db.execute(select(Tag).filter(Tag.id == tag_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_tags(
        db: AsyncSession,
        category: Optional[str] = None,
        parent_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Tag], int]:
        """
        获取标签列表
        
        需求：47.1 - 实现标签CRUD接口
        """
        query = select(Tag)
        
        # 排除分类数据（category='category'的是分类，不是标签）
        query = query.filter(Tag.category != CategoryService.CATEGORY_TYPE)
        
        # 按分类筛选
        if category:
            query = query.filter(Tag.category == category)
        
        # 按父标签筛选
        if parent_id is not None:
            if parent_id == "":
                # 查询顶级标签
                query = query.filter(Tag.parent_id.is_(None))
            else:
                query = query.filter(Tag.parent_id == parent_id)
        
        # 搜索
        if search:
            query = query.filter(Tag.name.like(f"%{search}%"))
        
        # 总数
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar() or 0
        
        # 分页
        query = query.order_by(Tag.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        tags = result.scalars().all()
        
        return tags, total
    
    @staticmethod
    async def update_tag(db: AsyncSession, tag_id: str, tag_data: TagUpdate) -> Tag:
        """
        更新标签
        
        需求：47.1 - 实现标签CRUD接口
        """
        result = await db.execute(select(Tag).filter(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        # 验证父标签
        if tag_data.parent_id is not None:
            if tag_data.parent_id:
                # 检查父标签是否存在
                parent_result = await db.execute(select(Tag).filter(Tag.id == tag_data.parent_id))
                parent = parent_result.scalar_one_or_none()
                if not parent:
                    raise HTTPException(status_code=404, detail="父标签不存在")
                
                # 防止循环引用
                if tag_data.parent_id == tag_id:
                    raise HTTPException(status_code=400, detail="不能将标签设置为自己的父标签")
                
                # 检查是否会形成循环
                if await TagService._would_create_cycle(db, tag_id, tag_data.parent_id):
                    raise HTTPException(status_code=400, detail="不能形成循环引用")
        
        # 更新字段
        if tag_data.name is not None:
            # 检查同名标签
            existing_result = await db.execute(
                select(Tag).filter(
                    Tag.name == tag_data.name,
                    Tag.category == (tag_data.category or tag.category),
                    Tag.id != tag_id
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=400, detail="标签名称已存在")
            
            tag.name = tag_data.name
        
        if tag_data.category is not None:
            tag.category = tag_data.category
        
        if tag_data.parent_id is not None:
            tag.parent_id = tag_data.parent_id if tag_data.parent_id else None
        
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    @staticmethod
    async def delete_tag(db: AsyncSession, tag_id: str, force: bool = False) -> None:
        """
        删除标签
        
        需求：47.4 - 实现标签删除和清理
        """
        result = await db.execute(select(Tag).filter(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        # 检查是否有子标签
        children_result = await db.execute(
            select(func.count(Tag.id)).filter(Tag.parent_id == tag_id)
        )
        children_count = children_result.scalar() or 0
        if children_count > 0 and not force:
            raise HTTPException(
                status_code=400,
                detail=f"标签下有 {children_count} 个子标签，请先删除子标签或使用强制删除"
            )
        
        # 检查是否有关联内容
        content_result = await db.execute(
            select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag_id)
        )
        content_count = content_result.scalar() or 0
        if content_count > 0 and not force:
            raise HTTPException(
                status_code=400,
                detail=f"标签关联了 {content_count} 个内容，请先解除关联或使用强制删除"
            )
        
        # 如果强制删除，先删除所有关联
        if force:
            # 删除内容关联
            await db.execute(
                delete(ContentTag).where(ContentTag.tag_id == tag_id)
            )
            
            # 递归删除子标签
            children_result = await db.execute(select(Tag).filter(Tag.parent_id == tag_id))
            children = children_result.scalars().all()
            for child in children:
                await TagService.delete_tag(db, child.id, force=True)
        
        # 删除标签
        await db.delete(tag)
        await db.commit()
    
    @staticmethod
    async def get_tag_tree(db: AsyncSession, category: Optional[str] = None) -> List[TagTreeNode]:
        """
        获取标签树
        
        需求：47.2 - 实现标签分类管理
        """
        # 查询所有标签（排除分类数据）
        query = select(Tag).filter(Tag.category != CategoryService.CATEGORY_TYPE)
        if category:
            query = query.filter(Tag.category == category)
        
        result = await db.execute(query)
        all_tags = result.scalars().all()
        
        # 构建标签字典
        tag_dict = {tag.id: tag for tag in all_tags}
        
        # 统计子标签和内容数量
        tag_stats = {}
        for tag in all_tags:
            # 统计子标签数量
            children_result = await db.execute(
                select(func.count(Tag.id)).filter(Tag.parent_id == tag.id)
            )
            children_count = children_result.scalar() or 0
            
            # 统计内容数量
            content_result = await db.execute(
                select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag.id)
            )
            content_count = content_result.scalar() or 0
            
            tag_stats[tag.id] = {
                'children_count': children_count,
                'content_count': content_count
            }
        
        # 构建树结构
        def build_tree(parent_id: Optional[str]) -> List[TagTreeNode]:
            nodes = []
            for tag in all_tags:
                if tag.parent_id == parent_id:
                    stats = tag_stats.get(tag.id, {})
                    node = TagTreeNode(
                        id=tag.id,
                        name=tag.name,
                        category=tag.category,
                        parent_id=tag.parent_id,
                        created_at=tag.created_at,
                        children_count=stats.get('children_count', 0),
                        content_count=stats.get('content_count', 0),
                        children=build_tree(tag.id)
                    )
                    nodes.append(node)
            return nodes
        
        return build_tree(None)
    
    @staticmethod
    async def batch_assign_tags(
        db: AsyncSession,
        content_ids: List[str],
        tag_ids: List[str]
    ) -> Dict[str, Any]:
        """
        批量分配标签
        
        需求：47.5 - 实现多标签分配
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        # 验证标签是否存在
        result = await db.execute(select(Tag).filter(Tag.id.in_(tag_ids)))
        tags = result.scalars().all()
        if len(tags) != len(tag_ids):
            found_ids = {tag.id for tag in tags}
            missing_ids = set(tag_ids) - found_ids
            raise HTTPException(
                status_code=404,
                detail=f"以下标签不存在: {', '.join(missing_ids)}"
            )
        
        # 验证内容是否存在
        result = await db.execute(select(Content).filter(Content.id.in_(content_ids)))
        contents = result.scalars().all()
        if len(contents) != len(content_ids):
            found_ids = {content.id for content in contents}
            missing_ids = set(content_ids) - found_ids
            raise HTTPException(
                status_code=404,
                detail=f"以下内容不存在: {', '.join(missing_ids)}"
            )
        
        # 批量分配
        for content_id in content_ids:
            for tag_id in tag_ids:
                try:
                    # 检查是否已存在
                    result = await db.execute(
                        select(ContentTag).filter(
                            ContentTag.content_id == content_id,
                            ContentTag.tag_id == tag_id
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        content_tag = ContentTag(
                            id=str(uuid4()),
                            content_id=content_id,
                            tag_id=tag_id,
                            is_auto=False  # 手动分配
                        )
                        db.add(content_tag)
                        success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"内容 {content_id} 分配标签 {tag_id} 失败: {str(e)}")
        
        await db.commit()
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }
    
    @staticmethod
    async def _would_create_cycle(db: AsyncSession, tag_id: str, new_parent_id: str) -> bool:
        """检查是否会形成循环引用"""
        visited = set()
        current_id = new_parent_id
        
        while current_id:
            if current_id == tag_id:
                return True
            
            if current_id in visited:
                # 已经访问过，说明有循环
                return True
            
            visited.add(current_id)
            
            # 查找父标签
            result = await db.execute(select(Tag).filter(Tag.id == current_id))
            parent = result.scalar_one_or_none()
            if not parent:
                break
            
            current_id = parent.parent_id
        
        return False


class CategoryService:
    """分类服务（使用Tag实现，category字段为None或'category'）"""
    
    CATEGORY_TYPE = "category"
    
    @staticmethod
    async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Tag:
        """
        创建分类
        
        需求：46.2 - 实现分类CRUD操作
        """
        # 验证父分类是否存在
        if category_data.parent_id:
            result = await db.execute(
                select(Tag).filter(
                    Tag.id == category_data.parent_id,
                    Tag.category == CategoryService.CATEGORY_TYPE
                )
            )
            parent = result.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=404, detail="父分类不存在")
        
        # 检查同名分类
        result = await db.execute(
            select(Tag).filter(
                Tag.name == category_data.name,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="分类名称已存在")
        
        # 创建分类
        category = Tag(
            id=str(uuid4()),
            name=category_data.name,
            category=CategoryService.CATEGORY_TYPE,
            parent_id=category_data.parent_id
        )
        
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return category
    
    @staticmethod
    async def get_category(db: AsyncSession, category_id: str) -> Optional[Tag]:
        """获取分类详情"""
        result = await db.execute(
            select(Tag).filter(
                Tag.id == category_id,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_categories(
        db: AsyncSession,
        parent_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Tag]:
        """
        获取分类列表
        
        需求：46.1 - 以层次结构显示所有现有分类
        """
        query = select(Tag).filter(Tag.category == CategoryService.CATEGORY_TYPE)
        
        # 按父分类筛选
        if parent_id is not None:
            if parent_id == "":
                # 查询顶级分类
                query = query.filter(Tag.parent_id.is_(None))
            else:
                query = query.filter(Tag.parent_id == parent_id)
        
        # 搜索
        if search:
            query = query.filter(Tag.name.like(f"%{search}%"))
        
        query = query.order_by(Tag.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_category(db: AsyncSession, category_id: str, category_data: CategoryUpdate) -> Tag:
        """
        更新分类
        
        需求：46.3 - 实现分类编辑
        """
        result = await db.execute(
            select(Tag).filter(
                Tag.id == category_id,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 验证父分类
        if category_data.parent_id is not None:
            if category_data.parent_id:
                # 检查父分类是否存在
                parent_result = await db.execute(
                    select(Tag).filter(
                        Tag.id == category_data.parent_id,
                        Tag.category == CategoryService.CATEGORY_TYPE
                    )
                )
                parent = parent_result.scalar_one_or_none()
                if not parent:
                    raise HTTPException(status_code=404, detail="父分类不存在")
                
                # 防止循环引用
                if category_data.parent_id == category_id:
                    raise HTTPException(status_code=400, detail="不能将分类设置为自己的父分类")
                
                # 检查是否会形成循环
                if await TagService._would_create_cycle(db, category_id, category_data.parent_id):
                    raise HTTPException(status_code=400, detail="不能形成循环引用")
        
        # 更新字段
        if category_data.name is not None:
            # 检查同名分类
            existing_result = await db.execute(
                select(Tag).filter(
                    Tag.name == category_data.name,
                    Tag.category == CategoryService.CATEGORY_TYPE,
                    Tag.id != category_id
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=400, detail="分类名称已存在")
            
            category.name = category_data.name
        
        if category_data.parent_id is not None:
            category.parent_id = category_data.parent_id if category_data.parent_id else None
        
        await db.commit()
        await db.refresh(category)
        
        return category
    
    @staticmethod
    async def delete_category(db: AsyncSession, category_id: str) -> None:
        """
        删除分类
        
        需求：46.4 - 实现分类删除保护
        需求：46.5 - 当分类具有子分类时，阻止删除
        """
        result = await db.execute(
            select(Tag).filter(
                Tag.id == category_id,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 检查是否有子分类
        children_result = await db.execute(
            select(func.count(Tag.id)).filter(
                Tag.parent_id == category_id,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        children_count = children_result.scalar() or 0
        if children_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"分类下有 {children_count} 个子分类，请先删除或重新分配子分类"
            )
        
        # 检查是否有关联内容
        content_result = await db.execute(
            select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category_id)
        )
        content_count = content_result.scalar() or 0
        if content_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"分类关联了 {content_count} 个内容，请先重新分配内容到其他分类"
            )
        
        # 删除分类
        await db.delete(category)
        await db.commit()
    
    @staticmethod
    async def get_category_tree(db: AsyncSession) -> List[CategoryTreeNode]:
        """
        获取分类树
        
        需求：46.1 - 以层次结构显示所有现有分类
        """
        # 查询所有分类
        result = await db.execute(
            select(Tag).filter(Tag.category == CategoryService.CATEGORY_TYPE)
        )
        all_categories = result.scalars().all()
        
        # 统计子分类和内容数量
        category_stats = {}
        for category in all_categories:
            # 统计子分类数量
            children_result = await db.execute(
                select(func.count(Tag.id)).filter(
                    Tag.parent_id == category.id,
                    Tag.category == CategoryService.CATEGORY_TYPE
                )
            )
            children_count = children_result.scalar() or 0
            
            # 统计内容数量
            content_result = await db.execute(
                select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category.id)
            )
            content_count = content_result.scalar() or 0
            
            category_stats[category.id] = {
                'children_count': children_count,
                'content_count': content_count
            }
        
        # 构建树结构
        def build_tree(parent_id: Optional[str]) -> List[CategoryTreeNode]:
            nodes = []
            for category in all_categories:
                if category.parent_id == parent_id:
                    stats = category_stats.get(category.id, {})
                    node = CategoryTreeNode(
                        id=category.id,
                        name=category.name,
                        parent_id=category.parent_id,
                        created_at=category.created_at,
                        children_count=stats.get('children_count', 0),
                        content_count=stats.get('content_count', 0),
                        children=build_tree(category.id)
                    )
                    nodes.append(node)
            return nodes
        
        return build_tree(None)
