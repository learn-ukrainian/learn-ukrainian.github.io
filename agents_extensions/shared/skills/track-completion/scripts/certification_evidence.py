"""Strict, side-effect-free certification evidence reader and validator."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "curriculum-lifecycle" / "schema" / "certification-evidence.v1.schema.json"
)
QUALIFICATION_SCHEMA_PATH = SCHEMA_PATH.with_name("production-qg-qualification.v1.schema.json")
ARMING_SCHEMA_PATH = SCHEMA_PATH.with_name("production-qg-human-arming.v1.schema.json")
PBR_MATERIAL_SEVERITIES = frozenset({"blocker", "high", "medium"})
QG_MATERIAL_SEVERITIES = frozenset({"critical", "warning"})
QG_IDENTITY_KEYS = frozenset(
    {
        "gate",
        "profile",
        "prompt",
        "checker",
        "checker_config",
        "policy",
        "schema",
        "tool",
        "routing",
        "canary",
        "cost",
        "circuit",
        "resume",
    }
)


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


def _normalize_family(value: object) -> str:
    return str(value or "").strip().casefold()


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
        item["severity"] in PBR_MATERIAL_SEVERITIES and not item["resolved"] for item in review["material_findings"]
    )
    reviewer_family = _normalize_family(review["reviewer_family"])
    recorded_authors = {_normalize_family(family) for family in review["author_families"]}
    forbidden = {_normalize_family(item) for item in track_policy.get("forbidden_reviewer_families", ())}
    allowed = {_normalize_family(item) for item in track_policy.get("allowed_reviewer_groups", ())}
    reviewer_group = _reviewer_group(reviewer_family, config)
    return bool(
        review["verdict"] == "PASS"
        and review["resolution_state"] == "RESOLVED"
        and not material_open
        and reviewer_group not in author_groups
        and recorded_authors == {_normalize_family(family) for family in author_families}
        and reviewer_family not in forbidden
        and (not allowed or reviewer_group in allowed)
    )


def _reviewer_group(family: str, config: Mapping[str, Any]) -> str:
    group = config["review_family_groups"].get(_normalize_family(family))
    if not isinstance(group, str) or not group:
        raise CertificationEvidenceError(f"unknown reviewer family: {family}")
    return _normalize_family(group)


def integration_passes(artifact: EvidenceArtifact) -> bool:
    integration = artifact.value["integration"]
    telemetry = integration["telemetry"]
    premerge = integration["premerge"]
    worktree = Path(integration["worktree"])
    if worktree.is_absolute() or ".." in worktree.parts:
        return False
    return bool(
        integration["ci_gate"] == "PASS"
        and integration["review_gate"] == "PASS"
        and all(value == "PASS" for value in premerge.values())
        and integration["cleanup"]["state"] == "COMPLETE"
        and (not telemetry["applicable"] or bool(telemetry["receipt"]))
    )


def _load_and_validate_json(path: Path, schema_path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CertificationEvidenceError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise CertificationEvidenceError(f"{label} must be a JSON object")
    if errors:
        raise CertificationEvidenceError(f"invalid {label} artifact: {errors[0].message}")
    return value


def _qualification_route_is_current(route: Mapping[str, Any], identity: Mapping[str, str]) -> bool:
    canary = route["canary"]
    budget = route["budget"]
    circuit = route["circuit"]
    resume = route["resume"]
    return bool(
        canary["route"] == route["route"]
        and canary["model"] == route["model"]
        and canary["prompt_identity"] == identity["prompt"]
        and canary["gate_identity"] == identity["gate"]
        and budget["policy_sha256"] == identity["cost"]
        and circuit["policy_sha256"] == identity["circuit"]
        and resume["contract_sha256"] == identity["resume"]
    )


def runtime_authorization_is_current(
    authorization: Mapping[str, Any], expected_identity: Mapping[str, str]
) -> bool:
    """Return whether a recorded authorization still binds the live QG contracts."""
    route = authorization.get("route")
    return bool(
        isinstance(route, Mapping)
        and set(expected_identity) == QG_IDENTITY_KEYS
        and _qualification_route_is_current(route, expected_identity)
    )


def load_authorization(
    qg_profile: Mapping[str, Any],
    *,
    repo_root: Path,
    expected_profile: Mapping[str, Any],
    expected_identity: Mapping[str, str],
) -> dict[str, Any]:
    """Load explicit human authorization and bind it to current QG contracts."""
    if qg_profile.get("mode") != "armed-canary":
        raise CertificationEvidenceError("production QG profile is not armed")
    if set(expected_identity) != QG_IDENTITY_KEYS:
        raise CertificationEvidenceError("current production-QG identity must contain exactly the declared 13 classes")
    paths = [repo_root / str(qg_profile[key]) for key in ("qualification_artifact", "human_arming_artifact")]
    qualification = _load_and_validate_json(paths[0], QUALIFICATION_SCHEMA_PATH, "qualification")
    arming = _load_and_validate_json(paths[1], ARMING_SCHEMA_PATH, "human arming")
    qualification_sha = _sha256(paths[0].read_bytes())
    if qualification["profile"] != dict(expected_profile) or qualification["identity"] != dict(expected_identity):
        raise CertificationEvidenceError("qualification does not bind the current profile/QG contract")
    route = qualification["route"]
    if not _qualification_route_is_current(route, expected_identity):
        raise CertificationEvidenceError("qualification route/canary/budget/circuit/resume is not current")
    if (
        arming["qualification_sha256"] != qualification_sha
        or arming["profile"] != dict(expected_profile)
        or arming["route"] != route
        or arming["budget"] != route["budget"]
    ):
        raise CertificationEvidenceError("arming does not bind this qualification/profile/route/budget")
    return {
        "qualification_sha256": qualification_sha,
        "human_arming_sha256": _sha256(paths[1].read_bytes()),
        "route": dict(route),
    }


def qg_decision_card(
    qualification_path: Path,
    *,
    target: str,
    expected_profile: Mapping[str, Any],
    expected_identity: Mapping[str, str],
) -> dict[str, Any]:
    """Build the exact human decision card for one current qualification."""
    qualification = _load_and_validate_json(
        qualification_path, QUALIFICATION_SCHEMA_PATH, "qualification"
    )
    if (
        qualification["profile"] != dict(expected_profile)
        or qualification["identity"] != dict(expected_identity)
        or not _qualification_route_is_current(qualification["route"], expected_identity)
    ):
        raise CertificationEvidenceError(
            "qualification does not bind the current profile/QG contract"
        )
    qualification_sha = _sha256(qualification_path.read_bytes())
    approval_id = "qg-arm-" + _sha256(
        _stable(
            {
                "target": target,
                "profile": expected_profile,
                "identity": expected_identity,
                "qualification_sha256": qualification_sha,
            }
        ).encode("utf-8")
    )[:24]
    route = qualification["route"]
    return {
        "schema_version": "production-qg-decision-card.v1",
        "decision": "HUMAN_ARMING_REQUIRED",
        "target": target,
        "approval_id": approval_id,
        "qualification_sha256": qualification_sha,
        "profile": dict(expected_profile),
        "proposed_reviewer": {
            key: route[key] for key in ("family", "model", "route", "lineage")
        },
        "canary": dict(route["canary"]),
        "budget": dict(route["budget"]),
        "circuit": dict(route["circuit"]),
        "resume": dict(route["resume"]),
    }


def load_runtime_authorization(
    qualification_path: Path,
    arming_path: Path,
    *,
    target: str,
    expected_profile: Mapping[str, Any],
    expected_identity: Mapping[str, str],
) -> dict[str, Any]:
    """Validate separate qualification and human-arming artifacts for one run."""
    card = qg_decision_card(
        qualification_path,
        target=target,
        expected_profile=expected_profile,
        expected_identity=expected_identity,
    )
    qualification = _load_and_validate_json(
        qualification_path, QUALIFICATION_SCHEMA_PATH, "qualification"
    )
    arming = _load_and_validate_json(arming_path, ARMING_SCHEMA_PATH, "human arming")
    route = qualification["route"]
    if (
        arming["approval_id"] != card["approval_id"]
        or arming["qualification_sha256"] != card["qualification_sha256"]
        or arming["profile"] != dict(expected_profile)
        or arming["route"] != route
        or arming["budget"] != route["budget"]
    ):
        raise CertificationEvidenceError(
            "human arming does not bind the current decision card/qualification"
        )
    return {
        "qualification_path": str(qualification_path.resolve()),
        "qualification_sha256": card["qualification_sha256"],
        "human_arming_path": str(arming_path.resolve()),
        "human_arming_sha256": _sha256(arming_path.read_bytes()),
        "approval_id": card["approval_id"],
        "route": dict(route),
    }


def deployment_passes(
    artifact: EvidenceArtifact,
    *,
    publication: Mapping[str, Any],
    expected_workflow_identity: str,
) -> bool:
    """Require a successful canonical Pages run and verified target marker."""
    value = artifact.value
    deployment = value["deployment"]
    workflow = deployment["workflow"]
    verification = deployment["verification"]
    try:
        workflow_created_at = datetime.fromisoformat(workflow["created_at"])
        certified_at = datetime.fromisoformat(workflow["certified_at"])
    except (TypeError, ValueError):
        return False
    if workflow_created_at.tzinfo is None:
        workflow_created_at = workflow_created_at.replace(tzinfo=UTC)
    if certified_at.tzinfo is None:
        certified_at = certified_at.replace(tzinfo=UTC)
    return bool(
        value["workflow_identity"] == expected_workflow_identity
        and value["publication"]["pr"] == publication.get("pr")
        and value["publication"]["merge_sha"] == publication.get("merge_sha")
        and workflow["name"] == "Deploy to GitHub Pages"
        and workflow["path"] == ".github/workflows/deploy-pages.yml"
        and workflow["event"] == "workflow_dispatch"
        and workflow["branch"] == "main"
        and workflow["post_certification"] == "PASS"
        and workflow_created_at >= certified_at
        and workflow["publication_ancestor"] == "PASS"
        and workflow["conclusion"] == "success"
        and deployment["environment"] == "github-pages"
        and deployment["url"].startswith("https://learn-ukrainian.github.io/")
        and verification["http_status"] == 200
        and verification["target"] == value["target"]
        and verification["marker"] == value["target"]
        and verification["marker_sha256"]
        == _sha256(verification["marker"].encode("utf-8"))
        and verification["deployed_head_sha"] == workflow["head_sha"]
        and verification["deployment_marker_url"]
        == (
            "https://learn-ukrainian.github.io/.well-known/"
            f"learn-ukrainian-deployment-{workflow['head_sha']}.txt"
        )
        and verification["deployment_marker_body_sha256"]
        == _sha256(f"{workflow['head_sha']}\n".encode())
    )


def current_qg_facts(*, target: str, module_dir: Path) -> dict[str, str]:
    """Derive the current QG facts from source, without a reviewer call or cache read."""
    from scripts.audit import llm_qg_store, llm_reviewer, qg_workflow
    from scripts.audit.content_surface_gates import policy_for_level
    from scripts.audit.curriculum_qg_harness import CHECKER_VERSION, checker_config_hash

    level, separator, slug = target.partition("/")
    if not separator or not level or not slug or not module_dir.is_dir():
        raise CertificationEvidenceError("production QG requires one directory-layout target module")
    texts = {
        name: (module_dir / name).read_text(encoding="utf-8") if (module_dir / name).is_file() else ""
        for name in llm_qg_store.CONTENT_FILES
    }
    prompt = llm_reviewer.build_reviewer_prompt(
        level=level,
        slug=slug,
        module_md=texts.get("module.md", ""),
        activities_yaml=texts.get("activities.yaml", ""),
        vocabulary_yaml=texts.get("vocabulary.yaml", ""),
        resources_yaml=texts.get("resources.yaml", ""),
    )
    return {
        "target": target,
        "content_sha": llm_qg_store.content_sha_for_module(module_dir),
        "prompt_hash": llm_qg_store.prompt_hash_for_text(prompt) or "",
        "gate_version": qg_workflow.DEFAULT_GATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "checker_config_hash": checker_config_hash(),
        "policy_family": policy_for_level(level).family,
    }


def _canonical_route(dispatch: Mapping[str, Any]) -> dict[str, str] | None:
    """Return qualification route identity, never author-lineage evidence.

    ``route_lineage_id`` is the deterministic family/model/route identifier
    that a qualification artifact binds.  It deliberately does not establish
    who authored the learner material; that evidence is separately captured by
    the live dispatcher in ``author_lineage``.
    """
    values = {
        "family": dispatch.get("reviewer_family"),
        "model": dispatch.get("reviewer_model_id"),
        "route": dispatch.get("route_name"),
        "lineage": dispatch.get("route_lineage_id"),
    }
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        return None
    return {key: str(value) for key, value in values.items()}


def _captured_source_events(dispatch: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    from scripts.audit import llm_reviewer_dispatch

    source_events: list[dict[str, Any]] = []
    for event in llm_reviewer_dispatch.tool_events_from_dispatch_meta(dispatch):
        if not llm_reviewer_dispatch.is_source_tool(str(event.get("tool") or "")):
            continue
        if str(event.get("status") or "").strip().casefold() != "completed":
            return ()
        if not isinstance(event.get("tool_call_id"), str) or not event["tool_call_id"].strip():
            return ()
        if not isinstance(event.get("input"), Mapping) or not event["input"]:
            return ()
        if "output" not in event or event["output"] in (None, ""):
            return ()
        source_events.append(event)
    return tuple(source_events)


def _live_author_lineage_passes(dispatch: Mapping[str, Any]) -> bool:
    """Require repository-owned live-dispatch and resolved author provenance."""
    from scripts.audit import llm_reviewer_dispatch

    execution = dispatch.get("execution_provenance")
    lineage = dispatch.get("author_lineage")
    if not isinstance(execution, Mapping) or not isinstance(lineage, Mapping):
        return False
    dispatcher_provenance = execution.get("dispatcher_provenance")
    if not isinstance(dispatcher_provenance, Mapping):
        return False
    if (
        execution.get("capture_path") != "qg_workflow.live_reviewer_dispatcher"
        or execution.get("mode") != "live"
        or execution.get("dispatcher") != "LiveReviewerDispatcher"
        or dispatcher_provenance.get("kind") != "live_reviewer_dispatcher"
        or dispatcher_provenance.get("dispatcher") != "LiveReviewerDispatcher"
    ):
        return False
    author_family = llm_reviewer_dispatch.normalize_family(lineage.get("family"))
    reviewer_family = llm_reviewer_dispatch.normalize_family(dispatch.get("reviewer_family"))
    if not author_family or not reviewer_family or author_family == reviewer_family:
        return False
    return all(isinstance(lineage.get(key), str) and lineage[key].strip() for key in ("source", "evidence"))


def _raw_response_matches_payload(raw_response: str, payload: Mapping[str, Any]) -> bool:
    """Bind the persisted raw reviewer bytes to the canonical parsed payload."""
    from scripts.audit import llm_reviewer_dispatch, qg_workflow

    try:
        parsed = llm_reviewer_dispatch._json_payload_from_response(raw_response)
        return qg_workflow._payload_from_reviewer_payload(parsed) == dict(payload)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _replay_capture_is_coherent(tier2: Mapping[str, Any]) -> bool:
    """Verify raw, retry, dispatch, and cache linkage without consulting SQLite."""
    from scripts.audit import llm_reviewer_dispatch

    dispatch = tier2.get("dispatch")
    history = tier2.get("retry_history")
    raw_response = tier2.get("raw_response")
    if not isinstance(dispatch, Mapping) or not isinstance(history, list) or not history:
        return False
    if not isinstance(raw_response, str) or not raw_response or not _raw_response_matches_payload(
        raw_response, tier2["payload"]
    ):
        return False
    final_attempt = history[-1]
    if not isinstance(final_attempt, Mapping):
        return False
    if (
        final_attempt.get("attempt") != tier2.get("attempt_id")
        or final_attempt.get("raw_response") != raw_response
        or final_attempt.get("raw_response_sha256") != tier2.get("raw_response_sha256")
        or not isinstance(final_attempt.get("dispatch"), Mapping)
    ):
        return False
    attempt_dispatch = dict(final_attempt["dispatch"])
    replay_dispatch = dict(dispatch)
    replay_dispatch.pop("cache_run_id", None)
    if attempt_dispatch != replay_dispatch:
        return False
    events = llm_reviewer_dispatch.tool_events_from_dispatch_meta(dispatch)
    tools_used = tuple(str(tool) for tool in dispatch.get("tools_used") or ())
    if (
        not events
        or not tools_used
        or any(str(event.get("tool") or "") not in tools_used for event in events)
        or llm_reviewer_dispatch.tool_call_count_from_dispatch_meta(dispatch) < len(events)
    ):
        return False
    return tier2.get("status") != "cache_hit" or dispatch.get("cache_run_id") == tier2.get("tier2_run_id")


def _positive_fact_checks_have_captured_sources(
    payload: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> bool:
    from scripts.audit import anchor_primitives

    for fact_check in payload.get("fact_checks", []):
        if not isinstance(fact_check, Mapping):
            return False
        if fact_check.get("verdict") not in {"CONFIRMED", "REFUTED_BY_CONTRADICTION", "CONTESTED"}:
            continue
        grounding = fact_check.get("grounding")
        if not isinstance(grounding, Mapping):
            return False
        if not any(
            str(event.get("tool_call_id") or "") == str(grounding.get("tool_call_id") or "")
            and anchor_primitives.canonical_tool_name(event.get("tool"))
            == anchor_primitives.canonical_tool_name(grounding.get("tool"))
            and anchor_primitives.event_input_matches_query(event, str(grounding.get("query") or ""))
            for event in events
        ):
            return False
    return True


def _canonical_tier_matches(record: Mapping[str, Any], tier2: Mapping[str, Any]) -> bool:
    workflow = record.get("qg_workflow")
    if not isinstance(workflow, Mapping) or not isinstance(workflow.get("tiers"), list):
        return False
    index = tier2["canonical_tier_index"]
    tiers = workflow["tiers"]
    if index >= len(tiers) or not isinstance(tiers[index], Mapping):
        return False
    canonical = tiers[index]
    return bool(
        canonical.get("tier") == 2
        and canonical.get("name") == "llm_reviewer"
        and canonical.get("source") == tier2["source"]
        and canonical.get("workflow_run_id") == tier2["workflow_run_id"]
        and canonical.get("tier2_run_id") == tier2["tier2_run_id"]
        and canonical.get("attempt_id") == tier2["attempt_id"]
        and canonical.get("status") == tier2["status"]
        and canonical.get("completion_status") == tier2["completion_status"]
        and canonical.get("dispatch") == tier2["dispatch"]
        and canonical.get("payload") == tier2["payload"]
        and canonical.get("raw_response") == tier2["raw_response"]
        and canonical.get("raw_response_sha256") == tier2["raw_response_sha256"]
        and canonical.get("retry_history") == tier2["retry_history"]
        and canonical.get("gate_outcomes") == tier2["gate_outcomes"]
    )


def _contains_forbidden_workflow_state(value: object) -> bool:
    forbidden = {
        "unavailable",
        "legacy",
        "skipped",
        "provider_error",
        "provider_failure",
        "parse_failure",
        "schema_failure",
        "cost_overrun",
        "canary_required",
        "circuit_open",
        "incomplete",
    }
    if isinstance(value, Mapping):
        return any(_contains_forbidden_workflow_state(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_forbidden_workflow_state(item) for item in value)
    return isinstance(value, str) and value.strip().casefold() in forbidden


def production_qg_passes(
    artifact: EvidenceArtifact,
    *,
    expected_identity: Mapping[str, str],
    expected_facts: Mapping[str, str],
    seminar: bool,
    authorization: Mapping[str, Any],
) -> bool:
    """Accept only an exact, captured production-qualified QG workflow run."""
    from scripts.audit import llm_reviewer_dispatch, qg_schema

    value = artifact.value
    if value.get("arm") != "production-qualified" or value["authorization"]["identity"] != dict(expected_identity):
        return False
    record, tier2 = value["canonical_record"], value["tier2"]
    route = authorization.get("route")
    if not isinstance(route, Mapping) or set(expected_identity) != QG_IDENTITY_KEYS:
        return False
    try:
        qg_schema.validate_record(record)
        qg_schema.validate_reviewer_payload(tier2["payload"], "seminar" if seminar else "core")
    except (ValueError, KeyError, TypeError):
        return False
    canonical_route = _canonical_route(tier2["dispatch"])
    if canonical_route is None or canonical_route != {
        key: str(route.get(key) or "") for key in ("family", "model", "route", "lineage")
    }:
        return False
    workflow = record.get("qg_workflow")
    provenance = record.get("provenance")
    if not isinstance(workflow, Mapping) or not isinstance(provenance, Mapping):
        return False
    if (
        record.get("module_id") != expected_facts["target"]
        or record.get("content_sha") != expected_facts["content_sha"]
        or record.get("level_policy", {}).get("family") != expected_facts["policy_family"]
        or provenance.get("source") != "qg_workflow"
        or provenance.get("run_id") != tier2["workflow_run_id"]
        or workflow.get("gate_version") != expected_facts["gate_version"]
        or workflow.get("prompt_hash") != expected_facts["prompt_hash"]
        or workflow.get("checker_version") != expected_facts["checker_version"]
        or workflow.get("checker_config_hash") != expected_facts["checker_config_hash"]
        or workflow.get("reviewer_family") != route["family"]
        or workflow.get("reviewer_model_id") != route["model"]
        or record.get("completion_status") != "COMPLETE"
        or record.get("terminal_verdict") != "PASS"
        or record.get("workflow_verdict") != "PASS"
        or tier2.get("completion_status") != "COMPLETE"
        or not _canonical_tier_matches(record, tier2)
    ):
        return False
    if tier2["raw_response_sha256"] != _sha256(tier2["raw_response"].encode("utf-8")):
        return False
    if not _live_author_lineage_passes(tier2["dispatch"]) or not _replay_capture_is_coherent(tier2):
        return False
    if _contains_forbidden_workflow_state(tier2["dispatch"]) or _contains_forbidden_workflow_state(
        tier2["gate_outcomes"]
    ):
        return False
    if tier2["status"] == "ran":
        if tier2.get("cache_regate") is not None or tier2["dispatch"].get("cache_run_id") is not None:
            return False
    elif (
        tier2["status"] != "cache_hit"
        or tier2.get("cache_regate") != "replayed"
        or tier2["dispatch"].get("cache_run_id") != tier2["tier2_run_id"]
    ):
        return False
    gate = tier2["gate_outcomes"]
    if not isinstance(gate, Mapping) or gate.get("status") != "ran":
        return False
    grounding_gate = gate.get("grounding")
    if not isinstance(grounding_gate, Mapping):
        return False
    if gate.get("workflow_override") not in (None, "PASS") or any(
        int(grounding_gate.get(key, 0) or 0) != 0
        for key in ("required_ungrounded_findings", "invalid_fact_checks", "inadmissible_positive_verdicts")
    ):
        return False
    if any(tier2["dispatch"].get(key) is True for key in ("shadow", "advisory", "attested_judge")):
        return False
    theatre = llm_reviewer_dispatch.tool_theatre_violation(
        policy_family="seminar" if seminar else "core",
        payload=tier2["payload"],
        dispatch_meta=tier2["dispatch"],
    )
    if theatre is not None or llm_reviewer_dispatch.deep_read_required(tier2["payload"], tier2["dispatch"]):
        return False
    if seminar:
        events = _captured_source_events(tier2["dispatch"])
        if not events or not _positive_fact_checks_have_captured_sources(tier2["payload"], events):
            return False
    try:
        grounded = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
            tier2["payload"], tier2["dispatch"], policy_family="seminar" if seminar else "core", gate_version="v2"
        )
    except (ValueError, TypeError):
        return False
    return bool(
        grounded.required_ungrounded_findings == 0
        and grounded.invalid_fact_checks == 0
        and grounded.inadmissible_positive_verdicts == 0
        and not llm_reviewer_dispatch.factual_sweep_incomplete(
            grounded.payload, policy_family="seminar" if seminar else "core", invalid_fact_checks=grounded.invalid_fact_checks
        )
    )


def production_qg_stability_key(artifact: EvidenceArtifact) -> str:
    """Hash only immutable reviewer inputs, never response/tool output or timestamps."""
    qg = artifact.value
    route = _canonical_route(qg["tier2"]["dispatch"])
    payload = {
        "target": qg["target"],
        "profile": qg["profile"],
        "preparation": qg["preparation_identity"],
        "learner": qg["learner_hashes"],
        "identity": qg["authorization"]["identity"],
        "route": route,
        "authorization": {
            "qualification": qg["authorization"]["qualification_sha256"],
            "arming": qg["authorization"]["human_arming_sha256"],
        },
    }
    return _sha256(_stable(payload).encode("utf-8"))


def production_qg_material_fingerprint(artifact: EvidenceArtifact) -> str:
    """Include every material QG finding plus factual verdicts and final disposition."""
    tier2 = artifact.value["tier2"]
    material = [
        item for item in tier2["payload"].get("findings", []) if item.get("severity") in QG_MATERIAL_SEVERITIES
    ]
    facts = [
        {key: item.get(key) for key in ("claim", "verdict", "grounding")}
        for item in tier2["payload"].get("fact_checks", [])
        if isinstance(item, Mapping)
    ]
    return _sha256(
        _stable(
            {
                "terminal": artifact.value["canonical_record"].get("terminal_verdict"),
                "workflow": artifact.value["canonical_record"].get("workflow_verdict"),
                "findings": sorted(material, key=_stable),
                "fact_checks": sorted(facts, key=_stable),
            }
        ).encode("utf-8")
    )
