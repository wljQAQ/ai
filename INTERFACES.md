# 核心接口定义

## 1. AI适配器接口

### 基础适配器接口 (adapters/base.py)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass

@dataclass
class ChatMessage:
    """聊天消息数据结构"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class ChatRequest:
    """聊天请求数据结构"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    session_id: Optional[str] = None

@dataclass
class ChatResponse:
    """聊天响应数据结构"""
    message: ChatMessage
    usage: Optional[Dict] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None

class BaseAIAdapter(ABC):
    """AI适配器基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider_name = self._get_provider_name()
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """获取提供商名称"""
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
    async def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass
```

## 2. 会话管理接口

### 会话服务接口 (services/session_service.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

@dataclass
class Session:
    """会话数据结构"""
    id: str
    user_id: str
    title: str
    ai_provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict] = None

@dataclass
class SessionConfig:
    """会话配置"""
    ai_provider: str
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None

class ISessionService(ABC):
    """会话服务接口"""
    
    @abstractmethod
    async def create_session(self, user_id: str, config: SessionConfig) -> Session:
        """创建新会话"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Session]:
        """获取用户会话列表"""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, user_id: str, **kwargs) -> bool:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    async def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """添加消息到会话"""
        pass
    
    @abstractmethod
    async def get_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """获取会话消息"""
        pass
```

## 3. 聊天服务接口

### 聊天服务接口 (services/chat_service.py)

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class IChatService(ABC):
    """聊天服务接口"""
    
    @abstractmethod
    async def send_message(
        self, 
        session_id: str, 
        user_id: str, 
        message: str,
        stream: bool = False
    ) -> ChatResponse:
        """发送消息"""
        pass
    
    @abstractmethod
    async def send_message_stream(
        self, 
        session_id: str, 
        user_id: str, 
        message: str
    ) -> AsyncGenerator[ChatResponse, None]:
        """流式发送消息"""
        pass
    
    @abstractmethod
    async def regenerate_response(
        self, 
        session_id: str, 
        user_id: str
    ) -> ChatResponse:
        """重新生成回复"""
        pass
    
    @abstractmethod
    async def get_available_providers(self) -> List[str]:
        """获取可用的AI提供商"""
        pass
    
    @abstractmethod
    async def get_provider_models(self, provider: str) -> List[str]:
        """获取提供商支持的模型"""
        pass
```

## 4. 数据仓库接口

### 基础仓库接口 (repositories/base.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class IRepository(ABC):
    """基础仓库接口"""
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        """创建记录"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """列表查询"""
        pass
```

## 5. API响应格式

### 统一响应格式

```python
@dataclass
class APIResponse:
    """API统一响应格式"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

# 成功响应示例
{
    "success": true,
    "data": {
        "session_id": "sess_123",
        "message": "Hello, how can I help you?"
    },
    "message": "Message sent successfully",
    "timestamp": "2024-01-01T12:00:00Z"
}

# 错误响应示例
{
    "success": false,
    "data": null,
    "message": "Invalid session ID",
    "error_code": "INVALID_SESSION",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## 6. 配置接口

### 配置管理接口

```python
class IConfigManager(ABC):
    """配置管理接口"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def get_ai_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取AI提供商配置"""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        pass
    
    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        pass
```
