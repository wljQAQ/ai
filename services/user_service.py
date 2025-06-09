"""
用户服务 - 统一Flask和FastAPI用户业务逻辑
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_service import BaseService
from models.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRole,
    UserStatus,
    UserStatistics,
    UserPreferences
)


class UserService(BaseService):
    """用户服务 - 统一Flask和FastAPI实现"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建新用户"""
        try:
            # 验证用户名和邮箱唯一性（模拟）
            if await self.get_user_by_username(user_data.username):
                raise ValueError("用户名已存在")
            
            if await self.get_user_by_email(user_data.email):
                raise ValueError("邮箱已存在")
            
            user_id = str(uuid.uuid4())
            
            user = UserResponse(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                preferences={}
            )
            
            # 缓存用户信息
            await self.set_cache(f"user:{user_id}", user.json())
            await self.set_cache(f"user_by_username:{user_data.username}", user_id)
            await self.set_cache(f"user_by_email:{user_data.email}", user_id)
            
            return user
            
        except Exception as e:
            self.logger.error(f"Create user error: {str(e)}")
            raise Exception(f"创建用户错误: {str(e)}")
    
    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        try:
            # 先从缓存获取
            cached_user = await self.get_cache(f"user:{user_id}")
            if cached_user:
                return UserResponse.parse_raw(cached_user)
            
            # 模拟从数据库获取
            # 这里应该实现真实的数据库查询
            return None
            
        except Exception as e:
            self.logger.error(f"Get user error: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """根据用户名获取用户"""
        try:
            # 先从缓存获取用户ID
            user_id = await self.get_cache(f"user_by_username:{username}")
            if user_id:
                return await self.get_user(user_id)
            
            # 模拟查询
            return None
            
        except Exception as e:
            self.logger.error(f"Get user by username error: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户"""
        try:
            # 先从缓存获取用户ID
            user_id = await self.get_cache(f"user_by_email:{email}")
            if user_id:
                return await self.get_user(user_id)
            
            # 模拟查询
            return None
            
        except Exception as e:
            self.logger.error(f"Get user by email error: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[UserResponse]:
        """更新用户信息"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return None
            
            # 更新字段
            if update_data.full_name is not None:
                user.full_name = update_data.full_name
            
            if update_data.email is not None:
                # 检查邮箱唯一性
                existing_user = await self.get_user_by_email(update_data.email)
                if existing_user and existing_user.id != user_id:
                    raise ValueError("邮箱已存在")
                user.email = update_data.email
            
            if update_data.role is not None:
                user.role = update_data.role
            
            if update_data.status is not None:
                user.status = update_data.status
            
            if update_data.preferences is not None:
                user.preferences.update(update_data.preferences)
            
            user.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"user:{user_id}", user.json())
            
            return user
            
        except Exception as e:
            self.logger.error(f"Update user error: {str(e)}")
            raise Exception(f"更新用户错误: {str(e)}")
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # 软删除 - 更新状态
            user.status = UserStatus.DELETED
            user.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"user:{user_id}", user.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Delete user error: {str(e)}")
            return False
    
    async def list_users(
        self, 
        page: int = 1, 
        size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> Dict[str, Any]:
        """获取用户列表"""
        try:
            # 模拟用户列表
            users = []
            for i in range(min(size, 10)):  # 模拟最多10个用户
                user = UserResponse(
                    id=str(uuid.uuid4()),
                    username=f"user_{i+1}",
                    email=f"user{i+1}@example.com",
                    full_name=f"用户 {i+1}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    preferences={}
                )
                users.append(user)
            
            total = 100  # 模拟总数
            pages = (total + size - 1) // size
            
            return {
                "users": users,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
            
        except Exception as e:
            self.logger.error(f"List users error: {str(e)}")
            raise Exception(f"获取用户列表错误: {str(e)}")
    
    async def get_user_statistics(self, user_id: str) -> UserStatistics:
        """获取用户统计信息"""
        return UserStatistics(
            total_sessions=25,
            total_messages=500,
            total_tokens=25000,
            total_cost=12.50,
            join_days=30,
            last_active_days=1,
            favorite_provider="openai",
            favorite_model="gpt-3.5-turbo",
            daily_usage=[
                {"date": "2024-01-01", "messages": 20, "tokens": 1000, "cost": 0.50},
                {"date": "2024-01-02", "messages": 25, "tokens": 1250, "cost": 0.63}
            ]
        )
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """更新用户偏好设置"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # 更新偏好设置
            user.preferences.update(preferences.dict())
            user.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"user:{user_id}", user.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Update user preferences error: {str(e)}")
            return False
    
    async def activate_user(self, user_id: str) -> bool:
        """激活用户"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"user:{user_id}", user.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Activate user error: {str(e)}")
            return False
    
    async def suspend_user(self, user_id: str) -> bool:
        """暂停用户"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.status = UserStatus.SUSPENDED
            user.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"user:{user_id}", user.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Suspend user error: {str(e)}")
            return False
