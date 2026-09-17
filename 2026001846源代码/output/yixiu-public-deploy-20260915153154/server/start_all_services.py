import os
import sys
import io
import subprocess
import signal
import time
import logging
import socket
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from getpass import getpass

repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "backend"))
sys.path.insert(0, str(repo_root))

# Windows 默认控制台编码常为 gbk，输出 emoji 会导致 UnicodeEncodeError。
# 这里强制 stdout/stderr 使用 utf-8 并容错替换，避免脚本被日志打断。
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

backend_env_path = repo_root / "backend" / ".env"
if backend_env_path.exists():
    load_dotenv(backend_env_path, override=True)

from database.backend.core.db_config import get_config
from database.backend.core.db_pool import get_pool, close_pool
from database.backend.core.db_manager import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_port_available(port: int, host: str = 'localhost') -> Tuple[bool, str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                return False, f"端口 {port} 已被占用"
            return True, f"端口 {port} 可用"
    except Exception as e:
        return False, f"端口检查失败: {e}"


def kill_process_on_port(port: int) -> Tuple[bool, str]:
    """
    Kill process listening on the given TCP port (best-effort, Windows).
    Used to force-restart services after code changes.
    """
    try:
        pids = set()
        # psutil.net_connections can be slow; keep it simple and best-effort.
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr:
                continue
            if conn.laddr.port != port:
                continue
            if conn.status != psutil.CONN_LISTEN:
                continue
            if conn.pid:
                pids.add(conn.pid)

        if not pids:
            return False, f"未找到占用端口 {port} 的进程"

        killed = 0
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                killed += 1
                proc.terminate()
            except Exception:
                continue

        # Give terminate a moment, then force kill remaining.
        time.sleep(1)
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    proc.kill()
            except Exception:
                continue

        return True, f"已尝试结束端口 {port} 相关进程 (count={killed})"
    except Exception as e:
        return False, f"终止端口进程失败: {e}"


def get_process_info(pid: int) -> Optional[Dict]:
    try:
        process = psutil.Process(pid)
        return {
            'pid': pid,
            'name': process.name(),
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'status': process.status(),
            'create_time': datetime.fromtimestamp(process.create_time())
        }
    except psutil.NoSuchProcess:
        return None


def validate_api_endpoint(url: str, timeout: int = 5) -> Tuple[bool, str]:
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True, f"API端点 {url} 响应正常"
            else:
                return False, f"API端点 {url} 返回状态码: {response.status}"
    except urllib.error.URLError as e:
        return False, f"API端点 {url} 连接失败: {e}"
    except Exception as e:
        return False, f"API端点 {url} 验证失败: {e}"


class Service:
    def __init__(self, name: str, command: List[str], cwd: str,
                 check_url: Optional[str] = None, startup_delay: int = 2,
                 port: Optional[int] = None, api_endpoints: Optional[List[str]] = None,
                 max_retries: int = 3, restart_on_failure: bool = False,
                 kill_on_port_conflict: bool = False):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.check_url = check_url
        self.startup_delay = startup_delay
        self.port = port
        self.api_endpoints = api_endpoints or []
        self.max_retries = max_retries
        self.restart_on_failure = restart_on_failure
        self.kill_on_port_conflict = kill_on_port_conflict
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.status = 'stopped'
        self.restart_count = 0
        self.error_log: List[str] = []
        self.startup_time: Optional[float] = None

    def start(self) -> bool:
        if self.process and self.process.poll() is None:
            logger.warning(f"[{self.name}] 服务已在运行")
            return True

        logger.info(f"[{self.name}] 正在启动...")
        logger.info(f"  命令: {' '.join(self.command)}")
        logger.info(f"  目录: {self.cwd}")

        if self.port:
            port_available, port_msg = check_port_available(self.port)
            if not port_available:
                logger.warning(f"[{self.name}] 端口占用: {port_msg}，尝试启动时可能需要重启...")

                # If you changed code, you want to force-restart to pick up new logic.
                if self.kill_on_port_conflict:
                    killed, kill_msg = kill_process_on_port(self.port)
                    if killed:
                        logger.info(f"[{self.name}] ✅ {kill_msg}，等待端口释放后重启...")
                        time.sleep(1)
                        port_available, _ = check_port_available(self.port)
                    else:
                        logger.warning(f"[{self.name}] 端口终止失败: {kill_msg}，继续走健康检查逻辑...")

                if not port_available:
                    # 端口已占用时，不直接失败：若健康检查通过，认为服务已在外部就绪
                    if self._check_health():
                        self.status = "running"
                        self.startup_time = 0
                        logger.info(f"[{self.name}] ✅ 端口占用但健康检查通过，视为已就绪")
                        self._log_process_info()
                        return True

                    logger.error(f"[{self.name}] ❌ {port_msg}")
                    self.error_log.append(f"端口检查失败: {port_msg}")
                    return False
            else:
                logger.info(f"[{self.name}] ✅ {port_msg}")

        attempt = 0
        while attempt < self.max_retries:
            attempt += 1
            logger.info(f"[{self.name}] 启动尝试 {attempt}/{self.max_retries}")

            try:
                start_timestamp = time.time()
                self.process = subprocess.Popen(
                    self.command,
                    cwd=self.cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    shell=False
                )
                self.start_time = datetime.now()
                self.status = 'starting'

                logger.info(f"[{self.name}] 进程已启动 (PID: {self.process.pid})")

                if self.startup_delay > 0:
                    time.sleep(self.startup_delay)

                if self._check_health():
                    self.status = 'running'
                    self.startup_time = time.time() - start_timestamp
                    logger.info(f"[{self.name}] ✅ 启动成功 (耗时: {self.startup_time:.2f}秒)")
                    self._log_process_info()
                    return True
                else:
                    self.status = 'failed'
                    error_msg = f"健康检查失败 (尝试 {attempt}/{self.max_retries})"
                    logger.error(f"[{self.name}] ❌ {error_msg}")
                    self.error_log.append(error_msg)

                    if attempt < self.max_retries:
                        logger.info(f"[{self.name}] 等待 3 秒后重试...")
                        time.sleep(3)
                        self.stop()
                    else:
                        logger.error(f"[{self.name}] ❌ 达到最大重试次数")
                        return False

            except Exception as e:
                self.status = 'failed'
                error_msg = f"启动失败: {e}"
                logger.error(f"[{self.name}] ❌ {error_msg}")
                self.error_log.append(error_msg)

                if attempt < self.max_retries:
                    logger.info(f"[{self.name}] 等待 3 秒后重试...")
                    time.sleep(3)
                else:
                    logger.error(f"[{self.name}] ❌ 达到最大重试次数")
                    return False

        return False

    def _check_health(self) -> bool:
        if not self.check_url:
            return True

        try:
            import urllib.request
            import urllib.error

            for attempt in range(10):
                try:
                    req = urllib.request.Request(self.check_url)
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status == 200:
                            logger.info(f"[{self.name}] 主健康检查通过: {self.check_url}")

                            if self.api_endpoints:
                                logger.info(f"[{self.name}] 开始验证 {len(self.api_endpoints)} 个API端点...")
                                all_endpoints_ok = True
                                for endpoint in self.api_endpoints:
                                    success, msg = validate_api_endpoint(endpoint, timeout=3)
                                    if success:
                                        logger.info(f"[{self.name}] ✅ {msg}")
                                    else:
                                        logger.warning(f"[{self.name}] ⚠️ {msg}")
                                        all_endpoints_ok = False

                                if not all_endpoints_ok:
                                    logger.warning(f"[{self.name}] 部分API端点验证失败，但服务已启动")

                                return True

                            return True
                except (urllib.error.URLError, urllib.error.HTTPError, ConnectionRefusedError, TimeoutError):
                    time.sleep(0.5)

            return False
        except ImportError:
            return True

    def _log_process_info(self):
        if self.process and self.process.pid:
            process_info = get_process_info(self.process.pid)
            if process_info:
                logger.info(f"[{self.name}] 进程信息:")
                logger.info(f"  名称: {process_info['name']}")
                logger.info(f"  CPU使用率: {process_info['cpu_percent']:.1f}%")
                logger.info(f"  内存占用: {process_info['memory_mb']:.1f} MB")
                logger.info(f"  状态: {process_info['status']}")

    def stop(self) -> bool:
        if not self.process:
            logger.warning(f"[{self.name}] 进程不存在")
            return True

        if self.process.poll() is not None:
            logger.info(f"[{self.name}] 进程已停止")
            self.status = 'stopped'
            return True

        logger.info(f"[{self.name}] 正在停止...")

        try:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
                logger.info(f"[{self.name}] ✅ 已正常停止")
            except subprocess.TimeoutExpired:
                logger.warning(f"[{self.name}] 未响应，强制终止...")
                self.process.kill()
                self.process.wait()
                logger.info(f"[{self.name}] ✅ 已强制停止")

            self.status = 'stopped'
            return True

        except Exception as e:
            error_msg = f"停止失败: {e}"
            logger.error(f"[{self.name}] ❌ {error_msg}")
            self.error_log.append(error_msg)
            return False

    def restart(self) -> bool:
        logger.info(f"[{self.name}] 正在重启服务...")
        self.restart_count += 1

        if self.stop():
            time.sleep(2)
            return self.start()
        return False

    def get_error_log(self) -> List[str]:
        return self.error_log.copy()

    def clear_error_log(self):
        self.error_log.clear()

    def is_running(self) -> bool:
        if self.process:
            return self.process.poll() is None
        return self.status == "running"

    def get_uptime(self) -> Optional[float]:
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None


class ServiceManager:
    def __init__(self):
        self.services: Dict[str, Service] = {}
        self.shutdown_requested = False
        self.service_failures: Dict[str, int] = {}
        self.max_consecutive_failures = 5
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"\n接收到信号 {signum}，准备停止所有服务...")
        self.shutdown_requested = True

    def add_service(self, service: Service):
        self.services[service.name] = service

    def start_all(self) -> bool:
        logger.info("=" * 60)
        logger.info("开始启动所有服务")
        logger.info("=" * 60)

        success_count = 0

        for name, service in self.services.items():
            if service.start():
                success_count += 1
            else:
                logger.error(f"[{name}] 启动失败，继续启动其他服务...")

        logger.info("=" * 60)
        if success_count == len(self.services):
            logger.info(f"✅ 所有服务启动成功 ({success_count}/{len(self.services)})")
        elif success_count > 0:
            logger.warning(f"⚠️ 部分服务启动成功 ({success_count}/{len(self.services)})")
        else:
            logger.error(f"❌ 所有服务启动失败")
            return False

        logger.info("=" * 60)

        self._print_status()

        return success_count > 0

    def stop_all(self):
        logger.info("=" * 60)
        logger.info("开始停止所有服务")
        logger.info("=" * 60)

        for name, service in reversed(list(self.services.items())):
            service.stop()

        # 关闭数据库连接池（如果已初始化）
        try:
            close_pool()
        except Exception as e:
            logger.warning(f"关闭数据库连接池失败: {e}")

        logger.info("=" * 60)
        logger.info("所有服务已停止")
        logger.info("=" * 60)

    def monitor(self):
        logger.info("开始监控服务状态，按 Ctrl+C 停止所有服务...")
        logger.info("=" * 60)

        try:
            monitor_count = 0
            while not self.shutdown_requested:
                monitor_count += 1
                all_running = True
                failed_services = []

                for name, service in self.services.items():
                    if not service.is_running():
                        logger.error(f"[{name}] 检测到服务已停止！")
                        all_running = False
                        failed_services.append(name)

                        if service.restart_on_failure and service.restart_count < service.max_retries:
                            logger.info(f"[{name}] 尝试自动重启服务...")
                            if service.restart():
                                logger.info(f"[{name}] ✅ 服务重启成功")
                                self.service_failures[name] = 0
                            else:
                                logger.error(f"[{name}] ❌ 服务重启失败")
                                self.service_failures[name] = self.service_failures.get(name, 0) + 1
                        else:
                            self.service_failures[name] = self.service_failures.get(name, 0) + 1
                            logger.error(f"[{name}] 连续失败次数: {self.service_failures[name]}")
                    else:
                        # 健康检查：进程仍在运行，但端点不可用则按失败处理
                        if service.check_url:
                            success, msg = validate_api_endpoint(service.check_url, timeout=2)
                            if not success:
                                logger.error(f"[{name}] 健康检查失败: {msg}")
                                all_running = False
                                failed_services.append(name)
                                self.service_failures[name] = self.service_failures.get(name, 0) + 1

                                if service.restart_on_failure and service.restart_count < service.max_retries:
                                    logger.info(f"[{name}] 尝试根据健康检查失败重启服务...")
                                    if service.restart():
                                        logger.info(f"[{name}] ✅ 健康重启成功")
                                        self.service_failures[name] = 0
                                    else:
                                        logger.error(f"[{name}] ❌ 健康重启失败")
                                else:
                                    logger.error(f"[{name}] 连续失败次数: {self.service_failures[name]}")

                if failed_services:
                    for name in failed_services:
                        if self.service_failures.get(name, 0) >= self.max_consecutive_failures:
                            logger.error(f"[{name}] ❌ 达到最大连续失败次数，停止监控")
                            self.shutdown_requested = True
                            break

                if not all_running and not self.shutdown_requested:
                    logger.warning("检测到服务异常，继续监控...")

                if monitor_count % 12 == 0:
                    logger.info(f"系统运行正常，已监控 {monitor_count * 5} 秒")
                    self._print_status()
                    self._print_service_health()

                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("\n接收到中断信号")

        finally:
            self._print_error_summary()
            self.stop_all()

    def _print_service_health(self):
        print("\n" + "=" * 60)
        print("服务健康检查")
        print("=" * 60)

        for name, service in self.services.items():
            if service.is_running() and service.check_url:
                success, msg = validate_api_endpoint(service.check_url, timeout=2)
                status_icon = "✅" if success else "⚠️"
                print(f"{status_icon} {name}: {msg}")

                if service.api_endpoints:
                    for endpoint in service.api_endpoints:
                        success, msg = validate_api_endpoint(endpoint, timeout=2)
                        status_icon = "✅" if success else "⚠️"
                        print(f"  {status_icon} {endpoint}")

        print("=" * 60)

    def _print_error_summary(self):
        print("\n" + "=" * 60)
        print("错误摘要")
        print("=" * 60)

        for name, service in self.services.items():
            if service.error_log:
                print(f"\n{name}:")
                for error in service.error_log[-5:]:
                    print(f"  - {error}")
                if service.restart_count > 0:
                    print(f"  重启次数: {service.restart_count}")

        print("=" * 60)

    def _print_status(self):
        print("\n" + "=" * 60)
        print("服务状态")
        print("=" * 60)

        for name, service in self.services.items():
            status_icon = "🟢" if service.is_running() else "🔴"
            uptime = service.get_uptime()
            uptime_str = f"{uptime:.0f}秒" if uptime else "N/A"

            print(f"\n{status_icon} {name}")
            print(f"   状态: {service.status}")
            print(f"   运行时长: {uptime_str}")
            if service.startup_time:
                print(f"   启动耗时: {service.startup_time:.2f}秒")
            if service.check_url:
                print(f"   检查地址: {service.check_url}")
            if service.process:
                print(f"   进程ID: {service.process.pid}")
                process_info = get_process_info(service.process.pid)
                if process_info:
                    print(f"   CPU使用率: {process_info['cpu_percent']:.1f}%")
                    print(f"   内存占用: {process_info['memory_mb']:.1f} MB")
            if service.restart_count > 0:
                print(f"   重启次数: {service.restart_count}")

        print("\n" + "=" * 60)
        print("访问地址:")
        print("=" * 60)

        for name, service in self.services.items():
            if service.check_url and service.is_running():
                print(f"   {name}: {service.check_url}")

        print("=" * 60)
        print("服务说明:")
        print("=" * 60)
        print("   统一智能体服务: 所有智能体服务的统一入口 (端口: 5000)")
        print("   智能问答助手: 智能问答系统后端服务 (路径: /tuantuan)")
        print("   检修评估智能体: 检修评估智能体服务 (路径: /takeout)")
        print("   标准化作业服务: 标准化作业智能体服务 (路径: /health)")
        print("   检修评估智能体(独立): 独立检修评估服务 (端口: 5001)")
        # print("   标准化作业服务(独立): 标准化作业独立服务 (端口: 8000)")  # 暂时禁用
        print("=" * 60 + "\n")


def initialize_database_schema(script_dir: Path, db_config) -> bool:
    logger.info("=" * 60)
    logger.info("初始化数据库表结构")
    logger.info("=" * 60)

    sql_files = [
        ("主数据库结构", script_dir / "database" / "schema.sql"),
        ("社区模块结构", script_dir / "database" / "community_schema.sql"),
        ("地图智能体数据库", script_dir / "database" / "init.sql"),
    ]

    import pymysql

    try:
        connection = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            charset='utf8mb4',
            autocommit=True
        )
        cursor = connection.cursor()

        for desc, sql_path in sql_files:
            if not sql_path.exists():
                logger.warning(f"⚠️ {desc} SQL文件不存在: {sql_path}，跳过")
                continue

            logger.info(f"正在执行 {desc}: {sql_path.name}")
            try:
                with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                statements = []
                current = []
                for line in sql_content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith('--') or not stripped:
                        continue
                    current.append(line)
                    if stripped.endswith(';'):
                        statements.append('\n'.join(current))
                        current = []

                if current:
                    statements.append('\n'.join(current))

                for stmt in statements:
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except pymysql.err.MySQLError as e:
                            if e.args[0] == 1050:
                                pass
                            elif 'already exists' in str(e).lower():
                                pass
                            else:
                                logger.warning(f"  SQL执行警告: {e}")

                logger.info(f"✅ {desc} 执行完成")

            except Exception as e:
                logger.error(f"❌ {desc} 执行失败: {e}")

        cursor.close()
        connection.close()
        logger.info("=" * 60)
        logger.info("✅ 数据库表结构初始化完成")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"❌ 数据库表结构初始化失败: {e}")
        logger.info("=" * 60)
        return False


def initialize_database() -> bool:
    logger.info("=" * 60)
    logger.info("初始化数据库连接")
    logger.info("=" * 60)

    try:
        config = get_config()

        if not config.password:
            logger.info("未检测到数据库密码配置")
            logger.info("请输入数据库连接信息:")

            host = input("数据库主机 (默认: localhost): ").strip() or "localhost"
            port = input("数据库端口 (默认: 3306): ").strip() or "3306"
            user = input("数据库用户名 (默认: root): ").strip() or "root"
            password = getpass("数据库密码: ").strip()
            database = input("数据库名称 (默认: health_diet_db): ").strip() or "health_diet_db"

            config.host = host
            config.port = int(port)
            config.user = user
            config.password = password
            config.database = database

            logger.info(f"数据库配置已更新: {config}")

        logger.info(f"数据库配置: {config}")

        is_valid, msg = config.validate_config()
        if not is_valid:
            logger.error(f"❌ 配置验证失败: {msg}")
            logger.info("提示: 请检查数据库服务是否运行，以及配置是否正确")
            logger.info("运行 'python backend/test_database_connection.py' 进行详细测试")
            return False

        logger.info("✅ 配置验证通过")

        pool = get_pool()
        success, message = pool.test_connection()

        if not success:
            logger.error(f"❌ 数据库连接失败: {message}")
            logger.info("提示: 请检查数据库服务是否运行，以及配置是否正确")
            logger.info("运行 'python backend/test_database_connection.py' 进行详细测试")
            return False

        logger.info("✅ 数据库连接成功")

        db = get_db()
        status = db.test_connection()

        logger.info(f"连接状态: {status['message']}")

        pool_status = pool.get_pool_status()
        logger.info(f"连接池状态:")
        logger.info(f"  初始化: {'✅' if pool_status['initialized'] else '❌'}")
        logger.info(f"  连接池大小: {pool_status['config']['pool_size']}")
        logger.info(f"  自动重连: {'✅' if pool_status['config']['auto_reconnect'] else '❌'}")

        logger.info("=" * 60)
        logger.info("✅ 数据库初始化完成")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        logger.info("提示: 请检查数据库服务是否运行，以及配置是否正确")
        logger.info("运行 'python backend/test_database_connection.py' 进行详细测试")
        logger.info("=" * 60)
        return False


def wait_for_database_ready(script_dir: Path, manager: ServiceManager, max_attempts: int = 10,
                             delay_seconds: int = 5) -> bool:
    """
    数据库就绪等待（带自动重试）。
    - 不启动额外数据库进程（本项目使用外部 MySQL）
    - 成功条件：连接成功 + 执行 schema 初始化成功
    """
    logger.info("=" * 60)
    logger.info("数据库服务启动阶段（初始化/连通性检查/重试）")
    logger.info("=" * 60)

    for attempt in range(1, max_attempts + 1):
        if manager.shutdown_requested:
            logger.warning("收到停止请求，跳过数据库初始化等待")
            return False

        logger.info(f"[数据库] 初始化尝试 {attempt}/{max_attempts} ...")
        if not initialize_database():
            logger.warning(f"[数据库] 连接初始化失败（尝试 {attempt}/{max_attempts}）")
        else:
            db_config = get_config()
            if initialize_database_schema(script_dir, db_config):
                logger.info("✅ 数据库服务就绪（连接成功 + 表结构已初始化）")
                return True
            logger.warning(f"[数据库] 表结构初始化失败（尝试 {attempt}/{max_attempts}）")

        if attempt < max_attempts:
            logger.info(f"[数据库] 等待 {delay_seconds} 秒后重试...")
            time.sleep(delay_seconds)

    logger.error("❌ 数据库在规定重试次数内未就绪")
    return False


def check_dependencies() -> bool:
    logger.info("=" * 60)
    logger.info("检查系统依赖")
    logger.info("=" * 60)

    python_cmd = sys.executable
    logger.info(f"Python路径: {python_cmd}")
    logger.info(f"Python版本: {sys.version}")

    required_packages = [
        ("flask", "flask"),
        ("flask_cors", "flask_cors"),
        ("pymysql", "pymysql"),
        ("python-dotenv", "dotenv"),
        ("psutil", "psutil")
    ]

    missing_packages = []
    for package, import_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"✅ {package} 已安装")
        except ImportError:
            logger.warning(f"⚠️ {package} 未安装")
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"缺少以下依赖包: {', '.join(missing_packages)}")
        logger.info("请运行: pip install " + " ".join(missing_packages))
        logger.info("=" * 60)
        return False

    logger.info("=" * 60)
    logger.info("✅ 依赖检查完成")
    logger.info("=" * 60)
    return True


def validate_config_files(script_dir: Path) -> Tuple[bool, List[str]]:
    logger.info("=" * 60)
    logger.info("验证配置文件")
    logger.info("=" * 60)

    config_files = {
        "db_config.py": script_dir / "database" / "backend" / "core" / "db_config.py",
        "unified_app.py": script_dir / "backend" / "unified_app.py",
        "takeout-agent/app.py": script_dir / "backend" / "takeout-agent" / "app.py",
        "map-agent/main.py": script_dir / "map-agent" / "main.py",
        # "HealthManager/run.py": script_dir / "HealthManager" / "HealthManager" / "run.py",  # 暂时禁用
    }

    missing_files = []
    for name, path in config_files.items():
        if path.exists():
            logger.info(f"✅ {name}: {path}")
        else:
            logger.warning(f"❌ {name}: {path} (不存在)")
            missing_files.append(name)

    logger.info("=" * 60)

    if missing_files:
        logger.warning(f"缺少以下配置文件: {', '.join(missing_files)}")
        return False, missing_files

    logger.info("✅ 配置文件验证完成")
    return True, []


def check_service_directories(script_dir: Path) -> Tuple[bool, List[str]]:
    logger.info("=" * 60)
    logger.info("检查服务目录")
    logger.info("=" * 60)

    directories = {
        "backend": script_dir / "backend",
        "backend/takeout-agent": script_dir / "backend" / "takeout-agent",
        "map-agent": script_dir / "map-agent",
        # "HealthManager": script_dir / "HealthManager" / "HealthManager",  # 暂时禁用
        "database": script_dir / "database",
    }

    missing_dirs = []
    for name, path in directories.items():
        if path.exists():
            logger.info(f"✅ {name}: {path}")
        else:
            logger.warning(f"❌ {name}: {path} (不存在)")
            missing_dirs.append(name)

    logger.info("=" * 60)

    if missing_dirs:
        logger.warning(f"缺少以下服务目录: {', '.join(missing_dirs)}")
        return False, missing_dirs

    logger.info("✅ 所有服务目录检查完成")
    return True, []


def main():
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"

    logger.info("=" * 60)
    logger.info("系统启动流程")
    logger.info("=" * 60)

    dirs_ok, missing_dirs = check_service_directories(script_dir)
    if not dirs_ok:
        logger.error(f"❌ 服务目录检查失败，缺少: {', '.join(missing_dirs)}")
        return 1

    config_ok, missing_files = validate_config_files(script_dir)
    if not config_ok:
        logger.error(f"❌ 配置文件验证失败，缺少: {', '.join(missing_files)}")
        return 1

    if not check_dependencies():
        logger.error("❌ 依赖检查失败，无法继续启动服务")
        return 1

    manager = ServiceManager()

    python_cmd = sys.executable

    # Phase 1: 智能体服务（独立服务）
    unified_service = Service(
        name="统一智能体服务",
        command=[python_cmd, "unified_app.py"],
        cwd=str(backend_dir),
        check_url="http://localhost:5000",
        port=5000,
        api_endpoints=[
            "http://localhost:5000/tuantuan/",
            "http://localhost:5000/takeout/",
            "http://localhost:5000/health/",
        ],
        startup_delay=5,
        max_retries=3,
        restart_on_failure=True,
        kill_on_port_conflict=True
    )

    takeout_service = Service(
        name="检修评估智能体",
        command=[python_cmd, "app.py"],
        cwd=str(backend_dir / "takeout-agent"),
        check_url="http://localhost:5001/api/health",
        port=5001,
        startup_delay=5,
        max_retries=3,
        restart_on_failure=True
    )

    # map_agent_service 已禁用 - 空间智能服务
    # map_agent_service = Service(
    #     name="空间智能服务(独立)",
    #     command=[python_cmd, "-c",
    #              "import uvicorn, sys; sys.path.insert(0, '.'); "
    #              "from main import app; uvicorn.run(app, host='0.0.0.0', port=8002, log_level='warning')"],
    #     cwd=str(script_dir / "map-agent"),
    #     check_url="http://localhost:8002/openapi.json",
    #     port=8002,
    #     startup_delay=5,
    #     max_retries=3,
    #     restart_on_failure=True,
    #     kill_on_port_conflict=True
    # )

    # health_manager_service = Service(
    #     name="标准化作业服务(独立)",
    #     command=[python_cmd, "run.py"],
    #     cwd=str(script_dir / "HealthManager" / "HealthManager"),
    #     check_url="http://localhost:8000",
    #     port=8000,
    #     startup_delay=5,
    #     max_retries=3,
    #     restart_on_failure=True
    # )

    # Phase 1（启动顺序）：智能体服务
    manager.add_service(takeout_service)
    # manager.add_service(map_agent_service)  # 空间智能服务已禁用
    # manager.add_service(health_manager_service)  # 暂时禁用 HealthManager
    # Phase 2（启动顺序）：后端 API 服务
    manager.add_service(unified_service)

    logger.info("=" * 60)
    logger.info("服务启动配置")
    logger.info("=" * 60)
    logger.info("   统一智能体服务: http://localhost:5000")
    logger.info("   智能问答助手: http://localhost:5000/tuantuan")
    logger.info("   检修评估智能体: http://localhost:5000/takeout")
    logger.info("   标准化作业服务: http://localhost:5000/health")
    logger.info("   检修评估智能体(独立): http://localhost:5001")
    # logger.info("   标准化作业服务(独立): http://localhost:8000")  # 暂时禁用
    logger.info("=" * 60)
    logger.info("启动参数:")
    logger.info("   端口检查: ✅ 启用")
    logger.info("   API端点验证: ✅ 启用")
    logger.info("   自动重启: ✅ 启用 (最多3次)")
    logger.info("   性能监控: ✅ 启用")
    logger.info("   错误日志: ✅ 启用")
    logger.info("   数据库自动初始化: ✅ 启用（启动后重试）")
    logger.info("=" * 60)
    logger.info("")

    if manager.start_all():
        # Phase 3（启动顺序）：数据库服务（初始化/就绪）
        db_ready = wait_for_database_ready(script_dir, manager, max_attempts=10, delay_seconds=5)

        if not db_ready:
            logger.error("❌ 数据库就绪失败，停止所有服务")
            manager.stop_all()
            return 1

        # 最终就绪检查：所有服务端点可访问（数据库已就绪）
        logger.info("=" * 60)
        logger.info("最终就绪检查（等待所有组件可用）")
        logger.info("=" * 60)

        system_ready = True
        for name, service in manager.services.items():
            if not service.is_running():
                system_ready = False
                logger.error(f"[就绪检查] {name} 进程未运行")
                continue
            if service.check_url:
                ok, msg = validate_api_endpoint(service.check_url, timeout=2)
                if not ok:
                    system_ready = False
                    logger.error(f"[就绪检查] {name} 健康检查失败: {msg}")

                if service.api_endpoints and system_ready:
                    for endpoint in service.api_endpoints:
                        ep_ok, ep_msg = validate_api_endpoint(endpoint, timeout=2)
                        if not ep_ok:
                            system_ready = False
                            logger.error(f"[就绪检查] {name} API端点失败: {endpoint} ({ep_msg})")
                            break

        if system_ready:
            logger.info("✅ 系统就绪：所有核心组件已启动并通过健康检查")
        else:
            logger.warning("⚠️ 系统部分就绪：仍有组件未通过健康检查，将由监控器继续重试/重启")

        manager.monitor()
        return 0
    else:
        manager.stop_all()
        return 1


if __name__ == "__main__":
    sys.exit(main())
