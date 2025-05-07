# flask app 工厂函数

from omni_ai_app import OmniAiApp
from modules.chat.chat_controller import bp


def create_app() -> OmniAiApp:
    app = OmniAiApp("ai")

    app.register_blueprint(bp, url_prefix="/api")

    return app
