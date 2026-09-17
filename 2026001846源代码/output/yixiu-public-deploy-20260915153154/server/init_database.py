#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于快速创建数据库和导入表结构
"""

import sys
import os
import subprocess
from pathlib import Path

def get_mysql_command():
    """获取 MySQL 命令"""
    mysql_cmd = shutil.which("mysql")
    if not mysql_cmd:
        print("❌ 错误: 未找到 mysql 命令")
        print("请先安装 MySQL: sudo apt install mysql-client")
        return None
    return mysql_cmd

def create_database(host, port, user, password, database):
    """创建数据库"""
    print(f"\n📦 创建数据库: {database}")

    mysql_cmd = get_mysql_command()
    if not mysql_cmd:
        return False

    # 构建命令
    cmd = [mysql_cmd]
    if host != "localhost":
        cmd.extend(["-h", host])
    if port != 3306:
        cmd.extend(["-P", str(port)])
    cmd.extend(["-u", user])

    if password:
        cmd.append(f"-p{password}")

    # 执行 SQL
    sql = f"""
    CREATE DATABASE IF NOT EXISTS {database}
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

    GRANT ALL PRIVILEGES ON {database}.* TO '{user}'@'%';
    FLUSH PRIVILEGES;
    """

    try:
        result = subprocess.run(
            cmd,
            input=sql,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✅ 数据库 {database} 创建成功")
            return True
        else:
            print(f"❌ 创建数据库失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 连接超时，请检查 MySQL 服务是否运行")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def import_schema(host, port, user, password, database, sql_file):
    """导入 SQL 文件"""
    print(f"\n📄 导入表结构: {sql_file.name}")

    mysql_cmd = get_mysql_command()
    if not mysql_cmd:
        return False

    # 构建命令
    cmd = [mysql_cmd]
    if host != "localhost":
        cmd.extend(["-h", host])
    if port != 3306:
        cmd.extend(["-P", str(port)])
    cmd.extend(["-u", user])

    if password:
        cmd.append(f"-p{password}")

    cmd.append(database)

    # 读取 SQL 文件
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        result = subprocess.run(
            cmd,
            input=sql_content,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"✅ {sql_file.name} 导入成功")
            return True
        else:
            print(f"⚠️  {sql_file.name} 导入时有警告:")
            if result.stderr:
                # 过滤掉 "already exists" 警告
                warnings = [line for line in result.stderr.split('\n')
                           if line.strip() and 'already exists' not in line.lower()]
                for warning in warnings[:5]:
                    print(f"    {warning}")
            return True  # 警告不算失败

    except subprocess.TimeoutExpired:
        print("❌ 导入超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print(" 设备检修知识作业系统 - 数据库初始化")
    print("=" * 60)

    # 默认配置
    host = os.getenv("DATABASE_HOST", "localhost")
    port = int(os.getenv("DATABASE_PORT", "3306"))
    user = os.getenv("DATABASE_USER", "root")
    password = os.getenv("DATABASE_PASSWORD", "")
    database = os.getenv("DATABASE_NAME", "health_diet_db")

    # 如果命令行参数提供
    if len(sys.argv) >= 2:
        database = sys.argv[1]
    if len(sys.argv) >= 3:
        user = sys.argv[2]
    if len(sys.argv) >= 4:
        password = sys.argv[3]

    print(f"\n📋 配置信息:")
    print(f"   主机: {host}:{port}")
    print(f"   用户: {user}")
    print(f"   数据库: {database}")

    # SQL 文件列表
    base_dir = Path(__file__).parent
    sql_files = [
        base_dir / "database" / "schema.sql",
        base_dir / "database" / "community_schema.sql",
        base_dir / "database" / "equipment_maintenance_schema.sql",
        base_dir / "database" / "init.sql",
    ]

    # 检查 SQL 文件
    print("\n📁 检查 SQL 文件:")
    for sql_file in sql_files:
        if sql_file.exists():
            print(f"   ✅ {sql_file.name}")
        else:
            print(f"   ❌ {sql_file.name} (不存在)")

    # 确认
    print("\n" + "-" * 60)
    confirm = input("是否继续初始化数据库? (y/N): ").strip().lower()

    if confirm not in ['y', 'yes', '是']:
        print("\n❌ 已取消")
        return

    # 创建数据库
    if not create_database(host, port, user, password, database):
        print("\n❌ 数据库创建失败，终止初始化")
        return

    # 导入表结构
    print("\n" + "-" * 60)
    print("开始导入表结构...")

    success_count = 0
    for sql_file in sql_files:
        if sql_file.exists():
            if import_schema(host, port, user, password, database, sql_file):
                success_count += 1

    # 汇总
    print("\n" + "=" * 60)
    print(" 初始化完成")
    print("=" * 60)
    print(f"\n  成功导入: {success_count}/{len(sql_files)} 个文件")
    print(f"  数据库: {database}")

    # 测试连接
    print("\n🔍 测试数据库连接...")
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

        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"✅ 连接成功，共 {len(tables)} 个表:")
        for table in tables[:10]:
            print(f"   - {table[0]}")
        if len(tables) > 10:
            print(f"   ... 还有 {len(tables) - 10} 个表")

        cursor.close()
        conn.close()

    except ImportError:
        print("⚠️  未安装 pymysql，跳过连接测试")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

    print("\n" + "=" * 60)
    print(" 初始化完成！")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import shutil
    main()
