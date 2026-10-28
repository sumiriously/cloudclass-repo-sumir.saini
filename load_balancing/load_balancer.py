import threading

import requests
from flask import Flask, Response, request

load_balancer = Flask(__name__)

# Round-robin pool. Uncomment app3 and app4 after those processes are running
# to simulate scaling out.
targets = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003",
]

index = 0
index_lock = threading.Lock()

SKIP_REQUEST_HEADERS = {"host", "content-length", "connection"}
SKIP_RESPONSE_HEADERS = {"content-encoding", "content-length", "transfer-encoding", "connection"}


def next_target():
    global index
    with index_lock:
        target = targets[index % len(targets)]
        index = (index + 1) % len(targets)
        return target


@load_balancer.get("/favicon.ico")
def favicon():
    return Response(status=204)


@load_balancer.get("/pool")
def pool():
    rows = []
    for target in targets:
        try:
            health = requests.get(f"{target.rstrip('/')}/health", timeout=1).json()
            name = health.get("instance", target)
            port = health.get("port", "")
            state = "up"
        except requests.RequestException:
            name = target
            port = ""
            state = "down"
        rows.append(
            f"<li><strong>{name}</strong> {target} — {state}"
            + (f" (port {port})" if port else "")
            + "</li>"
        )
    body = "".join(rows)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Load balancer pool</title>
    <style>
      body {{
        margin: 0;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        background: linear-gradient(165deg, #023047 0%, #046873 42%, #94d2bd 100%);
        color: #07262f;
      }}
      main {{
        max-width: 720px;
        margin: 10vh auto;
        padding: 2rem;
        background: rgba(255, 251, 244, 0.95);
        border-radius: 22px;
      }}
      h1 {{ font-family: Georgia, serif; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Auto-scaling pool</h1>
      <p>Active targets: {len(targets)}</p>
      <ul>{body}</ul>
    </main>
  </body>
</html>
"""


@load_balancer.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@load_balancer.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def balance(path):
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in SKIP_REQUEST_HEADERS
    }
    last_error = None

    for _ in range(len(targets)):
        target = next_target()
        url = target.rstrip("/") + request.path
        if request.query_string:
            url = f"{url}?{request.query_string.decode()}"
        try:
            resp = requests.request(
                method=request.method,
                url=url,
                data=request.get_data(),
                headers=headers,
                timeout=2,
            )
        except requests.RequestException as error:
            last_error = error
            continue

        response_headers = [
            (key, value)
            for key, value in resp.headers.items()
            if key.lower() not in SKIP_RESPONSE_HEADERS
        ]
        return Response(resp.content, status=resp.status_code, headers=response_headers)

    return Response(f"No application instances are available. {last_error}", status=503)


if __name__ == "__main__":
    load_balancer.run(host="127.0.0.1", port=8000)
