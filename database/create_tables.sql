-- ==========================================
-- 企业短视频学习平台 - 数据库初始化脚本
-- ==========================================
-- 用途：手动创建所有表结构和初始数据
-- 使用方法：
--   mysql -u用户名 -p密码 数据库名 < create_tables.sql
-- 或在MySQL客户端中：
--   source /path/to/create_tables.sql
-- ==========================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ==========================================
-- 1. 用户表
-- ==========================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `employee_id` VARCHAR(50) NOT NULL COMMENT '员工ID',
  `name` VARCHAR(100) NOT NULL COMMENT '姓名',
  `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
  `department` VARCHAR(100) DEFAULT NULL COMMENT '部门',
  `position` VARCHAR(100) DEFAULT NULL COMMENT '岗位',
  `is_kol` TINYINT(1) DEFAULT 0 COMMENT '是否为KOL',
  `is_admin` TINYINT(1) DEFAULT 0 COMMENT '是否为管理员',
  `password_hash` VARCHAR(255) DEFAULT NULL COMMENT '密码哈希',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已删除',
  `deleted_at` DATETIME DEFAULT NULL COMMENT '删除时间',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`),
  KEY `idx_user_employee_id` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ==========================================
-- 2. 内容表
-- ==========================================
DROP TABLE IF EXISTS `contents`;
CREATE TABLE `contents` (
  `id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `title` VARCHAR(200) NOT NULL COMMENT '标题',
  `description` TEXT COMMENT '描述',
  `video_url` VARCHAR(500) NOT NULL COMMENT '视频URL',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '封面URL',
  `duration` INT DEFAULT NULL COMMENT '时长（秒）',
  `file_size` BIGINT DEFAULT NULL COMMENT '文件大小（字节）',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创作者ID',
  `status` ENUM('draft', 'under_review', 'approved', 'rejected', 'published', 'removed') NOT NULL DEFAULT 'draft' COMMENT '状态',
  `content_type` VARCHAR(50) DEFAULT NULL COMMENT '内容类型',
  `view_count` INT DEFAULT 0 COMMENT '观看次数',
  `like_count` INT DEFAULT 0 COMMENT '点赞数',
  `favorite_count` INT DEFAULT 0 COMMENT '收藏数',
  `comment_count` INT DEFAULT 0 COMMENT '评论数',
  `share_count` INT DEFAULT 0 COMMENT '分享数',
  `is_featured` INT NOT NULL DEFAULT 0 COMMENT '是否精选（0=否，1=是）',
  `featured_priority` INT NOT NULL DEFAULT 0 COMMENT '精选优先级（1-100，数字越大优先级越高）',
  `featured_position` VARCHAR(50) DEFAULT NULL COMMENT '精选位置（homepage, category_top等）',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT NULL COMMENT '更新时间',
  `published_at` DATETIME DEFAULT NULL COMMENT '发布时间',
  PRIMARY KEY (`id`),
  KEY `idx_content_creator` (`creator_id`),
  KEY `idx_content_status` (`status`),
  KEY `idx_content_published` (`published_at`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_content_featured` (`is_featured`, `featured_priority` DESC),
  CONSTRAINT `fk_content_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容表';

-- ==========================================
-- 3. 标签表
-- ==========================================
DROP TABLE IF EXISTS `tags`;
CREATE TABLE `tags` (
  `id` VARCHAR(36) NOT NULL COMMENT '标签ID',
  `name` VARCHAR(50) NOT NULL COMMENT '标签名称',
  `category` VARCHAR(50) DEFAULT NULL COMMENT '标签分类',
  `parent_id` VARCHAR(36) DEFAULT NULL COMMENT '父标签ID',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `fk_tag_parent` (`parent_id`),
  CONSTRAINT `fk_tag_parent` FOREIGN KEY (`parent_id`) REFERENCES `tags` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- ==========================================
-- 4. 内容标签关联表
-- ==========================================
DROP TABLE IF EXISTS `content_tags`;
CREATE TABLE `content_tags` (
  `id` VARCHAR(36) NOT NULL COMMENT '关联ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `tag_id` VARCHAR(36) NOT NULL COMMENT '标签ID',
  `confidence` FLOAT DEFAULT NULL COMMENT 'AI匹配的置信度',
  `is_auto` TINYINT(1) DEFAULT 1 COMMENT '是否AI自动匹配',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_content_tag_content` (`content_id`),
  KEY `idx_content_tag_tag` (`tag_id`),
  CONSTRAINT `fk_content_tag_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`),
  CONSTRAINT `fk_content_tag_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容标签关联表';

-- ==========================================
-- 5. AI分析结果表
-- ==========================================
DROP TABLE IF EXISTS `ai_analyses`;
CREATE TABLE `ai_analyses` (
  `id` VARCHAR(36) NOT NULL COMMENT '分析ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `key_frames` JSON DEFAULT NULL COMMENT '关键帧URL列表',
  `transcript` TEXT COMMENT '语音转文字',
  `ocr_text` TEXT COMMENT 'OCR提取的文字',
  `scene_description` TEXT COMMENT '场景描述',
  `suggested_tags` JSON DEFAULT NULL COMMENT '建议标签列表',
  `moderation_result` JSON DEFAULT NULL COMMENT '审核结果',
  `has_nsfw` TINYINT(1) DEFAULT 0 COMMENT '是否涉黄',
  `has_violence` TINYINT(1) DEFAULT 0 COMMENT '是否涉爆',
  `has_sensitive` TINYINT(1) DEFAULT 0 COMMENT '是否有敏感内容',
  `sensitive_words` JSON DEFAULT NULL COMMENT '检测到的敏感词列表',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_id` (`content_id`),
  CONSTRAINT `fk_ai_analysis_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI分析结果表';

-- ==========================================
-- 6. 互动记录表
-- ==========================================
DROP TABLE IF EXISTS `interactions`;
CREATE TABLE `interactions` (
  `id` VARCHAR(36) NOT NULL COMMENT '互动ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `type` ENUM('LIKE', 'FAVORITE', 'BOOKMARK', 'COMMENT', 'SHARE') NOT NULL COMMENT '互动类型',
  `note` TEXT COMMENT '标记笔记',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_interaction_user` (`user_id`),
  KEY `idx_interaction_content` (`content_id`),
  KEY `idx_interaction_type` (`type`),
  KEY `idx_user_content_type` (`user_id`, `content_id`, `type`),
  CONSTRAINT `fk_interaction_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_interaction_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='互动记录表';

-- ==========================================
-- 7. 评论表
-- ==========================================
DROP TABLE IF EXISTS `comments`;
CREATE TABLE `comments` (
  `id` VARCHAR(36) NOT NULL COMMENT '评论ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `parent_id` VARCHAR(36) DEFAULT NULL COMMENT '父评论ID',
  `text` TEXT NOT NULL COMMENT '评论文本',
  `mentioned_users` JSON DEFAULT NULL COMMENT '提及的用户ID列表',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_comment_content` (`content_id`),
  KEY `idx_comment_user` (`user_id`),
  KEY `idx_comment_created` (`created_at`),
  KEY `fk_comment_parent` (`parent_id`),
  CONSTRAINT `fk_comment_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`),
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `comments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- ==========================================
-- 8. 审核记录表
-- ==========================================
DROP TABLE IF EXISTS `review_records`;
CREATE TABLE `review_records` (
  `id` VARCHAR(36) NOT NULL COMMENT '审核记录ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `reviewer_id` VARCHAR(36) NOT NULL COMMENT '审核员ID',
  `review_type` VARCHAR(20) DEFAULT NULL COMMENT '审核类型',
  `status` VARCHAR(20) DEFAULT NULL COMMENT '审核状态',
  `reason` TEXT COMMENT '拒绝原因',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `fk_review_content` (`content_id`),
  KEY `fk_review_reviewer` (`reviewer_id`),
  CONSTRAINT `fk_review_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`),
  CONSTRAINT `fk_review_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审核记录表';

-- ==========================================
-- 9. 关注关系表
-- ==========================================
DROP TABLE IF EXISTS `follows`;
CREATE TABLE `follows` (
  `id` VARCHAR(36) NOT NULL COMMENT '关注ID',
  `follower_id` VARCHAR(36) NOT NULL COMMENT '关注者ID',
  `followee_id` VARCHAR(36) NOT NULL COMMENT '被关注者ID',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_follow_unique` (`follower_id`, `followee_id`),
  KEY `idx_follow_follower` (`follower_id`),
  KEY `idx_follow_followee` (`followee_id`),
  CONSTRAINT `fk_follow_follower` FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_follow_followee` FOREIGN KEY (`followee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注关系表';

-- ==========================================
-- 10. 用户偏好表
-- ==========================================
DROP TABLE IF EXISTS `user_preferences`;
CREATE TABLE `user_preferences` (
  `id` VARCHAR(36) NOT NULL COMMENT '偏好ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `role_tag_weights` JSON DEFAULT NULL COMMENT '角色标签权重',
  `topic_tag_weights` JSON DEFAULT NULL COMMENT '主题标签权重',
  `content_type_weights` JSON DEFAULT NULL COMMENT '内容类型权重',
  `creator_weights` JSON DEFAULT NULL COMMENT '创作者权重',
  `total_watch_count` FLOAT DEFAULT 0.0 COMMENT '总观看次数',
  `total_watch_duration` FLOAT DEFAULT 0.0 COMMENT '总观看时长（秒）',
  `total_like_count` FLOAT DEFAULT 0.0 COMMENT '总点赞次数',
  `total_favorite_count` FLOAT DEFAULT 0.0 COMMENT '总收藏次数',
  `total_comment_count` FLOAT DEFAULT 0.0 COMMENT '总评论次数',
  `total_share_count` FLOAT DEFAULT 0.0 COMMENT '总分享次数',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `idx_user_preference_user` (`user_id`),
  CONSTRAINT `fk_user_preference_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好表';

-- ==========================================
-- 11. 推荐缓存表
-- ==========================================
DROP TABLE IF EXISTS `recommendation_caches`;
CREATE TABLE `recommendation_caches` (
  `id` VARCHAR(36) NOT NULL COMMENT '缓存ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `content_ids` JSON NOT NULL COMMENT '推荐内容ID列表',
  `page` INT DEFAULT 1 COMMENT '页码',
  `page_size` INT DEFAULT 20 COMMENT '每页数量',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_recommendation_cache_user` (`user_id`),
  KEY `idx_recommendation_cache_expires` (`expires_at`),
  CONSTRAINT `fk_recommendation_cache_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推荐缓存表';

-- ==========================================
-- 12. 分享表
-- ==========================================
DROP TABLE IF EXISTS `shares`;
CREATE TABLE `shares` (
  `id` VARCHAR(36) NOT NULL COMMENT '分享记录ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '分享用户ID',
  `platform` VARCHAR(50) NOT NULL COMMENT '分享平台（wechat/link）',
  `created_at` DATETIME NOT NULL COMMENT '分享时间',
  PRIMARY KEY (`id`),
  KEY `idx_share_content` (`content_id`),
  KEY `idx_share_user` (`user_id`),
  KEY `idx_share_created` (`created_at`),
  CONSTRAINT `fk_share_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`),
  CONSTRAINT `fk_share_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分享表';

-- ==========================================
-- 13. 播放进度表
-- ==========================================
DROP TABLE IF EXISTS `playback_progress`;
CREATE TABLE `playback_progress` (
  `id` VARCHAR(36) NOT NULL COMMENT '进度ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `progress_seconds` FLOAT NOT NULL DEFAULT 0.0 COMMENT '播放进度（秒）',
  `duration_seconds` FLOAT NOT NULL COMMENT '视频总时长（秒）',
  `progress_percentage` FLOAT NOT NULL DEFAULT 0.0 COMMENT '播放进度百分比',
  `playback_speed` FLOAT NOT NULL DEFAULT 1.0 COMMENT '播放速度',
  `is_completed` INT NOT NULL DEFAULT 0 COMMENT '是否完成（0=未完成，1=已完成）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `last_played_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后播放时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_playback_user_content` (`user_id`, `content_id`),
  KEY `idx_playback_user` (`user_id`),
  KEY `idx_playback_content` (`content_id`),
  KEY `idx_playback_last_played` (`last_played_at`),
  CONSTRAINT `fk_playback_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_playback_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='播放进度表';

-- ==========================================
-- 14. 视频质量偏好表
-- ==========================================
DROP TABLE IF EXISTS `video_quality_preferences`;
CREATE TABLE `video_quality_preferences` (
  `id` VARCHAR(36) NOT NULL COMMENT '偏好ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `quality` VARCHAR(20) NOT NULL DEFAULT 'auto' COMMENT '视频质量：auto, hd, sd',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_video_quality_user` (`user_id`),
  CONSTRAINT `fk_video_quality_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频质量偏好表';

-- ==========================================
-- 15. 下载记录表
-- ==========================================
DROP TABLE IF EXISTS `downloads`;
CREATE TABLE `downloads` (
  `id` VARCHAR(36) NOT NULL COMMENT '下载ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `file_size` FLOAT NOT NULL COMMENT '文件大小（字节）',
  `download_progress` FLOAT NOT NULL DEFAULT 0.0 COMMENT '下载进度（0-100）',
  `download_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '下载状态：pending, downloading, completed, failed',
  `local_path` VARCHAR(500) DEFAULT NULL COMMENT '本地存储路径',
  `quality` VARCHAR(20) NOT NULL DEFAULT 'hd' COMMENT '下载质量：hd, sd',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `completed_at` DATETIME DEFAULT NULL COMMENT '完成时间',
  PRIMARY KEY (`id`),
  KEY `idx_download_user` (`user_id`),
  KEY `idx_download_content` (`content_id`),
  KEY `idx_download_user_content` (`user_id`, `content_id`),
  KEY `idx_download_status` (`download_status`),
  KEY `idx_download_created` (`created_at`),
  CONSTRAINT `fk_download_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_download_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='下载记录表';

-- ==========================================
-- 16. 举报表
-- ==========================================
DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `id` VARCHAR(36) NOT NULL COMMENT '举报ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `reporter_id` VARCHAR(36) NOT NULL COMMENT '举报者ID',
  `reason` ENUM('inappropriate_content', 'spam', 'harassment', 'false_information', 'copyright_violation', 'violence', 'hate_speech', 'other') NOT NULL COMMENT '举报原因',
  `description` TEXT COMMENT '举报描述',
  `status` ENUM('pending', 'reviewing', 'resolved', 'rejected') NOT NULL DEFAULT 'pending' COMMENT '处理状态',
  `handler_id` VARCHAR(36) DEFAULT NULL COMMENT '处理人ID',
  `handler_note` TEXT COMMENT '处理备注',
  `handled_at` DATETIME DEFAULT NULL COMMENT '处理时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_report_content` (`content_id`),
  KEY `idx_report_reporter` (`reporter_id`),
  KEY `idx_report_status` (`status`),
  KEY `idx_report_created` (`created_at`),
  KEY `fk_report_handler` (`handler_id`),
  CONSTRAINT `fk_report_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`),
  CONSTRAINT `fk_report_reporter` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_report_handler` FOREIGN KEY (`handler_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='举报表';

-- ==========================================
-- 17. 专题表
-- ==========================================
DROP TABLE IF EXISTS `topics`;
CREATE TABLE `topics` (
  `id` VARCHAR(36) NOT NULL COMMENT '专题ID',
  `name` VARCHAR(200) NOT NULL COMMENT '专题名称',
  `description` TEXT COMMENT '专题描述',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '专题封面图片URL',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创建者ID',
  `is_active` INT DEFAULT 1 COMMENT '是否激活：1-激活，0-停用',
  `content_count` INT DEFAULT 0 COMMENT '内容数量',
  `view_count` INT DEFAULT 0 COMMENT '浏览次数',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_topic_creator` (`creator_id`),
  KEY `idx_topic_active` (`is_active`),
  CONSTRAINT `fk_topic_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专题表';

-- ==========================================
-- 18. 专题内容关联表
-- ==========================================
DROP TABLE IF EXISTS `topic_contents`;
CREATE TABLE `topic_contents` (
  `topic_id` VARCHAR(36) NOT NULL COMMENT '专题ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `order` INT DEFAULT 0 COMMENT '排序',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`topic_id`, `content_id`),
  KEY `fk_topic_content_content` (`content_id`),
  CONSTRAINT `fk_topic_content_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_topic_content_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专题内容关联表';

-- ==========================================
-- 19. 合集表
-- ==========================================
DROP TABLE IF EXISTS `collections`;
CREATE TABLE `collections` (
  `id` VARCHAR(36) NOT NULL COMMENT '合集ID',
  `name` VARCHAR(200) NOT NULL COMMENT '合集名称',
  `description` TEXT COMMENT '合集描述',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '合集封面图片URL',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创建者ID',
  `is_active` INT DEFAULT 1 COMMENT '是否激活：1-激活，0-停用',
  `content_count` INT DEFAULT 0 COMMENT '内容数量',
  `view_count` INT DEFAULT 0 COMMENT '浏览次数',
  `completion_count` INT DEFAULT 0 COMMENT '完成次数',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_collection_creator` (`creator_id`),
  KEY `idx_collection_active` (`is_active`),
  CONSTRAINT `fk_collection_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合集表';

-- ==========================================
-- 20. 合集内容关联表
-- ==========================================
DROP TABLE IF EXISTS `collection_contents`;
CREATE TABLE `collection_contents` (
  `collection_id` VARCHAR(36) NOT NULL COMMENT '合集ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `order` INT NOT NULL COMMENT '内容在合集中的顺序',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`collection_id`, `content_id`),
  KEY `fk_collection_content_content` (`content_id`),
  CONSTRAINT `fk_collection_content_collection` FOREIGN KEY (`collection_id`) REFERENCES `collections` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_collection_content_content` FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合集内容关联表';

-- ==========================================
-- 21. 学习提醒表
-- ==========================================
DROP TABLE IF EXISTS `learning_reminders`;
CREATE TABLE `learning_reminders` (
  `id` VARCHAR(36) NOT NULL COMMENT '提醒ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `enabled` TINYINT(1) DEFAULT 1 COMMENT '是否启用提醒',
  `frequency` VARCHAR(20) NOT NULL COMMENT '提醒频率：daily, weekly, custom',
  `time_of_day` VARCHAR(5) DEFAULT NULL COMMENT '提醒时间（HH:MM格式）',
  `days_of_week` VARCHAR(50) DEFAULT NULL COMMENT '每周提醒日期（逗号分隔）',
  `next_reminder_at` DATETIME DEFAULT NULL COMMENT '下次提醒时间',
  `created_at` DATETIME NOT NULL COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_reminder_user` (`user_id`),
  KEY `idx_reminder_enabled` (`enabled`),
  KEY `idx_reminder_next` (`next_reminder_at`),
  CONSTRAINT `fk_reminder_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习提醒表';

-- ==========================================
-- 22. 学习分析表
-- ==========================================
DROP TABLE IF EXISTS `learning_analytics`;
CREATE TABLE `learning_analytics` (
  `id` VARCHAR(36) NOT NULL COMMENT '分析ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `total_videos_watched` INT DEFAULT 0 COMMENT '总观看视频数',
  `total_watch_time` INT DEFAULT 0 COMMENT '总观看时长（秒）',
  `learning_streak_days` INT DEFAULT 0 COMMENT '连续学习天数',
  `last_learning_date` DATE DEFAULT NULL COMMENT '最后学习日期',
  `category_stats` VARCHAR(1000) DEFAULT NULL COMMENT '分类统计',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_learning_analytics_user` (`user_id`),
  CONSTRAINT `fk_learning_analytics_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习分析表';

-- ==========================================
-- 23. 每日学习记录表
-- ==========================================
DROP TABLE IF EXISTS `daily_learning_records`;
CREATE TABLE `daily_learning_records` (
  `id` VARCHAR(36) NOT NULL COMMENT '记录ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `learning_date` DATE NOT NULL COMMENT '学习日期',
  `videos_watched` INT DEFAULT 0 COMMENT '观看视频数',
  `watch_time` INT DEFAULT 0 COMMENT '观看时长（秒）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_daily_learning_user_date` (`user_id`, `learning_date`),
  CONSTRAINT `fk_daily_learning_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日学习记录表';

-- ==========================================
-- 24. 排行榜条目表
-- ==========================================
DROP TABLE IF EXISTS `leaderboard_entries`;
CREATE TABLE `leaderboard_entries` (
  `id` VARCHAR(36) NOT NULL COMMENT '条目ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `rank` INT DEFAULT NULL COMMENT '排名',
  `score` INT DEFAULT 0 COMMENT '得分',
  `videos_watched` INT DEFAULT 0 COMMENT '观看视频数',
  `watch_time` INT DEFAULT 0 COMMENT '观看时长（秒）',
  `videos_created` INT DEFAULT 0 COMMENT '创建视频数',
  `period_date` DATE NOT NULL COMMENT '统计周期日期',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_leaderboard_date_rank` (`period_date`, `rank`),
  KEY `idx_leaderboard_user_date` (`user_id`, `period_date`),
  CONSTRAINT `fk_leaderboard_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排行榜条目表';

-- ==========================================
-- 25. 成就定义表
-- ==========================================
DROP TABLE IF EXISTS `achievements`;
CREATE TABLE `achievements` (
  `id` VARCHAR(36) NOT NULL COMMENT '成就ID',
  `name` VARCHAR(100) NOT NULL COMMENT '成就名称',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '成就描述',
  `icon_url` VARCHAR(500) DEFAULT NULL COMMENT '成就图标URL',
  `achievement_type` ENUM('learning_milestone', 'contribution_milestone', 'streak_milestone', 'social_milestone') NOT NULL COMMENT '成就类型',
  `requirement_value` INT NOT NULL COMMENT '达成要求值',
  `requirement_description` VARCHAR(200) DEFAULT NULL COMMENT '达成要求描述',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成就定义表';

-- ==========================================
-- 26. 用户成就表
-- ==========================================
DROP TABLE IF EXISTS `user_achievements`;
CREATE TABLE `user_achievements` (
  `id` VARCHAR(36) NOT NULL COMMENT '用户成就ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `achievement_id` VARCHAR(36) NOT NULL COMMENT '成就ID',
  `unlocked_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '解锁时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_achievement_user` (`user_id`),
  KEY `idx_user_achievement_achievement` (`achievement_id`),
  CONSTRAINT `fk_user_achievement_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_user_achievement_achievement` FOREIGN KEY (`achievement_id`) REFERENCES `achievements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户成就表';

-- ==========================================
-- 27. 通知表
-- ==========================================
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id` VARCHAR(36) NOT NULL COMMENT '通知ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '接收通知的用户ID',
  `type` ENUM('review_status', 'interaction', 'mention', 'follow', 'learning_reminder', 'system') NOT NULL COMMENT '通知类型',
  `title` VARCHAR(200) NOT NULL COMMENT '通知标题',
  `content` TEXT NOT NULL COMMENT '通知内容',
  `related_content_id` VARCHAR(36) DEFAULT NULL COMMENT '关联的内容ID',
  `related_user_id` VARCHAR(36) DEFAULT NULL COMMENT '关联的用户ID',
  `related_comment_id` VARCHAR(36) DEFAULT NULL COMMENT '关联的评论ID',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已读',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `read_at` DATETIME DEFAULT NULL COMMENT '阅读时间',
  PRIMARY KEY (`id`),
  KEY `idx_notifications_user_id` (`user_id`),
  KEY `idx_notifications_is_read` (`is_read`),
  KEY `idx_notifications_created_at` (`created_at`),
  CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- ==========================================
-- 28. 通知设置表
-- ==========================================
DROP TABLE IF EXISTS `notification_settings`;
CREATE TABLE `notification_settings` (
  `id` VARCHAR(36) NOT NULL COMMENT '设置ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `enable_review_notifications` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用审核通知',
  `enable_interaction_notifications` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用互动通知',
  `enable_mention_notifications` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用@提及通知',
  `enable_follow_notifications` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用关注通知',
  `enable_learning_reminders` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用学习提醒',
  `enable_system_notifications` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '启用系统通知',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `idx_notification_settings_user_id` (`user_id`),
  CONSTRAINT `fk_notification_settings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知设置表';



-- ==========================================
-- 初始数据插入
-- ==========================================

-- 插入默认管理员用户
INSERT INTO `users` (`id`, `employee_id`, `name`, `avatar_url`, `department`, `position`, `is_kol`, `is_admin`, `password_hash`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`)
VALUES 
  (UUID(), 'ADMIN001', '系统管理员', NULL, '技术部', '系统管理员', 0, 1, '$2b$12$SAIhy87vn3Vzj9t1RrV3uevAyMm0USAoh07ybIJnPJX4BqiA5DXsy', 0, NULL, NOW(), NOW());
-- 默认密码: admin123

-- 插入示例标签
INSERT INTO `tags` (`id`, `name`, `category`, `parent_id`, `created_at`)
VALUES 
  (UUID(), '技术培训', '主题', NULL, NOW()),
  (UUID(), '产品知识', '主题', NULL, NOW()),
  (UUID(), '企业文化', '主题', NULL, NOW()),
  (UUID(), '安全培训', '主题', NULL, NOW()),
  (UUID(), '新员工入职', '主题', NULL, NOW());

-- 插入示例成就
INSERT INTO `achievements` (`id`, `name`, `description`, `icon_url`, `achievement_type`, `requirement_value`, `requirement_description`, `created_at`)
VALUES 
  (UUID(), '初学者', '完成第一个视频学习', NULL, 'learning_milestone', 1, '观看完成1个视频', NOW()),
  (UUID(), '学习达人', '累计学习10个视频', NULL, 'learning_milestone', 10, '观看完成10个视频', NOW()),
  (UUID(), '学习狂人', '累计学习50个视频', NULL, 'learning_milestone', 50, '观看完成50个视频', NOW()),
  (UUID(), '坚持不懈', '连续学习7天', NULL, 'streak_milestone', 7, '连续7天学习', NOW()),
  (UUID(), '创作新星', '发布第一个视频', NULL, 'contribution_milestone', 1, '发布1个视频', NOW()),
  (UUID(), '人气创作者', '视频获得100个点赞', NULL, 'social_milestone', 100, '累计获得100个点赞', NOW());

-- ==========================================
-- 恢复外键检查
-- ==========================================
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 完成提示
-- ==========================================
SELECT '数据库初始化完成！' AS message;
SELECT CONCAT('共创建 ', COUNT(*), ' 张表') AS table_count 
FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE';
