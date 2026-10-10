"""Claude weekly cap guard in the launcher (operator 2026-10-10)."""

from __future__ import annotations

import pytest

from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def _exec_line(stdout: str) -> str:
    return next(line for line in stdout.splitlines() if line.startswith("would exec "))


@pytest.mark.rules_core_absent
def test_driver_below_opus_max_keeps_opus_default() -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", "infra", env={"LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE": "50"})
    assert result.returncode == 0, result.stderr
    assert "claude-opus-5-5" in _exec_line(result.stdout)


@pytest.mark.rules_core_absent
def test_driver_over_opus_max_defaults_to_sonnet() -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", "infra", env={"LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE": "89"})
    assert result.returncode == 0, result.stderr
    assert "--model claude-sonnet-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" in result.stderr


@pytest.mark.parametrize("model", ("opus", "claude-opus-5-5[1m]"))
def test_explicit_opus_over_opus_max_is_refused(model: str) -> None:
    result = run_launcher(
        "start-claude-driver.sh", "--epic", "infra", "--model", model, env={"LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE": "85"}
    )
    assert result.returncode == 7
    assert "Opus refused" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.parametrize("pct", ("90", "97.5"))
def test_driver_at_stop_threshold_refuses_any_model(pct: str) -> None:
    for extra in ((), ("--model", "sonnet")):
        result = run_launcher(
            "start-claude-driver.sh", "--epic", "infra", *extra, env={"LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE": pct}
        )
        assert result.returncode == 7
        assert "No Claude launch until the weekly reset" in result.stderr
        assert "would exec" not in result.stdout
