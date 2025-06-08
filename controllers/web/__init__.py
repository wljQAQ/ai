"""
Web API模块 - 前端应用接口
"""

from flask import Flask, Blueprint
from controllers.web.chat import chat_bp
from controllers.web.session import session_bp


def init_web_routes(app: Flask) -> None:
    """初始化Web路由"""
    
    # 创建Web主蓝图
    web_bp = Blueprint("web", __name__, url_prefix="/api/web")
    
    # 注册子模块蓝图
    web_bp.register_blueprint(chat_bp)
    web_bp.register_blueprint(session_bp)
    
    # 添加健康检查
    @web_bp.route("/health", methods=["GET"])
    def health_check():
        return {
            "status": "healthy", 
            "message": "Web API is running", 
            "success": True
        }, 200
    
    # 注册到应用
    app.register_blueprint(web_bp)
    
    app.logger.info("Web routes initialized")
