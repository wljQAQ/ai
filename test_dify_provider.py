"""
测试 Dify 提供商实现
"""

import asyncio
import os
from core.model_providers import provider_registry
from models.schemas.ai_provider import (
    DifyConfig,
    UnifiedChatRequest,
    UnifiedMessage,
    MessageRole,
    ProviderType,
)


async def test_dify_provider():
    """测试 Dify 提供商基本功能"""
    
    # 配置 Dify 提供商
    config = DifyConfig(
        api_key="your-dify-api-key-here",  # 替换为实际的 API key
        base_url="https://api.dify.ai",
        default_model="gpt-3.5-turbo",
        timeout=30.0,
        max_retries=3,
    )
    
    # 创建提供商实例
    try:
        provider = provider_registry.create_provider(
            ProviderType.DIFY,
            config.model_dump()
        )
        print("✅ Dify 提供商创建成功")
    except Exception as e:
        print(f"❌ 创建 Dify 提供商失败: {e}")
        return
    
    # 创建测试请求
    request = UnifiedChatRequest(
        messages=[
            UnifiedMessage(
                role=MessageRole.SYSTEM,
                content="你是一个有用的AI助手。"
            ),
            UnifiedMessage(
                role=MessageRole.USER,
                content="你好，请介绍一下你自己。"
            )
        ],
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,
    )
    
    print("\n🧪 测试非流式响应...")
    try:
        # 测试非流式响应
        response = await provider.chat(request)
        print(f"✅ 非流式响应成功:")
        print(f"   ID: {response.id}")
        print(f"   内容: {response.content[:100]}...")
        print(f"   模型: {response.model}")
        print(f"   提供商: {response.provider}")
        print(f"   Token 使用: {response.usage}")
        print(f"   延迟: {response.latency_ms}ms")
        
        if response.extra_data:
            print(f"   扩展数据: {response.extra_data}")
            
    except Exception as e:
        print(f"❌ 非流式响应测试失败: {e}")
    
    print("\n🌊 测试流式响应...")
    try:
        # 测试流式响应
        stream_request = request.model_copy()
        stream_request.stream = True
        
        full_content = ""
        chunk_count = 0
        
        async for chunk in provider.chat_stream(stream_request):
            chunk_count += 1
            full_content += chunk.delta
            print(f"   Chunk {chunk_count}: {chunk.delta}", end="", flush=True)
            
            if chunk.finish_reason:
                print(f"\n✅ 流式响应完成，结束原因: {chunk.finish_reason}")
                break
        
        print(f"\n   总共接收到 {chunk_count} 个数据块")
        print(f"   完整内容长度: {len(full_content)} 字符")
        
    except Exception as e:
        print(f"❌ 流式响应测试失败: {e}")
    
    # 测试性能指标
    print("\n📊 性能指标:")
    metrics = provider.get_metrics()
    print(f"   请求次数: {metrics.request_count}")
    print(f"   成功次数: {metrics.success_count}")
    print(f"   错误次数: {metrics.error_count}")
    print(f"   平均延迟: {metrics.avg_latency_ms:.2f}ms")
    print(f"   总 Token 数: {metrics.total_tokens}")
    
    # 清理资源
    if hasattr(provider, 'client'):
        await provider.client.aclose()
    
    print("\n✅ 测试完成")


async def test_provider_registry():
    """测试提供商注册表功能"""
    print("🔍 测试提供商注册表...")
    
    # 检查 Dify 提供商是否已注册
    if provider_registry.is_registered(ProviderType.DIFY):
        print("✅ Dify 提供商已成功注册")
    else:
        print("❌ Dify 提供商未注册")
        return
    
    # 列出所有注册的提供商
    providers = provider_registry.list_providers()
    print(f"📋 已注册的提供商: {[p.value for p in providers]}")
    
    # 获取 Dify 配置类
    config_class = provider_registry.get_config_class(ProviderType.DIFY)
    if config_class:
        print(f"✅ 获取到 Dify 配置类: {config_class.__name__}")
    else:
        print("❌ 无法获取 Dify 配置类")
    
    # 获取 Dify 提供商类
    provider_class = provider_registry.get_provider_class(ProviderType.DIFY)
    if provider_class:
        print(f"✅ 获取到 Dify 提供商类: {provider_class.__name__}")
    else:
        print("❌ 无法获取 Dify 提供商类")


def test_dify_config():
    """测试 Dify 配置验证"""
    print("⚙️ 测试 Dify 配置验证...")
    
    # 测试有效配置
    try:
        config = DifyConfig(
            api_key="valid-dify-api-key-12345",
            base_url="https://api.dify.ai",
            default_model="gpt-3.5-turbo",
        )
        print("✅ 有效配置创建成功")
        print(f"   提供商类型: {config.provider_type}")
        print(f"   默认模型: {config.default_model}")
        print(f"   支持的模型: {config.supported_models}")
    except Exception as e:
        print(f"❌ 有效配置创建失败: {e}")
    
    # 测试无效配置
    try:
        invalid_config = DifyConfig(
            api_key="",  # 空 API key
            base_url="https://api.dify.ai",
        )
        print("❌ 应该拒绝空 API key")
    except ValueError as e:
        print(f"✅ 正确拒绝了无效配置: {e}")
    
    try:
        invalid_config = DifyConfig(
            api_key="short",  # 太短的 API key
            base_url="https://api.dify.ai",
        )
        print("❌ 应该拒绝太短的 API key")
    except ValueError as e:
        print(f"✅ 正确拒绝了太短的 API key: {e}")


async def main():
    """主测试函数"""
    print("🚀 开始测试 Dify 提供商实现\n")
    
    # 测试配置验证
    test_dify_config()
    print()
    
    # 测试注册表功能
    await test_provider_registry()
    print()
    
    # 测试实际 API 调用（需要有效的 API key）
    print("⚠️ 注意: 以下测试需要有效的 Dify API key")
    print("   请在代码中替换 'your-dify-api-key-here' 为实际的 API key")
    print("   如果没有 API key，以下测试将失败，这是正常的。\n")
    
    await test_dify_provider()


if __name__ == "__main__":
    asyncio.run(main())
