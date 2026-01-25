import time
from urllib.parse import quote_plus

import feedparser

def _urls_for_query(query: str, templates: list[str]) -> list[str]:
    q = quote_plus(query)
    return [t.format(query=q) for t in templates]

def collect_rss(entity: dict, templates: list[str]) -> list[dict]:
    items = []
    now = int(time.time())

    for q in entity.get("queries", []):
        for url in _urls_for_query(q, templates):
            feed = feedparser.parse(url)
            for e in getattr(feed, "entries", []):
                items.append({
                    "entity_id": entity.get("id"),
                    "entity_name": entity.get("name"),
                    "entity_type": entity.get("type"),
                    "source": "rss",
                    "query": q,
                    "title": getattr(e, "title", ""),
                    "url": getattr(e, "link", ""),
                    "published": getattr(e, "published", ""),
                    "captured_at": now,
                })
    return items
