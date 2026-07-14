#!/usr/bin/env python3
"""Deterministic classifier for obvious non-lemma noise in the Word Atlas intake review-queue (#4222)."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

# Closed list of interjections and onomatopoeia as required by triage plan.
CLOSED_INTERJECTIONS = {
    "ааа",
    "а-а-а",
    "ау",
    "ах",
    "ало",
    "алло",
    "апчхи",
    "бах",
    "бабах",
    "бе",
    "бом",
    "бум",
    "вау",
    "гав",
    "гей",
    "гоп",
    "гуп",
    "еге",
    "е-е-е",
    "ех",
    "и-и-и",
    "і-і-і",
    "кап",
    "ква",
    "ко-ко-ко",
    "ку-ку",
    "кукуріку",
    "ме",
    "му",
    "няв",
    "о",
    "ой",
    "ох",
    "ого",
    "ооо",
    "о-о-о",
    "охохо",
    "плиг",
    "п-п-п-п",
    "тиць",
    "тьху",
    "уа",
    "ура",
    "ур-ра",
    "ух",
    "у-у-у",
    "хрю",
    "ціп-ціп",
    "хе-хе",
    "ха-ха",
    "хі-хі",
    "хо-хо",
    "цок",
    "чирик",
    "чух",
    "ша",
    "шух",
}


def is_interjection_onomatopoeia(lemma: str) -> bool:
    """Identify interjections and onomatopoeia from a closed list."""
    return lemma.lower() in CLOSED_INTERJECTIONS


def is_bare_number(lemma: str) -> bool:
    """Identify bare numbers/numerals-as-digits."""
    return bool(re.match(r"^[0-9\s.,-]+$", lemma) and any(c.isdigit() for c in lemma))


def is_single_letter(lemma: str) -> bool:
    """Identify single letters."""
    return len(lemma) == 1 and lemma.isalpha()


def is_markup_debris(lemma: str) -> bool:
    """Identify markup/template debris (e.g. braces, brackets, percent formatting)."""
    return any(c in lemma for c in "[]{}<>`*%\\")


def is_latin_script(lemma: str) -> bool:
    """Identify Latin-script tokens containing no Cyrillic characters."""
    contains_latin = any("a" <= c.lower() <= "z" for c in lemma)
    contains_cyrillic = any("\u0400" <= c <= "\u04ff" or "\u0500" <= c <= "\u052f" for c in lemma)
    has_valid_chars = bool(re.match(r"^[A-Za-z0-9\s.,\-\x27\u2019]+$", lemma))
    return contains_latin and not contains_cyrillic and has_valid_chars


def is_punctuation_debris(lemma: str) -> bool:
    """Identify punctuation remnants/debris."""
    return all(not c.isalnum() for c in lemma)


def classify_lemma(lemma: str) -> str | None:
    """Classify a lemma using noise rules, ensuring a clean intersection.

    If multiple rules match a lemma, it is considered ambiguous and returned as None
    so it remains in the queue untouched.
    """
    matches = []
    if is_interjection_onomatopoeia(lemma):
        matches.append("interjection_onomatopoeia")
    if is_bare_number(lemma):
        matches.append("bare_number")
    if is_single_letter(lemma):
        matches.append("single_letter")
    if is_markup_debris(lemma):
        matches.append("markup_debris")
    if is_latin_script(lemma):
        matches.append("latin_script")
    if is_punctuation_debris(lemma):
        matches.append("punctuation_debris")

    if len(matches) == 1:
        return matches[0]
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic classifier for obvious non-lemma noise.")
    parser.add_argument("--ledger-in", type=Path, default=Path("/tmp/curriculum-ledger.yaml"))
    parser.add_argument("--write", action="store_true", help="Write reject batch YAML to the decisions directory")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.ledger_in.exists():
        print(f"error: input ledger {args.ledger_in} not found. Run curriculum intake first.", file=sys.stderr)
        return 1

    with args.ledger_in.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)

    decisions = payload.get("decisions", [])
    unrecognized = [
        d
        for d in decisions
        if d.get("decision") == "needs_more_evidence" and "vesum_unrecognized" in d.get("review_queue_reasons", [])
    ]

    matches: dict[str, list[dict[str, Any]]] = {
        "interjection_onomatopoeia": [],
        "bare_number": [],
        "single_letter": [],
        "markup_debris": [],
        "latin_script": [],
        "punctuation_debris": [],
    }

    for row in unrecognized:
        lemma = row.get("lemma", "")
        cls = classify_lemma(lemma)
        if cls:
            matches[cls].append(row)

    print(f"Total vesum_unrecognized rows: {len(unrecognized)}")
    for rule_name, rows in matches.items():
        print(f"Rule '{rule_name}': matches={len(rows)}")

    if args.write:
        # Build reject batch decisions list
        reject_decisions = []
        for rule_name, rows in matches.items():
            for row in rows:
                reject_row = {
                    "lemma": row["lemma"],
                    "decision": "reject",
                    "sense_note": f"Bulk-reject noise: {rule_name}",
                    "source_inventory": row["source_inventory"],
                    "evidence_refs": row.get("evidence_refs", ["vesum_unrecognized"]),
                    "original_flags": row.get("review_queue_reasons", ["vesum_unrecognized"]),
                }
                reject_decisions.append(reject_row)

        # Sort decisions deterministically
        reject_decisions.sort(key=lambda d: (d["lemma"].casefold(), d["lemma"]))

        batch_id = "curriculum-intake-2026-07-14-bulk-reject-R1"
        batch_label = "Refs #4222 — bulk-reject rules batch R1"

        reject_payload = {
            "version": 1,
            "kind": "atlas_source_inventory_review_decisions",
            "batch_id": batch_id,
            "batch_label": batch_label,
            "reviewer": "curriculum-intake-automation",
            "reviewed_at": "2026-07-14",
            "source_queue": {
                "workflow": "source_inventory_publish_review_queue.v1",
                "total_queue_rows": len(decisions),
                "approved_in_queue": 0,
                "promotion_batch_size": 1,
            },
            "production_outputs_updated": [],
            "decisions": reject_decisions,
        }

        out_path = (
            PROJECT_ROOT
            / "data/lexicon/source-inventory-review-decisions/2026-07-14-curriculum-intake-bulk-reject-R1.yaml"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(reject_payload, fh, allow_unicode=True, sort_keys=False)

        print(f"Wrote {len(reject_decisions)} rejects to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
