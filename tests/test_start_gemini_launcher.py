"""Gemini adapter and driver lifecycle tests."""

from __future__ import annotations

import re

import pytest

from tests.test_launcher_contract import run_launcher

_DRIVE_EPIC_NEEDLE = "agents_extensions/shared/skills/drive-epic/SKILL.md"
_AGY_PROMPT_FLAG = re.compile(r"(?:^|\s)(-i|--prompt-interactive)(?:\s|$)")
_AGY_SKIP_PERMISSIONS = "--dangerously-skip-permissions"
# Dry-run uses bash %q, so the prompt may appear as Load\ agents_extensions/...
# or as a quoted string. The flag must attach to that argument.
_AGY_BOUND_PROMPT = re.compile(
    r"(?:-i|--prompt-interactive)\s+(?:Load\\ |'Load |\"Load )"
)


def _would_exec_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("would exec "):
            return line
    raise AssertionError(f"missing would-exec line:\n{stdout}")


def _assert_drive_epic_uses_agy_interactive_flag(exec_line: str) -> None:
    assert _DRIVE_EPIC_NEEDLE in exec_line, exec_line
    bound = _AGY_BOUND_PROMPT.search(exec_line)
    assert bound, f"expected -i/--prompt-interactive before drive-epic text:\n{exec_line}"
    assert bound.start() < exec_line.find(_DRIVE_EPIC_NEEDLE), exec_line
    assert exec_line.count(_DRIVE_EPIC_NEEDLE) == 1, exec_line
    # Regression: --model <id> followed by the prompt with no -i.
    assert not re.search(r"--model\s+\S+\s+Load\\?\s", exec_line), exec_line
    assert _AGY_SKIP_PERMISSIONS in exec_line, exec_line


def test_gemini_interactive_defaults_to_agy_and_rejects_epic() -> None:
    interactive = run_launcher("start-gemini.sh")
    epic = run_launcher("start-gemini.sh", "--epic", "atlas")
    assert interactive.returncode == 0, interactive.stderr
    exec_line = _would_exec_line(interactive.stdout)
    assert "would exec agy --model gemini-3.7-flash-high" in exec_line
    assert not _AGY_PROMPT_FLAG.search(exec_line), exec_line
    assert _DRIVE_EPIC_NEEDLE not in exec_line
    assert _AGY_SKIP_PERMISSIONS not in exec_line, exec_line
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


@pytest.mark.parametrize("selector", ("atlas", "practice", "infra.devops", "seminars-bio"))
def test_gemini_driver_claims_a_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would run provider canary" in result.stdout
    assert "would bind drive-epic" in result.stdout
    _assert_drive_epic_uses_agy_interactive_flag(_would_exec_line(result.stdout))


@pytest.mark.parametrize("model", ("gemini-3.6-flash-high", "gemini-3.1-pro-high"))
def test_gemini_driver_allows_only_certified_models(model: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", model)
    assert result.returncode == 0, result.stderr


def test_gemini_driver_rejects_uncertified_model_and_non_agy_harness() -> None:
    uncertified = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", "gemini-unknown")
    harness = run_launcher("start-gemini.sh", "--harness", "gemini-cli")
    assert uncertified.returncode == 4
    assert harness.returncode == 2
    assert "only --harness agy" in harness.stderr


def test_gemini_forwards_provider_arguments_only_after_separator() -> None:
    result = run_launcher("start-gemini.sh", "--", "--sandbox", "read-only")
    assert result.returncode == 0, result.stderr
    exec_line = _would_exec_line(result.stdout)
    assert "--sandbox read-only" in exec_line
    assert not _AGY_PROMPT_FLAG.search(exec_line), exec_line
    assert _AGY_SKIP_PERMISSIONS not in exec_line, exec_line


def test_gemini_driver_passes_binding_via_agy_interactive_flag() -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "hramatka")
    assert result.returncode == 0, result.stderr
    exec_line = _would_exec_line(result.stdout)
    assert "would exec agy --model" in exec_line
    _assert_drive_epic_uses_agy_interactive_flag(exec_line)


def test_gemini_driver_forwards_provider_args_without_duplicating_prompt() -> None:
    result = run_launcher(
        "start-gemini-driver.sh", "--epic", "devops", "--", "--sandbox", "read-only"
    )
    assert result.returncode == 0, result.stderr
    exec_line = _would_exec_line(result.stdout)
    assert "--sandbox read-only" in exec_line
    _assert_drive_epic_uses_agy_interactive_flag(exec_line)
