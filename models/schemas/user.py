"""
用户相关的Pydantic模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(description="密码", min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱地址")
    role: Optional[UserRole] = Field(default=None, description="用户角色")
    status: Optional[UserStatus] = Field(default=None, description="用户状态")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="用户偏好设置")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱地址")
    full_name: Optional[str] = Field(description="全名")
    role: UserRole = Field(description="用户角色")
    status: UserStatus = Field(description="用户状态")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好设置")
    statistics: Optional[Dict[str, Any]] = Field(default=None, description="用户统计信息")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")
    remember_me: bool = Field(default=False, description="记住我")


class UserLoginResponse(BaseModel):
    """用户登录响应"""
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")
    user: UserResponse = Field(description="用户信息")


class TokenRefresh(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(description="刷新令牌")


class ChangePassword(BaseModel):
    """修改密码请求"""
    current_password: str = Field(description="当前密码")
    new_password: str = Field(description="新密码", min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class ResetPassword(BaseModel):
    """重置密码请求"""
    email: EmailStr = Field(description="邮箱地址")


class ResetPasswordConfirm(BaseModel):
    """确认重置密码请求"""
    token: str = Field(description="重置令牌")
    new_password: str = Field(description="新密码", min_length=8, max_length=128)


class UserPreferences(BaseModel):
    """用户偏好设置"""
    language: str = Field(default="zh-CN", description="界面语言")
    theme: str = Field(default="light", description="主题模式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    default_ai_provider: Optional[str] = Field(default=None, description="默认AI提供商")
    default_model: Optional[str] = Field(default=None, description="默认模型")
    auto_save_sessions: bool = Field(default=True, description="自动保存会话")
    max_sessions: int = Field(default=100, ge=1, le=1000, description="最大会话数")
    notifications: Dict[str, bool] = Field(default_factory=dict, description="通知设置")


class UserStatistics(BaseModel):
    """用户统计信息"""
    total_sessions: int = Field(description="总会话数")
    total_messages: int = Field(description="总消息数")
    total_tokens: int = Field(description="总token数")
    total_cost: float = Field(description="总费用")
    join_days: int = Field(description="加入天数")
    last_active_days: int = Field(description="最后活跃天数")
    favorite_provider: Optional[str] = Field(default=None, description="最常用提供商")
    favorite_model: Optional[str] = Field(default=None, description="最常用模型")
    daily_usage: List[Dict[str, Any]] = Field(description="每日使用统计")


class APIKey(BaseModel):
    """API密钥模型"""
    id: str = Field(description="密钥ID")
    name: str = Field(description="密钥名称")
    key_preview: str = Field(description="密钥预览")
    permissions: List[str] = Field(description="权限列表")
    created_at: datetime = Field(description="创建时间")
    last_used_at: Optional[datetime] = Field(default=None, description="最后使用时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    is_active: bool = Field(description="是否激活")


class CreateAPIKey(BaseModel):
    """创建API密钥请求"""
    name: str = Field(description="密钥名称", min_length=1, max_length=100)
    permissions: List[str] = Field(description="权限列表", min_items=1)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365, description="有效期(天)")


class UpdateAPIKey(BaseModel):
    """更新API密钥请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="密钥名称")
    permissions: Optional[List[str]] = Field(default=None, min_items=1, description="权限列表")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
