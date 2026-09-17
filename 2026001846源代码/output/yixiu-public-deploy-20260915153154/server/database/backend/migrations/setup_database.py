"""
MySQL数据库连接检查和配置助手
"""
import os
import sys
import getpass
from pathlib import Path

def check_mysql_service():
    """检查MySQL服务状态"""
    print("=" * 60)
    print("1. 检查MySQL服务状态")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            ['sc', 'query', 'MySQL*'],
            capture_output=True,
            text=True
        )
        if 'RUNNING' in result.stdout:
            print("✅ MySQL服务正在运行")
            return True
        else:
            print("⚠️  MySQL服务未运行")
            print("请启动MySQL服务：")
            print("  方法1: services.msc -> 找到MySQL -> 启动")
            print("  方法2: net start MySQL")
            return False
    except Exception as e:
        print(f"❌ 无法检查MySQL服务: {e}")
        return False

def check_mysql_connection(host, port, user, password, database):
    """测试MySQL连接"""
    print("\n" + "=" * 60)
    print("2. 测试MySQL连接")
    print("=" * 60)
    
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        print(f"✅ 成功连接到MySQL数据库: {database}")
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"❌ 连接失败: {e}")
        return False

def check_database_exists(host, port, user, password, database):
    """检查数据库是否存在"""
    print("\n" + "=" * 60)
    print("3. 检查数据库是否存在")
    print("=" * 60)
    
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{database}'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"✅ 数据库 '{database}' 已存在")
            return True
        else:
            print(f"⚠️  数据库 '{database}' 不存在")
            return False
    except pymysql.Error as e:
        print(f"❌ 检查失败: {e}")
        return False

def create_database(host, port, user, password, database):
    """创建数据库"""
    print("\n" + "=" * 60)
    print("4. 创建数据库")
    print("=" * 60)
    
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {database} "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()
        print(f"✅ 数据库 '{database}' 创建成功")
        return True
    except pymysql.Error as e:
        print(f"❌ 创建失败: {e}")
        return False

def check_env_file():
    """检查.env文件"""
    print("\n" + "=" * 60)
    print("5. 检查.env配置文件")
    print("=" * 60)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env文件不存在")
        return None
    
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': int(os.getenv('DATABASE_PORT', 3306)),
        'user': os.getenv('DATABASE_USER', 'root'),
        'password': os.getenv('DATABASE_PASSWORD', ''),
        'database': os.getenv('DATABASE_NAME', 'health_diet_db'),
    }
    
    print("当前配置:")
    print(f"  主机: {config['host']}")
    print(f"  端口: {config['port']}")
    print(f"  用户: {config['user']}")
    print(f"  密码: {'***已设置***' if config['password'] else '❌ 未设置'}")
    print(f"  数据库: {config['database']}")
    
    return config

def update_env_password(password):
    """更新.env文件中的密码"""
    print("\n" + "=" * 60)
    print("6. 更新.env文件")
    print("=" * 60)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env文件不存在")
        return False
    
    content = env_path.read_text(encoding='utf-8')
    
    if 'DATABASE_PASSWORD=' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('DATABASE_PASSWORD='):
                lines[i] = f'DATABASE_PASSWORD={password}'
                break
        content = '\n'.join(lines)
        env_path.write_text(content, encoding='utf-8')
        print("✅ 密码已更新到.env文件")
        return True
    else:
        print("❌ .env文件中未找到DATABASE_PASSWORD配置")
        return False

def main():
    print("\n" + "=" * 60)
    print("MySQL数据库连接配置助手")
    print("=" * 60)
    
    # 检查服务
    service_running = check_mysql_service()
    if not service_running:
        print("\n请先启动MySQL服务，然后重新运行此脚本")
        return
    
    # 检查配置
    config = check_env_file()
    if not config:
        print("\n请确保.env文件存在")
        return
    
    # 如果密码未设置，询问用户
    if not config['password']:
        print("\n⚠️  数据库密码未设置")
        password = getpass.getpass("请输入MySQL root密码: ")
        
        # 测试连接
        if check_mysql_connection(
            config['host'],
            config['port'],
            config['user'],
            password,
            config['database']
        ):
            # 更新密码
            update_env_password(password)
            config['password'] = password
        else:
            print("\n❌ 密码错误，请检查后重试")
            return
    
    # 测试连接
    if not check_mysql_connection(
        config['host'],
        config['port'],
        config['user'],
        config['password'],
        config['database']
    ):
        print("\n❌ 连接失败，请检查配置")
        return
    
    # 检查数据库
    if not check_database_exists(
        config['host'],
        config['port'],
        config['user'],
        config['password'],
        config['database']
    ):
        print("\n是否要创建数据库？(y/n): ", end='')
        choice = input().strip().lower()
        if choice == 'y':
            create_database(
                config['host'],
                config['port'],
                config['user'],
                config['password'],
                config['database']
            )
    
    # 运行完整测试
    print("\n" + "=" * 60)
    print("7. 运行完整数据库测试")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'test_database.py'],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode == 0:
            print("\n🎉 所有配置完成！数据库连接正常。")
        else:
            print("\n⚠️  部分测试失败，请检查配置")
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")

if __name__ == "__main__":
    main()
