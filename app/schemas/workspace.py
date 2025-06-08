"""
工作空间相关的Pydantic模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from .chat import AIProvider


class WorkspaceSettings(BaseModel):
    """工作空间设置"""
    default_ai_provider: AIProvider = Field(default=AIProvider.OPENAI, description="默认AI提供商")
    default_model: str = Field(default="gpt-3.5-turbo", description="默认模型")
    max_sessions_per_user: int = Field(default=100, ge=1, le=1000, description="每用户最大会话数")
    max_messages_per_session: int = Field(default=1000, ge=1, le=10000, description="每会话最大消息数")
    session_timeout: int = Field(default=3600, ge=300, le=86400, description="会话超时时间(秒)")
    auto_cleanup_days: int = Field(default=30, ge=1, le=365, description="自动清理天数")
    enable_message_history: bool = Field(default=True, description="启用消息历史")
    enable_session_sharing: bool = Field(default=False, description="启用会话分享")
    enable_export: bool = Field(default=True, description="启用导出功能")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000, description="每分钟请求限制")
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=10000, description="每小时请求限制")
    allowed_file_types: List[str] = Field(default_factory=list, description="允许的文件类型")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="最大文件大小(MB)")


class AIProviderConfig(BaseModel):
    """AI提供商配置"""
    provider: AIProvider = Field(description="提供商名称")
    enabled: bool = Field(default=True, description="是否启用")
    api_key: str = Field(description="API密钥")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    models: List[str] = Field(description="支持的模型列表")
    default_model: str = Field(description="默认模型")
    max_requests_per_minute: int = Field(default=60, ge=1, description="每分钟最大请求数")
    timeout: int = Field(default=30, ge=5, le=300, description="请求超时时间(秒)")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="重试次数")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="自定义请求头")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('API密钥无效')
        return v.strip()


class WorkspaceInfo(BaseModel):
    """工作空间信息"""
    id: str = Field(description="工作空间ID")
    name: str = Field(description="工作空间名称")
    description: Optional[str] = Field(default=None, description="工作空间描述")
    owner_id: str = Field(description="所有者ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    settings: WorkspaceSettings = Field(description="工作空间设置")
    member_count: int = Field(default=0, description="成员数量")
    session_count: int = Field(default=0, description="会话数量")
    message_count: int = Field(default=0, description="消息数量")
    is_active: bool = Field(default=True, description="是否激活")


class UpdateWorkspaceRequest(BaseModel):
    """更新工作空间请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="工作空间名称")
    description: Optional[str] = Field(default=None, max_length=500, description="工作空间描述")
    settings: Optional[WorkspaceSettings] = Field(default=None, description="工作空间设置")


class WorkspaceStatistics(BaseModel):
    """工作空间统计信息"""
    total_users: int = Field(description="总用户数")
    active_users: int = Field(description="活跃用户数")
    total_sessions: int = Field(description="总会话数")
    active_sessions: int = Field(description="活跃会话数")
    total_messages: int = Field(description="总消息数")
    total_tokens: int = Field(description="总token数")
    total_cost: float = Field(description="总费用")
    provider_usage: Dict[str, Dict[str, Any]] = Field(description="提供商使用统计")
    model_usage: Dict[str, Dict[str, Any]] = Field(description="模型使用统计")
    daily_stats: List[Dict[str, Any]] = Field(description="每日统计")
    hourly_stats: List[Dict[str, Any]] = Field(description="每小时统计")
    user_activity: List[Dict[str, Any]] = Field(description="用户活动统计")


class ProviderConfigRequest(BaseModel):
    """提供商配置请求"""
    configs: List[AIProviderConfig] = Field(description="提供商配置列表")


class ProviderTestRequest(BaseModel):
    """提供商测试请求"""
    provider: AIProvider = Field(description="提供商名称")
    api_key: str = Field(description="API密钥")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    model: str = Field(description="测试模型")


class ProviderTestResponse(BaseModel):
    """提供商测试响应"""
    provider: AIProvider = Field(description="提供商名称")
    is_available: bool = Field(description="是否可用")
    response_time: float = Field(description="响应时间(毫秒)")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    supported_models: List[str] = Field(description="支持的模型列表")


class WorkspaceUsageReport(BaseModel):
    """工作空间使用报告"""
    workspace_id: str = Field(description="工作空间ID")
    report_period: str = Field(description="报告周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    total_requests: int = Field(description="总请求数")
    total_tokens: int = Field(description="总token数")
    total_cost: float = Field(description="总费用")
    top_users: List[Dict[str, Any]] = Field(description="活跃用户排行")
    top_models: List[Dict[str, Any]] = Field(description="热门模型排行")
    cost_breakdown: Dict[str, float] = Field(description="费用分解")
    usage_trends: List[Dict[str, Any]] = Field(description="使用趋势")


class WorkspaceAlert(BaseModel):
    """工作空间告警"""
    id: str = Field(description="告警ID")
    workspace_id: str = Field(description="工作空间ID")
    alert_type: str = Field(description="告警类型")
    severity: str = Field(description="严重程度")
    title: str = Field(description="告警标题")
    message: str = Field(description="告警消息")
    created_at: datetime = Field(description="创建时间")
    resolved_at: Optional[datetime] = Field(default=None, description="解决时间")
    is_resolved: bool = Field(default=False, description="是否已解决")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class WorkspaceBackup(BaseModel):
    """工作空间备份"""
    id: str = Field(description="备份ID")
    workspace_id: str = Field(description="工作空间ID")
    backup_type: str = Field(description="备份类型")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小(字节)")
    created_at: datetime = Field(description="创建时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    is_encrypted: bool = Field(default=True, description="是否加密")
    checksum: str = Field(description="校验和")


class CreateBackupRequest(BaseModel):
    """创建备份请求"""
    backup_type: str = Field(default="full", regex="^(full|incremental)$", description="备份类型")
    include_messages: bool = Field(default=True, description="包含消息")
    include_sessions: bool = Field(default=True, description="包含会话")
    include_users: bool = Field(default=False, description="包含用户")
    include_settings: bool = Field(default=True, description="包含设置")
    encrypt: bool = Field(default=True, description="是否加密")
    retention_days: int = Field(default=30, ge=1, le=365, description="保留天数")
