#!/bin/bash
# ============================================================
# 设备检修知识作业系统 - 部署脚本
# 适用环境：LoongArch + 银河麒麟高级服务器 V10/V11
# ============================================================

set -e  # 遇到错误立即退出

# 配置变量
APP_NAME="device-maintenance"
APP_DIR="/opt/${APP_NAME}"
BACKEND_DIR="${APP_DIR}/backend"
UPLOADS_DIR="${BACKEND_DIR}/uploads"
VENV_DIR="${BACKEND_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
NGINX_CONF="/etc/nginx/conf.d/${APP_NAME}.conf"
PORT=5000

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================
# 1. 系统环境检查
# ============================================================
check_system() {
    print_info "检查系统环境..."

    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_info "操作系统: $PRETTY_NAME"

        if [[ "$ID" != "kylin" ]] && [[ "$ID_LIKE" != *"kylin"* ]]; then
            print_warn "当前系统不是银河麒麟，可能需要调整部分配置"
        fi
    fi

    # 检查架构
    ARCH=$(uname -m)
    print_info "系统架构: $ARCH"

    if [[ "$ARCH" != "loongarch64" ]]; then
        print_warn "当前架构不是 LoongArch，可能需要调整部分配置"
    fi

    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_info "Python 版本: $PYTHON_VERSION"
    else
        print_error "未找到 Python3，请先安装"
        exit 1
    fi

    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        print_warn "未找到 pip3，尝试安装..."
        sudo yum install -y python3-pip
    fi
}

# ============================================================
# 2. 安装系统依赖
# ============================================================
install_dependencies() {
    print_info "安装系统依赖..."

    sudo yum install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        nginx \
        wget \
        curl \
        git

    print_info "系统依赖安装完成"
}

# ============================================================
# 3. 创建目录结构
# ============================================================
create_directories() {
    print_info "创建目录结构..."

    sudo mkdir -p ${APP_DIR}
    sudo mkdir -p ${BACKEND_DIR}
    sudo mkdir -p ${UPLOADS_DIR}

    # 设置权限
    sudo chown -R $USER:$USER ${APP_DIR}
    chmod 755 ${APP_DIR}

    print_info "目录结构创建完成"
}

# ============================================================
# 4. 部署后端代码
# ============================================================
deploy_backend() {
    print_info "部署后端代码..."

    # 复制后端代码
    if [ -d "server/backend" ]; then
        cp -r server/backend/* ${BACKEND_DIR}/
        print_info "后端代码复制完成"
    else
        print_error "未找到 server/backend 目录"
        exit 1
    fi

    # 创建虚拟环境
    print_info "创建 Python 虚拟环境..."
    cd ${BACKEND_DIR}
    python3 -m venv venv
    source venv/bin/activate

    # 安装依赖
    print_info "安装 Python 依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # 安装核心依赖
        pip install flask flask-cors python-dotenv gunicorn
        pip install requests pillow
    fi

    # 创建 requirements.txt（如果不存在）
    if [ ! -f "requirements.txt" ]; then
        pip freeze > requirements.txt
        print_info "已生成 requirements.txt"
    fi

    deactivate

    print_info "后端部署完成"
}

# ============================================================
# 5. 配置环境变量
# ============================================================
setup_environment() {
    print_info "配置环境变量..."

    ENV_FILE="${BACKEND_DIR}/.env"

    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << 'EOF'
# Flask 配置
FLASK_APP=unified_app.py
FLASK_ENV=production
SECRET_KEY=change-this-to-random-string

# 数据库配置
DATABASE_URL=sqlite:///database.db

# AI 服务配置（根据实际情况填写）
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.deepseek.com

# 上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
EOF
        print_warn "已创建 .env 文件，请根据实际情况修改配置"
    else
        print_info ".env 文件已存在，跳过创建"
    fi
}

# ============================================================
# 6. 配置 Systemd 服务
# ============================================================
setup_systemd() {
    print_info "配置 Systemd 服务..."

    sudo tee ${SERVICE_FILE} > /dev/null << EOF
[Unit]
Description=Device Maintenance Backend Service
After=network.target

[Service]
Type=notify
User=$(whoami)
Group=$(whoami)
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:${PORT} \
    --timeout 120 \
    --access-logfile /var/log/${APP_NAME}/access.log \
    --error-logfile /var/log/${APP_NAME}/error.log \
    unified_app:create_unified_app()
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # 创建日志目录
    sudo mkdir -p /var/log/${APP_NAME}
    sudo chown $USER:$USER /var/log/${APP_NAME}

    # 重载 systemd
    sudo systemctl daemon-reload

    print_info "Systemd 服务配置完成"
}

# ============================================================
# 7. 配置 Nginx
# ============================================================
setup_nginx() {
    print_info "配置 Nginx..."

    sudo tee ${NGINX_CONF} > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;  # 修改为实际域名或 IP

    # 后端服务入口：本项目已移除 H5 / uni-app 前端，根路径直接转发到 Flask。
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
        client_max_body_size 16M;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（AI 调用可能较慢）
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;

        # 允许大文件上传
        client_max_body_size 16M;
    }

    # Cook Agent API
    location /cook-agent/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 上传文件目录
    location /uploads/ {
        alias /opt/device-maintenance/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # WebSocket 支持（语音功能）
    location /ws/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }

    # 日志配置
    access_log /var/log/nginx/device-maintenance-access.log;
    error_log /var/log/nginx/device-maintenance-error.log;
}
EOF

    # 测试 Nginx 配置
    sudo nginx -t

    print_info "Nginx 配置完成"
}

# ============================================================
# 8. 启动服务
# ============================================================
start_services() {
    print_info "启动服务..."

    # 启动后端服务
    sudo systemctl enable ${APP_NAME}
    sudo systemctl start ${APP_NAME}

    # 重载 Nginx
    sudo systemctl reload nginx

    print_info "服务启动完成"
}

# ============================================================
# 9. 验证部署
# ============================================================
verify_deployment() {
    print_info "验证部署..."

    # 等待服务启动
    sleep 3

    # 检查后端服务
    if sudo systemctl is-active --quiet ${APP_NAME}; then
        print_info "✓ 后端服务运行正常"
    else
        print_error "✗ 后端服务启动失败"
        sudo systemctl status ${APP_NAME}
        return 1
    fi

    # 检查 Nginx
    if sudo systemctl is-active --quiet nginx; then
        print_info "✓ Nginx 运行正常"
    else
        print_error "✗ Nginx 启动失败"
        sudo systemctl status nginx
        return 1
    fi

    # 测试 API
    if curl -s http://localhost/api/health > /dev/null 2>&1; then
        print_info "✓ API 接口可访问"
    else
        print_warn "⚠ API 接口暂时无法访问，请检查日志"
    fi

    # 获取服务器 IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo ""
    echo "=========================================="
    echo "  部署完成！"
    echo "=========================================="
    echo ""
    echo "  访问地址: http://${SERVER_IP}"
    echo "  后端 API: http://${SERVER_IP}/api/"
    echo ""
    echo "  服务管理命令:"
    echo "    启动: sudo systemctl start ${APP_NAME}"
    echo "    停止: sudo systemctl stop ${APP_NAME}"
    echo "    重启: sudo systemctl restart ${APP_NAME}"
    echo "    状态: sudo systemctl status ${APP_NAME}"
    echo "    日志: sudo journalctl -u ${APP_NAME} -f"
    echo ""
    echo "  Nginx 日志:"
    echo "    访问日志: /var/log/nginx/device-maintenance-access.log"
    echo "    错误日志: /var/log/nginx/device-maintenance-error.log"
    echo ""
    echo "=========================================="
}

# ============================================================
# 主流程
# ============================================================
main() {
    echo ""
    echo "=========================================="
    echo "  设备检修知识作业系统 - 部署脚本"
    echo "  适用环境: LoongArch + 银河麒麟 V10/V11"
    echo "=========================================="
    echo ""

    # 执行部署步骤
    check_system
    install_dependencies
    create_directories
    deploy_backend
    setup_environment
    setup_systemd
    setup_nginx
    start_services
    verify_deployment
}

# 执行主流程
main "$@"
