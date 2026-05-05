from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.agent_runtime.registry import get_agent_entry
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
    assert calls[0][2]["tool_config"]["output_format"] == "text"
    if writer == "codex-tools":
        assert calls[0][2]["tool_config"]["mcp_servers"]["sources"]["url"].endswith("/sse")
    else:
        assert calls[0][2]["tool_config"] == {"output_format": "text"}


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
