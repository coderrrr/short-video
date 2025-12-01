-- 企业短视频学习平台 - 数据库初始化脚本
-- 此脚本在MySQL容器首次启动时自动执行

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS short_video 
  DEFAULT CHARACTER SET utf8mb4 
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE short_video;

-- 授予用户权限
GRANT ALL PRIVILEGES ON short_video.* TO 'short_video_user'@'%';
FLUSH PRIVILEGES;

-- 设置时区
SET time_zone = '+08:00';

-- 记录初始化完成
SELECT '数据库初始化完成' AS status;
