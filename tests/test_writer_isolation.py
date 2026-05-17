from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.agent_runtime.runner import invoke
from scripts.audit.failure_classes import FailureClass
from scripts.build import linear_pipeline
from scripts.build.linear_pipeline import classify_writer_trace

REPO_ROOT = Path(__file__).resolve().parent.parent


def _failure_subclasses(records: list) -> set[str | None]:
    return {record.sub_class for record in records}


def test_classify_1944_incident_as_infra_context_contamination() -> None:
    trace = json.loads(
        (REPO_ROOT / "audit/incidents/2026-05-13-1944-writer-tool-calls.json").read_text(
            encoding="utf-8"
        )
    )

    records = classify_writer_trace(trace)

    assert {
        FailureClass.INFRA_CONTEXT_CONTAMINATION,
    } == {record.failure_class for record in records}
    assert {"wrong_tool_family", "handoff_or_orchestrator_file"} <= _failure_subclasses(
        records
    )
    assert all(record.severity == "TERMINAL" for record in records)
    assert all(record.terminal is True for record in records)


def test_pure_mcp_writer_passes_isolation() -> None:
    records = classify_writer_trace(
        [
            {
                "name": "mcp__sources__verify_word",
                "arguments": {"word": "кіт"},
            }
        ]
    )

    assert records == []


def test_mixed_writer_fails_isolation() -> None:
    records = classify_writer_trace(
        [
            {
                "name": "mcp__sources__verify_word",
                "arguments": {"word": "кіт"},
            },
            {
                "name": "Bash",
                "arguments": {"command": "curl http://localhost:8765/api/delegate/active"},
            },
        ]
    )

    assert "wrong_tool_family" in _failure_subclasses(records)


def test_writer_reads_handoff_fails_isolation() -> None:
    records = classify_writer_trace(
        [
            {
                "name": "Read",
                "arguments": {"file_path": "docs/session-state/current.md"},
            }
        ]
    )

    assert {"wrong_tool_family", "handoff_or_orchestrator_file"} <= _failure_subclasses(
        records
    )


def test_writer_runtime_gate_reports_contamination_and_zero_mcp() -> None:
    events: list[dict] = []

    def fake_invoker(_agent: str, _prompt: str, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            response="writer output",
            tool_calls=[
                {
                    "name": "Bash",
                    "arguments": {"command": "curl http://localhost:8765/api/delegate/active"},
                }
            ],
        )

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"infra_context_contamination:wrong_tool_family.*mcp_tools_never_invoked",
    ):
        linear_pipeline.invoke_writer(
            "Write the module.",
            writer="claude-tools",
            invoker=fake_invoker,
            module="a1/1",
            sections=["vocab"],
            event_sink=lambda event, **fields: events.append({"event": event, **fields}),
        )

    failure_events = [
        event for event in events if event["event"] == "writer_failure_class"
    ]
    assert [event["failure_class"] for event in failure_events] == [
        "infra_context_contamination",
        "mcp_tools_never_invoked",
    ]


def test_claude_subprocess_argv_contains_allowed_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.agent_runtime.adapters import claude as claude_adapter_mod

    class FakeProc:
        def __init__(self) -> None:
            self.pid = 12345
            self.stdout = io.StringIO('{"result":"ok"}\n')
            self.stderr = io.StringIO("")
            self.stdin = None
            self.returncode = 0

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

        def kill(self) -> None:
            self.returncode = -9

        def terminate(self) -> None:
            self.returncode = -15

    captured_argv: list[list[str]] = []

    def fake_popen(cmd: list[str], *_args: object, **_kwargs: object) -> FakeProc:
        captured_argv.append(cmd)
        return FakeProc()

    monkeypatch.setattr(
        claude_adapter_mod,
        "_ensure_supported_claude_cli_version",
        lambda _cmd_prefix: (2, 1, 119),
    )

    # This test mocks subprocess.Popen with a FakeProc whose
    # ``stdout`` is an in-memory ``io.StringIO``. That's a pipe-mode
    # contract — the PTY path (#2071) reads from a real master fd
    # that the fake never writes to, so we'd see response='' even
    # when the mock did the right thing. Opt out: the test is about
    # argv assembly + adapter parse, not about the spawn mechanism.
    monkeypatch.setenv("DELEGATE_DISABLE_PTY", "1")

    with patch("scripts.agent_runtime.runner.has_headroom", return_value=(True, "")), patch(
        "scripts.agent_runtime.runner.write_record"
    ), patch("scripts.agent_runtime.runner.subprocess.Popen", side_effect=fake_popen):
        result = invoke(
            "claude",
            "Write the module.",
            mode="read-only",
            cwd=tmp_path,
            tool_config={
                "cmd_prefix": ["claude"],
                "mcp_config_path": str(tmp_path / ".mcp.json"),
                "allowed_tools": "mcp__sources__*",
                "agent": "curriculum-writer",
                "output_format": "stream-json",
            },
        )

    assert result.response == "ok"
    assert captured_argv
    argv = captured_argv[0]
    assert "--agent" in argv
    assert argv[argv.index("--agent") + 1] == "curriculum-writer"
    assert "--allowedTools" in argv
    assert argv[argv.index("--allowedTools") + 1] == "mcp__sources__*"
