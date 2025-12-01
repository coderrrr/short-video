"""
学习计划API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models import get_db, User
from app.services.learning_service import LearningService
from app.schemas.learning_schemas import (
    TopicCreate, TopicUpdate, TopicResponse, TopicDetailResponse,
    TopicAddContent, TopicReorderContent,
    CollectionCreate, CollectionUpdate, CollectionResponse, CollectionDetailResponse,
    CollectionAddContent, CollectionReorderContent,
    ReminderCreate, ReminderUpdate, ReminderResponse,
    LearningProgressResponse, CollectionProgressResponse, TopicProgressResponse,
    LearningProgressUpdate
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/learning", tags=["learning"])


# ============ 专题API ============

@router.post("/topics", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_data: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建专题"""
    service = LearningService(db)
    topic = await service.create_topic(topic_data, current_user.id)
    return topic


@router.get("/topics", response_model=List[TopicResponse])
async def list_topics(
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取专题列表"""
    service = LearningService(db)
    topics = await service.list_topics(skip, limit, is_active)
    return topics


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取专题详情"""
    service = LearningService(db)
    topic = await service.get_topic_with_contents(topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 构建响应
    response = TopicDetailResponse(
        id=topic.id,
        name=topic.name,
        description=topic.description,
        cover_url=topic.cover_url,
        creator_id=topic.creator_id,
        is_active=bool(topic.is_active),
        content_count=topic.content_count,
        view_count=topic.view_count,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        contents=[
            {
                "id": content.id,
                "title": content.title,
                "cover_url": content.cover_url,
                "duration": content.duration,
                "view_count": content.view_count
            }
            for content in topic.contents
        ]
    )
    return response


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: str,
    topic_data: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新专题"""
    service = LearningService(db)
    
    # 检查专题是否存在
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 检查权限（只有创建者可以更新）
    if topic.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新此专题"
        )
    
    updated_topic = await service.update_topic(topic_id, topic_data)
    return updated_topic


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除专题"""
    service = LearningService(db)
    
    # 检查专题是否存在
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 检查权限（只有创建者可以删除）
    if topic.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此专题"
        )
    
    await service.delete_topic(topic_id)


@router.post("/topics/{topic_id}/contents", status_code=status.HTTP_200_OK)
async def add_contents_to_topic(
    topic_id: str,
    content_data: TopicAddContent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """向专题添加内容"""
    service = LearningService(db)
    
    # 检查专题是否存在
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 检查权限
    if topic.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此专题"
        )
    
    success = await service.add_contents_to_topic(topic_id, content_data.content_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加内容失败"
        )
    
    return {"message": "内容添加成功"}


@router.delete("/topics/{topic_id}/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_content_from_topic(
    topic_id: str,
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从专题移除内容"""
    service = LearningService(db)
    
    # 检查专题是否存在
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 检查权限
    if topic.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此专题"
        )
    
    success = await service.remove_content_from_topic(topic_id, content_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不在此专题中"
        )


@router.put("/topics/{topic_id}/contents/reorder", status_code=status.HTTP_200_OK)
async def reorder_topic_contents(
    topic_id: str,
    reorder_data: TopicReorderContent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重新排序专题内容"""
    service = LearningService(db)
    
    # 检查专题是否存在
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    # 检查权限
    if topic.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此专题"
        )
    
    success = await service.reorder_topic_contents(topic_id, reorder_data.content_orders)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重新排序失败"
        )
    
    return {"message": "排序更新成功"}


# ============ 合集API ============

@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建合集"""
    service = LearningService(db)
    collection = await service.create_collection(collection_data, current_user.id)
    return collection


@router.get("/collections", response_model=List[CollectionResponse])
async def list_collections(
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取合集列表"""
    service = LearningService(db)
    collections = await service.list_collections(skip, limit, is_active)
    return collections


@router.get("/collections/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取合集详情"""
    service = LearningService(db)
    collection = await service.get_collection_with_contents(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 构建响应
    response = CollectionDetailResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        cover_url=collection.cover_url,
        creator_id=collection.creator_id,
        is_active=bool(collection.is_active),
        content_count=collection.content_count,
        view_count=collection.view_count,
        completion_count=collection.completion_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        contents=[
            {
                "id": content.id,
                "title": content.title,
                "cover_url": content.cover_url,
                "duration": content.duration,
                "view_count": content.view_count
            }
            for content in collection.contents
        ]
    )
    return response


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection_data: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新合集"""
    service = LearningService(db)
    
    # 检查合集是否存在
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 检查权限（只有创建者可以更新）
    if collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新此合集"
        )
    
    updated_collection = await service.update_collection(collection_id, collection_data)
    return updated_collection


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除合集"""
    service = LearningService(db)
    
    # 检查合集是否存在
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 检查权限（只有创建者可以删除）
    if collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此合集"
        )
    
    await service.delete_collection(collection_id)


@router.post("/collections/{collection_id}/contents", status_code=status.HTTP_200_OK)
async def add_contents_to_collection(
    collection_id: str,
    content_data: CollectionAddContent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """向合集添加内容"""
    service = LearningService(db)
    
    # 检查合集是否存在
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 检查权限
    if collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此合集"
        )
    
    success = await service.add_contents_to_collection(collection_id, content_data.content_orders)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加内容失败"
        )
    
    return {"message": "内容添加成功"}


@router.delete("/collections/{collection_id}/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_content_from_collection(
    collection_id: str,
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从合集移除内容"""
    service = LearningService(db)
    
    # 检查合集是否存在
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 检查权限
    if collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此合集"
        )
    
    success = await service.remove_content_from_collection(collection_id, content_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不在此合集中"
        )


@router.put("/collections/{collection_id}/contents/reorder", status_code=status.HTTP_200_OK)
async def reorder_collection_contents(
    collection_id: str,
    reorder_data: CollectionReorderContent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重新排序合集内容"""
    service = LearningService(db)
    
    # 检查合集是否存在
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    # 检查权限
    if collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此合集"
        )
    
    success = await service.reorder_collection_contents(collection_id, reorder_data.content_orders)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重新排序失败"
        )
    
    return {"message": "排序更新成功"}


@router.get("/collections/{collection_id}/next/{content_id}")
async def get_next_content(
    collection_id: str,
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取合集中的下一个内容"""
    service = LearningService(db)
    next_content_id = await service.get_next_content_in_collection(collection_id, content_id)
    
    if not next_content_id:
        return {"next_content_id": None, "message": "已是最后一个内容"}
    
    return {"next_content_id": next_content_id}


# ============ 学习计划API ============

@router.get("/plans/my")
async def get_my_learning_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的学习计划"""
    service = LearningService(db)
    plan = await service.get_learning_plan(current_user.id)
    
    # 格式化响应
    from app.schemas.learning_schemas import LearningPlanResponse
    
    response = LearningPlanResponse(
        user_id=plan["user_id"],
        recommended_topics=[
            TopicResponse.model_validate(topic) for topic in plan["recommended_topics"]
        ],
        recommended_collections=[
            CollectionResponse.model_validate(collection) for collection in plan["recommended_collections"]
        ],
        recommended_contents=[
            {
                "id": content.id,
                "title": content.title,
                "cover_url": content.cover_url,
                "duration": content.duration,
                "view_count": content.view_count,
                "content_type": content.content_type
            }
            for content in plan["recommended_contents"]
        ]
    )
    
    return response


@router.post("/plans/progress")
async def update_learning_progress(
    content_id: str,
    completed: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新学习进度"""
    service = LearningService(db)
    success = await service.update_plan_progress(current_user.id, content_id, completed)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新进度失败"
        )
    
    return {"message": "进度更新成功"}


# ============ 学习提醒API ============

@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建或更新学习提醒"""
    service = LearningService(db)
    reminder = await service.create_reminder(current_user.id, reminder_data)
    return reminder


@router.get("/reminders/my", response_model=ReminderResponse)
async def get_my_reminder(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的学习提醒设置"""
    service = LearningService(db)
    reminder = await service.get_reminder(current_user.id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未设置学习提醒"
        )
    
    return reminder


@router.put("/reminders/my", response_model=ReminderResponse)
async def update_my_reminder(
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新我的学习提醒"""
    service = LearningService(db)
    reminder = await service.update_reminder(current_user.id, reminder_data)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未设置学习提醒"
        )
    
    return reminder


@router.delete("/reminders/my", status_code=status.HTTP_204_NO_CONTENT)
async def disable_my_reminder(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """禁用我的学习提醒"""
    service = LearningService(db)
    success = await service.disable_reminder(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未设置学习提醒"
        )



# ============ 学习进度API ============

@router.get("/progress/my", response_model=LearningProgressResponse)
async def get_my_learning_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的学习进度统计"""
    service = LearningService(db)
    progress = await service.get_learning_progress(current_user.id)
    return LearningProgressResponse(**progress)


@router.get("/progress/collections/{collection_id}", response_model=CollectionProgressResponse)
async def get_collection_progress(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取合集学习进度"""
    service = LearningService(db)
    progress = await service.get_collection_progress(current_user.id, collection_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在"
        )
    
    return CollectionProgressResponse(**progress)


@router.get("/progress/topics/{topic_id}", response_model=TopicProgressResponse)
async def get_topic_progress(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取专题学习进度"""
    service = LearningService(db)
    progress = await service.get_topic_progress(current_user.id, topic_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="专题不存在"
        )
    
    return TopicProgressResponse(**progress)


@router.post("/progress/record")
async def record_learning_progress(
    content_id: str,
    progress_seconds: int,
    total_seconds: int,
    completed: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """记录学习进度"""
    service = LearningService(db)
    success = await service.record_progress(
        current_user.id,
        content_id,
        progress_seconds,
        total_seconds,
        completed
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="记录进度失败"
        )
    
    return {"message": "进度记录成功"}


@router.post("/progress/complete/{content_id}")
async def mark_content_completed(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记内容为已完成"""
    service = LearningService(db)
    success = await service.mark_content_completed(current_user.id, content_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在"
        )
    
    return {"message": "已标记为完成"}
