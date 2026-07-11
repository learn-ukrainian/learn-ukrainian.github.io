#!/usr/bin/env python3
"""Generate high-precision prefix-based antonym candidates from VESUM.

The output is review-only.  A candidate exists only when both the prefixed
form and its unprefixed base are exact VESUM lemmas with the same POS.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "lexicon" / "cache" / "morphological_antonym_candidates.json"
PREFIXES = ("не", "без", "анти", "проти")
ALLOWED_POS = ("adj", "adv", "noun")
_RARE_MARKERS = (":rare", ":arch", ":dial", ":obsolete", ":slang")


def _norm(value: str) -> str:
    return value.strip().lower()


def load_exact_lemmas(db_path: Path) -> tuple[dict[str, set[str]], dict[tuple[str, str], set[str]]]:
    """Return direct lemma/POS membership and its VESUM tags."""
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT lemma, pos, tags FROM forms "
            "WHERE word_form = lemma AND pos IN ('adj', 'adv', 'noun')"
        ).fetchall()
    finally:
        connection.close()
    exact: dict[str, set[str]] = defaultdict(set)
    tags: dict[tuple[str, str], set[str]] = defaultdict(set)
    for lemma, pos, raw_tags in rows:
        key = _norm(str(lemma))
        pos_key = str(pos)
        exact[key].add(pos_key)
        tags[(key, pos_key)].add(str(raw_tags or ""))
    return dict(exact), dict(tags)


def generate(*, vesum_db: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build candidates and report every base-lemma gate rejection."""
    exact, tags = load_exact_lemmas(vesum_db)
    rows: list[dict[str, Any]] = []
    dropped = Counter()
    seen: set[tuple[str, str, str, str]] = set()
    for negative in sorted(exact):
        for prefix in PREFIXES:
            if not negative.startswith(prefix) or len(negative) <= len(prefix):
                continue
            base = negative[len(prefix) :]
            if base.startswith(PREFIXES):
                dropped["already_prefixed_base"] += 1
                continue
            for pos in sorted(exact[negative] & set(ALLOWED_POS)):
                if pos not in exact.get(base, set()):
                    dropped["base_absent_or_wrong_pos"] += 1
                    continue
                base_tags = tags.get((base, pos), set())
                if any(marker in tag for tag in base_tags for marker in _RARE_MARKERS):
                    dropped["base_rare"] += 1
                    continue
                key = (base, negative, prefix, pos)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "word_a": base,
                        "word_b": negative,
                        "relation": "antonym",
                        "prefix": f"{prefix}-",
                        "pos": pos,
                        "confidence": "high",
                        "source": "VESUM exact lemmas + morphological prefix gate",
                        "evidence": {
                            "base_exact_lemma": True,
                            "negated_exact_lemma": True,
                            "same_pos": True,
                            "base_tags": sorted(base_tags),
                        },
                    }
                )
    rows.sort(key=lambda row: (row["word_a"], row["word_b"], row["prefix"], row["pos"]))
    summary: dict[str, Any] = {
        "candidate_count": len(rows),
        "base_lemma_gate_dropped": sum(dropped.values()),
        "base_lemma_gate_dropped_by_reason": dict(sorted(dropped.items())),
        "prefix_counts": dict(Counter(row["prefix"] for row in rows)),
        "pos_counts": dict(Counter(row["pos"] for row in rows)),
        "samples": rows[:10],
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesum-db", type=Path, default=ROOT / "data" / "vesum.db")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows, summary = generate(vesum_db=args.vesum_db)
    payload = {"schema_version": 1, "relations": rows, "summary": summary}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
