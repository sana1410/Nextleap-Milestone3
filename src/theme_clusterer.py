import json
import os
import time
from datetime import datetime, timezone

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    CLEANED_REVIEWS_PATH,
    MAX_THEMES,
    NUM_QUOTES,
    THEMES_PATH,
)

DISCOVERY_SYSTEM_PROMPT = f"""You are an expert app review analyst for Groww, a leading Indian fintech platform for stocks, mutual funds, and IPOs.

Analyze these representative user reviews and identify up to {MAX_THEMES} recurring themes.

Rules:
- Identify up to {MAX_THEMES} themes. Use short, descriptive labels (e.g., "Customer Support & Responsiveness").
- Provide a one-sentence description for each theme.
- Rank themes by how frequently they appear in the sample.

Respond with ONLY valid JSON:
{{
  "themes": [
    {{"label": "Theme Name", "description": "One sentence describing this theme."}},
    ...
  ]
}}"""

BATCH_SIZE = 40
RATE_LIMIT_DELAY = 65


def build_discovery_prompt(reviews):
    top_reviews = sorted(reviews, key=lambda r: r.get("thumbsUpCount", 0), reverse=True)[:30]
    lines = []
    for i, r in enumerate(top_reviews):
        lines.append(f"[{i}] ({r['rating']}*, {r.get('thumbsUpCount', 0)}up) {r['text']}")
    return "Identify recurring themes from these reviews:\n\n" + "\n".join(lines)


def build_classify_prompt(batch, theme_labels):
    labels_str = ", ".join(f'{i}="{l}"' for i, l in enumerate(theme_labels))
    lines = []
    for i, r in enumerate(batch):
        lines.append(f"[{i}] ({r['rating']}*) {r['text'][:150]}")
    return (
        f"Themes: {labels_str}\n\n"
        f"For each review, respond with ONLY a JSON object mapping review index to theme index.\n"
        f"Example: {{\"0\":2,\"1\":0,\"2\":3}}\n\n"
        + "\n".join(lines)
    )


CLASSIFY_SYSTEM = "Classify each review into exactly one theme. Respond with ONLY a JSON object mapping review index (string) to theme index (integer). Nothing else."


def build_quotes_prompt(theme_reviews, theme_label):
    lines = []
    for i, r in enumerate(theme_reviews[:15]):
        lines.append(f"[{i}] ({r['rating']}*, {r.get('thumbsUpCount', 0)}up) {r['text']}")
    return (
        f'Theme: "{theme_label}"\n\n'
        f"Select the {NUM_QUOTES} best verbatim quotes from these reviews that represent this theme.\n"
        f"Quotes must be EXACT substrings from the review text. Prefer articulate reviews with high thumbsUp.\n\n"
        + "\n".join(lines)
    )


QUOTES_SYSTEM = f"Select {NUM_QUOTES} representative verbatim quotes. Respond with ONLY valid JSON: {{\"quotes\": [{{\"index\": 0, \"text\": \"exact quote\"}}]}}"


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return text[start:end]
    return text


def call_groq(client, system_prompt, user_prompt, max_tokens=2000, retries=2, json_mode=True):
    for attempt in range(retries + 1):
        try:
            kwargs = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**kwargs)
            raw_text = response.choices[0].message.content
            json_str = extract_json(raw_text)
            data = json.loads(json_str)
            tokens_used = response.usage.prompt_tokens + response.usage.completion_tokens
            return data, tokens_used
        except json.JSONDecodeError as e:
            print(f"    JSON parse error (attempt {attempt + 1}): {e}")
            if attempt < retries:
                time.sleep(RATE_LIMIT_DELAY)
                continue
            raise
        except Exception as e:
            err_str = str(e)
            if "json_validate_failed" in err_str:
                if json_mode and attempt == 0:
                    print(f"    JSON mode failed, retrying without it...")
                    json_mode = False
                    time.sleep(RATE_LIMIT_DELAY)
                    continue
            print(f"    Error (attempt {attempt + 1}): {err_str[:150]}")
            if attempt < retries:
                time.sleep(RATE_LIMIT_DELAY)
                continue
            raise
    return None, 0


def discover_themes(client, reviews):
    print("Phase 1: Discovering themes from top 30 reviews...")
    prompt = build_discovery_prompt(reviews)
    data, tokens = call_groq(client, DISCOVERY_SYSTEM_PROMPT, prompt, max_tokens=1000)
    themes = data.get("themes", [])
    print(f"  Found {len(themes)} themes ({tokens} tokens):")
    for t in themes:
        print(f"    - {t['label']}: {t['description']}")
    return themes


def classify_batch(client, batch, theme_labels, batch_num, total_batches):
    print(f"  Batch {batch_num}/{total_batches}: {len(batch)} reviews...")
    prompt = build_classify_prompt(batch, theme_labels)
    data, tokens = call_groq(client, CLASSIFY_SYSTEM, prompt, max_tokens=800, json_mode=False)
    assignments = {}
    for k, v in data.items():
        try:
            idx = int(k)
            theme_idx = int(v)
            if 0 <= idx < len(batch) and 0 <= theme_idx < len(theme_labels):
                assignments[idx] = theme_labels[theme_idx]
        except (ValueError, TypeError):
            pass
    print(f"    {len(assignments)}/{len(batch)} classified ({tokens} tokens)")
    return assignments


def collect_quotes(client, theme_label, theme_reviews):
    print(f"  Quotes for '{theme_label}' ({len(theme_reviews)} reviews)...")
    prompt = build_quotes_prompt(theme_reviews, theme_label)
    data, tokens = call_groq(client, QUOTES_SYSTEM, prompt, max_tokens=1500)
    quotes = []
    for q in data.get("quotes", []):
        text = q.get("text", "")
        idx = q.get("index", -1)
        if text and 0 <= idx < len(theme_reviews):
            if text in theme_reviews[idx]["text"]:
                quotes.append({
                    "text": text,
                    "rating": theme_reviews[idx].get("rating", 0),
                    "thumbsUpCount": theme_reviews[idx].get("thumbsUpCount", 0),
                })
    print(f"    {len(quotes)} verified quotes ({tokens} tokens)")
    return quotes


def validate_themes(final_data, reviews):
    issues = []
    themes = final_data.get("themes", [])
    if not themes:
        issues.append("No themes returned")
        return issues
    if len(themes) > MAX_THEMES:
        issues.append(f"Too many themes: {len(themes)} (max {MAX_THEMES})")
    total = sum(t.get("count", 0) for t in themes)
    if total != len(reviews):
        issues.append(f"Theme counts sum to {total}, expected {len(reviews)}")
    for t in themes:
        for q in t.get("quotes", []):
            quote_text = q.get("text", "")
            found = any(quote_text in r["text"] for r in reviews)
            if not found:
                short = quote_text[:60] + "..." if len(quote_text) > 60 else quote_text
                issues.append(f"Quote not found verbatim: \"{short}\"")
    return issues


def cluster_reviews(reviews):
    client = Groq(api_key=GROQ_API_KEY)

    print(f"Clustering {len(reviews)} reviews into up to {MAX_THEMES} themes...")
    print(f"Model: {GROQ_MODEL} via Groq (batched for free-tier 8K TPM limit)\n")

    # Phase 1: Discover themes
    theme_defs = discover_themes(client, reviews)
    theme_labels = [t["label"] for t in theme_defs]

    # Phase 2: Classify in batches (compact output: just index -> theme_index)
    print(f"\nPhase 2: Classifying {len(reviews)} reviews in batches of {BATCH_SIZE}...")
    print(f"  Waiting {RATE_LIMIT_DELAY}s after discovery...")
    time.sleep(RATE_LIMIT_DELAY)
    all_assignments = {}
    batches = [reviews[i:i + BATCH_SIZE] for i in range(0, len(reviews), BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        if batch_idx > 0:
            print(f"  Waiting {RATE_LIMIT_DELAY}s for rate limit...")
            time.sleep(RATE_LIMIT_DELAY)

        batch_assignments = classify_batch(
            client, batch, theme_labels, batch_idx + 1, len(batches)
        )
        global_offset = batch_idx * BATCH_SIZE
        for local_idx, label in batch_assignments.items():
            all_assignments[global_offset + local_idx] = label

    # Assign unclassified reviews to the largest theme
    unassigned = [i for i in range(len(reviews)) if i not in all_assignments]
    if unassigned:
        print(f"\n  {len(unassigned)} unassigned reviews -> defaulting to '{theme_labels[0]}'")
        for i in unassigned:
            all_assignments[i] = theme_labels[0]

    # Phase 3: Aggregate and compute stats
    print("\nPhase 3: Aggregating...")
    theme_data = {}
    for td in theme_defs:
        theme_data[td["label"]] = {
            "label": td["label"],
            "description": td["description"],
            "count": 0,
            "review_indices": [],
            "rating_sum": 0,
        }

    for idx, label in sorted(all_assignments.items()):
        if label in theme_data:
            theme_data[label]["review_indices"].append(idx)
            theme_data[label]["count"] += 1
            theme_data[label]["rating_sum"] += reviews[idx].get("rating", 0)

    for td in theme_data.values():
        if td["count"] > 0:
            td["avg_rating"] = round(td["rating_sum"] / td["count"], 1)
        else:
            td["avg_rating"] = 0.0
        del td["rating_sum"]

    # Phase 4: Collect quotes for top themes
    print("\nPhase 4: Collecting quotes for each theme...")
    for label, td in theme_data.items():
        if td["count"] == 0:
            td["quotes"] = []
            continue
        time.sleep(RATE_LIMIT_DELAY)
        theme_reviews = sorted(
            [reviews[i] for i in td["review_indices"]],
            key=lambda r: r.get("thumbsUpCount", 0),
            reverse=True,
        )
        td["quotes"] = collect_quotes(client, label, theme_reviews)

    themes_list = sorted(theme_data.values(), key=lambda t: t["count"], reverse=True)
    themes_list = [t for t in themes_list if t["count"] > 0]

    result = {"themes": themes_list}
    issues = validate_themes(result, reviews)

    result["metadata"] = {
        "clustered_at": datetime.now(timezone.utc).isoformat(),
        "model": GROQ_MODEL,
        "review_count": len(reviews),
        "theme_count": len(themes_list),
        "batches": len(batches),
        "validation_issues": issues,
    }

    print(f"\n=== Clustering Results ===")
    for t in themes_list:
        print(f"  {t['label']}: {t['count']} reviews (avg {t['avg_rating']}*), {len(t['quotes'])} quotes")
    if issues:
        print(f"  Validation issues: {len(issues)}")
        for issue in issues[:5]:
            print(f"    - {issue}")

    return result


def save_themes(themes_data, path=THEMES_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(themes_data, f, indent=2, ensure_ascii=False)
    print(f"Saved themes to {path}")


def load_themes(path=THEMES_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data['themes'])} themes from {path}")
    return data


if __name__ == "__main__":
    with open(CLEANED_REVIEWS_PATH, "r", encoding="utf-8") as f:
        cleaned_data = json.load(f)

    reviews = cleaned_data["reviews"]
    print(f"Loaded {len(reviews)} cleaned reviews")

    themes_data = cluster_reviews(reviews)
    save_themes(themes_data)
