#!/usr/bin/env python
"""Orchestrator control plane for delegated worker runs.

This script deliberately sits above ``delegate.py`` instead of replacing it:
``delegate.py`` owns process lifecycle and worktree setup, while this helper
owns the durable operator view the orchestrator needs across thread rollovers.
It records which delegate task ids belong to an orchestration run and renders a
compact inbox from ``batch_state/tasks`` so a fresh thread can resume without
rediscovering raw state files by hand.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PYTHON = ".venv/bin/python"
TASK_STATUS_ATTENTION = {
    "cancelled",
    "crashed",
    "failed",
    "needs_finalize",
    "rate_limited",
    "timeout",
}
TASK_STATUS_ACTIVE = {"running", "spawning"}
TASK_STATUS_TERMINAL = TASK_STATUS_ATTENTION | {"done"}
PR_URL_RE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/\d+")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_run_id(value: str) -> str:
    run_id = value.strip()
    if not SAFE_ID_RE.fullmatch(run_id):
        raise argparse.ArgumentTypeError("run ids must match [A-Za-z0-9][A-Za-z0-9._:-]*")
    return run_id


def default_run_id() -> str:
    return "orchestrator-" + utc_now().strftime("%Y%m%dT%H%M%SZ")


def safe_path_component(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip(".-")
    return safe or "task"


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def runs_dir(repo_root: Path) -> Path:
    return repo_root / "batch_state" / "orchestrator-runs"


def tasks_dir(repo_root: Path) -> Path:
    return repo_root / "batch_state" / "tasks"


def run_state_path(repo_root: Path, run_id: str) -> Path:
    return runs_dir(repo_root) / f"{safe_path_component(run_id)}.json"


def task_state_path(task_dir: Path, task_id: str) -> Path:
    safe = task_id.replace("/", "_").replace("\\", "_")
    return task_dir / f"{safe}.json"


def create_run_state(
    run_id: str, *, description: str | None = None, owner_agent: str = "orchestrator"
) -> dict[str, Any]:
    now = isoformat_z(utc_now())
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "description": description or "",
        "owner_agent": owner_agent,
        "created_at": now,
        "updated_at": now,
        "tasks": [],
    }


def load_run_state(repo_root: Path, run_id: str) -> dict[str, Any] | None:
    return read_json(run_state_path(repo_root, run_id))


def ensure_run_state(repo_root: Path, run_id: str, *, description: str | None = None) -> dict[str, Any]:
    existing = load_run_state(repo_root, run_id)
    if existing is not None:
        return existing
    state = create_run_state(run_id, description=description)
    write_json_atomic(run_state_path(repo_root, run_id), state)
    return state


def record_task(
    repo_root: Path,
    run_id: str,
    *,
    task_id: str,
    agent: str | None,
    prompt_file: str | None = None,
    command: list[str] | None = None,
    note: str | None = None,
    lifecycle_file: str | None = None,
) -> dict[str, Any]:
    state = ensure_run_state(repo_root, run_id)
    now = isoformat_z(utc_now())
    previous = next(
        (item for item in state.get("tasks", []) if item.get("task_id") == task_id),
        None,
    )
    tasks = [item for item in state.get("tasks", []) if item.get("task_id") != task_id]
    lifecycle = (previous or {}).get("task_lifecycle")
    if lifecycle_file:
        from scripts.orchestration import task_lifecycle

        lifecycle_path = Path(lifecycle_file).expanduser().resolve()
        lifecycle = task_lifecycle.carrier_projection(
            task_lifecycle.load_lifecycle(lifecycle_path), state_file=str(lifecycle_path)
        )
    tasks.append(
        {
            "task_id": task_id,
            "agent": agent,
            "prompt_file": prompt_file,
            "command": command,
            "note": note or "",
            "task_lifecycle": lifecycle,
            "recorded_at": now,
        }
    )
    state["tasks"] = tasks
    state["updated_at"] = now
    write_json_atomic(run_state_path(repo_root, run_id), state)
    return state


def load_task_state(task_dir: Path, task_id: str) -> dict[str, Any] | None:
    return read_json(task_state_path(task_dir, task_id))


def discover_task_states(task_dir: Path, *, limit: int) -> list[dict[str, Any]]:
    if not task_dir.exists():
        return []
    tasks: list[dict[str, Any]] = []
    for path in sorted(task_dir.glob("*.json")):
        state = read_json(path)
        if not state:
            continue
        state["_state_file"] = str(path)
        tasks.append(state)
    tasks.sort(
        key=lambda item: parse_iso_datetime(item.get("started_at")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return tasks[: max(1, limit)]


def read_text_excerpt(path: Path, max_chars: int) -> tuple[str | None, bool]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, False
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip() + "\n[truncated]", True


def resolve_existing_path(raw_path: Any, repo_root: Path) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = repo_root / path
    return path if path.exists() else None


def task_age_seconds(task: dict[str, Any]) -> float | None:
    started = parse_iso_datetime(task.get("started_at"))
    if started is None:
        return None
    return round((utc_now() - started).total_seconds(), 1)


def extract_pr_urls(*texts: str | None) -> list[str]:
    found: list[str] = []
    for text in texts:
        if not text:
            continue
        for match in PR_URL_RE.findall(text):
            if match not in found:
                found.append(match)
    return found


def summarize_task(
    task: dict[str, Any],
    *,
    repo_root: Path,
    include_results: bool,
    include_logs: bool,
    max_result_chars: int,
    max_log_chars: int,
) -> dict[str, Any]:
    result_path = resolve_existing_path(task.get("result_file"), repo_root)
    result_excerpt = None
    result_truncated = False
    if include_results and result_path:
        result_excerpt, result_truncated = read_text_excerpt(result_path, max_result_chars)

    stdout_excerpt = None
    stderr_excerpt = None
    if include_logs:
        task_id = str(task.get("task_id") or "")
        log_dir = tasks_dir(repo_root) / "logs"
        stdout_path = log_dir / f"{task_id}.stdout.log"
        stderr_path = log_dir / f"{task_id}.stderr.log"
        if stdout_path.exists():
            stdout_excerpt, _ = read_text_excerpt(stdout_path, max_log_chars)
        if stderr_path.exists():
            stderr_excerpt, _ = read_text_excerpt(stderr_path, max_log_chars)

    status = str(task.get("status") or "unknown")
    pr_urls = extract_pr_urls(result_excerpt, task.get("stderr_excerpt"))
    attention: list[str] = []
    if status in TASK_STATUS_ATTENTION:
        attention.append(status)
    if task.get("worktree_dirty_on_exit"):
        attention.append("dirty_worktree")
    if task.get("needs_finalize"):
        attention.append("needs_finalize")
    if pr_urls:
        attention.append("pr_ready_for_review")

    return {
        "task_id": task.get("task_id"),
        "agent": task.get("agent"),
        "status": status,
        "started_at": task.get("started_at"),
        "finished_at": task.get("finished_at"),
        "age_s": task_age_seconds(task),
        "duration_s": task.get("duration_s"),
        "worktree_path": task.get("worktree_path"),
        "worktree_branch": task.get("worktree_branch"),
        "worktree_dirty_on_exit": task.get("worktree_dirty_on_exit"),
        "commits_ahead": task.get("commits_ahead"),
        "result_file": str(result_path) if result_path else task.get("result_file"),
        "result_excerpt": result_excerpt,
        "result_truncated": result_truncated,
        "stderr_excerpt": task.get("stderr_excerpt"),
        "stdout_log_excerpt": stdout_excerpt,
        "stderr_log_excerpt": stderr_excerpt,
        "pr_urls": pr_urls,
        "attention": attention,
        "task_lifecycle": task.get("task_lifecycle"),
    }


def collect_inbox(
    repo_root: Path,
    *,
    run_id: str | None,
    recent: int,
    include_results: bool,
    include_logs: bool,
    max_result_chars: int,
    max_log_chars: int,
) -> dict[str, Any]:
    task_dir = tasks_dir(repo_root)
    run_state = load_run_state(repo_root, run_id) if run_id else None
    task_records: list[dict[str, Any]]
    missing: list[dict[str, Any]] = []

    if run_id:
        if run_state is None:
            task_records = []
            missing.append({"task_id": None, "reason": f"run not found: {run_id}"})
        else:
            task_records = []
            for record in run_state.get("tasks") or []:
                task_id = str(record.get("task_id") or "")
                task = load_task_state(task_dir, task_id)
                if task is None:
                    missing.append({"task_id": task_id, "reason": "delegate state not found"})
                    task = {
                        "task_id": task_id,
                        "agent": record.get("agent"),
                        "status": "missing",
                        "task_lifecycle": record.get("task_lifecycle"),
                    }
                task_records.append(task)
    else:
        task_records = discover_task_states(task_dir, limit=recent)

    summaries = [
        summarize_task(
            task,
            repo_root=repo_root,
            include_results=include_results,
            include_logs=include_logs,
            max_result_chars=max_result_chars,
            max_log_chars=max_log_chars,
        )
        for task in task_records
    ]

    counts: dict[str, int] = {}
    for task in summaries:
        status = str(task.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": isoformat_z(utc_now()),
        "repo_root": str(repo_root),
        "run_id": run_id,
        "run": run_state,
        "counts": counts,
        "missing": missing,
        "tasks": summaries,
    }


def table(rows: list[list[str]], headers: list[str]) -> str:
    if not rows:
        return "_None._"
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))
    header = "| " + " | ".join(name.ljust(widths[idx]) for idx, name in enumerate(headers)) + " |"
    sep = "| " + " | ".join("-" * width for width in widths) + " |"
    body = ["| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def short_path(value: Any, repo_root: Path) -> str:
    if not value:
        return ""
    return rel(Path(str(value)), repo_root)


def render_markdown_inbox(payload: dict[str, Any]) -> str:
    repo_root = Path(str(payload["repo_root"]))
    tasks = payload["tasks"]
    rows = []
    for task in tasks:
        prs = ", ".join(f"#{url.rsplit('/', 1)[-1]}" for url in task.get("pr_urls") or [])
        attention = ", ".join(task.get("attention") or [])
        rows.append(
            [
                str(task.get("task_id") or ""),
                str(task.get("agent") or ""),
                str(task.get("status") or ""),
                str(task.get("duration_s") or task.get("age_s") or ""),
                short_path(task.get("worktree_path"), repo_root),
                prs,
                str((task.get("task_lifecycle") or {}).get("current_state") or ""),
                attention,
            ]
        )

    action_rows = []
    for task in tasks:
        attention = task.get("attention") or []
        if not attention:
            continue
        action_rows.append(
            [
                str(task.get("task_id") or ""),
                ", ".join(attention),
                (task.get("stderr_excerpt") or "").replace("\n", " ")[:120],
            ]
        )

    lines = [
        "# Orchestrator Worker Inbox",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Repo: `{payload['repo_root']}`",
        f"- Run: `{payload.get('run_id') or 'recent tasks'}`",
        f"- Counts: `{payload.get('counts')}`",
        "",
        "## Tasks",
        "",
        table(
            rows,
            ["Task", "Agent", "Status", "Age/Duration", "Worktree", "PR", "Lifecycle", "Attention"],
        ),
        "",
        "## Needs Orchestrator Attention",
        "",
        table(action_rows, ["Task", "Reason", "Last Error"]),
    ]

    missing = payload.get("missing") or []
    if missing:
        lines.extend(
            [
                "",
                "## Missing",
                "",
                table(
                    [[str(item.get("task_id") or ""), str(item.get("reason") or "")] for item in missing],
                    ["Task", "Reason"],
                ),
            ]
        )

    excerpt_blocks = []
    for task in tasks:
        result_excerpt = task.get("result_excerpt")
        stdout_excerpt = task.get("stdout_log_excerpt")
        stderr_excerpt = task.get("stderr_log_excerpt")
        if not any((result_excerpt, stdout_excerpt, stderr_excerpt)):
            continue
        excerpt_blocks.append(f"### {task.get('task_id')}")
        if result_excerpt:
            excerpt_blocks.extend(["", "Result:", "", "```text", result_excerpt.rstrip(), "```"])
        if stdout_excerpt:
            excerpt_blocks.extend(["", "Stdout log:", "", "```text", stdout_excerpt.rstrip(), "```"])
        if stderr_excerpt:
            excerpt_blocks.extend(["", "Stderr log:", "", "```text", stderr_excerpt.rstrip(), "```"])

    if excerpt_blocks:
        lines.extend(["", "## Excerpts", "", *excerpt_blocks])

    return "\n".join(lines).rstrip() + "\n"


def resolve_prompt_file(repo_root: Path, args: argparse.Namespace) -> Path:
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise FileNotFoundError(f"prompt file not found: {path}")
        return path.resolve()

    prompt = args.prompt
    if prompt is None:
        raise ValueError("--prompt or --prompt-file is required")
    prompt_dir = runs_dir(repo_root) / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    path = prompt_dir / f"{safe_path_component(args.run_id)}-{safe_path_component(args.task_id)}.md"
    path.write_text(prompt, encoding="utf-8")
    return path


def build_delegate_command(args: argparse.Namespace, prompt_file: Path) -> list[str]:
    command = [
        PYTHON,
        "scripts/delegate.py",
        "dispatch",
        "--agent",
        args.agent,
        "--task-id",
        args.task_id,
        "--mode",
        args.mode,
        "--prompt-file",
        str(prompt_file),
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.effort:
        command.extend(["--effort", args.effort])
    if args.cwd:
        command.extend(["--cwd", args.cwd])
    if args.worktree is not None:
        command.append("--worktree")
        if args.worktree != "auto":
            command.append(args.worktree)
    if args.base:
        command.extend(["--base", args.base])
    if args.hard_timeout is not None:
        command.extend(["--hard-timeout", str(args.hard_timeout)])
    if args.silence_timeout is not None:
        command.extend(["--silence-timeout", str(args.silence_timeout)])
    if args.initial_response_timeout is not None:
        command.extend(["--initial-response-timeout", str(args.initial_response_timeout)])
    if args.max_budget_usd is not None:
        command.extend(["--max-budget-usd", str(args.max_budget_usd)])
    if args.lifecycle_file:
        command.extend(["--lifecycle-file", str(Path(args.lifecycle_file).expanduser().resolve())])
    return command


def cmd_start_run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    run_id = args.run_id or default_run_id()
    path = run_state_path(repo_root, run_id)
    if path.exists() and not args.reuse:
        print(json.dumps({"error": f"run already exists: {run_id}", "run_file": rel(path, repo_root)}, indent=2))
        return 2
    state = load_run_state(repo_root, run_id) if args.reuse else None
    if state is None:
        state = create_run_state(run_id, description=args.description, owner_agent=args.owner_agent)
        write_json_atomic(path, state)
    print(json.dumps({"run_id": run_id, "run_file": rel(path, repo_root)}, indent=2))
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    task = load_task_state(tasks_dir(repo_root), args.task_id)
    agent = args.agent or (task or {}).get("agent")
    record_task(
        repo_root,
        args.run_id,
        task_id=args.task_id,
        agent=agent,
        note=args.note,
        lifecycle_file=args.lifecycle_file,
    )
    print(json.dumps({"run_id": args.run_id, "task_id": args.task_id, "agent": agent}, indent=2))
    return 0


def cmd_dispatch(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    try:
        prompt_file = resolve_prompt_file(repo_root, args)
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2

    command = build_delegate_command(args, prompt_file)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "run_id": args.run_id,
                    "task_id": args.task_id,
                    "prompt_file": str(prompt_file),
                    "command": command,
                },
                indent=2,
            )
        )
        return 0

    proc = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(
            json.dumps(
                {
                    "error": "delegate dispatch failed",
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "command": command,
                },
                indent=2,
            )
        )
        return proc.returncode

    record_task(
        repo_root,
        args.run_id,
        task_id=args.task_id,
        agent=args.agent,
        prompt_file=str(prompt_file),
        command=command,
        note=args.note,
        lifecycle_file=args.lifecycle_file,
    )
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "task_id": args.task_id,
                "agent": args.agent,
                "delegate_stdout": proc.stdout.strip(),
                "run_file": rel(run_state_path(repo_root, args.run_id), repo_root),
            },
            indent=2,
        )
    )
    return 0


def cmd_inbox(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    payload = collect_inbox(
        repo_root,
        run_id=args.run_id,
        recent=args.recent,
        include_results=args.include_results,
        include_logs=args.include_logs,
        max_result_chars=args.max_result_chars,
        max_log_chars=args.max_log_chars,
    )
    if args.format == "json":
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(render_markdown_inbox(payload), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start-run", help="Create a durable orchestration run ledger.")
    start.add_argument("--run-id", type=validate_run_id)
    start.add_argument("--description", default="")
    start.add_argument("--owner-agent", default="orchestrator")
    start.add_argument("--reuse", action="store_true", help="Return the existing ledger if it already exists.")
    start.set_defaults(func=cmd_start_run)

    add = sub.add_parser("add-task", help="Attach an existing delegate task id to a run ledger.")
    add.add_argument("--run-id", required=True, type=validate_run_id)
    add.add_argument("--task-id", required=True)
    add.add_argument("--agent")
    add.add_argument("--note", default="")
    add.add_argument("--lifecycle-file")
    add.set_defaults(func=cmd_add_task)

    dispatch = sub.add_parser("dispatch", help="Dispatch a delegate worker and record it in a run ledger.")
    dispatch.add_argument("--run-id", required=True, type=validate_run_id)
    dispatch.add_argument("--task-id", required=True)
    dispatch.add_argument(
        "--agent",
        required=True,
        choices=[
            "codex",
            "gemini",
            "claude",
            "grok",
            "grok-build",
            "grok-hermes",
            "deepseek",
            "qwen",
            "agy",
            "cursor",
        ],
    )
    dispatch.add_argument("--prompt")
    dispatch.add_argument("--prompt-file")
    dispatch.add_argument("--note", default="")
    dispatch.add_argument("--mode", default="read-only", choices=["read-only", "workspace-write", "danger"])
    dispatch.add_argument("--model")
    dispatch.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    dispatch.add_argument("--cwd")
    dispatch.add_argument("--worktree", nargs="?", const="auto")
    dispatch.add_argument("--base", default="main")
    dispatch.add_argument("--hard-timeout", type=int, default=7200)
    dispatch.add_argument("--silence-timeout", type=int, default=3600)
    dispatch.add_argument("--initial-response-timeout", type=int, default=180)
    dispatch.add_argument("--max-budget-usd", type=float)
    dispatch.add_argument(
        "--lifecycle-file",
        help="Canonical task-lifecycle.v1 ledger forwarded to delegate state and the run ledger.",
    )
    dispatch.add_argument("--dry-run", action="store_true")
    dispatch.set_defaults(func=cmd_dispatch)

    inbox = sub.add_parser("inbox", help="Render a resumable worker status/result packet.")
    inbox.add_argument("--run-id", type=validate_run_id)
    inbox.add_argument("--recent", type=int, default=20)
    inbox.add_argument("--include-results", action="store_true")
    inbox.add_argument("--include-logs", action="store_true")
    inbox.add_argument("--max-result-chars", type=int, default=2000)
    inbox.add_argument("--max-log-chars", type=int, default=1200)
    inbox.add_argument("--format", choices=["markdown", "json"], default="markdown")
    inbox.set_defaults(func=cmd_inbox)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
