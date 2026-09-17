#!/bin/bash
# 设备检修知识作业系统 - 快速启动脚本
# 适用于 Ubuntu/Debian 系统

set -e  # 遇到错误立即退出

echo "============================================================"
echo " 设备检修知识作业系统 - 快速启动"
echo "============================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "📌 $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查系统依赖
check_system_deps() {
    print_info "检查系统依赖..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        print_info "安装命令: sudo apt install python3 python3-pip python3-venv"
        return 1
    fi
    print_success "Python3 已安装: $(python3 --version)"

    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装"
        return 1
    fi
    print_success "pip3 已安装"

    # 检查 MySQL
    if ! command -v mysql &> /dev/null; then
        print_warning "MySQL 客户端未安装"
        print_info "安装命令: sudo apt install mysql-client"
        return 1
    fi
    print_success "MySQL 客户端已安装"

    return 0
}

# 安装系统依赖
install_system_deps() {
    print_info "安装系统依赖..."

    apt-get update

    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        mysql-client \
        curl \
        wget

    print_success "系统依赖安装完成"
}

# 配置数据库
setup_database() {
    print_info "配置数据库..."

    read -p "MySQL 主机 [localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-localhost}

    read -p "MySQL 端口 [3306]: " DB_PORT
    DB_PORT=${DB_PORT:-3306}

    read -p "MySQL 用户 [root]: " DB_USER
    DB_USER=${DB_USER:-root}

    read -sp "MySQL 密码: " DB_PASS
    echo ""

    read -p "数据库名 [health_diet_db]: " DB_NAME
    DB_NAME=${DB_NAME:-health_diet_db}

    # 创建数据库
    print_info "创建数据库..."

    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
EOF

    if [ $? -eq 0 ]; then
        print_success "数据库创建成功"
    else
        print_error "数据库创建失败"
        return 1
    fi

    # 导入表结构
    print_info "导入表结构..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SQL_FILES=(
        "$SCRIPT_DIR/database/schema.sql"
        "$SCRIPT_DIR/database/community_schema.sql"
        "$SCRIPT_DIR/database/equipment_maintenance_schema.sql"
        "$SCRIPT_DIR/database/init.sql"
    )

    for sql_file in "${SQL_FILES[@]}"; do
        if [ -f "$sql_file" ]; then
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$sql_file"
            print_success "导入: $(basename $sql_file)"
        else
            print_warning "文件不存在: $(basename $sql_file)"
        fi
    done

    # 保存数据库配置
    export DATABASE_HOST="$DB_HOST"
    export DATABASE_PORT="$DB_PORT"
    export DATABASE_USER="$DB_USER"
    export DATABASE_PASSWORD="$DB_PASS"
    export DATABASE_NAME="$DB_NAME"

    return 0
}

# 配置后端
setup_backend() {
    print_info "配置后端..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKEND_DIR="$SCRIPT_DIR/backend"

    # 检查 .env 文件
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        if [ -f "$BACKEND_DIR/.env.example" ]; then
            cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
            print_success "创建 .env 文件"
        else
            print_error ".env.example 文件不存在"
            return 1
        fi
    fi

    # 更新 .env 配置
    sed -i "s|^DATABASE_HOST=.*|DATABASE_HOST=$DATABASE_HOST|" "$BACKEND_DIR/.env"
    sed -i "s|^DATABASE_PORT=.*|DATABASE_PORT=$DATABASE_PORT|" "$BACKEND_DIR/.env"
    sed -i "s|^DATABASE_USER=.*|DATABASE_USER=$DATABASE_USER|" "$BACKEND_DIR/.env"
    sed -i "s|^DATABASE_PASSWORD=.*|DATABASE_PASSWORD=$DATABASE_PASSWORD|" "$BACKEND_DIR/.env"
    sed -i "s|^DATABASE_NAME=.*|DATABASE_NAME=$DATABASE_NAME|" "$BACKEND_DIR/.env"

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_KEY=$(openssl rand -hex 32)

    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" "$BACKEND_DIR/.env"
    sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_KEY|" "$BACKEND_DIR/.env"

    print_success "后端配置完成"

    # 创建虚拟环境
    print_info "创建 Python 虚拟环境..."

    python3 -m venv "$BACKEND_DIR/venv"
    source "$BACKEND_DIR/venv/bin/activate"

    # 安装依赖
    print_info "安装 Python 依赖..."
    pip install --upgrade pip
    pip install -r "$BACKEND_DIR/requirements.txt"

    deactivate

    print_success "Python 依赖安装完成"

    return 0
}

# 启动后端服务
start_backend() {
    print_info "启动后端服务..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKEND_DIR="$SCRIPT_DIR/backend"

    # 检查 .env 文件
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        print_error ".env 文件不存在"
        return 1
    fi

    # 启动服务
    cd "$BACKEND_DIR"
    source venv/bin/activate

    print_info "启动 Flask 应用..."
    python unified_app.py &

    BACKEND_PID=$!
    print_success "后端服务已启动 (PID: $BACKEND_PID)"

    # 等待服务启动
    print_info "等待服务就绪..."
    sleep 5

    # 测试连接
    if curl -s http://localhost:5000/ > /dev/null; then
        print_success "后端服务运行正常"
    else
        print_warning "后端服务可能未就绪，请检查日志"
    fi

    return 0
}

# 主函数
main() {
    echo ""
    print_info "欢迎使用设备检修知识作业系统快速启动脚本"
    echo ""

    # 步骤 1: 检查系统依赖
    if ! check_system_deps; then
        read -p "是否安装系统依赖? (y/N): " INSTALL_DEPS
        if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
            install_system_deps
        else
            print_error "缺少系统依赖，无法继续"
            exit 1
        fi
    fi

    # 步骤 2: 配置数据库
    read -p "是否配置数据库? (y/N): " SETUP_DB
    if [[ $SETUP_DB =~ ^[Yy]$ ]]; then
        setup_database
        if [ $? -ne 0 ]; then
            print_error "数据库配置失败"
            exit 1
        fi
    fi

    # 步骤 3: 配置后端
    read -p "是否配置后端? (y/N): " SETUP_BE
    if [[ $SETUP_BE =~ ^[Yy]$ ]]; then
        setup_backend
        if [ $? -ne 0 ]; then
            print_error "后端配置失败"
            exit 1
        fi
    fi

    # 步骤 4: 启动服务
    read -p "是否启动后端服务? (y/N): " START_BE
    if [[ $START_BE =~ ^[Yy]$ ]]; then
        start_backend
    fi

    echo ""
    echo "============================================================"
    print_success "部署完成！"
    echo "============================================================"
    echo ""
    print_info "访问地址: http://localhost:5000"
    print_info "查看日志: tail -f /var/log/syslog"
    echo ""
}

# 运行主函数
main "$@"
