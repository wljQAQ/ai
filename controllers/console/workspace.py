"""
控制台工作空间控制器 - 管理后台工作空间管理功能
"""

import logging
from flask import Blueprint
from controllers.base_controller import BaseController
from core.middleware import (
    require_auth,
    validate_json,
    rate_limit,
    handle_errors,
)


class ConsoleWorkspaceController(BaseController):
    """控制台工作空间控制器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_workspace_info(self):
        """获取工作空间信息"""
        try:
            user_id = self.get_user_id()
            
            # 模拟工作空间信息
            workspace_info = {
                "id": "workspace_123",
                "name": "AI Chat Workspace",
                "description": "统一AI聊天系统工作空间",
                "owner_id": user_id,
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
            
            return self.create_response(
                data=workspace_info,
                message="Workspace info retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Console get workspace info error: {str(e)}")
            return self.create_error_response(
                "Failed to get workspace info",
                status_code=500
            )
    
    async def update_workspace_settings(self):
        """更新工作空间设置"""
        try:
            user_id = self.get_user_id()
            data = self.get_json_data()
            
            # 这里应该实现实际的工作空间设置更新逻辑
            # 目前返回成功响应
            
            return self.create_response(
                message="Workspace settings updated successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Console update workspace settings error: {str(e)}")
            return self.create_error_response(
                "Failed to update workspace settings",
                status_code=500
            )
    
    async def get_workspace_statistics(self):
        """获取工作空间统计信息"""
        try:
            user_id = self.get_user_id()
            
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
            
            return self.create_response(
                data=statistics,
                message="Workspace statistics retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Console get workspace statistics error: {str(e)}")
            return self.create_error_response(
                "Failed to get workspace statistics",
                status_code=500
            )
    
    async def get_ai_providers_config(self):
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
            
            return self.create_response(
                data=providers_config,
                message="AI providers config retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Console get AI providers config error: {str(e)}")
            return self.create_error_response(
                "Failed to get AI providers config",
                status_code=500
            )
    
    async def update_ai_provider_config(self, provider_name: str):
        """更新AI提供商配置"""
        try:
            user_id = self.get_user_id()
            data = self.get_json_data()
            
            # 这里应该实现实际的AI提供商配置更新逻辑
            # 目前返回成功响应
            
            return self.create_response(
                message=f"AI provider '{provider_name}' config updated successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Console update AI provider config error: {str(e)}")
            return self.create_error_response(
                "Failed to update AI provider config",
                status_code=500
            )


# 创建蓝图和控制器实例
workspace_bp = Blueprint("workspace", __name__, url_prefix="/workspace")
console_workspace_controller = ConsoleWorkspaceController()


# 注册路由
@workspace_bp.route("/info", methods=["GET"])
@handle_errors
@require_auth
async def get_workspace_info():
    """获取工作空间信息路由"""
    return await console_workspace_controller.get_workspace_info()


@workspace_bp.route("/settings", methods=["PUT"])
@handle_errors
@require_auth
async def update_workspace_settings():
    """更新工作空间设置路由"""
    return await console_workspace_controller.update_workspace_settings()


@workspace_bp.route("/statistics", methods=["GET"])
@handle_errors
@require_auth
async def get_workspace_statistics():
    """获取工作空间统计信息路由"""
    return await console_workspace_controller.get_workspace_statistics()


@workspace_bp.route("/ai-providers", methods=["GET"])
@handle_errors
@require_auth
async def get_ai_providers_config():
    """获取AI提供商配置路由"""
    return await console_workspace_controller.get_ai_providers_config()


@workspace_bp.route("/ai-providers/<provider_name>", methods=["PUT"])
@handle_errors
@require_auth
async def update_ai_provider_config(provider_name: str):
    """更新AI提供商配置路由"""
    return await console_workspace_controller.update_ai_provider_config(provider_name)
