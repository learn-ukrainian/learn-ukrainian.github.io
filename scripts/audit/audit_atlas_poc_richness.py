#!/usr/bin/env python3
"""Audit Atlas search glosses and POC-style page richness.

The legacy Atlas gate only checks that an entry has an ``enrichment`` object.
That misses two learner-facing failures:

* the typeahead suggestion has no visible English gloss (``SearchRow.g``);
* the detail page renders with too few rich POC sections even though the old
  enrichment gate passes.
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

# #4515: the BINDING thin-page cap. Enforced hard at publish time
# (scripts/lexicon/publish_manifest.py) — the per-PR CI step reports the same
# number advisorily. Raising this value is threshold-lowering and needs an
# operator decision; the aligned fix is enriching thin pages before publish.
DEFAULT_MAX_POC_THIN_PAGES = 900

SCRIPT_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_atlas_thin_enriched import (
    has_learner_english_anchor,
    old_gate_enriched,
)

from scripts.lexicon.manifest_io import load_manifest

RICH_SECTION_ORDER = (
    "meaning",
    "etymology",
    "morphology",
    "synonyms_antonyms",
    "idioms",
    "literary_attestation",
    "translation",
    "wikipedia",
    "course_usage",
)


def _read_local_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_list(value: object) -> bool:
    return isinstance(value, list) and any(_nonempty_string(item) for item in value)


def _nonempty_items(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0


def _is_sum11_card(card: dict[str, Any]) -> bool:
    card_id = str(card.get("id") or "")
    source = str(card.get("source") or "")
    source_pill = str(card.get("source_pill") or "")
    return "sum11" in card_id or "СУМ-11" in source or "СУМ-11" in source_pill


def _rendered_definition_cards(enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    cards = enrichment.get("definition_cards")
    if not isinstance(cards, list):
        return []
    return [card for card in cards if isinstance(card, dict) and not _is_sum11_card(card)]


def rendered_sections(entry: dict[str, Any]) -> set[str]:
    """Return non-empty rich section buckets rendered by WordAtlasArticle."""
    sections: set[str] = set()
    enrichment = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}
    extra_sections = entry.get("sections") if isinstance(entry.get("sections"), dict) else {}

    meaning = enrichment.get("meaning") if isinstance(enrichment.get("meaning"), dict) else {}
    if (
        _rendered_definition_cards(enrichment)
        or _nonempty_list(meaning.get("definitions"))
        or (_nonempty_string(entry.get("gloss")) and not meaning)
    ):
        sections.add("meaning")

    etymology = enrichment.get("etymology") if isinstance(enrichment.get("etymology"), dict) else {}
    if _nonempty_string(etymology.get("text")):
        sections.add("etymology")

    morphology = enrichment.get("morphology") if isinstance(enrichment.get("morphology"), dict) else {}
    if (
        _nonempty_items(morphology.get("forms"))
        or _nonempty_items(morphology.get("marked_forms"))
        or isinstance(morphology.get("paradigm"), dict)
    ):
        sections.add("morphology")

    synonyms = extra_sections.get("synonyms") if isinstance(extra_sections.get("synonyms"), dict) else {}
    antonyms = extra_sections.get("antonyms") if isinstance(extra_sections.get("antonyms"), dict) else {}
    if _nonempty_items(synonyms.get("items")) or _nonempty_items(antonyms.get("items")):
        sections.add("synonyms_antonyms")

    idioms = extra_sections.get("idioms") if isinstance(extra_sections.get("idioms"), dict) else {}
    if _nonempty_items(idioms.get("items")):
        sections.add("idioms")

    literary = (
        enrichment.get("literary_attestation")
        if isinstance(enrichment.get("literary_attestation"), dict)
        else {}
    )
    if _nonempty_string(literary.get("text")):
        sections.add("literary_attestation")

    translation = enrichment.get("translation") if isinstance(enrichment.get("translation"), dict) else {}
    if _nonempty_list(translation.get("en")):
        sections.add("translation")

    wiki = entry.get("wiki_reference") if isinstance(entry.get("wiki_reference"), dict) else {}
    if wiki.get("wikipedia") or wiki.get("wiktionary_url") or wiki.get("wikisource_url"):
        sections.add("wikipedia")

    if _nonempty_items(entry.get("course_usage")):
        sections.add("course_usage")

    return sections


def _is_static_search_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("lemma")) and bool(entry.get("url_slug")) and entry.get("pos") != "grammar term"


def _static_search_gloss(entry: dict[str, Any]) -> str | None:
    if _nonempty_string(entry.get("gloss")):
        return str(entry["gloss"])
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    translation = enrichment.get("translation")
    if not isinstance(translation, dict):
        return None
    terms = translation.get("en")
    if not isinstance(terms, list):
        return None
    visible = [str(term).strip() for term in terms if _nonempty_string(term)]
    return "; ".join(visible[:3]) if visible else None


def search_has_visible_gloss(entry: dict[str, Any]) -> bool:
    return _is_static_search_entry(entry) and _nonempty_string(_static_search_gloss(entry))


def _entry_cefr(entry: dict[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        cefr = enrichment.get("cefr")
        if isinstance(cefr, dict) and _nonempty_string(cefr.get("level")):
            return str(cefr["level"]).upper()
    return None


def _row(entry: dict[str, Any], sections: set[str]) -> dict[str, Any]:
    return {
        "lemma": entry.get("lemma"),
        "url_slug": entry.get("url_slug"),
        "pos": entry.get("pos"),
        "cefr": _entry_cefr(entry) or "unknown",
        "primary_source": entry.get("primary_source"),
        "course_used": bool(entry.get("course_usage")),
        "search_has_gloss": search_has_visible_gloss(entry),
        "has_english_anchor": has_learner_english_anchor(entry),
        "rich_section_count": len(sections),
        "rich_sections": [name for name in RICH_SECTION_ORDER if name in sections],
    }


def audit_manifest(
    manifest: dict[str, Any],
    *,
    min_rich_sections: int = 5,
    sample_limit: int = 25,
) -> dict[str, Any]:
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
    search_entries = [entry for entry in entries if _is_static_search_entry(entry)]
    old_enriched = [entry for entry in search_entries if old_gate_enriched(entry)]

    search_no_gloss: list[dict[str, Any]] = []
    old_gate_no_english: list[dict[str, Any]] = []
    poc_thin: list[dict[str, Any]] = []
    rows_by_slug: dict[str, dict[str, Any]] = {}
    section_counts: Counter[int] = Counter()

    for entry in old_enriched:
        sections = rendered_sections(entry)
        section_counts[len(sections)] += 1
        row = _row(entry, sections)
        rows_by_slug[str(entry.get("url_slug"))] = row
        if not row["search_has_gloss"]:
            search_no_gloss.append(row)
        if not row["has_english_anchor"]:
            old_gate_no_english.append(row)
        if len(sections) < min_rich_sections:
            poc_thin.append(row)

    priority = [
        row
        for row in poc_thin
        if row["course_used"] or row["cefr"] in {"A1", "A2"}
    ]

    return {
        "total_entries": len(entries),
        "search_entries": len(search_entries),
        "old_gate_enriched_search_entries": len(old_enriched),
        "min_rich_sections": min_rich_sections,
        "search_no_visible_gloss": len(search_no_gloss),
        "old_gate_no_english_anchor": len(old_gate_no_english),
        "poc_thin_pages": len(poc_thin),
        "priority_poc_thin_pages": len(priority),
        "section_count_histogram": {str(k): v for k, v in sorted(section_counts.items())},
        "poc_thin_by_source": dict(Counter(str(row["primary_source"]) for row in poc_thin).most_common()),
        "poc_thin_by_pos": dict(Counter(str(row["pos"] or "unknown") for row in poc_thin).most_common()),
        "samples": {
            "search_no_visible_gloss": search_no_gloss[:sample_limit],
            "old_gate_no_english_anchor": old_gate_no_english[:sample_limit],
            "poc_thin_pages": poc_thin[:sample_limit],
            "priority_poc_thin_pages": priority[:sample_limit],
        },
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print(
        "Atlas POC richness audit: "
        f"{summary['poc_thin_pages']}/{summary['old_gate_enriched_search_entries']} "
        f"old-gate search entries have fewer than {summary['min_rich_sections']} rich sections."
    )
    print(f"Search suggestions without visible English gloss: {summary['search_no_visible_gloss']}")
    print(f"Old-gate entries without any English anchor: {summary['old_gate_no_english_anchor']}")
    print(f"Priority thin pages (course-used or A1/A2): {summary['priority_poc_thin_pages']}")
    print("Rich-section histogram:")
    for count, total in summary["section_count_histogram"].items():
        print(f"  {count}: {total}")
    print("Top thin-page sources:")
    for source, total in list(summary["poc_thin_by_source"].items())[:10]:
        print(f"  {source}: {total}")
    print("Samples:")
    for name, rows in summary["samples"].items():
        print(f"  {name}:")
        for row in rows[:5]:
            print(
                "    "
                f"{row['lemma']} slug={row['url_slug']} sections={row['rich_section_count']} "
                f"gloss={row['search_has_gloss']} english={row['has_english_anchor']} "
                f"cefr={row['cefr']} source={row['primary_source']}"
            )


def _print_tsv(summary: dict[str, Any]) -> None:
    print("bucket\tlemma\turl_slug\tpos\tcefr\tsections\tsearch_gloss\tenglish_anchor\tprimary_source")
    for bucket, rows in summary["samples"].items():
        for row in rows:
            print(
                "\t".join(
                    [
                        bucket,
                        str(row["lemma"]),
                        str(row["url_slug"]),
                        str(row["pos"] or ""),
                        str(row["cefr"]),
                        str(row["rich_section_count"]),
                        str(row["search_has_gloss"]).lower(),
                        str(row["has_english_anchor"]).lower(),
                        str(row["primary_source"] or ""),
                    ]
                )
            )


def _max_failures(summary: dict[str, Any], limits: dict[str, int | None]) -> list[str]:
    failures: list[str] = []
    for key, limit in limits.items():
        if limit is None:
            continue
        if limit < 0:
            failures.append(f"{key}: max must be non-negative, got {limit}")
            continue
        count = int(summary[key])
        if count > limit:
            failures.append(f"{key}: {count} exceeds max {limit}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read manifest path directly instead of hydrating canonical release asset.",
    )
    parser.add_argument("--min-rich-sections", type=int, default=5)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--format", choices=("summary", "json", "tsv"), default="summary")
    parser.add_argument("--fail-if-any", action="store_true")
    parser.add_argument("--max-search-no-visible-gloss", type=int, default=None)
    parser.add_argument("--max-old-gate-no-english-anchor", type=int, default=None)
    parser.add_argument("--max-poc-thin-pages", type=int, default=None)
    args = parser.parse_args(argv)

    manifest = _read_local_manifest(args.manifest) if args.local else load_manifest(args.manifest)
    summary = audit_manifest(
        manifest,
        min_rich_sections=args.min_rich_sections,
        sample_limit=args.limit,
    )

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.format == "tsv":
        _print_tsv(summary)
    else:
        _print_summary(summary)

    failures = _max_failures(
        summary,
        {
            "search_no_visible_gloss": args.max_search_no_visible_gloss,
            "old_gate_no_english_anchor": args.max_old_gate_no_english_anchor,
            "poc_thin_pages": args.max_poc_thin_pages,
        },
    )

    if args.fail_if_any and (
        summary["search_no_visible_gloss"]
        or summary["old_gate_no_english_anchor"]
        or summary["poc_thin_pages"]
    ):
        failures.append("--fail-if-any matched at least one non-zero audit bucket")

    if failures:
        print("Atlas POC richness gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
