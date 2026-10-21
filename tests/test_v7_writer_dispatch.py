from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.agent_runtime import tool_config as tool_config_mod
from scripts.agent_runtime.registry import get_agent_entry
from scripts.build import linear_pipeline, v7_build

pytestmark = pytest.mark.reads_content


@pytest.fixture(autouse=True)
def _simulate_worktree_child(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(v7_build.run_archive.ENV_KEY, "test-child")
    # These tests exercise writer dispatch, not the CF-before-build gate.
    monkeypatch.setattr(v7_build, "_enforce_cf_preflight", lambda *_a, **_k: None)


def _seed_sources_mcp_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mcp_config_path = tmp_path / ".mcp.json"
    mcp_config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:8766/mcp",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    # agy resolves MCP servers from the global Antigravity config, not
    # `.mcp.json`; seed it too so agy-tools writers reach the runtime gate on
    # hosts (CI) without a real Antigravity profile.
    agy_app_data_dir = tmp_path / "agy-app-data"
    agy_app_data_dir.mkdir(exist_ok=True)
    (agy_app_data_dir / "mcp_config.json").write_text(
        json.dumps({"mcpServers": {"sources": {"httpUrl": "http://127.0.0.1:8766/mcp"}}}),
        encoding="utf-8",
    )
    tool_config_mod._load_mcp_config.cache_clear()
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", mcp_config_path)
    monkeypatch.setenv(tool_config_mod._AGY_APP_DATA_ENV, str(agy_app_data_dir))
    # Hermetic `agy mcp list`: a live HTTP catalog row, so agy-tools writers
    # pass the #7994 catalog preflight without a real agy binary.
    _stub_agy_catalog(
        monkeypatch,
        {"sources": {"type": "http", "status": "enabled", "target": "http://127.0.0.1:8766/mcp"}},
    )


def _stub_agy_catalog(monkeypatch: pytest.MonkeyPatch, servers: dict[str, dict[str, str]]) -> list[list[str]]:
    """Replace the `agy mcp` subprocess with an in-memory catalog; returns the call log."""
    calls: list[list[str]] = []

    def fake_run(args: list[str]) -> str:
        calls.append(args)
        if args[0] == "add":
            servers[args[3]] = {"type": "http", "status": "enabled", "target": args[4]}
            return ""
        rows = [f"{name}  {row['type']}  {row['status']}  {row['target']}" for name, row in servers.items()]
        return "\n".join(["NAME  TYPE  STATUS  COMMAND/URL", *rows])

    monkeypatch.setattr(tool_config_mod, "_run_agy_mcp", fake_run)
    return calls


@pytest.mark.parametrize(
    ("writer", "agent_name"),
    [
        ("claude-tools", "claude"),
        ("gemini-tools", "gemini"),
        ("codex-tools", "codex"),
        ("grok-tools", "grok"),
        ("cursor-tools", "cursor"),
        ("deepseek-tools", "deepseek"),
        ("qwen-tools", "glm"),
    ],
)
def test_v7_writer_choices_resolve_to_runtime_adapters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer: str,
    agent_name: str,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    _seed_sources_mcp_config(tmp_path, monkeypatch)

    def fake_invoker(agent: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        calls.append((agent, prompt, kwargs))
        # A -tools writer with an empty MCP trace now fails the runtime gate
        # even when the prompt carries no module ref (#7994).
        return SimpleNamespace(
            response="writer output",
            tool_calls=[{"name": "mcp__sources__verify_words", "arguments": {"words": ["ранок"]}}],
        )

    response = linear_pipeline.invoke_writer(
        "Write the module.",
        writer=writer,
        cwd=tmp_path,
        invoker=fake_invoker,
        event_sink=lambda _event, **_fields: None,
    )

    entry = get_agent_entry(agent_name)
    module_name, class_name = entry["adapter"].split(":", 1)
    adapter_module = importlib.import_module(module_name)

    assert response == "writer output"
    assert getattr(adapter_module, class_name)
    assert calls[0][0] == agent_name
    assert calls[0][1] == "Write the module."
    assert calls[0][2]["mode"] == "workspace-write"
    assert calls[0][2]["cwd"] == tmp_path
    assert calls[0][2]["entrypoint"] == "dispatch"
    assert calls[0][2]["model"] == linear_pipeline.WRITER_DEFAULTS[writer]["model"]
    assert calls[0][2]["effort"] == linear_pipeline.WRITER_DEFAULTS[writer]["effort"]
    assert calls[0][2]["tool_config"]["output_format"] == "stream-json"
    if writer == "codex-tools":
        sources_cfg = calls[0][2]["tool_config"]["mcp_servers"]["sources"]
        assert sources_cfg["url"].endswith("/mcp")
        assert "type" not in sources_cfg
    elif writer == "claude-tools":
        assert calls[0][2]["tool_config"]["mcp_config_path"] == str(
            (tmp_path / ".mcp.json").resolve()
        )
        assert calls[0][2]["tool_config"]["allowed_tools"] == "mcp__sources__*"
    elif writer in {"gemini-tools", "grok-tools", "qwen-tools"}:
        assert calls[0][2]["tool_config"]["mcp_server_names"] == ["sources"]
    elif writer == "cursor-tools":
        assert calls[0][2]["tool_config"]["cursor_mode"] == "plan"
        assert calls[0][2]["tool_config"]["cursor_workspace"] == str(tmp_path.resolve())
    else:
        assert calls[0][2]["tool_config"]["hermes_mcp_servers"] == ["sources"]


def test_v7_build_seminar_stress_path_strips_combining_acute(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("# Те́ма\n\nПро́за.\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("- lemma: сло́во\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("- title: Впра́ва\n", encoding="utf-8")

    result = v7_build._run_stress_annotation_for_level(module_dir, "folk")

    assert result["passed"] is True
    assert result["skipped"] is True
    assert result["total_removed"] == 4
    assert "\u0301" not in (module_dir / "module.md").read_text(encoding="utf-8")
    assert "\u0301" not in (module_dir / "vocabulary.yaml").read_text(encoding="utf-8")
    assert "\u0301" not in (module_dir / "activities.yaml").read_text(encoding="utf-8")


def test_v7_build_core_stress_path_keeps_existing_marks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("# Те́ма\n\nПро́за.\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("- lemma: сло́во\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("- title: Впра́ва\n", encoding="utf-8")
    calls: list[Path] = []

    def fake_run_stress_annotation(path: Path) -> dict[str, Any]:
        calls.append(path)
        return {"phase": "stress_annotation", "passed": True}

    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_stress_annotation",
        fake_run_stress_annotation,
    )

    result = v7_build._run_stress_annotation_for_level(module_dir, "a1")

    assert result["passed"] is True
    assert calls == [module_dir]
    assert "\u0301" in (module_dir / "module.md").read_text(encoding="utf-8")
    assert "\u0301" in (module_dir / "vocabulary.yaml").read_text(encoding="utf-8")
    assert "\u0301" in (module_dir / "activities.yaml").read_text(encoding="utf-8")


def test_v7_writer_trace_capture_clears_tool_theatre(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    telemetry = tmp_path / "trace.jsonl"
    writer_output = (
        '<plan_reasoning section="vocab">'
        "Verification: `verify_words` checked the candidate words."
        "</plan_reasoning>"
    )

    def fake_invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            response=writer_output,
            tool_calls=[
                {
                    "name": "mcp__sources__verify_words",
                    "arguments": {"words": ["ранок"]},
                    "output_summary": "verified",
                    "timestamp": "2026-05-07T10:00:00Z",
                }
            ],
        )

    with linear_pipeline.telemetry_event_sink(telemetry):
        response = linear_pipeline.invoke_writer(
            "Write the module.",
            writer="claude-tools",
            cwd=tmp_path,
            invoker=fake_invoker,
            module="a1/1",
            sections=["vocab"],
        )

    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]
    summary = next(event for event in events if event["event"] == "phase_writer_summary")

    assert response == writer_output
    assert summary["tool_calls_total"] == 1
    assert summary["verify_words_calls"] == 1
    assert summary["tool_theatre_violations"] == []


def test_positive_runtime_gate_fires_when_tools_writer_makes_zero_mcp_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """v7 must fail loud when a -tools writer produces 0 MCP calls (#1812)."""
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    events: list[dict[str, Any]] = []

    def fake_invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(response="writer output", tool_calls=[])

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="mcp_tools_never_invoked",
    ):
        linear_pipeline.invoke_writer(
            "Write the module.",
            writer="codex-tools",
            cwd=tmp_path,
            invoker=fake_invoker,
            module="a1/1",
            sections=["vocab"],
            event_sink=lambda event, **fields: events.append({"event": event, **fields}),
        )

    summary = next(event for event in events if event["event"] == "phase_writer_summary")
    assert summary["tool_calls_total"] == 0


UPGRADE_SHAPED_PROMPT = (
    "# V7 UPGRADE writer — preserve and expand an existing module\n\n"
    "Mode: upgrade. Base level: a1. Module: special-signs.\n"
    "Your current published unit: lesson 1.\n"
)


def _invoke_upgrade_writer(
    tmp_path: Path,
    tool_calls: list[dict[str, Any]],
    events: list[dict[str, Any]],
    **kwargs: Any,
) -> str:
    def fake_invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(response="writer output", tool_calls=tool_calls)

    return linear_pipeline.invoke_writer(
        UPGRADE_SHAPED_PROMPT,
        writer="agy-tools",
        cwd=tmp_path,
        invoker=fake_invoker,
        event_sink=lambda event, **fields: events.append({"event": event, **fields}),
        **kwargs,
    )


def test_upgrade_shaped_prompt_runs_runtime_gate_on_empty_agy_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#7994: no `- Level:` list / Contract YAML must not skip the MCP gate."""
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    events: list[dict[str, Any]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="mcp_tools_never_invoked"):
        _invoke_upgrade_writer(tmp_path, [], events)

    summary = next(event for event in events if event["event"] == "phase_writer_summary")
    assert summary["module"] == "a1/special-signs"
    assert summary["tool_calls_total"] == 0
    failure = next(event for event in events if event["event"] == "writer_failure_class")
    assert failure["failure_class"] == "mcp_tools_never_invoked"


def test_agy_writer_self_heals_dead_stdio_catalog_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#7994: a foreign `httpUrl` config lists as dead stdio; preflight re-registers HTTP."""
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    calls = _stub_agy_catalog(monkeypatch, {"sources": {"type": "stdio", "status": "enabled", "target": ""}})
    events: list[dict[str, Any]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="mcp_tools_never_invoked"):
        _invoke_upgrade_writer(tmp_path, [], events)

    assert ["add", "--type", "http", "sources", "http://127.0.0.1:8766/mcp"] in calls
    preflight = next(event for event in events if event["event"] == "agy_mcp_catalog_preflight")
    assert preflight["ok"] is True
    assert preflight["registered"] == ["sources"]


def test_agy_writer_refuses_dispatch_when_catalog_stays_dead(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#7994: never let agy write a module it cannot probe — HARD stop pre-dispatch."""
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    dead = "NAME  TYPE  STATUS  COMMAND/URL\nsources  stdio  enabled  "
    monkeypatch.setattr(tool_config_mod, "_run_agy_mcp", lambda _args: dead)
    events: list[dict[str, Any]] = []
    invoked: list[str] = []

    def fake_invoker(agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        invoked.append(agent)
        return SimpleNamespace(response="writer output", tool_calls=[])

    with pytest.raises(linear_pipeline.LinearPipelineError, match="re-run the register helper"):
        linear_pipeline.invoke_writer(
            UPGRADE_SHAPED_PROMPT,
            writer="agy-tools",
            cwd=tmp_path,
            invoker=fake_invoker,
            event_sink=lambda event, **fields: events.append({"event": event, **fields}),
        )

    assert invoked == []
    preflight = next(event for event in events if event["event"] == "agy_mcp_catalog_preflight")
    assert preflight["ok"] is False


def test_shell_vesum_trace_does_not_satisfy_mcp_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shell `python3 vesum.py`, curl and raw sqlite are not sources proofs."""
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    events: list[dict[str, Any]] = []
    shell_calls = [
        {"name": "run_shell_command", "arguments": {"command": "python3 scripts/verification/vesum.py ранок"}},
        {"name": "run_shell_command", "arguments": {"command": "curl -s localhost:8765/verify_words?w=ранок"}},
        {"name": "Bash", "arguments": {"command": "sqlite3 data/vesum.db 'select * from forms'"}},
    ]

    with pytest.raises(linear_pipeline.LinearPipelineError, match="mcp_tools_never_invoked"):
        _invoke_upgrade_writer(
            tmp_path, shell_calls, events, module="a1/special-signs", sections=["Апостроф"],
        )

    summary = next(event for event in events if event["event"] == "phase_writer_summary")
    assert summary["tool_calls_total"] == 0


def test_sources_search_text_and_verify_words_pass_never_invoked_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    events: list[dict[str, Any]] = []
    trace = tmp_path / "writer_tool_calls.json"
    calls = [
        {"name": "mcp__sources__search_text", "arguments": {"query": "апостроф після губних"}},
        {"name": "mcp__sources__verify_words", "arguments": {"words": ["м'ята", "сім'я"]}},
    ]

    response = _invoke_upgrade_writer(
        tmp_path, calls, events, module="a1/special-signs", sections=["Апостроф"],
        tool_trace_path=trace,
    )

    summary = next(event for event in events if event["event"] == "phase_writer_summary")
    assert response == "writer output"
    assert summary["tool_calls_total"] == 2
    assert summary["verify_words_calls"] == 1
    assert [call["name"] for call in json.loads(trace.read_text("utf-8"))] == [
        "mcp__sources__search_text",
        "mcp__sources__verify_words",
    ]


def test_grok_unknown_tool_telemetry_is_not_treated_as_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    events: list[dict[str, Any]] = []

    def fake_invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            response="writer output",
            tool_calls=[],
            tool_calls_total=None,
        )

    response = linear_pipeline.invoke_writer(
        "Write the module.",
        writer="grok-tools",
        cwd=tmp_path,
        invoker=fake_invoker,
        module="a1/1",
        sections=["vocab"],
        event_sink=lambda event, **fields: events.append({"event": event, **fields}),
    )

    summary = next(event for event in events if event["event"] == "phase_writer_summary")
    assert response == "writer output"
    assert summary["tool_calls_total"] is None
    assert summary["verify_words_calls"] is None
    assert summary["tool_call_telemetry_available"] is False


def test_positive_runtime_gate_does_not_fire_for_non_tools_writer() -> None:
    """Gate must only apply to *-tools writers, not legacy claude/gemini."""
    linear_pipeline._enforce_tools_writer_runtime_gate(
        writer="claude",
        module="a1/1",
        phase_writer_summary={"tool_calls_total": 0},
    )
