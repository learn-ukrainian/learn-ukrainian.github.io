from __future__ import annotations

import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.audit import judge_calibration_matrix as matrix


def test_unsupported_effort_returns_n_a_not_fabricated(tmp_path: Path) -> None:
    cell = matrix.Cell(
        family="anthropic",
        model="claude-sonnet-4-6",
        harness="native_cli",
        effort="max",
        mcp_state="with_mcp",
    )
    called = False

    def runner(_cell: matrix.Cell, _prompt: str) -> matrix.HarnessCall:
        nonlocal called
        called = True
        raise AssertionError("unsupported cells must not call a harness")

    record = matrix.run_cell(out_dir=tmp_path, cell=cell, cases=[], harness_runner=runner)

    assert record["result"] == "n/a"
    assert "effort=max" in record["reason"]
    assert "scores" not in record
    assert called is False
    assert matrix.cell_path(tmp_path, cell).exists()


def test_resume_skips_existing_cells(tmp_path: Path) -> None:
    cell = matrix.Cell(
        family="openai",
        model="gpt-5.5",
        harness="native_cli",
        effort="medium",
        mcp_state="with_mcp",
    )
    existing = {"cell": asdict(cell), "scores": {"f1": 0.42}}
    matrix.write_json(matrix.cell_path(tmp_path, cell), existing)

    def runner(_cell: matrix.Cell, _prompt: str) -> matrix.HarnessCall:
        raise AssertionError("resume should skip complete cell JSON")

    records = matrix.run_cells(
        out_dir=tmp_path,
        cells=[cell],
        cases=[],
        resume=True,
        max_parallel=1,
        harness_runner=runner,
    )

    assert records == [existing]


def test_hermes_config_swap_is_atomic(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    original = "model:\n  default: gpt-5.5\nagent:\n  reasoning_effort: medium\n"
    config.write_text(original, encoding="utf-8")

    with pytest.raises(RuntimeError, match="boom"):
        with matrix.hermes_effort_swap(config, "xhigh") as previous:
            assert previous == "medium"
            assert "  reasoning_effort: xhigh\n" in config.read_text(encoding="utf-8")
            raise RuntimeError("boom")

    assert config.read_text(encoding="utf-8") == original
    assert not (tmp_path / "config.yaml.judge-calibration-backup").exists()


def test_native_codex_rejects_old_model_before_subprocess(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unapproved Codex model reached subprocess")
    monkeypatch.setattr(matrix, "run_subprocess", forbidden)
    cell = matrix.Cell("openai", "gpt-5.5", "native_cli", "medium", "with_mcp")
    with pytest.raises(ValueError, match=r"only gpt-6\.1-sol"):
        matrix.run_native_cli(cell, "prompt")


def test_native_claude_runs_without_background_work(monkeypatch):
    """The headless Claude lane carries the #9690 controls from the adapter (#9750)."""
    from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES

    calls = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="verdict", stderr="")

    monkeypatch.setenv("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0")
    monkeypatch.setattr(matrix.subprocess, "run", run)
    cell = matrix.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp")
    assert matrix.run_native_cli(cell, "prompt").ok
    ((cmd, kwargs),) = calls
    denies = cmd.index("--disallowedTools")
    assert cmd[denies + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
    assert denies < cmd.index("--") and cmd[-1] == "prompt"
    assert kwargs["env"].items() >= HEADLESS_BACKGROUND_ENV.items()


def test_native_codex_gets_no_claude_background_controls(monkeypatch):
    calls = []
    monkeypatch.setattr(matrix, "run_subprocess", lambda cmd, **kwargs: calls.append((cmd, kwargs)) or "result")
    matrix.run_native_cli(matrix.Cell("openai", "gpt-6.1-sol", "native_cli", "medium", "no_mcp"), "prompt")
    ((cmd, kwargs),) = calls
    assert "--disallowedTools" not in cmd
    assert kwargs["headless_claude"] is False
