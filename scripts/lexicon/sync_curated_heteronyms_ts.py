#!/usr/bin/env python3
"""Regenerate site/src/lib/lexicon/curated-heteronyms.ts from the Python SSOT.

Root-cause fix for #8039 batch drift risk: the TS client-side fallback must be
byte-for-byte derivable from `enrich_heteronyms.CURATED_HETERONYMS` (per
`tests/test_enrich_heteronyms.py::test_curated_heteronyms_ts_parity`). Hand
duplication invites drift; this script regenerates the JSON-literal block
deterministically so the two SSOTs cannot diverge.

Usage:
    .venv/bin/python scripts/lexicon/sync_curated_heteronyms_ts.py [--check]

--check exits non-zero (no write) if the regenerated content differs from
what's committed -- suitable for a pre-commit/CI drift gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.enrich_heteronyms import CURATED_HETERONYMS

TS_PATH = ROOT / "site" / "src" / "lib" / "lexicon" / "curated-heteronyms.ts"
PREFIX = "export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = "
FOOTER_MARKER = ";\n\nexport function getEffectiveHeteronyms"


def build_ts_data() -> dict:
    ts_data = {}
    for lemma, items in CURATED_HETERONYMS.items():
        ts_data[lemma] = [
            {"lemma": lemma, "url_slug": lemma, **item} for item in items
        ]
    return ts_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 on drift, do not write")
    args = parser.parse_args()

    content = TS_PATH.read_text(encoding="utf-8")
    start_idx = content.find(PREFIX)
    if start_idx == -1:
        print(f"Could not find CURATED_HETERONYMS assignment in {TS_PATH}", file=sys.stderr)
        return 2
    start_idx += len(PREFIX)
    end_idx = content.find(FOOTER_MARKER, start_idx)
    if end_idx == -1:
        print(f"Could not find end marker in {TS_PATH}", file=sys.stderr)
        return 2

    new_json = json.dumps(build_ts_data(), ensure_ascii=False, indent=2)
    new_content = content[:start_idx] + new_json + content[end_idx:]

    if new_content == content:
        print("curated-heteronyms.ts already in sync.")
        return 0

    if args.check:
        print("DRIFT: curated-heteronyms.ts is out of sync with the Python SSOT.", file=sys.stderr)
        return 1

    TS_PATH.write_text(new_content, encoding="utf-8")
    print(f"Regenerated {TS_PATH} ({len(build_ts_data())} lemmas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
