# -*- coding: utf-8 -*-
"""
使用配置好的数据库连接初始化数据库
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database.backend.core.db_config import get_config
from database.backend.core.db_pool import get_pool
from database.backend.core.db_manager import get_db


def initialize_database():
    """初始化数据库表"""
    print("=" * 60)
    print("数据库初始化")
    print("=" * 60)
    
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
        
        print("\n开始创建数据库表...")
        
        tables = [
            {
                'name': 'users',
                'sql': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(50),
                    avatar VARCHAR(255),
                    height DECIMAL(5,2),
                    weight DECIMAL(5,2),
                    age INT,
                    gender VARCHAR(10),
                    level INT DEFAULT 1,
                    level_name VARCHAR(20) DEFAULT '新手',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_phone (phone)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'user_preferences',
                'sql': """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    allergies TEXT,
                    favorite_cuisines TEXT,
                    dietary_habits TEXT,
                    custom_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'health_goals',
                'sql': """
                CREATE TABLE IF NOT EXISTS health_goals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    calorie_goal INT DEFAULT 2000,
                    protein_goal INT DEFAULT 120,
                    fat_goal INT DEFAULT 60,
                    carbs_goal INT DEFAULT 250,
                    steps_goal INT DEFAULT 10000,
                    water_goal INT DEFAULT 2000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'health_records',
                'sql': """
                CREATE TABLE IF NOT EXISTS health_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    record_date DATE NOT NULL,
                    calories INT DEFAULT 0,
                    protein DECIMAL(5,1) DEFAULT 0,
                    fat DECIMAL(5,1) DEFAULT 0,
                    carbs DECIMAL(5,1) DEFAULT 0,
                    steps INT DEFAULT 0,
                    water INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_date (user_id, record_date),
                    INDEX idx_date (record_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'restaurants',
                'sql': """
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50),
                    rating DECIMAL(2,1) DEFAULT 0,
                    price DECIMAL(8,2),
                    address VARCHAR(255),
                    phone VARCHAR(20),
                    opening_hours VARCHAR(100),
                    image_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_rating (rating),
                    INDEX idx_type (type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'user_achievements',
                'sql': """
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    achievement_id INT NOT NULL,
                    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_achievement (user_id, achievement_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            },
            {
                'name': 'achievements',
                'sql': """
                CREATE TABLE IF NOT EXISTS achievements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    icon VARCHAR(50),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            }
        ]
        
        created_tables = []
        for table in tables:
            try:
                db.execute(table['sql'])
                created_tables.append(table['name'])
                print(f"  ✅ {table['name']} 表创建成功")
            except Exception as e:
                print(f"  ❌ {table['name']} 表创建失败: {e}")
                return False
        
        print(f"\n✅ 成功创建 {len(created_tables)} 个表")
        
        print("\n插入初始成就数据...")
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
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        
        print("\n已创建的表：")
        for i, table in enumerate(created_tables, 1):
            print(f"  {i}. {table}")
        
        print("\n现在可以正常使用所有智能体功能了")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = initialize_database()
    
    if success:
        print("\n🎉 数据库初始化成功！")
        print("\n下一步：")
        print("  1. 运行数据库连接测试: python test_database_connection.py")
        print("  2. 启动系统: python ../start_all_services.py")
        return 0
    else:
        print("\n❌ 数据库初始化失败")
        print("\n请检查：")
        print("  1. MySQL服务是否正在运行")
        print("  2. 数据库配置是否正确（.env文件）")
        print("  3. 是否有创建表的权限")
        return 1


if __name__ == "__main__":
    sys.exit(main())
