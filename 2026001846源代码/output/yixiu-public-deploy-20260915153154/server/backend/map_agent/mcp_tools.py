"""MCP工具接口层"""
from typing import Dict, List, Optional, Any, Type, Callable
from pydantic import BaseModel, Field

from .map_processor import MapProcessor


class MCPTool(BaseModel):
    """MCP工具基础类"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    input_schema: Type[BaseModel] = Field(description="输入参数模式")
    output_schema: Type[BaseModel] = Field(description="输出参数模式")
    function: Callable = Field(description="工具函数")
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """运行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            # 验证输入参数
            input_data = self.input_schema(**kwargs)
            # 执行工具函数
            result = self.function(**input_data.dict())
            # 验证输出结果
            if isinstance(result, dict):
                return result
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}


class MCPToolRegistry:
    """MCP工具注册表"""
    
    def __init__(self):
        """初始化工具注册表"""
        self.tools: Dict[str, MCPTool] = {}
    
    def register_tool(self, tool: MCPTool) -> None:
        """注册工具
        
        Args:
            tool: MCP工具实例
        """
        self.tools[tool.name] = tool
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            MCP工具实例，不存在返回None
        """
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具
        
        Returns:
            工具信息列表
        """
        tool_list = []
        for tool_name, tool in self.tools.items():
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {}
                },
                "output_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
            
            # 解析输入参数模式
            if tool.input_schema:
                input_properties = {}
                for field_name, field in tool.input_schema.__fields__.items():
                    input_properties[field_name] = {
                        "type": field.type_.__name__ if hasattr(field.type_, "__name__") else str(field.type_),
                        "description": field.field_info.description or ""
                    }
                tool_info["input_schema"]["properties"] = input_properties
            
            # 解析输出参数模式
            if tool.output_schema:
                output_properties = {}
                for field_name, field in tool.output_schema.__fields__.items():
                    output_properties[field_name] = {
                        "type": field.type_.__name__ if hasattr(field.type_, "__name__") else str(field.type_),
                        "description": field.field_info.description or ""
                    }
                tool_info["output_schema"]["properties"] = output_properties
            
            tool_list.append(tool_info)
        
        return tool_list


# 创建全局工具注册表
tool_registry = MCPToolRegistry()


# 输入/输出模式定义

class GeocodeInput(BaseModel):
    """地理编码工具输入"""
    address: str = Field(description="要查询的地址")


class GeocodeOutput(BaseModel):
    """地理编码工具输出"""
    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")
    address: str = Field(description="地址")
    province: Optional[str] = Field(description="省份")
    city: Optional[str] = Field(description="城市")
    district: Optional[str] = Field(description="区县")


class ReverseGeocodeInput(BaseModel):
    """反向地理编码工具输入"""
    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")


class ReverseGeocodeOutput(BaseModel):
    """反向地理编码工具输出"""
    address: str = Field(description="地址")
    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")
    province: Optional[str] = Field(description="省份")
    city: Optional[str] = Field(description="城市")
    district: Optional[str] = Field(description="区县")


class DirectionsInput(BaseModel):
    """路径规划工具输入"""
    origin_lat: float = Field(description="起点纬度")
    origin_lon: float = Field(description="起点经度")
    dest_lat: float = Field(description="终点纬度")
    dest_lon: float = Field(description="终点经度")
    mode: str = Field(default="driving", description="交通方式: driving, walking, biking, transit")


class DirectionsOutput(BaseModel):
    """路径规划工具输出"""
    distance: str = Field(description="距离")
    duration: str = Field(description="耗时")
    start_address: str = Field(description="起点地址")
    end_address: str = Field(description="终点地址")
    steps: List[Dict[str, Any]] = Field(description="路径步骤")
    mode: str = Field(description="交通方式")


class NearbySearchInput(BaseModel):
    """附近搜索工具输入"""
    lat: float = Field(description="中心点纬度")
    lon: float = Field(description="中心点经度")
    radius: int = Field(default=5000, description="搜索半径（米）")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")


class NearbySearchOutput(BaseModel):
    """附近搜索工具输出"""
    places: List[Dict[str, Any]] = Field(description="附近地点列表")


class PlaceDetailsInput(BaseModel):
    """地点详情工具输入"""
    place_id: str = Field(description="地点ID")


class PlaceDetailsOutput(BaseModel):
    """地点详情工具输出"""
    name: str = Field(description="地点名称")
    address: str = Field(description="地点地址")
    rating: Optional[str] = Field(description="评分")
    cost: Optional[str] = Field(description="人均消费")
    open_time: Optional[str] = Field(description="营业时间")
    photos: List[Dict[str, Any]] = Field(description="照片列表")
    reviews: List[Dict[str, Any]] = Field(description="评价列表")


# 地图处理器实例
map_processor = MapProcessor()


# 工具函数定义
def geocode_function(address: str) -> Dict[str, Any]:
    """地理编码函数"""
    result = map_processor.geocode(address)
    if result:
        return result
    return {"error": "地理编码失败"}


def reverse_geocode_function(lat: float, lon: float) -> Dict[str, Any]:
    """反向地理编码函数"""
    result = map_processor.reverse_geocode(lat, lon)
    if result:
        return result
    return {"error": "反向地理编码失败"}


def directions_function(origin_lat: float, origin_lon: float, 
                       dest_lat: float, dest_lon: float, 
                       mode: str = "driving") -> Dict[str, Any]:
    """路径规划函数"""
    origin = (origin_lat, origin_lon)
    destination = (dest_lat, dest_lon)
    result = map_processor.get_directions(origin, destination, mode)
    if result:
        return result
    return {"error": "路径规划失败"}


def nearby_search_function(lat: float, lon: float, 
                          radius: int = 5000, 
                          keyword: Optional[str] = None) -> Dict[str, Any]:
    """附近搜索函数"""
    location = (lat, lon)
    result = map_processor.search_nearby(location, radius, keyword)
    if result:
        return {"places": result}
    return {"places": []}


def place_details_function(place_id: str) -> Dict[str, Any]:
    """地点详情函数"""
    result = map_processor.get_place_details(place_id)
    if result:
        return result
    return {"error": "获取地点详情失败"}


# 注册MCP工具
def register_mcp_tools():
    """注册MCP工具"""
    # 地理编码工具
    geocode_tool = MCPTool(
        name="geocode",
        description="根据地址获取经纬度信息",
        input_schema=GeocodeInput,
        output_schema=GeocodeOutput,
        function=geocode_function
    )
    tool_registry.register_tool(geocode_tool)
    
    # 反向地理编码工具
    reverse_geocode_tool = MCPTool(
        name="reverse_geocode",
        description="根据经纬度获取地址信息",
        input_schema=ReverseGeocodeInput,
        output_schema=ReverseGeocodeOutput,
        function=reverse_geocode_function
    )
    tool_registry.register_tool(reverse_geocode_tool)
    
    # 路径规划工具
    directions_tool = MCPTool(
        name="get_directions",
        description="计算两点之间的最优路径",
        input_schema=DirectionsInput,
        output_schema=DirectionsOutput,
        function=directions_function
    )
    tool_registry.register_tool(directions_tool)
    
    # 附近搜索工具
    nearby_search_tool = MCPTool(
        name="search_nearby",
        description="查找指定位置附近的地点",
        input_schema=NearbySearchInput,
        output_schema=NearbySearchOutput,
        function=nearby_search_function
    )
    tool_registry.register_tool(nearby_search_tool)
    
    # 地点详情工具
    place_details_tool = MCPTool(
        name="get_place_details",
        description="根据地点ID获取详细信息，包括评价、评分、人均消费等",
        input_schema=PlaceDetailsInput,
        output_schema=PlaceDetailsOutput,
        function=place_details_function
    )
    tool_registry.register_tool(place_details_tool)


# 初始化时注册工具
register_mcp_tools()


def get_mcp_tools() -> List[Dict[str, Any]]:
    """获取所有MCP工具
    
    Returns:
        MCP工具列表
    """
    return tool_registry.list_tools()


def get_mcp_tool(tool_name: str) -> Optional[MCPTool]:
    """获取指定MCP工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        MCP工具实例，不存在返回None
    """
    return tool_registry.get_tool(tool_name)


def run_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """运行指定MCP工具
    
    Args:
        tool_name: 工具名称
        **kwargs: 工具参数
        
    Returns:
        工具执行结果
    """
    tool = tool_registry.get_tool(tool_name)
    if tool:
        return tool.run(**kwargs)
    return {"error": f"工具不存在: {tool_name}"}
