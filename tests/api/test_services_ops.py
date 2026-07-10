"""Integration and hermetic tests for services.sh operations and safety guards using a dynamic port."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICES_SH = PROJECT_ROOT / "services.sh"
PIDS_DIR = PROJECT_ROOT / ".pids"
LOGS_DIR = PROJECT_ROOT / "logs"

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

    # Replace the real uvicorn start command with a python sleep command to avoid binding to real ports
    old_cmd = f'SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port {port} --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"'
    dummy_cmd = f'SVC_CMD[api]="{sys.executable} -c \\"import time; time.sleep(30)\\" scripts.api.main:app --host 0.0.0.0 --port {port}"'

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
    """Create a mock lsof script and expose it via SVC_LSOF_BIN env var."""
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

@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="services.sh is macOS-targeted local-ops tooling; its process-lifecycle "
    "behavior diverges on Linux CI (issue #4930 tracks the divergence). The "
    "platform-neutral logic tests (preload, guards, missing-lsof) run everywhere.",
)
def test_pid_reconciliation(temp_services_sh, mock_lsof_env):
    """Test stale pid file / listener interactions hermetically."""
    script_path, port = temp_services_sh
    set_pids, clear_pids, env = mock_lsof_env
    api_pid_file = PIDS_DIR / "api.pid"

    # Start a dummy sleep process to act as the listener process.
    proc = subprocess.Popen([
        sys.executable, "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
    ])
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
            env=env
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
            env=env
        )
        assert res_stop.returncode == 0, f"stop failed. returncode={res_stop.returncode}\nstdout:\n{res_stop.stdout}\nstderr:\n{res_stop.stderr}"
        proc.wait(timeout=5)
        assert proc.returncode is not None

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()

    # Scenario B: stale pid file + NO listener -> the removal path CI observed
    api_pid_file.write_text("999999\n", encoding="utf-8")
    clear_pids()  # lsof shim returns nothing

    res = subprocess.run(
        [str(script_path), "status", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env
    )
    assert "removing stale pid file" in res.stderr or "removing stale pid file" in res.stdout, f"stale pid check failed. returncode={res.returncode}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert not api_pid_file.exists()

def test_crashloop_backoff(temp_services_sh, mock_lsof_env):
    """Test that starting the api twice within 60s raises an error without --force."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    api_start_file = PIDS_DIR / "api.last_start"

    # Write a last start timestamp from 10 seconds ago
    now = int(time.time())
    api_start_file.write_text(str(now - 10) + "\n", encoding="utf-8")

    # Run start; should trigger the crashloop backoff error since it's <60s
    res = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env
    )

    assert res.returncode != 0, f"expected crashloop backoff non-zero return code. returncode={res.returncode}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "ERROR: api started less than 60s ago" in res.stderr or "ERROR: api started less than 60s ago" in res.stdout, f"crashloop error message missing. stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "Use --force to override" in res.stderr or "Use --force to override" in res.stdout, f"force warning message missing. stdout:\n{res.stdout}\nstderr:\n{res.stderr}"

    # Now run with --force and verify it bypasses the check (it should print starting)
    res_force = subprocess.run(
        [str(script_path), "start", "api", "--force"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env
    )

    assert "potential crashloop" not in res_force.stderr, f"unexpected crashloop warning in stderr.\nstdout:\n{res_force.stdout}\nstderr:\n{res_force.stderr}"
    assert "potential crashloop" not in res_force.stdout, f"unexpected crashloop warning in stdout.\nstdout:\n{res_force.stdout}\nstderr:\n{res_force.stderr}"

    # Clean up the started process if it actually launched
    api_pid_file = PIDS_DIR / "api.pid"
    if api_pid_file.exists():
        try:
            pid = int(api_pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 15)  # SIGTERM
        except Exception:
            pass
    subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT), env=env)

def test_log_rotation(temp_services_sh, mock_lsof_env):
    """Test size-based log rotation for api log file."""
    script_path, _port = temp_services_sh
    _, _, env = mock_lsof_env
    api_log_file = LOGS_DIR / "api.log"
    orig_content = api_log_file.read_bytes() if api_log_file.exists() else b""

    try:
        # Create a log file exceeding 10MB
        large_size = 11 * 1024 * 1024
        api_log_file.write_bytes(b"A" * large_size)

        # Run patched services.sh start api (rotation happens first)
        res = subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        assert res.returncode == 0, f"start failed in log rotation test. returncode={res.returncode}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"

        # Verify rotation occurred: api.log.1 should exist and contain our "A"s
        rotated_file = LOGS_DIR / "api.log.1"
        assert rotated_file.exists()
        assert rotated_file.stat().st_size == large_size

    finally:
        # Clean up the started process if it actually launched
        api_pid_file = PIDS_DIR / "api.pid"
        if api_pid_file.exists():
            try:
                pid = int(api_pid_file.read_text(encoding="utf-8").strip())
                os.kill(pid, 15)  # SIGTERM
            except Exception:
                pass
        subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT), env=env)
        # Restore original log
        if api_log_file.exists():
            api_log_file.unlink()
        if (LOGS_DIR / "api.log.1").exists():
            (LOGS_DIR / "api.log.1").unlink()
        if len(orig_content) > 0:
            api_log_file.write_bytes(orig_content)

@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="services.sh is macOS-targeted local-ops tooling; its process-lifecycle "
    "behavior diverges on Linux CI (issue #4930 tracks the divergence). The "
    "platform-neutral logic tests (preload, guards, missing-lsof) run everywhere.",
)
def test_crashloop_backoff_clean_vs_crash(temp_services_sh, mock_lsof_env):
    """Verify stop-then-start within 60s does NOT trip backoff, but start-after-crash within 60s DOES."""
    script_path, port = temp_services_sh
    set_pids, _, env = mock_lsof_env
    api_start_file = PIDS_DIR / "api.last_start"
    api_pid_file = PIDS_DIR / "api.pid"

    # Start a dummy sleep process
    proc = subprocess.Popen([
        sys.executable, "-c", "import time; time.sleep(30)",
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
    ])

    try:
        # Write the actual listener PID to the pid file to simulate a running state
        api_pid_file.write_text(f"{proc.pid}\n", encoding="utf-8")

        # Configure lsof shim to report our dummy process pid
        set_pids([proc.pid])

        # Write a last start timestamp from 10 seconds ago
        api_start_file.write_text(str(int(time.time()) - 10) + "\n", encoding="utf-8")

        # Now run stop (operator-initiated clean stop). This should succeed, kill proc, and delete api.last_start.
        res_stop = subprocess.run(
            [str(script_path), "stop", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        assert res_stop.returncode == 0, f"stop failed. returncode={res_stop.returncode}\nstdout:\n{res_stop.stdout}\nstderr:\n{res_stop.stderr}"
        assert not api_start_file.exists(), f"last_start file was not deleted on clean stop\nstdout:\n{res_stop.stdout}\nstderr:\n{res_stop.stderr}"

        # Now run start. Since api.last_start was deleted, it should NOT trigger backoff.
        res_start = subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        assert "potential crashloop" not in res_start.stderr, f"unexpected crashloop warning in stderr.\nstdout:\n{res_start.stdout}\nstderr:\n{res_start.stderr}"
        assert "potential crashloop" not in res_start.stdout, f"unexpected crashloop warning in stdout.\nstdout:\n{res_start.stdout}\nstderr:\n{res_start.stderr}"
        assert "ERROR: api started less than 60s ago" not in res_start.stderr, f"expected no crashloop error. stdout:\n{res_start.stdout}\nstderr:\n{res_start.stderr}"
        assert "ERROR: api started less than 60s ago" not in res_start.stdout, f"expected no crashloop error. stdout:\n{res_start.stdout}\nstderr:\n{res_start.stderr}"

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
        # Clean up any started background processes from the start command
        subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT), env=env)

    # Case 2: Start-after-crash (no clean-stop marker) within 60s DOES trigger backoff.
    api_start_file.write_text(str(int(time.time()) - 10) + "\n", encoding="utf-8")

    res_crash_start = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env
    )
    assert res_crash_start.returncode != 0, f"expected crash start to fail. returncode={res_crash_start.returncode}\nstdout:\n{res_crash_start.stdout}\nstderr:\n{res_crash_start.stderr}"
    assert "potential crashloop" in res_crash_start.stderr or "potential crashloop" in res_crash_start.stdout, f"expected crashloop warning. stdout:\n{res_crash_start.stdout}\nstderr:\n{res_crash_start.stderr}"

@pytest.mark.skipif(
    shutil.which("lsof") is None or sys.platform != "darwin",
    reason="macOS local-ops integration; logic covered hermetically above"
)
def test_pid_reconciliation_integration(temp_services_sh_real):
    """Integration test using real sockets and real lsof on macOS."""
    script_path, port = temp_services_sh_real
    api_pid_file = PIDS_DIR / "api.pid"

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
        sys.executable, "-c", dummy_code,
        "scripts.api.main:app", "--host", "0.0.0.0", "--port", str(port)
    ])

    try:
        # Wait a moment for port to bind
        for _ in range(20):
            if not is_port_free(port):
                break
            time.sleep(0.1)

        assert not is_port_free(port), f"Dummy listener did not bind port {port}"

        # Write stale PID to the pid file
        api_pid_file.write_text("999999\n", encoding="utf-8")

        # Run patched services.sh status
        res = subprocess.run(
            [str(script_path), "status", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
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
            cwd=str(PROJECT_ROOT)
        )

        # Verify the dummy process was killed
        proc.wait(timeout=5)
        assert proc.returncode is not None
        assert is_port_free(port)

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
