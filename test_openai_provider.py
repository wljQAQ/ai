"""
测试重构后的 OpenAI Provider
"""

import asyncio
from core.model_providers.openai_provider import OpenAIProvider, OpenAIConfig, OpenAIRequest


async def test_openai_provider():
    """测试 OpenAI Provider 的功能"""
    
    print("=== 测试 OpenAI Provider 重构 ===\n")
    
    # 1. 测试配置验证
    print("1. 测试配置验证:")
    print("-" * 40)
    
    # 有效配置
    valid_config = {
        "api_key": "sk-test123456789",
        "models": ["gpt-3.5-turbo", "gpt-4"],
        "timeout": 60.0,
        "max_retries": 3
    }
    
    try:
        provider = OpenAIProvider(valid_config)
        print("✅ 有效配置创建成功")
        print(f"   支持的模型: {provider.get_supported_models()}")
        print(f"   提供商名称: {provider._get_provider_name()}")
    except Exception as e:
        print(f"❌ 配置创建失败: {e}")
    
    # 无效配置
    invalid_config = {
        "api_key": "invalid-key",  # 不以 sk- 开头
        "models": ["invalid-model"],  # 不支持的模型
    }
    
    try:
        provider = OpenAIProvider(invalid_config)
        print("❌ 无效配置不应该创建成功")
    except Exception as e:
        print(f"✅ 无效配置正确被拒绝: {e}")
    
    # 2. 测试请求验证
    print("\n2. 测试请求验证:")
    print("-" * 40)
    
    # 有效请求
    valid_request = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        request = OpenAIRequest(**valid_request)
        print("✅ 有效请求创建成功")
        print(f"   消息数量: {len(request.messages)}")
        print(f"   模型: {request.model}")
        print(f"   温度: {request.temperature}")
    except Exception as e:
        print(f"❌ 请求创建失败: {e}")
    
    # 无效请求
    invalid_request = {
        "messages": [
            {"role": "invalid", "content": "Hello"}  # 无效角色
        ],
        "temperature": 3.0,  # 超出范围
        "max_tokens": 10000  # 超出范围
    }
    
    try:
        request = OpenAIRequest(**invalid_request)
        print("❌ 无效请求不应该创建成功")
    except Exception as e:
        print(f"✅ 无效请求正确被拒绝: {e}")
    
    # 3. 测试聊天功能（模拟）
    print("\n3. 测试聊天功能:")
    print("-" * 40)
    
    try:
        provider = OpenAIProvider(valid_config)
        request = OpenAIRequest(**valid_request)
        
        # 测试同步聊天
        response = await provider.chat(request)
        print("✅ 聊天响应成功")
        print(f"   响应ID: {response.id}")
        print(f"   内容: {response.content}")
        print(f"   模型: {response.model}")
        print(f"   Token使用: {response.usage}")
        
        # 测试流式聊天
        print("\n   流式响应:")
        async for chunk in provider.chat_stream(request):
            print(f"   📝 {chunk}", end="")
        print()  # 换行
        
    except Exception as e:
        print(f"❌ 聊天测试失败: {e}")
    
    # 4. 测试序列化
    print("\n4. 测试序列化:")
    print("-" * 40)
    
    try:
        config = OpenAIConfig(**valid_config)
        request = OpenAIRequest(**valid_request)
        
        # JSON 序列化
        config_json = config.model_dump_json()
        request_json = request.model_dump_json()
        
        print("✅ 序列化成功")
        print(f"   配置JSON长度: {len(config_json)} 字符")
        print(f"   请求JSON长度: {len(request_json)} 字符")
        
        # 反序列化
        config_restored = OpenAIConfig.model_validate_json(config_json)
        request_restored = OpenAIRequest.model_validate_json(request_json)
        
        print("✅ 反序列化成功")
        print(f"   配置API密钥: {config_restored.api_key[:10]}...")
        print(f"   请求消息数: {len(request_restored.messages)}")
        
    except Exception as e:
        print(f"❌ 序列化测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_openai_provider())
