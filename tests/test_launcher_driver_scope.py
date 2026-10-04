"""Kernel/manager fakes for scope entry; live containment is opt-in and bounded."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def scope_sandbox(root: Path, tmp_path: Path) -> dict[str, str]:
    """Copy the real helper, replacing only kernel reads with test-owned files."""
    helper = root / "scripts/lib/driver_scope.sh"
    helper.parent.mkdir(parents=True, exist_ok=True)
    body = (REPO / "scripts/lib/driver_scope.sh").read_text()
    body = body.replace('"/proc/$$/cgroup"', '"$FAKE_CGROUP"')
    helper.write_text(body)
    bindir = tmp_path / "scope-bin"
    bindir.mkdir(exist_ok=True)
    exe = bindir / "systemd-run"
    exe.write_text("""#!/usr/bin/env bash
printf 'start\\n' >> "$FAKE_STARTS"
for arg; do case "$arg" in --unit=*) unit="${arg#*=}" ;; esac; done
while [ "$1" != -- ]; do shift; done
shift
[ "${FAKE_SCOPE_FAIL:-0}" = 0 ] || exit 1
printf '0::/test/lu.slice/lu-driver.slice/%s\\n' "$unit" > "$FAKE_CGROUP"
exec "$@"
""")
    exe.chmod(0o755)
    exe = bindir / "systemctl"
    exe.write_text("""#!/usr/bin/env bash
[ "${FAKE_BUS_FAIL:-0}" = 0 ] || exit 1
if [[ "$*" == *lu-driver.slice* ]]; then
  printf 'LoadState=%s\\nFragmentPath=%s\\n' "${FAKE_SLICE_LOAD_STATE:-loaded}" "${FAKE_SLICE_FRAGMENT-/test/lu-driver.slice}"
  exit
fi
printf 'Id=%s\\nControlGroup=/test/lu.slice/lu-driver.slice/%s\\nSlice=lu-driver.slice\\nOOMPolicy=%s\\nActiveState=active\\n' "$LU_DRIVER_SCOPE_UNIT" "$LU_DRIVER_SCOPE_UNIT" "${FAKE_OOM_POLICY:-continue}"
""")
    exe.chmod(0o755)
    exe = bindir / "cat"
    exe.write_text("""#!/usr/bin/env bash
case "$1" in
 */memory.high) printf '%s\\n' "${LU_DRIVER_MEMORY_HIGH:-6442450944}" ;;
 */memory.max) printf '%s\\n' "${LU_DRIVER_MEMORY_MAX:-9663676416}" ;;
 */memory.swap.max) printf '%s\\n' "${LU_DRIVER_MEMORY_SWAP_MAX:-1073741824}" ;;
 */memory.current) printf '123456\\n' ;;
 */memory.swap.current) printf '654321\\n' ;;
 *) exec /bin/cat "$@" ;;
esac
""")
    exe.chmod(0o755)
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("0::/test/outside.scope\n")
    return {
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "FAKE_CGROUP": str(cgroup),
        "FAKE_STARTS": str(tmp_path / "scope-starts"),
    }


def install_scope_sandbox(root: Path) -> None:
    """Give existing lifecycle fixtures a fake manager and kernel boundary."""
    env = scope_sandbox(root, root.parent)
    for launcher in root.glob("start-*-driver.sh"):
        body = launcher.read_text()
        first, rest = body.split("\n", 1)
        exports = "\n".join(
            f'export PATH={shlex.quote(value.split(":", 1)[0])}:"$PATH"'
            if key == "PATH"
            else f"export {key}={shlex.quote(value)}"
            for key, value in env.items()
        )
        launcher.write_text(first + "\n" + exports + "\n" + rest)


def _launcher(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    root = tmp_path / "repo"
    env = scope_sandbox(root, tmp_path)
    core = root / "scripts/lib/launcher_core.sh"
    shutil.copy2(REPO / "scripts/lib/launcher_core.sh", core)
    # Only provider/lease/preparation seams are stubbed. The full main entry,
    # scope setup, identity and limit validation stay real.
    core.write_text(
        core.read_text()
        + """
launcher_defaults() { LC_DRY_RUN=0; LC_GOVERNOR=${TEST_GOVERNOR:-0}; LC_EPIC=devops; }
launcher_clear_foreign_route_state() { :; }
launcher_parse() { :; }
launcher_drop_force_from_successor_args() { :; }
launcher_normalize_effort() { :; }
launcher_resolve_roots() { :; }
launcher_publication_path() { :; }
launcher_normalize_model() { :; }
launcher_validate_mode() { :; }
launcher_validate_driver_certification() { :; }
launcher_load_rules_core() { printf 'PREPARED\\n'; }
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
launcher_adapter_exec() { read -r line; printf 'PROVIDER:%s\\n' "$line"; exit "${TEST_RC:-0}"; }
""")
    launcher = root / "start-claude-driver.sh"
    launcher.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\nsource "$(dirname "$0")/scripts/lib/launcher_core.sh"\nlauncher_main claude driver "$@"\n'
    )
    return launcher, env


def _run(launcher: Path, env: dict[str, str], **extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(launcher)],
        cwd=launcher.parent,
        env={**os.environ, **env, **extra},
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
    assert "PROVIDER:stdin survives" in result.stdout
    assert "high=6442450944 max=9663676416 swap=1073741824 oom=continue" in result.stderr
    assert "DRIVER_SCOPE_VERIFIED" in result.stderr
    assert "parent_memory_current=123456 parent_swap_current=654321" in result.stderr


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


@pytest.mark.parametrize("rc", [1, 2, 3, 4, 5, 137])
def test_provider_status_preserved(tmp_path: Path, rc: int) -> None:
    launcher, env = _launcher(tmp_path)
    assert _run(launcher, env, TEST_RC=str(rc)).returncode == rc


@pytest.mark.parametrize(
    "extra,reason",
    [
        ({"FAKE_BUS_FAIL": "1"}, "user-manager-unavailable"),
        ({"FAKE_SCOPE_FAIL": "1"}, "scope-start-failed"),
        ({"FAKE_OOM_POLICY": "stop"}, "unit-properties-mismatch"),
        ({"LU_DRIVER_MEMORY_MAX": "max"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_HIGH": "5", "LU_DRIVER_MEMORY_MAX": "5"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_HIGH": "6442450945"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_MAX": "9663676417"}, "invalid-limits"),
        ({"LU_DRIVER_MEMORY_SWAP_MAX": "1073741825"}, "invalid-limits"),
    ],
)
def test_refuse_before_preparation(tmp_path: Path, extra: dict[str, str], reason: str) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, **extra)
    assert result.returncode == 6
    assert reason in result.stderr
    assert "PREPARED" not in result.stdout
    assert "LEASE" not in result.stdout


def test_lower_test_limits_are_preserved(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(
        launcher,
        env,
        LU_DRIVER_MEMORY_HIGH="3221225472",
        LU_DRIVER_MEMORY_MAX="5368709120",
        LU_DRIVER_MEMORY_SWAP_MAX="0",
    )
    assert result.returncode == 0, result.stderr
    assert "high=3221225472 max=5368709120 swap=0 oom=continue" in result.stderr
    assert "PROVIDER:stdin survives" in result.stdout


def test_inherited_identity_is_not_reentry(tmp_path: Path) -> None:
    launcher, env = _launcher(tmp_path)
    result = _run(launcher, env, LU_DRIVER_SCOPE_PID="1", LU_DRIVER_SCOPE_UNIT="lu-driver-parent.scope")
    assert result.returncode == 0, result.stderr
    assert Path(env["FAKE_STARTS"]).read_text().splitlines() == ["start"]


def test_same_pid_forged_identity_refused(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    env = scope_sandbox(root, tmp_path)
    helper = root / "scripts/lib/driver_scope.sh"
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {shlex.quote(str(helper))}; LC_MODE=driver; export LU_DRIVER_SCOPE_PID=$$ LU_DRIVER_SCOPE_UNIT=lu-driver-fake.scope; launcher_enter_driver_scope",
        ],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 6
    assert "cgroup-mismatch" in result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()


def test_same_pid_without_unit_refused(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    env = scope_sandbox(root, tmp_path)
    Path(env["FAKE_CGROUP"]).write_text("0::/test/lu.slice/lu-driver.slice/lu-driver-fake.scope\n")
    helper = root / "scripts/lib/driver_scope.sh"
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"set -u; source {shlex.quote(str(helper))}; LC_MODE=driver; "
            "export LU_DRIVER_SCOPE_PID=$$; unset LU_DRIVER_SCOPE_UNIT; launcher_enter_driver_scope",
        ],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 6, result.stderr
    assert "DRIVER_SCOPE_REFUSED reason=unit-mismatch" in result.stderr
    assert not Path(env["FAKE_STARTS"]).exists()


def test_bounded_live_scope_soak(tmp_path: Path) -> None:
    """Explicit opt-in: real launcher/provider death, finite cgroup, service proof."""
    import json
    import sys
    import time
    import uuid

    from tests.test_launcher_contract import _core_driver_exit_fixture

    if os.environ.get("LU_RUN_DRIVER_SCOPE_SOAK") != "1":
        pytest.skip("bounded live soak requires LU_RUN_DRIVER_SCOPE_SOAK=1")
    services = [
        "learn-ukrainian-api.service",
        "learn-ukrainian-sources.service",
        "learn-ukrainian-astro.service",
        "learn-ukrainian-work.service",
    ]
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

    def snapshot():
        rows = {}
        for service in services:
            result = subprocess.run(
                [
                    "systemctl",
                    "--user",
                    "show",
                    service,
                    "-p",
                    "MainPID",
                    "-p",
                    "MemoryCurrent",
                    "-p",
                    "ControlGroup",
                    "-p",
                    "InvocationID",
                    "-p",
                    "NRestarts",
                ],
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

    hog = tmp_path / "hog.py"
    proof = tmp_path / "hog-proof.json"
    hog.write_text(f"""import json, os
from pathlib import Path
cg = Path('/sys/fs/cgroup' + Path('/proc/self/cgroup').read_text().strip().split('::')[-1])
assert (cg / 'memory.max').read_text().strip() == '536870912'
assert (cg / 'memory.swap.max').read_text().strip() == '0'
Path('/proc/self/oom_score_adj').write_text('1000')
Path({str(proof)!r}).write_text(json.dumps({{'unit': cg.name, 'events': (cg / 'memory.events').read_text(), 'max': (cg / 'memory.max').read_text().strip()}}))
blocks = []
while True:
    blocks.append(bytearray(16 * 1024 * 1024))
""")
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
    env.update(LU_DRIVER_MEMORY_HIGH="536866816", LU_DRIVER_MEMORY_MAX="536870912", LU_DRIVER_MEMORY_SWAP_MAX="0")
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
        for _ in range(100):
            if keeper.poll() is not None:
                raise AssertionError("cannot activate bounded test slice: " + keeper.stderr.read().decode())
            state = subprocess.run(
                ["systemctl", "--user", "show", keeper_unit, "-p", "ActiveState", "--value"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if state.stdout.strip() == "active":
                break
            time.sleep(0.05)
        else:
            raise AssertionError("test slice did not activate")
        before = snapshot()
        global_before = int(dict(line.split() for line in Path("/proc/vmstat").read_text().splitlines())["oom_kill"])
        result = subprocess.run(
            ["bash", str(launcher), "--epic", "devops"],
            cwd=launcher.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=45,
        )
        after = snapshot()
        global_after = int(dict(line.split() for line in Path("/proc/vmstat").read_text().splitlines())["oom_kill"])
        assert result.returncode == 137, result.stdout + result.stderr
        assert closed.exists() and attempts.read_text().strip() == "1"
        receipt = json.loads(proof.read_text())
        assert receipt["max"] == "536870912"
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
        assert "OOM" in journal.stdout or "oom" in journal.stdout, journal.stdout
        assert global_after - global_before == 1
        for service in services:
            for key in ("MainPID", "InvocationID", "NRestarts", "oom_kill"):
                assert before[service][key] == after[service][key], (service, key, before, after)
        print(
            "SOAK_RECEIPT "
            + json.dumps(
                {
                    "hog_returncode": result.returncode,
                    "cleanup_attempts": 1,
                    "global_oom_kill_delta": global_after - global_before,
                    "before": before,
                    "after": after,
                    "unit": receipt["unit"],
                    "journal": journal.stdout.strip(),
                }
            )
        )
    finally:
        if proof.exists():
            unit = json.loads(proof.read_text())["unit"]
            subprocess.run(["systemctl", "--user", "stop", unit], env=env, capture_output=True, timeout=10, check=False)
        keeper.terminate()
        keeper.communicate(timeout=10)
