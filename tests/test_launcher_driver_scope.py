"""Kernel/manager fakes for scope entry; live containment is opt-in and bounded."""

from __future__ import annotations

import contextlib
import os
import re
import select
import shlex
import shutil
import signal
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.wait_helpers import wait_until

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("name", "expected"), [("INT", 130), ("TERM", 143), ("HUP", 129)])
@pytest.mark.parametrize("delivery", ["pid", "group"])
def test_forwarder_finishes_close_and_reaps_children_after_repeated_signal(
    tmp_path: Path, name: str, expected: int, delivery: str
) -> None:
    """Check the core's own status without the outer scope's status translation."""
    from tests.test_launcher_interactive_scope import DEADLINE_S, _assert_no_test_processes, _test_processes, _write

    gate = tmp_path / "gate"
    os.mkfifo(gate)
    gate_fd = os.open(gate, os.O_RDWR | os.O_NONBLOCK)
    ready = tmp_path / "ready"
    received = tmp_path / "received"
    attempts = tmp_path / "attempts"
    closed = tmp_path / "closed"
    client_pid = tmp_path / "client-pid"
    core = _write(tmp_path / "launcher_core.sh", (REPO / "scripts/lib/launcher_core.sh").read_text())
    provider = _write(tmp_path / "provider.py", """import signal, sys
from pathlib import Path
def stop(sig, frame):
    Path(sys.argv[2]).write_text(str(sig))
    raise SystemExit(0)
for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, stop)
Path(sys.argv[1]).write_text('ready')
signal.pause()
""")
    # Only this disposable helper can receive the real close function's call.
    _write(tmp_path / ".venv/bin/python", """#!/usr/bin/env bash
[ "$*" = '-m scripts.session_supervisor close --role driver' ] || exit 97
printf '%s\\n' "$$" > "$TEST_CLIENT_PID"
printf 'close\\n' >> "$TEST_ATTEMPTS"
IFS= read -r -t 60 _ < "$TEST_GATE" || exit 98
printf 'closed\\n' > "$TEST_CLOSED"
""", 0o755)
    launcher = _write(tmp_path / "forwarder.sh", f"""#!/usr/bin/env bash
source {shlex.quote(str(core))}
source {shlex.quote(str(REPO / 'scripts/lib/session_supervisor.sh'))}
LC_DURABLE_HELPER_ROOT="$PWD"
LC_PROVIDER=claude
{shlex.quote(sys.executable)} -I {shlex.quote(str(provider))} {shlex.quote(str(ready))} {shlex.quote(str(received))} &
LC_DRIVER_CHILD_PID=$!
sleep 300 & LC_SUPERVISORY_WATCH_PID=$!
sleep 300 & LC_DRIVER_RENEW_PID=$!
sleep 300 & LC_OBSERVER_HEARTBEAT_PID=$!
trap 'launcher_forward_driver_signal {name} {expected}' {name}
printf 'armed\\n' > armed
IFS= read -r _ < "$TEST_GATE"
""")
    env = {**os.environ, "TEST_GATE": str(gate), "TEST_ATTEMPTS": str(attempts),
           "TEST_CLOSED": str(closed), "TEST_CLIENT_PID": str(client_pid)}
    process = subprocess.Popen(["bash", str(launcher)], cwd=tmp_path, env=env, start_new_session=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        wait_until(lambda: ready.exists() and (tmp_path / "armed").exists(), timeout=DEADLINE_S,
                   message="provider and direct forwarder traps")
        sig = getattr(signal, f"SIG{name}")
        process.send_signal(sig)
        wait_until(attempts.exists, timeout=DEADLINE_S, message="in-flight close client")
        assert not closed.exists()
        if delivery == "group":
            # The new session belongs only to this fixture. Refuse delivery if
            # either its identity or any current member cannot be established.
            assert process.poll() is None
            assert os.getpgid(process.pid) == os.getsid(process.pid) == process.pid
            assert process.pid != os.getpgrp()
            members = set()
            for entry in Path("/proc").iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
                except FileNotFoundError:
                    continue
                if int(fields[2]) == process.pid:
                    assert int(fields[3]) == process.pid
                    members.add(int(entry.name))
            assert {process.pid, int(client_pid.read_text())} <= members
            assert members <= set(_test_processes(tmp_path))
            os.killpg(process.pid, sig)
        else:
            process.send_signal(sig)
        os.write(gate_fd, b"release\nrelease\n")
        stdout, stderr = process.communicate(timeout=DEADLINE_S)
        assert process.returncode == expected, stdout + stderr
        assert received.read_text() == str(sig)
        assert attempts.read_text().splitlines() == ["close"]
        assert closed.read_text() == "closed\n"
        wait_until(lambda: not _test_processes(tmp_path),
                   timeout=5, message="provider and watcher cleanup")
        _assert_no_test_processes(tmp_path)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=10)
        os.close(gate_fd)


def manager_guard(directory: Path) -> Path:
    """Stand-ins that refuse and record any user-manager call no fake intercepted.

    Placed after a fixture's fake manager on PATH: a launcher fixture that would
    reach this host's real user manager fails at once instead (#9624).
    """
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("systemd-run", "systemctl"):
        exe = directory / name
        exe.write_text(
            "#!/usr/bin/env bash\n"
            f'printf \'%s\\n\' "{name} $*" >> "${{LU_TEST_REAL_MANAGER_CONTACT:-/dev/null}}"\n'
            f"printf 'TEST GUARD: {name} would reach the real user manager\\n' >&2\n"
            "exit 97\n"
        )
        exe.chmod(0o755)
    return directory


def scope_sandbox(root: Path, tmp_path: Path) -> dict[str, str]:
    """Copy the real helper, replacing only kernel reads with test-owned files."""
    helper = root / "scripts/lib/driver_scope.sh"
    helper.parent.mkdir(parents=True, exist_ok=True)
    body = (REPO / "scripts/lib/driver_scope.sh").read_text()
    assert body.count('"/proc/$$/cgroup"') == 1
    body = body.replace('"/proc/$$/cgroup"', '"$FAKE_CGROUP"')
    helper.write_text(body)
    bindir = tmp_path / "scope-bin"
    bindir.mkdir(exist_ok=True)
    exe = bindir / "systemd-run"
    exe.write_text("""#!/usr/bin/env bash
printf 'start\\n' >> "$FAKE_STARTS"
printf 'systemd-run %s\\n' "$*" >> "${FAKE_MANAGER_CALLS:-/dev/null}"
[ -z "${FAKE_RUN_ARGV:-}" ] || printf '%s\\0' "$@" > "$FAKE_RUN_ARGV"
for arg; do case "$arg" in --unit=*) unit="${arg#*=}" ;; esac; done
while [ "$1" != -- ]; do shift; done
shift
[ "${FAKE_SCOPE_FAIL:-0}" = 0 ] || { printf 'fake systemd-run: scope start failed\\n' >&2; exit 1; }
printf '0::/test/lu.slice/lu-driver.slice/%s\\n' "$unit" > "$FAKE_CGROUP"
if [ "${FAKE_UNLINK_ENTRY:-0}" = 1 ]; then
  rc=0
  "$@" || rc=$?
  rm -f "$TMPDIR"/tmp.*
  exit "$rc"
fi
exec "$@"
""")
    exe.chmod(0o755)
    exe = bindir / "systemctl"
    exe.write_text("""#!/usr/bin/env bash
printf 'systemctl %s\\n' "$*" >> "${FAKE_MANAGER_CALLS:-/dev/null}"
[ "${FAKE_BUS_FAIL:-0}" = 0 ] || exit 1
if [[ "$*" == *lu-driver.slice* ]]; then
  printf 'LoadState=%s\\nFragmentPath=%s\\n' "${FAKE_SLICE_LOAD_STATE:-loaded}" "${FAKE_SLICE_FRAGMENT-/test/lu-driver.slice}"
  exit
fi
printf 'Id=%s\\nControlGroup=/test/lu.slice/lu-driver.slice/%s\\nSlice=%s\\nOOMPolicy=%s\\nActiveState=active\\n' "$LU_DRIVER_SCOPE_UNIT" "$LU_DRIVER_SCOPE_UNIT" "${FAKE_UNIT_SLICE:-lu-driver.slice}" "${FAKE_OOM_POLICY:-continue}"
""")
    exe.chmod(0o755)
    exe = bindir / "cat"
    exe.write_text("""#!/usr/bin/env bash
case "$1" in
 */memory.high) printf '%s\\n' "${FAKE_MEMORY_HIGH:-${LU_DRIVER_MEMORY_HIGH:-2147483648}}" ;;
 */memory.max) printf '%s\\n' "${FAKE_MEMORY_MAX:-${LU_DRIVER_MEMORY_MAX:-3221225472}}" ;;
 */memory.swap.max) printf '%s\\n' "${FAKE_MEMORY_SWAP_MAX:-${LU_DRIVER_MEMORY_SWAP_MAX:-536870912}}" ;;
 */memory.current) printf '123456\\n' ;;
 */memory.swap.current) printf '654321\\n' ;;
 *) exec /bin/cat "$@" ;;
esac
""")
    exe.chmod(0o755)
    exe = bindir / "logger"
    exe.write_text("""#!/usr/bin/env bash
[ "$#" = 3 ] && [ "$1" = -t ] && [ "$2" = lu-driver ] || exit 99
printf '%s\\n' "$3" >> "$FAKE_LOGGER_MESSAGES"
exit "${FAKE_LOGGER_RC:-0}"
""")
    exe.chmod(0o755)
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("0::/test/outside.scope\n")
    guard = manager_guard(tmp_path / "manager-guard-bin")
    return {
        "PATH": f"{bindir}:{guard}:{os.environ['PATH']}",
        "FAKE_CGROUP": str(cgroup),
        "FAKE_STARTS": str(tmp_path / "scope-starts"),
        "FAKE_MANAGER_CALLS": str(tmp_path / "manager-calls"),
        "LU_TEST_REAL_MANAGER_CONTACT": str(tmp_path / "real-manager-contact"),
        "FAKE_LOGGER_MESSAGES": str(tmp_path / "logger-messages"),
        # Hermetic: never read a deployment config from the runner's home.
        "LU_DRIVER_SCOPE_CONFIG": str(tmp_path / "no-driver-scope.env"),
        "FLEET_COMMS_ROOT": str(tmp_path / "fleet-plane"),
        "LC_SUPERVISORY_PREDECESSOR_GENERATION": "",
    }


def install_scope_sandbox(root: Path) -> None:
    """Give lifecycle fixtures a fake manager and kernel boundary.

    Every wrapper enters a scope (#9624), so each present wrapper, interactive,
    compatibility, CTO, driver or bio, exports the fakes ahead of the manager
    guard, even when a test replaces PATH.
    """
    env = scope_sandbox(root, root.parent)
    fakes, guard = env["PATH"].split(":")[:2]
    for launcher in (*root.glob("start-*.sh"), *root.glob("scripts/start-*.sh")):
        body = launcher.read_text()
        first, rest = body.split("\n", 1)
        exports = "\n".join(
            f'export PATH={shlex.quote(fakes)}:{shlex.quote(guard)}:"$PATH"'
            if key == "PATH"
            # A caller's own contact record (run_launcher) takes precedence.
            else f'export {key}="${{{key}:-{value}}}"'
            if key == "LU_TEST_REAL_MANAGER_CONTACT"
            else f"export {key}={shlex.quote(value)}"
            for key, value in env.items()
        )
        launcher.write_text(first + "\n" + exports + "\n" + rest)


def _launcher(tmp_path: Path, provider: str = "claude") -> tuple[Path, dict[str, str]]:
    root = tmp_path / "repo"
    env = scope_sandbox(root, tmp_path)
    core = root / "scripts/lib/launcher_core.sh"
    shutil.copy2(REPO / "scripts/lib/launcher_core.sh", core)
    shutil.copy2(REPO / "scripts/lib/git_identity.py", root / "scripts/lib/git_identity.py")
    env["TEST_PROJECT_PYTHON"] = sys.executable
    # Only provider/lease/preparation seams are stubbed. The full main entry,
    # defaults, uncertified-Gemini refusal, scope setup, identity and limit validation stay real.
    core.write_text(
        core.read_text()
        + """
launcher_clear_foreign_route_state() { :; }
launcher_parse() { LC_DRY_RUN=0; LC_GOVERNOR=${TEST_GOVERNOR:-0}; LC_EPIC=devops; }
launcher_drop_force_from_successor_args() { :; }
launcher_normalize_effort() { :; }
launcher_resolve_roots() { :; }
launcher_project_python() { printf '%s\\n' "$TEST_PROJECT_PYTHON"; }
launcher_publication_path() { :; }
launcher_normalize_model() { :; }
launcher_validate_mode() { :; }
launcher_load_rules_core() { [ -s "$FAKE_STARTS" ] || exit 98; printf 'PREPARED\\n'; }
launcher_prepare_driver_identity() { :; }
launcher_import_rollover_bundle() { printf 'IMPORT\\n'; }
launcher_claim_driver_lease() { printf 'LEASE\\n'; }
launcher_bind_drive_epic() { :; }
"""
    )
    (root / "scripts/lib/handoff_identity.sh").write_text("")
    (root / "scripts/lib/deploy_extensions.sh").write_text("deploy_agent_extensions() { :; }\n")
    adapter = root / "scripts/launchers/claude.sh"
    adapter.parent.mkdir(parents=True)
    adapter.write_text("""launcher_adapter_validate() { :; }
launcher_adapter_preflight() { :; }
launcher_adapter_canary() { :; }
launcher_adapter_exec() {
  read -r line
  printf 'PROVIDER:%s\\n' "$line"
  printf 'XDIST_AUTO:%s\\n' "${PYTEST_XDIST_AUTO_NUM_WORKERS:-unset}"
  printf 'GIT_IDENTITY:%s|%s|%s|%s\\n' "$GIT_AUTHOR_NAME" "$GIT_AUTHOR_EMAIL" "$GIT_COMMITTER_NAME" "$GIT_COMMITTER_EMAIL"
  exit "${TEST_RC:-0}"
}
""")
    launcher = root / f"start-{provider}-driver.sh"
    launcher.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\nsource "$(dirname "$0")/scripts/lib/launcher_core.sh"\n'
        f'launcher_main {provider} driver "$@"\n'
    )
    return launcher, env


_INHERITED_HOLDS = ("LU_DRIVER_", "PYTEST_XDIST_AUTO_NUM_WORKERS")


def _inherited_environ() -> dict[str, str]:
    """The process environment minus holds the pre-push gate or a driver scope exports.

    The gate sets PYTEST_XDIST_AUTO_NUM_WORKERS and a driver scope sets the
    LU_DRIVER_* limits; each test supplies the ones it asserts on explicitly.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith(_INHERITED_HOLDS)}


def _run(launcher: Path, env: dict[str, str], **extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(launcher)],
        cwd=launcher.parent,
        env={**_inherited_environ(), **env, **extra},
        input="stdin survives\n",
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize("extra", [{}, {"LC_DRIVER_LEASE_ENABLED": "0"}, {"TEST_GOVERNOR": "1"}])
def test_all_paths_enter_once_before_preparation(tmp_path: Path, extra: dict[str, str]) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, **extra)
    assert result.returncode == 0, result.stderr
    assert Path(env["FAKE_STARTS"]).read_text().splitlines() == ["start"]
    assert result.stdout.count("PREPARED\n") == 1
    assert "PROVIDER:stdin survives" in result.stdout
    assert "GIT_IDENTITY:Claude|claude@local.invalid|Claude|claude@local.invalid" in result.stdout
    # Generic fallbacks when neither the environment nor a config file sets limits.
    assert "high=2147483648 max=3221225472 swap=536870912 oom=continue" in result.stderr
    assert "DRIVER_SCOPE_VERIFIED" in result.stderr
    assert "parent_memory_current=123456 parent_swap_current=654321" in result.stderr


@pytest.mark.parametrize(
    "provider,model",
    [
        ("gemini", "gemini-unknown"),
        ("gemini", "gemini-3.7-flash-high"),
        ("claude", "gemini-3.8-flash-high"),
        ("claude", "gemini:gemini-3.1-pro-high"),
    ],
)
def test_uncertified_gemini_driver_refused_without_entering_scope(tmp_path: Path, provider: str, model: str) -> None:
    launcher, env = _launcher(tmp_path, provider)
    result = _run(launcher, env, LAUNCHER_MODEL=model, FAKE_BUS_FAIL="1")
    assert result.returncode == 4, result.stderr
    assert f"model '{model}' " in result.stderr
    assert "(certified: gemini-3.1-pro-high, gemini-3.8-flash-high)." in result.stderr
    assert result.stdout == ""
    assert not Path(env["FAKE_STARTS"]).exists()
    assert "DRIVER_SCOPE_" not in result.stderr


@pytest.mark.parametrize(
    "state,fragment,installed",
    [
        ("loaded", "/test/lu-driver.slice", True),
        ("loaded", "", False),
        ("masked", "/dev/null", False),
        ("not-found", "", False),
    ],
)
def test_slice_requires_loaded_unit_file(tmp_path: Path, state: str, fragment: str, installed: bool) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, FAKE_SLICE_LOAD_STATE=state, FAKE_SLICE_FRAGMENT=fragment)
    starts = Path(env["FAKE_STARTS"])
    if installed:
        assert result.returncode == 0, result.stderr
        assert starts.read_text().splitlines() == ["start"]
        assert "PROVIDER:stdin survives" in result.stdout
    else:
        assert result.returncode == 6, result.stderr
        assert "DRIVER_SCOPE_REFUSED reason=slice-not-installed" in result.stderr
        assert not starts.exists()
        assert "PREPARED" not in result.stdout
        assert "LEASE" not in result.stdout
        assert "PROVIDER:" not in result.stdout


def _assert_exit_line(stderr: str, env: dict[str, str], rc: int, forwarded: str = "none") -> None:
    lines = [line for line in stderr.splitlines() if line.startswith("DRIVER_SCOPE_EXIT")]
    assert len(lines) == 1, stderr
    match = re.fullmatch(
        rf"DRIVER_SCOPE_EXIT epic=devops rc={rc} signal={forwarded} ts=(\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}Z)",
        lines[0],
    )
    assert match, lines[0]
    timestamp = datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    assert abs((datetime.now(UTC) - timestamp).total_seconds()) < 15
    assert Path(env["FAKE_LOGGER_MESSAGES"]).read_text().splitlines() == lines


@pytest.mark.parametrize("rc", [0, 1, 2, 3, 4, 5, 137])
def test_provider_status_preserved(tmp_path: Path, rc: int) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, TEST_RC=str(rc), TZ="Pacific/Honolulu")
    assert result.returncode == rc, result.stderr
    _assert_exit_line(result.stderr, env, rc)


@pytest.mark.parametrize("rc", [0, 130])
def test_closed_stderr_preserves_exit_and_journal(tmp_path: Path, rc: int) -> None:
    launcher, env = _launcher(tmp_path)
    with subprocess.Popen(
        ["bash", str(launcher)],
        cwd=launcher.parent,
        env={**_inherited_environ(), **env, "TEST_RC": str(rc)},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        assert process.stdout is not None and process.stderr is not None
        # Preparation follows scope verification. The child then waits for
        # stdin, so the exit write happens only after the stderr reader closes.
        assert select.select([process.stdout], [], [], 15)[0], "preparation timed out"
        assert process.stdout.readline() == "PREPARED\n"
        process.stderr.close()
        stdout, _ = process.communicate("stdin survives\n", timeout=15)
    assert process.returncode == rc
    assert "PROVIDER:stdin survives" in stdout
    journal = Path(env["FAKE_LOGGER_MESSAGES"]).read_text()
    _assert_exit_line(journal, env, rc)


def test_forwarded_term_records_exit_once(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    adapter = launcher.parent / "scripts/launchers/claude.sh"
    with adapter.open("a") as stream:
        # Signal the waiting parent while this child is still running; wait for
        # the forwarded TERM instead of exiting independently.
        stream.write("""
launcher_adapter_exec() {
  trap 'exit 0' TERM
  kill -TERM "$PPID"
  while :; do sleep 0.1; done
}
""")
    result = _run(launcher, env)
    assert result.returncode == 143, result.stderr
    _assert_exit_line(result.stderr, env, 143, "TERM")


# Bash discards a child's status when a trapped signal interrupts `wait` as the
# child exits (a later `wait` then reports 127), so the waiting launcher must
# only `wait` for a child that has already exited. The race itself is
# timing-dependent; this asserts the invariant that rules it out (#9624). The
# waiter's trap is the real relay, which also must not stall the timed pause.
_WAIT_CHILD_SCRIPT = """
source "$1"
exec {ready}<> "$2"
exec {release}<> "$3"
violations=0
wait() {
  if driver_scope_child_running "$1"; then violations=$((violations + 1)); fi
  builtin wait "$@"
}
LC_MODE=driver
relayed=""
child=""
trap 'driver_scope_relay TERM' TERM
( trap - TERM; %s ) &
child=$!
%s
driver_scope_wait_child "$child"
printf 'rc=%%s violations=%%s relayed=%%s\\n' "$DS_CHILD_RC" "$violations" "$relayed"
"""


@pytest.mark.parametrize(
    ("child", "signal_waiter", "expected"),
    [
        # TERM reaches the driver waiter while its child runs; the collector
        # retains the child's own status without waiting on a running child.
        (
            "trap 'echo child-trap=TERM >&2; exit 43' TERM; "
            "echo child-ready >&\"$ready\"; while :; do sleep 0.05; done",
            True,
            "rc=43 violations=0 relayed=TERM",
        ),
        ('echo child-ready >&"$ready"; read -r -u "$release" _; exit 0', False, "rc=0 violations=0 relayed="),
        (
            'echo child-ready >&"$ready"; read -r -u "$release" _; kill -KILL $BASHPID',
            False,
            "rc=137 violations=0 relayed=",
        ),
        # Already exited, and not yet collected, when the launcher starts waiting.
        ("exit 7", False, "rc=7 violations=0 relayed="),
    ],
)
def test_waiting_launcher_collects_status_without_waiting_on_a_running_child(
    tmp_path: Path, child: str, signal_waiter: bool, expected: str
) -> None:
    ready = tmp_path / "ready"
    release = tmp_path / "release"
    os.mkfifo(ready)
    os.mkfifo(release)
    if child == "exit 7":
        synchronize = 'while driver_scope_child_running "$child"; do sleep 0.01; done'
    else:
        release_child = 'echo waiter-ready >&"$ready"' if signal_waiter else 'echo release >&"$release"'
        sender = '''(
  IFS= builtin read -r -u "$ready" token
  [ "$token" = waiter-ready ] || exit 98
  echo signal=TERM >&2
  kill -TERM $$
) &''' if signal_waiter else ""
        synchronize = f'''
IFS= read -r -u "$ready" token
[ "$token" = child-ready ] || exit 98
echo "$token" >&2
# The first read belongs to the real collector's timed pause. Release or
# signal the child only after the collector reaches that running-child path.
read() {{
  unset -f read
  echo waiter-ready >&2
  {release_child}
  builtin read "$@"
}}
{sender}
'''
    result = subprocess.run(
        [
            "bash", "-c", _WAIT_CHILD_SCRIPT % (child, synchronize), "bash",
            str(REPO / "scripts/lib/driver_scope.sh"), str(ready), str(release),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        # No controlling terminal: the waiter is never in a foreground group.
        start_new_session=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected, result.stderr
    assert "not a child" not in result.stderr
    assert "No such file" not in result.stderr
    if signal_waiter:
        assert result.stderr.splitlines() == ["child-ready", "waiter-ready", "signal=TERM", "child-trap=TERM"]
    elif child != "exit 7":
        assert result.stderr.splitlines()[:2] == ["child-ready", "waiter-ready"]


def test_reaped_child_probe_does_not_exit_the_waiting_shell() -> None:
    """A vanished /proc entry is an ordinary false result, including on Bash 5.2."""
    result = subprocess.run(
        ["bash", "-eu", "-c", '''
source "$1"
( exit 0 ) &
child=$!
wait "$child"
if driver_scope_child_running "$child"; then exit 99; fi
printf 'reaped child; waiter alive\\n'
''', "bash", str(REPO / "scripts/lib/driver_scope.sh")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "reaped child; waiter alive\n"
    assert result.stderr == ""


@pytest.mark.parametrize("name", ["plain child", "child) \nexit"])
def test_child_probe_recognizes_a_zombie_with_a_multiline_command_name(name: str) -> None:
    """Keep the child unreaped so its real kernel state remains Z during the probe."""
    child = subprocess.Popen(
        [sys.executable, "-I", "-c", """
import ctypes, sys
raise SystemExit(0 if ctypes.CDLL(None).prctl(15, sys.argv[1].encode(), 0, 0, 0) == 0 else 1)
""", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    stat = Path(f"/proc/{child.pid}/stat")
    try:
        wait_until(
            lambda: stat.read_text().rsplit(")", 1)[1].split()[0] == "Z",
            timeout=5,
            message="unreaped child to become a zombie",
        )
        assert f"({name}) Z " in stat.read_text()
        result = subprocess.run(
            ["bash", "-eu", "-c", '''
source "$1"
if driver_scope_child_running "$2"; then echo running; else echo exited; fi
''', "bash", str(REPO / "scripts/lib/driver_scope.sh"), str(child.pid)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == "exited\n"
        assert result.stderr == ""
    finally:
        _, stderr = child.communicate(timeout=10)
    assert child.returncode == 0, stderr.decode()


@pytest.mark.parametrize("phase", ["collector", "logger"])
@pytest.mark.parametrize("provider_exit", ["exit 42", "kill -KILL $$"])
def test_late_term_preserves_the_collected_provider_status(tmp_path: Path, provider_exit: str, phase: str) -> None:
    """Deliver TERM both after wait and during the final journal write."""
    from tests.test_launcher_interactive_scope import DEADLINE_S, _checkout, _lines, _Terminal, _write

    root, env = _checkout(tmp_path)
    collected = tmp_path / "collected"
    release = tmp_path / "release"
    os.mkfifo(release)
    release_fd = os.open(release, os.O_RDWR | os.O_NONBLOCK)
    hold = (
        f"printf 'collected\\n' > {shlex.quote(str(collected))}\n"
        + f"IFS= read -r -t {DEADLINE_S} _ < {shlex.quote(str(release))}\n"
    )
    if phase == "collector":
        helper = root / "scripts/lib/driver_scope.sh"
        body = helper.read_text().replace("driver_scope_wait_child() {", "original_wait_child() {")
        helper.write_text(
            body + '\ndriver_scope_wait_child() {\n  original_wait_child "$@"\n' + hold + "}\n"
        )
    else:
        logger = Path(env["PATH"].split(":")[0]) / "logger"
        first, body = logger.read_text().split("\n", 1)
        logger.write_text(first + "\n" + hold + body)
    _write(Path(env["TEST_PROVIDER"]), f"#!/usr/bin/env bash\n{provider_exit}\n", 0o755)
    terminal = _Terminal(tmp_path, ["bash", str(root / "start-claude-driver.sh"), "--epic", "devops"], env, root)
    try:
        terminal.wait_for(collected.exists, "collected provider exit")
        job = int(next(line.split()[1] for line in _lines(terminal.status) if line.startswith("job ")))
        os.kill(job, signal.SIGTERM)
        # Writing the FIFO completes the collector's positive synchronization;
        # the pending trap runs before the launcher chooses its final status.
        os.write(release_fd, b"release\n")
        expected = 137 if provider_exit.startswith("kill") else 42
        assert terminal.finish() == expected
        assert f"rc={expected} signal=none " in terminal.output.decode(errors="replace")
    finally:
        terminal.close()
        os.close(release_fd)


@pytest.mark.parametrize(("sig", "rc"), [(signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)])
def test_signal_reaches_provider_when_the_timed_pause_expires_in_the_trap(
    tmp_path: Path, sig: signal.Signals, rc: int
) -> None:
    """#11094: a trap still running when the collector's `read -t` expires is abandoned.

    Bash checks the expired read timer at the trap's next read, `mapfile` included,
    and jumps back to the read's caller. The wrapped relay sleeps past the 0.1 s
    pause first, so any trap step after the sleep that reads is cut off.
    """
    launcher, env = _launcher(tmp_path)
    helper = launcher.parent / "scripts/lib/driver_scope.sh"
    body = helper.read_text()
    assert body.count("driver_scope_relay() {") == 1
    helper.write_text(
        body.replace("driver_scope_relay() {", "original_relay() {")
        + '\ndriver_scope_relay() {\n  sleep 0.15\n  original_relay "$@"\n}\n'
    )
    child_ready, received = tmp_path / "child-ready", tmp_path / "received"
    with (launcher.parent / "scripts/launchers/claude.sh").open("a") as stream:
        stream.write("""
launcher_adapter_exec() {
  trap 'printf "INT\\n" > "$TEST_RECEIVED"; exit 0' INT
  trap 'printf "TERM\\n" > "$TEST_RECEIVED"; exit 0' TERM
  trap 'printf "HUP\\n" > "$TEST_RECEIVED"; exit 0' HUP
  : > "$TEST_CHILD_READY"
  while :; do sleep 0.05; done
}
""")
    with subprocess.Popen(
        ["bash", str(launcher)],
        cwd=launcher.parent,
        env={**_inherited_environ(), **env, "TEST_CHILD_READY": str(child_ready), "TEST_RECEIVED": str(received)},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            wait_until(child_ready.exists, timeout=15, message="provider signal traps")
            # The waiting shell spends almost all of its time in the timed pause.
            os.kill(process.pid, sig)
            try:
                _, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                pytest.fail(f"{sig.name} never reached the provider; the waiting launcher kept running")
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
    assert process.returncode == rc, stderr
    assert received.read_text() == f"{sig.name[3:]}\n"
    _assert_exit_line(stderr, env, rc, sig.name[3:])


_RELAY_SCRIPT = """
source "$1"
exec {ready}<> "$2"
exec {release}<> "$3"
relayed=""
child=""
trap 'driver_scope_relay TERM' TERM
%s
driver_scope_wait_child "$child"
printf 'rc=%%s relayed=%%s\\n' "$DS_CHILD_RC" "$relayed"
"""
# The bounded read keeps a child that is never signalled from outliving the test.
_RUNNING_CHILD = """( trap - TERM; echo child-ready >&"$ready"; read -r -t 20 -u "$release" _; exit 7 ) &
child=$!
IFS= read -r -u "$ready" token
[ "$token" = child-ready ] || exit 98"""


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        # A signal recorded before the child exists reaches it at the first wait.
        ("kill -TERM $$\n" + _RUNNING_CHILD, "rc=143 relayed=TERM"),
        # A signal recorded while the child runs, before the first wait.
        (_RUNNING_CHILD + "\nkill -TERM $$", "rc=143 relayed=TERM"),
        # The child exited on its own before the signal: its status stands.
        (
            '( exit 7 ) &\nchild=$!\nwhile driver_scope_child_running "$child"; do sleep 0.01; done\nkill -TERM $$',
            "rc=7 relayed=",
        ),
        # Recorded while the child ran, but it exited on its own before the
        # collector forwarded anything: it never received the signal, and its
        # status stands. The child state is read when forwarding, not in the trap.
        (
            _RUNNING_CHILD
            + """
read() {
  unset -f read
  kill -TERM $$
  echo release >&"$release"
  while driver_scope_child_running "$child"; do sleep 0.01; done
  builtin read "$@"
}""",
            "rc=7 relayed=",
        ),
    ],
    ids=["before-child", "before-first-wait", "child-exited", "exited-before-forward"],
)
def test_recorded_signal_is_forwarded_only_to_a_running_child(tmp_path: Path, setup: str, expected: str) -> None:
    ready = tmp_path / "ready"
    release = tmp_path / "release"
    os.mkfifo(ready)
    os.mkfifo(release)
    result = subprocess.run(
        [
            "bash", "-c", _RELAY_SCRIPT % setup, "bash",
            str(REPO / "scripts/lib/driver_scope.sh"), str(ready), str(release),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        start_new_session=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected, result.stderr


@pytest.mark.parametrize("rc", [0, 5, 137])
def test_logger_failure_preserves_exit_and_stderr(tmp_path: Path, rc: int) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, TEST_RC=str(rc), FAKE_LOGGER_RC="1")
    assert result.returncode == rc, result.stderr
    _assert_exit_line(result.stderr, env, rc)


def test_missing_logger_preserves_exit_and_stderr(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    bindir = Path(env["PATH"].split(os.pathsep, 1)[0])
    (bindir / "logger").unlink()
    # Keep the sandbox utilities available without falling back to host logger.
    for name in ("bash", "dirname", "mktemp", "rm", "date", "id", "git", "awk"):
        executable = shutil.which(name)
        assert executable is not None
        (bindir / name).symlink_to(executable)
    env["PATH"] = str(bindir)
    result = _run(launcher, env, TEST_RC="137")
    assert result.returncode == 137, result.stderr
    assert shutil.which("logger", path=env["PATH"]) is None
    assert not Path(env["FAKE_LOGGER_MESSAGES"]).exists()
    lines = [line for line in result.stderr.splitlines() if line.startswith("DRIVER_SCOPE_EXIT")]
    assert len(lines) == 1, result.stderr
    assert re.fullmatch(
        r"DRIVER_SCOPE_EXIT epic=devops rc=137 signal=none ts=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
        lines[0],
    )


@pytest.mark.parametrize("extra", [{"FAKE_SCOPE_FAIL": "1"}, {"FAKE_OOM_POLICY": "stop"}])
def test_reaped_scope_refusal_records_exit(tmp_path: Path, extra: dict[str, str]) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, **extra)
    assert result.returncode == 6, result.stderr
    _assert_exit_line(result.stderr, env, 6)


def test_entry_owner_observes_verified_after_path_unlinked(tmp_path: Path) -> None:
    """A sibling's cleanup cannot erase the completed child's entry proof."""
    launcher, env = _launcher(tmp_path)
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    result = _run(launcher, env, TMPDIR=str(temporary), FAKE_UNLINK_ENTRY="1", TEST_RC="3")
    assert result.returncode == 3, result.stderr
    assert "DRIVER_SCOPE_VERIFIED" in result.stderr
    assert "scope-start-failed" not in result.stderr
    assert "PROVIDER:stdin survives" in result.stdout
    assert not list(temporary.iterdir())


def test_failed_scope_start_publishes_only_for_a_driver_successor(tmp_path: Path) -> None:
    """The full driver wrapper still publishes only its captured start failure."""
    from tests.test_launcher_interactive_scope import _SUPERVISOR, _checkout, _events, _launch

    root, env = _checkout(tmp_path)
    result = _launch(root, env, "start-claude-driver.sh", "--epic", "devops", FAKE_SCOPE_FAIL="1", **_SUPERVISOR)
    assert result.returncode == 6, result.stdout + result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=scope-start-failed;" in result.stderr
    names = [name for name, _ in _events(env)]
    assert names.count("publish") == 1, names
    assert not [name for name in names if name.startswith(("lease-", "rollover-"))]


@pytest.mark.parametrize("publish_ok", [True, False])
def test_failed_supervisory_successor_scope_publishes_and_preserves_exit(tmp_path: Path, publish_ok: bool) -> None:
    from tests.test_session_supervisor_shell import _assert_failure_publication, _failure_publication_fixture

    launcher, env = _launcher(tmp_path)
    env.update(_failure_publication_fixture(tmp_path, seed_channel=publish_ok))
    launcher.chmod(0o755)
    helper = launcher.parent / "scripts/lib/session_supervisor.sh"
    shutil.copy2(REPO / "scripts/lib/session_supervisor.sh", helper)
    predecessor = tmp_path / "predecessor.sh"
    predecessor.write_text(f"""#!/usr/bin/env bash
set -euo pipefail
source {shlex.quote(str(helper))}
LC_ROOT={shlex.quote(str(launcher.parent))}
LC_PROVIDER=claude
LC_DRIVER_LEASE_CLOSED=1
LC_SUPERVISORY_DELIVERY=fixture-delivery
LC_DRIVER_ORIGINAL_ARGS=()
export SESSION_STREAM_ID=epic:9999 SESSION_STREAM_GENERATION=30 SESSION_STREAM_LEASE_ID=fixture-lease
session_supervisor_exec_successor
""")
    result = _run(predecessor, env, FAKE_SCOPE_FAIL="1")
    assert result.returncode == 6, result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=scope-start-failed" in result.stderr
    assert result.stdout == ""
    _assert_failure_publication(env, "scope-start-failed", published=publish_ok)


@pytest.mark.parametrize(
    "failure,generation",
    [
        ("FAKE_SCOPE_FAIL", ""),
        ("FAKE_BUS_FAIL", ""),
        ("FAKE_BUS_FAIL", "30"),
        ("FAKE_OOM_POLICY", ""),
        ("FAKE_OOM_POLICY", "30"),
    ],
)
def test_scope_refusals_publish_only_for_captured_successor_start(
    tmp_path: Path,
    failure: str,
    generation: str,
) -> None:
    from tests.test_session_supervisor_shell import _failure_publication_fixture

    launcher, env = _launcher(tmp_path)
    env.update(_failure_publication_fixture(tmp_path, seed_channel=True))
    shutil.copy2(REPO / "scripts/lib/session_supervisor.sh", launcher.parent / "scripts/lib/session_supervisor.sh")
    result = _run(
        launcher,
        env,
        **{failure: "stop" if failure == "FAKE_OOM_POLICY" else "1"},
        SESSION_SUPERVISOR_WAKE_DELIVERY="fixture-delivery",
        SESSION_SUPERVISOR_WAKE_STREAM="epic:9999",
        # No captured generation => ordinary failure; other refusal reasons
        # never publish even with a captured predecessor.
        LC_SUPERVISORY_PREDECESSOR_GENERATION=generation,
    )
    assert result.returncode == 6, result.stderr
    assert result.stdout == ""
    assert not Path(env["TEST_PUBLISH_ARGS"]).exists()


@pytest.mark.parametrize(
    "extra,reason",
    [
        ({"FAKE_BUS_FAIL": "1"}, "user-manager-unavailable"),
        ({"FAKE_SCOPE_FAIL": "1"}, "scope-start-failed"),
        ({"FAKE_OOM_POLICY": "stop"}, "unit-properties-mismatch"),
        ({"FAKE_UNIT_SLICE": "app.slice"}, "unit-properties-mismatch"),
        ({"LU_DRIVER_MEMORY_MAX": "max"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_HIGH": "5", "LU_DRIVER_MEMORY_MAX": "5"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_HIGH": "3221225473"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_MAX": "999999999999999"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_SWAP_MAX": "3221225473"}, "invalid-limits"),
        ({"LU_DRIVER_PYTEST_MAX_WORKERS": "auto"}, "invalid-limits"),
    ],
)
def test_refuse_before_preparation(tmp_path: Path, extra: dict[str, str], reason: str) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, **extra)
    assert result.returncode == 6
    assert reason in result.stderr
    assert "PREPARED" not in result.stdout
    assert "LEASE" not in result.stdout


def test_deployment_limits_from_environment_are_used(tmp_path: Path) -> None:
    # Deployment values may sit above the generic fallbacks, up to MemTotal.
    launcher, env = _launcher(tmp_path)
    result = _run(
        launcher,
        env,
        LU_DRIVER_MEMORY_HIGH="3221225472",
        LU_DRIVER_MEMORY_MAX="3758096384",
        LU_DRIVER_MEMORY_SWAP_MAX="0",
    )
    assert result.returncode == 0, result.stderr
    assert "high=3221225472 max=3758096384 swap=0 oom=continue" in result.stderr
    assert "PROVIDER:stdin survives" in result.stdout


def test_deployment_config_file_is_parsed_and_environment_wins(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    config = Path(env["LU_DRIVER_SCOPE_CONFIG"])
    config.write_text(
        "# deployment limits\n"
        "LU_DRIVER_MEMORY_HIGH=2684354560\n"
        "LU_DRIVER_MEMORY_MAX=3758096384\n"
        "LU_DRIVER_MEMORY_SWAP_MAX=268435456\n"
        "LU_DRIVER_PYTEST_MAX_WORKERS=6\n"
        "LU_DRIVER_MEMORY_SWAP_MAX=$(touch pwned)\n"
        "UNRELATED=1\n"
    )
    result = _run(
        launcher,
        env,
        LU_DRIVER_MEMORY_HIGH="3221225472",
        FAKE_MEMORY_MAX="3758096384",
        FAKE_MEMORY_SWAP_MAX="268435456",
    )
    assert result.returncode == 0, result.stderr
    assert "high=3221225472 max=3758096384 swap=268435456 oom=continue" in result.stderr
    assert "XDIST_AUTO:6" in result.stdout
    assert not (launcher.parent / "pwned").exists()


def test_inherited_identity_is_not_reentry(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, LU_DRIVER_SCOPE_PID="1", LU_DRIVER_SCOPE_UNIT="lu-driver-parent.scope")
    assert result.returncode == 0, result.stderr
    assert Path(env["FAKE_STARTS"]).read_text().splitlines() == ["start"]


def _direct_entry(
    tmp_path: Path, identity: str, cgroup: str | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    """Call scope entry from a tracked driver entry point after forging identity."""
    root = tmp_path / "repo"
    env = scope_sandbox(root, tmp_path)
    if cgroup is not None:
        Path(env["FAKE_CGROUP"]).write_text(cgroup)
    entry = root / "start-claude-driver.sh"
    entry.write_text(
        f"set -u\nsource {shlex.quote(str(root / 'scripts/lib/driver_scope.sh'))}\n"
        f"LC_ROOT={shlex.quote(str(root))}; LC_PROVIDER=claude; LC_MODE=driver; LC_EPIC=devops\n"
        f"{identity}\nlauncher_enter_driver_scope\n"
    )
    result = subprocess.run(
        ["bash", str(entry)],
        env={**_inherited_environ(), **env},
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result, env


def test_same_pid_forged_identity_refused(tmp_path: Path) -> None:
    result, env = _direct_entry(
        tmp_path, "export LU_DRIVER_SCOPE_PID=$$ LU_DRIVER_SCOPE_UNIT=lu-driver-claude-devops-fake.scope"
    )
    assert result.returncode == 6
    assert "cgroup-mismatch" in result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()


def test_same_pid_without_unit_refused(tmp_path: Path) -> None:
    result, env = _direct_entry(
        tmp_path,
        "export LU_DRIVER_SCOPE_PID=$$; unset LU_DRIVER_SCOPE_UNIT",
        "0::/test/lu.slice/lu-driver.slice/lu-driver-fake.scope\n",
    )
    assert result.returncode == 6, result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=unit-mismatch" in result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()


# The approved safe live-soak envelope (#9624): a throwaway scope far below any
# deployment limit, swap off, on a quiet host, one run at a time, never filling
# the live pool. Opt-in only; CI never runs it.
SOAK_OPT_IN = "LU_RUN_DRIVER_SCOPE_SOAK"
SOAK_HIGH = 128 * 1024 * 1024
SOAK_MAX = 192 * 1024 * 1024
SOAK_LOAD_CEILING = 18.0
SOAK_SERVICES = (
    "learn-ukrainian-api.service",
    "learn-ukrainian-sources.service",
    "learn-ukrainian-astro.service",
    "learn-ukrainian-work.service",
)


def require_soak_opt_in() -> None:
    if os.environ.get(SOAK_OPT_IN) != "1":
        pytest.skip(f"bounded live soak requires {SOAK_OPT_IN}=1")


def soak_environment() -> dict[str, str]:
    """The caller's environment against the real manager, with the soak limits."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
    env.update(LU_DRIVER_MEMORY_HIGH=str(SOAK_HIGH), LU_DRIVER_MEMORY_MAX=str(SOAK_MAX), LU_DRIVER_MEMORY_SWAP_MAX="0")
    return env


def soak_hog(tmp_path: Path) -> tuple[Path, Path]:
    """An allocator that reads its scope's limits back before allocating anything."""
    hog = tmp_path / "hog.py"
    proof = tmp_path / "hog-proof.json"
    expected = {"memory.high": str(SOAK_HIGH), "memory.max": str(SOAK_MAX), "memory.swap.max": "0"}
    hog.write_text(f"""import json
from pathlib import Path
cg = Path('/sys/fs/cgroup' + Path('/proc/self/cgroup').read_text().strip().split('::')[-1])
limits = {{name: (cg / name).read_text().strip() for name in {sorted(expected)!r}}}
assert limits == {expected!r}, limits
Path('/proc/self/oom_score_adj').write_text('1000')
Path({str(proof)!r}).write_text(json.dumps({{'unit': cg.name, 'limits': limits}}))
blocks = []
while True:
    blocks.append(bytearray(16 * 1024 * 1024))
""")
    return hog, proof


def _service_snapshot(env: dict[str, str]) -> dict[str, dict[str, str]]:
    rows = {}
    for service in SOAK_SERVICES:
        properties = ("MainPID", "MemoryCurrent", "ControlGroup", "InvocationID", "NRestarts")
        result = subprocess.run(
            ["systemctl", "--user", "show", service, *(arg for name in properties for arg in ("-p", name))],
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        props = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        assert int(props["MainPID"]) > 0
        assert "/app.slice/" in props["ControlGroup"]
        root = Path("/sys/fs/cgroup" + props.pop("ControlGroup"))
        events = dict(line.split() for line in (root / "memory.events").read_text().splitlines())
        props["oom_kill"] = events["oom_kill"]
        rows[service] = props
    return rows


def _global_oom_kills() -> int:
    return int(dict(line.split() for line in Path("/proc/vmstat").read_text().splitlines())["oom_kill"])


def _require_pool_headroom(env: dict[str, str]) -> None:
    """Refuse unless the shared pool keeps twice the scope's maximum free."""
    shown = subprocess.run(
        ["systemctl", "--user", "show", "lu.slice", "-p", "ControlGroup", "--value"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    if not shown:
        return
    pool = Path("/sys/fs/cgroup" + shown)
    current = int((pool / "memory.current").read_text())
    for name in ("memory.high", "memory.max"):
        limit = (pool / name).read_text().strip()
        if limit != "max":
            if int(limit) - current < 2 * SOAK_MAX:
                pytest.fail(f"lu.slice {name} leaves {int(limit) - current} bytes; the soak needs {2 * SOAK_MAX}")
            return


def run_live_soak(
    argv: list[str], cwd: Path, env: dict[str, str], proof: Path
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    """Run one launcher under the real manager in the safe envelope and prove containment."""
    import fcntl
    import json
    import uuid

    from tests.wait_helpers import wait_until

    load = os.getloadavg()[0]
    if load > SOAK_LOAD_CEILING:
        pytest.fail(f"one-minute load {load:.1f} is above {SOAK_LOAD_CEILING}; soak refused")
    with open(Path(env["XDG_RUNTIME_DIR"]) / "lu-scope-soak.lock", "w") as lock:

        def acquired() -> bool:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            return True

        wait_until(acquired, timeout=600, interval=1, message="the soak lock (one run at a time)")
        _require_pool_headroom(env)
        # A temporary keeper activates the otherwise uninstalled empty test slice.
        # No user-unit installation or persistent configuration is performed.
        keeper_unit = f"lu-driver-soak-keeper-{uuid.uuid4().hex}.scope"
        keeper = subprocess.Popen(
            [
                "systemd-run",
                "--user",
                "--scope",
                "--collect",
                "--quiet",
                "--slice=lu-driver.slice",
                f"--unit={keeper_unit}",
                "--property=MemoryMax=33554432",
                "--property=MemorySwapMax=0",
                "--",
                "sleep",
                "60",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:

            def keeper_active() -> bool:
                if keeper.poll() is not None:
                    raise AssertionError("cannot activate bounded test slice: " + keeper.stderr.read().decode())
                state = subprocess.run(
                    ["systemctl", "--user", "show", keeper_unit, "-p", "ActiveState", "--value"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return state.stdout.strip() == "active"

            wait_until(keeper_active, timeout=10, interval=0.05, message="test slice activation")
            before = _service_snapshot(env)
            global_before = _global_oom_kills()
            result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
            after = _service_snapshot(env)
            global_after = _global_oom_kills()
            receipt = json.loads(proof.read_text())
            # Scope collection removes its files; the manager journal supplies the
            # completed scope's OOM event, tied to the exact unit recorded by hog.
            journal = subprocess.run(
                ["journalctl", "--user", "--no-pager", "-o", "cat", "-u", receipt["unit"]],
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
        finally:
            if proof.exists():
                unit = json.loads(proof.read_text())["unit"]
                subprocess.run(
                    ["systemctl", "--user", "stop", unit], env=env, capture_output=True, timeout=10, check=False
                )
            keeper.terminate()
            keeper.communicate(timeout=10)
    assert receipt["limits"] == {"memory.high": str(SOAK_HIGH), "memory.max": str(SOAK_MAX), "memory.swap.max": "0"}
    assert "OOM" in journal.stdout or "oom" in journal.stdout, journal.stdout
    assert global_after - global_before == 1
    for service in SOAK_SERVICES:
        for key in ("MainPID", "InvocationID", "NRestarts", "oom_kill"):
            assert before[service][key] == after[service][key], (service, key, before, after)
    print(
        "SOAK_RECEIPT "
        + json.dumps(
            {
                "hog_returncode": result.returncode,
                "global_oom_kill_delta": global_after - global_before,
                "before": before,
                "after": after,
                "unit": receipt["unit"],
                "journal": journal.stdout.strip(),
            }
        )
    )
    return result, receipt


def test_bounded_live_scope_soak(tmp_path: Path) -> None:
    """Explicit opt-in: real driver launcher/provider death, finite cgroup, service proof."""
    from tests.test_launcher_contract import _core_driver_exit_fixture

    require_soak_opt_in()
    hog, proof = soak_hog(tmp_path)
    launcher, attempts, closed, _ = _core_driver_exit_fixture(
        tmp_path,
        provider_body=f"exec {shlex.quote(sys.executable)} {shlex.quote(str(hog))}",
    )
    # Use the production helper and manager, rather than the fake kernel/manager.
    shutil.copy2(REPO / "scripts/lib/driver_scope.sh", launcher.parent / "scripts/lib/driver_scope.sh")
    launcher.write_text(
        "\n".join(
            line for line in launcher.read_text().splitlines() if not line.startswith(("export FAKE_", "export PATH="))
        )
        + "\n"
    )
    result, receipt = run_live_soak(
        ["bash", str(launcher), "--epic", "devops"], launcher.parent, soak_environment(), proof
    )
    assert result.returncode == 137, result.stdout + result.stderr
    assert closed.exists() and attempts.read_text().strip() == "1"
    assert str(receipt["unit"]).startswith("lu-driver-claude-devops-")


@pytest.mark.parametrize(
    ("cap", "inherited", "expected"),
    [
        (None, None, "2"),
        (None, "3", "2"),
        (None, "1", "1"),
        ("5", None, "5"),
        ("5", "64", "5"),
        ("5", "abc", "5"),
        ("5", "4", "4"),
        ("5", "0", "0"),
    ],
)
def test_driver_scope_caps_pytest_auto_workers(
    tmp_path: Path, cap: str | None, inherited: str | None, expected: str
) -> None:
    launcher, env = _launcher(tmp_path)
    extra = {} if inherited is None else {"PYTEST_XDIST_AUTO_NUM_WORKERS": inherited}
    if cap is not None:
        extra["LU_DRIVER_PYTEST_MAX_WORKERS"] = cap
    result = _run(launcher, env, **extra)
    assert result.returncode == 0, result.stderr
    assert f"XDIST_AUTO:{expected}" in result.stdout


@pytest.mark.parametrize(
    ("unit", "parent"), [("lu.slice", None), ("lu-dispatch.slice", "lu.slice"), ("lu-driver.slice", "lu.slice")]
)
def test_slice_units_are_structure_only(unit: str, parent: str | None) -> None:
    """Slices carry accounting only; memory and swap limits come from a deployment drop-in."""
    body = (REPO / "packaging/systemd" / unit).read_text()
    assert "[Unit]" in body and "[Slice]" in body
    section = body.split("[Slice]", 1)[1]
    keys = dict(line.split("=", 1) for line in section.splitlines() if "=" in line and not line.startswith("#"))
    assert keys == {"MemoryAccounting": "yes"}
    assert not any(key.startswith(("Memory", "CPU", "Tasks")) and key != "MemoryAccounting" for key in keys)
    if unit != "lu-driver.slice":
        assert f"{unit}.d/10-limits.conf" in body
    # systemd.slice(5): the name encodes the parent, so no Slice= line is needed.
    assert "Slice=" not in section
    if parent is not None:
        assert unit.startswith(parent.removesuffix(".slice") + "-")
