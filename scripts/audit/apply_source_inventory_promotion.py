#!/usr/bin/env python3
"""Apply an approved source-inventory promotion plan to the live Atlas manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import apply_source_inventory_provenance as provenance_overlay
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon import promote_grow_candidates as promote
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, write_fingerprint

DEFAULT_PLAN = planner.DEFAULT_OUT
DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
WORKFLOW_ID = "source_inventory_approved_live_promotion.v1"
SelfCheck = Callable[[Path], int]
FingerprintWriter = Callable[[Path], Any]
_SAFE_INVENTORY_PREFIX = "data/lexicon/source-inventory/"
_PRIVATE_PROVENANCE_MARKERS = (
    "/users/",
    "\\users\\",
    "native-reviewer-lessons",
    ".docx",
    "alona",
    "альона",
    "алёна",
)


def apply_promotion_plan(
    manifest: dict[str, Any],
    plan: Mapping[str, Any],
    *,
    source_family: str | None = None,
    expected_additions: int | None = None,
    expected_skipped_existing: int | None = None,
) -> dict[str, Any]:
    """Insert approved plan additions into ``manifest`` and return a summary."""
    _validate_plan(plan)
    additions = _filter_by_source_family(_plan_rows(plan, "proposed_manifest_additions"), source_family)
    skipped_existing = _filter_by_source_family(_plan_rows(plan, "skipped_existing"), source_family)

    if expected_additions is not None and len(additions) != expected_additions:
        raise SourceInventoryError(
            f"expected {expected_additions} planned additions, found {len(additions)}"
        )
    if expected_skipped_existing is not None and len(skipped_existing) != expected_skipped_existing:
        raise SourceInventoryError(
            f"expected {expected_skipped_existing} skipped-existing rows, found {len(skipped_existing)}"
        )

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise SourceInventoryError("manifest entries must be list")
    manifest_entries = [entry for entry in entries if isinstance(entry, dict)]
    if len(manifest_entries) != len(entries):
        raise SourceInventoryError("manifest entries must all be mappings")

    existing_keys = {
        _lemma_key(str(entry["lemma"]))
        for entry in manifest_entries
        if isinstance(entry.get("lemma"), str) and entry["lemma"].strip()
    }
    sorted_keys = [
        _lemma_key(str(entry.get("lemma") or ""))
        for entry in manifest_entries
    ]

    promoted: list[dict[str, Any]] = []
    already_present: list[dict[str, Any]] = []

    for row in additions:
        manifest_entry = row.get("manifest_entry")
        if not isinstance(manifest_entry, Mapping):
            raise SourceInventoryError(f"{row.get('lemma')}: manifest_entry must be a mapping")
        entry = dict(manifest_entry)
        lemma = _clean_text(entry.get("lemma")) or _clean_text(row.get("lemma"))
        if not lemma:
            raise SourceInventoryError("planned addition missing lemma")
        entry["lemma"] = lemma
        _validate_privacy_safe_provenance(entry)
        key = _lemma_key(lemma)
        summary_row = {
            "lemma": lemma,
            "source_inventory_key": row.get("source_inventory_key"),
            "source_family": _source_family(row),
            "decision_file": row.get("decision_file"),
        }
        if key in existing_keys:
            already_present.append({**summary_row, "reason": "already_in_manifest"})
            continue
        promote._insert_manifest_entry(entries, sorted_keys, entry)
        existing_keys.add(key)
        promoted.append(summary_row)

    if promoted:
        promote._refresh_manifest_metadata(manifest)

    return {
        "workflow": WORKFLOW_ID,
        "source_family": source_family,
        "counts": {
            "planned_additions": len(additions),
            "promoted": len(promoted),
            "already_present": len(already_present),
            "skipped_existing": len(skipped_existing),
        },
        "promoted_entries": promoted,
        "already_present": already_present,
        "skipped_existing": skipped_existing,
        "existing_provenance_overlay": None,
        "production_outputs_updated": [],
    }


def apply_existing_provenance_overlay(
    manifest: dict[str, Any],
    result: dict[str, Any],
    candidate_index: Mapping[str, planner.CandidateMatch],
    approved_decisions: Sequence[planner.ApprovedDecision],
    *,
    source_family: str | None = None,
) -> dict[str, Any]:
    """Overlay approved provenance for rows already present in the manifest."""
    overlay_result = provenance_overlay.apply_existing_provenance_overlay(
        manifest,
        candidate_index,
        approved_decisions,
        source_family=source_family,
    )
    counts = overlay_result["counts"]
    if counts["missing_candidates"] or counts["missing_manifest_entries"]:
        raise SourceInventoryError(
            "existing provenance overlay incomplete: "
            f"missing_candidates={counts['missing_candidates']} "
            f"missing_manifest_entries={counts['missing_manifest_entries']}"
        )
    if counts["updated_entries"]:
        for row in overlay_result.get("updated_entries", []):
            lemma = row.get("manifest_lemma") or row.get("lemma")
            entry = _manifest_entry_for_lemma(manifest, str(lemma))
            if entry is not None:
                _validate_privacy_safe_provenance(entry)
        promote._refresh_manifest_metadata(manifest)

    result["existing_provenance_overlay"] = overlay_result
    result["counts"]["overlay_updated_entries"] = counts["updated_entries"]
    result["counts"]["overlay_added_provenance_refs"] = counts["added_provenance_refs"]
    return result


def write_manifest_if_changed(
    manifest: dict[str, Any],
    result: dict[str, Any],
    *,
    manifest_path: Path,
    fingerprint_path: Path,
    self_check: SelfCheck | None = None,
    fingerprint_writer: FingerprintWriter | None = None,
) -> dict[str, Any]:
    """Validate and write the mutated manifest when the result promoted rows."""
    if not _has_manifest_changes(result):
        return result
    self_check = self_check or promote.verify_prospective_manifest
    fingerprint_writer = fingerprint_writer or _write_fingerprint_sidecar
    promote._validate_before_write(manifest, manifest_path, self_check)
    promote._write_json_atomically(manifest_path, manifest)
    fingerprint_writer(fingerprint_path)
    result["production_outputs_updated"] = [
        _display_path(manifest_path),
        _display_path(fingerprint_path),
    ]
    return result


def format_report(result: Mapping[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Source Inventory Approved Live Promotion",
        "",
        f"- workflow: `{result['workflow']}`",
        f"- source_family: `{result.get('source_family') or 'all'}`",
        f"- planned_additions: {counts['planned_additions']}",
        f"- promoted: {counts['promoted']}",
        f"- already_present: {counts['already_present']}",
        f"- skipped_existing: {counts['skipped_existing']}",
        f"- overlay_updated_entries: {counts.get('overlay_updated_entries', 0)}",
        f"- overlay_added_provenance_refs: {counts.get('overlay_added_provenance_refs', 0)}",
        f"- production_outputs_updated: {result.get('production_outputs_updated', [])}",
    ]
    if result.get("promoted_entries"):
        lines.extend(["", "## Promoted Entries", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']})"
            for row in result["promoted_entries"]
        )
    if result.get("already_present"):
        lines.extend(["", "## Already Present", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row['reason']}"
            for row in result["already_present"]
        )
    if result.get("skipped_existing"):
        lines.extend(["", "## Existing Entries From Plan", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row.get('reason', 'already_in_manifest')}"
            for row in result["skipped_existing"]
        )
    overlay = result.get("existing_provenance_overlay")
    if isinstance(overlay, Mapping) and overlay.get("updated_entries"):
        lines.extend(["", "## Provenance Overlay Applied", ""])
        lines.extend(
            f"- `{row.get('lemma') or row.get('manifest_lemma')}` "
            f"({row.get('source_inventory_key')}): "
            f"+{row.get('added_provenance_refs')} provenance ref(s)"
            for row in overlay["updated_entries"]
        )
    return "\n".join(lines)


def _validate_plan(plan: Mapping[str, Any]) -> None:
    if plan.get("workflow") != planner.WORKFLOW_ID:
        raise SourceInventoryError(f"unsupported plan workflow {plan.get('workflow')!r}")
    if plan.get("production_outputs_updated", []) != []:
        raise SourceInventoryError("promotion plan must be review-only before live apply")
    missing = _plan_rows(plan, "missing_candidates")
    if missing:
        raise SourceInventoryError(f"promotion plan has {len(missing)} missing candidate(s)")


def _plan_rows(plan: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    rows = plan.get(key, [])
    if not isinstance(rows, list):
        raise SourceInventoryError(f"plan {key} must be a list")
    clean_rows: list[Mapping[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SourceInventoryError(f"plan {key}[{idx}] must be a mapping")
        clean_rows.append(row)
    return clean_rows


def _filter_by_source_family(rows: Sequence[Mapping[str, Any]], source_family: str | None) -> list[Mapping[str, Any]]:
    if not source_family:
        return list(rows)
    return [row for row in rows if _source_family(row) == source_family]


def _source_family(row: Mapping[str, Any]) -> str | None:
    source_inventory = row.get("source_inventory")
    if isinstance(source_inventory, Mapping):
        value = source_inventory.get("source_family")
        return str(value) if value else None
    return None


def _manifest_entry_for_lemma(manifest: Mapping[str, Any], lemma: str) -> dict[str, Any] | None:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return None
    key = _lemma_key(lemma)
    for entry in entries:
        if isinstance(entry, dict) and _lemma_key(str(entry.get("lemma") or "")) == key:
            return entry
    return None


def _validate_privacy_safe_provenance(entry: Mapping[str, Any]) -> None:
    provenance = entry.get("source_provenance")
    if provenance is None:
        return
    if not isinstance(provenance, list):
        raise SourceInventoryError(f"{entry.get('lemma')}: source_provenance must be a list")
    for idx, item in enumerate(provenance):
        if not isinstance(item, Mapping):
            raise SourceInventoryError(f"{entry.get('lemma')}: source_provenance[{idx}] must be a mapping")
        inventory_path = _clean_text(item.get("inventory_path"))
        if inventory_path and not inventory_path.startswith(_SAFE_INVENTORY_PREFIX):
            raise SourceInventoryError(
                f"{entry.get('lemma')}: source_provenance[{idx}].inventory_path is not a committed inventory path"
            )
        for key, value in item.items():
            text = _clean_text(value)
            if not text:
                continue
            normalized = text.casefold()
            if any(marker in normalized for marker in _PRIVATE_PROVENANCE_MARKERS):
                raise SourceInventoryError(
                    f"{entry.get('lemma')}: source_provenance[{idx}].{key} contains private source detail"
                )


def _has_manifest_changes(result: Mapping[str, Any]) -> bool:
    counts = result.get("counts")
    if not isinstance(counts, Mapping):
        return False
    return int(counts.get("promoted", 0)) > 0 or int(counts.get("overlay_updated_entries", 0)) > 0


def _clean_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _display_path(path: Path) -> str:
    path = path if path.is_absolute() else PROJECT_ROOT / path
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _write_fingerprint_sidecar(path: Path) -> dict[str, Any]:
    return write_fingerprint(path, root=PROJECT_ROOT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--candidates", type=Path, default=planner.DEFAULT_CANDIDATES)
    parser.add_argument("--decision-file", type=Path, action="append", dest="decision_files", default=[])
    parser.add_argument("--source-family", help="Limit apply to one source family, e.g. teacher_lesson")
    parser.add_argument("--expected-additions", type=int)
    parser.add_argument("--expected-skipped-existing", type=int)
    parser.add_argument(
        "--overlay-existing-provenance",
        action="store_true",
        help="Also add approved provenance to already-present manifest entries",
    )
    parser.add_argument("--write", action="store_true", help="Write manifest and fingerprint sidecar")
    parser.add_argument("--report", action="store_true", help="Print Markdown report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = apply_promotion_plan(
            manifest,
            plan,
            source_family=args.source_family,
            expected_additions=args.expected_additions,
            expected_skipped_existing=args.expected_skipped_existing,
        )
        if args.overlay_existing_provenance:
            candidate_index = planner._candidate_index(planner._read_candidate_payload(args.candidates))
            approved_decisions = planner._approved_decisions(planner._decision_paths(args.decision_files))
            result = apply_existing_provenance_overlay(
                manifest,
                result,
                candidate_index,
                approved_decisions,
                source_family=args.source_family,
            )
        if args.write:
            result = write_manifest_if_changed(
                manifest,
                result,
                manifest_path=args.manifest,
                fingerprint_path=args.fingerprint,
            )
    except (OSError, SourceInventoryError, json.JSONDecodeError, promote.SelfCheckError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return getattr(exc, "exit_code", 2)
    if args.report:
        print(format_report(result))
    else:
        print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
