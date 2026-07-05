from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_workflow


def _write_module(tmp_path: Path, *, level: str = "b1", slug: str = "sample") -> Path:
    module_dir = tmp_path / level / slug
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(
        "# Модуль\n\nУчні читають український текст і виконують коротке завдання.\n",
        encoding="utf-8",
    )
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _target(module_dir: Path, *, level: str = "b1") -> qg_workflow.ReviewTarget:
    return qg_workflow.ReviewTarget(level=level, slug=module_dir.name, module_dir=module_dir)


def _tier(record: dict[str, Any], tier_number: int) -> dict[str, Any]:
    return next(tier for tier in record["qg_workflow"]["tiers"] if tier["tier"] == tier_number)


def _canary_artifact(tmp_path: Path, *, level: str = "b1") -> Path:
    route = llm_reviewer_dispatch.route_for_review(policy_family="seminar" if level == "seminar" else "b1_plus")
    path = tmp_path / f"{level}-canary.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": llm_reviewer_dispatch.CANARY_SCHEMA_VERSION,
                "level": level,
                "gate_version": qg_workflow.DEFAULT_GATE_VERSION,
                "prompt_template_hash": llm_reviewer_dispatch.prompt_template_hash(),
                "reviewer_model_id": route.reviewer_model_id,
                "reviewer_family": route.reviewer_family,
                "route_name": route.route_name,
                "passed": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _dispatch_result(response: str, *, observed_cost_usd: float = 0.0) -> llm_reviewer_dispatch.DispatchResult:
    route = llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response,
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        observed_cost_usd=observed_cost_usd,
    )


def test_routing_b1_surface_uses_gemma_and_seminar_uses_frontier() -> None:
    b1_route = llm_reviewer_dispatch.route_for_review(policy_family="b1_plus")
    seminar_route = llm_reviewer_dispatch.route_for_review(policy_family="seminar")

    assert b1_route.bridge_command[0] == "ask-gemma"
    assert b1_route.reviewer_model_id == "openrouter/google/gemma-4-31b-it"
    assert seminar_route.bridge_command[:2] == ("ask-agy", "--to-model")
    assert seminar_route.reviewer_model_id == "gemini-3.1-pro-high"


def test_self_review_hard_fails() -> None:
    route = llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE
    lineage = llm_reviewer_dispatch.AuthorLineage(family="google", source="test")

    with pytest.raises(llm_reviewer_dispatch.ReviewerSelfReviewError):
        llm_reviewer_dispatch.validate_cross_family(route, lineage)


def test_deepseek_routes_are_excluded() -> None:
    bad_route = llm_reviewer_dispatch.ReviewerRoute(
        route_name="deepseek_bad",
        bridge_command=("ask-deepseek",),
        reviewer_model_id="deepseek-v4-pro",
        reviewer_family="deepseek",
        purpose="forbidden",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
    )

    llm_reviewer_dispatch.assert_route_allowed(llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE)

    with pytest.raises(
        llm_reviewer_dispatch.ReviewerRouteError,
        match="DeepSeek/Hermes reviewer routes are forbidden",
    ):
        llm_reviewer_dispatch.assert_route_allowed(bad_route)
    hermes_route = llm_reviewer_dispatch.ReviewerRoute(
        route_name="hermes_bad",
        bridge_command=("ask-hermes",),
        reviewer_model_id="openrouter/hermes/deepseek-r1",
        reviewer_family="openrouter",
        purpose="forbidden",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
    )

    with pytest.raises(
        llm_reviewer_dispatch.ReviewerRouteError,
        match="DeepSeek/Hermes reviewer routes are forbidden",
    ):
        llm_reviewer_dispatch.assert_route_allowed(hermes_route)
    assert all("deepseek" not in route.reviewer_model_id for route in llm_reviewer_dispatch.ROUTES)


def test_live_single_call_requires_exact_canary(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _dispatch_result('{"findings": []}')

    record = qg_workflow.review_module(
        _target(module_dir),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            author_family="openai",
            max_cost_usd=1.0,
            daily_spend_path=tmp_path / "spend.jsonl",
        ),
        reviewer=reviewer,
    )

    assert _tier(record, 2)["status"] == "skipped_canary_required"
    assert record["completion_status"] == "INCOMPLETE"
    assert calls == 0


def test_missing_canary_aborts_remaining_records(tmp_path: Path) -> None:
    first = _write_module(tmp_path, slug="first")
    second = _write_module(tmp_path, slug="second")
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _dispatch_result('{"findings": []}')

    records = qg_workflow.review_modules(
        [_target(first), _target(second)],
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            author_family="openai",
            max_cost_usd=1.0,
            daily_spend_path=tmp_path / "spend.jsonl",
        ),
        reviewer=reviewer,
    )

    assert [_tier(record, 2)["status"] for record in records] == [
        "skipped_canary_required",
        "aborted_batch",
    ]
    assert records[1]["completion_status"] == "INCOMPLETE"
    assert calls == 0


def test_live_cli_requires_max_cost_usd(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    canary = _canary_artifact(tmp_path)
    output = tmp_path / "out.json"

    code = qg_workflow.main(
        [
            "--module-dir",
            str(module_dir),
            "--level",
            "b1",
            "--live-reviewer",
            "--author-family",
            "openai",
            "--canary-artifact",
            f"b1={canary}",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    assert code == 2
    assert not output.exists()


def test_abort_gate_emits_incomplete_records_after_parse_failure(tmp_path: Path) -> None:
    first = _write_module(tmp_path, slug="first")
    second = _write_module(tmp_path, slug="second")
    canary = _canary_artifact(tmp_path)
    calls: list[str] = []

    def reviewer(target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(target.slug)
        return _dispatch_result("not json")

    records = qg_workflow.review_modules(
        [_target(first), _target(second)],
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            author_family="openai",
            canary_artifacts={"b1": canary},
            max_cost_usd=1.0,
            daily_spend_path=tmp_path / "spend.jsonl",
        ),
        reviewer=reviewer,
    )

    assert [_tier(record, 2)["status"] for record in records] == ["parse_failure", "aborted_batch"]
    assert records[1]["completion_status"] == "INCOMPLETE"
    assert calls == ["first"]


def test_schema_failures_use_parse_schema_abort_threshold() -> None:
    record = {"qg_workflow": {"tiers": [{"tier": 2, "status": "schema_failure"}]}}

    assert qg_workflow._batch_abort_reason([record]) == "parse_failure_rate"


def test_cost_overrun_gate_fails_closed(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    canary = _canary_artifact(tmp_path)

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result('{"findings": []}', observed_cost_usd=10.0)

    record = qg_workflow.review_module(
        _target(module_dir),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            author_family="openai",
            canary_artifacts={"b1": canary},
            max_cost_usd=20.0,
            daily_spend_path=tmp_path / "spend.jsonl",
        ),
        reviewer=reviewer,
    )

    assert _tier(record, 2)["status"] == "cost_overrun"
    assert record["completion_status"] == "INCOMPLETE"


def test_dry_run_gateable_artifact_shape(tmp_path: Path) -> None:
    first = _write_module(tmp_path, slug="one")
    second = _write_module(tmp_path, slug="two")
    output = tmp_path / "dry-run.json"

    code = qg_workflow.main(
        [
            "--target",
            f"b1:one:{first}",
            "--target",
            f"b1:two:{second}",
            "--dry-run",
            "--live-reviewer",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    artifact = payload["gateable_artifact"]

    assert code == 0
    assert artifact["schema_version"] == "qg_workflow_dry_run_gate.v1"
    assert len(artifact["module_list"]) == 2
    assert artifact["per_tier_counts"]["tier2_estimated_calls"] == 2
    assert artifact["cache_estimate"]["cold"] == 2
    assert artifact["expected_spend"]["estimated_cost_usd"] > 0
    assert artifact["exact_run_command"].startswith(".venv/bin/python scripts/audit/qg_workflow.py")
    assert "--dry-run" not in artifact["exact_run_command"]
