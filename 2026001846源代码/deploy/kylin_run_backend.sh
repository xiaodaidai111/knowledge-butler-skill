#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

echo "=========================================="
echo "  设备检修知识作业系统 - 麒麟后端启动"
echo "=========================================="

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[INFO] 已创建 .env，请按需修改其中的密码和 API Key。"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[WARN] 未检测到 docker。"
  echo "[WARN] 请改用非 Docker 部署：sudo bash deploy/deploy.sh"
  exit 2
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "[WARN] 未检测到 docker compose。"
  echo "[WARN] 请安装 Docker Compose，或改用：sudo bash deploy/deploy.sh"
  exit 2
fi

echo "[INFO] 启动后端和数据库容器..."
"${COMPOSE_CMD[@]}" up -d --build

echo "[INFO] 当前容器状态："
"${COMPOSE_CMD[@]}" ps

echo "[INFO] 等待后端服务启动..."
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:5000/api/system/health >/tmp/device-maintenance-health.json 2>/dev/null; then
    echo "[OK] 后端健康检查通过："
    cat /tmp/device-maintenance-health.json
    echo
    echo "[OK] 浏览器访问：http://127.0.0.1:5000/"
    exit 0
  fi
  sleep 2
done

echo "[ERROR] 后端健康检查未通过，最近日志如下："
"${COMPOSE_CMD[@]}" logs --tail=80 backend
exit 1
