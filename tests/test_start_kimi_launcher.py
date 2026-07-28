"""Native Kimi launcher behavior after the interactive/driver split."""

from __future__ import annotations

import pytest

from tests.test_launcher_contract import run_launcher


def test_kimi_native_is_default_and_interactive_rejects_epic() -> None:
    interactive = run_launcher("start-kimi.sh")
    epic = run_launcher("start-kimi.sh", "--epic", "devops")
    assert interactive.returncode == 0, interactive.stderr
    assert "would exec kimi --model k3" in interactive.stdout
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


@pytest.mark.parametrize("harness", ("claude", "native", "agy"))
def test_kimi_rejects_harnesses_outside_native_or_claude_code(harness: str) -> None:
    result = run_launcher("start-kimi.sh", "--harness", harness)
    assert result.returncode == 2
    assert "kimi-code|claude-code" in result.stderr


def test_kimi_native_accepts_explicit_model_and_provider_arguments() -> None:
    result = run_launcher("start-kimi.sh", "--model", "k3", "--", "--yolo")
    assert result.returncode == 0, result.stderr
    assert "would exec kimi --model k3 --yolo" in result.stdout


def test_kimi_claude_code_requires_a_kimi_credential_in_noninteractive_dry_run(tmp_path) -> None:
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={
            "HOME": str(tmp_path / "home"),
            "KIMICC_AUTH_TOKEN": "",
            "MOONSHOT_API_KEY": "",
            "KIMI_API_KEY": "",
        },
    )
    assert result.returncode == 3
    assert "no Kimi API credential" in result.stderr


def test_kimi_rejects_unknown_launcher_flag_with_usage_exit() -> None:
    result = run_launcher("start-kimi.sh", "--not-a-real-flag")
    assert result.returncode == 2
    assert "run --help" in result.stderr
