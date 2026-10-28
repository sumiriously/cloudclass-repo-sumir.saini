import sys
from pathlib import Path

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from page import page as _page

app = Flask(__name__)
INSTANCE = "app3"
PORT = 5002
handled = 0


@app.get("/")
def home():
    global handled
    handled += 1
    return _page(INSTANCE, PORT, handled)


@app.get("/health")
def health():
    return {"status": "ok", "instance": INSTANCE, "port": PORT}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT)
