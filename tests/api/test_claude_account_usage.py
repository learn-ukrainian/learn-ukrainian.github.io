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
import stat
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
# The unpatched check; ``tests/api/conftest.py`` scopes it to ``tmp_path`` in every test.
_REAL_INSIDE_GIT = cau._inside_git


def test_git_tree_recognises_every_git_layout(tmp_path):
    """The unpatched check, on layouts that are Git wherever ``tmp_path`` lives."""
    (tmp_path / "checkout" / ".git").mkdir(parents=True)
    (tmp_path / "worktree").mkdir()
    (tmp_path / "worktree" / ".git").write_text("gitdir: /fixture/primary/.git/worktrees/x\n")
    bare = tmp_path / "bare"
    (bare / "objects").mkdir(parents=True)
    (bare / "refs").mkdir()
    (bare / "HEAD").write_text("ref: refs/heads/main\n")
    for directory in ("checkout", "checkout/.git", "worktree", "bare"):
        assert cau._git_tree(tmp_path / directory)
    (tmp_path / "plain").mkdir()
    assert not cau._git_tree(tmp_path / "plain")
    assert _REAL_INSIDE_GIT((tmp_path / "checkout" / "nested" / "scratch").resolve())


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


def _write_private(path: Path, value) -> None:
    path.write_text(json.dumps(value))
    path.chmod(0o600)


def _write_login_record(path: Path, account: str | None) -> None:
    """Claude Code's global config with the account it recorded at login."""
    _write_private(path, {"oauthAccount": {"accountUuid": account}} if account else {"projects": {}})


_TOKEN_PREFIX = "synthetic-access-token-"


def _token(account: str, serial: int = 0) -> str:
    """A synthetic access token; the fixture provider names ``account`` as its owner."""
    return f"{_TOKEN_PREFIX}{serial}:{account}"


def _write_credentials(directory: Path, account: str | None, *, serial: int = 0, expires_in_s: float = 3600) -> None:
    """The directory's Claude credentials file, holding a token of ``account`` (none: removed)."""
    path = directory / ".credentials.json"
    if account is None:
        path.unlink(missing_ok=True)
        return
    expires_at = int((time.time() + expires_in_s) * 1000)
    _write_private(path, {"claudeAiOauth": {"accessToken": _token(account, serial), "expiresAt": expires_at}})


class _Provider:
    """The provider's answer to "whose token is this?" for synthetic tokens; never the network."""

    def __init__(self):
        self.calls = 0
        self.down = False

    def __call__(self, token: str) -> str:
        self.calls += 1
        if self.down or not token.startswith(_TOKEN_PREFIX):
            raise cau.ClaudeAccountRefused("claude_account_identity_unavailable")
        return token.split(":", 1)[1]


@pytest.fixture
def provider(monkeypatch) -> _Provider:
    answer = _Provider()
    monkeypatch.setattr(cau, "_claude_selected_identity", answer)
    return answer


def _settle() -> None:
    """Wait for a revalidation a serve scheduled, so the next serve sees its result."""
    thread = cau._revalidation
    if thread is not None:
        thread.join(timeout=30)
        assert not thread.is_alive()


@contextlib.contextmanager
def _open_leaf_no_follow(path):
    """The production opener's leaf rule (a link is never followed), without its
    walk from root, which refuses the shared temporary directory fixtures live under."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        raise cau.ClaudeAccountRefused("claude_account_config_dir_missing") from None
    except OSError:
        raise cau.ClaudeAccountRefused("claude_account_config_dir_not_private") from None
    try:
        yield fd
    finally:
        os.close(fd)


def _bind_b(binding_file: Path, config_dir: Path, account: str) -> None:
    """The private binding of label ``b`` to a fixture directory and the account it holds."""
    entry = {"config_dir": str(config_dir), "account_uuid": account}
    _write_private(binding_file, {"schema_version": 1, "accounts": {"b": entry}})


@pytest.fixture
def account_dirs(tmp_path, monkeypatch, provider) -> dict[str, Path]:
    """Fixture home (label ``a``) and a second Claude directory bound to label ``b``,
    each with its login record and credentials; every probe runs the real binding
    checks, and the fixture provider names each token's owner."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    other = tmp_path / "claude-b"
    other.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _write_login_record(home / ".claude.json", _ACCOUNT_A)
    _write_login_record(other / ".claude.json", _ACCOUNT_B)
    _write_credentials(home / ".claude", _ACCOUNT_A)
    _write_credentials(other, _ACCOUNT_B)
    _bind_b(tmp_path / "claude-accounts.json", other, _ACCOUNT_B)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(tmp_path / "claude-accounts.json"))
    monkeypatch.setattr(cau, "_open_claude_directory", _open_leaf_no_follow)
    yield {"a": home / ".claude", "b": other}
    _settle()


def _set_login_account(dirs: dict[str, Path], label: str, account: str | None) -> None:
    """Log a label's directory in to ``account``: its login record and credentials.

    ``None`` leaves the credentials and records no account. ``b`` stays bound to
    what its directory holds.
    """
    record = dirs["a"].parent / ".claude.json" if label == "a" else dirs["b"] / ".claude.json"
    _write_login_record(record, account)
    if account is not None:
        _write_credentials(dirs[label], account)
    if label == "b" and account is not None:
        _bind_b(dirs["b"].parent / "claude-accounts.json", dirs["b"], account)


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

    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")  # empty: no binding file

    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "ok"
    row_b = _row(snapshot, "b")
    assert row_b["status"] == "unknown"
    assert row_b["reason"] == "claude_account_binding_missing"
    assert row_b["weekly"]["left_pct"] is None


def test_binding_missing_through_the_real_loader(monkeypatch):
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")
    with pytest.raises(cau.ClaudeAccountRefused) as exc, cau.account_binding("b"):
        pass
    assert exc.value.code == "claude_account_binding_missing"


def test_default_label_is_the_host_default_directory(monkeypatch, tmp_path, provider):
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".claude").mkdir()
    _write_login_record(tmp_path / ".claude.json", _ACCOUNT_A)
    _write_credentials(tmp_path / ".claude", _ACCOUNT_A)
    with cau.account_binding("a") as binding:
        assert binding.config_dir == tmp_path / ".claude"
        assert binding.account == _ACCOUNT_A
    assert provider.calls == 1


@contextlib.contextmanager
def _open_fixture_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def test_binding_that_names_the_default_directory_is_refused(monkeypatch, tmp_path, provider):
    default = tmp_path / ".claude"
    default.mkdir()
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    binding = ClaudeAccountBinding(label="b", config_dir=default, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    monkeypatch.setattr(cau, "_open_claude_directory", _open_fixture_dir)
    with pytest.raises(cau.ClaudeAccountRefused) as exc, cau.account_binding("b"):
        pass
    assert exc.value.code == "claude_account_binding_is_default"

    other = tmp_path / "other"
    other.mkdir()
    _write_login_record(other / ".claude.json", _FAKE_ACCOUNT_ID)
    _write_credentials(other, _FAKE_ACCOUNT_ID)
    binding = ClaudeAccountBinding(label="b", config_dir=other, account_uuid=_FAKE_ACCOUNT_ID)
    monkeypatch.setattr(cau, "load_claude_account_binding", lambda label: binding)
    with cau.account_binding("b") as bound:
        assert bound.config_dir == other


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
    with pytest.raises(cau.ClaudeAccountRefused) as exc, cau.account_binding("b"):
        pass
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


@pytest.mark.parametrize(
    "outcome",
    [
        None,
        cau._ProbeFailed("timeout"),
        cau.ClaudeAccountRefused("claude_account_unverified"),
        RuntimeError("unexpected"),
    ],
    ids=["success", "probe_failed", "account_refused", "unexpected"],
)
def test_probe_sandbox_is_private_managed_scratch_removed_however_the_probe_ends(
    fake_probe, tmp_path, monkeypatch, outcome
):
    scratch_root = tmp_path / "scratch-root"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))
    seen: list[tuple[Path, int]] = []

    def run(codexbar, env, *, timeout_s, max_bytes):
        sandbox = Path(env["HOME"])
        seen.append((sandbox, sandbox.stat().st_mode))
        (sandbox / "cache-entry").write_text("probe state")
        if outcome is not None:
            raise outcome
        return json.dumps(_payload_a()).encode()

    monkeypatch.setattr(cau, "_run_codexbar", run)
    if outcome is None:
        row, _ = cau.probe_account("a")
        assert row["session5h"]["left_pct"] == 93.0
    else:
        with pytest.raises(type(outcome)):
            cau.probe_account("a")
    [(sandbox, mode)] = seen
    # Sandboxes live in a private (0700) directory of their own under the scratch root.
    assert sandbox.parent == scratch_root / cau._SANDBOX_PARENT
    assert stat.S_IMODE(sandbox.parent.stat().st_mode) == 0o700
    assert sandbox.name.startswith("lu-claude-usage-")
    assert stat.S_IMODE(mode) == 0o700
    assert not sandbox.exists()
    assert list(sandbox.parent.iterdir()) == []


@contextlib.contextmanager
def _restore_modes(root: Path):
    """Give every directory under ``root`` back to its owner so the fixture tree can be removed."""
    try:
        yield
    finally:
        for dirpath, dirnames, _ in os.walk(root, topdown=True):
            for name in dirnames:
                path = Path(dirpath) / name
                if not path.is_symlink():
                    path.chmod(0o700)


def _populate(sandbox: Path, outside: Path) -> list[Path]:
    """A sandbox a probe could leave: a populated nested directory the owner cannot
    read, write or search, and links to a directory and a file outside it."""
    locked = sandbox / "cache" / "locked"
    (locked / "deeper").mkdir(parents=True)
    (locked / "deeper" / "entry").write_text("probe state")
    (locked / "entry").write_text("probe state")
    (locked / "outside-dir").symlink_to(outside)
    (sandbox / "outside-dir").symlink_to(outside)
    (sandbox / "outside-file").symlink_to(outside / "keep")
    (locked / "deeper").chmod(0o000)
    locked.chmod(0o000)
    return [locked, locked / "deeper"]


@pytest.fixture
def outside_dir(tmp_path) -> Path:
    """A directory outside the sandbox, reached only through links; never changed."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("not the probe's")
    outside.chmod(0o500)
    yield outside
    outside.chmod(0o700)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
@pytest.mark.parametrize("lock_sandbox", [False, True], ids=["nested_000", "sandbox_000"])
def test_probe_sandbox_removes_directories_the_owner_locked(tmp_path, monkeypatch, outside_dir, lock_sandbox):
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch-root"))
    with _restore_modes(tmp_path / "scratch-root"), cau._probe_sandbox() as sandbox:
        _populate(sandbox, outside_dir)
        if lock_sandbox:
            sandbox.chmod(0o000)
    assert not os.path.lexists(sandbox)
    assert cau.probe_sandbox_residue() == 0
    # Links were removed, never followed: what they pointed at is untouched.
    assert stat.S_IMODE(outside_dir.stat().st_mode) == 0o500
    assert (outside_dir / "keep").read_text() == "not the probe's"


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_probe_sandbox_reports_residue_it_cannot_remove(tmp_path, monkeypatch, outside_dir, caplog, fake_probe):
    """Removal that truly fails is counted and logged without a value; the probe still succeeds."""
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch-root"))
    monkeypatch.setattr(cau, "_grant_owner", lambda path: None)
    seen: list[Path] = []

    def run(codexbar, env, *, timeout_s, max_bytes):
        seen.append(Path(env["HOME"]))
        _populate(seen[0], outside_dir)
        return json.dumps(_payload_a()).encode()

    monkeypatch.setattr(cau, "_run_codexbar", run)
    with _restore_modes(tmp_path / "scratch-root"), caplog.at_level("WARNING", logger=cau.__name__):
        row, _ = cau.probe_account("a")
        assert os.path.lexists(seen[0])
    assert row["session5h"]["left_pct"] == 93.0
    assert cau.probe_sandbox_residue() == 1
    [record] = [record for record in caplog.records if record.name == cau.__name__]
    assert record.levelname == "WARNING"
    assert str(tmp_path) not in record.getMessage()
    assert record.args in ((), None)
    cau._reset_for_tests()
    assert cau.probe_sandbox_residue() == 0


def _assert_sandbox_refused(spawned: list[object]) -> None:
    with pytest.raises(cau._ProbeFailed) as raised:
        with cau._probe_sandbox():
            spawned.append("sandbox")
    assert raised.value.code == "sandbox_unavailable"
    # No OS error, and so no path, travels with the refusal.
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None or raised.value.__suppress_context__
    assert spawned == []


@pytest.mark.parametrize(
    ("which", "mode"),
    [("parent", 0o777), ("parent", 0o770), ("parent", 0o707), ("root", 0o777), ("root", 0o707)],
)
def test_probe_sandbox_refuses_a_parent_others_can_write(tmp_path, monkeypatch, which, mode):
    root = tmp_path / "scratch-root"
    (root / cau._SANDBOX_PARENT).mkdir(parents=True, mode=0o700)
    target = root if which == "root" else root / cau._SANDBOX_PARENT
    target.chmod(mode)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    _assert_sandbox_refused([])


@pytest.mark.parametrize("which", ["parent", "root"])
def test_probe_sandbox_accepts_a_sticky_shared_directory(tmp_path, monkeypatch, which):
    root = tmp_path / "scratch-root"
    (root / cau._SANDBOX_PARENT).mkdir(parents=True, mode=0o700)
    target = root if which == "root" else root / cau._SANDBOX_PARENT
    target.chmod(0o1777)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    with cau._probe_sandbox() as sandbox:
        assert stat.S_IMODE(sandbox.stat().st_mode) == 0o700
    assert not sandbox.exists()


@pytest.mark.parametrize("own_group", [True, False])
def test_probe_sandbox_root_may_be_shared_only_with_the_users_own_group(tmp_path, monkeypatch, own_group):
    """The host default root is group-writable for the user's private group."""
    root = tmp_path / "scratch-root"
    root.mkdir()
    root.chmod(0o775)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    if not own_group:
        gid = os.getgid()
        monkeypatch.setattr(cau.os, "getgid", lambda: gid + 1)
        _assert_sandbox_refused([])
        return
    with cau._probe_sandbox() as sandbox:
        assert stat.S_IMODE(sandbox.parent.stat().st_mode) == 0o700
    assert not sandbox.exists()


def test_probe_sandbox_refuses_a_parent_owned_by_another_user(tmp_path, monkeypatch):
    root = tmp_path / "scratch-root"
    (root / cau._SANDBOX_PARENT).mkdir(parents=True, mode=0o700)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    uid = os.getuid()
    monkeypatch.setattr(cau.os, "getuid", lambda: uid + 1)
    _assert_sandbox_refused([])


@pytest.mark.parametrize("layout", ["checkout", "linked_worktree", "git_directory", "bare_repository"])
def test_probe_sandbox_refuses_a_root_inside_git(tmp_path, monkeypatch, layout):
    repo = tmp_path / "repo"
    repo.mkdir()
    if layout == "checkout":
        (repo / ".git").mkdir()
        root = repo / "nested" / "scratch"
    elif layout == "linked_worktree":
        (repo / ".git").write_text("gitdir: /fixture/primary/.git/worktrees/x\n")
        root = repo / "scratch"
    elif layout == "git_directory":
        root = repo / ".git" / "scratch"
    else:
        (repo / "HEAD").write_text("ref: refs/heads/main\n")
        (repo / "objects").mkdir()
        (repo / "refs").mkdir()
        root = repo / "scratch"
    root.mkdir(parents=True)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    _assert_sandbox_refused([])
    assert not (root / cau._SANDBOX_PARENT).exists()


@pytest.mark.parametrize("override", ["missing-parent/scratch", "a-file", "link-to-dir", "relative/scratch"])
def test_probe_sandbox_turns_an_unusable_override_into_a_typed_failure(tmp_path, monkeypatch, override):
    (tmp_path / "a-file").write_text("not a directory")
    (tmp_path / "real-dir").mkdir()
    (tmp_path / "link-to-dir").symlink_to(tmp_path / "real-dir")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LU_SCRATCH_ROOT", override if override.startswith("relative") else str(tmp_path / override))
    _assert_sandbox_refused([])
    assert list((tmp_path / "real-dir").iterdir()) == []
    assert not (tmp_path / "relative").exists()


@pytest.mark.exercises_default_scratch_root
def test_probe_sandbox_never_falls_back_to_the_system_temp(tmp_path, monkeypatch):
    from scripts.common import scratch

    system_temp = tmp_path / "system-temp"
    system_temp.mkdir()
    monkeypatch.setattr(scratch.tempfile, "tempdir", str(system_temp))
    monkeypatch.setattr(scratch, "DEFAULT_SCRATCH_ROOT", tmp_path / "missing" / "lu")
    _assert_sandbox_refused([])
    assert list(system_temp.iterdir()) == []


@pytest.mark.exercises_default_scratch_root
def test_probe_sandbox_uses_the_default_root_when_no_override(tmp_path, monkeypatch):
    from scripts.common import scratch

    with cau._probe_sandbox() as sandbox:
        assert sandbox.parent == scratch.DEFAULT_SCRATCH_ROOT / cau._SANDBOX_PARENT
    assert not sandbox.exists()


@pytest.mark.parametrize("failing", ["root", "parent", "sandbox"])
def test_every_sandbox_creation_failure_is_typed(tmp_path, monkeypatch, failing):
    """The root, the private parent and the sandbox are created in that order; any
    of them failing is the typed refusal, never a raw OS error."""
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch-root"))
    real_mkdir = os.mkdir
    failing_call = ["root", "parent", "sandbox"].index(failing)
    made: list[object] = []

    def mkdir(path, mode=0o777, *, dir_fd=None):
        made.append(path)
        if len(made) - 1 == failing_call:
            raise OSError(28, "No space left on device")
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(cau.os, "mkdir", mkdir)
    _assert_sandbox_refused([])
    assert len(made) == failing_call + 1


@pytest.mark.parametrize("mismatch", ["parent", "sandbox"])
def test_probe_sandbox_refuses_a_path_that_does_not_name_what_it_created(tmp_path, monkeypatch, mismatch):
    """A path redirected between creation and use is refused; a created sandbox is removed."""
    root = tmp_path / "scratch-root"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    real_same_file = cau._same_file

    def same_file(path, info):
        is_sandbox = path.name.startswith(cau._SANDBOX_PREFIX)
        return real_same_file(path, info) and is_sandbox != (mismatch == "sandbox")

    monkeypatch.setattr(cau, "_same_file", same_file)
    _assert_sandbox_refused([])
    assert list((root / cau._SANDBOX_PARENT).iterdir()) == []


def test_sandbox_failure_is_the_rows_registered_reason(fake_probe, tmp_path, monkeypatch):
    (tmp_path / "a-file").write_text("not a directory")
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "a-file"))
    cau.refresh_claude_account_usage()
    _, calls = fake_probe
    assert calls == []
    row = _row(cau.claude_accounts_snapshot(), "a")
    assert (row["status"], row["reason"]) == ("unknown", "sandbox_unavailable")
    assert "sandbox_unavailable" in cau.ROW_REASON_CODES


def test_missing_codexbar_is_unknown(monkeypatch, account_dirs):
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
# Since af927d37bd the unidentifiable label is withheld on its own; the other,
# proven by the provider, cannot be duplicated by a row that is not served.
def test_unidentifiable_account_beside_another_is_withheld(fake_probe, account_dirs):
    outputs, _ = fake_probe
    _write_credentials(account_dirs["a"], None)
    outputs["a"] = _without_returned_identity(_payload_a())
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    _assert_withheld(_row(fields["claude_accounts"], "a"), "claude_account_credentials_missing")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"
    assert fields["preferred_claude_account"] is None


def test_single_measured_account_needs_no_second_identity(fake_probe, account_dirs):
    """With label b unmeasured, label a cannot duplicate another row."""
    outputs, _ = fake_probe
    outputs["a"] = _without_returned_identity(_payload_a())
    outputs["b"] = cau._ProbeFailed("timeout")
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    assert _row(snapshot, "a")["status"] == "ok"
    assert _row(snapshot, "b")["reason"] == "timeout"


# Fails on af927d37bd: distinct opaque ids CodexBar returned were taken as proof
# for a label with no recorded account.
def test_returned_identity_alone_is_not_proof(fake_probe, account_dirs):
    outputs, _ = fake_probe
    _set_login_account(account_dirs, "a", None)
    for label, make in (("a", _payload_a), ("b", _payload_b)):
        payload = make()
        payload[0]["usage"]["identity"] = {"accountID": f"claude-owner-v1:{label}"}
        outputs[label] = payload
    cau.refresh_claude_account_usage()
    snapshot = cau.claude_accounts_snapshot()
    _assert_withheld(_row(snapshot, "a"), "claude_account_unverified")
    assert _row(snapshot, "b")["status"] == "ok"  # b's credentials are proven its own


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
    _assert_withheld(_row(snapshot, "a"), "claude_account_config_not_private")
    assert _row(snapshot, "b")["status"] == "ok"


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


# ---- review regressions (#10630 fix round 2) -----------------------------------
# Attribution holds through the probe and the cache: every case below measures the
# real binding checks against fixture directories, never a real account.

_ACCOUNT_C = "0c0c0c0c-0c0c-4c0c-8c0c-0c0c0c0c0c0c"
_FIXTURE_ACCOUNTS = {"a": _ACCOUNT_A, "b": _ACCOUNT_B, "c": _ACCOUNT_C}
_FIXTURE_WEEKLY_USED = {"a": 74, "b": 20, "c": 50}
_REAL_RUN_CODEXBAR = cau._run_codexbar


class _BoundFixture:
    """Label ``a`` is the fixture home's ``.claude``; ``b`` is bound by a private binding file.

    Each directory holds ``usage.json``, the answer a probe of that directory gives,
    so a probe that reads another directory reports that directory's numbers
    (weekly left: a 26, b 80, c 50).
    """

    def __init__(self, root: Path, monkeypatch):
        self.root = root
        self.home = root / "home"
        self.dirs = {"a": self.home / ".claude", "b": root / "selected", "c": root / "replacement"}
        for label, directory in self.dirs.items():
            directory.mkdir(parents=True, mode=0o700)
            self.answer(label, self.payload(label))
            _write_login_record(directory / ".claude.json", _FIXTURE_ACCOUNTS[label])
            _write_credentials(directory, _FIXTURE_ACCOUNTS[label])
        _write_login_record(self.home / ".claude.json", _ACCOUNT_A)
        self.binding = root / "claude-accounts.json"
        self.bind("b")
        self.hook = None
        self.calls = 0
        monkeypatch.setenv("HOME", str(self.home))
        monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(self.binding))
        monkeypatch.setattr(cau, "_open_claude_directory", _open_leaf_no_follow)
        monkeypatch.setattr(cau, "_codexbar_bin", lambda: "/fixture/bin/codexbar")
        monkeypatch.setattr(cau, "_run_codexbar", self.run)

    def payload(self, label: str) -> list[dict]:
        """The directory's answer naming no account; a case adds the identity it tests."""
        used = _FIXTURE_WEEKLY_USED[label]
        payload = _codexbar_payload(session_used=10, session_expected=50, weekly_used=used, weekly_expected=50)
        return _without_returned_identity(payload)

    def answer(self, label: str, payload: list[dict]) -> None:
        _write_private(self.dirs[label] / "usage.json", payload)

    def bind(self, label: str) -> None:
        """Bind ``b`` to a fixture directory and the account it holds."""
        _bind_b(self.binding, self.dirs[label], _FIXTURE_ACCOUNTS[label])

    def unbind(self) -> None:
        _write_private(self.binding, {"schema_version": 1, "accounts": {}})

    def run(self, codexbar, env, *, timeout_s, max_bytes):
        self.calls += 1
        directory = Path(env["CLAUDE_CONFIG_DIR"])
        if self.hook is not None:
            self.hook(directory)
        return (directory / "usage.json").read_bytes()


@pytest.fixture
def bound(tmp_path, monkeypatch, provider) -> _BoundFixture:
    yield _BoundFixture(tmp_path, monkeypatch)
    _settle()


def _replace_with_link(directory: Path, target: Path) -> None:
    directory.rename(directory.with_name(directory.name + "-moved"))
    directory.symlink_to(target, target_is_directory=True)


def _replace_with_directory(directory: Path, replacement: Path) -> None:
    directory.rename(directory.with_name(directory.name + "-moved"))
    replacement.rename(directory)


def _assert_not_published(fields, label, *, reason=None):
    row = _row(fields["claude_accounts"], label)
    published = (label, row["status"], row["reason"], row["weekly"]["left_pct"], fields["preferred_claude_account"])
    assert row["status"] == "unknown", f"published (label, status, reason, weekly left, preferred): {published}"
    assert row["weekly"]["left_pct"] is None
    assert fields["preferred_claude_account"] is None
    if reason is not None:
        assert row["reason"] == reason


def test_bound_fixture_publishes_each_directory(bound):
    """The fixture's healthy baseline, so the withheld cases below are not vacuous."""
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    assert _row(fields["claude_accounts"], "a")["status"] == "ok"
    assert _row(fields["claude_accounts"], "a")["weekly"]["left_pct"] == 26.0
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"
    assert _row(fields["claude_accounts"], "b")["weekly"]["left_pct"] == 80.0
    assert fields["preferred_claude_account"] == "b"


# Fails on e75cb7e113: the validated directory was released before the probe, so a
# directory replaced after validation was measured and published ``ok`` as ``b``.
@pytest.mark.parametrize("replacement", ["link", "directory"])
def test_selected_directory_replaced_during_the_probe_is_withheld(bound, replacement):
    selected = bound.dirs["b"]
    if replacement == "directory":
        # Same recorded account and credentials owner, different directory, the default's numbers.
        bound.answer("c", bound.payload("a"))
        _write_login_record(bound.dirs["c"] / ".claude.json", _ACCOUNT_B)
        _write_credentials(bound.dirs["c"], _ACCOUNT_B)

    def swap(directory):
        if directory == selected:
            if replacement == "link":
                _replace_with_link(selected, bound.dirs["a"])
            else:
                _replace_with_directory(selected, bound.dirs["c"])
            bound.hook = None

    bound.hook = swap
    cau.refresh_claude_account_usage()
    _assert_not_published(cau.routing_budget_fields(), "b")


# Fails on e75cb7e113: a real child that replaced the selected directory after
# validation read the default's answer, published ``ok`` as ``b``.
def test_real_probe_replacing_the_selected_directory_is_withheld(bound, monkeypatch):
    body = (
        "directory = os.environ['CLAUDE_CONFIG_DIR']\n"
        f"if directory == {str(bound.dirs['b'])!r}:\n"
        "    os.rename(directory, directory + '-moved')\n"
        f"    os.symlink({str(bound.dirs['a'])!r}, directory)\n"
        "print(open(os.path.join(directory, 'usage.json')).read())"
    )
    monkeypatch.setattr(cau, "_run_codexbar", _REAL_RUN_CODEXBAR)
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: _fake_codexbar(bound.root, body))
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    assert _row(fields["claude_accounts"], "a")["weekly"]["left_pct"] == 26.0  # the child really ran
    _assert_not_published(fields, "b")


# Fails on e75cb7e113: the default directory was never validated, so a link to the
# selected directory published the selected account's numbers as ``a``.
def test_default_directory_linked_to_the_selected_directory_is_withheld(bound):
    _replace_with_link(bound.dirs["a"], bound.dirs["b"])
    cau.refresh_claude_account_usage()
    _assert_not_published(cau.routing_budget_fields(), "a")


# Fails on e75cb7e113: the default label had no before/after check, so a default
# directory or login replaced during the probe was published ``ok``.
@pytest.mark.parametrize("change", ["directory", "login"])
def test_default_account_changed_during_the_probe_is_withheld(bound, change):
    default = bound.dirs["a"]

    def swap(directory):
        if directory == default:
            if change == "directory":
                _replace_with_directory(default, bound.dirs["c"])
            else:
                _write_login_record(bound.home / ".claude.json", _ACCOUNT_C)
            bound.hook = None

    bound.hook = swap
    cau.refresh_claude_account_usage()
    _assert_not_published(cau.routing_budget_fields(), "a")


# Fails on e75cb7e113: a returned account other than the bound one was published ``ok``,
# because returned and recorded identities were compared in different namespaces.
@pytest.mark.parametrize("a_named", [False, True])
def test_named_account_other_than_the_binding_is_withheld(bound, a_named):
    payload = bound.payload("b")
    payload[0]["usage"]["identity"] = {"accountID": _ACCOUNT_A}
    bound.answer("b", payload)
    if a_named:
        payload = bound.payload("a")
        payload[0]["usage"]["identity"] = {"accountID": _ACCOUNT_A}
        bound.answer("a", payload)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    _assert_not_published(fields, "b")
    assert _row(fields["claude_accounts"], "b")["reason"] == "claude_account_unverified"


def test_named_account_matching_the_binding_is_published(bound):
    for label, account in (("a", _ACCOUNT_A.upper()), ("b", f" {_ACCOUNT_B} ")):
        payload = bound.payload(label)
        payload[0]["usage"]["identity"] = {"accountID": account}
        bound.answer(label, payload)
    cau.refresh_claude_account_usage()
    assert {row["status"] for row in cau.claude_accounts_snapshot().values()} == {"ok"}


# Fails on e75cb7e113: one answer named its account and the other named none, and
# both rows were published ``ok``.
def test_named_answer_beside_an_unnamed_one_is_withheld(bound):
    payload = bound.payload("b")
    payload[0]["usage"]["identity"] = {"accountID": _ACCOUNT_B}
    bound.answer("b", payload)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    for label in ("a", "b"):
        _assert_withheld(_row(fields["claude_accounts"], label), "account_ambiguous")
    assert fields["preferred_claude_account"] is None


# Fails on e75cb7e113: samples were keyed by label only, so a sample measured under
# the old binding stayed ``ok`` and preferred after the binding changed.
@pytest.mark.parametrize(
    ("change", "reason"), [("reassigned", "not_probed"), ("removed", "claude_account_binding_missing")]
)
def test_cached_sample_is_withheld_once_its_binding_changes(bound, change, reason):
    cau.refresh_claude_account_usage()
    assert cau.routing_budget_fields()["preferred_claude_account"] == "b"
    probes = bound.calls

    if change == "reassigned":
        bound.bind("c")
    else:
        bound.unbind()
    fields = cau.routing_budget_fields()

    # Serving sees the binding file change without reading it.
    _assert_not_published(fields, "b", reason="not_probed")
    assert _row(fields["claude_accounts"], "a")["status"] == "ok"
    _settle()  # the background revalidation reads the binding and names why
    _assert_not_published(cau.routing_budget_fields(), "b", reason=reason)
    assert bound.calls == probes  # neither serving nor revalidation probed


# Fails on e75cb7e113: the default label's sample stayed ``ok`` after its directory
# or recorded login changed between refreshes.
@pytest.mark.parametrize("change", ["directory", "login"])
def test_cached_default_sample_is_withheld_once_the_default_account_changes(bound, change):
    cau.refresh_claude_account_usage()
    assert _row(cau.claude_accounts_snapshot(), "a")["status"] == "ok"

    if change == "directory":
        _replace_with_directory(bound.dirs["a"], bound.dirs["c"])
    else:
        _write_login_record(bound.home / ".claude.json", _ACCOUNT_C)
    fields = cau.routing_budget_fields()

    _assert_not_published(fields, "a", reason="not_probed")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"


def test_restored_binding_is_rearmed_by_revalidation(bound, monkeypatch):
    """A binding restored before any revalidation ran keeps its sample once revalidated."""
    cau.refresh_claude_account_usage()
    monkeypatch.setattr(cau, "_schedule_revalidation", lambda: None)
    bound.unbind()
    assert _row(cau.claude_accounts_snapshot(), "b")["reason"] == "not_probed"
    bound.bind("b")
    assert _row(cau.claude_accounts_snapshot(), "b")["reason"] == "not_probed"  # its file was rewritten
    cau.revalidate_claude_accounts()
    assert _row(cau.claude_accounts_snapshot(), "b")["status"] == "ok"


def test_binding_generation_and_fingerprints_are_never_published(bound, caplog):
    cau.refresh_claude_account_usage()
    accounts = cau._last_good["b"].accounts
    serialized = json.dumps(cau.routing_budget_fields()) + repr(cau._last_good) + repr(accounts) + caplog.text
    for secret in (accounts.generation, *accounts.fingerprints):
        assert secret.hex() not in serialized
        assert repr(secret) not in serialized
    assert "generation" not in serialized and "fingerprints" not in serialized


@pytest.mark.parametrize(
    ("make", "code"),
    [
        (lambda default: None, "claude_account_config_dir_missing"),
        (lambda default: default.write_text("{}"), "claude_account_config_dir_not_private"),
        (lambda default: default.symlink_to(default.parent / "elsewhere"), "claude_account_config_dir_not_private"),
    ],
)
def test_default_directory_must_be_a_real_directory(monkeypatch, tmp_path, make, code):
    monkeypatch.setattr(cau.Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / "elsewhere").mkdir()
    make(tmp_path / ".claude")
    with pytest.raises(cau.ClaudeAccountRefused) as exc, cau.account_binding("a"):
        pass
    assert exc.value.code == code


def test_unreadable_default_directory_is_unavailable(monkeypatch, tmp_path):
    def refuse(*_args, **_kwargs):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(cau.os, "open", refuse)
    with pytest.raises(cau.ClaudeAccountRefused) as exc, cau._open_default_directory(tmp_path):
        pass
    assert exc.value.code == "claude_account_config_dir_unavailable"


def test_default_answer_naming_the_other_account_is_refused(bound):
    for label, account in (("a", _ACCOUNT_A), ("b", _ACCOUNT_B)):
        payload = bound.payload(label)
        payload[0]["usage"]["identity"] = {"accountID": account}
        bound.answer(label, payload)
    cau.refresh_claude_account_usage()
    assert {row["status"] for row in cau.claude_accounts_snapshot().values()} == {"ok"}

    # Named as b's account, the default answer contradicts its proven account.
    payload = bound.payload("a")
    payload[0]["usage"]["identity"] = {"accountID": _ACCOUNT_B}
    bound.answer("a", payload)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    _assert_not_published(fields, "a", reason="claude_account_unverified")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"


def test_unidentified_default_beside_a_bound_account_is_withheld(bound):
    """Neither answer names an account and the default records none: it cannot be proven."""
    _write_login_record(bound.home / ".claude.json", None)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    _assert_not_published(fields, "a", reason="claude_account_unverified")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"


def test_binding_check_defect_never_publishes_ok(bound, monkeypatch):
    """Serving never runs the binding check; a refresh that hits a defect in it marks rows stale."""
    cau.refresh_claude_account_usage()

    def broken(label, **_kwargs):
        raise RuntimeError(_MARKER)

    monkeypatch.setattr(cau, "account_binding", broken)
    assert {row["status"] for row in cau.claude_accounts_snapshot().values()} == {"ok"}  # files unchanged
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    for label in ("a", "b"):
        row = _row(fields["claude_accounts"], label)
        assert (row["status"], row["reason"]) == ("stale", "probe_error")
    assert fields["preferred_claude_account"] is None
    assert _MARKER not in json.dumps(fields)


def test_sample_without_attribution_is_refused():
    with pytest.raises(TypeError):
        cau._record("a", {"session5h": {}, "weekly": {}, "updated": None}, None)
    assert "a" not in cau._last_good


# ---- review regressions (#10630 fix round 3) -----------------------------------
# A row is ``ok`` only on positive proof: the provider names the bound account as
# the owner of the credentials the probed directory holds. Serving never reads or
# parses an account file; it compares the validated files' cheap stat facts.


def _token_measuring_codexbar(root: Path, *, identity: str) -> str:
    """A CodexBar stand-in that measures whichever account its directory's token belongs to.

    Weekly used: a 74, b 20, c 10. ``identity`` is what the answer names: nothing,
    or an email derived from the token.
    """
    used = {_token(account): value for account, value in ((_ACCOUNT_A, 74), (_ACCOUNT_B, 20), (_ACCOUNT_C, 10))}
    body = (
        "path = os.path.join(os.environ['CLAUDE_CONFIG_DIR'], '.credentials.json')\n"
        "token = json.load(open(path))['claudeAiOauth']['accessToken']\n"
        f"usage = {{'primary': {{'usedPercent': 10}}, 'secondary': {{'usedPercent': {used!r}[token]}}}}\n"
    )
    if identity == "email":
        body += "usage['identity'] = {'accountEmail': token[-12:] + '@synthetic.invalid'}\n"
    body += "print(json.dumps([{'provider': 'claude', 'source': 'oauth', 'usage': usage}]))"
    return _fake_codexbar(root, body)


# Fails on af927d37bd: the measured account changed inside the selected directory
# while its binding and login record did not, and b was published ``ok`` (weekly
# left 90) and preferred, with no answer identity or an email-only one.
@pytest.mark.parametrize("identity", ["omitted", "email"])
def test_measured_account_drift_under_an_unchanged_binding_is_withheld(bound, monkeypatch, identity):
    monkeypatch.setattr(cau, "_run_codexbar", _REAL_RUN_CODEXBAR)
    monkeypatch.setattr(cau, "_codexbar_bin", lambda: _token_measuring_codexbar(bound.root, identity=identity))
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"
    assert _row(fields["claude_accounts"], "b")["weekly"]["left_pct"] == 80.0  # the child measured b

    # The selected directory now holds a third account's credentials; its binding
    # and the login record beside it still name b.
    _write_credentials(bound.dirs["b"], _ACCOUNT_C)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()

    _assert_not_published(fields, "b", reason="claude_account_unverified")
    assert "b" not in cau._last_good


# Fails on af927d37bd: answers with no provider proof of their account were
# published ``ok`` on login metadata and pairwise inequality alone.
@pytest.mark.parametrize(
    "identity",
    [None, {"accountEmail": _FAKE_EMAIL}, {"accountID": "claude-owner-v1:synthetic"}],
    ids=["omitted", "email", "opaque"],
)
def test_answer_without_provider_proof_is_withheld(bound, identity):
    for label in ("a", "b"):
        _write_credentials(bound.dirs[label], None)
        payload = bound.payload(label)
        if identity is not None:
            payload[0]["usage"]["identity"] = {
                key: f"{label}-{value}" for key, value in identity.items()
            }  # distinct per label
        bound.answer(label, payload)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    for label in ("a", "b"):
        _assert_not_published(fields, label, reason="claude_account_credentials_missing")


# Fails on af927d37bd: rows whose credentials could not be shown to belong to the
# bound account were published ``ok``.
@pytest.mark.parametrize(
    ("break_proof", "reason"),
    [
        (lambda bound, provider: _write_credentials(bound.dirs["b"], _ACCOUNT_B, expires_in_s=-60), "expired"),
        (lambda bound, provider: setattr(provider, "down", True), "identity_unavailable"),
        (lambda bound, provider: (bound.dirs["b"] / ".credentials.json").chmod(0o644), "not_private"),
        (lambda bound, provider: (bound.dirs["b"] / ".credentials.json").write_text("{"), "invalid"),
    ],
)
def test_unprovable_credentials_withhold_the_row(bound, provider, break_proof, reason):
    break_proof(bound, provider)
    cau.refresh_claude_account_usage()
    code = f"claude_account_{reason}" if reason == "identity_unavailable" else f"claude_account_credentials_{reason}"
    _assert_not_published(cau.routing_budget_fields(), "b", reason=code)


# Fails on af927d37bd: the directory's credentials were replaced by another
# account's during the probe and the sample was published ``ok``.
@pytest.mark.parametrize(("account", "published"), [(_ACCOUNT_C, False), (_ACCOUNT_B, True)])
def test_credentials_rewritten_during_the_probe(bound, provider, account, published):
    def rewrite(directory):
        if directory == bound.dirs["b"]:
            _write_credentials(directory, account, serial=1)
            bound.hook = None

    bound.hook = rewrite
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    if published:
        assert _row(fields["claude_accounts"], "b")["status"] == "ok"  # a refreshed token of the same account
        assert provider.calls == 3  # a, b before the probe, b's new token after it
    else:
        _assert_not_published(fields, "b", reason="claude_account_unverified")


# Fails on af927d37bd: the default label with no recorded account was attributed
# to whatever its answer named or left unnamed, instead of being refused.
def test_default_without_a_recorded_account_is_unverified(bound):
    _write_login_record(bound.home / ".claude.json", None)
    payload = bound.payload("a")
    payload[0]["usage"]["identity"] = {"accountID": _ACCOUNT_A}
    bound.answer("a", payload)
    cau.refresh_claude_account_usage()
    fields = cau.routing_budget_fields()
    _assert_not_published(fields, "a", reason="claude_account_unverified")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"  # b is proven on its own


def test_credentials_never_leave_the_refresh(bound, caplog):
    cau.refresh_claude_account_usage()
    serialized = json.dumps(cau.routing_budget_fields()) + repr(cau._last_good) + caplog.text
    for account in _FIXTURE_ACCOUNTS.values():
        assert _token(account) not in serialized
    assert _TOKEN_PREFIX not in serialized


class _NoRead:
    """Raises if serving opens, reads or parses anything."""

    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, name):
        def refuse(*_args, **_kwargs):
            self.calls.append(name)
            raise AssertionError(f"serve called {name}")

        return refuse


def _forbid_reads(monkeypatch) -> _NoRead:
    import builtins

    from scripts.agent_runtime import attempt_boundary

    guard = _NoRead()
    for module, name in (
        (cau.json, "loads"),
        (attempt_boundary.json, "loads"),
        (attempt_boundary.os, "read"),
        (cau.os, "open"),
        (builtins, "open"),
    ):
        monkeypatch.setattr(module, name, guard(f"{module.__name__}.{name}"))
    for name in ("account_binding", "_claude_selected_identity", "probe_account"):
        monkeypatch.setattr(cau, name, guard(f"cau.{name}"))
    return guard


# Fails on af927d37bd: serving re-read and fully parsed every account record on
# the event loop (two 16 MiB records held it for over a second).
def test_serving_never_reads_or_parses_account_files(bound, monkeypatch):
    cau.refresh_claude_account_usage()
    scheduled: list[str] = []
    monkeypatch.setattr(cau, "_schedule_revalidation", lambda: scheduled.append("revalidate"))
    # A same-account rewrite of the default login record, as Claude Code makes.
    _write_login_record(bound.home / ".claude.json", _ACCOUNT_A)
    (bound.home / ".claude.json").write_text(json.dumps({"oauthAccount": {"accountUuid": _ACCOUNT_A}, "n": 1}))

    with monkeypatch.context() as serving:
        guard = _forbid_reads(serving)
        fields = cau.routing_budget_fields()

    assert guard.calls == []
    _assert_not_published(fields, "a", reason="not_probed")
    assert _row(fields["claude_accounts"], "b")["status"] == "ok"
    assert scheduled == ["revalidate"]


def test_unchanged_files_serve_without_scheduling(bound, monkeypatch):
    cau.refresh_claude_account_usage()
    scheduled: list[str] = []
    monkeypatch.setattr(cau, "_schedule_revalidation", lambda: scheduled.append("revalidate"))
    with monkeypatch.context() as serving:
        guard = _forbid_reads(serving)
        fields = cau.routing_budget_fields()
    assert guard.calls == []
    assert {row["status"] for row in fields["claude_accounts"].values()} == {"ok"}
    assert fields["preferred_claude_account"] == "b"
    assert scheduled == []


# Fails on af927d37bd: the warm async handler parsed account records on the
# event-loop thread. Thread identity, not elapsed time, is the measure.
def test_event_loop_thread_never_parses_account_records(bound, monkeypatch, tmp_path):
    import asyncio
    from types import SimpleNamespace

    from scripts.agent_runtime import attempt_boundary
    from scripts.api import state_router

    # Large, valid records within the 16 MiB bound, as in the review's measurement.
    projects = {f"p{index:06d}": {"lastCost": 0, "allowedTools": []} for index in range(20000)}
    for label, record in (("a", bound.home / ".claude.json"), ("b", bound.dirs["b"] / ".claude.json")):
        _write_private(record, {"oauthAccount": {"accountUuid": _FIXTURE_ACCOUNTS[label]}, "projects": projects})
    cau.refresh_claude_account_usage()

    parsers: list[int] = []
    real_read = attempt_boundary._read_private_json

    def tracked(*args, **kwargs):
        parsers.append(threading.get_ident())
        return real_read(*args, **kwargs)

    monkeypatch.setattr(attempt_boundary, "_read_private_json", tracked)
    budget = {"agents": {"claude": {"status": "ok"}}, "recommendation": {"primary_agent_for_code": "claude"}}
    monkeypatch.setattr(state_router, "cache_get_stored", lambda *_args, **_kwargs: (budget, 0))
    monkeypatch.setattr(state_router, "cache_retain", lambda *_args, **_kwargs: None)
    ctx = SimpleNamespace(
        roots=SimpleNamespace(project_root=tmp_path, batch_state_dir=tmp_path, curriculum_root=tmp_path)
    )

    async def serve_twice():
        loop_thread = threading.get_ident()
        warm = await state_router.routing_budget(fresh_codexbar=False, transport="dispatch", ctx=ctx)
        # A record rewritten between serves: withheld, revalidated off the loop.
        (bound.home / ".claude.json").write_text((bound.home / ".claude.json").read_text() + " ")
        changed = await state_router.routing_budget(fresh_codexbar=False, transport="dispatch", ctx=ctx)
        return loop_thread, warm, changed

    loop_thread, warm, changed = asyncio.run(serve_twice())
    _settle()

    assert {row["status"] for row in warm["claude_accounts"].values()} == {"ok"}
    assert _row(changed["claude_accounts"], "a")["reason"] == "not_probed"
    assert loop_thread not in parsers
    assert parsers, "the background revalidation parsed the rewritten record"
    assert _row(cau.claude_accounts_snapshot(), "a")["status"] == "ok"  # re-armed, same account


def test_revalidation_rearms_a_same_account_rewrite_without_asking_the_provider(bound, provider):
    cau.refresh_claude_account_usage()
    asked = provider.calls
    (bound.dirs["b"] / ".claude.json").write_text(
        json.dumps({"oauthAccount": {"accountUuid": _ACCOUNT_B}, "projects": {"x": {}}})
    )
    assert _row(cau.claude_accounts_snapshot(), "b")["reason"] == "not_probed"
    _settle()
    row = _row(cau.claude_accounts_snapshot(), "b")
    assert row["status"] == "ok"
    assert row["weekly"]["left_pct"] == 80.0
    assert provider.calls == asked  # the credentials did not change


def test_revalidation_verifies_rotated_credentials(bound, provider):
    cau.refresh_claude_account_usage()
    asked = provider.calls
    _write_credentials(bound.dirs["b"], _ACCOUNT_B, serial=2)
    assert _row(cau.claude_accounts_snapshot(), "b")["reason"] == "not_probed"
    _settle()
    assert _row(cau.claude_accounts_snapshot(), "b")["status"] == "ok"
    assert provider.calls == asked + 1

    _write_credentials(bound.dirs["b"], _ACCOUNT_C, serial=3)
    cau.claude_accounts_snapshot()
    _settle()
    _assert_not_published(cau.routing_budget_fields(), "b", reason="claude_account_unverified")
    assert "b" not in cau._last_good


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("reassigned", "not_probed"),
        ("removed", "claude_account_binding_missing"),
        ("relogged", "claude_account_unverified"),
    ],
)
def test_revalidation_forgets_a_sample_whose_binding_changed(bound, change, reason):
    cau.refresh_claude_account_usage()
    if change == "reassigned":
        bound.bind("c")
    elif change == "removed":
        bound.unbind()
    else:  # the default directory's login record names another account
        _write_login_record(bound.home / ".claude.json", _ACCOUNT_C)
    label = "a" if change == "relogged" else "b"
    _assert_not_published(cau.routing_budget_fields(), label, reason="not_probed")
    _settle()
    _assert_not_published(cau.routing_budget_fields(), label, reason=reason)
    assert label not in cau._last_good


def test_revalidation_is_single_flight(bound, monkeypatch):
    cau.refresh_claude_account_usage()
    release = threading.Event()
    started: list[str] = []

    def slow():
        started.append("run")
        release.wait(10)

    monkeypatch.setattr(cau, "revalidate_claude_accounts", slow)
    _write_login_record(bound.home / ".claude.json", _ACCOUNT_A)
    for _ in range(5):
        cau.claude_accounts_snapshot()
    release.set()
    _settle()
    assert started == ["run"]


def test_revalidation_does_not_replace_a_newer_sample(bound, monkeypatch):
    cau.refresh_claude_account_usage()
    stale = cau._last_good["b"]
    bound.unbind()
    cau.refresh_claude_account_usage()  # forgets b
    bound.bind("b")
    cau.refresh_claude_account_usage()  # a newer sample
    newer = cau._last_good["b"]
    cau._revalidate_one("b", stale)  # a revalidation of the old sample finishing late
    assert cau._last_good["b"] is newer


def test_revalidation_defect_withholds_the_row(bound, monkeypatch):
    cau.refresh_claude_account_usage()

    def broken(label, **_kwargs):
        raise RuntimeError(_MARKER)

    monkeypatch.setattr(cau, "account_binding", broken)
    _write_login_record(bound.home / ".claude.json", _ACCOUNT_A)
    cau.claude_accounts_snapshot()
    _settle()
    fields = cau.routing_budget_fields()
    _assert_withheld(_row(fields["claude_accounts"], "a"), "probe_error")
    assert _MARKER not in json.dumps(fields)


def test_serving_withholds_when_the_starting_paths_move(bound, monkeypatch):
    """A new home or binding location is a different binding, seen without reading it."""
    cau.refresh_claude_account_usage()
    monkeypatch.setattr(cau, "_schedule_revalidation", lambda: None)
    monkeypatch.setenv("HOME", str(bound.root / "elsewhere"))
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(bound.root / "other-accounts.json"))
    for row in cau.claude_accounts_snapshot().values():
        _assert_withheld(row, "not_probed")


def test_serving_withholds_when_a_validated_path_cannot_be_examined(bound, monkeypatch):
    cau.refresh_claude_account_usage()
    monkeypatch.setattr(cau, "_schedule_revalidation", lambda: None)

    def denied(*_args, **_kwargs):
        raise PermissionError(13, "denied")

    with monkeypatch.context() as serving:
        serving.setattr(cau.os, "stat", denied)
        rows = cau.claude_accounts_snapshot()
    for row in rows.values():
        _assert_withheld(row, "not_probed")


def test_unexaminable_binding_file_is_unavailable(bound, monkeypatch):
    bound.binding.parent.joinpath("locked").mkdir()
    locked = bound.binding.parent / "locked" / "claude-accounts.json"
    _bind_b(locked, bound.dirs["b"], _ACCOUNT_B)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(locked))
    locked.parent.chmod(0o000)
    try:
        with pytest.raises(cau.ClaudeAccountRefused) as exc, cau.account_binding("b"):
            pass
    finally:
        locked.parent.chmod(0o700)
    assert exc.value.code == "claude_account_binding_unavailable"


def test_refresh_keeps_the_byte_bounds(bound, monkeypatch):
    from scripts.agent_runtime import attempt_boundary

    limits: list[int] = []
    real_read = os.read

    def tracked(fd, limit):
        limits.append(limit)
        return real_read(fd, limit)

    monkeypatch.setattr(attempt_boundary.os, "read", tracked)
    cau.refresh_claude_account_usage()
    assert {65537, 16 * 1024 * 1024 + 1} <= set(limits)  # binding and credentials; login records
    assert max(limits) == 16 * 1024 * 1024 + 1


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
