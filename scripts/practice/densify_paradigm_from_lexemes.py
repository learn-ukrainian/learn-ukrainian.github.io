#!/usr/bin/env python3
"""Rebuild practice-paradigm shards + index mode flags from practice-lexemes.

Uses existing hydrated lexeme paradigms only (no LLM, no new pair invention).
Applies current ``_build_paradigm_items`` (VESUM English keys + syncretic surfaces).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.generate_practice_deck import (
    DRILL_MODES,
    _build_paradigm_items,
    _json_bytes,
)

DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"
LEVELS = ("A1", "A2", "B1", "B2", "C1")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected object")
    return payload


def densify_level(practice_dir: Path, level: str) -> dict[str, int]:
    lexemes_path = practice_dir / f"practice-lexemes.{level}.json"
    paradigm_path = practice_dir / f"practice-paradigm.{level}.json"
    index_path = practice_dir / f"practice-index.{level}.json"

    lexemes_payload = _load(lexemes_path)
    paradigm_payload = _load(paradigm_path)
    index_payload = _load(index_path)

    lexemes = lexemes_payload.get("lexemes")
    if not isinstance(lexemes, list):
        raise ValueError(f"{lexemes_path}: lexemes must be a list")
    index_items = index_payload.get("items")
    if not isinstance(index_items, list):
        raise ValueError(f"{index_path}: items must be a list")

    paradigm_items: list[dict[str, Any]] = []
    lemma_ids_with_paradigm: set[str] = set()
    for lexeme in lexemes:
        if not isinstance(lexeme, dict):
            continue
        items = _build_paradigm_items(lexeme)
        if not items:
            continue
        lemma_id = str(lexeme.get("lemmaId") or "").strip()
        if lemma_id:
            lemma_ids_with_paradigm.add(lemma_id)
        paradigm_items.extend(items)

    before_unique = len(
        {
            str(item.get("lemmaId") or "").strip()
            for item in (paradigm_payload.get("paradigm") or [])
            if isinstance(item, dict) and str(item.get("lemmaId") or "").strip()
        }
    )

    paradigm_payload["paradigm"] = paradigm_items
    paradigm_path.write_bytes(_json_bytes(paradigm_payload))

    for item in index_items:
        if not isinstance(item, dict):
            continue
        lemma_id = str(item.get("lemmaId") or "").strip()
        modes = item.get("modes")
        if not isinstance(modes, list):
            continue
        mode_list = [str(mode) for mode in modes if str(mode).strip()]
        has = "paradigm" in mode_list
        should = lemma_id in lemma_ids_with_paradigm
        if should and not has:
            # Keep drill modes after recognition modes; append before end.
            insert_at = len(mode_list)
            for drill in DRILL_MODES:
                if drill in mode_list:
                    insert_at = mode_list.index(drill)
                    break
            mode_list.insert(insert_at, "paradigm")
            item["modes"] = mode_list
        elif has and not should:
            item["modes"] = [mode for mode in mode_list if mode != "paradigm"]

    counts = index_payload.get("counts")
    if isinstance(counts, dict):
        mode_counts = counts.get("modeCounts")
        if isinstance(mode_counts, dict):
            mode_counts["paradigm"] = len(paradigm_items)
        mode_coverage = counts.get("modeCoverage")
        if isinstance(mode_coverage, dict) and lexemes:
            mode_coverage["paradigm"] = round(len(lemma_ids_with_paradigm) / len(lexemes), 4)

    index_path.write_bytes(_json_bytes(index_payload))
    return {
        "level": level,
        "before_unique": before_unique,
        "after_unique": len(lemma_ids_with_paradigm),
        "items": len(paradigm_items),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    args = parser.parse_args(argv)

    rows = [densify_level(args.practice_dir, level) for level in LEVELS]
    before = sum(row["before_unique"] for row in rows)
    after = sum(row["after_unique"] for row in rows)
    # Recompute global unique via coverage-style union
    from scripts.practice.coverage_report import collect_mode_inventory

    inv = collect_mode_inventory(args.practice_dir)
    paradigm = inv["modes"].get("paradigm") or {}
    print("per-level:", rows)
    print(
        f"paradigm unique_lemmas_all_levels={paradigm.get('unique_lemmas_all_levels')} "
        f"(sum-of-levels before≈{before} after≈{after})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
