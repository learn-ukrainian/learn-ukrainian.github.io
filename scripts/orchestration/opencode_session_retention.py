#!/usr/bin/env python3
"""Remove old OpenCode sessions while idle so SQLite can reuse freed pages.

Deletion and WAL checkpointing need not shrink the main database: SQLite keeps
freed pages on its freelist for later inserts. VACUUM is intentionally not run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SESSION_QUERY = "SELECT id, parent_id AS parent, time_updated AS updated FROM session ORDER BY time_updated ASC"


class RetentionError(RuntimeError):
    """An unsafe or unsuccessful retention run."""


class OpenCodeRunning(RetentionError):
    """Another OpenCode process is active."""


def _run(command: list[str], *, timeout: int = 600) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RetentionError(f"command failed: {command[:3]}: {exc}") from exc
    if result.returncode:
        raise RetentionError(f"command failed ({result.returncode}): {command[:3]}: {result.stderr.strip()}")
    return result.stdout.strip()


def _require_idle() -> None:
    if shutil.which("pgrep") is None:
        raise RetentionError("pgrep is required to verify OpenCode is idle")
    try:
        result = subprocess.run(["pgrep", "-x", "opencode"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RetentionError(f"could not check OpenCode processes: {exc}") from exc
    if result.returncode == 0:
        raise OpenCodeRunning("OpenCode is running; skipping the whole run")
    if result.returncode != 1:
        raise RetentionError(f"pgrep failed ({result.returncode}): {result.stderr.strip()}")


def _database_path(opencode: str) -> Path:
    _require_idle()
    raw = _run([opencode, "db", "path", "--pure"])
    if not raw or "\n" in raw:
        raise RetentionError("OpenCode returned an invalid database path")
    path = Path(raw).expanduser()
    if not path.is_absolute() or path.name != "opencode.db":
        raise RetentionError("OpenCode returned an unexpected database path")
    return path


def _database_bytes(path: Path) -> tuple[int, int]:
    def size(part: Path) -> int:
        return part.stat().st_size if part.is_file() else 0

    try:
        return size(path), size(Path(f"{path}-wal"))
    except OSError as exc:
        raise RetentionError(f"could not measure OpenCode database: {exc}") from exc


def _database_pages(opencode: str) -> tuple[int, int, int]:
    """Read SQLite page statistics through the same read-only CLI DB path as sessions."""
    values: list[int] = []
    for name in ("freelist_count", "page_count", "page_size"):
        raw = _run([opencode, "db", f"PRAGMA {name}", "--format", "json", "--pure"])
        try:
            rows = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RetentionError(f"invalid {name} response: {exc}") from exc
        if (
            not isinstance(rows, list)
            or len(rows) != 1
            or not isinstance(rows[0], dict)
            or type(rows[0].get(name)) is not int
            or rows[0][name] < 0
        ):
            raise RetentionError(f"invalid {name} response")
        values.append(rows[0][name])
    if values[2] == 0 or values[0] > values[1]:
        raise RetentionError("invalid SQLite page statistics")
    return values[0], values[1], values[2]


def _old_session_ids(raw: str, cutoff_ms: int) -> tuple[list[str], list[tuple[str, int]], set[str]]:
    # The CLI db query covers every project and child session in the database.
    if not raw:
        raise RetentionError("opencode db returned no JSON")
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RetentionError(f"invalid JSON from opencode db: {exc}") from exc
    if not isinstance(rows, list):
        raise RetentionError("opencode db did not return a JSON array")
    records: dict[str, tuple[int, str | None]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RetentionError("session list contains a non-object")
        session_id = row.get("id")
        updated = row.get("updated")
        parent = row.get("parent")
        if (
            not isinstance(session_id, str)
            or not session_id.startswith("ses_")
            or not session_id.isascii()
            or not session_id.replace("_", "").isalnum()
        ):
            raise RetentionError("session list contains an invalid session id")
        if session_id in records:
            raise RetentionError("session list contains duplicate session ids")
        if type(updated) is not int or updated < 0:
            raise RetentionError(f"session {session_id} has no valid updated timestamp")
        if parent is not None and (not isinstance(parent, str) or not parent.startswith("ses_")):
            raise RetentionError(f"session {session_id} has an invalid parent id")
        records[session_id] = updated, parent
    depth_cache: dict[str, int] = {}
    root_cache: dict[str, str] = {}

    def depth(session_id: str, visiting: set[str]) -> int:
        if session_id in depth_cache:
            return depth_cache[session_id]
        if session_id in visiting:
            raise RetentionError("session parent graph contains a cycle")
        parent = records[session_id][1]
        if parent not in records:
            result = 0
            root_cache[session_id] = session_id
        else:
            result = 1 + depth(parent, visiting | {session_id})
            root_cache[session_id] = root_cache[parent]
        depth_cache[session_id] = result
        return result

    for session_id in records:
        depth(session_id, set())
    newest_by_root: dict[str, int] = {}
    roots_with_old_sessions: set[str] = set()
    for session_id, (updated, _) in records.items():
        root = root_cache[session_id]
        newest_by_root[root] = max(updated, newest_by_root.get(root, updated))
        if updated < cutoff_ms:
            roots_with_old_sessions.add(root)
    selected = {
        session_id for session_id in records if newest_by_root[root_cache[session_id]] < cutoff_ms
    }
    blocked = sorted(
        (root, newest_by_root[root])
        for root in roots_with_old_sessions
        if newest_by_root[root] >= cutoff_ms
    )
    ordered = sorted(selected, key=lambda session_id: (-depth_cache[session_id], records[session_id][0], session_id))
    return ordered, blocked, set(records)


def retain(*, days: int, dry_run: bool, opencode: str = "opencode", now_ms: int | None = None) -> int:
    if days < 1:
        raise RetentionError("--days must be at least 1")
    now = int(time.time() * 1000) if now_ms is None else now_ms
    cutoff_ms = now - days * 86_400_000
    _require_idle()
    db_path = _database_path(opencode)
    before = _database_bytes(db_path)
    _require_idle()
    before_pages = _database_pages(opencode)
    _require_idle()
    # `session list` is scoped to the current project and defaults to 100 roots.
    # A read-only CLI query is needed for the issue's all-sessions denominator.
    raw = _run([opencode, "db", SESSION_QUERY, "--format", "json", "--pure"])
    selected, blocked, all_ids = _old_session_ids(raw, cutoff_ms)
    print(f"mode={'dry-run' if dry_run else 'apply'} days={days} cutoff_ms={cutoff_ms} selected={len(selected)}")
    print(
        f"before_db_bytes={before[0]} before_wal_bytes={before[1]} before_total_bytes={sum(before)} "
        f"before_freelist_pages={before_pages[0]} before_page_count={before_pages[1]} "
        f"before_page_size={before_pages[2]}"
    )
    for root, newest_updated in blocked:
        print(f"skipped_family_root={root} newest_age_days={(now - newest_updated) / 86_400_000:.2f}")
    deleted_count = 0

    def idle_or_fail() -> None:
        try:
            _require_idle()
        except OpenCodeRunning as exc:
            if deleted_count:
                raise RetentionError(
                    f"OpenCode started after {deleted_count} deletions; retention run is incomplete"
                ) from exc
            raise

    for session_id in selected:
        if dry_run:
            print(f"would_delete={session_id}")
            continue
        idle_or_fail()
        _run([opencode, "session", "delete", session_id, "--pure"])
        deleted_count += 1
        print(f"deleted={session_id}", flush=True)
    if dry_run:
        print("dry-run: no deletion or WAL checkpoint")
    if selected and not dry_run:
        idle_or_fail()
        after_raw = _run([opencode, "db", SESSION_QUERY, "--format", "json", "--pure"])
        _, _, remaining_ids = _old_session_ids(after_raw, cutoff_ms)
        lingering = set(selected) & remaining_ids
        missing_preserved = (all_ids - set(selected)) - remaining_ids
        if lingering or missing_preserved:
            raise RetentionError(
                f"deletion verification failed: old_remaining={len(lingering)} preserved_missing={len(missing_preserved)}"
            )
        idle_or_fail()
        checkpoint = _run([opencode, "db", "PRAGMA wal_checkpoint(TRUNCATE)", "--format", "json", "--pure"])
        try:
            rows = json.loads(checkpoint)
        except json.JSONDecodeError as exc:
            raise RetentionError(f"invalid WAL checkpoint response: {exc}") from exc
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get("busy") != 0:
            raise RetentionError(f"WAL checkpoint did not complete: {checkpoint}")
        print(f"wal_checkpoint={checkpoint}")
    idle_or_fail()
    after = _database_bytes(db_path)
    after_pages = _database_pages(opencode)
    reclaimed = sum(before) - sum(after)
    print(
        f"after_db_bytes={after[0]} after_wal_bytes={after[1]} after_total_bytes={sum(after)} "
        f"after_freelist_pages={after_pages[0]} after_page_count={after_pages[1]} "
        f"after_page_size={after_pages[2]} reclaimed_bytes={reclaimed}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Delete OpenCode session families whose every session is older than N days using the OpenCode CLI.\nFamilies with recent sessions are skipped; use on an idle host and inspect with --dry-run first.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/orchestration/opencode_session_retention.py --dry-run\n  .venv/bin/python scripts/orchestration/opencode_session_retention.py --days 14\nOutputs: read-only OpenCode CLI queries for sessions and SQLite page statistics; stdout/journal IDs, DB/WAL bytes and freelist pages before/after. Apply deletes via CLI and checkpoints the WAL. Freed pages are reused by later inserts; the main DB need not shrink. VACUUM is intentionally not run.\nExit codes: 0 successful deletion/checkpoint, dry run, or idle skip; 1 CLI, process-check, verification, or checkpoint failure.\nRelated: packaging/systemd/README.md; issue #8920.",
    )
    parser.add_argument("--days", type=int, default=7, help="retention age in whole days (default: 7; example: 14)")
    parser.add_argument(
        "--dry-run", action="store_true", help="list eligible session IDs and skipped families without deleting or checkpointing (default: apply)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return retain(days=args.days, dry_run=args.dry_run)
    except OpenCodeRunning as exc:
        print(f"SKIP: {exc}")
        return 0
    except RetentionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
