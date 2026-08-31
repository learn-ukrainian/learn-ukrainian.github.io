"""Integration and hermetic tests for services.sh operations and safety guards using a dynamic port."""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts.common.repo_root import main_checkout_root

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICES_SH = PROJECT_ROOT / "services.sh"
PIDS_DIR = PROJECT_ROOT / ".pids"
LOGS_DIR = PROJECT_ROOT / "logs"
# Service commands use the repository virtual environment in normal CI.  The
# explicit override lets a dispatch worktree use the shared project interpreter
# without creating a worktree-local virtual environment. Default to the primary
# checkout interpreter so sparse worktrees without a local .venv still run.
VENV_PYTHON = Path(
    os.environ.get(
        "SERVICES_TEST_PYTHON",
        main_checkout_root(PROJECT_ROOT) / ".venv" / "bin" / "python",
    )
)
def find_free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def is_port_free(port: int) -> bool:
    """Check if a port is free on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def reap_process_on_exit(process: subprocess.Popen[object]) -> None:
    """Prevent a killed dummy listener staying a zombie during shell waits."""
    threading.Thread(target=process.wait, daemon=True).start()

@pytest.fixture
def temp_services_sh_real():
    """Create a copy of services.sh configured with a dynamic free port and the real API command."""
    port = find_free_port()
    temp_script = PROJECT_ROOT / f"services_test_real_{port}.sh"

    # Read and patch services.sh content
    content = SERVICES_SH.read_text(encoding="utf-8")
    content = content.replace("8765", str(port))

    temp_script.write_text(content, encoding="utf-8")
    temp_script.chmod(0o755)

    yield temp_script, port

    # Cleanup temp script
    if temp_script.exists():
        temp_script.unlink()

@pytest.fixture
def temp_services_sh():
    """Create a copy of services.sh configured with a dynamic free port and a hermetic sleep API command."""
    port = find_free_port()
    temp_script = PROJECT_ROOT / f"services_test_{port}.sh"

    # Read and patch services.sh content
    content = SERVICES_SH.read_text(encoding="utf-8")
    content = content.replace("8765", str(port))
    # This fixture exercises PID and log handling with a dummy command, not
    # the release builder. Keep that scope hermetic and fast.
    content = content.replace("API_LIVE_MODE=0", "API_LIVE_MODE=1")

    # Replace the real uvicorn start command with a python sleep command to avoid binding to real ports
    old_cmd = f'SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 127.0.0.1 --port {port} --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"'
    dummy_cmd = f'SVC_CMD[api]="{VENV_PYTHON} -c \\"import time; time.sleep(30)\\" scripts.api.main:app --host 127.0.0.1 --port {port}"'

    if old_cmd in content:
        content = content.replace(old_cmd, dummy_cmd)
    else:
        # Fallback to regex substitution
        import re
        content = re.sub(
            r'SVC_CMD\[api\]="\$VENV/python -m uvicorn scripts\.api\.main:app --host 127\.0\.0\.1 --port \d+ --log-config scripts/api/logging\.json --timeout-graceful-shutdown \d+"',
            dummy_cmd,
            content
        )

    temp_script.write_text(content, encoding="utf-8")
    temp_script.chmod(0o755)

    yield temp_script, port

    # Cleanup temp script
    if temp_script.exists():
        temp_script.unlink()

@pytest.fixture
def mock_lsof_env(tmp_path):
    """Create mock lsof and launchd-supervisor commands for shell lifecycle tests."""
    shim_dir = tmp_path / "mock_bin"
    shim_dir.mkdir()
    lsof_script = shim_dir / "mock_lsof"
    mock_file = tmp_path / "lsof_mock_pids.txt"

    # Write the script. It filters PIDs to ensure they are still running.
    lsof_script.write_text(
        f"#!/bin/sh\n"
        f"if [ -f '{mock_file}' ]; then\n"
        f"  while read -r pid; do\n"
        f"    if [ -n \"$pid\" ] && kill -0 \"$pid\" 2>/dev/null; then\n"
        f"      echo \"$pid\"\n"
        f"    fi\n"
        f"  done < '{mock_file}'\n"
        f"fi\n",
        encoding="utf-8"
    )
    lsof_script.chmod(0o755)

    supervisor_capture = tmp_path / "supervisor_calls.txt"
    supervisor_script = shim_dir / "mock_api_supervisor"
    supervisor_script.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$@\" >> '{supervisor_capture}'\n",
        encoding="utf-8",
    )
    supervisor_script.chmod(0o755)

    def _set_pids(pids: list[int]):
        mock_file.write_text("\n".join(str(p) for p in pids) + "\n", encoding="utf-8")

    def _clear_pids():
        if mock_file.exists():
            mock_file.unlink()

    env = os.environ.copy()
    env.pop("LU_SERVICES_SSH_HOST", None)
    if os.environ.get("MOCK_LSOF_EMPTY") == "1":
        env["SVC_LSOF_BIN"] = "/nonexistent/lsof"
    else:
        env["SVC_LSOF_BIN"] = str(lsof_script.resolve())
    env["SVC_API_SUPERVISOR_BIN"] = str(supervisor_script.resolve())
    env["SVC_API_SUPERVISOR_CAPTURE"] = str(supervisor_capture)

    return _set_pids, _clear_pids, env

@pytest.fixture(autouse=True)
def cleanup_pids_and_logs():
    """Ensure a clean state for pid files and last start timestamps."""
    PIDS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    api_pid_file = PIDS_DIR / "api.pid"
    api_start_file = PIDS_DIR / "api.last_start"

    # Save original values if they exist
    orig_pid = api_pid_file.read_text(encoding="utf-8") if api_pid_file.exists() else None
    orig_start = api_start_file.read_text(encoding="utf-8") if api_start_file.exists() else None

    if api_pid_file.exists():
        api_pid_file.unlink()
    if api_start_file.exists():
        api_start_file.unlink()

    yield

    # Restore original values
    if orig_pid is not None:
        api_pid_file.write_text(orig_pid, encoding="utf-8")
    elif api_pid_file.exists():
        api_pid_file.unlink()

    if orig_start is not None:
        api_start_file.write_text(orig_start, encoding="utf-8")
    elif api_start_file.exists():
        api_start_file.unlink()

def _patch_script_pids_dir(script_path: Path, pids_dir: Path) -> None:
    """Point a patched services.sh copy at an isolated pid directory."""
    content = script_path.read_text(encoding="utf-8")
    content = content.replace(
        'PIDS_DIR="$PROJECT_ROOT/.pids"',
        f'PIDS_DIR="{pids_dir}"',
    )
    script_path.write_text(content, encoding="utf-8")


def test_pid_reconciliation(temp_services_sh, mock_lsof_env, tmp_path):
    """Test stale pid file / listener interactions hermetically."""
    script_path, port = temp_services_sh
    pids_dir = tmp_path / "pids"
    pids_dir.mkdir()
    _patch_script_pids_dir(script_path, pids_dir)
    set_pids, clear_pids, env = mock_lsof_env
    api_pid_file = pids_dir / "api.pid"

    # Start a dummy sleep process to act as the listener process.
    proc = subprocess.Popen([
        str(VENV_PYTHON), "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "127.0.0.1", "--port", str(port)
    ])
    reap_process_on_exit(proc)
    try:
        # Scenario A: pid-file vs listener mismatch -> 'pid file mismatch' warning + rewrite
        # Write a stale PID to the pid file
        api_pid_file.write_text("999999\n", encoding="utf-8")

        # Configure lsof shim to report our dummy process pid
        set_pids([proc.pid])

        # Run status api
        res = subprocess.run(
            [str(script_path), "status", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env, timeout=30
        )

        assert "WARNING: pid file mismatch" in res.stderr or "WARNING: pid file mismatch" in res.stdout, f"mismatch check failed. returncode={res.returncode}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
        assert api_pid_file.exists()
        reconciled_pid = api_pid_file.read_text(encoding="utf-8").strip()
        assert reconciled_pid == str(proc.pid)

        # Stop service with stop cmd
        res_stop = subprocess.run(
            [str(script_path), "stop", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env, timeout=30
        )
        assert res_stop.returncode == 0, f"stop failed. returncode={res_stop.returncode}\nstdout:\n{res_stop.stdout}\nstderr:\n{res_stop.stderr}"
        proc.wait(timeout=5)
        assert proc.returncode is not None

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    # Scenario B: stale pid file + NO listener -> the removal path CI observed
    api_pid_file.write_text("999999\n", encoding="utf-8")
    clear_pids()  # lsof shim returns nothing

    res = subprocess.run(
        [str(script_path), "status", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env, timeout=30
    )
    assert "removing stale pid file" in res.stderr or "removing stale pid file" in res.stdout, f"stale pid check failed. returncode={res.returncode}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert not api_pid_file.exists()

def test_api_start_delegates_recovery_to_launchd(temp_services_sh, mock_lsof_env):
    """API start delegates restart/backoff to launchd instead of a shell timer."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    res = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env, timeout=30
    )

    assert res.returncode == 0, res.stderr
    assert "launchd supervised" in res.stdout
    calls = Path(env["SVC_API_SUPERVISOR_CAPTURE"]).read_text(encoding="utf-8").splitlines()
    assert calls[:3] == ["start", "--repo-root", str(PROJECT_ROOT)]


@pytest.mark.skipif(
    not (PROJECT_ROOT / ".venv" / "bin" / "python").exists(),
    reason="boots the real services.sh, which requires the repo venv ($VENV/python)",
)
def test_live_fallback_is_passed_to_launchd_with_a_loud_warning(temp_services_sh_real, mock_lsof_env):
    """``--live`` remains an explicit, visible escape hatch for API recovery."""
    script_path, _port = temp_services_sh_real
    _, _, env = mock_lsof_env
    result = subprocess.run(
        [str(script_path), "start", "api", "--live", "--force"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "WARNING: API live mode enabled" in result.stderr
    calls = Path(env["SVC_API_SUPERVISOR_CAPTURE"]).read_text(encoding="utf-8").splitlines()
    assert calls == ["start", "--repo-root", str(PROJECT_ROOT), "--live"]

def test_stop_disables_supervision_before_killing_api_listener(temp_services_sh, mock_lsof_env):
    """A deliberate stop asks launchd to disable before touching the listener."""
    script_path, port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    api_pid_file = PIDS_DIR / "api.pid"

    # Start a dummy sleep process
    proc = subprocess.Popen([
        str(VENV_PYTHON), "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "127.0.0.1", "--port", str(port)
    ])
    reap_process_on_exit(proc)

    try:
        # Write the actual listener PID to the pid file to simulate a running state
        api_pid_file.write_text(f"{proc.pid}\n", encoding="utf-8")

        # Configure lsof shim to report our dummy process pid
        set_pids([proc.pid])

        res_stop = subprocess.run(
            [str(script_path), "stop", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env, timeout=30
        )
        assert res_stop.returncode == 0, f"stop failed. returncode={res_stop.returncode}\nstdout:\n{res_stop.stdout}\nstderr:\n{res_stop.stderr}"
        assert Path(env["SVC_API_SUPERVISOR_CAPTURE"]).read_text(encoding="utf-8").splitlines() == ["stop"]

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        # Clean up any started background processes from the start command
        subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT), env=env, timeout=30)

@pytest.mark.skipif(
    shutil.which("lsof") is None or sys.platform != "darwin",
    reason="macOS local-ops integration; logic covered hermetically above"
)
def test_pid_reconciliation_integration(temp_services_sh_real, mock_lsof_env, tmp_path):
    """Integration test using real sockets and real lsof on macOS."""
    script_path, port = temp_services_sh_real
    pids_dir = tmp_path / "pids"
    pids_dir.mkdir()
    _patch_script_pids_dir(script_path, pids_dir)
    api_pid_file = pids_dir / "api.pid"
    set_pids, _, env = mock_lsof_env

    # Start a dummy listener process with the API signature configured for our dynamic port
    dummy_code = (
        f"import socket, time; "
        f"s = socket.socket(); "
        f"s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); "
        f"s.bind(('127.0.0.1', {port})); "
        f"s.listen(1); "
        f"time.sleep(30)"
    )
    proc = subprocess.Popen([
        str(VENV_PYTHON), "-c", dummy_code,
        "scripts.api.main:app", "--host", "127.0.0.1", "--port", str(port)
    ])
    reap_process_on_exit(proc)

    try:
        # Wait a moment for port to bind
        for _ in range(20):
            if not is_port_free(port):
                break
            time.sleep(0.1)

        assert not is_port_free(port), f"Dummy listener did not bind port {port}"

        # Write stale PID to the pid file
        api_pid_file.write_text("999999\n", encoding="utf-8")
        set_pids([proc.pid])

        # Run patched services.sh status
        res = subprocess.run(
            [str(script_path), "status", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env, timeout=30,
        )

        assert "WARNING: pid file mismatch" in res.stderr or "WARNING: pid file mismatch" in res.stdout
        assert api_pid_file.exists()
        reconciled_pid = api_pid_file.read_text(encoding="utf-8").strip()
        assert reconciled_pid == str(proc.pid)

        # Stop the service using patched services.sh
        subprocess.run(
            [str(script_path), "stop", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env, timeout=30,
        )

        # Verify the dummy process was killed
        proc.wait(timeout=5)
        assert proc.returncode is not None
        assert is_port_free(port)

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)


def _extract_bash_function(source: str, name: str) -> str:
    """Return a top-level ``name() { ... }`` block from ``services.sh``."""
    start = source.find(f"{name}() {{")
    if start < 0:
        raise AssertionError(f"function {name}() not found in services.sh")
    depth = 0
    for index in range(start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unclosed function {name}() in services.sh")


def test_cmdline_for_pid_silent_when_procfs_missing() -> None:
    """Missing /proc/$pid/cmdline must not print a bash redirect error."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    helper = _extract_bash_function(source, "_cmdline_for_pid")
    # A pid that cannot exist: no /proc entry and no live process for ps.
    dead_pid = 2_147_483_647
    result = subprocess.run(
        ["bash", "-c", f"{helper}\n_cmdline_for_pid {dead_pid}\n"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "/proc/" not in combined, combined
    assert "No such file or directory" not in combined, combined


def test_astro_match_accepts_bin_astro_dev() -> None:
    """Astro identity must match the live ``node …/.bin/astro dev`` argv."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    match_line = next(
        line for line in source.splitlines() if line.startswith("SVC_MATCH[astro]=")
    )
    assert ".bin/astro dev" in match_line

    helper = "\n".join(
        [
            "declare -A SVC_MATCH",
            match_line,
            _extract_bash_function(source, "_cmdline_for_pid"),
            _extract_bash_function(source, "_pid_matches_service"),
            # Inject the observed live listener argv; skip real /proc and ps.
            '_cmdline_for_pid() { printf "%s\\n" "$FAKE_CMDLINE"; }',
            'FAKE_CMDLINE="node /repo/site/node_modules/.bin/astro dev --host 127.0.0.1 --port 4321 --force"',
            "if _pid_matches_service astro 1; then echo MATCH_BIN; else echo MISS_BIN; fi",
            'FAKE_CMDLINE="node /repo/site/node_modules/astro/astro.mjs dev --host 127.0.0.1 --port 4321"',
            "if _pid_matches_service astro 1; then echo MATCH_MJS; else echo MISS_MJS; fi",
            'FAKE_CMDLINE="node /repo/site/node_modules/.bin/vite --port 4321"',
            "if _pid_matches_service astro 1; then echo MATCH_FOREIGN; else echo MISS_FOREIGN; fi",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", helper],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "MATCH_BIN" in result.stdout
    assert "MATCH_MJS" in result.stdout
    assert "MISS_FOREIGN" in result.stdout


def test_status_does_not_print_proc_on_missing_procfs(temp_services_sh, mock_lsof_env) -> None:
    """``status`` must stay quiet about /proc even when resolving a live PID."""
    script_path, port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    api_pid_file = PIDS_DIR / "api.pid"

    proc = subprocess.Popen([
        str(VENV_PYTHON), "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "127.0.0.1", "--port", str(port)
    ])
    reap_process_on_exit(proc)
    try:
        api_pid_file.write_text(f"{proc.pid}\n", encoding="utf-8")
        set_pids([proc.pid])
        res = subprocess.run(
            [str(script_path), "status", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        combined = f"{res.stdout}\n{res.stderr}"
        assert "/proc/" not in combined, combined
        assert "No such file or directory" not in combined, combined
        # Dummy listener has no health endpoint → Linux CI reports degraded
        # (PID resolved). Either degraded or running is fine; require the PID.
        assert str(proc.pid) in res.stdout, res.stdout
        assert "degraded" in res.stdout or "running" in res.stdout, res.stdout
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)


def test_work_status_reports_typed_missing_checkout(tmp_path, mock_lsof_env) -> None:
    """A missing private sibling is explicit and does not crash public status."""
    _, _, env = mock_lsof_env
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(tmp_path / "missing-private")
    result = subprocess.run(
        [str(SERVICES_SH), "status", "work"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "work" in result.stdout
    assert "unavailable" in result.stdout
    assert "private_checkout_missing" in result.stdout
    assert "sources" not in result.stdout


@pytest.mark.parametrize(
    ("create_venv", "create_module", "reason"),
    [
        (False, False, "private_venv_missing"),
        (True, False, "private_module_missing"),
    ],
)
def test_work_status_reports_other_typed_prerequisite_failures(
    tmp_path, mock_lsof_env, create_venv: bool, create_module: bool, reason: str
) -> None:
    """Every private prerequisite failure has a stable operator-facing type."""
    _, _, env = mock_lsof_env
    private_root = tmp_path / "private"
    (private_root / ".git").mkdir(parents=True)
    if create_venv:
        (private_root / ".venv" / "bin").mkdir(parents=True)
        (private_root / ".venv" / "bin" / "python").symlink_to(VENV_PYTHON)
    if create_module:
        (private_root / "work_projection").mkdir()
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(private_root)

    result = subprocess.run(
        [str(SERVICES_SH), "status", "work"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "unavailable" in result.stdout
    assert reason in result.stdout


def test_work_status_rejects_foreign_health_listener(tmp_path, mock_lsof_env) -> None:
    """A foreign 8769 owner is blocked even if it could answer the health path."""
    set_pids, _, env = mock_lsof_env
    private_root = tmp_path / "private"
    (private_root / ".git").mkdir(parents=True)
    (private_root / ".venv" / "bin").mkdir(parents=True)
    (private_root / "work_projection").mkdir()
    (private_root / ".venv" / "bin" / "python").symlink_to(VENV_PYTHON)
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(private_root)

    proc = subprocess.Popen([str(VENV_PYTHON), "-c", "import time; time.sleep(30)"])
    reap_process_on_exit(proc)
    set_pids([proc.pid])
    try:
        result = subprocess.run(
            [str(SERVICES_SH), "status", "work"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "blocked" in result.stdout
        assert "foreign_listener" in result.stdout
        assert "running" not in result.stdout
        assert "tunneled" not in result.stdout
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_work_status_reports_ssh_tunnel_when_health_ok(tmp_path, mock_lsof_env) -> None:
    """An SSH LocalForward owner is tunneled, not a foreign blocker, when health is 2xx."""
    set_pids, _, env = mock_lsof_env
    private_root = tmp_path / "private"
    (private_root / ".git").mkdir(parents=True)
    (private_root / ".venv" / "bin").mkdir(parents=True)
    (private_root / "work_projection").mkdir()
    (private_root / ".venv" / "bin" / "python").symlink_to(VENV_PYTHON)
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(private_root)

    port = find_free_port()
    script_path = tmp_path / "services.sh"
    script_path.write_text(
        SERVICES_SH.read_text(encoding="utf-8").replace("8769", str(port)),
        encoding="utf-8",
    )
    script_path.chmod(0o755)

    health = subprocess.Popen(
        [
            str(VENV_PYTHON),
            "-c",
            (
                "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
                f"port = {port}\n"
                "class H(BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        body = b'ok'\n"
                "        self.send_response(200)\n"
                "        self.send_header('Content-Type', 'text/plain')\n"
                "        self.send_header('Content-Length', str(len(body)))\n"
                "        self.end_headers()\n"
                "        self.wfile.write(body)\n"
                "    def log_message(self, *args):\n"
                "        return\n"
                "HTTPServer(('127.0.0.1', port), H).serve_forever()\n"
            ),
        ]
    )
    reap_process_on_exit(health)

    ssh_shim = tmp_path / "ssh"
    ssh_shim.write_text("#!/bin/sh\nwhile true; do sleep 30; done\n", encoding="utf-8")
    ssh_shim.chmod(0o755)
    tunnel = subprocess.Popen([str(ssh_shim), "-N", "job-tunnel"])
    reap_process_on_exit(tunnel)
    set_pids([tunnel.pid])
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            if not is_port_free(port):
                break
            time.sleep(0.05)
        result = subprocess.run(
            ["bash", str(script_path), "status", "work"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "tunneled" in result.stdout
        assert "ssh_tunnel" in result.stdout
        assert "blocked" not in result.stdout
        assert "foreign_listener" not in result.stdout
    finally:
        tunnel.terminate()
        health.terminate()
        tunnel.wait(timeout=5)
        health.wait(timeout=5)


def test_work_lifecycle_uses_sibling_checkout_and_fixed_loopback(tmp_path) -> None:
    """Start/status/stop owns the adapter without a manual private-repo command."""
    port = find_free_port()
    script_path = tmp_path / "services.sh"
    script_path.write_text(
        SERVICES_SH.read_text(encoding="utf-8").replace("8769", str(port)),
        encoding="utf-8",
    )
    script_path.chmod(0o755)

    private_root = tmp_path / "private"
    (private_root / ".git").mkdir(parents=True)
    (private_root / ".venv" / "bin").mkdir(parents=True)
    module = private_root / "work_projection"
    module.mkdir()
    (private_root / ".venv" / "bin" / "python").symlink_to(VENV_PYTHON)
    (module / "__init__.py").write_text("", encoding="utf-8")
    (module / "__main__.py").write_text(
        """from http.server import BaseHTTPRequestHandler, HTTPServer
import os

with open(os.environ["WORK_FAKE_PID_FILE"], "w", encoding="utf-8") as pid_file:
    pid_file.write(str(os.getpid()))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/v1/health":
            self.send_response(404)
            self.end_headers()
            return
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_args):
        return

HTTPServer(("127.0.0.1", int(os.environ["WORK_TEST_PORT"])), Handler).serve_forever()
""",
        encoding="utf-8",
    )

    env = os.environ.copy()
    fake_pid_file = tmp_path / "work.pid"
    mock_lsof = tmp_path / "mock_lsof"
    mock_lsof.write_text(
        "#!/bin/sh\n"
        f"if [ -f '{fake_pid_file}' ]; then\n"
        f"  pid=$(cat '{fake_pid_file}')\n"
        "  if kill -0 \"$pid\" 2>/dev/null; then echo \"$pid\"; fi\n"
        "fi\n",
        encoding="utf-8",
    )
    mock_lsof.chmod(0o755)
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(private_root)
    env["WORK_TEST_PORT"] = str(port)
    env["WORK_FAKE_PID_FILE"] = str(fake_pid_file)
    env["SVC_LSOF_BIN"] = str(mock_lsof)
    start = subprocess.run(
        [str(script_path), "start", "work"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
        timeout=30,
    )
    try:
        assert start.returncode == 0, f"{start.stdout}\n{start.stderr}"
        status = None
        for _ in range(40):
            status = subprocess.run(
                [str(script_path), "status", "work"],
                capture_output=True,
                text=True,
                cwd=str(tmp_path),
                env=env,
                timeout=30,
            )
            if "running" in status.stdout:
                break
            time.sleep(0.1)
        assert status is not None
        assert status.returncode == 0, status.stderr
        assert "running" in status.stdout
        assert f"127.0.0.1:{port}" in status.stdout
        assert str(private_root / "logs" / "work-projection.log") in start.stdout
    finally:
        stop = subprocess.run(
            [str(script_path), "stop", "work"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
            timeout=30,
        )
        assert stop.returncode == 0, f"{stop.stdout}\n{stop.stderr}"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        assert probe.connect_ex(("127.0.0.1", port)) != 0


def test_local_service_ports_do_not_collide_with_bridge_or_kubedojo() -> None:
    """Frozen Learn Ukrainian ports avoid the bridge and KubeDojo declarations."""
    assignment = re.compile(r"^SVC_PORT\[([^]]+)\]=\"?(\d+)\"?$", re.MULTILINE)
    learn_ports = {
        name: int(port)
        for name, port in assignment.findall(SERVICES_SH.read_text(encoding="utf-8"))
    }
    assert learn_ports == {"sources": 8766, "api": 8765, "work": 8769, "astro": 4321}

    bridge_source = (PROJECT_ROOT / "scripts" / "ai_agent_bridge" / "_cli.py").read_text(
        encoding="utf-8"
    )
    bridge_port_match = re.search(
        r'add_argument\(\s*"--port",\s*type=int,\s*default=(\d+),', bridge_source
    )
    assert bridge_port_match is not None
    openai_compat_proxy_port = int(bridge_port_match.group(1))
    assert openai_compat_proxy_port == 8767
    assert learn_ports["work"] != openai_compat_proxy_port

    # CI has no sibling checkout, so the reviewed KubeDojo contract is frozen
    # here and cross-checked against its real services.sh whenever available.
    kubedojo_ports = {"api": 8768, "dev": 4333}
    kubedojo_script = main_checkout_root(PROJECT_ROOT).parent / "kubedojo" / "services.sh"
    if kubedojo_script.exists():
        declared = {
            name: int(port)
            for name, port in assignment.findall(kubedojo_script.read_text(encoding="utf-8"))
        }
        assert {name: declared[name] for name in kubedojo_ports} == kubedojo_ports

    assert set(learn_ports.values()).isdisjoint(kubedojo_ports.values())


def _supervisor_was_not_called(env: dict[str, str]) -> bool:
    """Local API start writes this file; missing/empty means no local spawn."""
    path = Path(env["SVC_API_SUPERVISOR_CAPTURE"])
    if not path.exists():
        return True
    return path.read_text(encoding="utf-8") == ""


def _ssh_recorder(tmp_path: Path, exit_code: int = 0) -> tuple[Path, Path]:
    """Return (shim_dir, capture_file) for a PATH-first ``ssh`` recorder."""
    capture = tmp_path / "ssh_args.txt"
    shim_dir = tmp_path / "ssh_bin"
    shim_dir.mkdir()
    ssh = shim_dir / "ssh"
    ssh.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$@\" >> '{capture}'\nexit {exit_code}\n",
        encoding="utf-8",
    )
    ssh.chmod(0o755)
    return shim_dir, capture


def _start_named_ssh_process(tmp_path: Path) -> subprocess.Popen[object]:
    """Spawn a process whose argv looks like ``…/ssh -N …`` for tunnel detection."""
    tunnel_dir = tmp_path / "tunnel_proc"
    tunnel_dir.mkdir()
    tunnel_ssh = tunnel_dir / "ssh"
    tunnel_ssh.write_text("#!/bin/sh\nwhile true; do sleep 30; done\n", encoding="utf-8")
    tunnel_ssh.chmod(0o755)
    proc = subprocess.Popen([str(tunnel_ssh), "-N", "writer-tunnel"])
    reap_process_on_exit(proc)
    return proc


def test_is_ssh_tunnel_pid_detects_ssh_and_rejects_non_ssh(tmp_path) -> None:
    """``_is_ssh_tunnel_pid`` matches ssh comm/argv and rejects other owners."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    tunnel = _start_named_ssh_process(tmp_path)
    non_ssh = subprocess.Popen([str(VENV_PYTHON), "-c", "import time; time.sleep(30)"])
    reap_process_on_exit(non_ssh)
    helper = "\n".join(
        [
            _extract_bash_function(source, "_cmdline_for_pid"),
            _extract_bash_function(source, "_is_ssh_tunnel_pid"),
            f"if _is_ssh_tunnel_pid {tunnel.pid}; then echo SSH_TUNNEL; else echo NOT_SSH; fi",
            f"if _is_ssh_tunnel_pid {non_ssh.pid}; then echo NON_SSH_MATCH; else echo NON_SSH_OK; fi",
        ]
    )
    try:
        result = subprocess.run(
            ["bash", "-c", helper],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "SSH_TUNNEL" in result.stdout
        assert "NON_SSH_OK" in result.stdout
        assert "NON_SSH_MATCH" not in result.stdout
    finally:
        tunnel.terminate()
        non_ssh.terminate()
        tunnel.wait(timeout=5)
        non_ssh.wait(timeout=5)


def test_delegate_rejects_injection_payload(
    temp_services_sh, mock_lsof_env, tmp_path
) -> None:
    """Shell metacharacters in service args must never reach the ssh delegate."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    shim_dir, capture = _ssh_recorder(tmp_path)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env["LU_SERVICES_SSH_HOST"] = "fakehost"

    payload = "api;touch /tmp/ssh_inject_test/PWNED"
    result = subprocess.run(
        [str(script_path), "start", payload],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Unknown service" in combined, combined
    assert result.returncode != 0
    assert not capture.exists() or capture.read_text(encoding="utf-8") == ""


def test_should_delegate_remote_env_or_tunnel() -> None:
    """Delegation triggers on LU_SERVICES_SSH_HOST or an ssh-owned port, not the default alias."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    helper = "\n".join(
        [
            "declare -A SVC_CMD",
            "SVC_CMD[api]=dummy",
            _extract_bash_function(source, "_requested_has_ssh_tunnel"),
            _extract_bash_function(source, "_should_delegate_remote"),
            "_ssh_tunnel_port_pid() { return 1; }",
            "unset LU_SERVICES_SSH_HOST",
            "if _should_delegate_remote api; then echo TRIGGER; else echo LOCAL; fi",
            "LU_SERVICES_SSH_HOST=writer-host",
            "if _should_delegate_remote api; then echo ENV; else echo NOENV; fi",
            "unset LU_SERVICES_SSH_HOST",
            "_ssh_tunnel_port_pid() { return 0; }",
            "if _should_delegate_remote api; then echo TUNNEL; else echo NOTUNNEL; fi",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", helper],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["LOCAL", "ENV", "TUNNEL"]


def test_abort_if_ssh_owned_port_refuses_spawn() -> None:
    """Local spawn must refuse an ssh LocalForward owner with a fix/restart hint."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    helper = "\n".join(
        [
            _extract_bash_function(source, "_abort_if_ssh_owned_port"),
            '_port_owner_label() { printf "127.0.0.1:8765"; }',
            "_ssh_tunnel_port_pid() { return 1; }",
            "if _abort_if_ssh_owned_port api; then echo ALLOW; else echo REFUSE; fi",
            "_ssh_tunnel_port_pid() { return 0; }",
            "if _abort_if_ssh_owned_port api; then echo ALLOW2; else echo REFUSE2; fi",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", helper],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "ALLOW" in result.stdout
    assert "REFUSE2" in result.stdout
    assert "owned by an ssh LocalForward" in result.stderr
    assert "fix api" in result.stderr
    assert "restart api" in result.stderr


def test_usage_documents_fix_and_ssh_env() -> None:
    """Header comments and help list fix plus the SSH Host / remote-root overrides."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    assert "./services.sh fix" in source
    assert "./services.sh fix api" in source
    assert "LU_SERVICES_SSH_HOST" in source
    assert "LU_SERVICES_REMOTE_ROOT" in source
    assert "auto-delegate" in source

    env = os.environ.copy()
    env.pop("LU_SERVICES_SSH_HOST", None)
    result = subprocess.run(
        ["bash", str(SERVICES_SH), "help"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "fix" in result.stdout
    assert "LU_SERVICES_SSH_HOST" in result.stdout
    assert "LU_SERVICES_REMOTE_ROOT" in result.stdout
    assert "auto-delegate" in result.stdout


def test_start_delegates_when_ssh_host_set(temp_services_sh, mock_lsof_env, tmp_path) -> None:
    """An explicit LU_SERVICES_SSH_HOST must ssh to remote services.sh and not spawn locally."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    shim_dir, capture = _ssh_recorder(tmp_path)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env["LU_SERVICES_SSH_HOST"] = "writer-host"
    env["LU_SERVICES_REMOTE_ROOT"] = "/srv/writer/learn-ukrainian"

    result = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    args = capture.read_text(encoding="utf-8")
    assert "BatchMode=yes" in args
    assert "writer-host" in args
    assert "/srv/writer/learn-ukrainian" in args
    assert "./services.sh start api" in args
    assert "Delegating start api" in result.stdout
    assert _supervisor_was_not_called(env)


def test_start_delegates_when_ssh_owns_port(temp_services_sh, mock_lsof_env, tmp_path) -> None:
    """An ssh LocalForward listener plus explicit host overrides delegates start."""
    script_path, _port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    shim_dir, capture = _ssh_recorder(tmp_path)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env.pop("LU_SERVICES_SSH_HOST", None)
    env["LU_SERVICES_SSH_HOST"] = "writer-host"
    env["LU_SERVICES_REMOTE_ROOT"] = "/srv/writer/learn-ukrainian"

    tunnel = _start_named_ssh_process(tmp_path)
    set_pids([tunnel.pid])
    try:
        result = subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        args = capture.read_text(encoding="utf-8")
        assert "BatchMode=yes" in args
        assert "writer-host" in args
        assert "./services.sh start api" in args
        assert _supervisor_was_not_called(env)
    finally:
        tunnel.terminate()
        tunnel.wait(timeout=5)


def test_start_tunnel_without_host_fails_closed(temp_services_sh, mock_lsof_env, tmp_path) -> None:
    """A detected tunnel without LU_SERVICES_SSH_HOST refuses instead of guessing an alias."""
    script_path, _port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    shim_dir, capture = _ssh_recorder(tmp_path)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env.pop("LU_SERVICES_SSH_HOST", None)
    env.pop("LU_SERVICES_REMOTE_ROOT", None)

    tunnel = _start_named_ssh_process(tmp_path)
    set_pids([tunnel.pid])
    try:
        result = subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        assert result.returncode != 0, f"{result.stdout}\n{result.stderr}"
        combined = f"{result.stdout}\n{result.stderr}"
        assert "LU_SERVICES_SSH_HOST" in combined, combined
        assert "no public defaults" in combined, combined
        assert not capture.exists() or capture.read_text(encoding="utf-8") == ""
        assert _supervisor_was_not_called(env)
    finally:
        tunnel.terminate()
        tunnel.wait(timeout=5)


def test_no_public_ssh_host_or_remote_root_defaults() -> None:
    """The public script must not bake any SSH Host alias or remote-root path."""
    source = SERVICES_SH.read_text(encoding="utf-8")
    assert "LU_SERVICES_SSH_HOST" in source
    assert "LU_SERVICES_REMOTE_ROOT" in source
    assert "hramatka" not in source
    assert "/home/ops" not in source


def test_failed_remote_delegate_does_not_spawn_local(
    temp_services_sh, mock_lsof_env, tmp_path
) -> None:
    """A failed ssh delegate must not fall through to local uvicorn/launchd."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    shim_dir, _capture = _ssh_recorder(tmp_path, exit_code=1)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env["LU_SERVICES_SSH_HOST"] = "writer-host"
    env["LU_SERVICES_REMOTE_ROOT"] = "/srv/writer/learn-ukrainian"

    result = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode != 0
    assert _supervisor_was_not_called(env)


def test_fix_prints_ok_when_healthy(temp_services_sh, mock_lsof_env) -> None:
    """Healthy services print ok and do not restart."""
    script_path, port = temp_services_sh
    _, _, env = mock_lsof_env
    env.pop("LU_SERVICES_SSH_HOST", None)

    health = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
                f"port = {port}\n"
                "class H(BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        body = b'ok'\n"
                "        self.send_response(200)\n"
                "        self.send_header('Content-Type', 'text/plain')\n"
                "        self.send_header('Content-Length', str(len(body)))\n"
                "        self.end_headers()\n"
                "        self.wfile.write(body)\n"
                "    def log_message(self, *args):\n"
                "        return\n"
                "HTTPServer(('127.0.0.1', port), H).serve_forever()\n"
            ),
        ]
    )
    reap_process_on_exit(health)
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            if not is_port_free(port):
                break
            time.sleep(0.05)
        result = subprocess.run(
            [str(script_path), "fix", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        assert "api ok" in result.stdout
        assert _supervisor_was_not_called(env)
    finally:
        health.terminate()
        health.wait(timeout=5)


def test_fix_unhealthy_ssh_tunnel_delegates_restart(
    temp_services_sh, mock_lsof_env, tmp_path
) -> None:
    """Unhealthy tunneled ports remote-restart; they must not spawn local listeners."""
    script_path, _port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    shim_dir, capture = _ssh_recorder(tmp_path)
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
    env.pop("LU_SERVICES_SSH_HOST", None)
    env["LU_SERVICES_SSH_HOST"] = "writer-host"
    env["LU_SERVICES_REMOTE_ROOT"] = "/srv/writer/learn-ukrainian"

    tunnel = _start_named_ssh_process(tmp_path)
    set_pids([tunnel.pid])
    try:
        result = subprocess.run(
            [str(script_path), "fix", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=30,
        )
        # Remote restart is recorded; local health stays down without a real writer.
        args = capture.read_text(encoding="utf-8")
        assert "BatchMode=yes" in args
        assert "./services.sh restart api" in args
        assert _supervisor_was_not_called(env)
        assert "not starting or stopping local processes" in result.stdout
    finally:
        tunnel.terminate()
        tunnel.wait(timeout=5)


def _notebook_env(tmp_path: Path, mock_lsof_env, role: str) -> tuple[dict[str, str], Path, Path]:
    """Env for role tests: private sibling root plus a launcher-arg capture file."""
    _, _, env = mock_lsof_env
    private_root = tmp_path / "private"
    (private_root / "ops").mkdir(parents=True)
    env["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] = str(private_root)
    env["LU_SERVICES_ROLE"] = role
    capture = tmp_path / "launcher_args.txt"
    return env, private_root, capture


def _write_fake_launcher(private_root: Path, capture: Path) -> Path:
    launcher = private_root / "ops" / "writer-notebook.sh"
    launcher.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$@\" >> '{capture}'\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher


def test_notebook_role_execs_private_launcher(tmp_path, mock_lsof_env) -> None:
    """Notebook role hands every action to the private launcher, no local spawn."""
    env, private_root, capture = _notebook_env(tmp_path, mock_lsof_env, "notebook")
    _write_fake_launcher(private_root, capture)

    result = subprocess.run(
        [str(SERVICES_SH), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert capture.read_text(encoding="utf-8").splitlines() == ["start", "api"]
    assert _supervisor_was_not_called(env)


def test_notebook_role_fails_closed_without_launcher(tmp_path, mock_lsof_env) -> None:
    """A missing private launcher aborts with a hint instead of spawning locally."""
    env, _private_root, capture = _notebook_env(tmp_path, mock_lsof_env, "notebook")

    result = subprocess.run(
        [str(SERVICES_SH), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode != 0, f"{result.stdout}\n{result.stderr}"
    combined = f"{result.stdout}\n{result.stderr}"
    assert "writer-notebook.sh" in combined, combined
    assert "LU_SERVICES_ROLE=local" in combined, combined
    assert not capture.exists()
    assert _supervisor_was_not_called(env)


def test_notebook_role_rejects_non_executable_launcher(tmp_path, mock_lsof_env) -> None:
    """A present-but-not-executable launcher also fails closed."""
    env, private_root, capture = _notebook_env(tmp_path, mock_lsof_env, "notebook")
    launcher = private_root / "ops" / "writer-notebook.sh"
    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    launcher.chmod(0o644)

    result = subprocess.run(
        [str(SERVICES_SH), "status", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode != 0, f"{result.stdout}\n{result.stderr}"
    assert "LU_SERVICES_ROLE=local" in result.stderr, result.stderr
    assert not capture.exists()


def test_local_role_skips_notebook_handoff(tmp_path, mock_lsof_env) -> None:
    """LU_SERVICES_ROLE=local runs services.sh itself even when a launcher exists."""
    env, private_root, capture = _notebook_env(tmp_path, mock_lsof_env, "local")
    _write_fake_launcher(private_root, capture)

    result = subprocess.run(
        [str(SERVICES_SH), "help"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "Usage:" in result.stdout
    assert not capture.exists()
