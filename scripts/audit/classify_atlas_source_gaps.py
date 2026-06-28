#!/usr/bin/env python3
"""Classify source-backed gaps on static Word Atlas entries.

This is a DB-free audit over the release-hydrated Atlas manifest. It gives
thin pages an explicit gap bucket instead of treating absent sections as vague
"awaiting source" work. Future manifest enrichment can replace the default
``unclassified_source_gap`` rows with source-backed statuses.
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

from scripts.lexicon.manifest_io import load_manifest

SOURCE_BACKED_SECTIONS = (
    "meaning",
    "etymology",
    "morphology",
    "synonyms_antonyms",
    "idioms",
    "literary_attestation",
    "translation",
    "wikipedia",
)

ALLOWED_SOURCE_GAP_STATUSES = {
    "source_absent",
    "lookup_granularity_gap",
    "needs_review",
    "source_not_integrated",
    "not_applicable",
    "unclassified_source_gap",
    "invalid_source_gap_status",
}


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
    source = card.get("source")
    source_pill = card.get("source_pill")
    card_id = card.get("id")
    return (
        (isinstance(source, str) and "СУМ-11" in source)
        or (isinstance(source_pill, str) and "СУМ-11" in source_pill)
        or (isinstance(card_id, str) and "sum11" in card_id)
    )


def _rendered_definition_cards(enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    cards = enrichment.get("definition_cards")
    if not isinstance(cards, list):
        return []
    return [card for card in cards if isinstance(card, dict) and not _is_sum11_card(card)]


def rendered_sections(entry: dict[str, Any]) -> set[str]:
    """Return source-backed sections rendered by the current Atlas article."""
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
    if _nonempty_items(morphology.get("forms")) or isinstance(morphology.get("paradigm"), dict):
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

    return sections


def old_gate_enriched(entry: dict[str, Any]) -> bool:
    return bool(entry.get("enrichment"))


def is_lexeme_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("lemma")) and bool(entry.get("url_slug")) and entry.get("pos") != "grammar term"


def _entry_cefr(entry: dict[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        cefr = enrichment.get("cefr")
        if isinstance(cefr, dict) and _nonempty_string(cefr.get("level")):
            return str(cefr["level"]).upper()
    return None


def _declared_gap_payloads(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    enrichment = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}
    for container in (entry.get("source_gaps"), enrichment.get("source_gaps")):
        if isinstance(container, list):
            for item in container:
                if isinstance(item, dict) and _nonempty_string(item.get("section")):
                    payloads[str(item["section"])] = item
        elif isinstance(container, dict):
            for section, value in container.items():
                if isinstance(value, str):
                    payloads[str(section)] = {"section": str(section), "status": value}
                elif isinstance(value, dict):
                    payloads[str(section)] = {"section": str(section), **value}
    return payloads


def _gap_status(payload: dict[str, Any] | None) -> tuple[str, str | None, str | None]:
    if payload is None:
        return "unclassified_source_gap", None, None
    raw_status = payload.get("status") or payload.get("classification") or payload.get("class")
    status = str(raw_status).strip() if raw_status is not None else ""
    source = str(payload["source"]).strip() if _nonempty_string(payload.get("source")) else None
    note = str(payload["note"]).strip() if _nonempty_string(payload.get("note")) else None
    if status in ALLOWED_SOURCE_GAP_STATUSES:
        return status, source, note
    return "invalid_source_gap_status", source, note or f"invalid status: {status or '<missing>'}"


def _gap_row(
    entry: dict[str, Any],
    *,
    section: str,
    status: str,
    source: str | None,
    note: str | None,
    rich_section_count: int,
) -> dict[str, Any]:
    return {
        "lemma": entry.get("lemma"),
        "url_slug": entry.get("url_slug"),
        "pos": entry.get("pos"),
        "cefr": _entry_cefr(entry) or "unknown",
        "primary_source": entry.get("primary_source"),
        "rich_section_count": rich_section_count,
        "section": section,
        "status": status,
        "source": source,
        "note": note,
    }


def classify_manifest(
    manifest: dict[str, Any],
    *,
    min_rich_sections: int = 5,
    sample_limit: int = 25,
) -> dict[str, Any]:
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
    checked = [
        entry
        for entry in entries
        if is_lexeme_entry(entry) and old_gate_enriched(entry)
    ]
    rows: list[dict[str, Any]] = []

    for entry in checked:
        present = rendered_sections(entry)
        if len(present) >= min_rich_sections:
            continue
        declared = _declared_gap_payloads(entry)
        for section in SOURCE_BACKED_SECTIONS:
            if section in present:
                continue
            status, source, note = _gap_status(declared.get(section))
            if status == "not_applicable":
                continue
            rows.append(
                _gap_row(
                    entry,
                    section=section,
                    status=status,
                    source=source,
                    note=note,
                    rich_section_count=len(present),
                )
            )

    unclassified = [row for row in rows if row["status"] == "unclassified_source_gap"]
    unclassified_entries = {(row["lemma"], row["url_slug"]) for row in unclassified}
    return {
        "total_entries": len(entries),
        "checked_entries": len(checked),
        "thin_entries": len({(row["lemma"], row["url_slug"]) for row in rows}),
        "source_gap_rows": len(rows),
        "unclassified_source_gap_rows": len(unclassified),
        "unclassified_source_gap_entries": len(unclassified_entries),
        "by_status": dict(Counter(str(row["status"]) for row in rows).most_common()),
        "by_section": dict(Counter(str(row["section"]) for row in rows).most_common()),
        "by_primary_source": dict(Counter(str(row["primary_source"] or "unknown") for row in rows).most_common()),
        "samples": rows[:sample_limit],
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print(
        "Atlas source-gap classification audit: "
        f"{summary['source_gap_rows']} source-backed gaps across "
        f"{summary['thin_entries']} thin entries."
    )
    print(
        "Unclassified source gaps: "
        f"{summary['unclassified_source_gap_rows']} rows across "
        f"{summary['unclassified_source_gap_entries']} entries."
    )
    print("By status:")
    for status, count in summary["by_status"].items():
        print(f"  {status}: {count}")
    print("By section:")
    for section, count in summary["by_section"].items():
        print(f"  {section}: {count}")
    print("Samples:")
    for row in summary["samples"][:5]:
        print(
            "  "
            f"{row['lemma']} slug={row['url_slug']} section={row['section']} "
            f"status={row['status']} source={row['source'] or ''}"
        )


def _print_tsv(summary: dict[str, Any]) -> None:
    print("lemma\turl_slug\tpos\tcefr\tsection\tstatus\tsource\tnote\tprimary_source")
    for row in summary["samples"]:
        print(
            "\t".join(
                [
                    str(row["lemma"] or ""),
                    str(row["url_slug"] or ""),
                    str(row["pos"] or ""),
                    str(row["cefr"] or ""),
                    str(row["section"] or ""),
                    str(row["status"] or ""),
                    str(row["source"] or ""),
                    str(row["note"] or ""),
                    str(row["primary_source"] or ""),
                ]
            )
        )


def _max_failures(summary: dict[str, Any], max_unclassified: int | None) -> list[str]:
    if max_unclassified is None:
        return []
    if max_unclassified < 0:
        return [f"max unclassified source gaps must be non-negative, got {max_unclassified}"]
    count = int(summary["unclassified_source_gap_rows"])
    if count > max_unclassified:
        return [f"unclassified_source_gap_rows: {count} exceeds max {max_unclassified}"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read manifest path directly instead of hydrating the canonical release asset.",
    )
    parser.add_argument("--min-rich-sections", type=int, default=5)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--format", choices=("summary", "json", "tsv"), default="summary")
    parser.add_argument("--fail-on-unclassified", action="store_true")
    parser.add_argument("--max-unclassified-source-gaps", type=int, default=None)
    args = parser.parse_args(argv)

    manifest = _read_local_manifest(args.manifest) if args.local else load_manifest(args.manifest)
    summary = classify_manifest(
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

    failures = _max_failures(summary, args.max_unclassified_source_gaps)
    if args.fail_on_unclassified and summary["unclassified_source_gap_rows"]:
        failures.append("--fail-on-unclassified matched at least one unclassified source gap")
    if failures:
        print("Atlas source-gap classification gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
