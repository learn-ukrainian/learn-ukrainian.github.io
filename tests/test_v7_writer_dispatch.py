from __future__ import annotations

import importlib
import json
import signal
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from scripts.agent_runtime import tool_config as tool_config_mod
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.registry import get_agent_entry
from scripts.agent_runtime.result import ParseResult
from scripts.agent_runtime.telemetry import InvocationTelemetry
from scripts.build import linear_pipeline, v7_build


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
    tool_config_mod._load_mcp_config.cache_clear()
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", mcp_config_path)


@pytest.mark.parametrize(
    ("writer", "agent_name"),
    [
        ("claude-tools", "claude"),
        ("gemini-tools", "gemini"),
        ("codex-tools", "codex"),
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
        return SimpleNamespace(response="writer output")

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
    else:
        assert calls[0][2]["tool_config"]["mcp_server_names"] == ["sources"]


def test_v7_build_accepts_codex_alias() -> None:
    assert "codex-tools" in v7_build.WRITER_CHOICES
    assert "codex" in v7_build.WRITER_CHOICES
    assert v7_build._normalize_writer("codex") == "codex-tools"


@pytest.mark.parametrize(
    ("writer", "expected_cwd"),
    [
        ("gemini-tools", v7_build.PROJECT_ROOT),
        ("claude-tools", None),
        ("codex-tools", None),
    ],
)
def test_v7_build_invokes_gemini_tools_from_project_root(
    tmp_path: Path,
    writer: str,
    expected_cwd: Path | None,
) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("level: a1\nslug: my-morning\nsequence: 1\n", encoding="utf-8")
    module_dir = tmp_path / "module"
    plan = {
        "level": "a1",
        "slug": "my-morning",
        "sequence": 1,
        "content_outline": [],
    }

    with (
        patch.object(v7_build.linear_pipeline, "plan_path_for", return_value=plan_path),
        patch.object(v7_build.linear_pipeline, "load_plan", return_value=plan),
        patch.object(v7_build.linear_pipeline, "validate_plan"),
        patch.object(
            v7_build.linear_pipeline,
            "build_knowledge_packet",
            return_value="knowledge packet",
        ),
        patch.object(v7_build, "_writer_prompt", return_value="writer prompt"),
        patch.object(
            v7_build.linear_pipeline,
            "invoke_writer",
            side_effect=linear_pipeline.LinearPipelineError("stop after writer invoke"),
        ) as invoke_writer,
    ):
        exit_code = v7_build.main(
            [
                "a1",
                "my-morning",
                "--writer",
                writer,
                "--out",
                str(module_dir),
            ]
        )

    assert exit_code == 1
    assert invoke_writer.call_count == 1
    assert invoke_writer.call_args.kwargs["cwd"] == (expected_cwd or module_dir)
    assert invoke_writer.call_args.kwargs["tool_trace_path"] == (
        module_dir / "writer_tool_calls.json"
    )


def test_v7_build_dry_run_telemetry_out_writes_file_not_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    telemetry = tmp_path / "out.jsonl"

    exit_code = v7_build.main(
        [
            "a1",
            "my-morning",
            "--writer",
            "codex-tools",
            "--dry-run",
            "--telemetry-out",
            str(telemetry),
        ]
    )

    captured = capsys.readouterr()
    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]

    assert exit_code == 0
    assert captured.out == ""
    assert events
    assert {event["event"] for event in events} >= {"module_start", "phase_done", "module_done"}
    assert events[-1]["event"] == "module_done"
    assert events[-1]["dry_run"] is True


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
        match="MCP_TOOLS_NEVER_INVOKED",
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


def test_positive_runtime_gate_does_not_fire_for_non_tools_writer() -> None:
    """Gate must only apply to *-tools writers, not legacy claude/gemini."""
    linear_pipeline._enforce_tools_writer_runtime_gate(
        writer="claude",
        module="a1/1",
        phase_writer_summary={"tool_calls_total": 0},
    )


def test_v7_build_writer_timeout_kills_silent_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    telemetry = tmp_path / "timeout.jsonl"
    out_dir = tmp_path / "out"
    returncode_file = tmp_path / "returncode.txt"
    from scripts.agent_runtime import runner as runtime_runner

    class SleepingAdapter:
        name = "claude"
        default_model = "fixture-model"
        supported_modes = frozenset({"workspace-write"})

        def build_invocation(self, **kwargs: Any) -> InvocationPlan:
            return InvocationPlan(
                cmd=["/bin/sh", "-c", "sleep 60"],
                cwd=Path(kwargs["cwd"]),
            )

        def parse_response(
            self,
            *,
            stdout: str,
            stderr: str,
            returncode: int,
            **_kwargs: Any,
        ) -> ParseResult:
            returncode_file.write_text(str(returncode), encoding="utf-8")
            return ParseResult(ok=False, response="", stderr_excerpt=stderr or stdout)

        def liveness_signal_paths(self, _plan: InvocationPlan) -> tuple[Path, ...]:
            return ()

    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_knowledge_packet",
        lambda **_kwargs: "knowledge packet",
    )
    monkeypatch.setattr(runtime_runner, "has_headroom", lambda *_args: (True, ""))
    monkeypatch.setattr(runtime_runner, "write_record", lambda _record: None)
    monkeypatch.setattr(
        runtime_runner,
        "resolve_invocation_telemetry",
        lambda **_kwargs: InvocationTelemetry(
            model="fixture-model",
            effort="unknown",
            cli_version="fixture",
        ),
    )
    monkeypatch.setitem(runtime_runner._ADAPTER_CACHE, "claude", SleepingAdapter())

    started = time.monotonic()
    exit_code = v7_build.main(
        [
            "a1",
            "my-morning",
            "--writer",
            "claude-tools",
            "--writer-timeout",
            "1",
            "--out",
            str(out_dir),
            "--telemetry-out",
            str(telemetry),
        ]
    )
    elapsed = time.monotonic() - started
    captured = capsys.readouterr()
    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]
    timeout_event = next(event for event in events if event["event"] == "writer_timeout")

    assert exit_code == 124
    assert elapsed < 6
    assert int(returncode_file.read_text("utf-8")) == -signal.SIGKILL
    assert "timed out in phase writer" in captured.err
    assert timeout_event["writer"] == "claude-tools"
    assert timeout_event["last_event_type"] == "phase_done"
    assert timeout_event["last_event_ts"]
    assert timeout_event["total_wall_time_s"] < 6
