@echo off
REM 设备检修知识作业系统 - Windows 快速启动脚本

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  设备检修知识作业系统 - Windows 快速启动
echo ============================================================
echo.

REM 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    echo    请安装 Python 3.8+ 并添加到系统 PATH
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i

REM 检查 pip
echo.
echo [2/4] 检查 pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip 未安装
    pause
    exit /b 1
)
echo ✅ pip 已安装

REM 检查 MySQL
echo.
echo [3/4] 检查 MySQL...
mysql --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  MySQL 客户端未安装或未添加到 PATH
    echo    请确保 MySQL 已安装并添加到系统 PATH
    set /p CONTINUE="是否继续? (Y/N): "
    if /i not "!CONTINUE!"=="Y" exit /b 1
) else (
    for /f "tokens=*" %%i in ('mysql --version') do echo ✅ %%i
)

REM 检查 .env 文件
echo.
echo [4/4] 检查配置文件...

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend

if not exist "%BACKEND_DIR%\.env" (
    if exist "%BACKEND_DIR%\.env.example" (
        echo ⚠️  .env 文件不存在，正在从模板创建...
        copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
        echo ✅ 已创建 .env 文件
        echo.
        echo ⚠️  请编辑 %BACKEND_DIR%\.env 配置以下内容：
        echo    - DATABASE_HOST (数据库主机)
        echo    - DATABASE_PORT (数据库端口)
        echo    - DATABASE_USER (数据库用户)
        echo    - DATABASE_PASSWORD (数据库密码)
        echo    - DATABASE_NAME (数据库名称)
        echo    - DASHSCOPE_API_KEY (阿里云百炼 API Key)
        echo.
        pause
    ) else (
        echo ❌ .env.example 文件不存在
        pause
        exit /b 1
    )
) else (
    echo ✅ .env 文件已存在
)

REM 创建虚拟环境
echo.
echo ============================================================
echo  配置 Python 环境
echo ============================================================

if not exist "%BACKEND_DIR%\venv" (
    echo.
    echo 正在创建虚拟环境...
    cd /d "%BACKEND_DIR%"
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境并安装依赖
echo.
echo 正在激活虚拟环境并安装依赖...
call "%BACKEND_DIR%\venv\Scripts\activate.bat"

echo.
echo 正在安装 Python 依赖...
cd /d "%BACKEND_DIR%"
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️  部分依赖安装失败，继续尝试...
)

echo.
echo ✅ Python 依赖安装完成

REM 数据库初始化
echo.
echo ============================================================
echo  数据库配置
echo ============================================================

set /p SETUP_DB="是否需要初始化数据库? (Y/N): "
if /i "!SETUP_DB!"=="Y" (
    echo.
    set /p DB_HOST="MySQL 主机 [localhost]: "
    if "!DB_HOST!"=="" set DB_HOST=localhost

    set /p DB_PORT="MySQL 端口 [3306]: "
    if "!DB_PORT!"=="" set DB_PORT=3306

    set /p DB_USER="MySQL 用户 [root]: "
    if "!DB_USER!"=="" set DB_USER=root

    set /p DB_PASS="MySQL 密码: "

    set /p DB_NAME="数据库名 [health_diet_db]: "
    if "!DB_NAME!"=="" set DB_NAME=health_diet_db

    echo.
    echo 正在创建数据库...
    mysql -h !DB_HOST! -P !DB_PORT! -u !DB_USER! -p!DB_PASS! -e "CREATE DATABASE IF NOT EXISTS !DB_NAME! CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    if errorlevel 1 (
        echo ❌ 数据库创建失败
        pause
        exit /b 1
    )
    echo ✅ 数据库创建成功

    echo.
    echo 正在导入表结构...
    cd /d "%SCRIPT_DIR%database"

    if exist "schema.sql" (
        mysql -h !DB_HOST! -P !DB_PORT! -u !DB_USER! -p!DB_PASS! !DB_NAME! < schema.sql
        echo ✅ schema.sql 导入完成
    )

    if exist "community_schema.sql" (
        mysql -h !DB_HOST! -P !DB_PORT! -u !DB_USER! -p!DB_PASS! !DB_NAME! < community_schema.sql
        echo ✅ community_schema.sql 导入完成
    )

    if exist "equipment_maintenance_schema.sql" (
        mysql -h !DB_HOST! -P !DB_PORT! -u !DB_USER! -p!DB_PASS! !DB_NAME! < equipment_maintenance_schema.sql
        echo ✅ equipment_maintenance_schema.sql 导入完成
    )

    if exist "init.sql" (
        mysql -h !DB_HOST! -P !DB_PORT! -u !DB_USER! -p!DB_PASS! !DB_NAME! < init.sql
        echo ✅ init.sql 导入完成
    )

    echo.
    echo ✅ 数据库初始化完成

    REM 更新 .env 配置
    echo.
    echo 正在更新 .env 配置...
    cd /d "%BACKEND_DIR%"

    powershell -Command "(Get-Content .env) -replace '^DATABASE_HOST=.*', 'DATABASE_HOST=!DB_HOST!' | Set-Content .env"
    powershell -Command "(Get-Content .env) -replace '^DATABASE_PORT=.*', 'DATABASE_PORT=!DB_PORT!' | Set-Content .env"
    powershell -Command "(Get-Content .env) -replace '^DATABASE_USER=.*', 'DATABASE_USER=!DB_USER!' | Set-Content .env"
    powershell -Command "(Get-Content .env) -replace '^DATABASE_PASSWORD=.*', 'DATABASE_PASSWORD=!DB_PASS!' | Set-Content .env"
    powershell -Command "(Get-Content .env) -replace '^DATABASE_NAME=.*', 'DATABASE_NAME=!DB_NAME!' | Set-Content .env"

    echo ✅ .env 配置已更新
)

REM 启动后端服务
echo.
echo ============================================================
echo  启动后端服务
echo ============================================================

set /p START_BE="是否启动后端服务? (Y/N): "
if /i "!START_BE!"=="Y" (
    echo.
    echo 正在启动后端服务...
    cd /d "%BACKEND_DIR%"
    call "%BACKEND_DIR%\venv\Scripts\activate.bat"

    echo.
    echo 📌 后端服务启动中，请稍候...
    echo    访问地址: http://localhost:5000
    echo    按 Ctrl+C 停止服务
    echo.

    python unified_app.py
)

echo.
echo ============================================================
echo  部署完成
echo ============================================================
echo.
echo  如需重新启动，请运行:
echo    cd %BACKEND_DIR%
echo    venv\Scripts\activate
echo    python unified_app.py
echo.
pause
