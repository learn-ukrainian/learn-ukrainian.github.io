from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge._opencode import OpencodeStreamParse, _extract_tool_event
from scripts.audit import llm_qg_store, llm_reviewer, llm_reviewer_dispatch, qg_schema, qg_workflow

_DISPATCH = "scripts.audit.llm_reviewer_dispatch"


def _write_module(
    tmp_path: Path,
    *,
    level: str = "b1",
    slug: str = "sample",
    module_md: str | None = None,
) -> Path:
    module_dir = tmp_path / level / slug
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(
        module_md or "# Модуль\n\nУчні читають український текст і виконують коротке завдання.\n",
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


def _issue_ids(record: dict[str, Any]) -> list[str]:
    return [
        str(finding["issue_id"])
        for entry in record.get("dimensions", {}).values()
        if isinstance(entry, dict)
        for finding in entry.get("findings", [])
        if isinstance(finding, dict)
    ]


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


def _seminar_options() -> qg_workflow.WorkflowOptions:
    return qg_workflow.WorkflowOptions(
        enable_llm=True,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
    )


def _sources_event(
    *,
    query: str = "Веснянки",
    mode: str = "section",
    output: str = "Веснянки — це весняні обрядові пісні.",
    call_id: str = "call_1",
    tool: str = "sources_query_wikipedia",
) -> dict[str, Any]:
    return {
        "tool": tool,
        "input": {"query": query, "mode": mode},
        "status": "completed",
        "tool_call_id": call_id,
        "output": output,
    }


def _seminar_result(
    response: str,
    events: tuple[dict[str, Any], ...],
    *,
    tool_call_count: int | None = None,
) -> llm_reviewer_dispatch.DispatchResult:
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        route_name="opencode_frontier",
        tool_call_count=len(events) if tool_call_count is None else tool_call_count,
        tools_used=tuple(dict.fromkeys(str(event["tool"]) for event in events)),
        tool_events=events,
    )


def _fact_response(
    *,
    verdict: str = "CONFIRMED",
    claim: str = "Веснянки — це весняні обрядові пісні.",
    grounding_query: str = "Веснянки",
    evidence_excerpt: str = "весняні обрядові пісні",
    tool_call_id: str = "call_1",
    findings: list[dict[str, Any]] | None = None,
    extra_fact_fields: dict[str, Any] | None = None,
) -> str:
    fact_check: dict[str, Any] = {
        "claim": claim,
        "verdict": verdict,
        **(extra_fact_fields or {}),
    }
    if verdict in {"CONFIRMED", "REFUTED_BY_CONTRADICTION", "CONTESTED", "UNATTESTED_AFTER_SEARCH"}:
        fact_check["grounding"] = {
            "tool": "sources_query_wikipedia",
            "query": grounding_query,
            "evidence_excerpt": evidence_excerpt,
            "tool_call_id": tool_call_id,
        }
    return json.dumps(
        {
            "findings": findings or [],
            "fact_checks": [fact_check],
            "evidence_gaps": [],
        },
        ensure_ascii=False,
    )


def test_routing_b1_surface_uses_gemma_and_seminar_uses_tooled_opencode() -> None:
    b1_route = llm_reviewer_dispatch.route_for_review(policy_family="b1_plus")
    seminar_route = llm_reviewer_dispatch.route_for_review(policy_family="seminar")
    factual_route = llm_reviewer_dispatch.route_for_review(policy_family="b1_plus", factual_sensitive=True)

    assert b1_route.bridge_command[0] == "ask-gemma"
    assert b1_route.reviewer_model_id == "openrouter/google/gemma-4-31b-it"
    assert b1_route.requires_mcp is False
    # #2156: seminar/factual now flows through the tooled opencode route, not agy.
    assert seminar_route is llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    assert seminar_route.route_name == "opencode_frontier"
    assert seminar_route.bridge_command[:2] == ("ask-opencode", "--model")
    assert seminar_route.requires_mcp is True
    assert factual_route is llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    # The old agy route stays defined for fallback/reference (not returned).
    assert llm_reviewer_dispatch.FRONTIER_FACTUAL_ROUTE.reviewer_model_id == "gemini-3.1-pro-high"


@pytest.mark.parametrize(
    ("model_id", "expected_profile", "median_tools", "max_tools", "median_wall_s"),
    [
        ("openrouter/google/gemma-4-31b-it", "gemma-4-31b-it", 4.0, 5, 34.685),
        ("openrouter/deepseek/deepseek-v4-pro", "deepseek-v4-pro", 15.5, 17, 210.8475),
        ("openrouter/deepseek/deepseek-v4-flash", "deepseek-v4-flash", 30.0, 35, 170.207),
    ],
)
def test_estimates_attach_scorecard_measured_cost_profiles(
    model_id: str,
    expected_profile: str,
    median_tools: float,
    max_tools: int,
    median_wall_s: float,
) -> None:
    route = replace(llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE, reviewer_model_id=model_id)

    estimate = llm_reviewer_dispatch.estimate_route_cost(
        "Перевірте фактичні твердження.",
        route,
        policy_family="seminar",
    )

    assert estimate["measured_cost_profile"] == expected_profile
    assert estimate["estimated_tool_call_median"] == median_tools
    assert estimate["observed_tool_call_max"] == max_tools
    assert estimate["tool_call_anomaly_threshold"] == max_tools * 1.5
    assert estimate["estimated_wall_s_median"] == median_wall_s
    assert llm_reviewer_dispatch.SCORECARD_COST_BASIS_PATH in estimate["basis"]
    assert llm_reviewer_dispatch.SCORECARD_COST_BASIS_GENERATED_AT in estimate["basis"]
    assert estimate["estimated_cost_usd"] > 0


def test_qg_workflow_legacy_estimate_uses_scorecard_basis() -> None:
    estimate = qg_workflow.estimate_llm_cost("Перевірте фактичні твердження.", "seminar")

    assert estimate["measured_cost_profile"] == "gemma-4-31b-it"
    assert estimate["estimated_tool_call_median"] == 4.0
    assert llm_reviewer_dispatch.SCORECARD_COST_BASIS_PATH in estimate["basis"]
    assert "replace with telemetry median" not in estimate["basis"]


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


def test_frontier_opencode_route_passes_allowlist_and_hermes_still_fails() -> None:
    # The new tooled route must clear the DeepSeek/Hermes hard-ban...
    llm_reviewer_dispatch.assert_route_allowed(llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE)
    # ...while a hermes-flavored route still fails.
    hermes_route = llm_reviewer_dispatch.ReviewerRoute(
        route_name="opencode_hermes",
        bridge_command=("ask-opencode", "--model", "openrouter/hermes/x"),
        reviewer_model_id="openrouter/hermes/x",
        reviewer_family="openrouter",
        purpose="forbidden",
        input_usd_per_mtok=0.0,
        output_usd_per_mtok=0.0,
    )
    with pytest.raises(llm_reviewer_dispatch.ReviewerRouteError):
        llm_reviewer_dispatch.assert_route_allowed(hermes_route)


def test_dispatch_result_metadata_carries_tool_telemetry() -> None:
    result = llm_reviewer_dispatch.DispatchResult(
        response_text="{}",
        reviewer_model_id="m",
        reviewer_family="google",
        route_name="opencode_frontier",
        tool_call_count=7,
        tools_used=("sources_query_wikipedia", "sources_search_heritage"),
    )
    meta = result.metadata()
    assert meta["tool_call_count"] == 7
    assert meta["tools_used"] == ["sources_query_wikipedia", "sources_search_heritage"]


def test_invoke_bridge_route_opencode_populates_tool_fields() -> None:
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    parse = OpencodeStreamParse(
        text='{"findings": []}',
        tool_events=(
            {"tool": "sources_query_wikipedia", "input": {}, "status": "completed", "tool_call_id": "c1"},
            {"tool": "sources_query_wikipedia", "input": {"q": "x"}, "status": "completed", "tool_call_id": "c2"},
            {"tool": "sources_search_heritage", "input": {}, "status": "completed", "tool_call_id": "c3"},
        ),
    )
    with (
        patch(f"{_DISPATCH}._assert_sources_mcp_available"),
        patch(
            "scripts.ai_agent_bridge._opencode._invoke_opencode_detailed",
            return_value=parse,
        ) as invoke,
    ):
        result = llm_reviewer_dispatch.invoke_bridge_route(route, "prompt", "task-1")

    invoke.assert_called_once()
    assert result.response_text == '{"findings": []}'
    assert result.route_name == "opencode_frontier"
    assert result.tool_call_count == 3
    # distinct tool names, first-seen order (query_wikipedia deduped by name)
    assert result.tools_used == ("sources_query_wikipedia", "sources_search_heritage")


def test_invoke_opencode_reviewer_persists_module_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(llm_reviewer_dispatch, "PROJECT_ROOT", repo)
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    prompt = llm_reviewer.build_reviewer_prompt("folk", "vesnianky", "Passage text.")
    parse = OpencodeStreamParse(text='{"findings": []}', tool_events=())
    with (
        patch(f"{_DISPATCH}._assert_sources_mcp_available"),
        patch(
            "scripts.ai_agent_bridge._opencode._invoke_opencode_detailed",
            return_value=parse,
        ),
    ):
        llm_reviewer_dispatch._invoke_opencode_reviewer(
            prompt,
            route,
            default_timeout_s=30,
            require_mcp=True,
        )

    review_path = repo / "curriculum" / "l2-uk-en" / "folk" / "vesnianky" / "review-review.md"
    assert review_path.is_file()
    assert review_path.read_text(encoding="utf-8") == '{"findings": []}'


def test_invoke_opencode_reviewer_no_module_persistence_skips_curriculum_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(llm_reviewer_dispatch, "PROJECT_ROOT", repo)
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    prompt = llm_reviewer.build_reviewer_prompt("folk", "bakeoff-koliadky", "Passage text.")
    parse = OpencodeStreamParse(text='{"findings": []}', tool_events=())
    with (
        patch(f"{_DISPATCH}._assert_sources_mcp_available"),
        patch(
            "scripts.ai_agent_bridge._opencode._invoke_opencode_detailed",
            return_value=parse,
        ),
    ):
        llm_reviewer_dispatch._invoke_opencode_reviewer(
            prompt,
            route,
            default_timeout_s=30,
            require_mcp=True,
            no_module_persistence=True,
        )

    curriculum_root = repo / "curriculum" / "l2-uk-en"
    assert not list(curriculum_root.rglob("review-review.md"))


def test_invoke_opencode_reviewer_runs_transport_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#4642 (second leak path): the reviewer is a tool-using model with default
    write tools, and opencode resolves relative tool-writes against the subprocess
    cwd. The transport must run in an out-of-repo dir so a stray write (e.g. the
    observed status/<slug>-review.json) never lands in the checkout. This is the
    leak the no_module_persistence flag does NOT cover: that flag only gates our
    own persist_reviewer_module_review, not the model's own file writes.

    RED before the cwd firewall (transport inherits PROJECT_ROOT → stray write hits
    the checkout); GREEN after (transport runs in a throwaway out-of-repo dir).
    """
    repo = tmp_path / "repo"
    (repo / "curriculum" / "l2-uk-en" / "folk").mkdir(parents=True)
    monkeypatch.setattr(llm_reviewer_dispatch, "PROJECT_ROOT", repo)
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    prompt = llm_reviewer.build_reviewer_prompt("folk", "bakeoff-koliadky", "Passage text.")

    seen: dict[str, Any] = {}

    def fake_detailed(content: str, model: str, *, cwd: Path | None = None, **kwargs: Any) -> OpencodeStreamParse:
        # Simulate a tool-using reviewer writing a stray status file with a
        # RELATIVE path; opencode resolves it against the subprocess cwd.
        seen["cwd"] = cwd
        base = Path(cwd) if cwd is not None else repo
        stray = base / "curriculum" / "l2-uk-en" / "folk" / "status" / "bakeoff-koliadky-review.json"
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_text("{}", encoding="utf-8")
        return OpencodeStreamParse(text='{"findings": []}', tool_events=())

    with (
        patch(f"{_DISPATCH}._assert_sources_mcp_available"),
        patch(
            "scripts.ai_agent_bridge._opencode._invoke_opencode_detailed",
            side_effect=fake_detailed,
        ),
    ):
        llm_reviewer_dispatch._invoke_opencode_reviewer(
            prompt,
            route,
            default_timeout_s=30,
            require_mcp=True,
            no_module_persistence=True,
        )

    assert seen["cwd"] is not None
    reviewer_cwd = Path(seen["cwd"])
    assert reviewer_cwd != repo and repo not in reviewer_cwd.parents
    assert not list(repo.rglob("*-review.json"))
    assert not (repo / "curriculum" / "l2-uk-en" / "folk" / "status").exists()


def test_frontier_opencode_fails_fast_when_mcp_endpoint_down() -> None:
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    config = {"mcp": {"sources": {"enabled": True, "url": llm_reviewer_dispatch.SOURCES_MCP_URL}}}
    with (
        patch(f"{_DISPATCH}._load_opencode_config", return_value=config),
        patch(f"{_DISPATCH}._http_endpoint_responds", return_value=False),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode_detailed") as invoke,
    ):
        with pytest.raises(llm_reviewer_dispatch.ReviewerProviderError, match="not reachable"):
            llm_reviewer_dispatch.invoke_bridge_route(route, "prompt", "task-1")
    invoke.assert_not_called()


def test_frontier_opencode_fails_fast_when_mcp_not_configured() -> None:
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    with (
        patch(f"{_DISPATCH}._load_opencode_config", return_value={"mcp": {}}),
        patch(f"{_DISPATCH}._http_endpoint_responds", return_value=True),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode_detailed") as invoke,
    ):
        with pytest.raises(llm_reviewer_dispatch.ReviewerProviderError, match="not configured"):
            llm_reviewer_dispatch.invoke_bridge_route(route, "prompt", "task-1")
    invoke.assert_not_called()


def test_gemma_surface_route_does_not_require_mcp() -> None:
    # Surface/register review is prompt-only per design D1 — must run even when
    # the sources MCP is unconfigured/unreachable.
    route = llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE
    parse = OpencodeStreamParse(text='{"findings": []}', tool_events=())
    with (
        patch(f"{_DISPATCH}._load_opencode_config", return_value={"mcp": {}}),
        patch(f"{_DISPATCH}._http_endpoint_responds", return_value=False),
        patch(
            "scripts.ai_agent_bridge._opencode._invoke_opencode_detailed",
            return_value=parse,
        ) as invoke,
    ):
        result = llm_reviewer_dispatch.invoke_bridge_route(route, "prompt", "task-1")

    invoke.assert_called_once()
    assert result.route_name == "gemma_surface"
    assert result.tool_call_count == 0


def test_theatre_gate_retries_zero_tool_run_then_accepts_valid_retry(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    calls: list[str] = []
    valid_event = _sources_event(output="Веснянки — це весняні обрядові пісні.")

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        if len(calls) == 1:
            return _seminar_result(_fact_response(), (), tool_call_count=0)
        return _seminar_result(_fact_response(), (valid_event,))

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "ran"
    assert len(calls) == 2
    assert "Tools Required" in calls[1]


def test_theatre_gate_rejects_irrelevant_tool_only_run(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    irrelevant = _sources_event(query="борщ", output="Борщ — страва.")
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _seminar_result(_fact_response(), (irrelevant,))

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == llm_reviewer_dispatch.RETRY_EXHAUSTED
    assert tier["reason"] == llm_reviewer_dispatch.INVALID_TOOL_THEATRE
    assert record["completion_status"] == "INCOMPLETE"
    assert record["terminal_verdict"] == "PASS"
    assert calls == 2


def test_tools_used_only_theatre_fallback_requires_tool_name_relevance_for_claims() -> None:
    payload = json.loads(_fact_response())
    dispatch_meta = {
        "route_name": "opencode_frontier",
        "tool_call_count": 1,
        "tools_used": ["sources_query_wikipedia"],
    }

    violation = llm_reviewer_dispatch.tool_theatre_violation(
        policy_family="seminar",
        payload=payload,
        dispatch_meta=dispatch_meta,
    )
    no_claim_violation = llm_reviewer_dispatch.tool_theatre_violation(
        policy_family="seminar",
        payload={"findings": []},
        dispatch_meta=dispatch_meta,
    )

    assert violation == {
        "status": llm_reviewer_dispatch.INVALID_TOOL_THEATRE,
        "reason": "no_relevant_source_tool_calls",
    }
    assert no_claim_violation is None


def test_theatre_gate_retry_then_invalid_zero_tool_path(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _seminar_result(_fact_response(), (), tool_call_count=0)

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == llm_reviewer_dispatch.RETRY_EXHAUSTED
    assert record["completion_status"] == "INCOMPLETE"
    assert calls == 2


def test_deep_read_gate_retries_summary_only_unverified_then_accepts_attested(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    calls: list[str] = []
    summary_event = _sources_event(mode="summary", output="Короткий опис веснянок.")
    section_event = _sources_event(mode="section", output="Веснянки — це весняні обрядові пісні.")

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        if len(calls) == 1:
            return _seminar_result(
                _fact_response(verdict="UNVERIFIED_INSUFFICIENT_SEARCH"),
                (summary_event,),
            )
        return _seminar_result(_fact_response(), (section_event,))

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "ran"
    assert len(calls) == 2
    assert "Deep Read Required" in calls[1]


def test_budget_cap_raises_before_cache_write(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    db_path = tmp_path / "qg.db"

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        event = _sources_event()
        return _seminar_result(
            _fact_response(),
            (event,),
            tool_call_count=llm_reviewer_dispatch.MAX_REVIEWER_TOOLS + 1,
        )

    with pytest.raises(llm_reviewer_dispatch.ReviewerDispatchError, match="hard cap"):
        qg_workflow.review_module(
            _target(module_dir, level="folk"),
            options=_seminar_options(),
            reviewer=reviewer,
            store_path=db_path,
        )

    assert llm_qg_store.latest_llm_qg("folk", "vesnianky", path=db_path) is None


def test_fake_grounding_excerpt_absent_from_telemetry_drops_required_finding(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    event = _sources_event(output="Веснянки — це весняні обрядові пісні.")
    finding = {
        "issue_id": "SEMINAR_FACTUAL_DETAIL",
        "issue_class": "other",
        "dimension": "seminar_sensitivity",
        "severity": "warning",
        "excerpt": "український текст",
        "message": "Grounding excerpt is fabricated.",
        "grounding": {
            "tool": "sources_query_wikipedia",
            "query": "Веснянки",
            "evidence_excerpt": "цього фрагмента немає в telemetry",
            "tool_call_id": "call_1",
        },
    }

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _seminar_result(_fact_response(findings=[finding]), (event,))

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == llm_reviewer_dispatch.UNGROUNDED_FINDINGS
    issue_ids = _issue_ids(record)
    assert "SEMINAR_FACTUAL_DETAIL" not in issue_ids
    assert "LLM_REVIEWER_GROUNDING_GATE" in issue_ids
    assert record["verdict"] == "WARN"
    assert record["terminal_verdict"] == "PASS"


def test_fake_grounding_query_without_matching_tool_use_drops_required_finding(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    event = _sources_event(query="Веснянки", output="Веснянки — це весняні обрядові пісні.")
    finding = {
        "issue_id": "SEMINAR_FACTUAL_DETAIL",
        "issue_class": "other",
        "dimension": "seminar_sensitivity",
        "severity": "warning",
        "excerpt": "український текст",
        "message": "Grounding query is not logged.",
        "grounding": {
            "tool": "sources_query_wikipedia",
            "query": "гаї стрічками",
            "evidence_excerpt": "весняні обрядові пісні",
            "tool_call_id": "call_1",
        },
    }

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _seminar_result(_fact_response(findings=[finding]), (event,))

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == llm_reviewer_dispatch.UNGROUNDED_FINDINGS
    assert "SEMINAR_FACTUAL_DETAIL" not in _issue_ids(record)


def test_offline_vesnianky_fixture_exercises_all_fact_check_verdicts(tmp_path: Path) -> None:
    module_dir = _write_module(
        tmp_path,
        level="folk",
        slug="vesnianky",
        module_md=(
            "# Веснянки\n\n"
            "Веснянки — це весняні обрядові пісні. Їхні мелодії нібито завжди світлі й піднесені. "
            "Гаївка має спірну етимологію, а обряд зі стрічковими деревами не засвідчений.\n"
        ),
    )
    events = (
        _sources_event(
            query="Веснянки",
            output="Веснянки — це весняні обрядові пісні.",
            call_id="call_confirmed",
        ),
        _sources_event(
            query="Веснянки мелодика",
            output="Мелодія веснянок часто побудована на повторенні однієї-двох поспівок.",
            call_id="call_refuted",
        ),
        _sources_event(
            query="веснянки гаї стрічками",
            output="No results for: веснянки гаї стрічками",
            call_id="call_unattested",
            tool="sources_search_text",
        ),
        _sources_event(
            query="гаївка етимологія",
            output="ЕСУМ: походження слова неясне; подано кілька пояснень.",
            call_id="call_contested",
            tool="sources_search_esum",
        ),
        _sources_event(
            query="веснянки психологічне відновлення",
            output="No deep source found before budget expired.",
            call_id="call_unverified",
            tool="sources_search_literary",
        ),
    )
    fact_checks = [
        {
            "claim": "Веснянки — це весняні обрядові пісні.",
            "verdict": "CONFIRMED",
            "grounding": {
                "tool": "sources_query_wikipedia",
                "query": "Веснянки",
                "evidence_excerpt": "весняні обрядові пісні",
                "tool_call_id": "call_confirmed",
            },
        },
        {
            "claim": "Мелодика веснянок завжди світла й піднесена.",
            "verdict": "REFUTED_BY_CONTRADICTION",
            "grounding": {
                "tool": "sources_query_wikipedia",
                "query": "Веснянки мелодика",
                "evidence_excerpt": "повторенні однієї-двох поспівок",
                "tool_call_id": "call_refuted",
            },
        },
        {
            "claim": "У ритуалі виставляли гаї як дерева зі стрічками.",
            "verdict": "UNATTESTED_AFTER_SEARCH",
            "grounding": {
                "tool": "sources_search_text",
                "query": "веснянки гаї стрічками",
                "evidence_excerpt": "No results",
                "tool_call_id": "call_unattested",
            },
            "deep_read_attempted": True,
            "searches": [
                "sources_query_wikipedia: Веснянки",
                "sources_search_literary: веснянки гаї",
                "sources_search_text: веснянки гаї стрічками",
                "sources_search_grinchenko_1907: гаї",
            ],
        },
        {
            "claim": "Гаївка походить від слова гай.",
            "verdict": "CONTESTED",
            "grounding": {
                "tool": "sources_search_esum",
                "query": "гаївка етимологія",
                "evidence_excerpt": "походження слова неясне",
                "tool_call_id": "call_contested",
            },
        },
        {
            "claim": "Веснянки доводять психологічне відновлення людини.",
            "verdict": "UNVERIFIED_INSUFFICIENT_SEARCH",
            "budget_exhausted": True,
            "deep_read_attempted": True,
        },
    ]
    response = json.dumps({"findings": [], "fact_checks": fact_checks, "evidence_gaps": []}, ensure_ascii=False)

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _seminar_result(response, events)

    db_path = tmp_path / "qg.db"
    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=db_path,
    )

    assert _tier(record, 2)["status"] == "factual_sweep_incomplete"
    assert record["terminal_verdict"] == "FAIL"
    assert _tier(record, 2)["dispatch"]["tool_call_count"] == 5
    latest = llm_qg_store.latest_llm_qg("folk", "vesnianky", path=db_path)
    assert latest is not None
    verdicts = [row["verdict"] for row in latest.payload["fact_checks"]]
    assert verdicts == [
        "CONFIRMED",
        "REFUTED_BY_CONTRADICTION",
        "UNATTESTED_AFTER_SEARCH",
        "CONTESTED",
        "UNVERIFIED_INSUFFICIENT_SEARCH",
    ]


def test_tool_call_anomaly_is_soft_telemetry_warning(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    event = _sources_event(output="Веснянки — це весняні обрядові пісні.")

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _seminar_result(_fact_response(), (event,), tool_call_count=13)

    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=_seminar_options(),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == "ran"
    warning = tier["dispatch"]["telemetry_warning"]
    assert warning["kind"] == "tool_call_anomaly"
    assert warning["severity"] == "warning"
    assert warning["observed_tool_call_count"] == 13
    assert warning["observed_tool_call_max"] == 5
    assert warning["measured_cost_profile"] == "gemma-4-31b-it"
    assert record["completion_status"] == "COMPLETE"


def test_http_endpoint_responds_true_on_streaming_timeout() -> None:
    # curl on a streaming MCP endpoint exits 28 but still emits %{http_code}=200;
    # liveness must key on the code, not curl's exit status.
    class _Proc:
        stdout = "200"

    with (
        patch(f"{_DISPATCH}.shutil.which", return_value="/usr/bin/curl"),
        patch(f"{_DISPATCH}.subprocess.run", return_value=_Proc()),
    ):
        assert llm_reviewer_dispatch._http_endpoint_responds("http://127.0.0.1:8766/mcp") is True

    class _Down:
        stdout = "000"

    with (
        patch(f"{_DISPATCH}.shutil.which", return_value="/usr/bin/curl"),
        patch(f"{_DISPATCH}.subprocess.run", return_value=_Down()),
    ):
        assert llm_reviewer_dispatch._http_endpoint_responds("http://127.0.0.1:8766/mcp") is False


def test_loads_jsonc_strips_comments_and_trailing_commas() -> None:
    cfg = llm_reviewer_dispatch._loads_jsonc(
        """
        {
          // sources MCP, url has // inside a string and must survive
          "mcp": {
            "sources": {"url": "http://127.0.0.1:8766/mcp", "enabled": true},
          },
        }
        """
    )
    assert cfg["mcp"]["sources"]["url"] == "http://127.0.0.1:8766/mcp"
    assert cfg["mcp"]["sources"]["enabled"] is True


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


def test_live_seminar_route_hard_fails_if_mcp_not_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_dir = _write_module(tmp_path, level="folk", slug="vesnianky")
    prompt_only_route = replace(llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE, requires_mcp=False)
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _seminar_result(_fact_response(), (_sources_event(),))

    monkeypatch.setattr(
        llm_reviewer_dispatch,
        "route_for_review",
        lambda **_kwargs: prompt_only_route,
    )
    record = qg_workflow.review_module(
        _target(module_dir, level="folk"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            author_family="openai",
            max_cost_usd=1.0,
            daily_spend_path=tmp_path / "spend.jsonl",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == "provider_error"
    assert tier["reason"] == "disallowed_reviewer_route"
    assert "sources MCP" in tier["message"]
    assert record["workflow_verdict"] == "INCOMPLETE"
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


def test_load_opencode_config_merges_documented_sources(tmp_path, monkeypatch) -> None:
    """codex review of #4401 (High): the gate must read the EFFECTIVE config.

    opencode merges global -> $OPENCODE_CONFIG -> project -> inline content;
    reading only the first global file falsely blocks (sources wired in a
    higher-precedence source) or falsely passes (higher-precedence disable).
    """
    home = tmp_path / "home"
    (home / ".config" / "opencode").mkdir(parents=True)
    (home / ".config" / "opencode" / "opencode.jsonc").write_text(
        '{"mcp": {"sources": {"enabled": true, "url": "http://global/mcp"}}, "theme": "g"}',
        encoding="utf-8",
    )
    env_cfg = tmp_path / "env-config.json"
    env_cfg.write_text('{"mcp": {"lightpanda": {"enabled": true}}}', encoding="utf-8")
    project = tmp_path / "proj"
    project.mkdir()
    (project / "opencode.json").write_text(
        '{"mcp": {"sources": {"enabled": true, "url": "http://project/mcp"}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setenv("OPENCODE_CONFIG", str(env_cfg))
    monkeypatch.delenv("OPENCODE_CONFIG_CONTENT", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.chdir(project)

    merged = llm_reviewer_dispatch._load_opencode_config()
    # project sources overrides global; env config's other mcp entries survive
    assert merged["mcp"]["sources"]["url"] == "http://project/mcp"
    assert merged["mcp"]["lightpanda"] == {"enabled": True}
    assert merged["theme"] == "g"

    # inline content is the TOP source — a disable there must win (false-pass guard)
    monkeypatch.setenv(
        "OPENCODE_CONFIG_CONTENT", '{"mcp": {"sources": {"enabled": false}}}'
    )
    merged = llm_reviewer_dispatch._load_opencode_config()
    assert merged["mcp"]["sources"] == {"enabled": False}


def test_project_config_discovered_walking_up_to_repo_root(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / ".config").mkdir(parents=True)
    repo = tmp_path / "repo"
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()
    (repo / "opencode.jsonc").write_text(
        '{"mcp": {"sources": {"enabled": true, "url": "http://repo/mcp"}}}', encoding="utf-8"
    )
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)
    monkeypatch.delenv("OPENCODE_CONFIG_CONTENT", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.chdir(nested)

    merged = llm_reviewer_dispatch._load_opencode_config()
    assert merged["mcp"]["sources"]["url"] == "http://repo/mcp"


def test_grounding_matches_despite_model_invented_call_id() -> None:
    """Live «Веснянки» proof regression (2026-07-05): the transport tool_call_id
    (chatcmpl-tool-…) is never shown to the model, which invents call_0/call_1.
    Grounding validity = tool + query + excerpt ⊆ captured output; the id is
    advisory. Requiring id equality failed EVERY legitimate grounding live."""
    events = (
        {
            "tool": "sources_query_wikipedia",
            "input": {"mode": "extract", "query": "Веснянки"},
            "status": "completed",
            "tool_call_id": "chatcmpl-tool-8aa58af0f4248afc",
            "output": "# Веснянки\nВесня́нки — назва старовинних слов'янських обрядових пісень.",
        },
    )
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "назва старовинних слов'янських обрядових пісень",
        "tool_call_id": "call_0",  # model-invented — must NOT invalidate
    }
    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is True

    # fabrication still caught: excerpt absent from every captured output
    fabricated = dict(grounding, evidence_excerpt="гаї — це прикрашені стрічками дерева")
    assert llm_reviewer_dispatch._grounding_matches_events(fabricated, events) is False
    # and a query never actually made still fails
    ghost_query = dict(grounding, query="мелодика веснянок")
    assert llm_reviewer_dispatch._grounding_matches_events(ghost_query, events) is False


def test_grounding_matches_containment_query() -> None:
    # 1. POSITIVE: Cited query contains the event query candidate
    events = (
        {
            "tool": "sources_query_wikipedia",
            "input": {"mode": "section", "query": "Сковорода Григорій Савич"},
            "status": "completed",
            "tool_call_id": "call_1",
            "output": "Григорій Савич Сковорода був видатним українським філософом.",
        },
    )
    # The model cites a decorated/expanded query, but it contains the event query "Сковорода Григорій Савич"
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Сковорода Григорій Савич mode=section 3 (Придворна капела)",
        "evidence_excerpt": "Григорій Савич Сковорода був видатним українським філософом",
        "tool_call_id": "call_1",
    }
    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is True

    # 2. NEGATIVE (anti-fabrication):
    # - Cited query does NOT contain the event query candidate
    unrelated_cited = dict(grounding, query="Шевченко Тарас mode=section 3")
    assert llm_reviewer_dispatch._grounding_matches_events(unrelated_cited, events) is False

    # - Excerpt is NOT in the matching event's output
    fabricated_excerpt = dict(grounding, evidence_excerpt="Він народився у Києві")
    assert llm_reviewer_dispatch._grounding_matches_events(fabricated_excerpt, events) is False

    # 3. NON-REGRESSION:
    # - Exact-equal query still matches
    exact_match = dict(grounding, query="Сковорода Григорій Савич")
    assert llm_reviewer_dispatch._grounding_matches_events(exact_match, events) is True

    # - Unrelated query still rejected
    unrelated_query = dict(grounding, query="Котляревський Іван Петрович")
    assert llm_reviewer_dispatch._grounding_matches_events(unrelated_query, events) is False

    # 4. MIN-LENGTH GUARD:
    # If the candidate query in the event input is < 3 characters (trivially short), it must not match.
    short_events = (
        {
            "tool": "sources_query_wikipedia",
            "input": {"mode": "section", "query": "Ск"},
            "status": "completed",
            "tool_call_id": "call_1",
            "output": "Григорій Савич Сковорода був видатним українським філософом.",
        },
    )
    # Even if "Сковорода" contains "Ск", the candidate query is < 3 chars so it should not match
    short_grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Сковорода Григорій Савич",
        "evidence_excerpt": "Григорій Савич Сковорода був видатним українським філософом",
        "tool_call_id": "call_1",
    }
    assert llm_reviewer_dispatch._grounding_matches_events(short_grounding, short_events) is False

    # 5. EMBEDDED-SUBSTRING GUARD (codex review): a 3+ char real event query embedded
    # MID-STRING in an unrelated cited query must NOT match. Prefix-boundary containment
    # (not arbitrary `cand in cited`) is what closes this hole.
    embed_events = (
        {
            "tool": "sources_query_wikipedia",
            "input": {"query": "гай"},
            "status": "completed",
            "tool_call_id": "call_e",
            "output": "Священний гай був місцем поклоніння давніх слов'ян.",
        },
    )
    embed_grounding = {
        "tool": "sources_query_wikipedia",
        "query": "старий гай навколо села",  # real query "гай" embedded mid-string, NOT a prefix
        "evidence_excerpt": "Священний гай був місцем поклоніння",
        "tool_call_id": "call_e",
    }
    assert llm_reviewer_dispatch._grounding_matches_events(embed_grounding, embed_events) is False


@pytest.mark.parametrize("ellipsis", ["…", "..."])
def test_grounding_matches_ellipsized_excerpt_segments_in_order(ellipsis: str) -> None:
    events = (
        _sources_event(
            output=(
                "# Веснянки\n"
                "Весня́нки — назва старовинних слов'янських обрядових пісень, "
                "що виконуються навесні."
            ),
        ),
    )
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": f"Веснянки {ellipsis} слов'янських обрядових пісень",
        "tool_call_id": "model-invented",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is True


def _ast_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _ast_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def test_no_production_entrypoint_constructs_bare_bakeoff_arm() -> None:
    root = Path(__file__).resolve().parents[1]
    bare_entrypoints = {
        "BARE_ARM",
        "BOTH_ARM",
        "build_bare_factcheck_prompt",
        "invoke_bakeoff_route_bare",
        "run_one_bare",
    }
    violations: list[str] = []
    source_paths = [
        *sorted((root / "scripts" / "build").rglob("*.py")),
        *sorted((root / "scripts" / "audit").rglob("*.py")),
    ]
    for path in source_paths:
        if path.name == "qg_bakeoff.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in {
                "scripts.audit.qg_bakeoff",
                "audit.qg_bakeoff",
                "qg_bakeoff",
            }:
                for alias in node.names:
                    if alias.name in bare_entrypoints:
                        violations.append(f"{path.relative_to(root)} imports {alias.name}")
            elif isinstance(node, ast.Call):
                call_name = _ast_call_name(node.func)
                if call_name in bare_entrypoints:
                    violations.append(f"{path.relative_to(root)} calls {call_name}")
                for keyword in node.keywords:
                    if keyword.arg == "arm" and _ast_string(keyword.value) in {"bare", "both"}:
                        violations.append(f"{path.relative_to(root)} passes arm={_ast_string(keyword.value)!r}")

    assert violations == []


def test_grounding_rejects_out_of_order_ellipsized_segments() -> None:
    events = (
        _sources_event(
            output="Веснянки — назва старовинних слов'янських обрядових пісень.",
        ),
    )
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "слов'янських обрядових пісень … Веснянки",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is False


def test_grounding_rejects_ellipsized_segments_spanning_events() -> None:
    events = (
        _sources_event(output="Веснянки — назва старовинних пісень.", call_id="call_1"),
        _sources_event(output="Обрядових пісень багато виконують навесні.", call_id="call_2"),
    )
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "Веснянки … обрядових пісень",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is False


def test_grounding_normalizes_nfkc_whitespace_case_and_ukrainian_stress_only() -> None:
    events = (_sources_event(output="Весня́нки\u00a0— НАЗВА старовинних пісень."),)
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "веснянки — назва",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is True
    assert llm_reviewer_dispatch._normalize_for_match("й ї") == "й ї"


def test_grounding_rejects_fabricated_segment_among_real_segments() -> None:
    events = (_sources_event(output="Веснянки — назва старовинних обрядових пісень."),)
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "Веснянки … стрічкові гаї … обрядових пісень",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is False


def test_grounding_rejects_ellipsized_excerpt_with_only_short_glue_segments() -> None:
    events = (_sources_event(output="а в і"),)
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "а…в…і",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is False


def test_grounding_matches_dict_shaped_event_output_after_stringify() -> None:
    events = (
        _sources_event(
            output={
                "title": "Веснянки",
                "body": "Веснянки — це весняні обрядові пісні.",
            },
        ),
    )
    grounding = {
        "tool": "sources_query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "весняні обрядові пісні",
        "tool_call_id": "call_1",
    }

    assert llm_reviewer_dispatch._grounding_matches_events(grounding, events) is True


def test_extract_tool_event_preserves_dict_output_as_json_text() -> None:
    extracted = _extract_tool_event(
        {
            "type": "tool_use",
            "part": {
                "tool": "sources_query_wikipedia",
                "callID": "call_1",
                "state": {
                    "status": "completed",
                    "input": {"query": "Веснянки", "mode": "summary"},
                    "output": {"title": "Веснянки", "body": ["весняні обрядові пісні"]},
                },
            },
        }
    )

    assert extracted is not None
    assert isinstance(extracted["output"], str)
    assert json.loads(extracted["output"]) == {"title": "Веснянки", "body": ["весняні обрядові пісні"]}


def test_positive_verdict_summary_only_grounding_forces_deep_read_retry() -> None:
    payload = json.loads(_fact_response())
    summary_event = _sources_event(mode="summary", output="Веснянки — це весняні обрядові пісні.")

    assert llm_reviewer_dispatch.deep_read_required(payload, {"tool_events": [summary_event]}) is True

    payload["fact_checks"][0]["deep_read_attempted"] = True
    assert llm_reviewer_dispatch.deep_read_required(payload, {"tool_events": [summary_event]}) is False


def test_summary_only_positive_verdict_downgrades_after_deep_read_attempt() -> None:
    payload = json.loads(_fact_response(extra_fact_fields={"deep_read_attempted": True}))
    summary_event = _sources_event(mode="summary", output="Веснянки — це весняні обрядові пісні.")

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [summary_event]},
        policy_family="seminar",
    )

    fact_check = result.payload["fact_checks"][0]
    assert fact_check["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert fact_check["original_verdict"] == "CONFIRMED"
    assert fact_check["admissibility_downgraded"] is True
    assert result.inadmissible_positive_verdicts == 1
    assert result.invalid_fact_checks == 0
    assert llm_reviewer_dispatch.factual_sweep_incomplete(
        result.payload,
        policy_family="seminar",
        invalid_fact_checks=result.invalid_fact_checks,
    )
    qg_schema.validate_reviewer_payload(result.payload, "seminar")


def test_deep_read_wiki_positive_verdict_remains_admissible() -> None:
    payload = json.loads(_fact_response(extra_fact_fields={"deep_read_attempted": True}))
    section_event = _sources_event(mode="section", output="Веснянки — це весняні обрядові пісні.")

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [section_event]},
        policy_family="seminar",
    )

    assert result.payload["fact_checks"][0]["verdict"] == "CONFIRMED"
    assert result.inadmissible_positive_verdicts == 0


def test_positive_verdict_matching_summary_and_deep_events_is_admissible() -> None:
    payload = json.loads(_fact_response(extra_fact_fields={"deep_read_attempted": True}))
    summary_event = _sources_event(mode="summary", output="Веснянки — це весняні обрядові пісні.")
    section_event = _sources_event(
        mode="section",
        output="У розділі сказано: Веснянки — це весняні обрядові пісні.",
        call_id="call_2",
    )

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [summary_event, section_event]},
        policy_family="seminar",
    )

    assert result.payload["fact_checks"][0]["verdict"] == "CONFIRMED"
    assert result.inadmissible_positive_verdicts == 0


def test_neighboring_deep_read_event_does_not_rescue_summary_grounded_verdict() -> None:
    payload = json.loads(_fact_response(extra_fact_fields={"deep_read_attempted": True}))
    summary_event = _sources_event(mode="summary", output="Веснянки — це весняні обрядові пісні.")
    other_section = _sources_event(
        query="Гаївка",
        mode="section",
        output="Гаївка має окрему історію опису.",
        call_id="call_2",
    )

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [summary_event, other_section]},
        policy_family="seminar",
    )

    assert result.payload["fact_checks"][0]["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert result.inadmissible_positive_verdicts == 1


def test_non_wiki_positive_grounding_is_not_summary_admissibility_failure() -> None:
    payload = json.loads(
        _fact_response(
            grounding_query="Веснянки література",
            evidence_excerpt="весняні обрядові пісні",
            extra_fact_fields={"deep_read_attempted": True},
        )
    )
    payload["fact_checks"][0]["grounding"]["tool"] = "sources_search_literary"
    literary_event = _sources_event(
        query="Веснянки література",
        output="Веснянки — це весняні обрядові пісні.",
        tool="sources_search_literary",
    )

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [literary_event]},
        policy_family="seminar",
    )

    assert result.payload["fact_checks"][0]["verdict"] == "CONFIRMED"
    assert result.inadmissible_positive_verdicts == 0


def test_refuted_by_contradiction_summary_only_grounding_downgrades() -> None:
    payload = json.loads(
        _fact_response(
            verdict="REFUTED_BY_CONTRADICTION",
            claim="Мелодика веснянок завжди світла й піднесена.",
            evidence_excerpt="повторенні однієї-двох поспівок",
            extra_fact_fields={"deep_read_attempted": True},
        )
    )
    summary_event = _sources_event(
        mode="summary",
        output="Мелодія веснянок часто побудована на повторенні однієї-двох поспівок.",
    )

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [summary_event]},
        policy_family="seminar",
    )

    assert result.payload["fact_checks"][0]["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert result.payload["fact_checks"][0]["original_verdict"] == "REFUTED_BY_CONTRADICTION"
    assert result.inadmissible_positive_verdicts == 1


@pytest.mark.parametrize("shallow_mode", ["search", "", "snippet"])
def test_non_deep_wiki_mode_positive_verdict_is_inadmissible(shallow_mode: str) -> None:
    """Missing/unknown wiki modes must fail CLOSED, not certify (cursor review of #4429).

    ``all(mode == "summary")`` failed open: one matching wiki event with
    ``mode=""``/``"search"`` let a shallow-grounded CONFIRMED through both the
    retry and the downgrade. Shallow = wiki-only matches with NO deep-read mode.
    """
    payload = json.loads(_fact_response())
    shallow_event = _sources_event(mode=shallow_mode, output="Веснянки — це весняні обрядові пісні.")

    assert llm_reviewer_dispatch.deep_read_required(payload, {"tool_events": [shallow_event]}) is True

    attempted = json.loads(_fact_response(extra_fact_fields={"deep_read_attempted": True}))
    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        attempted,
        {"tool_events": [shallow_event]},
        policy_family="seminar",
    )
    fact_check = result.payload["fact_checks"][0]
    assert fact_check["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert fact_check["original_verdict"] == "CONFIRMED"
    assert result.inadmissible_positive_verdicts == 1


def test_contested_summary_only_grounding_downgrades() -> None:
    payload = json.loads(
        _fact_response(
            verdict="CONTESTED",
            extra_fact_fields={"deep_read_attempted": True},
        )
    )
    summary_event = _sources_event(mode="summary", output="Веснянки — це весняні обрядові пісні.")

    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [summary_event]},
        policy_family="seminar",
    )

    fact_check = result.payload["fact_checks"][0]
    assert fact_check["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert fact_check["original_verdict"] == "CONTESTED"
    assert result.inadmissible_positive_verdicts == 1


def test_ellipsized_evidence_mass_boundary_twelve_nonspace_chars() -> None:
    """Retained-segment nonspace mass: 11 chars fails closed, 12 passes."""
    output = "абвгд еєжзиі клмнопрст"
    # Two retained segments (5 + 7 = 12 nonspace chars) in order → match.
    assert llm_reviewer_dispatch._output_contains_excerpt(output, "абвгд…клмнопр") is True
    # 5 + 6 = 11 nonspace chars → evidence-mass guard fails closed.
    assert llm_reviewer_dispatch._output_contains_excerpt(output, "абвгд…клмноп") is False


def test_canonical_tool_name_handles_all_transport_forms() -> None:
    """Regression for dot-form MCP tool names (gpt-5.5 / codex QG) vs __ / bare.

    All of these must canonicalize to the bare tool name so grounding gate admits
    legitimate citations (previously dot-form `sources.query_*` produced 0 confirms
    even when excerpt was present in captured output).
    """
    canonical = llm_reviewer_dispatch._canonical_tool_name

    # The six primary forms cited in the bug
    assert canonical("mcp__sources__query_wikipedia") == "query_wikipedia"
    assert canonical("mcp__sources.query_wikipedia") == "query_wikipedia"
    assert canonical("sources_query_wikipedia") == "query_wikipedia"
    assert canonical("sources__query_wikipedia") == "query_wikipedia"
    assert canonical("mcp__query_wikipedia") == "query_wikipedia"
    assert canonical("query_wikipedia") == "query_wikipedia"

    # Tool names containing underscores + digits must preserve them (no generic _ strip)
    assert canonical("mcp__sources.search_grinchenko_1907") == "search_grinchenko_1907"
    assert canonical("sources_search_grinchenko_1907") == "search_grinchenko_1907"
    assert canonical("mcp__sources__search_grinchenko_1907") == "search_grinchenko_1907"

    # Case folding still applies
    assert canonical("MCP__Sources.Query_Wikipedia") == "query_wikipedia"

    # Edge cases
    assert canonical(None) == ""
    assert canonical("") == ""
    assert canonical("   ") == ""
    assert canonical("unknown.tool") == "tool"

    # Malformed dot forms MUST fail closed, not collapse to "" (an empty canonical
    # would be treated as "no tool" by the gate and wildcard past the tool filter).
    # They are left non-empty so they simply never match a real event.
    assert canonical("mcp__sources.") == "sources."
    assert canonical(".query_wikipedia") == ".query_wikipedia"
    assert canonical("mcp__sources.") != ""
    assert canonical(".query_wikipedia") != ""


def test_grounding_matches_events_across_dot_and_underscore_tool_forms() -> None:
    """End-to-end match: grounding with dot-form tool name must match __-form event.

    This was False before the canonicalizer fix → every codex/gpt dot-cited grounding
    was rejected even when the excerpt was verifiably in the captured tool output.
    Example from koliadky QG sweep: 0/14 → 14/14 after fix.
    """
    # Event captured with double-underscore form (typical of adapter/runtime)
    event = _sources_event(
        tool="mcp__sources__query_wikipedia",
        query="koliadky",
        output=(
            "Колядки — традиційні українські обрядові пісні, "
            "що виконуються на Різдво та в інші зимові свята. "
            "Містять побажання щастя, здоров'я та доброго врожаю."
        ),
    )

    # Grounding emitted by model using dot form (gpt-5.5 / recent codex)
    grounding = {
        "tool": "mcp__sources.query_wikipedia",
        "query": "koliadky",
        "evidence_excerpt": "Колядки — традиційні українські обрядові пісні, що виконуються на Різдво",
        "tool_call_id": "call_0",
    }
    assert llm_reviewer_dispatch._grounding_matches_events(grounding, (event,)) is True

    # Mixed other dot/underscore forms also match the same event
    for variant in ("sources.query_wikipedia", "sources__query_wikipedia", "query_wikipedia"):
        g = dict(grounding, tool=variant)
        assert llm_reviewer_dispatch._grounding_matches_events(g, (event,)) is True, variant

    # Wrong tool (different canonical name) must not match even if query/excerpt overlap
    bad = dict(grounding, tool="mcp__sources.search_grinchenko_1907")
    assert llm_reviewer_dispatch._grounding_matches_events(bad, (event,)) is False

    # Malformed dot-form tool names must NOT wildcard past the tool filter
    # (regression: an empty canonical would bypass `if tool and ...` and match
    # any event with the same query/excerpt). These must fail closed.
    for malformed in ("mcp__sources.", "sources.", ".query_wikipedia"):
        g = dict(grounding, tool=malformed)
        assert llm_reviewer_dispatch._grounding_matches_events(g, (event,)) is False, malformed


# --- Guard 3 abstain-recovery (task guard3-abstain; fleet-reviewed codex/agy/cursor) ---
# The v2 gate ABSTAINS (anchored=False) when an excerpt is verbatim-present in >=2 DIFFERENT
# tool outputs — provenance is satisfied, source is ambiguous. Enforcement previously mapped that
# to a hard reject, over-rejecting ~117 gold-true groundings. Enforcement now recovers only the
# EXACT-match (sim==1.0) multi-output abstains; fuzzy near-tie abstains stay fail-closed, and the
# hardened gate is untouched (its fail-closed probes still assert on grounding_gate_v2 directly).


def _stub_anchor(monkeypatch, *, anchored: bool, abstained: bool, similarity: float) -> None:
    from scripts.audit import grounding_gate_v2

    def fake(grounding, events, *, tau=None):
        return grounding_gate_v2.AnchorResult(
            anchored=anchored,
            abstained=abstained,
            similarity=similarity,
            source_index=None,
            span=None,
            reason="stub",
        )

    monkeypatch.setattr(grounding_gate_v2, "anchor_evidence_to_events", fake)


def _enforce_v2(payload):
    return llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload,
        {"tool_events": [_sources_event()]},
        policy_family="seminar",
        gate_version="v2",
    )


def test_v2_enforcement_recovers_exact_multi_output_abstain(monkeypatch) -> None:
    _stub_anchor(monkeypatch, anchored=False, abstained=True, similarity=1.0)
    result = _enforce_v2(json.loads(_fact_response()))
    assert result.invalid_fact_checks == 0  # recovered as provenance-passed, not dropped
    fc = result.payload["fact_checks"][0]
    assert fc["anchor_recovered_ambiguous"] is True
    assert fc["anchor_abstained"] is True


def test_v2_enforcement_fuzzy_abstain_stays_fail_closed(monkeypatch) -> None:
    _stub_anchor(monkeypatch, anchored=False, abstained=True, similarity=0.9)
    result = _enforce_v2(json.loads(_fact_response()))
    assert result.invalid_fact_checks == 1  # below the exact-match recovery threshold → rejected
    assert result.payload["fact_checks"][0]["anchor_recovered_ambiguous"] is False


def test_v2_enforcement_non_anchor_non_abstain_rejected(monkeypatch) -> None:
    _stub_anchor(monkeypatch, anchored=False, abstained=False, similarity=0.5)
    result = _enforce_v2(json.loads(_fact_response()))
    assert result.invalid_fact_checks == 1  # ordinary below-tau miss → rejected (fabrication path intact)


def test_v2_enforcement_real_multi_output_verbatim_recovered() -> None:
    # Real gate: excerpt with a salient token, verbatim in TWO different outputs → abstain → recovered.
    excerpt = "Сковорода народився у 1722 році"
    payload = json.loads(_fact_response(evidence_excerpt=excerpt, grounding_query="Сковорода"))
    events = [
        _sources_event(
            query="Сковорода",
            output="Григорій Сковорода народився у 1722 році. Він був філософом.",
            call_id="call_1",
        ),
        _sources_event(
            query="Сковорода",
            output="Сковорода народився у 1722 році згідно з джерелами.",
            call_id="call_2",
        ),
    ]
    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload, {"tool_events": events}, policy_family="seminar", gate_version="v2"
    )
    fc = result.payload["fact_checks"][0]
    assert result.invalid_fact_checks == 0
    assert fc["anchor_abstained"] is True
    assert fc["anchor_recovered_ambiguous"] is True


def test_v2_enforcement_real_number_swap_still_rejected() -> None:
    # Fabrication defense must be intact: a swapped year is not verbatim-present → digit_not_aligned reject.
    payload = json.loads(
        _fact_response(evidence_excerpt="Сковорода народився у 1900 році", grounding_query="Сковорода")
    )
    events = [_sources_event(query="Сковорода", output="Сковорода народився у 1722 році.", call_id="call_1")]
    result = llm_reviewer_dispatch.enforce_grounding_against_tool_events(
        payload, {"tool_events": events}, policy_family="seminar", gate_version="v2"
    )
    assert result.invalid_fact_checks == 1
    assert result.payload["fact_checks"][0]["anchor_recovered_ambiguous"] is False
