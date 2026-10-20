# Architecture — Weekly App Review Pulse for Groww

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Orchestration Layer                         │
│                     (main pipeline / agent)                        │
└──────┬──────────────┬──────────────┬──────────────┬────────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐
│   Review   │ │  Analysis  │ │   Pulse    │ │     Delivery       │
│ Collection │ │  & Theming │ │ Generation │ │ (Docs + Gmail MCP) │
└────────────┘ └────────────┘ └────────────┘ └────────────────────┘
```

The system is a four-stage pipeline:

1. **Collect** — Fetch public Play Store reviews for Groww.
2. **Analyze** — Clean data, strip PII, cluster into ≤ 5 themes.
3. **Generate** — Produce a ≤ 250-word weekly pulse (top 3 themes, 3 quotes, 3 actions).
4. **Deliver** — Publish to Google Docs and create a Gmail draft via MCP.

---

## 2. High-Level Architecture Diagram

```
                         ┌──────────────┐
                         │  Play Store  │
                         │  (Public)    │
                         └──────┬───────┘
                                │  HTTP (public API / RSS)
                                ▼
                   ┌────────────────────────┐
                   │  1. Review Collector   │
                   │  ────────────────────  │
                   │  • google-play-scraper │
                   │  • Last 8–12 weeks     │
                   │  • Fields: rating,     │
                   │    text, date, etc.    │
                   └────────────┬───────────┘
                                │  Raw reviews (JSON / CSV)
                                ▼
                   ┌────────────────────────┐
                   │  2. Data Processor     │
                   │  ────────────────────  │
                   │  • PII stripping       │
                   │  • Deduplication       │
                   │  • Normalization       │
                   └────────────┬───────────┘
                                │  Cleaned reviews
                                ▼
                   ┌────────────────────────┐
                   │  3. Theme Clusterer    │
                   │  ────────────────────  │
                   │  • LLM-based grouping  │
                   │  • ≤ 5 themes          │
                   │  • Quote selection     │
                   └────────────┬───────────┘
                                │  Themed data + quotes
                                ▼
                   ┌────────────────────────┐
                   │  4. Pulse Generator    │
                   │  ────────────────────  │
                   │  • Top 3 themes        │
                   │  • 3 verbatim quotes   │
                   │  • 3 action ideas      │
                   │  • ≤ 250 words         │
                   └────────────┬───────────┘
                                │  Formatted pulse (Markdown)
                        ┌───────┴───────┐
                        ▼               ▼
              ┌──────────────┐  ┌──────────────┐
              │ Google Docs  │  │    Gmail     │
              │  (via MCP)   │  │  (via MCP)   │
              │              │  │              │
              │ Create/update│  │ Create draft │
              │ pulse doc    │  │ with pulse   │
              └──────────────┘  └──────────────┘
```

---

## 3. Component Details

### 3.1 Review Collector

| Aspect | Detail |
|---|---|
| **Purpose** | Fetch recent Groww reviews from the Play Store |
| **Input** | App ID (`com.nextbillion.groww`), date range (8–12 weeks) |
| **Output** | Raw review list (JSON) |
| **Library** | `google-play-scraper` (Python) |
| **Constraint** | Public data only — no authenticated scraping or ToS violation |

**Fields extracted per review:**
- `rating` (1–5 stars)
- `text` (review body)
- `date` (submission date)
- `thumbsUpCount` (helpfulness signal)
- `reviewCreatedVersion` (app version, if available)

**Storage:** Reviews are saved to `data/raw_reviews.json` for reproducibility and debugging.

---

### 3.2 Data Processor

| Aspect | Detail |
|---|---|
| **Purpose** | Clean and normalize raw reviews; strip PII |
| **Input** | Raw reviews JSON |
| **Output** | Cleaned reviews JSON |

**Processing steps:**

1. **PII Removal** — Strip usernames, emails, phone numbers, device IDs using regex patterns. Replace with `[REDACTED]` where needed.
2. **Deduplication** — Remove exact-duplicate review texts.
3. **Normalization** — Trim whitespace, normalize Unicode, filter out empty/non-English reviews.
4. **Date Filtering** — Keep only reviews from the target window (last 8–12 weeks).

**Storage:** Cleaned reviews saved to `data/cleaned_reviews.json`.

---

### 3.3 Theme Clusterer

| Aspect | Detail |
|---|---|
| **Purpose** | Group reviews into ≤ 5 themes and select representative quotes |
| **Input** | Cleaned reviews |
| **Output** | Theme assignments, theme summaries, candidate quotes |
| **Method** | LLM-based clustering via Claude API |

**Approach:**

The clusterer sends batches of cleaned reviews to Claude with a structured prompt that asks the model to:

1. Identify up to 5 recurring themes across the reviews.
2. Assign each review to its best-fitting theme.
3. Rank themes by volume (number of reviews).
4. Select 3–5 candidate verbatim quotes per theme (anonymous, no PII).

**Why LLM-based clustering over traditional NLP (TF-IDF, BERTopic, etc.):**
- Review volume is moderate (hundreds, not millions) — LLM cost is acceptable.
- LLM produces human-readable theme labels directly (e.g., "KYC Verification Delays") rather than keyword clusters that need manual labeling.
- Single tool does clustering + labeling + quote extraction in one pass.

**Theme examples** (Groww-specific):
- App Performance & Crashes
- KYC / Account Verification
- Payments & Withdrawals
- UI / UX Feedback
- Customer Support

**Storage:** Theme data saved to `data/themes.json`.

---

### 3.4 Pulse Generator

| Aspect | Detail |
|---|---|
| **Purpose** | Produce the final weekly pulse document |
| **Input** | Theme data with ranked themes and quotes |
| **Output** | Formatted pulse text (≤ 250 words) |
| **Method** | LLM generation via Claude API with structured prompt |

**Pulse structure:**

```
Weekly App Review Pulse — Groww
Week of [date range]
Reviews analyzed: [count]

## Top Themes This Week

1. [Theme Name] ([count] reviews, [avg rating]★)
   Summary of what users are saying.

2. [Theme Name] ([count] reviews, [avg rating]★)
   Summary of what users are saying.

3. [Theme Name] ([count] reviews, [avg rating]★)
   Summary of what users are saying.

## What Users Are Saying

> "[Verbatim quote 1]" — [rating]★

> "[Verbatim quote 2]" — [rating]★

> "[Verbatim quote 3]" — [rating]★

## Recommended Actions

1. [Action idea grounded in theme data]
2. [Action idea grounded in theme data]
3. [Action idea grounded in theme data]
```

---

### 3.5 Delivery Layer (MCP Integrations)

#### Google Docs (via MCP)

| Aspect | Detail |
|---|---|
| **Purpose** | Create or update the pulse document for stakeholder access |
| **MCP Server** | Google Docs MCP server (or Google Drive MCP) |
| **Operations** | `create_document` / `update_document` |

**Flow:**
1. Check if a pulse document already exists for the current week.
2. If yes → update the existing document with new content.
3. If no → create a new document titled "Groww Weekly Pulse — [Date]".
4. Return the document URL for linking in the email.

#### Gmail (via MCP)

| Aspect | Detail |
|---|---|
| **Purpose** | Create a draft email containing or linking to the pulse |
| **MCP Server** | Gmail MCP server |
| **Operations** | `create_draft` |

**Draft email structure:**
- **To:** Self (or configured alias)
- **Subject:** "Groww Weekly Pulse — Week of [date]"
- **Body:** Full pulse text + link to Google Docs version

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.11+ | Rich ecosystem for data processing and API integration |
| **Review Fetching** | `google-play-scraper` | Public Play Store data, no auth required |
| **LLM** | Claude API (Anthropic) | Theme clustering + pulse generation |
| **MCP Client** | MCP Python SDK | Communicate with Docs and Gmail MCP servers |
| **Data Format** | JSON | Simple, human-readable, easy to debug |
| **Config** | `.env` + `config.py` | API keys, app ID, date ranges, email alias |

---

## 5. Project Structure

```
Milestone3/
├── Docs/
│   ├── ProblemStatement.txt
│   ├── problemStatement.md
│   └── architecture.md            ← this file
├── src/
│   ├── main.py                    ← pipeline orchestrator
│   ├── review_collector.py        ← Stage 1: fetch reviews
│   ├── data_processor.py          ← Stage 2: clean + PII strip
│   ├── theme_clusterer.py         ← Stage 3: LLM clustering
│   ├── pulse_generator.py         ← Stage 4: generate pulse
│   ├── delivery.py                ← Stage 5: Docs + Gmail via MCP
│   └── config.py                  ← configuration and constants
├── data/
│   ├── raw_reviews.json           ← fetched reviews (gitignored)
│   ├── cleaned_reviews.json       ← processed reviews
│   └── themes.json                ← clustered themes
├── .env                           ← API keys (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 6. Data Flow

```
Play Store API
      │
      ▼
raw_reviews.json ──▶ data_processor ──▶ cleaned_reviews.json
                                              │
                                              ▼
                                     theme_clusterer (Claude API)
                                              │
                                              ▼
                                        themes.json
                                              │
                                              ▼
                                     pulse_generator (Claude API)
                                              │
                                              ▼
                                      Formatted Pulse Text
                                         │          │
                                         ▼          ▼
                                   Google Docs    Gmail Draft
                                    (MCP)          (MCP)
```

---

## 7. Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| **Clustering method** | LLM-based (not TF-IDF / BERTopic) | Moderate volume; produces labeled themes directly without manual post-processing |
| **Integration pattern** | MCP-first | Course requirement; avoids bespoke OAuth + REST plumbing |
| **Data storage** | Local JSON files | Simple for a batch pipeline; no database needed |
| **Pipeline style** | Sequential batch | Reviews are fetched once, processed once, delivered once per run — no streaming needed |
| **PII handling** | Regex strip + LLM instruction | Defense in depth: regex catches patterns, LLM prompt reinforces "no PII in output" |

---

## 8. Error Handling

| Stage | Failure Mode | Mitigation |
|---|---|---|
| Review Collection | Play Store rate limit / network error | Retry with exponential backoff; fall back to cached `raw_reviews.json` |
| Data Processing | Malformed review data | Skip malformed entries; log warnings |
| Theme Clustering | LLM API error / timeout | Retry up to 3 times; fail gracefully with error message |
| Pulse Generation | LLM produces > 250 words | Post-processing word count check; re-prompt if exceeded |
| Google Docs MCP | Auth failure / server down | Log error; save pulse locally as fallback (`data/pulse_fallback.md`) |
| Gmail MCP | Auth failure / server down | Log error; print pulse to console as fallback |

---

## 9. Privacy & Compliance

- **No PII in any output** — usernames, emails, phone numbers, device IDs stripped at Stage 2.
- **Public data only** — `google-play-scraper` accesses the same data any user sees on the Play Store.
- **No stored credentials** — API keys live in `.env` (gitignored); MCP handles OAuth for Google services.
- **Quotes are anonymous** — reviewer identity is never included in the pulse.

---

## 10. Configuration

```python
# config.py
APP_ID = "com.nextbillion.groww"
REVIEW_LANGUAGE = "en"
REVIEW_COUNTRY = "in"
REVIEW_WINDOW_WEEKS = 10          # 8–12 week range
MAX_THEMES = 5
TOP_THEMES_IN_PULSE = 3
NUM_QUOTES = 3
NUM_ACTIONS = 3
PULSE_MAX_WORDS = 250
EMAIL_RECIPIENT = "self"          # or configured alias
```

---

## 11. Future Considerations

- **Scheduling** — Automate weekly runs via cron or a task scheduler.
- **Historical tracking** — Store past pulses to show trend over time.
- **Multi-platform** — Extend to Apple App Store reviews.
- **Slack delivery** — Add a Slack MCP integration for real-time team notifications.
- **Dashboard** — Build a lightweight dashboard over stored theme data for visual trend analysis.
