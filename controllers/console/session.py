"""
控制台会话控制器 - FastAPI实现
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from services.session_service import SessionService
from services.auth_service import AuthService
from models.schemas.base import BaseResponse
from models.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse,
    SessionListResponse, SessionStatistics
)
from models.schemas.user import UserResponse

# 创建FastAPI路由器
router = APIRouter(prefix="/sessions", tags=["Console Sessions"])

# 依赖注入函数
def get_session_service() -> SessionService:
    """获取会话服务实例"""
    return SessionService()

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()

def get_current_user_id() -> str:
    """获取当前用户ID（模拟）"""
    return "user_123"

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
@router.post("", response_model=BaseResponse[SessionResponse])
async def create_session(
    request: SessionCreate,
    current_user_id: str = Depends(get_current_user_id),
    session_service: SessionService = Depends(get_session_service)
):
    """创建会话"""
    try:
        response = await session_service.create_session(current_user_id, request)

        return BaseResponse(
            data=response,
            message="会话创建成功"
        )
    except Exception as e:
        logging.error(f"Console create session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )

@router.get("", response_model=BaseResponse[SessionListResponse])
async def list_sessions(
    page: int = 1,
    size: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    session_service: SessionService = Depends(get_session_service)
):
    """获取会话列表"""
    try:
        response = await session_service.list_sessions(
            user_id=current_user_id,
            page=page,
            size=size
        )

        return BaseResponse(
            data=response,
            message="会话列表获取成功"
        )
    except Exception as e:
        logging.error(f"Console list sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )

@router.get("/{session_id}", response_model=BaseResponse[SessionResponse])
async def get_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session_service: SessionService = Depends(get_session_service)
):
    """获取会话详情"""
    try:
        response = await session_service.get_session(session_id, current_user_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        return BaseResponse(
            data=response,
            message="会话详情获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Console get session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话详情失败: {str(e)}"
        )

@router.put("/{session_id}", response_model=BaseResponse[SessionResponse])
async def update_session(
    session_id: str,
    request: SessionUpdate,
    current_user_id: str = Depends(get_current_user_id),
    session_service: SessionService = Depends(get_session_service)
):
    """更新会话"""
    try:
        response = await session_service.update_session(session_id, current_user_id, request)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        return BaseResponse(
            data=response,
            message="会话更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Console update session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话失败: {str(e)}"
        )

@router.delete("/{session_id}", response_model=BaseResponse[dict])
async def delete_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session_service: SessionService = Depends(get_session_service)
):
    """删除会话"""
    try:
        success = await session_service.delete_session(session_id, current_user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        return BaseResponse(
            data={"session_id": session_id},
            message="会话删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Console delete session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )

@router.get("/statistics", response_model=BaseResponse[SessionStatistics])
async def get_session_statistics(
    _: UserResponse = Depends(get_admin_user),
    session_service: SessionService = Depends(get_session_service)
):
    """获取会话统计信息"""
    try:
        statistics = await session_service.get_session_statistics("user_123")

        return BaseResponse(
            data=statistics,
            message="会话统计信息获取成功"
        )
    except Exception as e:
        logging.error(f"Console get session statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话统计信息失败: {str(e)}"
        )
