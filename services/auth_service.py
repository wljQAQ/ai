"""
认证服务 - 统一Flask和FastAPI认证业务逻辑
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

from .base_service import BaseService
from models.schemas.user import UserLoginResponse, UserResponse, UserRole, UserStatus


class AuthService(BaseService):
    """认证服务 - 统一Flask和FastAPI实现"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # 配置参数
        self.secret_key = "your-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
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
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.JWTError:
            return None
    
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
        
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
        refresh_token = self.create_access_token(
            data={"sub": user.id, "type": "refresh"}, expires_delta=refresh_token_expires
        )
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=user
        )
    
    async def refresh_token(self, refresh_token: str) -> UserLoginResponse:
        """刷新令牌"""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("令牌中缺少用户信息")
        
        # 这里应该从数据库获取用户信息，现在模拟
        user = UserResponse(
            id=user_id,
            username="user",
            email="user@example.com",
            full_name="用户",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # 保持原刷新令牌
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=user
        )
    
    async def logout(self, token: str) -> bool:
        """用户登出"""
        try:
            # 将令牌加入黑名单（使用Redis）
            if self.redis:
                await self.set_cache(f"blacklist:{token}", "1", ttl=self.access_token_expire_minutes * 60)
            return True
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return False
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        if not self.redis:
            return False
        
        result = await self.get_cache(f"blacklist:{token}")
        return result is not None
    
    async def get_current_user(self, token: str) -> Optional[UserResponse]:
        """根据令牌获取当前用户"""
        # 检查黑名单
        if await self.is_token_blacklisted(token):
            return None
        
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 这里应该从数据库获取用户信息，现在模拟
        return UserResponse(
            id=user_id,
            username="user",
            email="user@example.com",
            full_name="用户",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
