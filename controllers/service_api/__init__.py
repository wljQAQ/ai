"""
服务API模块 - 第三方集成接口
"""

from flask import Flask, Blueprint
from controllers.service_api.chat import chat_bp


def init_service_api_routes(app: Flask) -> None:
    """初始化服务API路由"""
    
    # 创建服务API主蓝图
    service_api_bp = Blueprint("service_api", __name__, url_prefix="/api/service")
    
    # 注册子模块蓝图
    service_api_bp.register_blueprint(chat_bp)
    
    # 添加健康检查
    @service_api_bp.route("/health", methods=["GET"])
    def health_check():
        return {
            "status": "healthy", 
            "message": "Service API is running", 
            "success": True
        }, 200
    
    # 注册到应用
    app.register_blueprint(service_api_bp)
    
    app.logger.info("Service API routes initialized")
