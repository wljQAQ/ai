"""
控制台工作空间控制器 - FastAPI实现
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from services.auth_service import AuthService
from models.schemas.base import BaseResponse
from models.schemas.user import UserResponse

# 创建FastAPI路由器
router = APIRouter(prefix="/workspace", tags=["Console Workspace"])

# 依赖注入函数
def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()

def get_admin_user() -> UserResponse:
    """获取管理员用户（模拟）"""
    from datetime import datetime
    from models.schemas.user import UserRole, UserStatus
    return UserResponse(
        id="admin_123",
        username="admin",
        email="admin@example.com",
        full_name="系统管理员",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# FastAPI路由定义
@router.get("/info", response_model=BaseResponse[Dict[str, Any]])
async def get_workspace_info(
    _: UserResponse = Depends(get_admin_user)
):
    """获取工作空间信息"""
    try:
        # 模拟工作空间信息
        workspace_info = {
            "id": "workspace_123",
            "name": "AI Chat Workspace",
            "description": "统一AI聊天系统工作空间",
            "owner_id": "admin_123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "settings": {
                "default_ai_provider": "openai",
                "default_model": "gpt-3.5-turbo",
                "max_sessions_per_user": 100,
                "session_timeout": 3600
            },
            "statistics": {
                "total_sessions": 0,
                "total_messages": 0,
                "active_users": 1
            }
        }

        return BaseResponse(
            data=workspace_info,
            message="工作空间信息获取成功"
        )
    except Exception as e:
        logging.error(f"Console get workspace info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作空间信息失败: {str(e)}"
        )

@router.get("/statistics", response_model=BaseResponse[Dict[str, Any]])
async def get_workspace_statistics(
    _: UserResponse = Depends(get_admin_user)
):
    """获取工作空间统计信息"""
    try:
        # 模拟统计信息
        statistics = {
            "sessions": {
                "total": 0,
                "active": 0,
                "today": 0,
                "this_week": 0,
                "this_month": 0
            },
            "messages": {
                "total": 0,
                "today": 0,
                "this_week": 0,
                "this_month": 0
            },
            "users": {
                "total": 1,
                "active": 1,
                "new_today": 0,
                "new_this_week": 0,
                "new_this_month": 0
            },
            "ai_providers": {
                "openai": {
                    "requests": 0,
                    "tokens_used": 0,
                    "cost": 0.0
                },
                "qwen": {
                    "requests": 0,
                    "tokens_used": 0,
                    "cost": 0.0
                }
            }
        }

        return BaseResponse(
            data=statistics,
            message="工作空间统计信息获取成功"
        )
    except Exception as e:
        logging.error(f"Console get workspace statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作空间统计信息失败: {str(e)}"
        )

@router.get("/ai-providers", response_model=BaseResponse[Dict[str, Any]])
async def get_ai_providers_config(
    _: UserResponse = Depends(get_admin_user)
):
    """获取AI提供商配置"""
    try:
        # 模拟AI提供商配置
        providers_config = {
            "openai": {
                "enabled": True,
                "api_key": "sk-***",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "default_model": "gpt-3.5-turbo"
            },
            "qwen": {
                "enabled": True,
                "api_key": "sk-***",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "models": ["qwen-turbo", "qwen-plus"],
                "default_model": "qwen-turbo"
            },
            "dify": {
                "enabled": False,
                "api_key": "",
                "base_url": "",
                "models": [],
                "default_model": ""
            }
        }

        return BaseResponse(
            data=providers_config,
            message="AI提供商配置获取成功"
        )
    except Exception as e:
        logging.error(f"Console get AI providers config error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取AI提供商配置失败: {str(e)}"
        )
