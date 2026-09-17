#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_ROOT="/var/www/yixiu"
NGINX_CONF="/etc/nginx/conf.d/yixiu.conf"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

echo "[1/6] Installing runtime dependencies..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y nginx curl ca-certificates
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | bash
  fi
elif command -v yum >/dev/null 2>&1; then
  yum install -y nginx curl ca-certificates
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | bash
  fi
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y nginx curl ca-certificates
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | bash
  fi
else
  echo "Unsupported Linux distribution: apt/yum/dnf not found."
  exit 1
fi

echo "[2/6] Starting Docker..."
systemctl enable docker >/dev/null 2>&1 || true
systemctl start docker

echo "[3/6] Preparing environment..."
cd "$APP_DIR"
if [ ! -f ".env" ]; then
  cat > .env <<'EOF'
MYSQL_ROOT_PASSWORD=Yixiu_2026_Strong_Password
MYSQL_DATABASE=yixiu_db
SECRET_KEY=yixiu-production-secret
JWT_SECRET_KEY=yixiu-jwt-production-secret
DASHSCOPE_API_KEY=
AMAP_API_KEY=
EOF
fi

echo "[4/6] Deploying backend containers..."
docker compose up -d --build

echo "[5/6] Deploying frontend assets..."
mkdir -p "$WEB_ROOT"
rm -rf "$WEB_ROOT"/*
cp -r "$APP_DIR/frontend/dist/"* "$WEB_ROOT/"

cat > "$NGINX_CONF" <<'EOF'
server {
    listen 80;
    server_name _;

    root /var/www/yixiu;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 180s;
    }
}
EOF

echo "[6/6] Starting Nginx..."
nginx -t
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx

echo "Done."
echo "Frontend: http://47.95.202.36/"
echo "Health:   http://47.95.202.36/api/system/health"
