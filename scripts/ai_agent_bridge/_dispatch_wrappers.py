"""Hardcoded delegate.py wrapper commands for recurring agent dispatches."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Bootstrap import path for scripts.* from any cwd
_local_repo_root = Path(__file__).resolve().parents[2]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.common.repo_root import resolve_repo_root

REPO_ROOT = resolve_repo_root(Path(__file__), 2)
PYTHON = ".venv/bin/python"

MANDATORY_COMMIT_PUSH_PR_CHECKLIST = """## MANDATORY checklist — do NOT skip these (the dispatch will be marked failed if you do)

1. `git add` your work (specific files, not `git add -A`)
2. `git commit -m "..."` — commit hooks will run ruff + targeted pytest
3. `git push -u origin <branch-name>`
4. `gh pr create --title "..." --body "..."` — return the URL in your final response
5. Worktree at `.worktrees/dispatch/codex/<task-id>/`. NEVER branch in the main checkout.
6. Put transient artifacts in `$LU_RUNTIME_TMP_ROOT` or the task worktree; never leave
   evidence copies or model caches in bare `/tmp`. Explicitly clean any named temporary
   path outside those locations before finishing.

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


@contextmanager
def _prompt_directory() -> Iterator[Path]:
    """Yield a task lease or a self-cleaning directory for prompt files."""
    runtime_tmp_root = os.environ.get("LU_RUNTIME_TMP_ROOT")
    if runtime_tmp_root:
        lease_root = Path(runtime_tmp_root)
        if not lease_root.is_dir():
            raise RuntimeError(f"runtime tmp lease is not a directory: {lease_root}")
        yield lease_root
        return

    with tempfile.TemporaryDirectory(prefix="learn-ukrainian-bridge-") as directory:
        yield Path(directory)


def _write_dispatch_fix_auto_brief(task_id: str, prompt_directory: Path) -> Path:
    issue = _run_json_command(["gh", "issue", "view", task_id, "--json", "title,body"])
    title = str(issue.get("title") or "").strip()
    body = str(issue.get("body") or "").strip()
    prompt = (
        f"# Dispatch fix: {task_id}\n\n"
        f"## GitHub issue {task_id}: {title}\n\n"
        f"{body}\n\n"
        f"{MANDATORY_COMMIT_PUSH_PR_CHECKLIST}"
    )
    brief_path = prompt_directory / f"dispatch-fix-{_safe_path_component(task_id)}.md"
    brief_path.write_text(prompt, encoding="utf-8")
    return brief_path


def _dispatch_fix_prompt_file(
    task_id: str,
    brief_file: str | None,
    prompt_directory: Path,
) -> Path:
    if brief_file:
        path = Path(brief_file).expanduser()
        prompt = path.read_text(encoding="utf-8")
        if MANDATORY_COMMIT_PUSH_PR_CHECKLIST not in prompt:
            prompt = f"{prompt.rstrip()}\n\n{MANDATORY_COMMIT_PUSH_PR_CHECKLIST}"
        brief_path = prompt_directory / f"dispatch-fix-{_safe_path_component(task_id)}.md"
        brief_path.write_text(prompt, encoding="utf-8")
        return brief_path
    return _write_dispatch_fix_auto_brief(task_id, prompt_directory)


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


def _write_review_deep_pr_prompt(pr_number: str, prompt_directory: Path) -> Path:
    """Pointer-only PR review prompt (Sol fleet-comms Phase 2).

    Never embed full PR body or diff — worker/delegate pulls evidence under
    read-only mode. Prefer ``review-pr`` for formal CF gates.
    """
    from ._review_safety import (
        MAX_REVIEW_REQUEST_BYTES,
        assert_content_size,
        prepend_read_only_contract,
    )

    pr = _run_json_command(["gh", "pr", "view", pr_number, "--json", "title,files,url,headRefOid"])
    title = str(pr.get("title") or "").strip()
    url = str(pr.get("url") or f"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/{pr_number}")
    head = str(pr.get("headRefOid") or "").strip()
    files = _serialize_files(pr.get("files"))
    prompt = prepend_read_only_contract(
        f"{REVIEW_DEEP_INSTRUCTIONS}\n\n"
        f"## PR #{pr_number}: {title}\n\n"
        f"**URL:** {url}\n"
        f"**Expected head SHA:** `{head}`\n\n"
        f"### Changed files (names only — pull the diff yourself)\n\n{files}\n\n"
        "Do **not** ask the operator to paste the diff. Use `gh pr diff` / sealed "
        "snapshot in the read-only dispatch worktree.\n\n"
        "End with exactly one line: `VERDICT: APPROVED` or "
        "`VERDICT: CHANGES_REQUESTED` or `VERDICT: BLOCKED`.\n"
    )
    assert_content_size(prompt, limit=MAX_REVIEW_REQUEST_BYTES, label="review_deep_prompt")
    prompt_path = prompt_directory / f"review-deep-pr-{_safe_path_component(pr_number)}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def _list_review_path_names(target: Path, *, max_files: int = 80) -> str:
    """List paths only — never dump full file contents into the prompt."""
    if target.is_file():
        return f"- {target.name}"
    lines: list[str] = []
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        lines.append(f"- {path.relative_to(target)}")
        if len(lines) >= max_files:
            lines.append(f"- … truncated after {max_files} paths")
            break
    return "\n".join(lines) if lines else "(no files)"


def _write_review_deep_path_prompt(target: str, prompt_directory: Path) -> Path:
    from ._review_safety import (
        MAX_REVIEW_REQUEST_BYTES,
        assert_content_size,
        prepend_read_only_contract,
    )

    path = Path(target).expanduser()
    if not path.exists():
        raise SystemExit(f"review-deep target is not a PR number or existing path: {target}")
    resolved = path.resolve()
    listing = _list_review_path_names(resolved)
    prompt = prepend_read_only_contract(
        f"{REVIEW_DEEP_INSTRUCTIONS}\n\n"
        f"## Path target\n\n`{resolved}`\n\n"
        f"### Paths (names only — open files in the read-only worktree)\n\n{listing}\n\n"
        "Do not request bulk paste of file contents into the prompt.\n\n"
        "End with exactly one line: `VERDICT: APPROVED` or "
        "`VERDICT: CHANGES_REQUESTED` or `VERDICT: BLOCKED`.\n"
    )
    assert_content_size(prompt, limit=MAX_REVIEW_REQUEST_BYTES, label="review_deep_prompt")
    prompt_path = prompt_directory / f"review-deep-path-{_safe_path_component(target)}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def _review_task_id(target: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"review-{_safe_path_component(target)}-{timestamp}"


def _review_prompt_file(target: str, prompt_directory: Path) -> Path:
    if _is_pr_number(target):
        return _write_review_deep_pr_prompt(target.lstrip("#"), prompt_directory)
    return _write_review_deep_path_prompt(target, prompt_directory)


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
    with _prompt_directory() as prompt_directory:
        prompt_file = _dispatch_fix_prompt_file(
            args.task_id,
            args.brief_file,
            prompt_directory,
        )
        command = build_dispatch_fix_command(args.task_id, prompt_file)
        return _run_dispatch(command, args.dry_run, prompt_file)


def handle_review_deep(args: Any) -> int:
    with _prompt_directory() as prompt_directory:
        prompt_file = _review_prompt_file(args.target, prompt_directory)
        command = build_review_deep_command(args.target, prompt_file, args.effort)
        return _run_dispatch(command, args.dry_run, prompt_file)
