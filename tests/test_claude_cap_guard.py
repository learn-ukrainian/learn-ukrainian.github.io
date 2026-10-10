"""Claude weekly cap guard in the launcher (operator 2026-10-10)."""

from __future__ import annotations

import io
import json
import shlex
from datetime import UTC, datetime
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


@pytest.fixture(autouse=True)
def reader_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "https://monitor.invalid")
    clock = Mock(wraps=datetime)
    clock.now.return_value = datetime(2030, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(claude_weekly_used, "datetime", clock)


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
    assert "LU_CLAUDE_CAP_OVERRIDE=1" in result.stderr
    assert "LU_CLAUDE_OPUS_MAX_PCT=100" in result.stderr
    assert "the stop threshold still applies" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("opus", "claude-opus-5-5[1m]"))
@pytest.mark.parametrize("pct", ("80", "85", "90", "97.5"))
def test_operator_override_preserves_explicit_opus(name: str, model: str, pct: str, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", model, name=name, env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 0, result.stderr
    command = shlex.split(_exec_line(result.stdout))
    assert command[command.index("--model") + 1] == "claude-opus-5-5[1m]"
    assert "WARNING" in result.stderr
    assert "LU_CLAUDE_CAP_OVERRIDE=1 set by the operator" in result.stderr
    assert "switched from Opus" not in result.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("pct", ("80", "90"))
def test_operator_override_preserves_default_opus(pct: str, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra", env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 0, result.stderr
    assert "--model claude-opus-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


@pytest.mark.parametrize("override", ("0", "true", "yes", "2"))
@pytest.mark.parametrize("pct", ("80", "90"))
def test_invalid_operator_override_does_not_bypass_caps(override: str, pct: str, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra", "--model", "opus", env={"LU_CLAUDE_CAP_OVERRIDE": override})
    assert result.returncode == 7
    assert "would exec" not in result.stdout
    assert ("Opus refused" if pct == "80" else "No Claude launch") in result.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("pct", ("85", "90"))
def test_adjusted_opus_limit_keeps_stop_threshold(pct: str, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra", "--model", "opus", env={"LU_CLAUDE_OPUS_MAX_PCT": "100"})
    if pct == "85":
        assert result.returncode == 0, result.stderr
        command = shlex.split(_exec_line(result.stdout))
        assert command[command.index("--model") + 1] == "claude-opus-5-5[1m]"
    else:
        assert result.returncode == 7
        assert "No Claude launch" in result.stderr
        assert "would exec" not in result.stdout


@pytest.mark.parametrize("pct", ("90", "97.5"))
def test_driver_at_stop_threshold_refuses_any_model(pct: str, launch_with_usage) -> None:
    for extra in ((), ("--model", "sonnet")):
        result = launch_with_usage(pct, "--epic", "infra", *extra)
        assert result.returncode == 7
        assert "No Claude launch until the weekly reset" in result.stderr
        assert "would exec" not in result.stdout


@pytest.mark.parametrize("base", (None, "", " \t\n", "/"))
def test_weekly_reader_without_configuration_makes_no_request(
    base: str | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if base is None:
        monkeypatch.delenv("LU_MONITOR_LOOPBACK", raising=False)
    else:
        monkeypatch.setenv("LU_MONITOR_LOOPBACK", base)
    urlopen = Mock()
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_not_called()
    assert capsys.readouterr().out == "unknown\n"


def test_weekly_reader_uses_only_configured_target(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", " https://configured.invalid/ ")
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "agents": {"claude": {"codexbar": {"weekly_used_pct": 95}}},
    }
    urlopen = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_called_once_with(
        "https://configured.invalid/api/state/routing-budget", timeout=4
    )
    assert capsys.readouterr().out == "95\n"


@pytest.mark.parametrize("pct", (85, 95))
def test_weekly_reader_ignores_environment_override(
    pct: int, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE", "0")
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "agents": {"claude": {"codexbar": {"weekly_used_pct": pct}}},
    }
    urlopen = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_called_once()
    assert capsys.readouterr().out == f"{pct}\n"


@pytest.mark.parametrize(
    ("other_provider_stale", "agent_stale", "bar_stale", "expected"),
    (
        (True, False, False, "95"),
        (True, True, False, "unknown"),
        (True, False, True, "unknown"),
        (False, True, False, "unknown"),
        (False, False, True, "unknown"),
        (False, False, False, "95"),
    ),
)
def test_weekly_reader_checks_claude_freshness(
    other_provider_stale: bool,
    agent_stale: bool,
    bar_stale: bool,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "diagnostics": {"stale": other_provider_stale, "data_age_s": 1800},
        "agents": {
            "codex": {"codexbar": {"stale": other_provider_stale}},
            "claude": {
                "stale": agent_stale,
                "codexbar": {"stale": bar_stale, "weekly_used_pct": 95},
            }
        },
    }
    urlopen = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr(claude_weekly_used.urllib.request, "urlopen", urlopen)

    claude_weekly_used.main()

    urlopen.assert_called_once()
    assert capsys.readouterr().out == f"{expected}\n"


@pytest.mark.parametrize(
    ("generated_at", "expected"),
    (
        ("2029-12-31T23:45:00Z", "95"),
        ("2029-12-31T23:44:59Z", "unknown"),
        ("2030-01-01T00:00:01Z", "95"),
        ("2030-01-01T00:01:00Z", "95"),
        ("2030-01-01T00:01:01Z", "unknown"),
        ("2030-01-01T00:00:00", "unknown"),
        ("invalid", "unknown"),
        (None, "unknown"),
    ),
)
def test_weekly_reader_rejects_untrusted_response_age(
    generated_at: str | None,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = {
        "diagnostics": {"stale": False},
        "agents": {"claude": {"codexbar": {"stale": False, "weekly_used_pct": 95}}},
    }
    if generated_at is not None:
        payload["generated_at"] = generated_at
    monkeypatch.setattr(
        claude_weekly_used.urllib.request, "urlopen",
        Mock(return_value=io.BytesIO(json.dumps(payload).encode())),
    )

    claude_weekly_used.main()

    assert capsys.readouterr().out == f"{expected}\n"


def test_fresh_claude_usage_blocks_launch_when_other_provider_is_stale(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    launch_with_usage,
) -> None:
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "diagnostics": {"stale": True, "data_age_s": 1800},
        "agents": {
            "claude": {"codexbar": {"stale": False, "weekly_used_pct": 95}},
            "codex": {"codexbar": {"stale": True}},
        },
    }
    monkeypatch.setattr(
        claude_weekly_used.urllib.request, "urlopen",
        Mock(return_value=io.BytesIO(json.dumps(payload).encode())),
    )
    claude_weekly_used.main()
    usage = capsys.readouterr().out.strip()
    assert usage == "95"

    result = launch_with_usage(usage, "--epic", "infra")

    assert result.returncode == 7
    assert "No Claude launch until the weekly reset" in result.stderr
    assert "would exec" not in result.stdout


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
@pytest.mark.parametrize(
    "forwarded",
    (
        ("--model", "opus"), ("--model=opus",), ("--model=",), ("--model",),
        ("-m", "opus"), ("-mopus",), ("-m=opus",), ("-m",),
        ("--m", "opus"), ("--m=opus",),
        ("--mo", "opus"), ("--mo=opus",),
        ("--mod", "opus"), ("--mod=opus",),
        ("--mode", "opus"), ("--mode=opus",),
    ),
)
def test_claude_refuses_forwarded_model_selectors(name: str, pct: str, forwarded: tuple[str, ...], launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--", *forwarded, name=name, env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 2, result.stderr
    assert "model selectors must use the launcher --model" in result.stderr
    assert "would exec" not in result.stdout
    assert "switched from Opus" not in result.stderr


@pytest.mark.parametrize("forwarded", (("-m", "opus"), ("--mod", "opus"), ("--mod=opus",)))
@pytest.mark.parametrize("separator", ((), ("--",)))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet")))
def test_driver_rejects_forwarded_selectors_above_opus_limit(
    forwarded: tuple[str, ...], separator: tuple[str, ...], model: tuple[str, ...], launch_with_usage,
) -> None:
    result = launch_with_usage("85", "--epic", "infra", *model, *separator, *forwarded)
    assert result.returncode == 2, result.stderr
    assert "model selectors must use the launcher --model" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet"), ("--model", "opus")))
def test_unknown_usage_warns_for_every_model(name: str, model: tuple[str, ...], launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage("unknown", *args, *model, name=name)
    assert result.returncode == 0, result.stderr
    assert result.stderr.count("WARNING Claude weekly usage unknown") == 1
    assert "would exec" in result.stdout


@pytest.mark.rules_core_absent
def test_claude_still_forwards_other_provider_arguments(launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--", "--verbose", "synthetic prompt")
    assert result.returncode == 0, result.stderr
    command = _exec_line(result.stdout)
    assert "--model claude-sonnet-5-5" in command
    assert "--verbose" in command
    assert "synthetic" in command
