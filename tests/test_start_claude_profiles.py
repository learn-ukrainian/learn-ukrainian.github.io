"""Native Claude adapter profile and route-isolation regression tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.test_launcher_contract import run_launcher


def _stub_claude(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "claude"
    binary.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'base=%s\\n' \"${ANTHROPIC_BASE_URL:-unset}\"\n"
        "printf 'max=%s\\n' \"${CLAUDE_CODE_MAX_CONTEXT_TOKENS:-unset}\"\n"
        "printf 'compact=%s\\n' \"${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-unset}\"\n"
        "printf 'profile=%s\\n' \"${LEARN_UKRAINIAN_PROFILE_ID:-unset}\"\n"
        "printf 'args=%s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return bin_dir


def test_claude_interactive_keeps_tui_model_unless_explicit() -> None:
    default = run_launcher("start-claude.sh")
    fable = run_launcher("start-claude.sh", "--model", "fable")
    sonnet = run_launcher("start-claude.sh", "--model", "sonnet")
    assert default.returncode == sonnet.returncode == 0
    assert fable.returncode == 0
    assert "would exec claude --model" not in default.stdout
    assert "would exec claude " in default.stdout
    assert "would exec claude --model claude-fable-5" in fable.stdout
    assert "would exec claude --model claude-sonnet-5" in sonnet.stdout


@pytest.mark.parametrize("model", ("not-certified", "gpt-5.6-sol"))
def test_claude_rejects_models_outside_native_profile(model: str) -> None:
    result = run_launcher("start-claude.sh", "--model", model)
    assert result.returncode == 2
    assert "profile" in result.stderr


def test_certified_claude_driver_models_are_revalidated() -> None:
    for model in ("opus", "fable", "sonnet"):
        result = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", model)
        assert result.returncode == 0, result.stderr
        assert "would claim lease" in result.stdout
    untrusted = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", "claude-haiku-5")
    assert untrusted.returncode == 4


def test_claude_driver_defaults_to_opus_xhigh() -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", "devops")
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model claude-opus-5" in result.stdout
    assert "--effort xhigh" in result.stdout


@pytest.mark.parametrize(
    "argv",
    (
        ("--effort", "high", "--epic", "devops"),
        ("--effort=high", "--epic", "devops"),
        ("--epic", "devops", "--effort", "high"),
    ),
)
def test_claude_driver_accepts_effort_before_or_after_epic(argv: tuple[str, ...]) -> None:
    result = run_launcher("start-claude-driver.sh", *argv)
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model claude-opus-5" in result.stdout
    assert "--effort high" in result.stdout
    assert "--effort xhigh" not in result.stdout


def test_native_claude_clears_foreign_route_and_capacity_overrides(tmp_path: Path) -> None:
    bin_dir = _stub_claude(tmp_path)
    result = run_launcher(
        "start-claude.sh",
        env={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "ANTHROPIC_BASE_URL": "https://foreign.invalid",
            "ANTHROPIC_AUTH_TOKEN": "foreign-secret",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "123",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "122",
        },
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    assert "base=unset" in result.stdout
    assert "max=unset" in result.stdout
    assert "compact=unset" in result.stdout
    assert "profile=native_claude" in result.stdout
    assert "foreign-secret" not in result.stdout + result.stderr
