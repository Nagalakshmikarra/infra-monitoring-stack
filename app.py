from flask import Flask, jsonify, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUESTS = Counter("app_requests_total", "Total requests received", ["endpoint"])

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Infra Monitoring Stack</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: Segoe UI, Arial, sans-serif;
      background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
      color: #fff;
    }
    .card {
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      padding: 40px 50px;
      text-align: center;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
      max-width: 520px;
    }
    h1 { font-size: 2rem; margin-bottom: 10px; }
    p { margin-bottom: 25px; opacity: 0.9; }
    .status {
      display: inline-block;
      padding: 8px 22px;
      border-radius: 30px;
      background: #22c55e;
      font-weight: bold;
      margin-bottom: 25px;
    }
    .links a {
      display: inline-block;
      margin: 5px;
      padding: 10px 20px;
      border-radius: 10px;
      background: #fff;
      color: #764ba2;
      text-decoration: none;
      font-weight: 600;
    }
    .links a:hover { background: #f3e8ff; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Hello from the infra-monitoring-stack!</h1>
    <p>Flask + Nginx + Prometheus running in Docker</p>
    <div class="status">Status: OK</div>
    <div class="links">
      <a href="/health">Health</a>
      <a href="/metrics">Metrics</a>
      <a href="/api/status">JSON</a>
    </div>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    REQUESTS.labels(endpoint="/").inc()
    return PAGE


@app.route("/api/status")
def api_status():
    REQUESTS.labels(endpoint="/api/status").inc()
    return jsonify(message="Hello from the infra-monitoring-stack!", status="ok")


@app.route("/health")
def health():
    REQUESTS.labels(endpoint="/health").inc()
    return jsonify(status="healthy")


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)