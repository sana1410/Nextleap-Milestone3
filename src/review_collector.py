import json
import os
import time
from datetime import datetime, timedelta, timezone

from google_play_scraper import Sort, reviews

from config import (
    APP_ID,
    DATA_DIR,
    MAX_REVIEWS_PER_FETCH,
    RAW_REVIEWS_PATH,
    REVIEW_COUNTRY,
    REVIEW_LANGUAGE,
    REVIEW_WINDOW_WEEKS,
)


def _fetch_batch(app_id, sort_order, max_count, cutoff_date, retries=3):
    all_reviews = []
    continuation_token = None
    batch_num = 0
    sort_name = "NEWEST" if sort_order == Sort.NEWEST else "MOST_RELEVANT"

    while len(all_reviews) < max_count:
        batch_size = min(200, max_count - len(all_reviews))
        attempt = 0
        result = None

        while attempt < retries:
            try:
                result, continuation_token = reviews(
                    app_id,
                    lang=REVIEW_LANGUAGE,
                    country=REVIEW_COUNTRY,
                    sort=sort_order,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
                break
            except Exception as e:
                attempt += 1
                wait = 2 ** attempt
                print(f"  [{sort_name}] Fetch error (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    print(f"  Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print("  Max retries reached for this batch, stopping.")
                    result = None

        if not result:
            break

        batch_num += 1
        in_window = 0
        past_window = 0

        for r in result:
            review_date = r.get("at")
            if review_date is None:
                continue
            if hasattr(review_date, "tzinfo") and review_date.tzinfo is None:
                review_date = review_date.replace(tzinfo=timezone.utc)
            if review_date < cutoff_date:
                past_window += 1
                continue

            in_window += 1
            all_reviews.append({
                "rating": r.get("score"),
                "text": r.get("content", ""),
                "date": review_date.isoformat(),
                "thumbsUpCount": r.get("thumbsUpCount", 0),
                "reviewCreatedVersion": r.get("reviewCreatedVersion", ""),
                "replyContent": r.get("replyContent", ""),
                "reviewId": r.get("reviewId", ""),
            })

        print(f"  [{sort_name}] Batch {batch_num}: {len(result)} fetched, {in_window} in window, {past_window} past cutoff")

        if past_window > len(result) * 0.5:
            print(f"  [{sort_name}] Majority past date window, stopping.")
            break
        if continuation_token is None:
            print(f"  [{sort_name}] No more pages available.")
            break

        time.sleep(1)

    return all_reviews


def fetch_reviews(app_id=APP_ID, max_reviews=MAX_REVIEWS_PER_FETCH, retries=3):
    cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=REVIEW_WINDOW_WEEKS)

    print(f"Fetching reviews for {app_id} (last {REVIEW_WINDOW_WEEKS} weeks)...")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")

    print("\n--- Pass 1: NEWEST ---")
    newest = _fetch_batch(app_id, Sort.NEWEST, max_reviews, cutoff_date, retries)

    print("\n--- Pass 2: MOST_RELEVANT ---")
    relevant = _fetch_batch(app_id, Sort.MOST_RELEVANT, max_reviews, cutoff_date, retries)

    seen_ids = set()
    merged = []
    for r in newest + relevant:
        rid = r["reviewId"]
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            merged.append(r)
        elif not rid:
            merged.append(r)

    merged.sort(key=lambda r: r["date"], reverse=True)

    print(f"\nTotal: {len(newest)} newest + {len(relevant)} relevant = {len(merged)} unique reviews")
    return merged


def save_reviews(reviews_list, path=RAW_REVIEWS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    output = {
        "metadata": {
            "app_id": APP_ID,
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "review_count": len(reviews_list),
            "window_weeks": REVIEW_WINDOW_WEEKS,
        },
        "reviews": reviews_list,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(reviews_list)} reviews to {path}")


def load_reviews(path=RAW_REVIEWS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data['reviews'])} reviews from {path}")
    return data["reviews"]


if __name__ == "__main__":
    fetched = fetch_reviews()
    if fetched:
        save_reviews(fetched)
    else:
        print("No reviews fetched.")
