"""
数据库查询优化工具
提供查询优化、批量操作和N+1问题解决方案
"""
from typing import List, Optional, Any, Type
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    async def batch_load(
        session: AsyncSession,
        model: Type,
        ids: List[Any],
        relationships: Optional[List[str]] = None
    ) -> List[Any]:
        """
        批量加载实体，避免N+1查询问题
        
        Args:
            session: 数据库会话
            model: 模型类
            ids: ID列表
            relationships: 需要预加载的关系列表
            
        Returns:
            实体列表
        """
        if not ids:
            return []
        
        query = select(model).where(model.id.in_(ids))
        
        # 预加载关系
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(model, rel)))
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def paginate(
        session: AsyncSession,
        query,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> dict:
        """
        分页查询
        
        Args:
            session: 数据库会话
            query: SQLAlchemy查询对象
            page: 页码（从1开始）
            page_size: 每页大小
            max_page_size: 最大每页大小
            
        Returns:
            包含items、total、page、page_size的字典
        """
        # 限制每页大小
        page_size = min(page_size, max_page_size)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # 获取分页数据
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        result = await session.execute(paginated_query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    @staticmethod
    async def bulk_insert(
        session: AsyncSession,
        model: Type,
        data_list: List[dict]
    ) -> int:
        """
        批量插入数据
        
        Args:
            session: 数据库会话
            model: 模型类
            data_list: 数据字典列表
            
        Returns:
            插入的记录数
        """
        if not data_list:
            return 0
        
        try:
            objects = [model(**data) for data in data_list]
            session.add_all(objects)
            await session.flush()
            return len(objects)
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            raise
    
    @staticmethod
    async def bulk_update(
        session: AsyncSession,
        model: Type,
        updates: List[dict]
    ) -> int:
        """
        批量更新数据
        
        Args:
            session: 数据库会话
            model: 模型类
            updates: 更新数据列表，每项包含id和要更新的字段
            
        Returns:
            更新的记录数
        """
        if not updates:
            return 0
        
        try:
            count = 0
            for update_data in updates:
                obj_id = update_data.pop('id')
                result = await session.execute(
                    select(model).where(model.id == obj_id)
                )
                obj = result.scalar_one_or_none()
                if obj:
                    for key, value in update_data.items():
                        setattr(obj, key, value)
                    count += 1
            await session.flush()
            return count
        except Exception as e:
            logger.error(f"批量更新失败: {e}")
            raise
    
    @staticmethod
    def optimize_eager_loading(query, model: Type, relationships: List[str]):
        """
        优化预加载策略
        
        Args:
            query: SQLAlchemy查询对象
            model: 模型类
            relationships: 关系列表
            
        Returns:
            优化后的查询对象
        """
        for rel in relationships:
            # 对于一对多关系使用selectinload
            # 对于多对一关系使用joinedload
            rel_attr = getattr(model, rel)
            if hasattr(rel_attr.property, 'uselist') and rel_attr.property.uselist:
                query = query.options(selectinload(rel_attr))
            else:
                query = query.options(joinedload(rel_attr))
        
        return query


class QueryCache:
    """查询结果缓存"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    async def get_or_query(
        self,
        cache_key: str,
        query_func,
        expire: int = 300
    ):
        """
        从缓存获取或执行查询
        
        Args:
            cache_key: 缓存键
            query_func: 查询函数
            expire: 过期时间（秒）
            
        Returns:
            查询结果
        """
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 执行查询
        result = await query_func()
        
        # 存入缓存
        if result is not None:
            await self.cache.set(cache_key, result, expire)
        
        return result


def build_filter_query(query, filters: dict):
    """
    构建过滤查询
    
    Args:
        query: SQLAlchemy查询对象
        filters: 过滤条件字典
        
    Returns:
        添加过滤条件后的查询对象
    """
    for field, value in filters.items():
        if value is not None:
            if isinstance(value, list):
                query = query.where(getattr(query.column_descriptions[0]['type'], field).in_(value))
            else:
                query = query.where(getattr(query.column_descriptions[0]['type'], field) == value)
    
    return query


def build_search_query(query, model: Type, search_fields: List[str], search_term: str):
    """
    构建搜索查询
    
    Args:
        query: SQLAlchemy查询对象
        model: 模型类
        search_fields: 搜索字段列表
        search_term: 搜索词
        
    Returns:
        添加搜索条件后的查询对象
    """
    if not search_term:
        return query
    
    from sqlalchemy import or_
    
    search_conditions = []
    for field in search_fields:
        field_attr = getattr(model, field)
        search_conditions.append(field_attr.like(f"%{search_term}%"))
    
    if search_conditions:
        query = query.where(or_(*search_conditions))
    
    return query
