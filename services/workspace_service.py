"""
工作空间服务 - 统一Flask和FastAPI工作空间业务逻辑
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_service import BaseService
from models.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceStatus,
    WorkspaceSettings,
    WorkspaceStatistics,
    AIProviderConfig,
    ProviderTestResponse
)
from models.schemas.chat import AIProvider


class WorkspaceService(BaseService):
    """工作空间服务 - 统一Flask和FastAPI实现"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
    
    async def create_workspace(self, owner_id: str, workspace_data: WorkspaceCreate) -> WorkspaceResponse:
        """创建新工作空间"""
        try:
            workspace_id = str(uuid.uuid4())
            
            # 创建默认设置
            settings = workspace_data.settings or WorkspaceSettings()
            
            workspace = WorkspaceResponse(
                id=workspace_id,
                name=workspace_data.name,
                description=workspace_data.description,
                owner_id=owner_id,
                status=WorkspaceStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                settings=settings,
                member_count=1,  # 创建者
                session_count=0,
                message_count=0,
                is_active=True
            )
            
            # 缓存工作空间信息
            await self.set_cache(f"workspace:{workspace_id}", workspace.json())
            
            return workspace
            
        except Exception as e:
            self.logger.error(f"Create workspace error: {str(e)}")
            raise Exception(f"创建工作空间错误: {str(e)}")
    
    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceResponse]:
        """获取工作空间详情"""
        try:
            # 先从缓存获取
            cached_workspace = await self.get_cache(f"workspace:{workspace_id}")
            if cached_workspace:
                return WorkspaceResponse.parse_raw(cached_workspace)
            
            # 模拟从数据库获取
            # 这里应该实现真实的数据库查询
            return None
            
        except Exception as e:
            self.logger.error(f"Get workspace error: {str(e)}")
            return None
    
    async def update_workspace(self, workspace_id: str, update_data: WorkspaceUpdate) -> Optional[WorkspaceResponse]:
        """更新工作空间"""
        try:
            workspace = await self.get_workspace(workspace_id)
            if not workspace:
                return None
            
            # 更新字段
            if update_data.name is not None:
                workspace.name = update_data.name
            
            if update_data.description is not None:
                workspace.description = update_data.description
            
            if update_data.settings is not None:
                workspace.settings = update_data.settings
            
            if update_data.status is not None:
                workspace.status = update_data.status
            
            workspace.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"workspace:{workspace_id}", workspace.json())
            
            return workspace
            
        except Exception as e:
            self.logger.error(f"Update workspace error: {str(e)}")
            raise Exception(f"更新工作空间错误: {str(e)}")
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """删除工作空间（软删除）"""
        try:
            workspace = await self.get_workspace(workspace_id)
            if not workspace:
                return False
            
            # 软删除 - 更新状态
            workspace.status = WorkspaceStatus.DELETED
            workspace.is_active = False
            workspace.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"workspace:{workspace_id}", workspace.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Delete workspace error: {str(e)}")
            return False
    
    async def list_workspaces(
        self, 
        owner_id: Optional[str] = None,
        page: int = 1, 
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[WorkspaceStatus] = None
    ) -> WorkspaceListResponse:
        """获取工作空间列表"""
        try:
            # 模拟工作空间列表
            workspaces = []
            for i in range(min(size, 5)):  # 模拟最多5个工作空间
                workspace = WorkspaceResponse(
                    id=str(uuid.uuid4()),
                    name=f"工作空间 {i+1}",
                    description=f"这是工作空间 {i+1} 的描述",
                    owner_id=owner_id or "default_owner",
                    status=WorkspaceStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    settings=WorkspaceSettings(),
                    member_count=i + 1,
                    session_count=i * 10,
                    message_count=i * 100,
                    is_active=True
                )
                workspaces.append(workspace)
            
            total = 20  # 模拟总数
            pages = (total + size - 1) // size
            
            return WorkspaceListResponse(
                workspaces=workspaces,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            self.logger.error(f"List workspaces error: {str(e)}")
            raise Exception(f"获取工作空间列表错误: {str(e)}")
    
    async def get_workspace_statistics(self, workspace_id: str) -> WorkspaceStatistics:
        """获取工作空间统计信息"""
        return WorkspaceStatistics(
            total_users=50,
            active_users=35,
            total_sessions=200,
            active_sessions=150,
            total_messages=5000,
            total_tokens=250000,
            total_cost=125.00,
            provider_usage={
                "openai": {"requests": 3000, "tokens": 150000, "cost": 75.00},
                "qwen": {"requests": 1500, "tokens": 75000, "cost": 37.50},
                "claude": {"requests": 500, "tokens": 25000, "cost": 12.50}
            },
            model_usage={
                "gpt-3.5-turbo": {"requests": 2000, "tokens": 100000, "cost": 50.00},
                "gpt-4": {"requests": 1000, "tokens": 50000, "cost": 25.00},
                "qwen-turbo": {"requests": 1500, "tokens": 75000, "cost": 37.50}
            },
            daily_stats=[
                {"date": "2024-01-01", "users": 30, "sessions": 15, "messages": 200, "cost": 10.00},
                {"date": "2024-01-02", "users": 35, "sessions": 20, "messages": 250, "cost": 12.50}
            ],
            hourly_stats=[
                {"hour": "09:00", "requests": 50, "tokens": 2500},
                {"hour": "10:00", "requests": 75, "tokens": 3750}
            ],
            user_activity=[
                {"user_id": "user1", "sessions": 10, "messages": 100, "last_active": "2024-01-02"},
                {"user_id": "user2", "sessions": 8, "messages": 80, "last_active": "2024-01-02"}
            ]
        )
    
    async def test_provider(self, config: AIProviderConfig) -> ProviderTestResponse:
        """测试AI提供商配置"""
        try:
            # 模拟测试提供商连接
            import asyncio
            await asyncio.sleep(0.5)  # 模拟网络延迟
            
            # 模拟测试结果
            if config.provider == AIProvider.OPENAI:
                return ProviderTestResponse(
                    provider=config.provider,
                    is_available=True,
                    response_time=250.5,
                    supported_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
                )
            elif config.provider == AIProvider.QWEN:
                return ProviderTestResponse(
                    provider=config.provider,
                    is_available=True,
                    response_time=180.3,
                    supported_models=["qwen-turbo", "qwen-plus", "qwen-max"]
                )
            else:
                return ProviderTestResponse(
                    provider=config.provider,
                    is_available=False,
                    response_time=0,
                    error_message="提供商暂不支持",
                    supported_models=[]
                )
                
        except Exception as e:
            self.logger.error(f"Test provider error: {str(e)}")
            return ProviderTestResponse(
                provider=config.provider,
                is_available=False,
                response_time=0,
                error_message=str(e),
                supported_models=[]
            )
    
    async def update_provider_configs(self, workspace_id: str, configs: List[AIProviderConfig]) -> bool:
        """更新工作空间的AI提供商配置"""
        try:
            workspace = await self.get_workspace(workspace_id)
            if not workspace:
                return False
            
            # 这里应该保存提供商配置到数据库
            # 现在只是模拟更新
            workspace.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"workspace:{workspace_id}", workspace.json())
            await self.set_cache(f"workspace_providers:{workspace_id}", str(configs))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Update provider configs error: {str(e)}")
            return False
    
    async def get_provider_configs(self, workspace_id: str) -> List[AIProviderConfig]:
        """获取工作空间的AI提供商配置"""
        try:
            # 从缓存获取配置
            cached_configs = await self.get_cache(f"workspace_providers:{workspace_id}")
            if cached_configs:
                # 这里应该解析配置，现在返回默认配置
                pass
            
            # 返回默认配置
            return [
                AIProviderConfig(
                    provider=AIProvider.OPENAI,
                    enabled=True,
                    api_key="sk-xxxxxxxxxxxxxxxx",
                    models=["gpt-3.5-turbo", "gpt-4"],
                    default_model="gpt-3.5-turbo"
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Get provider configs error: {str(e)}")
            return []
