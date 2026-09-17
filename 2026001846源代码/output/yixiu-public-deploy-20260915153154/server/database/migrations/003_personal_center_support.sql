USE health_diet_db;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS age INT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS height DECIMAL(5,2) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS weight DECIMAL(5,2) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL DEFAULT NULL;

CREATE TABLE IF NOT EXISTS user_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSON NULL,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_activity_user (user_id),
    INDEX idx_user_activity_type (activity_type),
    INDEX idx_user_activity_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_avatars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    avatar_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    file_size INT,
    file_format VARCHAR(20),
    width INT,
    height INT,
    is_current TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_avatar_user (user_id),
    INDEX idx_user_avatar_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
