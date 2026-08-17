# 龙芯 / 银河麒麟 Docker 部署说明

当前项目已移除 H5 / uni-app 前端，部署目标是后端 API 服务。

## 一、服务器准备

在龙芯 / 银河麒麟服务器上确认：

```bash
uname -m
cat /etc/os-release
docker --version
docker compose version
```

如果 `uname -m` 显示 `loongarch64`，说明是龙芯架构。

## 二、上传项目

在本机项目根目录打包：

```bash
tar -czf device-maintenance-backend.tar.gz \
  Dockerfile \
  docker-compose.yml \
  .dockerignore \
  .env.example \
  server \
  deploy
```

上传到服务器：

```bash
scp device-maintenance-backend.tar.gz user@服务器IP:/opt/
```

在服务器上解压：

```bash
cd /opt
sudo mkdir -p device-maintenance
sudo tar -xzf device-maintenance-backend.tar.gz -C device-maintenance
cd device-maintenance
```

## 三、配置环境变量

```bash
cp .env.example .env
vim .env
```

至少修改：

```env
MYSQL_ROOT_PASSWORD=你的数据库密码
SECRET_KEY=随机字符串
JWT_SECRET_KEY=随机字符串
DASHSCOPE_API_KEY=你的百炼 API Key
AMAP_API_KEY=你的高德 Key
```

## 四、启动

推荐直接执行一键脚本：

```bash
bash deploy/kylin_run_backend.sh
```

也可以手动执行：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f backend
```

验证：

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/api/system/health
```

如果云服务器安全组开放了 5000 端口，也可以从浏览器访问：

```text
http://服务器IP:5000/
http://服务器IP:5000/api/system/health
```

## 五、龙芯注意事项

龙芯 `loongarch64` 上 Docker 镜像和 Python 包可能存在架构兼容问题，尤其是：

- `opencv-python`
- `ultralytics`
- `lightrag-hku`
- `numpy`

如果 `docker compose up -d --build` 在安装依赖时报错，建议改用项目里的非 Docker 部署脚本：

```bash
sudo bash deploy/deploy.sh
```

非 Docker 方式会使用系统 Python 环境创建虚拟环境，更容易针对龙芯源单独处理依赖。
