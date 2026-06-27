#!/usr/bin/env python3
"""Report Atlas entries that pass the old enrichment gate but lack English anchors.

The legacy gate only checks for any ``enrichment`` block. That catches empty-manifest
regressions, but it also treats pages with Ukrainian-only cards as learner-ready. This
audit keeps that broader gate intact and identifies the narrower class that needs
targeted re-enrichment.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.build_kaikki_lookup import KAIKKI_SOURCE
from scripts.lexicon.manifest_io import load_manifest


def old_gate_enriched(entry: dict[str, Any]) -> bool:
    """Return the legacy enrichment-gate predicate."""
    return bool(entry.get("enrichment"))


def _has_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_nonempty_list(value: object) -> bool:
    return isinstance(value, list) and any(_has_nonempty_string(item) for item in value)


def has_learner_english_anchor(entry: dict[str, Any]) -> bool:
    """Return True when an entry has a learner-facing English meaning anchor."""
    if _has_nonempty_string(entry.get("gloss")):
        return True

    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False

    translation = enrichment.get("translation")
    if isinstance(translation, dict) and _has_nonempty_list(translation.get("en")):
        return True

    meaning = enrichment.get("meaning")
    if not isinstance(meaning, dict):
        return False
    if meaning.get("source") != KAIKKI_SOURCE:
        return False
    return _has_nonempty_list(meaning.get("definitions"))


def thin_old_gate_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Entries counted enriched by the old gate but lacking an English anchor."""
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and old_gate_enriched(entry)
        and not has_learner_english_anchor(entry)
    ]


def _entry_cefr(entry: dict[str, Any]) -> str:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        cefr = enrichment.get("cefr")
        if isinstance(cefr, dict):
            level = cefr.get("level")
            if isinstance(level, str):
                return level.upper()
    level = entry.get("cefr")
    return str(level or "").upper()


def _entry_row(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "lemma": entry.get("lemma"),
        "pos": entry.get("pos"),
        "primary_source": entry.get("primary_source") or "unknown",
        "cefr": _entry_cefr(entry) or None,
        "course_usage": entry.get("course_usage") or [],
    }


def summarize_manifest(manifest: dict[str, Any], *, sample_limit: int = 50) -> dict[str, Any]:
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
    old_enriched = [entry for entry in entries if old_gate_enriched(entry)]
    thin = [entry for entry in old_enriched if not has_learner_english_anchor(entry)]
    by_source = Counter(str(entry.get("primary_source") or "unknown") for entry in thin)
    by_pos = Counter(str(entry.get("pos") or "unknown") for entry in thin)
    course_used = [entry for entry in thin if entry.get("course_usage")]
    beginner = [entry for entry in thin if _entry_cefr(entry) in {"A1", "A2"}]

    return {
        "total_entries": len(entries),
        "old_gate_enriched": len(old_enriched),
        "old_gate_no_english_anchor": len(thin),
        "course_used_no_english_anchor": len(course_used),
        "beginner_cefr_no_english_anchor": len(beginner),
        "by_primary_source": dict(by_source.most_common()),
        "by_pos": dict(by_pos.most_common()),
        "samples": [_entry_row(entry) for entry in thin[:sample_limit]],
    }


def _print_summary(summary: dict[str, Any]) -> None:
    old_gate = int(summary["old_gate_enriched"])
    thin = int(summary["old_gate_no_english_anchor"])
    ratio = thin / old_gate if old_gate else 0.0
    print(
        "Atlas old-gate/no-English-anchor audit: "
        f"{thin}/{old_gate} old-gate-enriched entries ({ratio:.1%})."
    )
    print(f"Course-used no-English entries: {summary['course_used_no_english_anchor']}")
    print(f"Beginner CEFR no-English entries: {summary['beginner_cefr_no_english_anchor']}")
    print("Top primary sources:")
    for source, count in list(summary["by_primary_source"].items())[:10]:
        print(f"  {source}: {count}")
    print("Top POS buckets:")
    for pos, count in list(summary["by_pos"].items())[:10]:
        print(f"  {pos}: {count}")
    if summary["samples"]:
        print("Samples:")
        for entry in summary["samples"]:
            usage = entry["course_usage"]
            usage_label = f" course_usage={len(usage)}" if usage else ""
            print(
                f"  {entry['lemma']} pos={entry['pos'] or 'unknown'} "
                f"cefr={entry['cefr'] or 'unknown'} source={entry['primary_source']}"
                f"{usage_label}"
            )


def _print_tsv(rows: list[dict[str, Any]]) -> None:
    print("lemma\tpos\tcefr\tprimary_source\tcourse_usage_count")
    for row in rows:
        print(
            f"{row['lemma']}\t{row['pos'] or ''}\t{row['cefr'] or ''}\t"
            f"{row['primary_source']}\t{len(row['course_usage'])}"
        )


def _read_local_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit old-gate-enriched Atlas entries that lack learner English anchors."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read the manifest path directly instead of hydrating the canonical release asset.",
    )
    parser.add_argument("--format", choices=("summary", "json", "tsv"), default="summary")
    parser.add_argument("--limit", type=int, default=50, help="Sample/output row limit.")
    parser.add_argument("--fail-if-any", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = _read_local_manifest(manifest_path) if args.local else load_manifest(manifest_path)
    summary = summarize_manifest(manifest, sample_limit=args.limit)

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.format == "tsv":
        _print_tsv(summary["samples"])
    else:
        _print_summary(summary)

    return 1 if args.fail_if_any and summary["old_gate_no_english_anchor"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
