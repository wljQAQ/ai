"""
API v1模块初始化
"""
from flask import Flask, Blueprint
from .chat import chat_bp
from .session import session_bp
from .health import health_bp


def init_api_v1(app: Flask) -> None:
    """初始化API v1路由"""
    
    # 创建v1蓝图
    api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    
    # 注册子蓝图
    api_v1.register_blueprint(chat_bp)
    api_v1.register_blueprint(session_bp)
    api_v1.register_blueprint(health_bp)
    
    # 注册到应用
    app.register_blueprint(api_v1)
    
    app.logger.info("API v1 routes initialized")
