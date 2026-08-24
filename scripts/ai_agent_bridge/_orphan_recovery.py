"""Auto-commit stranded Codex work after a workspace-write inbox run."""

from __future__ import annotations

import contextlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ._config import REPO_ROOT

_ALLOWED_ROOTS = ("scripts/", "tests/", "docs/", "plans/")
_PATH_HINT_RE = re.compile(r"(?:[A-Za-z0-9_.-]+/)+(?:[A-Za-z0-9_.-]+)?")


def _sanitized_git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}


@dataclass(frozen=True)
class RecoveryCandidate:
    delivery_id: str
    thread_id: str
    latest_message_body: str
    thread_bodies: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryResult:
    commit_sha: str | None
    reason: str | None
    changed_files: tuple[str, ...] = ()


DEFAULT_GIT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_RUFF_TIMEOUT_SECONDS: float = 30.0
GIT_COMMIT_TIMEOUT_SECONDS: float = 120.0


def _run(
    repo_root: Path,
    *args: str,
    check: bool = True,
    timeout: float = DEFAULT_GIT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        text=True,
        env=_sanitized_git_env(),
        timeout=timeout,
    )


def _git_head_changed_files(repo_root: Path) -> tuple[str, ...]:
    tracked = _run(repo_root, "diff", "--name-only", "HEAD", "--").stdout.splitlines()
    untracked = _run(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).stdout.splitlines()
    changed = sorted({path.strip() for path in (*tracked, *untracked) if path.strip()})
    return tuple(changed)


def _extract_path_hints(text: str) -> set[str]:
    hints: set[str] = set()
    for match in _PATH_HINT_RE.finditer(text):
        raw = match.group(0).strip("`()[]{}<>,.:;\"'")
        if "/" not in raw:
            continue
        if raw.endswith("/"):
            hints.add(raw)
            continue
        hints.add(raw)
        parent = raw.rsplit("/", 1)[0]
        if parent:
            hints.add(f"{parent}/")
    return hints


def _matches_thread(path: str, hints: set[str]) -> bool:
    return any(path == hint.rstrip("/") or path.startswith(hint) for hint in hints)


def _short_description(body: str) -> str:
    for line in body.splitlines():
        cleaned = line.strip().lstrip("#*- ").strip()
        if cleaned:
            return cleaned[:72]
    return "workspace-write delivery"


def _build_commit_message(candidate: RecoveryCandidate) -> str:
    short = _short_description(candidate.latest_message_body)
    return (
        f"[TIMEOUT RECOVERY] {short}\n\n"
        f"Recovery of stranded Codex work from delivery {candidate.delivery_id}\n"
        f"in thread {candidate.thread_id}. Original run exceeded hard_timeout=900s\n"
        "but the edits looked complete.\n\n"
        "Co-Authored-By: Codex (timeout recovery)\n"
    )


def _run_ruff(
    repo_root: Path,
    py_files: tuple[str, ...],
    *,
    timeout: float = DEFAULT_RUFF_TIMEOUT_SECONDS,
) -> bool:
    if not py_files:
        return True
    ruff_bin = repo_root / ".venv" / "bin" / "ruff"
    if not ruff_bin.exists():
        ruff_bin = REPO_ROOT / ".venv" / "bin" / "ruff"
    try:
        result = subprocess.run(
            [str(ruff_bin), "check", *py_files],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def recover_orphan_commit(
    candidate: RecoveryCandidate,
    *,
    repo_root: Path = REPO_ROOT,
) -> RecoveryResult:
    changed_files = _git_head_changed_files(repo_root)
    if not changed_files:
        return RecoveryResult(commit_sha=None, reason="clean-tree")

    if any(not path.startswith(_ALLOWED_ROOTS) for path in changed_files):
        return RecoveryResult(
            commit_sha=None,
            reason="outside-allowed-scope",
            changed_files=changed_files,
        )

    hints = {
        hint
        for body in candidate.thread_bodies
        for hint in _extract_path_hints(body)
    }
    if not hints or any(not _matches_thread(path, hints) for path in changed_files):
        return RecoveryResult(
            commit_sha=None,
            reason="thread-mismatch",
            changed_files=changed_files,
        )

    py_files = tuple(path for path in changed_files if path.endswith(".py"))
    if not _run_ruff(repo_root, py_files):
        return RecoveryResult(
            commit_sha=None,
            reason="ruff-failed",
            changed_files=changed_files,
        )

    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "add", "--", *changed_files],
            check=True,
            capture_output=True,
            text=True,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return RecoveryResult(
            commit_sha=None,
            reason="pre-commit-failed",
            changed_files=changed_files,
        )
    try:
        commit = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "commit",
                "-m",
                _build_commit_message(candidate),
                "--only",
                "--",
                *changed_files,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=_sanitized_git_env(),
            timeout=GIT_COMMIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            subprocess.run(
                ["git", "-C", str(repo_root), "restore", "--staged", "--", *changed_files],
                check=False,
                capture_output=True,
                text=True,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
            )
        return RecoveryResult(
            commit_sha=None,
            reason="pre-commit-failed",
            changed_files=changed_files,
        )
    if commit.returncode != 0:
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            subprocess.run(
                ["git", "-C", str(repo_root), "restore", "--staged", "--", *changed_files],
                check=False,
                capture_output=True,
                text=True,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
            )
        return RecoveryResult(
            commit_sha=None,
            reason="pre-commit-failed",
            changed_files=changed_files,
        )

    sha = _run(repo_root, "rev-parse", "HEAD").stdout.strip()
    return RecoveryResult(commit_sha=sha, reason=None, changed_files=changed_files)
