import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        user=os.getenv('DATABASE_USER', 'root'),
        password=os.getenv('DATABASE_PASSWORD', ''),
        database=os.getenv('DATABASE_NAME', 'health_diet_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def execute_sql_file(file_path):
    """执行SQL文件"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
                sql_statements = []
                current_statement = []
                
                for line in sql_content.split('\n'):
                    line = line.strip()
                    
                    if not line or line.startswith('--'):
                        continue
                    
                    current_statement.append(line)
                    
                    if line.endswith(';'):
                        statement = ' '.join(current_statement)
                        sql_statements.append(statement)
                        current_statement = []
                
                for statement in sql_statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                            print(f"✓ 执行成功: {statement[:50]}...")
                        except Exception as e:
                            print(f"✗ 执行失败: {e}")
                            print(f"  SQL: {statement[:100]}...")
                
                conn.commit()
                print("\n✓ 数据库初始化完成！")
    except Exception as e:
        print(f"✗ 错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("初始化社区数据库表")
    print("=" * 60)
    
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'community_schema.sql')
    print(f"SQL文件路径: {sql_file}")
    
    if os.path.exists(sql_file):
        execute_sql_file(sql_file)
    else:
        print(f"✗ SQL文件不存在: {sql_file}")
