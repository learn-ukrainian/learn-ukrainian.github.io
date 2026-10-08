"""Gemini adapter and driver lifecycle tests."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

CERTIFIED = "certified: gemini-3.1-pro-high, gemini-3.8-flash-high"


@pytest.mark.rules_core_absent
@pytest.mark.parametrize(
    ("arguments", "model"),
    (
        ((), "gemini-3.1-pro-high"),
        (("--model", "gemini-3.1-pro-high"), "gemini-3.1-pro-high"),
        (("--model", "gemini-3.8-flash-high"), "gemini-3.8-flash-high"),
    ),
)
def test_gemini_driver_accepts_certified_models(arguments: tuple[str, ...], model: str) -> None:
    """The Gemini driver enters the shared driver path on both certified pins (dry run, no lease)."""
    result = run_launcher("start-gemini-driver.sh", "--epic", "infra", *arguments)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "LAUNCHER_DRY_RUN=1: would enter a verified per-driver memory-limited scope in lu-driver.slice" in lines
    assert any(line.startswith("launcher: would claim lease ") and "agent=gemini harness=agy" in line for line in lines)
    assert any("slot=gemini-infra" in line for line in lines)
    assert "gemini adapter: would run provider canary" in lines
    assert "launcher: would bind drive-epic after lease and provider canary" in lines
    exec_line = _would_exec_line(result.stdout)
    assert exec_line.startswith(f"would exec agy --model {model} -i ")
    assert _DRIVE_EPIC_NEEDLE in exec_line
    assert _AGY_SKIP_PERMISSIONS not in exec_line


def test_gemini_driver_default_respects_launcher_model() -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "infra", env={"LAUNCHER_MODEL": "gemini-3.8-flash-high"})
    assert result.returncode == 0, result.stderr
    assert _would_exec_line(result.stdout).startswith("would exec agy --model gemini-3.8-flash-high ")


def test_gemini_driver_help_is_usable() -> None:
    result = run_launcher("start-gemini-driver.sh", "--help")
    assert result.returncode == 0, result.stderr
    assert "Usage: ./start-gemini-driver.sh" in result.stdout
    assert "Gemini driver" in result.stdout
    assert "gemini-3.1-pro-high" in result.stdout


@pytest.mark.parametrize("dry_run", (True, False))
@pytest.mark.parametrize(
    "model",
    (
        "gemini-unknown",
        "gemini-3.8-flash-medium",
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.7-flash-high",
        "gemini-3.5-flash-high",
    ),
)
def test_gemini_driver_refuses_other_gemini_models_before_lifecycle(model: str, dry_run: bool) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", model, dry_run=dry_run)
    assert result.returncode == 4, result.stderr
    assert f"model '{model}' is not certified for the gemini driver ({CERTIFIED})." in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("dry_run", (True, False))
@pytest.mark.parametrize(
    "forwarded",
    (
        ("--model", "gemini-unknown"),
        ("--model=gemini-unknown",),
        ("--model", "gemini-3.8-flash-high"),
        ("--model=gemini-3.1-pro-high",),
        ("--sandbox", "read-only", "--model", "k3-256k"),
    ),
)
def test_gemini_driver_refuses_forwarded_model_before_lifecycle(forwarded: tuple[str, ...], dry_run: bool) -> None:
    """A provider --model after `--` would put a second model on the agy exec line."""
    result = run_launcher("start-gemini-driver.sh", "--epic", "infra", "--", *forwarded, dry_run=dry_run)
    assert result.returncode == 4, result.stderr
    flag = next(arg for arg in forwarded if arg.startswith("--model"))
    assert f"the gemini driver takes its model from the launcher --model, not from forwarded '{flag}' ({CERTIFIED})." in result.stderr
    assert result.stdout == ""
    assert "would exec" not in result.stdout


@pytest.mark.parametrize(
    ("provider", "arguments", "message"),
    (
        ("gemini", ("--epic", "devops", "--model", "gemini-unknown"), "is not certified for the gemini driver"),
        ("gemini", ("--epic", "devops", "--model", "k3-256k"), "is not certified for the gemini driver"),
        ("gemini", ("--epic", "devops", "--", "--model", "gemini-unknown"), "not from forwarded '--model'"),
        ("gemini", ("--epic", "devops", "--", "--model=glm-5"), "not from forwarded '--model=glm-5'"),
        ("codex", ("--governor", "AUTO", "--model", "gemini-3.8-flash-high"), "is a Gemini model"),
        ("claude", ("--epic", "devops", "--model", "gemini-3.1-pro-high"), "is a Gemini model"),
        ("claude", ("--epic", "devops", "--model", "gemini:gemini-3.1-pro-high"), "is a Gemini model"),
        ("grok", ("--epic", "devops", "--model", "gemini-3.8-flash-high"), "is a Gemini model"),
    ),
)
def test_shared_core_refuses_uncertified_gemini_driver_before_any_startup(
    provider: str, arguments: tuple[str, ...], message: str, tmp_path: Path
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
    assert message in result.stderr
    assert CERTIFIED in result.stderr
    assert not sentinel.exists(), "refusal must precede all startup dependencies"


_DRIVE_EPIC_NEEDLE = "agents_extensions/shared/skills/drive-epic/SKILL.md"
_AGY_PROMPT_FLAG = re.compile(r"(?:^|\s)(-i|--prompt-interactive)(?:\s|$)")
_AGY_SKIP_PERMISSIONS = "--dangerously-skip-permissions"


@pytest.mark.parametrize("mode", ("interactive", "driver"))
def test_gemini_adapter_never_emits_skip_permissions(mode: str) -> None:
    """Neither the driver nor the interactive adapter enables permission skipping."""
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
@pytest.mark.parametrize(
    ("selector", "slot"),
    (
        ("atlas", "gemini-atlas"),
        ("practice", "gemini-atlas"),
        ("infra.devops", "gemini-devops"),
        ("seminars-bio", "gemini-bio"),
        ("hramatka", "gemini-hramatka"),
    ),
)
def test_gemini_driver_accepts_registered_selectors(selector: str, slot: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert any(f"slot={slot} " in line for line in result.stdout.splitlines()), result.stdout


def test_gemini_driver_rejects_non_agy_harness() -> None:
    driver = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--harness", "gemini-cli")
    harness = run_launcher("start-gemini.sh", "--harness", "gemini-cli")
    assert driver.returncode == 2
    assert "only --harness agy" in driver.stderr
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
def test_gemini_driver_forwards_provider_args_after_binding() -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--", "--sandbox", "read-only")
    assert result.returncode == 0, result.stderr
    exec_line = _would_exec_line(result.stdout)
    assert _DRIVE_EPIC_NEEDLE in exec_line
    assert exec_line.rstrip().endswith(" --sandbox read-only")
    assert _AGY_SKIP_PERMISSIONS not in exec_line


@pytest.mark.rules_core_absent
def test_gemini_driver_preserves_interactive_and_claude_prompts() -> None:
    driver = run_launcher("start-gemini-driver.sh", "--epic", "devops")
    assert driver.returncode == 0, driver.stderr
    assert _DRIVE_EPIC_NEEDLE in _would_exec_line(driver.stdout)

    interactive = run_launcher("start-gemini.sh")
    assert interactive.returncode == 0, interactive.stderr
    interactive_line = _would_exec_line(interactive.stdout)
    assert interactive_line.startswith("would exec agy --model gemini-3.8-flash-high")
    assert _DRIVE_EPIC_NEEDLE not in interactive_line

    claude_driver = run_launcher("start-claude-driver.sh", "--epic", "devops")
    assert claude_driver.returncode == 0, claude_driver.stderr
    claude_exec_line = _would_exec_line(claude_driver.stdout)
    assert "After\\ context\\ compaction" not in claude_exec_line
    assert "hydration\\ permission" not in claude_exec_line
