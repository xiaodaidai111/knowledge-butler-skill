"""
检查并创建缺失的数据库表
"""
import pymysql
import logging

from database.backend.core.db_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_create_tables():
    """检查并创建缺失的数据库表"""
    try:
        db_config = get_config()
        
        logger.info(f"连接到数据库: {db_config.host}:{db_config.port}/{db_config.database}")
        
        conn = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查所有表
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"现有表: {existing_tables}")
        
        # 需要创建的表
        tables_to_create = {
            'user_activities': """
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户活动记录表'
            """,
            'user_settings': """
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好设置表'
            """,
            'user_avatars': """
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户头像存储表'
            """,
            'login_history': """
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
            """
        }
        
        # 创建缺失的表
        for table_name, create_sql in tables_to_create.items():
            if table_name not in existing_tables:
                logger.info(f"创建表: {table_name}")
                cursor.execute(create_sql)
                logger.info(f"✓ 成功创建表: {table_name}")
            else:
                logger.info(f"○ 表已存在，跳过: {table_name}")
        
        conn.commit()
        
        # 验证结果
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        logger.info("\n" + "="*80)
        logger.info("数据库表检查完成！")
        logger.info("="*80)
        logger.info(f"所有表: {all_tables}")
        logger.info("="*80)
        
        cursor.close()
        conn.close()
        
        logger.info("\n✓ 数据库表检查完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库表检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = check_and_create_tables()
    exit(0 if success else 1)
