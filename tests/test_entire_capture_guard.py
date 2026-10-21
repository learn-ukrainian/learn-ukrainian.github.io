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
        # Opt-in: record the scheduling priority each call actually ran at (#11289).
        'if [ -n "${PRIO_LOG:-}" ]; then\n'
        '  printf "%s ni=%s io=%s\\n" "$1" $(ps -o ni= -p $$) "$(ionice -p $$)" >> "$PRIO_LOG"\n'
        "fi\n"
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


POST_COMMIT = ("hooks", "git", "post-commit")
POST_COMMIT_CALLS = ["version", "status --json", "hooks git post-commit"]
# Every other entry point that reaches the guard keeps today's priority (#11289).
OTHER_ENTRY_POINTS = (
    ("hooks", "git", "prepare-commit-msg", ".git/COMMIT_EDITMSG", "message"),
    ("hooks", "git", "commit-msg", ".git/COMMIT_EDITMSG"),
    ("hooks", "git", "post-rewrite", "amend"),
    ("hooks", "git", "pre-push", "origin"),
    ("--budget", "25", "hooks", "claude-code", "stop"),
    ("--budget", "25", "hooks", "codex", "stop"),
)


def _guard_python() -> Path:
    """The interpreter capture_guard.sh resolves: this checkout's venv, else the primary's."""
    root = REPO_ROOT.resolve()
    if os.access(root / ".venv/bin/python", os.X_OK):
        return root / ".venv/bin/python"
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    return Path(common).parent / ".venv/bin/python"


def _fake_wrappers(tmp_path: Path, env: dict[str, str], *, ionice_fails: bool = False) -> Path:
    """Logging stand-ins for `nice` and `ionice` that exec the wrapped command."""
    bin_dir = Path(env["PATH"].split(os.pathsep)[0])
    log = tmp_path / "wrappers.log"
    for name in ("nice", "ionice"):
        # Both wrappers take two options before the command: -n 10 and -c3 -t.
        body = "exit 1\n" if name == "ionice" and ionice_fails else 'shift 2\nexec "$@"\n'
        (bin_dir / name).write_text(f'#!/bin/sh\nprintf "{name} %s\\n" "$*" >> "$WRAP_LOG"\n{body}', encoding="utf-8")
        (bin_dir / name).chmod(0o755)
    env["WRAP_LOG"] = str(log)
    return log


def _wrapper_calls(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _without_system_wrappers(tmp_path: Path, env: dict[str, str], *keep: str) -> None:
    """Replace the system PATH with only the tools the guard and the fake CLI need."""
    tools = tmp_path / "tools"
    tools.mkdir()
    for tool in ("sh", "dirname", "git", "cat", "sleep", "true"):
        (tools / tool).symlink_to(shutil.which(tool, path=SYSTEM_PATH))
    bin_dir = env["PATH"].split(os.pathsep)[0]
    for name in ("nice", "ionice"):
        if name not in keep:
            (Path(bin_dir) / name).unlink(missing_ok=True)
    env["PATH"] = f"{bin_dir}{os.pathsep}{tools}"


def _commit_repo(tmp_path: Path, *, trailer: bool) -> Path:
    """A repository whose HEAD commit does or does not carry an Entire-Checkpoint trailer."""
    repo = tmp_path / "work"
    repo.mkdir()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    message = "change\n\nEntire-Checkpoint: 0123456789ab\n" if trailer else "change\n"
    for argv in (
        ["init", "-q"],
        ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", message],
    ):
        subprocess.run(["git", "-C", str(repo), *argv], check=True, env=env, capture_output=True, timeout=30)
    return repo


def _priority_now() -> tuple[str, str]:
    ni = str(os.getpriority(os.PRIO_PROCESS, 0))
    pid = str(os.getpid())
    io = subprocess.run(["ionice", "-p", pid], capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    return ni, io


@pytest.mark.parametrize("trailer", [True, False], ids=["trailer", "no-trailer"])
@pytest.mark.parametrize("budget", [(), ("--budget", "30")], ids=["hook-argv", "budget"])
def test_post_commit_runs_guard_probes_and_capture_under_nice_and_ionice(
    tmp_path: Path, trailer: bool, budget: tuple[str, ...]
) -> None:
    """AC-01/AC-02: one priority wrapper around the guard; the CLI calls are unchanged."""
    _state, env = _fake_entire(tmp_path)
    wrappers = _fake_wrappers(tmp_path, env)
    guarded = f"{_guard_python()} -I {REPO_ROOT.resolve()}/scripts/entire/capture_guard.py {' '.join((*budget, *POST_COMMIT))}"

    result = _guard(env, _commit_repo(tmp_path, trailer=trailer), *budget, *POST_COMMIT)

    assert (result.returncode, result.stderr) == (0, "")
    assert _wrapper_calls(wrappers) == [
        "ionice -c3 -t true",
        "nice -n 10 true",
        f"nice -n 10 ionice -c3 -t {guarded}",
        f"ionice -c3 -t {guarded}",
    ]
    assert _calls(env) == POST_COMMIT_CALLS


@pytest.mark.parametrize("trailer", [True, False], ids=["trailer", "no-trailer"])
def test_post_commit_probes_and_capture_observably_run_at_low_priority(tmp_path: Path, trailer: bool) -> None:
    """With the real nice/ionice, every CLI call runs at idle I/O and niceness +10."""
    _state, env = _fake_entire(tmp_path)
    env["PRIO_LOG"] = str(tmp_path / "prio.log")
    base_ni, _base_io = _priority_now()
    low = f"ni={min(int(base_ni) + 10, 19)} io=idle"

    result = _guard(env, _commit_repo(tmp_path, trailer=trailer), *POST_COMMIT)

    assert (result.returncode, result.stderr) == (0, "")
    assert _calls(env) == POST_COMMIT_CALLS
    assert Path(env["PRIO_LOG"]).read_text(encoding="utf-8").splitlines() == [
        f"version {low}",
        f"status {low}",
        f"hooks {low}",
    ]


@pytest.mark.parametrize("args", OTHER_ENTRY_POINTS, ids=lambda args: " ".join(args[args.index("hooks") + 1 :][:2]))
def test_other_entry_points_keep_their_priority_and_calls(tmp_path: Path, args: tuple[str, ...]) -> None:
    _state, env = _fake_entire(tmp_path)
    env["PRIO_LOG"] = str(tmp_path / "prio.log")
    base_ni, base_io = _priority_now()
    command = " ".join(args[args.index("hooks") :])

    result = _guard(env, tmp_path, *args)

    assert (result.returncode, result.stderr) == (0, "")
    assert _calls(env) == ["version", "status --json", command]
    assert Path(env["PRIO_LOG"]).read_text(encoding="utf-8").splitlines() == [
        f"{verb} ni={base_ni} io={base_io}" for verb in ("version", "status", "hooks")
    ]
    del env["PRIO_LOG"]
    wrappers = _fake_wrappers(tmp_path, env)
    assert _guard(env, tmp_path, *args).returncode == 0
    assert _wrapper_calls(wrappers) == []


@pytest.mark.parametrize(
    ("keep", "expected"),
    [
        (("nice",), ["nice -n 10 true", "nice -n 10 {guarded}"]),
        (("ionice",), ["ionice -c3 -t true", "ionice -c3 -t {guarded}"]),
        ((), []),
    ],
    ids=["ionice-missing", "nice-missing", "both-missing"],
)
def test_missing_priority_tool_still_captures(tmp_path: Path, keep: tuple[str, ...], expected: list[str]) -> None:
    _state, env = _fake_entire(tmp_path)
    wrappers = _fake_wrappers(tmp_path, env)
    _without_system_wrappers(tmp_path, env, *keep)
    guarded = f"{_guard_python()} -I {REPO_ROOT.resolve()}/scripts/entire/capture_guard.py hooks git post-commit"

    result = _guard(env, tmp_path, *POST_COMMIT)

    assert (result.returncode, result.stderr) == (0, "")
    assert _calls(env) == POST_COMMIT_CALLS
    assert _wrapper_calls(wrappers) == [line.format(guarded=guarded) for line in expected]


def test_ionice_that_cannot_run_the_command_is_dropped_not_fatal(tmp_path: Path) -> None:
    """An ionice that fails its probe (unsupported -t, denied) never aborts the capture."""
    _state, env = _fake_entire(tmp_path)
    wrappers = _fake_wrappers(tmp_path, env, ionice_fails=True)
    guarded = f"{_guard_python()} -I {REPO_ROOT.resolve()}/scripts/entire/capture_guard.py hooks git post-commit"

    result = _guard(env, tmp_path, *POST_COMMIT)

    assert (result.returncode, result.stderr) == (0, "")
    assert _calls(env) == POST_COMMIT_CALLS
    assert _wrapper_calls(wrappers) == ["ionice -c3 -t true", "nice -n 10 true", f"nice -n 10 {guarded}"]


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


ADR = REPO_ROOT / "docs" / "architecture" / "adr" / "adr-018-entire-acp-context-layer.md"
EVIDENCE = REPO_ROOT / "docs" / "architecture" / "adr" / "evidence" / "entire-0115-canary"
# Stack-currency policy v3 consequence for ADR-018, required verbatim (#10846).
STACK_CURRENCY_CONSEQUENCE = (
    "The last accepted Entire CLI version is recorded in stack_pins.yaml; it is an acceptance record, "
    "not an expiry. A newer CLI is allowed only after a compatibility review re-proves the "
    "version-sensitive canaries (fail-closed version preflight, private-destination allowlist, zero "
    "public entire/* refs, body-leakage scan, fail-open outage behaviour, locator digest checks), with "
    "independent cross-family review and a reviewed rollback procedure. Until that review is recorded, "
    "automated calls prove the accepted version. A version probe is not that review. After approval, "
    "the native-recall preflight and the runtime version guard move to the new version in the same change."
)
CANARIES = (
    "Fail-closed version preflight",
    "Private-destination allowlist",
    "Zero public `entire/*` refs",
    "Body-leakage scan",
    "Fail-open outage behaviour",
    "Locator digest checks",
)


def test_adr_018_carries_the_stack_currency_consequence_and_the_accepted_version() -> None:
    text = ADR.read_text(encoding="utf-8")

    assert STACK_CURRENCY_CONSEQUENCE in text
    assert "Entire is pinned to 0.11.5. An upgrade requires" not in text
    # Until stack_pins.yaml lands, the ADR is the acceptance record the guard must match.
    assert not (REPO_ROOT / "stack_pins.yaml").exists()
    assert f"**Entire CLI {capture_guard.ACCEPTED_VERSION}**" in text


def test_adr_018_names_a_receipt_for_every_canary_and_each_receipt_exists() -> None:
    text = ADR.read_text(encoding="utf-8")
    table = text.split("The six version-sensitive canaries")[1].split("Wrapper bytes:")[0]
    rows = [line for line in table.splitlines() if line.startswith("| ") and not line.startswith("| Canary")]

    assert [row.split(" | ")[0].removeprefix("| ") for row in rows if not row.startswith("| ---")] == list(CANARIES)
    named = re.findall(
        r"`((?:round-[12]/)?(?:log|status|refs|tool|wrapper|mutation|explain|CANARY)[\w.-]*\.(?:json|txt))`",
        text,
    )
    assert len(named) >= 15
    for name in named:
        path = EVIDENCE / name if name.startswith("round-") else EVIDENCE / "round-2" / name
        assert path.is_file(), name


@pytest.mark.repo_wide
def test_canary_evidence_bundle_carries_no_local_absolute_paths() -> None:
    absolute = re.compile(r"(^|[\s'\"=:(\[])/(home|var/tmp|run/user|tmp)/")
    files = sorted(path for path in EVIDENCE.rglob("*") if path.is_file())

    assert len(files) > 80
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not absolute.search(line), f"{path.relative_to(EVIDENCE)}:{number}"
