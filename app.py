from flask import Flask
from markupsafe import escape
from app_factory import create_app


def hello(name):
    return f"Hello, {escape(name)}!"


def main():
    app = create_app()

    app.run(host="0.0.0.0", port=3000, debug=True)


if __name__ == "__main__":
    main()
