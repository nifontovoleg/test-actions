# Time Server API

A small FastAPI service that returns server time and date, converts UTC to a target timezone, and deploys with one push via GitHub Actions → Docker → VPS.

Use it as a CI/CD learning sandbox or as a lightweight time backend for bots, frontends, and internal scripts.

---

## Why this project

| Goal | How it helps |
|------|----------------|
| Get server time / date | `GET /time`, `GET /date` |
| Convert UTC → city / timezone | `GET /convert` |
| Check that the service is up | `GET /health` |
| Learn end-to-end API deploy | Docker + GHCR + SSH — see [DEPLOYMENT.md](DEPLOYMENT.md) |

This is not “yet another world clock”. It is a **clear scaffold**: minimal backend + container + automatic VPS rollout. Perfect for practicing the pipeline, then growing features on top.

---

## Who it is for

- **Developers** who need a simple time API without heavy infrastructure
- **People learning FastAPI / Docker / GitHub Actions** — from code to production
- **Bot and mini-app authors** who need server-side date/time and timezone conversion
- **Teams** that want a reference flow: push to `main` → container on a VPS

---

## How to use it

### As a learning project
Clone → run locally → open Swagger → push to `main` → see the container on the server. The full path from code to production lives in one repo.

### As a microservice
Call it over HTTP from a bot, frontend, or cron:

```text
GET /time
GET /date
GET /convert?time=15.00&timezone=Yekaterinburg
GET /health
```

### As a deploy template
Copy `Dockerfile` + `.github/workflows/deploy.yml`, set your secrets — the same pipeline works for another FastAPI app.

### Live stand (example)
After deploy the API is available on the VPS:

- Health: `http://<HOST>:8000/health`
- Docs: `http://<HOST>:8000/docs`

---

## Features

- Server time as ISO, Unix timestamp, and human-readable string
- Date with year / month / day and weekday
- **UTC → timezone** conversion (city alias or IANA name)
- Health check for monitoring and load balancers
- Single-file Docker image
- CI/CD: build → GHCR → SSH deploy

---

## Quick start

### Requirements

- Python **3.11+**
- Docker (optional)
- GitHub repo + VPS with Docker (for deploy)

### Install

```powershell
git clone https://github.com/nifontovoleg/test-actions.git
cd test-actions
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy env.example .env
```

### Run locally

```powershell
python main.py
```

or:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| What | URL |
|------|-----|
| API | http://127.0.0.1:8000 |
| Swagger | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

### Run with Docker

```powershell
docker build -t time-server-api .
docker run -d --name time-server -p 8000:8000 time-server-api
```

Smoke test:

```powershell
curl http://127.0.0.1:8000/health
```

---

## Repository layout

```text
.
├── main.py                      # FastAPI application
├── requirements.txt             # dependencies
├── env.example                  # sample environment variables
├── Dockerfile                   # application image
├── .dockerignore
├── .gitignore
├── README.md                    # this file
├── DEPLOYMENT.md                # deploy guide and secrets
└── .github/workflows/deploy.yml # CI/CD: build → GHCR → SSH
```

| File | Role |
|------|------|
| `main.py` | Endpoints and time logic |
| `DEPLOYMENT.md` | Secrets, SSH, GHCR, troubleshooting |
| `deploy.yml` | Two jobs: image build and VPS deploy |

---

## API

Base path: `/`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Welcome message and docs link |
| `GET` | `/time` | Current server time |
| `GET` | `/date` | Current server date |
| `GET` | `/convert` | Convert time from UTC |
| `GET` | `/health` | Service status |

Interactive docs: [`/docs`](http://127.0.0.1:8000/docs).

### `GET /time`

```json
{
  "current_time": "2026-07-21T20:17:00.123456",
  "timestamp": 1753112220.123456,
  "formatted_time": "2026-07-21 20:17:00",
  "timezone": "UTC"
}
```

### `GET /date`

```json
{
  "date": "2026-07-21",
  "formatted_date": "21.07.2026",
  "year": 2026,
  "month": 7,
  "day": 21,
  "weekday": "Tuesday"
}
```

### `GET /convert`

Converts **UTC** time into the target timezone.

| Parameter | Example | Description |
|-----------|---------|-------------|
| `time` | `15.00` | UTC time (`15.00`, `15:00`, `15:00:00`) |
| `timezone` | `Yekaterinburg` | City alias or IANA (`Asia/Yekaterinburg`) |

```text
GET /convert?time=15.00&timezone=Yekaterinburg
```

```json
{
  "input_time_utc": "15:00:00",
  "timezone": "Asia/Yekaterinburg",
  "converted_time": "20:00:00",
  "converted_datetime": "2026-07-21T20:00:00+05:00"
}
```

Logic: `15:00 UTC` + Yekaterinburg (`UTC+5`) → `20:00`.

City aliases include (partial list):  
Yekaterinburg, Moscow, Saint Petersburg, Novosibirsk, Krasnoyarsk, Vladivostok, London, Berlin, Tokyo, New York — or any valid IANA name. Russian aliases (e.g. `Екатеринбург`) still work.

### `GET /health`

```json
{
  "status": "healthy",
  "timestamp": "2026-07-21T19:19:28.224821"
}
```

---

## Environment variables

Copy `env.example` → `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Port |
| `DEBUG` | `false` | `true` enables uvicorn reload |

`.env` is not committed to git.

---

## CI/CD and deploy

Short path:

```text
push to main
   → Docker build
   → push to ghcr.io/<owner>/<repo>
   → SSH to VPS
   → docker pull + run (container time-server, port 8000)
```

Full guide (secrets, SSH key, GHCR, errors): **[DEPLOYMENT.md](DEPLOYMENT.md)**

Required repository secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` (+ optional `SSH_PORT`).

---

## How to grow the project

Ideas from simple to serious:

### Near-term improvements
1. **More timezones** — expand the city map or expose `GET /timezones`
2. **Full datetime in `/convert`** — accept `2026-07-21T15:00`, not only time-of-day
3. **Reverse conversion** — local timezone → UTC
4. **Tests** — `pytest` + `httpx` / `TestClient` for `/time`, `/date`, `/convert`
5. **Linters in CI** — ruff / mypy job before deploy

### Product directions
- Rate limit and a simple API key for a public stand
- Metrics (`/metrics`) and alerts on `/health`
- Nginx/Caddy + HTTPS in front of the container
- API versioning (`/api/v1/...`)
- Time for multiple regions in one response

### Infrastructure
- Staging environment (deploy from `develop`)
- Rollback to a previous image SHA tag
- docker compose for local api + reverse-proxy

Growth pattern: **stabilize the API contract and tests first**, then add auth, HTTPS, and monitoring.

---

## Request examples

```powershell
# local
curl http://127.0.0.1:8000/time
curl http://127.0.0.1:8000/date
curl "http://127.0.0.1:8000/convert?time=15.00&timezone=Yekaterinburg"
curl http://127.0.0.1:8000/health
```

```powershell
# Python
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/time').read().decode())"
```

---

## Stack

| Layer | Tech |
|-------|------|
| API | Python 3.11+, FastAPI, Uvicorn |
| Time | `datetime`, `zoneinfo` |
| Config | `python-dotenv` |
| Container | Docker (`python:3.11-slim`) |
| CI/CD | GitHub Actions, GHCR, SSH deploy |

---

## Contributing

This is a practical learning repository. Fork it, adapt it, reuse the deploy workflow.

When you add a feature:
1. Branch from `main`
2. Update the README if the API changes
3. PR or merge into `main` → automatic deploy

---

## Useful links

- [DEPLOYMENT.md](DEPLOYMENT.md) — deploy, secrets, troubleshooting
- Swagger UI — `/docs`
- FastAPI — https://fastapi.tiangolo.com/
- GitHub Container Registry — https://docs.github.com/packages/learn-github-packages
