#!/usr/bin/env python3
"""Reversibly park structurally thin Atlas lemma articles.

The Atlas richness audit remains the sole authority for thinness.  This tool
removes only audit-classified thin ``lemma_article`` entries, preserving the
original entry payload and position in a parked artifact so the operation can
be reversed after new source material makes those articles worth publishing.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.audit_atlas_poc_richness import audit_manifest
from scripts.lexicon.backfill_course_usage import (
    _fingerprint_path_for,
    _refresh_manifest_fingerprint,
)
from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, load_manifest, write_manifest

DEFAULT_PARKED_DIR = PROJECT_ROOT / "data" / "lexicon" / "parked"
DEFAULT_PARKED_OUT = DEFAULT_PARKED_DIR / f"parked-thin-entries-{datetime.now(UTC).date().isoformat()}.json"
PARKED_SCHEMA_VERSION = 1
_THIN_LEMMA_SAMPLE = "poc_thin_lemma_article"
_ENRICHED_STAT_KEYS = ("enriched", "enriched_total", "enriched_count")


@dataclass(frozen=True)
class ParkResult:
    """Outcome of a park or restore operation."""

    mode: str
    parked_count: int
    restored_count: int
    guard_excluded: dict[str, int]
    limit_excluded: int
    pre_park_poc_thin_pages: int | None
    projected_poc_thin_pages: int
    projected_form_stub_broken: int
    manifest_written: bool
    parked_artifact_written: bool
    fingerprint_written: bool
    dry_run: bool

    def json_summary(self) -> dict[str, object]:
        """Return the stable CLI report payload."""
        return {
            "mode": self.mode,
            "dry_run": self.dry_run,
            "parked_count": self.parked_count,
            "restored_count": self.restored_count,
            "guard_excluded": self.guard_excluded,
            "limit_excluded": self.limit_excluded,
            "pre_park_poc_thin_pages": self.pre_park_poc_thin_pages,
            "projected_poc_thin_pages": self.projected_poc_thin_pages,
            "projected_form_stub_broken": self.projected_form_stub_broken,
            "manifest_written": self.manifest_written,
            "parked_artifact_written": self.parked_artifact_written,
            "fingerprint_written": self.fingerprint_written,
        }


def park_thin_entries(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    parked_out: Path = DEFAULT_PARKED_OUT,
    write: bool = False,
    limit: int | None = None,
) -> ParkResult:
    """Park audit-classified thin lemma articles without changing audit rules."""
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative")

    manifest_path = _resolve_path(manifest_path)
    parked_out = _resolve_path(parked_out)
    manifest = load_manifest(manifest_path)
    entries = _manifest_entries(manifest, manifest_path)
    pre_park_audit = _audit_all_thin_rows(manifest, entries)
    candidate_indices = _thin_lemma_candidate_indices(entries, pre_park_audit)

    non_candidates = [entry for index, entry in enumerate(entries) if index not in candidate_indices]
    protected_indices = {
        index
        for index in candidate_indices
        if _is_form_target_of_any(entry=entries[index], remaining_entries=non_candidates)
    }
    eligible_indices = [index for index in candidate_indices if index not in protected_indices]
    selected_indices = eligible_indices if limit is None else eligible_indices[:limit]

    prospective_manifest = copy.deepcopy(manifest)
    prospective_manifest["entries"] = [
        entry for index, entry in enumerate(entries) if index not in set(selected_indices)
    ]
    _refresh_manifest_stats(prospective_manifest)
    projected_audit = _audit_all_thin_rows(prospective_manifest, _manifest_entries(prospective_manifest, manifest_path))
    _refuse_broken_form_stubs(projected_audit)

    result = ParkResult(
        mode="park",
        parked_count=len(selected_indices),
        restored_count=0,
        guard_excluded={"form_of_target": len(protected_indices)},
        limit_excluded=len(eligible_indices) - len(selected_indices),
        pre_park_poc_thin_pages=int(pre_park_audit["poc_thin_pages"]),
        projected_poc_thin_pages=int(projected_audit["poc_thin_pages"]),
        projected_form_stub_broken=int(projected_audit["form_stub_broken"]),
        manifest_written=False,
        parked_artifact_written=False,
        fingerprint_written=False,
        dry_run=not write,
    )
    if not write or not selected_indices:
        return result
    if parked_out.exists():
        raise FileExistsError(f"Refusing to overwrite existing parked artifact: {parked_out}")

    parked_payload = _parked_payload(
        manifest_path=manifest_path,
        pre_park_audit=pre_park_audit,
        selected_indices=selected_indices,
        entries=entries,
    )
    # The artifact is the recovery point.  It must be durable before the live
    # manifest can shrink, even if a later manifest write fails.
    write_manifest(parked_out, parked_payload)
    fingerprint_path = _fingerprint_path_for(manifest_path)
    _refresh_manifest_fingerprint(prospective_manifest, fingerprint_path)
    write_manifest(manifest_path, prospective_manifest)
    return ParkResult(
        **{
            **result.__dict__,
            "manifest_written": True,
            "parked_artifact_written": True,
            "fingerprint_written": True,
        }
    )


def restore_parked_entries(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    parked_file: Path,
    write: bool = False,
) -> ParkResult:
    """Restore verbatim entries from a parked artifact at their original indices."""
    manifest_path = _resolve_path(manifest_path)
    parked_file = _resolve_path(parked_file)
    manifest = load_manifest(manifest_path)
    entries = _manifest_entries(manifest, manifest_path)
    artifact = _load_parked_artifact(parked_file)
    records = _parked_records(artifact, parked_file)
    expected_thin_count = _artifact_pre_park_thin_count(artifact, parked_file)
    _ensure_restore_has_no_collisions(entries, records, parked_file)

    prospective_manifest = copy.deepcopy(manifest)
    restored_entries = list(entries)
    for index, entry in records:
        if index > len(restored_entries):
            raise ValueError(f"Parked index {index} is outside the current manifest: {parked_file}")
        restored_entries.insert(index, copy.deepcopy(entry))
    prospective_manifest["entries"] = restored_entries
    _refresh_manifest_stats(prospective_manifest)
    projected_audit = _audit_all_thin_rows(
        prospective_manifest,
        _manifest_entries(prospective_manifest, manifest_path),
    )
    _refuse_broken_form_stubs(projected_audit)
    projected_thin_count = int(projected_audit["poc_thin_pages"])
    if projected_thin_count != expected_thin_count:
        raise ValueError(
            "Refusing restore because its re-audited thin count does not match the parked artifact: "
            f"expected {expected_thin_count}, got {projected_thin_count}"
        )

    result = ParkResult(
        mode="restore",
        parked_count=0,
        restored_count=len(records),
        guard_excluded={"form_of_target": 0},
        limit_excluded=0,
        pre_park_poc_thin_pages=expected_thin_count,
        projected_poc_thin_pages=projected_thin_count,
        projected_form_stub_broken=int(projected_audit["form_stub_broken"]),
        manifest_written=False,
        parked_artifact_written=False,
        fingerprint_written=False,
        dry_run=not write,
    )
    if not write or not records:
        return result

    fingerprint_path = _fingerprint_path_for(manifest_path)
    _refresh_manifest_fingerprint(prospective_manifest, fingerprint_path)
    write_manifest(manifest_path, prospective_manifest)
    return ParkResult(
        **{
            **result.__dict__,
            "manifest_written": True,
            "fingerprint_written": True,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the park/restore command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--parked-out", type=Path, default=DEFAULT_PARKED_OUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Write the parked artifact and manifest mutation.")
    mode.add_argument("--dry-run", action="store_true", help="Report only (the default).")
    parser.add_argument("--restore", type=Path, help="Restore entries from this parked artifact.")
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum eligible entries to park, for a deliberate staged operation.",
    )
    parser.add_argument("--json", action="store_true", help="Print the machine-readable report.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a conventional process status."""
    args = build_parser().parse_args(argv)
    try:
        if args.restore is not None:
            if args.limit is not None:
                raise ValueError("--limit applies only to parking, not --restore")
            result = restore_parked_entries(
                manifest_path=args.manifest,
                parked_file=args.restore,
                write=args.write,
            )
        else:
            result = park_thin_entries(
                manifest_path=args.manifest,
                parked_out=args.parked_out,
                write=args.write,
                limit=args.limit,
            )
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.json_summary(), ensure_ascii=False, indent=2))
    else:
        _print_summary(result)
    return 0


def _manifest_entries(manifest: dict[str, Any], manifest_path: Path) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"Manifest entries must be a list of objects: {manifest_path}")
    return entries


def _audit_all_thin_rows(manifest: dict[str, Any], entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Run the audit with an exhaustive sample, never reconstructed local logic."""
    return audit_manifest(manifest, sample_limit=len(entries))


def _thin_lemma_candidate_indices(entries: Sequence[dict[str, Any]], audit: dict[str, Any]) -> list[int]:
    samples = audit.get("samples")
    rows = samples.get(_THIN_LEMMA_SAMPLE) if isinstance(samples, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError(f"Audit did not return the {_THIN_LEMMA_SAMPLE} sample")
    thin_by_class = audit.get("thin_by_class")
    expected_count = thin_by_class.get("lemma_article") if isinstance(thin_by_class, Mapping) else None
    if not isinstance(expected_count, int) or len(rows) != expected_count:
        raise ValueError("Audit sample was not exhaustive for thin lemma articles")

    indices_by_slug: dict[str, list[int]] = defaultdict(list)
    for index, entry in enumerate(entries):
        slug = _nonempty_string(entry.get("url_slug"))
        if slug is not None:
            indices_by_slug[slug].append(index)

    candidate_indices: list[int] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("Audit thin lemma sample contains a non-object row")
        slug = _nonempty_string(row.get("url_slug"))
        matches = indices_by_slug.get(slug, []) if slug is not None else []
        if len(matches) != 1:
            raise ValueError(f"Audit thin lemma row cannot be matched uniquely by url_slug: {slug!r}")
        candidate_indices.append(matches[0])
    return candidate_indices


def _is_form_target_of_any(*, entry: dict[str, Any], remaining_entries: Sequence[dict[str, Any]]) -> bool:
    entry_slug = _nonempty_string(entry.get("url_slug"))
    entry_lemma = _nonempty_string(entry.get("lemma"))
    for remaining in remaining_entries:
        form_of = remaining.get("form_of")
        if not isinstance(form_of, Mapping):
            continue
        target_slug = _nonempty_string(form_of.get("url_slug"))
        target_lemma = _nonempty_string(form_of.get("lemma"))
        if target_slug is not None and target_slug == entry_slug:
            return True
        if target_lemma is not None and target_lemma == entry_lemma:
            return True
    return False


def _refresh_manifest_stats(manifest: dict[str, Any]) -> None:
    """Maintain every existing entry-derived count, following promotion semantics."""
    entries = _manifest_entries(manifest, Path("<in-memory manifest>"))
    stats = manifest.setdefault("stats", {})
    if not isinstance(stats, dict):
        stats = {}
        manifest["stats"] = stats
    stats["lemmas_total"] = len(entries)
    if "entries_total" in stats:
        stats["entries_total"] = len(entries)
    if "form_of_count" in stats:
        stats["form_of_count"] = sum(1 for entry in entries if "form_of" in entry)
    if "from_built" in stats:
        stats["from_built"] = sum(
            1 for entry in entries if str(entry.get("primary_source") or "").startswith("built_vocabulary")
        )
    if "from_surzhyk_to_avoid" in stats:
        stats["from_surzhyk_to_avoid"] = sum(1 for entry in entries if entry.get("seed_group") == "surzhyk-to-avoid")
    if "from_heritage_status_seed" in stats:
        stats["from_heritage_status_seed"] = sum(
            1 for entry in entries if entry.get("seed_group") == "heritage-status-samples"
        )
    enriched_count = sum(1 for entry in entries if entry.get("enrichment"))
    for key in _ENRICHED_STAT_KEYS:
        if key in stats:
            stats[key] = enriched_count


def _parked_payload(
    *,
    manifest_path: Path,
    pre_park_audit: dict[str, Any],
    selected_indices: Sequence[int],
    entries: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": PARKED_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_manifest": _display_path(manifest_path),
        "pre_park_audit": {
            "poc_thin_pages": int(pre_park_audit["poc_thin_pages"]),
            "form_stub_broken": int(pre_park_audit["form_stub_broken"]),
        },
        "entries": [{"index": index, "entry": copy.deepcopy(entries[index])} for index in selected_indices],
    }


def _load_parked_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read parked artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid parked artifact JSON: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != PARKED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported parked artifact: {path}")
    return payload


def _parked_records(payload: dict[str, Any], path: Path) -> list[tuple[int, dict[str, Any]]]:
    raw_records = payload.get("entries")
    if not isinstance(raw_records, list):
        raise ValueError(f"Parked artifact entries must be a list: {path}")
    records: list[tuple[int, dict[str, Any]]] = []
    for raw_record in raw_records:
        if not isinstance(raw_record, Mapping):
            raise ValueError(f"Parked artifact entry record must be an object: {path}")
        index = raw_record.get("index")
        entry = raw_record.get("entry")
        if not isinstance(index, int) or index < 0 or not isinstance(entry, dict):
            raise ValueError(f"Parked artifact entry record is invalid: {path}")
        records.append((index, entry))
    if len({index for index, _entry in records}) != len(records):
        raise ValueError(f"Parked artifact has duplicate original indices: {path}")
    return sorted(records, key=lambda record: record[0])


def _artifact_pre_park_thin_count(payload: dict[str, Any], path: Path) -> int:
    audit = payload.get("pre_park_audit")
    count = audit.get("poc_thin_pages") if isinstance(audit, Mapping) else None
    if not isinstance(count, int) or count < 0:
        raise ValueError(f"Parked artifact has no valid pre-park thin count: {path}")
    return count


def _ensure_restore_has_no_collisions(
    entries: Sequence[dict[str, Any]],
    records: Sequence[tuple[int, dict[str, Any]]],
    parked_file: Path,
) -> None:
    existing_slugs = {_nonempty_string(entry.get("url_slug")) for entry in entries}
    existing_lemmas = {_nonempty_string(entry.get("lemma")) for entry in entries}
    for _index, entry in records:
        slug = _nonempty_string(entry.get("url_slug"))
        lemma = _nonempty_string(entry.get("lemma"))
        if slug is not None and slug in existing_slugs:
            raise ValueError(f"Restore slug already exists in manifest: {slug!r} ({parked_file})")
        if lemma is not None and lemma in existing_lemmas:
            raise ValueError(f"Restore lemma already exists in manifest: {lemma!r} ({parked_file})")
        if slug is not None:
            existing_slugs.add(slug)
        if lemma is not None:
            existing_lemmas.add(lemma)


def _refuse_broken_form_stubs(audit: Mapping[str, Any]) -> None:
    broken_count = audit.get("form_stub_broken")
    if not isinstance(broken_count, int):
        raise ValueError("Audit did not return a valid form_stub_broken count")
    if broken_count > 0:
        raise ValueError(f"Refusing to write a manifest with {broken_count} broken form stubs")


def _nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _resolve_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _print_summary(result: ParkResult) -> None:
    print(f"Mode: {result.mode}")
    print(f"Parked: {result.parked_count}")
    print(f"Restored: {result.restored_count}")
    print(f"Guard-excluded form_of targets: {result.guard_excluded['form_of_target']}")
    print(f"Limit-excluded: {result.limit_excluded}")
    print(f"Projected POC-thin pages: {result.projected_poc_thin_pages}")
    print(f"Projected broken form stubs: {result.projected_form_stub_broken}")
    print(f"Manifest written: {str(result.manifest_written).lower()}")
    print(f"Parked artifact written: {str(result.parked_artifact_written).lower()}")


if __name__ == "__main__":
    raise SystemExit(main())
