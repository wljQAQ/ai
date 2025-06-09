"""
聊天服务 - 统一Flask和FastAPI聊天业务逻辑
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional, Dict, Any

from .base_service import BaseService
from models.schemas.chat import (
    ChatResponse,
    StreamChatResponse,
    ProviderInfo,
    ModelInfo,
    ChatStatistics,
    AIProvider,
    MessageRole
)


class ChatService(BaseService):
    """聊天服务 - 统一Flask和FastAPI实现"""
    
    def __init__(self, session_service=None, redis: Optional[Any] = None, db: Optional[Any] = None):
        super().__init__(db, redis)
        self.session_service = session_service
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> ChatResponse:
        """发送聊天消息"""
        try:
            # 验证输入
            self.validate_required_fields(
                {"session_id": session_id, "user_id": user_id, "message": message},
                ["session_id", "user_id", "message"]
            )
            
            # 清理输入
            message = self.sanitize_input(message)
            
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
            
            # 缓存响应
            await self.set_cache(f"chat_response:{response.id}", response.model_dump_json())
            
            return response
            
        except Exception as e:
            self.logger.error(f"Chat service error: {str(e)}")
            raise Exception(f"聊天服务错误: {str(e)}")
    
    async def send_message_stream(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[StreamChatResponse, None]:
        """发送流式聊天消息"""
        try:
            # 验证输入
            self.validate_required_fields(
                {"session_id": session_id, "user_id": user_id, "message": message},
                ["session_id", "user_id", "message"]
            )
            
            # 清理输入
            message = self.sanitize_input(message)
            
            # 模拟流式响应
            response_parts = ["这是", "对消息", f"'{message}'", "的", "AI", "流式", "回复。"]
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
                yield response
                
                # 模拟延迟
                import asyncio
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Stream chat service error: {str(e)}")
            raise Exception(f"流式聊天服务错误: {str(e)}")
    
    async def regenerate_response(self, session_id: str, user_id: str, message_id: Optional[str] = None) -> ChatResponse:
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
            self.logger.error(f"Regenerate response error: {str(e)}")
            raise Exception(f"重新生成回复错误: {str(e)}")
    
    async def get_available_providers(self) -> List[ProviderInfo]:
        """获取可用的AI提供商"""
        return [
            ProviderInfo(
                name=AIProvider.OPENAI,
                display_name="OpenAI",
                description="OpenAI GPT模型",
                models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                is_available=True,
                default_model="gpt-3.5-turbo"
            ),
            ProviderInfo(
                name=AIProvider.QWEN,
                display_name="通义千问",
                description="阿里云通义千问模型",
                models=["qwen-turbo", "qwen-plus", "qwen-max"],
                is_available=True,
                default_model="qwen-turbo"
            ),
            ProviderInfo(
                name=AIProvider.CLAUDE,
                display_name="Claude",
                description="Anthropic Claude模型",
                models=["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
                is_available=True,
                default_model="claude-3-haiku"
            )
        ]
    
    async def get_provider_models(self, provider_name: str) -> List[ModelInfo]:
        """获取指定提供商的模型列表"""
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
                    description="最强大的GPT模型",
                    max_tokens=8192,
                    input_price=0.03,
                    output_price=0.06,
                    is_available=True
                )
            ],
            "qwen": [
                ModelInfo(
                    id="qwen-turbo",
                    name="通义千问-Turbo",
                    provider=AIProvider.QWEN,
                    description="快速响应的千问模型",
                    max_tokens=6000,
                    input_price=0.008,
                    output_price=0.008,
                    is_available=True
                )
            ],
            "claude": [
                ModelInfo(
                    id="claude-3-haiku",
                    name="Claude 3 Haiku",
                    provider=AIProvider.CLAUDE,
                    description="快速的Claude模型",
                    max_tokens=4096,
                    input_price=0.00025,
                    output_price=0.00125,
                    is_available=True
                )
            ]
        }
        
        return models_map.get(provider_name.lower(), [])
    
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
