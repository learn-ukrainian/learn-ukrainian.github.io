#!/usr/bin/env python3
"""Apply approved learner-English anchors from a curation worksheet.

The worksheet is deliberately the review artifact.  Its metadata selects an
allowlisted translation source, and this applier only adds a translation where
one is still absent; it never replaces a published gloss or translation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.enrich_manifest import (
    _entry_has_learner_english_anchor,
    _fill_learner_english_anchor_from_slovnyk_cache,
    _load_current_slovnyk_cache_file,
    _slovnyk_cache_path,
)
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, build_fingerprint, write_fingerprint
from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, write_manifest

DEFAULT_WORKSHEET = PROJECT_ROOT / "data" / "lexicon" / "anchor_curation_worksheet.yaml"
ANCHOR_SOURCE = "anchor_curation_worksheet (#5133)"
AGY_EN_SOURCE = "agy_en_proposal"
AGY_EN_WORKSHEET_LABEL = "agy_en_proposal (Gemini; not a dictionary)"
APPROVED_CONFIDENCES = frozenset({"high", "medium"})
WORKSHEET_SOURCE_KEYS: dict[str, str] = {
    ANCHOR_SOURCE: ANCHOR_SOURCE,
    AGY_EN_SOURCE: AGY_EN_SOURCE,
    AGY_EN_WORKSHEET_LABEL: AGY_EN_SOURCE,
}


@dataclass(frozen=True)
class ApplyResult:
    cached_fills: tuple[str, ...]
    approved: int
    applied: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    skipped_null: int
    skipped_unapproved: int
    manifest_written: bool
    fingerprint_written: bool


def apply_anchor_worksheet(
    manifest: dict[str, Any], worksheet: Mapping[str, Any]
) -> ApplyResult:
    """Add approved worksheet anchors to entries that lack any English anchor."""
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")

    index = _manifest_index(entries)
    source = _worksheet_source(worksheet)
    approved = 0
    applied: list[str] = []
    skipped_existing: list[str] = []
    skipped_null = 0
    skipped_unapproved = 0

    for record in _records(worksheet):
        anchor = record.get("proposed_anchor")
        if anchor is None:
            skipped_null += 1
            continue
        if not isinstance(anchor, str) or not anchor.strip():
            skipped_unapproved += 1
            continue
        if not _record_is_approved(record):
            skipped_unapproved += 1
            continue

        lemma = _required_text(record, "lemma")
        url_slug = _required_text(record, "url_slug")
        entry = index.get((lemma, url_slug))
        if entry is None:
            raise ValueError(f"worksheet entry is absent from manifest: {lemma} ({url_slug})")
        approved += 1
        if _entry_has_learner_english_anchor(entry) or _entry_has_existing_translation(entry):
            skipped_existing.append(lemma)
            continue
        _set_anchor(entry, anchor.strip(), source)
        applied.append(lemma)

    return ApplyResult(
        cached_fills=(),
        approved=approved,
        applied=tuple(applied),
        skipped_existing=tuple(skipped_existing),
        skipped_null=skipped_null,
        skipped_unapproved=skipped_unapproved,
        manifest_written=False,
        fingerprint_written=False,
    )


def apply_from_paths(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    worksheet_path: Path = DEFAULT_WORKSHEET,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    write: bool = False,
) -> ApplyResult:
    """Apply the worksheet, optionally writing canonical manifest artifacts."""
    manifest_path = _repo_path(manifest_path)
    worksheet_path = _repo_path(worksheet_path)
    fingerprint_path = _repo_path(fingerprint_path)
    manifest = _load_json_object(manifest_path)
    worksheet = _load_yaml_object(worksheet_path)
    result = apply_anchor_worksheet(manifest, worksheet)
    cached_fills = () if _worksheet_source(worksheet) == AGY_EN_SOURCE else _apply_cached_slovnyk_anchors(manifest)

    result = ApplyResult(**{**result.__dict__, "cached_fills": cached_fills})
    if not write or not (result.applied or result.cached_fills):
        return result

    fingerprint = build_fingerprint(PROJECT_ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint["schema_version"],
        "fingerprint": fingerprint["fingerprint"],
    }
    write_manifest(manifest_path, manifest)
    write_fingerprint(fingerprint_path, root=PROJECT_ROOT)
    return ApplyResult(
        **{**result.__dict__, "manifest_written": True, "fingerprint_written": True}
    )


def format_result(result: ApplyResult) -> str:
    """Format an auditable, stable command-line summary."""
    return "\n".join(
        (
            "Anchor worksheet application",
            f"Cached slovnyk anchors applied: {len(result.cached_fills)}",
            f"Approved records: {result.approved}",
            f"Anchors applied: {len(result.applied)}",
            f"Skipped existing anchors: {len(result.skipped_existing)}",
            f"Skipped null proposals: {result.skipped_null}",
            f"Skipped unapproved proposals: {result.skipped_unapproved}",
            f"Manifest written: {str(result.manifest_written).lower()}",
            f"Fingerprint written: {str(result.fingerprint_written).lower()}",
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply approved learner-English anchors from a YAML worksheet.\n"
            "Use for a bounded dry-run or explicit write; do not use it to hydrate the live manifest implicitly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/lexicon/apply_anchor_worksheet.py --worksheet data/lexicon/agy_en_slice51_worksheet.yaml
  .venv/bin/python scripts/lexicon/apply_anchor_worksheet.py --worksheet data/lexicon/agy_en_slice51_worksheet.yaml --manifest /tmp/manifest.json

Outputs:
  Dry-run prints an auditable summary and keeps all changes in memory. --write updates the manifest and fingerprint sidecar.
Exit codes:
  0 means the worksheet was validated and processed; 1 or higher means loading or application failed.
Related: data/lexicon/anchor_curation_worksheet.yaml and issue #6876.
""",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Manifest JSON to inspect or write (default: %(default)s).",
    )
    parser.add_argument(
        "--worksheet",
        type=Path,
        default=DEFAULT_WORKSHEET,
        help="Approved worksheet YAML to apply (default: %(default)s).",
    )
    parser.add_argument(
        "--fingerprint",
        type=Path,
        default=DEFAULT_FINGERPRINT,
        help="Fingerprint sidecar written with --write (default: %(default)s).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist applied anchors and the fingerprint sidecar; omit for an in-memory dry-run (default).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = apply_from_paths(
        manifest_path=args.manifest,
        worksheet_path=args.worksheet,
        fingerprint_path=args.fingerprint,
        write=args.write,
    )
    print(format_result(result))
    return 0


def _records(worksheet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = worksheet.get("records")
    if not isinstance(records, list):
        raise ValueError("worksheet records must be a list")
    return [record for record in records if isinstance(record, Mapping)]


def _worksheet_source(worksheet: Mapping[str, Any]) -> str:
    """Resolve a worksheet's source key through the explicit source allowlist."""
    meta = worksheet.get("meta")
    if meta is None:
        return ANCHOR_SOURCE
    if not isinstance(meta, Mapping):
        raise ValueError("worksheet meta must be an object")
    label = meta.get("source_label_if_applied")
    if label is None:
        return ANCHOR_SOURCE
    if not isinstance(label, str) or not label.strip():
        raise ValueError("worksheet meta.source_label_if_applied must be a non-empty string")
    try:
        return WORKSHEET_SOURCE_KEYS[label.strip()]
    except KeyError as exc:
        raise ValueError(f"unsupported worksheet source label: {label}") from exc


def _record_is_approved(record: Mapping[str, Any]) -> bool:
    """Accept explicit approval, adjudication, or the Stage 1 confidence decision."""
    if str(record.get("status") or "").strip().lower() == "approved":
        return True
    if isinstance(record.get("verified_by"), str) and record["verified_by"].strip():
        return True
    return str(record.get("confidence") or "").strip().lower() in APPROVED_CONFIDENCES


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"approved worksheet record lacks {field}")
    return value.strip()


def _manifest_index(entries: Sequence[Any]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lemma = entry.get("lemma")
        url_slug = entry.get("url_slug")
        if isinstance(lemma, str) and isinstance(url_slug, str):
            index[(lemma, url_slug)] = entry
    return index


def _entry_has_existing_translation(entry: Mapping[str, Any]) -> bool:
    """Return whether an entry already carries a non-empty translation list."""
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return False
    translation = enrichment.get("translation")
    if not isinstance(translation, Mapping):
        return False
    terms = translation.get("en")
    return isinstance(terms, list) and any(isinstance(term, str) and term.strip() for term in terms)


def _set_anchor(entry: dict[str, Any], anchor: str, source: str = ANCHOR_SOURCE) -> None:
    enrichment = entry.setdefault("enrichment", {})
    if not isinstance(enrichment, dict):
        raise ValueError(f"entry enrichment must be an object: {entry.get('lemma')}")
    enrichment["translation"] = {"en": [anchor], "source": source}
    sources = enrichment.get("sources")
    source_set = {source for source in sources if isinstance(source, str)} if isinstance(sources, list) else set()
    source_set.add(source)
    enrichment["sources"] = sorted(source_set)


def _apply_cached_slovnyk_anchors(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Materialize the offline-safe #5132 cache fill alongside worksheet anchors.

    Stage 1 deliberately simulated these 38 cache-backed additions while
    leaving the manifest untouched.  This calls the exact #5132 helper with
    read-only cache rows, so it cannot fetch or fabricate a gloss.
    """
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    filled: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lemma = entry.get("lemma")
        if not isinstance(lemma, str) or not lemma.strip():
            continue
        cache = _load_current_slovnyk_cache_file(_slovnyk_cache_path(lemma))
        if _fill_learner_english_anchor_from_slovnyk_cache(entry, lemma, cache):
            filled.append(lemma)
    return tuple(filled)


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest must contain an object: {path}")
    return payload


def _load_yaml_object(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"worksheet must contain an object: {path}")
    return payload


def _repo_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
