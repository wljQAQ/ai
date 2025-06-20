"""
AI 提供商统一数据模型
定义所有 AI 提供商的统一请求/响应格式
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator

# 导入共享的基础定义
from .common import (
    MessageRole,
    ProviderType,
    TokenUsage,
    BaseMessage,
    ModelType,
    ContentType,
)


# ============= 统一请求模型 =============
# 使用共享的 BaseMessage 作为 UnifiedMessage 的别名
UnifiedMessage = BaseMessage


class UnifiedChatRequest(BaseModel):
    """统一聊天请求格式"""

    messages: List[UnifiedMessage] = Field(..., description="消息列表", min_items=1)
    model: str = Field(..., description="模型名称")
    temperature: float = Field(default=0.7, gt=0.0, lt=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(
        default=None, ge=1, le=32000, description="最大token数"
    )
    stream: bool = Field(default=False, description="是否流式响应")
    top_p: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="核采样参数"
    )
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="频率惩罚"
    )
    presence_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="存在惩罚"
    )
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="停止序列")
    user: Optional[str] = Field(default=None, description="用户标识")

    # 扩展参数，用于特定提供商的特殊需求
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="扩展参数")


class UnifiedStreamResponseContent(BaseModel):
    """统一流式响应内容Content格式  目前只支持文本"""

    type: ContentType = Field(default=ContentType.TEXT, description="内容类型")
    text: Optional[str] = Field(default=None, description="文本内容")
    reasoning: Optional[str] = Field(default=None, description="推理内容")


# ============= 统一响应模型 =============
class UnifiedChatResponse(BaseModel):
    """统一聊天响应格式"""

    id: str = Field(..., description="响应ID")
    content: str = Field(..., description="响应内容")
    model: str = Field(..., description="使用的模型")
    provider: ProviderType = Field(..., description="AI提供商")
    usage: TokenUsage = Field(..., description="token使用情况")
    finish_reason: str = Field(..., description="结束原因")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    # 性能指标
    latency_ms: Optional[int] = Field(default=None, description="响应延迟(毫秒)")

    # 扩展字段，用于特定提供商的额外信息
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")


class UnifiedStreamResponse(BaseModel):
    """统一流式响应格式"""

    id: str = Field(..., description="响应ID")
    delta: str = Field(..., description="增量内容")
    reasoning: Optional[str] = Field(default=None, description="推理内容")
    content: UnifiedStreamResponseContent = Field(..., description="内容")
    model: str = Field(..., description="使用的模型")
    provider: ProviderType = Field(..., description="AI提供商")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


# ============= 提供商配置模型 =============
class BaseProviderConfig(BaseModel):
    """基础提供商配置"""

    provider_type: ProviderType = Field(..., description="提供商类型")
    api_key: str = Field(..., description="API密钥", min_length=1)
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="请求超时时间(秒)"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="重试延迟(秒)")

    # 支持的模型列表
    supported_models: List[str] = Field(
        default_factory=list, description="支持的模型列表"
    )

    # 默认参数
    default_model: str = Field(default="", description="默认模型")
    default_temperature: float = Field(default=0.7, description="默认温度")
    default_max_tokens: Optional[int] = Field(
        default=None, description="默认最大token数"
    )

    # 扩展配置
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="扩展配置")


class OpenAIConfig(BaseProviderConfig):
    """OpenAI 配置模型"""

    provider_type: ProviderType = Field(
        default=ProviderType.OPENAI, description="提供商类型"
    )
    supported_models: List[str] = Field(
        default=[
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-32k",
            "gpt-4o",
            "gpt-4o-mini",
        ],
        description="支持的模型列表",
    )
    default_model: str = Field(default="gpt-3.5-turbo", description="默认模型")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v.startswith("sk-"):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v


class ClaudeConfig(BaseProviderConfig):
    """Claude 配置模型"""

    provider_type: ProviderType = Field(
        default=ProviderType.CLAUDE, description="提供商类型"
    )
    supported_models: List[str] = Field(
        default=[
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
        ],
        description="支持的模型列表",
    )
    default_model: str = Field(
        default="claude-3-haiku-20240307", description="默认模型"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v.startswith("sk-ant-"):
            raise ValueError('Claude API key must start with "sk-ant-"')
        return v


class DifyConfig(BaseProviderConfig):
    """Dify 配置模型"""

    provider_type: ProviderType = Field(
        default=ProviderType.DIFY, description="提供商类型"
    )
    base_url: str = Field(default="https://api.dify.ai", description="Dify API 基础URL")
    supported_models: List[str] = Field(
        default=[
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "claude-3-haiku",
            "claude-3-sonnet",
            "claude-3-opus",
        ],
        description="支持的模型列表（取决于 Dify 应用配置）",
    )
    default_model: str = Field(default="gpt-3.5-turbo", description="默认模型")

    # Dify 特有配置
    app_id: Optional[str] = Field(
        default=None, description="Dify 应用ID（可选，用于多应用场景）"
    )
    conversation_id: Optional[str] = Field(
        default=None, description="对话ID（用于维持对话状态）"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Dify API key cannot be empty")
        # Dify API key 通常是较长的字符串，不像 OpenAI 有固定前缀
        if len(v) < 10:
            raise ValueError("Dify API key seems too short")
        return v


# ============= 错误处理模型 =============
class ProviderErrorInfo(BaseModel):
    """提供商错误信息数据模型"""

    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    provider: ProviderType = Field(..., description="出错的提供商")
    retry_after: Optional[int] = Field(default=None, description="重试等待时间(秒)")
    is_retryable: bool = Field(default=False, description="是否可重试")


class ProviderError(Exception):
    """AI提供商异常类"""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        provider: ProviderType,
        retry_after: Optional[int] = None,
        is_retryable: bool = False,
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.provider = provider
        self.retry_after = retry_after
        self.is_retryable = is_retryable
        super().__init__(error_message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "provider": self.provider.value,
            "retry_after": self.retry_after,
            "is_retryable": self.is_retryable,
        }

    def to_model(self) -> ProviderErrorInfo:
        """转换为Pydantic模型"""
        return ProviderErrorInfo(
            error_code=self.error_code,
            error_message=self.error_message,
            provider=self.provider,
            retry_after=self.retry_after,
            is_retryable=self.is_retryable,
        )


# ============= 性能监控模型 =============
class ProviderMetrics(BaseModel):
    """提供商性能指标"""

    provider: ProviderType = Field(..., description="提供商")
    model: str = Field(..., description="模型名称")
    request_count: int = Field(default=0, description="请求次数")
    success_count: int = Field(default=0, description="成功次数")
    error_count: int = Field(default=0, description="错误次数")
    avg_latency_ms: float = Field(default=0.0, description="平均延迟(毫秒)")
    total_tokens: int = Field(default=0, description="总token数")
    total_cost: float = Field(default=0.0, description="总费用")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最后更新时间"
    )
