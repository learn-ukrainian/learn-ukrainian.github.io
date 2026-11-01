"""Strict structured code-review contract: schema validation, exits, receipts.

Canonical format is versioned JSON (``code-review-findings.v1``). Legacy
``FINDING:`` text blocks are **removed** as a dual source of truth — they fail
closed as invalid input (issue #5284 compatibility decision).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.orchestration.integration_sweep import (
    ITEM_ID_RE,
    VOID_QUOTE_MISMATCH,
    VOID_REVIEWER_BOOKKEEPING,
)
from scripts.review.evidence import (
    OUTCOME_MALFORMED,
    UNVERIFIED_FOLLOW_UP_OUTCOMES,
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


def schema_path(
    tooling_root: Path | None = None,
    *,
    profile: str | None = None,
    task: Mapping[str, Any] | None = None,
) -> Path | None:
    """Select the structured findings schema for a review target, or None when unstructured.

    Code and infra reviews bind the canonical code-review findings schema. Ukrainian content
    reviews use item-judgment envelopes parsed from free-text blocks and do not bind a
    top-level JSON schema.
    """
    from scripts.review.language_lane import is_ukrainian_review

    if profile is not None and profile.strip().casefold() == "ukrainian":
        return None
    if task is not None and is_ukrainian_review(task):
        return None
    root = tooling_root or package_repo_root()
    return root / SCHEMA_RELATIVE_PATH


def load_schema(
    tooling_root: Path | None = None,
    *,
    profile: str | None = None,
    task: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    path = schema_path(tooling_root, profile=profile, task=task)
    if path is None:
        return None
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
    """Parse bare JSON or the approved review-loop envelope, without prose extraction."""
    text = raw.strip()
    if not text:
        raise ContractError("empty_review_input", exit_code=EXIT_INCOMPLETE)
    if text.startswith("VERDICT:"):
        try:
            return _parse_review_loop_envelope(text)
        except (ValueError, RecursionError) as exc:
            raise ContractError(f"review_envelope_unreadable:{type(exc).__name__}") from exc
    if _looks_like_legacy_text(text) and not text.lstrip().startswith("{"):
        raise ContractError(
            f"legacy_FINDING_text_removed: use schema_version {SCHEMA_VERSION!r} JSON (see docs/review-protocol.md)",
            exit_code=EXIT_INVALID,
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"non_json_or_chatter:{exc.msg}",
            exit_code=EXIT_INVALID,
        ) from exc
    if not isinstance(payload, dict):
        raise ContractError("review_root_must_be_object", exit_code=EXIT_INVALID)
    return payload


def _parse_review_loop_envelope(text: str) -> dict[str, Any]:
    from markdown_it import MarkdownIt

    from scripts.fleet_comms.review_publication import ReviewPublicationError
    from scripts.review.verdict_parser import (
        _REVIEW_SCORE_LABEL_RE,
        _REVIEW_VERDICT_LINE_RE,
        _closes_code_fence,
        _commonmark_lines,
        _without_code_fences,
        checked_findings_payload,
    )

    lines = _commonmark_lines(text)
    verdict = re.fullmatch(r"VERDICT: (APPROVE|REQUEST_CHANGES|BLOCKED)(?:[ \t]+[^\r\n]+)?", lines[0])
    score = re.fullmatch(r"[ \t]*SCORE: (?:[1-9]|10)/10(?:[ \t]+[^\r\n]+|[.,;:!?)](?:[ \t]+[^\r\n]+)?)?", lines[1]) if len(lines) > 1 else None
    if verdict is None or score is None:
        raise ContractError("review_envelope_invalid_headers")
    visible = _without_code_fences(text, keep_unclosed=False)
    for label, pattern in (("VERDICT", _REVIEW_VERDICT_LINE_RE), ("SCORE", _REVIEW_SCORE_LABEL_RE)):
        if sum(
            bool(pattern.match(line) or re.match(rf"^[ \t]*{label}:", line, re.IGNORECASE))
            for line in _commonmark_lines(visible)
        ) != 1:
            raise ContractError(f"review_envelope_duplicate_{label.lower()}")
    blocks = [token for token in MarkdownIt("commonmark").parse(text) if token.type == "fence"]
    if len(blocks) != 1:
        raise ContractError("review_envelope_requires_one_json_block")
    block = blocks[0]
    if (
        block.level != 0
        or block.info.strip() not in {"", "json"}
        or not _closes_code_fence(lines[block.map[1] - 1], block.markup)
    ):
        raise ContractError("review_envelope_invalid_json_fence")
    try:
        payload = json.loads(block.content)
    except json.JSONDecodeError as exc:
        raise ContractError(f"review_envelope_invalid_json:{exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ContractError("review_root_must_be_object")
    stated = verdict.group(1)
    expected = {"APPROVE": "correct", "REQUEST_CHANGES": "incorrect", "BLOCKED": "uncertain"}[stated]
    validate_reviewer_payload(payload)
    if payload["overall"]["correctness"] != expected:
        raise ContractError("review_envelope_verdict_mismatch")
    canonical = {"APPROVE": "APPROVED", "REQUEST_CHANGES": "CHANGES_REQUESTED", "BLOCKED": "BLOCKED"}[stated]
    try:
        derived, _ = checked_findings_payload(payload, stated=canonical)
    except ReviewPublicationError as exc:
        raise ContractError(f"review_envelope_invalid_verdict:{exc}") from exc
    if derived != canonical:
        raise ContractError("review_envelope_verdict_mismatch")
    return payload


_CORRECTNESS_FOR_VERDICT = {
    "APPROVE": "correct",
    "APPROVED": "correct",
    "REQUEST_CHANGES": "incorrect",
    "CHANGES_REQUESTED": "incorrect",
    "BLOCKED": "uncertain",
}


def canonical_receipt_payload(raw: str) -> dict[str, Any]:
    """Return the findings object when the reply can build a canonical receipt.

    A verdict line without the one JSON block, and a JSON object that misses
    ``confidence`` or ``verbatim``, still fail here. This does not accept a
    reply the recorder or ``verify_review`` would refuse.
    """
    text = raw.strip()
    payload = parse_reviewer_json(text)
    if not text.startswith("VERDICT:"):
        validate_reviewer_payload(payload)
    return payload


def _json_objects(text: str) -> list[dict[str, Any]]:
    """JSON objects in ``text``, including one that follows commentary."""
    found: list[dict[str, Any]] = []
    decoder = json.JSONDecoder()
    index = 0
    while True:
        start = text.find("{", index)
        if start < 0:
            return found
        try:
            payload, end = decoder.raw_decode(text, start)
        except (json.JSONDecodeError, RecursionError):
            index = start + 1
            continue
        if isinstance(payload, dict):
            found.append(payload)
        index = max(end, start + 1)


def _outside_blockquotes(text: str) -> str:
    """Drop CommonMark blockquotes so an example object cannot lock a decision."""
    from markdown_it import MarkdownIt

    from scripts.review.verdict_parser import _commonmark_lines

    raw_lines = _commonmark_lines(text, keepends=True)
    lines = _commonmark_lines(text)
    parser = MarkdownIt("commonmark")
    spans: list[tuple[int, int]] = []
    for token in parser.parse("\n".join(lines)):
        if token.type != "blockquote_open":
            continue
        source_map = token.map
        if not isinstance(source_map, (list, tuple)) or len(source_map) != 2:
            raise ValueError("CommonMark blockquote map unavailable")
        start, end = source_map
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(lines):
            raise ValueError("CommonMark blockquote map invalid")
        spans.append((start, end))
    parts: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        if end <= cursor:
            continue
        parts.extend(raw_lines[cursor:start])
        parts.append("\n")
        cursor = end
    parts.extend(raw_lines[cursor:])
    return "".join(parts)


def _effective_verdict(payload: Mapping[str, Any]) -> str | None:
    """The verdict the receipt's evidence states, when the payload can be read."""
    from scripts.fleet_comms.review_publication import ReviewPublicationError, resolve_verdict_and_evidence

    try:
        verdict, _evidence = resolve_verdict_and_evidence(payload)
    except ReviewPublicationError:
        return None
    return verdict


def _explanation_rejections(payload: Mapping[str, Any]) -> set[str]:
    """Rejection tokens written in an explanation, even when the object is not yet valid."""
    overall = payload.get("overall")
    if not isinstance(overall, Mapping):
        return set()
    explanation = overall.get("explanation")
    if not isinstance(explanation, str):
        return set()
    from scripts.fleet_comms.review_publication import _stated_verdicts

    return _stated_verdicts(explanation) - {"APPROVED"}


def _findings_candidate(payload: dict[str, Any]) -> bool:
    if payload.get("schema_version") == SCHEMA_VERSION:
        return True
    return isinstance(payload.get("overall"), dict) or isinstance(payload.get("findings"), list)


def decision_lock(raw: str) -> dict[str, Any]:
    """Freeze a reply's verdict and findings before one format correction.

    Not an approval path. ``ambiguous`` is true when the reply carries more
    than one verdict or more than one findings object. ``payload`` is set
    only when exactly one findings object is readable, even if it does not
    yet validate.
    """
    from scripts.review.verdict_parser import recognized_verdicts

    try:
        visible = _outside_blockquotes(raw)
    except ValueError:
        return {"ambiguous": True, "verdicts": [], "payload": None}
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()
    for payload in _json_objects(visible):
        if not _findings_candidate(payload):
            continue
        key = json.dumps(payload, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            objects.append(payload)
    verdicts = list(dict.fromkeys(recognized_verdicts(raw)))
    return {
        "ambiguous": len(objects) > 1 or len(verdicts) > 1,
        "verdicts": verdicts,
        "payload": objects[0] if len(objects) == 1 else None,
    }


def same_decision(lock: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
    """Whether a corrected reply kept the locked verdict and findings."""
    if lock.get("ambiguous"):
        return False
    stated = False
    prior = lock.get("payload")
    if isinstance(prior, Mapping):
        prior_overall = prior.get("overall")
        later = payload.get("overall")
        later_correctness = later.get("correctness") if isinstance(later, Mapping) else None
        if isinstance(prior_overall, Mapping) and "correctness" in prior_overall:
            stated = True
            if prior_overall.get("correctness") != later_correctness:
                return False
        if "findings" in prior and prior.get("findings") != payload.get("findings"):
            return False
    verdicts = list(lock.get("verdicts") or [])
    if len(verdicts) == 1:
        stated = True
        expected = _CORRECTNESS_FOR_VERDICT.get(str(verdicts[0]).upper())
        overall = payload.get("overall")
        got = overall.get("correctness") if isinstance(overall, Mapping) else None
        if expected is None or got != expected:
            return False
    if isinstance(prior, Mapping):
        prior_verdict = _effective_verdict(prior)
        later_verdict = _effective_verdict(payload)
        if prior_verdict is not None and later_verdict != prior_verdict:
            return False
        # A missing required field can hide a rejection the explanation already states.
        # Filling the field cannot turn that rejection into an approval.
        if prior_verdict is None and (rejections := _explanation_rejections(prior)):
            allowed = set()
            if rejections & {"CHANGES_REQUESTED", "REQUEST_CHANGES"}:
                allowed.add("CHANGES_REQUESTED")
            if "BLOCKED" in rejections:
                allowed.add("BLOCKED")
            if later_verdict not in allowed:
                return False
    return stated


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
        message = first.message
        if first.validator == "additionalProperties":
            # Name the allowed fields so the reviewer can correct the reply in the same round.
            message += f"; allowed: {sorted(first.schema.get('properties', {}))}"
        raise ContractError(
            f"schema_violation:{path}:{message}",
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


def finding_supports_approval(finding: Mapping[str, Any]) -> bool:
    disposition = finding.get("disposition")
    rationale = finding.get("disposition_rationale")
    if (
        not isinstance(disposition, str)
        or disposition not in ALLOWED_DISPOSITIONS - {"stop_and_escalate"}
        or not isinstance(rationale, str)
        or not rationale.strip()
    ):
        return False
    outcome = finding.get("outcome")
    return outcome == "verified" or (
        disposition == "follow_up"
        and isinstance(outcome, str)
        and outcome in UNVERIFIED_FOLLOW_UP_OUTCOMES
    )


def unverified_follow_up_notes(findings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(finding) for finding in findings
        if finding.get("outcome") != "verified" and finding_supports_approval(finding)
    ]


def _classify_exit(
    payload: dict[str, Any],
    validations: list[FindingValidation],
) -> tuple[int, str]:
    """Keep findings actionable, including non-blocking findings on correct code.

    ``correct`` with findings means no finding is blocking under critical-rules
    section 8.4. The findings and their dispositions remain in the receipt;
    lifecycle acceptance checks that approval without reclassifying it as clean.
    """
    outcomes = {v.outcome for v in validations}
    if OUTCOME_MALFORMED in outcomes:
        return EXIT_INVALID, EXIT_NAMES[EXIT_INVALID]
    bad_evidence = outcomes & UNVERIFIED_FOLLOW_UP_OUTCOMES
    approved_follow_ups = payload["overall"]["correctness"] == "correct" and all(
        finding_supports_approval(validation.to_dict()) for validation in validations
    )
    if bad_evidence and not approved_follow_ups:
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
    # Findings remain actionable even when the reviewer judges them non-blocking.
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
        "unverified_follow_up_notes": unverified_follow_up_notes([v.to_dict() for v in validations]),
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


def build_ukrainian_behavior_receipt(
    *,
    behavior_proof: dict[str, Any],
    frozen_intended_behavior: str,
    comments: Sequence[Mapping[str, Any]],
    authenticated_login: str,
    head_sha: str,
    author_attributions: Sequence[Mapping[str, str]],
    target: Mapping[str, Any],
    input_sha256: str,
    issue_ref: str,
    scope: Mapping[str, Any],
    tests: Mapping[str, Any],
    isolation_attestation_validator: Callable[[dict[str, Any], ReviewTarget], bool] | None = None,
    review_target: ReviewTarget | None = None,
) -> dict[str, Any]:
    """Receipt for a frozen ukrainian proof carrier.

    Reviewer identity is the recorded seat chunks. Caller reviewer flags and
    code-review findings are not inputs. The singular reviewer key is omitted.
    """
    from scripts.orchestration.integration_sweep import contributing_ukrainian_chunks

    provenance = contributing_ukrainian_chunks(
        comments,
        head_sha,
        authenticated_login,
        learner_content=True,
    )
    if provenance["refused"]:
        raise ContractError(
            f"ukrainian_seat_quorum_refused:{provenance['refused']}",
            exit_code=EXIT_INCOMPLETE,
        )
    by_model: dict[str, str] = {}
    for item in author_attributions:
        model = str(item.get("model") or "")
        harness = str(item.get("harness") or "")
        if not model or not harness or _is_placeholder(model) or _is_placeholder(harness):
            raise ContractError("author_attribution_unresolved", exit_code=EXIT_INCOMPLETE)
        previous = by_model.get(model)
        if previous is not None and previous != harness:
            raise ContractError("author_attribution_conflict", exit_code=EXIT_INCOMPLETE)
        by_model[model] = harness
    if tuple(sorted(by_model)) != tuple(provenance["author_models"]):
        raise ContractError("author_attribution_conflict", exit_code=EXIT_INCOMPLETE)
    incomplete, failures = _tests_envelope_status(dict(tests))
    if incomplete or failures:
        raise ContractError("tests_envelope_invalid", exit_code=EXIT_INCOMPLETE)
    proof_target = review_target or ReviewTarget(
        mode=str(target.get("mode") or "local"),
        base_sha=target.get("base_sha"),
        head_sha=target.get("head_sha"),
        changed_paths=tuple(target.get("changed_paths") or ()),
        non_test_loc=int(target.get("non_test_loc") or 0),
        clean_tree=bool(target.get("clean_tree")),
        description=str(target.get("description") or "ukrainian behavior proof"),
    )
    proof_incomplete, proof_failures = _behavior_proof_envelope_status(
        behavior_proof,
        target_input_sha256=input_sha256,
        frozen_intended_behavior=frozen_intended_behavior,
        isolation_attestation_validator=isolation_attestation_validator,
        target=proof_target,
    )
    if proof_incomplete or proof_failures:
        raise ContractError(
            "behavior_proof_invalid:" + ",".join([*proof_incomplete, *proof_failures]),
            exit_code=EXIT_INCOMPLETE,
        )
    author_models = list(provenance["author_models"])
    author_families = list(provenance["author_families"])
    harnesses = sorted(set(by_model.values()))
    author: dict[str, Any] = {
        "models": author_models,
        "families": author_families,
        "harnesses": harnesses,
        "selection_reason": "implementation-author",
        "selection_reason_source": "commit-x-agent",
    }
    if len(author_models) == 1 and len(author_families) == 1 and len(harnesses) == 1:
        author["model"] = author_models[0]
        author["family"] = author_families[0]
        author["harness"] = harnesses[0]
    seats = [dict(seat) for seat in provenance["seats"]]
    seat_names = [f"{seat['family']}:{chunk['model']}" for seat in seats for chunk in seat["chunks"]]
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "review_profile": "ukrainian",
        "issue_ref": issue_ref,
        "scope": dict(scope),
        "author": author,
        "ukrainian_seat_verdicts": seats,
        "target": {
            "mode": proof_target.mode,
            "base_sha": proof_target.base_sha,
            "head_sha": head_sha,
            "changed_paths": list(proof_target.changed_paths),
            "non_test_loc": proof_target.non_test_loc,
            "clean_tree": proof_target.clean_tree,
            "description": proof_target.description,
            "input_sha256": input_sha256,
        },
        "tests": dict(tests),
        "behavior_proof": _render_behavior_proof(behavior_proof),
        "final_disposition": "clean",
        "exit_code": EXIT_CLEAN,
        "error": None,
        "routing_lineage": {
            "implementation_agents": ",".join(author_models),
            "accountable_seats": ",".join(seat_names),
        },
    }

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
        disp = ctx.dispositions.get(finding["id"], {})
        rationale = disp.get("rationale") if isinstance(disp, dict) else None
        check: EvidenceCheckResult = verify_finding_evidence(
            finding,
            repo_root=ctx.repo_root,
            target=ctx.target,
            changed_lines=line_map,
            allow_unchanged_follow_up=(
                isinstance(disp, dict)
                and disp.get("disposition") == "follow_up"
                and isinstance(rationale, str)
                and bool(rationale.strip())
            ),
        )
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


# A chunked Ukrainian review. The tool builds the packet; the reviewer returns judgments only.
PACKET_SCHEMA = "ukrainian-item-packet.v1"
JUDGMENT_SCHEMA = "ukrainian-item-judgments.v1"
MAX_CHUNK_ROWS = 250
_JUDGMENT_KEYS = frozenset({"id", "verdict", "finding", "sources"})
_UKRAINIAN_JUDGMENT_KEYS = frozenset({"id", "verdict", "finding", "sources", "evidence", "_approval_void"})
_QUOTE_KEYS = frozenset({"quote", "quotes"})
_JUDGMENT_VERDICT = {
    "APPROVE": "APPROVED",
    "APPROVED": "APPROVED",
    "REQUEST_CHANGES": "CHANGES_REQUESTED",
    "CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "BLOCKED": "BLOCKED",
    "unknown": "UNKNOWN",
    "UNKNOWN": "UNKNOWN",
}


@dataclass(frozen=True)
class ClaimsValidationResult:
    claims_total: int
    claims_unsupported: int
    unknown_items: int
    dropped_claims: tuple[dict[str, Any], ...]


def validate_item_claims(
    payload: Mapping[str, Any],
    ledger_path: Path | None = None,
    binding: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ClaimsValidationResult]:
    """Validate item claims against the attempt receipt ledger, dropping unsupported references.

    A claim must cite an existing receipt in this attempt's ledger (matching review_id,
    attempt_id, manifest_sha256) and provide a non-empty quote that is a literal substring
    of that receipt's stored result. Unsupported and foreign-attempt citations are dropped,
    recorded with reasons for audit, and counted.
    """
    from scripts.review.receipts import ledger

    indexed: dict[str, dict[str, Any]] = {}
    foreign: dict[str, dict[str, Any]] = {}
    if ledger_path is not None and Path(ledger_path).exists():
        try:
            records = ledger.records(Path(ledger_path))
        except Exception:
            records = []
        for record in records:
            rid = record.get("receipt_id")
            if not isinstance(rid, str):
                continue
            if binding is not None:
                record_identity = (
                    record.get("review_id"),
                    record.get("attempt_id"),
                    record.get("manifest_sha256"),
                )
                expected_identity = (
                    binding.get("review_id"),
                    binding.get("attempt_id"),
                    binding.get("manifest_sha256"),
                )
                if record_identity == expected_identity:
                    indexed[rid] = record
                else:
                    foreign[rid] = record
            else:
                indexed[rid] = record

    if binding is not None:
        try:
            from scripts.dispatcher import store

            root = store.receipts_root()
            if root and root.exists():
                this_path = Path(ledger_path).resolve() if ledger_path else None
                for other_file in root.rglob("*.jsonl"):
                    if this_path and other_file.resolve() == this_path:
                        continue
                    try:
                        other_records = ledger.records(other_file)
                    except Exception:
                        continue
                    for o_rec in other_records:
                        o_rid = o_rec.get("receipt_id")
                        if isinstance(o_rid, str) and o_rid not in indexed:
                            foreign[o_rid] = o_rec
        except Exception:
            pass

    claims_total = 0
    claims_unsupported = 0
    unknown_items = 0
    dropped: list[dict[str, Any]] = []

    def _validate_claim(
        claim: Any,
        item_id: str | None = None,
        *,
        require_quote: bool = True,
    ) -> tuple[bool, str | None]:
        if not isinstance(claim, dict):
            return False, "malformed_claim"
        receipt = claim.get("receipt") or claim.get("receipt_id")
        quote = claim.get("quote")
        claim_keys = set(claim) - {"category", "outcome"}

        if require_quote:
            if claim_keys != {"receipt", "quote"} and claim_keys != {"receipt_id", "quote"}:
                return False, "malformed_claim"
            if not isinstance(receipt, str) or not receipt.strip():
                return False, "malformed_receipt"
            if not isinstance(quote, str) or not quote.strip():
                return False, "empty_quote"
            if receipt in foreign:
                return False, "foreign_attempt_receipt"
            if receipt not in indexed:
                return False, "receipt_not_found"
            rec = indexed[receipt]
            stored_result = rec.get("result")
            if not isinstance(stored_result, str) or quote not in stored_result:
                return False, "quote_not_in_result"
            return True, None

        # require_quote is False (for YAML findings, etc.)
        has_quote = "quote" in claim
        if has_quote:
            if claim_keys != {"receipt", "quote"} and claim_keys != {"receipt_id", "quote"}:
                return False, "malformed_claim"
            if not isinstance(quote, str) or not quote.strip():
                return False, "empty_quote"
        else:
            if claim_keys != {"receipt"} and claim_keys != {"receipt_id"}:
                return False, "malformed_claim"

        if not isinstance(receipt, str) or not receipt.strip():
            return False, "malformed_receipt"
        if receipt in foreign:
            return False, "foreign_attempt_receipt"
        if receipt not in indexed:
            return False, "receipt_not_found"

        if has_quote:
            rec = indexed[receipt]
            stored_result = rec.get("result")
            if not isinstance(stored_result, str) or quote not in stored_result:
                return False, "quote_not_in_result"

        return True, None

    updated_items = []
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            updated_items.append(item)
            continue
        item_copy = dict(item)
        verdict = _JUDGMENT_VERDICT.get(item_copy.get("verdict"))
        if verdict == "UNKNOWN":
            unknown_items += 1

        evidence = item_copy.get("evidence")
        if evidence is not None:
            was_dict = isinstance(evidence, dict)
            claims_list = [evidence] if was_dict else (list(evidence) if isinstance(evidence, list) else [evidence])
            valid_claims = []
            has_dropped = False
            for claim in claims_list:
                claims_total += 1
                ok, reason = _validate_claim(claim, item_copy.get("id"), require_quote=True)
                if not ok:
                    claims_unsupported += 1
                    has_dropped = True
                    dropped.append({
                        "item_id": item_copy.get("id"),
                        "claim": claim,
                        "reason": reason,
                    })
                else:
                    valid_claims.append(claim)

            if was_dict:
                if valid_claims:
                    item_copy["evidence"] = valid_claims[0]
                else:
                    item_copy.pop("evidence", None)
            else:
                item_copy["evidence"] = valid_claims

            if has_dropped and verdict == "APPROVED":
                item_copy["_approval_void"] = True

        updated_items.append(item_copy)

    updated_evidence = None
    if "evidence" in payload:
        evidence = payload["evidence"]
        was_dict = isinstance(evidence, dict)
        claims_list = [evidence] if was_dict else (list(evidence) if isinstance(evidence, list) else [evidence])
        valid_claims = []
        for claim in claims_list:
            claims_total += 1
            ok, reason = _validate_claim(claim, None, require_quote=False)
            if not ok:
                claims_unsupported += 1
                dropped.append({
                    "item_id": None,
                    "claim": claim,
                    "reason": reason,
                })
            else:
                valid_claims.append(claim)
        updated_evidence = (valid_claims[0] if valid_claims else None) if was_dict else valid_claims

    updated_broadened = None
    if "broadened_searches" in payload:
        broadened = payload["broadened_searches"]
        if isinstance(broadened, list):
            valid_searches = []
            for claim in broadened:
                claims_total += 1
                ok, reason = _validate_claim(claim, None, require_quote=True)
                if not ok:
                    claims_unsupported += 1
                    dropped.append({
                        "item_id": None,
                        "claim": claim,
                        "reason": reason,
                    })
                else:
                    valid_searches.append(claim)
            updated_broadened = valid_searches
        else:
            updated_broadened = broadened

    updated_findings = None
    if "findings" in payload:
        findings = payload["findings"]
        if isinstance(findings, list):
            updated_findings = []
            for finding in findings:
                if not isinstance(finding, dict):
                    updated_findings.append(finding)
                    continue
                f_copy = dict(finding)
                f_id = f_copy.get("id")
                valid_receipt_ids: list[str] = []

                if "evidence" in f_copy:
                    ev = f_copy["evidence"]
                    was_dict = isinstance(ev, dict)
                    claims_list = [ev] if was_dict else (list(ev) if isinstance(ev, list) else [ev])
                    valid_ev = []
                    for claim in claims_list:
                        claims_total += 1
                        ok, reason = _validate_claim(claim, f_id, require_quote=False)
                        if not ok:
                            claims_unsupported += 1
                            dropped.append({
                                "item_id": f_id,
                                "claim": claim,
                                "reason": reason,
                            })
                        else:
                            valid_ev.append(claim)
                            r_id = claim.get("receipt") or claim.get("receipt_id")
                            if isinstance(r_id, str):
                                valid_receipt_ids.append(r_id)
                    if was_dict:
                        if valid_ev:
                            f_copy["evidence"] = valid_ev[0]
                        else:
                            f_copy.pop("evidence", None)
                    else:
                        f_copy["evidence"] = valid_ev

                if "source_conflict" in f_copy and isinstance(f_copy["source_conflict"], dict):
                    sc = dict(f_copy["source_conflict"])
                    for side in ("a", "b"):
                        if side in sc and isinstance(sc[side], dict):
                            claims_total += 1
                            ok, reason = _validate_claim(sc[side], f_id, require_quote=False)
                            if not ok:
                                claims_unsupported += 1
                                dropped.append({
                                    "item_id": f_id,
                                    "claim": sc[side],
                                    "reason": reason,
                                })
                                sc.pop(side, None)
                            else:
                                r_id = sc[side].get("receipt") or sc[side].get("receipt_id")
                                if isinstance(r_id, str):
                                    valid_receipt_ids.append(r_id)
                    f_copy["source_conflict"] = sc

                if "unsupported_by_source" in f_copy and isinstance(f_copy["unsupported_by_source"], dict):
                    ubs = dict(f_copy["unsupported_by_source"])
                    if "searches" in ubs and isinstance(ubs["searches"], list):
                        valid_searches = []
                        for s in ubs["searches"]:
                            claims_total += 1
                            ok, reason = _validate_claim(s, f_id, require_quote=False)
                            if not ok:
                                claims_unsupported += 1
                                dropped.append({
                                    "item_id": f_id,
                                    "claim": s,
                                    "reason": reason,
                                })
                            else:
                                valid_searches.append(s)
                                r_id = s.get("receipt") or s.get("receipt_id")
                                if isinstance(r_id, str):
                                    valid_receipt_ids.append(r_id)
                        ubs["searches"] = valid_searches
                    f_copy["unsupported_by_source"] = ubs

                if "expected" in f_copy:
                    expected = f_copy["expected"]
                    claims_total += 1
                    ok = False
                    reason = None
                    if not isinstance(expected, str) or not expected.strip():
                        reason = "empty_quote"
                    else:
                        stored_results = []
                        for rid in valid_receipt_ids:
                            rec = indexed.get(rid)
                            if isinstance(rec, dict) and isinstance(rec.get("result"), str):
                                stored_results.append(rec["result"])
                        if not stored_results or not any(expected in res for res in stored_results):
                            reason = "quote_not_in_result"
                        else:
                            ok = True

                    if not ok:
                        claims_unsupported += 1
                        dropped.append({
                            "item_id": f_id,
                            "claim": {"expected": expected},
                            "reason": reason,
                        })
                        f_copy.pop("expected", None)

                updated_findings.append(f_copy)

    updated_payload = dict(payload)
    if "items" in payload:
        updated_payload["items"] = updated_items
    if "evidence" in payload:
        if updated_evidence is not None:
            updated_payload["evidence"] = updated_evidence
        else:
            updated_payload.pop("evidence", None)
    if updated_broadened is not None:
        updated_payload["broadened_searches"] = updated_broadened
    if updated_findings is not None:
        updated_payload["findings"] = updated_findings

    return updated_payload, ClaimsValidationResult(
        claims_total=claims_total,
        claims_unsupported=claims_unsupported,
        unknown_items=unknown_items,
        dropped_claims=tuple(dropped),
    )


@dataclass(frozen=True)
class ItemChunk:
    """The items one chunk verdict covers. ``void`` means that coverage does not count."""

    denominator: tuple[str, ...]
    coverage: tuple[str, ...]
    void: str | None = None


def _fenced(text: str, info: str) -> list[str]:
    return re.findall(rf"^```{re.escape(info)}[ \t]*\n(.*?)\n```[ \t]*$", text, re.M | re.S)


def _item_id(value: object, label: str) -> str:
    if not isinstance(value, str) or ITEM_ID_RE.fullmatch(value) is None:
        raise ContractError(f"{label} is not an item id")
    return value


def _frozen_row(item: Mapping[str, Any]) -> dict[str, str]:
    row = {"id": _item_id(item.get("id"), "item id"), "text": item.get("text")}
    if not isinstance(row["text"], str):
        raise ContractError(f"{row['id']}: frozen item text must be a string")
    activity = item.get("activity")
    if activity is not None:
        if not isinstance(activity, str) or not activity:
            raise ContractError(f"{row['id']}: activity must be a non-empty string")
        row["activity"] = activity
    return row


def split_item_chunks(
    items: Sequence[Mapping[str, Any]], *, limit: int = MAX_CHUNK_ROWS
) -> list[tuple[dict[str, str], ...]]:
    """Split frozen items into chunks of at most ``limit`` rows, never splitting an activity."""
    if limit < 1:
        raise ContractError("chunk limit must be positive")
    rows = [_frozen_row(item) for item in items]
    if len({row["id"] for row in rows}) != len(rows):
        raise ContractError("duplicate item id")
    groups: list[list[dict[str, str]]] = []
    by_activity: dict[str, list[dict[str, str]]] = {}
    for row in sorted(rows, key=lambda item: item["id"]):
        activity = row.get("activity")
        if activity is None:
            groups.append([row])
            continue
        by_activity.setdefault(activity, []).append(row)
    for activity, grouped in by_activity.items():
        if len(grouped) > limit:
            raise ContractError(f"activity {activity!r} has {len(grouped)} items, above the {limit}-row chunk limit")
        groups.append(grouped)
    groups.sort(key=lambda group: group[0]["id"])
    chunks: list[tuple[dict[str, str], ...]] = []
    current: list[dict[str, str]] = []
    for group in groups:
        if current and len(current) + len(group) > limit:
            chunks.append(tuple(current))
            current = []
        current.extend(group)
    if current:
        chunks.append(tuple(current))
    return chunks


def build_item_packet(
    items: Sequence[Mapping[str, Any]], *, denominator: Sequence[str] | None = None
) -> dict[str, Any]:
    """Per-item table, offsets, pointers, counts and coverage for one chunk of frozen items.

    Offsets are into this chunk's own text: the item texts in id order, joined by a newline.
    ``denominator`` is the brief's full item set. It defaults to this chunk's ids.
    """
    rows = [_frozen_row(item) for item in items]
    if len({row["id"] for row in rows}) != len(rows):
        raise ContractError("duplicate item id")
    if not rows:
        raise ContractError("ITEM_PACKET_EMPTY: a packet needs at least one item")
    if len(rows) > MAX_CHUNK_ROWS:
        raise ContractError(f"chunk exceeds {MAX_CHUNK_ROWS} items")
    ordered = sorted(rows, key=lambda row: row["id"])
    ids = [row["id"] for row in ordered]
    declared = [_item_id(item, "denominator id") for item in (ids if denominator is None else denominator)]
    if declared != sorted(set(declared)):
        raise ContractError("denominator must be sorted, unique item ids")
    if not set(ids) <= set(declared):
        raise ContractError("chunk items are outside the denominator")
    table = []
    cursor = 0
    for index, row in enumerate(ordered):
        if index:
            cursor += 1
        text = row["text"]
        table.append(
            {
                "id": row["id"],
                "offset": cursor,
                "end": cursor + len(text),
                "length": len(text),
                "text": text,
                "pointer": f"items/{row['id']}",
                "state": "unreviewed",
            }
        )
        cursor += len(text)
    return {
        "schema": PACKET_SCHEMA,
        "denominator": declared,
        "coverage": ids,
        "counts": {"items": len(table), "unreviewed": len(table)},
        "items": table,
    }


def render_item_packet(packet: Mapping[str, Any]) -> str:
    """The fence the review brief hands to the reviewer. The reviewer does not rebuild it."""
    body = json.dumps(packet, ensure_ascii=False, indent=2)
    return f"```ukrainian-item-packet\n{body}\n```\n"


def parse_item_packet(text: str) -> dict[str, Any]:
    """The one tool-built packet in ``text``. A hand-edited offset, count or pointer is refused."""
    bodies = _fenced(text, "ukrainian-item-packet")
    if len(bodies) != 1:
        raise ContractError("ITEM_PACKET_COUNT: the brief must contain one item packet")
    try:
        payload = json.loads(bodies[0])
    except json.JSONDecodeError as exc:
        raise ContractError(f"ITEM_PACKET_MALFORMED: {exc.msg}") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ContractError("ITEM_PACKET_MALFORMED: packet items are required")
    if not isinstance(payload.get("denominator"), list):
        raise ContractError("ITEM_PACKET_MALFORMED: packet denominator is required")
    frozen = []
    for row in payload["items"]:
        if not isinstance(row, dict):
            raise ContractError("ITEM_PACKET_MALFORMED: each item must be an object")
        frozen.append({"id": row.get("id"), "text": row.get("text")})
    expected = build_item_packet(frozen, denominator=payload["denominator"])
    if payload != expected:
        raise ContractError(
            "PACKET_NOT_TOOL_BUILT: offsets, counts, pointers or coverage do not match the frozen items"
        )
    return expected


def load_frozen_item_packet(task: Mapping[str, Any]) -> dict[str, Any] | None:
    """The packet frozen in the task's brief, or None when that brief declares no denominator.

    A task that names a brief must still be readable, and a stored prompt digest must
    match the bytes on disk, before the absence of a packet means there is no
    denominator. A missing, unreadable or drifted brief is not an unchunked review.
    """
    path = task.get("prompt_file")
    if not isinstance(path, str) or not path:
        return None
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ContractError("FROZEN_BRIEF_UNREADABLE: the frozen review brief cannot be read") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ContractError("FROZEN_BRIEF_UNREADABLE: review brief is not utf-8") from exc
    digest = task.get("prompt_sha256")
    if isinstance(digest, str) and digest and hashlib.sha256(raw).hexdigest() != digest:
        raise ContractError("FROZEN_BRIEF_MISMATCH: the item packet is not the brief the task froze")
    if "```ukrainian-item-packet" not in text:
        return None
    if not (isinstance(digest, str) and digest):
        raise ContractError("FROZEN_BRIEF_MISMATCH: the item packet is not the brief the task froze")
    return parse_item_packet(text)


def reply_has_item_judgments(reply: str) -> bool:
    return "```ukrainian-item-judgments" in reply


# Opener to the marks that can close it. An apostrophe between two letters is part of
# the word (м'ясо, п’ять), not a boundary, so a pair can contain one.
_QUOTE_CLOSERS = {
    "«": ("»",),
    "„": ("“", "”", '"'),
    "“": ("”",),
    '"': ('"',),
    "‘": ("’",),
    "'": ("'",),
    "`": ("`",),
}
_APOSTROPHES = frozenset({"'", "’"})


def _presented_quotes(text: str) -> list[str]:
    """Complete paired quotations in ``text``. An interior word apostrophe stays inside the pair."""
    spans: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        mark = text[index]
        closers = _QUOTE_CLOSERS.get(mark)
        if closers is None or _interior_apostrophe(text, index):
            index += 1
            continue
        end = index + 1
        while end < length:
            if text[end] in closers and not _interior_apostrophe(text, end):
                span = text[index + 1 : end]
                if span:
                    spans.append(span)
                index = end
                break
            end += 1
        index += 1
    return spans


def _interior_apostrophe(text: str, index: int) -> bool:
    mark = text[index]
    if mark not in _APOSTROPHES or index == 0 or index + 1 == len(text):
        return False
    return text[index - 1].isalpha() and text[index + 1].isalpha()


def _quote_spans(row: Mapping[str, Any]) -> list[str] | None:
    """Spans the judgment presents as quotes of the frozen item, or None when one is not text."""
    spans: list[str] = []
    if "quote" in row:
        quote = row["quote"]
        if not isinstance(quote, str):
            return None
        spans.append(quote)
    if "quotes" in row:
        quotes = row["quotes"]
        if not isinstance(quotes, list) or not all(isinstance(item, str) for item in quotes):
            return None
        spans.extend(quotes)
    return spans


def _rollup(verdicts: Sequence[str]) -> str:
    if any(item == "BLOCKED" for item in verdicts):
        return "BLOCKED"
    if any(item == "CHANGES_REQUESTED" for item in verdicts):
        return "CHANGES_REQUESTED"
    return "APPROVED"


def judge_item_reply(
    packet: Mapping[str, Any], reply: str, *, stated: str, ukrainian: bool = False
) -> ItemChunk:
    """Coverage of one chunk. A quote that is not a literal substring of its item voids the chunk.

    The reply's only payload is per-item verdict, finding and Sources evidence, keyed by the
    packet's item id. Offsets, counts, pointers, tables and a coverage set void it as
    reviewer bookkeeping and do not count. A quote of the frozen item, in the quote fields
    or as a quoted span in the finding, the Sources evidence or the reply, must be
    a literal substring. On an approval that mismatch voids the chunk. It does not erase a
    rejection verdict.
    """
    bodies = _fenced(reply, "ukrainian-item-judgments")
    if len(bodies) != 1:
        raise ContractError("ITEM_JUDGMENTS_MISSING: a declared item denominator needs one judgment block")
    try:
        payload = json.loads(bodies[0])
    except json.JSONDecodeError as exc:
        raise ContractError(f"ITEM_JUDGMENTS_MALFORMED: {exc.msg}") from None
    if not isinstance(payload, dict) or payload.get("schema") != JUDGMENT_SCHEMA:
        raise ContractError("ITEM_JUDGMENTS_MALFORMED: judgments schema is required")
    rows = payload.get("items")
    if not isinstance(rows, list) or not rows:
        raise ContractError("ITEM_JUDGMENTS_MALFORMED: judgments need at least one item")
    frozen = {row["id"]: row["text"] for row in packet["items"]}
    allowed = set(packet["coverage"])
    bookkeeping = bool(set(payload) - {"schema", "items"})
    quote_bad = False
    seen_ids: set[str] = set()
    judged: list[str] = []
    verdicts: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError("ITEM_JUDGMENTS_MALFORMED: each judgment must be an object")
        item_id = row.get("id")
        if not isinstance(item_id, str) or item_id not in allowed:
            raise ContractError("ITEM_OUTSIDE_CHUNK: a judgment names an item this chunk was not given")
        if item_id in seen_ids:
            raise ContractError(f"ITEM_JUDGMENTS_MALFORMED: duplicate judgment {item_id}")
        seen_ids.add(item_id)
        verdict = _JUDGMENT_VERDICT.get(row.get("verdict"))
        finding = row.get("finding")
        sources = row.get("sources")
        if verdict is None or not isinstance(finding, str) or not isinstance(sources, str):
            raise ContractError(f"ITEM_JUDGMENTS_MALFORMED: {item_id} needs a verdict, finding and sources")
        allowed_keys = _UKRAINIAN_JUDGMENT_KEYS if ukrainian else _JUDGMENT_KEYS
        if set(row) - allowed_keys - _QUOTE_KEYS:
            bookkeeping = True
        spans = _quote_spans(row)
        item_text = frozen[item_id]
        presented = _presented_quotes(finding) + _presented_quotes(sources)
        if spans is None or any(not span or span not in item_text for span in spans):
            quote_bad = True
        if any(span not in item_text for span in presented):
            quote_bad = True
        if verdict != "UNKNOWN" and not row.get("_approval_void"):
            judged.append(item_id)
        verdicts.append(verdict)
    outside = re.sub(
        r"^```ukrainian-item-judgments[ \t]*\n.*?\n```[ \t]*\n?",
        "",
        reply,
        count=1,
        flags=re.M | re.S,
    )
    item_texts = tuple(frozen.values())
    if any(all(span not in text for text in item_texts) for span in _presented_quotes(outside)):
        quote_bad = True
    rollup = _rollup(verdicts)
    if rollup != stated:
        raise ContractError("VERDICT_ITEM_MISMATCH: the verdict line does not match the item judgments")
    # A mismatched quote drops an approval's coverage. It must not hide a rejection.
    if quote_bad and rollup == "APPROVED":
        void: str | None = VOID_QUOTE_MISMATCH
    elif bookkeeping:
        void = VOID_REVIEWER_BOOKKEEPING
    else:
        void = None
    covered = () if void else tuple(sorted(judged))
    return ItemChunk(tuple(packet["denominator"]), covered, void)
