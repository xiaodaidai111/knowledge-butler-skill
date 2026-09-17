"""工具调用模块"""
from typing import Dict, List, Optional, Tuple, Any, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .map_processor import MapProcessor


class MapTools:
    """地图工具类"""
    
    def __init__(self):
        """初始化地图工具"""
        self.map_processor = MapProcessor()
    
    def get_geocode_tool(self):
        """获取地理编码工具
        
        Returns:
            GeocodeTool: 地理编码工具
        """
        return GeocodeTool(self.map_processor)
    
    def get_reverse_geocode_tool(self):
        """获取反向地理编码工具
        
        Returns:
            ReverseGeocodeTool: 反向地理编码工具
        """
        return ReverseGeocodeTool(self.map_processor)
    
    def get_directions_tool(self):
        """获取路径规划工具
        
        Returns:
            DirectionsTool: 路径规划工具
        """
        return DirectionsTool(self.map_processor)
    
    def get_nearby_search_tool(self):
        """获取附近地点查询工具
        
        Returns:
            NearbySearchTool: 附近地点查询工具
        """
        return NearbySearchTool(self.map_processor)
    
    def get_place_details_tool(self):
        """获取地点详情工具
        
        Returns:
            GetPlaceDetailsTool: 地点详情工具
        """
        return GetPlaceDetailsTool(self.map_processor)
    
    def get_all_tools(self):
        """获取所有地图工具
        
        Returns:
            List[BaseTool]: 地图工具列表
        """
        return [
            self.get_geocode_tool(),
            self.get_reverse_geocode_tool(),
            self.get_directions_tool(),
            self.get_nearby_search_tool(),
            self.get_place_details_tool()
        ]


# 工具输入模式定义

class GeocodeInput(BaseModel):
    """地理编码工具输入"""
    address: str = Field(description="要查询的地址")


class ReverseGeocodeInput(BaseModel):
    """反向地理编码工具输入"""
    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")


class DirectionsInput(BaseModel):
    """路径规划工具输入"""
    origin_lat: float = Field(description="起点纬度")
    origin_lon: float = Field(description="起点经度")
    dest_lat: float = Field(description="终点纬度")
    dest_lon: float = Field(description="终点经度")
    mode: str = Field(default="driving", description="交通方式: driving, walking, biking, transit")


class NearbySearchInput(BaseModel):
    """附近地点查询工具输入"""
    lat: float = Field(description="中心点纬度")
    lon: float = Field(description="中心点经度")
    radius: int = Field(default=5000, description="搜索半径（米）")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")


class GetPlaceDetailsInput(BaseModel):
    """获取地点详情工具输入"""
    place_id: str = Field(description="地点ID")


# 工具类定义

class GeocodeTool(BaseTool):
    """地理编码工具"""
    name: str = "geocode"
    description: str = "根据地址获取经纬度信息"
    args_schema: Type[BaseModel] = GeocodeInput
    
    def __init__(self, map_processor: MapProcessor):
        """初始化地理编码工具
        
        Args:
            map_processor: 地图处理器实例
        """
        super().__init__()
        # 使用__dict__来设置实例变量，避免Pydantic验证
        self.__dict__['map_processor'] = map_processor
    
    def _run(self, address: str) -> Dict[str, Any]:
        """执行地理编码
        
        Args:
            address: 地址字符串
            
        Returns:
            包含经纬度和其他信息的字典
        """
        result = self.map_processor.geocode(address)
        if result:
            return result
        return {"error": "地理编码失败"}
    
    async def _arun(self, address: str) -> Dict[str, Any]:
        """异步执行地理编码
        
        Args:
            address: 地址字符串
            
        Returns:
            包含经纬度和其他信息的字典
        """
        return self._run(address)


class ReverseGeocodeTool(BaseTool):
    """反向地理编码工具"""
    name: str = "reverse_geocode"
    description: str = "根据经纬度获取地址信息"
    args_schema: Type[BaseModel] = ReverseGeocodeInput
    
    def __init__(self, map_processor: MapProcessor):
        """初始化反向地理编码工具
        
        Args:
            map_processor: 地图处理器实例
        """
        super().__init__()
        # 使用__dict__来设置实例变量，避免Pydantic验证
        self.__dict__['map_processor'] = map_processor
    
    def _run(self, lat: float, lon: float) -> Dict[str, Any]:
        """执行反向地理编码
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            包含地址和其他信息的字典
        """
        result = self.map_processor.reverse_geocode(lat, lon)
        if result:
            return result
        return {"error": "反向地理编码失败"}
    
    async def _arun(self, lat: float, lon: float) -> Dict[str, Any]:
        """异步执行反向地理编码
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            包含地址和其他信息的字典
        """
        return self._run(lat, lon)


class DirectionsTool(BaseTool):
    """路径规划工具"""
    name: str = "get_directions"
    description: str = "计算两点之间的最优路径"
    args_schema: Type[BaseModel] = DirectionsInput
    
    def __init__(self, map_processor: MapProcessor):
        """初始化路径规划工具
        
        Args:
            map_processor: 地图处理器实例
        """
        super().__init__()
        # 使用__dict__来设置实例变量，避免Pydantic验证
        self.__dict__['map_processor'] = map_processor
    
    def _run(self, origin_lat: float, origin_lon: float, 
             dest_lat: float, dest_lon: float, 
             mode: str = "driving") -> Dict[str, Any]:
        """执行路径规划
        
        Args:
            origin_lat: 起点纬度
            origin_lon: 起点经度
            dest_lat: 终点纬度
            dest_lon: 终点经度
            mode: 交通方式
            
        Returns:
            包含路径信息的字典
        """
        origin = (origin_lat, origin_lon)
        destination = (dest_lat, dest_lon)
        result = self.map_processor.get_directions(origin, destination, mode)
        if result:
            return result
        return {"error": "路径规划失败"}
    
    async def _arun(self, origin_lat: float, origin_lon: float, 
                    dest_lat: float, dest_lon: float, 
                    mode: str = "driving") -> Dict[str, Any]:
        """异步执行路径规划
        
        Args:
            origin_lat: 起点纬度
            origin_lon: 起点经度
            dest_lat: 终点纬度
            dest_lon: 终点经度
            mode: 交通方式
            
        Returns:
            包含路径信息的字典
        """
        return self._run(origin_lat, origin_lon, dest_lat, dest_lon, mode)


class NearbySearchTool(BaseTool):
    """附近地点查询工具"""
    name: str = "search_nearby"
    description: str = "查找指定位置附近的地点"
    args_schema: Type[BaseModel] = NearbySearchInput
    
    def __init__(self, map_processor: MapProcessor):
        """初始化附近地点查询工具
        
        Args:
            map_processor: 地图处理器实例
        """
        super().__init__()
        # 使用__dict__来设置实例变量，避免Pydantic验证
        self.__dict__['map_processor'] = map_processor
    
    def _run(self, lat: float, lon: float, 
             radius: int = 5000, 
             keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行附近地点查询
        
        Args:
            lat: 中心点纬度
            lon: 中心点经度
            radius: 搜索半径（米）
            keyword: 搜索关键词
            
        Returns:
            包含附近地点信息的列表
        """
        location = (lat, lon)
        result = self.map_processor.search_nearby(location, radius, keyword)
        if result:
            return result
        return []
    
    async def _arun(self, lat: float, lon: float, 
                    radius: int = 5000, 
                    keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """异步执行附近地点查询
        
        Args:
            lat: 中心点纬度
            lon: 中心点经度
            radius: 搜索半径（米）
            keyword: 搜索关键词
            
        Returns:
            包含附近地点信息的列表
        """
        return self._run(lat, lon, radius, keyword)


class GetPlaceDetailsTool(BaseTool):
    """获取地点详情工具"""
    name: str = "get_place_details"
    description: str = "根据地点ID获取详细信息，包括评价、评分、人均消费等"
    args_schema: Type[BaseModel] = GetPlaceDetailsInput
    
    def __init__(self, map_processor: MapProcessor):
        """初始化地点详情工具
        
        Args:
            map_processor: 地图处理器实例
        """
        super().__init__()
        # 使用__dict__来设置实例变量，避免Pydantic验证
        self.__dict__['map_processor'] = map_processor
    
    def _run(self, place_id: str) -> Dict[str, Any]:
        """执行获取地点详情
        
        Args:
            place_id: 地点ID
            
        Returns:
            包含地点详细信息的字典
        """
        try:
            # 调用地图处理器的方法获取地点详情
            result = self.map_processor.get_place_details(place_id)
            if result:
                return result
            return {"error": "获取地点详情失败"}
        except Exception as e:
            return {"error": f"获取地点详情失败: {str(e)}"}
    
    async def _arun(self, place_id: str) -> Dict[str, Any]:
        """异步执行获取地点详情
        
        Args:
            place_id: 地点ID
            
        Returns:
            包含地点详细信息的字典
        """
        return self._run(place_id)
