#!/usr/bin/env python3
"""Apply approved #5133 learner-English anchors from a curation worksheet.

The worksheet is deliberately the review artifact.  This applier only adds a
translation where a learner-facing English anchor is still absent; it never
replaces a published gloss or translation.
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
    _load_slovnyk_cache_file,
    _slovnyk_cache_path,
)
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, build_fingerprint, write_fingerprint
from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, write_manifest

DEFAULT_WORKSHEET = PROJECT_ROOT / "data" / "lexicon" / "anchor_curation_worksheet.yaml"
ANCHOR_SOURCE = "anchor_curation_worksheet (#5133)"
APPROVED_CONFIDENCES = frozenset({"high", "medium"})


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
        if _entry_has_learner_english_anchor(entry):
            skipped_existing.append(lemma)
            continue
        _set_anchor(entry, anchor.strip())
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
    cached_fills = _apply_cached_slovnyk_anchors(manifest)

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--write", action="store_true", help="Write the manifest and fingerprint sidecar.")
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


def _set_anchor(entry: dict[str, Any], anchor: str) -> None:
    enrichment = entry.setdefault("enrichment", {})
    if not isinstance(enrichment, dict):
        raise ValueError(f"entry enrichment must be an object: {entry.get('lemma')}")
    enrichment["translation"] = {"en": [anchor], "source": ANCHOR_SOURCE}
    sources = enrichment.get("sources")
    source_set = {source for source in sources if isinstance(source, str)} if isinstance(sources, list) else set()
    source_set.add(ANCHOR_SOURCE)
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
        cache = _load_slovnyk_cache_file(_slovnyk_cache_path(lemma))
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
