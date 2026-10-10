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
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "https://configured.invalid")
    clock = Mock(wraps=datetime)
    clock.now.return_value = datetime(2030, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(claude_weekly_used, "datetime", clock)


@pytest.fixture
def launch_with_usage(tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Inject telemetry in a fixture reader, without a production bypass."""
    reader = tmp_path / "weekly_reader.py"
    for variable in (
        "LAUNCHER_MODEL", "LU_CLAUDE_OPUS_BLOCKED", "LU_CLAUDE_STOP_PCT",
        "LU_CLAUDE_CAP_OVERRIDE", "LU_CLAUDE_OPUS_MAX_PCT", "LU_CLAUDE_SONNET_STOP_PCT",
    ):
        # Keep the policy matrix independent of the operator's shell settings.
        monkeypatch.delenv(variable, raising=False)
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
@pytest.mark.parametrize("pct, expected", (("0", "claude-opus-5-5[1m]"), ("79.999", "claude-opus-5-5[1m]"), ("80", "claude-sonnet-5-5"), ("89.999", "claude-sonnet-5-5")))
def test_default_driver_model_tracks_opus_threshold(pct, expected, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra")
    assert result.returncode == 0, result.stderr
    command = shlex.split(_exec_line(result.stdout))
    assert command[command.index("--model") + 1] == expected
    assert ("switched from Opus" in result.stderr) == (float(pct) >= 80)


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("opus", "claude-opus-5-5[1m]"))
@pytest.mark.parametrize("pct", ("0", "79.999", "80", "89.999"))
@pytest.mark.parametrize("via_env", (False, True))
def test_explicit_opus_tracks_usage(name, model, pct, via_env, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, *(() if via_env else ("--model", model)), name=name,
                               env={"LAUNCHER_MODEL": model} if via_env else {})
    if float(pct) >= 80:
        assert result.returncode == 7, result.stderr
        assert "Opus refused at 80%" in result.stderr
        assert "would exec" not in result.stdout
        assert "would claim lease" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert "--model" in _exec_line(result.stdout)
        assert "claude-opus-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("90", "90.1", "100"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet"), ("--model", "opus"), ("--model", "haiku")))
def test_stop_threshold_refuses_every_claude_launch(name, pct, model, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, *model, name=name)
    if name == "start-claude-driver.sh" and model == ("--model", "haiku"):
        assert result.returncode == 4
        assert "not certified" in result.stderr
    else:
        assert result.returncode == 7
        assert "stop at 90%" in result.stderr
    assert "would exec" not in result.stdout
    assert "would claim lease" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("sonnet", "claude-sonnet-5-5"))
@pytest.mark.parametrize("pct", ("0", "79.999", "80", "89.999"))
def test_explicit_sonnet_launches_below_stop(name, model, pct, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", model, name=name)
    assert result.returncode == 0, result.stderr
    assert "--model claude-sonnet-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("85", "90", "100", "unknown"))
@pytest.mark.parametrize("model", ("opus", "sonnet"))
def test_operator_override_bypasses_usage_limits(name, pct, model, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", model, name=name,
                               env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 0, result.stderr
    assert "operator override enabled" in result.stderr
    assert f"claude-{model}-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("variable, threshold, model", (("LU_CLAUDE_STOP_PCT", "89.5", "sonnet"), ("LU_CLAUDE_STOP_PCT", "95.5", "sonnet"), ("LU_CLAUDE_OPUS_MAX_PCT", "75.5", "opus"), ("LU_CLAUDE_OPUS_MAX_PCT", "85.5", "opus")))
@pytest.mark.parametrize("offset", (-0.001, 0, 0.001))
def test_environment_limits_apply_at_exact_boundary(variable, threshold, model, offset, launch_with_usage) -> None:
    result = launch_with_usage(str(float(threshold) + offset), "--epic", "infra", "--model", model,
                               env={variable: threshold})
    if offset >= 0:
        assert result.returncode == 7, result.stderr
        assert "would exec" not in result.stdout
        assert "would claim lease" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert f"claude-{model}-5-5" in _exec_line(result.stdout)


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("pct", ("74.999", "75", "89.999"))
def test_configured_opus_limit_controls_default_downgrade(pct, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra", env={"LU_CLAUDE_OPUS_MAX_PCT": "75"})
    assert result.returncode == 0, result.stderr
    model = "claude-sonnet-5-5" if float(pct) >= 75 else "claude-opus-5-5"
    assert model in _exec_line(result.stdout)


@pytest.mark.parametrize("override", ("0", "true", "yes", "2"))
def test_only_exact_operator_override_bypasses_cap(override, launch_with_usage) -> None:
    result = launch_with_usage("100", "--epic", "infra", env={"LU_CLAUDE_CAP_OVERRIDE": override})
    assert result.returncode == 7
    assert "stop at 90%" in result.stderr


def _mock_request(monkeypatch, response):
    request = Mock(return_value=response) if not isinstance(response, Exception) else Mock(side_effect=response)
    opener = Mock(open=request)
    builder = Mock(return_value=opener)
    monkeypatch.setattr(claude_weekly_used.urllib.request, "build_opener", builder)
    return request, builder


def test_weekly_reader_uses_environment_target(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "https://configured.invalid")
    monkeypatch.setenv("https_proxy", "https://untrusted.invalid")
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "agents": {"claude": {"codexbar": {"weekly_used_pct": 95}}},
    }
    request, builder = _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))
    claude_weekly_used.main()
    request.assert_called_once_with("https://configured.invalid/api/state/routing-budget", timeout=4)
    proxy_handler, redirect_handler = builder.call_args.args
    assert proxy_handler.proxies == {}
    assert isinstance(redirect_handler, claude_weekly_used._NoRedirect)
    assert capsys.readouterr().out == "95\n"


@pytest.mark.parametrize("base", ("", "file:synthetic", "https://", "https://user:" + "synthetic-pw" + "@synthetic.invalid", "https://synthetic.invalid/?token=secret", "https://synthetic.invalid/#fragment"))
def test_weekly_reader_rejects_invalid_environment_target(base, monkeypatch, capsys) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", base)
    request, _ = _mock_request(monkeypatch, io.BytesIO(b"{}"))
    claude_weekly_used.main()
    request.assert_not_called()
    assert capsys.readouterr().out == "unknown\n"


@pytest.mark.parametrize("base", (None, " https://configured.invalid/ "))
def test_weekly_reader_default_and_normalized_target(base, monkeypatch, capsys) -> None:
    if base is None:
        monkeypatch.delenv("LU_MONITOR_LOOPBACK", raising=False)
    else:
        monkeypatch.setenv("LU_MONITOR_LOOPBACK", base)
    payload = {"generated_at": "2030-01-01T00:00:00Z", "agents": {"claude": {"codexbar": {"weekly_used_pct": 50}}}}
    request, _ = _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))
    claude_weekly_used.main()
    target = "http://127.0.0.1:8765" if base is None else "https://configured.invalid"
    request.assert_called_once_with(target + "/api/state/routing-budget", timeout=4)
    assert capsys.readouterr().out == "50\n"


def test_weekly_reader_refuses_redirects() -> None:
    with pytest.raises(ValueError, match="redirect refused"):
        claude_weekly_used._NoRedirect().redirect_request(None, None, 302, "", {}, "https://untrusted.invalid")


@pytest.mark.parametrize("pct", (None, True, -1, 101, "0", float("nan"), float("inf")))
def test_weekly_reader_rejects_invalid_percentages(pct, monkeypatch, capsys) -> None:
    payload = {"generated_at": "2030-01-01T00:00:00Z", "agents": {"claude": {"codexbar": {"weekly_used_pct": pct}}}}
    _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))
    claude_weekly_used.main()
    assert capsys.readouterr().out == "unknown\n"


@pytest.mark.parametrize("pct", (85, 95))
def test_weekly_reader_ignores_environment_override(
    pct: int, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE", "0")
    payload = {
        "generated_at": "2030-01-01T00:00:00Z",
        "agents": {"claude": {"codexbar": {"weekly_used_pct": pct}}},
    }
    urlopen, _ = _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))

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
    urlopen, _ = _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))

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
    _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))

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
            "claude": {"codexbar": {"stale": False, "weekly_used_pct": 99}},
            "codex": {"codexbar": {"stale": True}},
        },
    }
    _mock_request(monkeypatch, io.BytesIO(json.dumps(payload).encode()))
    claude_weekly_used.main()
    usage = capsys.readouterr().out.strip()
    assert usage == "99"

    result = launch_with_usage(usage, "--epic", "infra")

    assert result.returncode == 7
    assert "No Claude launch until the weekly reset" in result.stderr
    assert "would exec" not in result.stdout


def test_weekly_reader_override_cannot_hide_request_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_CLAUDE_WEEKLY_USED_PCT_OVERRIDE", "0")
    urlopen, _ = _mock_request(monkeypatch, OSError("unavailable"))

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
def test_driver_rejects_forwarded_selectors_before_percentage_check(
    forwarded: tuple[str, ...], separator: tuple[str, ...], model: tuple[str, ...], launch_with_usage,
) -> None:
    result = launch_with_usage("85", "--epic", "infra", *model, *separator, *forwarded)
    assert result.returncode == 2, result.stderr
    assert "model selectors must use the launcher --model" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("unknown", "", "nan", "inf", "-1", "101", "0\n95"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet")))
def test_unknown_or_invalid_usage_warns_and_allows_launch(name, pct, model, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, *model, name=name)
    assert result.returncode == 0, result.stderr
    assert "warning: Claude weekly usage unknown or invalid" in result.stderr
    assert "would exec" in result.stdout
    assert "switched from Opus" not in result.stderr


@pytest.mark.rules_core_absent
def test_claude_still_forwards_other_provider_arguments(launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--", "--verbose", "synthetic prompt")
    assert result.returncode == 0, result.stderr
    command = _exec_line(result.stdout)
    assert "--model claude-sonnet-5-5" in command
    assert "--verbose" in command
    assert "synthetic" in command


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet")))
@pytest.mark.parametrize("separator", ((), ("--",)))
@pytest.mark.parametrize("override", ("0", "1"))
@pytest.mark.parametrize(
    "forwarded",
    (
        ("--settings", '{"model":"opus"}'),
        ('--settings={"model":"opus"}',),
        ("--settings", "synthetic-settings.json"),
        ("--settings",), ("--settings=",),
        ("--settings", "invalid"),
        ("--set", '{"model":"opus"}'),
        ('--set={"model":"opus"}',),
        ("--fallback-model", "opus"), ("--fallback-model=opus",),
        ("--fallback-model", "claude-opus-5-5[1m]"),
        ("--fallback-model",), ("--fallback-model=",),
        ("--fallback-m", "opus"), ("--fallback-m=opus",),
    ),
)
def test_claude_refuses_unvalidated_configuration_models(
    name: str, model: tuple[str, ...], separator: tuple[str, ...], override: str,
    forwarded: tuple[str, ...], launch_with_usage,
) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(
        "85", *args, *model, *separator, *forwarded, name=name,
        env={"LU_CLAUDE_CAP_OVERRIDE": override},
    )
    assert result.returncode == 2, result.stderr
    if name == "start-claude.sh" and not separator:
        assert "unknown launcher flag" in result.stderr
    else:
        assert "model selectors must use the launcher --model" in result.stderr
    assert "would exec" not in result.stdout
    assert "would enter" not in result.stdout
    assert "would claim lease" not in result.stdout


@pytest.mark.parametrize("variable", ("LU_CLAUDE_STOP_PCT", "LU_CLAUDE_OPUS_MAX_PCT"))
@pytest.mark.parametrize("value", ("invalid", "-1", "101", "nan", "80junk"))
def test_invalid_environment_limits_are_configuration_errors(variable, value, launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--model", "opus", env={variable: value})
    assert result.returncode == 2, result.stderr
    assert "thresholds must be percentages" in result.stderr
    assert "would exec" not in result.stdout


def test_driver_cap_documentation_matches_enforced_policy() -> None:
    comment = (REPO / "start-claude-driver.sh").read_text()
    result = run_launcher("start-claude-driver.sh", "--help")
    assert result.returncode == 0
    runbook = (REPO / "docs/runbooks/epic-orchestrator-roster.md").read_text()
    for text in (comment, result.stdout, runbook):
        for variable in ("LU_CLAUDE_STOP_PCT", "LU_CLAUDE_OPUS_MAX_PCT", "LU_CLAUDE_CAP_OVERRIDE=1", "LU_MONITOR_LOOPBACK"):
            assert variable in text
    assert "default 90 percent" in result.stdout
    assert "default 80 percent" in result.stdout
    assert "Unknown usage warns and allows launch" in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("forwarded", (("-max-tokens", "100"), ("-max-tokens=100",)))
def test_unrelated_short_provider_flag_is_forwarded(name, forwarded, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage("50", *args, "--", *forwarded, name=name)
    assert result.returncode == 0, result.stderr
    command = shlex.split(_exec_line(result.stdout))
    assert all(arg in command for arg in forwarded)


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
def test_real_reader_unavailable_warns_without_disclosing_target(name, tmp_path) -> None:
    checkout = _build_view(tmp_path / "checkout", {
        ("scripts", "lib", "rules_core.sh"): _LOADER_STUB.format(real=REPO / "scripts/lib/rules_core.sh"),
    })
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = run_launcher(name, *args, "--model", "opus", root=checkout,
                          env={"LU_MONITOR_LOOPBACK": "file:private-telemetry-target", "LU_CLAUDE_CAP_OVERRIDE": "0",
                               "LU_CLAUDE_STOP_PCT": "90", "LU_CLAUDE_OPUS_MAX_PCT": "80"})
    assert result.returncode == 0, result.stderr
    assert "warning: Claude weekly usage unknown or invalid" in result.stderr
    assert "claude-opus-5-5" in _exec_line(result.stdout)
    assert "private-telemetry-target" not in result.stdout + result.stderr


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct, stop, opus_max, expected", (
    ("0", "0", "80", 7),
    ("0", "100", "0", 7),
    ("99.999", "100", "100", 0),
    ("100", "100", "100", 7),
))
def test_limit_percentage_extremes(name, pct, stop, opus_max, expected, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", "opus", name=name,
                               env={"LU_CLAUDE_STOP_PCT": stop, "LU_CLAUDE_OPUS_MAX_PCT": opus_max})
    assert result.returncode == expected, result.stderr
    assert ("would exec" in result.stdout) == (expected == 0)
