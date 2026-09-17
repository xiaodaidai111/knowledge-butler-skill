import sys
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database.backend.core.db_config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def execute_sql_file(sql_file_path):
    """执行SQL文件"""
    try:
        config = get_config()
        
        logger.info("=" * 60)
        logger.info("开始执行家常菜推荐榜数据库初始化")
        logger.info("=" * 60)
        
        logger.info(f"数据库配置:")
        logger.info(f"  主机: {config.host}")
        logger.info(f"  端口: {config.port}")
        logger.info(f"  用户: {config.user}")
        logger.info(f"  数据库: {config.database}")
        
        connection = mysql.connector.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset='utf8mb4'
        )
        
        if connection.is_connected():
            logger.info("✅ 数据库连接成功")
            
            cursor = connection.cursor()
            
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()
                
            statements = sql_script.split(';')
            
            executed_count = 0
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        connection.commit()
                        executed_count += 1
                    except Error as e:
                        logger.warning(f"⚠️  执行语句时出错: {e}")
                        logger.warning(f"语句内容: {statement[:100]}...")
                        connection.rollback()
            
            cursor.close()
            connection.close()
            
            logger.info("=" * 60)
            logger.info(f"✅ 数据库初始化完成！执行了 {executed_count} 条SQL语句")
            logger.info("=" * 60)
            
            return True
            
    except Error as e:
        logger.error(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        return False

def main():
    sql_file = Path(__file__).parent.parent / 'database' / 'recipe_recommendation_schema.sql'
    
    if not sql_file.exists():
        logger.error(f"❌ SQL文件不存在: {sql_file}")
        return 1
    
    success = execute_sql_file(sql_file)
    
    if success:
        logger.info("\n🎉 家常菜推荐榜数据库初始化成功！")
        logger.info("\n下一步：")
        logger.info("  1. 启动后端服务: python backend/unified_app.py")
        logger.info("  2. 启动定时更新服务: python backend/scripts/recipe_recommendation_updater.py")
        logger.info("  3. 访问家常菜推荐榜页面")
        return 0
    else:
        logger.error("\n❌ 数据库初始化失败")
        logger.error("\n请检查：")
        logger.error("  1. MySQL服务是否正在运行")
        logger.error("  2. 数据库配置是否正确（.env文件）")
        logger.error("  3. 是否有创建表的权限")
        return 1

if __name__ == "__main__":
    sys.exit(main())