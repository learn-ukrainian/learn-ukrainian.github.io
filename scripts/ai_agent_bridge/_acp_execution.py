"""Isolated cwd selection for bounded ACP provider transport.

ACP adapters keep their primary-checkout refusal. Compatibility callers that
start from the human/service checkout receive a short-lived detached,
no-checkout worktree instead of weakening that guard or inventing a trusted
caller bypass.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from types import FrameType
from typing import Any

from scripts.common.acp_runtime_lock import (
    build_lock_reason,
    holds_only_git_pointer,
    owner_alive,
    parse_lock_owner,
)
from scripts.common.git_context import sanitized_git_env
from scripts.guardrails.worktree_containment import (
    classify_repo_path,
    resolve_main_root,
)
from scripts.orchestration.worktree_claims import WorktreeRemoval, remove_unclaimed_worktree

logger = logging.getLogger(__name__)

_SAFE_TASK = re.compile(r"[^A-Za-z0-9._-]+")


class AcpExecutionWorkspaceError(RuntimeError):
    """ACP could not obtain or release its isolated execution cwd."""


def _execution_label(task_id: str) -> str:
    """Return a bounded directory label, rejecting transport-shaped debris."""
    raw = task_id.strip()
    if not raw or raw.startswith("-") or "{" in raw or "}" in raw:
        raise AcpExecutionWorkspaceError("unsafe_acp_execution_task_id")
    label = _SAFE_TASK.sub("-", raw).strip("-._")[:32]
    if not label or label.startswith("-") or label in {".", ".."}:
        raise AcpExecutionWorkspaceError("unsafe_acp_execution_task_id")
    return label


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


def _acp_runtime_root(main_root: Path) -> Path:
    return (main_root / ".worktrees" / "dispatch" / "acp").resolve()


def _holds_more_than_git_pointer(path: Path) -> bool:
    """Dirty probe for a no-checkout runtime: anything beyond ``.git`` counts."""
    return not holds_only_git_pointer(path)


def _own_runtime_is_scratch(_path: Path) -> bool:
    """Dirty probe for the runtime this ask created: its contents are the ask's scratch."""
    return False


def _remove_runtime_worktree(
    main_root: Path,
    workspace: Path,
    *,
    owner_task_id: str | None,
    reason: str,
    dirty_probe: Callable[[Path], bool],
) -> WorktreeRemoval:
    """Force-remove one ACP runtime through the shared guarded chokepoint (#8610).

    The chokepoint holds the per-worktree lock dispatch attaches under,
    refuses while another task's unfinished record names the runtime, and
    only then lifts this bridge's own git worktree lock and removes it.
    """
    return remove_unclaimed_worktree(
        workspace,
        repo_root=main_root,
        reason=reason,
        owner_task_id=owner_task_id,
        force=True,
        dirty_probe=dirty_probe,
        unlock=True,
    )


def sweep_dead_acp_runtime_worktrees(main_root: Path) -> list[Path]:
    """Remove locked ACP runtime worktrees whose owner is provably dead.

    Best-effort self-healing before a new ACP execution creates its own
    workspace (#8344): a previous ask that was SIGKILLed (or lost to a host
    reboot) never unwound, leaving its lock behind. Only owner-tagged locks
    whose pid is absent or recycled are touched; alive or unknown owners are
    left alone, as is any runtime directory holding more than its ``.git``
    pointer. A sweep failure is logged and never raised into the caller.
    """
    swept: list[Path] = []
    try:
        listing = _run_git(main_root, "worktree", "list", "--porcelain")
        if listing.returncode != 0:
            logger.warning(
                "ACP runtime sweep could not list worktrees: %s",
                " ".join((listing.stderr or listing.stdout).split())[:240],
            )
            return swept
        acp_root = _acp_runtime_root(main_root)
        current: Path | None = None
        locked_reason: str | None = None

        def handle() -> None:
            nonlocal current, locked_reason
            if current is None:
                return
            owner = parse_lock_owner(locked_reason)
            if owner is None:
                return
            pid, start_time = owner
            try:
                resolved = current.resolve()
                if resolved.parent != acp_root or not resolved.name.startswith("runtime-"):
                    return
            except OSError:
                return
            if owner_alive(pid, start_time) is not False:
                return
            # The dead owner's task id is not recoverable from its lock, so
            # no record is exempt from the claim scan.
            removal = _remove_runtime_worktree(
                main_root,
                resolved,
                owner_task_id=None,
                reason="dead-owner ACP runtime sweep",
                dirty_probe=_holds_more_than_git_pointer,
            )
            if removal.action == "removed":
                swept.append(resolved)
            elif removal.action == "skipped":
                logger.warning(
                    "ACP runtime sweep left %s for the reaper: %s",
                    resolved,
                    removal.reason,
                )
            else:
                logger.warning(
                    "ACP runtime sweep could not remove dead-owner worktree %s: %s",
                    resolved,
                    removal.error,
                )

        for line in (listing.stdout or "").splitlines():
            if line.startswith("worktree "):
                handle()
                current = Path(line.removeprefix("worktree ").strip())
                locked_reason = None
            elif line == "locked":
                locked_reason = ""
            elif line.startswith("locked "):
                locked_reason = line.removeprefix("locked ").strip()
        handle()
    except Exception:  # a sweep failure must never block the ask itself
        logger.exception("ACP runtime sweep failed; proceeding with the ask")
    return swept


def _install_orderly_sigterm() -> Any:
    """Convert SIGTERM into an orderly unwind so context cleanup can run.

    Python's default SIGTERM disposition terminates the process without
    unwinding, which skipped the worktree cleanup ``finally`` exactly when an
    ask was cancelled (#8344). Raising ``SystemExit(143)`` lets every context
    manager unwind and then exits with the conventional 128+SIGTERM code, so
    the signal is not swallowed. Main-thread only; the caller restores the
    previous handler on exit.
    """
    if threading.current_thread() is not threading.main_thread():
        return None

    def _unwind(signum: int, _frame: FrameType | None) -> None:
        raise SystemExit(128 + signum)

    previous = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, _unwind)
    return previous


def _restore_sigterm(previous: Any) -> None:
    if previous is None or threading.current_thread() is not threading.main_thread():
        return
    signal.signal(signal.SIGTERM, previous)


@contextlib.contextmanager
def acp_execution_cwd(repo_root: Path, *, task_id: str) -> Iterator[Path]:
    """Yield a non-primary registered worktree for one bounded ACP call.

    Existing worktree callers are unchanged. A primary-root caller gets a
    unique detached worktree with no checkout, so the runtime gains only the
    Git/worktree identity required by ACP admission—not another source copy.
    """
    # Validate before any mkdir/worktree operation.  ACP/opencode stdout is an
    # NDJSON event stream; a wiring or quoting fault must fail closed instead
    # of turning a raw event line, JSON fragment, or flag-shaped token into a
    # filesystem segment (#6863).
    label = _execution_label(task_id)
    resolved = repo_root.resolve()
    test_primary = os.environ.get("LU_TEST_ACP_PRIMARY_ROOT")
    test_scratch = os.environ.get("LU_TEST_ACP_SCRATCH_ROOT")
    if os.environ.get("PYTEST_CURRENT_TEST") and test_primary and test_scratch and resolved == Path(test_primary).resolve():
        yield Path(tempfile.mkdtemp(prefix="acp-execution-", dir=test_scratch))
        return
    path_class = classify_repo_path(resolved, cwd=resolved)
    if path_class in {"dispatch_worktree", "other_worktree"}:
        yield resolved
        return
    if path_class != "primary_checkout":
        raise AcpExecutionWorkspaceError("acp_repo_root_must_be_a_registered_checkout")

    main_root = resolve_main_root(resolved)
    sweep_dead_acp_runtime_worktrees(main_root)
    workspace = _acp_runtime_root(main_root) / f"runtime-{label}-{uuid.uuid4().hex[:10]}"
    workspace.parent.mkdir(parents=True, exist_ok=True)
    created = False
    previous_sigterm = _install_orderly_sigterm()
    try:
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
            build_lock_reason(label),
            str(workspace),
        )
        if lock.returncode != 0:
            _remove_runtime_worktree(
                main_root,
                workspace,
                owner_task_id=task_id,
                reason="ACP runtime lock failed",
                dirty_probe=_own_runtime_is_scratch,
            )
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
                removal = _remove_runtime_worktree(
                    main_root,
                    workspace,
                    owner_task_id=task_id,
                    reason="ACP execution finished",
                    dirty_probe=_own_runtime_is_scratch,
                )
                if removal.action != "removed" and workspace.exists():
                    logger.error(
                        "ACP execution worktree cleanup failed for %s: %s",
                        workspace,
                        " ".join(f"{removal.reason}: {removal.error or ''}".split())[:240],
                    )
    finally:
        _restore_sigterm(previous_sigterm)
