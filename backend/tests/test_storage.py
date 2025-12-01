"""
存储服务集成测试
测试本地存储、数据库连接和存储抽象层
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import io

from app.services.storage_local import LocalStorageService
from app.services.storage import StorageFactory, get_storage
from app.config import settings
from app.database import check_db_connection, get_db, AsyncSessionLocal
from sqlalchemy import text


class TestLocalStorageService:
    """本地存储服务测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def storage_service(self, temp_storage_path):
        """创建存储服务实例"""
        return LocalStorageService(base_path=temp_storage_path)
    
    @pytest.mark.asyncio
    async def test_upload_file(self, storage_service):
        """测试文件上传"""
        # 准备测试数据
        test_content = b"This is a test video file"
        filename = "test_video.mp4"
        
        # 上传文件
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos",
            user_id="test_user_123"
        )
        
        # 验证文件路径
        assert file_path is not None
        assert "videos" in file_path
        assert "test_user_123" in file_path
        
        # 验证文件存在
        exists = await storage_service.file_exists(file_path)
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_download_file(self, storage_service):
        """测试文件下载"""
        # 上传文件
        test_content = b"Test content for download"
        filename = "download_test.mp4"
        
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos"
        )
        
        # 下载文件
        downloaded_content = await storage_service.download_file(file_path)
        
        # 验证内容一致
        assert downloaded_content == test_content
    
    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service):
        """测试文件删除"""
        # 上传文件
        test_content = b"File to be deleted"
        filename = "delete_test.mp4"
        
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos"
        )
        
        # 验证文件存在
        exists_before = await storage_service.file_exists(file_path)
        assert exists_before is True
        
        # 删除文件
        deleted = await storage_service.delete_file(file_path)
        assert deleted is True
        
        # 验证文件不存在
        exists_after = await storage_service.file_exists(file_path)
        assert exists_after is False
    
    @pytest.mark.asyncio
    async def test_get_file_size(self, storage_service):
        """测试获取文件大小"""
        # 上传文件
        test_content = b"Test content with known size"
        filename = "size_test.mp4"
        
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos"
        )
        
        # 获取文件大小
        file_size = await storage_service.get_file_size(file_path)
        
        # 验证大小
        assert file_size == len(test_content)
    
    @pytest.mark.asyncio
    async def test_get_file_url(self, storage_service):
        """测试获取文件URL"""
        # 上传文件
        test_content = b"Test content"
        filename = "url_test.mp4"
        
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos"
        )
        
        # 获取URL
        url = await storage_service.get_file_url(file_path)
        
        # 验证URL格式
        assert url is not None
        assert "/files/" in url
        assert file_path in url
    
    @pytest.mark.asyncio
    async def test_storage_stats(self, storage_service):
        """测试存储统计"""
        # 上传多个文件
        for i in range(3):
            test_content = f"Test video {i}".encode()
            await storage_service.upload_file(
                file=test_content,
                filename=f"video_{i}.mp4",
                file_type="videos"
            )
        
        for i in range(2):
            test_content = f"Test cover {i}".encode()
            await storage_service.upload_file(
                file=test_content,
                filename=f"cover_{i}.jpg",
                file_type="covers"
            )
        
        # 获取统计信息
        stats = await storage_service.get_storage_stats()
        
        # 验证统计
        assert stats["videos"]["count"] == 3
        assert stats["covers"]["count"] == 2
        assert stats["file_count"] == 5
        assert stats["total_size"] > 0


class TestStorageFactory:
    """存储工厂测试"""
    
    def test_get_storage_local(self, monkeypatch):
        """测试获取本地存储"""
        # 重置工厂
        StorageFactory.reset()
        
        # 设置配置为本地存储
        monkeypatch.setattr(settings, "STORAGE_TYPE", "local")
        
        # 获取存储服务
        storage = StorageFactory.get_storage()
        
        # 验证类型
        assert isinstance(storage, LocalStorageService)
    
    def test_get_storage_singleton(self, monkeypatch):
        """测试单例模式"""
        # 重置工厂
        StorageFactory.reset()
        
        # 设置配置
        monkeypatch.setattr(settings, "STORAGE_TYPE", "local")
        
        # 多次获取
        storage1 = StorageFactory.get_storage()
        storage2 = StorageFactory.get_storage()
        
        # 验证是同一个实例
        assert storage1 is storage2
    
    def test_get_storage_convenience_function(self, monkeypatch):
        """测试便捷函数"""
        # 重置工厂
        StorageFactory.reset()
        
        # 设置配置
        monkeypatch.setattr(settings, "STORAGE_TYPE", "local")
        
        # 使用便捷函数
        storage = get_storage()
        
        # 验证类型
        assert isinstance(storage, LocalStorageService)


class TestDatabaseConnection:
    """数据库连接集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not asyncio.run(check_db_connection()),
        reason="数据库未运行，跳过数据库连接测试。请使用 docker-compose up -d 启动数据库"
    )
    async def test_database_connection(self):
        """测试数据库连接是否正常"""
        # 检查数据库连接
        is_connected = await check_db_connection()
        
        # 验证连接成功
        assert is_connected is True, "数据库连接失败"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not asyncio.run(check_db_connection()),
        reason="数据库未运行，跳过数据库会话测试。请使用 docker-compose up -d 启动数据库"
    )
    async def test_database_session_creation(self):
        """测试数据库会话创建"""
        # 创建数据库会话
        async with AsyncSessionLocal() as session:
            # 执行简单查询
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            # 验证查询结果
            assert row is not None
            assert row[0] == 1
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not asyncio.run(check_db_connection()),
        reason="数据库未运行，跳过数据库事务测试。请使用 docker-compose up -d 启动数据库"
    )
    async def test_database_transaction_commit(self):
        """测试数据库事务提交"""
        async with AsyncSessionLocal() as session:
            # 开始事务
            async with session.begin():
                # 执行查询
                result = await session.execute(text("SELECT 1"))
                assert result is not None
            
            # 事务应该自动提交
            # 验证会话仍然有效
            result = await session.execute(text("SELECT 2"))
            row = result.fetchone()
            assert row[0] == 2
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not asyncio.run(check_db_connection()),
        reason="数据库未运行，跳过数据库回滚测试。请使用 docker-compose up -d 启动数据库"
    )
    async def test_database_transaction_rollback(self):
        """测试数据库事务回滚"""
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    # 执行查询
                    await session.execute(text("SELECT 1"))
                    
                    # 模拟错误
                    raise Exception("测试回滚")
            except Exception:
                # 异常应该触发回滚
                pass
            
            # 验证会话仍然可用
            result = await session.execute(text("SELECT 1"))
            assert result is not None


class TestStorageIntegration:
    """存储服务集成测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def storage_service(self, temp_storage_path):
        """创建存储服务实例"""
        return LocalStorageService(base_path=temp_storage_path)
    
    @pytest.mark.asyncio
    async def test_upload_download_integration(self, storage_service):
        """集成测试：上传和下载文件"""
        # 准备测试数据
        test_content = b"Integration test video content"
        filename = "integration_test.mp4"
        
        # 上传文件
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos",
            user_id="integration_user"
        )
        
        # 验证文件路径
        assert file_path is not None
        assert "videos" in file_path
        
        # 下载文件
        downloaded_content = await storage_service.download_file(file_path)
        
        # 验证内容一致
        assert downloaded_content == test_content
        
        # 清理
        await storage_service.delete_file(file_path)
    
    @pytest.mark.asyncio
    async def test_multiple_file_types_integration(self, storage_service):
        """集成测试：多种文件类型上传"""
        test_files = [
            (b"Video content", "test.mp4", "videos"),
            (b"Cover image", "cover.jpg", "covers"),
            (b"Avatar image", "avatar.png", "avatars"),
        ]
        
        uploaded_paths = []
        
        # 上传不同类型的文件
        for content, filename, file_type in test_files:
            file_path = await storage_service.upload_file(
                file=content,
                filename=filename,
                file_type=file_type
            )
            uploaded_paths.append(file_path)
            
            # 验证文件类型在路径中
            assert file_type in file_path
            
            # 验证文件存在
            exists = await storage_service.file_exists(file_path)
            assert exists is True
        
        # 获取存储统计
        stats = await storage_service.get_storage_stats()
        
        # 验证统计信息
        assert stats["videos"]["count"] >= 1
        assert stats["covers"]["count"] >= 1
        assert stats["avatars"]["count"] >= 1
        
        # 清理所有文件
        for file_path in uploaded_paths:
            await storage_service.delete_file(file_path)
    
    @pytest.mark.asyncio
    async def test_file_lifecycle_integration(self, storage_service):
        """集成测试：文件完整生命周期"""
        # 1. 上传文件
        test_content = b"Lifecycle test content"
        filename = "lifecycle.mp4"
        
        file_path = await storage_service.upload_file(
            file=test_content,
            filename=filename,
            file_type="videos"
        )
        
        # 2. 验证文件存在
        exists = await storage_service.file_exists(file_path)
        assert exists is True
        
        # 3. 获取文件大小
        file_size = await storage_service.get_file_size(file_path)
        assert file_size == len(test_content)
        
        # 4. 获取文件URL
        file_url = await storage_service.get_file_url(file_path)
        assert file_url is not None
        assert file_path in file_url
        
        # 5. 下载文件
        downloaded = await storage_service.download_file(file_path)
        assert downloaded == test_content
        
        # 6. 删除文件
        deleted = await storage_service.delete_file(file_path)
        assert deleted is True
        
        # 7. 验证文件不存在
        exists_after = await storage_service.file_exists(file_path)
        assert exists_after is False
    
    @pytest.mark.asyncio
    async def test_storage_abstraction_layer(self, monkeypatch, temp_storage_path):
        """集成测试：存储抽象层"""
        # 重置工厂
        StorageFactory.reset()
        
        # 设置配置
        monkeypatch.setattr(settings, "STORAGE_TYPE", "local")
        monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", temp_storage_path)
        
        # 通过抽象层获取存储服务
        storage = get_storage()
        
        # 验证类型
        assert isinstance(storage, LocalStorageService)
        
        # 测试上传
        test_content = b"Abstraction layer test"
        file_path = await storage.upload_file(
            file=test_content,
            filename="abstraction.mp4",
            file_type="videos"
        )
        
        # 验证文件存在
        exists = await storage.file_exists(file_path)
        assert exists is True
        
        # 清理
        await storage.delete_file(file_path)
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, storage_service):
        """集成测试：并发上传"""
        # 准备多个文件
        files = [
            (f"Content {i}".encode(), f"concurrent_{i}.mp4")
            for i in range(5)
        ]
        
        # 并发上传
        upload_tasks = [
            storage_service.upload_file(
                file=content,
                filename=filename,
                file_type="videos"
            )
            for content, filename in files
        ]
        
        file_paths = await asyncio.gather(*upload_tasks)
        
        # 验证所有文件都上传成功
        assert len(file_paths) == 5
        for file_path in file_paths:
            assert file_path is not None
            exists = await storage_service.file_exists(file_path)
            assert exists is True
        
        # 清理
        for file_path in file_paths:
            await storage_service.delete_file(file_path)
    
    @pytest.mark.asyncio
    async def test_storage_with_io_objects(self, storage_service):
        """集成测试：使用IO对象上传"""
        # 创建BytesIO对象
        test_content = b"IO object test content"
        file_obj = io.BytesIO(test_content)
        
        # 上传
        file_path = await storage_service.upload_file(
            file=file_obj,
            filename="io_test.mp4",
            file_type="videos"
        )
        
        # 验证
        exists = await storage_service.file_exists(file_path)
        assert exists is True
        
        # 下载并验证内容
        downloaded = await storage_service.download_file(file_path)
        assert downloaded == test_content
        
        # 清理
        await storage_service.delete_file(file_path)


class TestStorageAndDatabaseIntegration:
    """存储服务与数据库集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not asyncio.run(check_db_connection()),
        reason="数据库未运行，跳过存储和数据库集成测试。请使用 docker-compose up -d 启动数据库"
    )
    async def test_storage_and_database_together(self, monkeypatch):
        """集成测试：存储服务和数据库同时工作"""
        # 创建临时存储
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 重置工厂
            StorageFactory.reset()
            
            # 配置存储
            monkeypatch.setattr(settings, "STORAGE_TYPE", "local")
            monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", temp_dir)
            
            # 1. 检查数据库连接
            db_connected = await check_db_connection()
            assert db_connected is True, "数据库连接失败"
            
            # 2. 获取存储服务
            storage = get_storage()
            assert storage is not None
            
            # 3. 上传文件
            test_content = b"Combined test content"
            file_path = await storage.upload_file(
                file=test_content,
                filename="combined.mp4",
                file_type="videos",
                user_id="test_user"
            )
            
            # 4. 验证文件存在
            exists = await storage.file_exists(file_path)
            assert exists is True
            
            # 5. 模拟在数据库中记录文件信息
            async with AsyncSessionLocal() as session:
                # 执行查询验证数据库可用
                result = await session.execute(text("SELECT 1"))
                assert result is not None
            
            # 6. 清理文件
            await storage.delete_file(file_path)
            
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
