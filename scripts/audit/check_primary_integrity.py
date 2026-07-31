#!/usr/bin/env python3
"""Primary-checkout integrity watchdog: DETECT drift, repair ONLY when safe.

Follow-up to #5803 / #5389 / #5396. A dispatched worker ran git against the
PRIMARY checkout and left it detached (``checkout: moving from main to
FETCH_HEAD``) because it believed local ``origin/main`` was stale and the
primary was the nearest fresh copy. PR #5803 tried git-level prevention via a
``reference-transaction`` hook; cross-family review bypassed it with three live
commands, and a two-seat design panel (gpt-5.6-sol, agy) concluded git-layer
enforcement against a same-UID process is categorically impossible.

So this module is **detection + conservative repair**, not prevention:

- DETECT: HEAD not symbolically attached to ``refs/heads/main`` (detached or
  wrong branch), git operation in progress (merge/rebase/bisect/cherry-pick/
  revert state dirs, ``index.lock``), and working-tree cleanliness.
- RECORD: every detection appends a JSONL event with HEAD/main SHAs, a reflog
  excerpt, dirty detail, and the dispatches running at the time — enough to
  identify the likely offending actor.
- REPAIR only when ALL of: HEAD detached, tree demonstrably clean, no
  operation in progress, no dispatch running, and ``main`` has NOT moved since
  the drift was first recorded (baseline). Re-attach is ``git symbolic-ref``
  when HEAD already equals main's tip (zero working-tree effect) or a plain
  ``git checkout main`` on a clean tree (no committed or uncommitted state can
  be lost either way).
- NEVER touch a DIRTY tree, an in-progress operation, or a ``main`` that moved
  unexpectedly: ALERT and preserve evidence instead. A human may be working in
  the primary checkout — never blindly reset it (advisor directive).

Usage::

    python scripts/audit/check_primary_integrity.py          # check only
    python scripts/audit/check_primary_integrity.py --fix    # repair when safe

Wired read-only into: ``cmd_dispatch`` pre-dispatch gate, ``_run_worker``
post-exit sweep (both in ``scripts/delegate.py``), and the Monitor API
health-orient canary (``scripts/api/main.py``). ``--fix`` is an explicit
operator doctor action and is not called by those automatic paths.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Git commit hooks inject GIT_DIR / GIT_INDEX_FILE / etc. into the environment.
# Integrity checks must not inherit those or they inspect the outer repo, not
# the fixture / --repo path under test. Same scrub list as check_core_bare.
_GIT_REDIRECT_KEYS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
        "GIT_NAMESPACE",
    }
)

# Git state markers that mean an operation is in progress in the primary.
_OP_STATE_MARKERS = (
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_LOG",
    "rebase-merge",
    "rebase-apply",
)

_HEALTHY_BRANCHES = ("main", "master")


def _clean_git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT_KEYS}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        env=_clean_git_env(),
        timeout=60,
    )


def _resolve_main_root(repo: Path) -> Path:
    """Resolve the primary checkout root that owns the shared .git store."""
    try:
        from scripts.guardrails.worktree_containment import resolve_main_root
    except ImportError:  # path-flavoured import for test/script contexts
        # Invoked as a file path (python scripts/audit/...py): sys.path[0] is
        # the script's own directory, so neither `scripts.` nor `guardrails.`
        # resolves until the repo root is on sys.path.
        _repo_candidate = Path(__file__).resolve().parents[2]
        if str(_repo_candidate) not in sys.path:
            sys.path.insert(0, str(_repo_candidate))
        try:
            from scripts.guardrails.worktree_containment import resolve_main_root
        except ImportError:
            try:
                from guardrails.worktree_containment import resolve_main_root
            except ImportError:
                resolve_main_root = None  # type: ignore[assignment]
    if resolve_main_root is not None:
        try:
            return resolve_main_root(repo)
        except Exception:
            pass
    # Structural fallback. A plain checkout has a .git DIRECTORY; a linked
    # worktree has a .git FILE pointing at <primary>/.git/worktrees/<name> —
    # follow it so a worktree is never mistaken for the primary.
    git_path = repo / ".git"
    if git_path.is_file():
        try:
            first = git_path.read_text(encoding="utf-8").splitlines()[0]
            if first.startswith("gitdir:"):
                git_dir = Path(first.split(":", 1)[1].strip())
                if not git_dir.is_absolute():
                    git_dir = repo / git_dir
                if git_dir.parent.name == "worktrees" and git_dir.parent.parent.name == ".git":
                    return git_dir.parent.parent.parent
        except (IndexError, OSError):
            pass
    return repo


def _git_dir(main_root: Path) -> Path:
    proc = _git(main_root, "rev-parse", "--git-dir")
    if proc.returncode == 0:
        raw = Path(proc.stdout.strip())
        return raw if raw.is_absolute() else (main_root / raw).resolve()
    return main_root / ".git"


def _head_state(main_root: Path) -> dict[str, Any]:
    """HEAD attachment state: symbolic target (or None) plus the commit SHA."""
    sym = _git(main_root, "symbolic-ref", "-q", "HEAD")
    attached_to = sym.stdout.strip() if sym.returncode == 0 else None
    sha_proc = _git(main_root, "rev-parse", "HEAD")
    head_sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else None
    return {"attached_to": attached_to, "head_sha": head_sha}


def _branch_sha(main_root: Path, branch: str) -> str | None:
    proc = _git(main_root, "rev-parse", "--verify", f"refs/heads/{branch}")
    return proc.stdout.strip() if proc.returncode == 0 else None


def _op_in_progress(main_root: Path) -> list[str]:
    git_dir = _git_dir(main_root)
    found = [name for name in _OP_STATE_MARKERS if (git_dir / name).exists()]
    if (git_dir / "index.lock").exists():
        found.append("index.lock")
    return found


def _dirty_entries(main_root: Path) -> list[str] | None:
    """Porcelain dirty entries; None when cleanliness cannot be determined."""
    proc = _git(main_root, "status", "--porcelain=v1", "--untracked-files=all")
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _reflog_excerpt(main_root: Path, *, lines: int = 8) -> list[str]:
    proc = _git(main_root, "reflog", "-n", str(lines), "--date=iso")
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _running_dispatches(tasks_dir: Path | None) -> list[dict[str, Any]]:
    """Dispatch tasks whose state says running/spawning with a live PID."""
    if tasks_dir is None or not tasks_dir.is_dir():
        return []
    running: list[dict[str, Any]] = []
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            state = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if state.get("status") not in ("running", "spawning"):
            continue
        pid = state.get("pid")
        if pid and _pid_alive(int(pid)):
            running.append(
                {
                    "task_id": state.get("task_id") or path.stem,
                    "agent": state.get("agent"),
                    "pid": pid,
                    "status": state.get("status"),
                }
            )
    return running


def _state_dir(main_root: Path, state_dir: Path | None) -> Path:
    # data/telemetry/ is gitignored local runtime state (never committed).
    return state_dir or (main_root / "data" / "telemetry" / "primary-integrity")


def _load_state(state_dir: Path) -> dict[str, Any]:
    path = state_dir / "state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state_dir: Path, state: dict[str, Any]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp = state_dir / f"state.json.tmp.{os.getpid()}"
    tmp.write_text(json.dumps(state, indent=2, default=str))
    os.replace(tmp, state_dir / "state.json")


def _append_event(state_dir: Path, event: str, **fields: Any) -> None:
    payload = {"ts": datetime.now(UTC).isoformat(), "event": event, **fields}
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        with open(state_dir / "events.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    except OSError as exc:
        print(
            f"[primary-integrity] WARNING: failed to log event: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )


def _repair(main_root: Path, *, head_sha: str | None, main_sha: str) -> tuple[bool, str]:
    """Re-attach HEAD to main. Caller guarantees clean tree + idle + no dispatch."""
    if head_sha == main_sha:
        # HEAD already sits on main's tip: a pure symbolic-ref flip with ZERO
        # working-tree effect — the safest possible repair.
        proc = _git(main_root, "symbolic-ref", "HEAD", "refs/heads/main")
        if proc.returncode != 0:
            return False, f"git symbolic-ref HEAD refs/heads/main failed: {proc.stderr.strip()}"
        return True, f"re-attached HEAD to main via symbolic-ref (unchanged tip {main_sha[:12]})"
    # Clean tree at a different commit: checkout cannot lose committed state
    # and refuses rather than clobbering conflicting untracked files.
    proc = _git(main_root, "checkout", "main")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, f"git checkout main failed: {detail}"
    return True, f"checked out main from detached {str(head_sha)[:12]} (clean tree, no data loss)"


def check_primary_integrity(
    repo: Path,
    *,
    fix: bool = False,
    tasks_dir: Path | None = None,
    state_dir: Path | None = None,
) -> tuple[bool, str]:
    """Check (and conservatively repair) primary-checkout attachment to main.

    Returns ``(ok, message)``. ``ok`` is True when the primary is on main (or
    master), or when drift was repaired. ``ok`` is False for unrepaired drift —
    dirty tree, operation in progress, running dispatch, unexpected main
    movement, or ``fix`` not requested. Never mutates anything except the
    watchdog's own state/log unless the full repair gate passes.
    """
    main_root = _resolve_main_root(Path(repo))
    sdir = _state_dir(main_root, state_dir)
    state = _load_state(sdir)

    head = _head_state(main_root)
    attached_to = head["attached_to"]
    head_sha = head["head_sha"]

    if attached_to is not None:
        branch = attached_to.removeprefix("refs/heads/")
        if not branch:
            # rc 0 with empty stdout is not something real git produces (it
            # shows up when subprocess.run is stubbed in tests). No positive
            # evidence of drift — fail open rather than grounding the fleet
            # on an inconclusive read.
            return True, "HEAD symbolic-ref inconclusive (empty) — no drift evidence"
        if branch in _HEALTHY_BRANCHES:
            if state.get("drift") is not None:
                state["drift"] = None
            state["healthy_main_sha"] = _branch_sha(main_root, branch)
            _save_state(sdir, state)
            return True, f"primary on {branch} ({main_root})"
        # Wrong branch: not the detached-HEAD case this watchdog repairs.
        _append_event(
            sdir,
            "primary_drift_alert",
            reason="wrong_branch",
            branch=branch,
            head_sha=head_sha,
            main_root=str(main_root),
            reflog=_reflog_excerpt(main_root),
        )
        return False, (
            f"ALERT: primary checkout is on branch {branch!r}, not main — "
            "refusing to switch a human checkout; inspect and `git checkout main` manually"
        )

    # --- HEAD is detached: gather full evidence BEFORE any decision. ---
    main_sha = _branch_sha(main_root, "main")
    ops = _op_in_progress(main_root)
    dirty = _dirty_entries(main_root)
    running = _running_dispatches(tasks_dir)
    evidence = {
        "head_sha": head_sha,
        "main_sha": main_sha,
        "ops_in_progress": ops,
        "dirty_entries": dirty,
        "running_dispatches": running,
        "reflog": _reflog_excerpt(main_root),
        "main_root": str(main_root),
    }
    _append_event(sdir, "primary_drift_detected", **evidence)

    def _alert(reason: str) -> tuple[bool, str]:
        _append_event(sdir, "primary_drift_alert", reason=reason, **evidence)
        return False, (
            f"ALERT: primary checkout DETACHED at {str(head_sha)[:12]} — {reason}. "
            "NOT touched; evidence preserved under "
            f"{sdir}/events.jsonl. A human may be working there — inspect manually."
        )

    # Tree dirty (or cleanliness unknown): never touch a human checkout.
    if dirty is None:
        return _alert("working-tree cleanliness could not be determined")
    if dirty:
        return _alert(f"working tree is DIRTY ({len(dirty)} entr{'y' if len(dirty) == 1 else 'ies'})")
    # Operation in progress: merge/rebase/bisect/cherry-pick/revert/index.lock.
    if ops:
        return _alert(f"git operation in progress ({', '.join(ops)})")
    # A running dispatch may legitimately be mid-operation on the shared refs;
    # defer repair rather than racing it. Never kill the running dispatch.
    if running:
        ids = ", ".join(str(d["task_id"]) for d in running)
        return _alert(f"dispatch(es) still running ({ids}) — repair deferred")
    # main must exist to re-attach to.
    if main_sha is None:
        return _alert("refs/heads/main does not exist")

    # Main-movement baseline: the first sighting of a drift episode records
    # where main was. Repair is allowed only once main has been observed
    # STABLE across two checks — if it moved while HEAD was detached, that is
    # unexpected primary-side activity: alert and preserve, do not touch.
    drift = state.get("drift")
    if not drift or drift.get("head_sha") != head_sha:
        state["drift"] = {
            "first_seen": datetime.now(UTC).isoformat(),
            "head_sha": head_sha,
            "main_sha": main_sha,
        }
        _save_state(sdir, state)
        return _alert("drift baseline recorded; awaiting a stable-main confirmation pass")
    if drift.get("main_sha") != main_sha:
        state["drift"] = {
            "first_seen": datetime.now(UTC).isoformat(),
            "head_sha": head_sha,
            "main_sha": main_sha,
        }
        _save_state(sdir, state)
        return _alert(
            f"main moved unexpectedly while detached "
            f"({str(drift.get('main_sha'))[:12]} → {main_sha[:12]})"
        )

    if not fix:
        return False, (
            f"primary DETACHED at {str(head_sha)[:12]} (clean, idle, main stable) — "
            "repairable; re-run with --fix to re-attach HEAD to main"
        )

    ok, detail = _repair(main_root, head_sha=head_sha, main_sha=main_sha)
    if not ok:
        return _alert(f"repair attempted but failed safely: {detail}")
    state["drift"] = None
    state["healthy_main_sha"] = main_sha
    _save_state(sdir, state)
    _append_event(sdir, "primary_drift_repaired", detail=detail, **evidence)
    return True, f"repaired: {detail}"


def worktree_origin_points_at_remote(worktree: Path) -> tuple[bool, str]:
    """Verify a dispatch worktree's ``origin`` is the canonical REMOTE, not a
    local filesystem path to the primary checkout (#5803 root cause: the
    worker treated the primary as the nearest fresh copy of main).

    Returns ``(ok, message)``. ``ok`` is False when origin is unset or is a
    local path — in which case fetches silently bind to the primary and the
    worker has every reason to go poke it.
    """
    proc = _git(Path(worktree), "config", "--get", "remote.origin.url")
    url = proc.stdout.strip() if proc.returncode == 0 else ""
    if not url:
        return False, "remote.origin.url is not set — fetches cannot reach the canonical remote"
    # Local path forms: /abs/path, ../rel/path, file:// URLs.
    if url.startswith(("/", ".", "file://")) or ("://" not in url and "@" not in url):
        return False, (
            f"remote.origin.url resolves to a LOCAL path ({url!r}) — fetches would bind to "
            "the primary checkout instead of the canonical remote; point it at "
            "github.com:learn-ukrainian/learn-ukrainian.github.io"
        )
    return True, f"origin → {url}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect (and conservatively repair) primary-checkout drift (#5803 follow-up).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="re-attach HEAD to main ONLY when detached + clean + idle + no dispatch + stable main",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress the OK message (alerts and repairs still print)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repo path to check (default: this project root)",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help="dispatch tasks dir for the running-dispatch gate (default: <root>/batch_state/tasks)",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="watchdog state/log dir (default: <main_root>/data/telemetry/primary-integrity)",
    )
    args = parser.parse_args(argv)

    tasks_dir = args.tasks_dir
    if tasks_dir is None:
        try:
            tasks_dir = _resolve_main_root(args.repo) / "batch_state" / "tasks"
        except Exception:
            tasks_dir = None

    ok, message = check_primary_integrity(
        args.repo,
        fix=args.fix,
        tasks_dir=tasks_dir,
        state_dir=args.state_dir,
    )
    if not ok:
        print(f"❌ {message}", file=sys.stderr)
        return 1
    if "repaired" in message:
        print(f"⚠️  {message}", file=sys.stderr)
    elif not args.quiet:
        print(f"✅ {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
