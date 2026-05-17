"""Tests for the PTY-wrapped subprocess spawn path in agent_runtime.

Background — Issue #2071: Codex (and any agent CLI that uses libc stdio)
block-buffers stdout when it isn't a TTY. With the legacy pipe-based
spawn, events accumulated in the child's stdout buffer and only flushed
on buffer-full / exit / explicit fflush — so the watchdog's stdout
silence timer fired even though the child was actively producing
events. The PTY-wrapped spawn makes the child's stdout look like a TTY,
which forces libc to switch to line-buffering, and events arrive in
real time.

These tests pin the PTY spawn helper + the PTY-mode watchdog streamer:

* Spawn returns valid fds, applies window size, EOF works on child exit
* Block-buffering regression — the load-bearing assertion: an unflushed
  child write becomes visible to the watchdog BEFORE the child exits
* UTF-8 split across read boundary doesn't corrupt characters
* ANSI escape sequences emitted by TTY-detecting CLIs are stripped
* DELEGATE_DISABLE_PTY=1 falls back to pipe spawn (escape hatch)
* Master fds are closed on cleanup; multi-line chunks split correctly;
  streamer threads join cleanly on child kill
* End-to-end via the watchdog: 10 child lines with no fflush all reach
  state.stdout_lines in real time
"""
from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_VENV_PYTHON_CANDIDATES = [
    _REPO_ROOT / ".venv" / "bin" / "python",
]


def _resolve_test_python() -> str:
    """Resolve `.venv/bin/python` for subprocess tests.

    Worktree-aware: when the worktree's own .venv doesn't exist, walk
    up via ``git rev-parse --git-common-dir`` to the main checkout's
    venv. AGENTS.md forbids falling back to ``sys.executable``.
    """
    for candidate in _VENV_PYTHON_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    try:
        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(_REPO_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if common_dir:
            main_venv = (Path(common_dir) / ".." / ".venv" / "bin" / "python").resolve()
            if main_venv.exists():
                return str(main_venv)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    raise RuntimeError(
        "No project virtualenv Python found. Expected `.venv/bin/python` "
        "in the current checkout or via git-common-dir."
    )


_TEST_PYTHON = _resolve_test_python()

from agent_runtime.runner import (
    _pty_disabled_via_env,
    _spawn_pipe_subprocess,
    _spawn_pty_subprocess,
    _spawn_subprocess,
)
from agent_runtime.watchdog import (
    WatchdogState,
    _strip_ansi,
    start_watchdog,
    stop_watchdog,
)


@pytest.fixture
def clean_env(monkeypatch):
    """Ensure DELEGATE_DISABLE_PTY is unset; tests opt in explicitly."""
    monkeypatch.delenv("DELEGATE_DISABLE_PTY", raising=False)
    yield


# ----------------------------------------------------------------------
# Test 1: PTY spawn returns valid fds + child output reaches master.
# ----------------------------------------------------------------------

def test_pty_spawn_returns_valid_fds_and_master_reads_child_output(clean_env, tmp_path):
    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        ["echo", "hi"],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    try:
        assert isinstance(stdout_fd, int) and stdout_fd >= 0
        assert isinstance(stderr_fd, int) and stderr_fd >= 0
        # fds are valid (fstat succeeds)
        assert os.fstat(stdout_fd).st_mode != 0
        assert os.fstat(stderr_fd).st_mode != 0
        # Read until EOF — child is `echo hi`.
        chunks = []
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                chunk = os.read(stdout_fd, 4096)
            except OSError:  # Linux EIO on PTS close
                break
            if not chunk:
                break
            chunks.append(chunk)
            if proc.poll() is not None and not chunk:
                break
        data = b"".join(chunks)
        # OPOST disabled → \n stays \n. Some kernels still re-add \r,
        # so check the payload not the exact line terminator.
        assert b"hi" in data
    finally:
        for fd in (stdout_fd, stderr_fd):
            with contextlib.suppress(OSError):
                os.close(fd)
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5.0)


# ----------------------------------------------------------------------
# Test 2: TIOCSWINSZ is applied to the slave so children see the window.
# ----------------------------------------------------------------------

def test_pty_spawn_sets_window_size_visible_to_child(clean_env, tmp_path):
    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [
            _TEST_PYTHON,
            "-c",
            "import sys, fcntl, termios, struct; "
            "buf = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b'\\0'*8); "
            "rows, cols, _, _ = struct.unpack('HHHH', buf); "
            "print(f'{rows} {cols}', flush=True)",
        ],
        cwd=tmp_path,
        env=os.environ.copy(),
        pty_window=(48, 132),
    )
    try:
        data = _read_until_eof(stdout_fd, timeout_s=5.0)
        assert "48 132" in data, f"window not applied; got {data!r}"
    finally:
        _safe_close(stdout_fd)
        _safe_close(stderr_fd)
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5.0)


# ----------------------------------------------------------------------
# Test 3: EOF on child exit — either b"" or EIO, both treated as shutdown.
# ----------------------------------------------------------------------

def test_pty_master_read_returns_eof_or_eio_on_child_exit(clean_env, tmp_path):
    import errno as _errno

    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [_TEST_PYTHON, "-c", "import sys; sys.stdout.write('done\\n'); sys.stdout.flush()"],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    try:
        # Drain the pty as the child runs — on macOS, kernel may discard
        # pending bytes when the slave side closes, so we MUST read while
        # the child is still alive or right at the boundary.
        data = b""
        deadline = time.monotonic() + 5.0
        saw_eof = False
        while time.monotonic() < deadline:
            try:
                chunk = os.read(stdout_fd, 4096)
            except OSError as exc:
                # Linux raises EIO on slave close — that IS the EOF signal.
                assert exc.errno == _errno.EIO, f"unexpected errno: {exc.errno}"
                saw_eof = True
                break
            if not chunk:
                # macOS path: empty bytes signal EOF.
                saw_eof = True
                break
            data += chunk
        proc.wait(timeout=5.0)
        assert b"done" in data, f"missed 'done' marker: {data!r}"
        assert saw_eof, "expected EOF / EIO after child exit"
    finally:
        _safe_close(stdout_fd)
        _safe_close(stderr_fd)


# ----------------------------------------------------------------------
# Test 4 (LOAD-BEARING): block-buffered child output reaches the streamer
# in real time when PTY-wrapped.
#
# This is the core regression guard. With the legacy pipe spawn, a child
# that writes "a", sleeps 0.5s, writes "b" — without ever calling
# fflush(stdout) — would not surface "a" until the buffer filled or the
# child exited. PTY makes the child line-buffer, so "a" appears
# immediately.
# ----------------------------------------------------------------------

def test_pty_breaks_block_buffering_for_unflushed_child(clean_env, tmp_path):
    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [
            _TEST_PYTHON,
            "-c",
            # No flush calls — relies entirely on line-buffering kicking in
            # because the child detects stdout is a TTY (PTY).
            "import sys, time; "
            "sys.stdout.write('a\\n'); "
            "time.sleep(0.5); "
            "sys.stdout.write('b\\n')",
        ],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    state = None
    threads = []
    try:
        state, threads = start_watchdog(
            proc,
            liveness_paths=[],
            stdout_master_fd=stdout_fd,
            stderr_master_fd=stderr_fd,
        )
        # Within ~0.3s — before the 0.5s sleep — "a\n" must be visible.
        # If we get this within 0.3s the PTY line-buffering is working.
        # If it only shows up after the child exits (~0.5s+), the PTY
        # change isn't actually taking effect.
        deadline = time.monotonic() + 0.4
        while time.monotonic() < deadline:
            if state.stdout_lines and any("a" in ln for ln in state.stdout_lines):
                break
            time.sleep(0.02)
        assert state.stdout_lines, (
            "no stdout lines reached the streamer within 0.4s — "
            "PTY is not actually line-buffering the child"
        )
        assert any("a" in ln for ln in state.stdout_lines), (
            f"first line missing 'a'; got lines: {state.stdout_lines!r}"
        )
        # Both lines should be present after child exits.
        proc.wait(timeout=5.0)
        time.sleep(0.1)  # let streamer drain
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)
        if state is not None:
            stop_watchdog(
                state,
                threads,
                proc=proc,
                stdout_master_fd=stdout_fd,
                stderr_master_fd=stderr_fd,
                timeout=2.0,
            )
        else:
            _safe_close(stdout_fd)
            _safe_close(stderr_fd)
    # After draining, both lines must be present.
    joined = "".join(state.stdout_lines) if state else ""
    assert "a" in joined and "b" in joined, (
        f"expected both 'a' and 'b' lines; got: {joined!r}"
    )


# ----------------------------------------------------------------------
# Test 5: UTF-8 multi-byte sequence split across two reads stays intact.
#
# We construct this at the streamer level: feed a pre-made WatchdogState
# and master_fd from a socketpair to deterministically split bytes.
# ----------------------------------------------------------------------

def test_pty_streamer_handles_utf8_split_across_read_boundary():
    import socket

    from agent_runtime.watchdog import _pty_line_streamer

    # Use socketpair as a stand-in for the master_fd. os.read() works
    # the same way on a socket fd, so this isolates the streamer logic
    # from PTY-specific termios behavior.
    parent, child = socket.socketpair()
    parent.setblocking(True)

    state = WatchdogState(start_time=time.monotonic(), last_activity=time.monotonic())
    t = threading.Thread(
        target=_pty_line_streamer,
        args=(parent.fileno(), state),
        kwargs={"is_stderr": False},
        daemon=True,
    )
    t.start()
    try:
        # Encode "україна\n" as UTF-8 then write 1 byte at a time so the
        # streamer's reads land on a multi-byte boundary.
        payload = "україна\n".encode()
        for byte in payload:
            child.sendall(bytes([byte]))
            time.sleep(0.005)
        child.close()  # EOF
        t.join(timeout=2.0)
        assert state.stdout_lines == ["україна\n"], (
            f"UTF-8 was corrupted by the read split; got: {state.stdout_lines!r}"
        )
    finally:
        parent.close()
        with contextlib.suppress(OSError):
            child.close()


# ----------------------------------------------------------------------
# Test 6: ANSI escape sequences are stripped from streamed lines.
# ----------------------------------------------------------------------

def test_pty_streamer_strips_ansi_sgr_codes():
    import socket

    from agent_runtime.watchdog import _pty_line_streamer

    parent, child = socket.socketpair()
    parent.setblocking(True)

    state = WatchdogState(start_time=time.monotonic(), last_activity=time.monotonic())
    t = threading.Thread(
        target=_pty_line_streamer,
        args=(parent.fileno(), state),
        kwargs={"is_stderr": False},
        daemon=True,
    )
    t.start()
    try:
        # Red "hello" then reset, plus a cursor-position CSI.
        payload = b"\x1b[31mhello\x1b[0m\x1b[2;5Hworld\n"
        child.sendall(payload)
        child.close()
        t.join(timeout=2.0)
        assert state.stdout_lines == ["helloworld\n"], (
            f"ANSI not stripped; got: {state.stdout_lines!r}"
        )
    finally:
        parent.close()
        with contextlib.suppress(OSError):
            child.close()


def test_strip_ansi_helper_unit():
    assert _strip_ansi("\x1b[31mred\x1b[0m") == "red"
    assert _strip_ansi("plain") == "plain"
    assert _strip_ansi("\x1b[K") == ""  # CSI K = erase-line, all-stripped


# ----------------------------------------------------------------------
# Test 7: DELEGATE_DISABLE_PTY env var falls back to pipe spawn.
# ----------------------------------------------------------------------

@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_delegate_disable_pty_env_var_routes_to_pipe_spawn(monkeypatch, tmp_path, value):
    monkeypatch.setenv("DELEGATE_DISABLE_PTY", value)
    assert _pty_disabled_via_env()
    proc, stdout_fd, stderr_fd = _spawn_subprocess(
        [_TEST_PYTHON, "-c", "print('hi')"],
        cwd=tmp_path,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
    )
    try:
        # Pipe path returns None fds and exposes proc.stdout/proc.stderr.
        assert stdout_fd is None
        assert stderr_fd is None
        assert proc.stdout is not None
        assert proc.stderr is not None
        proc.wait(timeout=5.0)
        out = proc.stdout.read()
        assert "hi" in out
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5.0)


def test_delegate_disable_pty_unset_routes_to_pty_spawn(clean_env, tmp_path):
    assert not _pty_disabled_via_env()
    proc, stdout_fd, stderr_fd = _spawn_subprocess(
        [_TEST_PYTHON, "-c", "print('hi')"],
        cwd=tmp_path,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
    )
    try:
        assert stdout_fd is not None and stdout_fd >= 0
        assert stderr_fd is not None and stderr_fd >= 0
        proc.wait(timeout=5.0)
    finally:
        _safe_close(stdout_fd)
        _safe_close(stderr_fd)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


def test_pipe_spawn_helper_directly(tmp_path):
    proc, sfd, efd = _spawn_pipe_subprocess(
        [_TEST_PYTHON, "-c", "print('p')"],
        cwd=tmp_path,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
    )
    try:
        assert sfd is None and efd is None
        assert proc.stdout is not None
        proc.wait(timeout=5.0)
        assert "p" in proc.stdout.read()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


# ----------------------------------------------------------------------
# Test 8: Master fds are closed after stop_watchdog cleanup.
# ----------------------------------------------------------------------

def test_stop_watchdog_closes_pty_master_fds(clean_env, tmp_path):
    import errno as _errno

    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [_TEST_PYTHON, "-c", "print('cleanup')"],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    state, threads = start_watchdog(
        proc,
        liveness_paths=[],
        stdout_master_fd=stdout_fd,
        stderr_master_fd=stderr_fd,
    )
    proc.wait(timeout=5.0)
    stop_watchdog(
        state,
        threads,
        proc=proc,
        stdout_master_fd=stdout_fd,
        stderr_master_fd=stderr_fd,
        timeout=2.0,
    )
    # Verify both fds are closed (fstat raises EBADF).
    for fd in (stdout_fd, stderr_fd):
        with pytest.raises(OSError) as exc_info:
            os.fstat(fd)
        assert exc_info.value.errno == _errno.EBADF, (
            f"expected EBADF on closed fd; got {exc_info.value.errno}"
        )


# ----------------------------------------------------------------------
# Test 9: Multiple lines in a single os.read chunk are split correctly.
# ----------------------------------------------------------------------

def test_pty_streamer_splits_multiple_lines_per_read():
    import socket

    from agent_runtime.watchdog import _pty_line_streamer

    parent, child = socket.socketpair()
    state = WatchdogState(start_time=time.monotonic(), last_activity=time.monotonic())
    t = threading.Thread(
        target=_pty_line_streamer,
        args=(parent.fileno(), state),
        kwargs={"is_stderr": False},
        daemon=True,
    )
    t.start()
    try:
        # Send 3 lines in a single write; streamer must emit 3 entries.
        child.sendall(b"line-1\nline-2\nline-3\n")
        child.close()
        t.join(timeout=2.0)
        assert state.stdout_lines == ["line-1\n", "line-2\n", "line-3\n"], (
            f"line splitting wrong; got: {state.stdout_lines!r}"
        )
    finally:
        parent.close()
        with contextlib.suppress(OSError):
            child.close()


def test_pty_streamer_flushes_trailing_fragment_on_eof():
    """If the child writes a partial last line then exits, capture it."""
    import socket

    from agent_runtime.watchdog import _pty_line_streamer

    parent, child = socket.socketpair()
    state = WatchdogState(start_time=time.monotonic(), last_activity=time.monotonic())
    t = threading.Thread(
        target=_pty_line_streamer,
        args=(parent.fileno(), state),
        kwargs={"is_stderr": False},
        daemon=True,
    )
    t.start()
    try:
        child.sendall(b"final-fragment-no-newline")
        child.close()
        t.join(timeout=2.0)
        # Trailing fragment is emitted on EOF as its own entry.
        joined = "".join(state.stdout_lines)
        assert "final-fragment-no-newline" in joined, (
            f"trailing fragment dropped; got: {state.stdout_lines!r}"
        )
    finally:
        parent.close()
        with contextlib.suppress(OSError):
            child.close()


# ----------------------------------------------------------------------
# Test 10: Streamer thread joins cleanly on child kill.
# ----------------------------------------------------------------------

def test_streamer_threads_join_quickly_after_child_kill(clean_env, tmp_path):
    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [_TEST_PYTHON, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    state, threads = start_watchdog(
        proc,
        liveness_paths=[],
        stdout_master_fd=stdout_fd,
        stderr_master_fd=stderr_fd,
    )
    try:
        stdout_threads = [t for t in threads if "stdout" in t.name]
        assert stdout_threads, "stdout streamer thread missing"
        proc.kill()
        proc.wait(timeout=5.0)
        stop_watchdog(
            state,
            threads,
            proc=proc,
            stdout_master_fd=stdout_fd,
            stderr_master_fd=stderr_fd,
            timeout=2.0,
        )
        # All streamer threads must have exited.
        for t in threads:
            assert not t.is_alive(), (
                f"thread {t.name} leaked after stop_watchdog"
            )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


# ----------------------------------------------------------------------
# Test 11 (END-TO-END): 10 unflushed child lines all reach state in ~1s.
# Combines the block-buffer fix with the full watchdog hookup.
# ----------------------------------------------------------------------

def test_end_to_end_pty_watchdog_streams_unflushed_child_in_real_time(
    clean_env, tmp_path,
):
    proc, stdout_fd, stderr_fd = _spawn_pty_subprocess(
        [
            _TEST_PYTHON,
            "-c",
            "import sys, time; "
            "[(sys.stdout.write(f'event-{i}\\n')) or time.sleep(0.05) "
            "for i in range(10)]",
        ],
        cwd=tmp_path,
        env=os.environ.copy(),
    )
    state, threads = start_watchdog(
        proc,
        liveness_paths=[],
        stdout_master_fd=stdout_fd,
        stderr_master_fd=stderr_fd,
    )
    try:
        proc.wait(timeout=10.0)
        # Give the streamer a brief moment to drain after EOF.
        for _ in range(50):
            if len(state.stdout_lines) >= 10:
                break
            time.sleep(0.05)
        assert len(state.stdout_lines) >= 10, (
            f"streamer captured {len(state.stdout_lines)} / 10 lines; "
            f"got: {state.stdout_lines!r}"
        )
        # All event-N markers should be present.
        joined = "".join(state.stdout_lines)
        for i in range(10):
            assert f"event-{i}" in joined, (
                f"missing event-{i} in: {joined!r}"
            )
    finally:
        stop_watchdog(
            state,
            threads,
            proc=proc,
            stdout_master_fd=stdout_fd,
            stderr_master_fd=stderr_fd,
            timeout=2.0,
        )
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _safe_close(fd: int | None) -> None:
    if fd is None:
        return
    with contextlib.suppress(OSError):
        os.close(fd)


def _read_until_eof(fd: int, *, timeout_s: float) -> str:
    """Drain a PTY master fd until EOF or timeout; return decoded text."""
    chunks: list[bytes] = []
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break  # Linux EIO
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace")
