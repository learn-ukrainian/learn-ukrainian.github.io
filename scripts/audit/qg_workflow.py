#!/usr/bin/env python3
"""Cost-aware tiered curriculum quality-gate workflow.

This composes the deterministic/lookup adapters and the gated LLM reviewer into
one canonical ``qg_schema`` evidence record per module. Live reviewer dispatch
is intentionally absent until #4370 calibrates the prompt and canary runbook;
callers must inject a reviewer response or reuse a composite cache hit. The
live Tier-2 retry composition is capped at three reviewer calls per module:
initial response, at most one theatre retry, and at most one deep-read retry.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import (
    llm_qg_canaries,
    llm_qg_store,
    llm_reviewer,
    llm_reviewer_dispatch,
    qg_schema,
)
from scripts.audit.content_surface_gates import policy_for_level
from scripts.audit.curriculum_qg_harness import CHECKER_VERSION, checker_config_hash
from scripts.audit.qg_adapters import (
    DeterministicRuleAdapter,
    ScorerInput,
    UaGecGoldFixtureAdapter,
    dimensions_from_findings,
)

# v3 (#4416): grounding/admissibility gates changed; cache hits only re-check
# theatre, so pre-fix rows must miss the composite cache and re-run with tools.
DEFAULT_GATE_VERSION = "qg_workflow.v3"
DEFAULT_REVIEWER_MODEL_ID = "llm-reviewer-disabled-until-4370"
DEFAULT_REVIEWER_FAMILY = "qg_workflow"
LLM_POLICY_FAMILIES = frozenset({"b1_plus", "seminar"})
CONTENT_HASH_BASIS = "llm_qg_store.CONTENT_FILES"

Reviewer = Callable[["ReviewTarget", str], Any]


@dataclass(frozen=True, slots=True)
class ReviewTarget:
    """One module review target."""

    level: str
    slug: str
    module_dir: Path
    fixture_id: str | None = None
    plan_path: Path | None = None


@dataclass(frozen=True, slots=True)
class WorkflowOptions:
    """Runtime policy for the cost-aware review workflow."""

    gate_version: str = DEFAULT_GATE_VERSION
    reviewer_model_id: str = DEFAULT_REVIEWER_MODEL_ID
    reviewer_family: str = DEFAULT_REVIEWER_FAMILY
    live_reviewer: bool = False
    author_family: str | None = None
    canary_artifacts: Mapping[str, Path] | None = None
    daily_spend_path: Path | None = None
    circuit_state_path: Path | None = None
    run_command: str | None = None
    enable_llm: bool = False
    force_llm: bool = False
    llm_on_fail: bool = False
    calibration_sample: bool = False
    dry_run: bool = False
    canary_passed: bool = False
    max_llm_calls: int | None = None
    max_cost_usd: float | None = None
    max_daily_cost_usd: float | None = None
    max_module_cost_usd: float | None = None
    fail_closed_on_llm_skip: bool = True
    use_llm_cache: bool = True
    persist_llm_qg: bool = True
    record_live_outcomes: bool = True
    record_daily_spend: bool = True
    capture_tier2: bool = False


@dataclass(slots=True)
class BudgetState:
    """Mutable per-run budget accounting."""

    llm_calls: int = 0
    cost_usd: float = 0.0
    daily_cost_usd: float = 0.0

    def spend_allowed(self, estimate: Mapping[str, Any], options: WorkflowOptions) -> tuple[bool, str | None]:
        cost = float(estimate.get("estimated_cost_usd") or 0.0)
        if options.max_module_cost_usd is not None and cost > options.max_module_cost_usd:
            return False, "max_module_cost_usd"
        if options.max_llm_calls is not None and self.llm_calls >= options.max_llm_calls:
            return False, "max_llm_calls"
        if options.max_cost_usd is not None and self.cost_usd + cost > options.max_cost_usd:
            return False, "max_cost_usd"
        if options.max_daily_cost_usd is not None and self.daily_cost_usd + cost > options.max_daily_cost_usd:
            return False, "max_daily_cost_usd"
        return True, None

    def record_spend(self, estimate: Mapping[str, Any], *, observed_cost_usd: float | None = None) -> None:
        self.llm_calls += 1
        cost = float(observed_cost_usd if observed_cost_usd is not None else estimate.get("estimated_cost_usd") or 0.0)
        self.cost_usd += cost
        self.daily_cost_usd += cost


@dataclass(frozen=True, slots=True)
class _ReviewerGateOutcome:
    """Deterministic post-response reviewer gate outcome."""

    payload: dict[str, Any]
    findings: list[dict[str, Any]]
    status: str = "ran"
    workflow_override: str | None = None
    grounding_gate: llm_reviewer_dispatch.GroundingGateResult | None = None
    retry_reason: str | None = None
    gate_reason: str | None = None


def review_module(
    target: ReviewTarget,
    *,
    options: WorkflowOptions | None = None,
    reviewer: Reviewer | None = None,
    store_path: Path | None = None,
    budget: BudgetState | None = None,
) -> dict[str, Any]:
    """Run all eligible tiers for one module and return canonical evidence."""

    effective_options = options or WorkflowOptions()
    effective_budget = budget or BudgetState()
    module_dir = target.module_dir
    level = target.level.strip().lower()
    slug = target.slug.strip() or module_dir.name
    policy = policy_for_level(level)
    texts = _read_module_texts(module_dir)
    prompt = llm_reviewer.build_reviewer_prompt(
        level=level,
        slug=slug,
        module_md=texts.get("module.md", ""),
        activities_yaml=texts.get("activities.yaml", ""),
        vocabulary_yaml=texts.get("vocabulary.yaml", ""),
        resources_yaml=texts.get("resources.yaml", ""),
    )
    prompt_hash = llm_qg_store.prompt_hash_for_text(prompt)
    content_sha = llm_qg_store.content_sha_for_module(module_dir)
    all_findings: list[dict[str, Any]] = []
    tier_results: list[dict[str, Any]] = []

    tier0_findings = _tier0_findings(target, level, slug, texts)
    all_findings.extend(tier0_findings)
    tier0_verdict = _verdict_for_findings(tier0_findings)
    tier0_hard_fail = any(finding.get("severity") == "critical" for finding in tier0_findings)
    tier_results.append(
        {
            "tier": 0,
            "name": "deterministic_structural",
            "status": "ran",
            "findings": len(tier0_findings),
            "verdict": tier0_verdict,
        }
    )

    tier1_findings, tier1_meta = _tier1_findings(target)
    all_findings.extend(tier1_findings)
    tier_results.append(
        {
            "tier": 1,
            "name": "ua_gec_gold_fixture",
            "status": "ran",
            "gold_rows_matched": tier1_meta["gold_rows_matched"],
            "gold_rows_suppressed_contested": tier1_meta["gold_rows_suppressed_contested"],
            "findings": len(tier1_findings),
        }
    )

    tier2 = _run_tier2(
        target=target,
        level=level,
        slug=slug,
        policy_family=policy.family,
        texts=texts,
        prompt=prompt,
        prompt_hash=prompt_hash,
        tier0_hard_fail=tier0_hard_fail,
        contested_gold_suppressed=bool(tier1_meta["gold_rows_suppressed_contested"]),
        options=effective_options,
        reviewer=reviewer,
        store_path=store_path,
        budget=effective_budget,
    )
    tier_results.append(tier2["result"])
    all_findings.extend(tier2["findings"])

    merged_findings = _dedupe_by_finding_id(all_findings)
    workflow_verdict = tier2.get("workflow_verdict")
    completion_status = tier2.get("completion_status", "COMPLETE")
    return _build_evidence_record(
        level=level,
        slug=slug,
        target=target,
        policy_family=policy.family,
        policy_english=policy.english_policy,
        content_sha=content_sha,
        prompt_hash=prompt_hash,
        findings=merged_findings,
        tier_results=tier_results,
        workflow_verdict=workflow_verdict,
        completion_status=completion_status,
        llm_used=bool(tier2.get("llm_used")),
        llm_required_by_policy=bool(tier2.get("llm_required_by_policy")),
        llm_required_by_harness=tier0_verdict != "PASS",
        llm_cost_override=bool(tier2.get("llm_cost_override")),
        reviewer_model_id=str(tier2.get("reviewer_model_id") or effective_options.reviewer_model_id),
        reviewer_family=str(tier2.get("reviewer_family") or effective_options.reviewer_family),
        options=effective_options,
    )


def dry_run_modules(
    targets: Sequence[ReviewTarget],
    *,
    options: WorkflowOptions | None = None,
    store_path: Path | None = None,
) -> dict[str, Any]:
    """Return per-tier counts and cost estimates without writing cache records."""

    dry_options = options or WorkflowOptions()
    dry_options = WorkflowOptions(
        gate_version=dry_options.gate_version,
        reviewer_model_id=dry_options.reviewer_model_id,
        reviewer_family=dry_options.reviewer_family,
        live_reviewer=dry_options.live_reviewer,
        author_family=dry_options.author_family,
        canary_artifacts=dry_options.canary_artifacts,
        daily_spend_path=dry_options.daily_spend_path,
        circuit_state_path=dry_options.circuit_state_path,
        run_command=dry_options.run_command,
        enable_llm=True,
        force_llm=dry_options.force_llm,
        llm_on_fail=dry_options.llm_on_fail,
        calibration_sample=dry_options.calibration_sample,
        dry_run=True,
        canary_passed=dry_options.canary_passed,
        max_llm_calls=dry_options.max_llm_calls,
        max_cost_usd=dry_options.max_cost_usd,
        max_daily_cost_usd=dry_options.max_daily_cost_usd,
        max_module_cost_usd=dry_options.max_module_cost_usd,
        fail_closed_on_llm_skip=dry_options.fail_closed_on_llm_skip,
        use_llm_cache=dry_options.use_llm_cache,
        persist_llm_qg=dry_options.persist_llm_qg,
        record_live_outcomes=dry_options.record_live_outcomes,
        record_daily_spend=dry_options.record_daily_spend,
        capture_tier2=dry_options.capture_tier2,
    )
    budget = BudgetState()
    records = [
        review_module(target, options=dry_options, store_path=store_path, budget=budget)
        for target in targets
    ]
    by_family: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "modules": 0,
            "tier2_eligible": 0,
            "tier2_estimated_calls": 0,
            "estimated_prompt_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    )
    counts = {
        "modules": len(records),
        "tier0_modules": len(records),
        "tier0_hard_fail": 0,
        "tier1_gold_rows_matched": 0,
        "tier1_gold_rows_suppressed_contested": 0,
        "tier2_cache_hits": 0,
        "tier2_estimated_calls": 0,
        "tier2_skipped_budget": 0,
    }
    for record in records:
        family = str(record["level_policy"]["family"])
        bucket = by_family[family]
        bucket["modules"] += 1
        for tier in record["qg_workflow"]["tiers"]:
            if tier["tier"] == 0 and tier.get("verdict") == "FAIL":
                counts["tier0_hard_fail"] += 1
            if tier["tier"] == 1:
                counts["tier1_gold_rows_matched"] += int(tier.get("gold_rows_matched") or 0)
                counts["tier1_gold_rows_suppressed_contested"] += int(
                    tier.get("gold_rows_suppressed_contested") or 0
                )
            if tier["tier"] == 2:
                if tier.get("llm_required_by_policy"):
                    bucket["tier2_eligible"] += 1
                if tier.get("status") == "cache_hit":
                    counts["tier2_cache_hits"] += 1
                if tier.get("status") == "dry_run_estimate":
                    counts["tier2_estimated_calls"] += 1
                    bucket["tier2_estimated_calls"] += 1
                    estimate = tier.get("estimate") if isinstance(tier.get("estimate"), Mapping) else {}
                    bucket["estimated_prompt_tokens"] += int(estimate.get("estimated_prompt_tokens") or 0)
                    bucket["estimated_cost_usd"] += float(estimate.get("estimated_cost_usd") or 0.0)
                if tier.get("status") == "skipped_budget":
                    counts["tier2_skipped_budget"] += 1
    gateable = _dry_run_gateable_artifact(
        records=records,
        counts=counts,
        level_profiles=dict(sorted(by_family.items())),
        options=dry_options,
    )
    return {
        "schema_version": "qg_workflow_dry_run.v1",
        "dry_run": True,
        "writes": 0,
        "counts": counts,
        "level_profiles": dict(sorted(by_family.items())),
        "module_list": gateable["module_list"],
        "per_tier_counts": gateable["per_tier_counts"],
        "cache_estimate": gateable["cache_estimate"],
        "expected_spend": gateable["expected_spend"],
        "stale_cache_count": gateable["cache_estimate"]["stale"],
        "exact_run_command": gateable["exact_run_command"],
        "gateable_artifact": gateable,
        "modules": records,
    }


def review_modules(
    targets: Sequence[ReviewTarget],
    *,
    options: WorkflowOptions | None = None,
    reviewer: Reviewer | None = None,
    store_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Run the workflow over a bounded target list with shared budget state."""

    effective_options = options or WorkflowOptions()
    if effective_options.live_reviewer:
        if (
            not effective_options.dry_run
            and _llm_enabled_for_any_target(targets, effective_options)
            and llm_qg_store.live_tier2_circuit_status(effective_options.circuit_state_path)["open"]
        ):
            message = llm_qg_store.live_tier2_circuit_open_message(effective_options.circuit_state_path)
            return [
                _build_aborted_record(
                    target,
                    options=effective_options,
                    reason="circuit_open",
                    status="circuit_open",
                    message=message,
                )
                for target in targets
            ]
        _validate_live_reviewer_preflight(targets, effective_options, reviewer=reviewer)
    elif (
        len(targets) > 1
        and _llm_enabled_for_any_target(targets, effective_options)
        and not effective_options.canary_passed
    ):
        raise ValueError("broad LLM batches require an explicit passing canary pre-gate")
    budget = BudgetState(daily_cost_usd=_initial_daily_spend(effective_options))
    records: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        record = review_module(
            target,
            options=effective_options,
            reviewer=reviewer,
            store_path=store_path,
            budget=budget,
        )
        records.append(record)
        abort_reason = _batch_abort_reason(records)
        if abort_reason and index + 1 < len(targets):
            for remaining in targets[index + 1:]:
                records.append(
                    _build_aborted_record(
                        remaining,
                        options=effective_options,
                        reason=abort_reason,
                    )
                )
            break
    return records


def canary_result_passes(path: Path, *, level: str) -> bool:
    """Evaluate a reviewer canary result JSON using the existing canary gate."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    report = llm_qg_canaries.evaluate_canaries(payload, level)
    return bool(report.get("passed"))


def _dry_run_gateable_artifact(
    *,
    records: Sequence[Mapping[str, Any]],
    counts: Mapping[str, Any],
    level_profiles: Mapping[str, Mapping[str, Any]],
    options: WorkflowOptions,
) -> dict[str, Any]:
    module_list: list[dict[str, Any]] = []
    expected_by_reviewer: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"modules": 0, "estimated_cost_usd": 0.0, "estimated_total_tokens": 0}
    )
    warm = cold = stale = 0
    total_cost = 0.0
    total_tokens = 0
    for record in records:
        tier2 = _tier_from_record(record, 2)
        estimate = tier2.get("estimate") if isinstance(tier2.get("estimate"), Mapping) else {}
        cache_status = "warm" if tier2.get("status") == "cache_hit" else estimate.get("cache_status") or "none"
        if cache_status == "warm":
            warm += 1
        elif cache_status == "stale":
            stale += 1
        elif tier2.get("status") == "dry_run_estimate":
            cold += 1
        reviewer_model = str(tier2.get("reviewer_model_id") or record["qg_workflow"]["reviewer_model_id"])
        cost = float(estimate.get("estimated_cost_usd") or 0.0)
        tokens = int(estimate.get("estimated_total_tokens") or 0)
        total_cost += cost
        total_tokens += tokens
        if cost or tokens:
            bucket = expected_by_reviewer[reviewer_model]
            bucket["modules"] += 1
            bucket["estimated_cost_usd"] += cost
            bucket["estimated_total_tokens"] += tokens
        module_list.append(
            {
                "module_id": record["module_id"],
                "level": str(record["module_id"]).split("/", 1)[0],
                "slug": str(record["module_id"]).split("/", 1)[1],
                "module_dir": record["provenance"]["module_dir"],
                "policy_family": record["level_policy"]["family"],
                "tier2_status": tier2.get("status"),
                "reviewer_model_id": reviewer_model,
                "reviewer_family": tier2.get("reviewer_family"),
                "reviewer_route": tier2.get("reviewer_route"),
                "cache_status": cache_status,
                "estimated_cost_usd": cost,
            }
        )
    return {
        "schema_version": "qg_workflow_dry_run_gate.v1",
        "module_list": module_list,
        "per_tier_counts": dict(counts),
        "level_profiles": dict(level_profiles),
        "cache_estimate": {
            "warm": warm,
            "cold": cold,
            "stale": stale,
        },
        "expected_spend": {
            "estimated_cost_usd": round(total_cost, 6),
            "estimated_total_tokens": total_tokens,
            "by_reviewer_model": {
                model: {
                    "modules": values["modules"],
                    "estimated_cost_usd": round(float(values["estimated_cost_usd"]), 6),
                    "estimated_total_tokens": values["estimated_total_tokens"],
                }
                for model, values in sorted(expected_by_reviewer.items())
            },
        },
        "exact_run_command": options.run_command or "",
    }


def _validate_live_reviewer_preflight(
    targets: Sequence[ReviewTarget],
    options: WorkflowOptions,
    *,
    reviewer: Reviewer | None,
) -> None:
    if options.dry_run:
        return
    if _llm_enabled_for_any_target(targets, options) and options.max_cost_usd is None:
        raise ValueError("live Tier-2 runs require --max-cost-usd")
    if reviewer is not None:
        return
    if len(targets) <= 1 or not _llm_enabled_for_any_target(targets, options):
        return
    routes = _live_preflight_routes(targets, options)
    try:
        llm_reviewer_dispatch.live_batch_preflight(routes)
    except llm_reviewer_dispatch.ReviewerPreflightError as exc:
        raise ValueError(f"live Tier-2 quota preflight failed: {exc.reason}: {exc}") from exc


def _live_preflight_routes(
    targets: Sequence[ReviewTarget],
    options: WorkflowOptions,
) -> list[llm_reviewer_dispatch.ReviewerRoute]:
    routes: list[llm_reviewer_dispatch.ReviewerRoute] = []
    for target in targets:
        policy = policy_for_level(target.level)
        if not (
            policy.family in LLM_POLICY_FAMILIES
            or options.force_llm
            or options.calibration_sample
        ):
            continue
        route = _tier2_route(
            options=options,
            policy_family=policy.family,
            contested_gold_suppressed=False,
        )
        if route is not None:
            routes.append(route)
    return routes


def _initial_daily_spend(options: WorkflowOptions) -> float:
    if not options.live_reviewer or options.max_daily_cost_usd is None:
        return 0.0
    return llm_reviewer_dispatch.read_daily_spend(options.daily_spend_path)


def _batch_abort_reason(records: Sequence[Mapping[str, Any]]) -> str | None:
    attempted = 0
    provider_errors = 0
    parse_failures = 0
    for record in records:
        tier2 = _tier_from_record(record, 2)
        status = str(tier2.get("status"))
        if status in {"ran", "provider_error", "parse_failure", "schema_failure", "cost_overrun"}:
            attempted += 1
        if status == "provider_error":
            provider_errors += 1
        if status in {"parse_failure", "schema_failure"}:
            parse_failures += 1
        if status == "cost_overrun":
            return "cost_overrun"
        if status == "self_review_blocked":
            return "self_review_blocked"
        if status == "lineage_required":
            return "lineage_required"
        if status == "skipped_canary_required":
            return "canary_required"
        if status == "circuit_open":
            return "circuit_open"
    if attempted and parse_failures / attempted > 0.05:
        return "parse_failure_rate"
    if attempted and provider_errors / attempted > 0.10:
        return "provider_error_rate"
    return None


def _build_aborted_record(
    target: ReviewTarget,
    *,
    options: WorkflowOptions,
    reason: str,
    status: str = "aborted_batch",
    message: str | None = None,
) -> dict[str, Any]:
    level = target.level.strip().lower()
    slug = target.slug.strip() or target.module_dir.name
    policy = policy_for_level(level)
    texts = _read_module_texts(target.module_dir)
    prompt = llm_reviewer.build_reviewer_prompt(
        level=level,
        slug=slug,
        module_md=texts.get("module.md", ""),
        activities_yaml=texts.get("activities.yaml", ""),
        vocabulary_yaml=texts.get("vocabulary.yaml", ""),
        resources_yaml=texts.get("resources.yaml", ""),
    )
    prompt_hash = llm_qg_store.prompt_hash_for_text(prompt)
    content_sha = llm_qg_store.content_sha_for_module(target.module_dir)
    route = _tier2_route(
        options=options,
        policy_family=policy.family,
        contested_gold_suppressed=False,
    )
    reviewer_model_id = route.reviewer_model_id if route else options.reviewer_model_id
    reviewer_family = route.reviewer_family if route else options.reviewer_family
    tiers = [
        {"tier": 0, "name": "deterministic_structural", "status": "not_run_batch_aborted"},
        {"tier": 1, "name": "ua_gec_gold_fixture", "status": "not_run_batch_aborted"},
        {
            "tier": 2,
            "name": "llm_reviewer",
            "status": status,
            "reason": reason,
            "llm_required_by_policy": policy.family in LLM_POLICY_FAMILIES,
            "policy_family": policy.family,
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
            "findings": 0,
        },
    ]
    if message:
        tiers[2]["message"] = message
    return _build_evidence_record(
        level=level,
        slug=slug,
        target=target,
        policy_family=policy.family,
        policy_english=policy.english_policy,
        content_sha=content_sha,
        prompt_hash=prompt_hash,
        findings=[],
        tier_results=tiers,
        workflow_verdict="INCOMPLETE",
        completion_status="INCOMPLETE",
        llm_used=False,
        llm_required_by_policy=policy.family in LLM_POLICY_FAMILIES,
        llm_required_by_harness=False,
        llm_cost_override=False,
        reviewer_model_id=reviewer_model_id,
        reviewer_family=reviewer_family,
        options=options,
    )


def _tier_from_record(record: Mapping[str, Any], tier_number: int) -> dict[str, Any]:
    workflow = record.get("qg_workflow")
    tiers = workflow.get("tiers") if isinstance(workflow, Mapping) else []
    if isinstance(tiers, list):
        for tier in tiers:
            if isinstance(tier, Mapping) and tier.get("tier") == tier_number:
                return dict(tier)
    return {}


def _tier0_findings(
    target: ReviewTarget,
    level: str,
    slug: str,
    texts: Mapping[str, str],
) -> list[dict[str, Any]]:
    deterministic = DeterministicRuleAdapter().findings(
        ScorerInput(
            module_dir=target.module_dir,
            level=level,
            slug=slug,
            fixture_id=target.fixture_id,
            plan_path=target.plan_path,
        )
    )
    structural = llm_reviewer.run_structural_checks(
        level,
        texts.get("activities.yaml", ""),
        file_name="activities.yaml",
    )
    return _dedupe_by_finding_id([*deterministic, *structural])


def _tier1_findings(target: ReviewTarget) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if not target.fixture_id:
        return [], {"gold_rows_matched": 0, "gold_rows_suppressed_contested": 0}
    raw_findings = UaGecGoldFixtureAdapter().findings(ScorerInput(fixture_id=target.fixture_id))
    kept: list[dict[str, Any]] = []
    suppressed = 0
    for finding in raw_findings:
        if _gold_contested(finding):
            suppressed += 1
            continue
        kept.append(finding)
    return kept, {
        "gold_rows_matched": len(raw_findings),
        "gold_rows_suppressed_contested": suppressed,
    }


def _run_tier2(
    *,
    target: ReviewTarget,
    level: str,
    slug: str,
    policy_family: str,
    texts: Mapping[str, str],
    prompt: str,
    prompt_hash: str | None,
    tier0_hard_fail: bool,
    contested_gold_suppressed: bool,
    options: WorkflowOptions,
    reviewer: Reviewer | None,
    store_path: Path | None,
    budget: BudgetState,
) -> dict[str, Any]:
    policy_eligible = (
        policy_family in LLM_POLICY_FAMILIES
        or options.force_llm
        or options.calibration_sample
        or contested_gold_suppressed
    )
    route = _tier2_route(
        options=options,
        policy_family=policy_family,
        contested_gold_suppressed=contested_gold_suppressed,
    )
    reviewer_model_id = route.reviewer_model_id if route else options.reviewer_model_id
    reviewer_family = route.reviewer_family if route else options.reviewer_family
    route_name = route.route_name if route else None
    base_result: dict[str, Any] = {
        "tier": 2,
        "name": "llm_reviewer",
        "llm_required_by_policy": policy_eligible,
        "policy_family": policy_family,
        "reviewer_model_id": reviewer_model_id,
        "reviewer_family": reviewer_family,
        "findings": 0,
    }
    if route is not None:
        base_result["reviewer_route"] = route.route_name
        base_result["bridge_command"] = list(route.bridge_command)
    if not policy_eligible:
        return {
            "findings": [],
            "result": {**base_result, "status": "skipped_policy"},
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }
    if tier0_hard_fail and not (options.llm_on_fail or options.calibration_sample):
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_tier0_hard_fail",
                "cost_override": True,
                "reason": "Tier-0 hard FAIL short-circuits LLM by default; use --llm-on-fail to opt in.",
            },
            "llm_cost_override": True,
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }
    if not options.enable_llm:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_flag_off",
                "reason": "Live Tier-2 reviewer remains flag-off until #4370 calibration lands.",
            },
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }

    if options.live_reviewer:
        circuit_status = llm_qg_store.live_tier2_circuit_status(options.circuit_state_path)
        if circuit_status["open"]:
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": "circuit_open",
                    "reason": "circuit_open",
                    "message": llm_qg_store.live_tier2_circuit_open_message(options.circuit_state_path),
                },
                "workflow_verdict": "INCOMPLETE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }
        blocked = _live_reviewer_block(
            target=target,
            level=level,
            slug=slug,
            policy_family=policy_family,
            route=route,
            options=options,
        )
        if blocked is not None:
            return {
                "findings": [],
                "result": {**base_result, **blocked},
                "workflow_verdict": "INCOMPLETE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }

    cached = (
        llm_qg_store.current_llm_qg_for_module(
            level,
            slug,
            target.module_dir,
            gate_version=options.gate_version,
            prompt_hash=prompt_hash,
            checker_version=CHECKER_VERSION,
            level_policy_family=policy_family,
            reviewer_model=reviewer_model_id,
            route_name=route_name,
            path=store_path,
        )
        if options.use_llm_cache
        else None
    )
    if cached is not None:
        cached_payload = dict(cached.payload)
        cached_meta = {
            "tool_call_count": cached.tool_call_count,
            "tools_used": list(cached.tools_used),
            "route_name": cached.route_name,
        }
        if cached.tool_events is not None:
            cached_meta["tool_events"] = [dict(event) for event in cached.tool_events]
            try:
                llm_reviewer.validate_reviewer_payload(cached_payload, policy_family)
                cache_gate = _run_reviewer_gate_sequence(
                    cached_payload,
                    cached_meta,
                    policy_family=policy_family,
                    theatre_retry_available=True,
                    deep_read_retry_available=True,
                    retry_unavailable_fails=True,
                )
            except ValueError:
                cache_gate = _ReviewerGateOutcome(
                    payload=cached_payload,
                    findings=[],
                    retry_reason="schema_failure",
                )
            if cache_gate.retry_reason is None:
                findings = cache_gate.findings
                grounding_gate = cache_gate.grounding_gate or llm_reviewer_dispatch.GroundingGateResult(
                    payload=cache_gate.payload
                )
                return {
                    "findings": findings,
                    "result": {
                        **base_result,
                        "status": "cache_hit" if cache_gate.status == "ran" else cache_gate.status,
                        "findings": len(findings),
                        "cache_run_id": cached.run_id,
                        "cache_regate": "replayed",
                        "invalid_fact_checks": grounding_gate.invalid_fact_checks,
                        "inadmissible_positive_verdicts": grounding_gate.inadmissible_positive_verdicts,
                    },
                    "llm_used": True,
                    "workflow_verdict": cache_gate.workflow_override,
                    "reviewer_model_id": reviewer_model_id,
                    "reviewer_family": reviewer_family,
                }
        else:
            try:
                llm_reviewer.validate_reviewer_payload(cached_payload, policy_family)
                cache_theatre = llm_reviewer_dispatch.tool_theatre_violation(
                    policy_family=policy_family,
                    payload=cached_payload,
                    dispatch_meta=cached_meta,
                )
            except ValueError:
                cache_theatre = {"status": llm_reviewer_dispatch.INVALID_TOOL_THEATRE}
            if cache_theatre is None:
                findings = _findings_from_payload(cached_payload)
                return {
                    "findings": findings,
                    "result": {
                        **base_result,
                        "status": "cache_hit",
                        "findings": len(findings),
                        "cache_run_id": cached.run_id,
                        "cache_regate": "unavailable",
                    },
                    "llm_used": True,
                    "reviewer_model_id": reviewer_model_id,
                    "reviewer_family": reviewer_family,
                }

    stale_cache = (
        _has_stale_cache(
            level=level,
            slug=slug,
            gate_version=options.gate_version,
            checker_version=CHECKER_VERSION,
            level_policy_family=policy_family,
            reviewer_model=reviewer_model_id,
            route_name=route_name,
            store_path=store_path,
        )
        if options.use_llm_cache
        else False
    )
    estimate = (
        llm_reviewer_dispatch.estimate_route_cost(prompt, route, policy_family=policy_family)
        if route is not None
        else estimate_llm_cost(prompt, policy_family)
    )
    estimate["cache_status"] = "stale" if stale_cache else "cold"
    if options.live_reviewer and not options.dry_run and options.max_cost_usd is None:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_budget_required",
                "reason": "max_cost_usd_required",
                "estimate": estimate,
            },
            "workflow_verdict": "SKIPPED_BUDGET",
            "completion_status": "INCOMPLETE",
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }
    allowed, reason = budget.spend_allowed(estimate, options)
    if not allowed:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_budget",
                "reason": reason,
                "estimate": estimate,
            },
            "workflow_verdict": "SKIPPED_BUDGET",
            "completion_status": "INCOMPLETE",
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }
    if options.dry_run:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "dry_run_estimate",
                "estimate": estimate,
                "stale_cache": stale_cache,
            },
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }
    effective_reviewer = reviewer
    if effective_reviewer is None and options.live_reviewer and route is not None:
        effective_reviewer = llm_reviewer_dispatch.LiveReviewerDispatcher(
            policy_family=policy_family,
            gate_version=options.gate_version,
            contested_gold_suppressed=contested_gold_suppressed,
            factual_sensitive=policy_family == "seminar",
            author_family=options.author_family,
        )
    if effective_reviewer is None:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_no_reviewer",
                "estimate": estimate,
                "reason": "No live reviewer dispatcher is wired until #4370; provide a reviewer response.",
            },
            "workflow_verdict": "INCOMPLETE",
            "completion_status": "INCOMPLETE",
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
        }

    attempt_prompt = prompt
    theatre_retried = False
    deep_read_retried = False
    payload: dict[str, Any]
    findings: list[dict[str, Any]]
    dispatch_meta: dict[str, Any]
    tier2_status = "ran"
    workflow_override: str | None = None
    capture_attempts: list[dict[str, Any]] = []
    while True:
        try:
            raw_response = effective_reviewer(target, attempt_prompt)
        except llm_reviewer_dispatch.ReviewerDispatchError as exc:
            budget.record_spend(estimate)
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=reviewer_model_id,
                reviewer_family=reviewer_family,
                route_name=route_name,
                status="provider_error",
                reason=type(exc).__name__,
            )
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": "provider_error",
                    "reason": type(exc).__name__,
                    "message": str(exc),
                    "estimate": estimate,
                },
                "workflow_verdict": "PROVIDER_FAILURE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }
        response_text, dispatch_meta = _coerce_reviewer_response(raw_response)
        if options.capture_tier2:
            capture_attempts.append(
                {
                    "attempt": len(capture_attempts) + 1,
                    "raw_response": response_text,
                    "dispatch": dict(dispatch_meta),
                }
            )
        actual_model_id = str(dispatch_meta.get("reviewer_model_id") or reviewer_model_id)
        actual_family = str(dispatch_meta.get("reviewer_family") or reviewer_family)
        actual_route_name = str(dispatch_meta.get("route_name") or route_name)
        observed_cost = _observed_cost(dispatch_meta)
        budget.record_spend(estimate, observed_cost_usd=observed_cost)
        if route is not None:
            _record_daily_spend(
                options=options,
                level=level,
                slug=slug,
                route=route,
                estimate=estimate,
                observed_cost_usd=observed_cost,
            )
        if (
            actual_model_id != reviewer_model_id
            or actual_family != reviewer_family
            # route_name keys the composite cache — a reviewer answering from the
            # wrong route must not poison route-keyed rows (codex review of #4401;
            # LiveReviewerDispatcher checks this itself, but _run_tier2 accepts
            # arbitrary reviewer callables). Only enforceable when the workflow
            # resolved an expected route (live mode); injected test reviewers with
            # no resolved route (route_name=None) keep their reported name.
            or (route_name is not None and actual_route_name != route_name)
        ):
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=actual_model_id,
                reviewer_family=actual_family,
                route_name=actual_route_name,
                status="provider_error",
                reason="reviewer_identity_mismatch",
            )
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": "provider_error",
                    "reason": "reviewer_identity_mismatch",
                    "actual_reviewer_model_id": actual_model_id,
                    "actual_reviewer_family": actual_family,
                    "actual_route_name": actual_route_name,
                    "estimate": estimate,
                },
                "workflow_verdict": "PROVIDER_FAILURE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": actual_model_id,
                "reviewer_family": actual_family,
            }
        if _cost_overrun(estimate, observed_cost):
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=reviewer_model_id,
                reviewer_family=reviewer_family,
                route_name=route_name,
                status="cost_overrun",
                reason="observed_cost_gt_125pct_estimate",
            )
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": "cost_overrun",
                    "estimate": estimate,
                    "observed_cost_usd": observed_cost,
                    "reason": "observed_cost_gt_125pct_estimate",
                },
                "workflow_verdict": "COST_OVERRUN",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }
        llm_reviewer_dispatch.enforce_tool_budget(dispatch_meta)
        telemetry_warning = llm_reviewer_dispatch.tool_call_anomaly_warning(dispatch_meta, estimate)
        if telemetry_warning is not None:
            dispatch_meta = {**dispatch_meta, "telemetry_warning": telemetry_warning}
        try:
            parsed_payload = llm_reviewer.parse_and_evaluate_llm_response(
                response_text,
                module_md=texts.get("module.md", ""),
                activities_yaml=texts.get("activities.yaml", ""),
                vocabulary_yaml=texts.get("vocabulary.yaml", ""),
                resources_yaml=texts.get("resources.yaml", ""),
                return_payload=True,
            )
            if not isinstance(parsed_payload, Mapping):
                raise ValueError("parsed reviewer payload must be a mapping")
            payload = _payload_from_reviewer_payload(parsed_payload)
            llm_reviewer.validate_reviewer_payload(payload, policy_family)
        except ValueError as exc:
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=reviewer_model_id,
                reviewer_family=reviewer_family,
                route_name=route_name,
                status="schema_failure",
                reason=str(exc),
            )
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": "schema_failure",
                    "reason": str(exc),
                    "estimate": estimate,
                },
                "workflow_verdict": "SCHEMA_FAILURE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }
        findings = _findings_from_payload(payload)
        if _parse_failed(findings):
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=reviewer_model_id,
                reviewer_family=reviewer_family,
                route_name=route_name,
                status="parse_failure",
            )
            return {
                "findings": findings,
                "result": {
                    **base_result,
                    "status": "parse_failure",
                    "findings": len(findings),
                    "estimate": estimate,
                },
                "workflow_verdict": "PARSE_FAILURE",
                "completion_status": "INCOMPLETE",
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }

        gate_outcome = _run_reviewer_gate_sequence(
            payload,
            dispatch_meta,
            policy_family=policy_family,
            theatre_retry_available=not theatre_retried,
            deep_read_retry_available=not deep_read_retried,
        )
        if gate_outcome.retry_reason == llm_reviewer_dispatch.INVALID_TOOL_THEATRE:
            theatre_retried = True
            attempt_prompt = llm_reviewer_dispatch.reviewer_retry_prompt(
                prompt,
                llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
            )
            continue
        if gate_outcome.retry_reason == llm_reviewer_dispatch.DEEP_READ_REQUIRED:
            deep_read_retried = True
            attempt_prompt = llm_reviewer_dispatch.reviewer_retry_prompt(
                prompt,
                llm_reviewer_dispatch.DEEP_READ_REQUIRED,
            )
            continue
        if gate_outcome.status == llm_reviewer_dispatch.RETRY_EXHAUSTED:
            _record_live_tier2_outcome(
                options=options,
                level=level,
                slug=slug,
                reviewer_model_id=reviewer_model_id,
                reviewer_family=reviewer_family,
                route_name=route_name,
                status=llm_reviewer_dispatch.RETRY_EXHAUSTED,
                reason=llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
            )
            return {
                "findings": [],
                "result": {
                    **base_result,
                    "status": llm_reviewer_dispatch.RETRY_EXHAUSTED,
                    "reason": llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
                    "gate_reason": gate_outcome.gate_reason,
                    "estimate": estimate,
                    "dispatch": dispatch_meta,
                },
                "workflow_verdict": llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
                "completion_status": "INCOMPLETE",
                "llm_used": True,
                "reviewer_model_id": reviewer_model_id,
                "reviewer_family": reviewer_family,
            }

        payload = gate_outcome.payload
        findings = gate_outcome.findings
        tier2_status = gate_outcome.status
        workflow_override = gate_outcome.workflow_override
        grounding_gate = gate_outcome.grounding_gate or llm_reviewer_dispatch.GroundingGateResult(payload=payload)
        break

    _record_live_tier2_outcome(
        options=options,
        level=level,
        slug=slug,
        reviewer_model_id=reviewer_model_id,
        reviewer_family=reviewer_family,
        route_name=route_name,
        status=tier2_status,
        reason=workflow_override,
    )
    tier2_run_id = f"qg-workflow-{uuid4().hex}"
    if options.persist_llm_qg:
        llm_qg_store.record_llm_qg(
            level=level,
            slug=slug,
            module_dir=target.module_dir,
            payload=payload,
            gate_version=options.gate_version,
            prompt_hash=prompt_hash,
            checker_version=CHECKER_VERSION,
            level_policy_family=policy_family,
            reviewer_model=reviewer_model_id,
            reviewer_family=reviewer_family,
            route_name=route_name,
            tool_call_count=llm_reviewer_dispatch.tool_call_count_from_dispatch_meta(dispatch_meta),
            tools_used=[str(tool) for tool in (dispatch_meta.get("tools_used") or ())],
            tool_events=llm_reviewer_dispatch.tool_events_from_dispatch_meta(dispatch_meta),
            source="qg_workflow",
            run_id=tier2_run_id,
            path=store_path,
        )
    result = {
        **base_result,
        "status": tier2_status,
        "findings": len(findings),
        "estimate": estimate,
        "dispatch": dispatch_meta,
        "invalid_fact_checks": grounding_gate.invalid_fact_checks,
        "inadmissible_positive_verdicts": grounding_gate.inadmissible_positive_verdicts,
    }
    if options.capture_tier2:
        result.update(
            {
                "tier2_run_id": tier2_run_id,
                "payload": payload,
                "raw_response": response_text,
                "retry_history": capture_attempts,
                "gate_outcomes": {
                    "status": tier2_status,
                    "workflow_override": workflow_override,
                    "theatre_retried": theatre_retried,
                    "deep_read_retried": deep_read_retried,
                    "grounding": {
                        "ungrounded_findings": grounding_gate.ungrounded_findings,
                        "required_ungrounded_findings": grounding_gate.required_ungrounded_findings,
                        "invalid_fact_checks": grounding_gate.invalid_fact_checks,
                        "inadmissible_positive_verdicts": grounding_gate.inadmissible_positive_verdicts,
                    },
                },
            }
        )
    return {
        "findings": findings,
        "result": result,
        "llm_used": True,
        "workflow_verdict": workflow_override,
        "reviewer_model_id": reviewer_model_id,
        "reviewer_family": reviewer_family,
    }


def _tier2_route(
    *,
    options: WorkflowOptions,
    policy_family: str,
    contested_gold_suppressed: bool,
) -> llm_reviewer_dispatch.ReviewerRoute | None:
    if not options.live_reviewer:
        return None
    return llm_reviewer_dispatch.route_for_review(
        policy_family=policy_family,
        contested_gold_suppressed=contested_gold_suppressed,
        factual_sensitive=policy_family == "seminar",
    )


def _live_reviewer_block(
    *,
    target: ReviewTarget,
    level: str,
    slug: str,
    policy_family: str,
    route: llm_reviewer_dispatch.ReviewerRoute | None,
    options: WorkflowOptions,
) -> dict[str, Any] | None:
    if route is None:
        return None
    if options.dry_run:
        return None
    try:
        llm_reviewer_dispatch.assert_mcp_required_for_policy(
            policy_family=policy_family,
            route=route,
        )
        lineage = llm_reviewer_dispatch.resolve_author_lineage(
            level=level,
            slug=slug,
            module_dir=target.module_dir,
            explicit_author_family=options.author_family,
        )
        llm_reviewer_dispatch.validate_cross_family(route, lineage)
    except llm_reviewer_dispatch.ReviewerSelfReviewError as exc:
        return {
            "status": "self_review_blocked",
            "reason": "self_review",
            "message": str(exc),
        }
    except llm_reviewer_dispatch.ReviewerLineageError as exc:
        return {
            "status": "lineage_required",
            "reason": "author_family_unavailable",
            "message": str(exc),
        }
    except llm_reviewer_dispatch.ReviewerRouteError as exc:
        return {
            "status": "provider_error",
            "reason": "disallowed_reviewer_route",
            "message": str(exc),
        }
    if not options.dry_run and not _exact_canary_passes(level=level, route=route, options=options):
        return {
            "status": "skipped_canary_required",
            "reason": "exact_canary_required",
            "message": "live Tier-2 calls require a passing same-route canary artifact",
        }
    return None


def _exact_canary_passes(
    *,
    level: str,
    route: llm_reviewer_dispatch.ReviewerRoute,
    options: WorkflowOptions,
) -> bool:
    artifacts = options.canary_artifacts or {}
    for key in (_canary_level_key(level), level.strip().lower(), "seminar"):
        path = artifacts.get(key)
        if path and llm_reviewer_dispatch.canary_artifact_passes(
            path,
            level=level,
            gate_version=options.gate_version,
            route=route,
        ):
            return True
    return False


def _canary_level_key(level: str) -> str:
    policy = policy_for_level(level)
    if policy.family == "seminar":
        return "seminar"
    clean = level.strip().lower()
    if clean.startswith("b1"):
        return "b1"
    return clean


def _coerce_reviewer_response(raw_response: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(raw_response, llm_reviewer_dispatch.DispatchResult):
        return raw_response.response_text, raw_response.metadata()
    if isinstance(raw_response, Mapping):
        dispatch = raw_response.get("_llm_reviewer_dispatch")
        if isinstance(dispatch, Mapping):
            response = raw_response.get("response_text") or raw_response.get("response")
            if isinstance(response, str):
                return response, dict(dispatch)
        return json.dumps(raw_response, ensure_ascii=False), {}
    return str(raw_response), {}


def _observed_cost(dispatch_meta: Mapping[str, Any]) -> float | None:
    value = dispatch_meta.get("observed_cost_usd")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cost_overrun(
    estimate: Mapping[str, Any],
    observed_cost: float | None,
) -> bool:
    if observed_cost is None:
        return False
    estimated = float(estimate.get("estimated_cost_usd") or 0.0)
    if estimated <= 0:
        return False
    return observed_cost > estimated * 1.25


def _record_daily_spend(
    *,
    options: WorkflowOptions,
    level: str,
    slug: str,
    route: llm_reviewer_dispatch.ReviewerRoute,
    estimate: Mapping[str, Any],
    observed_cost_usd: float | None,
) -> None:
    if not options.live_reviewer or not options.record_daily_spend:
        return
    llm_reviewer_dispatch.append_daily_spend(
        path=options.daily_spend_path,
        level=level,
        slug=slug,
        route=route,
        estimated_cost_usd=float(estimate.get("estimated_cost_usd") or 0.0),
        observed_cost_usd=observed_cost_usd,
    )


def _record_live_tier2_outcome(
    *,
    options: WorkflowOptions,
    level: str,
    slug: str,
    reviewer_model_id: str | None,
    reviewer_family: str | None,
    route_name: str | None,
    status: str,
    reason: str | None = None,
) -> dict[str, Any] | None:
    if not options.live_reviewer or options.dry_run or not options.record_live_outcomes:
        return None
    return llm_qg_store.record_live_tier2_outcome(
        level=level,
        slug=slug,
        gate_version=options.gate_version,
        reviewer_model=reviewer_model_id,
        reviewer_family=reviewer_family,
        route_name=route_name,
        status=status,
        reason=reason,
        path=options.circuit_state_path,
    )


def _parse_failed(findings: Sequence[Mapping[str, Any]]) -> bool:
    return any(str(finding.get("issue_id")) == "LLM_RESPONSE_PARSE_FAILURE" for finding in findings)


def _run_reviewer_gate_sequence(
    payload: Mapping[str, Any],
    dispatch_meta: Mapping[str, Any],
    *,
    policy_family: str,
    theatre_retry_available: bool,
    deep_read_retry_available: bool,
    retry_unavailable_fails: bool = False,
) -> _ReviewerGateOutcome:
    """Apply the canonical theatre/deep-read/grounding/factual-sweep gates."""
    working_payload = dict(payload)
    theatre = llm_reviewer_dispatch.tool_theatre_violation(
        policy_family=policy_family,
        payload=working_payload,
        dispatch_meta=dispatch_meta,
    )
    if theatre is not None:
        if theatre_retry_available or retry_unavailable_fails:
            return _ReviewerGateOutcome(
                payload=working_payload,
                findings=[],
                retry_reason=llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
                gate_reason=str(theatre.get("reason") or ""),
            )
        return _ReviewerGateOutcome(
            payload=working_payload,
            findings=[],
            status=llm_reviewer_dispatch.RETRY_EXHAUSTED,
            workflow_override=llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
            gate_reason=str(theatre.get("reason") or ""),
        )

    if llm_reviewer_dispatch.deep_read_required(working_payload, dispatch_meta):
        if deep_read_retry_available or retry_unavailable_fails:
            return _ReviewerGateOutcome(
                payload=working_payload,
                findings=[],
                retry_reason=llm_reviewer_dispatch.DEEP_READ_REQUIRED,
            )
        working_payload = llm_reviewer_dispatch.mark_deep_read_attempted(working_payload)
        llm_reviewer.validate_reviewer_payload(working_payload, policy_family)

    grounding_gate = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        working_payload,
        dispatch_meta,
        policy_family=policy_family,
    )
    working_payload = grounding_gate.payload
    sweep_incomplete = llm_reviewer_dispatch.factual_sweep_incomplete(
        working_payload,
        policy_family=policy_family,
        invalid_fact_checks=grounding_gate.invalid_fact_checks,
    )
    if grounding_gate.inadmissible_positive_verdicts:
        working_payload["inadmissible_positive_verdicts"] = grounding_gate.inadmissible_positive_verdicts
    if (
        grounding_gate.required_ungrounded_findings
        or grounding_gate.invalid_fact_checks
        or grounding_gate.inadmissible_positive_verdicts
        or sweep_incomplete
    ):
        if (
            grounding_gate.inadmissible_positive_verdicts
            and not grounding_gate.invalid_fact_checks
            and not grounding_gate.required_ungrounded_findings
        ):
            status = "inadmissible_citations"
        elif grounding_gate.required_ungrounded_findings or grounding_gate.invalid_fact_checks:
            status = llm_reviewer_dispatch.UNGROUNDED_FINDINGS
        else:
            status = "factual_sweep_incomplete"
        workflow_override = "FAIL" if sweep_incomplete else "WARN"
        severity = "critical" if sweep_incomplete else "warning"
        message = "Grounded reviewer gate found ungrounded evidence or an incomplete seminar fact-check sweep."
        if (
            grounding_gate.inadmissible_positive_verdicts
            and not grounding_gate.invalid_fact_checks
            and not grounding_gate.required_ungrounded_findings
        ):
            message = (
                "reviewer confirmed/refuted claims on summary-only wiki evidence after the forced "
                "deep-read retry — factual sweep uncertified"
            )
        findings = [
            *_findings_from_payload(working_payload),
            _reviewer_gate_finding(
                severity=severity,
                issue_id="LLM_REVIEWER_GROUNDING_GATE",
                message=message,
            ),
        ]
        working_payload = _payload_from_findings(
            findings,
            fact_checks=working_payload.get("fact_checks", []),
            evidence_gaps=working_payload.get("evidence_gaps", []),
        )
        if grounding_gate.inadmissible_positive_verdicts:
            working_payload["inadmissible_positive_verdicts"] = grounding_gate.inadmissible_positive_verdicts
        llm_reviewer.validate_reviewer_payload(working_payload, policy_family)
        return _ReviewerGateOutcome(
            payload=working_payload,
            findings=findings,
            status=status,
            workflow_override=workflow_override,
            grounding_gate=grounding_gate,
        )

    return _ReviewerGateOutcome(
        payload=working_payload,
        findings=_findings_from_payload(working_payload),
        grounding_gate=grounding_gate,
    )


def _has_stale_cache(
    *,
    level: str,
    slug: str,
    gate_version: str,
    checker_version: str,
    level_policy_family: str,
    reviewer_model: str,
    route_name: str | None,
    store_path: Path | None,
) -> bool:
    latest = llm_qg_store.latest_llm_qg(
        level,
        slug,
        gate_version=gate_version,
        checker_version=checker_version,
        level_policy_family=level_policy_family,
        reviewer_model=reviewer_model,
        route_name=route_name,
        path=store_path,
    )
    return latest is not None


def estimate_llm_cost(prompt: str, policy_family: str) -> dict[str, Any]:
    """Estimate reviewer token/cost by level profile."""

    prompt_tokens = max(1, len(prompt.encode("utf-8")) // 4)
    completion_tokens = 900 if policy_family == "seminar" else 600
    profile = llm_reviewer_dispatch.measured_cost_profile_for_policy(policy_family)
    total_tokens = prompt_tokens + completion_tokens
    return {
        "policy_family": policy_family,
        "estimated_prompt_tokens": prompt_tokens,
        "estimated_completion_tokens": completion_tokens,
        "estimated_total_tokens": total_tokens,
        "estimated_cost_usd": llm_reviewer_dispatch.measured_estimated_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            profile=profile,
        ),
        **profile.estimate_fields(),
        "basis": llm_reviewer_dispatch.measured_cost_basis(profile),
    }


def _build_evidence_record(
    *,
    level: str,
    slug: str,
    target: ReviewTarget,
    policy_family: str,
    policy_english: str,
    content_sha: str,
    prompt_hash: str | None,
    findings: Sequence[Mapping[str, Any]],
    tier_results: Sequence[Mapping[str, Any]],
    workflow_verdict: str | None,
    completion_status: str,
    llm_used: bool,
    llm_required_by_policy: bool,
    llm_required_by_harness: bool,
    llm_cost_override: bool,
    reviewer_model_id: str,
    reviewer_family: str,
    options: WorkflowOptions,
) -> dict[str, Any]:
    dimensions = dimensions_from_findings(findings)
    aggregate = _aggregate_from_dimensions(dimensions)
    schema_verdict = aggregate["verdict"]
    terminal_verdict = aggregate["terminal_verdict"]
    infra_only_incomplete = workflow_verdict in {
        llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
        llm_reviewer_dispatch.RETRY_EXHAUSTED,
    }
    if completion_status == "INCOMPLETE" and options.fail_closed_on_llm_skip and not infra_only_incomplete:
        schema_verdict = "FAIL"
        terminal_verdict = "FAIL"
    aggregate.update(
        {
            "workflow_verdict": workflow_verdict or schema_verdict,
            "completion_status": completion_status,
            "finding_count": len(findings),
            "content_hash_basis": CONTENT_HASH_BASIS,
            "content_files": list(llm_qg_store.CONTENT_FILES),
        }
    )
    record = qg_schema.build_evidence_record(
        profile="curriculum_llm_compact",
        evidence_kind="module",
        module_id=f"{level}/{slug}",
        fixture_id=target.fixture_id,
        level_policy={
            "family": policy_family,
            "english_policy": policy_english,
            "llm_policy_families": sorted(LLM_POLICY_FAMILIES),
        },
        dimensions=dimensions,
        checker_runs=_checker_runs(
            tier_results,
            options,
            reviewer_model_id=reviewer_model_id,
            reviewer_family=reviewer_family,
        ),
        content_sha=content_sha,
        provenance={
            "created_at": _now_z(),
            "run_id": f"qg-workflow-{uuid4().hex}",
            "source": "qg_workflow",
            "module_dir": str(target.module_dir),
        },
        verdict=schema_verdict,
        terminal_verdict=terminal_verdict,
        aggregate=aggregate,
    )
    record["qg_workflow"] = {
        "gate_version": options.gate_version,
        "prompt_hash": prompt_hash,
            "checker_version": CHECKER_VERSION,
            "checker_config_hash": checker_config_hash(),
            "reviewer_model_id": reviewer_model_id,
            "reviewer_family": reviewer_family,
            "content_hash_basis": CONTENT_HASH_BASIS,
            "content_files": list(llm_qg_store.CONTENT_FILES),
            "tiers": [dict(item) for item in tier_results],
    }
    record["llm_review"] = {
        "used": llm_used,
        "required_by_policy": llm_required_by_policy,
        "required_by_harness": llm_required_by_harness,
        "cost_override_applied": llm_cost_override,
        "default_fail_override": (
            "Tier-0 hard FAIL short-circuits the LLM tier by default for cost; "
            "use --llm-on-fail or calibration sample mode for richer diagnostics."
        ),
    }
    record["workflow_verdict"] = aggregate["workflow_verdict"]
    record["completion_status"] = completion_status
    qg_schema.validate_record(record)
    return record


def _checker_runs(
    tier_results: Sequence[Mapping[str, Any]],
    options: WorkflowOptions,
    *,
    reviewer_model_id: str,
    reviewer_family: str,
) -> list[dict[str, Any]]:
    runs = [
        {
            "source": "deterministic",
            "checker": CHECKER_VERSION,
            "config_hash": checker_config_hash(),
            "provider": None,
            "model": None,
        }
    ]
    if any(tier.get("tier") == 1 and int(tier.get("gold_rows_matched") or 0) for tier in tier_results):
        runs.append(
            {
                "source": "lookup",
                "checker": "ua_gec_gold_fixture",
                "config_hash": None,
                "provider": None,
                "model": None,
            }
        )
    if any(tier.get("tier") == 2 and tier.get("status") in {"ran", "cache_hit"} for tier in tier_results):
        runs.append(
            {
                "source": "llm_reviewer",
                "checker": options.gate_version,
                "config_hash": None,
                "provider": reviewer_family,
                "model": reviewer_model_id,
            }
        )
    return runs


def _payload_from_findings(
    findings: Sequence[Mapping[str, Any]],
    *,
    fact_checks: Sequence[Mapping[str, Any]] = (),
    evidence_gaps: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    dimensions = dimensions_from_findings(findings)
    return {
        "schema_version": qg_schema.SCHEMA_VERSION,
        "aggregate": _aggregate_from_dimensions(dimensions),
        "dimensions": dimensions,
        "findings": [dict(finding) for finding in findings],
        "fact_checks": [dict(item) for item in fact_checks],
        "evidence_gaps": [dict(item) for item in evidence_gaps],
    }


def _payload_from_reviewer_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError("reviewer payload findings must be a list")
    fact_checks = payload.get("fact_checks", [])
    evidence_gaps = payload.get("evidence_gaps", [])
    return _payload_from_findings(
        [dict(item) for item in findings if isinstance(item, Mapping)],
        fact_checks=[dict(item) for item in fact_checks if isinstance(item, Mapping)]
        if isinstance(fact_checks, list)
        else (),
        evidence_gaps=[dict(item) for item in evidence_gaps if isinstance(item, Mapping)]
        if isinstance(evidence_gaps, list)
        else (),
    )


def _findings_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    findings = payload.get("findings")
    if isinstance(findings, list):
        out = [dict(item) for item in findings if isinstance(item, Mapping)]
        for finding in out:
            qg_schema.validate_finding(finding)
        return out
    dimensions = payload.get("dimensions")
    out: list[dict[str, Any]] = []
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if not isinstance(entry, Mapping) or not isinstance(entry.get("findings"), list):
                continue
            out.extend(dict(item) for item in entry["findings"] if isinstance(item, Mapping))
    for finding in out:
        qg_schema.validate_finding(finding)
    return out


def _reviewer_gate_finding(*, severity: str, issue_id: str, message: str) -> dict[str, Any]:
    return qg_schema.build_finding(
        issue_id=issue_id,
        issue_class="other",
        dimension="mechanics",
        severity=severity,
        file="llm_response",
        line=None,
        span=None,
        excerpt="grounded reviewer gate",
        message=message,
        confidence="deterministic",
        disposition="defect",
        detector={
            "adapter": "llm_reviewer_dispatch",
            "rule_id": issue_id,
        },
        attribution={
            "corpus": "reviewer_tool_telemetry",
            "evidence": "Deterministic grounded-reviewer gate",
        },
    )


def _aggregate_from_dimensions(dimensions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    has_fail = any(entry.get("verdict") == "FAIL" for entry in dimensions.values())
    has_warn = any(entry.get("verdict") == "WARN" for entry in dimensions.values())
    verdict = "FAIL" if has_fail else "WARN" if has_warn else "PASS"
    return {
        "verdict": verdict,
        "terminal_verdict": "FAIL" if has_fail else "PASS",
        "failing_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "FAIL"],
        "warning_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "WARN"],
    }


def _verdict_for_findings(findings: Sequence[Mapping[str, Any]]) -> str:
    if any(finding.get("severity") == "critical" for finding in findings):
        return "FAIL"
    if findings:
        return "WARN"
    return "PASS"


def _dedupe_by_finding_id(findings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for finding in findings:
        qg_schema.validate_finding(finding)
        finding_id = str(finding["finding_id"])
        if finding_id in seen:
            continue
        seen.add(finding_id)
        out.append(dict(finding))
    return out


def _gold_contested(finding: Mapping[str, Any]) -> bool:
    metadata = finding.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    gold = metadata.get("ua_gec_gold")
    if not isinstance(gold, Mapping):
        return False
    return bool(gold.get("contested_flag") or gold.get("contested"))


def _read_module_texts(module_dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for name in llm_qg_store.CONTENT_FILES:
        path = module_dir / name
        texts[name] = path.read_text(encoding="utf-8") if path.exists() else ""
    return texts


def _llm_enabled_for_any_target(targets: Sequence[ReviewTarget], options: WorkflowOptions) -> bool:
    if not options.enable_llm:
        return False
    return any(
        policy_for_level(target.level).family in LLM_POLICY_FAMILIES
        or options.force_llm
        or options.calibration_sample
        for target in targets
    )


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _targets_from_args(args: argparse.Namespace) -> list[ReviewTarget]:
    if args.target:
        targets = []
        for raw in args.target:
            parts = raw.split(":", 2)
            if len(parts) != 3:
                raise ValueError("--target must be level:slug:module_dir")
            targets.append(ReviewTarget(level=parts[0], slug=parts[1], module_dir=Path(parts[2])))
        return targets
    if not args.module_dir or not args.level:
        raise ValueError("--module-dir requires --level")
    return [
        ReviewTarget(
            level=args.level,
            slug=args.slug or Path(args.module_dir).name,
            module_dir=Path(args.module_dir),
            fixture_id=args.fixture_id,
            plan_path=args.plan_path,
        )
    ]


def _reviewer_from_response(path: Path | None) -> Reviewer | None:
    if path is None:
        return None
    response_text = path.read_text(encoding="utf-8")

    def reviewer(_target: ReviewTarget, _prompt: str) -> str:
        return response_text

    return reviewer


def calibrate_modules(
    targets: Sequence[ReviewTarget],
    *,
    options: WorkflowOptions,
    reviewer: Reviewer | None = None,
    store_path: Path | None = None,
    probes: int = 5,
) -> dict[str, Any]:
    """Run a small live probe set and report observed/estimated cost factors."""

    if not options.live_reviewer:
        raise ValueError("--calibrate requires --live-reviewer")
    if options.max_cost_usd is None:
        raise ValueError("--calibrate requires --max-cost-usd")
    sample = list(targets[: max(1, probes)])
    calibration_options = WorkflowOptions(
        gate_version=options.gate_version,
        reviewer_model_id=options.reviewer_model_id,
        reviewer_family=options.reviewer_family,
        live_reviewer=True,
        author_family=options.author_family,
        canary_artifacts=options.canary_artifacts,
        daily_spend_path=options.daily_spend_path,
        circuit_state_path=options.circuit_state_path,
        run_command=options.run_command,
        enable_llm=True,
        force_llm=True,
        llm_on_fail=True,
        calibration_sample=True,
        dry_run=False,
        canary_passed=options.canary_passed,
        max_llm_calls=options.max_llm_calls,
        max_cost_usd=options.max_cost_usd,
        max_daily_cost_usd=options.max_daily_cost_usd,
        max_module_cost_usd=options.max_module_cost_usd,
        fail_closed_on_llm_skip=options.fail_closed_on_llm_skip,
    )
    records = review_modules(
        sample,
        options=calibration_options,
        reviewer=reviewer,
        store_path=store_path,
    )
    factors: list[float] = []
    probes_out: list[dict[str, Any]] = []
    for record in records:
        tier2 = _tier_from_record(record, 2)
        estimate = tier2.get("estimate") if isinstance(tier2.get("estimate"), Mapping) else {}
        dispatch = tier2.get("dispatch") if isinstance(tier2.get("dispatch"), Mapping) else {}
        estimated_cost = float(estimate.get("estimated_cost_usd") or 0.0)
        observed_cost = _observed_cost(dispatch)
        if estimated_cost > 0 and observed_cost is not None:
            factors.append(observed_cost / estimated_cost)
        probes_out.append(
            {
                "module_id": record["module_id"],
                "status": tier2.get("status"),
                "reviewer_model_id": tier2.get("reviewer_model_id"),
                "estimated_cost_usd": estimated_cost,
                "observed_cost_usd": observed_cost,
            }
        )
    factor = sorted(factors)[len(factors) // 2] if factors else None
    return {
        "schema_version": "qg_workflow_calibration.v1",
        "probe_count": len(probes_out),
        "cost_factor_median": round(factor, 4) if factor is not None else None,
        "probes": probes_out,
        "run_command": options.run_command,
    }


def _canary_artifacts_from_args(
    args: argparse.Namespace,
    targets: Sequence[ReviewTarget],
) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for spec in args.canary_artifact or []:
        if "=" not in spec:
            raise ValueError("--canary-artifact must use LEVEL=PATH")
        level, raw_path = spec.split("=", 1)
        artifacts[_canary_level_key(level)] = Path(raw_path)
    if args.canary_result and args.live_reviewer and len(targets) == 1:
        artifacts.setdefault(_canary_level_key(targets[0].level), args.canary_result)
    return artifacts


def _exact_run_command(argv: Sequence[str]) -> str:
    filtered: list[str] = []
    skip_next = False
    drop_value_after = {"--output"}
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item == "--dry-run":
            continue
        if item in drop_value_after:
            skip_next = True
            continue
        filtered.append(item)
    return ".venv/bin/python scripts/audit/qg_workflow.py " + shlex.join(filtered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-dir", type=Path, help="Single module directory to review.")
    parser.add_argument("--level", help="Level for --module-dir, e.g. b1 or folk.")
    parser.add_argument("--slug", help="Slug for --module-dir; defaults to directory name.")
    parser.add_argument("--fixture-id", help="Optional UA-GEC/curriculum fixture id.")
    parser.add_argument("--plan-path", type=Path, help="Optional plan path for deterministic plan checks.")
    parser.add_argument(
        "--target",
        action="append",
        help="Repeatable broad target in level:slug:module_dir form.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print per-tier counts and cost estimates; write nothing.")
    parser.add_argument("--force-llm", action="store_true", help="Enable Tier-2 for this run and override A1/A2 policy skip.")
    parser.add_argument("--llm-on-fail", action="store_true", help="Run Tier-2 even after Tier-0 hard FAIL.")
    parser.add_argument("--calibration-sample", action="store_true", help="Treat targets as an explicit calibration sample.")
    parser.add_argument("--live-reviewer", action="store_true", help="Use the live reviewer dispatcher; requires budget and exact canary artifacts.")
    parser.add_argument("--author-family", help="Explicit module author family for live cross-family review.")
    parser.add_argument("--max-llm-calls", type=int, help="Per-run reviewer call ceiling.")
    parser.add_argument("--max-cost-usd", type=float, help="Per-run cost ceiling.")
    parser.add_argument("--max-daily-cost-usd", type=float, help="Per-day safety rail for this local run.")
    parser.add_argument("--max-module-cost-usd", type=float, help="Per-module pathological prompt cost cap.")
    parser.add_argument("--daily-spend-ledger", type=Path, help="Optional local JSONL spend ledger path.")
    parser.add_argument("--qg-circuit-state", type=Path, help="Optional live Tier-2 circuit sidecar JSON path.")
    parser.add_argument("--reset-circuit", action="store_true", help="Clear the live Tier-2 circuit sidecar and exit unless targets are also supplied.")
    parser.add_argument("--gate-version", default=DEFAULT_GATE_VERSION)
    parser.add_argument("--reviewer-model-id", default=DEFAULT_REVIEWER_MODEL_ID)
    parser.add_argument("--reviewer-family", default=DEFAULT_REVIEWER_FAMILY)
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite cache path.")
    parser.add_argument("--llm-response-json", type=Path, help="Precomputed reviewer response JSON; no live dispatch.")
    parser.add_argument("--canary-result", type=Path, help="Reviewer canary JSON that must pass before broad LLM.")
    parser.add_argument(
        "--canary-artifact",
        action="append",
        default=[],
        help="Exact dispatcher canary artifact in LEVEL=PATH form; repeat for mixed-level live batches.",
    )
    parser.add_argument("--calibrate", action="store_true", help="Run up to five live probes to calibrate route cost estimates.")
    parser.add_argument("--calibration-probes", type=int, default=5, help="Number of live probes for --calibrate.")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    parser.add_argument("--output", type=Path, help="Optional output file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv_list = list(argv) if argv is not None else sys.argv[1:]
    args = build_parser().parse_args(argv_list)
    try:
        if args.reset_circuit:
            reset_payload = llm_qg_store.reset_live_tier2_circuit(args.qg_circuit_state)
            has_targets = bool(args.target or args.module_dir)
            if not has_targets:
                output = (
                    json.dumps(reset_payload, ensure_ascii=False, indent=2, sort_keys=True)
                    if args.format == "json"
                    else "live Tier-2 circuit reset"
                )
                if args.output:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(output + "\n", encoding="utf-8")
                else:
                    print(output)
                return 0
        targets = _targets_from_args(args)
        canary_artifacts = _canary_artifacts_from_args(args, targets)
        enable_llm = bool(
            args.force_llm
            or args.llm_response_json
            or args.dry_run
            or args.db
            or args.live_reviewer
            or args.calibrate
        )
        canary_passed = False
        if not args.dry_run and not args.live_reviewer and len(targets) > 1 and _llm_enabled_for_any_target(
            targets,
            WorkflowOptions(
                enable_llm=enable_llm,
                force_llm=args.force_llm,
                calibration_sample=args.calibration_sample,
            ),
        ):
            canary_passed = args.canary_result is not None and canary_result_passes(
                args.canary_result,
                level=targets[0].level,
            )
            if not canary_passed:
                raise ValueError("broad Tier-2 runs require a passing llm_qg_canaries.py result")
        options = WorkflowOptions(
            gate_version=args.gate_version,
            reviewer_model_id=args.reviewer_model_id,
            reviewer_family=args.reviewer_family,
            live_reviewer=args.live_reviewer or args.calibrate,
            author_family=args.author_family,
            canary_artifacts=canary_artifacts,
            daily_spend_path=args.daily_spend_ledger,
            circuit_state_path=args.qg_circuit_state,
            run_command=_exact_run_command(argv_list),
            enable_llm=enable_llm,
            force_llm=args.force_llm,
            llm_on_fail=args.llm_on_fail,
            calibration_sample=args.calibration_sample or args.calibrate,
            dry_run=args.dry_run,
            canary_passed=canary_passed,
            max_llm_calls=args.max_llm_calls,
            max_cost_usd=args.max_cost_usd,
            max_daily_cost_usd=args.max_daily_cost_usd,
            max_module_cost_usd=args.max_module_cost_usd,
        )
        if args.calibrate:
            payload = calibrate_modules(
                targets,
                options=options,
                reviewer=_reviewer_from_response(args.llm_response_json),
                store_path=args.db,
                probes=args.calibration_probes,
            )
        elif args.dry_run:
            payload: dict[str, Any] | list[dict[str, Any]] = dry_run_modules(
                targets,
                options=options,
                store_path=args.db,
            )
        else:
            payload = review_modules(
                targets,
                options=options,
                reviewer=_reviewer_from_response(args.llm_response_json),
                store_path=args.db,
            )
            if len(payload) == 1:
                payload = payload[0]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.format == "json" else _summary(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0 if _passes(payload) else 1


def _summary(payload: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> str:
    if isinstance(payload, Mapping) and payload.get("dry_run") is True:
        counts = payload["counts"]
        return (
            "QG workflow dry-run\n"
            f"Modules: {counts['modules']}\n"
            f"Tier-1 gold rows matched: {counts['tier1_gold_rows_matched']}\n"
            f"Tier-2 estimated calls: {counts['tier2_estimated_calls']}"
        )
    if isinstance(payload, Mapping) and payload.get("schema_version") == "qg_workflow_calibration.v1":
        return (
            "QG workflow calibration\n"
            f"Probes: {payload['probe_count']}\n"
            f"Median cost factor: {payload['cost_factor_median']}"
        )
    records = [payload] if isinstance(payload, Mapping) else list(payload)
    lines = ["QG workflow evidence"]
    for record in records:
        lines.append(
            f"- {record['module_id']}: {record['workflow_verdict']} "
            f"({record['completion_status']}, findings={record['aggregate']['finding_count']})"
        )
    return "\n".join(lines)


def _passes(payload: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> bool:
    if isinstance(payload, Mapping) and payload.get("dry_run") is True:
        return True
    if isinstance(payload, Mapping) and payload.get("schema_version") == "qg_workflow_calibration.v1":
        return all(str(probe.get("status")) == "ran" for probe in payload.get("probes", []))
    records = [payload] if isinstance(payload, Mapping) else list(payload)
    return all(str(record.get("terminal_verdict")) == "PASS" for record in records)


if __name__ == "__main__":
    raise SystemExit(main())
