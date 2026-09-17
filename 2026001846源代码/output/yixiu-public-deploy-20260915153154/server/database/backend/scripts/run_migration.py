import pymysql
import logging
from pathlib import Path
from database.backend.core.db_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_migration():
    """执行数据库迁移脚本"""
    try:
        config = get_config()
        logger.info("开始执行数据库迁移...")
        
        # 读取迁移脚本
        # 迁移 SQL 文件位置以实际项目为准；此脚本保留原逻辑，但基准目录改为仓库根
        migration_file = Path(__file__).resolve().parents[2] / "database" / "migrations" / "001_extend_users_table.sql"
        
        if not migration_file.exists():
            logger.error(f"迁移文件不存在: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 连接数据库
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        
        try:
            cursor = conn.cursor()
            
            # 分割SQL语句并逐个执行
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        conn.commit()
                        logger.info(f"执行成功: {statement[:50]}...")
                    except pymysql.Error as e:
                        # 忽略"IF NOT EXISTS"相关的错误
                        if "IF NOT EXISTS" in statement or "already exists" in str(e).lower():
                            logger.info(f"跳过已存在的对象: {statement[:50]}...")
                            conn.commit()
                        else:
                            logger.error(f"执行失败: {e}")
                            logger.error(f"SQL: {statement[:100]}...")
                            conn.rollback()
            
            logger.info("✅ 数据库迁移完成")
            return True
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == "__main__":
    success = execute_migration()
    exit(0 if success else 1)
