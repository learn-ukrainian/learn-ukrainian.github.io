"""Isolated cwd selection for bounded ACP provider transport.

ACP adapters keep their primary-checkout refusal. Compatibility callers that
start from the human/service checkout receive a short-lived detached,
no-checkout worktree instead of weakening that guard or inventing a trusted
caller bypass.
"""

from __future__ import annotations

import contextlib
import logging
import re
import shutil
import subprocess
import uuid
from collections.abc import Iterator
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.guardrails.worktree_containment import (
    classify_repo_path,
    resolve_main_root,
)

logger = logging.getLogger(__name__)

_SAFE_TASK = re.compile(r"[^A-Za-z0-9._-]+")


class AcpExecutionWorkspaceError(RuntimeError):
    """ACP could not obtain or release its isolated execution cwd."""


def _git_binary() -> str:
    binary = shutil.which("git")
    if binary is None:
        raise AcpExecutionWorkspaceError("git_binary_unavailable")
    return str(Path(binary).resolve())


def _run_git(main_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_git_binary(), "-C", str(main_root), *args],
        cwd=main_root,
        env=sanitized_git_env(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


@contextlib.contextmanager
def acp_execution_cwd(repo_root: Path, *, task_id: str) -> Iterator[Path]:
    """Yield a non-primary registered worktree for one bounded ACP call.

    Existing worktree callers are unchanged. A primary-root caller gets a
    unique detached worktree with no checkout, so the runtime gains only the
    Git/worktree identity required by ACP admission—not another source copy.
    """
    resolved = repo_root.resolve()
    path_class = classify_repo_path(resolved, cwd=resolved)
    if path_class in {"dispatch_worktree", "other_worktree"}:
        yield resolved
        return
    if path_class != "primary_checkout":
        raise AcpExecutionWorkspaceError("acp_repo_root_must_be_a_registered_checkout")

    main_root = resolve_main_root(resolved)
    label = _SAFE_TASK.sub("-", task_id).strip("-._")[:32] or "task"
    workspace = main_root / ".worktrees" / "dispatch" / "acp" / f"runtime-{label}-{uuid.uuid4().hex[:10]}"
    workspace.parent.mkdir(parents=True, exist_ok=True)
    created = False
    add = _run_git(
        main_root,
        "worktree",
        "add",
        "--detach",
        "--no-checkout",
        str(workspace),
        "HEAD",
    )
    if add.returncode != 0:
        detail = " ".join((add.stderr or add.stdout).split())[:240]
        raise AcpExecutionWorkspaceError(f"acp_execution_worktree_create_failed: {detail or 'git worktree add failed'}")
    created = True
    lock = _run_git(
        main_root,
        "worktree",
        "lock",
        "--reason",
        f"active ACP execution {label}",
        str(workspace),
    )
    if lock.returncode != 0:
        _run_git(main_root, "worktree", "remove", "--force", str(workspace))
        detail = " ".join((lock.stderr or lock.stdout).split())[:240]
        raise AcpExecutionWorkspaceError(
            f"acp_execution_worktree_lock_failed: {detail or 'git worktree lock failed'}"
        )
    try:
        if classify_repo_path(workspace, cwd=workspace) not in {
            "dispatch_worktree",
            "other_worktree",
        }:
            raise AcpExecutionWorkspaceError("acp_execution_worktree_not_registered")
        yield workspace
    finally:
        if created:
            unlock = _run_git(main_root, "worktree", "unlock", str(workspace))
            remove = _run_git(main_root, "worktree", "remove", "--force", str(workspace))
            if remove.returncode != 0 and workspace.exists():
                logger.error(
                    "ACP execution worktree cleanup failed for %s: %s",
                    workspace,
                    " ".join((remove.stderr or remove.stdout).split())[:240],
                )
            elif unlock.returncode != 0 and workspace.exists():
                logger.error(
                    "ACP execution worktree unlock failed for %s: %s",
                    workspace,
                    " ".join((unlock.stderr or unlock.stdout).split())[:240],
                )
