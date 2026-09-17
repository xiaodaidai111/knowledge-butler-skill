# -*- coding: utf-8 -*-
"""
创建缺失的数据库表
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database.backend.core.db_config import get_config
from database.backend.core.db_pool import get_pool
from database.backend.core.db_manager import get_db

def create_missing_tables():
    print("创建缺失的数据库表")
    print("=" * 60)
    print()
    
    try:
        config = get_config()
        print(f"\n数据库配置:")
        print(f"  主机: {config.host}")
        print(f"  端口: {config.port}")
        print(f"  用户: {config.user}")
        print(f"  数据库: {config.database}")
        
        pool = get_pool()
        success, message = pool.test_connection()
        
        if not success:
            print(f"\n❌ 数据库连接失败: {message}")
            return False
        
        print(f"\n✅ 数据库连接成功")
        
        db = get_db()
        
        print("\n开始创建缺失的数据库表...")
        
        # 1. 创建 user_avatars 表
        print("\n正在创建 user_avatars 表...")
        create_user_avatars_table = """
        CREATE TABLE IF NOT EXISTS user_avatars (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            avatar_url VARCHAR(255) NOT NULL,
            thumbnail_url VARCHAR(255),
            file_size INT,
            file_format VARCHAR(10),
            width INT,
            height INT,
            is_current TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_is_current (is_current)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_user_avatars_table)
        print("✅ user_avatars 表创建成功")
        
        # 2. 创建 user_activities 表
        print("\n正在创建 user_activities 表...")
        create_user_activities_table = """
        CREATE TABLE IF NOT EXISTS user_activities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            activity_type VARCHAR(50) NOT NULL,
            activity_data TEXT,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_activity_type (activity_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_user_activities_table)
        print("✅ user_activities 表创建成功")
        
        # 3. 创建 achievements 表（如果不存在）
        print("\n正在创建 achievements 表...")
        create_achievements_table = """
        CREATE TABLE IF NOT EXISTS achievements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            icon VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_achievements_table)
        print("✅ achievements 表创建成功")
        
        # 4. 创建 user_achievements 表（如果不存在）
        print("\n正在创建 user_achievements 表...")
        create_user_achievements_table = """
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            achievement_id INT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_user_achievements_table)
        print("✅ user_achievements 表创建成功")
        
        # 5. 创建 favorites 表
        print("\n正在创建 favorites 表...")
        create_favorites_table = """
        CREATE TABLE IF NOT EXISTS favorites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(20) NOT NULL,
            item_id INT NOT NULL,
            title VARCHAR(100),
            image VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_type (type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_favorites_table)
        print("✅ favorites 表创建成功")
        
        # 6. 创建 browse_history 表
        print("\n正在创建 browse_history 表...")
        create_browse_history_table = """
        CREATE TABLE IF NOT EXISTS browse_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(100),
            url VARCHAR(255),
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_visited_at (visited_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_browse_history_table)
        print("✅ browse_history 表创建成功")
        
        # 7. 创建 takeaway_analysis 表
        print("\n正在创建 takeaway_analysis 表...")
        create_takeaway_analysis_table = """
        CREATE TABLE IF NOT EXISTS takeaway_analysis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100),
            image VARCHAR(255),
            score DECIMAL(3,1),
            calories INT,
            protein DECIMAL(5,1),
            fat DECIMAL(5,1),
            carbs DECIMAL(5,1),
            analysis_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_takeaway_analysis_table)
        print("✅ takeaway_analysis 表创建成功")
        
        # 插入初始成就数据
        print("\n正在插入初始成就数据...")
        achievements_data = [
            ('从零开始', '🌱', '完成第一次健康记录'),
            ('七日连胜', '🔥', '连续7天完成健康目标'),
            ('健康达人', '💪', '累计完成30次健康记录'),
            ('完美一周', '⭐', '一周内所有指标达标'),
            ('早起鸟', '🌅', '连续7天早起打卡'),
            ('运动健将', '🏃', '累计运动10000步'),
            ('饮水冠军', '💧', '单日饮水达到3000ml'),
            ('营养均衡', '🥗', '连续7天营养均衡')
        ]
        
        for achievement in achievements_data:
            try:
                db.execute(
                    "INSERT IGNORE INTO achievements (name, icon, description) VALUES (%s, %s, %s)",
                    achievement
                )
            except Exception as e:
                print(f"  ⚠️  插入成就 '{achievement[0]}' 失败: {e}")
        
        print("  ✅ 初始成就数据插入完成")
        
        print("\n" + "=" * 60)
        print("✅ 所有缺失的表创建完成！")
        print("=" * 60)
        print("\n已创建的表：")
        print("  1. user_avatars - 用户头像表")
        print("  2. user_activities - 用户活动表")
        print("  3. achievements - 成就表")
        print("  4. user_achievements - 用户成就表")
        print("  5. favorites - 收藏表")
        print("  6. browse_history - 浏览历史表")
        print("  7. takeaway_analysis - 外卖分析表")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)
