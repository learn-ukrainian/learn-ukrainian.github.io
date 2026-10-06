"""Run one hook entry in a child interpreter and classify its process starts (#9807)."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.hooks_runtime.policy import ObservedStart, classify_start

REPO_ROOT = Path(__file__).resolve().parents[2]
CHILD_MAIN = Path(__file__).resolve().parent / "child_main.py"
COLLECT_FORK_CHILDREN = "HOOK_RUNTIME_COLLECT_FORK_CHILDREN"


@dataclass(frozen=True)
class EntryReceipt:
    entry: str
    pairs_completed: int
    pairs_expected: int
    pair_errors: tuple[str, ...]
    violations: tuple[str, ...]
    events: tuple[ObservedStart, ...]
    canary: bool
    timed_out: bool
    driver_error: str

    @property
    def passed(self) -> bool:
        return (
            self.canary
            and not self.timed_out
            and not self.driver_error
            and not self.pair_errors
            and not self.violations
            and self.pairs_completed == self.pairs_expected
        )


def _clean_env(home: Path, tmp: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Isolated environment. Command variables and credentials are not copied."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
    }
    if os.environ.get(COLLECT_FORK_CHILDREN) == "0":
        env[COLLECT_FORK_CHILDREN] = "0"
    if extra:
        env.update(extra)
    return env


def _load_events(path: Path) -> tuple[ObservedStart, ...]:
    if not path.is_file():
        return ()
    events: list[ObservedStart] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("event") in {"os.putenv", "os.unsetenv"}:
            continue
        names = item.get("env_injection")
        events.append(
            ObservedStart(
                event=item["event"],
                pid=int(item["pid"]),
                parent_pid=int(item["parent_pid"]),
                pair_index=int(item["pair_index"]),
                executable=str(item.get("executable") or ""),
                argv=tuple(item.get("argv") or ()),
                explicit_env=None,
                inherited_dangerous={},
                shell_mediated=str(item.get("shell_mediated") or ""),
                env_injection=tuple(names) if isinstance(names, list) else None,
                explicit=bool(item.get("explicit")),
            )
        )
    return tuple(events)


def run_entry(
    entry: Path,
    commands: list[str],
    *,
    cwd: Path,
    timeout: float,
    extra_env: dict[str, str] | None = None,
    allow_argv: tuple[str, ...] | None = None,
) -> EntryReceipt:
    """Execute ``entry`` once per command. Missing canary, crash, or timeout fails the receipt."""
    home = cwd / "home"
    tmp = cwd / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    log_path = cwd / "audit.jsonl"
    commands_path = cwd / "commands.json"
    commands_path.write_text(json.dumps(commands), encoding="utf-8")
    env = _clean_env(home, tmp, extra_env)
    env["HOOK_RUNTIME_LOG"] = str(log_path)
    env["HOOK_RUNTIME_ENTRY"] = str(entry)
    env["HOOK_RUNTIME_COMMANDS"] = str(commands_path)
    if allow_argv is not None:
        env["HOOK_RUNTIME_ALLOW_ARGV"] = json.dumps(list(allow_argv))
    proc = subprocess.Popen(
        [sys.executable, str(CHILD_MAIN)],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate(timeout=5)
    events = _load_events(log_path)
    canary = any(event.argv == ("__audit_canary__", "intercept") for event in events)
    violations: list[str] = []
    for event in events:
        if event.argv == ("__audit_canary__", "intercept"):
            continue
        if event.event in {"os.fork", "os.forkpty"}:
            continue
        for reason in classify_start(event):
            shown = " ".join(event.argv) if event.argv else event.executable
            violations.append(f"{reason} :: {event.event} :: {shown}")
    pair_errors: tuple[str, ...] = ()
    completed = 0
    expected = len(commands)
    driver_error = ""
    if timed_out:
        driver_error = "timeout"
    elif proc.returncode not in {0, None}:
        tail = (stderr or b"").decode("utf-8", "replace")[-500:]
        driver_error = f"child-exit:{proc.returncode}:{tail}"
    else:
        text = (stdout or b"").decode("utf-8", "replace").strip()
        if not text:
            driver_error = "missing-receipt"
        else:
            try:
                summary = json.loads(text.splitlines()[-1])
            except json.JSONDecodeError as exc:
                driver_error = f"receipt:{exc}"
            else:
                completed = int(summary.get("completed") or 0)
                expected = int(summary.get("expected") or len(commands))
                pair_errors = tuple(summary.get("pair_errors") or ())
    if not canary and not driver_error:
        driver_error = "missing-canary"
    return EntryReceipt(
        entry=str(entry),
        pairs_completed=completed,
        pairs_expected=expected,
        pair_errors=pair_errors,
        violations=tuple(violations),
        events=events,
        canary=canary,
        timed_out=timed_out,
        driver_error=driver_error,
    )
