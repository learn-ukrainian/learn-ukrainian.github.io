"""Strict structured code-review contract: schema validation, exits, receipts.

Canonical format is versioned JSON (``code-review-findings.v1``). Legacy
``FINDING:`` text blocks are **removed** as a dual source of truth — they fail
closed as invalid input (issue #5284 compatibility decision).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.review.evidence import (
    OUTCOME_LINE_MISMATCH,
    OUTCOME_MALFORMED,
    OUTCOME_OUT_OF_SCOPE,
    OUTCOME_QUOTE_MISSING,
    OUTCOME_VERIFIED,
    EvidenceCheckResult,
    changed_lines_map,
    normalize_line_endings,
    verify_finding_evidence,
)
from scripts.review.target_resolution import ReviewTarget

SCHEMA_VERSION = "code-review-findings.v1"
RECEIPT_SCHEMA_VERSION = "code-review-receipt.v1"
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
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ContractError(f"schema_unavailable:{path}:{exc}", exit_code=EXIT_INVALID) from exc


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _looks_like_legacy_text(raw: str) -> bool:
    return bool(_LEGACY_FINDING_RE.search(raw))


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
    except ImportError as exc:  # pragma: no cover - venv always has jsonschema
        raise ContractError("jsonschema_unavailable", exit_code=EXIT_INVALID) from exc

    sch = schema if schema is not None else load_schema(tooling_root)
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
    input_sha256: str
    expected_head: str | None = None
    expected_input_sha256: str | None = None
    tests: dict[str, Any] = field(default_factory=dict)
    behavior_proof: dict[str, Any] = field(default_factory=dict)
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
            "input_sha256": ctx.input_sha256,
        },
        "findings": [v.to_dict() for v in validations],
        "tests": ctx.tests,
        "behavior_proof": ctx.behavior_proof,
        "final_disposition": final_disposition,
        "exit_code": exit_code,
        "error": error,
        "routing_lineage": ctx.routing_lineage
        or {
            "implementation_agent": "grok/5284-strict-review-receipts",
            "accountable_advisor": "GPT-5.6 Sol",
            "selection_note": (
                "Grok 4.5 high substituted for the issue's provisional Claude "
                "developer due to live routing-budget recommendation; "
                "GPT-5.6 Sol remains accountable advisor/integrator and "
                "cross-family reviewer."
            ),
        },
    }
    if payload is not None:
        receipt["reviewer_payload"] = {
            "schema_version": payload.get("schema_version"),
            "overall": payload.get("overall"),
            "finding_ids": [f["id"] for f in payload.get("findings", [])],
        }
    return receipt


def verify_review(
    raw_input: str,
    ctx: VerifyContext,
    *,
    schema: dict[str, Any] | None = None,
) -> VerifyResult:
    """Full pipeline: parse → schema → stale checks → evidence → receipt."""
    input_hash = sha256_text(raw_input)
    # Prefer the hash the runner computed when building ctx, but keep consistency.
    if ctx.input_sha256 and ctx.input_sha256 != input_hash:
        # Runner may have hashed a different byte string; trust recomputed hash
        # for the receipt and treat expected hash checks against ctx fields.
        pass
    ctx.input_sha256 = input_hash

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
                disposition=disp.get("disposition"),
                disposition_rationale=disp.get("rationale"),
            )
        )

    exit_code, final_disposition = _classify_exit(payload, validations)
    receipt = build_receipt(
        ctx,
        payload=payload,
        validations=validations,
        exit_code=exit_code,
        final_disposition=final_disposition,
        error=None,
    )
    return VerifyResult(
        exit_code=exit_code,
        final_disposition=final_disposition,
        payload=payload,
        validations=validations,
        receipt=receipt,
        error=None,
    )


def normalize_for_hash(raw: str) -> str:
    """Expose line-ending-only normalization for callers that need it."""
    return normalize_line_endings(raw)
