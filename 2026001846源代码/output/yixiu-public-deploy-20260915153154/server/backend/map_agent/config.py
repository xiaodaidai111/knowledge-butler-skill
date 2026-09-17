"""配置管理模块"""
import os
from typing import Optional, Dict

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取backend目录的绝对路径
backend_dir = os.path.dirname(current_dir)
# 构建.env文件的绝对路径
env_file_path = os.path.join(backend_dir, ".env")


class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置"""
        # 加载环境变量
        self._load_env()
        
        # 服务器配置
        self.port: int = int(os.getenv("PORT", "8000"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.debug: bool = os.getenv("DEBUG", "True").lower() == "true"
        
        # 地图服务API配置
        self.openstreetmap_api_url: str = os.getenv("OPENSTREETMAP_API_URL", "https://nominatim.openstreetmap.org")
        self.amap_api_key: Optional[str] = os.getenv("AMAP_API_KEY")
        self.amap_api_url: str = os.getenv("AMAP_API_URL", "https://restapi.amap.com/v3")
        
        # 智能体配置
        # 统一 AI 配置，兼容旧 DeepSeek 变量
        self.ai_provider: str = os.getenv("AI_PROVIDER", "qwen")
        self.ai_api_key: Optional[str] = (
            os.getenv("DASHSCOPE_API_KEY_TUANTUAN")
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("QWEN_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        self.ai_model_name: str = os.getenv("QWEN_MODEL") or os.getenv("DEEPSEEK_MODEL_NAME", "qwen-plus")
        self.ai_base_url: str = os.getenv("QWEN_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.ai_temperature: float = float(os.getenv("AI_TEMPERATURE", os.getenv("DEEPSEEK_TEMPERATURE", "0.7")))
        self.deepseek_api_key: Optional[str] = self.ai_api_key
        self.deepseek_model_name: str = self.ai_model_name
        self.deepseek_temperature: float = self.ai_temperature
        
        # 智能体参数
        self.agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
        self.agent_verbose: bool = os.getenv("AGENT_VERBOSE", "True").lower() == "true"
        
        # 对话管理配置
        self.conversation_max_turns: int = int(os.getenv("CONVERSATION_MAX_TURNS", "20"))
        self.conversation_timeout: int = int(os.getenv("CONVERSATION_TIMEOUT", "3600"))
        
        # 地图处理配置
        self.map_default_zoom: int = int(os.getenv("MAP_DEFAULT_ZOOM", "15"))
        self.map_search_radius: int = int(os.getenv("MAP_SEARCH_RADIUS", "5000"))
        
        # 日志配置
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    def _load_env(self):
        """加载.env文件中的环境变量"""
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value
    
    def get_map_api_config(self) -> Dict[str, any]:
        """获取地图API配置
        
        Returns:
            dict: 地图API配置
        """
        return {
            "openstreetmap_api_url": self.openstreetmap_api_url,
            "amap_api_key": self.amap_api_key,
            "amap_api_url": self.amap_api_url
        }
    
    def get_agent_config(self) -> Dict[str, any]:
        """获取智能体配置
        
        Returns:
            dict: 智能体配置
        """
        return {
            "deepseek_api_key": self.deepseek_api_key,
            "deepseek_model_name": self.deepseek_model_name,
            "deepseek_temperature": self.deepseek_temperature,
            "ai_provider": self.ai_provider,
            "ai_model_name": self.ai_model_name,
            "ai_base_url": self.ai_base_url,
            "agent_max_iterations": self.agent_max_iterations,
            "agent_verbose": self.agent_verbose
        }
    
    def get_conversation_config(self) -> Dict[str, any]:
        """获取对话管理配置
        
        Returns:
            dict: 对话管理配置
        """
        return {
            "conversation_max_turns": self.conversation_max_turns,
            "conversation_timeout": self.conversation_timeout
        }
    
    def get_map_config(self) -> Dict[str, any]:
        """获取地图处理配置
        
        Returns:
            dict: 地图处理配置
        """
        return {
            "map_default_zoom": self.map_default_zoom,
            "map_search_radius": self.map_search_radius
        }
    
    def get_server_config(self) -> Dict[str, any]:
        """获取服务器配置
        
        Returns:
            dict: 服务器配置
        """
        return {
            "port": self.port,
            "host": self.host,
            "debug": self.debug
        }
    
    def get_log_config(self) -> Dict[str, any]:
        """获取日志配置
        
        Returns:
            dict: 日志配置
        """
        return {
            "log_level": self.log_level,
            "log_format": self.log_format
        }


# 创建全局配置实例
config = Config()
