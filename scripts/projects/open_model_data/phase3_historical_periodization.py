#!/usr/bin/env python3
"""Freeze and apply attributed historical-Ukrainian periodizations.

The registry preserves competing scholarly frameworks. It never chooses one
canonical chronology, mutates a modern Atlas headword, or turns a historical
form into modern correction gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
FREEZE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_historical_periodization_freeze_v1.json"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_historical_periodization_freeze_v1.schema.json"
SCHEMA_VERSION = "phase3_historical_periodization_freeze_v1"
ASSIGNMENT_SCHEMA_VERSION = "phase3_historical_periodization_assignment_v1"
EXPECTED_FREEZE_SHA256 = "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198"
EXPECTED_BINDINGS = {
    "phase3_reboot_prompt_v3_sha256": ("5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"),
    "phase3_recovery_prompt_v2_sha256": ("298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"),
    "phase3_complete_source_policy_v4_sha256": ("98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"),
}
REQUIRED_FRAMEWORKS = {
    "university_five_stage_synthesis": 5,
    "shevelov_detailed_six_period": 6,
    "nimchuk_five_stage_with_middle_subperiods": 5,
}


class HistoricalPeriodizationError(ValueError):
    """The comparative periodization freeze or assignment is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalPeriodizationError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalPeriodizationError(f"cannot read periodization JSON: {path}") from exc
    require(isinstance(value, dict), "periodization freeze must be a JSON object")
    return value


def _schema_validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(_schema_validator().iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "freeze"
        raise HistoricalPeriodizationError(f"periodization schema violation at {location}: {errors[0].message}")


def _validate_boundary(boundary: Mapping[str, Any], label: str) -> None:
    earliest = boundary["earliest_year"]
    latest = boundary["latest_year"]
    if earliest is None or latest is None:
        require(earliest is None and latest is None, f"{label} boundary must be wholly open or bounded")
        require(boundary["precision"] == "open", f"{label} open boundary must use open precision")
    else:
        require(earliest <= latest, f"{label} boundary range is reversed")
        require(boundary["precision"] != "open", f"{label} bounded boundary cannot use open precision")


def validate_freeze(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate schema, evidence closure, chronology, and non-collapse safeguards."""
    freeze = json.loads(json.dumps(value, ensure_ascii=False))
    _validate_schema(freeze)
    require(freeze["schema_version"] == SCHEMA_VERSION, "periodization schema version drift")
    require(freeze["bindings"] == EXPECTED_BINDINGS, "periodization bindings drift")

    body = {key: item for key, item in freeze.items() if key != "receipt_sha256"}
    expected_receipt = hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest()
    require(freeze["receipt_sha256"] == expected_receipt, "periodization receipt seal mismatch")

    evidence = freeze["evidence"]
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    require(len(evidence_by_id) == len(evidence), "duplicate periodization evidence ID")
    for item in evidence:
        locator = item["locator"]
        if item["full_text_state"] == "locally_acquired":
            require(item["document_sha256"] is not None, "acquired evidence lacks a document hash")
            require(locator["project_relative_path"] is not None, "acquired evidence lacks a path")
        else:
            require(item["document_sha256"] is None, "bibliographic-only evidence cannot claim bytes")
            require(locator["project_relative_path"] is None, "bibliographic-only evidence cannot claim a path")
            require(
                item["authority"] == "bibliographic_only",
                "bibliographic-only evidence cannot claim content authority",
            )

    frameworks = freeze["frameworks"]
    framework_by_id = {item["framework_id"]: item for item in frameworks}
    require(len(framework_by_id) == len(frameworks), "duplicate periodization framework ID")
    require(REQUIRED_FRAMEWORKS.keys() <= framework_by_id.keys(), "required framework is missing")

    for framework_id, framework in framework_by_id.items():
        framework_evidence = set(framework["evidence_ids"])
        require(framework_evidence <= evidence_by_id.keys(), f"{framework_id}: unknown framework evidence")
        for evidence_id in framework_evidence:
            require(
                framework_id in evidence_by_id[evidence_id]["supports_framework_ids"],
                f"{framework_id}: evidence does not declare framework support",
            )

        stages = framework["stages"]
        stage_by_id = {item["stage_id"]: item for item in stages}
        require(len(stage_by_id) == len(stages), f"{framework_id}: duplicate stage ID")
        primary_count = sum(item["parent_stage_id"] is None for item in stages)
        require(primary_count == framework["primary_stage_count"], f"{framework_id}: primary-stage count drift")
        if framework_id in REQUIRED_FRAMEWORKS:
            require(
                primary_count == REQUIRED_FRAMEWORKS[framework_id],
                f"{framework_id}: frozen primary-stage denominator drift",
            )

        for stage in stages:
            parent = stage["parent_stage_id"]
            require(parent is None or parent in stage_by_id, f"{framework_id}: unknown parent stage")
            require(parent != stage["stage_id"], f"{framework_id}: stage cannot parent itself")
            stage_evidence = set(stage["evidence_ids"])
            require(stage_evidence <= framework_evidence, f"{framework_id}: stage evidence escapes framework")
            _validate_boundary(stage["start_boundary"], f"{framework_id}:{stage['stage_id']}:start")
            _validate_boundary(stage["end_boundary"], f"{framework_id}:{stage['stage_id']}:end")
            start = stage["start_boundary"]["earliest_year"]
            end = stage["end_boundary"]["latest_year"]
            require(start is None or end is None or start <= end, f"{framework_id}: reversed stage")

    evidence_frameworks = {framework_id for item in evidence for framework_id in item["supports_framework_ids"]}
    require(evidence_frameworks <= framework_by_id.keys(), "evidence supports an unknown framework")
    gap_ids = {item["gap_id"] for item in freeze["remaining_gaps"]}
    require(
        "nimchuk_1997_1998_primary_full_text" in gap_ids,
        "unacquired Nimchuk primary text gap must remain explicit",
    )
    return freeze


def load_freeze(path: Path = FREEZE_PATH) -> dict[str, Any]:
    """Load the exact tracked freeze and reject byte drift at its canonical path."""
    path = Path(path)
    freeze = validate_freeze(_read_json(path))
    if path.resolve() == FREEZE_PATH.resolve():
        require(sha256_file(path) == EXPECTED_FREEZE_SHA256, "tracked periodization freeze byte drift")
    return freeze


def validate_acquired_evidence(freeze: Mapping[str, Any], source_root: Path) -> dict[str, Any]:
    """Prove every locally acquired source against its project-relative SHA-256."""
    source_root = Path(source_root).resolve()
    verified: list[dict[str, str]] = []
    for item in freeze["evidence"]:
        if item["full_text_state"] != "locally_acquired":
            continue
        relative = Path(item["locator"]["project_relative_path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe evidence path")
        candidate = (source_root / relative).resolve()
        require(candidate.is_relative_to(source_root), "evidence path escapes source root")
        require(candidate.is_file(), f"missing acquired evidence: {relative.as_posix()}")
        actual = sha256_file(candidate)
        require(actual == item["document_sha256"], f"evidence byte drift: {item['evidence_id']}")
        verified.append(
            {
                "evidence_id": item["evidence_id"],
                "project_relative_path": relative.as_posix(),
                "document_sha256": actual,
            }
        )
    return {
        "schema_version": "phase3_historical_periodization_source_verification_v1",
        "verified_source_count": len(verified),
        "verified_sources": verified,
        "provider_calls": False,
    }


def _year_match(stage: Mapping[str, Any], year: int) -> str | None:
    start = stage["start_boundary"]
    end = stage["end_boundary"]
    earliest_start = start["earliest_year"]
    latest_start = start["latest_year"]
    earliest_end = end["earliest_year"]
    latest_end = end["latest_year"]

    possible = (earliest_start is None or year >= earliest_start) and (latest_end is None or year <= latest_end)
    if not possible:
        return None
    definite = (latest_start is None or year >= latest_start) and (earliest_end is None or year <= earliest_end)
    return "definite" if definite else "possible_boundary_overlap"


def classify_year(year: int, *, freeze: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return every applicable stage without choosing a canonical framework."""
    require(isinstance(year, int), "historical year must be an integer")
    checked = load_freeze() if freeze is None else validate_freeze(freeze)
    framework_matches: list[dict[str, Any]] = []
    for framework in checked["frameworks"]:
        matches = []
        for stage in framework["stages"]:
            status = _year_match(stage, year)
            if status is None:
                continue
            matches.append(
                {
                    "stage_id": stage["stage_id"],
                    "stage_label_uk": stage["label_uk"],
                    "parent_stage_id": stage["parent_stage_id"],
                    "match_status": status,
                    "start_label": stage["start_boundary"]["label"],
                    "end_label": stage["end_boundary"]["label"],
                    "evidence_ids": list(stage["evidence_ids"]),
                    "ambiguity": list(stage["ambiguity"]),
                }
            )
        require(matches, f"{framework['framework_id']}: year has no periodization match")
        framework_matches.append(
            {
                "framework_id": framework["framework_id"],
                "attributed_to": framework["attributed_to"],
                "authority": framework["authority"],
                "matches": matches,
            }
        )
    return {
        "schema_version": ASSIGNMENT_SCHEMA_VERSION,
        "year": year,
        "canonical_framework_id": None,
        "framework_matches": framework_matches,
        "safeguards": dict(checked["scope"]),
        "provider_calls": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=FREEZE_PATH)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--year", type=int)
    return parser


def main() -> int:
    args = _parser().parse_args()
    freeze = load_freeze(args.freeze)
    output: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "freeze_sha256": sha256_file(args.freeze),
        "framework_count": len(freeze["frameworks"]),
        "primary_stage_count": sum(item["primary_stage_count"] for item in freeze["frameworks"]),
        "status": freeze["status"],
        "provider_calls": False,
    }
    if args.source_root is not None:
        output["source_verification"] = validate_acquired_evidence(freeze, args.source_root)
    if args.year is not None:
        output["assignment"] = classify_year(args.year, freeze=freeze)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
