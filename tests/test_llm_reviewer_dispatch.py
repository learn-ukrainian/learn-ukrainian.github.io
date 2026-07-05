from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge._opencode import OpencodeStreamParse
from scripts.audit import llm_reviewer_dispatch, qg_workflow

_DISPATCH = "scripts.audit.llm_reviewer_dispatch"


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
