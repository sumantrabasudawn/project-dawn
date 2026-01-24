import time
from pathlib import Path

def main():
    out_dir = Path("state/out")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"items_{int(time.time())}.jsonl"
    out_file.write_text("", encoding="utf-8")
    print(f"Wrote: {out_file}")

if __name__ == "__main__":
    main()

