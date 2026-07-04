#!/usr/bin/env python3
"""Count public Atlas entries against the finalized entry model.

This audit is aggregate-only. It reads the current manifest, separates reviewed
article entries from legacy alias/form records, and reports counts by the
entry-model buckets defined in docs/runbooks/word-atlas-entry-model.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.manifest_io import load_manifest

WORKFLOW_ID = "atlas_entry_model_census.v1"
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

ENTRY_TYPES = (
    "lemma",
    "expression",
    "phraseologism",
    "proverb",
    "multiword_term",
    "proper_name",
)
NON_ENTRY_TYPES = (
    "form_alias",
    "grammar_term",
    "noise_rejected",
    "invalid",
)
EXPLICIT_REJECTED_TYPES = {"noise", "rejected", "noise_rejected"}
WORD_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-]+")
WHITESPACE_RE = re.compile(r"\s")
DELIMITED_RE = re.compile(r"\.\.\.|/")


@dataclass(frozen=True)
class EntryClassification:
    """One aggregate-safe classification result."""

    bucket: str
    counts_as_entry: bool
    source: str
    warning: str | None = None


def _is_default_manifest(path: Path) -> bool:
    return path.resolve() == DEFAULT_MANIFEST.resolve()


def _read_manifest(path: Path) -> dict[str, Any]:
    if _is_default_manifest(path):
        return load_manifest(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _normalize_label(value: object) -> str:
    text = strip_acute_stress(str(value or "")).strip().casefold()
    text = text.replace("-", "_").replace(" ", "_").replace("/", "_")
    return re.sub(r"_+", "_", text).strip("_")


def _normalize_entry_type(value: object) -> str | None:
    label = _normalize_label(value)
    aliases = {
        "idiom": "phraseologism",
        "idiom_phrase": "phraseologism",
        "phraseological_unit": "phraseologism",
        "fixed_expression": "expression",
        "set_phrase": "expression",
        "formula": "expression",
        "saying": "proverb",
        "proper_noun": "proper_name",
        "multiword": "multiword_term",
        "multi_word_term": "multiword_term",
        "term": "multiword_term",
    }
    if label in ENTRY_TYPES or label in NON_ENTRY_TYPES:
        return label
    if label in EXPLICIT_REJECTED_TYPES:
        return "noise_rejected"
    return aliases.get(label)


def _base_pos(entry: Mapping[str, Any]) -> str:
    return _normalize_label(entry.get("pos")).split(":", 1)[0]


def _has_multiword_shape(value: str) -> bool:
    return bool(WHITESPACE_RE.search(value)) or bool(DELIMITED_RE.search(value))


def _is_genuine_multiword(value: str) -> bool:
    return len(WORD_TOKEN_RE.findall(value)) >= 2


def _legacy_multiword_type(entry: Mapping[str, Any], lemma: str) -> EntryClassification:
    pos = _base_pos(entry)
    if "proverb" in pos or "pryslivia" in pos:
        return EntryClassification("proverb", True, "legacy_pos")
    if "phraseologism" in pos or "idiom" in pos:
        return EntryClassification("phraseologism", True, "legacy_pos")
    if "expression" in pos or "formula" in pos or "greeting" in pos:
        return EntryClassification("expression", True, "legacy_pos")
    if "proper_noun" in pos or "proper_name" in pos:
        return EntryClassification("proper_name", True, "legacy_pos")
    if _is_genuine_multiword(lemma):
        return EntryClassification(
            "multiword_term",
            True,
            "legacy_shape",
            "legacy_multiword_defaulted_to_multiword_term",
        )
    return EntryClassification(
        "invalid",
        False,
        "legacy_shape",
        "multiword_shape_without_two_tokens",
    )


def classify_entry(entry: Mapping[str, Any]) -> EntryClassification:
    """Classify one manifest record without exposing its text in reports."""

    lemma = str(entry.get("lemma") or "").strip()
    slug = str(entry.get("url_slug") or "").strip()
    if not lemma or not slug:
        return EntryClassification("invalid", False, "structural", "missing_lemma_or_url_slug")

    if entry.get("form_of"):
        return EntryClassification("form_alias", False, "form_of")

    explicit_type = _normalize_entry_type(entry.get("entry_type"))
    if explicit_type in ENTRY_TYPES:
        return EntryClassification(explicit_type, True, "entry_type")
    if explicit_type in NON_ENTRY_TYPES:
        return EntryClassification(explicit_type, False, "entry_type")
    if entry.get("entry_type") is not None:
        return EntryClassification("invalid", False, "entry_type", "unknown_entry_type")

    pos = _base_pos(entry)
    if pos == "grammar_term":
        return EntryClassification("grammar_term", False, "legacy_pos")
    if pos in {"proper_noun", "proper_name"}:
        return EntryClassification("proper_name", True, "legacy_pos")
    if _has_multiword_shape(lemma):
        return _legacy_multiword_type(entry, lemma)
    return EntryClassification("lemma", True, "legacy_shape")


def build_entry_model_census(manifest: Mapping[str, Any]) -> dict[str, Any]:
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, Mapping)]
    reviewed_counts: Counter[str] = Counter({entry_type: 0 for entry_type in ENTRY_TYPES})
    non_entry_counts: Counter[str] = Counter({entry_type: 0 for entry_type in NON_ENTRY_TYPES})
    classification_sources: Counter[str] = Counter()
    warnings: Counter[str] = Counter()

    for entry in entries:
        classification = classify_entry(entry)
        classification_sources[classification.source] += 1
        if classification.warning:
            warnings[classification.warning] += 1
        if classification.counts_as_entry:
            reviewed_counts[classification.bucket] += 1
        else:
            non_entry_counts[classification.bucket] += 1

    return {
        "workflow": WORKFLOW_ID,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "production_outputs_updated": [],
        "safety": {
            "public_payload_includes_raw_text": False,
            "public_payload_includes_candidate_lemmas": False,
            "public_payload_includes_private_paths": False,
            "manifest_content_mutated": False,
            "manifest_hydrated_from_release": False,
        },
        "manifest_records": len(entries),
        "total_reviewed_entries": sum(reviewed_counts.values()),
        "reviewed_entries_by_type": dict(reviewed_counts),
        "non_entry_records": dict(non_entry_counts),
        "classification_sources": dict(classification_sources),
        "warnings": dict(warnings),
        "notes": [
            "Counts are aggregate-only and do not expose entry text.",
            "Legacy manifests without entry_type are classified by conservative shape and POS heuristics.",
            "form_of records are treated as alias/form records and excluded from reviewed entry totals.",
        ],
    }


def format_markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Word Atlas Entry Model Census",
        "",
        f"- workflow: `{payload['workflow']}`",
        f"- generated_at: `{payload['generated_at']}`",
        "- production_outputs_updated: []",
        "- raw_text_included: false",
        "- candidate_lemmas_included: false",
        "- private_paths_included: false",
        f"- manifest_records: {payload['manifest_records']}",
        f"- total_reviewed_entries: {payload['total_reviewed_entries']}",
        "",
        "## Reviewed Entries By Type",
        "",
        "| entry type | count |",
        "| --- | ---: |",
    ]
    for entry_type, count in payload["reviewed_entries_by_type"].items():
        lines.append(f"| `{entry_type}` | {count} |")

    lines.extend(
        [
            "",
            "## Non-Entry Records",
            "",
            "| record bucket | count |",
            "| --- | ---: |",
        ]
    )
    for bucket, count in payload["non_entry_records"].items():
        lines.append(f"| `{bucket}` | {count} |")

    lines.extend(
        [
            "",
            "## Classification Sources",
            "",
            "| source | records |",
            "| --- | ---: |",
        ]
    )
    for source, count in payload["classification_sources"].items():
        lines.append(f"| `{source}` | {count} |")

    if payload["warnings"]:
        lines.extend(["", "## Warnings", "", "| warning | records |", "| --- | ---: |"])
        for warning, count in payload["warnings"].items():
            lines.append(f"| `{warning}` | {count} |")

    lines.extend(["", "## Notes", ""])
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Count Atlas manifest records by finalized entry-model bucket.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Atlas manifest JSON path.")
    parser.add_argument("--json-out", type=Path, help="Write aggregate JSON report.")
    parser.add_argument("--markdown-out", type=Path, help="Write aggregate Markdown report.")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text", help="Print format.")
    parser.add_argument(
        "--fail-on-legacy-heuristic",
        action="store_true",
        help="Exit non-zero if any record had to be classified without explicit entry_type.",
    )
    return parser


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest if args.manifest.is_absolute() else PROJECT_ROOT / args.manifest
    manifest_existed = manifest_path.exists()
    payload = build_entry_model_census(_read_manifest(manifest_path))
    payload["safety"]["manifest_hydrated_from_release"] = (
        _is_default_manifest(manifest_path) and not manifest_existed and manifest_path.exists()
    )

    if args.json_out:
        out = args.json_out if args.json_out.is_absolute() else PROJECT_ROOT / args.json_out
        _write_text(out, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if args.markdown_out:
        out = args.markdown_out if args.markdown_out.is_absolute() else PROJECT_ROOT / args.markdown_out
        _write_text(out, format_markdown_report(payload) + "\n")

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(format_markdown_report(payload))
    else:
        print(
            "Atlas entry-model census: "
            f"{payload['total_reviewed_entries']} reviewed entries across "
            f"{payload['manifest_records']} manifest records."
        )
        print("reviewed_entries_by_type=" + json.dumps(payload["reviewed_entries_by_type"], sort_keys=True))
        print("non_entry_records=" + json.dumps(payload["non_entry_records"], sort_keys=True))

    if args.fail_on_legacy_heuristic:
        legacy_count = sum(
            count
            for source, count in payload["classification_sources"].items()
            if source.startswith("legacy_")
        )
        if legacy_count:
            print(f"--fail-on-legacy-heuristic matched {legacy_count} records")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
