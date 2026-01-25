import json
import time
from pathlib import Path

import yaml
from connectors.rss_connector import collect_rss

ROOT = Path(__file__).resolve().parents[2]  # repo root
ENTITIES = ROOT / "state" / "entities.yaml"
RSS_SOURCES = ROOT / "connectors" / "rss_sources.yaml"
OUT_DIR = ROOT / "state" / "out"

def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    t0 = time.time()

    cfg = load_yaml(ENTITIES)
    entities = cfg.get("entities", [])
    print(f"[DAWN] entities={len(entities)} from {ENTITIES}")

    rss_cfg = load_yaml(RSS_SOURCES)
    templates = rss_cfg.get("default", [])
    print(f"[DAWN] rss_templates={len(templates)} from {RSS_SOURCES}")

    all_items = []

    for e in entities:
        sources = set(e.get("sources", []))
        print(f"[DAWN] entity={e.get('id')} sources={sorted(sources)} queries={len(e.get('queries', []))}")

        if "rss" in sources and templates:
            got = collect_rss(e, templates)
            print(f"[DAWN]  ↳ rss_items={len(got)}")
            all_items.extend(got)
        if "web" in sources:
            print("[DAWN]  ↳ web connector not added yet (skipping)")

    out_file = OUT_DIR / f"items_{int(time.time())}.jsonl"
    write_jsonl(out_file, all_items)
    print(f"[DAWN] wrote={len(all_items)} → {out_file} in {time.time()-t0:.2f}s")

if __name__ == "__main__":
    main()
