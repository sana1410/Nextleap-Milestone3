# Implementation Plan — Weekly App Review Pulse for Groww

## Phase Overview

| Phase | Focus | Key Output | Depends On |
|---|---|---|---|
| **Phase 1** | Project Setup & Configuration | Scaffolded repo, dependencies installed, config ready | — |
| **Phase 2** | Review Collection | `review_collector.py` fetching live Play Store reviews | Phase 1 |
| **Phase 3** | Data Processing & PII Stripping | `data_processor.py` producing clean, safe review data | Phase 2 |
| **Phase 4** | Theme Clustering (LLM) | `theme_clusterer.py` grouping reviews into ≤ 5 themes | Phase 3 |
| **Phase 5** | Pulse Generation (LLM) | `pulse_generator.py` producing the ≤ 250-word weekly note | Phase 4 |
| **Phase 6** | MCP Integration (Google Docs & Gmail) | `delivery.py` publishing to Docs and drafting in Gmail | Phase 5 |
| **Phase 7** | Pipeline Orchestration & End-to-End Testing | `main.py` wiring all stages; full pipeline runs cleanly | Phases 2–6 |

---

## Phase 1 — Project Setup & Configuration

**Goal:** A working project skeleton with all dependencies, config, and directory structure in place.

### Tasks

1. **Initialize project directory structure**
   ```
   Milestone3/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── review_collector.py
   │   ├── data_processor.py
   │   ├── theme_clusterer.py
   │   ├── pulse_generator.py
   │   ├── delivery.py
   │   └── config.py
   ├── data/                   ← runtime output (gitignored)
   ├── Docs/
   ├── .env.example
   ├── .gitignore
   └── requirements.txt
   ```

2. **Create `requirements.txt`**
   ```
   google-play-scraper
   groq
   python-dotenv
   ```

3. **Create `.env.example`** (template — no real keys)
   ```
   GROQ_API_KEY=your_key_here
   EMAIL_RECIPIENT=your_email_here
   ```

4. **Create `.gitignore`**
   - `.env`, `data/`, `__pycache__/`, `*.pyc`

5. **Create `src/config.py`** with all constants
   - `APP_ID`, `REVIEW_WINDOW_WEEKS`, `MAX_THEMES`, `TOP_THEMES_IN_PULSE`, `NUM_QUOTES`, `NUM_ACTIONS`, `PULSE_MAX_WORDS`

6. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Exit Criteria
- `python -c "import google_play_scraper; import groq"` succeeds.
- Directory structure matches the architecture doc.

---

## Phase 2 — Review Collection

**Goal:** Fetch 8–12 weeks of public Groww reviews from the Play Store and persist them locally.

### Tasks

1. **Implement `src/review_collector.py`**
   - Function: `fetch_reviews(app_id, count) -> list[dict]`
   - Use `google_play_scraper.reviews()` with `sort=Sort.NEWEST`.
   - Fetch in batches (the library paginates via a continuation token).
   - Filter to reviews within the configured date window.
   - Extract fields: `rating`, `text`, `date`, `thumbsUpCount`, `reviewCreatedVersion`.

2. **Save raw output**
   - Write results to `data/raw_reviews.json` with `json.dump`.
   - Include metadata: fetch timestamp, app ID, review count.

3. **Add basic error handling**
   - Retry on network errors (up to 3 attempts with backoff).
   - Log how many reviews were fetched vs. how many fell within the date window.

4. **Manual verification**
   - Run the collector standalone.
   - Spot-check 5–10 reviews against the Play Store listing for accuracy.

### Exit Criteria
- `data/raw_reviews.json` contains 100+ reviews with correct fields.
- Reviews span the last ~10 weeks.

---

## Phase 3 — Data Processing & PII Stripping

**Goal:** Clean raw reviews and guarantee no PII appears in downstream outputs.

### Tasks

1. **Implement `src/data_processor.py`**
   - Function: `process_reviews(raw_reviews) -> list[dict]`

2. **PII removal** — Build regex patterns for:
   - Email addresses (`\b[\w.-]+@[\w.-]+\.\w+\b`)
   - Phone numbers (Indian formats: `+91`, 10-digit)
   - Usernames / handles (`@username`)
   - Device IDs, UPI IDs, account numbers
   - Replace matches with `[REDACTED]`.

3. **Deduplication**
   - Remove reviews with identical `text` content (keep the most recent).

4. **Normalization**
   - Strip leading/trailing whitespace.
   - Normalize Unicode (NFC).
   - Filter out empty reviews or reviews with only emojis / non-text content.
   - Filter out non-English reviews (simple heuristic: check for ASCII letter ratio).

5. **Date filtering**
   - Enforce the configured window (e.g., last 10 weeks from today).

6. **Save cleaned output**
   - Write to `data/cleaned_reviews.json`.

7. **Verification**
   - Grep cleaned output for common PII patterns — should find zero matches.
   - Compare count: raw vs. cleaned (log how many were dropped and why).

### Exit Criteria
- `data/cleaned_reviews.json` exists with no PII.
- Count delta from raw to cleaned is logged and reasonable (< 30% drop).

---

## Phase 4 — Theme Clustering

**Goal:** Group cleaned reviews into ≤ 5 meaningful themes using the Groq API (`qwen/qwen3.8-27b`, free tier), with ranked themes and candidate quotes.

### Input Data Profile (from `cleaned_reviews.json`)

| Metric | Value |
|---|---|
| **Total reviews** | 380 |
| **Date range** | 2026-08-08 to 2026-10-16 (~10 weeks) |
| **Rating split** | 1-star: 174 (45.8%), 2-star: 25 (6.6%), 3-star: 44 (11.6%), 4-star: 30 (7.9%), 5-star: 107 (28.2%) |
| **Word count** | Min 9, Max 110, Avg 40.9, Median 36 |
| **Engagement** | 273 reviews have thumbsUp > 0; max thumbsUp = 958 |

### Keyword Signals (guide theme labels)

Top keywords from the cleaned corpus suggest these natural clustering directions:

| Keyword cluster | Frequency | Likely theme |
|---|---|---|
| `customer`, `support`, `please`, `issue` | 80, 70, 51, 44 | Customer Support & Responsiveness |
| `trading`, `chart`, `option` | 71, 64, 48 | Trading Experience & Charts |
| `charges`, `account` | 54, 45 | Fees, Charges & Account Issues |
| `update`, `time`, `easy`, `good` | 48, 60, 50, 57 | App Performance & Usability |
| `groww` (general mentions) | 137 | General Sentiment (split across themes) |

**Note:** Final theme labels will be determined by the LLM clustering — these keywords inform prompt design, not hard-code the output.

### Tasks

1. **Implement `src/theme_clusterer.py`**
   - Function: `cluster_reviews(reviews) -> dict`
   - Returns: `{ themes: [...] }` with counts, avg_rating, quotes, and review_indices per theme.

2. **2-phase batched clustering (Groq free-tier 8K TPM constraint)**

   **Phase A — Theme Discovery** (single request, ~4K tokens):
   - Send top 30 reviews (by thumbsUpCount) to the LLM.
   - System prompt: app review analyst for Groww, a fintech platform (stocks, mutual funds, IPOs).
   - Ask for up to 5 theme labels + one-sentence descriptions.
   - Groq JSON mode (`response_format: json_object`) ensures structured output.

   **Phase B — Batch Classification** (10 batches of 40 reviews, ~2K tokens each):
   - For each batch, send the 5 pre-defined theme labels + batch reviews.
   - Compact output: model returns a JSON map of review index to theme index (e.g., `{"0":2,"1":0,...}`).
   - 65-second delay between batches to respect the 8K TPM rate limit.
   - Total classification time: ~10 minutes.

   **Phase C — Quote Collection** (5 requests, one per theme):
   - For each theme, send its top 15 reviews (by thumbsUpCount) and ask for 3 verbatim quotes.
   - Verify each quote is an exact substring of the source review.

   **Phase D — Local Aggregation** (no API call):
   - Merge all batch assignments into global theme data.
   - Compute counts, avg_rating, attach verified quotes.
   - Rank themes by review count.

3. **Parse and validate LLM output**
   - Parse JSON response per batch.
   - Validate: ≤ 5 themes, each theme has label + description + count + avg_rating + quotes.
   - Verify quotes are verbatim substrings of the cleaned reviews.
   - Retry on malformed output with rate-limit-aware backoff.

5. **Save theme data**
   - Write to `data/themes.json`.

6. **Verification**
   - Confirm ≤ 5 themes.
   - Confirm quotes are verbatim substrings of `cleaned_reviews.json`.
   - Confirm every review is assigned to exactly one theme.
   - Confirm theme counts sum to 380.

### Exit Criteria
- `data/themes.json` has 3–5 themes, each with label, description, count, avg_rating, and quotes.
- Themes plausibly reflect the keyword signals (customer support, trading/charts, charges, app usability, etc.).
- Theme counts sum to 380; all quotes verified against source.

---

## Phase 5 — Pulse Generation

**Goal:** Produce a polished, ≤ 250-word weekly pulse from theme data.

### Tasks

1. **Implement `src/pulse_generator.py`**
   - Function: `generate_pulse(themes, review_count, date_range) -> str`
   - Returns formatted Markdown text.

2. **Design the generation prompt**
   - Input: the top 3 themes (by volume), their descriptions, their candidate quotes, total review count, date range.
   - Instructions:
     - Write a weekly pulse titled "Weekly App Review Pulse — Groww".
     - Include: date range, total reviews analyzed.
     - Section 1: Top 3 themes — name, review count, average rating, one-sentence summary.
     - Section 2: 3 verbatim user quotes (one per theme, with star rating).
     - Section 3: 3 concrete action ideas (each tied to a theme).
     - Hard limit: ≤ 250 words.
     - Tone: professional, scannable, no jargon.

3. **Post-processing**
   - Count words in the output. If > 250, re-prompt with a stricter instruction.
   - Validate that quotes appear verbatim in the theme data (no hallucinated quotes).

4. **Save pulse locally**
   - Write to `data/pulse.md` as a fallback / debug artifact.

5. **Verification**
   - Word count ≤ 250.
   - Contains exactly 3 themes, 3 quotes, 3 actions.
   - Quotes match source data.

### Exit Criteria
- `data/pulse.md` is a scannable, well-formatted pulse under 250 words.
- No invented quotes; all are traceable to `cleaned_reviews.json`.

---

## Phase 6 — MCP Integration (Google Docs & Gmail)

**Goal:** Deliver the pulse to a Google Doc and send it via Gmail, using the `mcp-gmail-gdocs` MCP server (`github.com/sana1410/mcp-gmail-gdocs`).

### MCP Server Tools Available

The MCP server exposes three tools:

| Tool | Purpose | Key Parameters |
|---|---|---|
| **`auth_status`** | Check Google OAuth status, connected account, granted scopes | — |
| **`gdocs_append_text`** | Append text to an **existing** Google Doc (append-only, never deletes) | `document_id` (ID or URL), `text`, `add_heading`, `add_timestamp`, `separator`, `dry_run`, `idempotency_key` |
| **`gmail_send_email`** | Send an email from the authenticated Gmail account | `to` (string[]), `subject`, `body`, `body_format` ("plain"/"html"), `cc`, `bcc`, `reply_to`, `dry_run` (default **true**), `idempotency_key` |

**Important constraints:**
- `gdocs_append_text` is **append-only** — it cannot create a new doc or overwrite existing content. A blank Google Doc must be **pre-created manually** and its document ID configured.
- `gmail_send_email` defaults to `dry_run: true` — set `dry_run: false` to actually send.

### Prerequisites

1. **Clone and build the MCP server**
   ```bash
   git clone https://github.com/sana1410/mcp-gmail-gdocs.git
   cd mcp-gmail-gdocs
   npm install && npm run build
   ```

2. **Configure Google Cloud credentials**
   - Follow `docs/GOOGLE_CLOUD_SETUP.md` in the repo.
   - Enable Gmail API and Google Docs API in the Google Cloud project.
   - Create OAuth 2.0 client credentials (Desktop app type).
   - Copy `.env.example` to `.env`, fill in `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

3. **Authorize Google account**
   ```bash
   npm run auth
   ```
   Opens a browser for Google consent; tokens are saved locally after approval.

4. **Register as MCP server in Claude Code**
   ```bash
   claude mcp add gmail-gdocs -- node /path/to/mcp-gmail-gdocs/dist/index.js
   ```
   Or add to `.claude/settings.json`:
   ```json
   {
     "mcpServers": {
       "gmail-gdocs": {
         "command": "node",
         "args": ["/path/to/mcp-gmail-gdocs/dist/index.js"],
         "env": {
           "GOOGLE_CLIENT_ID": "<your-client-id>",
           "GOOGLE_CLIENT_SECRET": "<your-client-secret>"
         }
       }
     }
   }
   ```

5. **Pre-create a Google Doc** for the pulse
   - Create a blank Google Doc (manually or via Google Drive).
   - Note its document ID (the long string in the URL: `docs.google.com/document/d/<DOCUMENT_ID>/edit`).
   - Add `GOOGLE_DOC_ID=<DOCUMENT_ID>` to the project `.env` file.

### Tasks

1. **Verify MCP server connectivity**
   - Call `auth_status` to confirm the Google account is authorized and both Gmail + Docs scopes are granted.

2. **Implement `src/delivery.py`**

   **Google Docs delivery:**
   - Function: `publish_to_docs(pulse_text, title) -> str` (returns doc URL)
   - Use the MCP tool `gdocs_append_text` with:
     - `document_id`: from `GOOGLE_DOC_ID` env var.
     - `add_heading`: `"Groww Weekly Pulse — Week of [date]"` (creates a heading before the content).
     - `text`: the full pulse Markdown content.
     - `add_timestamp`: `true` (prefixes with date/time for auditability).
     - `separator`: `"horizontal_rule"` (visually separates from any prior content).
   - Return the doc URL: `https://docs.google.com/document/d/{doc_id}/edit`.

   **Gmail delivery:**
   - Function: `send_pulse_email(pulse_text, doc_url, recipient) -> dict`
   - Use the MCP tool `gmail_send_email` with:
     - `to`: `[recipient]` (from `EMAIL_RECIPIENT` config).
     - `subject`: `"Groww Weekly Pulse — Week of [date]"`.
     - `body`: Full pulse text + `"\n\nView in Google Docs: {doc_url}"`.
     - `body_format`: `"plain"`.
     - `dry_run`: `false` to actually send (after confirming via a dry-run preview first).

3. **Fallback handling**
   - If Docs MCP fails → save pulse to `data/pulse_fallback.md`, log the error, continue to Gmail step.
   - If Gmail MCP fails → log the error, print the pulse to console as final fallback.
   - Both MCP calls wrapped in try/except with descriptive error messages.

4. **Verification**
   - Call `auth_status` and confirm scopes include `gmail.send` and `docs`.
   - Run `gdocs_append_text` with `dry_run: true` to preview the doc append.
   - Run `gmail_send_email` with `dry_run: true` to preview the email.
   - Then run both with `dry_run: false` to confirm actual delivery.
   - Verify the Google Doc has the pulse appended (open the doc URL).
   - Verify the email was received by the recipient.

### Exit Criteria
- The pulse text is appended to the configured Google Doc with heading and timestamp.
- An email with the pulse (and doc link) is sent to the configured recipient.
- Fallback to `data/pulse_fallback.md` works when MCP is unavailable.

---

## Phase 7 — Pipeline Orchestration & End-to-End Testing

**Goal:** Wire all stages into a single `main.py` entry point and validate the full pipeline end to end.

### Tasks

1. **Implement `src/main.py`**
   ```python
   def run_pipeline(skip_fetch=False, dry_run=False):
       # Stage 1: Collect
       raw_reviews = load_reviews() if skip_fetch else fetch_reviews()
       save_reviews(raw_reviews)
       
       # Stage 2: Process
       cleaned, stats = process_reviews(raw_reviews)
       save_cleaned(cleaned, stats)
       
       # Stage 3: Cluster
       themes_data = cluster_reviews(cleaned)
       save_themes(themes_data)
       
       # Stage 4: Generate
       date_range = get_date_range()
       pulse = generate_pulse(themes_data, len(cleaned), date_range)
       save_pulse(pulse)
       
       # Stage 5: Deliver
       doc_url = deliver_pulse(pulse, dry_run=dry_run)
       
       print(f"Done. Doc: {doc_url}")
   ```

2. **Add CLI interface**
   - `python src/main.py` runs the full pipeline.
   - Optional flags: `--skip-fetch` (use cached reviews), `--dry-run` (skip delivery).

3. **End-to-end test run**
   - Run the full pipeline from scratch.
   - Verify each intermediate file is produced: `raw_reviews.json`, `cleaned_reviews.json`, `themes.json`, `pulse.md`.
   - Verify Google Doc is appended and Gmail email is sent (or previewed via dry-run).

4. **Logging**
   - Add summary log at each stage: review count, theme count, word count, delivery status.
   - Print a final summary to console.

5. **Edge cases to test**
   - Very few reviews (< 10) — should still produce a pulse.
   - All reviews are 5-star — themes should still emerge.
   - MCP server down — fallback behavior activates.
   - LLM returns malformed JSON — retry logic triggers.

### Exit Criteria
- `python src/main.py` runs end to end with no errors.
- Google Doc appended, Gmail email sent (or dry-run previewed), console summary printed.
- All intermediate JSON files are valid and consistent.

---

## Phase Summary Timeline

```
Phase 1 ─── Project Setup ──────────────────── [~30 min]
    │
Phase 2 ─── Review Collection ──────────────── [~1 hr]
    │
Phase 3 ─── Data Processing & PII ──────────── [~1 hr]
    │
Phase 4 ─── Theme Clustering (LLM) ─────────── [~2 hr]
    │
Phase 5 ─── Pulse Generation (LLM) ─────────── [~1.5 hr]
    │
Phase 6 ─── MCP Integration (Docs + Gmail) ─── [~2 hr]
    │
Phase 7 ─── Orchestration & E2E Testing ────── [~1.5 hr]
                                          Total: ~9.5 hr
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `google-play-scraper` blocked by Google | Medium | High | Cache reviews locally; switch to RSS/public export if needed |
| Groq API rate limit during clustering | Low | Medium | Retry with backoff; Groq free tier has generous limits for Llama 3.3 70B |
| MCP server auth issues | Medium | Medium | Test auth early in Phase 6; fallback to local file output |
| Reviews too few for meaningful themes | Low | Low | Reduce theme count dynamically; note low confidence in pulse |
| LLM hallucinates quotes | Medium | High | Validate every quote against source data; reject and re-prompt |
| Pulse exceeds 250 words | Medium | Low | Word count check + re-prompt with stricter limit |

---

## Dependencies & Prerequisites

- **Python 3.11+** installed
- **Groq API key** (for Qwen 3.8 27B calls in Phases 4–5, free tier)
- **Google account** authorized with MCP servers for Docs and Gmail (Phase 6)
- **Network access** to Play Store (Phase 2) and Groq API (Phases 4–5)
