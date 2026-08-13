"""Explain curated antonym or homonym practice residuals (#6338).

The audit imports the production selector, validators, frame filters, and item
builders. It therefore measures the same candidate pool and emit gate as a
real practice build; it never invents a lexeme or a CEFR placement to improve
coverage.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    RealVesumVerifier,
    _build_antonym_items,
    _build_homonym_items,
    _clean_text,
    _plain,
    _practice_priority_keys,
    _select_practice_lexemes,
    _strip_antonym_option_metadata,
    _strip_homonym_option_metadata,
    _valid_antonym_frames,
    _valid_homonym_frames,
    admit_thin_mode_pair_leg_surfaces,
    read_antonym_pairs,
    read_atlas_db,
    read_homonym_pairs,
    validate_antonym_item,
    validate_antonym_pair,
    validate_homonym_item,
    validate_homonym_pair,
)
from scripts.audit.lexeme_filter import is_lexeme_entry, practice_ineligibility_reason

RelationBuilder = Callable[..., list[dict[str, Any]]]
RelationValidator = Callable[[dict[str, Any]], list[str]]
FrameSelector = Callable[[dict[str, Any]], list[dict[str, Any]]]


def _relation_parts(
    relation: str,
) -> tuple[Callable[[Path], list[dict[str, Any]]], RelationValidator, FrameSelector, RelationBuilder, Callable[[dict[str, Any]], dict[str, Any]], Callable[[dict[str, Any], bool], list[str]]]:
    if relation == "antonym":
        return (
            read_antonym_pairs,
            validate_antonym_pair,
            _valid_antonym_frames,
            _build_antonym_items,
            _strip_antonym_option_metadata,
            lambda item, internal: validate_antonym_item(item, internal_options=internal),
        )
    return (
        read_homonym_pairs,
        validate_homonym_pair,
        _valid_homonym_frames,
        _build_homonym_items,
        _strip_homonym_option_metadata,
        lambda item, internal: validate_homonym_item(item, internal_options=internal),
    )


def _entry_lookup(entries: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_key: dict[str, dict[str, Any]] = {}
    by_plain: dict[str, dict[str, Any]] = {}
    for entry in entries:
        for key in (_clean_text(entry.get("url_slug")), _clean_text(entry.get("lemma"))):
            if key:
                by_key.setdefault(key, entry)
                by_plain.setdefault(_plain(key), entry)
    return by_key, by_plain


def _leg_status(
    slug: str,
    entry_by_key: dict[str, dict[str, Any]],
    entry_by_plain: dict[str, dict[str, Any]],
    lexemes_by_id: dict[str, dict[str, Any]],
    by_plain_lemma: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    entry = entry_by_key.get(slug) or entry_by_plain.get(_plain(slug))
    if entry is None:
        return {"slug": slug, "status": "missing_from_atlas"}, None
    if not is_lexeme_entry(entry):
        return {"slug": slug, "status": "not_lexeme_entry"}, None
    if reason := practice_ineligibility_reason(entry):
        return {"slug": slug, "status": "ineligible", "reason": reason}, None
    lexeme = lexemes_by_id.get(slug) or by_plain_lemma.get(_plain(slug))
    if lexeme is None:
        return {"slug": slug, "status": "eligible_not_selected"}, None
    return {
        "slug": slug,
        "status": "selected",
        "cefr": lexeme.get("cefr"),
        "cefr_status": "anchored" if lexeme.get("cefr") else "uses_b1_fallback",
    }, lexeme


def classify_pairs(
    relation: str,
    pairs: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    verifier: RealVesumVerifier,
) -> list[dict[str, Any]]:
    """Classify pair residuals through the production selection and item emitters."""
    _reader, validator, frame_selector, builder, strip_options, item_validator = _relation_parts(relation)
    priority_keys = _practice_priority_keys(
        [],
        None,
        None,
        None,
        antonym_pairs=pairs if relation == "antonym" else None,
        homonym_pairs=pairs if relation == "homonym" else None,
    )
    practice_entries = admit_thin_mode_pair_leg_surfaces(entries, priority_keys)
    _by_entry, all_lexemes, by_plain_lemma, lexemes_by_id = _select_practice_lexemes(
        practice_entries, verifier, BuildConfig(), priority_keys
    )
    for lexeme in all_lexemes:
        slug = _clean_text(lexeme.get("url_slug")) or _clean_text(lexeme.get("slug"))
        if slug:
            lexemes_by_id.setdefault(slug, lexeme)
    entry_by_key, entry_by_plain = _entry_lookup(practice_entries)

    results: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        row: dict[str, Any] = {"index": index, "slugA": pair.get("slugA"), "slugB": pair.get("slugB")}
        if errors := validator(pair):
            row.update(outcome="pair_invalid", errors=errors)
            results.append(row)
            continue
        if not frame_selector(pair):
            row["outcome"] = "no_valid_frames"
            results.append(row)
            continue

        slug_a = _clean_text(pair.get("slugA"))
        slug_b = _clean_text(pair.get("slugB"))
        leg_a, lex_a = _leg_status(slug_a, entry_by_key, entry_by_plain, lexemes_by_id, by_plain_lemma)
        leg_b, lex_b = _leg_status(slug_b, entry_by_key, entry_by_plain, lexemes_by_id, by_plain_lemma)
        row.update(legA=leg_a, legB=leg_b)
        if not lex_a or not lex_b:
            row["outcome"] = "missing_leg"
            results.append(row)
            continue

        internal_items = builder(pair, lex_a, lex_b, "relation-residual-audit", verifier=verifier, public_options=False)
        public_items = [strip_options(item) for item in internal_items]
        valid_items = [
            item
            for internal, item in zip(internal_items, public_items, strict=True)
            if not item_validator(internal, True) and not item_validator(item, False)
        ]
        if not valid_items:
            row["outcome"] = "frame_answer_unresolved"
        else:
            row.update(outcome="emitted", emitted_items=len(valid_items))
        results.append(row)
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    outcome_counts = Counter(row["outcome"] for row in results)
    leg_status_counts: Counter[str] = Counter()
    ineligible_by_reason: Counter[str] = Counter()
    cefr_status_counts: Counter[str] = Counter()
    for row in results:
        for leg_key in ("legA", "legB"):
            leg = row.get(leg_key)
            if not isinstance(leg, dict):
                continue
            leg_status_counts[str(leg["status"])] += 1
            if leg["status"] == "ineligible":
                ineligible_by_reason[str(leg.get("reason"))] += 1
            if leg["status"] == "selected":
                cefr_status_counts[str(leg["cefr_status"])] += 1
    return {
        "pairs_total": len(results),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "leg_status_counts": dict(sorted(leg_status_counts.items())),
        "ineligible_by_reason": dict(sorted(ineligible_by_reason.items())),
        "selected_cefr_status_counts": dict(sorted(cefr_status_counts.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relation", choices=("antonym", "homonym"), required=True)
    parser.add_argument("--atlas-db", type=Path, default=Path("data/atlas.db"))
    parser.add_argument("--pairs", type=Path)
    parser.add_argument("--vesum-db", type=Path, required=True)
    parser.add_argument("--out", type=Path, help="Write full pair classifications here")
    args = parser.parse_args(argv)

    reader, *_rest = _relation_parts(args.relation)
    pairs_path = args.pairs or Path(f"data/lexicon/{args.relation}_pairs.yaml")
    results = classify_pairs(args.relation, reader(pairs_path), read_atlas_db(args.atlas_db), RealVesumVerifier(args.vesum_db))
    summary = summarize(results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.out:
        args.out.write_text(json.dumps({"summary": summary, "pairs": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
