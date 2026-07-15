#!/usr/bin/env python3
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    candidates_path = PROJECT_ROOT / "audit/errorcorrection_candidates.json"
    if not candidates_path.exists():
        print("Candidates file not found.")
        sys.exit(1)

    with open(candidates_path, encoding="utf-8") as f:
        data = json.load(f)

    unique_words = data.get("unique_words", [])
    print(f"Total unique words: {len(unique_words)}")

    # We will generate batches of 100 words.
    batch_size = 100
    for i in range(0, len(unique_words), batch_size):
        batch = unique_words[i : i + batch_size]
        print(f"\n--- BATCH {i // batch_size + 1} (size {len(batch)}) ---")
        print(json.dumps(batch, ensure_ascii=False))


if __name__ == "__main__":
    main()
