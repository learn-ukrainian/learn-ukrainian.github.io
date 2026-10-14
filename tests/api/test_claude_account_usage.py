"""Per-account Claude usage rows (#10630): probe, cache, payload and balancing hint.

Fixtures only: no real Claude directory is read and CodexBar never runs against
a real account. ``HOME`` points at a fixture home in every test that reaches the
probe. Subprocess tests run small ``sys.executable`` children.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import signal
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.agent_runtime.attempt_boundary import ClaudeAccountBinding
from scripts.api import claude_account_usage as cau
from scripts.api import subscription_usage

# Shape of ``codexbar usage --json --provider claude``; identity values are synthetic.
# Each label's fixture reports its own email, as two distinct accounts would.
_FAKE_EMAIL = "owner-do-not-leak@example.invalid"
_FAKE_EMAIL_B = "second-do-not-leak@example.invalid"
_FAKE_ORG = "Do-Not-Leak Organization"
_FAKE_ACCOUNT_ID = "0f0e0d0c-0b0a-4908-8706-050403020100"
# The accounts Claude Code recorded at login in each fixture directory.
_ACCOUNT_A = "0a0a0a0a-0a0a-4a0a-8a0a-0a0a0a0a0a0a"
_ACCOUNT_B = "0b0b0b0b-0b0b-4b0b-8b0b-0b0b0b0b0b0b"
_MARKER = "SYNTHETIC_PRIVATE_MARKER"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _codexbar_payload(
    *,
    session_used,
    session_expected,
    weekly_used,
    weekly_expected,
    updated: str | None = None,
    email: str = _FAKE_EMAIL,
) -> list[dict]:
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
                "updatedAt": updated or _iso(datetime.now(UTC)),
                "primary": {"windowMinutes": 300, "resetsAt": "2026-10-14T18:00:00Z", "usedPercent": session_used},
                "secondary": {
                    "windowMinutes": 10080,
                    "resetsAt": "2026-10-18T07:00:00Z",
                    "usedPercent": weekly_used,
                },
                "accountEmail": email,
                "accountOrganization": _FAKE_ORG,
                "identity": {"accountEmail": email, "accountOrganization": _FAKE_ORG},
            },
        }
    ]


def _payload_a(**kwargs) -> list[dict]:
    return _codexbar_payload(session_used=7, session_expected=61, weekly_used=74, weekly_expected=47, **kwargs)


def _payload_b(**kwargs) -> list[dict]:
    return _codexbar_payload(
        session_used=30, session_expected=50, weekly_used=20, weekly_expected=47, email=_FAKE_EMAIL_B, **kwargs
    )


# Pace is derived from the measured numbers (used minus expected), never copied
# from CodexBar's free-text summary.
EXPECTED_A = {
    "session5h": {
        "left_pct": 93.0,
        "resets_at": "2026-10-14T18:00:00Z",
        "pace": "54% in reserve",
        "pace_delta_pct": -54.0,
        "leftover_pct": 89,  # round(100 - 7 * 100 / 61)
    },
    "weekly": {
        "left_pct": 26.0,
        "resets_at": "2026-10-18T07:00:00Z",
        "pace": "27% in deficit",
        "pace_delta_pct": 27.0,
        "leftover_pct": 0,  # 74 used against 47 expected: runs out before reset
    },
}
EXPECTED_B = {
    "session5h": {
        **EXPECTED_A["session5h"],
        "left_pct": 70.0,
        "pace": "20% in reserve",
        "pace_delta_pct": -20.0,
        "leftover_pct": 40,
    },
    "weekly": {
        **EXPECTED_A["weekly"],
        "left_pct": 80.0,
        "pace": "27% in reserve",
        "pace_delta_pct": -27.0,
        "leftover_pct": 57,  # round(100 - 2000 / 47)
    },
}


def _write_login_record(path: Path, account: str | None) -> None:
    """Claude Code's global config with the account it recorded at login."""
    path.write_text(json.dumps({"oauthAccount": {"accountUuid": account}} if account else {"projects": {}}))
    path.chmod(0o600)


@pytest.fixture
def account_dirs(tmp_path, monkeypatch) -> dict[str, Path]:
    """Fixture home (label ``a``) and a second Claude directory (label ``b``), each with its login record."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    other = tmp_path / "claude-b"
    other.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _write_login_record(home / ".claude.json", _ACCOUNT_A)
    _write_login_record(other / ".claude.json", _ACCOUNT_B)
    return {"a": home / ".claude", "b": other}


def _set_login_account(dirs: dict[str, Path], label: str, account: str | None) -> None:
    record = dirs["a"].parent / ".claude.json" if label == "a" else dirs["b"] / ".claude.json"
    _write_login_record(record, account)


@pytest.fixture
def fake_probe(monkeypatch, account_dirs):
    """Route each label's CodexBar call to a fixture keyed by CLAUDE_CONFIG_DIR."""
    outputs: dict[str, object] = {"a": _payload_a, "b": _payload_b}
    calls: list[dict[str, str]] = []

    def run(codexbar, env, *, timeout_s, max_bytes):
        calls.append(dict(env))
        assert codexbar == "/fixture/bin/codexbar"
        label = next(label for label, path in account_dirs.items() if env["CLAUDE_CONFIG_DIR"] == str(path))
        result = outputs[label]
        if isinstance(result, Exception):
            raise result
        return json.dumps(result() if callable(result) else result).encode()

    monkeypatch.setattr(cau, "account_config_dir", lambda label: account_dirs[label])
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: "/fixture/bin/codexbar")
    monkeypatch.setattr(cau, "_run_codexbar", run)
    return outputs, calls


def _row(snapshot, label):
    return snapshot[f"claude:{label}"]


# Fails on origin/main: the per-account module does not exist (no rows at all).
def test_two_healthy_accounts_publish_reference_numbers(fake_probe):
    outputs, _ = fake_probe
    updated = _iso(datetime.now(UTC) - timedelta(seconds=30))
    outputs["a"] = _payload_a(updated=updated)
    outputs["b"] = _payload_b(updated=updated)
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
        assert row["updated"] == updated
        assert isinstance(row["age_s"], float)
        assert 29.0 <= row["age_s"] < 120.0


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
        (-20, 50, 100),  # clamped to the 0..100 domain, never 140
    ],
)
def test_projected_leftover_formula(used, expected, leftover):
    assert cau.projected_leftover_pct(used, expected) == leftover


def test_pace_without_expected_keeps_leftover_unknown():
    payload = _codexbar_payload(session_used=10, session_expected=None, weekly_used=20, weekly_expected=0)
    row = cau.parse_codexbar_claude(payload)
    assert row["session5h"]["leftover_pct"] is None
    assert row["session5h"]["pace"] is None
    assert row["session5h"]["pace_delta_pct"] is None
    assert row["weekly"]["leftover_pct"] is None
    assert row["weekly"]["left_pct"] == 80.0


@pytest.mark.parametrize(
    ("used", "expected", "pace", "delta"),
    [(74, 47, "27% in deficit", 27.0), (20, 47, "27% in reserve", -27.0), (47.2, 47, "on pace", 0.2)],
)
def test_pace_label_is_derived_from_the_numbers(used, expected, pace, delta):
    payload = _codexbar_payload(session_used=1, session_expected=1, weekly_used=used, weekly_expected=expected)
    weekly = cau.parse_codexbar_claude(payload)["weekly"]
    assert weekly["pace"] == pace
    assert weekly["pace_delta_pct"] == delta


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


def test_missing_binding_is_unknown_and_forgets_old_numbers(fake_probe, account_dirs, monkeypatch):
    """A missing binding is a row state, not an error; the old sample is not reused."""
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "b")["status"] == "ok"

    def resolver(label):
        return account_dirs["a"] if label == "a" else _REAL_ACCOUNT_CONFIG_DIR(label)

    monkeypatch.setattr(cau, "account_config_dir", resolver)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")  # empty: no binding file

    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "ok"
    row_b = _row(snapshot, "b")
    assert row_b["status"] == "unknown"
    assert row_b["reason"] == "claude_account_binding_missing"
    assert row_b["weekly"]["left_pct"] is None


_REAL_ACCOUNT_CONFIG_DIR = cau.account_config_dir


def test_binding_missing_through_the_real_loader(monkeypatch):
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")
    with pytest.raises(cau.ClaudeAccountRefused) as exc:
        cau.account_config_dir("b")
    assert exc.value.code == "claude_account_binding_missing"


def test_default_label_is_the_host_default_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    assert cau.account_config_dir("a") == tmp_path / ".claude"


@contextlib.contextmanager
def _open_fixture_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def test_binding_that_names_the_default_directory_is_refused(monkeypatch, tmp_path):
    default = tmp_path / ".claude"
    default.mkdir()
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    binding = ClaudeAccountBinding(label="b", config_dir=default, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    monkeypatch.setattr(cau, "_open_claude_directory", _open_fixture_dir)
    with pytest.raises(cau.ClaudeAccountRefused) as exc:
        cau.account_config_dir("b")
    assert exc.value.code == "claude_account_binding_is_default"

    other = tmp_path / "other"
    other.mkdir()
    _write_login_record(other / ".claude.json", _FAKE_ACCOUNT_ID)
    binding = ClaudeAccountBinding(label="b", config_dir=other, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    assert cau.account_config_dir("b") == other


@pytest.mark.parametrize("recorded", [_ACCOUNT_A, None])
def test_binding_whose_directory_holds_another_account_is_refused(monkeypatch, tmp_path, recorded):
    """The bound directory must hold the bound account, as the sealed seat requires."""
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    other = tmp_path / "other"
    other.mkdir()
    _write_login_record(other / ".claude.json", recorded)
    binding = ClaudeAccountBinding(label="b", config_dir=other, account_uuid=_ACCOUNT_B)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    monkeypatch.setattr(cau, "_open_claude_directory", _open_fixture_dir)
    with pytest.raises(cau.ClaudeAccountRefused) as exc:
        cau.account_config_dir("b")
    assert exc.value.code == "claude_account_unverified"


def test_payload_has_no_identity_or_path_anywhere(fake_probe, account_dirs):
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    serialized = json.dumps(fields)
    assert {row["status"] for row in fields["claude_accounts"].values()} == {"ok"}
    for forbidden in (
        _FAKE_EMAIL,
        _FAKE_EMAIL_B,
        _FAKE_ORG,
        _FAKE_ACCOUNT_ID,
        _ACCOUNT_A,
        _ACCOUNT_B,
        "example.invalid",
        str(account_dirs["b"]),
        "claude-b",
        str(Path.home()),
        "accountEmail",
        "accountOrganization",
        "accountId",
        "accountUuid",
        "identity",
        "fingerprint",
        "config_dir",
        "CLAUDE_CONFIG_DIR",
        "email",
    ):
        assert forbidden not in serialized, forbidden


def test_child_environment_is_private_and_carries_no_ambient_credential():
    environ = {
        "PATH": "/usr/bin",
        "HOME": "/fixture/home",
        "LANG": "C.UTF-8",
        "XDG_CONFIG_HOME": "/fixture/shared-config",
        "XDG_CACHE_HOME": "/fixture/shared-cache",
        "CODEXBAR_CONFIG": "/fixture/shared-config/codexbar/config.json",
        "CLAUDE_SECURESTORAGE_CONFIG_DIR": "/fixture/other-account",
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
    env = cau.child_env(Path("/fixture/claude-b"), environ, sandbox=Path("/fixture/sandbox"))
    assert env == {
        "PATH": "/usr/bin",
        "LANG": "C.UTF-8",
        "HOME": "/fixture/sandbox",
        "TMPDIR": "/fixture/sandbox",
        "XDG_CONFIG_HOME": "/fixture/sandbox",
        "XDG_CACHE_HOME": "/fixture/sandbox",
        "XDG_DATA_HOME": "/fixture/sandbox",
        "XDG_STATE_HOME": "/fixture/sandbox",
        "CODEXBAR_CONFIG": "/fixture/sandbox/codexbar-config.json",
        "CLAUDE_CONFIG_DIR": "/fixture/claude-b",
    }
    assert "ambient" not in json.dumps(env)
    assert "shared" not in json.dumps(env)


def test_probe_passes_only_the_sanitized_environment(fake_probe, account_dirs, monkeypatch):
    _, calls = fake_probe
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ambient")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "ambient")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/fixture/ambient-dir")
    monkeypatch.setenv("CODEXBAR_CONFIG", "/fixture/shared-config.json")
    cau.refresh_claude_account_usage()
    assert len(calls) == 2
    sandboxes = set()
    for env in calls:
        assert set(env) - set(cau._INHERITED_ENV_NAMES) == set(cau._SANDBOX_ENV_NAMES) | {
            "CODEXBAR_CONFIG",
            "CLAUDE_CONFIG_DIR",
        }
        assert "ANTHROPIC_API_KEY" not in env
        assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
        assert env["CODEXBAR_CONFIG"] == str(Path(env["HOME"]) / "codexbar-config.json")
        sandboxes.add(env["HOME"])
    # Each probe gets its own sandbox, removed after the probe.
    assert len(sandboxes) == 2
    assert not any(Path(sandbox).exists() for sandbox in sandboxes)
    assert {env["CLAUDE_CONFIG_DIR"] for env in calls} == {str(path) for path in account_dirs.values()}


def test_missing_codexbar_is_unknown(monkeypatch, account_dirs):
    monkeypatch.setattr(cau, "account_config_dir", lambda label: account_dirs[label])
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: None)
    cau.refresh_claude_account_usage()
    row = _row(cau.claude_accounts_snapshot(), "a")
    assert row["status"] == "unknown"
    assert row["reason"] == "missing_binary"


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"not": "a list"}, "source_mismatch"),
        ({"source": "oauth", "not": "a list"}, "no_usage"),
        ([], "bad_json"),
        ([{"provider": "codex", "source": "oauth", "usage": {}}], "provider_mismatch"),
        ([{"provider": "claude", "source": "oauth", "error": {"kind": "auth"}}], "provider_error"),
        ([{"provider": "claude", "source": "oauth", "usage": {"primary": {"usedPercent": None}}}], "no_usage"),
        ([{"provider": "claude", "source": "oauth", "usage": {"primary": {"usedPercent": True}}}], "no_usage"),
        ([{"provider": "claude", "source": "web", "usage": {"primary": {"usedPercent": 5}}}], "source_mismatch"),
        ([{"provider": "claude", "source": "cli", "usage": {"primary": {"usedPercent": 5}}}], "source_mismatch"),
        ([{"provider": "claude", "usage": {"primary": {"usedPercent": 5}}}], "source_mismatch"),
        (
            # A configured token account was selected instead of the directory.
            [{"provider": "claude", "source": "oauth", "account": "x", "usage": {"primary": {"usedPercent": 5}}}],
            "source_mismatch",
        ),
        ([{"provider": "claude", "source": "oauth", "usage": {"primary": {"usedPercent": 101}}}], "out_of_range"),
        ([{"provider": "claude", "source": "oauth", "usage": {"primary": {"usedPercent": -0.5}}}], "out_of_range"),
        (
            [
                {
                    "provider": "claude",
                    "source": "oauth",
                    "usage": {"primary": {"usedPercent": 5}},
                    "pace": {"primary": {"expectedUsedPercent": 140}},
                }
            ],
            "out_of_range",
        ),
        (
            [{"provider": "claude", "source": "oauth", "usage": {"updatedAt": "soon", "primary": {"usedPercent": 5}}}],
            "bad_timestamp",
        ),
    ],
)
def test_malformed_payloads_are_failures(payload, code):
    with pytest.raises(cau._ProbeFailed) as exc:
        cau.parse_codexbar_claude(payload)
    assert exc.value.code == code


def test_failure_codes_are_registered_and_value_free():
    with pytest.raises(AssertionError):
        cau._ProbeFailed(_MARKER)
    for code in cau.ROW_REASON_CODES:
        assert code.replace("_", "").isalnum() and code == code.lower()


def test_non_json_output_is_a_failure(fake_probe, monkeypatch):
    monkeypatch.setattr(cau, "_run_codexbar", lambda codexbar, env, *, timeout_s, max_bytes: b"not json")
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "a")["reason"] == "bad_json"


def test_missing_updated_at_uses_probe_time(fake_probe):
    outputs, _ = fake_probe
    payload = _payload_a()
    del payload[0]["usage"]["updatedAt"]
    outputs["a"] = payload
    before = datetime.now(UTC).replace(microsecond=0)
    cau.refresh_claude_account_usage()
    row = _row(cau.claude_accounts_snapshot(), "a")
    assert row["status"] == "ok"
    assert row["updated"].endswith("Z")
    assert before <= datetime.fromisoformat(row["updated"]) <= datetime.now(UTC)


# ---- review regressions (#10630 fix round 1) -----------------------------------


def _assert_withheld(row, reason):
    assert row["status"] == "unknown"
    assert row["reason"] == reason
    assert row["age_s"] is None
    assert row["updated"] is None
    for window in ("session5h", "weekly"):
        assert row[window] == dict.fromkeys(("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct"))


# Fails on b62a4a3243: two directories holding one account were both published ``ok``.
def test_two_labels_measuring_the_same_account_are_both_withheld(fake_probe, account_dirs):
    _set_login_account(account_dirs, "b", _ACCOUNT_A)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    for label in ("a", "b"):
        _assert_withheld(_row(fields["claude_accounts"], label), "account_ambiguous")
    assert fields["preferred_claude_account"] is None


# Fails on b62a4a3243: the same returned account identity for both labels was published twice.
def test_same_returned_identity_for_both_labels_is_withheld(fake_probe):
    """Distinct login records, but CodexBar reports one account for both directories."""
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert {row["status"] for row in snapshot.values()} == {"ok"}  # distinct emails, distinct accounts

    outputs, _ = fake_probe
    for label, make in (("a", _payload_a), ("b", _payload_b)):
        payload = make()
        payload[0]["usage"]["identity"] = {"accountID": "claude-owner-v1:shared"}
        outputs[label] = payload
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    for label in ("a", "b"):
        _assert_withheld(_row(snapshot, label), "account_ambiguous")


def _without_returned_identity(payload: list[dict]) -> list[dict]:
    """CodexBar's CLI output as shipped: it never asks the provider for account identity."""
    usage = payload[0]["usage"]
    for key in ("identity", "accountEmail", "accountOrganization"):
        usage.pop(key)
    return payload


# Fails on b62a4a3243: a label whose account cannot be told apart was published ``ok``.
def test_unidentifiable_account_beside_another_is_withheld(fake_probe, account_dirs):
    outputs, _ = fake_probe
    _set_login_account(account_dirs, "a", None)
    outputs["a"] = _without_returned_identity(_payload_a())
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    for label in ("a", "b"):
        _assert_withheld(_row(snapshot, label), "account_ambiguous")


def test_single_measured_account_needs_no_second_identity(fake_probe, account_dirs):
    """With label b unmeasured, label a cannot duplicate another row."""
    outputs, _ = fake_probe
    _set_login_account(account_dirs, "a", None)
    outputs["b"] = cau._ProbeFailed("timeout")
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "ok"
    assert _row(snapshot, "b")["reason"] == "timeout"


def test_returned_identity_alone_distinguishes_accounts(fake_probe, account_dirs):
    outputs, _ = fake_probe
    _set_login_account(account_dirs, "a", None)
    for label, make in (("a", _payload_a), ("b", _payload_b)):
        payload = make()
        payload[0]["usage"]["identity"] = {"accountID": f"claude-owner-v1:{label}"}
        outputs[label] = payload
    cau.refresh_claude_account_usage()
    assert {row["status"] for row in cau.claude_accounts_snapshot().values()} == {"ok"}


def test_account_fingerprints_never_leave_the_cache(fake_probe, account_dirs, caplog):
    _set_login_account(account_dirs, "b", _ACCOUNT_A)
    cau.refresh_claude_account_usage()
    samples = repr(cau._last_good)
    serialized = json.dumps(cau.routing_budget_fields()) + samples + caplog.text
    for value in (_ACCOUNT_A, _ACCOUNT_B, _FAKE_EMAIL, _FAKE_EMAIL_B):
        assert value not in serialized
        for kind in ("login", "account_id", "email"):
            assert hashlib.sha256(f"{kind}\0{value}".encode()).hexdigest() not in serialized
    assert "accounts=" not in samples and "frozenset" not in samples


def test_login_records_identify_accounts_when_codexbar_returns_none(fake_probe):
    outputs, _ = fake_probe
    outputs["a"] = _without_returned_identity(_payload_a())
    outputs["b"] = _without_returned_identity(_payload_b())
    cau.refresh_claude_account_usage()
    assert {row["status"] for row in cau.claude_accounts_snapshot().values()} == {"ok"}


def test_unprivate_login_record_leaves_the_account_unidentified(fake_probe, account_dirs):
    outputs, _ = fake_probe
    (account_dirs["a"].parent / ".claude.json").chmod(0o644)
    outputs["a"] = _without_returned_identity(_payload_a())
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    for label in ("a", "b"):
        _assert_withheld(_row(snapshot, label), "account_ambiguous")


def _fake_codexbar_emulator(tmp_path: Path) -> str:
    """A CodexBar stand-in with the installed CLI's documented source precedence.

    Configuration comes from ``CODEXBAR_CONFIG``, else ``$XDG_CONFIG_HOME/codexbar``,
    else ``$HOME/.config/codexbar``; an explicit ``--source`` wins over the configured
    one. The web source answers for whatever browser session is signed in (one shared
    fixture account); the OAuth source reads only ``$CLAUDE_CONFIG_DIR``.
    """
    body = """
def config_path():
    if os.environ.get("CODEXBAR_CONFIG"):
        return os.environ["CODEXBAR_CONFIG"]
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg and os.path.isabs(xdg):
        return os.path.join(xdg, "codexbar", "config.json")
    return os.path.join(os.environ["HOME"], ".config", "codexbar", "config.json")
try:
    with open(config_path()) as handle:
        config = json.load(handle)
    session = os.path.join(os.path.dirname(config_path()), "web-session.json")
except OSError:
    config, session = {}, None
configured = next((p.get("source") for p in config.get("providers", []) if p.get("id") == "claude"), None)
source = args[args.index("--source") + 1] if "--source" in args else (configured or "auto")
usage_file = session if source == "web" else os.path.join(os.environ["CLAUDE_CONFIG_DIR"], "usage.json")
with open(usage_file) as handle:
    weekly_used = json.load(handle)["weekly_used"]
print(json.dumps([{"provider": "claude", "source": source, "usage": {
    "primary": {"usedPercent": 10}, "secondary": {"usedPercent": weekly_used}}}]))
"""
    return _fake_codexbar(tmp_path, body)


# Fails on b62a4a3243: a shared CodexBar configuration selecting the web source
# overrode the selected directory, so both labels published the same web numbers.
def test_shared_configuration_cannot_override_the_selected_directory(account_dirs, tmp_path, monkeypatch):
    shared = tmp_path / "shared-config" / "codexbar"
    shared.mkdir(parents=True)
    (shared / "config.json").write_text(
        json.dumps({"version": 1, "providers": [{"id": "claude", "enabled": True, "source": "web"}]})
    )
    (shared / "web-session.json").write_text(json.dumps({"weekly_used": 50}))
    for label, used in (("a", 74), ("b", 20)):
        (account_dirs[label] / "usage.json").write_text(json.dumps({"weekly_used": used}))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "shared-config"))
    monkeypatch.setenv("CODEXBAR_CONFIG", str(shared / "config.json"))
    monkeypatch.setattr(cau, "account_config_dir", lambda label: account_dirs[label])
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: _fake_codexbar_emulator(tmp_path))

    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()

    assert _row(snapshot, "a")["weekly"]["left_pct"] == 26.0
    assert _row(snapshot, "b")["weekly"]["left_pct"] == 80.0
    assert {row["status"] for row in snapshot.values()} == {"ok"}


# Fails on b62a4a3243: the query did not pin CodexBar's Claude source.
def test_run_codexbar_runs_the_fixed_query_from_root_cwd_with_given_env(tmp_path):
    body = (
        "print(json.dumps({'args': args, 'cwd': os.getcwd(),"
        " 'has_dir': 'CLAUDE_CONFIG_DIR' in os.environ, 'has_key': 'ANTHROPIC_API_KEY' in os.environ}))"
    )
    raw = cau._run_codexbar(
        _fake_codexbar(tmp_path, body), {"CLAUDE_CONFIG_DIR": "/fixture/x"}, timeout_s=30, max_bytes=65536
    )
    assert json.loads(raw) == {
        "args": ["usage", "--json", "--provider", "claude", "--source", "oauth"],
        "cwd": "/",
        "has_dir": True,
        "has_key": False,
    }


# Fails on b62a4a3243: upstream free text reached the published row unchanged.
@pytest.mark.parametrize(
    ("field", "path"),
    [
        ("updated", ("usage", "updatedAt")),
        ("resets_at", ("usage", "secondary", "resetsAt")),
        ("pace", ("pace", "secondary", "summary")),
    ],
)
def test_upstream_free_text_never_reaches_a_row(fake_probe, field, path):
    outputs, _ = fake_probe
    payload = _payload_b()
    target = payload[0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = _MARKER
    outputs["b"] = payload

    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()

    assert _MARKER not in json.dumps(fields)
    row_b = _row(fields["claude_accounts"], "b")
    if field == "updated":
        _assert_withheld(row_b, "bad_timestamp")
    elif field == "resets_at":
        assert row_b["status"] == "ok"
        assert row_b["weekly"]["resets_at"] is None
    else:
        assert row_b["status"] == "ok"
        assert row_b["weekly"]["pace"] == "27% in reserve"


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("2026-10-18T07:00:00Z", "2026-10-18T07:00:00Z"),
        ("2026-10-18T09:00:00.250+02:00", "2026-10-18T07:00:00Z"),
        (1792306800, "2026-10-18T07:00:00Z"),
        ("not a time", None),
        ("0001-01-01T00:00:00+01:00", None),  # outside the representable UTC range
        ("", None),
        (True, None),
        (float("nan"), None),
    ],
)
def test_reset_times_are_parsed_and_normalised(raw, canonical):
    payload = _payload_a()
    payload[0]["usage"]["secondary"]["resetsAt"] = raw
    assert cau.parse_codexbar_claude(payload)["weekly"]["resets_at"] == canonical


# Fails on b62a4a3243: out-of-domain percentages published 140% leftover and -25% left.
@pytest.mark.parametrize(("weekly_used", "published"), [(-20, 140), (125, -25.0)])
def test_out_of_domain_percentages_are_unknown_not_published(fake_probe, weekly_used, published):
    outputs, _ = fake_probe
    outputs["b"] = _codexbar_payload(session_used=10, session_expected=50, weekly_used=weekly_used, weekly_expected=50)
    cau.refresh_claude_account_usage()
    row_b = _row(cau.claude_accounts_snapshot(), "b")
    assert published not in (row_b["weekly"]["left_pct"], row_b["weekly"]["leftover_pct"])
    _assert_withheld(row_b, "out_of_range")


def test_published_percentages_stay_in_domain(fake_probe):
    outputs, _ = fake_probe
    outputs["a"] = _codexbar_payload(session_used=0, session_expected=100, weekly_used=100, weekly_expected=0.5)
    outputs["b"] = _codexbar_payload(
        session_used=100, session_expected=100, weekly_used=0, weekly_expected=100, email=_FAKE_EMAIL_B
    )
    cau.refresh_claude_account_usage()
    for row in cau.claude_accounts_snapshot().values():
        assert row["status"] == "ok"
        for window in (row["session5h"], row["weekly"]):
            for name in ("left_pct", "leftover_pct"):
                assert window[name] is None or 0 <= window[name] <= 100
            assert -100 <= window["pace_delta_pct"] <= 100


# Fails on b62a4a3243: an old source timestamp was published ``ok`` and preferred.
def test_old_source_timestamp_is_stale_and_not_preferred(fake_probe):
    outputs, _ = fake_probe
    outputs["b"] = _payload_b(updated="2000-01-01T00:00:00Z")
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    row_b = _row(fields["claude_accounts"], "b")
    assert row_b["status"] == "stale"
    assert row_b["reason"] == "expired"
    assert row_b["updated"] == "2000-01-01T00:00:00Z"
    assert row_b["age_s"] > 26 * 365 * 86400
    assert fields["preferred_claude_account"] is None


def test_future_source_timestamp_is_capped_at_observation(fake_probe):
    outputs, _ = fake_probe
    outputs["b"] = _payload_b(updated="2999-01-01T00:00:00Z")
    cau.refresh_claude_account_usage()
    row_b = _row(cau.claude_accounts_snapshot(), "b")
    assert row_b["status"] == "ok"
    assert datetime.fromisoformat(row_b["updated"]) <= datetime.now(UTC)


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


def _gone_within(pid: int, timeout_s: float) -> bool:
    """True once ``pid`` has exited (gone or a zombie awaiting its new parent)."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
        except FileNotFoundError:
            return True
        if state in {"Z", "X"}:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


def _helper_body(record: Path, *, then: str = "") -> str:
    """The child forks a helper that closes its output and keeps running."""
    return (
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    os.close(1)\n"
        "    time.sleep(30)\n"
        "    os._exit(0)\n"
        f"open({str(record)!r}, 'w').write(str(pid))\n"
        "print('[]', flush=True)\n"
        f"{then}\n"
    )


# Fails on b62a4a3243: process-group cleanup was skipped after a successful exit.
def test_run_codexbar_kills_helpers_after_a_successful_exit(tmp_path):
    record = tmp_path / "helper.pid"
    raw = cau._run_codexbar(_fake_codexbar(tmp_path, _helper_body(record)), {}, timeout_s=30, max_bytes=65536)
    helper = int(record.read_text())
    try:
        assert raw.strip() == b"[]"
        assert _gone_within(helper, 5.0), "a helper outlived a successful probe"
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(helper, signal.SIGKILL)


def test_run_codexbar_kills_helpers_on_timeout(tmp_path):
    record = tmp_path / "helper.pid"
    script = _fake_codexbar(tmp_path, _helper_body(record, then="time.sleep(30)"))
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(script, {}, timeout_s=0.5, max_bytes=65536)
    helper = int(record.read_text())
    try:
        assert exc.value.code == "timeout"
        assert _gone_within(helper, 5.0), "a helper outlived a timed-out probe"
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(helper, signal.SIGKILL)


def test_run_codexbar_times_out_when_the_leader_outlives_its_output(tmp_path):
    """The leader closes its output but keeps running: the deadline still holds."""
    body = "print('[]', flush=True); os.close(1); time.sleep(30)"
    started = time.monotonic()
    with pytest.raises(cau._ProbeFailed) as exc:
        cau._run_codexbar(_fake_codexbar(tmp_path, body), {}, timeout_s=0.5, max_bytes=65536)
    assert exc.value.code == "timeout"
    assert time.monotonic() - started < 10


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
