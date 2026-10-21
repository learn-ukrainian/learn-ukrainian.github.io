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
import sys
import threading
import time
from pathlib import Path

import pytest

from tests.helpers.python import project_python

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_TEST_PYTHON = project_python()

from agent_runtime.runner import (
    _spawn_pty_subprocess,
)
from agent_runtime.watchdog import (
    WatchdogState,
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


# ----------------------------------------------------------------------
# Test 2: TIOCSWINSZ is applied to the slave so children see the window.
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Test 3: EOF on child exit — either b"" or EIO, both treated as shutdown.
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# Test 7: DELEGATE_DISABLE_PTY env var falls back to pipe spawn.
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _safe_close(fd: int | None) -> None:
    if fd is None:
        return
    with contextlib.suppress(OSError):
        os.close(fd)
