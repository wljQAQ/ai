"""
认证服务
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

from app.services.base import BaseService
from app.core.config import settings
from app.schemas.user import UserLoginResponse, UserResponse, UserRole, UserStatus


class AuthService(BaseService):
    """认证服务"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """用户认证"""
        # 模拟用户认证
        if username == "admin" and password == "admin123":
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
        elif username == "user" and password == "user123":
            return UserResponse(
                id="user_123",
                username="user",
                email="user@example.com",
                full_name="普通用户",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        return None
    
    async def login(self, username: str, password: str) -> UserLoginResponse:
        """用户登录"""
        user = await self.authenticate_user(username, password)
        if not user:
            raise ValueError("用户名或密码错误")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = self.create_access_token(
            data={"sub": user.id, "type": "refresh"}, expires_delta=refresh_token_expires
        )
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
