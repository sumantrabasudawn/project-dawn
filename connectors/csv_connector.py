from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Union

import pandas as pd

from dawn.schema import Event


COLUMN_MAP = {
    "event_id": "event_id",
    "company": "company",
    "published_at": "published_at",
    "date": "published_at",
    "datetime": "published_at",
    "source_type": "source_type",
    "source": "source_type",
    "publisher": "publisher",
    "title": "title",
    "headline": "title",
    "url": "url",
    "link": "url",
    "text": "text",
    "content": "text",
    "summary": "text",
    "theme": "theme",
    "category": "theme",
    "sentiment": "sentiment",
    "impact_score": "impact_score",
    "impact": "impact_score",
    "is_trigger_event": "is_trigger_event",
    "trigger": "is_trigger_event",
}

DEFAULTS = {
    "company": "Unknown",
    "source_type": "csv",
    "publisher": "Unknown",
    "title": "Untitled",
    "text": "",
    "theme": "general",
    "sentiment": "neutral",
    "impact_score": 0.5,
    "is_trigger_event": False,
}


def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapped = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[key]
    return df.rename(columns=mapped)


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _build_event(record: dict) -> Event:
    data = {**DEFAULTS, **record}
    published_at = data.get("published_at") or datetime.utcnow()
    return Event(
        event_id=str(data.get("event_id", "")),
        company=str(data.get("company", DEFAULTS["company"])),
        published_at=published_at,
        source_type=str(data.get("source_type", DEFAULTS["source_type"])),
        publisher=str(data.get("publisher", DEFAULTS["publisher"])),
        title=str(data.get("title", DEFAULTS["title"])),
        url=data.get("url") or None,
        text=str(data.get("text", DEFAULTS["text"])),
        theme=str(data.get("theme", DEFAULTS["theme"])),
        sentiment=str(data.get("sentiment", DEFAULTS["sentiment"])),
        impact_score=float(data.get("impact_score", DEFAULTS["impact_score"])),
        is_trigger_event=_coerce_bool(data.get("is_trigger_event")),
    )


def load_events_from_csv(path_or_buffer: Union[str, Path, Iterable[bytes]]) -> List[Event]:
    df = pd.read_csv(path_or_buffer)
    df = _map_columns(df)
    events: List[Event] = []
    for record in df.to_dict(orient="records"):
        events.append(_build_event(record))
    return events


def load_events_from_directory(directory: Union[str, Path]) -> List[Event]:
    directory_path = Path(directory)
    events: List[Event] = []
    for csv_path in directory_path.glob("*.csv"):
        events.extend(load_events_from_csv(csv_path))
    return events
