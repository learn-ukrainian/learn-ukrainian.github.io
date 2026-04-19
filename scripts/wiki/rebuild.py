#!/usr/bin/env python3
"""Wiki rebuild orchestrator — phased, resumable, stop/start-friendly.

Manages the full wiki rebuild per `docs/wiki-rebuild-plan.md` without
requiring the user to babysit terminal windows. State persists across
Ctrl-C, laptop sleep, reboot — next `run` picks up exactly where it
stopped.

### Usage

    # Start (or resume) the rebuild
    .venv/bin/python scripts/wiki/rebuild.py run

    # Show progress (no work done)
    .venv/bin/python scripts/wiki/rebuild.py status

    # Preview what would run next
    .venv/bin/python scripts/wiki/rebuild.py dry-run

    # Stop after N tracks (for "let me run for an hour")
    .venv/bin/python scripts/wiki/rebuild.py run --max-tracks 2

    # Jump to a specific phase (marks earlier phases as skipped)
    .venv/bin/python scripts/wiki/rebuild.py run --from-phase 4

    # Skip a problematic track permanently
    .venv/bin/python scripts/wiki/rebuild.py skip --track lit-fantastika

    # Start over (prompts for confirmation)
    .venv/bin/python scripts/wiki/rebuild.py reset

### How resume works

State is persisted to `wiki/.state/rebuild-progress.json` BEFORE each
track starts. On Ctrl-C mid-track:

1. SIGINT propagates to the compile subprocess (same process group)
2. `compile.py` finishes the current article cleanly and exits
3. This orchestrator marks the track as "paused" and writes state
4. Next `run` invocation: finds the paused track, re-invokes
   `compile.py` on it. `compile.py::is_compiled` skips already-done
   articles within the track. Nothing is re-done.

### Shadow-mode guarantee

Every track is invoked with `--dim-review` (shadow mode by default).
Reports land in `wiki/.reviews/<domain>/<slug>.json`. Never blocks the
pipeline. See `docs/design/dimensional-review.md` §8.
"""
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Repo-root sys.path shim
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from wiki.config import WIKI_STATE_DIR

# ── Rebuild phases (source of truth) ──────────────────────────────

#: Ordered list of phases. Each phase has a list of (track, slug) tasks.
#: slug=None means "all articles in this track" (`--all` flag).
#: slug="<name>" means "just this one article" (`--slug <name>`).
PHASES: list[dict[str, Any]] = [
    {
        "num": 0,
        "name": "Smoke test — 1 article to prove pipeline",
        "tasks": [("a1", "sounds-letters-and-hello")],
    },
    {
        "num": 1,
        "name": "A1 full track — pedagogical briefs",
        "tasks": [("a1", None)],
    },
    {
        "num": 2,
        "name": "A2 → B1 → B2 — grammar briefs",
        "tasks": [("a2", None), ("b1", None), ("b2", None)],
    },
    {
        "num": 3,
        "name": "C1 → C2 — academic briefs",
        "tasks": [("c1", None), ("c2", None)],
    },
    {
        "num": 4,
        "name": "Seminars (history-rich)",
        "tasks": [("hist", None), ("bio", None), ("istorio", None)],
    },
    {
        "num": 5,
        "name": "LIT seminars",
        "tasks": [
            ("lit", None),
            ("lit-essay", None),
            ("lit-war", None),
            ("lit-hist-fic", None),
            ("lit-youth", None),
            ("lit-fantastika", None),
            ("lit-humor", None),
            ("lit-drama", None),
        ],
    },
    {
        "num": 6,
        "name": "OES + RUTH — specialized linguistics",
        "tasks": [("oes", None), ("ruth", None)],
    },
]

#: File where orchestrator state lives. Lives alongside wiki build log.
_STATE_FILE = WIKI_STATE_DIR / "rebuild-progress.json"

#: Status values a task can hold.
_STATUS_PENDING = "pending"
_STATUS_RUNNING = "running"
_STATUS_DONE = "done"
_STATUS_PAUSED = "paused"
_STATUS_SKIPPED = "skipped"
_STATUS_FAILED = "failed"

# ── State dataclasses ─────────────────────────────────────────────


@dataclass
class TaskState:
    """Per (phase, track, slug) record."""

    phase: int
    track: str
    slug: str | None  # None = all articles
    status: str = _STATUS_PENDING
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float | None = None
    returncode: int | None = None
    attempts: int = 0

    @property
    def key(self) -> tuple[int, str, str | None]:
        return (self.phase, self.track, self.slug)

    def display(self) -> str:
        tgt = f"{self.track}" + (f"/{self.slug}" if self.slug else " (all)")
        return f"Phase {self.phase} · {tgt}"


@dataclass
class RebuildState:
    started_at: str = ""
    last_resumed_at: str = ""
    tasks: list[TaskState] = field(default_factory=list)

    def to_jsonable(self) -> dict:
        return {
            "started_at": self.started_at,
            "last_resumed_at": self.last_resumed_at,
            "tasks": [asdict(t) for t in self.tasks],
        }

    @classmethod
    def from_jsonable(cls, data: dict) -> RebuildState:
        return cls(
            started_at=data.get("started_at", ""),
            last_resumed_at=data.get("last_resumed_at", ""),
            tasks=[TaskState(**t) for t in data.get("tasks", [])],
        )


# ── State persistence ─────────────────────────────────────────────


def _ensure_state_dir() -> None:
    WIKI_STATE_DIR.mkdir(parents=True, exist_ok=True)


def _load_state() -> RebuildState:
    _ensure_state_dir()
    if not _STATE_FILE.exists():
        return _initial_state()
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        state = RebuildState.from_jsonable(data)
        # Ensure schema is up-to-date: if new phases/tracks were added
        # to PHASES since the state was last saved, graft them in as
        # pending. Never drop existing task records.
        _sync_state_with_phases(state)
        return state
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        print(
            f"⚠️  Could not load state from {_STATE_FILE}: {exc}. "
            "Starting fresh.", file=sys.stderr,
        )
        return _initial_state()


def _save_state(state: RebuildState) -> None:
    _ensure_state_dir()
    _STATE_FILE.write_text(
        json.dumps(state.to_jsonable(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _initial_state() -> RebuildState:
    now = datetime.now(UTC).isoformat(timespec="seconds")
    state = RebuildState(started_at=now, last_resumed_at=now)
    for phase in PHASES:
        for track, slug in phase["tasks"]:
            state.tasks.append(TaskState(
                phase=phase["num"], track=track, slug=slug,
            ))
    return state


def _sync_state_with_phases(state: RebuildState) -> None:
    """Add any (phase, track, slug) tasks that exist in PHASES but not
    in state — keeps old state compatible with future phase changes."""
    existing_keys = {t.key for t in state.tasks}
    for phase in PHASES:
        for track, slug in phase["tasks"]:
            key = (phase["num"], track, slug)
            if key not in existing_keys:
                state.tasks.append(TaskState(
                    phase=phase["num"], track=track, slug=slug,
                ))


# ── Next-task lookup ──────────────────────────────────────────────


def _next_task(state: RebuildState) -> TaskState | None:
    """Return the first task not DONE / SKIPPED — includes PAUSED / FAILED
    for retry. Ordering matches PHASES list."""
    for task in state.tasks:
        if task.status in (_STATUS_DONE, _STATUS_SKIPPED):
            continue
        return task
    return None


# ── Signal handling ───────────────────────────────────────────────

_interrupt_requested = False


def _sigint_handler(signum, frame) -> None:
    """Flag interrupt; let the subprocess finish its current article.

    SIGINT is ALSO received by the subprocess because it's in our
    process group (no `start_new_session`). `compile.py` handles
    KeyboardInterrupt gracefully: finishes the current article, then
    exits. We wait for it, save state, and exit.
    """
    global _interrupt_requested
    _interrupt_requested = True
    # Re-install default handler so a second Ctrl-C kills us hard
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    print("\n⚠️  Interrupt received. Finishing current article cleanly; "
          "Ctrl-C again to force-kill.", file=sys.stderr)


# ── Subprocess invocation ─────────────────────────────────────────


def _run_compile(task: TaskState, *, dry_run: bool = False) -> int:
    """Invoke `compile.py --track X [--slug Y|--all] --dim-review`.

    Returns the subprocess exit code. Kills cleanly on SIGINT.
    `compile.py` handles per-article resume via `is_compiled()`, so
    re-invoking on the same track is idempotent — already-compiled
    articles are skipped.
    """
    cmd = [
        ".venv/bin/python", "scripts/wiki/compile.py",
        "--track", task.track,
        "--dim-review",
    ]
    if task.slug:
        cmd.extend(["--slug", task.slug])
    else:
        cmd.append("--all")

    if dry_run:
        print(f"  [dry-run] would execute: {' '.join(cmd)}")
        return 0

    print(f"\n▶️  {task.display()}")
    print(f"   $ {' '.join(cmd)}\n")

    # Parent keeps SIGINT handler; subprocess inherits the signal mask
    # (no start_new_session), so Ctrl-C hits both. compile.py's
    # KeyboardInterrupt handler finishes current article and exits.
    try:
        proc = subprocess.run(cmd, cwd=_REPO_ROOT, check=False)
        return proc.returncode
    except KeyboardInterrupt:
        # Shouldn't reach here — subprocess.run propagates but we
        # catch it defensively.
        return 130


# ── Runner ────────────────────────────────────────────────────────


def _run(state: RebuildState, *,
         max_tracks: int | None = None,
         from_phase: int | None = None,
         dry_run: bool = False) -> int:
    """Main run loop: pick next task, execute, update state, repeat."""
    global _interrupt_requested

    # Jump-to-phase: mark all prior-phase pending tasks as skipped
    if from_phase is not None:
        for task in state.tasks:
            if task.phase < from_phase and task.status == _STATUS_PENDING:
                task.status = _STATUS_SKIPPED
                task.finished_at = datetime.now(UTC).isoformat(timespec="seconds")
        _save_state(state)

    state.last_resumed_at = datetime.now(UTC).isoformat(timespec="seconds")
    _save_state(state)

    signal.signal(signal.SIGINT, _sigint_handler)

    tracks_run = 0
    while True:
        if _interrupt_requested:
            print("\n⏸   Paused by user. Run again to resume.", file=sys.stderr)
            return 130

        task = _next_task(state)
        if task is None:
            print("\n🎉 All phases complete.")
            return 0

        if max_tracks is not None and tracks_run >= max_tracks:
            print(f"\n⏸   Hit --max-tracks={max_tracks}. Resume later with `run`.")
            return 0

        # Mark task running + persist before spawning
        task.status = _STATUS_RUNNING
        task.started_at = datetime.now(UTC).isoformat(timespec="seconds")
        task.attempts += 1
        _save_state(state)

        t0 = time.monotonic()
        rc = _run_compile(task, dry_run=dry_run)
        task.duration_s = round(time.monotonic() - t0, 1)
        task.returncode = rc
        task.finished_at = datetime.now(UTC).isoformat(timespec="seconds")

        if _interrupt_requested:
            task.status = _STATUS_PAUSED
            _save_state(state)
            print(f"\n⏸   Paused mid-task: {task.display()} "
                  f"(rc={rc}, {task.duration_s}s)", file=sys.stderr)
            print("    Re-run to resume — compile.py will skip already-done articles.",
                  file=sys.stderr)
            return 130

        if rc == 0:
            task.status = _STATUS_DONE
            print(f"✅ {task.display()} — done in {task.duration_s}s")
        else:
            task.status = _STATUS_FAILED
            print(f"❌ {task.display()} — rc={rc}, {task.duration_s}s",
                  file=sys.stderr)
            _save_state(state)
            print("   Aborting. Fix the issue, then `run` to retry this task, "
                  "or `skip --track X` to skip it.", file=sys.stderr)
            return rc

        _save_state(state)
        tracks_run += 1


# ── Status / dry-run display ──────────────────────────────────────


_STATUS_ICONS = {
    _STATUS_PENDING: "⏳",
    _STATUS_RUNNING: "🔄",
    _STATUS_DONE: "✅",
    _STATUS_PAUSED: "⏸ ",
    _STATUS_SKIPPED: "⏭️ ",
    _STATUS_FAILED: "❌",
}


def _status(state: RebuildState) -> None:
    print(f"\nWiki rebuild progress — started {state.started_at}")
    if state.last_resumed_at and state.last_resumed_at != state.started_at:
        print(f"                        last resumed {state.last_resumed_at}")
    print()

    by_phase: dict[int, list[TaskState]] = {}
    for task in state.tasks:
        by_phase.setdefault(task.phase, []).append(task)

    total_done = total = 0
    for phase in PHASES:
        pn = phase["num"]
        tasks = by_phase.get(pn, [])
        done_count = sum(1 for t in tasks if t.status == _STATUS_DONE)
        total_count = len(tasks)
        total_done += done_count
        total += total_count
        header_icon = (
            "✅" if done_count == total_count > 0
            else "🔄" if any(t.status == _STATUS_RUNNING for t in tasks)
            else "⏳"
        )
        print(f"{header_icon} Phase {pn} — {phase['name']} "
              f"[{done_count}/{total_count}]")
        for task in tasks:
            icon = _STATUS_ICONS.get(task.status, "?")
            duration = f" ({task.duration_s}s)" if task.duration_s else ""
            print(f"     {icon} {task.track}"
                  + (f"/{task.slug}" if task.slug else "")
                  + f" — {task.status}{duration}")

    print(f"\nOverall: {total_done}/{total} tasks done.")


# ── Subcommands ───────────────────────────────────────────────────


def _cmd_run(args: argparse.Namespace) -> int:
    state = _load_state()
    return _run(
        state,
        max_tracks=args.max_tracks,
        from_phase=args.from_phase,
        dry_run=False,
    )


def _cmd_status(args: argparse.Namespace) -> int:
    del args
    state = _load_state()
    _status(state)
    return 0


def _cmd_dry_run(args: argparse.Namespace) -> int:
    del args
    state = _load_state()
    print("\nTasks that would run next (in order):\n")
    remaining = [
        t for t in state.tasks
        if t.status not in (_STATUS_DONE, _STATUS_SKIPPED)
    ]
    if not remaining:
        print("  (none — all tasks are done or skipped)")
        return 0
    for task in remaining:
        print(f"  {_STATUS_ICONS[task.status]} {task.display()} "
              f"(status={task.status})")
    return 0


def _cmd_skip(args: argparse.Namespace) -> int:
    state = _load_state()
    hits = [
        t for t in state.tasks
        if t.track == args.track
        and (args.slug is None or t.slug == args.slug)
        and t.status not in (_STATUS_DONE, _STATUS_SKIPPED)
    ]
    if not hits:
        print(f"No active task matches track={args.track!r} "
              f"slug={args.slug!r}.", file=sys.stderr)
        return 1
    for task in hits:
        task.status = _STATUS_SKIPPED
        task.finished_at = datetime.now(UTC).isoformat(timespec="seconds")
        print(f"⏭️  Skipped: {task.display()}")
    _save_state(state)
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        answer = input(
            f"Reset will delete {_STATE_FILE} and all progress records. "
            "Type 'yes' to confirm: "
        ).strip().lower()
        if answer != "yes":
            print("Aborted.")
            return 1
    if _STATE_FILE.exists():
        _STATE_FILE.unlink()
        print(f"🗑  Deleted {_STATE_FILE}.")
    else:
        print(f"(no state file to delete at {_STATE_FILE})")
    return 0


# ── CLI ──────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__ or "",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Start or resume the rebuild")
    p_run.add_argument("--max-tracks", type=int, default=None,
                       help="Stop after this many tracks complete")
    p_run.add_argument("--from-phase", type=int, default=None,
                       help="Skip to this phase (marks earlier phases as skipped)")
    p_run.set_defaults(func=_cmd_run)

    p_status = sub.add_parser("status", help="Show progress")
    p_status.set_defaults(func=_cmd_status)

    p_dry = sub.add_parser("dry-run", help="Preview what would run next")
    p_dry.set_defaults(func=_cmd_dry_run)

    p_skip = sub.add_parser("skip", help="Mark a task as permanently skipped")
    p_skip.add_argument("--track", required=True)
    p_skip.add_argument("--slug", default=None)
    p_skip.set_defaults(func=_cmd_skip)

    p_reset = sub.add_parser("reset", help="Delete state and start over")
    p_reset.add_argument("--yes", action="store_true",
                         help="Skip confirmation prompt")
    p_reset.set_defaults(func=_cmd_reset)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
