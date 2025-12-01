"""
管理后台 - 标签和分类管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.schemas.tag_schemas import (
    TagCreate, TagUpdate, TagResponse, TagListResponse, TagTreeNode,
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse, CategoryTreeNode,
    KOLCreate, KOLResponse, KOLListResponse,
    BatchTagAssignRequest, BatchTagAssignResponse
)
from app.services.tag_service import TagService, CategoryService
from app.services.user_service import UserService
from app.models.tag import Tag
from app.models.content_tag import ContentTag
from sqlalchemy import func

router = APIRouter(prefix="/admin/tags", tags=["管理后台-标签管理"])
category_router = APIRouter(prefix="/admin/categories", tags=["管理后台-分类管理"])
kol_router = APIRouter(prefix="/admin/kols", tags=["管理后台-KOL管理"])


# ==================== 标签管理 ====================

@router.post("", response_model=TagResponse, summary="创建标签")
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新标签
    
    需求：47.2 - 实现标签CRUD操作
    """
    from sqlalchemy import select, func
    
    tag = await TagService.create_tag(db, tag_data)
    
    # 统计子标签和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(Tag.parent_id == tag.id)
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag.id)
    )
    content_count = content_result.scalar() or 0
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        category=tag.category,
        parent_id=tag.parent_id,
        created_at=tag.created_at,
        children_count=children_count,
        content_count=content_count
    )


@router.get("", response_model=TagListResponse, summary="获取标签列表")
async def list_tags(
    category: Optional[str] = Query(None, description="标签分类"),
    parent_id: Optional[str] = Query(None, description="父标签ID，空字符串表示顶级标签"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取标签列表，支持分类筛选、父标签筛选和搜索
    
    需求：47.1 - 显示所有标签
    """
    from sqlalchemy import select, func
    
    tags, total = await TagService.list_tags(db, category, parent_id, search, page, page_size)
    
    # 构建响应
    tag_responses = []
    for tag in tags:
        children_result = await db.execute(
            select(func.count(Tag.id)).filter(Tag.parent_id == tag.id)
        )
        children_count = children_result.scalar() or 0
        
        content_result = await db.execute(
            select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag.id)
        )
        content_count = content_result.scalar() or 0
        
        tag_responses.append(TagResponse(
            id=tag.id,
            name=tag.name,
            category=tag.category,
            parent_id=tag.parent_id,
            created_at=tag.created_at,
            children_count=children_count,
            content_count=content_count
        ))
    
    return TagListResponse(
        tags=tag_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tree", response_model=List[TagTreeNode], summary="获取标签树")
async def get_tag_tree(
    category: Optional[str] = Query(None, description="标签分类"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取标签树形结构
    
    需求：47.2 - 实现标签分类管理
    """
    return await TagService.get_tag_tree(db, category)


@router.get("/{tag_id}", response_model=TagResponse, summary="获取标签详情")
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取标签详情"""
    from sqlalchemy import select, func
    
    tag = await TagService.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 统计子标签和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(Tag.parent_id == tag.id)
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag.id)
    )
    content_count = content_result.scalar() or 0
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        category=tag.category,
        parent_id=tag.parent_id,
        created_at=tag.created_at,
        children_count=children_count,
        content_count=content_count
    )


@router.put("/{tag_id}", response_model=TagResponse, summary="更新标签")
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新标签信息
    
    需求：47.3 - 实现标签编辑
    """
    from sqlalchemy import select, func
    
    tag = await TagService.update_tag(db, tag_id, tag_data)
    
    # 统计子标签和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(Tag.parent_id == tag.id)
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == tag.id)
    )
    content_count = content_result.scalar() or 0
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        category=tag.category,
        parent_id=tag.parent_id,
        created_at=tag.created_at,
        children_count=children_count,
        content_count=content_count
    )


@router.delete("/{tag_id}", summary="删除标签")
async def delete_tag(
    tag_id: str,
    force: bool = Query(False, description="是否强制删除（包括子标签和内容关联）"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除标签
    
    需求：47.4 - 实现标签删除和清理
    """
    await TagService.delete_tag(db, tag_id, force)
    return {"message": "标签删除成功"}


@router.post("/batch-assign", response_model=BatchTagAssignResponse, summary="批量分配标签")
async def batch_assign_tags(
    request: BatchTagAssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    批量为内容分配标签
    
    需求：47.5 - 实现多标签分配
    """
    result = await TagService.batch_assign_tags(db, request.content_ids, request.tag_ids)
    return BatchTagAssignResponse(**result)


# ==================== 分类管理 ====================

@category_router.post("", response_model=CategoryResponse, summary="创建分类")
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新分类
    
    需求：46.2 - 实现分类CRUD操作
    """
    from sqlalchemy import select, func
    
    category = await CategoryService.create_category(db, category_data)
    
    # 统计子分类和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(
            Tag.parent_id == category.id,
            Tag.category == CategoryService.CATEGORY_TYPE
        )
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category.id)
    )
    content_count = content_result.scalar() or 0
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        created_at=category.created_at,
        children_count=children_count,
        content_count=content_count
    )


@category_router.get("", response_model=CategoryListResponse, summary="获取分类列表")
async def list_categories(
    parent_id: Optional[str] = Query(None, description="父分类ID，空字符串表示顶级分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类列表
    
    需求：46.1 - 显示所有现有分类
    """
    from sqlalchemy import select, func
    
    categories = await CategoryService.list_categories(db, parent_id, search)
    
    # 构建响应
    category_responses = []
    for category in categories:
        children_result = await db.execute(
            select(func.count(Tag.id)).filter(
                Tag.parent_id == category.id,
                Tag.category == CategoryService.CATEGORY_TYPE
            )
        )
        children_count = children_result.scalar() or 0
        
        content_result = await db.execute(
            select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category.id)
        )
        content_count = content_result.scalar() or 0
        
        category_responses.append(CategoryResponse(
            id=category.id,
            name=category.name,
            parent_id=category.parent_id,
            created_at=category.created_at,
            children_count=children_count,
            content_count=content_count
        ))
    
    return CategoryListResponse(
        categories=category_responses,
        total=len(category_responses)
    )


@category_router.get("/tree", response_model=List[CategoryTreeNode], summary="获取分类树")
async def get_category_tree(
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类树形结构
    
    需求：46.1 - 以层次结构显示所有现有分类
    """
    return await CategoryService.get_category_tree(db)


@category_router.get("/{category_id}", response_model=CategoryResponse, summary="获取分类详情")
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取分类详情"""
    from sqlalchemy import select, func
    
    category = await CategoryService.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 统计子分类和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(
            Tag.parent_id == category.id,
            Tag.category == CategoryService.CATEGORY_TYPE
        )
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category.id)
    )
    content_count = content_result.scalar() or 0
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        created_at=category.created_at,
        children_count=children_count,
        content_count=content_count
    )


@category_router.put("/{category_id}", response_model=CategoryResponse, summary="更新分类")
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新分类信息
    
    需求：46.3 - 实现分类编辑
    """
    from sqlalchemy import select, func
    
    category = await CategoryService.update_category(db, category_id, category_data)
    
    # 统计子分类和内容数量
    children_result = await db.execute(
        select(func.count(Tag.id)).filter(
            Tag.parent_id == category.id,
            Tag.category == CategoryService.CATEGORY_TYPE
        )
    )
    children_count = children_result.scalar() or 0
    
    content_result = await db.execute(
        select(func.count(ContentTag.id)).filter(ContentTag.tag_id == category.id)
    )
    content_count = content_result.scalar() or 0
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        created_at=category.created_at,
        children_count=children_count,
        content_count=content_count
    )


@category_router.delete("/{category_id}", summary="删除分类")
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除分类
    
    需求：46.4 - 实现分类删除保护
    需求：46.5 - 当分类具有子分类时，阻止删除
    """
    await CategoryService.delete_category(db, category_id)
    return {"message": "分类删除成功"}


# ==================== KOL管理 ====================

@kol_router.post("", response_model=KOLResponse, summary="创建KOL账号")
async def create_kol(
    kol_data: KOLCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建KOL账号
    
    需求：48.1 - 实现KOL创建接口
    需求：48.2 - 授予后台内容上传权限
    需求：48.3 - 添加KOL徽章
    """
    from sqlalchemy import select, func
    from app.models.content import Content
    from app.models.follow import Follow
    
    user = await UserService.grant_kol_status(db, kol_data.user_id)
    
    # 统计内容和粉丝数量
    content_result = await db.execute(
        select(func.count(Content.id)).filter(Content.creator_id == user.id)
    )
    content_count = content_result.scalar() or 0
    
    follower_result = await db.execute(
        select(func.count(Follow.id)).filter(Follow.followee_id == user.id)
    )
    follower_count = follower_result.scalar() or 0
    
    return KOLResponse(
        id=user.id,
        employee_id=user.employee_id,
        name=user.name,
        avatar_url=user.avatar_url,
        department=user.department,
        position=user.position,
        is_kol=user.is_kol,
        created_at=user.created_at,
        content_count=content_count,
        follower_count=follower_count
    )


@kol_router.get("", response_model=KOLListResponse, summary="获取KOL列表")
async def list_kols(
    search: Optional[str] = Query(None, description="搜索关键词（姓名、员工ID）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取KOL列表
    
    需求：48.1 - 显示所有KOL
    """
    from sqlalchemy import select, func, or_
    from app.models.user import User
    from app.models.content import Content
    from app.models.follow import Follow
    
    query = select(User).filter(User.is_kol == True, User.is_deleted == False)
    
    # 搜索
    if search:
        query = query.filter(
            or_(User.name.like(f"%{search}%"), User.employee_id.like(f"%{search}%"))
        )
    
    # 总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    
    # 分页
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 构建响应
    kol_responses = []
    for user in users:
        content_result = await db.execute(
            select(func.count(Content.id)).filter(Content.creator_id == user.id)
        )
        content_count = content_result.scalar() or 0
        
        follower_result = await db.execute(
            select(func.count(Follow.id)).filter(Follow.followee_id == user.id)
        )
        follower_count = follower_result.scalar() or 0
        
        kol_responses.append(KOLResponse(
            id=user.id,
            employee_id=user.employee_id,
            name=user.name,
            avatar_url=user.avatar_url,
            department=user.department,
            position=user.position,
            is_kol=user.is_kol,
            created_at=user.created_at,
            content_count=content_count,
            follower_count=follower_count
        ))
    
    return KOLListResponse(
        kols=kol_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@kol_router.get("/{user_id}", response_model=KOLResponse, summary="获取KOL详情")
async def get_kol(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取KOL详情"""
    from sqlalchemy import select, func
    from app.models.user import User
    from app.models.content import Content
    from app.models.follow import Follow
    
    result = await db.execute(
        select(User).filter(User.id == user_id, User.is_kol == True, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="KOL不存在")
    
    content_result = await db.execute(
        select(func.count(Content.id)).filter(Content.creator_id == user.id)
    )
    content_count = content_result.scalar() or 0
    
    follower_result = await db.execute(
        select(func.count(Follow.id)).filter(Follow.followee_id == user.id)
    )
    follower_count = follower_result.scalar() or 0
    
    return KOLResponse(
        id=user.id,
        employee_id=user.employee_id,
        name=user.name,
        avatar_url=user.avatar_url,
        department=user.department,
        position=user.position,
        is_kol=user.is_kol,
        created_at=user.created_at,
        content_count=content_count,
        follower_count=follower_count
    )


@kol_router.delete("/{user_id}", summary="撤销KOL状态")
async def revoke_kol(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    撤销KOL状态
    
    需求：48.4 - 实现KOL撤销接口
    """
    user = await UserService.revoke_kol_status(db, user_id)
    return {"message": "KOL状态已撤销", "user_id": user.id}
