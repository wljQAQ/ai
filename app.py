"""
AI聊天系统应用入口
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入应用工厂
from app_factory import create_app


def main():
    """应用主入口"""
    try:
        # 创建Flask应用
        app = create_app()

        # 获取配置
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 3000))
        debug = os.getenv("DEBUG", "true").lower() == "true"

        # print(f"🚀 Starting AI Chat System...")
        # print(f"📍 Server: http://{host}:{port}")
        # print(f"🔧 Debug mode: {debug}")
        # print(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development')}")

        # 启动应用
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        print(f"❌ Failed to start application: {str(e)}")
        raise


if __name__ == "__main__":
    main()
