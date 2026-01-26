# connectors/web_parser.py
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import feedparser
import pandas as pd

LIVE_DIR = Path("data/live")
LIVE_FILE = LIVE_DIR / "dawn_live_data.csv"
LAST_GOOD_FILE = LIVE_DIR / "last_good.csv"
TMP_FILE = LIVE_DIR / "_tmp_dawn_live_data.csv"

# You can move this list to a config file later
DEFAULT_COMPANIES = [
    "Tata Steel",
    "JSW Steel",
    "SAIL",
    "Jindal Steel",
]

def _hash_id(*parts: str) -> str:
    raw = "||".join([p or "" for p in parts]).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:24]

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def fetch_google_news_rss(company: str) -> List[Dict]:
    # Google News RSS query endpoint
    url = f"https://news.google.com/rss/search?q={company}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    rows: List[Dict] = []
    for entry in feed.entries:
        published = entry.get("published") or entry.get("updated") or _now_utc_iso()

        title = entry.get("title", "") or ""
        link = entry.get("link", "") or ""
        summary = entry.get("summary", "") or ""

        # Publisher sometimes comes as "source" or within the title after " - "
        publisher = ""
        if "source" in entry and isinstance(entry["source"], dict):
            publisher = entry["source"].get("title", "") or ""
        if not publisher and " - " in title:
            # common pattern: "Headline - Publisher"
            publisher = title.split(" - ", 1)[-1].strip()

        event_id = _hash_id(company, title, link, str(published))

        rows.append(
            {
                "event_id": event_id,
                "company": company,
                "published_at": published,
                "source_type": "google_news_rss",
                "publisher": publisher or "Unknown",
                "title": title,
                "url": link or None,
                "text": summary,
                "theme": "general",
                "sentiment": "neutral",
                "impact_score": 0.5,
                "is_trigger_event": False,
            }
        )
    return rows

def run(companies: List[str] | None = None) -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)

    companies = companies or DEFAULT_COMPANIES
    all_rows: List[Dict] = []

    for c in companies:
        all_rows.extend(fetch_google_news_rss(c))

    df = pd.DataFrame(all_rows)

    # If nothing fetched, don't overwrite existing files
    if df.empty:
        print("No rows fetched; leaving existing live data untouched.")
        return

    # Clean + dedupe
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["published_at"])
    df = df.sort_values("published_at", ascending=False)
    df = df.drop_duplicates(subset=["event_id"], keep="first")

    # Atomic write (temp then replace)
    df.to_csv(TMP_FILE, index=False)
    os.replace(TMP_FILE, LIVE_FILE)

    # Update last_good only after successful live write
    df.to_csv(LAST_GOOD_FILE, index=False)

    print(f"Wrote {len(df)} rows to {LIVE_FILE} and updated {LAST_GOOD_FILE}")

if __name__ == "__main__":
    run()

