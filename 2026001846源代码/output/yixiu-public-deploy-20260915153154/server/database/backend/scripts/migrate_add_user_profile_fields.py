"""
执行数据库迁移：添加用户资料缺失字段
"""
import pymysql
import logging

from database.backend.core.db_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """执行数据库迁移"""
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
        
        # 检查现有字段
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
        """, (db_config.database,))
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"现有字段: {existing_columns}")
        
        # 需要添加的字段
        fields_to_add = [
            ('gender', "VARCHAR(10) DEFAULT '男' COMMENT '性别'", 'avatar'),
            ('age', 'INT DEFAULT NULL COMMENT \'年龄\'', 'gender'),
            ('height', 'DECIMAL(5,2) DEFAULT NULL COMMENT \'身高(cm)\'', 'age'),
            ('weight', 'DECIMAL(5,2) DEFAULT NULL COMMENT \'体重(kg)\'', 'height'),
            ('bio', 'TEXT DEFAULT NULL COMMENT \'个人简介\'', 'weight'),
            ('last_login_at', 'TIMESTAMP NULL DEFAULT NULL COMMENT \'最后登录时间\'', 'updated_at')
        ]
        
        # 添加缺失的字段
        for field_name, field_definition, after_field in fields_to_add:
            if field_name not in existing_columns:
                alter_sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_definition} AFTER {after_field}"
                logger.info(f"执行SQL: {alter_sql}")
                cursor.execute(alter_sql)
                logger.info(f"✓ 成功添加字段: {field_name}")
            else:
                logger.info(f"○ 字段已存在，跳过: {field_name}")
        
        # 添加索引
        indexes_to_add = ['gender', 'age']
        for index_field in indexes_to_add:
            if index_field in existing_columns:
                try:
                    cursor.execute(f"CREATE INDEX idx_{index_field} ON users({index_field})")
                    logger.info(f"✓ 成功添加索引: idx_{index_field}")
                except pymysql.MySQLError as e:
                    if e.args[0] == 1061:  # 索引已存在
                        logger.info(f"○ 索引已存在，跳过: idx_{index_field}")
                    else:
                        raise
        
        conn.commit()
        
        # 验证结果
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                COLUMN_TYPE, 
                IS_NULLABLE, 
                COLUMN_DEFAULT, 
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s 
              AND TABLE_NAME = 'users'
              AND COLUMN_NAME IN ('gender', 'age', 'height', 'weight', 'bio', 'last_login_at')
            ORDER BY ORDINAL_POSITION
        """, (db_config.database,))
        
        results = cursor.fetchall()
        
        logger.info("\n" + "="*80)
        logger.info("数据库迁移完成！验证结果：")
        logger.info("="*80)
        for row in results:
            logger.info(f"字段: {row[0]:15} | 类型: {row[1]:20} | 可空: {row[2]:5} | 默认值: {str(row[3]):15} | 注释: {row[4]}")
        logger.info("="*80)
        
        cursor.close()
        conn.close()
        
        logger.info("\n✓ 数据库迁移成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        return False

if __name__ == '__main__':
    success = migrate_database()
    exit(0 if success else 1)
