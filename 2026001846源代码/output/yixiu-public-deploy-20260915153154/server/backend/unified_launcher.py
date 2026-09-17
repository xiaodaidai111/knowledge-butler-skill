"""
统一智能体启动器
整合慧识外卖智能体和团团系统（Cook-Agent）
提供统一的启动、配置管理和错误处理机制
"""

import os
import sys
import logging
import threading
import time
import signal
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_launcher.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AgentConfig:
    """智能体配置管理类"""

    def __init__(self, config_file: str = '.env'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """从环境变量和配置文件加载配置"""
        config = {}

        # 从环境变量加载
        config.update({
            # 团团系统配置
            'TUANTUAN_HOST': os.getenv('TUANTUAN_HOST', '0.0.0.0'),
            'TUANTUAN_PORT': int(os.getenv('TUANTUAN_PORT', 5000)),
            'TUANTUAN_DEBUG': os.getenv('TUANTUAN_DEBUG', 'True').lower() == 'true',

            # 慧识外卖配置
            'TAKEOUT_HOST': os.getenv('TAKEOUT_HOST', '0.0.0.0'),
            'TAKEOUT_PORT': int(os.getenv('TAKEOUT_PORT', 5001)),
            'TAKEOUT_DEBUG': os.getenv('TAKEOUT_DEBUG', 'True').lower() == 'true',

            # API配置
            'QWEN_API_KEY': os.getenv('QWEN_API_KEY', ''),
            'QWEN_API_URL': os.getenv('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'),
            'QWEN_MODEL': os.getenv('QWEN_MODEL', 'qwen-turbo'),

            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'OPENAI_BASE_URL': os.getenv('OPENAI_BASE_URL', ''),
            'OPENAI_CHAT_MODEL': os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini'),
            'OPENAI_VISION_MODEL': os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini'),

            'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY', ''),
            'AMAP_API_KEY': os.getenv('AMAP_API_KEY', ''),

            # 数据库配置
            'DATABASE_HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'DATABASE_PORT': int(os.getenv('DATABASE_PORT', 3306)),
            'DATABASE_USER': os.getenv('DATABASE_USER', 'root'),
            'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'DATABASE_NAME': os.getenv('DATABASE_NAME', 'health_diet_db'),

            # JWT配置
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'),
            'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)),

            # 启动配置
            'ENABLE_TUANTUAN': os.getenv('ENABLE_TUANTUAN', 'True').lower() == 'true',
            'ENABLE_TAKEOUT': os.getenv('ENABLE_TAKEOUT', 'True').lower() == 'true',
        })

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value

    def validate(self) -> bool:
        """验证配置是否有效"""
        errors = []

        # 验证端口
        if not (1 <= self.config['TUANTUAN_PORT'] <= 65535):
            errors.append('TUANTUAN_PORT 必须在 1-65535 之间')
        if not (1 <= self.config['TAKEOUT_PORT'] <= 65535):
            errors.append('TAKEOUT_PORT 必须在 1-65535 之间')

        # 验证端口冲突
        if self.config['TUANTUAN_PORT'] == self.config['TAKEOUT_PORT']:
            errors.append('TUANTUAN_PORT 和 TAKEOUT_PORT 不能相同')

        if errors:
            for error in errors:
                logger.error(f"配置错误: {error}")
            return False

        return True


class AgentProcess:
    """智能体进程管理类"""

    def __init__(self, name: str, script_path: str, host: str, port: int, debug: bool):
        self.name = name
        self.script_path = script_path
        self.host = host
        self.port = port
        self.debug = debug
        self.process: Optional[threading.Thread] = None
        self.running = False
        self.start_time: Optional[datetime] = None

    def start(self):
        """启动智能体进程"""
        if self.running:
            logger.warning(f"{self.name} 已经在运行中")
            return False

        logger.info(f"正在启动 {self.name}...")
        logger.info(f"  脚本路径: {self.script_path}")
        logger.info(f"  监听地址: {self.host}:{self.port}")

        try:
            # 设置环境变量
            os.environ['FLASK_RUN_HOST'] = self.host
            os.environ['FLASK_RUN_PORT'] = str(self.port)
            os.environ['FLASK_DEBUG'] = str(self.debug)

            # 在新线程中启动Flask应用
            def run_agent():
                try:
                    # 切换到脚本所在目录
                    script_dir = os.path.dirname(os.path.abspath(self.script_path))
                    os.chdir(script_dir)

                    # 将脚本目录添加到Python路径，确保模块能够正确导入
                    if script_dir not in sys.path:
                        sys.path.insert(0, script_dir)

                    # 动态导入并运行
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("agent_app", self.script_path)
                    agent_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(agent_module)

                    # 如果模块中有app对象，运行它
                    if hasattr(agent_module, 'app'):
                        agent_module.app.run(
                            host=self.host,
                            port=self.port,
                            debug=self.debug,
                            use_reloader=False
                        )
                    else:
                        logger.error(f"{self.name} 模块中没有找到Flask应用对象")

                except Exception as e:
                    logger.error(f"{self.name} 运行错误: {str(e)}", exc_info=True)
                    self.running = False

            self.process = threading.Thread(target=run_agent, daemon=True)
            self.process.start()
            self.running = True
            self.start_time = datetime.now()

            logger.info(f"{self.name} 启动成功")
            return True

        except Exception as e:
            logger.error(f"{self.name} 启动失败: {str(e)}", exc_info=True)
            return False

    def stop(self):
        """停止智能体进程"""
        if not self.running:
            logger.warning(f"{self.name} 未在运行")
            return False

        logger.info(f"正在停止 {self.name}...")
        self.running = False

        if self.process:
            self.process.join(timeout=5)
            if self.process.is_alive():
                logger.warning(f"{self.name} 进程未能在5秒内停止")

        logger.info(f"{self.name} 已停止")
        return True

    def is_running(self) -> bool:
        """检查进程是否在运行"""
        return self.running and self.process and self.process.is_alive()

    def get_uptime(self) -> Optional[float]:
        """获取运行时长（秒）"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None


class UnifiedLauncher:
    """统一启动器类"""

    def __init__(self):
        self.config = AgentConfig()
        self.agents: Dict[str, AgentProcess] = {}
        self.shutdown_event = threading.Event()

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"接收到信号 {signum}，准备关闭所有智能体...")
        self.shutdown_event.set()

    def initialize_agents(self):
        """初始化所有智能体"""
        logger.info("正在初始化智能体...")

        backend_dir = Path(__file__).parent

        # 初始化团团系统（Cook-Agent）
        if self.config.get('ENABLE_TUANTUAN'):
            tuantuan_script = backend_dir / 'app_refactored.py'
            if tuantuan_script.exists():
                self.agents['tuantuan'] = AgentProcess(
                    name='团团系统（Cook-Agent）',
                    script_path=str(tuantuan_script),
                    host=self.config.get('TUANTUAN_HOST'),
                    port=self.config.get('TUANTUAN_PORT'),
                    debug=self.config.get('TUANTUAN_DEBUG')
                )
                logger.info("团团系统（Cook-Agent）初始化完成")
            else:
                logger.error(f"团团系统脚本不存在: {tuantuan_script}")

        # 初始化慧识外卖智能体
        if self.config.get('ENABLE_TAKEOUT'):
            takeout_script = backend_dir / 'takeout-agent' / 'app.py'
            if takeout_script.exists():
                self.agents['takeout'] = AgentProcess(
                    name='慧识外卖智能体',
                    script_path=str(takeout_script),
                    host=self.config.get('TAKEOUT_HOST'),
                    port=self.config.get('TAKEOUT_PORT'),
                    debug=self.config.get('TAKEOUT_DEBUG')
                )
                logger.info("慧识外卖智能体初始化完成")
            else:
                logger.error(f"慧识外卖脚本不存在: {takeout_script}")

        if not self.agents:
            logger.error("没有可用的智能体")
            return False

        return True

    def start_agents(self):
        """启动所有智能体"""
        logger.info("正在启动所有智能体...")

        success_count = 0
        for agent_name, agent in self.agents.items():
            if agent.start():
                success_count += 1
                # 等待一段时间确保服务启动
                time.sleep(2)
            else:
                logger.error(f"{agent.name} 启动失败")

        if success_count == 0:
            logger.error("所有智能体启动失败")
            return False
        elif success_count < len(self.agents):
            logger.warning(f"部分智能体启动失败 ({success_count}/{len(self.agents)})")
        else:
            logger.info(f"所有智能体启动成功 ({success_count}/{len(self.agents)})")

        return True

    def stop_agents(self):
        """停止所有智能体"""
        logger.info("正在停止所有智能体...")

        for agent_name, agent in self.agents.items():
            agent.stop()

        logger.info("所有智能体已停止")

    def monitor_agents(self):
        """监控智能体状态"""
        logger.info("开始监控智能体状态...")

        while not self.shutdown_event.is_set():
            for agent_name, agent in self.agents.items():
                if not agent.is_running():
                    logger.error(f"{agent.name} 已停止运行！")
                    self.shutdown_event.set()
                    break

            self.shutdown_event.wait(10)  # 每10秒检查一次

    def print_status(self):
        """打印智能体状态"""
        print("\n" + "=" * 60)
        print("智能体状态")
        print("=" * 60)

        for agent_name, agent in self.agents.items():
            status = "运行中" if agent.is_running() else "已停止"
            uptime = agent.get_uptime()
            uptime_str = f"{uptime:.0f}秒" if uptime else "N/A"

            print(f"\n{agent.name}")
            print(f"  状态: {status}")
            print(f"  地址: {agent.host}:{agent.port}")
            print(f"  运行时长: {uptime_str}")

        print("\n" + "=" * 60)
        print("访问地址:")
        print("=" * 60)

        if 'tuantuan' in self.agents:
            print(f"团团系统（Cook-Agent）: http://{self.config.get('TUANTUAN_HOST')}:{self.config.get('TUANTUAN_PORT')}")
        if 'takeout' in self.agents:
            print(f"慧识外卖智能体: http://{self.config.get('TAKEOUT_HOST')}:{self.config.get('TAKEOUT_PORT')}")

        print("=" * 60 + "\n")

    def run(self):
        """运行启动器"""
        print("\n" + "=" * 60)
        print("统一智能体启动器")
        print("=" * 60)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

        # 验证配置
        if not self.config.validate():
            logger.error("配置验证失败，请检查配置")
            return False

        # 初始化智能体
        if not self.initialize_agents():
            logger.error("智能体初始化失败")
            return False

        # 启动智能体
        if not self.start_agents():
            logger.error("智能体启动失败")
            self.stop_agents()
            return False

        # 打印状态
        self.print_status()

        # 监控智能体
        try:
            self.monitor_agents()
        except KeyboardInterrupt:
            logger.info("接收到中断信号")
        finally:
            self.stop_agents()

        logger.info("启动器已关闭")
        return True


def main():
    """主函数"""
    launcher = UnifiedLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
