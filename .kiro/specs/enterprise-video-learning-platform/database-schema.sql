-- 企业内部短视频平台 - 数据库表结构定义
-- 数据库: MySQL 8.0
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci

-- ============================================
-- 用户相关表
-- ============================================

-- 用户表
CREATE TABLE `users` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '用户ID (UUID)',
  `employee_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '员工工号',
  `name` VARCHAR(100) NOT NULL COMMENT '姓名',
  `avatar_url` VARCHAR(500) COMMENT '头像URL',
  `department` VARCHAR(100) COMMENT '部门',
  `position` VARCHAR(100) COMMENT '岗位',
  `is_kol` BOOLEAN DEFAULT FALSE COMMENT '是否为KOL',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_employee_id` (`employee_id`),
  INDEX `idx_is_kol` (`is_kol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 关注关系表
CREATE TABLE `follows` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关注关系ID',
  `follower_id` VARCHAR(36) NOT NULL COMMENT '关注者ID',
  `followee_id` VARCHAR(36) NOT NULL COMMENT '被关注者ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
  FOREIGN KEY (`follower_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`followee_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_follower_followee` (`follower_id`, `followee_id`),
  INDEX `idx_follower` (`follower_id`),
  INDEX `idx_followee` (`followee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注关系表';

-- ============================================
-- 内容相关表
-- ============================================

-- 内容表
CREATE TABLE `contents` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '内容ID',
  `title` VARCHAR(200) NOT NULL COMMENT '标题',
  `description` TEXT COMMENT '描述',
  `video_url` VARCHAR(500) NOT NULL COMMENT '视频URL (S3)',
  `cover_url` VARCHAR(500) COMMENT '封面URL',
  `duration` INT COMMENT '时长(秒)',
  `file_size` BIGINT COMMENT '文件大小(字节)',
  `original_file_size` BIGINT COMMENT '原始文件大小(字节，压缩前)',
  `is_compressed` BOOLEAN DEFAULT FALSE COMMENT '是否已压缩',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创作者ID',
  `status` ENUM('draft', 'under_review', 'approved', 'rejected', 'published', 'removed') NOT NULL DEFAULT 'draft' COMMENT '状态',
  `content_type` VARCHAR(50) COMMENT '内容类型(工作知识/生活分享/企业文化)',
  `view_count` INT DEFAULT 0 COMMENT '观看次数',
  `like_count` INT DEFAULT 0 COMMENT '点赞数',
  `favorite_count` INT DEFAULT 0 COMMENT '收藏数',
  `comment_count` INT DEFAULT 0 COMMENT '评论数',
  `share_count` INT DEFAULT 0 COMMENT '分享数',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `published_at` DATETIME COMMENT '发布时间',
  FOREIGN KEY (`creator_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_creator` (`creator_id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_published` (`published_at` DESC),
  INDEX `idx_content_type` (`content_type`),
  INDEX `idx_view_count` (`view_count` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容表';

-- AI分析结果表
CREATE TABLE `ai_analyses` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT 'AI分析ID',
  `content_id` VARCHAR(36) NOT NULL UNIQUE COMMENT '内容ID',
  `key_frames` JSON COMMENT '关键帧URL列表',
  `transcript` TEXT COMMENT '语音转文字',
  `ocr_text` TEXT COMMENT 'OCR提取的文字',
  `scene_description` TEXT COMMENT '场景描述',
  `suggested_tags` JSON COMMENT '建议标签 [{"tag_id": "xxx", "confidence": 0.95}]',
  `moderation_result` JSON COMMENT '审核结果 {"is_safe": true, "flags": [], "confidence": 0.99}',
  `has_nsfw` BOOLEAN DEFAULT FALSE COMMENT '是否涉黄',
  `has_violence` BOOLEAN DEFAULT FALSE COMMENT '是否涉爆',
  `has_sensitive` BOOLEAN DEFAULT FALSE COMMENT '是否敏感',
  `sensitive_words` JSON COMMENT '检测到的敏感词列表',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  INDEX `idx_content` (`content_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI分析结果表';

-- ============================================
-- 标签相关表
-- ============================================

-- 标签表
CREATE TABLE `tags` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '标签ID',
  `name` VARCHAR(50) NOT NULL COMMENT '标签名称',
  `category` VARCHAR(50) COMMENT '标签类别(角色/主题/形式/质量/推荐)',
  `parent_id` VARCHAR(36) COMMENT '父标签ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`parent_id`) REFERENCES `tags`(`id`) ON DELETE SET NULL,
  INDEX `idx_category` (`category`),
  INDEX `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- 内容标签关联表
CREATE TABLE `content_tags` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `tag_id` VARCHAR(36) NOT NULL COMMENT '标签ID',
  `confidence` FLOAT COMMENT 'AI匹配置信度',
  `is_auto` BOOLEAN DEFAULT TRUE COMMENT '是否AI自动匹配',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`tag_id`) REFERENCES `tags`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_content_tag` (`content_id`, `tag_id`),
  INDEX `idx_content` (`content_id`),
  INDEX `idx_tag` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容标签关联表';

-- ============================================
-- 互动相关表
-- ============================================

-- 互动记录表
CREATE TABLE `interactions` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '互动ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `type` ENUM('like', 'favorite', 'bookmark', 'share', 'view') NOT NULL COMMENT '互动类型',
  `note` TEXT COMMENT '标记笔记(仅bookmark类型)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_user_content_type` (`user_id`, `content_id`, `type`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_content` (`content_id`),
  INDEX `idx_type` (`type`),
  INDEX `idx_user_type` (`user_id`, `type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='互动记录表';

-- 评论表
CREATE TABLE `comments` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '评论ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `text` TEXT NOT NULL COMMENT '评论内容',
  `parent_id` VARCHAR(36) COMMENT '父评论ID(回复)',
  `mentioned_users` JSON COMMENT '@提及的用户ID列表',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`parent_id`) REFERENCES `comments`(`id`) ON DELETE CASCADE,
  INDEX `idx_content` (`content_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_parent` (`parent_id`),
  INDEX `idx_created` (`created_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- ============================================
-- 审核相关表
-- ============================================

-- 审核记录表
CREATE TABLE `review_records` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '审核记录ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `reviewer_id` VARCHAR(36) COMMENT '审核员ID',
  `review_type` VARCHAR(20) NOT NULL COMMENT '审核类型(platform_review/expert_review/ai_review)',
  `status` VARCHAR(20) NOT NULL COMMENT '审核状态(approved/rejected/pending)',
  `reason` TEXT COMMENT '拒绝原因',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '审核时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`reviewer_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_content` (`content_id`),
  INDEX `idx_reviewer` (`reviewer_id`),
  INDEX `idx_type` (`review_type`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审核记录表';

-- ============================================
-- 分类和集合相关表
-- ============================================

-- 分类表
CREATE TABLE `categories` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '分类ID',
  `name` VARCHAR(100) NOT NULL COMMENT '分类名称',
  `parent_id` VARCHAR(36) COMMENT '父分类ID',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`parent_id`) REFERENCES `categories`(`id`) ON DELETE SET NULL,
  INDEX `idx_parent` (`parent_id`),
  INDEX `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类表';

-- 内容分类关联表
CREATE TABLE `content_categories` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `category_id` VARCHAR(36) NOT NULL COMMENT '分类ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_content_category` (`content_id`, `category_id`),
  INDEX `idx_content` (`content_id`),
  INDEX `idx_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容分类关联表';

-- 专题表
CREATE TABLE `topics` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '专题ID',
  `name` VARCHAR(100) NOT NULL COMMENT '专题名称',
  `description` TEXT COMMENT '专题描述',
  `cover_url` VARCHAR(500) COMMENT '封面URL',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创建者ID',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`creator_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_creator` (`creator_id`),
  INDEX `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专题表';

-- 专题内容关联表
CREATE TABLE `topic_contents` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `topic_id` VARCHAR(36) NOT NULL COMMENT '专题ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`topic_id`) REFERENCES `topics`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_topic_content` (`topic_id`, `content_id`),
  INDEX `idx_topic` (`topic_id`),
  INDEX `idx_content` (`content_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专题内容关联表';

-- 合集表
CREATE TABLE `series` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '合集ID',
  `name` VARCHAR(100) NOT NULL COMMENT '合集名称',
  `description` TEXT COMMENT '合集描述',
  `cover_url` VARCHAR(500) COMMENT '封面URL',
  `creator_id` VARCHAR(36) NOT NULL COMMENT '创建者ID',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`creator_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_creator` (`creator_id`),
  INDEX `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合集表';

-- 合集内容关联表
CREATE TABLE `series_contents` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `series_id` VARCHAR(36) NOT NULL COMMENT '合集ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `sort_order` INT NOT NULL COMMENT '排序(顺序)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`series_id`) REFERENCES `series`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_series_content` (`series_id`, `content_id`),
  INDEX `idx_series` (`series_id`),
  INDEX `idx_content` (`content_id`),
  INDEX `idx_series_order` (`series_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合集内容关联表';

-- ============================================
-- 学习相关表
-- ============================================

-- 学习计划表
CREATE TABLE `learning_plans` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '学习计划ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '计划名称',
  `description` TEXT COMMENT '计划描述',
  `status` ENUM('active', 'completed', 'paused') DEFAULT 'active' COMMENT '状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `completed_at` DATETIME COMMENT '完成时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习计划表';

-- 学习计划内容关联表
CREATE TABLE `learning_plan_contents` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `plan_id` VARCHAR(36) NOT NULL COMMENT '学习计划ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '内容ID',
  `sort_order` INT NOT NULL COMMENT '排序',
  `is_completed` BOOLEAN DEFAULT FALSE COMMENT '是否完成',
  `completed_at` DATETIME COMMENT '完成时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`plan_id`) REFERENCES `learning_plans`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_plan_content` (`plan_id`, `content_id`),
  INDEX `idx_plan` (`plan_id`),
  INDEX `idx_content` (`content_id`),
  INDEX `idx_plan_order` (`plan_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习计划内容关联表';

-- ============================================
-- 通知相关表
-- ============================================

-- 通知表
CREATE TABLE `notifications` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '通知ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '接收用户ID',
  `type` VARCHAR(50) NOT NULL COMMENT '通知类型(review/interaction/mention/reminder)',
  `title` VARCHAR(200) NOT NULL COMMENT '通知标题',
  `content` TEXT COMMENT '通知内容',
  `related_id` VARCHAR(36) COMMENT '关联对象ID',
  `is_read` BOOLEAN DEFAULT FALSE COMMENT '是否已读',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_type` (`type`),
  INDEX `idx_read` (`is_read`),
  INDEX `idx_user_read` (`user_id`, `is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- ============================================
-- 举报相关表
-- ============================================

-- 举报表
CREATE TABLE `reports` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '举报ID',
  `content_id` VARCHAR(36) NOT NULL COMMENT '被举报内容ID',
  `reporter_id` VARCHAR(36) NOT NULL COMMENT '举报人ID',
  `reason` VARCHAR(100) NOT NULL COMMENT '举报原因',
  `description` TEXT COMMENT '详细描述',
  `status` ENUM('pending', 'processing', 'resolved', 'rejected') DEFAULT 'pending' COMMENT '处理状态',
  `handler_id` VARCHAR(36) COMMENT '处理人ID',
  `handle_result` TEXT COMMENT '处理结果',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '举报时间',
  `handled_at` DATETIME COMMENT '处理时间',
  FOREIGN KEY (`content_id`) REFERENCES `contents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`reporter_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`handler_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_content` (`content_id`),
  INDEX `idx_reporter` (`reporter_id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_handler` (`handler_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='举报表';

-- ============================================
-- 配置相关表
-- ============================================

-- 系统配置表
CREATE TABLE `system_configs` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '配置ID',
  `key` VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
  `value` TEXT NOT NULL COMMENT '配置值',
  `description` VARCHAR(500) COMMENT '配置说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 用户偏好表
CREATE TABLE `user_preferences` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '偏好ID',
  `user_id` VARCHAR(36) NOT NULL UNIQUE COMMENT '用户ID',
  `notification_enabled` BOOLEAN DEFAULT TRUE COMMENT '是否启用通知',
  `learning_reminder_enabled` BOOLEAN DEFAULT TRUE COMMENT '是否启用学习提醒',
  `interaction_notification_enabled` BOOLEAN DEFAULT TRUE COMMENT '是否启用互动通知',
  `video_quality` ENUM('auto', 'high', 'standard') DEFAULT 'auto' COMMENT '视频质量偏好',
  `preference_profile` JSON COMMENT '用户偏好配置文件(推荐算法用)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好表';


-- ============================================
-- 初始配置数据
-- ============================================

-- 插入默认系统配置
INSERT INTO `system_configs` (`id`, `key`, `value`, `description`) VALUES
(UUID(), 'video.max_size_mb', '500', '视频最大文件大小(MB)'),
(UUID(), 'video.compression_threshold_mb', '50', '视频压缩阈值(MB)，超过此大小自动压缩'),
(UUID(), 'video.compression_quality', '0.8', '视频压缩质量(0-1)'),
(UUID(), 'video.supported_formats', '["mp4", "mov", "avi"]', '支持的视频格式'),
(UUID(), 'image.max_size_mb', '10', '图片最大文件大小(MB)'),
(UUID(), 'image.supported_formats', '["jpg", "jpeg", "png"]', '支持的图片格式');
