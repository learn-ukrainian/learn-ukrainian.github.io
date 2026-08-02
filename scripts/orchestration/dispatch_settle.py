"""Deterministic settle helpers for dispatch task handoff (no LLM).

After Luna/Codex workers finish (or die with SIGKILL), the orchestrator needs a
cheap, repeatable way to:

* mark zombie task JSON when the recorded PID is dead
* release write-ownership claims for inactive tasks
* report branch/PR state for a task worktree
* optionally push and open a PR when commits exist and no PR is open

Formal cross-family review and auto-merge remain orchestrator-owned.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.guardrails.delegate_ownership import OwnershipLedger, default_ledger_path


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def default_task_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or repo_root_from_file()
    return root / "batch_state" / "tasks"


def _pid_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=check,
    )


def _load_task(task_dir: Path, task_id: str) -> dict[str, Any]:
    path = task_dir / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"task state missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"task state must be object: {path}")
    return data


def _save_task(task_dir: Path, task_id: str, data: dict[str, Any]) -> Path:
    path = task_dir / f"{task_id}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass
class SettleReport:
    task_id: str
    status: str | None
    pid: int | None
    pid_alive: bool
    worktree_path: str | None
    branch: str | None
    commits_ahead: int | None
    dirty: bool | None
    pr_url: str | None
    pr_number: int | None
    actions: list[str]
    closeout: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def heal_zombie_task(
    task_dir: Path,
    task_id: str,
    *,
    ledger: OwnershipLedger | None = None,
) -> list[str]:
    """If status is running but PID is dead, mark failed and release claims."""
    actions: list[str] = []
    data = _load_task(task_dir, task_id)
    status = data.get("status")
    raw_pid = data.get("pid")
    pid: int | None
    if isinstance(raw_pid, int):
        pid = raw_pid
    elif isinstance(raw_pid, str) and raw_pid.isdigit():
        pid = int(raw_pid)
    else:
        pid = None

    if status == "running" and not _pid_alive(pid):
        data["status"] = "failed"
        data["exit_code"] = data.get("exit_code") if data.get("exit_code") is not None else -9
        data["returncode"] = data.get("returncode") if data.get("returncode") is not None else -9
        data["last_error"] = (
            data.get("last_error")
            or "dispatch_settle: recorded PID is dead while status=running"
        )
        _save_task(task_dir, task_id, data)
        actions.append("marked_failed_zombie_running")
        if ledger is not None:
            ledger.release(task_id)
            actions.append("released_ownership_claims")
    return actions


def release_inactive_claims(ledger: OwnershipLedger | None = None) -> list[str]:
    """Release write claims for inactive tasks without extending the ownership API surface.

    Uses the ledger's existing reconcile path (already invoked on admit) so settle
    loops can free dead PIDs without a rail-gated ownership module edit.
    """
    own = ledger or OwnershipLedger(default_ledger_path())
    with own._connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        released = own._reconcile_stale(conn)
        conn.execute("COMMIT")
    return released


def _git_info(worktree: Path) -> tuple[str | None, int | None, bool | None]:
    if not worktree.is_dir():
        return None, None, None
    branch_p = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree)
    branch = branch_p.stdout.strip() if branch_p.returncode == 0 else None
    ahead_p = _run(
        ["git", "rev-list", "--count", "origin/main..HEAD"],
        cwd=worktree,
    )
    ahead: int | None
    if ahead_p.returncode == 0:
        try:
            ahead = int(ahead_p.stdout.strip() or "0")
        except ValueError:
            ahead = None
    else:
        ahead = None
    dirty_p = _run(["git", "status", "--porcelain"], cwd=worktree)
    dirty = None
    if dirty_p.returncode == 0:
        lines = [
            line
            for line in dirty_p.stdout.splitlines()
            if line.strip() and not line.endswith(" .venv") and line != "?? .venv"
        ]
        dirty = bool(lines)
    return branch, ahead, dirty


def _find_pr(branch: str | None, cwd: Path) -> tuple[str | None, int | None]:
    if not branch:
        return None, None
    proc = _run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--json",
            "number,url,state",
            "--jq",
            ".[0] // empty",
        ],
        cwd=cwd,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None, None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(data, dict):
        return None, None
    url = data.get("url") if isinstance(data.get("url"), str) else None
    number = data.get("number") if isinstance(data.get("number"), int) else None
    return url, number


def push_and_maybe_open_pr(
    worktree: Path,
    branch: str,
    *,
    open_pr: bool,
    title: str | None,
    body: str | None,
) -> list[str]:
    actions: list[str] = []
    push = _run(["git", "push", "-u", "origin", "HEAD"], cwd=worktree)
    if push.returncode != 0:
        actions.append(f"push_failed:{(push.stderr or push.stdout)[:300]}")
        return actions
    actions.append("pushed")
    if not open_pr:
        return actions
    url, _number = _find_pr(branch, worktree)
    if url:
        actions.append(f"pr_exists:{url}")
        return actions
    pr_title = title or f"chore(dispatch): settle {branch}"
    pr_body = body or (
        "Auto-opened by `python -m scripts.orchestration.dispatch_settle` "
        "after a worker left commits without a PR.\n"
    )
    create = _run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            pr_title,
            "--body",
            pr_body,
        ],
        cwd=worktree,
    )
    if create.returncode != 0:
        actions.append(f"pr_create_failed:{(create.stderr or create.stdout)[:300]}")
        return actions
    actions.append(f"pr_created:{(create.stdout or '').strip()}")
    return actions


def settle_task(
    task_id: str,
    *,
    repo_root: Path | None = None,
    task_dir: Path | None = None,
    open_pr: bool = False,
    pr_title: str | None = None,
    pr_body: str | None = None,
    push: bool = False,
    release_stale: bool = True,
) -> SettleReport:
    root = repo_root or repo_root_from_file()
    tdir = task_dir or default_task_dir(root)
    ledger = OwnershipLedger(default_ledger_path(), task_state_dir=tdir)
    actions: list[str] = []
    if release_stale:
        released = release_inactive_claims(ledger)
        if released:
            actions.append(f"released_inactive:{','.join(sorted(set(released)))}")

    actions.extend(heal_zombie_task(tdir, task_id, ledger=ledger))

    data = _load_task(tdir, task_id)
    status = data.get("status") if isinstance(data.get("status"), str) else None
    raw_pid = data.get("pid")
    if isinstance(raw_pid, int):
        pid = raw_pid
    elif isinstance(raw_pid, str) and raw_pid.isdigit():
        pid = int(raw_pid)
    else:
        pid = None
    worktree_raw = data.get("worktree_path") or data.get("cwd")
    worktree = Path(str(worktree_raw)) if worktree_raw else None
    branch_task = data.get("worktree_branch")
    branch: str | None = branch_task if isinstance(branch_task, str) else None
    commits_ahead: int | None = None
    dirty: bool | None = None
    if worktree is not None:
        b, ahead, d = _git_info(worktree)
        branch = branch or b
        commits_ahead = ahead
        dirty = d

    pr_url, pr_number = _find_pr(branch, worktree or root)

    if (
        push
        and worktree is not None
        and branch
        and (commits_ahead or 0) > 0
    ):
        actions.extend(
            push_and_maybe_open_pr(
                worktree,
                branch,
                open_pr=open_pr,
                title=pr_title,
                body=pr_body,
            )
        )
        pr_url, pr_number = _find_pr(branch, worktree)

    closeout = {
        "branch": branch,
        "sha": None,
        "pr": pr_url or "NONE",
        "pointer_committed": "unknown",
        "publish_ran": "unknown",
        "deck_version": "n/a",
        "tests": "n/a",
        "blocker": "none" if pr_url or (commits_ahead in (0, None)) else "commits_without_pr",
    }
    if worktree is not None and worktree.is_dir():
        sha_p = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
        if sha_p.returncode == 0:
            closeout["sha"] = sha_p.stdout.strip()

    return SettleReport(
        task_id=task_id,
        status=status,
        pid=pid,
        pid_alive=_pid_alive(pid),
        worktree_path=str(worktree) if worktree else None,
        branch=branch,
        commits_ahead=commits_ahead,
        dirty=dirty,
        pr_url=pr_url,
        pr_number=pr_number,
        actions=actions,
        closeout=closeout,
    )


def _cmd_task(args: argparse.Namespace) -> int:
    report = settle_task(
        args.task_id,
        open_pr=args.open_pr,
        pr_title=args.pr_title,
        pr_body=args.pr_body,
        push=args.push,
        release_stale=not args.no_release_stale,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"task_id={report.task_id} status={report.status} pid={report.pid} alive={report.pid_alive}")
        print(f"worktree={report.worktree_path}")
        print(f"branch={report.branch} ahead={report.commits_ahead} dirty={report.dirty}")
        print(f"pr={report.pr_url or 'NONE'}")
        if report.actions:
            print("actions:")
            for action in report.actions:
                print(f"  - {action}")
        print("CLOSEOUT")
        for key, value in report.closeout.items():
            print(f"{key}: {value}")
    return 0


def _cmd_release_stale(_args: argparse.Namespace) -> int:
    released = release_inactive_claims()
    print(json.dumps({"released": sorted(set(released))}, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    task = sub.add_parser("task", help="Heal/report/push-PR for one dispatch task id")
    task.add_argument("--task-id", required=True)
    task.add_argument("--push", action="store_true", help="git push when commits are ahead")
    task.add_argument(
        "--open-pr",
        action="store_true",
        help="gh pr create when push succeeds and no PR exists for the branch",
    )
    task.add_argument("--pr-title", default=None)
    task.add_argument("--pr-body", default=None)
    task.add_argument("--no-release-stale", action="store_true")
    task.add_argument("--json", action="store_true")
    task.set_defaults(func=_cmd_task)

    stale = sub.add_parser(
        "release-stale",
        help="Release write-ownership claims for inactive/dead dispatch tasks",
    )
    stale.set_defaults(func=_cmd_release_stale)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
