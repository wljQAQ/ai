"""
聊天相关的Pydantic模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class AIProvider(str, Enum):
    """AI提供商枚举"""
    OPENAI = "openai"
    QWEN = "qwen"
    DIFY = "dify"
    CLAUDE = "claude"
    GEMINI = "gemini"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole = Field(description="消息角色")
    content: str = Field(description="消息内容", min_length=1)
    name: Optional[str] = Field(default=None, description="发送者名称")
    function_call: Optional[Dict[str, Any]] = Field(default=None, description="函数调用")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: str = Field(description="会话ID")
    message: str = Field(description="用户消息", min_length=1, max_length=10000)
    stream: bool = Field(default=False, description="是否流式响应")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8000, description="最大token数")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('消息内容不能为空')
        return v.strip()


class ChatCompletionRequest(BaseModel):
    """OpenAI兼容的聊天完成请求"""
    messages: List[ChatMessage] = Field(description="消息列表", min_items=1)
    model: str = Field(default="gpt-3.5-turbo", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8000, description="最大token数")
    stream: bool = Field(default=False, description="是否流式响应")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="存在惩罚")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="停止序列")
    user: Optional[str] = Field(default=None, description="用户标识")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str = Field(description="消息ID")
    session_id: str = Field(description="会话ID")
    role: MessageRole = Field(description="消息角色")
    content: str = Field(description="响应内容")
    model: str = Field(description="使用的模型")
    provider: AIProvider = Field(description="AI提供商")
    created_at: datetime = Field(description="创建时间")
    prompt_tokens: Optional[int] = Field(default=None, description="输入token数")
    completion_tokens: Optional[int] = Field(default=None, description="输出token数")
    total_tokens: Optional[int] = Field(default=None, description="总token数")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class ChatCompletionResponse(BaseModel):
    """OpenAI兼容的聊天完成响应"""
    id: str = Field(description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(description="创建时间戳")
    model: str = Field(description="模型名称")
    choices: List[Dict[str, Any]] = Field(description="选择列表")
    usage: Optional[Dict[str, int]] = Field(default=None, description="token使用情况")


class StreamChatResponse(BaseModel):
    """流式聊天响应模型"""
    id: str = Field(description="消息ID")
    session_id: str = Field(description="会话ID")
    delta: str = Field(description="增量内容")
    model: str = Field(description="使用的模型")
    provider: AIProvider = Field(description="AI提供商")
    created_at: datetime = Field(description="创建时间")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class RegenerateRequest(BaseModel):
    """重新生成请求模型"""
    session_id: str = Field(description="会话ID")
    message_id: Optional[str] = Field(default=None, description="要重新生成的消息ID")


class ProviderInfo(BaseModel):
    """AI提供商信息"""
    name: AIProvider = Field(description="提供商名称")
    display_name: str = Field(description="显示名称")
    description: str = Field(description="描述")
    models: List[str] = Field(description="支持的模型列表")
    is_available: bool = Field(description="是否可用")
    default_model: str = Field(description="默认模型")


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(description="模型ID")
    name: str = Field(description="模型名称")
    provider: AIProvider = Field(description="提供商")
    description: str = Field(description="模型描述")
    max_tokens: int = Field(description="最大token数")
    input_price: Optional[float] = Field(default=None, description="输入价格(每1K tokens)")
    output_price: Optional[float] = Field(default=None, description="输出价格(每1K tokens)")
    is_available: bool = Field(description="是否可用")


class ChatStatistics(BaseModel):
    """聊天统计信息"""
    total_messages: int = Field(description="总消息数")
    total_tokens: int = Field(description="总token数")
    total_cost: float = Field(description="总费用")
    provider_stats: Dict[str, Dict[str, Any]] = Field(description="各提供商统计")
    model_stats: Dict[str, Dict[str, Any]] = Field(description="各模型统计")
    daily_stats: List[Dict[str, Any]] = Field(description="每日统计")


class SimpleChatRequest(BaseModel):
    """简化聊天请求（用于第三方API）"""
    message: str = Field(description="用户消息", min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default=None, description="会话ID（可选）")
    model: str = Field(default="gpt-3.5-turbo", description="模型名称")
    stream: bool = Field(default=False, description="是否流式响应")


class SimpleChatResponse(BaseModel):
    """简化聊天响应（用于第三方API）"""
    session_id: str = Field(description="会话ID")
    message: str = Field(description="AI回复")
    model: str = Field(description="使用的模型")
    created_at: datetime = Field(description="创建时间")
