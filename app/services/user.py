"""
用户服务
"""

from datetime import datetime
from typing import Optional

from app.services.base import BaseService
from app.schemas.user import UserResponse, UserRole, UserStatus


class UserService(BaseService):
    """用户服务"""
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        # 模拟用户数据
        users = {
            "admin_123": UserResponse(
                id="admin_123",
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "user_123": UserResponse(
                id="user_123",
                username="user",
                email="user@example.com",
                full_name="普通用户",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "dev_user_123": UserResponse(
                id="dev_user_123",
                username="dev_user",
                email="dev@example.com",
                full_name="开发用户",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        }
        
        return users.get(user_id)
