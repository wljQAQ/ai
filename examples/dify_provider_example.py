"""
Dify 提供商使用示例
演示如何使用 Dify 提供商进行 AI 对话
"""

import asyncio
import uuid
from typing import Optional

from core.model_providers import provider_registry
from models.schemas.ai_provider import (
    DifyConfig,
    UnifiedChatRequest,
    UnifiedMessage,
    MessageRole,
    ProviderType,
)


class DifyChatBot:
    """基于 Dify 提供商的聊天机器人示例"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai"):
        """初始化聊天机器人
        
        Args:
            api_key: Dify API 密钥
            base_url: Dify API 基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.conversation_id: Optional[str] = None
        self.provider = None
        
    async def start_conversation(self, system_prompt: str = "你是一个有用的AI助手。"):
        """开始新的对话
        
        Args:
            system_prompt: 系统提示词
        """
        # 生成新的对话ID
        self.conversation_id = str(uuid.uuid4())
        
        # 创建配置
        config = DifyConfig(
            api_key=self.api_key,
            base_url=self.base_url,
            conversation_id=self.conversation_id,
            default_model="gpt-3.5-turbo",
            timeout=30.0,
            max_retries=3,
        )
        
        # 创建提供商实例
        self.provider = provider_registry.create_provider(
            ProviderType.DIFY,
            config.model_dump()
        )
        
        print(f"🚀 开始新对话，对话ID: {self.conversation_id}")
        print(f"💡 系统提示: {system_prompt}")
        print("-" * 50)
        
    async def chat(self, user_input: str, stream: bool = False) -> str:
        """发送聊天消息
        
        Args:
            user_input: 用户输入
            stream: 是否使用流式响应
            
        Returns:
            AI 回复内容
        """
        if not self.provider:
            raise ValueError("请先调用 start_conversation() 开始对话")
        
        # 创建请求
        request = UnifiedChatRequest(
            messages=[
                UnifiedMessage(
                    role=MessageRole.USER,
                    content=user_input
                )
            ],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
            stream=stream,
        )
        
        print(f"👤 用户: {user_input}")
        print("🤖 AI: ", end="", flush=True)
        
        if stream:
            # 流式响应
            full_content = ""
            async for chunk in self.provider.chat_stream(request):
                if chunk.delta:
                    print(chunk.delta, end="", flush=True)
                    full_content += chunk.delta
                
                if chunk.finish_reason:
                    print()  # 换行
                    break
            
            return full_content
        else:
            # 非流式响应
            response = await self.provider.chat(request)
            print(response.content)
            return response.content
    
    async def get_conversation_stats(self):
        """获取对话统计信息"""
        if not self.provider:
            return None
        
        metrics = self.provider.get_metrics()
        return {
            "conversation_id": self.conversation_id,
            "request_count": metrics.request_count,
            "success_count": metrics.success_count,
            "error_count": metrics.error_count,
            "avg_latency_ms": metrics.avg_latency_ms,
            "total_tokens": metrics.total_tokens,
        }
    
    async def close(self):
        """关闭连接"""
        if self.provider and hasattr(self.provider, 'client'):
            await self.provider.client.aclose()


async def interactive_chat_demo():
    """交互式聊天演示"""
    print("🎯 Dify 提供商交互式聊天演示")
    print("=" * 50)
    
    # 配置 API key（请替换为实际的 API key）
    api_key = input("请输入您的 Dify API key: ").strip()
    if not api_key:
        print("❌ API key 不能为空")
        return
    
    # 创建聊天机器人
    bot = DifyChatBot(api_key)
    
    try:
        # 开始对话
        system_prompt = input("请输入系统提示词（回车使用默认）: ").strip()
        if not system_prompt:
            system_prompt = "你是一个有用的AI助手，请用中文回答问题。"
        
        await bot.start_conversation(system_prompt)
        
        # 选择响应模式
        stream_mode = input("是否使用流式响应？(y/n): ").strip().lower() == 'y'
        print(f"📡 响应模式: {'流式' if stream_mode else '非流式'}")
        print("-" * 50)
        
        # 开始聊天循环
        while True:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                break
            
            if user_input.lower() in ['stats', '统计']:
                stats = await bot.get_conversation_stats()
                if stats:
                    print("📊 对话统计:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                continue
            
            if not user_input:
                continue
            
            try:
                await bot.chat(user_input, stream=stream_mode)
            except Exception as e:
                print(f"❌ 错误: {e}")
        
        # 显示最终统计
        print("\n📊 最终统计:")
        stats = await bot.get_conversation_stats()
        if stats:
            for key, value in stats.items():
                print(f"   {key}: {value}")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出聊天")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        await bot.close()
        print("✅ 聊天结束")


async def batch_test_demo():
    """批量测试演示"""
    print("🧪 Dify 提供商批量测试演示")
    print("=" * 50)
    
    # 测试问题列表
    test_questions = [
        "你好，请介绍一下你自己。",
        "什么是人工智能？",
        "请用一句话总结机器学习的概念。",
        "Python 和 JavaScript 有什么区别？",
        "谢谢你的回答！"
    ]
    
    api_key = input("请输入您的 Dify API key: ").strip()
    if not api_key:
        print("❌ API key 不能为空")
        return
    
    bot = DifyChatBot(api_key)
    
    try:
        await bot.start_conversation("你是一个专业的技术助手，请简洁明了地回答问题。")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 测试 {i}/{len(test_questions)}")
            try:
                await bot.chat(question, stream=False)
            except Exception as e:
                print(f"❌ 测试 {i} 失败: {e}")
        
        # 显示统计
        stats = await bot.get_conversation_stats()
        print(f"\n📊 批量测试完成:")
        if stats:
            print(f"   成功率: {stats['success_count']}/{stats['request_count']}")
            print(f"   平均延迟: {stats['avg_latency_ms']:.2f}ms")
            print(f"   总Token数: {stats['total_tokens']}")
    
    except Exception as e:
        print(f"❌ 批量测试失败: {e}")
    finally:
        await bot.close()


async def main():
    """主函数"""
    print("🎉 欢迎使用 Dify 提供商示例程序")
    print("=" * 50)
    
    while True:
        print("\n请选择演示模式:")
        print("1. 交互式聊天演示")
        print("2. 批量测试演示")
        print("3. 退出")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == '1':
            await interactive_chat_demo()
        elif choice == '2':
            await batch_test_demo()
        elif choice == '3':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    asyncio.run(main())
