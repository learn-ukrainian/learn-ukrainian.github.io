"""Measure deterministic Russicism recall against extracted UA-GEC F/Calque pairs.

Usage:
    .venv/bin/python scripts/audit/measure_russicism_recall.py

Input:
    /tmp/ua-gec-pairs.jsonl, produced by /tmp/ua_gec_extract.py.

The measurement probes unique UA-GEC F/Calque `bad` strings in a minimal
lesson-content wrapper. "before" is the existing deterministic regex detector;
"after" adds the CSV-backed UA-GEC bulk lookup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit.checks.russicism_detection import check_russicisms, check_ua_gec_calques

SOURCE = Path("/tmp/ua-gec-pairs.jsonl")
PROBE_PATH = "/curriculum/l2-uk-en/b1/ua-gec-recall-probe.md"


def _wrap_probe(text: str) -> str:
    return f"---\nlevel: B1\n---\n\n# UA-GEC recall probe\n\n## Пояснення\n\n{text}\n"


def _load_unique_bad_forms(path: Path) -> list[str]:
    bad_forms: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("error_type") != "F/Calque":
                continue
            bad = (row.get("bad") or "").strip().casefold()
            good = (row.get("good") or "").strip()
            if bad and good:
                bad_forms.add(bad)
    return sorted(bad_forms)


def _is_caught_before(bad: str) -> bool:
    return bool(check_russicisms(_wrap_probe(bad), PROBE_PATH))


def _is_caught_after(bad: str) -> bool:
    content = _wrap_probe(bad)
    return bool(check_russicisms(content, PROBE_PATH) or check_ua_gec_calques(content, PROBE_PATH))


def _format_recall(label: str, caught: int, total: int) -> str:
    percentage = (caught / total * 100) if total else 0.0
    return f"{label}: {caught}/{total} ({percentage:.2f}%)"


def main() -> int:
    if not SOURCE.exists():
        print(__doc__.strip())
        print(f"\nERROR: missing required source file: {SOURCE}")
        return 2

    bad_forms = _load_unique_bad_forms(SOURCE)
    total = len(bad_forms)
    before = sum(1 for bad in bad_forms if _is_caught_before(bad))
    after = sum(1 for bad in bad_forms if _is_caught_after(bad))
    before_pct = (before / total * 100) if total else 0.0
    after_pct = (after / total * 100) if total else 0.0

    print(f"UA-GEC F/Calque source: {SOURCE}")
    print(f"unique_bad_entries: {total}")
    print(_format_recall("before_bulk_lookup", before, total))
    print(_format_recall("after_bulk_lookup", after, total))
    print(f"delta: +{after - before} entries (+{after_pct - before_pct:.2f} pp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
