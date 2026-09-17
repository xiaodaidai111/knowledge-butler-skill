"""
检查user_activities表结构
"""
import pymysql
import logging
from database.backend.core.db_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_structure():
    """检查user_activities表结构"""
    try:
        db_config = get_config()
        
        conn = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查user_activities表结构
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                COLUMN_TYPE, 
                IS_NULLABLE, 
                COLUMN_DEFAULT, 
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s 
              AND TABLE_NAME = 'user_activities'
            ORDER BY ORDINAL_POSITION
        """, (db_config.database,))
        
        results = cursor.fetchall()
        
        logger.info("\n" + "="*80)
        logger.info("user_activities 表结构：")
        logger.info("="*80)
        for row in results:
            logger.info(f"字段: {row[0]:20} | 类型: {row[1]:20} | 可空: {row[2]:5} | 默认值: {str(row[3]):15} | 注释: {row[4]}")
        logger.info("="*80)
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"检查表结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_table_structure()
