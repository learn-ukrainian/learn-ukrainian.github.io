"""Tool-prove why curated paronym pairs (#6338) do not emit a practice item.

Reuses the production selection path from ``generate_practice_deck`` (same
entries, same eligibility gate, same priority-key wiring) instead of
re-deriving membership rules, so the residual counts match a real build.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    RealVesumVerifier,
    _clean_text,
    _plain,
    _practice_priority_keys,
    _select_practice_lexemes,
    _valid_paronym_frames,
    read_atlas_db,
    read_paronym_pairs,
    validate_paronym_pair,
)
from scripts.audit.lexeme_filter import is_lexeme_entry, practice_ineligibility_reason


def _entry_lookup(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for entry in entries:
        for key in (_clean_text(entry.get("url_slug")), _clean_text(entry.get("lemma"))):
            if key and key not in by_key:
                by_key[key] = entry
    return by_key


def _leg_status(
    slug: str,
    entry_by_key: dict[str, dict[str, Any]],
    lexemes_by_slug: dict[str, dict[str, Any]],
    by_plain_lemma: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    entry = entry_by_key.get(slug)
    if entry is None:
        return {"slug": slug, "status": "missing_from_atlas"}
    if not is_lexeme_entry(entry):
        return {"slug": slug, "status": "not_lexeme_entry"}
    reason = practice_ineligibility_reason(entry)
    if reason is not None:
        return {"slug": slug, "status": "ineligible", "reason": reason}
    # Mirrors the production paronym resolution in generate_practice_deck.py:
    # slug_to_lex/lexemes_by_id (url_slug/lemmaId), then by_plain_lemma (#6338).
    if (
        slug not in lexemes_by_slug
        and _clean_text(entry.get("lemma")) not in lexemes_by_slug
        and _plain(slug) not in by_plain_lemma
    ):
        return {"slug": slug, "status": "eligible_not_selected"}
    return {"slug": slug, "status": "selected"}


def classify_pairs(
    pairs: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    verifier: RealVesumVerifier,
) -> list[dict[str, Any]]:
    config = BuildConfig()
    priority_keys = _practice_priority_keys([], None, pairs, None)
    _lexemes_by_entry, all_lexemes, by_plain_lemma, lexemes_by_id = _select_practice_lexemes(
        entries, verifier, config, priority_keys
    )
    lexemes_by_slug: dict[str, dict[str, Any]] = {}
    for lexeme in all_lexemes:
        slug = _clean_text(lexeme.get("url_slug")) or _clean_text(lexeme.get("slug")) or lexeme.get("lemmaId")
        if slug:
            lexemes_by_slug[slug] = lexeme
    lexemes_by_slug.update(lexemes_by_id)

    entry_by_key = _entry_lookup(entries)

    results: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        row: dict[str, Any] = {"index": index, "slugA": pair.get("slugA"), "slugB": pair.get("slugB")}
        pair_errors = validate_paronym_pair(pair)
        if pair_errors:
            row["outcome"] = "pair_invalid"
            row["errors"] = pair_errors
            results.append(row)
            continue
        frames = _valid_paronym_frames(pair)
        if not frames:
            row["outcome"] = "no_valid_frames"
            results.append(row)
            continue

        slug_a = _clean_text(pair.get("slugA"))
        slug_b = _clean_text(pair.get("slugB"))
        leg_a = _leg_status(slug_a, entry_by_key, lexemes_by_slug, by_plain_lemma)
        leg_b = _leg_status(slug_b, entry_by_key, lexemes_by_slug, by_plain_lemma)
        row["legA"] = leg_a
        row["legB"] = leg_b
        if leg_a["status"] == "selected" and leg_b["status"] == "selected":
            row["outcome"] = "should_emit"
        else:
            row["outcome"] = "missing_leg"
        results.append(row)
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    outcome_counts = Counter(row["outcome"] for row in results)
    leg_reason_counts: Counter[str] = Counter()
    missing_from_atlas: list[str] = []
    ineligible_by_reason: dict[str, list[str]] = {}
    eligible_not_selected: list[str] = []
    for row in results:
        for leg_key in ("legA", "legB"):
            leg = row.get(leg_key)
            if not leg or leg["status"] == "selected":
                continue
            leg_reason_counts[leg["status"]] += 1
            if leg["status"] == "missing_from_atlas":
                missing_from_atlas.append(leg["slug"])
            elif leg["status"] == "ineligible":
                ineligible_by_reason.setdefault(leg["reason"], []).append(leg["slug"])
            elif leg["status"] == "eligible_not_selected":
                eligible_not_selected.append(leg["slug"])
    return {
        "pairs_total": len(results),
        "outcome_counts": dict(outcome_counts),
        "leg_reason_counts": dict(leg_reason_counts),
        "missing_from_atlas": sorted(set(missing_from_atlas)),
        "ineligible_by_reason": {k: sorted(set(v)) for k, v in ineligible_by_reason.items()},
        "eligible_not_selected": sorted(set(eligible_not_selected)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas-db", type=Path, default=Path("data/atlas.db"))
    parser.add_argument("--paronym-pairs", type=Path, default=Path("data/lexicon/paronym_pairs.yaml"))
    parser.add_argument("--vesum-db", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None, help="Write full per-pair JSON here")
    args = parser.parse_args(argv)

    entries = read_atlas_db(args.atlas_db)
    pairs = read_paronym_pairs(args.paronym_pairs)
    verifier = RealVesumVerifier(args.vesum_db)

    results = classify_pairs(pairs, entries, verifier)
    summary = summarize(results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.out:
        args.out.write_text(
            json.dumps({"summary": summary, "pairs": results}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
