#!/usr/bin/env python3
"""Measure Word Atlas core-vocabulary enrichment coverage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
SECTIONS = ("stress", "meaning", "etymology", "translation", "cefr")


def _core_entries(manifest: dict) -> list[dict]:
    return [
        entry
        for entry in manifest.get("entries", [])
        if entry.get("lemma") and not re.search(r"\s", str(entry["lemma"]))
    ]


def measure(path: Path = MANIFEST) -> str:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = _core_entries(manifest)
    total = len(entries)
    lines = [f"core_single_word_entries {total}"]
    for section in SECTIONS:
        covered = sum(1 for entry in entries if (entry.get("enrichment") or {}).get(section))
        pct = covered / total * 100 if total else 0.0
        lines.append(f"{section} {covered}/{total} {pct:.1f}%")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure Word Atlas core-vocabulary coverage.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST, help="Lexicon manifest JSON path.")
    args = parser.parse_args()
    print(measure(args.manifest))


if __name__ == "__main__":
    main()
