"""地图数据处理模块"""
import requests
from typing import Dict, List, Optional, Tuple
from geopy.geocoders import Nominatim

from .config import config


class MapProcessor:
    """地图数据处理类"""
    
    def __init__(self):
        """初始化地图处理器"""
        self.openstreetmap_api_url = config.openstreetmap_api_url
        self.amap_api_key = config.amap_api_key
        self.amap_api_url = config.amap_api_url
        self.default_zoom = config.map_default_zoom
        self.search_radius = config.map_search_radius
        
        # 初始化地理编码器
        self.geolocator = Nominatim(user_agent="map_agent")
    
    def geocode(self, address: str) -> Optional[Dict[str, any]]:
        """地理编码：根据地址获取经纬度
        
        Args:
            address: 地址字符串
            
        Returns:
            包含经纬度和其他信息的字典，失败返回默认位置
        """
        # 尝试使用高德地图API
        if self.amap_api_key:
            try:
                result = self._amap_geocode(address)
                if result:
                    return result
                print("高德地图地理编码失败，尝试使用OpenStreetMap")
            except Exception as e:
                print(f"高德地图API调用失败: {e}")
        
        # 尝试使用OpenStreetMap
        try:
            result = self._openstreetmap_geocode(address)
            if result:
                return result
            print("OpenStreetMap地理编码失败")
        except Exception as e:
            print(f"OpenStreetMap API调用失败: {e}")
        
        # 所有服务都失败，返回默认位置（北京市中心）
        print("所有地理编码服务都失败，返回默认位置")
        return {
            "lat": 39.9042,
            "lon": 116.4074,
            "address": "北京市中心",
            "province": "北京市",
            "city": "北京市",
            "district": "东城区",
            "level": "城市"
        }
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, any]]:
        """反向地理编码：根据经纬度获取地址
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            包含地址和其他信息的字典，失败返回None
        """
        # 尝试使用高德地图API
        if self.amap_api_key:
            try:
                result = self._amap_reverse_geocode(lat, lon)
                if result:
                    return result
                print("高德地图反向地理编码失败，尝试使用OpenStreetMap")
            except Exception as e:
                print(f"高德地图API调用失败: {e}")
        
        # 尝试使用OpenStreetMap
        try:
            result = self._openstreetmap_reverse_geocode(lat, lon)
            if result:
                return result
            print("OpenStreetMap反向地理编码失败")
        except Exception as e:
            print(f"OpenStreetMap API调用失败: {e}")
        
        # 所有服务都失败
        return None
    
    def get_directions(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                      mode: str = "driving") -> Optional[Dict[str, any]]:
        """路径规划：计算两点之间的最优路径
        
        Args:
            origin: 起点经纬度 (lat, lon)
            destination: 终点经纬度 (lat, lon)
            mode: 交通方式，如driving, walking, biking, transit
            
        Returns:
            包含路径信息的字典，失败返回None
        """
        try:
            # 尝试使用高德地图API
            if self.amap_api_key:
                return self._amap_directions(origin, destination, mode)
            
            # 不使用模拟数据，直接返回None
            return None
        
        except Exception as e:
            print(f"路径规划失败: {e}")
            # 不返回模拟数据，直接返回None
            return None
    
    def search_nearby(self, location: Tuple[float, float], radius: int, 
                     keyword: Optional[str] = None) -> Optional[List[Dict[str, any]]]:
        """附近地点查询：查找指定位置附近的地点
        
        Args:
            location: 中心点经纬度 (lat, lon)
            radius: 搜索半径（米）
            keyword: 搜索关键词
            
        Returns:
            包含附近地点信息的列表，失败返回None
        """
        try:
            # 尝试使用高德地图API
            if self.amap_api_key:
                return self._amap_nearby_search(location, radius, keyword)
            
            # 不使用模拟数据，直接返回None
            return None
        
        except Exception as e:
            print(f"附近地点查询失败: {e}")
            # 不返回模拟数据，直接返回None
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, any]]:
        """获取地点详情：根据地点ID获取详细信息，包括评价
        
        Args:
            place_id: 地点ID
            
        Returns:
            包含地点详细信息的字典，失败返回None
        """
        try:
            # 尝试使用高德地图API
            if self.amap_api_key:
                return self._amap_poi_details(place_id)
            
            # 不使用模拟数据，直接返回None
            return None
        
        except Exception as e:
            print(f"获取地点详情失败: {e}")
            # 不返回模拟数据，直接返回None
            return None
    
    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点之间的距离（使用Haversine公式）
        
        Args:
            point1: 第一个点的经纬度 (lat, lon)
            point2: 第二个点的经纬度 (lat, lon)
            
        Returns:
            两点之间的距离（米）
        """
        import math
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # 地球半径（米）
        R = 6371000
        
        # 转换为弧度
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        # Haversine公式
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def parse_map_data(self, data: Dict[str, any]) -> Dict[str, any]:
        """解析地图数据
        
        Args:
            data: 原始地图数据
            
        Returns:
            解析后的地图数据
        """
        # 根据不同的地图服务API返回格式进行解析
        # 这里提供一个通用的解析方法
        parsed_data = {}
        
        # 示例解析逻辑
        if "results" in data:
            parsed_data["results"] = data["results"]
        elif "features" in data:
            parsed_data["results"] = data["features"]
        
        return parsed_data
    
    # 私有方法：高德地图API调用
    def _amap_geocode(self, address: str) -> Dict[str, any]:
        """使用高德地图API进行地理编码"""
        url = f"{self.amap_api_url}/geocode/geo"
        params = {
            "address": address,
            "key": self.amap_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "1":
                result = data["geocodes"][0]
                location = result["location"].split(",")
                return {
                    "lat": float(location[1]),
                    "lon": float(location[0]),
                    "address": result["formatted_address"],
                    "province": result.get("province"),
                    "city": result.get("city"),
                    "district": result.get("district"),
                    "adcode": result.get("adcode"),
                    "level": result.get("level")
                }
            else:
                print(f"高德地图API返回错误: {data.get('info', '未知错误')} (错误码: {data.get('infocode', '未知')})")
        except Exception as e:
            print(f"高德地图API请求异常: {e}")
        
        return None
    
    def _amap_reverse_geocode(self, lat: float, lon: float) -> Dict[str, any]:
        """使用高德地图API进行反向地理编码"""
        url = f"{self.amap_api_url}/geocode/regeo"
        params = {
            "location": f"{lon},{lat}",
            "key": self.amap_api_key,
            "extensions": "base"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1":
            result = data["regeocode"]
            return {
                "address": result["formatted_address"],
                "lat": lat,
                "lon": lon,
                "province": result.get("addressComponent", {}).get("province"),
                "city": result.get("addressComponent", {}).get("city"),
                "district": result.get("addressComponent", {}).get("district"),
                "township": result.get("addressComponent", {}).get("township"),
                "neighborhood": result.get("addressComponent", {}).get("neighborhood", {}).get("name"),
                "building": result.get("addressComponent", {}).get("building", {}).get("name")
            }
        
        return None
    
    def _amap_directions(self, origin: Tuple[float, float], 
                       destination: Tuple[float, float], 
                       mode: str = "driving") -> Dict[str, any]:
        """使用高德地图API进行路径规划"""
        # 转换交通方式
        amap_mode = "driving"
        if mode == "walking":
            amap_mode = "walking"
        elif mode == "biking":
            amap_mode = "bicycling"
        elif mode == "transit":
            amap_mode = "transit"
        
        url = f"{self.amap_api_url}/direction/{amap_mode}"
        params = {
            "origin": f"{origin[1]},{origin[0]}",
            "destination": f"{destination[1]},{destination[0]}",
            "key": self.amap_api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1":
            route = data["route"]
            path = route["paths"][0]
            
            steps = []
            if "steps" in path:
                for step in path["steps"]:
                    steps.append({
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": {"text": f"{step.get('distance', 0)}米"},
                        "duration": {"text": f"{step.get('duration', 0)}秒"}
                    })
            
            return {
                "distance": f"{path.get('distance', 0)}米",
                "duration": f"{path.get('duration', 0)}秒",
                "start_address": route.get("origin"),
                "end_address": route.get("destination"),
                "steps": steps,
                "mode": amap_mode
            }
        
        return None
    
    def _amap_nearby_search(self, location: Tuple[float, float], 
                          radius: int, 
                          keyword: Optional[str]) -> List[Dict[str, any]]:
        """使用高德地图API进行附近地点查询"""
        url = f"{self.amap_api_url}/place/around"
        params = {
            "location": f"{location[1]},{location[0]}",
            "radius": radius,
            "key": self.amap_api_key,
            "extensions": "base"
        }
        
        if keyword:
            params["keywords"] = keyword
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1":
            pois = data["pois"]
            # 为每个POI添加详细信息（包括评价）
            for poi in pois:
                if poi.get("id"):
                    details = self._amap_poi_details(poi["id"])
                    if details:
                        poi.update(details)
            return pois
        
        return []
    
    def _amap_poi_details(self, poi_id: str) -> Dict[str, any]:
        """使用高德地图API获取POI详情（包括评价）"""
        url = f"{self.amap_api_url}/place/detail"
        params = {
            "id": poi_id,
            "key": self.amap_api_key,
            "extensions": "all"  # 获取所有详细信息，包括评价
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "1":
            detail = data["pois"][0]
            # 提取有用的信息
            details = {
                "name": detail.get("name"),
                "address": detail.get("address"),
                "tel": detail.get("tel"),
                "rating": detail.get("biz_ext", {}).get("rating", "暂无评分"),
                "cost": detail.get("biz_ext", {}).get("cost", "暂无人均消费"),
                "open_time": detail.get("biz_ext", {}).get("open_time", "暂无营业时间"),
                "photos": detail.get("photos", []),
                "reviews": detail.get("reviews", []),
                "detail_url": detail.get("detail_url"),
                "type": detail.get("type"),
                "distance": detail.get("distance")
            }
            return details
        
        return {}
    

    
    # 私有方法：OpenStreetMap API调用
    def _openstreetmap_geocode(self, address: str) -> Dict[str, any]:
        """使用OpenStreetMap进行地理编码"""
        location = self.geolocator.geocode(address)
        
        if location:
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "address": location.address,
                "raw": location.raw
            }
        
        return None
    
    def _openstreetmap_reverse_geocode(self, lat: float, lon: float) -> Dict[str, any]:
        """使用OpenStreetMap进行反向地理编码"""
        location = self.geolocator.reverse((lat, lon))
        
        if location:
            return {
                "address": location.address,
                "lat": lat,
                "lon": lon,
                "raw": location.raw
            }
        
        return None
    


