"""
管理后台标签和分类管理测试
"""
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.tag import Tag
from app.models.user import User
from app.models.content import Content, ContentStatus
from app.models.content_tag import ContentTag
from app.services.tag_service import TagService, CategoryService
from app.schemas.tag_schemas import TagCreate, TagUpdate, CategoryCreate, CategoryUpdate


class TestTagService:
    """标签服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_tag(self, db_session: Session):
        """测试创建标签"""
        tag_data = TagCreate(
            name="测试标签",
            category="主题标签",
            parent_id=None
        )
        
        tag = await TagService.create_tag(db_session, tag_data)
        
        assert tag.id is not None
        assert tag.name == "测试标签"
        assert tag.category == "主题标签"
        assert tag.parent_id is None
    
    @pytest.mark.asyncio
    async def test_create_tag_with_parent(self, db_session: Session):
        """测试创建带父标签的标签"""
        # 创建父标签
        parent_data = TagCreate(name="父标签", category="主题标签")
        parent = await TagService.create_tag(db_session, parent_data)
        
        # 创建子标签
        child_data = TagCreate(
            name="子标签",
            category="主题标签",
            parent_id=parent.id
        )
        child = await TagService.create_tag(db_session, child_data)
        
        assert child.parent_id == parent.id
    
    @pytest.mark.asyncio
    async def test_list_tags(self, db_session: Session):
        """测试获取标签列表"""
        # 创建多个标签
        for i in range(3):
            tag_data = TagCreate(name=f"标签{i}", category="主题标签")
            await TagService.create_tag(db_session, tag_data)
        
        # 获取列表
        tags, total = await TagService.list_tags(db_session, page=1, page_size=10)
        
        assert total >= 3
        assert len(tags) >= 3
    
    @pytest.mark.asyncio
    async def test_update_tag(self, db_session: Session):
        """测试更新标签"""
        # 创建标签
        tag_data = TagCreate(name="原标签", category="主题标签")
        tag = await TagService.create_tag(db_session, tag_data)
        
        # 更新标签
        update_data = TagUpdate(name="新标签")
        updated_tag = await TagService.update_tag(db_session, tag.id, update_data)
        
        assert updated_tag.name == "新标签"
        assert updated_tag.category == "主题标签"
    
    @pytest.mark.asyncio
    async def test_delete_tag(self, db_session: Session):
        """测试删除标签"""
        # 创建标签
        tag_data = TagCreate(name="待删除标签", category="主题标签")
        tag = await TagService.create_tag(db_session, tag_data)
        
        # 删除标签
        await TagService.delete_tag(db_session, tag.id)
        
        # 验证已删除
        deleted_tag = await TagService.get_tag(db_session, tag.id)
        assert deleted_tag is None
    
    @pytest.mark.asyncio
    async def test_get_tag_tree(self, db_session: Session):
        """测试获取标签树"""
        # 创建父标签
        parent_data = TagCreate(name="父标签", category="主题标签")
        parent = await TagService.create_tag(db_session, parent_data)
        
        # 创建子标签
        child_data = TagCreate(
            name="子标签",
            category="主题标签",
            parent_id=parent.id
        )
        await TagService.create_tag(db_session, child_data)
        
        # 获取标签树
        tree = await TagService.get_tag_tree(db_session, category="主题标签")
        
        assert len(tree) > 0
        # 找到父标签
        parent_node = next((node for node in tree if node.name == "父标签"), None)
        assert parent_node is not None
        assert len(parent_node.children) > 0


class TestCategoryService:
    """分类服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_category(self, db_session: Session):
        """测试创建分类"""
        category_data = CategoryCreate(name="测试分类", parent_id=None)
        
        category = await CategoryService.create_category(db_session, category_data)
        
        assert category.id is not None
        assert category.name == "测试分类"
        assert category.category == CategoryService.CATEGORY_TYPE
    
    @pytest.mark.asyncio
    async def test_create_category_with_parent(self, db_session: Session):
        """测试创建带父分类的分类"""
        # 创建父分类
        parent_data = CategoryCreate(name="父分类")
        parent = await CategoryService.create_category(db_session, parent_data)
        
        # 创建子分类
        child_data = CategoryCreate(name="子分类", parent_id=parent.id)
        child = await CategoryService.create_category(db_session, child_data)
        
        assert child.parent_id == parent.id
    
    @pytest.mark.asyncio
    async def test_list_categories(self, db_session: Session):
        """测试获取分类列表"""
        # 创建多个分类
        for i in range(3):
            category_data = CategoryCreate(name=f"分类{i}")
            await CategoryService.create_category(db_session, category_data)
        
        # 获取列表
        categories = await CategoryService.list_categories(db)
        
        assert len(categories) >= 3
    
    @pytest.mark.asyncio
    async def test_update_category(self, db_session: Session):
        """测试更新分类"""
        # 创建分类
        category_data = CategoryCreate(name="原分类")
        category = await CategoryService.create_category(db_session, category_data)
        
        # 更新分类
        update_data = CategoryUpdate(name="新分类")
        updated_category = await CategoryService.update_category(db_session, category.id, update_data)
        
        assert updated_category.name == "新分类"
    
    @pytest.mark.asyncio
    async def test_delete_category_with_children_fails(self, db_session: Session):
        """测试删除有子分类的分类应该失败"""
        # 创建父分类
        parent_data = CategoryCreate(name="父分类")
        parent = await CategoryService.create_category(db_session, parent_data)
        
        # 创建子分类
        child_data = CategoryCreate(name="子分类", parent_id=parent.id)
        await CategoryService.create_category(db_session, child_data)
        
        # 尝试删除父分类应该失败
        with pytest.raises(Exception):
            await CategoryService.delete_category(db_session, parent.id)
    
    @pytest.mark.asyncio
    async def test_get_category_tree(self, db_session: Session):
        """测试获取分类树"""
        # 创建父分类
        parent_data = CategoryCreate(name="父分类")
        parent = await CategoryService.create_category(db_session, parent_data)
        
        # 创建子分类
        child_data = CategoryCreate(name="子分类", parent_id=parent.id)
        await CategoryService.create_category(db_session, child_data)
        
        # 获取分类树
        tree = await CategoryService.get_category_tree(db)
        
        assert len(tree) > 0
        # 找到父分类
        parent_node = next((node for node in tree if node.name == "父分类"), None)
        assert parent_node is not None
        assert len(parent_node.children) > 0


class TestBatchTagAssign:
    """批量标签分配测试"""
    
    @pytest.mark.asyncio
    async def test_batch_assign_tags(self, db_session: Session):
        """测试批量分配标签"""
        # 创建测试用户
        user = User(
            id=str(uuid4()),
            employee_id="TEST001",
            name="测试用户",
            department="技术部",
            position="工程师"
        )
        db_session.add(user)
        
        # 创建测试内容
        content1 = Content(
            id=str(uuid4()),
            title="测试内容1",
            description="描述1",
            video_url="http://example.com/video1.mp4",
            creator_id=user.id,
            status=ContentStatus.PUBLISHED
        )
        content2 = Content(
            id=str(uuid4()),
            title="测试内容2",
            description="描述2",
            video_url="http://example.com/video2.mp4",
            creator_id=user.id,
            status=ContentStatus.PUBLISHED
        )
        db_session.add(content1)
        db_session.add(content2)
        
        # 创建测试标签
        tag1_data = TagCreate(name="标签1", category="主题标签")
        tag1 = await TagService.create_tag(db_session, tag1_data)
        
        tag2_data = TagCreate(name="标签2", category="主题标签")
        tag2 = await TagService.create_tag(db_session, tag2_data)
        
        db.commit()
        
        # 批量分配标签
        result = await TagService.batch_assign_tags(
            db,
            content_ids=[content1.id, content2.id],
            tag_ids=[tag1.id, tag2.id]
        )
        
        assert result['success_count'] == 4  # 2个内容 × 2个标签
        assert result['failed_count'] == 0
        
        # 验证关联已创建
        content1_tags = db.query(ContentTag).filter(ContentTag.content_id == content1.id).count()
        assert content1_tags == 2
        
        content2_tags = db.query(ContentTag).filter(ContentTag.content_id == content2.id).count()
        assert content2_tags == 2
