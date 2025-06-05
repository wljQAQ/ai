"""
中间件模块
"""
import time
import uuid
import logging
from functools import wraps
from flask import Flask, request, g, jsonify
from werkzeug.exceptions import TooManyRequests


def init_middleware(app: Flask) -> None:
    """初始化中间件"""
    init_request_id_middleware(app)
    init_logging_middleware(app)
    init_cors_middleware(app)


def init_request_id_middleware(app: Flask) -> None:
    """初始化请求ID中间件"""
    
    @app.before_request
    def add_request_id():
        """为每个请求添加唯一ID"""
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.start_time = time.time()
    
    @app.after_request
    def add_request_id_header(response):
        """在响应头中添加请求ID"""
        response.headers['X-Request-ID'] = g.request_id
        return response


def init_logging_middleware(app: Flask) -> None:
    """初始化日志中间件"""
    
    @app.before_request
    def log_request():
        """记录请求日志"""
        app.logger.info(
            f"Request started - {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"[{g.request_id}]"
        )
    
    @app.after_request
    def log_response(response):
        """记录响应日志"""
        duration = time.time() - g.start_time
        app.logger.info(
            f"Request completed - {request.method} {request.path} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"[{g.request_id}]"
        )
        return response


def init_cors_middleware(app: Flask) -> None:
    """初始化CORS中间件"""
    
    @app.after_request
    def after_request(response):
        """添加CORS头"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Request-ID')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'message': 'Authorization header is required',
                'error_code': 'MISSING_AUTH_HEADER'
            }), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Invalid authorization header format',
                'error_code': 'INVALID_AUTH_FORMAT'
            }), 401
        
        token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        # 这里应该验证JWT token
        # 简化实现，假设token有效
        if not token or token == 'invalid':
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token',
                'error_code': 'INVALID_TOKEN'
            }), 401
        
        # 将用户信息添加到g对象
        g.user_id = 'user_123'  # 从token中解析用户ID
        g.token = token
        
        return f(*args, **kwargs)
    
    return decorated_function


class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if now - timestamp < window
            ]
        else:
            self.requests[key] = []
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True


# 全局限流器实例
rate_limiter = RateLimiter()


def rate_limit(limit: int = 100, window: int = 3600, per: str = 'ip'):
    """限流装饰器
    
    Args:
        limit: 限制次数
        window: 时间窗口（秒）
        per: 限流维度 ('ip', 'user', 'endpoint')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 确定限流键
            if per == 'ip':
                key = f"rate_limit:ip:{request.remote_addr}"
            elif per == 'user':
                user_id = getattr(g, 'user_id', None)
                if not user_id:
                    key = f"rate_limit:ip:{request.remote_addr}"
                else:
                    key = f"rate_limit:user:{user_id}"
            elif per == 'endpoint':
                key = f"rate_limit:endpoint:{request.endpoint}:{request.remote_addr}"
            else:
                key = f"rate_limit:default:{request.remote_addr}"
            
            # 检查限流
            if not rate_limiter.is_allowed(key, limit, window):
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded',
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json(required_fields: list = None):
    """JSON验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json',
                    'error_code': 'INVALID_CONTENT_TYPE'
                }), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON data',
                    'error_code': 'INVALID_JSON'
                }), 400
            
            # 检查必需字段
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'message': f'Missing required fields: {", ".join(missing_fields)}',
                        'error_code': 'MISSING_FIELDS'
                    }), 400
            
            # 将数据添加到g对象
            g.json_data = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def handle_errors(f):
    """错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Unhandled error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An internal error occurred',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated_function


def create_response(data=None, message=None, success=True, status_code=200):
    """创建标准响应"""
    response_data = {
        'success': success,
        'data': data,
        'message': message,
        'timestamp': time.time(),
        'request_id': getattr(g, 'request_id', None)
    }
    
    return jsonify(response_data), status_code
