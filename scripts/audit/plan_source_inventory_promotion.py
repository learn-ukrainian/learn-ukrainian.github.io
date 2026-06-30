#!/usr/bin/env python3
"""Build a review-only publish plan from approved source-inventory decisions."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon import promote_grow_candidates as promote
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.lemma_normalization import strip_acute_stress

WORKFLOW_ID = "source_inventory_approved_promotion_plan.v1"
DEFAULT_CANDIDATES = Path("/tmp/atlas-source-inventory-review-candidates.json")
DEFAULT_OUT = Path("/tmp/atlas-source-inventory-approved-promotion-plan.json")
DEFAULT_REPORT_OUT = Path("/tmp/atlas-source-inventory-approved-promotion-plan.md")


@dataclass(frozen=True)
class ApprovedDecision:
    lemma: str
    approved_pos: str
    approved_gloss: str
    sense_note: str
    source_inventory: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    review_queue_reasons: tuple[str, ...]
    surface_admission: Mapping[str, bool]
    batch_id: str
    batch_label: str
    decision_file: str

    @property
    def source_key(self) -> str:
        return str(self.source_inventory["key"])


@dataclass(frozen=True)
class CandidateMatch:
    entry: Mapping[str, Any]
    bucket: str
    reasons: tuple[str, ...]


def build_promotion_plan(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    decision_files: Sequence[Path] | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Return approved source-inventory rows as proposed manifest additions."""
    decision_paths = _decision_paths(decision_files)
    decision_summary = decisions.validate_committed_decision_files(decision_paths)
    approved = _approved_decisions(decision_paths)
    candidate_payload = _read_candidate_payload(candidates_path)
    candidate_index = _candidate_index(candidate_payload)
    manifest_keys = _manifest_keys(manifest_path)

    proposed: list[dict[str, Any]] = []
    skipped_existing: list[dict[str, Any]] = []
    missing_candidates: list[dict[str, Any]] = []

    for decision in approved:
        match = candidate_index.get(decision.source_key)
        base_row = {
            "lemma": decision.lemma,
            "source_inventory_key": decision.source_key,
            "source_inventory": dict(decision.source_inventory),
            "decision_file": decision.decision_file,
            "batch_id": decision.batch_id,
            "batch_label": decision.batch_label,
        }
        if match is None:
            missing_candidates.append({**base_row, "reason": "candidate_not_found"})
            continue
        if _lemma_key(decision.lemma) in manifest_keys:
            skipped_existing.append({**base_row, "reason": "already_in_manifest"})
            continue
        proposed.append(_planned_addition(decision, match))

    return {
        "workflow": WORKFLOW_ID,
        "policy": (
            "Review-only source-inventory promotion plan. This file proposes "
            "manifest additions but does not update live Atlas, search, browse, "
            "daily, practice, cloze, pointer, fingerprint, status, audit, review, "
            "or telemetry outputs."
        ),
        "source_candidate_payload": str(candidates_path),
        "source_decision_files": [str(path) for path in decision_paths],
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_loaded": manifest_path is not None,
        "production_outputs_updated": [],
        "counts": {
            "decision_files": decision_summary["files"],
            "approved_decisions": len(approved),
            "candidate_source_keys": len(candidate_index),
            "matched_candidates": len(proposed) + len(skipped_existing),
            "proposed_additions": len(proposed),
            "skipped_existing": len(skipped_existing),
            "missing_candidates": len(missing_candidates),
        },
        "proposed_manifest_additions": proposed,
        "skipped_existing": skipped_existing,
        "missing_candidates": missing_candidates,
    }


def write_plan(plan: Mapping[str, Any], out: Path = DEFAULT_OUT) -> Path:
    """Write promotion plan outside the repository."""
    output_path = resolve_ephemeral_plan_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_report(plan: Mapping[str, Any], out: Path = DEFAULT_REPORT_OUT) -> Path:
    """Write a human Markdown summary outside the repository."""
    output_path = resolve_ephemeral_plan_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_report(plan) + "\n", encoding="utf-8")
    return output_path


def format_report(plan: Mapping[str, Any]) -> str:
    counts = plan["counts"]
    lines = [
        "# Source Inventory Approved Promotion Plan",
        "",
        f"- workflow: `{plan['workflow']}`",
        f"- approved_decisions: {counts['approved_decisions']}",
        f"- proposed_additions: {counts['proposed_additions']}",
        f"- skipped_existing: {counts['skipped_existing']}",
        f"- missing_candidates: {counts['missing_candidates']}",
        "- production_outputs_updated: []",
        "",
        str(plan["policy"]),
        "",
        "## Proposed Manifest Additions",
        "",
        "| Lemma | POS | Gloss | Bucket | Source Key | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    proposed = plan.get("proposed_manifest_additions")
    if not proposed:
        lines.append("| - | - | - | - | - | - |")
    else:
        for row in proposed:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_cell(row["lemma"]),
                        _markdown_cell(row["approved_pos"]),
                        _markdown_cell(row["approved_gloss"]),
                        _markdown_cell(row["candidate_bucket"]),
                        _markdown_cell(row["source_inventory_key"]),
                        _markdown_cell(row["sense_note"]),
                    ]
                )
                + " |"
            )

    if plan.get("skipped_existing"):
        lines.extend(["", "## Skipped Existing", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row['reason']}"
            for row in plan["skipped_existing"]
        )
    if plan.get("missing_candidates"):
        lines.extend(["", "## Missing Candidates", ""])
        lines.extend(
            f"- `{row['lemma']}` ({row['source_inventory_key']}): {row['reason']}"
            for row in plan["missing_candidates"]
        )
    return "\n".join(lines)


def resolve_ephemeral_plan_output_path(out: Path) -> Path:
    """Reject committed or live output paths for review-only promotion plans."""
    return review.resolve_ephemeral_review_output_path(out)


def _planned_addition(decision: ApprovedDecision, match: CandidateMatch) -> dict[str, Any]:
    candidate = copy.deepcopy(dict(match.entry))
    candidate["pos"] = decision.approved_pos
    candidate["gloss"] = decision.approved_gloss
    candidate.pop("surface_admission", None)
    manifest_entry = promote.manifest_entry_from_candidate(candidate)
    manifest_entry["gloss"] = decision.approved_gloss
    manifest_entry["pos"] = decision.approved_pos
    if candidate.get("primary_source"):
        manifest_entry["primary_source"] = candidate["primary_source"]
    if decision.surface_admission:
        manifest_entry["surface_admission"] = dict(decision.surface_admission)
    return {
        "lemma": decision.lemma,
        "approved_pos": decision.approved_pos,
        "approved_gloss": decision.approved_gloss,
        "sense_note": decision.sense_note,
        "source_inventory_key": decision.source_key,
        "source_inventory": dict(decision.source_inventory),
        "evidence_refs": list(decision.evidence_refs),
        "review_queue_reasons": list(decision.review_queue_reasons),
        "surface_admission": dict(decision.surface_admission),
        "candidate_bucket": match.bucket,
        "candidate_reasons": list(match.reasons),
        "batch_id": decision.batch_id,
        "batch_label": decision.batch_label,
        "decision_file": decision.decision_file,
        "manifest_entry": manifest_entry,
    }


def _candidate_index(payload: Mapping[str, Any]) -> dict[str, CandidateMatch]:
    index: dict[str, CandidateMatch] = {}
    for entry, bucket, reasons in _candidate_entries(payload):
        for source_key in _candidate_source_keys(entry):
            if source_key in index:
                raise SourceInventoryError(f"duplicate candidate source key {source_key!r}")
            index[source_key] = CandidateMatch(
                entry=entry,
                bucket=bucket,
                reasons=tuple(reasons),
            )
    return index


def _candidate_entries(
    payload: Mapping[str, Any],
) -> list[tuple[Mapping[str, Any], str, list[str]]]:
    entries: list[tuple[Mapping[str, Any], str, list[str]]] = []
    for entry in payload.get("auto_merge", []):
        if isinstance(entry, Mapping):
            entries.append((entry, "auto_merge", review.publish_review_reasons(entry)))
    for item in payload.get("needs_review", []):
        if not isinstance(item, Mapping) or not isinstance(item.get("entry"), Mapping):
            continue
        entry = item["entry"]
        reason = _clean_text(item.get("reason")) or "unspecified"
        reasons = [f"grow_needs_review:{reason}"]
        reasons.extend(review.publish_review_reasons(entry))
        entries.append((entry, "needs_review", reasons))
    return entries


def _candidate_source_keys(entry: Mapping[str, Any]) -> list[str]:
    lemma = strip_acute_stress(_clean_text(entry.get("lemma")))
    provenance = entry.get("source_provenance")
    if not lemma or not isinstance(provenance, list):
        return []
    keys: list[str] = []
    for item in provenance:
        if not isinstance(item, Mapping):
            continue
        inventory_path = _clean_text(item.get("inventory_path"))
        locator = _clean_text(item.get("source_locator"))
        if not inventory_path or not locator:
            continue
        keys.append(
            decisions.source_inventory_key(
                lemma=lemma,
                inventory_path=inventory_path,
                locator=locator,
            )
        )
    return keys


def _read_candidate_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SourceInventoryError(f"candidate payload not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceInventoryError(f"{path}: candidate payload must be a mapping")
    review.validate_source_provenance(payload)
    return payload


def _approved_decisions(paths: Sequence[Path]) -> list[ApprovedDecision]:
    approved: list[ApprovedDecision] = []
    for path in paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise SourceInventoryError(f"{path}: expected mapping")
        for row in payload.get("decisions", []):
            if not isinstance(row, Mapping) or row.get("decision") != "approve_for_publish":
                continue
            approved.append(
                ApprovedDecision(
                    lemma=str(row["lemma"]),
                    approved_pos=str(row["approved_pos"]),
                    approved_gloss=str(row["approved_gloss"]),
                    sense_note=str(row["sense_note"]),
                    source_inventory=row["source_inventory"],
                    evidence_refs=tuple(str(item) for item in row["evidence_refs"]),
                    review_queue_reasons=tuple(
                        str(item) for item in row.get("review_queue_reasons", [])
                    ),
                    surface_admission=dict(row.get("surface_admission") or {}),
                    batch_id=str(payload["batch_id"]),
                    batch_label=str(payload["batch_label"]),
                    decision_file=str(path),
                )
            )
    return approved


def _decision_paths(paths: Sequence[Path] | None) -> list[Path]:
    if paths:
        return [Path(path) for path in paths]
    return sorted(decisions.DEFAULT_DECISION_DIR.glob("*.yaml"))


def _manifest_keys(path: Path | None) -> set[str]:
    if path is None:
        return set()
    if not path.exists():
        raise SourceInventoryError(f"manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        raise SourceInventoryError(f"{path}: manifest entries must be a list")
    return {
        _lemma_key(str(entry["lemma"]))
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("lemma")
    }


def _clean_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", r"\|")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--decision-file", type=Path, action="append", dest="decision_files")
    parser.add_argument("--manifest", type=Path, help="Optional existing manifest for duplicate checks")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    parser.add_argument(
        "--generate-candidates",
        action="store_true",
        help="Generate the review-only candidate payload before planning",
    )
    parser.add_argument("--limit", type=int, help="Limit candidate generation when used with --generate-candidates")
    parser.add_argument("--report", action="store_true", help="Print plan summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.generate_candidates:
            review.generate_review_candidates(limit=args.limit, out=args.candidates)
        plan = build_promotion_plan(
            candidates_path=args.candidates,
            decision_files=args.decision_files,
            manifest_path=args.manifest,
        )
        plan_path = write_plan(plan, args.out)
        report_path = write_report(plan, args.report_out)
    except (OSError, SourceInventoryError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.report:
        counts = plan["counts"]
        print(f"approved_decisions: {counts['approved_decisions']}")
        print(f"matched_candidates: {counts['matched_candidates']}")
        print(f"proposed_additions: {counts['proposed_additions']}")
        print(f"skipped_existing: {counts['skipped_existing']}")
        print(f"missing_candidates: {counts['missing_candidates']}")
        print(f"production_outputs_updated: {plan['production_outputs_updated']}")
        print(f"plan_output: {plan_path}")
        print(f"report_output: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
