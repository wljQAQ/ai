"""
FastAPI 依赖注入
"""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
# 延迟导入以避免循环依赖
from app.schemas.user import UserResponse


# 安全相关
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """获取当前用户ID"""
    if not credentials:
        # 开发环境允许无认证访问
        if settings.DEBUG:
            return "dev_user_123"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: str = Depends(get_current_user_id)
) -> "UserResponse":
    """获取当前用户信息"""
    from app.services.user import UserService
    from app.schemas.user import UserResponse, UserRole, UserStatus
    from datetime import datetime

    # 简化实现，直接返回模拟用户
    if user_id == "dev_user_123":
        return UserResponse(
            id="dev_user_123",
            username="dev_user",
            email="dev@example.com",
            full_name="开发用户",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="用户不存在"
    )


async def get_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """获取管理员用户（权限检查）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_request_id(request: Request) -> str:
    """获取请求ID"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
    return request_id


# 简化的服务依赖
async def get_chat_service():
    """获取聊天服务"""
    from app.services.chat import ChatService
    return ChatService()


async def get_session_service():
    """获取会话服务"""
    from app.services.session import SessionService
    return SessionService()


async def get_workspace_service():
    """获取工作空间服务"""
    from app.services.workspace import WorkspaceService
    return WorkspaceService()


# 分页依赖
def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> dict:
    """获取分页参数"""
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20
    
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size
    }


# 验证依赖
def validate_session_id(session_id: str) -> str:
    """验证会话ID格式"""
    if not session_id or len(session_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID"
        )
    return session_id


def validate_message_content(content: str) -> str:
    """验证消息内容"""
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容不能为空"
        )
    
    if len(content) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容过长"
        )
    
    return content.strip()


# 简化的限流依赖
async def rate_limit_60_per_minute():
    """60次/分钟限流"""
    # 简化实现，实际项目中应该使用Redis
    pass


async def rate_limit_30_per_minute():
    """30次/分钟限流"""
    # 简化实现，实际项目中应该使用Redis
    pass


async def rate_limit_10_per_minute():
    """10次/分钟限流"""
    # 简化实现，实际项目中应该使用Redis
    pass
