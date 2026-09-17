-- 修改外卖分析表结构，以支持健康评分算法
USE health_diet_db;

-- 修改takeaway_analysis表
ALTER TABLE takeaway_analysis
    -- 添加详细营养成分字段
    ADD COLUMN IF NOT EXISTS saturated_fat DECIMAL(5,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sugar DECIMAL(5,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sodium DECIMAL(5,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS fiber DECIMAL(5,2) DEFAULT 0,
    
    -- 添加加工方式和食材新鲜度
    ADD COLUMN IF NOT EXISTS processing VARCHAR(50) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS freshness VARCHAR(50) DEFAULT NULL,
    
    -- 添加食材列表
    ADD COLUMN IF NOT EXISTS ingredients JSON DEFAULT NULL,
    
    -- 添加营养分析详情
    ADD COLUMN IF NOT EXISTS nutrition_analysis JSON DEFAULT NULL,
    
    -- 添加评分详情
    ADD COLUMN IF NOT EXISTS processing_score INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS freshness_score INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS nutrition_score INT DEFAULT 0;

-- 创建外卖食品表，用于存储常见外卖食品的营养信息
CREATE TABLE IF NOT EXISTS takeaway_foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    calories INT DEFAULT 0,
    protein DECIMAL(5,2) DEFAULT 0,
    fat DECIMAL(5,2) DEFAULT 0,
    saturated_fat DECIMAL(5,2) DEFAULT 0,
    carbs DECIMAL(5,2) DEFAULT 0,
    sugar DECIMAL(5,2) DEFAULT 0,
    sodium DECIMAL(5,2) DEFAULT 0,
    fiber DECIMAL(5,2) DEFAULT 0,
    processing VARCHAR(50),
    ingredients JSON,
    average_score INT DEFAULT 0,
    popularity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category),
    INDEX idx_score (average_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建健康评分历史表，用于跟踪用户的外卖健康评分历史
CREATE TABLE IF NOT EXISTS health_score_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    takeaway_id INT DEFAULT NULL,
    food_name VARCHAR(100),
    score INT DEFAULT 0,
    nutrition_score INT DEFAULT 0,
    processing_score INT DEFAULT 0,
    freshness_score INT DEFAULT 0,
    calories INT DEFAULT 0,
    protein DECIMAL(5,2) DEFAULT 0,
    fat DECIMAL(5,2) DEFAULT 0,
    carbs DECIMAL(5,2) DEFAULT 0,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, analysis_date),
    INDEX idx_score (score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建健康建议表，用于存储针对不同健康问题的建议
CREATE TABLE IF NOT EXISTS health_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,  -- 建议类型：营养、加工方式、食材等
    condition VARCHAR(100) NOT NULL,  -- 触发条件
    suggestion TEXT NOT NULL,  -- 建议内容
    priority INT DEFAULT 1,  -- 优先级
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_condition (condition)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始健康建议数据
INSERT INTO health_suggestions (type, condition, suggestion, priority) VALUES
('nutrition', 'high_calories', '建议选择低热量的食物，控制每日总热量摄入', 1),
('nutrition', 'high_fat', '建议选择低脂食物，减少油脂摄入', 1),
('nutrition', 'high_sodium', '建议选择低盐食物，减少钠的摄入', 1),
('nutrition', 'low_protein', '建议增加蛋白质的摄入，选择瘦肉、鱼类等优质蛋白', 1),
('nutrition', 'low_fiber', '建议增加膳食纤维的摄入，多吃蔬菜和水果', 1),
('processing', 'fried', '建议选择清蒸、水煮等更健康的烹饪方式', 1),
('processing', 'deep_fried', '建议避免油炸食品，选择更健康的烹饪方式', 1),
('ingredients', 'no_vegetables', '建议增加蔬菜的摄入，保持饮食均衡', 1),
('ingredients', 'processed_food', '建议选择新鲜食材，减少加工食品的摄入', 1),
('general', 'low_score', '建议选择更健康的外卖选项，注意饮食均衡', 1);
