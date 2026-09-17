-- 家常菜推荐榜相关数据库表

-- 菜品评分表
CREATE TABLE IF NOT EXISTS recipe_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    rating DECIMAL(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_recipe (user_id, recipe_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 菜品点赞表
CREATE TABLE IF NOT EXISTS recipe_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_recipe_like (user_id, recipe_id),
    INDEX idx_recipe (recipe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 菜品分享表
CREATE TABLE IF NOT EXISTS recipe_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    share_type VARCHAR(20) DEFAULT 'general',
    platform VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    INDEX idx_recipe (recipe_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 菜品评论表
CREATE TABLE IF NOT EXISTS recipe_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    parent_id INT DEFAULT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
    INDEX idx_recipe (recipe_id),
    INDEX idx_user (user_id),
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 推荐榜单表
CREATE TABLE IF NOT EXISTS recommendation_lists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 榜单菜品关联表
CREATE TABLE IF NOT EXISTS list_recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_id INT NOT NULL,
    recipe_id INT NOT NULL,
    rank_position INT NOT NULL,
    score DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (list_id) REFERENCES recommendation_lists(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_list_recipe (list_id, recipe_id),
    INDEX idx_list (list_id),
    INDEX idx_rank (rank_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户推荐历史表
CREATE TABLE IF NOT EXISTS user_recommendation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    list_id INT NOT NULL,
    shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    clicked_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (list_id) REFERENCES recommendation_lists(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_shown (shown_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始推荐榜单数据
INSERT INTO recommendation_lists (name, type, description, icon, sort_order) VALUES
('热门推荐', 'hot', '最受欢迎的家常菜，基于用户评分和互动数据', '🔥', 1),
('季节性推荐', 'seasonal', '当季最佳食材搭配，营养又美味', '🌸', 2),
('新手友好', 'beginner', '简单易学，适合烹饪新手', '🌱', 3),
('快手菜', 'quick', '30分钟内可完成的快手菜', '⚡', 4),
('营养均衡', 'nutritious', '营养搭配均衡，健康美味', '💪', 5),
('经济实惠', 'economical', '性价比高，经济实惠', '💰', 6);

-- 插入示例菜品数据
INSERT INTO recipes (name, image, description, cuisine, cooking_time, difficulty, calories, ingredients, steps, tags) VALUES
('西红柿炒鸡蛋', 'https://example.com/tomato-egg.jpg', '经典家常菜，酸甜可口，营养丰富', '家常菜', 15, '简单', 180, 
 JSON_ARRAY('西红柿2个', '鸡蛋3个', '盐适量', '糖少许', '葱花'),
 JSON_ARRAY('西红柿洗净切块', '鸡蛋打散加少许盐', '热锅下油炒鸡蛋盛起', '再炒西红柿出汁', '加入鸡蛋翻炒均匀', '调味撒葱花即可'),
 JSON_ARRAY('快手菜', '新手友好', '经济实惠')),

('宫保鸡丁', 'https://example.com/kungpao-chicken.jpg', '川菜经典，麻辣鲜香', '川菜', 25, '中等', 320,
 JSON_ARRAY('鸡胸肉300g', '花生米50g', '干辣椒10个', '花椒适量', '葱姜蒜'),
 JSON_ARRAY('鸡肉切丁腌制', '花生米炸酥', '炒干辣椒花椒', '下鸡丁翻炒', '调味加花生米'),
 JSON_ARRAY('热门推荐', '川菜')),

('土豆烧牛肉', 'https://example.com/potato-beef.jpg', '家常炖菜，软烂入味', '家常菜', 60, '中等', 450,
 JSON_ARRAY('牛肉500g', '土豆2个', '胡萝卜1根', '洋葱半个', '八角桂皮'),
 JSON_ARRAY('牛肉切块焯水', '土豆胡萝卜切块', '炒糖色', '下牛肉翻炒', '加调料炖煮', '最后加土豆'),
 JSON_ARRAY('营养均衡', '家常菜')),

('麻婆豆腐', 'https://example.com/mapo-tofu.jpg', '川菜代表，麻辣鲜嫩', '川菜', 20, '中等', 280,
 JSON_ARRAY('嫩豆腐1盒', '猪肉末100g', '郫县豆瓣酱', '花椒粉', '葱花'),
 JSON_ARRAY('豆腐切块焯水', '炒肉末出油', '加豆瓣酱炒出红油', '下豆腐烧制', '撒花椒粉葱花'),
 JSON_ARRAY('热门推荐', '川菜', '麻辣')),

('清炒时蔬', 'https://example.com/stir-fry-vegetables.jpg', '简单清爽，营养健康', '家常菜', 10, '简单', 80,
 JSON_ARRAY('青菜500g', '蒜末', '盐', '鸡精'),
 JSON_ARRAY('青菜洗净切段', '热锅爆香蒜末', '下青菜大火快炒', '调味即可'),
 JSON_ARRAY('快手菜', '新手友好', '营养均衡', '季节性推荐')),

('红烧肉', 'https://example.com/braised-pork.jpg', '经典名菜，肥而不腻', '家常菜', 90, '困难', 580,
 JSON_ARRAY('五花肉500g', '冰糖', '生抽老抽', '料酒', '葱姜八角'),
 JSON_ARRAY('五花肉切块焯水', '炒糖色', '下肉块翻炒上色', '加调料炖煮', '大火收汁'),
 JSON_ARRAY('热门推荐', '营养均衡')),

('蒸蛋羹', 'https://example.com/steamed-egg.jpg', '嫩滑爽口，老少皆宜', '家常菜', 15, '简单', 120,
 JSON_ARRAY('鸡蛋3个', '温水', '盐', '香油', '葱花'),
 JSON_ARRAY('鸡蛋打散加温水', '过筛去泡沫', '蒸8-10分钟', '淋香油撒葱花'),
 JSON_ARRAY('新手友好', '快手菜', '营养均衡')),

('鱼香肉丝', 'https://example.com/yuxiang-pork.jpg', '川菜经典，酸甜微辣', '川菜', 25, '中等', 300,
 JSON_ARRAY('猪肉丝200g', '木耳', '胡萝卜', '青椒', '葱姜蒜'),
 JSON_ARRAY('肉丝腌制', '调鱼香汁', '炒肉丝盛起', '炒配菜', '合炒调味'),
 JSON_ARRAY('热门推荐', '川菜')),

('糖醋排骨', 'https://example.com/sweet-sour-ribs.jpg', '酸甜可口，老少皆宜', '家常菜', 45, '中等', 420,
 JSON_ARRAY('排骨500g', '冰糖', '醋', '生抽', '料酒'),
 JSON_ARRAY('排骨焯水', '炒糖色', '下排骨翻炒', '加调料炖煮', '收汁调味'),
 JSON_ARRAY('热门推荐', '家常菜')),

('蛋炒饭', 'https://example.com/egg-fried-rice.jpg', '简单快手，营养丰富', '家常菜', 10, '简单', 350,
 JSON_ARRAY('米饭1碗', '鸡蛋2个', '葱花', '盐', '生抽'),
 JSON_ARRAY('鸡蛋炒散盛起', '下米饭炒散', '加鸡蛋翻炒均匀', '调味撒葱花'),
 JSON_ARRAY('快手菜', '新手友好', '经济实惠'));

-- 插入榜单菜品关联数据
INSERT INTO list_recipes (list_id, recipe_id, rank_position, score) VALUES
-- 热门推荐
(1, 1, 1, 95.5),
(1, 2, 2, 92.3),
(1, 3, 3, 90.8),
(1, 4, 4, 88.6),
(1, 6, 5, 87.2),

-- 季节性推荐
(2, 5, 1, 88.5),
(2, 1, 2, 85.3),
(2, 3, 3, 82.1),
(2, 7, 4, 80.5),
(2, 10, 5, 78.9),

-- 新手友好
(3, 1, 1, 96.2),
(3, 5, 2, 93.8),
(3, 7, 3, 91.5),
(3, 10, 4, 89.3),
(3, 2, 5, 85.7),

-- 快手菜
(4, 5, 1, 94.5),
(4, 10, 2, 92.8),
(4, 1, 3, 90.3),
(4, 7, 4, 88.6),
(4, 4, 5, 86.2),

-- 营养均衡
(5, 3, 1, 93.5),
(5, 5, 2, 91.8),
(5, 7, 3, 89.5),
(5, 1, 4, 87.3),
(5, 2, 5, 85.9),

-- 经济实惠
(6, 10, 1, 95.2),
(6, 1, 2, 92.6),
(6, 5, 3, 90.4),
(6, 7, 4, 88.1),
(6, 4, 5, 86.5);