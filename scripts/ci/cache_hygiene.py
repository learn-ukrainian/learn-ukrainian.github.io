#!/usr/bin/env python3
"""Prune dead GitHub Actions cache entries so the repository stays under 10 GB (#9101).

Two entry kinds are pruned; every other entry is left alone.

- ``codeql-trap-<...>-<commit sha>``: CodeQL default setup saves one TRAP
  cache (~247 MB) per main commit and restores only the newest one per
  language and CodeQL version. On ``refs/heads/main`` the newest entry per
  family (the key without its commit sha) is kept by ``created_at``; the rest
  are deleted. TRAP entries on any other ref are deleted.
- ``setup-uv-<...>-<lock hash>`` on ``refs/heads/main``: the entry for the
  current ``requirements-lock.txt`` and the newest entry per family are kept.
  A superseded entry is deleted only once it has not been read for
  ``--uv-grace-hours`` (default 24), so PRs still based on the previous lock
  keep restoring it for a day. ``last_accessed_at`` is never earlier than
  ``created_at``, so this is at least as conservative as an age check.

The default is a dry run that prints the plan. ``--apply`` deletes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

MAIN_REF = "refs/heads/main"
PER_PAGE = 100
MAX_PAGES = 50
GH_TIMEOUT_SECONDS = 60
DEFAULT_UV_GRACE_HOURS = 24.0

CODEQL_TRAP_RE = re.compile(r"^(codeql-trap-.+-)[0-9a-f]{40}$")
SETUP_UV_RE = re.compile(r"^(setup-uv-.+-)([0-9a-f]{64})$")

GhApi = Callable[[list[str]], str]


@dataclass(frozen=True)
class CacheEntry:
    id: int
    key: str
    ref: str
    size_in_bytes: int
    created_at: datetime
    last_accessed_at: datetime

    @classmethod
    def from_api(cls, raw: dict) -> CacheEntry:
        return cls(
            id=int(raw["id"]),
            key=str(raw["key"]),
            ref=str(raw["ref"]),
            size_in_bytes=int(raw["size_in_bytes"]),
            created_at=_parse_time(raw["created_at"]),
            last_accessed_at=_parse_time(raw["last_accessed_at"]),
        )


@dataclass(frozen=True)
class Deletion:
    entry: CacheEntry
    reason: str


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def lock_hash(lock_file: Path) -> str:
    """Hash setup-uv puts at the end of its cache key for ``cache-dependency-glob``.

    Same algorithm as ``hashFiles()``: SHA-256 over each matched file's
    SHA-256 digest. The composite action matches exactly one file.
    """
    file_digest = hashlib.sha256(lock_file.read_bytes()).digest()
    return hashlib.sha256(file_digest).hexdigest()


def _gh_api(args: list[str]) -> str:
    result = subprocess.run(
        ["gh", "api", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    return result.stdout


def list_caches(repo: str, gh_api: GhApi = _gh_api) -> list[CacheEntry]:
    """Every cache entry in the repository, following page links until exhausted."""
    entries: list[CacheEntry] = []
    total: int | None = None
    for page in range(1, MAX_PAGES + 1):
        body = json.loads(gh_api([f"repos/{repo}/actions/caches?per_page={PER_PAGE}&page={page}"]))
        total = int(body["total_count"])
        batch = body["actions_caches"]
        entries.extend(CacheEntry.from_api(raw) for raw in batch)
        if not batch or len(entries) >= total:
            break
    else:
        raise RuntimeError(f"cache list did not end within {MAX_PAGES} pages")
    if total is not None and len(entries) < total:
        # Entries saved or evicted while paging shift the pages; the plan is
        # still safe because deletions go by id, but say so.
        print(f"note: listed {len(entries)} of {total} entries", file=sys.stderr)
    return entries


def plan_deletions(
    entries: Iterable[CacheEntry],
    current_lock_hash: str,
    now: datetime,
    uv_grace: timedelta = timedelta(hours=DEFAULT_UV_GRACE_HOURS),
) -> list[Deletion]:
    trap_families: dict[str, list[CacheEntry]] = {}
    uv_families: dict[str, list[CacheEntry]] = {}
    deletions: list[Deletion] = []

    for entry in entries:
        if entry.key.startswith("codeql-trap-"):
            if entry.ref != MAIN_REF:
                deletions.append(Deletion(entry, f"CodeQL TRAP cache on {entry.ref}, not main"))
                continue
            match = CODEQL_TRAP_RE.match(entry.key)
            if match:
                trap_families.setdefault(match.group(1), []).append(entry)
        elif entry.ref == MAIN_REF:
            match = SETUP_UV_RE.match(entry.key)
            if match:
                uv_families.setdefault(match.group(1), []).append(entry)

    for family, members in trap_families.items():
        newest = max(members, key=lambda e: (e.created_at, e.id))
        for entry in members:
            if entry is not newest:
                deletions.append(Deletion(entry, f"superseded by newest {family}* ({newest.key[len(family) :]})"))

    for members in uv_families.values():
        newest = max(members, key=lambda e: (e.created_at, e.id))
        for entry in members:
            if entry is newest or entry.key.endswith(f"-{current_lock_hash}"):
                continue
            idle = now - entry.last_accessed_at
            if idle >= uv_grace:
                hours = idle.total_seconds() / 3600
                deletions.append(Deletion(entry, f"superseded uv lock, unread for {hours:.1f} h"))

    return sorted(deletions, key=lambda d: (d.entry.ref, d.entry.key))


def _gb(size: int) -> str:
    return f"{size / 1e9:.2f} GB"


def render_plan(entries: list[CacheEntry], deletions: list[Deletion], apply: bool) -> str:
    total = sum(e.size_in_bytes for e in entries)
    freed = sum(d.entry.size_in_bytes for d in deletions)
    lines = [
        f"{'DELETE' if apply else 'would delete'} {d.entry.ref} {d.entry.key} ({_gb(d.entry.size_in_bytes)}): {d.reason}"
        for d in deletions
    ]
    lines.append(
        f"total: {len(entries)} entries, {_gb(total)}; "
        f"delete {len(deletions)} entries, {_gb(freed)}; "
        f"remaining {len(entries) - len(deletions)} entries, {_gb(total - freed)}"
    )
    return "\n".join(lines)


def delete_entries(repo: str, deletions: list[Deletion], gh_api: GhApi = _gh_api) -> list[str]:
    """Delete by id; return the keys that failed (an entry already gone is not a failure)."""
    failed: list[str] = []
    for deletion in deletions:
        try:
            gh_api(["--method", "DELETE", f"repos/{repo}/actions/caches/{deletion.entry.id}"])
        except subprocess.CalledProcessError as exc:
            if "404" in (exc.stderr or ""):
                continue
            print(f"failed to delete {deletion.entry.key}: {(exc.stderr or '').strip()}", file=sys.stderr)
            failed.append(deletion.entry.key)
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--lock-file", type=Path, default=Path("requirements-lock.txt"))
    parser.add_argument("--uv-grace-hours", type=float, default=DEFAULT_UV_GRACE_HOURS)
    parser.add_argument("--apply", action="store_true", help="delete the planned entries (default: dry run)")
    args = parser.parse_args(argv)

    entries = list_caches(args.repo)
    deletions = plan_deletions(
        entries,
        current_lock_hash=lock_hash(args.lock_file),
        now=datetime.now(UTC),
        uv_grace=timedelta(hours=args.uv_grace_hours),
    )
    print(render_plan(entries, deletions, args.apply))
    if not args.apply:
        return 0
    failed = delete_entries(args.repo, deletions)
    if failed:
        print(f"{len(failed)} deletions failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
