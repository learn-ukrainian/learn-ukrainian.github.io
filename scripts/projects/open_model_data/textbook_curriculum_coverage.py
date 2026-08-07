#!/usr/bin/env python3
"""Evaluate official textbook curriculum cells against a readiness receipt.

The denominator is a curriculum-cell inventory, not a publisher-edition
Cartesian product. Readiness is evidence for a cell; the 116-book selection
remains a separate receipt field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "textbook_curriculum_coverage_v1"
DENOMINATOR_SCHEMA_VERSION = "textbook_curriculum_denominator_v1"
READINESS_SCHEMA_VERSION = "textbook_corpus_readiness_v1"

REQUIREMENT_CLASSES = (
    "required_common",
    "required_one_of",
    "profile_or_track",
    "optional_elective",
    "no_textbook_required_or_unresolved",
)
TEXTBOOK_APPLICABILITY = {
    "required",
    "choice_required",
    "profile_conditional",
    "optional",
    "not_required",
    "unresolved",
}
EVIDENCE_STATES = {"resolved", "unresolved", "legacy_only"}
CELL_STATUSES = {
    "covered",
    "degraded",
    "acquisition_missing",
    "extraction_missing",
    "choice_satisfied",
    "not_required",
    "unresolved",
}
READINESS_STATUSES = {
    "ready",
    "pdf_without_chunks",
    "chunks_without_pdf",
    "chunks_not_ingested",
    "db_without_chunks",
    "suspect_extraction",
    "missing_selected_source",
    "untracked",
}
_STATUS_RANK = {
    "not_required": 0,
    "choice_satisfied": 1,
    "acquisition_missing": 2,
    "extraction_missing": 3,
    "degraded": 4,
    "covered": 5,
    "unresolved": 6,
}


class CoverageError(ValueError):
    """Raised when an input violates the curriculum coverage schema."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise CoverageError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for receipts and test comparisons."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _read_document(path: Path) -> Any:
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except CoverageError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CoverageError(f"cannot read document: {path}") from exc


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CoverageError(f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise CoverageError(f"{label} must be a list")
    result = [_string(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if not allow_empty and not result:
        raise CoverageError(f"{label} must not be empty")
    if len(result) != len(set(result)):
        raise CoverageError(f"{label} contains duplicate values")
    return result


def _validate_denominator(document: Any) -> dict[str, Any]:
    root = dict(_mapping(document, "denominator"))
    if root.get("schema_version") != DENOMINATOR_SCHEMA_VERSION:
        raise CoverageError("unsupported denominator schema_version")
    locators = _mapping(root.get("locator_registry"), "locator_registry")
    for locator_id, locator in locators.items():
        _string(locator_id, "locator_registry key")
        _string(locator, f"locator_registry[{locator_id!r}]")
    classes = _string_list(root.get("requirement_classes"), "requirement_classes", allow_empty=False)
    if tuple(classes) != REQUIREMENT_CLASSES:
        raise CoverageError("requirement_classes must list the canonical five classes in order")

    raw_cells = root.get("cells")
    if not isinstance(raw_cells, list) or not raw_cells:
        raise CoverageError("cells must be a non-empty list")
    cells: list[dict[str, Any]] = []
    cell_ids: set[str] = set()
    for index, raw_cell in enumerate(raw_cells):
        cell = dict(_mapping(raw_cell, f"cells[{index}]"))
        cell_id = _string(cell.get("cell_id"), f"cells[{index}].cell_id")
        if cell_id in cell_ids:
            raise CoverageError(f"duplicate cell_id: {cell_id}")
        cell_ids.add(cell_id)
        grade = cell.get("grade")
        if isinstance(grade, bool) or not isinstance(grade, int) or not 1 <= grade <= 11:
            raise CoverageError(f"{cell_id}: grade must be an explicit integer from 1 to 11")
        for field in ("canonical_subject_id", "display_name_uk", "cohort_or_effective_basis", "evidence_note"):
            _string(cell.get(field), f"{cell_id}.{field}")
        requirement_class = _string(cell.get("requirement_class"), f"{cell_id}.requirement_class")
        if requirement_class not in REQUIREMENT_CLASSES:
            raise CoverageError(f"{cell_id}: unknown requirement_class {requirement_class!r}")
        for field in ("official_program_locator_ids", "official_edition_catalog_locator_ids"):
            values = _string_list(cell.get(field), f"{cell_id}.{field}", allow_empty=False)
            for locator_id in values:
                if locator_id not in locators:
                    raise CoverageError(f"{cell_id}: unknown locator id {locator_id!r}")
        applicability = _string(cell.get("textbook_applicability"), f"{cell_id}.textbook_applicability")
        if applicability not in TEXTBOOK_APPLICABILITY:
            raise CoverageError(f"{cell_id}: unknown textbook_applicability {applicability!r}")

        coverage = dict(_mapping(cell.get("coverage"), f"{cell_id}.coverage"))
        _string(coverage.get("coverage_unit_id"), f"{cell_id}.coverage.coverage_unit_id")
        source_ids = _string_list(coverage.get("source_ids"), f"{cell_id}.coverage.source_ids")
        raw_groups = coverage.get("source_groups")
        if not isinstance(raw_groups, list):
            raise CoverageError(f"{cell_id}.coverage.source_groups must be a list")
        source_groups: list[list[str]] = []
        for group_index, group in enumerate(raw_groups):
            source_groups.append(
                _string_list(group, f"{cell_id}.coverage.source_groups[{group_index}]", allow_empty=False)
            )
        mode = _string(coverage.get("source_match_mode"), f"{cell_id}.coverage.source_match_mode")
        if mode not in {"any", "all"}:
            raise CoverageError(f"{cell_id}: source_match_mode must be any or all")
        if source_groups and mode != "all":
            raise CoverageError(f"{cell_id}: source_groups require source_match_mode=all")
        evidence_state = _string(coverage.get("evidence_state"), f"{cell_id}.coverage.evidence_state")
        if evidence_state not in EVIDENCE_STATES:
            raise CoverageError(f"{cell_id}: unknown evidence_state {evidence_state!r}")
        legacy = _string_list(
            coverage.get("legacy_inventory_source_ids"),
            f"{cell_id}.coverage.legacy_inventory_source_ids",
        )
        _string(coverage.get("edition_policy"), f"{cell_id}.coverage.edition_policy")
        coverage.update(
            source_ids=source_ids,
            source_groups=source_groups,
            source_match_mode=mode,
            evidence_state=evidence_state,
            legacy_inventory_source_ids=legacy,
        )
        cell["coverage"] = coverage

        group_id = cell.get("choice_group_id")
        member_id = cell.get("choice_member_id")
        requires = cell.get("choice_member_requires")
        if requirement_class == "required_one_of" and (group_id is None or member_id is None):
            raise CoverageError(f"{cell_id}: required_one_of needs choice_group_id and choice_member_id")
        if group_id is not None:
            _string(group_id, f"{cell_id}.choice_group_id")
            _string(member_id, f"{cell_id}.choice_member_id")
            if not isinstance(requires, list) or not requires:
                raise CoverageError(f"{cell_id}: choice_member_requires must be a non-empty list")
            cell["choice_member_requires"] = _string_list(
                requires,
                f"{cell_id}.choice_member_requires",
                allow_empty=False,
            )
        elif requires is not None:
            raise CoverageError(f"{cell_id}: choice_member_requires without choice_group_id")
        cells.append(cell)

    for cell in cells:
        for required_id in cell.get("choice_member_requires", []):
            if required_id not in cell_ids:
                raise CoverageError(f"{cell['cell_id']}: unknown choice member cell {required_id!r}")
    root["cells"] = cells
    return root


def load_denominator(path: Path) -> dict[str, Any]:
    """Read and validate denominator YAML."""
    return _validate_denominator(_read_document(Path(path)))


def _validate_readiness(document: Any) -> dict[str, Any]:
    root = dict(_mapping(document, "readiness"))
    if root.get("schema_version") != READINESS_SCHEMA_VERSION:
        raise CoverageError("unsupported readiness schema_version")
    sources = root.get("sources")
    if not isinstance(sources, list):
        raise CoverageError("readiness.sources must be a list")
    seen: set[str] = set()
    for index, raw_source in enumerate(sources):
        source = _mapping(raw_source, f"readiness.sources[{index}]")
        source_id = _string(source.get("source"), f"readiness.sources[{index}].source")
        if source_id in seen:
            raise CoverageError(f"duplicate readiness source: {source_id}")
        seen.add(source_id)
        status = _string(source.get("status"), f"{source_id}.status")
        if status not in READINESS_STATUSES:
            raise CoverageError(f"{source_id}: unsupported readiness status {status!r}")
        selection_ids = source.get("selection_ids", [])
        if not isinstance(selection_ids, list) or any(not isinstance(item, str) for item in selection_ids):
            raise CoverageError(f"{source_id}: selection_ids must be a string list")
    selection = root.get("selection", {})
    if not isinstance(selection, Mapping):
        raise CoverageError("readiness.selection must be a mapping")
    selected_count = selection.get("selected_count")
    if selected_count is not None and (
        isinstance(selected_count, bool) or not isinstance(selected_count, int) or selected_count < 0
    ):
        raise CoverageError("readiness.selection.selected_count must be a non-negative integer")
    return root


def load_readiness(path: Path) -> dict[str, Any]:
    """Read and validate readiness JSON/YAML."""
    return _validate_readiness(_read_document(Path(path)))


def _source_keys(source: Mapping[str, Any]) -> set[str]:
    return {_string(source["source"], "source"), *map(str, source.get("selection_ids", []))}


def _index_sources(readiness: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    index: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for source in readiness["sources"]:
        for key in sorted(_source_keys(source)):
            index[key].append(source)
    return index


def _readiness_status(source: Mapping[str, Any]) -> str:
    status = str(source["status"])
    if status == "ready":
        return "covered"
    if status == "suspect_extraction":
        return "degraded"
    if status in {"pdf_without_chunks", "chunks_not_ingested"}:
        return "extraction_missing"
    if status in {"chunks_without_pdf", "db_without_chunks"}:
        return "degraded"
    return "acquisition_missing"


def _combine_statuses(statuses: Iterable[str], *, empty: str = "acquisition_missing") -> str:
    values = list(statuses)
    if not values:
        return empty
    return max(values, key=lambda value: (_STATUS_RANK[value], value))


def _all_required_statuses(statuses: Iterable[str]) -> str:
    """Combine statuses for a cell/member whose every component is required."""
    values = list(statuses)
    if not values:
        return "acquisition_missing"
    if all(status == "covered" for status in values):
        return "covered"
    if all(status in {"covered", "degraded"} for status in values):
        return "degraded"
    for status in ("unresolved", "extraction_missing", "acquisition_missing", "degraded"):
        if status in values:
            return status
    return _combine_statuses(values)


def _candidate_status(
    source_ids: Sequence[str],
    source_index: Mapping[str, Sequence[Mapping[str, Any]]],
) -> tuple[str, list[dict[str, Any]], list[str]]:
    matches: list[dict[str, Any]] = []
    statuses: list[str] = []
    missing: list[str] = []
    seen_sources: set[str] = set()
    for source_id in source_ids:
        records = source_index.get(source_id, ())
        if not records:
            missing.append(source_id)
            continue
        for record in records:
            source_name = str(record["source"])
            if source_name in seen_sources:
                continue
            seen_sources.add(source_name)
            mapped = _readiness_status(record)
            statuses.append(mapped)
            matches.append(
                {
                    "source": source_name,
                    "readiness_status": str(record["status"]),
                    "coverage_status": mapped,
                }
            )
    return _combine_statuses(statuses), sorted(matches, key=lambda item: item["source"]), sorted(missing)


def _raw_cell_evaluation(
    cell: Mapping[str, Any],
    source_index: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    coverage = cell["coverage"]
    source_ids = list(coverage["source_ids"])
    source_groups = list(coverage["source_groups"])
    matches: list[dict[str, Any]] = []
    missing: list[str] = []
    if source_groups:
        group_results: list[str] = []
        for group in source_groups:
            status, group_matches, group_missing = _candidate_status(group, source_index)
            group_results.append(status)
            matches.extend(group_matches)
            missing.extend(group_missing)
        status = _all_required_statuses(group_results)
    else:
        status, matches, missing = _candidate_status(source_ids, source_index)

    requirement_class = cell["requirement_class"]
    applicability = cell["textbook_applicability"]
    evidence_state = coverage["evidence_state"]
    if requirement_class == "no_textbook_required_or_unresolved":
        status = "not_required" if applicability == "not_required" else "unresolved"
    elif evidence_state == "unresolved" or applicability == "unresolved":
        status = "unresolved"
    elif requirement_class in {"profile_or_track", "optional_elective"} and not source_ids and not source_groups:
        status = "not_required"
    elif evidence_state == "legacy_only":
        status = "acquisition_missing"

    reason_by_status = {
        "covered": "an accepted readiness source is ready",
        "degraded": "readiness has content but the source is incomplete or suspect",
        "extraction_missing": "an accepted source exists but extraction or ingest is missing",
        "acquisition_missing": "no accepted current source is present in the readiness receipt",
        "not_required": "the cell is conditional or optional and has no selected source evidence",
        "choice_satisfied": "another approved alternative in the choice group is covered",
        "unresolved": "official title-level enumeration or textbook applicability remains unresolved",
    }
    reason = reason_by_status[status]
    if evidence_state == "legacy_only":
        reason = "legacy inventory is retained as evidence but cannot satisfy the current cohort"
    return {
        "cell_id": cell["cell_id"],
        "grade": cell["grade"],
        "canonical_subject_id": cell["canonical_subject_id"],
        "display_name_uk": cell["display_name_uk"],
        "requirement_class": requirement_class,
        "textbook_applicability": applicability,
        "coverage_unit_id": coverage["coverage_unit_id"],
        "choice_group_id": cell.get("choice_group_id"),
        "choice_member_id": cell.get("choice_member_id"),
        "raw_status": status,
        "status": status,
        "reason": reason,
        "readiness_matches": matches,
        "missing_source_ids": missing,
        "legacy_inventory_source_ids": list(coverage["legacy_inventory_source_ids"]),
        "evidence_state": evidence_state,
    }


def _choice_groups(cells: Sequence[Mapping[str, Any]], evaluations: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[Mapping[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for cell in cells:
        group_id = cell.get("choice_group_id")
        if group_id:
            grouped[str(group_id)][str(cell["choice_member_id"])].append(cell)

    reports: list[dict[str, Any]] = []
    for group_id in sorted(grouped):
        members = grouped[group_id]
        member_reports: list[dict[str, Any]] = []
        for member_id in sorted(members):
            member_cells = sorted(members[member_id], key=lambda item: str(item["cell_id"]))
            required_ids = sorted({required for cell in member_cells for required in cell["choice_member_requires"]})
            component_statuses = [evaluations[cell_id]["raw_status"] for cell_id in required_ids]
            member_status = _all_required_statuses(component_statuses)
            member_reports.append(
                {
                    "member_id": member_id,
                    "cell_ids": [str(cell["cell_id"]) for cell in member_cells],
                    "required_cell_ids": required_ids,
                    "status": member_status,
                }
            )

        covered = [item for item in member_reports if item["status"] == "covered"]
        degraded = [item for item in member_reports if item["status"] == "degraded"]
        selected_member = (covered or degraded or [None])[0]
        group_status = "choice_satisfied" if covered else "degraded" if degraded else _combine_statuses(
            item["status"] for item in member_reports
        )

        if selected_member is not None and group_status == "choice_satisfied":
            selected_id = selected_member["member_id"]
            for item in member_reports:
                if item["member_id"] == selected_id:
                    continue
                for cell_id in item["cell_ids"]:
                    if evaluations[cell_id]["status"] in {
                        "acquisition_missing",
                        "extraction_missing",
                        "degraded",
                        "not_required",
                        "covered",
                    }:
                        evaluations[cell_id]["status"] = "choice_satisfied"
                        evaluations[cell_id]["reason"] = (
                            "another approved alternative in the choice group is covered"
                        )
        reports.append(
            {
                "choice_group_id": group_id,
                "status": group_status,
                "selected_member_id": selected_member["member_id"] if selected_member else None,
                "members": member_reports,
            }
        )
    return reports


def _coverage_units(evaluations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for evaluation in evaluations:
        grouped[str(evaluation["coverage_unit_id"])].append(evaluation)
    result: list[dict[str, Any]] = []
    for unit_id in sorted(grouped):
        items = sorted(grouped[unit_id], key=lambda item: str(item["cell_id"]))
        statuses = [str(item["status"]) for item in items]
        if all(status in {"covered", "choice_satisfied", "not_required"} for status in statuses):
            status = "covered" if "covered" in statuses else statuses[0]
        else:
            status = _combine_statuses(statuses)
        result.append(
            {
                "coverage_unit_id": unit_id,
                "cell_ids": [str(item["cell_id"]) for item in items],
                "status": status,
            }
        )
    return result


def evaluate(denominator: Mapping[str, Any], readiness: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate validated mappings and return a deterministic report."""
    denominator_doc = _validate_denominator(denominator)
    readiness_doc = _validate_readiness(readiness)
    cells = sorted(denominator_doc["cells"], key=lambda item: str(item["cell_id"]))
    source_index = _index_sources(readiness_doc)
    evaluations_by_id = {
        str(cell["cell_id"]): _raw_cell_evaluation(cell, source_index) for cell in cells
    }
    choice_groups = _choice_groups(cells, evaluations_by_id)
    evaluations = [evaluations_by_id[str(cell["cell_id"])] for cell in cells]
    for evaluation in evaluations:
        evaluation.pop("raw_status", None)
        evaluation["readiness_matches"] = sorted(
            evaluation["readiness_matches"],
            key=lambda item: (item["source"], item["readiness_status"]),
        )
        evaluation["missing_source_ids"] = sorted(set(evaluation["missing_source_ids"]))

    requirement_counts = Counter(str(cell["requirement_class"]) for cell in cells)
    status_counts = Counter(str(item["status"]) for item in evaluations)
    grade_counts = Counter(int(cell["grade"]) for cell in cells)
    unresolved_cells = sorted(str(item["cell_id"]) for item in evaluations if item["status"] == "unresolved")
    units = _coverage_units(evaluations)
    required_classes = {"required_common", "required_one_of"}
    required_evaluations = [item for item in evaluations if item["requirement_class"] in required_classes]
    required_status_counts = Counter(str(item["status"]) for item in required_evaluations)

    selection = readiness_doc.get("selection", {})
    report = {
        "schema_version": SCHEMA_VERSION,
        "denominator": {
            "schema_version": denominator_doc["schema_version"],
            "cell_count": len(cells),
            "grade_counts": {str(grade): grade_counts[grade] for grade in sorted(grade_counts)},
            "requirement_class_counts": {
                requirement_class: requirement_counts[requirement_class]
                for requirement_class in REQUIREMENT_CLASSES
            },
            "coverage_unit_count": len(units),
        },
        "selection": {
            "selected_count": selection.get("selected_count"),
            "source": "readiness.selection.selected_count",
            "is_official_curriculum_denominator": False,
            "note": "The selection count is reported separately and does not define cell completeness.",
        },
        "readiness": {
            "schema_version": readiness_doc["schema_version"],
            "source_count": len(readiness_doc["sources"]),
            "receipt_counts": readiness_doc.get("counts", {}),
        },
        "counts": {
            "cells": len(evaluations),
            "by_requirement_class": {
                requirement_class: requirement_counts[requirement_class]
                for requirement_class in REQUIREMENT_CLASSES
            },
            "by_status": {status: status_counts[status] for status in sorted(CELL_STATUSES)},
            "required_cells": len(required_evaluations),
            "required_by_status": {
                status: required_status_counts[status] for status in sorted(CELL_STATUSES)
            },
            "coverage_units": len(units),
            "coverage_units_by_status": {
                status: sum(unit["status"] == status for unit in units) for status in sorted(CELL_STATUSES)
            },
        },
        "choice_groups": choice_groups,
        "coverage_units": units,
        "unresolved_evidence_cells": unresolved_cells,
        "cells": evaluations,
        "limitations": [
            "The report evaluates only source identities and readiness states recorded in the inputs.",
            "It does not claim title-level official enumeration where the denominator evidence marks it unresolved.",
            "A legacy source listed in legacy_inventory_source_ids cannot satisfy a current cohort cell.",
        ],
    }
    return report


def build_report(*, denominator_path: Path, readiness_path: Path) -> dict[str, Any]:
    """Load both inputs, validate them, and build a deterministic report."""
    denominator_path = Path(denominator_path)
    readiness_path = Path(readiness_path)
    report = evaluate(load_denominator(denominator_path), load_readiness(readiness_path))
    report["input_hashes"] = {
        "denominator_sha256": _sha256_file(denominator_path),
        "readiness_sha256": _sha256_file(readiness_path),
    }
    return report


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_output(path: Path, report: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_json(report) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--denominator", type=Path, required=True)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_report(denominator_path=args.denominator, readiness_path=args.readiness)
    except (CoverageError, OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    serialized = canonical_json(report)
    if args.output:
        _write_output(args.output, report)
        print(f"Wrote deterministic curriculum coverage receipt: {args.output}")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
