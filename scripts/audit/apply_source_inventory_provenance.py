#!/usr/bin/env python3
"""Attach approved source-inventory provenance to existing Atlas entries."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit import plan_source_inventory_promotion as plan
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon import promote_grow_candidates as promote
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, write_fingerprint

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
WORKFLOW_ID = "source_inventory_existing_provenance_overlay.v1"


def apply_existing_provenance_overlay(
    manifest: dict[str, Any],
    candidate_index: Mapping[str, plan.CandidateMatch],
    approved_decisions: Sequence[plan.ApprovedDecision],
    *,
    source_family: str | None = None,
) -> dict[str, Any]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise SourceInventoryError("manifest entries must be list")

    entries_by_key: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("lemma"):
            continue
        entries_by_key[_lemma_key(str(entry["lemma"]))] = entry

    updates: list[dict[str, Any]] = []
    missing_candidates: list[dict[str, Any]] = []
    missing_manifest_entries: list[dict[str, Any]] = []
    unchanged_existing: list[dict[str, Any]] = []
    filtered_decisions = 0
    added_refs = 0

    for decision in approved_decisions:
        if source_family and decision.source_inventory.get("source_family") != source_family:
            continue
        filtered_decisions += 1

        base_row = {
            "lemma": decision.lemma,
            "source_inventory_key": decision.source_key,
            "source_family": decision.source_inventory.get("source_family"),
            "decision_file": decision.decision_file,
        }
        match = candidate_index.get(decision.source_key)
        if match is None:
            missing_candidates.append({**base_row, "reason": "approved source key missing from candidates"})
            continue

        entry = entries_by_key.get(_lemma_key(decision.lemma))
        if entry is None:
            missing_manifest_entries.append({**base_row, "reason": "approved lemma missing from manifest"})
            continue

        candidate_provenance = plan._approved_source_provenance(decision, match.entry)
        if not candidate_provenance:
            missing_candidates.append({**base_row, "reason": "matched candidate lacks source_provenance"})
            continue

        added = _append_missing_provenance(entry, candidate_provenance)
        if added:
            added_refs += added
            updates.append(
                {
                    **base_row,
                    "primary_source": entry.get("primary_source"),
                    "added_provenance_refs": added,
                    "manifest_lemma": entry.get("lemma"),
                }
            )
        else:
            unchanged_existing.append({**base_row, "reason": "source provenance already present"})

    return {
        "workflow": WORKFLOW_ID,
        "source_family": source_family,
        "counts": {
            "approved_decisions": len(approved_decisions),
            "filtered_decisions": filtered_decisions,
            "updated_entries": len(updates),
            "added_provenance_refs": added_refs,
            "unchanged_existing": len(unchanged_existing),
            "missing_candidates": len(missing_candidates),
            "missing_manifest_entries": len(missing_manifest_entries),
        },
        "updated_entries": updates,
        "unchanged_existing": unchanged_existing,
        "missing_candidates": missing_candidates,
        "missing_manifest_entries": missing_manifest_entries,
        "production_outputs_updated": [],
    }


def format_report(result: Mapping[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Source Inventory Existing Provenance Overlay",
        "",
        f"- workflow: `{result['workflow']}`",
        f"- source_family: `{result.get('source_family') or 'all'}`",
        f"- filtered_decisions: {counts['filtered_decisions']}",
        f"- updated_entries: {counts['updated_entries']}",
        f"- added_provenance_refs: {counts['added_provenance_refs']}",
        f"- unchanged_existing: {counts['unchanged_existing']}",
        f"- missing_candidates: {counts['missing_candidates']}",
        f"- missing_manifest_entries: {counts['missing_manifest_entries']}",
        "- production_outputs_updated: []",
    ]
    if result.get("updated_entries"):
        lines.extend(["", "## Updated Existing Entries", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): +{row['added_provenance_refs']} provenance ref(s)"
            for row in result["updated_entries"]
        )
    if result.get("missing_candidates"):
        lines.extend(["", "## Missing Candidates", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row['reason']}"
            for row in result["missing_candidates"]
        )
    if result.get("missing_manifest_entries"):
        lines.extend(["", "## Missing Manifest Entries", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row['reason']}"
            for row in result["missing_manifest_entries"]
        )
    return "\n".join(lines)


def _append_missing_provenance(entry: dict[str, Any], provenance: Sequence[Mapping[str, Any]]) -> int:
    existing_raw = entry.get("source_provenance")
    if existing_raw is None:
        existing: list[dict[str, Any]] = []
    elif isinstance(existing_raw, list):
        existing = [dict(item) for item in existing_raw if isinstance(item, Mapping)]
    else:
        raise SourceInventoryError(f"{entry.get('lemma')}: source_provenance must be list when present")

    seen = {_canonical_provenance_key(item) for item in existing}
    added = 0
    for item in provenance:
        row = dict(item)
        key = _canonical_provenance_key(row)
        if key in seen:
            continue
        existing.append(row)
        seen.add(key)
        added += 1

    if added:
        entry["source_provenance"] = existing
    return added


def _canonical_provenance_key(item: Mapping[str, Any]) -> str:
    return json.dumps(dict(item), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=plan.DEFAULT_CANDIDATES)
    parser.add_argument("--decision-file", type=Path, action="append", dest="decision_files")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--generate-candidates", action="store_true")
    parser.add_argument("--source-family", help="Limit overlay to one source family, e.g. ohoiko")
    parser.add_argument("--write", action="store_true", help="Write manifest and fingerprint sidecar")
    parser.add_argument("--report", action="store_true", help="Print Markdown report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.generate_candidates:
            review.generate_review_candidates(out=args.candidates)
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        candidate_index = plan._candidate_index(plan._read_candidate_payload(args.candidates))
        approved = plan._approved_decisions(plan._decision_paths(args.decision_files))
        result = apply_existing_provenance_overlay(
            manifest,
            candidate_index,
            approved,
            source_family=args.source_family,
        )
        if args.write and result["counts"]["updated_entries"]:
            promote._refresh_manifest_metadata(manifest)
            promote._validate_before_write(manifest, args.manifest, promote.verify_prospective_manifest)
            promote._write_json_atomically(args.manifest, manifest)
            write_fingerprint(args.fingerprint)
        if args.report:
            print(format_report(result))
        else:
            print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    except (OSError, SourceInventoryError, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
