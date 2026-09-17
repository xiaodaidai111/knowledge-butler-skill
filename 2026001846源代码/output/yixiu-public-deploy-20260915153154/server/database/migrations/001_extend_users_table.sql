-- 扩展用户表结构，添加更多用户信息字段
USE health_diet_db;

-- 为users表添加新字段
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT '男' COMMENT '性别',
ADD COLUMN IF NOT EXISTS age INT DEFAULT NULL COMMENT '年龄',
ADD COLUMN IF NOT EXISTS height DECIMAL(5,2) DEFAULT NULL COMMENT '身高(cm)',
ADD COLUMN IF NOT EXISTS weight DECIMAL(5,2) DEFAULT NULL COMMENT '体重(kg)',
ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT NULL COMMENT '个人简介',
ADD COLUMN IF NOT EXISTS is_guest TINYINT(1) DEFAULT 0 COMMENT '是否为游客',
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' COMMENT '账号状态: active, inactive, banned';

-- 添加索引
ALTER TABLE users ADD INDEX IF NOT EXISTS idx_status (status);
ALTER TABLE users ADD INDEX IF NOT EXISTS idx_is_guest (is_guest);

-- 创建游客会话表
CREATE TABLE IF NOT EXISTS guest_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL COMMENT '会话ID',
    device_info TEXT COMMENT '设备信息',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='游客会话表';

-- 创建用户登录历史表
CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL DEFAULT NULL,
    ip_address VARCHAR(50),
    device_info TEXT,
    login_type VARCHAR(20) DEFAULT 'password' COMMENT '登录类型: password, wechat, qq',
    status VARCHAR(20) DEFAULT 'success' COMMENT '状态: success, failed',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_login_time (login_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户登录历史表';

-- 创建用户偏好设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    theme VARCHAR(20) DEFAULT 'light' COMMENT '主题: light, dark',
    language VARCHAR(10) DEFAULT 'zh-CN' COMMENT '语言',
    notifications_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用通知',
    privacy_level VARCHAR(20) DEFAULT 'normal' COMMENT '隐私级别',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_settings (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好设置表';

-- 创建用户活动记录表
CREATE TABLE IF NOT EXISTS user_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(50) NOT NULL COMMENT '活动类型',
    activity_data JSON COMMENT '活动数据',
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户活动记录表';

-- 创建头像存储表
CREATE TABLE IF NOT EXISTS user_avatars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    avatar_url VARCHAR(500) NOT NULL COMMENT '头像URL',
    thumbnail_url VARCHAR(500) COMMENT '缩略图URL',
    file_size INT COMMENT '文件大小(bytes)',
    file_format VARCHAR(20) COMMENT '文件格式',
    width INT COMMENT '图片宽度',
    height INT COMMENT '图片高度',
    is_current TINYINT(1) DEFAULT 0 COMMENT '是否为当前头像',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户头像存储表';

-- 插入默认用户设置（为现有用户）
INSERT IGNORE INTO user_settings (user_id, theme, language, notifications_enabled, privacy_level)
SELECT id, 'light', 'zh-CN', 1, 'normal' FROM users WHERE id NOT IN (SELECT user_id FROM user_settings);

-- 创建触发器：当用户登录时更新最后登录时间
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_last_login 
AFTER INSERT ON login_history
FOR EACH ROW
BEGIN
    IF NEW.status = 'success' THEN
        UPDATE users SET last_login_at = NEW.login_time WHERE id = NEW.user_id;
    END IF;
END//
DELIMITER ;
