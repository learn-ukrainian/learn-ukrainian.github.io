from __future__ import annotations

import importlib
import json
import signal
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.registry import get_agent_entry
from scripts.agent_runtime.result import ParseResult
from scripts.agent_runtime.telemetry import InvocationTelemetry
from scripts.build import linear_pipeline, v7_build


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
    writer: str,
    agent_name: str,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_invoker(agent: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        calls.append((agent, prompt, kwargs))
        return SimpleNamespace(response="writer output")

    response = linear_pipeline.invoke_writer(
        "Write the module.",
        writer=writer,
        cwd=tmp_path,
        invoker=fake_invoker,
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
        assert calls[0][2]["tool_config"]["mcp_servers"]["sources"]["url"].endswith("/sse")
    else:
        assert calls[0][2]["tool_config"] == {"output_format": "stream-json"}


def test_v7_build_accepts_codex_alias() -> None:
    assert "codex-tools" in v7_build.WRITER_CHOICES
    assert "codex" in v7_build.WRITER_CHOICES
    assert v7_build._normalize_writer("codex") == "codex-tools"


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
