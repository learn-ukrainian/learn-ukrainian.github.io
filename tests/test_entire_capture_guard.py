"""Capture guard: Entire capture runs only behind the version and private-route proof (#10846)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from scripts.entire import capture_guard
from scripts.entire.validate_checkpoint_routing import PRIVATE_CHECKPOINT_REPO

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD = REPO_ROOT / "scripts" / "entire" / "capture_guard.sh"
CLAUDE_SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"
CODEX_HOOKS = REPO_ROOT / "agents_extensions" / "codex" / "hooks.json"
# The live CLI usually lives in a user bin directory; a fixed system PATH keeps it out.
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"

PRIVATE_STATUS = {
    "enabled": True,
    "checkpoint_sync_remote": PRIVATE_CHECKPOINT_REPO,
    "checkpoint_sync_remote_source": "dedicated",
}
# What 0.11.5 reported in the canary when the dedicated store was ignored (S3).
IGNORED_STATUS = {
    "enabled": True,
    "checkpoint_sync_remote": "origin",
    "checkpoint_sync_remote_source": "default",
    "checkpoint_remote_ignored": PRIVATE_CHECKPOINT_REPO,
}


def _fake_entire(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A fake `entire` whose answers come from files, logging every call and hook stdin."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "entire"
    fake.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$FAKE_LOG"\n'
        'case "$1" in\n'
        "  version)\n"
        '    [ -f "$FAKE_DIR/version-hang" ] && sleep 30\n'
        '    cat "$FAKE_DIR/version"; exit "$(cat "$FAKE_DIR/version-rc")";;\n'
        "  status)\n"
        '    cat "$FAKE_DIR/status"; exit "$(cat "$FAKE_DIR/status-rc")";;\n'
        "  hooks)\n"
        '    cat >> "$FAKE_DIR/hook-stdin"\n'
        '    [ -f "$FAKE_DIR/hook-hang" ] && sleep 60\n'
        '    exit "$(cat "$FAKE_DIR/hook-rc")";;\n'
        "esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    state = tmp_path / "fake"
    state.mkdir()
    _answer(state, version="Entire CLI 0.11.5\nGo version: go1.27.1\n", status=PRIVATE_STATUS)
    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:{SYSTEM_PATH}", "FAKE_LOG": str(tmp_path / "calls.log"), "FAKE_DIR": str(state)})
    return state, env


def _answer(
    state: Path,
    *,
    version: str | None = None,
    version_rc: int = 0,
    status: object = None,
    status_rc: int = 0,
    hook_rc: int = 0,
) -> None:
    if version is not None:
        (state / "version").write_text(version, encoding="utf-8")
    if status is not None:
        (state / "status").write_text(status if isinstance(status, str) else json.dumps(status), encoding="utf-8")
    (state / "version-rc").write_text(str(version_rc), encoding="utf-8")
    (state / "status-rc").write_text(str(status_rc), encoding="utf-8")
    (state / "hook-rc").write_text(str(hook_rc), encoding="utf-8")


def _calls(env: dict[str, str]) -> list[str]:
    log = Path(env["FAKE_LOG"])
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _guard(env: dict[str, str], cwd: Path, *args: str, stdin: str = "{}\n") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", str(GUARD), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env=env,
        timeout=60,
    )


def test_accepted_version_and_private_route_run_the_capture_with_host_stdin(tmp_path: Path) -> None:
    state, env = _fake_entire(tmp_path)

    result = _guard(env, tmp_path, "--budget", "25", "hooks", "claude-code", "stop", stdin='{"session_id":"s"}\n')

    assert result.returncode == 0
    assert result.stderr == ""
    assert _calls(env) == ["version", "status --json", "hooks claude-code stop"]
    assert (state / "hook-stdin").read_text(encoding="utf-8") == '{"session_id":"s"}\n'


@pytest.mark.parametrize(
    ("version", "version_rc"),
    [
        ("Entire CLI 0.8.42\n", 0),
        ("Entire CLI 0.11.50\n", 0),
        ("Entire CLI 0.11.6\n", 0),
        ("Entire CLI 0.11.4\n", 0),
        ("entire version 0.11.5\n", 0),
        ("Go version: go1.27.1\nEntire CLI 0.11.5\n", 0),
        ("", 0),
        ("Entire CLI 0.11.5\n", 1),
    ],
    ids=["older", "older-0842-live", "newer-0.11.50", "newer", "malformed", "not-first-line", "empty", "nonzero"],
)
def test_unaccepted_version_refuses_capture_without_probing_status(
    tmp_path: Path, version: str, version_rc: int
) -> None:
    state, env = _fake_entire(tmp_path)
    _answer(state, version=version, version_rc=version_rc)

    result = _guard(env, tmp_path, "hooks", "git", "pre-push", "origin")

    assert result.returncode == 0
    assert _calls(env) == ["version"]
    assert result.stderr.count("\n") == 1
    assert "capture refused (cli_version_not_accepted)" in result.stderr
    assert not (state / "hook-stdin").exists()


@pytest.mark.parametrize(
    ("status", "status_rc"),
    [
        ({}, 0),
        (IGNORED_STATUS, 0),
        ({**PRIVATE_STATUS, "checkpoint_sync_remote": "learn-ukrainian/learn-ukrainian.github.io"}, 0),
        ({**PRIVATE_STATUS, "checkpoint_sync_error": "election failed"}, 0),
        ({**PRIVATE_STATUS, "checkpoint_remote_ignored": PRIVATE_CHECKPOINT_REPO}, 0),
        ("not json", 0),
        (PRIVATE_STATUS, 1),
    ],
    ids=["empty", "ignored-default", "wrong-repo", "sync-error", "ignored-flag", "malformed", "nonzero"],
)
def test_route_not_proven_private_refuses_capture(tmp_path: Path, status: object, status_rc: int) -> None:
    state, env = _fake_entire(tmp_path)
    _answer(state, status=status, status_rc=status_rc)

    result = _guard(env, tmp_path, "hooks", "claude-code", "stop")

    assert result.returncode == 0
    assert _calls(env) == ["version", "status --json"]
    assert "capture refused (checkpoint_route_not_private)" in result.stderr


def test_version_probe_hang_refuses_within_the_budget(tmp_path: Path) -> None:
    state, env = _fake_entire(tmp_path)
    (state / "version-hang").touch()

    started = time.monotonic()
    result = _guard(env, tmp_path, "--budget", "2", "hooks", "claude-code", "stop")

    assert time.monotonic() - started < 10
    assert result.returncode == 0
    assert "capture refused (guard_probe_timeout)" in result.stderr
    assert "hooks claude-code stop" not in _calls(env)


@pytest.mark.parametrize("hook_rc", [1, 2, 127])
def test_capture_failure_is_an_outage_and_exits_zero(tmp_path: Path, hook_rc: int) -> None:
    state, env = _fake_entire(tmp_path)
    _answer(state, hook_rc=hook_rc)

    result = _guard(env, tmp_path, "hooks", "git", "pre-push", "origin")

    assert result.returncode == 0
    assert _calls(env)[-1] == "hooks git pre-push origin"
    assert f"capture failed (exit {hook_rc}); continuing without capture" in result.stderr


def test_capture_hang_is_stopped_at_the_budget_and_exits_zero(tmp_path: Path) -> None:
    state, env = _fake_entire(tmp_path)
    (state / "hook-hang").touch()

    started = time.monotonic()
    result = _guard(env, tmp_path, "--budget", "3", "hooks", "git", "pre-push", "origin")

    assert time.monotonic() - started < 15
    assert result.returncode == 0
    assert "capture timed out" in result.stderr


def test_missing_cli_is_a_silent_no_op(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PATH"] = SYSTEM_PATH
    if shutil.which("entire", path=SYSTEM_PATH):
        pytest.skip("an entire binary is installed on the system PATH")

    result = _guard(env, tmp_path, "hooks", "claude-code", "stop")

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_broken_routing_allowlist_refuses_before_any_cli_call(tmp_path: Path) -> None:
    root = tmp_path / "root"
    shutil.copytree(REPO_ROOT / ".entire", root / ".entire")
    settings_path = root / ".entire" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["strategy_options"]["checkpoint_remote"]["repo"] = "learn-ukrainian/learn-ukrainian.github.io"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def runner(argv, cwd, timeout):
        calls.append(tuple(argv))
        raise AssertionError("no CLI call expected")

    reason = capture_guard.refusal(root, "entire", time.monotonic() + 10, runner=runner)

    assert reason == "routing_allowlist_failed"
    assert calls == []


def test_refusal_passes_with_the_tracked_configuration_and_private_status() -> None:
    def runner(argv, cwd, timeout):
        assert timeout > 0
        stdout = "Entire CLI 0.11.5\n" if argv[1] == "version" else json.dumps(PRIVATE_STATUS)
        return subprocess.CompletedProcess(list(argv), 0, stdout, "")

    assert capture_guard.refusal(REPO_ROOT, "entire", time.monotonic() + 30, runner=runner) is None


def _entire_hook_commands(path: Path, agent: str) -> list[dict]:
    settings = json.loads(path.read_text(encoding="utf-8"))
    return [
        hook
        for entries in settings["hooks"].values()
        for entry in entries
        for hook in entry.get("hooks", [])
        if f"hooks {agent} " in hook.get("command", "")
    ]


@pytest.mark.parametrize(("path", "agent", "count"), [(CLAUDE_SETTINGS, "claude-code", 7), (CODEX_HOOKS, "codex", 4)])
def test_every_agent_entire_hook_runs_through_the_guard_within_its_timeout(path: Path, agent: str, count: int) -> None:
    hooks = _entire_hook_commands(path, agent)

    assert len(hooks) == count
    for hook in hooks:
        command = hook["command"]
        assert f"entire hooks {agent}" not in command, command
        assert '/scripts/entire/capture_guard.sh"; if [ -x "$g" ]; then "$g" --budget ' in command
        budget = int(re.search(r"--budget (\d+) hooks ", command).group(1))
        # Probes plus capture stop inside the host timeout, with launcher headroom.
        assert budget <= hook["timeout"] - 5, (command, hook["timeout"])


def test_configured_stop_hook_never_captures_with_an_old_cli(tmp_path: Path) -> None:
    """Review reproducer: Entire 0.8.42 with an empty status must not reach `hooks ... stop`."""
    state, env = _fake_entire(tmp_path)
    _answer(state, version="Entire CLI 0.8.42\n", status={})
    stop = next(h for h in _entire_hook_commands(CLAUDE_SETTINGS, "claude-code") if "claude-code stop" in h["command"])

    result = subprocess.run(
        ["/bin/sh", "-c", stop["command"]],
        input="{}\n",
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        env=env,
        timeout=60,
    )

    assert result.returncode == 0
    assert _calls(env) == ["version"]
    assert "capture refused (cli_version_not_accepted)" in result.stderr


@pytest.mark.parametrize(("path", "agent"), [(CLAUDE_SETTINGS, "claude-code"), (CODEX_HOOKS, "codex")])
def test_configured_hooks_capture_with_the_accepted_cli(tmp_path: Path, path: Path, agent: str) -> None:
    _state, env = _fake_entire(tmp_path)

    for hook in _entire_hook_commands(path, agent):
        verb = re.search(rf"hooks {agent} ([a-z-]+)", hook["command"]).group(1)
        result = subprocess.run(
            ["/bin/sh", "-c", hook["command"]],
            input="{}\n",
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
            env=env,
            timeout=60,
        )
        assert result.returncode == 0
        assert _calls(env)[-3:] == ["version", "status --json", f"hooks {agent} {verb}"]


def test_configured_hooks_refuse_outside_a_guarded_checkout(tmp_path: Path) -> None:
    _state, env = _fake_entire(tmp_path)
    outside = tmp_path / "not-a-repo"
    outside.mkdir()

    for hook in _entire_hook_commands(CLAUDE_SETTINGS, "claude-code"):
        result = subprocess.run(
            ["/bin/sh", "-c", hook["command"]],
            input="{}\n",
            capture_output=True,
            text=True,
            check=False,
            cwd=outside,
            env={**env, "GIT_CEILING_DIRECTORIES": str(tmp_path)},
            timeout=60,
        )
        assert result.returncode == 0
        assert "capture refused (guard_missing)" in result.stderr
    assert _calls(env) == []
