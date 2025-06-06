"""
聊天服务实现 - 业务逻辑层
"""
import logging
from typing import List, AsyncGenerator, Optional, Dict, Any
from core.model_providers import provider_registry, BaseModelProvider
from models.chat_model import (
    ChatRequest, ChatResponse, ChatMessage, MessageRole,
    ChatProvider, UsageInfo
)
from models.session_model import Session
from services.session_service import SessionService


class ChatService:
    """聊天服务 - 处理聊天相关的业务逻辑"""
    
    def __init__(self, session_service: SessionService, provider_registry):
        self.session_service = session_service
        self.provider_registry = provider_registry
        self.logger = logging.getLogger(__name__)
    
    async def send_message(
        self, 
        session_id: str, 
        user_id: str, 
        message: str,
        stream: bool = False
    ) -> ChatResponse:
        """发送聊天消息"""
        try:
            # 获取会话
            session = await self.session_service.get_session(session_id, user_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # 创建用户消息
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=message
            )
            
            # 添加用户消息到会话
            await self.session_service.add_message(session_id, user_message)
            
            # 获取会话历史消息
            messages = await self.session_service.get_messages(session_id)
            
            # 创建聊天请求
            chat_request = ChatRequest(
                messages=messages,
                model=session.model,
                stream=stream,
                session_id=session_id,
                user_id=user_id
            )
            
            # 获取AI提供商
            provider = self._get_provider(session.ai_provider)
            
            # 发送请求
            if stream:
                return await self._handle_stream_response(provider, chat_request, session_id)
            else:
                response = await provider.chat(chat_request)
                
                # 添加AI响应到会话
                await self.session_service.add_message(session_id, response.message)
                
                return response
        
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise
    
    async def send_message_stream(
        self, 
        session_id: str, 
        user_id: str, 
        message: str
    ) -> AsyncGenerator[ChatResponse, None]:
        """流式发送聊天消息"""
        try:
            # 获取会话
            session = await self.session_service.get_session(session_id, user_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # 创建用户消息
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=message
            )
            
            # 添加用户消息到会话
            await self.session_service.add_message(session_id, user_message)
            
            # 获取会话历史消息
            messages = await self.session_service.get_messages(session_id)
            
            # 创建聊天请求
            chat_request = ChatRequest(
                messages=messages,
                model=session.model,
                stream=True,
                session_id=session_id,
                user_id=user_id
            )
            
            # 获取AI提供商
            provider = self._get_provider(session.ai_provider)
            
            # 流式响应
            full_content = ""
            async for chunk in provider.chat_stream(chat_request):
                full_content += chunk.message.content
                yield chunk
            
            # 添加完整的AI响应到会话
            final_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_content
            )
            await self.session_service.add_message(session_id, final_message)
        
        except Exception as e:
            self.logger.error(f"Failed to send stream message: {str(e)}")
            raise
    
    async def regenerate_response(
        self, 
        session_id: str, 
        user_id: str
    ) -> ChatResponse:
        """重新生成回复"""
        try:
            # 获取会话
            session = await self.session_service.get_session(session_id, user_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # 获取会话历史消息（排除最后一条AI消息）
            messages = await self.session_service.get_messages(session_id)
            
            # 移除最后一条AI消息
            if messages and messages[-1].role == MessageRole.ASSISTANT:
                messages = messages[:-1]
            
            if not messages:
                raise ValueError("No messages to regenerate from")
            
            # 创建聊天请求
            chat_request = ChatRequest(
                messages=messages,
                model=session.model,
                stream=False,
                session_id=session_id,
                user_id=user_id
            )
            
            # 获取AI提供商
            provider = self._get_provider(session.ai_provider)
            
            # 发送请求
            response = await provider.chat(chat_request)
            
            # 添加新的AI响应到会话
            await self.session_service.add_message(session_id, response.message)
            
            return response
        
        except Exception as e:
            self.logger.error(f"Failed to regenerate response: {str(e)}")
            raise
    
    async def get_available_providers(self) -> List[ChatProvider]:
        """获取可用的AI提供商"""
        try:
            provider_names = self.provider_registry.list_providers()
            providers = []
            
            for name in provider_names:
                try:
                    provider_instance = self._get_provider(name)
                    models = provider_instance.get_supported_models()
                    
                    chat_provider = ChatProvider(
                        name=name,
                        display_name=name.title(),
                        models=models,
                        is_available=True
                    )
                    providers.append(chat_provider)
                    
                except Exception as e:
                    self.logger.warning(f"Provider {name} is not available: {str(e)}")
                    chat_provider = ChatProvider(
                        name=name,
                        display_name=name.title(),
                        models=[],
                        is_available=False
                    )
                    providers.append(chat_provider)
            
            return providers
        
        except Exception as e:
            self.logger.error(f"Failed to get available providers: {str(e)}")
            raise
    
    async def get_provider_models(self, provider_name: str) -> List[str]:
        """获取提供商支持的模型"""
        try:
            provider = self._get_provider(provider_name)
            return provider.get_supported_models()
        except Exception as e:
            self.logger.error(f"Failed to get models for provider {provider_name}: {str(e)}")
            raise ValueError(f"Unknown provider: {provider_name}")
    
    def _get_provider(self, provider_name: str) -> BaseModelProvider:
        """获取AI提供商实例"""
        try:
            # 获取提供商配置
            config = self._get_provider_config(provider_name)
            
            # 创建提供商实例
            return self.provider_registry.create_provider(provider_name, config)
        
        except Exception as e:
            self.logger.error(f"Failed to get provider {provider_name}: {str(e)}")
            raise ValueError(f"Provider {provider_name} is not available")
    
    def _get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """获取提供商配置"""
        from config.base import BaseConfig
        
        providers = BaseConfig.AI_PROVIDERS
        if provider_name in providers:
            return providers[provider_name]['config']
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    async def _handle_stream_response(
        self, 
        provider: BaseModelProvider, 
        request: ChatRequest, 
        session_id: str
    ) -> ChatResponse:
        """处理流式响应（非流式接口的内部处理）"""
        full_content = ""
        final_response = None
        
        async for chunk in provider.chat_stream(request):
            full_content += chunk.message.content
            final_response = chunk
        
        # 添加完整的AI响应到会话
        if final_response:
            final_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_content
            )
            await self.session_service.add_message(session_id, final_message)
            
            # 返回最终响应
            final_response.message.content = full_content
            return final_response
        
        raise RuntimeError("No response received from provider")
