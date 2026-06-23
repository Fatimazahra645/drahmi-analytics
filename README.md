# Drahmi BVC Dashboard

FastAPI app serving the quantitative analysis dashboard. Drahmi is called **server-side** via the same `/api/v1` client pattern as [eco-ai](../eco-ai/backend/apps/api/src/integrations/drahmi/client.py). The browser only hits `/api/drahmi/*` on this host (no CORS, API key stays in `.env`).

## Setup

```bash
cd eco-ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DRAHMI_API_KEY (same key as eco-ai backend)
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Layout

```
app/
  main.py                        # FastAPI app + static files
  settings.py                    # env config
  core/http.py                   # shared httpx pool (like eco-ai)
  core/drahmi_limiter.py         # max 4 concurrent upstream Drahmi calls
  integrations/drahmi/client.py  # DrahmiClient — /api/v1 paths + X-API-Key
  integrations/drahmi/cache.py   # in-memory TTL (stocks 15m, history/risk 10m)
  routes/drahmi.py               # browser proxy → DrahmiClient.proxy_get()
static/
  index.html                     # dashboard UI
```
