"""Convergent review loop with deterministic fixes and honest terminals."""

from __future__ import annotations

import hashlib
import time
import traceback
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from build.alignment_manifest import compose_manifest
from build.finding_normalizer import normalize_findings
from build.finding_topology import classify_topology
from build.module_memory import (
    PLAN_LEVEL_ERROR_CLASSES,
    WRITER_ADDRESSABLE_ERROR_CLASSES,
    append_history,
    load_module_memory,
    save_module_memory,
    upsert_constraint,
)
from build.patchability import (
    classify_patchability,
    compute_anchor_validation,
    validate_fix_anchors,
)

TerminalType = Literal["pass", "plan_revision_request", "budget_exhausted"]
TierName = Literal["patch", "plan_revision_request"]

# Single source of truth for the "ghost-finding" patchability status.
# GH #1529 P3 surfaces reviewer-emitted findings whose <fixes> anchor does not
# exist in current content — the reviewer hallucinated the text it claimed to
# quote. The predicate already tags these as anchor_missing (see
# build/patchability.py); this constant lets downstream callers (v6_build
# bundle writer, reviewer_ghosts_router) match the status without duplicating
# the string literal across files.
REVIEWER_GHOST_PATCHABILITY_STATUS: Literal["anchor_missing"] = "anchor_missing"


class RecoverableValidationError(Exception):
    """Raised by writer-output validators (sidecar drift, missing vocab, activity-order
    mismatch, word-budget miss) with structured findings for the next strategy
    selection instead of collapsing the convergence budget immediately.

    Use for content-shape problems in the *writer's* output. Do NOT use for pipeline
    or tooling failures (missing plan file, DB unreachable, subprocess crash) — those
    remain generic exceptions and terminate the loop.
    """

    def __init__(
        self,
        message: str,
        findings: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ) -> None:
        super().__init__(message)
        self.findings: tuple[dict[str, Any], ...] = tuple(findings)


@dataclass(frozen=True)
class ReviewObservation:
    passed: bool
    score: float
    review_text: str
    findings: tuple[dict[str, Any], ...]
    dim_floor_dimensions: tuple[str, ...]
    content_hash: str
    patch_available: bool = False
    parsed_scores: tuple[dict[str, Any], ...] = ()
    reviewer: str = ""
    writer_model_version: str = ""
    reviewer_model_version: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    input_tokens: int | None = None
    output_tokens: int | None = None
    # GH #1525 P0: validated-patchability predicate inputs. Callers that
    # populate both (real observations from v6_build) get the predicate.
    # Legacy callers that leave defaults (None) get "not_evaluated" — topology
    # classifier drives routing alone, preserving pre-P0 behavior.
    # An empty TUPLE (not None) means "observation was populated; reviewer
    # emitted zero fixes" → "no_fixes" status. Do NOT collapse () → None.
    parsed_fixes: tuple[dict[str, Any], ...] | None = None
    module_content: str | None = None
    # GH #1529 P3: reviewer ghost-findings — entries copied here when the
    # reviewer-emitted <fixes> anchor is not present in module_content. The
    # bundle writer (v6_build._write_reviewer_ghost_bundle) and the API
    # endpoint (/api/state/reviewer-ghosts) consume this directly so ghost
    # findings stay visible even if convergence escalates to plan_revision.
    # Primary ``findings`` list is NOT trimmed — reviewer still emitted the
    # finding, audit trail keeps it visible there too.
    reviewer_ghost_findings: tuple[dict[str, Any], ...] = ()

    @property
    def has_reviewer_ghosts(self) -> bool:
        """Convenience flag: True iff at least one ghost finding was tagged."""
        return bool(self.reviewer_ghost_findings)


@dataclass(frozen=True)
class MutationSummary:
    changed: bool
    mutation_count: int
    summary: str


@dataclass(frozen=True)
class ConvergenceDecision:
    tier: int
    strategy: TierName
    reason: str
    prioritized_findings: tuple[dict[str, Any], ...]
    stall_signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConvergenceRunResult:
    terminal: TerminalType
    rounds: tuple[dict[str, Any], ...]
    trace: tuple[dict[str, Any], ...]
    writer: str
    artifact_path: Path | None = None


ReviewCallback = Callable[[str], ReviewObservation]
PatchCallback = Callable[[ReviewObservation], MutationSummary]
RefreshCallback = Callable[[str], bool]


@dataclass
class ConvergenceContext:
    level: str
    slug: str
    writer: str
    review_round: ReviewCallback
    patch_round: PatchCallback
    refresh_sidecars: RefreshCallback
    memory_path: Path
    terminal_dir: Path
    stuck_modules_path: Path
    plan_hash: str
    plan_version: int
    sources_hash: str
    growth_log_path: Path | None = None
    max_escalations: int = 5


def _severity_rank(severity: str) -> int:
    order = {
        "critical": 0,
        "major": 1,
        "high": 1,
        "medium": 2,
        "minor": 3,
        "low": 4,
    }
    return order.get(str(severity or "").lower(), 9)


def _stable_hash(value: Any) -> str:
    payload = yaml.safe_dump(value, sort_keys=True, allow_unicode=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_observation(
    observation: ReviewObservation,
    *,
    growth_log_path: Path | None,
) -> tuple[dict[str, Any], ...]:
    normalized = normalize_findings(list(observation.findings), growth_log_path=growth_log_path)
    results = []
    floor_dimensions = set(observation.dim_floor_dimensions)
    # GH #1525 P0: validated-patchability predicate. Anchor validation runs
    # ONCE per observation (O(fixes) substring scans total) rather than per
    # finding (O(findings × fixes)). See build/patchability.py.
    # Pass parsed_fixes as-is — empty tuple MUST propagate as "no_fixes",
    # not collapse to None (which would be "not_evaluated"). None sentinel
    # is reserved for legacy callers that didn't populate the field.
    anchor_validation = compute_anchor_validation(
        observation.parsed_fixes,
        observation.module_content,
    )
    for item in normalized:
        classifier_topology = classify_topology(item)
        patchability_status, patchability_reason = classify_patchability(
            item, anchor_validation=anchor_validation
        )
        # Override ONLY when the predicate fully validates. Plan-level hardstop,
        # anchor_missing, no_fixes, and not_evaluated all leave the classifier's
        # output intact — preserves plan_revision_request routing for genuine
        # plan defects and for reviewer-side anchor bugs.
        effective_topology = classifier_topology
        if patchability_status == "patch_ok" and classifier_topology != "local_to_prose":
            effective_topology = "local_to_prose"
        severity = "critical" if item["dimension"] in floor_dimensions else item["severity"]
        results.append(
            {
                **item,
                "topology": effective_topology,
                "topology_classifier_output": classifier_topology,
                "patchability": patchability_status,
                "patchability_reason": patchability_reason,
                "effective_severity": severity,
            }
        )
    return tuple(
        sorted(
            results,
            key=lambda item: (
                _severity_rank(item["effective_severity"]),
                item["dimension"],
                item["error_class"],
                item["normalized_id"],
            ),
        )
    )


def _fix_anchor_text(fix: dict[str, Any]) -> str:
    """Return the anchor string used by ``_apply_review_fixes`` to locate the fix.

    Mirrors dispatch order in ``patchability._has_valid_anchor``: insert_after
    is checked FIRST because ``_apply_review_fixes`` uses it in preference to
    ``find`` when both keys are present.
    """
    if "insert_after" in fix and "text" in fix:
        return str(fix.get("insert_after") or "")
    if "find" in fix and "replace" in fix:
        return str(fix.get("find") or "")
    return ""


def _best_match_invalid_fix(
    finding: dict[str, Any],
    invalid_fixes: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    """Heuristically pair a ghost finding with the invalid fix it most likely refers to.

    Reviewer output format does not link findings to ``<fixes>`` entries by ID,
    so we match by substring: if the invalid fix's anchor text appears in the
    finding's ``fix`` or ``issue`` prose, assume they are paired. Falls back to
    the first invalid fix when no content overlap is found, so the bundle still
    attaches a concrete ``raw_fix`` for audit.
    """
    if not invalid_fixes:
        return None
    fix_text = str(finding.get("fix") or "").lower()
    issue_text = str(finding.get("issue") or "").lower()
    for fix in invalid_fixes:
        anchor = _fix_anchor_text(fix).lower()
        if not anchor:
            continue
        probe = anchor[:60]
        if probe and (probe in fix_text or probe in issue_text):
            return fix
    return invalid_fixes[0]


def collect_reviewer_ghost_findings(
    observation: ReviewObservation,
    *,
    growth_log_path: Path | None = None,
    normalized: Sequence[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Build the ghost-finding tuple for an observation.

    A ghost finding is a reviewer-emitted finding whose patchability status
    resolves to :data:`REVIEWER_GHOST_PATCHABILITY_STATUS` — i.e. the anchor
    text the reviewer "quoted" cannot be located in current module content.

    Each returned dict preserves the normalized finding fields and adds three
    bundle-writer affordances:
      * ``reviewer_find_anchor`` — the non-existent string
      * ``anchor_validation`` — always :data:`REVIEWER_GHOST_PATCHABILITY_STATUS`
      * ``raw_fix`` — the full reviewer-emitted fix dict that failed validation

    Pass ``normalized`` when the caller already ran ``_normalize_observation``
    to avoid a second normalization pass. Otherwise the helper normalizes
    internally using ``growth_log_path``.
    """
    if not observation.parsed_fixes or not observation.module_content:
        return ()
    _valid, invalid_fixes = validate_fix_anchors(
        observation.parsed_fixes, observation.module_content
    )
    if not invalid_fixes:
        return ()
    findings = (
        tuple(normalized)
        if normalized is not None
        else _normalize_observation(observation, growth_log_path=growth_log_path)
    )
    ghosts: list[dict[str, Any]] = []
    for item in findings:
        if item.get("patchability") != REVIEWER_GHOST_PATCHABILITY_STATUS:
            continue
        matched_fix = _best_match_invalid_fix(item, invalid_fixes)
        anchor = _fix_anchor_text(matched_fix) if matched_fix else ""
        ghosts.append(
            {
                **item,
                "reviewer_find_anchor": anchor,
                "anchor_validation": REVIEWER_GHOST_PATCHABILITY_STATUS,
                "raw_fix": dict(matched_fix) if matched_fix else {},
            }
        )
    return tuple(ghosts)


def tag_reviewer_ghosts(
    observation: ReviewObservation,
    *,
    growth_log_path: Path | None = None,
) -> ReviewObservation:
    """Return a copy of ``observation`` with ``reviewer_ghost_findings`` populated.

    Returns the input observation unchanged when no ghosts are detected so the
    common no-ghost path is zero-cost beyond the anchor scan. Callers who also
    need the normalized findings should call ``collect_reviewer_ghost_findings``
    and ``prioritize_findings`` directly to share one normalization pass.
    """
    ghosts = collect_reviewer_ghost_findings(
        observation, growth_log_path=growth_log_path
    )
    if not ghosts:
        return observation
    return replace(observation, reviewer_ghost_findings=ghosts)


def _top_ids(findings: tuple[dict[str, Any], ...], limit: int = 3) -> tuple[str, ...]:
    return tuple(item["normalized_id"] for item in findings[:limit])


def _stall_signals(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> tuple[str, ...]:
    if previous is None:
        return ()

    signals: list[str] = []
    previous_floors = set(previous.get("dim_floor_dimensions") or ())
    current_floors = set(current.get("dim_floor_dimensions") or ())
    if previous_floors & current_floors:
        signals.append("hard_floor_persisted")

    previous_top = set(_top_ids(previous.get("prioritized_findings") or ()))
    current_top = set(_top_ids(current.get("prioritized_findings") or ()))
    if len(previous_top & current_top) >= 2:
        signals.append("top3_overlap")

    if previous.get("content_hash") and previous.get("content_hash") == current.get("content_hash"):
        signals.append("content_hash_repeat")

    if previous.get("strategy") == "patch" and int(previous.get("mutation_count") or 0) == 0:
        signals.append("zero_mutation_patch")

    return tuple(signals)


def prioritize_findings(
    observation: ReviewObservation,
    *,
    growth_log_path: Path | None,
) -> tuple[dict[str, Any], ...]:
    return _normalize_observation(observation, growth_log_path=growth_log_path)


def select_strategy(
    *,
    observation: ReviewObservation,
    prioritized_findings: tuple[dict[str, Any], ...],
    previous_round: dict[str, Any] | None,
) -> ConvergenceDecision:
    if not prioritized_findings:
        return ConvergenceDecision(
            tier=5,
            strategy="plan_revision_request",
            reason="review failed without structured findings",
            prioritized_findings=prioritized_findings,
        )

    topologies = {item["topology"] for item in prioritized_findings}
    candidate_tier = 5
    candidate_strategy: TierName = "plan_revision_request"
    candidate_reason = "findings require human plan revision"

    if observation.patch_available and topologies == {"local_to_prose"}:
        candidate_tier = 1
        candidate_strategy = "patch"
        candidate_reason = "all findings are local prose edits and reviewer emitted deterministic fixes"

    signals = _stall_signals(previous_round, {
        "strategy": previous_round.get("strategy") if previous_round else "write",
        "mutation_count": previous_round.get("mutation_count") if previous_round else 0,
        "content_hash": observation.content_hash,
        "prioritized_findings": prioritized_findings,
        "dim_floor_dimensions": observation.dim_floor_dimensions,
    })
    if previous_round and signals and candidate_strategy == "patch":
        candidate_tier = 5
        candidate_strategy = "plan_revision_request"
        candidate_reason = f"stall detected ({', '.join(signals)})"

    return ConvergenceDecision(
        tier=candidate_tier,
        strategy=candidate_strategy,
        reason=candidate_reason,
        prioritized_findings=prioritized_findings,
        stall_signals=signals,
    )


def _record_round(
    *,
    memory: dict[str, Any],
    observation: ReviewObservation,
    prioritized_findings: tuple[dict[str, Any], ...],
    attempt: int,
    strategy: str,
    writer: str,
    decision_reason: str,
    mutation: MutationSummary | None,
    started_at: str,
    wall_clock_s: float,
) -> dict[str, Any]:
    scores = {
        str(score.get("name") or score.get("dimension")): score.get("score")
        for score in observation.parsed_scores
    }
    prompt_hash = _stable_hash("")
    prompt_path = observation.artifacts.get("prompt_path")
    if prompt_path:
        prompt_file = Path(prompt_path)
        if prompt_file.exists():
            prompt_hash = _stable_hash(prompt_file.read_text("utf-8"))
    round_record = {
        "attempt": attempt,
        "strategy": strategy,
        "writer": writer,
        "writer_model_version": observation.writer_model_version or writer,
        "reviewer": observation.reviewer,
        "reviewer_model_version": observation.reviewer_model_version or observation.reviewer,
        "score_overall": observation.score,
        "scores_per_dimension": scores,
        "dim_floor_fail": list(observation.dim_floor_dimensions),
        "verdict": "pass" if observation.passed else "revise",
        "content_hash": observation.content_hash,
        "prompt_hash": prompt_hash,
        "contract_snapshot_hash": _stable_hash(observation.artifacts),
        "findings_normalized": [item["normalized_id"] for item in prioritized_findings],
        "mutation_summary": None
        if mutation is None
        else {
            "changed": mutation.changed,
            "mutation_count": mutation.mutation_count,
            "summary": mutation.summary,
        },
        "decision_reason": decision_reason,
        "artifacts": dict(observation.artifacts),
        "timestamps": {
            "started": started_at,
            "finished": datetime.now(tz=UTC).isoformat(),
        },
        "cost": {
            "input_tokens": observation.input_tokens,
            "output_tokens": observation.output_tokens,
            "wall_clock_s": round(wall_clock_s, 3),
        },
    }
    append_history(memory, round_record)
    return round_record


def _record_exception_round(
    *,
    memory: dict[str, Any],
    attempt: int,
    strategy: str,
    writer: str,
    decision_reason: str,
    prioritized_findings: tuple[dict[str, Any], ...],
    started_at: str,
    wall_clock_s: float,
    exc: Exception,
) -> dict[str, Any]:
    round_record = {
        "attempt": attempt,
        "strategy": strategy,
        "writer": writer,
        "writer_model_version": writer,
        "reviewer": "",
        "reviewer_model_version": "",
        "score_overall": None,
        "scores_per_dimension": {},
        "dim_floor_fail": [],
        "verdict": "revise",
        "content_hash": None,
        "prompt_hash": _stable_hash(""),
        "contract_snapshot_hash": _stable_hash({}),
        "findings_normalized": [item["normalized_id"] for item in prioritized_findings],
        "mutation_summary": None,
        "decision_reason": decision_reason,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "exception_traceback": traceback.format_exc(),
        "artifacts": {},
        "timestamps": {
            "started": started_at,
            "finished": datetime.now(tz=UTC).isoformat(),
        },
        "cost": {
            "input_tokens": None,
            "output_tokens": None,
            "wall_clock_s": round(wall_clock_s, 3),
        },
    }
    append_history(memory, round_record)
    return round_record


def _constraint_from_finding(
    *,
    slug: str,
    finding: dict[str, Any],
    round_num: int,
    strategy: str,
    sequence: int,
    source_ids: tuple[str, ...],
) -> dict[str, Any] | None:
    if finding["error_class"] in PLAN_LEVEL_ERROR_CLASSES:
        return None
    if finding["error_class"] not in WRITER_ADDRESSABLE_ERROR_CLASSES:
        return None
    return {
        "id": f"c_{slug}_{sequence:03d}",
        "normalized_id": finding["normalized_id"],
        "dimension": finding["dimension"],
        "error_class": finding["error_class"],
        "scope": finding["scope"],
        "directive": finding.get("fix") or finding.get("issue") or finding["error_class"],
        "severity": finding["effective_severity"],
        "recur_count": 2,
        "status": "active",
        "learned_at": {
            "round": round_num,
            "strategy": strategy,
            "date": datetime.now(tz=UTC).date().isoformat(),
        },
        "source_finding_ids": list(source_ids),
        "conflicts_with_plan": False,
        "override_track_level": False,
    }


def _learn_constraints(
    memory: dict[str, Any],
    *,
    slug: str,
    previous_findings: tuple[dict[str, Any], ...] | None,
    current_findings: tuple[dict[str, Any], ...],
    round_num: int,
    strategy: str,
) -> None:
    if not previous_findings:
        return
    previous_by_id = {item["normalized_id"]: item for item in previous_findings}
    next_sequence = len(memory.get("constraints") or []) + 1
    for finding in current_findings:
        previous = previous_by_id.get(finding["normalized_id"])
        if previous is None:
            continue
        constraint = _constraint_from_finding(
            slug=slug,
            finding=finding,
            round_num=round_num,
            strategy=strategy,
            sequence=next_sequence,
            source_ids=(previous["normalized_id"], finding["normalized_id"]),
        )
        if constraint is None:
            continue
        upsert_constraint(memory, constraint)
        next_sequence += 1


def _write_terminal_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        "utf-8",
    )


def _append_stuck_module(path: Path, payload: dict[str, Any]) -> None:
    existing: list[dict[str, Any]] = []
    if path.exists():
        loaded = yaml.safe_load(path.read_text("utf-8"))
        if isinstance(loaded, list):
            existing = loaded
    key = (payload.get("level"), payload.get("slug"))
    existing = [
        item
        for item in existing
        if (item.get("level"), item.get("slug")) != key
    ]
    existing.append(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(existing, sort_keys=False, allow_unicode=True),
        "utf-8",
    )


def _persistent_finding_payload(
    findings: tuple[dict[str, Any], ...],
    *,
    summary: str | None = None,
) -> dict[str, Any]:
    if findings:
        finding = findings[0]
        return {
            "dimension": finding["dimension"],
            "persistent_finding_id": finding["normalized_id"],
            "proposed_plan_edit_summary": summary or finding.get("fix") or finding.get("issue"),
        }
    return {
        "dimension": "review_output",
        "persistent_finding_id": "unclassified:review_output:module",
        "proposed_plan_edit_summary": summary or "review failed without structured findings",
    }


def run_convergence_loop(context: ConvergenceContext) -> ConvergenceRunResult:
    current_manifest = compose_manifest(
        level=context.level,
        slug=context.slug,
    )
    memory, _invalidated = load_module_memory(
        context.memory_path,
        expected_plan_hash=context.plan_hash,
        expected_plan_version=context.plan_version,
        expected_sources_hash=context.sources_hash,
        current_manifest=current_manifest,
    )
    current_writer = context.writer
    rounds: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    previous_round: dict[str, Any] | None = None
    previous_findings: tuple[dict[str, Any], ...] | None = None
    exception_context: dict[str, Any] | None = None

    attempt_started_at = datetime.now(tz=UTC).isoformat()
    attempt_started_monotonic = time.monotonic()
    observation = context.review_round(current_writer)
    prioritized_findings = prioritize_findings(
        observation,
        growth_log_path=context.growth_log_path,
    )
    round_record = _record_round(
        memory=memory,
        observation=observation,
        prioritized_findings=prioritized_findings,
        attempt=1,
        strategy="write",
        writer=current_writer,
        decision_reason="initial",
        mutation=None,
        started_at=attempt_started_at,
        wall_clock_s=time.monotonic() - attempt_started_monotonic,
    )
    round_record["prioritized_findings"] = list(prioritized_findings)
    round_record["tier"] = 0
    rounds.append(round_record)
    save_module_memory(context.memory_path, memory, current_manifest=current_manifest)
    if observation.passed:
        return ConvergenceRunResult(
            terminal="pass",
            rounds=tuple(rounds),
            trace=tuple(trace),
            writer=current_writer,
        )

    for escalation in range(1, context.max_escalations + 1):
        attempt_started_at = datetime.now(tz=UTC).isoformat()
        attempt_started_monotonic = time.monotonic()
        decision = select_strategy(
            observation=observation,
            prioritized_findings=prioritized_findings,
            previous_round=previous_round,
        )
        trace.append(
            {
                "attempt": escalation,
                "tier": decision.tier,
                "strategy": decision.strategy,
                "reason": decision.reason,
                "stall_signals": list(decision.stall_signals),
                "finding_ids": [item["normalized_id"] for item in decision.prioritized_findings[:3]],
            }
        )

        mutation: MutationSummary | None = None
        artifact_path: Path | None = None
        if decision.strategy == "plan_revision_request":
            artifact_path = context.terminal_dir / "plan_revision_request.yaml"
            finding_payload = _persistent_finding_payload(decision.prioritized_findings)
            payload = {
                "level": context.level,
                "slug": context.slug,
                "attempts": escalation,
                "trace": trace,
                **finding_payload,
            }
            _write_terminal_artifact(artifact_path, payload)
            _append_stuck_module(
                context.stuck_modules_path,
                {
                    "level": context.level,
                    "slug": context.slug,
                    "terminal": "plan_revision_request",
                    "artifact": str(artifact_path),
                },
            )
            return ConvergenceRunResult(
                terminal="plan_revision_request",
                rounds=tuple(rounds),
                trace=tuple(trace),
                writer=current_writer,
                artifact_path=artifact_path,
            )

        try:
            if decision.strategy == "patch":
                mutation = context.patch_round(observation)
                if mutation.changed and not context.refresh_sidecars(decision.strategy):
                    raise RuntimeError("sidecar refresh failed after patch")
        except RecoverableValidationError as exc:
            synthetic_observation = ReviewObservation(
                passed=False,
                score=0.0,
                review_text=f"[validator] {exc}",
                findings=exc.findings,
                dim_floor_dimensions=(),
                content_hash=f"{observation.content_hash}|sidecar_invalid_{escalation}",
                parsed_scores=(),
                reviewer="sidecar_validator",
                writer_model_version=current_writer,
                reviewer_model_version="sidecar_validator",
                artifacts={},
            )
            previous_findings = prioritized_findings
            prioritized_findings = prioritize_findings(
                synthetic_observation,
                growth_log_path=context.growth_log_path,
            )
            _learn_constraints(
                memory,
                slug=context.slug,
                previous_findings=previous_findings,
                current_findings=prioritized_findings,
                round_num=len(rounds) + 1,
                strategy=decision.strategy,
            )
            round_record = _record_round(
                memory=memory,
                observation=synthetic_observation,
                prioritized_findings=prioritized_findings,
                attempt=len(rounds) + 1,
                strategy=decision.strategy,
                writer=current_writer,
                decision_reason=f"sidecar validation failed: {exc}",
                mutation=mutation,
                started_at=attempt_started_at,
                wall_clock_s=time.monotonic() - attempt_started_monotonic,
            )
            round_record["prioritized_findings"] = list(prioritized_findings)
            round_record["tier"] = decision.tier
            rounds.append(round_record)
            save_module_memory(context.memory_path, memory, current_manifest=current_manifest)
            previous_round = {
                "tier": decision.tier,
                "strategy": decision.strategy,
                "mutation_count": 0 if mutation is None else mutation.mutation_count,
                "content_hash": synthetic_observation.content_hash,
                "prioritized_findings": prioritized_findings,
                "dim_floor_dimensions": synthetic_observation.dim_floor_dimensions,
            }
            observation = synthetic_observation
            continue
        except Exception as exc:
            exception_context = {
                "attempt": escalation,
                "strategy": decision.strategy,
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
            round_record = _record_exception_round(
                memory=memory,
                attempt=len(rounds) + 1,
                strategy=decision.strategy,
                writer=current_writer,
                decision_reason="exception",
                prioritized_findings=decision.prioritized_findings,
                started_at=attempt_started_at,
                wall_clock_s=time.monotonic() - attempt_started_monotonic,
                exc=exc,
            )
            round_record["prioritized_findings"] = list(decision.prioritized_findings)
            round_record["tier"] = decision.tier
            rounds.append(round_record)
            save_module_memory(context.memory_path, memory, current_manifest=current_manifest)
            break

        previous_round = {
            "tier": decision.tier,
            "strategy": decision.strategy,
            "mutation_count": 0 if mutation is None else mutation.mutation_count,
            "content_hash": observation.content_hash,
            "prioritized_findings": prioritized_findings,
            "dim_floor_dimensions": observation.dim_floor_dimensions,
        }
        previous_findings = prioritized_findings

        observation = context.review_round(current_writer)
        prioritized_findings = prioritize_findings(
            observation,
            growth_log_path=context.growth_log_path,
        )
        _learn_constraints(
            memory,
            slug=context.slug,
            previous_findings=previous_findings,
            current_findings=prioritized_findings,
            round_num=len(rounds) + 1,
            strategy=decision.strategy,
        )
        round_record = _record_round(
            memory=memory,
            observation=observation,
            prioritized_findings=prioritized_findings,
            attempt=len(rounds) + 1,
            strategy=decision.strategy,
            writer=current_writer,
            decision_reason=decision.reason,
            mutation=mutation,
            started_at=attempt_started_at,
            wall_clock_s=time.monotonic() - attempt_started_monotonic,
        )
        round_record["prioritized_findings"] = list(prioritized_findings)
        round_record["tier"] = decision.tier
        rounds.append(round_record)
        save_module_memory(context.memory_path, memory, current_manifest=current_manifest)

        if observation.passed:
            return ConvergenceRunResult(
                terminal="pass",
                rounds=tuple(rounds),
                trace=tuple(trace),
                writer=current_writer,
            )

    artifact_path = context.terminal_dir / "budget_exhausted.yaml"
    payload = {
        "level": context.level,
        "slug": context.slug,
        "writer": current_writer,
        "attempts": len(rounds),
        "history": rounds,
        "trace": trace,
    }
    if exception_context is not None:
        payload["exception"] = exception_context
    _write_terminal_artifact(artifact_path, payload)
    _append_stuck_module(
        context.stuck_modules_path,
        {
            "level": context.level,
            "slug": context.slug,
            "terminal": "budget_exhausted",
            "artifact": str(artifact_path),
        },
    )
    return ConvergenceRunResult(
        terminal="budget_exhausted",
        rounds=tuple(rounds),
        trace=tuple(trace),
        writer=current_writer,
        artifact_path=artifact_path,
    )
