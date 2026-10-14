"""Per-account Claude usage rows (#10630): probe, cache, payload and balancing hint.

Fixtures only: no real Claude directory is read and CodexBar never runs against
a real account. Subprocess tests run small ``sys.executable`` children.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts.agent_runtime.attempt_boundary import ClaudeAccountBinding
from scripts.api import claude_account_usage as cau
from scripts.api import subscription_usage

# Shape of ``codexbar usage --json --provider claude``; identity values are synthetic.
_FAKE_EMAIL = "owner-do-not-leak@example.invalid"
_FAKE_ORG = "Do-Not-Leak Organization"
_FAKE_ACCOUNT_ID = "0f0e0d0c-0b0a-4908-8706-050403020100"


def _codexbar_payload(*, session_used, session_expected, weekly_used, weekly_expected) -> list[dict]:
    return [
        {
            "provider": "claude",
            "source": "oauth",
            "accountId": _FAKE_ACCOUNT_ID,
            "pace": {
                "primary": {
                    "expectedUsedPercent": session_expected,
                    "deltaPercent": -54,
                    "summary": "54% in reserve | Lasts until reset",
                },
                "secondary": {
                    "expectedUsedPercent": weekly_expected,
                    "deltaPercent": 27,
                    "summary": "27% in deficit | Runs out in 1d 3h",
                },
            },
            "usage": {
                "updatedAt": "2026-10-14T14:00:00Z",
                "primary": {"windowMinutes": 300, "resetsAt": "2026-10-14T18:00:00Z", "usedPercent": session_used},
                "secondary": {
                    "windowMinutes": 10080,
                    "resetsAt": "2026-10-18T07:00:00Z",
                    "usedPercent": weekly_used,
                },
                "accountEmail": _FAKE_EMAIL,
                "accountOrganization": _FAKE_ORG,
                "identity": {"accountEmail": _FAKE_EMAIL, "accountOrganization": _FAKE_ORG},
            },
        }
    ]


PAYLOAD_A = _codexbar_payload(session_used=7, session_expected=61, weekly_used=74, weekly_expected=47)
PAYLOAD_B = _codexbar_payload(session_used=30, session_expected=50, weekly_used=20, weekly_expected=47)

EXPECTED_A = {
    "session5h": {
        "left_pct": 93.0,
        "resets_at": "2026-10-14T18:00:00Z",
        "pace": "54% in reserve | Lasts until reset",
        "pace_delta_pct": -54.0,
        "leftover_pct": 89,  # round(100 - 7 * 100 / 61)
    },
    "weekly": {
        "left_pct": 26.0,
        "resets_at": "2026-10-18T07:00:00Z",
        "pace": "27% in deficit | Runs out in 1d 3h",
        "pace_delta_pct": 27.0,
        "leftover_pct": 0,  # 74 used against 47 expected: runs out before reset
    },
}
EXPECTED_B = {
    "session5h": {**EXPECTED_A["session5h"], "left_pct": 70.0, "leftover_pct": 40},
    "weekly": {**EXPECTED_A["weekly"], "left_pct": 80.0, "leftover_pct": 57},  # round(100 - 2000 / 47)
}

_DIRS = {"a": Path("/fixture/claude-a"), "b": Path("/fixture/claude-b")}


@pytest.fixture
def fake_probe(monkeypatch):
    """Route each label's CodexBar call to a fixture keyed by CLAUDE_CONFIG_DIR."""
    outputs: dict[str, object] = {"a": PAYLOAD_A, "b": PAYLOAD_B}
    calls: list[dict[str, str]] = []

    def run(codexbar, env, *, timeout_s, max_bytes):
        calls.append(dict(env))
        assert codexbar == "/fixture/bin/codexbar"
        label = next(label for label, path in _DIRS.items() if env["CLAUDE_CONFIG_DIR"] == str(path))
        result = outputs[label]
        if isinstance(result, Exception):
            raise result
        return json.dumps(result).encode()

    monkeypatch.setattr(cau, "account_config_dir", lambda label: _DIRS[label])
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: "/fixture/bin/codexbar")
    monkeypatch.setattr(cau, "_run_codexbar", run)
    return outputs, calls


def _row(snapshot, label):
    return snapshot[f"claude:{label}"]


# Fails on origin/main: the per-account module does not exist (no rows at all).
def test_two_healthy_accounts_publish_reference_numbers(fake_probe):
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()

    assert set(snapshot) == {"claude:a", "claude:b"}
    for label, expected in (("a", EXPECTED_A), ("b", EXPECTED_B)):
        row = _row(snapshot, label)
        assert row["session5h"] == expected["session5h"]
        assert row["weekly"] == expected["weekly"]
        assert row["status"] == "ok"
        assert row["stale"] is False
        assert row["reason"] is None
        assert row["updated"] == "2026-10-14T14:00:00Z"
        assert isinstance(row["age_s"], float)


@pytest.mark.parametrize(
    ("used", "expected", "leftover"),
    [
        (74, 47, 0),  # used above expected: runs out early
        (60, 50, 0),
        (20, 47, 57),
        (30, 50, 40),
        (0, 10, 100),
        (47, 47, 0),
        (None, 47, None),  # used unknown
        (20, None, None),  # expected missing
        (20, 0, None),  # expected 0: no elapsed share to project from
        (20, -5, None),
    ],
)
def test_projected_leftover_formula(used, expected, leftover):
    assert cau.projected_leftover_pct(used, expected) == leftover


def test_pace_without_expected_keeps_leftover_unknown():
    payload = _codexbar_payload(session_used=10, session_expected=None, weekly_used=20, weekly_expected=0)
    row = cau.parse_codexbar_claude(payload)
    assert row["session5h"]["leftover_pct"] is None
    assert row["weekly"]["leftover_pct"] is None
    assert row["weekly"]["left_pct"] == 80.0


def test_failed_or_timed_out_account_is_unknown_and_the_other_still_published(fake_probe):
    outputs, _ = fake_probe
    outputs["b"] = cau._ProbeFailed("timeout")

    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()

    assert _row(snapshot, "a")["status"] == "ok"
    assert _row(snapshot, "a")["weekly"] == EXPECTED_A["weekly"]
    row_b = _row(snapshot, "b")
    assert row_b["status"] == "unknown"
    assert row_b["reason"] == "timeout"
    assert row_b["weekly"] == dict.fromkeys(("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct"))
    assert row_b["session5h"]["left_pct"] is None


def test_failure_after_a_good_sample_is_stale_with_last_numbers(fake_probe):
    outputs, _ = fake_probe
    cau.refresh_claude_account_usage()
    outputs["b"] = cau._ProbeFailed("exit_nonzero")
    cau.refresh_claude_account_usage()

    row_b = _row(cau.claude_accounts_snapshot(), "b")
    assert row_b["status"] == "stale"
    assert row_b["stale"] is True
    assert row_b["reason"] == "exit_nonzero"
    assert row_b["weekly"] == EXPECTED_B["weekly"]


def test_sample_past_the_ttl_is_stale(fake_probe):
    cau.refresh_claude_account_usage()
    row = _row(cau.claude_accounts_snapshot(ttl_s=0.0), "a")
    assert row["status"] == "stale"
    assert row["reason"] == "expired"
    assert row["weekly"] == EXPECTED_A["weekly"]


def test_unexpected_probe_defect_does_not_break_refresh(fake_probe):
    outputs, _ = fake_probe
    outputs["a"] = RuntimeError("defect")
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "unknown"
    assert _row(snapshot, "a")["reason"] == "probe_error"
    assert _row(snapshot, "b")["status"] == "ok"


def test_missing_binding_is_unknown_and_forgets_old_numbers(fake_probe, monkeypatch):
    """A missing binding is a row state, not an error; the old sample is not reused."""
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "b")["status"] == "ok"

    monkeypatch.setattr(cau, "account_config_dir", _resolver_with_real_binding_lookup)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")  # empty: no binding file

    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "ok"
    row_b = _row(snapshot, "b")
    assert row_b["status"] == "unknown"
    assert row_b["reason"] == "claude_account_binding_missing"
    assert row_b["weekly"]["left_pct"] is None


_REAL_ACCOUNT_CONFIG_DIR = cau.account_config_dir


def _resolver_with_real_binding_lookup(label):
    if label == "a":
        return _DIRS["a"]
    return _REAL_ACCOUNT_CONFIG_DIR(label)


def test_binding_missing_through_the_real_loader(monkeypatch):
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")
    with pytest.raises(cau.ClaudeAccountRefused) as exc:
        cau.account_config_dir("b")
    assert exc.value.code == "claude_account_binding_missing"


def test_default_label_is_the_host_default_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    assert cau.account_config_dir("a") == tmp_path / ".claude"


def test_binding_that_names_the_default_directory_is_refused(monkeypatch, tmp_path):
    default = tmp_path / ".claude"
    default.mkdir()
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    binding = ClaudeAccountBinding(label="b", config_dir=default, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)

    @contextlib.contextmanager
    def open_dir(path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            yield fd
        finally:
            os.close(fd)

    monkeypatch.setattr(cau, "_open_claude_directory", open_dir)
    with pytest.raises(cau.ClaudeAccountRefused) as exc:
        cau.account_config_dir("b")
    assert exc.value.code == "claude_account_binding_is_default"

    other = tmp_path / "other"
    other.mkdir()
    binding = ClaudeAccountBinding(label="b", config_dir=other, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    assert cau.account_config_dir("b") == other


def test_payload_has_no_identity_or_path_anywhere(fake_probe):
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    serialized = json.dumps(fields)
    for forbidden in (
        _FAKE_EMAIL,
        _FAKE_ORG,
        _FAKE_ACCOUNT_ID,
        "example.invalid",
        "/fixture/",
        "claude-a",
        "claude-b",
        str(Path.home()),
        "accountEmail",
        "accountOrganization",
        "accountId",
        "identity",
        "config_dir",
        "CLAUDE_CONFIG_DIR",
        "email",
    ):
        assert forbidden not in serialized, forbidden


def test_child_environment_carries_no_ambient_credential():
    environ = {
        "PATH": "/usr/bin",
        "HOME": "/fixture/home",
        "LANG": "C.UTF-8",
        "ANTHROPIC_API_KEY": "sk-ambient",
        "ANTHROPIC_AUTH_TOKEN": "ambient",
        "CLAUDE_API_KEY": "ambient",
        "CLAUDE_CODE_OAUTH_TOKEN": "ambient",
        "CLAUDE_CONFIG_DIR": "/fixture/ambient-dir",
        "GITHUB_TOKEN": "ambient",
        "OPENAI_API_KEY": "ambient",
        "AWS_SECRET_ACCESS_KEY": "ambient",
        "SSH_AUTH_SOCK": "/fixture/agent.sock",
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/fixture/bus",
    }
    env = cau.child_env(Path("/fixture/claude-b"), environ)
    assert env == {
        "PATH": "/usr/bin",
        "HOME": "/fixture/home",
        "LANG": "C.UTF-8",
        "CLAUDE_CONFIG_DIR": "/fixture/claude-b",
    }
    assert "ambient" not in json.dumps(env)


def test_probe_passes_only_the_sanitized_environment(fake_probe, monkeypatch):
    _, calls = fake_probe
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ambient")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "ambient")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/fixture/ambient-dir")
    cau.refresh_claude_account_usage()
    assert len(calls) == 2
    for env in calls:
        assert set(env) <= set(cau._CHILD_ENV_NAMES) | {"CLAUDE_CONFIG_DIR"}
        assert env["CLAUDE_CONFIG_DIR"] in {str(path) for path in _DIRS.values()}
        assert "ANTHROPIC_API_KEY" not in env
        assert "CLAUDE_CODE_OAUTH_TOKEN" not in env


def test_missing_codexbar_is_unknown(monkeypatch):
    monkeypatch.setattr(cau, "account_config_dir", lambda label: _DIRS[label])
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: None)
    cau.refresh_claude_account_usage()
    row = _row(cau.claude_accounts_snapshot(), "a")
    assert row["status"] == "unknown"
    assert row["reason"] == "missing_binary"


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"not": "a list"}, "no_usage"),
        ([], "bad_json"),
        ([{"provider": "codex", "usage": {}}], "provider_mismatch"),
        ([{"provider": "claude", "error": {"kind": "auth"}}], "provider_error"),
        ([{"provider": "claude", "usage": {"primary": {"usedPercent": None}}}], "no_usage"),
        ([{"provider": "claude", "usage": {"primary": {"usedPercent": True}}}], "no_usage"),
    ],
)
def test_malformed_payloads_are_failures(payload, code):
    with pytest.raises(cau._ProbeFailed) as exc:
        cau.parse_codexbar_claude(payload)
    assert exc.value.code == code


def test_non_json_output_is_a_failure(fake_probe, monkeypatch):
    monkeypatch.setattr(cau, "_run_codexbar", lambda codexbar, env, *, timeout_s, max_bytes: b"not json")
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "a")["reason"] == "bad_json"


def test_missing_updated_at_uses_probe_time(fake_probe):
    outputs, _ = fake_probe
    payload = json.loads(json.dumps(PAYLOAD_A))
    del payload[0]["usage"]["updatedAt"]
    outputs["a"] = payload
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "a")["updated"].endswith("Z")


# ---- preferred_claude_account -------------------------------------------------


def _rows(a_leftover, b_leftover, *, a_status="ok", b_status="ok"):
    return {
        "claude:a": {"status": a_status, "weekly": {"leftover_pct": a_leftover}},
        "claude:b": {"status": b_status, "weekly": {"leftover_pct": b_leftover}},
    }


@pytest.mark.parametrize(
    ("rows", "preferred"),
    [
        (_rows(0, 57), "b"),
        (_rows(57, 0), "a"),
        (_rows(40, 40), None),  # tie
        (_rows(None, 57), None),  # leftover unknown
        (_rows(0, 57, a_status="unknown"), None),  # one account unknown
        (_rows(0, 57, b_status="stale"), None),
        ({"claude:a": {"status": "ok", "weekly": {"leftover_pct": 10}}}, None),  # b row absent
        ({}, None),
    ],
)
def test_preferred_claude_account(rows, preferred):
    assert cau.preferred_claude_account(rows) == preferred


def test_routing_budget_fields_prefers_the_larger_weekly_leftover(fake_probe):
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    assert set(fields) == {"claude_accounts", "preferred_claude_account"}
    assert fields["preferred_claude_account"] == "b"  # 57 > 0


# ---- bounded subprocess -------------------------------------------------------


def _fake_codexbar(tmp_path: Path, body: str) -> str:
    """An executable CodexBar stand-in run by this interpreter; ``args`` holds its arguments."""
    script = tmp_path / "codexbar"
    script.write_text(f"#!{sys.executable} -I\nimport json, os, sys, time\nargs = sys.argv[1:]\n{body}\n")
    script.chmod(0o700)
    return str(script)


def test_run_codexbar_runs_the_fixed_query_from_root_cwd_with_given_env(tmp_path):
    body = (
        "print(json.dumps({'args': args, 'cwd': os.getcwd(),"
        " 'has_dir': 'CLAUDE_CONFIG_DIR' in os.environ, 'has_key': 'ANTHROPIC_API_KEY' in os.environ}))"
    )
    raw = cau._run_codexbar(
        _fake_codexbar(tmp_path, body), {"CLAUDE_CONFIG_DIR": "/fixture/x"}, timeout_s=30, max_bytes=65536
    )
    assert json.loads(raw) == {
        "args": ["usage", "--json", "--provider", "claude"],
        "cwd": "/",
        "has_dir": True,
        "has_key": False,
    }


def test_run_codexbar_times_out_and_kills_the_child(tmp_path):
    started = time.monotonic()
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(_fake_codexbar(tmp_path, "time.sleep(30)"), {}, timeout_s=0.5, max_bytes=65536)
    assert exc.value.code == "timeout"
    assert time.monotonic() - started < 10


def test_run_codexbar_times_out_when_output_stays_open(tmp_path):
    """A child that writes some output then hangs still hits the deadline."""
    body = "sys.stdout.write('['); sys.stdout.flush(); time.sleep(30)"
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(_fake_codexbar(tmp_path, body), {}, timeout_s=0.5, max_bytes=65536)
    assert exc.value.code == "timeout"


def test_run_codexbar_caps_output(tmp_path):
    body = "sys.stdout.write('x' * 200000); sys.stdout.flush()"
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(_fake_codexbar(tmp_path, body), {}, timeout_s=30, max_bytes=1000)
    assert exc.value.code == "oversized"


def test_run_codexbar_nonzero_exit_is_a_failure(tmp_path):
    body = "print('[]'); sys.exit(3)"
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(_fake_codexbar(tmp_path, body), {}, timeout_s=30, max_bytes=65536)
    assert exc.value.code == "exit_nonzero"


def test_run_codexbar_spawn_failure():
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar("/fixture/no/such/binary", {}, timeout_s=5, max_bytes=65536)
    assert exc.value.code == "spawn_error"


# ---- refresh wiring -----------------------------------------------------------


def test_background_refresh_runs_the_account_probe(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(subscription_usage, "refresh_provider_usage_data", lambda providers, *, timeout_s=None: {})
    monkeypatch.setattr(subscription_usage, "_refresh_cursor_usage_live", lambda: None)
    monkeypatch.setattr(subscription_usage, "_refresh_api_accounts_live", lambda: None)
    monkeypatch.setattr(cau, "refresh_claude_account_usage", lambda: calls.append("accounts"))
    monkeypatch.setattr(subscription_usage, "_refresh_in_flight", threading.Lock())
    subscription_usage._run_all_refreshes()
    assert calls == ["accounts"]


def test_snapshot_never_probes(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("snapshot must not probe")

    monkeypatch.setattr(cau, "probe_account", forbidden)
    monkeypatch.setattr(cau, "_run_codexbar", forbidden)
    rows = cau.claude_accounts_snapshot()
    assert {row["status"] for row in rows.values()} == {"unknown"}
    assert {row["reason"] for row in rows.values()} == {"not_probed"}
