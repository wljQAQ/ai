"""
自定义异常和异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback

from app.schemas.base import ErrorResponse


class AIServiceException(Exception):
    """AI服务异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class SessionNotFoundException(Exception):
    """会话未找到异常"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.message = f"会话 {session_id} 不存在"
        super().__init__(self.message)


class UserNotFoundException(Exception):
    """用户未找到异常"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.message = f"用户 {user_id} 不存在"
        super().__init__(self.message)


class InsufficientPermissionException(Exception):
    """权限不足异常"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        self.message = f"需要权限: {required_permission}"
        super().__init__(self.message)


class RateLimitExceededException(Exception):
    """限流异常"""
    
    def __init__(self, limit: str, retry_after: int = 60):
        self.limit = limit
        self.retry_after = retry_after
        self.message = f"请求频率超过限制: {limit}"
        super().__init__(self.message)


class ValidationException(Exception):
    """验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class DatabaseException(Exception):
    """数据库异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)


class ExternalServiceException(Exception):
    """外部服务异常"""
    
    def __init__(
        self, 
        service_name: str, 
        message: str, 
        status_code: Optional[int] = None
    ):
        self.service_name = service_name
        self.message = message
        self.status_code = status_code
        super().__init__(f"{service_name}: {message}")


async def ai_service_exception_handler(
    request: Request, 
    exc: AIServiceException
) -> JSONResponse:
    """AI服务异常处理器"""
    logger.error(f"AI Service Error: {exc.message}")
    
    error_response = ErrorResponse(
        message=exc.message,
        error_code=exc.error_code or "AI_SERVICE_ERROR",
        details=exc.details,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.dict()
    )


async def session_not_found_exception_handler(
    request: Request, 
    exc: SessionNotFoundException
) -> JSONResponse:
    """会话未找到异常处理器"""
    logger.warning(f"Session not found: {exc.session_id}")
    
    error_response = ErrorResponse(
        message=exc.message,
        error_code="SESSION_NOT_FOUND",
        details={"session_id": exc.session_id},
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.dict()
    )


async def user_not_found_exception_handler(
    request: Request, 
    exc: UserNotFoundException
) -> JSONResponse:
    """用户未找到异常处理器"""
    logger.warning(f"User not found: {exc.user_id}")
    
    error_response = ErrorResponse(
        message=exc.message,
        error_code="USER_NOT_FOUND",
        details={"user_id": exc.user_id},
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.dict()
    )


async def insufficient_permission_exception_handler(
    request: Request, 
    exc: InsufficientPermissionException
) -> JSONResponse:
    """权限不足异常处理器"""
    logger.warning(f"Insufficient permission: {exc.required_permission}")
    
    error_response = ErrorResponse(
        message=exc.message,
        error_code="INSUFFICIENT_PERMISSION",
        details={"required_permission": exc.required_permission},
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response.dict()
    )


async def rate_limit_exceeded_exception_handler(
    request: Request, 
    exc: RateLimitExceededException
) -> JSONResponse:
    """限流异常处理器"""
    logger.warning(f"Rate limit exceeded: {exc.limit}")
    
    error_response = ErrorResponse(
        message=exc.message,
        error_code="RATE_LIMIT_EXCEEDED",
        details={"limit": exc.limit, "retry_after": exc.retry_after},
        request_id=getattr(request.state, "request_id", None)
    )
    
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.dict()
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    
    return response


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """请求验证异常处理器"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    error_response = ErrorResponse(
        message="请求参数验证失败",
        error_code="VALIDATION_ERROR",
        details={"errors": exc.errors()},
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


async def http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    error_response = ErrorResponse(
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    error_response = ErrorResponse(
        message="服务器内部错误",
        error_code="INTERNAL_SERVER_ERROR",
        details={"exception": str(exc)} if request.app.debug else None,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


def setup_exception_handlers(app):
    """设置异常处理器"""
    
    # 自定义异常处理器
    app.add_exception_handler(AIServiceException, ai_service_exception_handler)
    app.add_exception_handler(SessionNotFoundException, session_not_found_exception_handler)
    app.add_exception_handler(UserNotFoundException, user_not_found_exception_handler)
    app.add_exception_handler(InsufficientPermissionException, insufficient_permission_exception_handler)
    app.add_exception_handler(RateLimitExceededException, rate_limit_exceeded_exception_handler)
    
    # 标准异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
