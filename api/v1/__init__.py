"""
API v1模块初始化 - MVC架构
"""

from flask import Flask, Blueprint
from controllers.chat_controller import chat_bp
from controllers.session_controller import session_bp


def init_api_v1(app: Flask) -> None:
    """初始化API v1路由"""

    # 创建v1蓝图
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    # 注册控制器蓝图
    api_v1.register_blueprint(chat_bp)
    api_v1.register_blueprint(session_bp)

    # 添加健康检查路由
    @api_v1.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "message": "API v1 is running", "success": True}, 200

    # 注册到应用
    app.register_blueprint(api_v1)

    app.logger.info("API v1 routes initialized with MVC architecture")
