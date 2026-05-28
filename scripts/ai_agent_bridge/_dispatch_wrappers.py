"""Hardcoded delegate.py wrapper commands for recurring agent dispatches."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = ".venv/bin/python"

MANDATORY_COMMIT_PUSH_PR_CHECKLIST = """## MANDATORY checklist — do NOT skip these (the dispatch will be marked failed if you do)

1. `git add` your work (specific files, not `git add -A`)
2. `git commit -m "..."` — commit hooks will run ruff + targeted pytest
3. `git push -u origin <branch-name>`
4. `gh pr create --title "..." --body "..."` — return the URL in your final response
5. Worktree at `.worktrees/dispatch/codex/<task-id>/`. NEVER branch in the main checkout.

If you finish writing code but skip steps 2-4, the work is lost. Don't make that mistake.
"""

REVIEW_DEEP_INSTRUCTIONS = (
    "Adversarial review. Find logical bugs, security issues, contradictions, "
    "missing tests, dead code, performance footguns. Cite file:line. Be terse "
    "but complete. Do NOT propose stylistic preferences. Output: structured "
    "`## Findings` markdown."
)


def _safe_path_component(raw: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    return safe or "task"


def _is_pr_number(target: str) -> bool:
    return target.lstrip("#").isdigit()


def _task_state_path(task_id: str) -> Path:
    tasks_dir = REPO_ROOT / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir / f"{safe}.json"


def _run_json_command(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout or "{}")


def _run_text_command(cmd: list[str]) -> str:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def _write_dispatch_fix_auto_brief(task_id: str) -> Path:
    issue = _run_json_command(["gh", "issue", "view", task_id, "--json", "title,body"])
    title = str(issue.get("title") or "").strip()
    body = str(issue.get("body") or "").strip()
    prompt = (
        f"# Dispatch fix: {task_id}\n\n"
        f"## GitHub issue {task_id}: {title}\n\n"
        f"{body}\n\n"
        f"{MANDATORY_COMMIT_PUSH_PR_CHECKLIST}"
    )
    brief_path = Path("/tmp") / f"dispatch-fix-{_safe_path_component(task_id)}.md"
    brief_path.write_text(prompt, encoding="utf-8")
    return brief_path


def _dispatch_fix_prompt_file(task_id: str, brief_file: str | None) -> Path:
    if brief_file:
        path = Path(brief_file).expanduser()
        prompt = path.read_text(encoding="utf-8")
        if MANDATORY_COMMIT_PUSH_PR_CHECKLIST not in prompt:
            prompt = f"{prompt.rstrip()}\n\n{MANDATORY_COMMIT_PUSH_PR_CHECKLIST}"
        brief_path = Path("/tmp") / f"dispatch-fix-{_safe_path_component(task_id)}.md"
        brief_path.write_text(prompt, encoding="utf-8")
        return brief_path
    return _write_dispatch_fix_auto_brief(task_id)


def build_dispatch_fix_command(task_id: str, prompt_file: Path) -> list[str]:
    return [
        PYTHON,
        "scripts/delegate.py",
        "dispatch",
        "--agent",
        "codex",
        "--mode",
        "danger",
        "--worktree",
        "--base",
        "origin/main",
        "--task-id",
        task_id,
        "--effort",
        "high",
        "--prompt-file",
        str(prompt_file),
    ]


def _serialize_files(files: Any) -> str:
    if not files:
        return "(none)"
    if not isinstance(files, list):
        return json.dumps(files, indent=2, sort_keys=True)
    lines = []
    for item in files:
        if isinstance(item, dict):
            path = item.get("path") or item.get("filename") or item.get("name") or str(item)
            additions = item.get("additions")
            deletions = item.get("deletions")
            if additions is not None and deletions is not None:
                lines.append(f"- {path} (+{additions}/-{deletions})")
            else:
                lines.append(f"- {path}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _write_review_deep_pr_prompt(pr_number: str) -> Path:
    pr = _run_json_command(["gh", "pr", "view", pr_number, "--json", "title,body,files"])
    diff = _run_text_command(["gh", "pr", "diff", pr_number])
    title = str(pr.get("title") or "").strip()
    body = str(pr.get("body") or "").strip()
    files = _serialize_files(pr.get("files"))
    prompt = (
        f"{REVIEW_DEEP_INSTRUCTIONS}\n\n"
        f"## PR #{pr_number}: {title}\n\n"
        f"### Body\n\n{body}\n\n"
        f"### Files\n\n{files}\n\n"
        f"### Diff\n\n```diff\n{diff}\n```\n"
    )
    prompt_path = Path("/tmp") / f"review-deep-pr-{_safe_path_component(pr_number)}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def _read_review_path(target: Path) -> str:
    if target.is_file():
        return target.read_text(encoding="utf-8", errors="replace")
    chunks = []
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(target)
        content = path.read_text(encoding="utf-8", errors="replace")
        chunks.append(f"### {rel}\n\n```text\n{content}\n```")
    return "\n\n".join(chunks)


def _write_review_deep_path_prompt(target: str) -> Path:
    path = Path(target).expanduser()
    if not path.exists():
        raise SystemExit(f"review-deep target is not a PR number or existing path: {target}")
    resolved = path.resolve()
    content = _read_review_path(resolved)
    prompt = (
        f"{REVIEW_DEEP_INSTRUCTIONS}\n\n"
        f"## Path target\n\n{resolved}\n\n"
        f"## Contents\n\n{content}\n"
    )
    prompt_path = Path("/tmp") / f"review-deep-path-{_safe_path_component(target)}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def _review_task_id(target: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"review-{_safe_path_component(target)}-{timestamp}"


def _review_prompt_file(target: str) -> Path:
    if _is_pr_number(target):
        return _write_review_deep_pr_prompt(target.lstrip("#"))
    return _write_review_deep_path_prompt(target)


def build_review_deep_command(target: str, prompt_file: Path, effort: str) -> list[str]:
    return [
        PYTHON,
        "scripts/delegate.py",
        "dispatch",
        "--agent",
        "claude",
        "--mode",
        "read-only",
        "--model",
        "claude-opus-4-8",
        "--effort",
        effort,
        "--task-id",
        _review_task_id(target),
        "--prompt-file",
        str(prompt_file),
    ]


def _write_dry_run_state(task_id: str, command: list[str], prompt_file: Path) -> None:
    prompt = prompt_file.read_text(encoding="utf-8")
    state = {
        "task_id": task_id,
        "agent": command[command.index("--agent") + 1],
        "model": command[command.index("--model") + 1] if "--model" in command else None,
        "effort": command[command.index("--effort") + 1] if "--effort" in command else None,
        "mode": command[command.index("--mode") + 1],
        "status": "dry-run",
        "prompt_file": str(prompt_file),
        "prompt_chars": len(prompt),
        "command": command,
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "returncode": 0,
    }
    _task_state_path(task_id).write_text(json.dumps(state, indent=2), encoding="utf-8")


def _run_dispatch(command: list[str], dry_run: bool, prompt_file: Path) -> int:
    task_id = command[command.index("--task-id") + 1]
    if dry_run:
        _write_dry_run_state(task_id, command, prompt_file)
        print("DRY RUN: " + " ".join(command))
        print(f"Prompt file: {prompt_file}")
        print(f"State file: {_task_state_path(task_id)}")
        return 0
    proc = subprocess.run(command, cwd=REPO_ROOT)
    return int(proc.returncode)


def handle_dispatch_fix(args: Any) -> int:
    prompt_file = _dispatch_fix_prompt_file(args.task_id, args.brief_file)
    command = build_dispatch_fix_command(args.task_id, prompt_file)
    return _run_dispatch(command, args.dry_run, prompt_file)


def handle_review_deep(args: Any) -> int:
    prompt_file = _review_prompt_file(args.target)
    command = build_review_deep_command(args.target, prompt_file, args.effort)
    return _run_dispatch(command, args.dry_run, prompt_file)
