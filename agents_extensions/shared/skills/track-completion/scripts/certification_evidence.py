"""Strict, side-effect-free certification evidence reader and validator."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "curriculum-lifecycle" / "schema" / "certification-evidence.v1.schema.json"
)
QUALIFICATION_SCHEMA_PATH = SCHEMA_PATH.with_name("production-qg-qualification.v1.schema.json")
ARMING_SCHEMA_PATH = SCHEMA_PATH.with_name("production-qg-human-arming.v1.schema.json")
MATERIAL_SEVERITIES = frozenset({"blocker", "high", "medium"})


class CertificationEvidenceError(ValueError):
    """Raised when evidence is not a complete, current certification record."""


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    path: Path
    sha256: str
    value: dict[str, Any]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _schema() -> dict[str, Any]:
    try:
        value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CertificationEvidenceError(f"invalid certification evidence schema: {exc}") from exc
    if not isinstance(value, dict):
        raise CertificationEvidenceError("certification evidence schema must be an object")
    return value


def read_evidence(path: Path) -> EvidenceArtifact:
    """Read one explicit JSON artifact exactly; never inspect caches or runtime state."""
    if not path.is_file():
        raise CertificationEvidenceError(f"evidence artifact does not exist: {path}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CertificationEvidenceError(f"invalid certification evidence: {exc}") from exc
    validate_evidence_value(value)
    return EvidenceArtifact(path=path.resolve(), sha256=_sha256(raw), value=value)


def validate_evidence_value(value: object) -> None:
    """Validate a parsed record before it can influence a ledger projection."""
    if not isinstance(value, dict):
        raise CertificationEvidenceError("certification evidence must be a JSON object")
    errors = sorted(Draft202012Validator(_schema()).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise CertificationEvidenceError(f"certification evidence schema rejection at {where}: {error.message}")


def require_current(artifact: EvidenceArtifact, *, kind: str, expected: Mapping[str, Any]) -> None:
    """Require exact, declared identity bindings; unknown/missing values fail closed."""
    value = artifact.value
    validate_evidence_value(value)
    if value["kind"] != kind:
        raise CertificationEvidenceError(f"expected {kind} evidence, received {value['kind']}")
    for key in ("target", "preparation_identity", "learner_hashes"):
        if value.get(key) != expected.get(key):
            raise CertificationEvidenceError(f"stale certification evidence: {key} differs")
    if value["profile"] != expected.get("profile"):
        raise CertificationEvidenceError("stale certification evidence: profile differs")


def independent_review_passes(
    artifact: EvidenceArtifact,
    *,
    author_groups: set[str],
    author_families: set[str],
    config: Mapping[str, Any],
    track_policy: Mapping[str, Any],
) -> bool:
    review = artifact.value["review"]
    material_open = any(
        item["severity"] in MATERIAL_SEVERITIES and not item["resolved"] for item in review["material_findings"]
    )
    return bool(
        review["verdict"] == "PASS"
        and review["resolution_state"] == "RESOLVED"
        and not material_open
        and _reviewer_group(review["reviewer_family"], config) not in author_groups
        and set(review["author_families"]) == author_families
        and review["reviewer_family"] not in set(track_policy.get("forbidden_reviewer_families", ()))
        and (
            not track_policy.get("allowed_reviewer_groups")
            or _reviewer_group(review["reviewer_family"], config) in set(track_policy["allowed_reviewer_groups"])
        )
    )


def _reviewer_group(family: str, config: Mapping[str, Any]) -> str:
    group = config["review_family_groups"].get(str(family).lower())
    if not isinstance(group, str) or not group:
        raise CertificationEvidenceError(f"unknown reviewer family: {family}")
    return group


def integration_passes(artifact: EvidenceArtifact) -> bool:
    integration = artifact.value["integration"]
    telemetry = integration["telemetry"]
    worktree = Path(integration["worktree"])
    if worktree.is_absolute() or ".." in worktree.parts:
        return False
    return bool(
        integration["ci_gate"] == "PASS"
        and integration["review_gate"] == "PASS"
        and integration["cleanup"]["state"] == "COMPLETE"
        and (not telemetry["applicable"] or bool(telemetry["receipt"]))
    )


def load_authorization(
    qg_profile: Mapping[str, Any],
    *,
    repo_root: Path,
    expected_profile: Mapping[str, Any],
    expected_identity: Mapping[str, str],
) -> dict[str, Any]:
    """Load tracked qualification + human arming records, never infer arming from presence."""
    if qg_profile.get("mode") != "armed-canary":
        raise CertificationEvidenceError("production QG profile is not armed")
    paths = [repo_root / str(qg_profile[key]) for key in ("qualification_artifact", "human_arming_artifact")]
    try:
        qualification, arming = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CertificationEvidenceError(f"invalid tracked QG authorization: {exc}") from exc
    if not isinstance(qualification, Mapping) or not isinstance(arming, Mapping):
        raise CertificationEvidenceError("tracked QG authorization must be JSON objects")
    for value, schema_path, label in (
        (qualification, QUALIFICATION_SCHEMA_PATH, "qualification"),
        (arming, ARMING_SCHEMA_PATH, "human arming"),
    ):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(value))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CertificationEvidenceError(f"invalid {label} schema: {exc}") from exc
        if errors:
            raise CertificationEvidenceError(f"invalid {label} artifact: {errors[0].message}")
    qualification_sha = _sha256(paths[0].read_bytes())
    if (
        qualification.get("schema_version") != "production-qg-qualification.v1"
        or qualification.get("verdict") != "PASS"
    ):
        raise CertificationEvidenceError("qualification is not a passing v1 artifact")
    if qualification.get("profile") != dict(expected_profile) or qualification.get("identity") != dict(
        expected_identity
    ):
        raise CertificationEvidenceError("qualification does not bind the current profile/QG contract")
    route = qualification.get("route")
    required = ("family", "model", "route", "lineage", "canary", "budget", "circuit", "resume")
    if not isinstance(route, Mapping) or any(not route.get(key) for key in required):
        raise CertificationEvidenceError("qualification lacks exact route/canary/budget/circuit/resume binding")
    if (
        arming.get("schema_version") != "production-qg-human-arming.v1"
        or arming.get("decision") != "ARMED"
        or arming.get("actor_type") != "human"
    ):
        raise CertificationEvidenceError("arming is not an explicit human ARMED decision")
    if (
        arming.get("qualification_sha256") != qualification_sha
        or arming.get("profile") != dict(expected_profile)
        or arming.get("route") != route
    ):
        raise CertificationEvidenceError("arming does not bind this qualification/profile/route")
    return {
        "qualification_sha256": qualification_sha,
        "human_arming_sha256": _sha256(paths[1].read_bytes()),
        "route": dict(route),
    }


def production_qg_passes(
    artifact: EvidenceArtifact, *, expected_identity: Mapping[str, str], seminar: bool, authorization: Mapping[str, Any]
) -> bool:
    """Validate a captured canonical QG run with the production validators, read-only."""
    from scripts.audit import llm_reviewer_dispatch, qg_schema

    value = artifact.value
    if value["authorization"]["identity"] != dict(expected_identity):
        return False
    record, tier2 = value["canonical_record"], value["tier2"]
    try:
        qg_schema.validate_record(record)
        qg_schema.validate_reviewer_payload(tier2["payload"], "seminar" if seminar else "core")
    except (ValueError, KeyError, TypeError):
        return False
    dispatch = tier2["dispatch"]
    route = authorization["route"]
    if any(
        dispatch.get(key) != route[key] for key in ("reviewer_family", "reviewer_model_id", "route_name", "lineage")
    ):
        return False
    if tier2["status"] != "ran" or record.get("terminal_verdict") != "PASS":
        return False
    if dispatch.get("shadow") is True or dispatch.get("advisory") is True:
        return False
    cache_regate = tier2.get("cache_regate", dispatch.get("cache_regate"))
    if cache_regate not in {None, "replayed"}:
        return False
    if tier2["gate_outcomes"].get("status") != "ran":
        return False
    try:
        grounded = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
            tier2["payload"], dispatch, policy_family="seminar" if seminar else "core", gate_version="v2"
        )
    except (ValueError, TypeError):
        return False
    if seminar and (
        grounded.invalid_fact_checks
        or llm_reviewer_dispatch.factual_sweep_incomplete(
            grounded.payload, policy_family="seminar", invalid_fact_checks=grounded.invalid_fact_checks
        )
    ):
        return False
    return grounded.payload == tier2["payload"]


def production_qg_stability_key(artifact: EvidenceArtifact) -> str:
    qg = artifact.value
    payload = {
        "target": qg["target"],
        "profile": qg["profile"],
        "preparation": qg["preparation_identity"],
        "learner": qg["learner_hashes"],
        "identity": qg["authorization"]["identity"],
        "dispatch": qg["tier2"]["dispatch"],
    }
    return _sha256(_stable(payload).encode("utf-8"))


def production_qg_material_fingerprint(artifact: EvidenceArtifact) -> str:
    tier2 = artifact.value["tier2"]
    material = [item for item in tier2["payload"].get("findings", []) if item.get("severity") in MATERIAL_SEVERITIES]
    return _sha256(
        _stable(
            {
                "terminal": artifact.value["canonical_record"].get("terminal_verdict"),
                "findings": sorted(material, key=_stable),
            }
        ).encode("utf-8")
    )
