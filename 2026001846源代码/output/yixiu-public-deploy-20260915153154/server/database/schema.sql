-- 创建数据库
CREATE DATABASE IF NOT EXISTS health_diet_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE health_diet_db;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(50),
    avatar VARCHAR(255),
    level INT DEFAULT 1,
    level_name VARCHAR(20) DEFAULT '新手',
    is_guest TINYINT(1) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 健康记录表
CREATE TABLE IF NOT EXISTS health_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    record_date DATE NOT NULL,
    calories INT DEFAULT 0,
    protein DECIMAL(5,2) DEFAULT 0,
    fat DECIMAL(5,2) DEFAULT 0,
    carbs DECIMAL(5,2) DEFAULT 0,
    steps INT DEFAULT 0,
    water INT DEFAULT 0,
    sleep_hours DECIMAL(3,1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 健康目标表
CREATE TABLE IF NOT EXISTS health_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    calorie_goal INT DEFAULT 2000,
    protein_goal DECIMAL(5,2) DEFAULT 120,
    fat_goal DECIMAL(5,2) DEFAULT 60,
    carbs_goal DECIMAL(5,2) DEFAULT 250,
    steps_goal INT DEFAULT 10000,
    water_goal INT DEFAULT 2000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_goals (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 餐厅表
CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    image VARCHAR(255),
    rating DECIMAL(2,1) DEFAULT 0,
    type VARCHAR(50),
    price DECIMAL(10,2) DEFAULT 0,
    distance VARCHAR(20),
    address VARCHAR(255),
    phone VARCHAR(20),
    business_hours VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(10,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 餐厅评价表
CREATE TABLE IF NOT EXISTS restaurant_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    user_id INT NOT NULL,
    user_name VARCHAR(50),
    avatar VARCHAR(255),
    rating INT,
    content TEXT,
    images JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_restaurant (restaurant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 菜谱表
CREATE TABLE IF NOT EXISTS recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    image VARCHAR(255),
    description TEXT,
    cuisine VARCHAR(50),
    cooking_time INT DEFAULT 0,
    difficulty VARCHAR(20),
    calories INT,
    ingredients JSON,
    steps JSON,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cuisine (cuisine)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 外卖分析表
CREATE TABLE IF NOT EXISTS takeaway_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100),
    image VARCHAR(255),
    score INT DEFAULT 0,
    calories INT DEFAULT 0,
    protein DECIMAL(5,2) DEFAULT 0,
    fat DECIMAL(5,2) DEFAULT 0,
    carbs DECIMAL(5,2) DEFAULT 0,
    dimensions JSON,
    suggestions JSON,
    analysis_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 对话历史表
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(20) DEFAULT 'chat',
    title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 对话消息表
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 成就表
CREATE TABLE IF NOT EXISTS achievements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户成就表
CREATE TABLE IF NOT EXISTS user_achievements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    achievement_id INT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_achievement (user_id, achievement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    item_id INT NOT NULL,
    title VARCHAR(100),
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 浏览历史表
CREATE TABLE IF NOT EXISTS browse_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(100),
    url VARCHAR(255),
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始成就数据
INSERT INTO achievements (name, icon, description) VALUES
('从零开始', '🌱', '完成第一次健康记录'),
('七日连胜', '🔥', '连续7天完成健康目标'),
('健康达人', '💪', '累计完成30次健康记录'),
('完美一周', '⭐', '一周内所有指标达标'),
('早起鸟', '🌅', '连续7天早起打卡'),
('运动健将', '🏃', '累计运动10000步'),
('饮水冠军', '💧', '单日饮水达到3000ml'),
('营养均衡', '🥗', '连续7天营养均衡');

-- 用户饮食偏好表
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    allergies TEXT,
    favorite_cuisines TEXT,
    dietary_habits TEXT,
    custom_notes TEXT,
    cooking_exp INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_preferences (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 游客会话表
CREATE TABLE IF NOT EXISTS guest_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    device_info TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'zh-CN',
    notifications_enabled TINYINT(1) DEFAULT 1,
    privacy_level VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_settings (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 登录历史表
CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    device_info TEXT,
    login_type VARCHAR(20),
    status VARCHAR(20),
    INDEX idx_user_login (user_id, login_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Team Memory OS：AI 原生项目协作系统核心表
-- 目标：从“设备故障检索 / 工单闭环”升级为
-- Context Pack、Task Execution、Team Memory、Skill、Eval 的可计算资产体系
-- ============================================================

CREATE TABLE IF NOT EXISTS team_projects (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    repo_url VARCHAR(255),
    owner VARCHAR(80),
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_team_projects_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_context_packs (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64),
    title VARCHAR(160) NOT NULL,
    objective TEXT,
    source_refs_json JSON,
    code_refs_json JSON,
    memory_refs_json JSON,
    skill_refs_json JSON,
    risk_json JSON,
    status VARCHAR(30) DEFAULT 'draft',
    created_by VARCHAR(80) DEFAULT 'Context Engine',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_context_task (task_id),
    INDEX idx_context_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_memories (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    memory_type VARCHAR(40) DEFAULT 'Memory Unit',
    problem TEXT,
    attempts_json JSON,
    root_cause TEXT,
    solution TEXT,
    applies_when TEXT,
    validation_json JSON,
    source_refs_json JSON,
    tags_json JSON,
    status VARCHAR(30) DEFAULT 'pending_review',
    reviewer VARCHAR(80),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_team_memories_type (memory_type),
    INDEX idx_team_memories_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_skills (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    version VARCHAR(30) DEFAULT 'v0.1',
    purpose TEXT,
    trigger_rules TEXT,
    workflow_json JSON,
    required_context_json JSON,
    metrics_json JSON,
    status VARCHAR(30) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_team_skills_status (status),
    UNIQUE KEY uk_team_skill_version (name, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_eval_cases (
    id VARCHAR(64) PRIMARY KEY,
    skill_id VARCHAR(64),
    name VARCHAR(160) NOT NULL,
    input_json JSON,
    expected_json JSON,
    rubric_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_eval_cases_skill (skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_eval_runs (
    id VARCHAR(64) PRIMARY KEY,
    eval_case_id VARCHAR(64),
    skill_id VARCHAR(64),
    skill_version VARCHAR(30),
    score DECIMAL(5,2) DEFAULT 0,
    success TINYINT(1) DEFAULT 0,
    cost_json JSON,
    result_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_eval_runs_skill (skill_id, skill_version),
    INDEX idx_eval_runs_case (eval_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_issue_skill_links (
    id VARCHAR(64) PRIMARY KEY,
    issue_key VARCHAR(120) NOT NULL,
    task_id VARCHAR(64),
    repeat_count INT DEFAULT 1,
    memory_id VARCHAR(64),
    skill_id VARCHAR(64),
    status VARCHAR(30) DEFAULT 'candidate',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_issue_skill_issue (issue_key),
    INDEX idx_issue_skill_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS team_model_routing_logs (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64),
    agent_id VARCHAR(64),
    model_name VARCHAR(120),
    reason TEXT,
    context_pack_id VARCHAR(64),
    cost_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_routing_task (task_id),
    INDEX idx_model_routing_agent (agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
