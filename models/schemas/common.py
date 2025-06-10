"""
共享的基础数据模型
包含在多个模块中使用的通用定义
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举 - 统一定义"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class ProviderType(str, Enum):
    """AI提供商类型枚举 - 统一定义"""
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    GEMINI = "gemini"
    DIFY = "dify"


class TokenUsage(BaseModel):
    """Token使用情况 - 统一定义"""
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    total_tokens: int = Field(..., description="总token数")


class BaseMessage(BaseModel):
    """基础消息模型 - 统一定义"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容", min_length=1)
    name: Optional[str] = Field(default=None, description="发送者名称")
    function_call: Optional[Dict[str, Any]] = Field(default=None, description="函数调用")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('消息内容不能为空')
        return v.strip()


class ModelType(str, Enum):
    """模型类型枚举"""
    LLM = "llm"
    EMBEDDING = "embedding"
    TTS = "tts"
    STT = "stt"
    IMAGE = "image"
