# Problem Statement

## Overview

Build a **Weekly App Review Pulse** for the **Groww** platform ([Groww on Google Play](https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN)).

Turn raw mobile-store feedback into a weekly pulse your team can scan in minutes: what users care about, what they actually said, and what to do next. Reviews are already public; the job is to aggregate, theme, summarize, and deliver that insight through familiar surfaces — Google Docs for the written pulse and Gmail for a draft email.

---

## End-to-End Flow

1. **Pull** recent Play Store reviews for Groww (within the constraints below).
2. **Cluster** them into a small set of themes and distill a one-page weekly note.
3. **Publish** that note to Google Docs where stakeholders can read it.
4. **Draft** an email (to yourself or an alias) that contains or links to the pulse via Gmail.

---

## Deliverables

The weekly one-page pulse must include:

1. **Top themes** — what people are talking about most
2. **Real user quotes** — verbatim snippets from reviews (no invented wording)
3. **Three action ideas** — concrete next steps grounded in the themes

Finally: send a draft email containing this weekly note (or a clear pointer to it).

---

## Target Audience

| Audience | Why |
|---|---|
| **Product / Growth** | Prioritize fixes and improvements from real signals |
| **Support** | Align messaging with what users are actually saying |
| **Leadership** | One-page health check without drowning in raw reviews |

---

## What to Build

1. **Import reviews** from roughly the last 8–12 weeks (fields: rating, title, text, date, etc.).
2. **Group reviews** into at most **5 themes** (e.g., onboarding, KYC, payments, statements, withdrawals).
3. **Generate a weekly one-page note** with:
   - Top 3 themes (subset of the 5)
   - 3 user quotes
   - 3 action ideas
4. **Draft an email** with the note to yourself or an alias.

---

## Integrations: Google Docs & Gmail via MCP

Use **MCP (Model Context Protocol)** servers for Google Docs and Gmail — creating/updating the pulse document and creating the draft message — rather than integrating Google APIs directly. MCP servers expose tools the agent can call; this avoids duplicating auth and HTTP plumbing.

---

## Key Constraints

1. **Reviews** — Use public review exports only. No scraping behind store logins or ToS-violating automation.
2. **Themes** — Maximum 5 themes for clustering; the written pulse highlights the top 3.
3. **Length** — Keep the note scannable and ≤ 250 words.
4. **Privacy** — No PII (usernames, emails, device IDs, or other identifiable reviewer data). Quotes must be anonymous/stripped.
