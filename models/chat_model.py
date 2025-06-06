"""
聊天相关数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息模型"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """从字典创建实例"""
        return cls(
            role=MessageRole(data['role']),
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            metadata=data.get('metadata', {})
        )


@dataclass
class ChatRequest:
    """聊天请求模型"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'messages': [msg.to_dict() for msg in self.messages],
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'stream': self.stream,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'metadata': self.metadata or {}
        }


@dataclass
class UsageInfo:
    """使用信息模型"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }


@dataclass
class ChatResponse:
    """聊天响应模型"""
    message: ChatMessage
    usage: Optional[UsageInfo] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    provider: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message': self.message.to_dict(),
            'usage': self.usage.to_dict() if self.usage else None,
            'model': self.model,
            'finish_reason': self.finish_reason,
            'provider': self.provider,
            'request_id': self.request_id,
            'metadata': self.metadata or {}
        }


@dataclass
class ChatProvider:
    """AI提供商模型"""
    name: str
    display_name: str
    models: List[str]
    is_available: bool = True
    config: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'models': self.models,
            'is_available': self.is_available,
            'config': self.config or {}
        }
