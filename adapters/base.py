"""
AI适配器基类模块
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息数据结构"""
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
    """聊天请求数据结构"""
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
    """使用信息"""
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
    """聊天响应数据结构"""
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


class AdapterError(Exception):
    """适配器基础异常"""
    def __init__(self, message: str, error_code: str = None, provider: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.provider = provider


class AuthenticationError(AdapterError):
    """认证错误"""
    pass


class RateLimitError(AdapterError):
    """限流错误"""
    pass


class ModelNotFoundError(AdapterError):
    """模型不存在错误"""
    pass


class BaseAIAdapter(ABC):
    """AI适配器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self._get_provider_name()
        self.logger = logging.getLogger(f"{__name__}.{self.provider_name}")
        
        # 验证配置
        self._validate_config()
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置"""
        pass
    
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """同步聊天接口"""
        pass
    
    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[ChatResponse, None]:
        """流式聊天接口"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass
    
    async def validate_connection(self) -> bool:
        """验证连接是否有效"""
        try:
            # 发送一个简单的测试请求
            test_request = ChatRequest(
                messages=[ChatMessage(role=MessageRole.USER, content="test")],
                model=self.get_supported_models()[0] if self.get_supported_models() else None,
                max_tokens=1
            )
            await self.chat(test_request)
            return True
        except Exception as e:
            self.logger.error(f"Connection validation failed: {str(e)}")
            return False
    
    def _prepare_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """准备消息格式（子类可重写）"""
        return [{'role': msg.role.value, 'content': msg.content} for msg in messages]
    
    def _create_response(
        self, 
        content: str, 
        model: str = None, 
        usage: UsageInfo = None,
        finish_reason: str = None,
        request_id: str = None
    ) -> ChatResponse:
        """创建响应对象"""
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        return ChatResponse(
            message=message,
            usage=usage,
            model=model,
            finish_reason=finish_reason,
            provider=self.provider_name,
            request_id=request_id
        )
    
    async def _handle_error(self, error: Exception, context: str = "") -> None:
        """统一错误处理"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        
        # 根据错误类型抛出相应的异常
        if "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
            raise AuthenticationError(error_msg, provider=self.provider_name)
        elif "rate limit" in str(error).lower() or "quota" in str(error).lower():
            raise RateLimitError(error_msg, provider=self.provider_name)
        elif "model" in str(error).lower() and "not found" in str(error).lower():
            raise ModelNotFoundError(error_msg, provider=self.provider_name)
        else:
            raise AdapterError(error_msg, provider=self.provider_name)
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def _log_request(self, request: ChatRequest) -> None:
        """记录请求日志"""
        self.logger.info(
            f"Chat request - Model: {request.model}, "
            f"Messages: {len(request.messages)}, "
            f"Stream: {request.stream}, "
            f"Session: {request.session_id}"
        )
    
    def _log_response(self, response: ChatResponse) -> None:
        """记录响应日志"""
        usage_info = ""
        if response.usage:
            usage_info = f"Tokens: {response.usage.total_tokens}, "
        
        self.logger.info(
            f"Chat response - {usage_info}"
            f"Model: {response.model}, "
            f"Finish: {response.finish_reason}"
        )


class AdapterRegistry:
    """适配器注册表"""
    
    def __init__(self):
        self._adapters: Dict[str, type] = {}
    
    def register(self, name: str, adapter_class: type) -> None:
        """注册适配器"""
        if not issubclass(adapter_class, BaseAIAdapter):
            raise ValueError(f"Adapter class must inherit from BaseAIAdapter")
        
        self._adapters[name] = adapter_class
    
    def get(self, name: str) -> Optional[type]:
        """获取适配器类"""
        return self._adapters.get(name)
    
    def list_adapters(self) -> List[str]:
        """列出所有注册的适配器"""
        return list(self._adapters.keys())
    
    def create_adapter(self, name: str, config: Dict[str, Any]) -> BaseAIAdapter:
        """创建适配器实例"""
        adapter_class = self.get(name)
        if not adapter_class:
            raise ValueError(f"Unknown adapter: {name}")
        
        return adapter_class(config)


# 全局适配器注册表
adapter_registry = AdapterRegistry()
