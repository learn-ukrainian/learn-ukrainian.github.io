#!/usr/bin/env python3
"""Cost-aware tiered curriculum quality-gate workflow.

This composes the deterministic/lookup adapters and the gated LLM reviewer into
one canonical ``qg_schema`` evidence record per module. Live reviewer dispatch
is intentionally absent until #4370 calibrates the prompt and canary runbook;
callers must inject a reviewer response or reuse a composite cache hit.
"""

from __future__ import annotations

import argparse
import json
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

from scripts.audit import llm_qg_canaries, llm_qg_store, llm_reviewer, qg_schema
from scripts.audit.content_surface_gates import policy_for_level
from scripts.audit.curriculum_qg_harness import CHECKER_VERSION, checker_config_hash
from scripts.audit.qg_adapters import (
    DeterministicRuleAdapter,
    ScorerInput,
    UaGecGoldFixtureAdapter,
    dimensions_from_findings,
)

DEFAULT_GATE_VERSION = "qg_workflow.v1"
DEFAULT_REVIEWER_MODEL_ID = "llm-reviewer-disabled-until-4370"
DEFAULT_REVIEWER_FAMILY = "qg_workflow"
LLM_POLICY_FAMILIES = frozenset({"b1_plus", "seminar"})
CONTENT_HASH_BASIS = "llm_qg_store.CONTENT_FILES"

Reviewer = Callable[["ReviewTarget", str], str | Mapping[str, Any]]


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

    def record_spend(self, estimate: Mapping[str, Any]) -> None:
        self.llm_calls += 1
        cost = float(estimate.get("estimated_cost_usd") or 0.0)
        self.cost_usd += cost
        self.daily_cost_usd += cost


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
    return {
        "schema_version": "qg_workflow_dry_run.v1",
        "dry_run": True,
        "writes": 0,
        "counts": counts,
        "level_profiles": dict(sorted(by_family.items())),
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
    if (
        len(targets) > 1
        and _llm_enabled_for_any_target(targets, effective_options)
        and not effective_options.canary_passed
    ):
        raise ValueError("broad LLM batches require an explicit passing canary pre-gate")
    budget = BudgetState()
    return [
        review_module(
            target,
            options=effective_options,
            reviewer=reviewer,
            store_path=store_path,
            budget=budget,
        )
        for target in targets
    ]


def canary_result_passes(path: Path, *, level: str) -> bool:
    """Evaluate a reviewer canary result JSON using the existing canary gate."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    report = llm_qg_canaries.evaluate_canaries(payload, level)
    return bool(report.get("passed"))


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
    base_result: dict[str, Any] = {
        "tier": 2,
        "name": "llm_reviewer",
        "llm_required_by_policy": policy_eligible,
        "policy_family": policy_family,
        "findings": 0,
    }
    if not policy_eligible:
        return {"findings": [], "result": {**base_result, "status": "skipped_policy"}}
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
        }
    if not options.enable_llm:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "skipped_flag_off",
                "reason": "Live Tier-2 reviewer remains flag-off until #4370 calibration lands.",
            },
        }

    cached = llm_qg_store.current_llm_qg_for_module(
        level,
        slug,
        target.module_dir,
        gate_version=options.gate_version,
        prompt_hash=prompt_hash,
        checker_version=CHECKER_VERSION,
        level_policy_family=policy_family,
        reviewer_model=options.reviewer_model_id,
        path=store_path,
    )
    if cached is not None:
        findings = _findings_from_payload(cached.payload)
        return {
            "findings": findings,
            "result": {
                **base_result,
                "status": "cache_hit",
                "findings": len(findings),
                "cache_run_id": cached.run_id,
            },
            "llm_used": True,
        }

    estimate = estimate_llm_cost(prompt, policy_family)
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
        }
    if options.dry_run:
        return {
            "findings": [],
            "result": {
                **base_result,
                "status": "dry_run_estimate",
                "estimate": estimate,
            },
        }
    if reviewer is None:
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
        }

    budget.record_spend(estimate)
    raw_response = reviewer(target, prompt)
    response_text = json.dumps(raw_response, ensure_ascii=False) if isinstance(raw_response, Mapping) else str(raw_response)
    findings = llm_reviewer.parse_and_evaluate_llm_response(
        response_text,
        module_md=texts.get("module.md", ""),
        activities_yaml=texts.get("activities.yaml", ""),
        vocabulary_yaml=texts.get("vocabulary.yaml", ""),
        resources_yaml=texts.get("resources.yaml", ""),
    )
    payload = _payload_from_findings(findings)
    llm_qg_store.record_llm_qg(
        level=level,
        slug=slug,
        module_dir=target.module_dir,
        payload=payload,
        gate_version=options.gate_version,
        prompt_hash=prompt_hash,
        checker_version=CHECKER_VERSION,
        level_policy_family=policy_family,
        reviewer_model=options.reviewer_model_id,
        reviewer_family=options.reviewer_family,
        source="qg_workflow",
        path=store_path,
    )
    return {
        "findings": findings,
        "result": {
            **base_result,
            "status": "ran",
            "findings": len(findings),
            "estimate": estimate,
        },
        "llm_used": True,
    }


def estimate_llm_cost(prompt: str, policy_family: str) -> dict[str, Any]:
    """Estimate reviewer token/cost by level profile."""

    prompt_tokens = max(1, len(prompt.encode("utf-8")) // 4)
    completion_tokens = 900 if policy_family == "seminar" else 600
    per_1k = 0.012 if policy_family == "seminar" else 0.008 if policy_family == "b1_plus" else 0.004
    total_tokens = prompt_tokens + completion_tokens
    return {
        "policy_family": policy_family,
        "estimated_prompt_tokens": prompt_tokens,
        "estimated_completion_tokens": completion_tokens,
        "estimated_total_tokens": total_tokens,
        "estimated_cost_usd": round(total_tokens / 1000.0 * per_1k, 6),
        "basis": "prompt byte estimate; replace with telemetry median when available",
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
    options: WorkflowOptions,
) -> dict[str, Any]:
    dimensions = dimensions_from_findings(findings)
    aggregate = _aggregate_from_dimensions(dimensions)
    schema_verdict = aggregate["verdict"]
    terminal_verdict = aggregate["terminal_verdict"]
    if completion_status == "INCOMPLETE" and options.fail_closed_on_llm_skip:
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
        checker_runs=_checker_runs(tier_results, options),
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
        "reviewer_model_id": options.reviewer_model_id,
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
                "provider": options.reviewer_family,
                "model": options.reviewer_model_id,
            }
        )
    return runs


def _payload_from_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dimensions = dimensions_from_findings(findings)
    return {
        "schema_version": qg_schema.SCHEMA_VERSION,
        "aggregate": _aggregate_from_dimensions(dimensions),
        "dimensions": dimensions,
        "findings": [dict(finding) for finding in findings],
    }


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
    parser.add_argument("--max-llm-calls", type=int, help="Per-run reviewer call ceiling.")
    parser.add_argument("--max-cost-usd", type=float, help="Per-run cost ceiling.")
    parser.add_argument("--max-daily-cost-usd", type=float, help="Per-day safety rail for this local run.")
    parser.add_argument("--max-module-cost-usd", type=float, help="Per-module pathological prompt cost cap.")
    parser.add_argument("--gate-version", default=DEFAULT_GATE_VERSION)
    parser.add_argument("--reviewer-model-id", default=DEFAULT_REVIEWER_MODEL_ID)
    parser.add_argument("--reviewer-family", default=DEFAULT_REVIEWER_FAMILY)
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite cache path.")
    parser.add_argument("--llm-response-json", type=Path, help="Precomputed reviewer response JSON; no live dispatch.")
    parser.add_argument("--canary-result", type=Path, help="Reviewer canary JSON that must pass before broad LLM.")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    parser.add_argument("--output", type=Path, help="Optional output file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        targets = _targets_from_args(args)
        enable_llm = bool(args.force_llm or args.llm_response_json or args.dry_run or args.db)
        canary_passed = False
        if not args.dry_run and len(targets) > 1 and _llm_enabled_for_any_target(
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
            enable_llm=enable_llm,
            force_llm=args.force_llm,
            llm_on_fail=args.llm_on_fail,
            calibration_sample=args.calibration_sample,
            dry_run=args.dry_run,
            canary_passed=canary_passed,
            max_llm_calls=args.max_llm_calls,
            max_cost_usd=args.max_cost_usd,
            max_daily_cost_usd=args.max_daily_cost_usd,
            max_module_cost_usd=args.max_module_cost_usd,
        )
        if args.dry_run:
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
    records = [payload] if isinstance(payload, Mapping) else list(payload)
    return all(str(record.get("terminal_verdict")) == "PASS" for record in records)


if __name__ == "__main__":
    raise SystemExit(main())
