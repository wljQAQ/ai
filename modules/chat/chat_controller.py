from flask import Blueprint

bp = Blueprint("chat", __name__)


@bp.route("/chat")
def chat():
    print("chat")
    return "chat"
