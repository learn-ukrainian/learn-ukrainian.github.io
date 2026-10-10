"""Claude weekly cap guard in the launcher (operator 2026-10-10)."""

from __future__ import annotations

import io
import json
import shlex
import stat
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
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
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "https://untrusted.invalid")
    monkeypatch.setattr(claude_weekly_used.os, "fstat", lambda fd: SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o600))
    monkeypatch.setattr(claude_weekly_used.os, "pread", lambda *args: b'{"monitor_base_url":"https://configured.invalid"}')
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
@pytest.mark.parametrize("pct", ("10", "50", "79.9", "80", "89.9"))
def test_default_opus_obeys_percentage_limit(pct: str, launch_with_usage) -> None:
    result = launch_with_usage(pct, "--epic", "infra")
    assert result.returncode == 0, result.stderr
    switched = float(pct) >= 80
    expected = "claude-sonnet-5-5" if switched else "claude-opus-5-5[1m]"
    command = shlex.split(_exec_line(result.stdout))
    assert command[command.index("--model") + 1] == expected
    assert ("switched from Opus" in result.stderr) == switched


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("opus", "claude-opus-5-5[1m]"))
@pytest.mark.parametrize("pct", ("80", "85", "89.9"))
def test_explicit_opus_is_refused_at_percentage_limit(name: str, model: str, pct: str, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", model, name=name)
    assert result.returncode == 7
    assert "Opus refused" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("10", "79.9"))
@pytest.mark.parametrize("via_env", (False, True))
def test_explicit_opus_launches_below_limit(name: str, pct: str, via_env: bool, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(
        pct, *args, *(() if via_env else ("--model", "opus")), name=name,
        env={"LAUNCHER_MODEL": "opus"} if via_env else {},
    )
    assert result.returncode == 0, result.stderr
    assert "claude-opus-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


def test_environment_opus_is_an_explicit_request(launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", env={"LAUNCHER_MODEL": "opus"})
    assert result.returncode == 7
    assert "Opus refused" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("85", "90", "99", "100"))
@pytest.mark.parametrize("variable", ("LU_CLAUDE_CAP_OVERRIDE", "LU_CLAUDE_STOP_PCT", "LU_CLAUDE_OPUS_MAX_PCT"))
def test_shell_overrides_cannot_bypass_limits(name, pct, variable, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    value = "1" if variable == "LU_CLAUDE_CAP_OVERRIDE" else "100"
    result = launch_with_usage(pct, *args, "--model", "opus", name=name, env={variable: value})
    assert result.returncode == 7, result.stderr
    assert ("Opus refused" if pct == "85" else "stop at 90%") in result.stderr
    assert "would exec" not in result.stdout
    assert "would claim lease" not in result.stdout


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("90", "98", "99", "100"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet"), ("--model", "opus"), ("--model", "haiku")))
def test_stop_threshold_refuses_every_claude_launch(name: str, pct: str, model: tuple[str, ...], launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, *model, name=name)
    if name == "start-claude-driver.sh" and model == ("--model", "haiku"):
        assert result.returncode == 4
        assert "not certified" in result.stderr
    else:
        assert result.returncode == 7
        assert "No Claude launch until the weekly reset" in result.stderr
        assert "stop at 90%" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.rules_core_absent
@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("sonnet", "claude-sonnet-5-5"))
@pytest.mark.parametrize("pct", ("10", "80", "89.9"))
def test_explicit_sonnet_launches_below_stop(name: str, model: str, pct: str, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, "--model", model, name=name)
    assert result.returncode == 0, result.stderr
    assert "--model claude-sonnet-5-5" in _exec_line(result.stdout)
    assert "switched from Opus" not in result.stderr


@pytest.mark.parametrize("base", (None, "", "https://untrusted.invalid"))
def test_weekly_reader_environment_cannot_supply_configuration(base, monkeypatch, capsys) -> None:
    if base is not None:
        monkeypatch.setenv("LU_MONITOR_LOOPBACK", base)
    monkeypatch.setattr(claude_weekly_used.os, "fstat", Mock(side_effect=OSError("missing")))
    opener = Mock()
    monkeypatch.setattr(claude_weekly_used.urllib.request, "build_opener", opener)
    claude_weekly_used.main()
    opener.assert_not_called()
    assert capsys.readouterr().out == "unknown\n"


def _mock_request(monkeypatch, response):
    request = Mock(return_value=response) if not isinstance(response, Exception) else Mock(side_effect=response)
    opener = Mock(open=request)
    builder = Mock(return_value=opener)
    monkeypatch.setattr(claude_weekly_used.urllib.request, "build_opener", builder)
    return request, builder


def test_weekly_reader_uses_only_protected_target(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "https://untrusted.invalid")
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


@pytest.mark.parametrize("owner, mode", ((1234, stat.S_IFREG | 0o600), (0, stat.S_IFREG | 0o620), (0, stat.S_IFREG | 0o602), (0, stat.S_IFIFO | 0o600)))
def test_weekly_reader_rejects_unprotected_operator_state(owner, mode, monkeypatch, capsys) -> None:
    monkeypatch.setattr(claude_weekly_used.os, "fstat", lambda fd: SimpleNamespace(st_uid=owner, st_mode=mode))
    request, _ = _mock_request(monkeypatch, io.BytesIO(b"{}"))
    claude_weekly_used.main()
    request.assert_not_called()
    assert capsys.readouterr().out == "unknown\n"


@pytest.mark.parametrize("raw", (b"{}", b"invalid", b"[]", b'{"monitor_base_url":""}', b'{"monitor_base_url":"file:synthetic"}', b'{"monitor_base_url":true}', b" " * 65537))
def test_weekly_reader_rejects_invalid_operator_state(raw, monkeypatch, capsys) -> None:
    monkeypatch.setattr(claude_weekly_used.os, "pread", lambda *args: raw)
    request, _ = _mock_request(monkeypatch, io.BytesIO(b"{}"))
    claude_weekly_used.main()
    request.assert_not_called()
    assert capsys.readouterr().out == "unknown\n"


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


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("pct", ("unknown", "", "nan", "inf", "-1", "101", "0\n95"))
@pytest.mark.parametrize("model", ((), ("--model", "sonnet")))
def test_unknown_or_invalid_usage_refuses_launch(name, pct, model, launch_with_usage) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = launch_with_usage(pct, *args, *model, name=name, env={"LU_CLAUDE_CAP_OVERRIDE": "1"})
    assert result.returncode == 7, result.stderr
    assert "usage unknown or invalid" in result.stderr
    assert "would exec" not in result.stdout
    assert "would claim lease" not in result.stdout


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
def test_invalid_environment_limits_cannot_change_policy(variable, value, launch_with_usage) -> None:
    result = launch_with_usage("85", "--epic", "infra", "--model", "opus", env={variable: value})
    assert result.returncode == 7, result.stderr
    assert "Opus refused" in result.stderr
    assert "would exec" not in result.stdout


def test_driver_cap_documentation_matches_enforced_policy() -> None:
    comment = (REPO / "start-claude-driver.sh").read_text()
    assert "LU_CLAUDE_OPUS_BLOCKED" not in comment
    assert "default 99" not in comment
    assert "At 80% weekly usage" in comment
    assert "refused at 90%" in comment
    assert "trusted usage is unavailable" in comment
    result = run_launcher("start-claude-driver.sh", "--help")
    assert result.returncode == 0
    assert "all launches stop at 90%" in result.stdout
    assert "Unknown usage refuses launch" in result.stdout
    assert "LU_CLAUDE_CAP_OVERRIDE=1" not in result.stdout


@pytest.mark.parametrize("name", ("start-claude.sh", "start-claude-driver.sh"))
@pytest.mark.parametrize("model", ("opus", "sonnet"))
def test_real_reader_refuses_shell_controlled_configuration(name, model) -> None:
    args = ("--epic", "infra") if name == "start-claude-driver.sh" else ()
    result = run_launcher(
        name, *args, "--model", model,
        env={
            "LU_CLAUDE_CAP_OVERRIDE": "1",
            "LU_CLAUDE_STOP_PCT": "100",
            "LU_CLAUDE_OPUS_MAX_PCT": "100",
            "LU_MONITOR_LOOPBACK": "https://untrusted.invalid",
        },
    )
    assert result.returncode == 7, result.stderr
    assert "usage unknown or invalid" in result.stderr
    assert "would exec" not in result.stdout
    assert "would enter" not in result.stdout
    assert "would claim lease" not in result.stdout


def test_operator_target_reads_fixed_descriptor_without_consuming_offset(monkeypatch) -> None:
    metadata = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o600)
    fstat = Mock(return_value=metadata)
    pread = Mock(return_value=b'{"monitor_base_url":"https://configured.invalid/"}')
    monkeypatch.setattr(claude_weekly_used.os, "fstat", fstat)
    monkeypatch.setattr(claude_weekly_used.os, "pread", pread)
    for _ in range(2):
        assert claude_weekly_used._operator_target() == "https://configured.invalid"
    assert fstat.call_count == 2
    assert pread.call_count == 2
    fstat.assert_called_with(9)
    pread.assert_called_with(9, 65537, 0)
