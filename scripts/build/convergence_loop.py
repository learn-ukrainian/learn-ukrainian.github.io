"""Convergent review loop with tiered escalation and honest terminals."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
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

TerminalType = Literal["pass", "plan_revision_request", "budget_exhausted"]
TierName = Literal["patch", "section_rewrite", "full_rewrite", "writer_swap", "plan_revision_request"]


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
RewriteCallback = Callable[[tuple[dict[str, Any], ...], str], MutationSummary]
WriterSwapCallback = Callable[[tuple[dict[str, Any], ...], str], tuple[str | None, MutationSummary]]
RefreshCallback = Callable[[str], bool]
StyleReviewCallback = Callable[[str], None]


@dataclass
class ConvergenceContext:
    level: str
    slug: str
    writer: str
    review_round: ReviewCallback
    patch_round: PatchCallback
    section_rewrite_round: RewriteCallback
    full_rewrite_round: RewriteCallback
    writer_swap_round: WriterSwapCallback
    refresh_sidecars: RefreshCallback
    memory_path: Path
    terminal_dir: Path
    stuck_modules_path: Path
    plan_hash: str
    plan_version: int
    sources_hash: str
    reviewer_matrix_enforced: bool = False
    growth_log_path: Path | None = None
    style_review_after_swap: StyleReviewCallback | None = None
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
    for item in normalized:
        topology = classify_topology(item)
        severity = "critical" if item["dimension"] in floor_dimensions else item["severity"]
        results.append({**item, "topology": topology, "effective_severity": severity})
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
    attempted_tiers: set[int],
    full_rewrite_targets: set[str],
) -> ConvergenceDecision:
    if not prioritized_findings:
        return ConvergenceDecision(
            tier=5,
            strategy="plan_revision_request",
            reason="review failed without structured findings",
            prioritized_findings=prioritized_findings,
        )

    topologies = {item["topology"] for item in prioritized_findings}
    top_ids = set(_top_ids(prioritized_findings))
    candidate_tier = 5
    candidate_strategy: TierName = "plan_revision_request"
    candidate_reason = "defaulted to human plan revision"

    if observation.patch_available and topologies == {"local_to_prose"}:
        candidate_tier = 1
        candidate_strategy = "patch"
        candidate_reason = "all findings are local prose edits and reviewer emitted deterministic fixes"
    elif topologies <= {"local_to_prose", "section_local"}:
        candidate_tier = 2
        candidate_strategy = "section_rewrite"
        candidate_reason = "findings are confined to local prose or a single section"
    elif "plan_level" in topologies and 3 in attempted_tiers:
        candidate_tier = 5
        candidate_strategy = "plan_revision_request"
        candidate_reason = "plan-level finding persisted after a full rewrite"
    elif top_ids - full_rewrite_targets:
        candidate_tier = 3
        candidate_strategy = "full_rewrite"
        candidate_reason = "cross-section findings require a full module regeneration"
    elif 4 not in attempted_tiers:
        candidate_tier = 4
        candidate_strategy = "writer_swap"
        candidate_reason = "full rewrite already targeted the top findings without convergence"

    signals = _stall_signals(previous_round, {
        "strategy": previous_round.get("strategy") if previous_round else "write",
        "mutation_count": previous_round.get("mutation_count") if previous_round else 0,
        "content_hash": observation.content_hash,
        "prioritized_findings": prioritized_findings,
        "dim_floor_dimensions": observation.dim_floor_dimensions,
    })
    if previous_round and signals and candidate_tier < 5:
        candidate_tier = max(candidate_tier, int(previous_round.get("tier") or 0) + 1)
        candidate_strategy = {
            1: "patch",
            2: "section_rewrite",
            3: "full_rewrite",
            4: "writer_swap",
            5: "plan_revision_request",
        }[candidate_tier]
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
        "prompt_hash": _stable_hash(observation.review_text),
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
    memory, _invalidated = load_module_memory(
        context.memory_path,
        expected_plan_hash=context.plan_hash,
        expected_plan_version=context.plan_version,
        expected_sources_hash=context.sources_hash,
    )
    current_writer = context.writer
    attempted_tiers: set[int] = set()
    full_rewrite_targets: set[str] = set()
    rounds: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    previous_round: dict[str, Any] | None = None
    previous_findings: tuple[dict[str, Any], ...] | None = None

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
    save_module_memory(context.memory_path, memory)
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
            attempted_tiers=attempted_tiers,
            full_rewrite_targets=full_rewrite_targets,
        )
        attempted_tiers.add(decision.tier)
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

        if decision.strategy == "patch":
            mutation = context.patch_round(observation)
        elif decision.strategy == "section_rewrite":
            mutation = context.section_rewrite_round(decision.prioritized_findings, current_writer)
            if mutation.changed and not context.refresh_sidecars(decision.strategy):
                raise RuntimeError("sidecar refresh failed after section rewrite")
        elif decision.strategy == "full_rewrite":
            full_rewrite_targets.update(_top_ids(decision.prioritized_findings))
            mutation = context.full_rewrite_round(decision.prioritized_findings, current_writer)
            if mutation.changed and not context.refresh_sidecars(decision.strategy):
                raise RuntimeError("sidecar refresh failed after full rewrite")
        elif decision.strategy == "writer_swap":
            new_writer, mutation = context.writer_swap_round(decision.prioritized_findings, current_writer)
            if not new_writer:
                artifact_path = context.terminal_dir / "plan_revision_request.yaml"
                finding_payload = _persistent_finding_payload(
                    decision.prioritized_findings,
                    summary="writer swap unavailable under reviewer matrix",
                )
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
            current_writer = new_writer
            if mutation.changed and not context.refresh_sidecars(decision.strategy):
                raise RuntimeError("sidecar refresh failed after writer swap")
            if context.style_review_after_swap is not None:
                context.style_review_after_swap(current_writer)

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
        save_module_memory(context.memory_path, memory)

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
