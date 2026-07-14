"""Strict, side-effect-free certification evidence reader and validator."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "curriculum-lifecycle" / "schema" / "certification-evidence.v1.schema.json"
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


def independent_review_passes(artifact: EvidenceArtifact, *, author_groups: set[str], allowed_groups: set[str] | None = None) -> bool:
    review = artifact.value["review"]
    material_open = any(
        item["severity"] in MATERIAL_SEVERITIES and not item["resolved"]
        for item in review["material_findings"]
    )
    return bool(
        review["verdict"] == "PASS"
        and review["resolution_state"] == "RESOLVED"
        and not material_open
        and review["reviewer_group"] not in author_groups
        and (not allowed_groups or review["reviewer_group"] in allowed_groups)
    )


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


def _confirmed_facts_are_grounded(qg: Mapping[str, Any]) -> bool:
    events = {event["id"]: event for event in qg["tool_events"]}
    for check in qg["fact_checks"]:
        if check["verdict"] != "CONFIRMED":
            continue
        event = events.get(check.get("tool_event_id"))
        excerpt = check.get("excerpt")
        if not event or not isinstance(excerpt, str) or not excerpt:
            return False
        if not str(event["tool_name"]).startswith("mcp__sources__"):
            return False
        # A light ellipsis may omit only a contiguous middle span of real output.
        pieces = excerpt.split("…")
        if len(pieces) > 2 or any(piece and piece not in event["output"] for piece in pieces):
            return False
        if len(pieces) == 2 and event["output"].find(pieces[0]) > event["output"].find(pieces[1]):
            return False
    return True


def production_qg_passes(artifact: EvidenceArtifact, *, expected_identity: Mapping[str, str], seminar: bool) -> bool:
    qg = artifact.value["qg"]
    if qg["verdict"] != "PASS" or qg["shadow"] or qg["cache_regate"] == "unavailable":
        return False
    if qg["completion"] != "COMPLETE" or qg["canary"]["status"] != "PASS":
        return False
    if qg["budget"]["status"] != "WITHIN_BUDGET" or qg["circuit"] != "CLOSED":
        return False
    if qg["canary"]["route"] != qg["reviewer"]["route"]:
        return False
    if dict(qg["identity"]) != dict(expected_identity):
        return False
    return not seminar or _confirmed_facts_are_grounded(qg)


def production_qg_stability_key(artifact: EvidenceArtifact) -> str:
    qg = artifact.value["qg"]
    payload = {"target": artifact.value["target"], "profile": artifact.value["profile"], "preparation": artifact.value["preparation_identity"], "learner": artifact.value["learner_hashes"], "identity": qg["identity"], "reviewer": qg["reviewer"]}
    return _sha256(_stable(payload).encode("utf-8"))


def production_qg_material_fingerprint(artifact: EvidenceArtifact) -> str:
    material = [item for item in artifact.value["qg"]["findings"] if item.get("severity") in MATERIAL_SEVERITIES]
    return _sha256(_stable(sorted(material, key=_stable)).encode("utf-8"))
