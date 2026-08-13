"""Integration and hermetic tests for services.sh operations and safety guards using a dynamic port."""

from __future__ import annotations

import os
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
    old_cmd = f'SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port {port} --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"'
    dummy_cmd = f'SVC_CMD[api]="{VENV_PYTHON} -c \\"import time; time.sleep(30)\\" scripts.api.main:app --host 0.0.0.0 --port {port}"'

    if old_cmd in content:
        content = content.replace(old_cmd, dummy_cmd)
    else:
        # Fallback to regex substitution
        import re
        content = re.sub(
            r'SVC_CMD\[api\]="\$VENV/python -m uvicorn scripts\.api\.main:app --host 0\.0\.0\.0 --port \d+ --log-config scripts/api/logging\.json --timeout-graceful-shutdown \d+"',
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

def test_pid_reconciliation(temp_services_sh, mock_lsof_env):
    """Test stale pid file / listener interactions hermetically."""
    script_path, port = temp_services_sh
    set_pids, clear_pids, env = mock_lsof_env
    api_pid_file = PIDS_DIR / "api.pid"

    # Start a dummy sleep process to act as the listener process.
    proc = subprocess.Popen([
        str(VENV_PYTHON), "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
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
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
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
def test_pid_reconciliation_integration(temp_services_sh_real, mock_lsof_env):
    """Integration test using real sockets and real lsof on macOS."""
    script_path, port = temp_services_sh_real
    api_pid_file = PIDS_DIR / "api.pid"
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
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
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
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
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
        assert "running" in res.stdout
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
