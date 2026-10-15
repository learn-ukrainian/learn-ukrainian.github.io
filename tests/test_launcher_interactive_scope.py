"""Every launcher session, interactive or driver, enters the verified scope (#9624).

Each tracked wrapper runs non-dry through its own parser, the unmodified shared
core and the shared scope entry, against fake user-manager and kernel
boundaries. Adapters, preparation, leases and the provider are recording
stand-ins. Terminal behaviour runs through a pseudo-terminal under a minimal
job-control shell. Live containment stays the opt-in soak in
tests/test_launcher_driver_scope.py.
"""

from __future__ import annotations

import fcntl
import os
import re
import select
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import termios
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import pytest

from tests.launcher_libraries import launcher_catalog_files, launcher_library_files
from tests.launcher_sandbox import copy_slot_registry, tracked_launcher_wrappers
from tests.test_launcher_driver_scope import (
    manager_guard,
    require_soak_opt_in,
    run_live_soak,
    scope_sandbox,
    soak_environment,
    soak_hog,
)
from tests.wait_helpers import wait_until

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REPO = Path(__file__).resolve().parents[1]
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
PROVIDER_RC = 42
# A well-formed unit token for forged and parent scopes.
_PARENT = "0123abcd-0123-4abc-8def-0123456789ab"
DEADLINE_S = 60
# Caller arguments a replay must keep byte for byte: spaces, quotes, a nested
# separator, an empty value, a newline and unexpanded shell syntax.
TRICKY = ("a b", "q'\"uote", "", "--", "line\nbreak", "$HOME", "*")

# Every tracked wrapper, its provider and the label its unit carries (the lane
# for drivers). Each is executed below; the completeness guard compares this
# table with `git ls-files`.
INTERACTIVE = {
    "start-claude.sh": ("claude", "claude"),
    "start-codex.sh": ("codex", "codex"),
    "start-gemini.sh": ("gemini", "gemini"),
    "start-grok.sh": ("grok", "grok"),
    "start-kimi.sh": ("kimi", "kimi"),
    "start-kimicc.sh": ("kimi", "kimicc"),
    "start-glm.sh": ("glm", "glm"),
    "start-glmcc.sh": ("glm", "glmcc"),
    "scripts/start-bio-driver.sh": ("claude", "bio"),
}
DRIVERS = {
    "start-claude-driver.sh": ("claude", "devops"),
    "start-codex-driver.sh": ("codex", "devops"),
    "start-cursor-driver.sh": ("cursor", "devops"),
    "start-gemini-driver.sh": ("gemini", "devops"),
    "start-grok-driver.sh": ("grok", "devops"),
    "start-claude-cto.sh": ("claude", "epics"),
    "start-codex-cto.sh": ("codex", "epics"),
}
# Refused before scope entry in every real session: the Muse guard gate has
# no override (scripts/launchers/muse.sh). Its success path with admission
# stubbed is tests/test_start_muse_driver.py's shared-lifecycle coverage.
REFUSAL_ONLY = {"start-muse-driver.sh": (4, "MUSE_GUARD_PARITY_UNPROVEN")}

_EVENT = """lu_test_event() {
  local line cg=""
  while IFS= read -r line; do case "$line" in 0::*) cg="${line#0::}" ;; esac; done < "$FAKE_CGROUP"
  printf '%s cgroup=%s pid=%s\\n' "$1" "${cg##*/}" "$$" >> "$TEST_EVENTS"
}
"""
_ADAPTER = (
    _EVENT
    + """launcher_adapter_validate() { lu_test_event validate; }
launcher_adapter_preflight() { lu_test_event preflight; LC_AUTH_SOURCE=test; }
launcher_adapter_canary() { lu_test_event canary; }
launcher_adapter_exec() {
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'would exec test provider\\n'; return 0; fi
  lu_test_event exec
  {
    printf 'wrapper=%s\\nprovider=%s\\nmode=%s\\nharness=%s\\nepic=%s\\n' \\
      "${0##*/}" "$LC_PROVIDER" "$LC_MODE" "$LC_HARNESS" "${LC_EPIC:-}"
    printf 'glm_flash=%s\\nunit=%s\\nscope_pid=%s\\npid=%s\\n' \\
      "${GLM_OPENCODE_FLASH-unset}" "${LU_DRIVER_SCOPE_UNIT:-}" "${LU_DRIVER_SCOPE_PID:-}" "$$"
  } > "$TEST_IDENTITY"
  launcher_exec_command "$TEST_PROVIDER" ${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}
}
"""
)
_PROVIDER = (
    "#!/usr/bin/env bash\n"
    + _EVENT
    + """lu_test_event "provider xdist=${PYTEST_XDIST_AUTO_NUM_WORKERS-unset}"
printf '%s\\0' "$@" > "$TEST_ARGV"
exit "${TEST_PROVIDER_RC:-42}"
"""
)
# Traps first, then readiness; reads terminal lines until "done" (exit 42).
_SIGNAL_PROVIDER = """#!/usr/bin/env bash
log="$TEST_SIGNAL_LOG"
trap 'printf "INT\\n" >> "$log"' INT
trap 'printf "QUIT\\n" >> "$log"; exit 43' QUIT
trap 'printf "WINCH %s\\n" "$(stty size 2>/dev/null)" >> "$log"' WINCH
trap 'printf "CONT\\n" >> "$log"' CONT
stat="$(< /proc/$$/stat)"
read -r _state _ppid pgrp _session _tty tpgid _rest <<< "${stat##*) }"
tty=no
if [ -t 0 ] && [ -t 1 ]; then tty=yes; fi
printf 'ready pid=%s tty=%s pgrp=%s foreground=%s\\n' "$$" "$tty" "$pgrp" "$tpgid" >> "$log"
# Short reads: bash restarts a blocked read after WINCH and runs that trap only
# once the read returns.
while :; do
  IFS= read -r -t 0.2 line
  rc=$?
  if [ "$rc" -eq 0 ]; then
    printf 'LINE %s\\n' "$line" >> "$log"
    if [ "$line" = done ]; then exit 42; fi
  elif [ "$rc" -lt 128 ]; then
    exit 99
  fi
done
"""
_PYTHON = """#!/usr/bin/env bash
{event}
case "${{1:-}}:${{2:-}}" in
  -m:scripts.session_supervisor)
    lu_test_event "lease-${{3:-}}"
    if [ "${{3:-}}" = open ]; then
      cat <<'JSON'
{{"identity":{{"lease":{{"session_id":"session-test","lease_id":"lease-test","generation":1,"fencing_token":1,"expires_at":"2026-07-23T00:00:00Z"}}}}}}
JSON
    fi
    exit 0
    ;;
  -m:scripts.fleet_comms) lu_test_event publish; exit 0 ;;
esac
case "${{1:-}}" in */scripts/orchestration/thread_handoff.py) lu_test_event rollover-import; exit 0 ;; esac
exec {python} "$@"
"""
# A job-control shell for one foreground job, as a login shell runs a launcher:
# it owns the terminal, gives the job its own foreground process group, records
# a stop with the state of every process in that group, then resumes the job.
_JOBSHELL = r"""
import fcntl, os, resource, signal, sys, termios, time

status_path, argv = sys.argv[1], sys.argv[2:]
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
JOB_SIGNALS = (signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU)
for sig in JOB_SIGNALS:
    signal.signal(sig, signal.SIG_IGN)


def note(text):
    with open(status_path, "a") as stream:
        stream.write(text + "\n")


def group_states(pgid):
    states = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as stream:
                fields = stream.read().rsplit(")", 1)[1].split()
        except OSError:
            continue
        if int(fields[2]) == pgid:
            states.append(fields[0])
    return "".join(sorted(states))


pid = os.fork()
if pid == 0:
    os.setpgid(0, 0)
    os.tcsetpgrp(0, os.getpgrp())
    for sig in JOB_SIGNALS:
        signal.signal(sig, signal.SIG_DFL)
    os.execvp(argv[0], argv)
try:
    os.setpgid(pid, pid)
except OSError:
    pass
os.tcsetpgrp(0, pid)
note(f"job {pid}")
while True:
    _, status = os.waitpid(pid, os.WUNTRACED)
    if os.WIFSTOPPED(status):
        os.tcsetpgrp(0, os.getpgrp())
        # The group's other members stop as the signal reaches each of them.
        for _ in range(500):
            states = group_states(pid)
            if set(states) == {"T"}:
                break
            time.sleep(0.01)
        note(f"stopped {states}")
        os.tcsetpgrp(0, pid)
        os.killpg(pid, signal.SIGCONT)
        continue
    break
code = os.waitstatus_to_exitcode(status)
code = code if code >= 0 else 128 - code
note(f"exit {code}")
os._exit(code)
"""


def _write(path: Path, body: str, mode: int = 0o644) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(mode)
    return path


def _checkout(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """Copy every tracked wrapper and the shared core; stub only the edges."""
    root = tmp_path / "repo"
    for relative in (
        *tracked_launcher_wrappers(),
        "scripts/config/issue_streams.yaml",
        "scripts/config/launcher_stream_aliases.tsv",
        *launcher_library_files(REPO),
        *launcher_catalog_files(REPO),
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)
    copy_slot_registry(root)
    # The real helper with only its kernel cgroup read redirected.
    env = scope_sandbox(root, tmp_path)
    _write(
        root / "scripts/lib/rules_core.sh",
        _EVENT
        + 'rules_core_load() { lu_test_event rules; LC_RULES_CORE=""; LC_RULES_SEAT=core; LC_RULES_CORE_BYTES=0; }\n'
        + "rules_core_prefix() { printf '%s' \"$1\"; }\n",
    )
    _write(root / "scripts/lib/deploy_extensions.sh", _EVENT + "deploy_agent_extensions() { lu_test_event deploy; }\n")
    _write(root / "scripts/lib/claude_weekly_used.py", "print('0')\n")
    # The interpreter intercepts the rollover import by path; the slot registry
    # may import the real module, so keep it when present.
    handoff = root / "scripts/orchestration/thread_handoff.py"
    if not handoff.exists():
        _write(handoff, "raise SystemExit('intercepted by the test interpreter')\n")
    _write(root / "scripts/ai_agent_bridge/inbox_watch.sh", "#!/usr/bin/env bash\nexec sleep 300\n", 0o755)
    for provider in ("claude", "codex", "cursor", "gemini", "glm", "grok", "kimi"):
        _write(root / f"scripts/launchers/{provider}.sh", _ADAPTER)
    _write(root / ".venv/bin/python", _PYTHON.format(event=_EVENT, python=shlex.quote(sys.executable)), 0o755)
    provider = _write(root / "provider.sh", _PROVIDER, 0o755)
    signal_provider = _write(root / "signal-provider.sh", _SIGNAL_PROVIDER, 0o755)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, capture_output=True, timeout=30)
    base = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "LAUNCHER_", "SESSION_", "LC_", "LU_DRIVER_"))
        and key not in {"PYTEST_XDIST_AUTO_NUM_WORKERS", "GLM_OPENCODE_FLASH", "LU_RULES_SEAT"}
    }
    env = {
        **base,
        **env,
        "HOME": str(tmp_path / "home"),
        "LAUNCHER_DRY_RUN": "0",
        "TEST_EVENTS": str(tmp_path / "events"),
        "TEST_IDENTITY": str(tmp_path / "identity"),
        "TEST_ARGV": str(tmp_path / "argv"),
        "TEST_PROVIDER": str(provider),
        "TEST_SIGNAL_PROVIDER": str(signal_provider),
        "TEST_SIGNAL_LOG": str(tmp_path / "signal-log"),
    }
    return root, env


def _launch(
    root: Path, env: dict[str, str], wrapper: str, *args: str, **extra: str
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["bash", str(root / wrapper), *args],
        cwd=root,
        env={**env, **extra},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=DEADLINE_S,
    )
    _assert_no_real_manager(env)
    return result


def _assert_no_real_manager(env: dict[str, str]) -> None:
    contact = Path(env["LU_TEST_REAL_MANAGER_CONTACT"])
    assert not contact.exists(), f"fixture reached for the real user manager: {contact.read_text()}"


def _lines(path: str | Path) -> list[str]:
    path = Path(path)
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _events(env: dict[str, str]) -> list[tuple[str, str]]:
    """(event, cgroup basename) in order."""
    rows = []
    for line in _lines(env["TEST_EVENTS"]):
        match = re.fullmatch(r"(.+) cgroup=(\S*) pid=\d+", line)
        assert match, line
        rows.append((match[1], match[2]))
    return rows


def _identity(env: dict[str, str]) -> dict[str, str]:
    return dict(line.split("=", 1) for line in _lines(env["TEST_IDENTITY"]))


def _argv(env: dict[str, str]) -> list[str]:
    raw = Path(env["TEST_ARGV"]).read_bytes().decode()
    assert raw.endswith("\0")
    return raw[:-1].split("\0")


def _case_args(wrapper: str) -> tuple[str, ...]:
    if wrapper in INTERACTIVE:
        return ("prompt text", "--", *TRICKY)
    if wrapper.endswith("-cto.sh"):
        return ("--", *TRICKY)
    return ("--epic", "devops", "--", *TRICKY)


def _expected_forward(wrapper: str) -> list[str]:
    if wrapper in INTERACTIVE:
        forward = ["prompt text", *TRICKY]
        if wrapper == "scripts/start-bio-driver.sh":
            forward = ["--agent", "curriculum-track-orchestrator", *forward]
        return forward
    return list(TRICKY)


def test_completeness_guard_covers_every_tracked_wrapper() -> None:
    """Each tracked wrapper is an executed case below, success or classified refusal."""
    tracked = set(tracked_launcher_wrappers())
    cases = set(INTERACTIVE) | set(DRIVERS) | set(REFUSAL_ONLY)
    assert len(INTERACTIVE) + len(DRIVERS) + len(REFUSAL_ONLY) == len(cases)
    assert cases == tracked, f"missing cases: {sorted(tracked - cases)}; stale cases: {sorted(cases - tracked)}"


@pytest.mark.parametrize("wrapper", sorted({**INTERACTIVE, **DRIVERS}))
def test_every_wrapper_enters_one_verified_scope_then_reaches_its_provider_once(tmp_path: Path, wrapper: str) -> None:
    root, env = _checkout(tmp_path)
    provider, label = {**INTERACTIVE, **DRIVERS}[wrapper]
    mode = "interactive" if wrapper in INTERACTIVE else "driver"
    result = _launch(root, env, wrapper, *_case_args(wrapper), TEST_PROVIDER_RC=str(PROVIDER_RC))
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    start = re.search(
        rf"DRIVER_SCOPE_START unit=(lu-{mode}-{provider}-{re.escape(label)}-{UUID}\.scope) ", result.stderr
    )
    assert start, result.stderr
    unit = start[1]
    # Verified twice: by the entry helper, then by the replayed wrapper itself.
    assert result.stderr.count(f"DRIVER_SCOPE_VERIFIED unit={unit} ") == 2
    calls = _lines(env["FAKE_MANAGER_CALLS"])
    assert sum(call.startswith("systemd-run ") for call in calls) == 1
    assert f"--slice=lu-driver.slice --unit={unit} " in next(c for c in calls if c.startswith("systemd-run "))

    identity = _identity(env)
    assert identity["wrapper"] == Path(wrapper).name
    assert (identity["provider"], identity["mode"], identity["unit"]) == (provider, mode, unit)
    # Same-PID re-entry: the replayed wrapper is the process systemd-run started.
    assert identity["scope_pid"] == identity["pid"]
    if mode == "driver":
        assert identity["epic"] == label
    else:
        assert identity["epic"] == ""

    events = _events(env)
    assert [name for name, _ in events].count("provider xdist=2") == 1, events
    # Everything after the launcher's own admission runs inside the new scope.
    assert all(cgroup == unit for _, cgroup in events), events
    names = [name for name, _ in events]
    for prepared in ("rules", "validate", "preflight", "deploy", "exec"):
        assert names.count(prepared) == 1, (prepared, events)
    if mode == "driver":
        assert names.count("lease-open") == names.count("lease-close") == names.count("rollover-import") == 1
        assert names.index("lease-open") < names.index("provider xdist=2") < names.index("lease-close")
        # Caller arguments, then the drive-epic binding (a lane agent may lead).
        forward = _argv(env)
        assert forward[-1 - len(TRICKY) : -1] == list(TRICKY)
        assert forward[-1].startswith("Load agents_extensions/shared/skills/drive-epic/SKILL.md")
    else:
        assert not [name for name in names if name.startswith(("lease-", "rollover-", "canary", "publish"))]
        assert _argv(env) == _expected_forward(wrapper)
    exit_lines = [line for line in result.stderr.splitlines() if line.startswith("DRIVER_SCOPE_EXIT ")]
    if mode == "driver":
        assert len(exit_lines) == 1 and exit_lines[0].startswith(
            f"DRIVER_SCOPE_EXIT epic={label} rc={PROVIDER_RC} signal=none "
        )
        assert _lines(env["FAKE_LOGGER_MESSAGES"]) == exit_lines
    else:
        assert exit_lines == []
        assert _lines(env["FAKE_LOGGER_MESSAGES"]) == []


@pytest.mark.parametrize("wrapper", sorted(REFUSAL_ONLY))
def test_refusal_only_wrapper_refuses_before_any_manager_contact(tmp_path: Path, wrapper: str) -> None:
    """The real Muse admission refuses outside any scope; gh and the manager are fakes."""
    code, reason = REFUSAL_ONLY[wrapper]
    bindir = tmp_path / "bin"
    # Answers the publication shim's API request, as tests/test_start_muse_driver.py does.
    _write(
        bindir / "gh",
        "#!/bin/bash\nprintf 'HTTP/2 200 OK\\r\\nContent-Type: application/json\\r\\n\\r\\n"
        '{"visibility":"PUBLIC"}\\n\'\n',
        0o755,
    )
    _write(bindir / "muse", '#!/bin/bash\ntouch "$TEST_PROVIDER_STARTED"\n', 0o755)
    guard = manager_guard(tmp_path / "guard")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LAUNCHER_", "GIT_", "SESSION_", "LC_", "LU_DRIVER_"))
        and key not in {"LU_RULES_SEAT", "PYTEST_XDIST_AUTO_NUM_WORKERS"}
    }
    path = f"{bindir}:{guard}:{os.environ['PATH']}"
    env.update(
        PATH=path,
        AGENT_ORIGINAL_PATH=path,
        AGENT_REAL_GH=str(bindir / "gh"),
        LAUNCHER_DRY_RUN="0",
        LU_TEST_REAL_MANAGER_CONTACT=str(tmp_path / "real-manager-contact"),
        TEST_PROVIDER_STARTED=str(tmp_path / "provider-started"),
    )
    result = subprocess.run(
        [str(REPO / wrapper), "--epic", "devops"],
        cwd=REPO,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=DEADLINE_S,
    )
    assert result.returncode == code, result.stdout + result.stderr
    assert reason in result.stderr
    assert "DRIVER_SCOPE_" not in result.stderr
    _assert_no_real_manager(env)
    assert not Path(env["TEST_PROVIDER_STARTED"]).exists()


@pytest.mark.parametrize(
    ("wrapper", "flash", "harness", "forward_head"),
    [
        # The provider-derived name would replay start-glm.sh and export the flag.
        ("start-glmcc.sh", "unset", "claude-code", []),
        ("start-glm.sh", "1", "claude-code", []),
        ("start-kimicc.sh", "unset", "claude-code", []),
        ("start-kimi.sh", "unset", "kimi-code", []),
        ("scripts/start-bio-driver.sh", "unset", "claude-code", ["--agent", "curriculum-track-orchestrator"]),
    ],
)
def test_route_identity_survives_reentry(
    tmp_path: Path, wrapper: str, flash: str, harness: str, forward_head: list[str]
) -> None:
    """Wrapper identity and provider argv are checked separately, injections once."""
    root, env = _checkout(tmp_path)
    result = _launch(root, env, wrapper, "--", *TRICKY)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    identity = _identity(env)
    assert identity["wrapper"] == Path(wrapper).name
    assert identity["glm_flash"] == flash
    assert identity["harness"] == harness
    assert _argv(env) == [*forward_head, *TRICKY]


@pytest.mark.parametrize(
    ("wrapper", "mode"),
    [
        ("start-kimicc.sh", "interactive"),
        ("scripts/start-bio-driver.sh", "interactive"),
        ("start-claude-cto.sh", "driver"),
    ],
)
def test_scope_replays_the_invoked_wrapper_with_the_callers_argv(tmp_path: Path, wrapper: str, mode: str) -> None:
    """The manager receives the outermost wrapper and its original argv, never injected options."""
    root, env = _checkout(tmp_path)
    run_argv = tmp_path / "run-argv"
    result = _launch(root, env, wrapper, "--", *TRICKY, FAKE_RUN_ARGV=str(run_argv))
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    argv = run_argv.read_bytes().decode().removesuffix("\0").split("\0")
    command = argv[argv.index("--") + 1 :]
    assert command[:3] == ["bash", f"{root}/scripts/lib/driver_scope.sh", "--entry"]
    assert command[3] == mode
    assert re.fullmatch(rf"lu-{mode}-[a-z]+-[a-z]+-{UUID}\.scope", command[4])
    assert command[5:] == ["-" if mode == "interactive" else "219", f"{root}/{wrapper}", "--", *TRICKY]


# --- Ordering and refusals -------------------------------------------------


@pytest.mark.parametrize(
    ("wrapper", "args", "weekly", "code", "message"),
    [
        ("start-claude.sh", ("--does-not-exist",), "0", 2, "unknown launcher flag"),
        ("start-glmcc.sh", ("--epic", "devops"), "0", 2, "interactive launchers reject --epic"),
        ("start-kimicc.sh", ("--harness", "kimi-code"), "0", 2, "always uses Claude Code"),
        ("start-claude-driver.sh", ("--epic", "devops", "--model", "not-certified"), "0", 4, "not certified"),
        ("start-gemini-driver.sh", ("--epic", "devops", "--model", "gemini-unknown"), "0", 4, "not certified"),
        ("start-claude.sh", ("--model", "opus"), "0", 7, "Opus is blocked"),
        ("scripts/start-bio-driver.sh", (), "99", 7, "Claude weekly usage is 99%"),
        ("start-codex-cto.sh", ("--force",), "0", 2, "CTO launchers reject --force"),
    ],
)
def test_admission_refusals_keep_their_codes_before_manager_contact(
    tmp_path: Path, wrapper: str, args: tuple[str, ...], weekly: str, code: int, message: str
) -> None:
    root, env = _checkout(tmp_path)
    _write(root / "scripts/lib/claude_weekly_used.py", f"print('{weekly}')\n")
    result = _launch(root, env, wrapper, *args)
    assert result.returncode == code, result.stdout + result.stderr
    assert message in result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()
    assert "DRIVER_SCOPE_" not in result.stderr
    assert _events(env) == []


@pytest.mark.parametrize("wrapper", ["start-claude.sh", "start-glmcc.sh", "scripts/start-bio-driver.sh"])
@pytest.mark.parametrize("request_kind", ["help", "dry-run"])
def test_help_and_dry_run_make_no_manager_calls(tmp_path: Path, wrapper: str, request_kind: str) -> None:
    root, env = _checkout(tmp_path)
    extra = {"ZAI_API_KEY": "test-key"}
    if request_kind == "help":
        result = _launch(root, env, wrapper, "--help", **extra)
        assert "Usage:" in result.stdout
    else:
        result = _launch(root, env, wrapper, **extra, LAUNCHER_DRY_RUN="1")
        assert "would enter a verified per-session memory-limited scope in lu-driver.slice" in result.stdout
    assert result.returncode == 0, result.stdout + result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()
    assert not Path(env["TEST_ARGV"]).exists()


@pytest.mark.parametrize(
    ("extra", "reason"),
    [
        ({"FAKE_BUS_FAIL": "1"}, "user-manager-unavailable"),
        ({"FAKE_SLICE_FRAGMENT": ""}, "slice-not-installed"),
        ({"FAKE_OOM_POLICY": "stop"}, "unit-properties-mismatch"),
        ({"FAKE_UNIT_SLICE": "app.slice"}, "unit-properties-mismatch"),
        ({"FAKE_MEMORY_MAX": "1"}, "limits-mismatch"),
        ({"LU_DRIVER_MEMORY_MAX": "max"}, "invalid-limits"),
    ],
)
def test_interactive_scope_failures_exit_6_before_preparation(
    tmp_path: Path, extra: dict[str, str], reason: str
) -> None:
    root, env = _checkout(tmp_path)
    result = _launch(root, env, "start-claude.sh", **extra)
    assert result.returncode == 6, result.stdout + result.stderr
    assert f"DRIVER_SCOPE_REFUSED reason={reason};" in result.stderr
    names = [name for name, _ in _events(env)]
    assert not {"rules", "validate", "preflight", "deploy", "exec"} & set(names)
    assert not any(name.startswith("provider") for name in names)


def test_unlisted_entry_point_is_refused(tmp_path: Path) -> None:
    """A copy outside the checkout cannot name its own replay target."""
    root, env = _checkout(tmp_path)
    alias = tmp_path / "elsewhere" / "start-claude.sh"
    _write(
        alias,
        f'#!/usr/bin/env bash\nset -euo pipefail\nsource {shlex.quote(str(root))}/scripts/lib/launcher_core.sh\nlauncher_main claude interactive "$@"\n',
        0o755,
    )
    result = subprocess.run(
        ["bash", str(alias)],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=DEADLINE_S,
    )
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=entrypoint-not-allowlisted;" in result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()


def test_entry_point_must_run_its_listed_provider_and_mode(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    wrapper = root / "start-glmcc.sh"
    wrapper.write_text(wrapper.read_text().replace("launcher_main glm interactive", "launcher_main kimi interactive"))
    result = _launch(root, env, "start-glmcc.sh")
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=entrypoint-mismatch;" in result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()


# --- Re-entry identity -----------------------------------------------------


def _forged_reentry(
    root: Path, env: dict[str, str], wrapper: str, unit: str, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a wrapper as though the manager had placed this very PID in `unit`."""
    Path(env["FAKE_CGROUP"]).write_text(f"0::/test/lu.slice/lu-driver.slice/{unit}\n")
    forger = _write(
        root.parent / "forge.sh",
        f"export LU_DRIVER_SCOPE_PID=$$ LU_DRIVER_SCOPE_UNIT={shlex.quote(unit)}\n"
        f'exec bash {shlex.quote(str(root / wrapper))} "$@"\n',
    )
    result = subprocess.run(
        ["bash", str(forger), *args],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=DEADLINE_S,
    )
    _assert_no_real_manager(env)
    return result


@pytest.mark.parametrize(
    ("wrapper", "unit", "reason"),
    [
        # A driver adopting an interactive scope, and the reverse.
        ("start-claude-driver.sh", "lu-interactive-claude-claude-{uuid}.scope", "mode-mismatch"),
        ("start-claude.sh", "lu-driver-claude-devops-{uuid}.scope", "mode-mismatch"),
        # The right mode, another wrapper's identity: glm into a glmcc scope.
        ("start-glm.sh", "lu-interactive-glm-glmcc-{uuid}.scope", "identity-mismatch"),
        ("start-claude.sh", "lu-interactive-claude-bio-{uuid}.scope", "identity-mismatch"),
        ("start-claude-driver.sh", "lu-driver-claude-devops-x-{uuid}.scope", "identity-mismatch"),
        ("start-claude.sh", "lu-interactive-claude-claude-not-a-uuid.scope", "mode-mismatch"),
    ],
)
def test_same_pid_reentry_refuses_mode_or_identity_mismatch(
    tmp_path: Path, wrapper: str, unit: str, reason: str
) -> None:
    root, env = _checkout(tmp_path)
    unit = unit.format(uuid=_PARENT)
    args = ("--epic", "devops") if wrapper.endswith("-driver.sh") else ()
    result = _forged_reentry(root, env, wrapper, unit, *args)
    assert result.returncode == 6, result.stdout + result.stderr
    assert f"DRIVER_SCOPE_REFUSED reason={reason};" in result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()
    assert not [name for name, _ in _events(env) if name in {"rules", "exec"} or name.startswith("provider")]


def test_matching_same_pid_reentry_is_accepted(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    unit = f"lu-interactive-glm-glmcc-{_PARENT}.scope"
    result = _forged_reentry(root, env, "start-glmcc.sh", unit)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()
    assert _identity(env)["unit"] == unit


def test_inherited_scope_identity_from_a_parent_is_not_reentry(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    parent = f"lu-interactive-claude-claude-{_PARENT}.scope"
    result = _launch(root, env, "start-claude.sh", LU_DRIVER_SCOPE_PID="1", LU_DRIVER_SCOPE_UNIT=parent)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    assert _identity(env)["unit"] != parent


@pytest.mark.parametrize(
    ("mode", "unit"),
    [
        ("interactive", "lu-driver-claude-devops-{uuid}.scope"),
        ("driver", "lu-interactive-claude-claude-{uuid}.scope"),
        ("other", "lu-interactive-claude-claude-{uuid}.scope"),
    ],
)
def test_entry_helper_refuses_a_forged_mode(tmp_path: Path, mode: str, unit: str) -> None:
    """The initial verification ties the unit's mode to the launcher's validated mode."""
    root, env = _checkout(tmp_path)
    unit = unit.format(uuid=_PARENT)
    Path(env["FAKE_CGROUP"]).write_text(f"0::/test/lu.slice/lu-driver.slice/{unit}\n")
    marker = tmp_path / "marker"
    result = subprocess.run(
        [
            "bash",
            "-c",
            f'exec 219>{shlex.quote(str(marker))}; exec bash "$@"',
            "entry",
            str(root / "scripts/lib/driver_scope.sh"),
            "--entry",
            mode,
            unit,
            "219",
            str(root / "start-claude.sh"),
        ],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=DEADLINE_S,
    )
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=mode-mismatch;" in result.stderr
    assert marker.read_text() == "refused\n"
    assert not Path(env["TEST_EVENTS"]).exists()


# --- Lease isolation ---------------------------------------------------------

_SUPERVISOR = {
    "SESSION_SUPERVISOR_WAKE_DELIVERY": "fixture-delivery",
    "SESSION_SUPERVISOR_WAKE_STREAM": "epic:9999",
    "LC_SUPERVISORY_PREDECESSOR_GENERATION": "30",
    "SESSION_HANDOFF_AGENT": "fixture-driver",
    "SESSION_STREAM_ID": "epic:9999",
    "SESSION_STREAM_LEASE_ID": "inherited-lease",
}


@pytest.mark.parametrize("wrapper", sorted(INTERACTIVE))
def test_interactive_session_never_touches_a_lease_even_with_inherited_supervisor_state(
    tmp_path: Path, wrapper: str
) -> None:
    root, env = _checkout(tmp_path)
    result = _launch(root, env, wrapper, **_SUPERVISOR)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    names = [name for name, _ in _events(env)]
    assert not [name for name in names if name.startswith(("lease-", "rollover-", "publish", "canary"))], names


def test_interactive_scope_start_failure_preserves_systemd_status_without_publishing(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    result = _launch(root, env, "start-claude.sh", FAKE_SCOPE_FAIL="1", **_SUPERVISOR)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "fake systemd-run: scope start failed" in result.stderr
    assert "DRIVER_SCOPE_REFUSED" not in result.stderr
    assert "DRIVER_SCOPE_EXIT" not in result.stderr
    assert _events(env) == []
    assert _lines(env["FAKE_LOGGER_MESSAGES"]) == []


def test_interactive_scope_needs_no_entry_marker(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    _write(tmp_path / "scope-bin/mktemp", "#!/usr/bin/env bash\nexit 1\n", 0o755)
    result = _launch(root, env, "start-claude.sh")
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert "DRIVER_SCOPE_EXIT" not in result.stderr
    assert _lines(env["FAKE_LOGGER_MESSAGES"]) == []


# --- Nesting -------------------------------------------------------------------


@pytest.mark.parametrize(
    "parent",
    [f"lu-driver-claude-devops-{_PARENT}.scope", f"lu-interactive-codex-codex-{_PARENT}.scope"],
)
@pytest.mark.parametrize(("wrapper", "args"), [("start-claude.sh", ()), ("start-grok-driver.sh", ("--epic", "devops"))])
def test_launch_from_a_session_scope_starts_a_sibling_scope(
    tmp_path: Path, parent: str, wrapper: str, args: tuple[str, ...]
) -> None:
    root, env = _checkout(tmp_path)
    Path(env["FAKE_CGROUP"]).write_text(f"0::/test/lu.slice/lu-driver.slice/{parent}/tools\n")
    result = _launch(root, env, wrapper, *args, LU_DRIVER_SCOPE_PID="1", LU_DRIVER_SCOPE_UNIT=parent)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    unit = _identity(env)["unit"]
    assert unit != parent
    call = next(line for line in _lines(env["FAKE_MANAGER_CALLS"]) if line.startswith("systemd-run "))
    # A sibling in the same slice, never a child of the parent scope.
    assert f"--slice=lu-driver.slice --unit={unit} " in call


@pytest.mark.parametrize(
    ("wrapper", "args"),
    [("start-claude.sh", ()), ("scripts/start-bio-driver.sh", ()), ("start-claude-driver.sh", ("--epic", "devops"))],
)
@pytest.mark.parametrize(
    "cgroup",
    [
        "/test/lu.slice/lu-dispatch.slice/lu-worker-x.scope",
        "/test/lu.slice/lu-dispatch.slice/lu-dispatch-a.slice/w.scope/sub",
    ],
)
def test_launch_from_the_dispatch_slice_is_refused_without_manager_contact(
    tmp_path: Path, wrapper: str, args: tuple[str, ...], cgroup: str
) -> None:
    root, env = _checkout(tmp_path)
    Path(env["FAKE_CGROUP"]).write_text(f"0::{cgroup}\n")
    result = _launch(root, env, wrapper, *args)
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=inside-dispatch-slice;" in result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()
    assert _events(env) == []


def test_unreadable_caller_cgroup_is_refused(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    Path(env["FAKE_CGROUP"]).unlink()
    result = _launch(root, env, "start-claude.sh")
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=caller-cgroup-unavailable;" in result.stderr
    assert not Path(env["FAKE_MANAGER_CALLS"]).exists()


@pytest.mark.host_dispatch_probe
def test_dispatch_from_an_interactive_scope_stays_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, driver_scope_detection: Callable[[], bool]
) -> None:
    """Downstream: bounded worker scopes are allowed, the unbounded fallback is refused."""
    from scripts.orchestration import dispatch_isolation as iso
    from tests.test_dispatch_isolation import _PY, _env, _install_fakes, _subtree

    monkeypatch.setattr(iso, "_caller_in_driver_scope", driver_scope_detection)
    original = Path.read_text
    interactive = f"0::/user.slice/user-1000.slice/user@1000.service/lu.slice/lu-driver.slice/lu-interactive-claude-claude-{_PARENT}.scope\n"

    def read(path: Path, *args, **kwargs):
        return interactive if str(path) == "/proc/self/cgroup" else original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert iso._caller_in_driver_scope() is True
    env = _env(_install_fakes(tmp_path), FAKE_SYSTEMD_RUN="exec")
    proc, launch = iso.spawn_detached_worker(
        [_PY, "-c", "raise SystemExit(5)"],
        task_id="interactive-child",
        run_nonce="bounded",
        env=env,
        probe_env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        subtree_path=_subtree(tmp_path),
    )
    assert launch.mode == iso.LAUNCH_SCOPE
    assert proc.wait(timeout=10) == 5
    monkeypatch.setattr(iso, "probe_isolation", lambda *a, **kw: iso.ProbeResult(False, "bus unavailable"))
    started: list[object] = []
    with pytest.raises(iso.DispatchIsolationError, match="fallback-refused: inside-driver-scope"):
        iso.spawn_detached_worker(
            ["worker"], task_id="t", run_nonce="n", env={}, popen=lambda *a, **kw: started.append(a)
        )
    assert started == []


@pytest.mark.parametrize(("cap", "inherited", "expected"), [(None, None, "2"), ("3", "8", "3"), ("3", "1", "1")])
def test_interactive_scope_caps_pytest_auto_workers(
    tmp_path: Path, cap: str | None, inherited: str | None, expected: str
) -> None:
    root, env = _checkout(tmp_path)
    extra = {} if inherited is None else {"PYTEST_XDIST_AUTO_NUM_WORKERS": inherited}
    if cap is not None:
        extra["LU_DRIVER_PYTEST_MAX_WORKERS"] = cap
    result = _launch(root, env, "start-codex.sh", **extra)
    assert result.returncode == PROVIDER_RC, result.stdout + result.stderr
    assert f"provider xdist={expected}" in [name for name, _ in _events(env)]


def test_adapter_refusal_inside_the_scope_keeps_its_code(tmp_path: Path) -> None:
    root, env = _checkout(tmp_path)
    adapter = root / "scripts/launchers/grok.sh"
    adapter.write_text(adapter.read_text() + "launcher_adapter_validate() { lu_test_event validate; exit 2; }\n")
    result = _launch(root, env, "start-grok.sh")
    assert result.returncode == 2, result.stdout + result.stderr
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    assert [name for name, _ in _events(env)] == ["rules", "validate"]


# --- Terminal: signals, TTY, resize, suspend ---------------------------------


class _Terminal:
    """A launcher job under the job-control shell on a fresh pseudo-terminal."""

    def __init__(self, tmp_path: Path, argv: list[str], env: dict[str, str], cwd: Path) -> None:
        self.status = tmp_path / "jobshell-status"
        jobshell = _write(tmp_path / "jobshell.py", _JOBSHELL)
        self.master, slave = os.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        self.output = b""
        self.process = subprocess.Popen(
            [sys.executable, "-I", str(jobshell), str(self.status), *argv],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=cwd,
            env=env,
            start_new_session=True,
        )
        os.close(slave)

    def drain(self, timeout: float = 0.05) -> None:
        while select.select([self.master], [], [], timeout)[0]:
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                return
            if not chunk:
                return
            self.output += chunk
            timeout = 0

    def wait_for(self, predicate: Callable[[], bool], what: str) -> None:
        deadline = time.monotonic() + DEADLINE_S
        while time.monotonic() < deadline:
            self.drain()
            if predicate():
                return
            if self.process.poll() is not None and not predicate():
                break
        pytest.fail(f"timed out waiting for {what}; output:\n{self.output.decode(errors='replace')}")

    def send(self, data: bytes) -> None:
        os.write(self.master, data)

    def resize(self, rows: int, columns: int) -> None:
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))

    def finish(self) -> int:
        deadline = time.monotonic() + DEADLINE_S
        while self.process.poll() is None and time.monotonic() < deadline:
            self.drain()
        self.drain()
        assert self.process.returncode is not None, self.output.decode(errors="replace")
        return self.process.returncode

    def close(self) -> None:
        job = next((line.split()[1] for line in _lines(self.status) if line.startswith("job ")), None)
        if job is not None:
            with suppress(ProcessLookupError, PermissionError):
                os.killpg(int(job), signal.SIGKILL)
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=10)
        os.close(self.master)


def _signal_session(tmp_path: Path, wrapper: str, *args: str) -> tuple[_Terminal, dict[str, str]]:
    root, env = _checkout(tmp_path)
    env = {**env, "TEST_PROVIDER": env["TEST_SIGNAL_PROVIDER"]}
    terminal = _Terminal(tmp_path, ["bash", str(root / wrapper), *args], env, root)
    terminal.wait_for(
        lambda: any(line.startswith("ready ") for line in _lines(env["TEST_SIGNAL_LOG"])), "provider readiness"
    )
    return terminal, env


def _signal_log(env: dict[str, str]) -> list[str]:
    return _lines(env["TEST_SIGNAL_LOG"])


@pytest.mark.parametrize("name", ["HUP", "TERM"])
@pytest.mark.parametrize("target", ["group", "pid"])
def test_hup_term_delivery_exactly_once(tmp_path: Path, name: str, target: str) -> None:
    """Ten group and ten PID deliveries per signal, with one synthetic provider."""
    root, env = _checkout(tmp_path)
    provider = Path(env["TEST_SIGNAL_PROVIDER"])
    provider.write_text(
        provider.read_text().replace(
            'stat="$(< /proc/$$/stat)"',
            'trap \'printf "HUP\\n" >> "$log"\' HUP\n'
            'trap \'printf "TERM\\n" >> "$log"\' TERM\n'
            'stat="$(< /proc/$$/stat)"',
        )
    )
    counts = []
    for iteration in range(10):
        log = tmp_path / f"signal-{iteration}"
        case_env = {**env, "TEST_PROVIDER": str(provider), "TEST_SIGNAL_LOG": str(log)}
        process = subprocess.Popen(
            ["bash", str(root / "start-claude.sh")],
            cwd=root,
            env=case_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            wait_until(lambda log=log: any(row.startswith("ready ") for row in _lines(log)), timeout=DEADLINE_S)
            ready = next(row for row in _lines(log) if row.startswith("ready "))
            identity = dict(item.split("=", 1) for item in ready.split()[1:])
            assert int(identity["pid"]) == process.pid
            assert int(identity["pgrp"]) == process.pid
            members = []
            for entry in Path("/proc").iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
                except (FileNotFoundError, ProcessLookupError):
                    continue
                if int(fields[2]) == process.pid:
                    members.append(int(entry.name))
            assert members == [process.pid], members
            sig = getattr(signal, f"SIG{name}")
            if target == "group":
                os.killpg(process.pid, sig)
            else:
                os.kill(process.pid, sig)
            wait_until(lambda log=log: name in _lines(log), timeout=DEADLINE_S, message=f"provider {name}")
            _, stderr = process.communicate(b"done\n", timeout=DEADLINE_S)
            assert process.returncode == PROVIDER_RC, stderr.decode(errors="replace")
            rows = _lines(log)
            assert rows[-1] == "LINE done", rows
            counts.append(rows.count(name))
            assert "DRIVER_SCOPE_EXIT" not in stderr.decode(errors="replace")
        finally:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
    assert counts == [1] * 10, (name, target, counts)
    _assert_no_real_manager(env)


def test_interactive_terminal_keeps_tty_stdin_and_foreground_group(tmp_path: Path) -> None:
    terminal, env = _signal_session(tmp_path, "start-claude.sh")
    try:
        ready = next(line for line in _signal_log(env) if line.startswith("ready "))
        fields = dict(item.split("=", 1) for item in ready.split()[1:])
        assert fields["tty"] == "yes"
        # The provider is in the terminal's foreground process group.
        assert fields["pgrp"] == fields["foreground"]
        terminal.send(b"hello there\n")
        terminal.wait_for(lambda: "LINE hello there" in _signal_log(env), "a terminal line")
        terminal.send(b"done\n")
        assert terminal.finish() == PROVIDER_RC
    finally:
        terminal.close()
    _assert_no_real_manager(env)


@pytest.mark.parametrize(("key", "name", "status"), [(b"\x03", "INT", PROVIDER_RC), (b"\x1c", "QUIT", 43)])
def test_interactive_keyboard_signal_reaches_the_provider_exactly_once(
    tmp_path: Path, key: bytes, name: str, status: int
) -> None:
    terminal, env = _signal_session(tmp_path, "start-claude.sh")
    try:
        terminal.send(key)
        terminal.wait_for(lambda: name in _signal_log(env), f"provider {name}")
        if name == "INT":
            terminal.send(b"done\n")
        assert terminal.finish() == status
    finally:
        terminal.close()
    assert _signal_log(env).count(name) == 1, _signal_log(env)


def test_interactive_resize_reaches_the_provider_once(tmp_path: Path) -> None:
    terminal, env = _signal_session(tmp_path, "start-claude.sh")
    try:
        terminal.resize(33, 101)
        terminal.wait_for(lambda: any(line.startswith("WINCH") for line in _signal_log(env)), "provider WINCH")
        terminal.send(b"done\n")
        assert terminal.finish() == PROVIDER_RC
    finally:
        terminal.close()
    assert [line for line in _signal_log(env) if line.startswith("WINCH")] == ["WINCH 33 101"]


def test_interactive_suspend_and_resume_stop_and_continue_the_whole_job(tmp_path: Path) -> None:
    terminal, env = _signal_session(tmp_path, "start-claude.sh")
    try:
        terminal.send(b"\x1a")
        terminal.wait_for(lambda: "CONT" in _signal_log(env), "provider resume")
        terminal.send(b"after resume\n")
        terminal.wait_for(lambda: "LINE after resume" in _signal_log(env), "input after resume")
        terminal.send(b"done\n")
        assert terminal.finish() == PROVIDER_RC
    finally:
        terminal.close()
    stops = [line for line in _lines(terminal.status) if line.startswith("stopped ")]
    # Direct exec leaves just the synthetic provider in this foreground job.
    assert stops == ["stopped T"], _lines(terminal.status)
    assert _signal_log(env).count("CONT") == 1


def test_interactive_pid_signal_reaches_provider_once_without_a_foreground_terminal(tmp_path: Path) -> None:
    """Direct exec delivers PID INT and preserves the provider's own status."""
    root, env = _checkout(tmp_path)
    env = {**env, "TEST_PROVIDER": env["TEST_SIGNAL_PROVIDER"]}
    # A runner started as a background job ignores INT, and Bash cannot trap a
    # signal ignored on entry: give the launcher a caller's default disposition.
    original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        process = subprocess.Popen(
            ["bash", str(root / "start-claude.sh")],
            cwd=root,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    finally:
        signal.signal(signal.SIGINT, original_handler)

    def alive() -> bool:
        assert process.poll() is None, f"launcher exited early with {process.returncode}"
        return True

    try:
        wait_until(
            lambda: alive() and any(line.startswith("ready ") for line in _signal_log(env)),
            timeout=DEADLINE_S,
            message="provider readiness",
        )
        process.send_signal(signal.SIGINT)
        wait_until(lambda: "INT" in _signal_log(env), timeout=DEADLINE_S, message="provider INT")
        _, stderr = process.communicate(b"done\n", timeout=DEADLINE_S)
    finally:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    assert _signal_log(env).count("INT") == 1
    assert process.returncode == PROVIDER_RC, stderr.decode()
    assert "DRIVER_SCOPE_EXIT" not in stderr.decode()


def test_driver_keyboard_interrupt_cleans_the_lease_once(tmp_path: Path) -> None:
    """The real lease-owning supervisor path: one cleanup and the documented 130."""
    terminal, env = _signal_session(tmp_path, "start-claude-driver.sh", "--epic", "devops")
    try:
        terminal.send(b"\x03")
        terminal.wait_for(lambda: "INT" in _signal_log(env), "provider INT")
        terminal.send(b"done\n")
        assert terminal.finish() == 130
    finally:
        terminal.close()
    names = [name for name, _ in _events(env)]
    assert names.count("lease-open") == names.count("lease-close") == 1, names
    assert _signal_log(env).count("INT") >= 1


@pytest.mark.xfail(
    strict=True,
    reason="Residual (#9624, not fixed by D1): a terminal Ctrl-C reaches a driver's provider twice; "
    "the supervisor shell re-sends the INT the provider already received from the terminal.",
)
def test_driver_keyboard_interrupt_reaches_the_provider_exactly_once(tmp_path: Path) -> None:
    terminal, env = _signal_session(tmp_path, "start-claude-driver.sh", "--epic", "devops")
    try:
        terminal.send(b"\x03")
        terminal.wait_for(lambda: "INT" in _signal_log(env), "provider INT")
        # The supervisor forwards after its 0.1 s wait slice; allow it to land.
        with suppress(AssertionError):
            wait_until(lambda: _signal_log(env).count("INT") > 1, timeout=3, message="a second INT")
        terminal.send(b"done\n")
        terminal.finish()
    finally:
        terminal.close()
    assert _signal_log(env).count("INT") == 1, _signal_log(env)


# --- Live containment (opt-in) -----------------------------------------------


def test_bounded_live_interactive_scope_soak(tmp_path: Path) -> None:
    """Explicit opt-in: an interactive session's provider dies alone at its scope's maximum."""
    require_soak_opt_in()
    root, _ = _checkout(tmp_path)
    # The production helper and manager, rather than the fake kernel/manager.
    shutil.copy2(REPO / "scripts/lib/driver_scope.sh", root / "scripts/lib/driver_scope.sh")
    hog, proof = soak_hog(tmp_path)
    provider = _write(
        root / "provider.sh",
        f"#!/usr/bin/env bash\nexec {shlex.quote(sys.executable)} {shlex.quote(str(hog))}\n",
        0o755,
    )
    env = {
        **soak_environment(),
        "HOME": str(tmp_path / "home"),
        "LAUNCHER_DRY_RUN": "0",
        # The recording stand-ins read the real cgroup of the shell recording.
        "FAKE_CGROUP": "/proc/self/cgroup",
        "TEST_EVENTS": str(tmp_path / "events"),
        "TEST_IDENTITY": str(tmp_path / "identity"),
        "TEST_ARGV": str(tmp_path / "argv"),
        "TEST_PROVIDER": str(provider),
    }
    result, receipt = run_live_soak(["bash", str(root / "start-claude.sh")], root, env, proof)
    assert result.returncode == -signal.SIGKILL, result.stdout + result.stderr
    unit = str(receipt["unit"])
    assert unit.startswith("lu-interactive-claude-claude-")
    names = [name for name, _ in _events(env)]
    assert not [name for name in names if name.startswith(("lease-", "rollover-", "publish"))]
    assert all(cgroup == unit for _, cgroup in _events(env)), _events(env)
