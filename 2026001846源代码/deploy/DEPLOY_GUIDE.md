# 设备检修知识作业系统 - 后端部署指南

本项目已移除 H5 / uni-app 前端部分，部署目标调整为后端 API 服务。

## 部署架构

```text
服务器
├── Nginx：80/443 入口，反向代理到 Flask
├── Flask 后端：127.0.0.1:5000
├── 数据库：按 .env 配置连接 MySQL 或现有数据库
└── uploads：后端上传文件目录
```

## 需要准备的文件

```text
deploy-package/
├── deploy/
│   ├── deploy.sh
│   └── DEPLOY_GUIDE.md
└── server/
    └── backend/
```

打包示例：

```bash
tar -czf deploy-package.tar.gz deploy/ server/backend/
```

## 一键部署

```bash
tar -xzf deploy-package.tar.gz
cd deploy-package
chmod +x deploy/deploy.sh
sudo bash deploy/deploy.sh
```

脚本会完成：

1. 检查系统环境
2. 安装 Python、Nginx 等依赖
3. 创建 `/opt/device-maintenance/backend`
4. 部署后端代码
5. 创建 Python 虚拟环境并安装依赖
6. 生成 `.env` 模板
7. 配置 systemd 后端服务
8. 配置 Nginx 反向代理
9. 启动并验证服务

## 环境变量

部署后检查并修改：

```bash
/opt/device-maintenance/backend/.env
```

常用配置：

```env
FLASK_APP=unified_app.py
FLASK_ENV=production
SECRET_KEY=change-this-to-random-string

DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=health_diet_db

DASHSCOPE_API_KEY=your_dashscope_api_key
AMAP_API_KEY=your_amap_api_key

UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

## 验证

```bash
sudo systemctl status device-maintenance
sudo systemctl status nginx
curl http://localhost/api/system/health
curl http://localhost/
```

如果后端正常，`/api/system/health` 会返回健康状态，`/` 会返回 Flask 服务信息。

## 常用维护命令

```bash
sudo systemctl start device-maintenance
sudo systemctl stop device-maintenance
sudo systemctl restart device-maintenance
sudo journalctl -u device-maintenance -f
sudo nginx -t
sudo systemctl reload nginx
```

## 更新部署

```bash
sudo systemctl stop device-maintenance
cp -r server/backend/* /opt/device-maintenance/backend/
cd /opt/device-maintenance/backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl start device-maintenance
sudo systemctl reload nginx
```
