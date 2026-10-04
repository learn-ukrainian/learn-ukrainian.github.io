"""Gemini adapter and driver lifecycle tests."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

DRIVER_REFUSAL = (
    "AGY/Gemini is not a planning, design or driver seat. "
    "Eligible driver seats: claude-opus-5-5 (Opus 5.5), gpt-6.1-sol (Sol 6.1); "
    "driver fallback: grok-4.7."
)


@pytest.mark.parametrize("dry_run", (True, False))
@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--epic", "devops"),
        ("--epic", "atlas", "--force"),
        ("--help",),
        ("--unknown-launcher-flag",),
        ("--unknown-launcher-flag", "--epic", "devops"),
        ("--model",),
        ("--", "--help"),
    ),
)
def test_gemini_driver_refused_before_lifecycle(arguments: tuple[str, ...], dry_run: bool) -> None:
    result = run_launcher("start-gemini-driver.sh", *arguments, dry_run=dry_run)
    assert result.returncode == 4
    assert DRIVER_REFUSAL in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("provider", "arguments"),
    (
        ("gemini", ("--epic", "devops")),
        ("gemini", ("--governor", "AUTO")),
        ("codex", ("--governor", "AUTO", "--model", "gemini-3.8-flash-high")),
        ("claude", ("--epic", "devops", "--model", "gemini:gemini-3.1-pro-high")),
    ),
)
def test_shared_core_refuses_gemini_driver_before_any_startup(
    provider: str, arguments: tuple[str, ...], tmp_path: Path
) -> None:
    core = Path(__file__).resolve().parents[1] / "scripts/lib/launcher_core.sh"
    sentinel = tmp_path / "startup-called"
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; sentinel="$2"; shift 2; '
            'launcher_resolve_roots() { touch "$sentinel"; exit 99; }; '
            'launcher_main "$@"',
            "bash",
            str(core),
            str(sentinel),
            provider,
            "driver",
            *arguments,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 4, result.stderr
    assert DRIVER_REFUSAL in result.stderr
    assert not sentinel.exists(), "refusal must precede all startup dependencies"


_DRIVE_EPIC_NEEDLE = "agents_extensions/shared/skills/drive-epic/SKILL.md"
_AGY_PROMPT_FLAG = re.compile(r"(?:^|\s)(-i|--prompt-interactive)(?:\s|$)")
_AGY_SKIP_PERMISSIONS = "--dangerously-skip-permissions"


@pytest.mark.parametrize("mode", ("interactive", "driver"))
def test_gemini_adapter_never_emits_skip_permissions(mode: str) -> None:
    """Even bypassing the entrypoint refusal cannot enable permission skipping."""
    adapter = Path(__file__).resolve().parents[1] / "scripts/launchers/gemini.sh"
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; LC_MODE="$2"; LC_MODEL=gemini-3.8-flash-high; '
            'LC_DRY_RUN=1; LC_AUTH_SOURCE=agy-managed-auth; LC_RULES_CORE=""; '
            'LC_DRIVER_PROMPT=""; LC_FORWARD_ARGS=(--sandbox read-only); '
            'launcher_print_argv() { printf "%s " "$@"; }; launcher_adapter_exec',
            "bash",
            str(adapter),
            mode,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "would exec agy --model gemini-3.8-flash-high --sandbox read-only" in result.stdout
    assert _AGY_SKIP_PERMISSIONS not in result.stdout
    assert result.stderr == ""


def _would_exec_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("would exec "):
            return line
    raise AssertionError(f"missing would-exec line:\n{stdout}")


@pytest.mark.rules_core_absent
def test_gemini_interactive_defaults_to_agy_and_rejects_epic() -> None:
    interactive = run_launcher("start-gemini.sh")
    epic = run_launcher("start-gemini.sh", "--epic", "atlas")
    assert interactive.returncode == 0, interactive.stderr
    exec_line = _would_exec_line(interactive.stdout)
    assert "would exec agy --model gemini-3.8-flash-high" in exec_line
    assert not _AGY_PROMPT_FLAG.search(exec_line), exec_line
    assert _DRIVE_EPIC_NEEDLE not in exec_line
    assert _AGY_SKIP_PERMISSIONS not in exec_line, exec_line
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("selector", ("atlas", "practice", "infra.devops", "seminars-bio"))
def test_gemini_driver_refuses_supported_selectors(selector: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", selector)
    assert result.returncode == 4, result.stderr
    assert DRIVER_REFUSAL in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("model", ("gemini-3.8-flash-high", "gemini-3.1-pro-high"))
def test_gemini_driver_refuses_formerly_certified_models(model: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", model)
    assert result.returncode == 4, result.stderr
    assert DRIVER_REFUSAL in result.stderr


def test_gemini_driver_rejects_uncertified_model_and_non_agy_harness() -> None:
    uncertified = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", "gemini-unknown")
    harness = run_launcher("start-gemini.sh", "--harness", "gemini-cli")
    assert uncertified.returncode == 4
    assert DRIVER_REFUSAL in uncertified.stderr
    assert harness.returncode == 2
    assert "only --harness agy" in harness.stderr


@pytest.mark.rules_core_absent
def test_gemini_forwards_provider_arguments_only_after_separator() -> None:
    result = run_launcher("start-gemini.sh", "--", "--sandbox", "read-only")
    assert result.returncode == 0, result.stderr
    exec_line = _would_exec_line(result.stdout)
    assert "--sandbox read-only" in exec_line
    assert not _AGY_PROMPT_FLAG.search(exec_line), exec_line
    assert _AGY_SKIP_PERMISSIONS not in exec_line, exec_line


@pytest.mark.rules_core_absent
def test_gemini_driver_refuses_content_track_before_binding() -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "hramatka")
    assert result.returncode == 4, result.stderr
    assert DRIVER_REFUSAL in result.stderr
    assert result.stdout == ""


@pytest.mark.rules_core_absent
def test_gemini_driver_refuses_forwarded_provider_args() -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--", "--sandbox", "read-only")
    assert result.returncode == 4, result.stderr
    assert DRIVER_REFUSAL in result.stderr
    assert result.stdout == ""


@pytest.mark.rules_core_absent
def test_refused_gemini_driver_preserves_interactive_and_claude_prompts() -> None:
    driver = run_launcher("start-gemini-driver.sh", "--epic", "devops")
    assert driver.returncode == 4, driver.stderr
    assert DRIVER_REFUSAL in driver.stderr
    assert driver.stdout == ""

    interactive = run_launcher("start-gemini.sh")
    assert interactive.returncode == 0, interactive.stderr
    assert "After\\ context\\ compaction" not in _would_exec_line(interactive.stdout)

    claude_driver = run_launcher("start-claude-driver.sh", "--epic", "devops")
    assert claude_driver.returncode == 0, claude_driver.stderr
    claude_exec_line = _would_exec_line(claude_driver.stdout)
    assert "After\\ context\\ compaction" not in claude_exec_line
    assert "hydration\\ permission" not in claude_exec_line
