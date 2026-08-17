# 麒麟系统内继续部署步骤

当前推荐上传的部署包：

```text
tmp/device-maintenance-backend-deploy-20260813230612.tar.gz
```

## 方式一：云桌面有文件上传按钮

1. 上传 `device-maintenance-backend-deploy-20260813230612.tar.gz` 到麒麟系统。
2. 假设上传后文件在 `~/Downloads/`，执行：

```bash
cd /opt
sudo mkdir -p device-maintenance
sudo tar -xzf ~/Downloads/device-maintenance-backend-deploy-20260813230612.tar.gz -C device-maintenance
cd device-maintenance
bash deploy/kylin_run_backend.sh
```

## 方式二：有 SSH

本机上传：

```bash
scp tmp/device-maintenance-backend-deploy-20260813230612.tar.gz 用户名@服务器IP:/tmp/
```

服务器执行：

```bash
cd /opt
sudo mkdir -p device-maintenance
sudo tar -xzf /tmp/device-maintenance-backend-deploy-20260813230612.tar.gz -C device-maintenance
cd device-maintenance
bash deploy/kylin_run_backend.sh
```

## 验证

```bash
curl http://127.0.0.1:5000/api/system/health
```

如果返回健康状态，再打开：

```text
http://127.0.0.1:5000/
```

如果是在云服务器外部访问，需要开放安全组或防火墙端口 `5000`。

## Docker 不可用时

```bash
cd /opt/device-maintenance
sudo bash deploy/deploy.sh
curl http://127.0.0.1/api/system/health
```
