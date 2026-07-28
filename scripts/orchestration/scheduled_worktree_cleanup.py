#!/usr/bin/env python3
"""Run fail-closed worktree cleanup for an explicit repository set.

The scheduled runner fetches remote state, requires the macOS process-CWD
probe in apply mode, delegates eligibility and deletion to the canonical
reaper, and writes an immutable JSON receipt for every run. Orphaned
``.worktrees/**`` directories are reported but never deleted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.orchestration import reap_worktrees

SCHEMA_VERSION = "scheduled-worktree-cleanup.v1"
DEFAULT_INTERVAL_MINUTES = 15


def default_public_repo() -> Path:
    return PROJECT_ROOT


def default_private_repo(public_repo: Path) -> Path:
    return public_repo.parent / "learn-ukrainian-infra-private"


def default_state_dir() -> Path:
    return Path.home() / ".codex" / "worktree-cleanup"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=reap_worktrees.sanitized_git_env(),
    )


def _failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    return detail.splitlines()[-1] if detail else f"exit {proc.returncode}"


def _registered_paths(repo_root: Path) -> set[Path]:
    return {item.path.resolve() for item in reap_worktrees.list_git_worktrees(repo_root)}


def find_orphaned_worktree_directories(repo_root: Path) -> list[dict[str, Any]]:
    """Report unregistered checkout-shaped directories without deleting them."""
    worktrees_root = repo_root / ".worktrees"
    if not worktrees_root.is_dir():
        return []
    registered = _registered_paths(repo_root)
    orphans: list[dict[str, Any]] = []
    for directory, child_dirs, files in os.walk(worktrees_root, followlinks=False):
        path = Path(directory)
        if ".git" not in files:
            if len(path.relative_to(worktrees_root).parts) >= 4:
                child_dirs.clear()
            continue
        child_dirs.clear()
        resolved = path.resolve()
        if resolved in registered:
            continue
        git_file = path / ".git"
        try:
            first_line = git_file.read_text(encoding="utf-8").splitlines()[0]
        except (IndexError, OSError) as exc:
            orphans.append(
                {
                    "path": str(resolved),
                    "reason": f"unreadable .git file: {exc}",
                    "gitdir": None,
                }
            )
            continue
        prefix = "gitdir:"
        if not first_line.startswith(prefix):
            reason = "unrecognized .git file"
            gitdir = None
        else:
            target = Path(first_line.removeprefix(prefix).strip())
            if not target.is_absolute():
                target = path / target
            target = target.resolve()
            gitdir = str(target)
            reason = (
                "unregistered worktree with missing gitdir"
                if not target.exists()
                else "unregistered worktree with existing gitdir"
            )
        orphans.append({"path": str(resolved), "reason": reason, "gitdir": gitdir})
    return sorted(orphans, key=lambda item: item["path"])


def _repo_result(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "repo_root": str(repo_root),
        "fetch": None,
        "activity_probe": None,
        "results": [],
        "orphans": [],
        "errors": [],
    }
    if not (repo_root / ".git").exists():
        result["errors"].append("repository .git metadata is missing")
        return result

    fetch = _run_git(repo_root, "fetch", "--prune", "origin")
    result["fetch"] = {
        "ok": fetch.returncode == 0,
        "detail": None if fetch.returncode == 0 else _failure(fetch),
    }
    if fetch.returncode != 0:
        result["errors"].append("fetch failed; cleanup skipped")
        return result

    live_cwds = reap_worktrees._live_cwd_paths(repo_root)
    result["activity_probe"] = {
        "available": live_cwds is not None,
        "cwd_count": len(live_cwds or ()),
    }
    if apply and live_cwds is None:
        result["errors"].append("process-CWD activity probe unavailable; apply skipped")
        return result

    try:
        rows = reap_worktrees.reap_worktrees(
            repo_root=repo_root,
            apply=apply,
            preserve_then_reap=False,
            prune_merged_branches=True,
            safe_only=True,
            live_cwds=live_cwds,
            merged_pr_only=True,
        )
        result["results"] = [asdict(row) for row in rows]
        result["errors"].extend(
            f"{row.path}: {row.error or row.reason}"
            for row in rows
            if row.action == "error"
        )
        result["orphans"] = find_orphaned_worktree_directories(repo_root)
    except RuntimeError as exc:
        result["errors"].append(str(exc))
    return result


def build_receipt(
    repo_roots: list[Path],
    *,
    apply: bool,
    observed_at: str | None = None,
) -> dict[str, Any]:
    timestamp = observed_at or utc_now()
    repositories = [_repo_result(path.resolve(), apply=apply) for path in repo_roots]
    removed = sum(
        1
        for repository in repositories
        for row in repository["results"]
        if row["action"] in {"removed", "preserved_then_removed"}
    )
    errors = sum(len(repository["errors"]) for repository in repositories)
    orphans = sum(len(repository["orphans"]) for repository in repositories)
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": timestamp,
        "mode": "apply" if apply else "dry_run",
        "summary": {
            "repositories": len(repositories),
            "removed": removed,
            "orphans_reported": orphans,
            "errors": errors,
        },
        "repositories": repositories,
    }


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def ensure_private_directory(path: Path) -> None:
    """Create every missing directory component with owner-only permissions."""
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        if current.parent == current:
            break
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)
    os.chmod(path, 0o700)


def write_receipt(receipt: dict[str, Any], receipt_dir: Path) -> Path:
    content = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()[:12]
    timestamp = str(receipt["observed_at"]).replace(":", "").replace("-", "")
    destination = receipt_dir / f"{timestamp}-{digest}.json"
    ensure_private_directory(receipt_dir)
    atomic_write(destination, content)
    return destination


def build_parser() -> argparse.ArgumentParser:
    public_repo = default_public_repo()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        default=None,
        help="Repository root to sweep. Repeatable.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply safe cleanup candidates.")
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=default_state_dir() / "receipts" / "v1",
    )
    parser.set_defaults(
        default_repo_roots=[public_repo, default_private_repo(public_repo)]
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_roots = args.repo_root or args.default_repo_roots
    receipt = build_receipt(repo_roots, apply=bool(args.apply))
    receipt_path = write_receipt(receipt, args.receipt_dir.expanduser().resolve())
    payload = {**receipt, "receipt_path": str(receipt_path)}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if receipt["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
