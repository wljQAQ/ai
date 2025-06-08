"""
基础Pydantic模型
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# 通用类型变量
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """标准API响应格式"""
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="Success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: Optional[str] = Field(default=None, description="请求ID")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: Optional[str] = Field(default=None, description="请求ID")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """创建分页响应"""
        pages = (total + size - 1) // size
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """健康检查响应"""
    status: HealthStatus = Field(description="服务状态")
    version: str = Field(description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    services: Dict[str, HealthStatus] = Field(default_factory=dict, description="各服务状态")
    uptime: Optional[float] = Field(default=None, description="运行时间(秒)")


class APIKeyInfo(BaseModel):
    """API密钥信息"""
    key_id: str = Field(description="密钥ID")
    name: str = Field(description="密钥名称")
    created_at: datetime = Field(description="创建时间")
    last_used: Optional[datetime] = Field(default=None, description="最后使用时间")
    is_active: bool = Field(default=True, description="是否激活")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
