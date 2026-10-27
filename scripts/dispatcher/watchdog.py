"""Legacy composite deadlines over the dispatcher's file-backed child output."""

import math
import subprocess
import time
from pathlib import Path

from scripts.agent_runtime.watchdog import (
    _MAX_LIVENESS_PATHS,
    _PROCESS_ACTIVITY_POLL_INTERVAL_S,
    WatchdogState,
    _process_tree_has_activity,
    should_kill,
)

DEFAULT_HARD_TIMEOUT_S = 7200
DEFAULT_SILENCE_TIMEOUT_S = 3600
DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 600


class DeadlineExpired(subprocess.TimeoutExpired):
    def __init__(self, argv, kind, seconds):
        super().__init__(argv, seconds)
        self.kind = kind
        if kind == "initial_response_timeout":
            self.diagnostic = (
                f"initial_response_timeout fired after {seconds:g}s with no first observable startup activity "
                "(stdout, stderr, liveness file, or process-tree work) "
                f"— raise it with --initial-response-timeout (current default {DEFAULT_INITIAL_RESPONSE_TIMEOUT_S}s)"
            )
        elif kind == "stdout_silence_timeout":
            self.diagnostic = (
                f"stdout_silence_timeout fired after {seconds:g}s without watchdog activity "
                f"— raise it with --silence-timeout (current default {DEFAULT_SILENCE_TIMEOUT_S}s)"
            )
        else:
            self.diagnostic = "process deadline exceeded"


def deadlines(options):
    values = tuple(float(options.get(key, default)) for key, default in (
        ("hard_timeout", DEFAULT_HARD_TIMEOUT_S),
        ("silence_timeout", DEFAULT_SILENCE_TIMEOUT_S),
        ("initial_response_timeout", DEFAULT_INITIAL_RESPONSE_TIMEOUT_S),
    ))
    if values[0] < 0:
        raise ValueError("invalid process deadline or conflicting existing-worktree options")
    return values


def liveness_paths(spec, invocation):
    if paths := getattr(invocation, "liveness_paths", None):
        return paths
    if spec.agent in {"claude", "codex"}:
        from scripts.agent_runtime.adapters.base import InvocationPlan
        from scripts.agent_runtime.adapters.claude import ClaudeAdapter
        from scripts.agent_runtime.adapters.codex import CodexAdapter

        adapter = ClaudeAdapter() if spec.agent == "claude" else CodexAdapter()
        plan = InvocationPlan(cmd=invocation.argv, cwd=spec.worktree,
                              output_file=invocation.final_file, env_overrides=invocation.env)
        return lambda: adapter.liveness_signal_paths(plan)
    paths = (invocation.final_file,) if invocation.final_file else ()
    if spec.agent == "agy" and "--log-file" in invocation.argv:
        paths += (Path(invocation.argv[invocation.argv.index("--log-file") + 1]),)
    return lambda: paths


def communicate(child, invocation, stdout_path, stderr_path, hard_timeout, silence_timeout,
                initial_response_timeout, liveness, output_sizes):
    """Keep stdin nonblocking while observing I/O, session files and tree work."""
    started = time.monotonic()
    state = WatchdogState(start_time=started, last_activity=started)
    paths = (stdout_path, stderr_path)
    sizes = dict(zip(paths, output_sizes, strict=True))
    mtimes, primed, cpu, io = {}, set(), {}, {}
    for path in tuple(liveness())[:_MAX_LIVENESS_PATHS]:
        try:
            mtimes[Path(path)] = Path(path).stat().st_mtime_ns
        except OSError:
            mtimes[Path(path)] = 0
    next_activity_poll = started
    payload = invocation.stdin
    while True:
        try:
            child.communicate(payload, timeout=0.1)
            return
        except subprocess.TimeoutExpired:
            payload = None
        now = time.monotonic()
        for path in paths:
            size = path.stat().st_size
            if size != sizes[path]:
                state.last_activity, state.observed_io = now, True
                sizes[path] = size
        if now >= next_activity_poll:
            if _process_tree_has_activity(child, primed, cpu, io):
                state.last_activity, state.observed_io = now, True
            for path in tuple(liveness())[:_MAX_LIVENESS_PATHS]:
                path = Path(path)
                try:
                    mtime = path.stat().st_mtime_ns
                except OSError:
                    mtime = 0
                baseline = mtimes.setdefault(path, 0)
                if mtime > baseline:
                    state.last_activity, state.observed_io = now, True
                    mtimes[path] = mtime
            next_activity_poll = now + _PROCESS_ACTIVITY_POLL_INTERVAL_S
        if reason := should_kill(
            state, stall_timeout=0, hard_timeout=hard_timeout or math.inf,
            stdout_silence_timeout=silence_timeout, initial_response_timeout=initial_response_timeout,
        ):
            seconds = {"hard_timeout": hard_timeout, "stdout_silence_timeout": silence_timeout,
                       "initial_response_timeout": initial_response_timeout}[reason]
            raise DeadlineExpired(invocation.argv, reason, seconds)
