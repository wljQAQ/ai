"""
会话服务
"""

from app.services.base import BaseService


class SessionService(BaseService):
    """会话服务"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
    
    async def get_session(self, session_id: str, user_id: str):
        """获取会话"""
        # 模拟会话验证
        return {"id": session_id, "user_id": user_id, "valid": True}
