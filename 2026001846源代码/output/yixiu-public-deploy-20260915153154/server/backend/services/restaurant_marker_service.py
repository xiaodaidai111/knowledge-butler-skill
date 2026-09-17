import logging
import requests
import re
from typing import List, Dict, Optional, Any
from utils import Config

logger = logging.getLogger(__name__)

class RestaurantParser:
    """饭店名称解析器，从AI回复中提取饭店信息"""
    
    @staticmethod
    def extract_restaurants(text: str) -> List[Dict[str, Any]]:
        """
        从AI回复中提取饭店名称和相关信息
        
        Args:
            text: AI返回的回复文本
            
        Returns:
            饭店信息列表，每个元素包含name和可能的address
        """
        restaurants = []
        
        # 尝试多种模式匹配饭店名称
        patterns = [
            r'([《「『])?([^《「』\n]+?)([》」』])',  # 带引号的名称
            r'推荐[:：]\s*([^\n]+)',  # 推荐：后面的内容
            r'(\d+[:：]\.?\s*[^,\n]+)',  # 数字开头的列表项
            r'([^,\n]{2,10}店|[^,\n]{2,10}餐厅|[^,\n]{2,10}火锅|[^,\n]{2,10}料理|[^,\n]{2,10}菜)',  # 带店/餐厅/火锅/料理/菜后缀的名称
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1) if match.lastindex >= 1 else match.group(0)
                name = name.strip()
                if len(name) >= 2 and len(name) <= 20:
                    restaurants.append({
                        'name': name,
                        'source': 'ai_response'
                    })
        
        # 去重
        seen = set()
        unique_restaurants = []
        for restaurant in restaurants:
            name = restaurant['name']
            if name not in seen:
                seen.add(name)
                unique_restaurants.append(restaurant)
        
        logger.info(f"从AI回复中提取到 {len(unique_restaurants)} 个饭店名称")
        return unique_restaurants

class AMapService:
    """高德地图服务，处理地理编码和搜索"""
    
    def __init__(self):
        self.api_key = Config.AMAP_API_KEY
        self.base_url = "https://restapi.amap.com/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def geocode(self, address: str, city: str = "全国") -> Optional[Dict[str, Any]]:
        """
        地址解析，将地址转换为经纬度
        
        Args:
            address: 地址描述
            city: 城市名称
            
        Returns:
            包含经纬度的字典，失败返回None
        """
        try:
            url = f"{self.base_url}/geocode/geo"
            params = {
                'key': self.api_key,
                'address': address,
                'city': city
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == '1' and data.get('geocodes'):
                geocode = data['geocodes'][0]
                location = geocode['location'].split(',')
                return {
                    'lng': float(location[0]),
                    'lat': float(location[1]),
                    'formatted_address': geocode.get('formatted_address', ''),
                    'level': geocode.get('level', '')
                }
            
            logger.warning(f"地址解析失败: {address}")
            return None
            
        except Exception as e:
            logger.error(f"地址解析异常: {e}")
            return None
    
    def text_search(self, keywords: str, city: str = None, city_limit: bool = True) -> List[Dict[str, Any]]:
        """
        关键字搜索，搜索附近的POI
        
        Args:
            keywords: 搜索关键字
            city: 城市名称
            city_limit: 是否限制在指定城市
            
        Returns:
            POI信息列表
        """
        try:
            url = f"{self.base_url}/place/text"
            params = {
                'key': self.api_key,
                'keywords': keywords,
                'output': 'json',
                'offset': 20,
                'page': 1,
                'extensions': 'all'
            }
            
            if city:
                params['city'] = city
                params['citylimit'] = 'true' if city_limit else 'false'
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == '1' and data.get('pois'):
                pois = []
                for poi in data['pois']:
                    if poi.get('location'):
                        location = poi['location'].split(',')
                        pois.append({
                            'id': poi.get('id', ''),
                            'name': poi.get('name', ''),
                            'address': poi.get('address', ''),
                            'location': {
                                'lng': float(location[0]),
                                'lat': float(location[1])
                            },
                            'tel': poi.get('tel', ''),
                            'rating': poi.get('rating', ''),
                            'distance': poi.get('distance', ''),
                            'type': poi.get('type', ''),
                            'business_area': poi.get('business_area', ''),
                            'pname': poi.get('pname', ''),
                            'cityname': poi.get('cityname', ''),
                            'adname': poi.get('adname', '')
                        })
                
                logger.info(f"关键字搜索 '{keywords}' 找到 {len(pois)} 个POI")
                return pois
            
            logger.warning(f"关键字搜索无结果: {keywords}")
            return []
            
        except Exception as e:
            logger.error(f"关键字搜索异常: {e}")
            return []
    
    def around_search(self, location: Dict[str, float], keywords: str = "", radius: int = 3000) -> List[Dict[str, Any]]:
        """
        周边搜索，在指定位置附近搜索POI
        
        Args:
            location: 位置坐标 {'lng': xxx, 'lat': xxx}
            keywords: 搜索关键字
            radius: 搜索半径（米）
            
        Returns:
            POI信息列表
        """
        try:
            url = f"{self.base_url}/place/around"
            params = {
                'key': self.api_key,
                'location': f"{location['lng']},{location['lat']}",
                'keywords': keywords,
                'radius': radius,
                'output': 'json',
                'offset': 20,
                'page': 1,
                'extensions': 'all'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == '1' and data.get('pois'):
                pois = []
                for poi in data['pois']:
                    if poi.get('location'):
                        location_data = poi['location'].split(',')
                        pois.append({
                            'id': poi.get('id', ''),
                            'name': poi.get('name', ''),
                            'address': poi.get('address', ''),
                            'location': {
                                'lng': float(location_data[0]),
                                'lat': float(location_data[1])
                            },
                            'tel': poi.get('tel', ''),
                            'rating': poi.get('rating', ''),
                            'distance': poi.get('distance', ''),
                            'type': poi.get('type', ''),
                            'business_area': poi.get('business_area', '')
                        })
                
                logger.info(f"周边搜索找到 {len(pois)} 个POI")
                return pois
            
            logger.warning("周边搜索无结果")
            return []
            
        except Exception as e:
            logger.error(f"周边搜索异常: {e}")
            return []

class RestaurantMarkerService:
    """饭店标记服务，整合解析和定位功能"""
    
    def __init__(self):
        self.parser = RestaurantParser()
        self.amap = AMapService()
    
    def process_ai_response(self, ai_response: str, user_location: Dict[str, float] = None, city: str = None) -> Dict[str, Any]:
        """
        处理AI回复，提取饭店信息并在地图上标记
        
        Args:
            ai_response: AI返回的回复文本
            user_location: 用户位置 {'lng': xxx, 'lat': xxx}
            city: 城市名称
            
        Returns:
            包含饭店信息和标记数据的字典
        """
        # 1. 从AI回复中提取饭店名称
        restaurants = self.parser.extract_restaurants(ai_response)
        
        if not restaurants:
            logger.warning("未能从AI回复中提取到饭店信息")
            return {
                'success': False,
                'message': '未能识别到推荐的饭店',
                'restaurants': [],
                'markers': []
            }
        
        # 2. 对每个饭店进行地理编码或搜索
        marked_restaurants = []
        
        for restaurant in restaurants:
            restaurant_name = restaurant['name']
            
            # 优先使用周边搜索（如果有用户位置）
            if user_location:
                pois = self.amap.around_search(user_location, restaurant_name, radius=5000)
                if pois:
                    # 找到最匹配的POI
                    best_match = self._find_best_match(pois, restaurant_name)
                    if best_match:
                        marked_restaurants.append(best_match)
                        continue
            
            # 如果周边搜索没有结果，使用文本搜索
            if city:
                pois = self.amap.text_search(restaurant_name, city=city)
            else:
                pois = self.amap.text_search(restaurant_name)
            
            if pois:
                best_match = self._find_best_match(pois, restaurant_name)
                if best_match:
                    marked_restaurants.append(best_match)
        
        logger.info(f"成功标记 {len(marked_restaurants)} 个饭店")
        
        return {
            'success': True,
            'message': f'成功标记 {len(marked_restaurants)} 家餐厅',
            'restaurants': marked_restaurants,
            'markers': self._create_markers(marked_restaurants)
        }
    
    def _find_best_match(self, pois: List[Dict[str, Any]], target_name: str) -> Optional[Dict[str, Any]]:
        """
        从POI列表中找到最匹配的饭店
        
        Args:
            pois: POI列表
            target_name: 目标饭店名称
            
        Returns:
            最匹配的POI信息
        """
        if not pois:
            return None
        
        # 简单的名称匹配算法
        target_name = target_name.lower()
        best_match = None
        best_score = 0
        
        for poi in pois:
            poi_name = poi['name'].lower()
            
            # 完全匹配
            if poi_name == target_name:
                return poi
            
            # 包含匹配
            if target_name in poi_name or poi_name in target_name:
                score = min(len(target_name), len(poi_name)) / max(len(target_name), len(poi_name))
                if score > best_score:
                    best_score = score
                    best_match = poi
        
        # 如果最佳匹配分数太低，返回第一个结果
        if best_score < 0.5 and len(pois) > 0:
            return pois[0]
        
        return best_match
    
    def _create_markers(self, restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        创建地图标记数据
        
        Args:
            restaurants: 饭店信息列表
            
        Returns:
            标记数据列表
        """
        markers = []
        colors = ['#fa8c16', '#52c41a', '#1890ff', '#eb2f96', '#722ed1']
        
        for index, restaurant in enumerate(restaurants):
            color = colors[index % len(colors)]
            markers.append({
                'id': restaurant.get('id', f'marker_{index}'),
                'name': restaurant['name'],
                'address': restaurant['address'],
                'location': restaurant['location'],
                'tel': restaurant.get('tel', ''),
                'rating': restaurant.get('rating', ''),
                'distance': restaurant.get('distance', ''),
                'color': color,
                'index': index + 1
            })
        
        return markers

# 全局服务实例
restaurant_marker_service = RestaurantMarkerService()