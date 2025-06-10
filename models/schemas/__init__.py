"""
数据验证模式包
"""

from .base import (
    BaseResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    HealthStatus,
    HealthCheck,
    APIKeyInfo
)
from .chat import (
    ChatRequest,
    ChatResponse,
    StreamChatResponse,
    RegenerateRequest,
    ProviderInfo,
    ModelInfo,
    ChatStatistics,
    AIProvider,
    MessageRole
)
from .session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionStatus
)
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRole,
    UserStatus
)
from .workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceStatus
)
from .ai_provider import (
    UnifiedChatRequest,
    UnifiedChatResponse,
    UnifiedStreamResponse,
    UnifiedMessage,
    BaseProviderConfig,
    OpenAIConfig,
    ClaudeConfig
)


__all__ = [
    # Base schemas
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthStatus",
    "HealthCheck",
    "APIKeyInfo",

    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "StreamChatResponse",
    "RegenerateRequest",
    "ProviderInfo",
    "ModelInfo",
    "ChatStatistics",
    "AIProvider",
    "MessageRole",

    # Session schemas
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    "SessionStatus",

    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLoginRequest",
    "UserLoginResponse",
    "UserRole",
    "UserStatus",

    # Workspace schemas
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "WorkspaceListResponse",
    "WorkspaceStatus",

    # AI Provider schemas
    "UnifiedChatRequest",
    "UnifiedChatResponse",
    "UnifiedStreamResponse",
    "UnifiedMessage",
    "BaseProviderConfig",
    "OpenAIConfig",
    "ClaudeConfig",
]
