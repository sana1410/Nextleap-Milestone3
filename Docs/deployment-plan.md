# Deployment Plan — Weekly App Review Pulse

Deploy the entire project (backend pipeline + frontend dashboard) as a **single Streamlit app** on **Streamlit Community Cloud**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Streamlit Community Cloud                │
│                                                  │
│  streamlit_app.py                                │
│  ┌─────────────────┐  ┌──────────────────────┐  │
│  │  Dashboard UI    │  │  Pipeline Backend    │  │
│  │  - Stat cards    │  │  - Review collector  │  │
│  │  - Theme charts  │  │  - Data processor    │  │
│  │  - Quotes        │  │  - Theme clusterer   │  │
│  │  - Rating bars   │  │  - Pulse generator   │  │
│  │  - Donut chart   │  │  - MCP delivery      │  │
│  └─────────────────┘  └──────────────────────┘  │
│                                                  │
│  Reads: data_seed/themes.json                    │
│         data_seed/pulse.md                       │
└──────────────────────┬───────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
     Play Store    Groq LLM    MCP Server
      Scraper     (Qwen 27B)   (Railway)
                              Google Docs
                                Gmail
```

**Why Streamlit?**
- Single deployment — no separate backend/frontend
- Free hosting on Streamlit Community Cloud
- Direct GitHub integration — auto-deploys on push
- Built-in secrets management for API keys
- Native Python — reuses existing pipeline code directly

---

## Part 1: Create the Streamlit App

### Step 1 — Create `streamlit_app.py`

The Streamlit app combines the dashboard UI and pipeline access in one file. It reads data from `data_seed/` (committed to git) and renders the dashboard with Streamlit components, custom HTML/CSS, and Plotly charts.

```python
import streamlit as st
import json
import os

st.set_page_config(
    page_title="Weekly App Review Pulse — Groww",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(BASE_DIR, "data_seed")

@st.cache_data
def load_themes():
    path = os.path.join(SEED_DIR, "themes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_pulse():
    path = os.path.join(SEED_DIR, "pulse.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

data = load_themes()
themes = data["themes"]
total = data["metadata"]["review_count"]

# Render stat cards, charts, themes, quotes using:
#   st.columns(), st.metric(), st.progress()
#   st.markdown() with custom HTML/CSS
#   plotly for donut chart and bar charts
```

Key sections to implement:
1. **Nav bar** — Custom HTML via `st.markdown()` with Groww branding
2. **4 stat cards** — `st.columns(4)` + `st.metric()` for Reviews, Themes, Avg Rating, Window
3. **Top themes** — `st.columns([7,5])` for two-column layout, custom styled cards
4. **Suggested actions** — Numbered action items with theme pills
5. **User voices** — Quote cards with star ratings
6. **Donut chart** — `plotly.graph_objects.Pie` for theme distribution
7. **Rating breakdown** — Horizontal bar chart with `plotly` or `st.progress()`
8. **Pulse text** — Expandable section showing the raw pulse markdown

### Step 2 — Create Streamlit config

**Create `.streamlit/config.toml`:**
```toml
[theme]
primaryColor = "#00D09C"
backgroundColor = "#F5F6FA"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1A1A2E"
font = "sans serif"

[server]
headless = true
```

### Step 3 — Update `requirements.txt`

```
google-play-scraper
groq
python-dotenv
requests
streamlit
plotly
```

Remove `flask`, `flask-cors`, `gunicorn` — they are no longer needed.

---

## Part 2: Seed Data

The `data/` directory is gitignored (runtime output). The `data_seed/` directory is committed and contains the latest pipeline output for the dashboard to display:

- `data_seed/themes.json` — 5 themes with counts, ratings, quotes
- `data_seed/pulse.md` — Generated pulse note

To refresh seed data after a pipeline run:

```bash
cp data/themes.json data_seed/themes.json
cp data/pulse.md data_seed/pulse.md
git add data_seed/
git commit -m "Update seed data from latest pipeline run"
git push
```

Streamlit Community Cloud will auto-redeploy on push.

---

## Part 3: Deploy to Streamlit Community Cloud

### Step 1 — Push to GitHub

Ensure the repo is pushed with all required files:
```
streamlit_app.py          # Main Streamlit app
.streamlit/config.toml    # Theme configuration
requirements.txt          # Python dependencies (with streamlit, plotly)
data_seed/themes.json     # Seed data
data_seed/pulse.md        # Seed data
src/                      # Pipeline source code
```

### Step 2 — Connect to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - **Repository:** `sana1410/Nextleap-Milestone3`
   - **Branch:** `master`
   - **Main file path:** `streamlit_app.py`
5. Click **"Deploy"**

### Step 3 — Configure secrets

In the Streamlit Cloud dashboard → App settings → **Secrets**, add:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
EMAIL_RECIPIENT = "your_email_here"
GOOGLE_DOC_ID = "your_google_doc_id_here"
MCP_SERVER_URL = "https://desirable-dedication-production-f08d.up.railway.app"
```

Access in code via `st.secrets["GROQ_API_KEY"]`.

### Step 4 — Verify deployment

1. Open the provided `https://<your-app>.streamlit.app` URL
2. Confirm the dashboard loads with:
   - 4 stat cards (Reviews: 380, Themes: 5, Avg Rating: 2.6, Window: 10 wks)
   - Top 3 themes with progress bars and star ratings
   - Suggested actions with numbered items
   - User voice quotes
   - Donut chart showing review distribution across 5 themes
   - Rating breakdown with 1-star alert
   - Expandable pulse text section

---

## Part 4: Environment Variables Summary

| Variable          | Where                    | Value                                                        |
|-------------------|--------------------------|--------------------------------------------------------------|
| `GROQ_API_KEY`    | Streamlit Cloud Secrets  | Your Groq API key                                            |
| `EMAIL_RECIPIENT` | Streamlit Cloud Secrets  | Target email for pulse delivery                               |
| `GOOGLE_DOC_ID`   | Streamlit Cloud Secrets  | Google Doc ID for pulse publishing                            |
| `MCP_SERVER_URL`  | Streamlit Cloud Secrets  | `https://desirable-dedication-production-f08d.up.railway.app` |

Locally, these remain in `.env` (gitignored). On Streamlit Cloud, use the Secrets panel.

---

## Part 5: CI/CD

### Auto-deploy on push

Streamlit Community Cloud monitors the connected GitHub repo. Every push to `master` triggers an automatic redeploy — no extra CI/CD configuration needed.

### Refreshing dashboard data

After running the pipeline locally:
```bash
# Run pipeline
python src/main.py --skip-fetch --dry-run

# Copy fresh data to seed
cp data/themes.json data_seed/themes.json
cp data/pulse.md data_seed/pulse.md

# Push — Streamlit auto-redeploys
git add data_seed/
git commit -m "Refresh seed data"
git push
```

### Optional: Pipeline run from Streamlit sidebar

The Streamlit app can include a sidebar button to trigger the pipeline directly on Streamlit Cloud (limited by Groq rate limits — ~10 min runtime):

```python
with st.sidebar:
    if st.button("🔄 Run Pipeline"):
        with st.spinner("Running pipeline (~10 min)..."):
            from src.main import run_pipeline
            run_pipeline(skip_fetch=False, dry_run=True)
            st.cache_data.clear()
            st.rerun()
```

---

## Part 6: Files to Clean Up

The following files from the previous Railway/Vercel deployment plan are no longer needed:

| File                | Action          | Reason                                      |
|---------------------|-----------------|---------------------------------------------|
| `server.py`         | Delete          | Flask API wrapper replaced by Streamlit      |
| `Procfile`          | Delete          | Railway-specific                             |
| `nixpacks.toml`     | Delete          | Railway-specific                             |
| `runtime.txt`       | Delete          | Railway-specific                             |
| `frontend/vercel.json` | Delete       | Vercel-specific                              |
| `frontend/index.html`  | Keep (reference) | Design reference for Streamlit layout     |

Update `requirements.txt` to replace `flask`/`flask-cors`/`gunicorn` with `streamlit`/`plotly`.

---

## Deployment Checklist

- [ ] Create `streamlit_app.py` (dashboard + pipeline access)
- [ ] Create `.streamlit/config.toml` (Groww theme)
- [ ] Update `requirements.txt` (add `streamlit`, `plotly`; remove `flask`, `flask-cors`, `gunicorn`)
- [ ] Ensure `data_seed/` has latest `themes.json` and `pulse.md`
- [ ] Remove Railway/Vercel files (`server.py`, `Procfile`, `nixpacks.toml`, `runtime.txt`, `frontend/vercel.json`)
- [ ] Push to GitHub
- [ ] Connect repo on [share.streamlit.io](https://share.streamlit.io)
- [ ] Add secrets (GROQ_API_KEY, EMAIL_RECIPIENT, GOOGLE_DOC_ID, MCP_SERVER_URL)
- [ ] Verify dashboard loads at `*.streamlit.app` URL
- [ ] (Optional) Add sidebar pipeline trigger button
