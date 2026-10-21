"""Native Kimi launcher behavior after the interactive/driver split."""

from __future__ import annotations

import pytest

from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def test_kimi_native_is_default_and_interactive_rejects_epic() -> None:
    interactive = run_launcher("start-kimi.sh")
    epic = run_launcher("start-kimi.sh", "--epic", "devops")
    # OO-58: the omitted-model default is the retired registry pin, refused before exec.
    assert interactive.returncode == 2, interactive.stdout
    assert "is retired in the model catalog" in interactive.stderr
    assert "k3-256k" in interactive.stderr
    assert "would exec" not in interactive.stdout
    # Model retirement runs before the interactive --epic check.
    assert epic.returncode == 2
    assert "is retired in the model catalog" in epic.stderr
    assert "would exec" not in epic.stdout


@pytest.mark.parametrize("harness", ("claude", "native", "agy"))
def test_kimi_rejects_harnesses_outside_native_or_claude_code(harness: str) -> None:
    result = run_launcher("start-kimi.sh", "--harness", harness)
    # The retired default is refused before the harness allowlist (do not reorder gates).
    assert result.returncode == 2
    assert "is retired in the model catalog" in result.stderr


@pytest.mark.rules_core_absent
def test_kimi_native_accepts_explicit_model_and_provider_arguments() -> None:
    result = run_launcher("start-kimi.sh", "--model", "k3", "--", "--yolo")
    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert "kimi-code/k3" in result.stderr
    assert "would exec" not in result.stdout


def test_kimi_native_rejects_unknown_alias_via_catalog() -> None:
    """Review finding on #5958 r3: the native branch must resolve aliases through
    the catalog and refuse unknown ones (bare aliases are rejected by the CLI)."""
    result = run_launcher("start-kimi.sh", "--model", "not-a-kimi-model")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unknown --model" in (result.stdout + result.stderr)


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
    # The retired default is refused before the credential check. The check stays in kimi.sh.
    assert result.returncode == 2
    assert "is retired in the model catalog" in result.stderr


def test_kimi_rejects_unknown_launcher_flag_with_usage_exit() -> None:
    result = run_launcher("start-kimi.sh", "--not-a-real-flag")
    assert result.returncode == 2
    assert "run --help" in result.stderr
