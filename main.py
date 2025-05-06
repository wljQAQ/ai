from flask import Flask
from markupsafe import escape

app = Flask("ai")


@app.route("/<name>")
def hello(name):
    return f"Hello, {escape(name)}!"


def main():
    pass
    # app.run(host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
