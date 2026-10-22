import argparse
import os
import sys
import time

from config import (
    APP_ID,
    RAW_REVIEWS_PATH,
    CLEANED_REVIEWS_PATH,
    THEMES_PATH,
    PULSE_PATH,
)

from review_collector import fetch_reviews, save_reviews, load_reviews
from data_processor import process_reviews, save_cleaned
from theme_clusterer import cluster_reviews, save_themes
from pulse_generator import generate_pulse, save_pulse, get_date_range, validate_pulse
from delivery import deliver_pulse


def run_pipeline(skip_fetch=False, dry_run=False):
    start = time.time()
    print("=" * 60)
    print("  Weekly App Review Pulse — Groww")
    print("=" * 60)

    # Stage 1: Collect reviews
    print("\n[Stage 1/5] Review Collection")
    print("-" * 40)
    if skip_fetch:
        if not os.path.exists(RAW_REVIEWS_PATH):
            print(f"  ERROR: --skip-fetch used but {RAW_REVIEWS_PATH} not found.")
            print("  Run without --skip-fetch first to collect reviews.")
            sys.exit(1)
        raw_reviews = load_reviews()
    else:
        raw_reviews = fetch_reviews()
        save_reviews(raw_reviews)
    print(f"  => {len(raw_reviews)} raw reviews\n")

    # Stage 2: Data processing & PII stripping
    print("[Stage 2/5] Data Processing & PII Stripping")
    print("-" * 40)
    cleaned, stats = process_reviews(raw_reviews)
    save_cleaned(cleaned, stats)
    dropped = stats["total"] - stats["kept"]
    print(f"  => {len(cleaned)} cleaned reviews (dropped {dropped}: "
          f"{stats['empty']} empty, {stats['non_english']} non-English, "
          f"{stats['short']} short, {stats['duplicate']} duplicate, "
          f"{stats['pii_scrubbed']} PII-scrubbed)\n")

    # Stage 3: Theme clustering
    print("[Stage 3/5] Theme Clustering (LLM)")
    print("-" * 40)
    print("  NOTE: This stage takes ~10 min due to Groq free-tier rate limits.")
    themes_data = cluster_reviews(cleaned)
    save_themes(themes_data)
    themes = themes_data["themes"]
    print(f"  => {len(themes)} themes:")
    for t in themes:
        print(f"     - {t['label']}: {t['count']} reviews, avg {t['avg_rating']}*")
    print()

    # Stage 4: Pulse generation
    print("[Stage 4/5] Pulse Generation (LLM)")
    print("-" * 40)
    date_range = get_date_range()
    pulse_text = generate_pulse(themes_data, len(cleaned), date_range)
    save_pulse(pulse_text)
    word_count = len(pulse_text.split())
    issues = validate_pulse(pulse_text, themes_data)
    if issues:
        print(f"  Validation issues: {issues}")
    else:
        print(f"  Validation: OK")
    print(f"  => {word_count} words, {date_range}\n")

    # Stage 5: Delivery (Google Docs + Gmail)
    print("[Stage 5/5] Delivery (Google Docs & Gmail)")
    print("-" * 40)
    doc_url = deliver_pulse(pulse_text, dry_run=dry_run)

    # Final summary
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    print(f"\n{'=' * 60}")
    print("  PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Duration:  {minutes}m {seconds}s")
    print(f"  Reviews:   {len(raw_reviews)} raw -> {len(cleaned)} cleaned")
    print(f"  Themes:    {len(themes)}")
    print(f"  Pulse:     {word_count} words ({'OK' if word_count <= 250 else 'OVER LIMIT'})")
    print(f"  Delivery:  {'dry-run' if dry_run else 'sent'}")
    if doc_url:
        print(f"  Google Doc: {doc_url}")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Weekly App Review Pulse pipeline for Groww",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Use cached raw_reviews.json instead of fetching from Play Store",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview delivery without actually sending (Google Docs & Gmail)",
    )
    args = parser.parse_args()

    run_pipeline(skip_fetch=args.skip_fetch, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
