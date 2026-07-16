"""Strict structured code-review contract: schema validation, exits, receipts.

Canonical format is versioned JSON (``code-review-findings.v1``). Legacy
``FINDING:`` text blocks are **removed** as a dual source of truth — they fail
closed as invalid input (issue #5284 compatibility decision).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.review.evidence import (
    OUTCOME_LINE_MISMATCH,
    OUTCOME_MALFORMED,
    OUTCOME_OUT_OF_SCOPE,
    OUTCOME_QUOTE_MISSING,
    EvidenceCheckResult,
    EvidenceError,
    changed_lines_map,
    compute_target_input_fingerprint,
    normalize_line_endings,
    verify_finding_evidence,
)
from scripts.review.target_resolution import ReviewTarget

SCHEMA_VERSION = "code-review-findings.v1"
RECEIPT_SCHEMA_VERSION = "code-review-receipt.v1"
BEHAVIOR_PROOF_SCHEMA_VERSION = "behavior-proof.v1"
SCHEMA_RELATIVE_PATH = "schemas/code-review-findings.v1.schema.json"

# Stable exit classes (documented in docs/review-protocol.md).
EXIT_CLEAN = 0
EXIT_ACTIONABLE = 1
EXIT_INVALID = 2
EXIT_INCOMPLETE = 3
EXIT_STALE = 4
EXIT_UNVERIFIABLE = 5

EXIT_NAMES = {
    EXIT_CLEAN: "clean",
    EXIT_ACTIONABLE: "actionable",
    EXIT_INVALID: "invalid",
    EXIT_INCOMPLETE: "incomplete",
    EXIT_STALE: "stale",
    EXIT_UNVERIFIABLE: "unverifiable",
}

ALLOWED_DISPOSITIONS = frozenset(
    {
        "in_scope_blocker",
        "follow_up",
        "stop_and_escalate",
    }
)

# Explicitly rejected identity / envelope placeholders (fail closed).
PLACEHOLDER_VALUES = frozenset(
    {
        "unknown",
        "unspecified",
        "not_provided",
    }
)

_LEGACY_FINDING_RE = re.compile(r"(?m)^FINDING:\s*$")


class ContractError(RuntimeError):
    """Structured review input failed closed before evidence verification."""

    def __init__(self, message: str, *, exit_code: int = EXIT_INVALID) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def package_repo_root() -> Path:
    """Root of the learn-ukrainian checkout that ships the schema (not the review target)."""
    return Path(__file__).resolve().parents[2]


def schema_path(tooling_root: Path | None = None) -> Path:
    root = tooling_root or package_repo_root()
    return root / SCHEMA_RELATIVE_PATH


def load_schema(tooling_root: Path | None = None) -> dict[str, Any]:
    path = schema_path(tooling_root)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"schema_unavailable:{path}:{exc}", exit_code=EXIT_INVALID) from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"schema_invalid_json:{path}:{exc.msg}",
            exit_code=EXIT_INVALID,
        ) from exc


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _looks_like_legacy_text(raw: str) -> bool:
    return bool(_LEGACY_FINDING_RE.search(raw))


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    return stripped.lower() in PLACEHOLDER_VALUES


def _canonical_family(value: str) -> str:
    return value.strip().lower()


def parse_reviewer_json(raw: str) -> dict[str, Any]:
    """Parse reviewer stdout as a single JSON object. Fail closed on chatter."""
    text = raw.strip()
    if not text:
        raise ContractError("empty_review_input", exit_code=EXIT_INCOMPLETE)
    if _looks_like_legacy_text(text) and not text.lstrip().startswith("{"):
        raise ContractError(
            "legacy_FINDING_text_removed: use schema_version "
            f"{SCHEMA_VERSION!r} JSON (see docs/review-protocol.md)",
            exit_code=EXIT_INVALID,
        )
    # Reject non-JSON wrapper chatter: entire payload must be one JSON value.
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        # Also try: JSON embedded only if the whole stripped text is JSON —
        # no fence stripping, no prose extraction (fail closed).
        raise ContractError(
            f"non_json_or_chatter:{exc.msg}",
            exit_code=EXIT_INVALID,
        ) from exc
    if not isinstance(payload, dict):
        raise ContractError("review_root_must_be_object", exit_code=EXIT_INVALID)
    return payload


def validate_reviewer_payload(
    payload: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
    tooling_root: Path | None = None,
) -> dict[str, Any]:
    """Strict JSON Schema validation (Draft 2020-12). Unknown fields fail."""
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:  # pragma: no cover - venv always has jsonschema
        raise ContractError("jsonschema_unavailable", exit_code=EXIT_INVALID) from exc

    sch = schema if schema is not None else load_schema(tooling_root)
    try:
        Draft202012Validator.check_schema(sch)
    except SchemaError as exc:
        raise ContractError(
            f"schema_meta_invalid:{exc.message}",
            exit_code=EXIT_INVALID,
        ) from exc
    validator = Draft202012Validator(sch)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.absolute_path) or "(root)"
        raise ContractError(
            f"schema_violation:{path}:{first.message}",
            exit_code=EXIT_INVALID,
        )

    # Extra structural checks not fully expressible in JSON Schema alone.
    findings = payload["findings"]
    ids = [f["id"] for f in findings]
    if len(ids) != len(set(ids)):
        raise ContractError("duplicate_finding_ids", exit_code=EXIT_INVALID)
    for finding in findings:
        loc = finding["location"]
        if loc["end_line"] < loc["start_line"]:
            raise ContractError(
                f"invalid_line_range:{finding['id']}",
                exit_code=EXIT_INVALID,
            )
    return payload


def sort_findings_deterministically(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stable multi-finding order: path, start_line, end_line, id."""
    return sorted(
        findings,
        key=lambda f: (
            f["location"]["path"],
            f["location"]["start_line"],
            f["location"]["end_line"],
            f["id"],
        ),
    )


@dataclass
class FindingValidation:
    id: str
    outcome: str
    matched_line: int | None = None
    matched_text: str | None = None
    detail: str = ""
    disposition: str | None = None
    disposition_rationale: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "outcome": self.outcome,
            "matched_line": self.matched_line,
            "matched_text": self.matched_text,
            "detail": self.detail,
            "disposition": self.disposition,
            "disposition_rationale": self.disposition_rationale,
        }


@dataclass
class AgentIdentity:
    model: str
    family: str
    harness: str
    selection_reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class VerifyContext:
    """Runner-supplied envelope data (not trusted from the reviewer)."""

    issue_ref: str
    scope: dict[str, Any]
    author: AgentIdentity
    reviewer: AgentIdentity
    target: ReviewTarget
    repo_root: Path
    # Target-input fingerprint (validated review surface), not reviewer JSON.
    input_sha256: str
    # SHA-256 of the reviewer JSON bytes (recorded separately on the receipt).
    reviewer_output_sha256: str = ""
    expected_head: str | None = None
    # Required for clean/actionable: expected target-input fingerprint.
    expected_input_sha256: str | None = None
    tests: dict[str, Any] = field(default_factory=dict)
    behavior_proof: dict[str, Any] = field(default_factory=dict)
    # Supplied only by the frozen closeout state. A passing clause must use
    # this exact claim; callers must not substitute a free-text surface.
    frozen_intended_behavior: str = ""
    # #5285 owns actual isolation verification. This narrow boundary lets its
    # attestation interface plug in without duplicating isolation logic here.
    isolation_attestation_validator: Callable[[dict[str, Any], ReviewTarget], bool] | None = None
    dispositions: dict[str, dict[str, str]] = field(default_factory=dict)
    routing_lineage: dict[str, str] = field(default_factory=dict)


@dataclass
class VerifyResult:
    exit_code: int
    final_disposition: str
    payload: dict[str, Any] | None
    validations: list[FindingValidation]
    receipt: dict[str, Any]
    error: str | None = None


def _identity_errors(label: str, identity: AgentIdentity) -> list[str]:
    errors: list[str] = []
    for field_name in ("model", "family", "harness", "selection_reason"):
        value = getattr(identity, field_name)
        if not isinstance(value, str) or _is_placeholder(value):
            errors.append(f"{label}.{field_name}_missing_or_placeholder")
    return errors


def _tests_envelope_status(tests: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate tests closeout semantics.

    Returns (incomplete_errors, proof_failures).
    Successful closeout needs concrete commands + ``passed: true``, or explicit
    supported ``status: n/a`` with a non-empty reason. Explicit failure
    (``passed: false`` / ``status: fail``) is a proof failure, not incomplete.
    """
    incomplete: list[str] = []
    failures: list[str] = []
    if not isinstance(tests, dict) or not tests:
        return ["tests_empty"], failures

    status_raw = tests.get("status")
    status = status_raw.strip().lower() if isinstance(status_raw, str) else None
    passed = tests.get("passed")
    commands = tests.get("commands")
    reason = tests.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        rationale = tests.get("rationale")
        reason = rationale if isinstance(rationale, str) else reason

    if status in {"fail", "failed"}:
        failures.append("tests_failed")
        return incomplete, failures
    if passed is False:
        failures.append("tests_failed")
        return incomplete, failures
    if status in {"n/a", "na"}:
        if not isinstance(reason, str) or not reason.strip():
            incomplete.append("tests_na_reason_empty")
        return incomplete, failures
    if passed is True:
        if not isinstance(commands, list) or not commands:
            incomplete.append("tests_commands_missing")
        elif not all(isinstance(c, str) and c.strip() for c in commands):
            incomplete.append("tests_commands_invalid")
        return incomplete, failures

    incomplete.append("tests_result_missing_or_invalid")
    return incomplete, failures


def _behavior_proof_envelope_status(
    behavior_proof: Any,
    *,
    target_input_sha256: str,
    frozen_intended_behavior: str,
    isolation_attestation_validator: Callable[[dict[str, Any], ReviewTarget], bool] | None,
    target: ReviewTarget,
) -> tuple[list[str], list[str]]:
    """Validate source-aware / source-blind proof semantics.

    Each side must be ``status: pass`` backed by a complete, target-bound
    clause, or ``status: n/a`` with a non-empty reason. The clause claim is
    the frozen intended behavior, never a separate free-text behavior-surface
    field. Explicit ``fail`` is a proof failure (non-clean/actionable).
    Missing or invalid evidence remains incomplete.
    """
    incomplete: list[str] = []
    failures: list[str] = []
    if not isinstance(behavior_proof, dict):
        return ["behavior_proof_invalid"], failures
    if behavior_proof.get("schema_version") != BEHAVIOR_PROOF_SCHEMA_VERSION:
        incomplete.append("behavior_proof_schema_version_invalid")

    for key in ("source_aware", "source_blind"):
        proof = behavior_proof.get(key)
        if not isinstance(proof, dict) or not proof:
            incomplete.append(f"behavior_proof.{key}_missing")
            continue
        status_raw = proof.get("status")
        if not isinstance(status_raw, str) or not status_raw.strip():
            incomplete.append(f"behavior_proof.{key}_status_missing")
            continue
        status = status_raw.strip().lower()
        if key == "source_blind":
            blind_enforced = proof.get("blind_enforced")
            if blind_enforced is not None and not isinstance(blind_enforced, bool):
                incomplete.append("behavior_proof.source_blind_blind_enforced_invalid")
            if status == "pass" and not isinstance(blind_enforced, bool):
                incomplete.append("behavior_proof.source_blind_blind_enforced_missing")
            if blind_enforced is True:
                attestation = proof.get("isolation_attestation")
                if not isinstance(attestation, dict) or not attestation:
                    incomplete.append("behavior_proof.source_blind_enforced_without_attestation")
                elif attestation.get("target_input_sha256") != target_input_sha256:
                    incomplete.append("behavior_proof.source_blind_attestation_target_mismatch")
                elif isolation_attestation_validator is None:
                    incomplete.append("behavior_proof.source_blind_attestation_unvalidated")
                else:
                    try:
                        valid_attestation = isolation_attestation_validator(attestation, target)
                    except Exception:
                        valid_attestation = False
                    if valid_attestation is not True:
                        incomplete.append("behavior_proof.source_blind_attestation_invalid")
        if status == "fail":
            failures.append(f"behavior_proof.{key}_failed")
            continue
        if status == "pass":
            if not isinstance(frozen_intended_behavior, str) or not frozen_intended_behavior.strip():
                incomplete.append(f"behavior_proof.{key}_frozen_intended_behavior_missing")
                continue
            clauses = proof.get("clauses")
            if not isinstance(clauses, list) or not clauses:
                incomplete.append(f"behavior_proof.{key}_clauses_missing")
                continue

            complete_clause_found = False
            for clause in clauses:
                if not isinstance(clause, dict):
                    continue
                claim = clause.get("claim")
                binding = clause.get("target_input_sha256")
                command = clause.get("command")
                step = clause.get("step")
                has_command = isinstance(command, str) and bool(command.strip())
                has_step = isinstance(step, str) and bool(step.strip())
                has_cwd = isinstance(clause.get("cwd"), str) and bool(clause["cwd"].strip())
                exit_code = clause.get("exit_code")
                has_exit = isinstance(exit_code, int) and not isinstance(exit_code, bool)
                result = clause.get("result")
                has_result = isinstance(result, str) and bool(result.strip())
                observation = clause.get("observation")
                evidence_ref = clause.get("evidence_ref")
                complete = (
                    claim == frozen_intended_behavior
                    and binding == target_input_sha256
                    and (has_command ^ has_step)
                    and (not has_command or has_cwd)
                    and (has_exit or has_result)
                    and isinstance(observation, str)
                    and bool(observation.strip())
                    and isinstance(evidence_ref, str)
                    and bool(evidence_ref.strip())
                )
                if complete:
                    complete_clause_found = True
                    break
            if not complete_clause_found:
                incomplete.append(f"behavior_proof.{key}_complete_clause_missing")
                if not any(
                    isinstance(clause, dict)
                    and clause.get("target_input_sha256") == target_input_sha256
                    for clause in clauses
                ):
                    incomplete.append(f"behavior_proof.{key}_target_binding_mismatch")
                if not any(
                    isinstance(clause, dict)
                    and clause.get("claim") == frozen_intended_behavior
                    for clause in clauses
                ):
                    incomplete.append(f"behavior_proof.{key}_claim_mismatch")
                continue
            continue
        if status in {"n/a", "na"}:
            reason = proof.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                rationale = proof.get("rationale")
                reason = rationale if isinstance(rationale, str) else reason
            if not isinstance(reason, str) or not reason.strip():
                incomplete.append(f"behavior_proof.{key}_na_reason_empty")
            continue
        incomplete.append(f"behavior_proof.{key}_status_invalid")
    return incomplete, failures


def validate_closeout_envelope(
    ctx: VerifyContext,
    *,
    finding_ids: list[str],
) -> tuple[int, str] | None:
    """Return (exit_code, error) when envelope cannot support clean closeout.

    Never fabricates lineage. Placeholder values fail closed.

    Structural / missing / invalid envelope fields → ``EXIT_INCOMPLETE`` (or
    ``EXIT_INVALID`` for hard disposition errors alone). Explicit proof
    failures (failed tests, failed behavior proof, same-family author/reviewer)
    → ``EXIT_ACTIONABLE`` so the receipt is non-clean and never exits 0.
    """
    incomplete: list[str] = []
    proof_failures: list[str] = []
    hard_errors: list[str] = []

    if not isinstance(ctx.issue_ref, str) or _is_placeholder(ctx.issue_ref):
        incomplete.append("issue_ref_missing_or_placeholder")

    if not isinstance(ctx.scope, dict) or not ctx.scope:
        incomplete.append("scope_empty")
    else:
        # Require at least one concrete non-empty value.
        concrete = False
        for value in ctx.scope.values():
            if value is None:
                continue
            if isinstance(value, str) and _is_placeholder(value):
                continue
            if isinstance(value, (list, dict)) and not value:
                continue
            concrete = True
            break
        if not concrete:
            incomplete.append("scope_lacks_concrete_values")

    incomplete.extend(_identity_errors("author", ctx.author))
    incomplete.extend(_identity_errors("reviewer", ctx.reviewer))

    # Formal closeout requires concrete, distinct families (case-insensitive).
    author_family_ok = not any(
        e.startswith("author.family_") for e in incomplete
    )
    reviewer_family_ok = not any(
        e.startswith("reviewer.family_") for e in incomplete
    )
    if (
        author_family_ok
        and reviewer_family_ok
        and _canonical_family(ctx.author.family)
        == _canonical_family(ctx.reviewer.family)
    ):
        proof_failures.append("same_family_review")

    t_incomplete, t_failures = _tests_envelope_status(ctx.tests)
    incomplete.extend(t_incomplete)
    proof_failures.extend(t_failures)

    b_incomplete, b_failures = _behavior_proof_envelope_status(
        ctx.behavior_proof,
        target_input_sha256=ctx.input_sha256,
        frozen_intended_behavior=ctx.frozen_intended_behavior,
        isolation_attestation_validator=ctx.isolation_attestation_validator,
        target=ctx.target,
    )
    incomplete.extend(b_incomplete)
    proof_failures.extend(b_failures)

    if not isinstance(ctx.routing_lineage, dict) or not ctx.routing_lineage:
        incomplete.append("routing_lineage_empty")
    else:
        for key, value in ctx.routing_lineage.items():
            if not isinstance(key, str) or not key.strip():
                incomplete.append("routing_lineage_invalid_key")
                break
            if not isinstance(value, str) or _is_placeholder(value):
                incomplete.append(f"routing_lineage.{key}_missing_or_placeholder")

    if not ctx.expected_input_sha256 or _is_placeholder(str(ctx.expected_input_sha256)):
        incomplete.append("expected_input_sha256_required")

    finding_id_set = set(finding_ids)
    disposition_keys = set(ctx.dispositions.keys())
    unknown = sorted(disposition_keys - finding_id_set)
    missing = sorted(finding_id_set - disposition_keys)
    if unknown:
        hard_errors.append(f"disposition_unknown_ids:{','.join(unknown)}")
    if missing:
        incomplete.append(f"disposition_missing_ids:{','.join(missing)}")
    for fid in finding_ids:
        entry = ctx.dispositions.get(fid)
        if not isinstance(entry, dict):
            continue
        disp = entry.get("disposition")
        rationale = entry.get("rationale")
        if not isinstance(disp, str) or disp not in ALLOWED_DISPOSITIONS:
            hard_errors.append(f"disposition_invalid:{fid}")
        if not isinstance(rationale, str) or not rationale.strip():
            incomplete.append(f"disposition_rationale_empty:{fid}")

    if not incomplete and not proof_failures and not hard_errors:
        return None

    # Prefer incomplete when required runner fields are absent/invalid.
    if incomplete:
        return (
            EXIT_INCOMPLETE,
            "envelope_incomplete:" + ";".join(incomplete + hard_errors + proof_failures),
        )
    # Explicit failed proof / same-family → non-clean actionable (never exit 0).
    if proof_failures:
        return (
            EXIT_ACTIONABLE,
            "envelope_proof_failed:" + ";".join(proof_failures + hard_errors),
        )
    # Unknown disposition ids / invalid enums alone → invalid envelope.
    return EXIT_INVALID, "envelope_invalid:" + ";".join(hard_errors)


def _check_stale(ctx: VerifyContext) -> str | None:
    if ctx.expected_input_sha256 and ctx.expected_input_sha256 != ctx.input_sha256:
        return (
            f"stale_input_hash:expected={ctx.expected_input_sha256} "
            f"actual={ctx.input_sha256}"
        )
    if ctx.expected_head:
        if ctx.target.mode == "local":
            return "stale_head_not_applicable_to_local_mode"
        if not ctx.target.head_sha:
            return "stale_head:target_missing_head"
        if ctx.expected_head != ctx.target.head_sha:
            return (
                f"stale_head:expected={ctx.expected_head} "
                f"actual={ctx.target.head_sha}"
            )
    return None


def _classify_exit(
    payload: dict[str, Any],
    validations: list[FindingValidation],
) -> tuple[int, str]:
    outcomes = {v.outcome for v in validations}
    if OUTCOME_MALFORMED in outcomes:
        return EXIT_INVALID, EXIT_NAMES[EXIT_INVALID]
    bad_evidence = outcomes & {
        OUTCOME_QUOTE_MISSING,
        OUTCOME_LINE_MISMATCH,
        OUTCOME_OUT_OF_SCOPE,
    }
    if bad_evidence:
        return EXIT_UNVERIFIABLE, EXIT_NAMES[EXIT_UNVERIFIABLE]

    overall = payload["overall"]
    correctness = overall["correctness"]
    findings = payload["findings"]
    if correctness == "uncertain" and not findings:
        return EXIT_INCOMPLETE, EXIT_NAMES[EXIT_INCOMPLETE]
    if correctness == "incorrect" or findings:
        return EXIT_ACTIONABLE, EXIT_NAMES[EXIT_ACTIONABLE]
    if correctness == "correct" and not findings:
        return EXIT_CLEAN, EXIT_NAMES[EXIT_CLEAN]
    # correct + findings should not happen often; still actionable.
    return EXIT_ACTIONABLE, EXIT_NAMES[EXIT_ACTIONABLE]


def build_receipt(
    ctx: VerifyContext,
    *,
    payload: dict[str, Any] | None,
    validations: list[FindingValidation],
    exit_code: int,
    final_disposition: str,
    error: str | None = None,
) -> dict[str, Any]:
    """Build a runner receipt. Never fabricates routing lineage or identities."""
    target = ctx.target
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "issue_ref": ctx.issue_ref,
        "scope": ctx.scope,
        "author": ctx.author.to_dict(),
        "reviewer": ctx.reviewer.to_dict(),
        "target": {
            "mode": target.mode,
            "base_sha": target.base_sha,
            "head_sha": target.head_sha,
            "changed_paths": list(target.changed_paths),
            "non_test_loc": target.non_test_loc,
            "clean_tree": target.clean_tree,
            "description": target.description,
            # Target-input fingerprint of the validated review surface.
            "input_sha256": ctx.input_sha256,
        },
        "reviewer_output_sha256": ctx.reviewer_output_sha256,
        "findings": [v.to_dict() for v in validations],
        "tests": ctx.tests,
        "behavior_proof": _render_behavior_proof(ctx.behavior_proof),
        "final_disposition": final_disposition,
        "exit_code": exit_code,
        "error": error,
        # Explicit runner-supplied lineage only — empty when not provided.
        "routing_lineage": dict(ctx.routing_lineage),
    }
    if payload is not None:
        receipt["reviewer_payload"] = {
            "schema_version": payload.get("schema_version"),
            "overall": payload.get("overall"),
            "finding_ids": [f["id"] for f in payload.get("findings", [])],
        }
    return receipt


def _render_behavior_proof(behavior_proof: dict[str, Any]) -> dict[str, Any]:
    """Make declared-but-unenforced source-blind proof explicit in receipts."""
    rendered = deepcopy(behavior_proof)
    source_blind = rendered.get("source_blind")
    if isinstance(source_blind, dict) and source_blind.get("blind_enforced") is False:
        source_blind["blind_enforcement"] = "declared-blind/unenforced"
    return rendered


def verify_review(
    raw_input: str,
    ctx: VerifyContext,
    *,
    schema: dict[str, Any] | None = None,
) -> VerifyResult:
    """Full pipeline: target fingerprint → parse → schema → evidence → receipt."""
    reviewer_output_sha = sha256_text(raw_input)
    ctx.reviewer_output_sha256 = reviewer_output_sha

    try:
        target_fp = compute_target_input_fingerprint(ctx.repo_root, ctx.target)
    except EvidenceError as exc:
        err = f"target_fingerprint_unavailable:{exc}"
        ctx.input_sha256 = ""
        receipt = build_receipt(
            ctx,
            payload=None,
            validations=[],
            exit_code=EXIT_UNVERIFIABLE,
            final_disposition=EXIT_NAMES[EXIT_UNVERIFIABLE],
            error=err,
        )
        return VerifyResult(
            exit_code=EXIT_UNVERIFIABLE,
            final_disposition=EXIT_NAMES[EXIT_UNVERIFIABLE],
            payload=None,
            validations=[],
            receipt=receipt,
            error=err,
        )

    ctx.input_sha256 = target_fp

    stale = _check_stale(ctx)
    if stale:
        receipt = build_receipt(
            ctx,
            payload=None,
            validations=[],
            exit_code=EXIT_STALE,
            final_disposition=EXIT_NAMES[EXIT_STALE],
            error=stale,
        )
        return VerifyResult(
            exit_code=EXIT_STALE,
            final_disposition=EXIT_NAMES[EXIT_STALE],
            payload=None,
            validations=[],
            receipt=receipt,
            error=stale,
        )

    try:
        payload = parse_reviewer_json(raw_input)
        payload = validate_reviewer_payload(payload, schema=schema)
    except ContractError as exc:
        receipt = build_receipt(
            ctx,
            payload=None,
            validations=[],
            exit_code=exc.exit_code,
            final_disposition=EXIT_NAMES.get(exc.exit_code, "invalid"),
            error=str(exc),
        )
        return VerifyResult(
            exit_code=exc.exit_code,
            final_disposition=EXIT_NAMES.get(exc.exit_code, "invalid"),
            payload=None,
            validations=[],
            receipt=receipt,
            error=str(exc),
        )

    findings = sort_findings_deterministically(list(payload["findings"]))
    payload = {**payload, "findings": findings}

    try:
        line_map = changed_lines_map(ctx.repo_root, ctx.target)
    except Exception as exc:  # fail closed
        err = f"changed_lines_unavailable:{exc}"
        receipt = build_receipt(
            ctx,
            payload=payload,
            validations=[],
            exit_code=EXIT_UNVERIFIABLE,
            final_disposition=EXIT_NAMES[EXIT_UNVERIFIABLE],
            error=err,
        )
        return VerifyResult(
            exit_code=EXIT_UNVERIFIABLE,
            final_disposition=EXIT_NAMES[EXIT_UNVERIFIABLE],
            payload=payload,
            validations=[],
            receipt=receipt,
            error=err,
        )

    validations: list[FindingValidation] = []
    for finding in findings:
        check: EvidenceCheckResult = verify_finding_evidence(
            finding,
            repo_root=ctx.repo_root,
            target=ctx.target,
            changed_lines=line_map,
        )
        disp = ctx.dispositions.get(finding["id"], {})
        validations.append(
            FindingValidation(
                id=finding["id"],
                outcome=check.outcome,
                matched_line=check.matched_line,
                matched_text=check.matched_text,
                detail=check.detail,
                disposition=disp.get("disposition") if isinstance(disp, dict) else None,
                disposition_rationale=disp.get("rationale") if isinstance(disp, dict) else None,
            )
        )

    exit_code, final_disposition = _classify_exit(payload, validations)
    error: str | None = None

    # Clean/actionable require complete provenance + expected target fingerprint.
    if exit_code in (EXIT_CLEAN, EXIT_ACTIONABLE):
        envelope = validate_closeout_envelope(
            ctx,
            finding_ids=[f["id"] for f in findings],
        )
        if envelope is not None:
            exit_code, error = envelope
            final_disposition = EXIT_NAMES[exit_code]

    receipt = build_receipt(
        ctx,
        payload=payload,
        validations=validations,
        exit_code=exit_code,
        final_disposition=final_disposition,
        error=error,
    )
    return VerifyResult(
        exit_code=exit_code,
        final_disposition=final_disposition,
        payload=payload,
        validations=validations,
        receipt=receipt,
        error=error,
    )


def normalize_for_hash(raw: str) -> str:
    """Expose line-ending-only normalization for callers that need it."""
    return normalize_line_endings(raw)
