"""Expire preserved task entries by recorded preservation time only (C-2428)."""

import argparse
import contextlib
import errno
import json
import os
import stat
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.nofollow_walk import ComponentOpenError, open_directory_component
from scripts.common.task_scratch import ContainmentError, _remove_invocation_dir, fd_mount_id
from scripts.fleet.post_task_reap import _TERMINAL_STATUSES
from scripts.hygiene.batch_state_retention import default_batch_root


def directory(path: Path) -> int:
    """Open every ancestor separately, rejecting symlinks even above batch_state."""
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.absolute().parts[1:]:
            child = open_directory_component(fd, part)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_at(parent: int, name: str) -> str:
    info = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("nonregular_record")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    with os.fdopen(fd, encoding="utf-8") as handle:
        if (info.st_dev, info.st_ino) != (os.fstat(fd).st_dev, os.fstat(fd).st_ino):
            raise ValueError("record_changed")
        return handle.read()


def read_text(path: Path) -> str:
    parent = directory(path.parent)
    try:
        return read_at(parent, path.name)
    finally:
        os.close(parent)


def measure(fd: int) -> tuple[int, bool]:
    """Sum lstat sizes including directories and links; never traverse links."""
    total, unsafe = os.fstat(fd).st_size, False
    for name in os.listdir(fd):
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = open_directory_component(fd, name)
            try:
                if fd_mount_id(child) is None or fd_mount_id(child) != fd_mount_id(fd):
                    raise ValueError("mount_boundary")
                size, linked = measure(child)
            finally:
                os.close(child)
            total += size
            unsafe |= linked
        else:
            total += info.st_size
            unsafe |= not stat.S_ISREG(info.st_mode)
    return total, unsafe


def eligible(fd: int, name: str, batch: Path, cutoff: datetime) -> str | None:
    """Unknown provenance and unresolved retention always keep the entire entry."""
    try:
        task = json.loads(read_text(batch / "tasks" / f"{name}.json"))
    except (OSError, ValueError, ComponentOpenError):
        return "task_unreadable"
    if not isinstance(task, dict) or task.get("task_id") != name or task.get("status") not in _TERMINAL_STATUSES:
        return "task_state"
    pin = task.get("preserved_artifacts") or {}
    if not isinstance(pin, dict) or task.get("keep_worktree") or pin.get("retention_disposition") == "retained":
        return "pin"
    children = os.listdir(fd)
    manifests = sorted(child for child in children if child.endswith(".manifest.json"))
    if not manifests:
        return "missing_manifest"
    records = {}
    for manifest in manifests:
        try:
            record = json.loads(read_at(fd, manifest))
        except (OSError, ValueError):
            return "manifest_unreadable"
        if not isinstance(record, dict) or record.get("task_id") != name:
            return "manifest_identity"
        records[manifest.removesuffix(".manifest.json")] = record
    for child in children:
        if child not in records and not child.endswith(".manifest.json"):
            return "missing_manifest"
        if child.startswith("held-") and child in records and records[child].get("retention_disposition") != "released":
            return "held"
    for record in records.values():
        if record.get("retention_disposition") == "retained" and not (pin.get("retention_disposition") == "released" and pin.get("run_nonce") == record.get("run_nonce")):
            return "pin"
        stamp = record.get("preserved_at") or record.get("recorded_at") or record.get("created_at")
        if not isinstance(stamp, str):
            return "timestamp_unknown"
        preserved = datetime.fromisoformat(stamp)
        if preserved.tzinfo is None:
            return "timestamp_unknown"
        if preserved >= cutoff:
            return "fresh"
    return None


def run(batch: Path, keep_list: Path, reports: Path, *, apply: bool = False) -> int:
    root = directory(batch / "preserved")
    try:
        try:
            keep = set(read_text(keep_list).splitlines())
        except FileNotFoundError:
            keep = set()
        except (OSError, ValueError, ComponentOpenError, UnicodeError):
            keep = None
        parent = directory(reports.parent)
        try:
            with contextlib.suppress(FileExistsError):
                os.mkdir(reports.name, 0o700, dir_fd=parent)
        finally:
            os.close(parent)
        report_fd = directory(reports)
        try:
            receipt_name = f"preserved-retention-{time.time_ns()}.jsonl"
            receipt_fd = os.open(receipt_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=report_fd)
        finally:
            os.close(report_fd)
        counts, sizes = Counter(), Counter()
        cutoff = datetime.now(UTC) - timedelta(days=3)
        with os.fdopen(receipt_fd, "w", encoding="utf-8") as receipt:
            for name in sorted(os.listdir(root)):
                size, result = 0, "skipped:unknown"
                try:
                    info = os.stat(name, dir_fd=root, follow_symlinks=False)
                    size = info.st_size
                    if not stat.S_ISDIR(info.st_mode):
                        reason = "symlink" if stat.S_ISLNK(info.st_mode) else "not_directory"
                    else:
                        child = open_directory_component(root, name)
                        try:
                            size, unsafe = measure(child)
                            reason = "symlink_or_special" if unsafe else None
                            reason = reason or ("keep_list_unreadable" if keep is None else "keep_list" if name in keep else None)
                            reason = reason or eligible(child, name, batch, cutoff)
                        finally:
                            os.close(child)
                    result = f"skipped:{reason}" if reason else "skipped:dry_run"
                    if not reason and apply:
                        _remove_invocation_dir(root, name, namespace=batch / "preserved", expected_dev=info.st_dev, expected_ino=info.st_ino)
                        result = "deleted"
                except OSError as exc:
                    result = f"error:{exc.errno or errno.EIO}"
                except (ValueError, TypeError, KeyError, ComponentOpenError, ContainmentError):
                    result = "skipped:unreadable_or_invalid_record"
                receipt.write(json.dumps({"name": name, "bytes": size, "result": result}) + "\n")
                receipt.flush()
                os.fsync(receipt.fileno())
                counts[result] += 1
                sizes[result] += size
        print(json.dumps({"mode": "apply" if apply else "dry-run", "counts": counts, "bytes": sizes, "receipt": str(reports / receipt_name)}))
        return int(keep is None or any(key.startswith("error:") for key in counts))
    finally:
        os.close(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete direct preserved task entries with verified times older than 3 days.\nUse for evidence retention; unknown times, live tasks and pins are kept. Default: DRY-RUN.\nManifest preserved_at/recorded_at/created_at must be ISO 8601 with a timezone; every manifest must be old.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.preserved_retention\n  .venv/bin/python -m scripts.hygiene.preserved_retention --apply\nOutputs: one JSON-line receipt per entry under batch_state/reports/; one stdout summary.\nOnly --apply deletes; no Git operations or archives. Receipts include lstat bytes and typed results.\nExit codes: 0 scan complete (skips allowed); 1 I/O/deletion error or unreadable keep-list; 2 invalid arguments/configuration.\nRelated: C-2428; docs/runbooks/tmp-retention.md. Legacy manifests without recorded preservation times are kept.",
    )
    parser.add_argument("--batch-root", type=Path, help="State root (default: primary checkout batch_state; example fixture/batch_state).")
    parser.add_argument("--keep-list", type=Path, help="Plain entry names, one per line; absent = empty (default: batch_state/preserved-keep.txt).")
    parser.add_argument("--reports-dir", type=Path, help="Receipt directory (default: batch_state/reports; example worktree/batch_state/reports).")
    parser.add_argument("--apply", action="store_true", help="Delete eligible entries (default: dry-run, receipts only).")
    args = parser.parse_args(argv)
    batch = (args.batch_root or default_batch_root()).absolute()
    try:
        return run(batch, args.keep_list or batch / "preserved-keep.txt", args.reports_dir or batch / "reports", apply=args.apply)
    except (OSError, ValueError, ComponentOpenError) as exc:
        print(f"preserved-retention: {type(exc).__name__}", file=sys.stderr)
        return 1 if isinstance(exc, OSError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
