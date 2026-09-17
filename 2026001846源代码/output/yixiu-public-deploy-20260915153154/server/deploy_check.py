#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署前检查脚本
用于验证服务器环境是否满足部署要求
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_status(item, status, message=""):
    icon = "✅" if status else "❌"
    print(f"  {icon} {item}")
    if message:
        print(f"      {message}")

def check_python():
    print_header("检查 Python 环境")

    # Python 版本
    version = sys.version_info
    version_ok = version.major >= 3 and version.minor >= 8
    print_status(
        f"Python 版本: {version.major}.{version.minor}.{version.micro}",
        version_ok,
        "需要 Python 3.8+" if not version_ok else ""
    )

    # pip
    pip_ok = shutil.which("pip") or shutil.which("pip3")
    print_status("pip 已安装", bool(pip_ok))

    return version_ok

def check_mysql():
    print_header("检查 MySQL 环境")

    # MySQL 客户端
    mysql_client = shutil.which("mysql")
    print_status("MySQL 客户端", bool(mysql_client))

    # 检查 MySQL 服务
    try:
        result = subprocess.run(
            ["mysql", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_status("MySQL 服务", True, result.stdout.strip())
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print_status("MySQL 服务", False, "请安装 MySQL 5.7+")
    return False

def check_directories():
    print_header("检查项目目录")

    base_dir = Path(__file__).parent
    required_dirs = {
        "backend": base_dir / "backend",
        "database": base_dir / "database",
        "map-agent": base_dir / "map-agent",
        "routes": base_dir / "backend" / "routes",
    }

    all_ok = True
    for name, path in required_dirs.items():
        exists = path.exists()
        print_status(f"{name}: {path}", exists)
        if not exists:
            all_ok = False

    return all_ok

def check_env_file():
    print_header("检查环境配置")

    env_file = Path(__file__).parent / "backend" / ".env"
    env_example = Path(__file__).parent / "backend" / ".env.example"

    if env_file.exists():
        print_status(".env 文件", True, str(env_file))

        # 检查关键配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = {
            "DATABASE_HOST": "DATABASE_HOST" in content,
            "DATABASE_PASSWORD": "DATABASE_PASSWORD" in content,
            "DASHSCOPE_API_KEY": "DASHSCOPE_API_KEY" in content,
        }

        for key, exists in checks.items():
            print_status(f"配置项 {key}", exists)

        # 检查是否使用加密密码
        if "ENC:" in content:
            print_status("数据库密码", False, "使用了加密密码，需要解密或修改为明文")
            return False

        return all(checks.values())
    else:
        print_status(".env 文件", False, "需要从 .env.example 复制并配置")
        if env_example.exists():
            print(f"      运行: cp {env_example} {env_file}")
        return False

def check_python_packages():
    print_header("检查 Python 依赖")

    required_packages = [
        "flask",
        "flask_cors",
        "pymysql",
        "dotenv",
        "jwt",
        "requests",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_status(package, True)
        except ImportError:
            print_status(package, False, "未安装")
            missing.append(package)

    if missing:
        print(f"\n  ⚠️  缺少依赖包，运行: pip install {' '.join(missing)}")
        return False

    return True

def check_ports():
    print_header("检查端口可用性")

    import socket

    ports = {
        5000: "统一智能体服务",
        5001: "检修评估智能体",
        8002: "空间智能服务",
    }

    all_available = True
    for port, name in ports.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    print_status(f"端口 {port} ({name})", False, "已被占用")
                    all_available = False
                else:
                    print_status(f"端口 {port} ({name})", True, "可用")
        except Exception as e:
            print_status(f"端口 {port} ({name})", True, "可用")

    return all_available

def generate_report():
    print_header("部署检查报告")

    checks = {
        "Python 环境": check_python(),
        "MySQL 数据库": check_mysql(),
        "项目目录": check_directories(),
        "环境配置": check_env_file(),
        "Python 依赖": check_python_packages(),
        "端口可用性": check_ports(),
    }

    print("\n" + "=" * 60)
    print(" 检查结果汇总")
    print("=" * 60)

    all_ok = True
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
        if not status:
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print(" ✅ 所有检查通过！可以开始部署。")
    else:
        print(" ⚠️  存在问题，请修复后重新检查。")
    print("=" * 60 + "\n")

    return all_ok

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" 设备检修知识作业系统 - 部署前检查")
    print("=" * 60)

    success = generate_report()

    if not success:
        print("\n💡 提示：")
        print("  1. 安装 Python 依赖: pip install -r backend/requirements.txt")
        print("  2. 安装 MySQL: sudo apt install mysql-server")
        print("  3. 配置环境变量: cp backend/.env.example backend/.env")
        print("  4. 初始化数据库: mysql -u root -p < database/schema.sql")
        print()

    sys.exit(0 if success else 1)
