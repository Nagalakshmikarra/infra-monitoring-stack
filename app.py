from flask import Flask, jsonify, Response, request
from markupsafe import escape
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = Flask(__name__)

REQUESTS = Counter("app_requests_total", "Total requests received", ["endpoint"])

LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{TITLE}}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
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
      max-width: 620px;
      width: 100%;
    }
    h1 { font-size: 2rem; margin-bottom: 10px; }
    p { margin-bottom: 25px; opacity: 0.9; }
    .badge {
      display: inline-block;
      padding: 8px 22px;
      border-radius: 30px;
      background: #22c55e;
      font-weight: bold;
      margin-bottom: 25px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 25px;
    }
    .stat {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 14px;
      padding: 16px 10px;
    }
    .stat .num { font-size: 1.6rem; font-weight: bold; }
    .stat .label { font-size: 0.85rem; opacity: 0.9; margin-top: 4px; }
    pre {
      text-align: left;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 25px;
      overflow-x: auto;
      font-size: 0.95rem;
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
    {{BODY}}
    <div class="links">
      <a href="/">Home</a>
      <a href="/health">Health</a>
      <a href="/metrics">Metrics</a>
      <a href="/api/status">JSON</a>
    </div>
  </div>
</body>
</html>
"""


def page(title, body):
    return LAYOUT.replace("{{TITLE}}", title).replace("{{BODY}}", body)


def wants_html(plain_type):
    """True when the visitor is a browser. Programs like Prometheus,
    curl and CI get plain data instead."""
    if request.args.get("format") == "raw":
        return False
    best = request.accept_mimetypes.best_match([plain_type, "text/html"])
    return best == "text/html"


@app.route("/")
def index():
    REQUESTS.labels(endpoint="/").inc()
    body = """
    <h1>Hello from the infra-monitoring-stack!</h1>
    <p>Flask + Nginx + Prometheus running in Docker</p>
    <div class="badge">Status: OK</div>
    """
    return page("Infra Monitoring Stack", body)


@app.route("/api/status")
def api_status():
    REQUESTS.labels(endpoint="/api/status").inc()
    data = {"message": "Hello from the infra-monitoring-stack!", "status": "ok"}
    if wants_html("application/json"):
        body = (
            "<h1>JSON Status</h1>"
            "<p>This is the data that programs receive</p>"
            f"<pre>{escape(jsonify(data).get_data(as_text=True).strip())}</pre>"
        )
        return page("JSON Status", body)
    return jsonify(data)


@app.route("/health")
def health():
    REQUESTS.labels(endpoint="/health").inc()
    if wants_html("application/json"):
        body = """
        <h1>Health Check</h1>
        <p>Is the app alive and well?</p>
        <div class="badge">Healthy</div>
        """
        return page("Health Check", body)
    return jsonify(status="healthy")


def collect_stats():
    stats = {"requests": {}, "memory": None, "cpu": None, "fds": None, "python": None}
    for family in REGISTRY.collect():
        for sample in family.samples:
            if sample.name == "app_requests_total":
                stats["requests"][sample.labels.get("endpoint", "?")] = int(sample.value)
            elif sample.name == "process_resident_memory_bytes":
                stats["memory"] = round(sample.value / 1024 / 1024, 1)
            elif sample.name == "process_cpu_seconds_total":
                stats["cpu"] = round(sample.value, 2)
            elif sample.name == "process_open_fds":
                stats["fds"] = int(sample.value)
            elif sample.name == "python_info":
                stats["python"] = sample.labels.get("version")
    return stats


def stat_box(number, label):
    return f'<div class="stat"><div class="num">{escape(number)}</div><div class="label">{escape(label)}</div></div>'


@app.route("/metrics")
def metrics():
    if wants_html("text/plain"):
        s = collect_stats()
        boxes = ""
        for endpoint, count in sorted(s["requests"].items()):
            boxes += stat_box(count, f"Visits to {endpoint}")
        if s["memory"] is not None:
            boxes += stat_box(f'{s["memory"]} MB', "Memory used")
        if s["cpu"] is not None:
            boxes += stat_box(f'{s["cpu"]} s', "CPU time")
        if s["fds"] is not None:
            boxes += stat_box(s["fds"], "Open files")
        if s["python"]:
            boxes += stat_box(s["python"], "Python version")
        body = f"""
        <h1>Metrics Dashboard</h1>
        <p>Live numbers from your app. <a href="/metrics?format=raw" style="color:#fff">See raw data</a></p>
        <div class="grid">{boxes}</div>
        """
        return page("Metrics Dashboard", body)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)