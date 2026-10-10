"""Claude weekly cap guard in the launcher (operator 2026-10-10)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.lib import claude_weekly_used
from tests.rules_core_view import (
    _LOADER_STUB,
    _build_view,
    rules_core_absent_when_marked,  # noqa: F401  (autouse: serves @rules_core_absent)
)
from tests.test_launcher_contract import REPO, run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


@pytest.fixture
def launch_with_usage(tmp_path: Path, request: pytest.FixtureRequest):
    """Inject telemetry in a fixture reader, without a production bypass."""
    reader = tmp_path / "weekly_reader.py"
    overrides = {("scripts", "lib", "claude_weekly_used.py"): reader}
    if request.node.get_closest_marker("rules_core_absent") is not None:
        overrides[("scripts", "lib", "rules_core.sh")] = _LOADER_STUB.format(
            real=REPO / "scripts/lib/rules_core.sh"
        )
    checkout = _build_view(tmp_path / "checkout", overrides)

    def launch(pct: str, *args: str, name: str = "start-claude-driver.sh", env=None):
        reader.write_text(f"print({pct!r})\n", encoding="utf-8")
        return run_launcher(name, *args, env=env, root=checkout)

    return launch


def _exec_line(stdout: str) -> str:
    return next(line for line in stdout.splitlines() if line.startswith("would exec "))


@pytest.mark.rules_core_absent
def test_driver_below_opus_max_keeps_opus_default(launch_with_usage) -> None:
    result = launch_with_usage("50", "--epic", "infra")
    assert result.returncode == 0, result.stderr
    assert "claude-opus-5-5" in _exec_line(result.stdout)


@pytest.mark.rules_core_absent
def test_driver_over_opus_max_defaults_to_sonnet(launch_with_usage) -> None:
    result = launch_with_usage("89", "--epic", "infra")
    assert result.returncode == 0, result.stderr
    assert "--model claude-sonnet-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" in result.stderr


@pytest.mark.parametrize("model", ("opus", "claude-opus-5-5[1m]"))
def test_explicit_opus_over_opus_max_is_refused(model: str, launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--model", model)
    assert result.returncode == 7
    assert "Opus refused" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.parametrize("pct", ("90", "97.5"))
def test_driver_at_stop_threshold_refuses_any_model(pct: str, launch_with_usage) -> None:
    for extra in ((), ("--model", "sonnet")):
        result = launch_with_usage(pct, "--epic", "infra", *extra)
        assert result.returncode == 7
        assert "No Claude launch until the weekly reset" in result.stderr
        assert "would exec" not in result.stdout


@pytest.mark.parametrize("pct", (85, 95))
def test_weekly_reader_ignores_environment_override(
    pct: int, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE", "0")
    payload = {"agents": {"claude": {"codexbar": {"weekly_used_pct": pct}}}}
    urlopen = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_called_once()
    assert capsys.readouterr().out == f"{pct}\n"


def test_weekly_reader_override_cannot_hide_request_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE", "0")
    urlopen = Mock(side_effect=OSError("unavailable"))
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_called_once()
    assert capsys.readouterr().out == "unknown\n"


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("50", "85", "unknown"))
@pytest.mark.parametrize("forwarded", (("--model", "opus"), ("--model=opus",), ("--model=",), ("--model",)))
def test_claude_refuses_forwarded_model_selectors(name: str, pct: str, forwarded: tuple[str, ...], launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--", *forwarded, name=name, env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 2, result.stderr
    assert "model selectors must use the launcher --model" in result.stderr
    assert "would exec" not in result.stdout
    assert "switched from Opus" not in result.stderr


@pytest.mark.rules_core_absent
def test_claude_still_forwards_other_provider_arguments(launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--", "--verbose", "synthetic prompt")
    assert result.returncode == 0, result.stderr
    command = _exec_line(result.stdout)
    assert "--model claude-sonnet-5-5" in command
    assert "--verbose" in command
    assert "synthetic" in command
