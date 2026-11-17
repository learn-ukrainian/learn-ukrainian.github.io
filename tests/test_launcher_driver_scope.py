"""Fixtures retained for product launcher tests; machinery test cases run in machinery."""
from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

import pytest
from lu_machinery.common.repo_root import machinery_path

from tests.helpers import machinery_package
from tests.launcher_sandbox import launcher_environment
from tests.wait_helpers import wait_until


@pytest.fixture
def default_hup():
    """Bash cannot trap HUP ignored on entry, as with a nohup pytest parent."""
    previous = signal.signal(signal.SIGHUP, signal.SIG_DFL)
    try:
        assert signal.getsignal(signal.SIGHUP) == signal.SIG_DFL
        yield
    finally:
        signal.signal(signal.SIGHUP, previous)


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


def scope_sandbox(
    root: Path, tmp_path: Path, *, machinery: Path | None = None, package: str | None = None
) -> dict[str, str]:
    """Copy the real helper, replacing only kernel reads with test-owned files.

    ``machinery`` is the package directory whose helper is copied (the checkout's by
    default, or an installed release's) and ``package`` the directory name it takes under
    ``root``.
    """
    helper = root / (package or machinery_package()) / "lib/driver_scope.sh"
    helper.parent.mkdir(parents=True, exist_ok=True)
    body = ((machinery or machinery_path("lib/driver_scope.sh").parent.parent) / "lib/driver_scope.sh").read_text()
    assert body.count('"/proc/$$/cgroup"') == 1
    body = body.replace('"/proc/$$/cgroup"', '"$FAKE_CGROUP"')
    # Never write through a link into the source tree.
    helper.unlink(missing_ok=True)
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
if [[ "$*" == *--value* ]]; then
  if [ -n "${FAKE_SCOPE_STATE:-}" ]; then /bin/cat "$FAKE_SCOPE_STATE"; else printf 'inactive\\n'; fi
  exit 0
fi
if [ "${2:-}" = kill ]; then
  [ -n "${FAKE_SCOPE_ORPHAN:-}" ] || exit 0
  IFS= read -r cgroup < "$FAKE_CGROUP"
  [ "${@: -1}" = "${cgroup##*/}" ] || exit 97
  IFS= read -r orphan < "$FAKE_SCOPE_ORPHAN"
  case "$*" in
    *--signal=TERM*) printf 'TERM\\n' >> "$FAKE_SCOPE_SIGNALS"; kill -TERM "$orphan" || exit 97 ;;
    *--signal=KILL*) printf 'KILL\\n' >> "$FAKE_SCOPE_SIGNALS"; kill -KILL "$orphan" || exit 97
      printf 'inactive\\n' > "$FAKE_SCOPE_STATE" ;;
    *) exit 97 ;;
  esac
  exit 0
fi
[ "${2:-}" != stop ] || exit 0
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
        "PATH": f"{bindir}:{guard}:{os.defpath}",
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
    """An isolated environment with explicit access to the real user manager."""
    env = launcher_environment()
    env["PATH"] = os.defpath
    env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={env['XDG_RUNTIME_DIR']}/bus"
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
