"""
控制台API模块 - 管理后台接口
"""

from flask import Flask, Blueprint
from controllers.console.chat import chat_bp
from controllers.console.session import session_bp
from controllers.console.workspace import workspace_bp


def init_console_routes(app: Flask) -> None:
    """初始化控制台路由"""
    
    # 创建控制台主蓝图
    console_bp = Blueprint("console", __name__, url_prefix="/api/console")
    
    # 注册子模块蓝图
    console_bp.register_blueprint(chat_bp)
    console_bp.register_blueprint(session_bp)
    console_bp.register_blueprint(workspace_bp)
    
    # 添加健康检查
    @console_bp.route("/health", methods=["GET"])
    def health_check():
        return {
            "status": "healthy", 
            "message": "Console API is running", 
            "success": True
        }, 200
    
    # 注册到应用
    app.register_blueprint(console_bp)
    
    app.logger.info("Console routes initialized")
