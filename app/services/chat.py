"""
聊天服务
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis

from app.services.base import BaseService
from app.schemas.chat import (
    ChatResponse,
    StreamChatResponse,
    ProviderInfo,
    ModelInfo,
    ChatStatistics,
    AIProvider,
    MessageRole
)
from app.core.exceptions import SessionNotFoundException, AIServiceException


class ChatService(BaseService):
    """聊天服务"""
    
    def __init__(self, session_service=None, redis: Optional[aioredis.Redis] = None):
        # 简化构造函数，避免循环依赖
        self.redis = redis
        self.session_service = session_service
        self.logger = __import__('loguru').logger
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """发送聊天消息"""
        try:
            # 模拟AI响应
            response_content = f"这是对消息 '{message}' 的AI回复。"
            
            # 创建响应对象
            response = ChatResponse(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_content,
                model="gpt-3.5-turbo",
                provider=AIProvider.OPENAI,
                created_at=datetime.now(),
                prompt_tokens=len(message.split()),
                completion_tokens=len(response_content.split()),
                total_tokens=len(message.split()) + len(response_content.split()),
                finish_reason="stop"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Chat service error: {str(e)}")
            raise AIServiceException(f"聊天服务错误: {str(e)}")
    
    async def send_message_stream(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """发送流式聊天消息"""
        try:
            # 模拟流式响应
            response_parts = [
                "这是", "一个", "流式", "AI", "回复", "的", "示例", "。"
            ]
            
            message_id = str(uuid.uuid4())
            
            for i, part in enumerate(response_parts):
                response = StreamChatResponse(
                    id=message_id,
                    session_id=session_id,
                    delta=part + " ",
                    model="gpt-3.5-turbo",
                    provider=AIProvider.OPENAI,
                    created_at=datetime.now(),
                    finish_reason="stop" if i == len(response_parts) - 1 else None
                )
                
                yield f"data: {response.json()}\n\n"
                
                # 模拟延迟
                await __import__('asyncio').sleep(0.1)
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            self.logger.error(f"Stream chat service error: {str(e)}")
            error_data = {
                "error": {
                    "message": str(e),
                    "type": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    async def regenerate_response(
        self,
        session_id: str,
        user_id: str,
        message_id: Optional[str] = None
    ) -> ChatResponse:
        """重新生成回复"""
        try:
            # 模拟重新生成
            response_content = "这是重新生成的AI回复。"
            
            response = ChatResponse(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_content,
                model="gpt-3.5-turbo",
                provider=AIProvider.OPENAI,
                created_at=datetime.now(),
                prompt_tokens=10,
                completion_tokens=len(response_content.split()),
                total_tokens=10 + len(response_content.split()),
                finish_reason="stop"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Regenerate service error: {str(e)}")
            raise AIServiceException(f"重新生成服务错误: {str(e)}")
    
    async def get_available_providers(self) -> List[ProviderInfo]:
        """获取可用的AI提供商"""
        providers = [
            ProviderInfo(
                name=AIProvider.OPENAI,
                display_name="OpenAI",
                description="OpenAI GPT模型",
                models=["gpt-3.5-turbo", "gpt-4"],
                is_available=True,
                default_model="gpt-3.5-turbo"
            ),
            ProviderInfo(
                name=AIProvider.QWEN,
                display_name="通义千问",
                description="阿里云通义千问模型",
                models=["qwen-turbo", "qwen-plus"],
                is_available=True,
                default_model="qwen-turbo"
            ),
            ProviderInfo(
                name=AIProvider.CLAUDE,
                display_name="Claude",
                description="Anthropic Claude模型",
                models=["claude-3-sonnet", "claude-3-opus"],
                is_available=False,
                default_model="claude-3-sonnet"
            )
        ]
        
        return providers
    
    async def get_provider_models(self, provider_name: str) -> List[ModelInfo]:
        """获取提供商的模型列表"""
        models_map = {
            "openai": [
                ModelInfo(
                    id="gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    provider=AIProvider.OPENAI,
                    description="快速、经济的GPT模型",
                    max_tokens=4096,
                    input_price=0.0015,
                    output_price=0.002,
                    is_available=True
                ),
                ModelInfo(
                    id="gpt-4",
                    name="GPT-4",
                    provider=AIProvider.OPENAI,
                    description="更强大的GPT模型",
                    max_tokens=8192,
                    input_price=0.03,
                    output_price=0.06,
                    is_available=True
                )
            ],
            "qwen": [
                ModelInfo(
                    id="qwen-turbo",
                    name="通义千问 Turbo",
                    provider=AIProvider.QWEN,
                    description="快速的中文优化模型",
                    max_tokens=2048,
                    input_price=0.001,
                    output_price=0.002,
                    is_available=True
                )
            ]
        }
        
        return models_map.get(provider_name, [])
    
    async def get_chat_statistics(self) -> ChatStatistics:
        """获取聊天统计信息"""
        return ChatStatistics(
            total_messages=1000,
            total_tokens=50000,
            total_cost=25.50,
            provider_stats={
                "openai": {
                    "requests": 800,
                    "tokens": 40000,
                    "cost": 20.00
                },
                "qwen": {
                    "requests": 200,
                    "tokens": 10000,
                    "cost": 5.50
                }
            },
            model_stats={
                "gpt-3.5-turbo": {
                    "requests": 600,
                    "tokens": 30000,
                    "cost": 15.00
                },
                "gpt-4": {
                    "requests": 200,
                    "tokens": 10000,
                    "cost": 5.00
                }
            },
            daily_stats=[
                {"date": "2024-01-01", "messages": 100, "tokens": 5000, "cost": 2.50},
                {"date": "2024-01-02", "messages": 120, "tokens": 6000, "cost": 3.00}
            ]
        )
