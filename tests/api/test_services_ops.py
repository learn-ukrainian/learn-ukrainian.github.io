"""Integration tests for services.sh operations and safety guards using a dynamic port."""

from __future__ import annotations

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
def temp_services_sh():
    """Create a copy of services.sh configured with a dynamic free port."""
    port = find_free_port()
    temp_script = PROJECT_ROOT / f"services_test_{port}.sh"

    # Read and patch services.sh content
    content = SERVICES_SH.read_text(encoding="utf-8")
    content = content.replace("8765", str(port))

    temp_script.write_text(content, encoding="utf-8")
    temp_script.chmod(0o755)

    yield temp_script, port

    # Cleanup temp script
    if temp_script.exists():
        temp_script.unlink()

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

def test_pid_reconciliation(temp_services_sh):
    """Test stale pid file + live listener -> status reports listener, restart/stop kills listener."""
    script_path, port = temp_services_sh

    # Start a dummy listener process with the API signature configured for our dynamic port
    dummy_code = (
        f"import socket, time; "
        f"s = socket.socket(); "
        f"s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); "
        f"s.bind(('127.0.0.1', {port})); "
        f"s.listen(1); "
        f"time.sleep(30)"
    )
    # The arguments must match the SVC_MATCH pattern in the temp script
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
        api_pid_file = PIDS_DIR / "api.pid"
        api_pid_file.write_text("999999\n", encoding="utf-8")

        # Run patched services.sh status
        res = subprocess.run(
            [str(script_path), "status", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        # Assert reconciliation warned and updated the pid file
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

def test_crashloop_backoff(temp_services_sh):
    """Test that starting the api twice within 60s raises an error without --force."""
    script_path, _port = temp_services_sh
    api_start_file = PIDS_DIR / "api.last_start"

    # Write a last start timestamp from 10 seconds ago
    now = int(time.time())
    api_start_file.write_text(str(now - 10) + "\n", encoding="utf-8")

    # Run start; should trigger the crashloop backoff error since it's <60s
    res = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )

    assert res.returncode != 0
    assert "ERROR: api started less than 60s ago" in res.stderr or "ERROR: api started less than 60s ago" in res.stdout
    assert "Use --force to override" in res.stderr or "Use --force to override" in res.stdout

    # Now run with --force and verify it bypasses the check (it should print starting)
    res_force = subprocess.run(
        [str(script_path), "start", "api", "--force"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )

    assert "potential crashloop" not in res_force.stderr
    assert "potential crashloop" not in res_force.stdout

    # Clean up the started process if it actually launched
    api_pid_file = PIDS_DIR / "api.pid"
    if api_pid_file.exists():
        try:
            pid = int(api_pid_file.read_text(encoding="utf-8").strip())
            import os
            import signal
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT))

def test_log_rotation(temp_services_sh):
    """Test size-based log rotation for api log file."""
    script_path, _port = temp_services_sh
    api_log_file = LOGS_DIR / "api.log"
    orig_content = api_log_file.read_bytes() if api_log_file.exists() else b""

    try:
        # Create a log file exceeding 10MB
        large_size = 11 * 1024 * 1024
        api_log_file.write_bytes(b"A" * large_size)

        # Run patched services.sh start api (rotation happens first)
        subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

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
                import os
                import signal
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
        subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT))
        # Restore original log
        if api_log_file.exists():
            api_log_file.unlink()
        if (LOGS_DIR / "api.log.1").exists():
            (LOGS_DIR / "api.log.1").unlink()
        if len(orig_content) > 0:
            api_log_file.write_bytes(orig_content)


def test_crashloop_backoff_clean_vs_crash(temp_services_sh):
    """Verify stop-then-start within 60s does NOT trip backoff, but start-after-crash within 60s DOES."""
    script_path, port = temp_services_sh
    api_start_file = PIDS_DIR / "api.last_start"
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
        # Wait for dynamic port to bind
        for _ in range(20):
            if not is_port_free(port):
                break
            time.sleep(0.1)
        assert not is_port_free(port), f"Dummy listener did not bind port {port}"

        # Write the actual listener PID to the pid file to simulate a running state
        api_pid_file.write_text(f"{proc.pid}\n", encoding="utf-8")

        # Write a last start timestamp from 10 seconds ago
        api_start_file.write_text(str(int(time.time()) - 10) + "\n", encoding="utf-8")

        # Now run stop (operator-initiated clean stop). This should succeed, kill proc, and delete api.last_start.
        res_stop = subprocess.run(
            [str(script_path), "stop", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        assert res_stop.returncode == 0
        assert not api_start_file.exists(), "last_start file was not deleted on clean stop"

        # Now run start. Since api.last_start was deleted, it should NOT trigger backoff.
        # It will try to start. We check that the output does NOT contain "potential crashloop" or "ERROR: api started less than 60s ago".
        res_start = subprocess.run(
            [str(script_path), "start", "api"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        assert "potential crashloop" not in res_start.stderr
        assert "potential crashloop" not in res_start.stdout
        assert "ERROR: api started less than 60s ago" not in res_start.stderr
        assert "ERROR: api started less than 60s ago" not in res_start.stdout

    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
        # Clean up any started background processes from the start command
        subprocess.run([str(script_path), "stop", "api"], capture_output=True, cwd=str(PROJECT_ROOT))

    # Case 2: Start-after-crash (no clean-stop marker) within 60s DOES trigger backoff.
    api_start_file.write_text(str(int(time.time()) - 10) + "\n", encoding="utf-8")

    res_crash_start = subprocess.run(
        [str(script_path), "start", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res_crash_start.returncode != 0
    assert "potential crashloop" in res_crash_start.stderr or "potential crashloop" in res_crash_start.stdout
