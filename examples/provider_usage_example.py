"""
AI 提供商架构使用示例
演示如何使用重构后的 AI 提供商架构
"""

import asyncio
from typing import Dict, Any

# 导入重构后的模块
from core.model_providers.base_provider import provider_registry
from models.schemas.ai_provider import (
    OpenAIConfig,
    ClaudeConfig,
    UnifiedChatRequest,
    UnifiedMessage,
    MessageRole,
    ProviderType
)


async def demo_openai_provider():
    """演示 OpenAI 提供商的使用"""
    print("=== OpenAI 提供商演示 ===")
    
    # 1. 创建配置
    config_data = {
        "api_key": "sk-test123456789",  # 测试用的假密钥
        "base_url": None,
        "timeout": 30.0,
        "max_retries": 3,
        "default_model": "gpt-3.5-turbo"
    }
    
    try:
        # 2. 通过注册表创建提供商实例
        provider = provider_registry.create_provider(
            ProviderType.OPENAI,
            config_data
        )
        
        print(f"✅ 创建提供商成功: {provider.provider_type}")
        print(f"   支持的模型: {provider.get_supported_models()}")
        print(f"   默认模型: {provider.get_default_model()}")
        
        # 3. 创建聊天请求
        request = UnifiedChatRequest(
            messages=[
                UnifiedMessage(
                    role=MessageRole.USER,
                    content="你好，请介绍一下你自己"
                )
            ],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"📝 请求内容: {request.messages[0].content}")
        
        # 4. 发送聊天请求（这里会失败，因为是假密钥）
        try:
            response = await provider.chat(request)
            print(f"✅ 聊天响应: {response.content}")
            print(f"   Token使用: {response.usage}")
            print(f"   延迟: {response.latency_ms}ms")
        except Exception as e:
            print(f"❌ 聊天请求失败（预期的，因为使用了假密钥）: {str(e)}")
        
        # 5. 获取性能指标
        metrics = provider.get_metrics()
        print(f"📊 性能指标:")
        print(f"   请求次数: {metrics.request_count}")
        print(f"   成功次数: {metrics.success_count}")
        print(f"   错误次数: {metrics.error_count}")
        
    except Exception as e:
        print(f"❌ 创建提供商失败: {str(e)}")


async def demo_provider_switching():
    """演示提供商切换的便利性"""
    print("\n=== 提供商切换演示 ===")
    
    # 统一的聊天请求
    request = UnifiedChatRequest(
        messages=[
            UnifiedMessage(
                role=MessageRole.USER,
                content="解释一下什么是人工智能"
            )
        ],
        model="default",  # 使用默认模型
        temperature=0.7
    )
    
    # 不同提供商的配置
    providers_config = {
        ProviderType.OPENAI: {
            "api_key": "sk-test123456789",
            "default_model": "gpt-3.5-turbo"
        },
        # 注意：Claude 配置需要不同的 API key 格式
        # ProviderType.CLAUDE: {
        #     "api_key": "sk-ant-test123456789",
        #     "default_model": "claude-3-haiku-20240307"
        # }
    }
    
    # 遍历所有已注册的提供商
    for provider_type in provider_registry.list_providers():
        if provider_type in providers_config:
            try:
                print(f"\n🔄 切换到 {provider_type.value} 提供商")
                
                # 创建提供商实例
                provider = provider_registry.create_provider(
                    provider_type,
                    providers_config[provider_type]
                )
                
                # 使用相同的请求格式
                request.model = provider.get_default_model()
                
                print(f"   使用模型: {request.model}")
                print(f"   请求内容: {request.messages[0].content}")
                
                # 发送请求（会失败，但展示了统一接口）
                try:
                    response = await provider.chat(request)
                    print(f"   ✅ 响应: {response.content[:50]}...")
                except Exception as e:
                    print(f"   ❌ 请求失败（预期的）: {type(e).__name__}")
                
            except Exception as e:
                print(f"   ❌ 创建提供商失败: {str(e)}")


async def demo_stream_chat():
    """演示流式聊天"""
    print("\n=== 流式聊天演示 ===")
    
    config_data = {
        "api_key": "sk-test123456789",
        "default_model": "gpt-3.5-turbo"
    }
    
    try:
        provider = provider_registry.create_provider(
            ProviderType.OPENAI,
            config_data
        )
        
        request = UnifiedChatRequest(
            messages=[
                UnifiedMessage(
                    role=MessageRole.USER,
                    content="请写一首关于春天的短诗"
                )
            ],
            model="gpt-3.5-turbo",
            stream=True
        )
        
        print("🌊 开始流式聊天...")
        print("📝 响应内容: ", end="")
        
        try:
            async for chunk in provider.chat_stream(request):
                print(chunk.delta, end="", flush=True)
            print()  # 换行
        except Exception as e:
            print(f"\n❌ 流式聊天失败（预期的）: {type(e).__name__}")
            
    except Exception as e:
        print(f"❌ 创建提供商失败: {str(e)}")


async def demo_error_handling():
    """演示错误处理和重试机制"""
    print("\n=== 错误处理演示 ===")
    
    # 使用无效的配置来触发错误
    invalid_configs = [
        {
            "name": "无效的 API Key",
            "config": {
                "api_key": "invalid-key",  # 不符合 OpenAI 格式
                "default_model": "gpt-3.5-turbo"
            }
        },
        {
            "name": "空的 API Key",
            "config": {
                "api_key": "",
                "default_model": "gpt-3.5-turbo"
            }
        }
    ]
    
    for test_case in invalid_configs:
        print(f"\n🧪 测试: {test_case['name']}")
        try:
            provider = provider_registry.create_provider(
                ProviderType.OPENAI,
                test_case['config']
            )
            print("   ❌ 应该失败但没有失败")
        except Exception as e:
            print(f"   ✅ 正确捕获错误: {type(e).__name__}: {str(e)}")


async def main():
    """主函数"""
    print("🚀 AI 提供商架构演示")
    print("=" * 50)
    
    # 检查已注册的提供商
    registered_providers = provider_registry.list_providers()
    print(f"📋 已注册的提供商: {[p.value for p in registered_providers]}")
    
    # 运行各种演示
    await demo_openai_provider()
    await demo_provider_switching()
    await demo_stream_chat()
    await demo_error_handling()
    
    print("\n✨ 演示完成！")
    print("\n💡 重构后的架构优势:")
    print("   ✅ 统一的接口设计")
    print("   ✅ 类型安全的配置管理")
    print("   ✅ 完善的错误处理和重试机制")
    print("   ✅ 性能监控和指标收集")
    print("   ✅ 易于扩展新的 AI 提供商")


if __name__ == "__main__":
    asyncio.run(main())
