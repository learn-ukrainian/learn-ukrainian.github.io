#!/usr/bin/env python3
"""Reconcile stale ``remote.<remote>.fetch`` refspecs in narrow clones (#7121).

A configured fetch refspec that names a deleted remote head is a hard error
for ``git fetch`` / ``git pull`` — Git does not skip the missing ref. Narrow
clones accumulate these entries via ``git remote set-branches --add`` when
pulling PR branches; post-merge head deletion then arms the landmine.

This module:

* drops the matching fetch refspec when a merged/closed origin head is deleted
* reconciles configured refspecs against ``git ls-remote --heads`` (preflight)
* keeps the canonical ``main`` refspec
* adds per-branch refspecs idempotently (no duplicates)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Dual-flavor import: delegate workers put only ``scripts/`` on sys.path.
try:
    from scripts.common.git_context import sanitized_git_env
except ImportError:  # scripts/ on sys.path (stripped flavor)
    from common.git_context import sanitized_git_env  # type: ignore[no-redef]

CANONICAL_MAIN_BRANCH = "main"
DEFAULT_REMOTE = "origin"
_LS_REMOTE_TIMEOUT_S = 60
_GIT_TIMEOUT_S = 30

__all__ = [
    "CANONICAL_MAIN_BRANCH",
    "DEFAULT_REMOTE",
    "add_fetch_branch",
    "canonical_main_refspec",
    "drop_fetch_refspec_for_branch",
    "head_refspec",
    "list_fetch_refspecs",
    "list_live_remote_heads",
    "main",
    "reconcile_fetch_refspecs",
]


def canonical_main_refspec(remote: str = DEFAULT_REMOTE) -> str:
    return head_refspec(CANONICAL_MAIN_BRANCH, remote)


def head_refspec(branch: str, remote: str = DEFAULT_REMOTE) -> str:
    return f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}"


def _run_git(
    repo_root: Path,
    *args: str,
    timeout: int = _GIT_TIMEOUT_S,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def _config_key(remote: str) -> str:
    return f"remote.{remote}.fetch"


def _validate_remote(remote: str) -> str:
    if not remote or not all(ch.isalnum() or ch in "-_" for ch in remote):
        raise ValueError(f"invalid remote name: {remote!r}")
    return remote


def _validate_branch(repo_root: Path, branch: str) -> str:
    if not branch or branch.startswith("-") or any(ch in branch for ch in " \t:*?[^~\\"):
        raise ValueError(f"invalid branch name: {branch!r}")
    proc = _run_git(repo_root, "check-ref-format", "--branch", branch)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "invalid ref").strip()
        raise ValueError(f"invalid branch name {branch!r}: {detail}")
    return branch


def _single_head_name(refspec: str) -> str | None:
    """Return the single ``refs/heads/<name>`` source, or None if not exact."""
    spec = refspec.strip()
    if not spec or spec.startswith("^"):
        return None
    if spec.startswith("+"):
        spec = spec[1:]
    if ":" not in spec:
        return None
    src, _dst = spec.split(":", 1)
    prefix = "refs/heads/"
    if not src.startswith(prefix):
        return None
    name = src[len(prefix) :]
    if not name or any(ch in name for ch in "*?[\\"):
        return None
    return name


def _covers_all_heads(refspec: str) -> bool:
    spec = refspec.strip()
    if spec.startswith("+"):
        spec = spec[1:]
    if ":" not in spec:
        return False
    src, _dst = spec.split(":", 1)
    return src == "refs/heads/*"


def _has_main_coverage(refspecs: list[str]) -> bool:
    return any(
        _covers_all_heads(spec) or _single_head_name(spec) == CANONICAL_MAIN_BRANCH
        for spec in refspecs
    )


def _dedup_preserve(refspecs: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    for spec in refspecs:
        if spec in seen:
            duplicates.append(spec)
            continue
        seen.add(spec)
        kept.append(spec)
    return kept, duplicates


def list_fetch_refspecs(repo_root: Path, remote: str = DEFAULT_REMOTE) -> list[str]:
    """Return configured ``remote.<remote>.fetch`` values in file order."""
    remote = _validate_remote(remote)
    proc = _run_git(repo_root, "config", "--get-all", _config_key(remote))
    if proc.returncode == 1:
        return []
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git config failed").strip()
        raise RuntimeError(f"could not read {_config_key(remote)}: {detail}")
    return [line for line in (proc.stdout or "").splitlines() if line]


def list_live_remote_heads(
    repo_root: Path, remote: str = DEFAULT_REMOTE
) -> set[str] | None:
    """Return live remote head names, or None when ls-remote is unavailable."""
    remote = _validate_remote(remote)
    proc = _run_git(
        repo_root,
        "ls-remote",
        "--heads",
        remote,
        timeout=_LS_REMOTE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        return None
    heads: set[str] = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        ref = parts[1]
        prefix = "refs/heads/"
        if ref.startswith(prefix):
            heads.add(ref[len(prefix) :])
    return heads


def _write_fetch_refspecs(
    repo_root: Path,
    remote: str,
    desired: list[str],
    previous: list[str],
) -> None:
    key = _config_key(remote)
    unset = _run_git(repo_root, "config", "--unset-all", key)
    if unset.returncode not in (0, 5):
        detail = (unset.stderr or unset.stdout or "git config --unset-all failed").strip()
        raise RuntimeError(f"could not clear {key}: {detail}")
    try:
        for spec in desired:
            added = _run_git(repo_root, "config", "--add", key, spec)
            if added.returncode != 0:
                detail = (added.stderr or added.stdout or "git config --add failed").strip()
                raise RuntimeError(f"could not add {key}={spec}: {detail}")
    except Exception:
        restore = _run_git(repo_root, "config", "--unset-all", key)
        if restore.returncode in (0, 5):
            for spec in previous:
                _run_git(repo_root, "config", "--add", key, spec)
        raise


def add_fetch_branch(
    repo_root: Path,
    branch: str,
    remote: str = DEFAULT_REMOTE,
) -> dict[str, Any]:
    """Add one per-branch fetch refspec if it is not already present."""
    remote = _validate_remote(remote)
    branch = _validate_branch(repo_root, branch)
    spec = head_refspec(branch, remote)
    current = list_fetch_refspecs(repo_root, remote)
    if spec in current:
        return {
            "added": False,
            "already_present": True,
            "refspec": spec,
            "duplicates": current.count(spec) - 1,
        }
    desired = current + [spec]
    _write_fetch_refspecs(repo_root, remote, desired, current)
    return {
        "added": True,
        "already_present": False,
        "refspec": spec,
        "duplicates": 0,
    }


def drop_fetch_refspec_for_branch(
    repo_root: Path,
    branch: str,
    remote: str = DEFAULT_REMOTE,
) -> bool:
    """Drop every exact-head fetch refspec for ``branch``. Never drops ``main``."""
    remote = _validate_remote(remote)
    branch = _validate_branch(repo_root, branch)
    if branch == CANONICAL_MAIN_BRANCH:
        return False
    current = list_fetch_refspecs(repo_root, remote)
    remaining = [spec for spec in current if _single_head_name(spec) != branch]
    remaining, _dups = _dedup_preserve(remaining)
    if not _has_main_coverage(remaining):
        remaining.insert(0, canonical_main_refspec(remote))
    if remaining == current:
        return False
    _write_fetch_refspecs(repo_root, remote, remaining, current)
    return True


def reconcile_fetch_refspecs(
    repo_root: Path,
    remote: str = DEFAULT_REMOTE,
    *,
    apply: bool = True,
) -> dict[str, Any]:
    """Prune gone-head refspecs, dedup, and keep the canonical main refspec."""
    remote = _validate_remote(remote)
    before = list_fetch_refspecs(repo_root, remote)
    live = list_live_remote_heads(repo_root, remote)

    unique, duplicates = _dedup_preserve(before)
    pruned: list[str] = []
    kept: list[str] = []
    for spec in unique:
        head = _single_head_name(spec)
        if (
            live is not None
            and head is not None
            and head != CANONICAL_MAIN_BRANCH
            and head not in live
        ):
            pruned.append(spec)
            continue
        kept.append(spec)

    restored_main = False
    if not _has_main_coverage(kept):
        kept.insert(0, canonical_main_refspec(remote))
        restored_main = True

    error: str | None = None
    after = list(before)
    applied = False
    if apply and kept != before:
        try:
            _write_fetch_refspecs(repo_root, remote, kept, before)
            after = list_fetch_refspecs(repo_root, remote)
            applied = True
        except Exception as exc:
            error = str(exc)
            after = list_fetch_refspecs(repo_root, remote)
    elif not apply:
        after = list(kept)

    return {
        "ok": error is None,
        "remote": remote,
        "applied": applied,
        "before": before,
        "after": after,
        "pruned": pruned,
        "deduped": duplicates,
        "restored_main": restored_main,
        "live_heads_available": live is not None,
        "error": error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile remote fetch refspecs against live heads so a stale "
            "set-branches entry cannot hard-fail git fetch (#7121)."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository (or worktree) to repair. Default: cwd.",
    )
    parser.add_argument(
        "--remote",
        default=DEFAULT_REMOTE,
        help=f"Remote name (default: {DEFAULT_REMOTE}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing git config.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    args = parser.parse_args(argv)

    report = reconcile_fetch_refspecs(
        args.repo_root,
        remote=args.remote,
        apply=not args.dry_run,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        pruned = ", ".join(report["pruned"]) or "(none)"
        deduped = len(report["deduped"])
        print(
            f"fetch refspecs remote={report['remote']} "
            f"pruned={len(report['pruned'])} deduped={deduped} "
            f"restored_main={report['restored_main']} "
            f"applied={report['applied']}"
        )
        if report["pruned"]:
            print(f"  pruned: {pruned}")
        if report["error"]:
            print(f"  error: {report['error']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
