# 🚀 快速部署清单

## ✅ 已完成的修改

### 1. 修复 HealthManager 目录缺失问题 ✅

**修改文件**: `start_all_services.py`

**修改内容**:
- ✅ 注释掉了 `config_files` 中的 HealthManager 检查 (第 818 行)
- ✅ 注释掉了 `directories` 中的 HealthManager 检查 (第 848 行)
- ✅ 注释掉了 `health_manager_service` 服务定义 (第 941-950 行)
- ✅ 注释掉了服务启动和日志输出 (第 955, 579, 968 行)

**影响**: 
- 标准化作业功能仍可通过统一后端的 `/health` 路由访问
- 独立的 HealthManager 服务暂时禁用，不影响核心功能

### 2. 创建的辅助脚本 ✅

#### (1) 部署检查脚本 `deploy_check.py`
- 检查 Python 环境
- 检查 MySQL 数据库
- 检查项目目录结构
- 检查环境配置文件
- 检查 Python 依赖
- 检查端口可用性

**使用方法**:
```bash
cd server
python deploy_check.py
```

#### (2) 数据库初始化脚本 `init_database.py`
- 自动创建数据库
- 导入所有表结构
- 测试数据库连接

**使用方法**:
```bash
cd server
python init_database.py
# 或指定参数
python init_database.py health_diet_db root your_password
```

#### (3) 快速启动脚本

**Windows**:
```bash
quick_start.bat
```

**Linux/Mac**:
```bash
chmod +x quick_start.sh
sudo ./quick_start.sh
```

**功能**:
- 自动检查系统环境
- 自动配置数据库
- 自动安装 Python 依赖
- 自动启动后端服务

---

## 📋 部署步骤 (5 分钟快速部署)

### Windows 用户

```bash
# 1. 进入 server 目录
cd "D:/竞赛/软件杯/2026001846源代码/server"

# 2. 双击运行快速启动脚本
quick_start.bat

# 3. 按照提示操作：
#    - 配置数据库连接
#    - 等待自动安装依赖
#    - 启动后端服务

# 4. 访问测试
# 浏览器打开: http://localhost:5000
```

### Linux/Mac 用户

```bash
# 1. 进入 server 目录
cd /path/to/2026001846源代码/server

# 2. 添加执行权限
chmod +x quick_start.sh

# 3. 运行快速启动脚本
sudo ./quick_start.sh

# 4. 按照提示操作

# 5. 访问测试
curl http://localhost:5000/
```

---

## 🔧 手动部署 (高级用户)

### 步骤 1: 环境准备

```bash
# 安装系统依赖
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-client

# 或 CentOS
sudo yum install python3 python3-pip mysql
```

### 步骤 2: 配置数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE health_diet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON health_diet_db.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 导入表结构
cd database
mysql -u root -p health_diet_db < schema.sql
mysql -u root -p health_diet_db < community_schema.sql
mysql -u root -p health_diet_db < equipment_maintenance_schema.sql
mysql -u root -p health_diet_db < init.sql
```

### 步骤 3: 配置后端

```bash
cd backend

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**必须配置**:
```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_actual_password
DATABASE_NAME=health_diet_db
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 步骤 4: 创建虚拟环境并安装依赖

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 5: 启动服务

```bash
# 确保虚拟环境已激活
python unified_app.py
```

**验证**:
```bash
# 新终端
curl http://localhost:5000/
```

---

## 🧪 验证部署

### 1. 运行部署检查

```bash
cd server
python deploy_check.py
```

**预期输出**:
```
✅ Python 版本: 3.10.x
✅ pip 已安装
✅ MySQL 客户端
✅ 项目目录完整
✅ .env 文件已配置
✅ Python 依赖已安装
✅ 端口可用
✅ 所有检查通过！可以开始部署。
```

### 2. 测试 API 接口

```bash
# 系统根路径
curl http://localhost:5000/

# 健康检查
curl http://localhost:5000/api/system/health

# 用户注册测试
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "password": "test123", "name": "测试用户"}'
```

**预期结果**:
- ✅ 根路径返回系统信息
- ✅ 健康检查返回 `{"status": "healthy"}`
- ✅ 注册返回成功消息

### 3. 浏览器访问

- **主页**: http://localhost:5000/
- **API 文档**: http://localhost:5000/api/

---

## 🔑 获取 API Key

### 阿里云百炼 (必需)

1. 访问: https://dashscope.console.aliyun.com/
2. 注册/登录阿里云账号
3. 开通百炼服务
4. 创建 API Key
5. 复制 Key 到 `.env` 文件

**费用**: 新用户有免费额度，足够测试使用

### 高德地图 (可选，地图功能需要)

1. 访问: https://lbs.amap.com/
2. 注册/登录账号
3. 创建应用，获取 Key
4. 复制 Key 到 `.env` 文件

**费用**: 个人开发者免费额度充足

---

## 🐛 常见问题速查

### ❌ 后端启动失败

**症状**: `python unified_app.py` 报错

**快速解决**:
```bash
# 1. 检查虚拟环境
source venv/bin/activate

# 2. 检查依赖
pip list | grep flask

# 3. 检查 .env 配置
cat .env | grep DATABASE

# 4. 查看详细错误
python unified_app.py 2>&1 | tee error.log
```

### ❌ 数据库连接失败

**症状**: `pymysql.err.OperationalError`

**快速解决**:
```bash
# 1. 检查 MySQL 运行状态
sudo systemctl status mysql

# 2. 测试数据库连接
mysql -u root -p

# 3. 检查密码是否正确
# 编辑 .env，确保密码明文（不要使用 ENC: 加密格式）
```

### ❌ 缺少 Python 包

**症状**: `ModuleNotFoundError`

**快速解决**:
```bash
# 1. 确保虚拟环境激活
source venv/bin/activate

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 如果失败，逐个安装
pip install flask pymysql dashscope
```

### ❌ 端口被占用

**症状**: `Address already in use`

**快速解决**:
```bash
# Linux/Mac
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

## 📊 部署验证清单

### 环境检查
- [ ] Python 3.8+ 已安装
- [ ] pip 已安装
- [ ] MySQL 5.7+ 已安装
- [ ] MySQL 服务正在运行

### 配置文件
- [ ] `.env` 文件已创建
- [ ] 数据库连接信息正确
- [ ] API Key 已配置
- [ ] 密码使用明文格式

### 数据库
- [ ] 数据库已创建
- [ ] 表结构已导入
- [ ] 用户权限已配置
- [ ] 连接测试通过

### 后端服务
- [ ] 虚拟环境已创建
- [ ] Python 依赖已安装
- [ ] 服务成功启动
- [ ] API 接口可访问

### 功能测试
- [ ] 首页可访问
- [ ] 用户注册正常
- [ ] 用户登录正常
- [ ] API 接口响应正常

---

## 🎯 快速验证命令

```bash
# 1. 检查环境
python deploy_check.py

# 2. 启动服务
cd backend
source venv/bin/activate
python unified_app.py &

# 3. 测试接口
curl http://localhost:5000/
curl http://localhost:5000/api/system/health

# 4. 测试数据库
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "password": "test123", "name": "测试"}'

# 5. 查看日志
tail -f /var/log/syslog | grep maintenance
```

---

## 📞 需要帮助？

### 查看日志
```bash
# 后端日志
sudo journalctl -u maintenance-backend -f

# 实时日志
python unified_app.py 2>&1 | tee server.log
```

### 运行诊断
```bash
# 部署检查
python deploy_check.py

# 数据库测试
python init_database.py
```

### 常见文件位置
- **后端配置**: `backend/.env`
- **数据库脚本**: `database/*.sql`
- **启动日志**: 终端输出
- **部署报告**: `../PROJECT_CHECK_REPORT.md`

---

## ✨ 部署成功标志

当看到以下输出时，表示部署成功：

```bash
$ python unified_app.py
 * Serving Flask app 'unified_app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://localhost:5000
 * Press CTRL+C to quit

$ curl http://localhost:5000/
{
  "name": "智学多智能体 - 设备检修知识检索与标准作业系统",
  "version": "1.0.0",
  "status": "running"
}
```

**🎉 恭喜！系统已成功部署并运行！**

---

**快速开始**: 运行 `quick_start.bat` (Windows) 或 `./quick_start.sh` (Linux)
**详细文档**: 查看 `README.md`
**问题反馈**: 查看 `PROJECT_CHECK_REPORT.md`

---

**最后更新**: 2026-06-16
**版本**: v1.0
