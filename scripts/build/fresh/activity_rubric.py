"""A1's fixed activity rubric and exact-byte adoption boundary (#10109).

This checks coverage and provenance bindings, never pedagogical semantics.
The approval document is external to the candidate bytes and remains pending
until the driver supplies the independently graded, designated approval.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RUBRIC_PATH = "docs/best-practices/a1-activity-rubric.yaml"
APPROVAL_PATH = "docs/best-practices/a1-activity-rubric.approval.yaml"
PIN_PATHS = {"activity_rubric": RUBRIC_PATH, "activity_rubric_approval": APPROVAL_PATH}
ALIASES = {"multiple-choice": "quiz"}
SHA = re.compile(r"[0-9a-f]{64}")


class ActivityRubricError(ValueError):
    """A rubric, adoption, inventory or review-return refusal."""


def is_a1(level: str) -> bool:
    return level.lower().split("-")[0] == "a1"


def _mapping(data: bytes, label: str) -> dict:
    try:
        result = yaml.safe_load(data)
    except (yaml.YAMLError, UnicodeError) as exc:
        raise ActivityRubricError(f"{label}: invalid YAML") from exc
    if not isinstance(result, dict):
        raise ActivityRubricError(f"{label}: expected a mapping")
    return result


def validate_rubric(data: bytes) -> dict:
    """Validate the 20-row registry against the existing schema and placement table."""
    doc = _mapping(data, "activity_rubric")
    schema = json.loads((REPO_ROOT / "schemas/activities-a1.schema.json").read_bytes())
    types = {item["$ref"].rsplit("/", 1)[1].removesuffix("-a1") for item in schema["items"]["oneOf"]}
    placements = yaml.safe_load((REPO_ROOT / "scripts/curriculum/validate/placement_table.yaml").read_bytes())[
        "levels"
    ]["a1"]
    clauses = doc.get("clauses")
    rows = doc.get("rows")
    if doc.get("rubric_version") != 1 or not isinstance(clauses, list) or not isinstance(rows, list):
        raise ActivityRubricError("activity_rubric: expected version 1, clauses and rows")
    if doc.get("aliases") != ALIASES:
        raise ActivityRubricError("activity_rubric: aliases must explicitly map multiple-choice to quiz")
    ids: set[str] = set()
    for clause in clauses:
        if not isinstance(clause, dict) or not re.fullmatch(r"A1-[CB][0-9]{2}", str(clause.get("id"))):
            raise ActivityRubricError("activity_rubric: invalid clause ID")
        if clause["id"] in ids:
            raise ActivityRubricError("activity_rubric: duplicate clause ID")
        ids.add(clause["id"])
        if not clause.get("text") or not clause.get("references"):
            raise ActivityRubricError(f"{clause['id']}: text and references required")
    row_ids: set[str] = set()
    row_types: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not re.fullmatch(r"A1-ACT-[0-9]{3}", str(row.get("id"))):
            raise ActivityRubricError("activity_rubric: invalid row ID")
        if row["id"] in row_ids or row.get("type") in row_types:
            raise ActivityRubricError("activity_rubric: duplicate row ID or type")
        row_ids.add(row["id"])
        row_types.add(row.get("type"))
        if row.get("placement") != placements.get(row.get("type")):
            raise ActivityRubricError(f"{row['id']}: placement disagrees with placement_table.yaml")
        if row.get("verdict") not in {"conditional", "scaffold", "unscored_support", "forbidden"}:
            raise ActivityRubricError(f"{row['id']}: invalid verdict")
        if (row.get("type") == "classify") != (row["verdict"] == "forbidden"):
            raise ActivityRubricError("A1-ACT-002: classify must be the sole forbidden row")
        applicability = row.get("applicability")
        if not isinstance(applicability, dict) or set(applicability) != ids:
            raise ActivityRubricError(f"{row['id']}: fixed applicability must cover every clause")
        for clause, entry in applicability.items():
            if (
                not isinstance(entry, dict)
                or type(entry.get("applies")) is not bool
                or not isinstance(entry.get("reason"), str)
                or not entry["reason"].strip()
            ):
                raise ActivityRubricError(f"{row['id']}/{clause}: applicability and reason required")
        if not row.get("conditions") or not row.get("bans") or not row.get("references"):
            raise ActivityRubricError(f"{row['id']}: conditions, bans and references required")
    if row_types != types or len(rows) != 20:
        raise ActivityRubricError("activity_rubric: rows must cover exactly all 20 schema types")
    sources = doc.get("sources")
    if not isinstance(sources, dict):
        raise ActivityRubricError("activity_rubric: source ledger required")
    for record in [*clauses, *rows]:
        if not isinstance(record["references"], list) or not set(record["references"]) <= sources.keys():
            raise ActivityRubricError(f"{record['id']}: unknown source reference")
    for key, source in sources.items():
        if (
            not isinstance(source, dict)
            or source.get("role") not in {"S", "A", "U", "P"}
            or not source.get("locator")
            or not source.get("limit")
        ):
            raise ActivityRubricError(f"{key}: source role, locator and limit required")
        if source.get("rights") == "private_permission":
            raise ActivityRubricError("activity_rubric: private_permission sources cannot be published")
    return doc


def validate_approval(data: bytes, rubric_digest: str) -> dict:
    """Refuse pending adoption, drift and missing designated-approval provenance."""
    doc = _mapping(data, "activity_rubric_approval")
    if doc.get("status") != "approved":
        raise ActivityRubricError("activity_rubric_approval: adoption pending")
    if doc.get("rubric_sha256") != rubric_digest:
        raise ActivityRubricError("activity_rubric_approval: approved digest differs from candidate bytes")
    if (
        doc.get("author_model") != "gpt-6.1-sol"
        or doc.get("approver_model") != "claude-opus-5-5"
        or not isinstance(doc.get("approval_reference"), str)
        or not doc["approval_reference"].strip()
        or not SHA.fullmatch(str(doc.get("approval_sha256", "")))
    ):
        raise ActivityRubricError("activity_rubric_approval: designated approval reference/digest required")
    return doc


def pin_contract(level: str, inputs: dict) -> None:
    """Require both canonical A1 pins; refuse the new fields on every other level."""
    if not is_a1(level):
        if isinstance(inputs, dict) and set(inputs) & PIN_PATHS.keys():
            raise ActivityRubricError("activity_rubric: pins are A1-only")
        return
    if not isinstance(inputs, dict):
        raise ActivityRubricError("activity_rubric: missing A1 pin mapping")
    for key, path in PIN_PATHS.items():
        pin = inputs.get(key)
        if (
            not isinstance(pin, dict)
            or set(pin) != {"path", "sha256"}
            or pin.get("path") != path
            or not SHA.fullmatch(str(pin.get("sha256", "")))
        ):
            raise ActivityRubricError(f"activity_rubric: missing or invalid canonical {key} pin")


def pinned_rubric(level: str, inputs: dict, read_bytes: Any) -> dict | None:
    """Read only pinned, digest-matching candidate and approval bytes."""
    pin_contract(level, inputs)
    if not is_a1(level):
        return None
    content: dict[str, bytes] = {}
    for key, path in PIN_PATHS.items():
        content[key] = read_bytes(path)
        if hashlib.sha256(content[key]).hexdigest() != inputs[key]["sha256"]:
            raise ActivityRubricError(f"activity_rubric: changed {key} bytes")
    doc = validate_rubric(content["activity_rubric"])
    validate_approval(content["activity_rubric_approval"], inputs["activity_rubric"]["sha256"])
    return doc


def approved_pins(level: str, root: Path) -> dict:
    """Pin adopted bytes when creating a new attempt; never repair an existing pin."""
    if not is_a1(level):
        return {}
    try:
        inputs = {
            key: {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
            for key, path in PIN_PATHS.items()
        }
        pinned_rubric(level, inputs, lambda path: (root / path).read_bytes())
    except OSError as exc:
        raise ActivityRubricError("activity_rubric: candidate/approval file unavailable") from exc
    return inputs


def activity_table(plan: dict, rubric: dict, lesson: int | None = None) -> list[dict]:
    """Derive actual IDs/types from the pinned plan, refusing duplicates or unmapped types."""
    by_type = {row["type"]: row for row in rubric["rows"]}
    result: list[dict] = []
    for entry in plan.get("lessons", []):
        if lesson is not None and entry.get("n") != lesson:
            continue
        seen: set[str] = set()
        for activity in entry.get("activities", []):
            aid, typ = activity.get("id"), activity.get("type")
            row = by_type.get(ALIASES.get(typ, typ))
            if not isinstance(aid, str) or not aid or aid in seen or row is None:
                raise ActivityRubricError("activity_rubric: duplicate/missing activity ID or unmapped type")
            if row["verdict"] == "forbidden":
                raise ActivityRubricError(f"{row['id']}: classify forbidden")
            seen.add(aid)
            result.append(
                {
                    "activity": aid,
                    "lesson": entry["n"],
                    "type": typ,
                    "row": row["id"],
                    "clauses": [key for key, value in row["applicability"].items() if value["applies"]],
                }
            )
    if lesson is not None and not any(entry.get("n") == lesson for entry in plan.get("lessons", [])):
        raise ActivityRubricError("activity_rubric: pinned plan has no requested lesson")
    return result


def review_errors(review: dict, level: str, table: list[dict], rubric: dict | None) -> list[str]:
    """Bind coverage and activity findings to fixed clauses; semantics stay with reviewers."""
    raw_findings = review.get("findings")
    findings = [item for item in raw_findings if isinstance(item, dict)] if isinstance(raw_findings, list) else []
    if not is_a1(level):
        return (
            ["activity_rubric: return fields are A1-only"]
            if ("activity_rubric" in review or any("rubric" in item for item in findings))
            else []
        )
    assert rubric is not None
    errors: list[str] = []
    actual: dict[str, list[dict]] = {}
    for row in table:
        actual.setdefault(row["activity"], []).append(row)
    coverage = review.get("activity_rubric")
    if not isinstance(coverage, dict) or set(coverage) != set(actual):
        return ["activity_rubric: coverage keys must exactly match actual activity IDs"]
    linked: dict[str, set[str]] = {aid: set() for aid in actual}
    for finding in findings:
        locs = finding.get("locations", [])
        locs = locs if isinstance(locs, list) else []
        scope = finding.get("scope")
        if isinstance(scope, dict):
            locs = [*locs, scope]
        aids = {loc["activity"] for loc in locs if isinstance(loc, dict) and isinstance(loc.get("activity"), str)}
        binding = finding.get("rubric")
        if finding.get("dimension") == "activity" and not aids:
            errors.append(f"{finding.get('id')}: A1 activity finding must name actual activities")
        if not aids:
            if binding is not None:
                errors.append(f"{finding.get('id')}: rubric binding needs an activity location/scope")
            continue
        if not aids <= actual.keys():
            errors.append(f"{finding.get('id')}: unknown activity location")
            continue
        if not isinstance(binding, dict) or set(binding) != {"row", "clause"}:
            errors.append(f"{finding.get('id')}: A1 activity finding requires rubric row/clause")
            continue
        for aid in aids:
            occurrences = [loc for loc in locs if isinstance(loc, dict) and loc.get("activity") == aid]
            for loc in occurrences:
                matches = [
                    row for row in actual[aid] if review.get("kind") != "plan" or loc.get("lesson") == row["lesson"]
                ]
                if not matches:
                    errors.append(f"{finding.get('id')}: activity belongs to another lesson")
                elif any(binding["row"] != row["row"] or binding["clause"] not in row["clauses"] for row in matches):
                    errors.append(f"{finding.get('id')}: wrong row or inapplicable clause for {aid}")
            if isinstance(finding.get("id"), str):
                linked[aid].add(finding["id"])
        if finding.get("severity") not in {"MAJOR", "BLOCKER"}:
            errors.append(f"{finding.get('id')}: rubric ban/unmet necessary condition requires at least MAJOR")
        if "unsupported_by_source" in finding and finding.get("severity") != "MAJOR":
            errors.append(f"{finding.get('id')}: unsupported approval-critical activity claim requires MAJOR")
    for aid, value in coverage.items():
        if value == "clean":
            if linked[aid]:
                errors.append(f"{aid}: clean cannot coexist with an activity finding")
        elif (
            not isinstance(value, list)
            or not value
            or not all(isinstance(ref, str) for ref in value)
            or len(set(value)) != len(value)
            or set(value) != linked[aid]
        ):
            errors.append(f"{aid}: coverage must list exactly its activity finding IDs")
    return errors
