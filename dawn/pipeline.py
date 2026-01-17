from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

from dawn.schema import Event


SENTIMENT_MAP = {
    "positive": "positive",
    "pos": "positive",
    "p": "positive",
    "negative": "negative",
    "neg": "negative",
    "n": "negative",
    "neutral": "neutral",
    "neu": "neutral",
    "0": "neutral",
    "1": "positive",
    "-1": "negative",
}


@dataclass
class PipelineResult:
    events: List[Event]
    output_path: Path
    deduplicated: int
    total_input: int


def _normalize_sentiment(value: str) -> str:
    if value is None:
        return "neutral"
    normalized = str(value).strip().lower()
    return SENTIMENT_MAP.get(normalized, normalized or "neutral")


def _normalize_date(value) -> datetime:
    if isinstance(value, datetime):
        return value
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return datetime.utcnow()
    return parsed.to_pydatetime()


def _build_event_id(event: Event) -> str:
    base = "|".join(
        [
            event.company,
            event.published_at.isoformat(),
            event.publisher,
            event.title,
            str(event.url or ""),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _deduplicate(events: Iterable[Event]) -> Tuple[List[Event], int]:
    events_list = list(events)
    seen = {}
    for event in events_list:
        seen[event.event_id] = event
    deduped = list(seen.values())
    return deduped, len(events_list) - len(deduped)


def run_pipeline(
    events: Iterable[Event],
    output_dir: Path = Path("data/clean"),
    checkpoint_path: Path = Path("state/checkpoints.json"),
) -> PipelineResult:
    normalized_events: List[Event] = []
    for event in events:
        normalized = event.model_copy(
            update={
                "published_at": _normalize_date(event.published_at),
                "sentiment": _normalize_sentiment(event.sentiment),
            }
        )
        normalized = normalized.model_copy(update={"event_id": _build_event_id(normalized)})
        normalized_events.append(normalized)

    deduped_events, _ = _deduplicate(normalized_events)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "events.parquet"

    df = pd.DataFrame([event.model_dump() for event in deduped_events])
    wrote_parquet = False
    try:
        df.to_parquet(output_path, index=False)
        wrote_parquet = True
    except Exception:
        output_path = output_dir / "events.csv"
        df.to_csv(output_path, index=False)

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "last_run": datetime.utcnow().isoformat() + "Z",
        "total_input": len(normalized_events),
        "deduplicated": len(normalized_events) - len(deduped_events),
        "output": str(output_path),
        "wrote_parquet": wrote_parquet,
    }
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2))

    return PipelineResult(
        events=deduped_events,
        output_path=output_path,
        deduplicated=len(normalized_events) - len(deduped_events),
        total_input=len(normalized_events),
    )
