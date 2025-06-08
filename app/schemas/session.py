"""
会话相关的Pydantic模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from .chat import AIProvider


class SessionConfig(BaseModel):
    """会话配置模型"""
    ai_provider: AIProvider = Field(description="AI提供商")
    model: str = Field(description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=8000, description="最大token数")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="存在惩罚")
    system_prompt: Optional[str] = Field(default=None, max_length=2000, description="系统提示词")
    stop_sequences: Optional[List[str]] = Field(default=None, description="停止序列")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(default=None, max_length=100, description="会话标题")
    ai_provider: AIProvider = Field(default=AIProvider.OPENAI, description="AI提供商")
    model: str = Field(default="gpt-3.5-turbo", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=8000, description="最大token数")
    system_prompt: Optional[str] = Field(default=None, max_length=2000, description="系统提示词")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(default=None, max_length=100, description="会话标题")
    config: Optional[SessionConfig] = Field(default=None, description="会话配置")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('标题不能为空')
        return v.strip() if v else None


class SessionResponse(BaseModel):
    """会话响应模型"""
    id: str = Field(description="会话ID")
    title: str = Field(description="会话标题")
    user_id: str = Field(description="用户ID")
    config: SessionConfig = Field(description="会话配置")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    message_count: int = Field(default=0, description="消息数量")
    last_message_at: Optional[datetime] = Field(default=None, description="最后消息时间")
    is_active: bool = Field(default=True, description="是否激活")


class SessionSummary(BaseModel):
    """会话摘要模型（用于列表显示）"""
    id: str = Field(description="会话ID")
    title: str = Field(description="会话标题")
    ai_provider: AIProvider = Field(description="AI提供商")
    model: str = Field(description="模型名称")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    message_count: int = Field(default=0, description="消息数量")
    last_message_at: Optional[datetime] = Field(default=None, description="最后消息时间")
    last_message_preview: Optional[str] = Field(default=None, max_length=100, description="最后消息预览")


class SessionListRequest(BaseModel):
    """会话列表请求"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")
    ai_provider: Optional[AIProvider] = Field(default=None, description="筛选AI提供商")
    is_active: Optional[bool] = Field(default=None, description="筛选激活状态")
    sort_by: str = Field(default="updated_at", description="排序字段")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="排序方向")


class SessionStatistics(BaseModel):
    """会话统计信息"""
    total_sessions: int = Field(description="总会话数")
    active_sessions: int = Field(description="活跃会话数")
    total_messages: int = Field(description="总消息数")
    total_tokens: int = Field(description="总token数")
    provider_distribution: Dict[str, int] = Field(description="提供商分布")
    model_distribution: Dict[str, int] = Field(description="模型分布")
    daily_sessions: List[Dict[str, Any]] = Field(description="每日会话统计")
    daily_messages: List[Dict[str, Any]] = Field(description="每日消息统计")


class SessionMessage(BaseModel):
    """会话消息模型"""
    id: str = Field(description="消息ID")
    session_id: str = Field(description="会话ID")
    role: str = Field(description="消息角色")
    content: str = Field(description="消息内容")
    model: Optional[str] = Field(default=None, description="使用的模型")
    provider: Optional[AIProvider] = Field(default=None, description="AI提供商")
    created_at: datetime = Field(description="创建时间")
    prompt_tokens: Optional[int] = Field(default=None, description="输入token数")
    completion_tokens: Optional[int] = Field(default=None, description="输出token数")
    total_tokens: Optional[int] = Field(default=None, description="总token数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class SessionMessagesRequest(BaseModel):
    """会话消息列表请求"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=50, ge=1, le=200, description="每页大小")
    role: Optional[str] = Field(default=None, description="筛选消息角色")
    search: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")


class ExportSessionRequest(BaseModel):
    """导出会话请求"""
    session_ids: List[str] = Field(description="会话ID列表", min_items=1, max_items=100)
    format: str = Field(default="json", regex="^(json|csv|markdown)$", description="导出格式")
    include_metadata: bool = Field(default=False, description="是否包含元数据")
    include_statistics: bool = Field(default=False, description="是否包含统计信息")
