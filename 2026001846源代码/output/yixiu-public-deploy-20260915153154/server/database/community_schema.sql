-- 附近社区板块数据库表结构

USE health_diet_db;

-- 社区表
CREATE TABLE IF NOT EXISTS communities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '社区名称',
    description TEXT COMMENT '社区简介',
    avatar VARCHAR(255) COMMENT '社区头像',
    cover_image VARCHAR(255) COMMENT '社区封面图',
    category VARCHAR(50) DEFAULT 'general' COMMENT '社区分类',
    creator_id INT NOT NULL COMMENT '创建者ID',
    latitude DECIMAL(10,8) COMMENT '社区纬度',
    longitude DECIMAL(10,8) COMMENT '社区经度',
    address VARCHAR(255) COMMENT '社区地址',
    max_members INT DEFAULT 500 COMMENT '最大成员数',
    current_members INT DEFAULT 0 COMMENT '当前成员数',
    post_count INT DEFAULT 0 COMMENT '帖子总数',
    activity_score DECIMAL(5,2) DEFAULT 0 COMMENT '活跃度分数',
    is_public TINYINT(1) DEFAULT 1 COMMENT '是否公开',
    join_type ENUM('open', 'approval', 'invite') DEFAULT 'open' COMMENT '加入方式',
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active' COMMENT '社区状态',
    tags JSON COMMENT '社区标签',
    rules TEXT COMMENT '社区规则',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_location (latitude, longitude),
    INDEX idx_status (status),
    INDEX idx_join_type (join_type),
    INDEX idx_activity_score (activity_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区信息表';

-- 社区成员表
CREATE TABLE IF NOT EXISTS community_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    community_id INT NOT NULL COMMENT '社区ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role ENUM('owner', 'admin', 'moderator', 'member') DEFAULT 'member' COMMENT '成员角色',
    status ENUM('active', 'banned', 'left') DEFAULT 'active' COMMENT '成员状态',
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活跃时间',
    post_count INT DEFAULT 0 COMMENT '发帖数',
    comment_count INT DEFAULT 0 COMMENT '评论数',
    reputation_score INT DEFAULT 0 COMMENT '声誉分数',
    notification_enabled TINYINT(1) DEFAULT 1 COMMENT '是否接收通知',
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_community_user (community_id, user_id),
    INDEX idx_role (role),
    INDEX idx_status (status),
    INDEX idx_last_active (last_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区成员表';

-- 社区帖子表
CREATE TABLE IF NOT EXISTS community_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    community_id INT NOT NULL COMMENT '社区ID',
    user_id INT NOT NULL COMMENT '发帖用户ID',
    title VARCHAR(200) COMMENT '帖子标题',
    content TEXT NOT NULL COMMENT '帖子内容',
    images JSON COMMENT '图片列表',
    category VARCHAR(50) DEFAULT 'general' COMMENT '帖子分类',
    tags JSON COMMENT '帖子标签',
    is_pinned TINYINT(1) DEFAULT 0 COMMENT '是否置顶',
    is_locked TINYINT(1) DEFAULT 0 COMMENT '是否锁定',
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    comment_count INT DEFAULT 0 COMMENT '评论数',
    share_count INT DEFAULT 0 COMMENT '分享数',
    status ENUM('published', 'draft', 'deleted', 'hidden') DEFAULT 'published' COMMENT '帖子状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_community_id (community_id),
    INDEX idx_user_id (user_id),
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_is_pinned (is_pinned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区帖子表';

-- 帖子点赞表
CREATE TABLE IF NOT EXISTS community_post_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL COMMENT '帖子ID',
    user_id INT NOT NULL COMMENT '点赞用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_post_user (post_id, user_id),
    INDEX idx_post_id (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子点赞表';

-- 帖子评论表
CREATE TABLE IF NOT EXISTS community_post_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL COMMENT '帖子ID',
    user_id INT NOT NULL COMMENT '评论用户ID',
    parent_id INT DEFAULT NULL COMMENT '父评论ID(用于回复)',
    content TEXT NOT NULL COMMENT '评论内容',
    images JSON COMMENT '评论图片',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    reply_count INT DEFAULT 0 COMMENT '回复数',
    status ENUM('published', 'deleted', 'hidden') DEFAULT 'published' COMMENT '评论状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES community_post_comments(id) ON DELETE CASCADE,
    INDEX idx_post_id (post_id),
    INDEX idx_user_id (user_id),
    INDEX idx_parent_id (parent_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子评论表';

-- 评论点赞表
CREATE TABLE IF NOT EXISTS community_comment_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment_id INT NOT NULL COMMENT '评论ID',
    user_id INT NOT NULL COMMENT '点赞用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_id) REFERENCES community_post_comments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_comment_user (comment_id, user_id),
    INDEX idx_comment_id (comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论点赞表';

-- 社区加入申请表
CREATE TABLE IF NOT EXISTS community_join_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    community_id INT NOT NULL COMMENT '社区ID',
    user_id INT NOT NULL COMMENT '申请用户ID',
    message TEXT COMMENT '申请留言',
    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending' COMMENT '申请状态',
    reviewer_id INT COMMENT '审核人ID',
    review_message TEXT COMMENT '审核留言',
    reviewed_at TIMESTAMP NULL COMMENT '审核时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uk_community_user_pending (community_id, user_id, status),
    INDEX idx_community_id (community_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区加入申请表';

-- 社区通知表
CREATE TABLE IF NOT EXISTS community_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    community_id INT NOT NULL COMMENT '社区ID',
    user_id INT NOT NULL COMMENT '接收通知的用户ID',
    type ENUM('join_request', 'join_approved', 'join_rejected', 'new_post', 'new_comment', 'mention', 'system') NOT NULL COMMENT '通知类型',
    title VARCHAR(200) NOT NULL COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    related_id INT COMMENT '相关ID(帖子ID/评论ID等)',
    is_read TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_community_id (community_id),
    INDEX idx_type (type),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区通知表';

-- 社区活动记录表(用于计算活跃度)
CREATE TABLE IF NOT EXISTS community_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    community_id INT NOT NULL COMMENT '社区ID',
    user_id INT NOT NULL COMMENT '用户ID',
    activity_type ENUM('post', 'comment', 'like', 'share', 'join', 'leave') NOT NULL COMMENT '活动类型',
    related_id INT COMMENT '相关ID',
    activity_date DATE NOT NULL COMMENT '活动日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_community_date (community_id, activity_date),
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区活动记录表';

-- 用户位置表(用于计算距离)
CREATE TABLE IF NOT EXISTS user_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    latitude DECIMAL(10,8) NOT NULL COMMENT '纬度',
    longitude DECIMAL(10,8) NOT NULL COMMENT '经度',
    address VARCHAR(255) COMMENT '地址',
    accuracy DECIMAL(10,2) COMMENT '位置精度(米)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_location (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户位置表';

-- 插入示例社区数据
INSERT INTO communities (name, description, category, creator_id, latitude, longitude, address, max_members, current_members, activity_score, join_type, tags) VALUES
('健康饮食爱好者', '分享健康饮食心得,交流营养搭配技巧', 'health', 1, 39.9042, 116.4074, '北京市朝阳区', 500, 128, 85.5, 'open', '["健康", "饮食", "营养"]'),
('低碳生活社区', '记录低碳行动,分享环保生活经验', 'environment', 1, 39.9142, 116.4174, '北京市海淀区', 300, 89, 72.3, 'approval', '["低碳", "环保", "生活"]'),
('烹饪技巧交流', '学习烹饪技巧,分享美食制作心得', 'cooking', 1, 39.9242, 116.4274, '北京市西城区', 400, 156, 91.2, 'open', '["烹饪", "美食", "技巧"]'),
('健身达人俱乐部', '健身经验分享,运动计划交流', 'fitness', 1, 39.9342, 116.4374, '北京市东城区', 350, 203, 88.7, 'open', '["健身", "运动", "健康"]'),
('有机食品爱好者', '有机食品推荐,绿色生活理念分享', 'food', 1, 39.9442, 116.4474, '北京市丰台区', 250, 67, 65.8, 'approval', '["有机", "食品", "绿色"]'),
('营养师在线', '专业营养师在线答疑,个性化饮食建议', 'nutrition', 1, 39.9542, 116.4574, '北京市石景山区', 200, 145, 94.5, 'approval', '["营养", "专业", "咨询"]'),
('素食生活家', '素食食谱分享,素食生活方式交流', 'vegetarian', 1, 39.9642, 116.4674, '北京市通州区', 300, 112, 78.9, 'open', '["素食", "食谱", "生活"]'),
('家庭健康管理', '家庭健康饮食规划,全家营养搭配', 'family', 1, 39.9742, 116.4774, '北京市大兴区', 400, 178, 82.4, 'open', '["家庭", "健康", "营养"]');

-- 插入示例社区成员数据
INSERT INTO community_members (community_id, user_id, role, post_count, comment_count) VALUES
(1, 1, 'owner', 25, 156),
(1, 2, 'admin', 18, 89),
(1, 3, 'member', 5, 23),
(2, 1, 'owner', 12, 67),
(2, 4, 'admin', 8, 45),
(3, 1, 'owner', 30, 203),
(3, 5, 'moderator', 15, 112),
(4, 1, 'owner', 22, 178),
(5, 1, 'owner', 10, 56),
(6, 1, 'owner', 35, 245),
(7, 1, 'owner', 18, 134),
(8, 1, 'owner', 20, 167);

-- 插入示例帖子数据
INSERT INTO community_posts (community_id, user_id, title, content, category, view_count, like_count, comment_count) VALUES
(1, 1, '分享一周健康饮食计划', '这是我的一周健康饮食计划,包含早餐、午餐、晚餐的营养搭配,希望能给大家一些参考...', 'health', 523, 89, 34),
(1, 2, '低卡沙拉酱推荐', '推荐一款超棒的低卡沙拉酱,用希腊酸奶替代蛋黄酱,热量减少60%!', 'health', 312, 67, 23),
(2, 1, '今天骑行上班,减排3.6kg', '今天骑行上班,全程18公里!相比开车减少了约3.6kg的碳排放', 'environment', 456, 78, 31),
(3, 1, '空气炸锅做薯片教程', '今天学会了用空气炸锅做薯片,比油炸少用90%的油,一样香脆!', 'cooking', 678, 134, 56),
(4, 1, '三分练七分吃', '今天分享一份高蛋白低脂的健身餐——鸡胸肉+藜麦+蔬菜', 'fitness', 890, 203, 78),
(6, 1, '专业营养师答疑时间', '大家好,我是专业营养师,有什么饮食问题可以在这里提问', 'nutrition', 1234, 312, 145);

-- 更新社区的帖子数
UPDATE communities SET post_count = (
    SELECT COUNT(*) FROM community_posts WHERE community_id = communities.id
);

-- 插入示例用户位置
INSERT INTO user_locations (user_id, latitude, longitude, address) VALUES
(1, 39.9042, 116.4074, '北京市朝阳区建国路88号'),
(2, 39.9142, 116.4174, '北京市海淀区中关村大街'),
(3, 39.9242, 116.4274, '北京市西城区金融街'),
(4, 39.9342, 116.4374, '北京市东城区王府井大街'),
(5, 39.9442, 116.4474, '北京市丰台区丽泽商务区');
