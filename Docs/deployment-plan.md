# Deployment Plan — Weekly App Review Pulse

Deploy the backend pipeline on **Railway** and the frontend dashboard on **Vercel**.

---

## Architecture Overview

```
┌──────────────────────┐       ┌──────────────────────────┐
│   Vercel (Frontend)  │       │    Railway (Backend)      │
│                      │       │                           │
│  frontend/index.html │◄──────│  Python pipeline (cron)   │
│  Static dashboard    │  API  │  src/main.py              │
│                      │       │                           │
│  Reads: /api/data    │       │  Serves: /api/data        │
│         /api/pulse   │       │          /api/pulse       │
└──────────────────────┘       └───────────┬───────────────┘
                                           │
                              ┌────────────┼────────────┐
                              │            │            │
                         Play Store    Groq LLM    MCP Server
                          Scraper     (Qwen 27B)   (Railway)
                                                  Google Docs
                                                    Gmail
```

---

## Part 1: Backend on Railway

### Step 1 — Create a Flask API wrapper

The pipeline currently runs as a CLI script. Wrap it in a minimal Flask server so Railway can keep it alive and serve data to the frontend.

**Create `server.py`** in the project root:

```python
from flask import Flask, jsonify, send_file
import json
import os
import subprocess
import threading

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "weekly-app-review-pulse"})

@app.route("/api/data")
def get_data():
    """Return themes.json for the frontend dashboard."""
    themes_path = os.path.join(DATA_DIR, "themes.json")
    if not os.path.exists(themes_path):
        return jsonify({"error": "No data yet. Run the pipeline first."}), 404
    with open(themes_path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/pulse")
def get_pulse():
    """Return the generated pulse markdown."""
    pulse_path = os.path.join(DATA_DIR, "pulse.md")
    if not os.path.exists(pulse_path):
        return jsonify({"error": "No pulse yet. Run the pipeline first."}), 404
    with open(pulse_path, "r", encoding="utf-8") as f:
        return jsonify({"pulse": f.read()})

@app.route("/api/run", methods=["POST"])
def run_pipeline():
    """Trigger a pipeline run (non-blocking)."""
    def _run():
        subprocess.run(
            ["python", "src/main.py", "--dry-run"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({"status": "pipeline started"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
```

### Step 2 — Add deployment files

**Update `requirements.txt`:**
```
google-play-scraper
groq
python-dotenv
requests
flask
gunicorn
```

**Create `Procfile`** in the project root:
```
web: gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120
```

**Create `runtime.txt`** in the project root:
```
python-3.11.x
```

**Create `nixpacks.toml`** (Railway's build system):
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120"
```

### Step 3 — Seed data for first deploy

The `data/` directory is gitignored. For the first deploy, the pipeline needs to run at least once to generate `themes.json` and `pulse.md`. Options:

- **Option A (recommended):** Run the pipeline locally first, then commit the data files to a `data_seed/` directory. Add a startup script that copies seed data to `data/` if empty.
- **Option B:** After deploying, trigger `/api/run` to run the pipeline on Railway (~10 min).

### Step 4 — Deploy to Railway

```bash
# 1. Install Railway CLI (if not installed)
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create a new project
railway init

# 4. Set environment variables
railway variables set GROQ_API_KEY=your_key_here
railway variables set EMAIL_RECIPIENT=your_email_here
railway variables set GOOGLE_DOC_ID=your_google_doc_id_here
railway variables set MCP_SERVER_URL=https://desirable-dedication-production-f08d.up.railway.app

# 5. Deploy
railway up

# 6. Get the public URL
railway domain
```

Railway will:
- Detect the Python project via `requirements.txt` / `nixpacks.toml`
- Install dependencies
- Start the Gunicorn server on the assigned PORT
- Provide a public `*.up.railway.app` URL

### Step 5 — Verify backend

```bash
# Health check
curl https://<your-app>.up.railway.app/

# Fetch themes data
curl https://<your-app>.up.railway.app/api/data

# Fetch pulse
curl https://<your-app>.up.railway.app/api/pulse
```

---

## Part 2: Frontend on Vercel

### Step 1 — Make frontend dynamic

Update `frontend/index.html` to fetch data from the Railway backend API instead of using hardcoded values. Add a `<script>` block that:

1. Fetches `https://<railway-backend-url>/api/data` on page load
2. Populates stat cards, themes, quotes, donut chart, and rating bars from the API response
3. Falls back to the hardcoded values if the API is unreachable

Also add CORS headers on the backend (`flask-cors` package) or use Vercel rewrites to proxy `/api/*` to Railway.

### Step 2 — Create Vercel configuration

**Create `frontend/vercel.json`:**
```json
{
  "buildCommand": null,
  "outputDirectory": ".",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://<your-railway-app>.up.railway.app/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=3600" }
      ]
    }
  ]
}
```

The `rewrites` block proxies `/api/*` requests to the Railway backend, avoiding CORS issues entirely.

### Step 3 — Deploy to Vercel

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Navigate to frontend directory
cd frontend

# 3. Deploy (follow the prompts)
vercel

# 4. For production deployment
vercel --prod
```

Vercel will:
- Detect a static site (single `index.html`)
- Deploy it globally on their CDN
- Apply the `vercel.json` rewrite rules
- Provide a public `*.vercel.app` URL

### Step 4 — Verify frontend

1. Open `https://<your-app>.vercel.app` in a browser
2. Confirm the dashboard loads with all sections:
   - 4 stat cards (Reviews, Themes, Rating, Window)
   - Top 3 themes with progress bars
   - Suggested actions
   - User voice quotes
   - Donut chart (review distribution)
   - Rating breakdown with 1-star alert
3. Check browser DevTools Network tab — `/api/data` should proxy to Railway

---

## Part 3: Environment Variables Summary

| Variable          | Where         | Value                                                        |
|-------------------|---------------|--------------------------------------------------------------|
| `GROQ_API_KEY`    | Railway       | Your Groq API key                                            |
| `EMAIL_RECIPIENT` | Railway       | Target email for pulse delivery                               |
| `GOOGLE_DOC_ID`   | Railway       | Google Doc ID for pulse publishing                            |
| `MCP_SERVER_URL`  | Railway       | `https://desirable-dedication-production-f08d.up.railway.app` |
| `PORT`            | Railway (auto)| Set automatically by Railway                                  |

The frontend on Vercel needs **no environment variables** — it proxies API requests via `vercel.json` rewrites.

---

## Part 4: CI/CD (Optional)

### Auto-deploy on push

Both Railway and Vercel support GitHub integration:

1. **Railway:** Connect the GitHub repo → auto-deploys on push to `master`
2. **Vercel:** Connect the GitHub repo → set root directory to `frontend/` → auto-deploys on push

### Scheduled pipeline runs

To run the pipeline weekly (every Monday at 6 AM UTC), add a Railway cron job:

```bash
# In Railway dashboard → Settings → Cron
# Schedule: 0 6 * * 1
# Command: python src/main.py
```

Or use the `/api/run` endpoint with an external cron service (cron-job.org, GitHub Actions).

**GitHub Actions example** (`.github/workflows/weekly-pulse.yml`):
```yaml
name: Weekly Pulse
on:
  schedule:
    - cron: '0 6 * * 1'
  workflow_dispatch:

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger pipeline
        run: |
          curl -X POST https://<your-app>.up.railway.app/api/run
```

---

## Deployment Checklist

- [ ] Create `server.py` (Flask API wrapper)
- [ ] Update `requirements.txt` (add `flask`, `gunicorn`)
- [ ] Create `Procfile`
- [ ] Create `nixpacks.toml`
- [ ] Deploy backend to Railway
- [ ] Set Railway environment variables
- [ ] Verify backend API endpoints
- [ ] Update `frontend/index.html` to fetch from API
- [ ] Create `frontend/vercel.json` with rewrites
- [ ] Deploy frontend to Vercel
- [ ] Verify frontend loads with live data
- [ ] (Optional) Connect GitHub repo for auto-deploy
- [ ] (Optional) Set up weekly cron schedule
