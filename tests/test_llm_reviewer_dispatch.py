from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge._opencode import OpencodeStreamParse, _extract_tool_event
from scripts.audit import llm_qg_store, llm_reviewer_dispatch, qg_schema, qg_workflow

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
    # #2156: seminar/factual now flows through the tooled opencode route, not agy.
    assert seminar_route is llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    assert seminar_route.route_name == "opencode_frontier"
    assert seminar_route.bridge_command[:2] == ("ask-opencode", "--model")
    assert factual_route is llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    # The old agy route stays defined for fallback/reference (not returned).
    assert llm_reviewer_dispatch.FRONTIER_FACTUAL_ROUTE.reviewer_model_id == "gemini-3.1-pro-high"


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
