"""
会话管理API
"""
from flask import Blueprint, jsonify, request
import time
import uuid

session_bp = Blueprint('session', __name__, url_prefix='/sessions')


@session_bp.route('', methods=['GET'])
def list_sessions():
    """获取会话列表"""
    # 模拟数据
    sessions = [
        {
            'id': 'sess_123',
            'title': '示例会话',
            'ai_provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'created_at': time.time(),
            'updated_at': time.time()
        }
    ]
    
    return jsonify({
        'success': True,
        'data': {
            'sessions': sessions,
            'total': len(sessions)
        },
        'message': 'Sessions retrieved successfully'
    })


@session_bp.route('', methods=['POST'])
def create_session():
    """创建新会话"""
    data = request.get_json() or {}
    
    # 模拟创建会话
    session = {
        'id': f'sess_{uuid.uuid4().hex[:12]}',
        'title': data.get('title', '新的聊天会话'),
        'ai_provider': data.get('ai_provider', 'openai'),
        'model': data.get('model', 'gpt-3.5-turbo'),
        'created_at': time.time(),
        'updated_at': time.time()
    }
    
    return jsonify({
        'success': True,
        'data': session,
        'message': 'Session created successfully'
    }), 201


@session_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话详情"""
    # 模拟数据
    session = {
        'id': session_id,
        'title': '示例会话',
        'ai_provider': 'openai',
        'model': 'gpt-3.5-turbo',
        'created_at': time.time(),
        'updated_at': time.time()
    }
    
    return jsonify({
        'success': True,
        'data': session,
        'message': 'Session retrieved successfully'
    })
