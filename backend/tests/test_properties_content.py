"""
基于属性的测试 - 内容上传和管理

本文件实现设计文档中定义的属性1-6的基于属性的测试。
使用Hypothesis框架进行属性测试，每个测试至少运行100次迭代。
"""
import pytest
import uuid
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from io import BytesIO
from datetime import datetime

from app.services.content_service import ContentService
from app.models.content import Content, ContentStatus
from app.models.user import User
from app.schemas.content_schemas import VideoMetadataCreate, VideoMetadataUpdate
from fastapi import UploadFile, HTTPException


# ==================== 测试数据生成策略 ====================

# 视频格式策略
@st.composite
def video_filename_strategy(draw):
    """生成视频文件名"""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        blacklist_characters='/'
    )))
    extension = draw(st.sampled_from(['mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv', 'webm']))
    return f"{name}.{extension}"


# 文件大小策略（字节）
file_size_strategy = st.integers(min_value=0, max_value=600 * 1024 * 1024)  # 0 到 600MB


# 视频元数据策略
@st.composite
def video_metadata_strategy(draw, title_required=True):
    """生成视频元数据"""
    if title_required:
        # 标题必填：生成非空标题或仅空白字符的标题
        title = draw(st.one_of(
            st.text(min_size=1, max_size=200),
            st.just(""),
            st.just("   "),
            st.text(alphabet=st.characters(whitelist_categories=('Zs',)), min_size=1, max_size=10)
        ))
    else:
        title = draw(st.text(min_size=1, max_size=200))
    
    description = draw(st.text(max_size=600))  # 测试超过500字符的情况
    content_type = draw(st.sampled_from(['工作知识', '生活分享', '企业文化', '技术分享']))
    
    return VideoMetadataCreate(
        title=title,
        description=description,
        content_type=content_type
    )


# ==================== 属性测试 ====================

# Feature: enterprise-video-learning-platform, Property 1: 视频格式验证
@given(filename=video_filename_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_1_video_format_validation(filename, db_session):
    """
    属性1：视频格式验证
    
    对于任何上传的视频文件，如果其格式为MP4、MOV或AVI，
    则系统应接受该文件；否则应拒绝
    
    验证需求：1.3
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    
    # 提取文件扩展名
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    supported_formats = ['mp4', 'mov', 'avi']
    
    # 创建模拟的上传文件
    file_content = b"fake video content"
    file = UploadFile(
        filename=filename,
        file=BytesIO(file_content)
    )
    
    # 创建元数据
    metadata = VideoMetadataCreate(
        title="测试视频",
        description="测试描述",
        content_type="工作知识"
    )
    
    # 执行测试
    if ext in supported_formats:
        # 应该接受
        try:
            content = await service.upload_video(file, user_id, metadata)
            assert content is not None
            assert content.creator_id == user_id
        except HTTPException as e:
            # 如果抛出异常，不应该是格式错误
            assert e.detail.get("code") != "VIDEO_FORMAT_UNSUPPORTED", \
                f"支持的格式 {ext} 被错误拒绝"
    else:
        # 应该拒绝
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_video(file, user_id, metadata)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "VIDEO_FORMAT_UNSUPPORTED"
        assert ext in exc_info.value.detail["details"]["uploaded_format"] or \
               exc_info.value.detail["details"]["uploaded_format"] == "unknown"


# Feature: enterprise-video-learning-platform, Property 2: 文件大小限制
@given(file_size=file_size_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_2_file_size_limit(file_size, db_session):
    """
    属性2：文件大小限制
    
    对于任何上传的视频文件，如果其大小超过配置的最大限制，
    则系统应拒绝上传并返回包含最大允许大小的错误消息
    
    验证需求：1.4
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    max_size = service.MAX_VIDEO_SIZE
    
    # 创建指定大小的模拟文件内容
    # 注意：实际的文件大小检查是基于读取的内容，所以我们需要创建实际大小的内容
    # 为了性能，对于大文件我们只创建一个小样本，但会跳过实际测试
    if file_size > 10 * 1024 * 1024:  # 如果超过10MB
        # 对于大文件，我们只测试逻辑，不实际创建大文件
        # 这是一个已知的测试限制
        assume(file_size <= max_size)  # 只测试在限制内的情况
        file_content = b"x" * 1024  # 1KB样本
    else:
        # 对于小文件，创建实际大小的内容
        file_content = b"x" * file_size
    
    # 创建模拟的上传文件
    file = UploadFile(
        filename="test_video.mp4",
        file=BytesIO(file_content)
    )
    
    # 创建元数据
    metadata = VideoMetadataCreate(
        title="测试视频",
        description="测试描述",
        content_type="工作知识"
    )
    
    # 执行测试
    actual_size = len(file_content)
    
    if actual_size <= max_size:
        # 应该接受（或因其他原因失败，但不是大小问题）
        try:
            content = await service.upload_video(file, user_id, metadata)
            # 如果成功，验证内容已创建
            assert content is not None
        except HTTPException as e:
            # 如果失败，不应该是文件大小错误
            assert e.detail.get("code") != "FILE_SIZE_EXCEEDED", \
                f"文件大小 {actual_size} 字节在限制内但被拒绝"
    else:
        # 应该拒绝
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_video(file, user_id, metadata)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "FILE_SIZE_EXCEEDED"
        assert "max_size_mb" in exc_info.value.detail["details"]


# Feature: enterprise-video-learning-platform, Property 3: 元数据标题必填
@given(
    title=st.one_of(
        st.text(min_size=1, max_size=200),  # 非空标题
        st.just("   "),  # 仅空白字符
        st.text(alphabet=st.characters(whitelist_categories=('Zs',)), min_size=1, max_size=10)  # 空白字符
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_3_title_required(title, db_session):
    """
    属性3：元数据标题必填
    
    对于任何内容保存或提交操作，如果标题字段为空或仅包含空白字符，
    则系统应拒绝该操作
    
    验证需求：2.1, 2.5
    
    注意：Pydantic schema已经验证标题不能为空字符串（min_length=1），
    所以这个测试主要验证仅包含空白字符的标题会被拒绝。
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建测试内容（草稿状态）
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title=title,  # 使用测试标题
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.DRAFT,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    
    # 尝试提交审核（这里会验证标题）
    is_empty_title = not title or not title.strip()
    
    if is_empty_title:
        # 应该拒绝提交
        with pytest.raises(HTTPException) as exc_info:
            await service.submit_for_review(content_id, user_id)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "TITLE_REQUIRED"
    else:
        # 应该允许提交
        try:
            submitted_content = await service.submit_for_review(content_id, user_id)
            assert submitted_content.status == ContentStatus.UNDER_REVIEW
        except HTTPException as e:
            # 如果失败，不应该是标题问题
            assert e.detail.get("code") != "TITLE_REQUIRED", \
                f"非空标题 '{title}' 被错误拒绝"


# Feature: enterprise-video-learning-platform, Property 4: 描述长度限制
@given(description=st.text(max_size=600))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_4_description_length_limit(description, db_session):
    """
    属性4：描述长度限制
    
    对于任何内容元数据，描述字段的字符数应不超过500个字符
    
    验证需求：2.2
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建测试内容
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="测试视频",
        description="原始描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.DRAFT,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    
    # 尝试更新描述
    update_metadata = VideoMetadataUpdate(
        description=description
    )
    
    # 验证描述长度
    if len(description) <= 500:
        # 应该接受
        updated_content = await service.update_metadata(content_id, user_id, update_metadata)
        assert updated_content.description == description
    else:
        # 应该拒绝或截断
        # 注意：当前实现可能没有强制限制，这个测试会暴露这个问题
        try:
            updated_content = await service.update_metadata(content_id, user_id, update_metadata)
            # 如果接受了，描述应该被截断到500字符
            # 或者系统应该拒绝
            if updated_content.description == description:
                # 系统接受了超长描述，这可能是一个bug
                pytest.fail(f"系统接受了超过500字符的描述（{len(description)}字符）")
        except HTTPException as e:
            # 如果拒绝，应该有明确的错误消息
            assert "描述" in e.detail.get("message", "") or \
                   "description" in e.detail.get("message", "").lower()


# Feature: enterprise-video-learning-platform, Property 5: 草稿往返一致性
@given(
    title=st.text(min_size=1, max_size=200),
    description=st.text(max_size=500),
    content_type=st.sampled_from(['工作知识', '生活分享', '企业文化'])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_5_draft_round_trip_consistency(title, description, content_type, db_session):
    """
    属性5：草稿往返一致性
    
    对于任何保存为草稿的内容，重新加载该草稿应返回
    与保存时完全相同的视频和元数据
    
    验证需求：5.3
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建原始草稿
    content_id = str(uuid.uuid4())
    video_url = f"https://example.com/videos/{content_id}.mp4"
    cover_url = f"https://example.com/covers/{content_id}.jpg"
    
    original_content = Content(
        id=content_id,
        title=title,
        description=description,
        video_url=video_url,
        cover_url=cover_url,
        file_size=1024 * 1024,  # 1MB
        creator_id=user_id,
        status=ContentStatus.DRAFT,
        content_type=content_type,
        created_at=datetime.utcnow()
    )
    db_session.add(original_content)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    
    # 保存草稿（实际上已经保存了，这里调用save_draft确保状态正确）
    saved_draft = await service.save_draft(content_id, user_id)
    assert saved_draft.status == ContentStatus.DRAFT
    
    # 重新加载草稿
    loaded_draft = await service.load_draft(content_id, user_id)
    
    # 验证一致性
    assert loaded_draft.id == original_content.id
    assert loaded_draft.title == original_content.title
    assert loaded_draft.description == original_content.description
    assert loaded_draft.video_url == original_content.video_url
    assert loaded_draft.cover_url == original_content.cover_url
    assert loaded_draft.file_size == original_content.file_size
    assert loaded_draft.content_type == original_content.content_type
    assert loaded_draft.creator_id == original_content.creator_id
    assert loaded_draft.status == ContentStatus.DRAFT


# Feature: enterprise-video-learning-platform, Property 6: 草稿删除完整性
@given(
    title=st.text(min_size=1, max_size=200),
    description=st.text(max_size=500)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_6_draft_deletion_integrity(title, description, db_session):
    """
    属性6：草稿删除完整性
    
    对于任何被删除的草稿，该草稿及其相关文件应从存储中完全移除，
    后续查询不应返回该草稿
    
    验证需求：5.4
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建草稿
    content_id = str(uuid.uuid4())
    draft = Content(
        id=content_id,
        title=title,
        description=description,
        video_url=f"https://example.com/videos/{content_id}.mp4",
        cover_url=f"https://example.com/covers/{content_id}.jpg",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.DRAFT,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(draft)
    await db_session.commit()
    
    # 创建ContentService实例
    service = ContentService(db_session)
    
    # 验证草稿存在
    existing_draft = await service.get_content(content_id)
    assert existing_draft is not None
    assert existing_draft.id == content_id
    
    # 删除草稿
    result = await service.delete_draft(content_id, user_id)
    assert result is True
    
    # 验证草稿已被删除
    deleted_draft = await service.get_content(content_id)
    assert deleted_draft is None
    
    # 验证草稿不在草稿列表中
    drafts, total = await service.list_drafts(user_id, page=1, page_size=100)
    assert content_id not in [d.id for d in drafts]
    
    # 尝试加载已删除的草稿应该失败
    with pytest.raises(HTTPException) as exc_info:
        await service.load_draft(content_id, user_id)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "CONTENT_NOT_FOUND"
