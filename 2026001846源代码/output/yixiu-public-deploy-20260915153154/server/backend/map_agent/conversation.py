"""对话管理模块"""
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import config


class Conversation:
    """对话类"""
    
    def __init__(self, conversation_id: Optional[str] = None):
        """初始化对话
        
        Args:
            conversation_id: 对话ID，若不提供则自动生成
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.turns: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.max_turns = config.conversation_max_turns
        self.timeout = config.conversation_timeout
    
    def add_turn(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加对话轮次
        
        Args:
            role: 角色，如"user"、"assistant"、"tool"
            content: 对话内容
            metadata: 附加信息
        """
        # 检查对话是否超时
        if self.is_timeout():
            raise ValueError("对话已超时")
        
        # 检查对话轮次是否超过限制
        if len(self.turns) >= self.max_turns:
            # 移除最早的轮次
            self.turns.pop(0)
        
        # 添加新轮次
        turn = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.turns.append(turn)
        self.last_activity_time = datetime.now()
        
        return turn
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            limit: 限制返回的轮次数量
            
        Returns:
            对话历史列表
        """
        if limit:
            return self.turns[-limit:]
        return self.turns
    
    def get_context(self) -> str:
        """获取对话上下文
        
        Returns:
            对话上下文字符串
        """
        context = ""
        for turn in self.turns:
            context += f"{turn['role']}: {turn['content']}\n"
        return context
    
    def is_timeout(self) -> bool:
        """检查对话是否超时
        
        Returns:
            是否超时
        """
        elapsed = (datetime.now() - self.last_activity_time).total_seconds()
        return elapsed > self.timeout
    
    def get_turn_count(self) -> int:
        """获取对话轮次数量
        
        Returns:
            对话轮次数量
        """
        return len(self.turns)
    
    def get_last_turn(self) -> Optional[Dict[str, Any]]:
        """获取最后一个对话轮次
        
        Returns:
            最后一个对话轮次，若没有则返回None
        """
        if self.turns:
            return self.turns[-1]
        return None
    
    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息
        
        Returns:
            最后一条用户消息，若没有则返回None
        """
        for turn in reversed(self.turns):
            if turn['role'] == 'user':
                return turn['content']
        return None
    
    def clear(self):
        """清空对话历史"""
        self.turns = []
        self.last_activity_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """将对话转换为字典
        
        Returns:
            对话字典
        """
        return {
            "conversation_id": self.conversation_id,
            "turns": self.turns,
            "start_time": self.start_time.isoformat(),
            "last_activity_time": self.last_activity_time.isoformat(),
            "turn_count": len(self.turns),
            "is_timeout": self.is_timeout()
        }


class ConversationManager:
    """对话管理类"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.conversations: Dict[str, Conversation] = {}
        self.cleanup_interval = 300  # 清理间隔（秒）
        self.last_cleanup = time.time()
    
    def create_conversation(self) -> str:
        """创建新对话
        
        Returns:
            对话ID
        """
        conversation = Conversation()
        self.conversations[conversation.conversation_id] = conversation
        self._cleanup_timeout_conversations()
        return conversation.conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话对象，若不存在则返回None
        """
        conversation = self.conversations.get(conversation_id)
        
        # 检查对话是否超时
        if conversation and conversation.is_timeout():
            # 移除超时对话
            del self.conversations[conversation_id]
            return None
        
        self._cleanup_timeout_conversations()
        return conversation
    
    def add_message(self, conversation_id: str, role: str, 
                   content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """添加消息到对话
        
        Args:
            conversation_id: 对话ID
            role: 角色
            content: 内容
            metadata: 附加信息
            
        Returns:
            添加的消息，若对话不存在或超时则返回None
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return None
        
        try:
            return conversation.add_turn(role, content, metadata)
        except ValueError:
            # 对话超时
            del self.conversations[conversation_id]
            return None
    
    def get_conversation_history(self, conversation_id: str, 
                               limit: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """获取对话历史
        
        Args:
            conversation_id: 对话ID
            limit: 限制返回的轮次数量
            
        Returns:
            对话历史，若对话不存在则返回None
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return None
        
        return conversation.get_history(limit)
    
    def get_conversation_context(self, conversation_id: str) -> Optional[str]:
        """获取对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话上下文，若对话不存在则返回None
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return None
        
        return conversation.get_context()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否删除成功
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_conversation_count(self) -> int:
        """获取对话数量
        
        Returns:
            对话数量
        """
        self._cleanup_timeout_conversations()
        return len(self.conversations)
    
    def _cleanup_timeout_conversations(self):
        """清理超时对话"""
        current_time = time.time()
        
        # 检查是否需要清理
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # 清理超时对话
        timeout_conversations = []
        for conversation_id, conversation in self.conversations.items():
            if conversation.is_timeout():
                timeout_conversations.append(conversation_id)
        
        for conversation_id in timeout_conversations:
            del self.conversations[conversation_id]
        
        self.last_cleanup = current_time


# 创建全局对话管理器实例
conversation_manager = ConversationManager()
