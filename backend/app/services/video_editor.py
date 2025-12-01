"""
视频编辑服务 - 使用FFmpeg进行视频处理
"""
import os
import subprocess
import tempfile
import uuid
from typing import Optional
from io import BytesIO
import logging

from app.services.storage import get_storage

logger = logging.getLogger(__name__)


class VideoEditor:
    """视频编辑器类"""
    
    def __init__(self):
        self.storage = get_storage()
    
    def _extract_file_path(self, url: str) -> str:
        """
        从URL中提取文件路径
        
        Args:
            url: 文件URL
            
        Returns:
            str: 文件路径
        """
        # 简单处理：假设URL的最后部分是文件路径
        # 实际应用中可能需要更复杂的逻辑
        if url.startswith('http'):
            # 对于HTTP URL，提取路径部分
            parts = url.split('/')
            # 找到videos、covers等目录后的路径
            for i, part in enumerate(parts):
                if part in ['videos', 'covers', 'avatars', 'temp']:
                    return '/'.join(parts[i:])
            return parts[-1]
        else:
            # 对于本地路径，直接返回
            return url
    
    async def trim_video(
        self,
        input_url: str,
        start_time: float,
        end_time: float,
        output_key: str
    ) -> str:
        """
        裁剪视频
        
        Args:
            input_url: 输入视频URL
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_key: 输出文件的存储键
            
        Returns:
            str: 裁剪后视频的URL
            
        Raises:
            Exception: 裁剪失败
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_path = input_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # 下载输入视频
            file_path = self._extract_file_path(input_url)
            video_data = await self.storage.download_file(file_path)
            with open(input_path, 'wb') as f:
                f.write(video_data)
            
            # 计算时长
            duration = end_time - start_time
            
            # 使用FFmpeg裁剪视频
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # 使用copy避免重新编码，速度更快
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg裁剪失败: {result.stderr}")
                raise Exception(f"视频裁剪失败: {result.stderr}")
            
            # 读取输出文件并上传
            with open(output_path, 'rb') as f:
                output_file = BytesIO(f.read())
            
            # 从output_key提取文件名
            filename = output_key.split('/')[-1]
            output_url = await self.storage.upload_file(
                output_file,
                filename,
                file_type="videos"
            )
            
            logger.info(f"视频裁剪成功: {output_key}")
            return output_url
            
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def adjust_volume(
        self,
        input_url: str,
        volume: float,
        output_key: str
    ) -> str:
        """
        调节视频音量
        
        Args:
            input_url: 输入视频URL
            volume: 音量倍数（0-2）
            output_key: 输出文件的存储键
            
        Returns:
            str: 处理后视频的URL
            
        Raises:
            Exception: 处理失败
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_path = input_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # 下载输入视频
            file_path = self._extract_file_path(input_url)
            video_data = await self.storage.download_file(file_path)
            with open(input_path, 'wb') as f:
                f.write(video_data)
            
            # 使用FFmpeg调节音量
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', f'volume={volume}',
                '-c:v', 'copy',  # 视频流不重新编码
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg音量调节失败: {result.stderr}")
                raise Exception(f"音量调节失败: {result.stderr}")
            
            # 读取输出文件并上传
            with open(output_path, 'rb') as f:
                output_file = BytesIO(f.read())
            
            # 从output_key提取文件名
            filename = output_key.split('/')[-1]
            output_url = await self.storage.upload_file(
                output_file,
                filename,
                file_type="videos"
            )
            
            logger.info(f"音量调节成功: {output_key}")
            return output_url
            
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def extract_frame(
        self,
        input_url: str,
        timestamp: float,
        output_key: str
    ) -> str:
        """
        提取视频帧
        
        Args:
            input_url: 输入视频URL
            timestamp: 时间戳（秒）
            output_key: 输出图片的存储键
            
        Returns:
            str: 提取的帧图片URL
            
        Raises:
            Exception: 提取失败
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_path = input_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # 下载输入视频
            file_path = self._extract_file_path(input_url)
            video_data = await self.storage.download_file(file_path)
            with open(input_path, 'wb') as f:
                f.write(video_data)
            
            # 使用FFmpeg提取帧
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-q:v', '2',  # 高质量
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg帧提取失败: {result.stderr}")
                raise Exception(f"帧提取失败: {result.stderr}")
            
            # 读取输出文件并上传
            with open(output_path, 'rb') as f:
                output_file = BytesIO(f.read())
            
            # 从output_key提取文件名
            filename = output_key.split('/')[-1]
            output_url = await self.storage.upload_file(
                output_file,
                filename,
                file_type="covers"
            )
            
            logger.info(f"帧提取成功: {output_key}")
            return output_url
            
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def get_video_info(self, input_url: str) -> dict:
        """
        获取视频信息
        
        Args:
            input_url: 输入视频URL
            
        Returns:
            dict: 视频信息（时长、分辨率等）
            
        Raises:
            Exception: 获取失败
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_path = input_file.name
        
        try:
            # 下载输入视频
            file_path = self._extract_file_path(input_url)
            video_data = await self.storage.download_file(file_path)
            with open(input_path, 'wb') as f:
                f.write(video_data)
            
            # 使用FFprobe获取视频信息
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration:stream=width,height',
                '-of', 'default=noprint_wrappers=1',
                input_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"FFprobe获取信息失败: {result.stderr}")
                raise Exception(f"获取视频信息失败: {result.stderr}")
            
            # 解析输出
            info = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value
            
            return {
                'duration': float(info.get('duration', 0)),
                'width': int(info.get('width', 0)),
                'height': int(info.get('height', 0))
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.unlink(input_path)
