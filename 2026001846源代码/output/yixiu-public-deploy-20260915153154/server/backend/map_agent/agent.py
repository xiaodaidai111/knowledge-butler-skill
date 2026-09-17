"""智能体核心逻辑模块"""
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage

from .config import config
from .tools import MapTools
from .conversation import conversation_manager


# 系统提示模板
SYSTEM_PROMPT = """你是一个地图智能助手，能够帮助用户处理地图相关的问题。

你可以：
1. 根据地址获取经纬度
2. 根据经纬度获取地址
3. 计算两点之间的最优路径
4. 查找指定位置附近的地点
5. 根据地点ID获取详细信息，包括评价、评分、人均消费等

当用户提出地图相关的问题时，你应该使用相应的工具来获取信息，然后根据获取的信息为用户提供准确的回答。

请确保你的回答清晰、准确，并基于工具返回的结果。
"""


class MapAgent:
    """地图智能体类"""
    
    def __init__(self):
        """初始化地图智能体"""
        self.map_tools = MapTools()
        self.tools = self.map_tools.get_all_tools()
        self.llm = None
        
        # 初始化智能体
        self._initialize_agent()
    
    def _initialize_agent(self):
        """初始化智能体"""
        try:
            # 初始化语言模型
            self.llm = self._initialize_llm()
            
            if self.llm:
                print("智能体初始化成功")
            else:
                print("无法初始化语言模型，智能体将使用备用模式")
                
        except Exception as e:
            print(f"智能体初始化失败: {e}")
            self.llm = None
    
    def _initialize_llm(self):
        """初始化语言模型
        
        Returns:
            语言模型实例，失败返回None
        """
        try:
            print(f"AI Provider: {config.ai_provider}")
            print(f"AI API密钥配置: {bool(config.ai_api_key)}")
            print(f"AI模型名称: {config.ai_model_name}")
            print(f"AI温度参数: {config.ai_temperature}")
            
            if config.ai_api_key:
                print("正在初始化统一AI模型...")
                llm = ChatOpenAI(
                    model_name=config.ai_model_name,
                    temperature=config.ai_temperature,
                    api_key=config.ai_api_key,
                    base_url=config.ai_base_url
                )

                return llm
            else:
                print("未配置AI API密钥，无法初始化语言模型")
                return None
        
        except Exception as e:
            print(f"初始化语言模型失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def process_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """处理用户消息
        
        Args:
            conversation_id: 对话ID
            message: 用户消息
            
        Returns:
            包含响应和其他信息的字典
        """
        import time
        start_time = time.time()
        
        # 添加用户消息到对话历史
        conversation_manager.add_message(conversation_id, "user", message)
        
        # 获取对话历史
        history = conversation_manager.get_conversation_history(conversation_id)
        
        try:
            # 检查智能体是否初始化成功
            if self.llm:
                print(f"开始处理消息: {message}")
                
                # 更智能地理解用户意图，判断是否需要使用地图工具
                # 使用语言模型来分析用户意图和提取信息
                print("分析用户意图...")
                
                # 创建意图分析提示
                intent_prompt = ChatPromptTemplate.from_messages([
                    ("system", "你是一个意图分析助手，负责分析用户的地图相关请求。\n\n"+
                     "任务：\n"+
                     "1. 判断用户请求是否需要使用地图工具（地理编码、附近搜索、路径规划等）\n"+
                     "2. 如果需要，提取以下信息：\n"+
                     "   - 地点：用户提到的具体地点\n"+
                     "   - 类型：查询的地点类型（如餐馆、酒店、景点、商场等）\n"+
                     "   - 操作：需要执行的操作（如附近搜索、地理编码、路径规划等）\n"+
                     "3. 如果不需要，返回不需要使用地图工具\n\n"+
                     "输出格式：\n"+
                     "需要使用地图工具\n"+
                     "地点：[地点名称]\n"+
                     "类型：[地点类型]\n"+
                     "操作：[操作类型]\n"+
                     "或\n"+
                     "不需要使用地图工具"),
                    ("user", "用户请求：{input}")
                ])
                
                # 构建意图分析链
                intent_chain = intent_prompt | self.llm
                
                # 分析用户意图
                intent_response = intent_chain.invoke({"input": message})
                intent_content = intent_response.content if hasattr(intent_response, "content") else str(intent_response)
                print(f"意图分析结果: {intent_content}")
                
                # 解析意图分析结果
                need_map_tool = "需要使用地图工具" in intent_content and "不需要使用地图工具" not in intent_content
                location_name = ""
                keyword = ""
                operation = ""
                
                print(f"是否需要使用地图工具: {need_map_tool}")
                
                if need_map_tool:
                    print("检测到需要使用地图工具的请求")
                    
                    # 提取地点
                    if "地点：" in intent_content:
                        location_part = intent_content.split("地点：")[1].split("\n")[0].strip()
                        if location_part:
                            location_name = location_part
                    
                    # 提取类型
                    if "类型：" in intent_content:
                        type_part = intent_content.split("类型：")[1].split("\n")[0].strip()
                        if type_part:
                            keyword = type_part
                    
                    # 提取操作
                    if "操作：" in intent_content:
                        operation_part = intent_content.split("操作：")[1].split("\n")[0].strip()
                        if operation_part:
                            operation = operation_part
                    
                    print(f"提取到地点: {location_name}")
                    print(f"提取到类型: {keyword}")
                    print(f"提取到操作: {operation}")
                    
                    if location_name and (keyword or operation):
                        print(f"提取到地点: {location_name}, 类型: {keyword}, 操作: {operation}")
                        
                        # 1. 使用地理编码工具获取地点的经纬度
                        geocode_tool = self.tools[0]  # GeocodeTool
                        geocode_result = geocode_tool._run(location_name)
                        print(f"地理编码结果: {geocode_result}")
                        
                        if geocode_result and "lat" in geocode_result and "lon" in geocode_result:
                            lat = geocode_result["lat"]
                            lon = geocode_result["lon"]
                            print(f"获取到经纬度: {lat}, {lon}")
                            
                            # 2. 根据操作类型执行相应的工具调用
                            result_text = ""
                            if operation == "附近搜索" or not operation:
                                # 使用附近搜索工具搜索附近的地点
                                nearby_tool = self.tools[3]  # NearbySearchTool
                                nearby_result = nearby_tool._run(lat, lon, radius=5000, keyword=keyword)
                                print(f"附近搜索结果: {nearby_result}")
                                
                                if nearby_result:
                                    # 构建搜索结果文本
                                    result_text = f"在{location_name}附近找到了以下{keyword}：\n\n"
                                    for i, place in enumerate(nearby_result[:5], 1):
                                        name = place.get("name", "未知名称")
                                        address = place.get("address", "未知地址")
                                        distance = place.get("distance", "未知距离")
                                        rating = place.get("rating", "暂无评分")
                                        cost = place.get("cost", "暂无人均消费")
                                        result_text += f"{i}. {name}\n   地址: {address}\n   距离: {distance}米\n   评分: {rating}\n   人均: {cost}\n\n"
                                else:
                                    agent_response = f"抱歉，在{location_name}附近没有找到{keyword}信息。"
                                    
                            elif operation == "地理编码":
                                # 直接使用地理编码结果
                                result_text = f"{location_name}的经纬度信息：\n\n"
                                result_text += f"纬度: {lat}\n"
                                result_text += f"经度: {lon}\n"
                                result_text += f"完整地址: {geocode_result.get('address', '未知')}\n"
                                if "province" in geocode_result:
                                    result_text += f"省份: {geocode_result['province']}\n"
                                if "city" in geocode_result:
                                    result_text += f"城市: {geocode_result['city']}\n"
                                if "district" in geocode_result:
                                    result_text += f"区县: {geocode_result['district']}\n"
                            
                            # 3. 使用语言模型生成最终响应
                            if result_text:
                                prompt = ChatPromptTemplate.from_messages([
                                    ("system", SYSTEM_PROMPT),
                                    ("user", "用户问: {input}\n\n我找到了以下信息: {context}\n\n请根据这些信息为用户提供一个友好、详细的回答。"),
                                ])
                                
                                chain = prompt | self.llm
                                response = chain.invoke({"input": message, "context": result_text})
                                
                                if hasattr(response, "content"):
                                    agent_response = response.content
                                else:
                                    agent_response = str(response)
                        else:
                            agent_response = f"抱歉，无法获取{location_name}的位置信息。"
                    else:
                        agent_response = "抱歉，我需要知道具体的地点和您要搜索的内容，比如'北京附近的餐馆'。"
                else:
                    # 非地点查询请求，直接使用语言模型
                    print("不需要使用地图工具，直接使用语言模型")
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", SYSTEM_PROMPT),
                        ("user", "{input}")
                    ])
                    
                    chain = prompt | self.llm
                    response = chain.invoke({"input": message})
                    
                    if hasattr(response, "content"):
                        agent_response = response.content
                    else:
                        agent_response = str(response)
                
                print(f"语言模型响应时间: {time.time() - start_time:.2f}秒")
                print(f"智能体响应: {agent_response}")
                
                # 检查响应是否为空
                if not agent_response:
                    print("语言模型返回空响应")
                    agent_response = "抱歉，我暂时无法回答这个问题，请稍后再试。"
                
                # 添加智能体响应到对话历史
                conversation_manager.add_message(conversation_id, "assistant", agent_response)
                
                return {
                    "response": agent_response,
                    "status": "success",
                    "conversation_id": conversation_id,
                    "timestamp": history[-1]["timestamp"] if history else None
                }
            else:
                # 使用备用模式处理消息
                return self._fallback_process_message(conversation_id, message)
                
        except Exception as e:
            print(f"处理消息失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 添加错误消息到对话历史
            error_message = f"抱歉，处理您的请求时出现错误: {str(e)}"
            conversation_manager.add_message(conversation_id, "assistant", error_message)
            
            return {
                "response": error_message,
                "status": "error",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    def _fallback_process_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """备用消息处理模式
        
        Args:
            conversation_id: 对话ID
            message: 用户消息
            
        Returns:
            包含响应和其他信息的字典
        """
        # 简单的基于规则的处理
        response = """
        您好！我是地图智能助手，能够帮助您处理地图相关的问题。
        
        我可以：
        1. 根据地址获取经纬度
        2. 根据经纬度获取地址
        3. 计算两点之间的最优路径
        4. 查找指定位置附近的地点
        
        例如，您可以问我：
        - "北京市海淀区中关村大街1号的经纬度是多少？"
        - "纬度39.9042，经度116.4074的地址是什么？"
        - "从北京到上海的驾车路线是什么？"
        - "北京市海淀区中关村附近有哪些餐厅？"
        
        请注意，由于智能体初始化失败，我只能提供有限的功能。
        """
        
        # 添加备用响应到对话历史
        conversation_manager.add_message(conversation_id, "assistant", response)
        
        return {
            "response": response,
            "status": "success",
            "conversation_id": conversation_id,
            "mode": "fallback"
        }
    
    def get_conversation_history(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            conversation_id: 对话ID
            limit: 限制返回的轮次数量
            
        Returns:
            对话历史列表
        """
        return conversation_manager.get_conversation_history(conversation_id, limit)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清空对话历史
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否清空成功
        """
        # 删除旧对话
        deleted = conversation_manager.delete_conversation(conversation_id)
        
        # 创建新对话
        new_conversation_id = conversation_manager.create_conversation()
        
        return deleted and new_conversation_id is not None
    
    def create_conversation(self) -> str:
        """创建新对话
        
        Returns:
            对话ID
        """
        return conversation_manager.create_conversation()
    
    def is_initialized(self) -> bool:
        """检查智能体是否初始化成功
        
        Returns:
            是否初始化成功
        """
        return self.llm is not None
    
    def get_available_tools(self) -> List[str]:
        """获取可用的工具列表
        
        Returns:
            工具名称列表
        """
        return [tool.name for tool in self.tools]


# 创建全局智能体实例
map_agent = MapAgent()
