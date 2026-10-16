"""Run one Entire capture command only after the private-route guard passes.

Every checkpoint-producing entry point (agent lifecycle hooks and Entire's git
hook wrappers) calls ``scripts/entire/capture_guard.sh`` instead of ``entire``.
Before Entire runs, the guard proves, fail-closed and in this order:

1. the checked-in routing allowlist is intact (``validate_checkpoint_routing``);
2. ``entire version`` prints exactly ``Entire CLI <accepted version>`` first;
3. ``entire status --json`` reports the dedicated private checkpoint route.

A failed proof is a privacy refusal: one stderr line, Entire is never called,
exit 0, so the host session or git command continues without capture. An
Entire failure or hang after the proof is an outage: also exit 0, because
capture is optional and never decides a commit or push. ``private_mode_preflight``
imports the same version and route predicates, so recall and capture agree.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.entire.validate_checkpoint_routing import validate

ACCEPTED_VERSION = "0.11.5"
# `entire status --json` names the route checkpoints take; "dedicated" means the
# configured checkpoint_remote, not a git remote of this checkout.
DEDICATED_ROUTE = "dedicated"
DEFAULT_BUDGET_SECONDS = 110.0
VERSION_TIMEOUT_SECONDS = 10.0
STATUS_TIMEOUT_SECONDS = 20.0
RUNBOOK = "docs/runbooks/entire-cli-upgrade.md"

Runner = Callable[[Sequence[str], Path, float], subprocess.CompletedProcess[str]]


def version_accepted(result: subprocess.CompletedProcess[str]) -> bool:
    """True only for the exact accepted first line; a substring would admit 0.11.50."""
    first_line = next(iter((result.stdout or "").splitlines()), "").strip()
    return result.returncode == 0 and first_line == f"Entire CLI {ACCEPTED_VERSION}"


def route_private(status: Any, checkpoint_repo: str) -> bool:
    """True when ``entire status --json`` reports the dedicated private route."""
    return bool(
        isinstance(status, dict)
        and status.get("checkpoint_sync_remote_source") == DEDICATED_ROUTE
        and status.get("checkpoint_sync_remote") == checkpoint_repo
        and not status.get("checkpoint_remote_ignored")
        and not status.get("checkpoint_sync_error")
    )


def _kill_group(proc: subprocess.Popen[Any]) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def run_bounded(argv: Sequence[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    """Run a probe with no stdin; on timeout kill its whole process group."""
    proc = subprocess.Popen(
        list(argv),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        process_group=0,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        raise
    return subprocess.CompletedProcess(list(argv), proc.returncode, stdout, stderr)


def refusal(root: Path, entire: str, deadline: float, *, runner: Runner = run_bounded) -> str | None:
    """Return why capture must not run, or None when every proof passed."""
    if validate(root) is not None:
        return "routing_allowlist_failed"
    settings = json.loads((root / ".entire/settings.json").read_text(encoding="utf-8"))
    checkpoint_repo = settings["strategy_options"]["checkpoint_remote"]["repo"]
    try:
        remaining = deadline - time.monotonic()
        version = runner((entire, "version"), root, min(VERSION_TIMEOUT_SECONDS, remaining))
        if not version_accepted(version):
            return "cli_version_not_accepted"
        remaining = deadline - time.monotonic()
        status = runner((entire, "status", "--json"), root, min(STATUS_TIMEOUT_SECONDS, remaining))
    except subprocess.TimeoutExpired:
        return "guard_probe_timeout"
    except (OSError, ValueError):
        return "guard_probe_failed"
    try:
        payload = json.loads(status.stdout) if status.returncode == 0 else None
    except (TypeError, json.JSONDecodeError):
        payload = None
    if not route_private(payload, checkpoint_repo):
        return "checkpoint_route_not_private"
    return None


def _stop(proc: subprocess.Popen[Any]) -> None:
    """Kill the capture and every descendant, which may hold the host's stdout open."""
    import psutil  # Lazy: only a timed-out capture pays the import.

    try:
        tree = [*psutil.Process(proc.pid).children(recursive=True), psutil.Process(proc.pid)]
    except psutil.Error:
        tree = []
    for member in tree:
        with contextlib.suppress(psutil.Error):
            member.kill()
    psutil.wait_procs(tree, timeout=5)
    with contextlib.suppress(ProcessLookupError):
        proc.kill()
    proc.wait()


def capture(argv: Sequence[str], timeout: float) -> int | None:
    """Run Entire with the host's stdin/stdout/stderr; None means it timed out.

    Capture stays in the caller's process group: Entire's prepare-commit-msg may
    prompt on /dev/tty, which a background process group cannot read.
    """
    proc = subprocess.Popen(list(argv))
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _stop(proc)
        return None
    except BaseException:
        _stop(proc)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/entire/capture_guard.sh",
        description=(
            "Run an Entire capture command only when the accepted CLI version and the\n"
            "private checkpoint route are proven; otherwise skip capture. Always exits 0."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: scripts/entire/capture_guard.sh --budget 25 hooks claude-code user-prompt-submit\n"
            "Outputs: Entire's own output when capture runs; one '[entire]' stderr line when\n"
            "capture is refused or fails. Writes nothing itself.\n"
            "Exit codes: 0 always (capture is optional and never blocks the host or git).\n"
            f"Related: {RUNBOOK}; scripts/entire/private_mode_preflight.py; #10846."
        ),
    )
    parser.add_argument(
        "--budget", type=float, default=DEFAULT_BUDGET_SECONDS,
        help=f"Total seconds for probes plus capture (default: {DEFAULT_BUDGET_SECONDS:g}; example: 25).",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Entire arguments, e.g. hooks git pre-push origin.")
    args = parser.parse_args(argv)
    if not args.command:
        print("[entire] capture refused (no_command): no checkpoint written", file=sys.stderr)
        return 0
    deadline = time.monotonic() + max(args.budget, 1.0)
    entire = shutil.which("entire")
    if entire is None:
        return 0
    reason = refusal(ROOT, entire, deadline)
    if reason is not None:
        print(f"[entire] capture refused ({reason}): no checkpoint written; see {RUNBOOK}", file=sys.stderr)
        return 0
    remaining = max(deadline - time.monotonic(), 1.0)
    try:
        code = capture((entire, *args.command), remaining)
    except OSError as exc:
        print(f"[entire] capture failed ({type(exc).__name__}); continuing without capture", file=sys.stderr)
        return 0
    if code is None:
        print(f"[entire] capture timed out after {remaining:.0f}s; continuing without capture", file=sys.stderr)
    elif code != 0:
        print(f"[entire] capture failed (exit {code}); continuing without capture", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
