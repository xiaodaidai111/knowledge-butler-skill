# -*- coding: utf-8 -*-
"""
数据库更新脚本
添加缺失的字段和表
"""
import pymysql
import logging
from database.backend.core.db_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """更新数据库结构"""
    config = get_config()
    
    try:
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # 检查并添加 is_guest 字段
            cursor.execute("SHOW COLUMNS FROM users LIKE 'is_guest'")
            if not cursor.fetchone():
                logger.info("添加 is_guest 字段到 users 表")
                cursor.execute("ALTER TABLE users ADD COLUMN is_guest TINYINT(1) DEFAULT 0")
            
            # 检查并添加 status 字段
            cursor.execute("SHOW COLUMNS FROM users LIKE 'status'")
            if not cursor.fetchone():
                logger.info("添加 status 字段到 users 表")
                cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
            
            # 创建 guest_sessions 表
            cursor.execute("""
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建 user_settings 表
            cursor.execute("""
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建 login_history 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    device_info TEXT,
                    login_type VARCHAR(20),
                    status VARCHAR(20),
                    INDEX idx_user_login (user_id, login_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            logger.info("✅ 数据库更新完成")
            
    except Exception as e:
        logger.error(f"❌ 数据库更新失败: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database()