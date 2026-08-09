#!/usr/bin/env python3
"""Inventory and safely retain old local agent-session files (#4956).

The command is dry-run by default.  ``--apply`` requires the explicit
``LU_HOME_SESSION_APPLY=1`` environment gate and acts only on session files
under the fixed provider allowlist below.  It never removes a provider root,
configuration file, symlink, or file newer than the retention cutoff.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

DEFAULT_RETENTION_DAYS = 14.0
DEFAULT_ARCHIVE_ROOT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "learn-ukrainian"
    / "home-session-archives"
)
APPLY_ENV = "LU_HOME_SESSION_APPLY"


@dataclass(frozen=True)
class SessionStore:
    provider: str
    home_directory: str
    session_directories: tuple[str, ...]


@dataclass(frozen=True)
class SessionRootReport:
    provider: str
    path: str
    exists: bool
    size_bytes: int | None
    age_days: float | None
    session_files: int
    skipped_reason: str | None = None


@dataclass(frozen=True)
class SessionCandidate:
    provider: str
    path: str
    relative_path: str
    size_bytes: int
    age_days: float


# These are the provider homes already documented by the lane-retention
# scanner.  Apply targets only the session subtrees, never the home roots.
SESSION_STORES: tuple[SessionStore, ...] = (
    SessionStore("codex", ".codex", ("sessions", "archived_sessions")),
    SessionStore("claude", ".claude", ("projects",)),
    SessionStore("cursor", ".cursor", ("chats",)),
    SessionStore("grok", ".grok", ("sessions",)),
)


def _size_bytes(path: Path) -> int | None:
    """Return regular-file size below a real directory, or ``None`` on error."""
    try:
        return sum(
            entry.stat().st_size
            for entry in path.rglob("*")
            if entry.is_file() and not entry.is_symlink()
        )
    except OSError:
        return None


def _raw_age_days(path: Path, *, now: float) -> float | None:
    try:
        return max((now - path.stat().st_mtime) / 86400.0, 0.0)
    except OSError:
        return None


def _age_days(path: Path, *, now: float) -> float | None:
    raw_age = _raw_age_days(path, now=now)
    return None if raw_age is None else round(raw_age, 1)


def _real_directory(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _is_allowed_session_file(*, root: Path, session_root: Path, candidate: Path) -> bool:
    """Ensure a regular candidate remains within a non-symlink allowlisted root."""
    if not (_real_directory(root) and _real_directory(session_root)):
        return False
    if not candidate.is_file() or candidate.is_symlink():
        return False
    try:
        candidate.resolve().relative_to(session_root.resolve())
        session_root.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def inventory_home_sessions(
    *,
    home: Path | None = None,
    retention_days: float = DEFAULT_RETENTION_DAYS,
    now: float | None = None,
) -> tuple[list[SessionRootReport], list[SessionCandidate]]:
    """Return root size/age reports and stale, allowlisted session-file candidates."""
    if retention_days < 0:
        raise ValueError("retention_days must be non-negative")
    home_root = (home or Path.home()).expanduser()
    clock = time.time() if now is None else now
    roots: list[SessionRootReport] = []
    candidates: list[SessionCandidate] = []

    for store in SESSION_STORES:
        root = home_root / store.home_directory
        if not root.exists():
            roots.append(
                SessionRootReport(
                    provider=store.provider,
                    path=str(root),
                    exists=False,
                    size_bytes=0,
                    age_days=None,
                    session_files=0,
                )
            )
            continue
        if not _real_directory(root):
            roots.append(
                SessionRootReport(
                    provider=store.provider,
                    path=str(root),
                    exists=True,
                    size_bytes=None,
                    age_days=None,
                    session_files=0,
                    skipped_reason="provider home is not a real directory",
                )
            )
            continue

        session_count = 0
        for relative_dir in store.session_directories:
            session_root = root / relative_dir
            if not _real_directory(session_root):
                continue
            try:
                files = sorted(path for path in session_root.rglob("*") if path.is_file())
            except OSError:
                continue
            for candidate in files:
                if not _is_allowed_session_file(
                    root=root,
                    session_root=session_root,
                    candidate=candidate,
                ):
                    continue
                session_count += 1
                raw_age = _raw_age_days(candidate, now=clock)
                if raw_age is None or raw_age < retention_days:
                    continue
                candidates.append(
                    SessionCandidate(
                        provider=store.provider,
                        path=str(candidate),
                        relative_path=str(candidate.relative_to(root)),
                        size_bytes=candidate.stat().st_size,
                        age_days=round(raw_age, 1),
                    )
                )

        roots.append(
            SessionRootReport(
                provider=store.provider,
                path=str(root),
                exists=True,
                size_bytes=_size_bytes(root),
                age_days=_age_days(root, now=clock),
                session_files=session_count,
            )
        )
    return roots, candidates


def apply_retention(
    *,
    candidates: list[SessionCandidate],
    home: Path,
    archive_root: Path,
    action: Literal["archive", "delete"],
    retention_days: float,
) -> list[dict[str, object]]:
    """Archive or delete freshly revalidated allowlisted session files."""
    if os.environ.get(APPLY_ENV) != "1":
        raise PermissionError(f"--apply requires {APPLY_ENV}=1")

    store_by_provider = {store.provider: store for store in SESSION_STORES}
    results: list[dict[str, object]] = []
    for candidate in candidates:
        store = store_by_provider.get(candidate.provider)
        if store is None:
            results.append({"path": candidate.path, "action": "skipped", "reason": "unknown provider"})
            continue
        root = home / store.home_directory
        session_roots = [root / item for item in store.session_directories]
        path = Path(candidate.path)
        allowed_root = next(
            (
                session_root
                for session_root in session_roots
                if _is_allowed_session_file(root=root, session_root=session_root, candidate=path)
            ),
            None,
        )
        if allowed_root is None:
            results.append(
                {"path": candidate.path, "action": "skipped", "reason": "outside session allowlist"}
            )
            continue
        current_age = _raw_age_days(path, now=time.time())
        if current_age is None or current_age < retention_days:
            results.append(
                {"path": candidate.path, "action": "skipped", "reason": "file is no longer stale"}
            )
            continue
        if action == "delete":
            path.unlink()
            results.append({"path": candidate.path, "action": "deleted"})
            continue

        destination = archive_root / candidate.provider / candidate.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            results.append(
                {"path": candidate.path, "action": "skipped", "reason": "archive destination exists"}
            )
            continue
        shutil.move(str(path), str(destination))
        results.append({"path": candidate.path, "action": "archived", "archive_path": str(destination)})
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-days", type=float, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--apply", action="store_true", help=f"Mutate only with {APPLY_ENV}=1.")
    parser.add_argument(
        "--action",
        choices=("archive", "delete"),
        default="archive",
        help="Apply action; archive is the default.",
    )
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.retention_days < 0:
        raise SystemExit("--retention-days must be non-negative")
    if args.apply and os.environ.get(APPLY_ENV) != "1":
        print(f"--apply requires {APPLY_ENV}=1", file=sys.stderr)
        return 2

    home = Path.home()
    roots, candidates = inventory_home_sessions(home=home, retention_days=args.retention_days)
    results: list[dict[str, object]] = []
    mode = "dry_run"
    if args.apply:
        mode = args.action
        results = apply_retention(
            candidates=candidates,
            home=home,
            archive_root=args.archive_root.expanduser(),
            action=args.action,
            retention_days=args.retention_days,
        )
    else:
        results = [{"path": candidate.path, "action": "would_" + args.action} for candidate in candidates]

    payload = {
        "schema": "home-session-inventory.v1",
        "mode": mode,
        "retention_days": args.retention_days,
        "roots": [asdict(root) for root in roots],
        "candidates": [asdict(candidate) for candidate in candidates],
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Home session inventory ({mode}; stale >= {args.retention_days:g} days)")
    for root in roots:
        size = "unknown" if root.size_bytes is None else str(root.size_bytes)
        age = "unknown" if root.age_days is None else f"{root.age_days:g}d"
        print(f"  {root.provider}: {root.path} size={size}B age={age} sessions={root.session_files}")
    for result in results:
        print(f"  {result['action']}: {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
