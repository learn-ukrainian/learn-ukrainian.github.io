"""Stall detection watchdog for the agent runtime.

This module implements the two-layer stall detection described in
docs/design/agent-runtime.md § 4.6. Both layers feed a single
``last_activity`` clock; the runner kills the subprocess when either:

- ``now - last_activity > stall_timeout`` → AgentStalledError (agent went silent)
- ``now - start_time > hard_timeout`` → AgentTimeoutError (wall clock exceeded)

Layer 1 — Streaming stdout watchdog (primary):
    A background thread reads stdout line-by-line from ``Popen.stdout``
    and bumps ``last_activity`` on every line. Lifted from the prior art
    in ``scripts/ai_agent_bridge/_gemini.py::_stream_with_watchdog``
    (``_STALL_THRESHOLD = 120``).

Layer 2 — Liveness file mtime polling (fallback):
    For adapters where stdout is redirected to ``-o <file>`` or buffered
    (Codex writes final output to a file; Gemini's ``--output-path`` mode
    hides output from stdout), a second thread polls mtimes on the paths
    returned by ``adapter.liveness_signal_paths(plan)`` every 5 seconds.
    Any mtime bump is treated as "agent is alive" and resets the clock.

Why both: stdout streaming is the primary signal (works for any agent that
talks to stdout), but ``codex exec -o <file>`` can go silent on stdout for
minutes while still writing the output file. Mtime polling catches those.

Issue: #1184
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# Poll interval for the mtime fallback thread. 5s is a good balance — fast
# enough to extend the stall clock promptly, slow enough that the overhead
# is negligible (at most 5 stat calls per 5s = ~1 per second).
_MTIME_POLL_INTERVAL_S = 5.0

# Maximum number of liveness paths to poll. Adapters returning more than
# this many paths will only have the first _MAX_LIVENESS_PATHS polled.
# Arbitrary but bounded — prevents adapter mistakes from causing poll storms.
_MAX_LIVENESS_PATHS = 5


@dataclass
class WatchdogState:
    """Shared state between the main thread and the background watchdog threads.

    Mutable by design. Access is not lock-protected because we only write
    monotonic floats to ``last_activity`` and booleans to ``stop`` — both
    are atomic on CPython due to the GIL.

    Fields:
        start_time: monotonic timestamp when the subprocess was spawned.
        last_activity: monotonic timestamp of the most recent observed
            activity (stdout line or liveness file mtime bump).
        stop: Set to True by the main thread when the watchdog should exit.
        stdout_lines: Accumulated stdout lines captured by the streamer.
            The runner reads this on normal termination to build the final
            response. (Popen.communicate() would block; we need nonblocking.)
    """
    start_time: float
    last_activity: float
    stop: bool = False
    stdout_lines: list[str] = field(default_factory=list)


def _stdout_streamer(proc: subprocess.Popen, state: WatchdogState) -> None:
    """Background thread: read stdout line-by-line, bump last_activity.

    Exits when the pipe closes (subprocess terminates) or state.stop is True.
    """
    assert proc.stdout is not None  # Popen was configured with stdout=PIPE
    try:
        for line in iter(proc.stdout.readline, ""):
            if state.stop:
                break
            state.stdout_lines.append(line)
            state.last_activity = time.monotonic()
    except (ValueError, OSError):
        # Pipe closed or subprocess killed. Normal shutdown path.
        pass
    finally:
        # Ensure the pipe is drained/closed so the subprocess's exit
        # doesn't hang waiting for us to consume.
        try:
            if proc.stdout is not None:
                proc.stdout.close()
        except OSError:
            pass


def _mtime_poller(paths: Iterable[Path], state: WatchdogState) -> None:
    """Background thread: poll file mtimes, bump last_activity on changes.

    Exits when state.stop is True or after the subprocess terminates.
    """
    # Snapshot initial mtimes so we only react to CHANGES, not mere presence.
    baseline_mtimes: dict[Path, float] = {}
    for p in paths:
        try:
            baseline_mtimes[p] = p.stat().st_mtime
        except OSError:
            baseline_mtimes[p] = 0.0  # file doesn't exist yet; any future mtime counts

    while not state.stop:
        time.sleep(_MTIME_POLL_INTERVAL_S)
        if state.stop:
            break
        for p, baseline in baseline_mtimes.items():
            try:
                current = p.stat().st_mtime
            except OSError:
                continue  # file disappeared or permission denied; skip
            if current > baseline:
                state.last_activity = time.monotonic()
                baseline_mtimes[p] = current


def start_watchdog(
    proc: subprocess.Popen,
    liveness_paths: Iterable[Path],
) -> tuple[WatchdogState, list[threading.Thread]]:
    """Start the stdout streamer + mtime poller threads for a running subprocess.

    Args:
        proc: A Popen object with ``stdout=subprocess.PIPE`` and ``text=True``.
        liveness_paths: Paths to poll for mtime changes (adapter-provided).
            Capped at ``_MAX_LIVENESS_PATHS``.

    Returns:
        (state, threads): The shared state and the list of started threads.
        Callers must call ``stop_watchdog(state, threads)`` to join them
        cleanly after the subprocess terminates.
    """
    now = time.monotonic()
    state = WatchdogState(start_time=now, last_activity=now)

    threads: list[threading.Thread] = []

    # Layer 1: stdout streamer (always started if stdout is a pipe)
    if proc.stdout is not None:
        t_stdout = threading.Thread(
            target=_stdout_streamer,
            args=(proc, state),
            name=f"watchdog-stdout-{proc.pid}",
            daemon=True,
        )
        t_stdout.start()
        threads.append(t_stdout)

    # Layer 2: mtime poller (only if adapter returned any paths)
    capped = list(liveness_paths)[:_MAX_LIVENESS_PATHS]
    if capped:
        t_mtime = threading.Thread(
            target=_mtime_poller,
            args=(capped, state),
            name=f"watchdog-mtime-{proc.pid}",
            daemon=True,
        )
        t_mtime.start()
        threads.append(t_mtime)

    return state, threads


def stop_watchdog(
    state: WatchdogState,
    threads: list[threading.Thread],
    timeout: float = 2.0,
) -> None:
    """Signal the watchdog threads to stop and join them.

    Safe to call multiple times. Threads that don't join within ``timeout``
    are left running as daemons — they'll be killed on process exit.
    """
    state.stop = True
    for t in threads:
        t.join(timeout=timeout)


def should_kill(state: WatchdogState, stall_timeout: int, hard_timeout: int) -> str | None:
    """Check if the subprocess should be killed. Returns the kill reason or None.

    Returns:
        None if the process should continue running.
        "stalled" if no activity for longer than stall_timeout.
        "hard_timeout" if total runtime exceeded hard_timeout.

    Callers (the runner) poll this in a loop while waiting on the subprocess.
    """
    now = time.monotonic()
    if (now - state.start_time) > hard_timeout:
        return "hard_timeout"
    if (now - state.last_activity) > stall_timeout:
        return "stalled"
    return None


def tail_liveness_file_for_debug(
    paths: Iterable[Path],
    max_bytes: int = 4096,
) -> str:
    """Tail the newest liveness file for error diagnostics.

    Called by the runner on failure to capture the agent's "last known
    thoughts" from its session file, since stderr may be empty or useless.
    Returns the concatenated tails or an empty string if nothing found.

    Safe against all filesystem errors; returns "" on any problem.
    """
    candidates: list[tuple[float, Path]] = []
    for p in paths:
        try:
            mtime = p.stat().st_mtime
            candidates.append((mtime, p))
        except OSError:
            continue

    if not candidates:
        return ""

    # Pick the most recently modified file
    candidates.sort(reverse=True)
    _, newest = candidates[0]

    try:
        size = newest.stat().st_size
        if size == 0:
            return ""
        with open(newest, "rb") as f:
            if size > max_bytes:
                f.seek(-max_bytes, os.SEEK_END)
            tail_bytes = f.read()
        return tail_bytes.decode("utf-8", errors="replace")
    except OSError:
        return ""
