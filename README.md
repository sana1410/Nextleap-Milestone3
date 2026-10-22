# Weekly App Review Pulse — Groww

An automated pipeline that collects Play Store reviews for the **Groww** fintech app, clusters them into themes using an LLM, generates a concise weekly pulse note, and delivers it via Google Docs and Gmail. Includes a Streamlit dashboard for visualization.

**Live Dashboard:** [nextleap-milestone3-mefgibqssthnkyueg49otr.streamlit.app](https://nextleap-milestone3-mefgibqssthnkyueg49otr.streamlit.app/)

---

## Architecture

```
Play Store ──► Review Collector ──► Data Processor ──► Theme Clusterer ──► Pulse Generator ──► Delivery
  (scraper)     1,237 reviews       PII stripping       Groq/Qwen LLM       ≤250 words         MCP Server
                                    380 cleaned          5 themes                              Google Docs
                                                                                                Gmail
                                                         ▼
                                                   Streamlit Dashboard
```

## Pipeline Stages

| Stage | Module | Description |
|-------|--------|-------------|
| 1. Collection | `src/review_collector.py` | Fetches reviews from Google Play using dual-sort strategy (NEWEST + MOST_RELEVANT), deduplicates by reviewId |
| 2. Processing | `src/data_processor.py` | Strips PII (7 regex patterns), removes emoji, filters English-only (ASCII ratio ≥ 0.5), enforces >8 word minimum, case-insensitive dedup |
| 3. Clustering | `src/theme_clusterer.py` | 4-phase batched clustering via Groq API (Qwen 27B). Batch size 40, 65s rate-limit delay between batches |
| 4. Pulse | `src/pulse_generator.py` | Generates a ≤250-word pulse note with top 3 themes, user quotes, and suggested actions |
| 5. Delivery | `src/delivery.py` | Publishes to Google Docs and sends via Gmail using MCP (Model Context Protocol) Streamable HTTP transport |
| 6. Orchestration | `src/main.py` | End-to-end pipeline runner with `--skip-fetch` and `--dry-run` flags |
| 7. Dashboard | `streamlit_app.py` | Interactive Streamlit dashboard with stat cards, theme charts, quotes, and rating breakdown |

## Dashboard Features

- **4 stat cards** — Reviews analyzed, themes identified, average rating, analysis window
- **Top 3 themes** — With progress bars, star ratings, and descriptions
- **Suggested actions** — Data-informed interventions for product sprint
- **User voices** — Verbatim quotes from Play Store reviews
- **Donut chart** — Review distribution across 5 theme clusters (Plotly)
- **Rating breakdown** — Star tier distribution with 1-star alert
- **Expandable pulse note** — Full generated pulse markdown

## Project Structure

```
├── streamlit_app.py           # Streamlit dashboard (deployed on Streamlit Cloud)
├── .streamlit/config.toml     # Streamlit theme config (Groww green #00D09C)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── src/
│   ├── config.py              # Central configuration
│   ├── review_collector.py    # Stage 1: Play Store scraper
│   ├── data_processor.py      # Stage 2: PII stripping & cleaning
│   ├── theme_clusterer.py     # Stage 3: LLM-based theme clustering
│   ├── pulse_generator.py     # Stage 4: Pulse note generation
│   ├── delivery.py            # Stage 5: MCP delivery (Google Docs + Gmail)
│   └── main.py                # Stage 6: Pipeline orchestrator
├── data_seed/                 # Seed data for dashboard (committed)
│   ├── themes.json            # 5 clustered themes with quotes
│   └── pulse.md               # Generated pulse note
├── data/                      # Runtime pipeline output (gitignored)
├── frontend/
│   └── index.html             # Static HTML dashboard (design reference)
├── Docs/
│   ├── implementation-plan.md # 7-phase implementation plan
│   ├── deployment-plan.md     # Streamlit Cloud deployment guide
│   └── architecture.md        # System architecture
└── stitch_weekly_app_review_pulse/  # Google Stitch design output
    ├── code.html
    ├── DESIGN.md
    └── screen.png
```

## Quick Start

### Prerequisites

- Python 3.9+
- [Groq API key](https://console.groq.com/) (free tier)

### Setup

```bash
# Clone the repo
git clone https://github.com/sana1410/Nextleap-Milestone3.git
cd Nextleap-Milestone3

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY, EMAIL_RECIPIENT, GOOGLE_DOC_ID
```

### Run the Pipeline

```bash
# Full pipeline (fetches reviews, clusters, generates pulse, delivers)
python src/main.py

# Use cached reviews (skip Play Store fetch)
python src/main.py --skip-fetch

# Dry run (preview delivery without sending)
python src/main.py --skip-fetch --dry-run
```

> **Note:** The clustering stage takes ~10 minutes due to Groq free-tier rate limits (65s between batches).

### Run the Dashboard Locally

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM clustering and pulse generation |
| `EMAIL_RECIPIENT` | Target email for pulse delivery via Gmail |
| `GOOGLE_DOC_ID` | Google Doc ID for pulse publishing |
| `MCP_SERVER_URL` | MCP server URL for Google Docs/Gmail integration |

## Deployment

The dashboard is deployed on **Streamlit Community Cloud** — auto-deploys on push to `master`.

See [`Docs/deployment-plan.md`](Docs/deployment-plan.md) for the full deployment guide.

### Refresh Dashboard Data

```bash
# Run the pipeline locally
python src/main.py --skip-fetch --dry-run

# Copy fresh output to seed directory
cp data/themes.json data_seed/themes.json
cp data/pulse.md data_seed/pulse.md

# Push — Streamlit auto-redeploys
git add data_seed/
git commit -m "Refresh seed data"
git push
```

## Tech Stack

- **Python 3.9+** — Core language
- **google-play-scraper** — Play Store review collection
- **Groq API** (Qwen 27B) — LLM for theme clustering and pulse generation
- **MCP** (Model Context Protocol) — Streamable HTTP transport for Google Docs/Gmail delivery
- **Streamlit** — Dashboard UI and deployment
- **Plotly** — Interactive donut chart for review distribution

## Sample Output

**5 Themes Identified:**

| Theme | Reviews | Avg Rating |
|-------|---------|------------|
| Feature Gaps & Trading Tools | 109 | 3.0 |
| UI/UX & Navigation Issues | 101 | 3.5 |
| Customer Support & Responsiveness | 72 | 1.6 |
| App Performance & Stability | 58 | 2.6 |
| Order Execution & Reliability | 40 | 1.5 |

**380 reviews** analyzed over a 10-week window (Aug 8 – Oct 16, 2026).
