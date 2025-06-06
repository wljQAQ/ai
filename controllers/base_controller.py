"""
基础控制器 - 提供通用的控制器功能
"""
from typing import Dict, Any, Optional
from flask import jsonify, request, g


class BaseController:
    """基础控制器类"""
    
    @staticmethod
    def create_response(
        data: Any = None,
        message: str = "Success",
        success: bool = True,
        status_code: int = 200,
        **kwargs
    ) -> tuple:
        """创建标准化的API响应"""
        response_data = {
            "success": success,
            "message": message,
            **kwargs
        }
        
        if data is not None:
            response_data["data"] = data
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def create_error_response(
        message: str,
        error_code: str = None,
        status_code: int = 400,
        **kwargs
    ) -> tuple:
        """创建错误响应"""
        response_data = {
            "success": False,
            "message": message,
            **kwargs
        }
        
        if error_code:
            response_data["error_code"] = error_code
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def get_json_data(required_fields: list = None) -> Dict[str, Any]:
        """获取并验证JSON数据"""
        if not request.is_json:
            raise ValueError("Request must be JSON")
        
        data = request.get_json()
        if not data:
            raise ValueError("Request body is empty")
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return data
    
    @staticmethod
    def get_user_id() -> str:
        """获取当前用户ID"""
        # 这里应该从认证中间件获取用户ID
        # 简化实现，返回固定值
        return getattr(g, 'user_id', 'test_user_123')
    
    @staticmethod
    def get_query_params() -> Dict[str, Any]:
        """获取查询参数"""
        return request.args.to_dict()
    
    @staticmethod
    def validate_pagination(limit: int = 20, offset: int = 0) -> tuple:
        """验证分页参数"""
        try:
            limit = int(request.args.get('limit', limit))
            offset = int(request.args.get('offset', offset))
            
            # 限制最大值
            limit = min(limit, 100)
            offset = max(offset, 0)
            
            return limit, offset
        except ValueError:
            raise ValueError("Invalid pagination parameters")
