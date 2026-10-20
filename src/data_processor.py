import json
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from config import (
    CLEANED_REVIEWS_PATH,
    RAW_REVIEWS_PATH,
    REVIEW_WINDOW_WEEKS,
)

MIN_WORD_COUNT = 8
MIN_ENGLISH_RATIO = 0.5

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)

PII_PATTERNS = [
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{10,12}\b"), "[REDACTED_ID]"),
    (re.compile(r"@\w{2,30}\b"), "[REDACTED_HANDLE]"),
    (re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"), "[REDACTED_IFSC]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b[\w.-]+@[\w]{2,}\b(?=.*upi)", re.IGNORECASE), "[REDACTED_UPI]"),
]


def strip_pii(text):
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def strip_emojis(text):
    return EMOJI_PATTERN.sub("", text)


def normalize_text(text):
    text = unicodedata.normalize("NFC", text)
    text = strip_emojis(text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_english(text):
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    all_letters = sum(1 for c in text if c.isalpha())
    if all_letters == 0:
        return False
    return ascii_letters / all_letters >= MIN_ENGLISH_RATIO


def is_meaningful(text):
    if not text:
        return False
    alpha_chars = sum(1 for c in text if c.isalpha())
    if len(text) == 0 or alpha_chars / len(text) < 0.3:
        return False
    words = text.split()
    if len(words) <= MIN_WORD_COUNT:
        return False
    return True


def process_reviews(raw_reviews):
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=REVIEW_WINDOW_WEEKS)
    seen_texts = set()
    cleaned = []
    stats = {
        "total": len(raw_reviews),
        "empty": 0,
        "non_english": 0,
        "short": 0,
        "duplicate": 0,
        "pii_scrubbed": 0,
        "kept": 0,
    }

    for r in raw_reviews:
        text = r.get("text", "")
        if not text or not text.strip():
            stats["empty"] += 1
            continue

        text = normalize_text(text)

        if not is_english(text):
            stats["non_english"] += 1
            continue

        original = text
        text = strip_pii(text)
        if text != original:
            stats["pii_scrubbed"] += 1

        if not is_meaningful(text):
            stats["short"] += 1
            continue

        text_lower = text.lower()
        if text_lower in seen_texts:
            stats["duplicate"] += 1
            continue
        seen_texts.add(text_lower)

        cleaned.append({
            "rating": r.get("rating"),
            "text": text,
            "date": r.get("date", ""),
            "thumbsUpCount": r.get("thumbsUpCount", 0),
            "reviewCreatedVersion": r.get("reviewCreatedVersion", ""),
        })
        stats["kept"] += 1

    cleaned.sort(key=lambda r: r["date"], reverse=True)
    return cleaned, stats


def save_cleaned(reviews_list, stats, path=CLEANED_REVIEWS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    output = {
        "metadata": {
            "cleaned_at": datetime.now(timezone.utc).isoformat(),
            "review_count": len(reviews_list),
            "processing_stats": stats,
        },
        "reviews": reviews_list,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(reviews_list)} cleaned reviews to {path}")


def load_cleaned(path=CLEANED_REVIEWS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data['reviews'])} cleaned reviews from {path}")
    return data["reviews"]


if __name__ == "__main__":
    with open(RAW_REVIEWS_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    raw_reviews = raw_data["reviews"]
    print(f"Raw reviews loaded: {len(raw_reviews)}")

    cleaned, stats = process_reviews(raw_reviews)

    print(f"\n=== Processing Stats ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    save_cleaned(cleaned, stats)

    pii_check = 0
    for r in cleaned:
        if re.search(r"[\w.-]+@[\w.-]+\.\w{2,}", r["text"]):
            pii_check += 1
    print(f"\nPII post-check (emails found in cleaned): {pii_check}")
