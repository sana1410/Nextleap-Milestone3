import json
import os
import time
from datetime import datetime, timezone

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    CLEANED_REVIEWS_PATH,
    TOP_THEMES_IN_PULSE,
    NUM_QUOTES,
    NUM_ACTIONS,
    PULSE_MAX_WORDS,
    PULSE_PATH,
    THEMES_PATH,
)

RATE_LIMIT_DELAY = 65

SYSTEM_PROMPT = f"""You are a product insights analyst writing a concise weekly pulse for the Groww app team.

Write a weekly pulse in Markdown with EXACTLY this structure:

# Weekly App Review Pulse — Groww

**Period:** [date range] | **Reviews analyzed:** [count]

## Top Themes

For each of the {TOP_THEMES_IN_PULSE} themes provided, write ONE line:
- **Theme Name** ([count] reviews, avg [rating]★) — one-sentence summary

## User Voices

Pick exactly {NUM_QUOTES} quotes (one per theme) from the candidate quotes provided. PREFER SHORTER quotes (under 30 words) to stay within the word limit. Copy them EXACTLY — do not edit, shorten, or paraphrase. Format each as:
> "[exact quote]" — ★[rating]

## Suggested Actions

List exactly {NUM_ACTIONS} concrete, actionable ideas, one tied to each theme. Keep each to one sentence.

Rules:
- STRICT hard limit: ≤ {PULSE_MAX_WORDS} words total. Count every word including quotes. Budget ~80 words for themes, ~60 for quotes, ~50 for actions, ~30 for header. Choose shorter quotes to fit.
- Tone: professional, scannable, no jargon.
- Do NOT invent quotes. Use ONLY quotes from the provided candidates.
- Do NOT add any sections beyond the four above."""


def build_pulse_prompt(themes_data, review_count, date_range):
    top_themes = themes_data["themes"][:TOP_THEMES_IN_PULSE]
    lines = [
        f"Total reviews: {review_count}",
        f"Date range: {date_range}",
        "",
        "Top 3 themes (by volume):",
    ]
    for t in top_themes:
        lines.append(f"\nTheme: {t['label']}")
        lines.append(f"  Count: {t['count']} reviews")
        lines.append(f"  Avg rating: {t['avg_rating']}★")
        lines.append(f"  Description: {t['description']}")
        lines.append(f"  Candidate quotes:")
        for q in t.get("quotes", []):
            lines.append(f'    - "{q["text"]}" (★{q["rating"]}, {q.get("thumbsUpCount", 0)} thumbsUp)')
    return "\n".join(lines)


def call_groq_text(client, system_prompt, user_prompt, max_tokens=2000, retries=2):
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()
            tokens_used = response.usage.prompt_tokens + response.usage.completion_tokens
            return text, tokens_used
        except Exception as e:
            print(f"  Error (attempt {attempt + 1}): {str(e)[:150]}")
            if attempt < retries:
                time.sleep(RATE_LIMIT_DELAY)
                continue
            raise
    return "", 0


def count_words(text):
    return len(text.split())


def validate_pulse(pulse_text, themes_data, cleaned_path=CLEANED_REVIEWS_PATH):
    issues = []
    word_count = count_words(pulse_text)
    if word_count > PULSE_MAX_WORDS:
        issues.append(f"Word count {word_count} exceeds limit of {PULSE_MAX_WORDS}")

    with open(cleaned_path, "r", encoding="utf-8") as f:
        cleaned_data = json.load(f)
    reviews = cleaned_data["reviews"]

    import re
    quoted = re.findall(r'> "(.+?)"', pulse_text)
    verified = 0
    for q in quoted:
        q_clean = q.rstrip(".")
        if any(q_clean in r["text"] for r in reviews):
            verified += 1
        else:
            issues.append(f"Quote not traceable to reviews: \"{q[:60]}...\"")

    if len(quoted) < NUM_QUOTES:
        issues.append(f"Only {len(quoted)} quotes found in pulse (expected {NUM_QUOTES})")
    elif verified < len(quoted):
        issues.append(f"{len(quoted) - verified} quotes not verbatim from cleaned reviews")

    return issues


def get_date_range(cleaned_path=CLEANED_REVIEWS_PATH):
    with open(cleaned_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    reviews = data["reviews"]
    dates = [r["date"] for r in reviews if r.get("date")]
    if not dates:
        return "Unknown"
    dates.sort()
    earliest = dates[0][:10]
    latest = dates[-1][:10]
    return f"{earliest} to {latest}"


def generate_pulse(themes_data, review_count, date_range):
    client = Groq(api_key=GROQ_API_KEY)

    print(f"Generating pulse for {review_count} reviews ({date_range})...")
    print(f"Using model: {GROQ_MODEL}")
    print(f"Top {TOP_THEMES_IN_PULSE} themes, {NUM_QUOTES} quotes, {NUM_ACTIONS} actions, ≤{PULSE_MAX_WORDS} words")

    user_prompt = build_pulse_prompt(themes_data, review_count, date_range)

    pulse_text, tokens = call_groq_text(client, SYSTEM_PROMPT, user_prompt, max_tokens=1500)
    word_count = count_words(pulse_text)
    print(f"  Generated: {word_count} words ({tokens} tokens)")

    if word_count > PULSE_MAX_WORDS:
        print(f"  Over limit ({word_count} > {PULSE_MAX_WORDS}), re-prompting...")
        time.sleep(RATE_LIMIT_DELAY)
        stricter_prompt = (
            user_prompt + f"\n\nIMPORTANT: Your previous attempt was {word_count} words. "
            f"You MUST stay under {PULSE_MAX_WORDS} words. Be more concise."
        )
        pulse_text, tokens = call_groq_text(client, SYSTEM_PROMPT, stricter_prompt, max_tokens=1200)
        word_count = count_words(pulse_text)
        print(f"  Retry: {word_count} words ({tokens} tokens)")

    issues = validate_pulse(pulse_text, themes_data)
    if issues:
        print(f"  Validation issues:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"  Validation: OK")

    return pulse_text


def save_pulse(pulse_text, path=PULSE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pulse_text)
    print(f"Saved pulse to {path} ({count_words(pulse_text)} words)")


def load_pulse(path=PULSE_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        themes_data = json.load(f)

    review_count = themes_data["metadata"]["review_count"]
    date_range = get_date_range()

    print(f"Loaded {len(themes_data['themes'])} themes, {review_count} reviews")

    pulse_text = generate_pulse(themes_data, review_count, date_range)
    save_pulse(pulse_text)

    print(f"\n{'='*60}")
    print(pulse_text)
    print(f"{'='*60}")
