# Infra Monitoring Stack

A small, reproducible infrastructure project: a containerized Flask web app served behind an **Nginx** reverse proxy, with metrics scraped by **Prometheus** and visualized in **Grafana**. The whole stack starts with a single `docker compose up`, and a **GitHub Actions** pipeline builds it and runs smoke tests on every push.

I built this to practice the fundamentals of modern infrastructure and platform engineering: containerization, service orchestration, reverse proxying, observability and CI.

## Architecture
![Dashboard](docs/dashboard.png)
```
                 +-----------+        +---------------------+
   Browser ----> |   Nginx   | -----> |  Flask app (Gunicorn)|
   :8080         |  (proxy)  |        |  /  /health /metrics |
                 +-----------+        +----------+----------+
                                                 ^
                                                 | scrapes /metrics every 15s
                                      +----------+----------+
                                      |     Prometheus      |  :9090
                                      +----------+----------+
                                                 ^
                                                 | data source
                                      +----------+----------+
                                      |       Grafana       |  :3000
                                      +---------------------+
```

## Tech stack

| Layer | Tool |
| --- | --- |
| Application | Python, Flask, Gunicorn |
| Containers | Docker, Docker Compose |
| Reverse proxy | Nginx |
| Monitoring | Prometheus, Grafana |
| CI | GitHub Actions |

## Project structure

```
.
├── app.py                  # Flask app with Prometheus metrics
├── requirements.txt        # Python dependencies
├── Dockerfile              # Image for the Flask app
├── docker-compose.yml      # Defines app, nginx, prometheus, grafana
├── nginx.conf              # Reverse proxy configuration
├── prometheus.yml          # Prometheus scrape configuration
└── .github/workflows/
    └── ci.yml              # Build + smoke test pipeline
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (`docker compose version` should work)
- Git

## Getting started

```bash
git clone https://github.com/<your-username>/infra-monitoring-stack.git
cd infra-monitoring-stack
docker compose up -d --build
```

Check that all four containers are running:

```bash
docker compose ps
```

## Endpoints

| Service | URL | Notes |
| --- | --- | --- |
| App (via Nginx) | http://localhost:8080 | Returns a JSON greeting |
| Health check | http://localhost:8080/health | Returns `{"status": "healthy"}` |
| App metrics | http://localhost:8080/metrics | Prometheus text format |
| Prometheus | http://localhost:9090 | Check *Status > Targets* shows `flask-app` as UP |
| Grafana | http://localhost:3000 | Default login `admin` / `admin` (you will be asked to change it) |

## Set up the Grafana dashboard

1. Open Grafana at http://localhost:3000 and log in.
2. Go to **Connections > Data sources > Add data source > Prometheus**.
3. Set the URL to `http://prometheus:9090` and click **Save & test**.
4. Go to **Dashboards > New > New dashboard > Add visualization**, pick the Prometheus data source and use this query:

   ```
   rate(app_requests_total[1m])
   ```

5. Generate some traffic to see the graph move:

   ```bash
   for i in $(seq 1 50); do curl -s http://localhost:8080/ > /dev/null; done
   ```

## How it works

- **Flask app** exposes `/`, `/health` and `/metrics`. A Prometheus counter, `app_requests_total`, tracks requests per endpoint.
- **Gunicorn** runs the app inside the container, which is closer to production than Flask's development server.
- **Nginx** is the only public entry point for the app. The app container is only reachable on the internal Docker network.
- **Prometheus** scrapes `app:5000/metrics` every 15 seconds.
- **Grafana** reads from Prometheus and charts the metrics.
- **GitHub Actions** builds the stack, curls `/health` through Nginx, checks Prometheus is healthy, then tears everything down.

## Stopping and cleaning up

```bash
docker compose down        # stop containers
docker compose down -v     # also remove the Grafana volume
```

## What I learned

- Writing a Dockerfile and keeping the image small with a slim base image
- Wiring multiple services together with Docker Compose and internal networking
- Configuring Nginx as a reverse proxy
- Exposing custom application metrics and scraping them with Prometheus
- Automating build and smoke tests with GitHub Actions

## Possible improvements

- Provision the Grafana data source and dashboard automatically from files
- Add Prometheus alert rules and Alertmanager
- Add HTTPS with a self-signed certificate on Nginx
- Deploy the stack to a cloud VM with Terraform
- Port the deployment to Kubernetes with a Helm chart

## License

MIT