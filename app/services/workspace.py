"""
工作空间服务
"""

from app.services.base import BaseService


class WorkspaceService(BaseService):
    """工作空间服务"""
    
    async def get_workspace_info(self):
        """获取工作空间信息"""
        # 模拟工作空间信息
        return {
            "id": "workspace_123",
            "name": "AI Chat Workspace",
            "description": "FastAPI AI聊天系统工作空间"
        }
