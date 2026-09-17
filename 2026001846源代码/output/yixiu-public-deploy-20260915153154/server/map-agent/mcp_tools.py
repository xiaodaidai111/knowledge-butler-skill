"""MCP工具模块 - 包含配置、地图处理和工具定义"""
import json
import os
import requests
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUEST_TIMEOUT = 10

# 显式加载主后端和当前目录下的 .env，避免被其他服务的工作目录影响
load_dotenv(os.path.abspath(os.path.join(BASE_DIR, "..", "backend", ".env")))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ==========================================
# 1. 配置管理
# ==========================================

class Config:
    """配置管理类"""
    def __init__(self):
        # 服务器配置
        self.port = int(os.getenv("PORT", "8002"))
        self.host = os.getenv("HOST", "0.0.0.0")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        
        # 地图服务API配置 (高德)
        self.amap_api_key = os.getenv("AMAP_API_KEY")
        self.amap_api_url = os.getenv("AMAP_API_URL", "https://restapi.amap.com/v3")
        
        # 智能体配置：统一使用阿里云百炼/Qwen，兼容旧 DeepSeek 变量
        self.deepseek_api_key = (
            os.getenv("DASHSCOPE_API_KEY_TUANTUAN")
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("QWEN_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        self.deepseek_model_name = os.getenv("QWEN_MODEL") or os.getenv("DEEPSEEK_MODEL_NAME", "qwen-plus")
        self.deepseek_base_url = os.getenv("QWEN_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.deepseek_temperature = float(os.getenv("AI_TEMPERATURE", os.getenv("DEEPSEEK_TEMPERATURE", "0.7")))
        
        # 清理API密钥
        if self.deepseek_api_key and " #" in self.deepseek_api_key:
            self.deepseek_api_key = self.deepseek_api_key.split(" #")[0].strip()

config = Config()

# ==========================================
# 2. 地图数据处理 (Map Processor)
# ==========================================

class MapProcessor:
    """地图数据处理类 (封装高德API)"""
    
    def __init__(self):
        self.amap_api_key = config.amap_api_key
        self.amap_api_url = config.amap_api_url
    
    def geocode(self, address: str) -> Optional[Dict[str, any]]:
        """地理编码"""
        try:
            # 优先使用高德
            if self.amap_api_key:
                return self._amap_geocode(address)
            return None
        except Exception as e:
            print(f"[Error] Geocode: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, any]]:
        """反向地理编码"""
        try:
            if self.amap_api_key:
                return self._amap_reverse_geocode(lat, lon)
            return None
        except Exception:
            return None

    def search_nearby(self, location: Tuple[float, float], radius: int, keyword: Optional[str] = None) -> List[Dict[str, any]]:
        """附近搜索"""
        try:
            if self.amap_api_key:
                return self._amap_nearby_search(location, radius, keyword)
            return []
        except Exception:
            return []

    def get_directions(self, origin: Tuple[float, float], destination: Tuple[float, float], mode: str = "driving") -> Optional[Dict[str, any]]:
        """路径规划"""
        try:
            if self.amap_api_key:
                return self._amap_directions(origin, destination, mode)
            return None
        except Exception:
            return None

    # --- 高德 API 私有方法 ---
    def _amap_geocode(self, address: str) -> Dict[str, any]:
        response = requests.get(
            f"{self.amap_api_url}/geocode/geo",
            params={"address": address, "key": self.amap_api_key},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
        if data.get("status") == "1" and data.get("geocodes"):
            res = data["geocodes"][0]
            loc = res["location"].split(",")
            return {"lat": float(loc[1]), "lon": float(loc[0]), "address": res["formatted_address"], 
                    "province": res.get("province"), "city": res.get("city")}
        return None

    def _amap_reverse_geocode(self, lat: float, lon: float) -> Dict[str, any]:
        response = requests.get(
            f"{self.amap_api_url}/geocode/regeo",
            params={"location": f"{lon},{lat}", "key": self.amap_api_key, "extensions": "base"},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
        if data.get("status") == "1":
            return {"address": data["regeocode"]["formatted_address"], "lat": lat, "lon": lon}
        return None

    def _amap_nearby_search(self, location, radius, keyword):
        params = {
            "location": f"{location[1]},{location[0]}",
            "radius": radius,
            "key": self.amap_api_key,
            "extensions": "all",
            "offset": 10,
            "page": 1,
            "sortrule": "distance",
        }
        if keyword:
            params["keywords"] = keyword
        debug_params = dict(params)
        if debug_params.get("key"):
            debug_params["key"] = "***"
        print("[AMap] place/around params:", json.dumps(debug_params, ensure_ascii=False))
        data = requests.get(
            f"{self.amap_api_url}/place/around",
            params=params,
            timeout=REQUEST_TIMEOUT,
        ).json()
        print("[AMap] place/around raw:", json.dumps(data, ensure_ascii=False))
        if data.get("status") != "1":
            return []
        return [self._enrich_poi_detail(poi) for poi in data.get("pois", [])]

    def _amap_place_detail(self, poi_id: str) -> Optional[Dict[str, any]]:
        if not poi_id:
            return None
        response = requests.get(
            f"{self.amap_api_url}/place/detail",
            params={
                "id": poi_id,
                "key": self.amap_api_key,
                "extensions": "all",
            },
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
        print("[AMap] place/detail raw:", json.dumps(data, ensure_ascii=False))
        if data.get("status") == "1" and data.get("pois"):
            return data["pois"][0]
        return None

    def _enrich_poi_detail(self, poi: Dict[str, any]) -> Dict[str, any]:
        detail = self._amap_place_detail(str(poi.get("id") or ""))
        if not detail:
            return poi

        merged = dict(poi)
        for key, value in detail.items():
            if value in (None, "", [], {}):
                continue
            if key == "biz_ext" and isinstance(value, dict):
                base_biz_ext = merged.get("biz_ext") if isinstance(merged.get("biz_ext"), dict) else {}
                merged["biz_ext"] = {**base_biz_ext, **value}
            else:
                merged[key] = value
        return merged

    def _amap_directions(self, origin, destination, mode):
        amap_mode = {"walking": "walking", "biking": "bicycling", "transit": "transit"}.get(mode, "driving")
        url = f"{self.amap_api_url}/direction/{amap_mode}"
        params = {"origin": f"{origin[1]},{origin[0]}", "destination": f"{destination[1]},{destination[0]}", "key": self.amap_api_key}
        data = requests.get(url, params=params, timeout=REQUEST_TIMEOUT).json()
        if data.get("status") == "1" and data.get("route", {}).get("paths"):
            path = data["route"]["paths"][0]
            return {"distance": f"{path.get('distance')}米", "duration": f"{path.get('duration')}秒", "mode": amap_mode}
        return None

map_processor = MapProcessor()

# ==========================================
# 3. 工具定义 (MCP Tools)
# ==========================================

class GeocodeTool:
    """地理编码工具"""
    name = "geocode"
    description = "根据地址获取经纬度信息"
    
    def run(self, address: str) -> Dict[str, Any]:
        result = map_processor.geocode(address)
        if result:
            return result
        return {"error": "地理编码失败"}

class ReverseGeocodeTool:
    """反向地理编码工具"""
    name = "reverse_geocode"
    description = "根据经纬度获取真实地址信息"

    def run(self, lat: float, lon: float) -> Dict[str, Any]:
        result = map_processor.reverse_geocode(lat, lon)
        if result:
            return result
        return {"error": "反向地理编码失败"}

class NearbySearchTool:
    """附近搜索工具"""
    name = "search_nearby"
    description = "查找指定位置附近的地点"
    
    def run(self, lat: float, lon: float, radius: int = 5000, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        return map_processor.search_nearby((lat, lon), radius, keyword)

def get_all_tools() -> List[Any]:
    """返回所有可用工具实例"""
    return [GeocodeTool(), ReverseGeocodeTool(), NearbySearchTool()]

def get_tool(tool_name: str):
    """根据名称获取工具"""
    tools = {tool.name: tool for tool in get_all_tools()}
    return tools.get(tool_name)
