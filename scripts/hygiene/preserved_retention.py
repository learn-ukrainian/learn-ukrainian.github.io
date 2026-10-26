"""Expire preserved task entries by preservation proof or content age."""

import argparse
import contextlib
import errno
import json
import os
import stat
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.nofollow_walk import ComponentOpenError, open_directory_component
from scripts.common.task_scratch import ContainmentError, _remove_invocation_dir, fd_mount_id
from scripts.fleet import ignored_task_output, pr_identity
from scripts.fleet.post_task_reap import _TERMINAL_STATUSES
from scripts.hygiene.batch_state_retention import default_batch_root

RELEASE_AGE_DAYS = 3


@lru_cache(maxsize=4096)
def landed_reason(head: str, branch: str) -> str | None:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(["git", "merge-base", "--is-ancestor", head, "origin/main"], cwd=repo_root, env=pr_identity._sanitized_env(), capture_output=True, timeout=15, check=False)
        if result.returncode == 0:
            return "ancestor_of_main"
        repo = pr_identity.resolve_repo_slug(repo_root)
        opened, error = pr_identity.probe_open_pr_for_branch(repo_root=repo_root, repo=repo, branch=branch)
        if opened is not False or error:
            return None
        result = pr_identity._run_gh(["gh", "pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json", "number,state,headRefName,headRefOid,isCrossRepository"], cwd=repo_root, timeout=30)
        if result.returncode != 0:
            return None
        rows = json.loads(result.stdout)
        if not isinstance(rows, list) or not rows:
            return None
        for row in rows:
            if not isinstance(row, dict) or type(row.get("number")) is not int or row["number"] <= 0 or row.get("headRefName") != branch or row.get("headRefOid") != head or row.get("isCrossRepository") is not False or row.get("state") not in {"MERGED", "CLOSED"}:
                return None
        return "pushed_merged" if any(row["state"] == "MERGED" for row in rows) else "pushed_closed"
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def delivery_is_clean(task: dict) -> bool:
    return task.get("worktree_dirty_on_exit") is False


def release_reason(task: dict, cutoff: datetime) -> str | None:
    if task.get("status") not in {"done", "failed", "timeout", "crashed", "cancelled", "no_deliverable"}:
        return None
    stamp = task.get("finished_at")
    try:
        finished = datetime.fromisoformat(stamp) if isinstance(stamp, str) else None
    except ValueError:
        return None
    if finished is None or finished.tzinfo is None or finished >= cutoff or not delivery_is_clean(task):
        return None
    if task.get("mode") == "read-only" and task.get("push_state") == "not_applicable":
        return "released:read_only" if type(task.get("commits_ahead")) is int and task["commits_ahead"] == 0 else None
    head, branch = task.get("head_sha"), task.get("branch") or task.get("worktree_branch")
    if task.get("push_state") != "pushed" or not isinstance(head, str) or len(head) != 40 or any(c not in "0123456789abcdef" for c in head) or head != task.get("remote_head_sha") or not isinstance(branch, str) or not branch:
        return None
    reason = landed_reason(head, branch)
    return f"released:{reason}" if reason else None


def manifest_release_proven(task: dict, pin: dict, record: dict, batch: Path, child: str) -> bool:
    """Accept the release writer's proof only for this manifest's verified bytes."""
    release = pin.get("retention_release")
    if pin.get("retention_disposition") != "released" or not isinstance(release, dict):
        return False
    nonce, digest = task.get("run_nonce"), pin.get("retrieval_proof_sha256")
    if not isinstance(nonce, str) or not nonce or not isinstance(digest, str) or not digest:
        return False
    if pin.get("task_id") != task["task_id"] or pin.get("run_nonce") != nonce:
        return False
    if record.get("schema") != ignored_task_output.PRESERVED_ARTIFACTS_SCHEMA or record.get("location") != f"batch_state/preserved/{task['task_id']}/{child}":
        return False
    if release.get("owner") != task["task_id"] or release.get("run_nonce") != nonce or release.get("retrieval_proof_sha256") != digest:
        return False
    fields = ("schema", "task_id", "run_nonce", "location", "content_sha256", "paths", "retrieval_proof_sha256")
    if any(pin.get(key) != record.get(key) for key in fields):
        return False
    try:
        return ignored_task_output.verify_retrieval(batch.parent, record) == digest
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        return False


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


def measure(fd: int, *, newest: list[int] | None = None) -> tuple[int, bool]:
    """Sum lstat sizes including directories and links; never traverse links."""
    info = os.fstat(fd)
    total, unsafe = info.st_size, False
    if newest is not None:
        newest[0] = max(newest[0], info.st_mtime_ns)
    for name in os.listdir(fd):
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if newest is not None:
            newest[0] = max(newest[0], info.st_mtime_ns)
        if stat.S_ISDIR(info.st_mode):
            child = open_directory_component(fd, name)
            try:
                if fd_mount_id(child) is None or fd_mount_id(child) != fd_mount_id(fd):
                    raise ValueError("mount_boundary")
                size, linked = measure(child, newest=newest)
            finally:
                os.close(child)
            total += size
            unsafe |= linked
        else:
            total += info.st_size
            unsafe |= not stat.S_ISREG(info.st_mode)
    return total, unsafe


def task_record(batch: Path, name: str) -> tuple[dict, bool]:
    try:
        return json.loads(read_text(batch / "tasks" / f"{name}.json")), False
    except FileNotFoundError:
        return json.loads(read_text(batch / "tasks" / "archive" / f"{name}.json")), True


def keep_names(path: Path) -> set[str]:
    return {line.strip() for line in read_text(path).splitlines() if line.strip() and not line.lstrip().startswith("#")}


def eligible(fd: int, name: str, batch: Path, cutoff: datetime, release_cutoff: datetime) -> str | None:
    """Unknown provenance and unresolved retention always keep the entire entry."""
    try:
        task, archived = task_record(batch, name)
    except (OSError, ValueError, ComponentOpenError):
        return "task_unreadable"
    if not isinstance(task, dict) or task.get("task_id") != name or task.get("status") not in _TERMINAL_STATUSES:
        return "task_state"
    pin = task.get("preserved_artifacts") or {}
    if not isinstance(pin, dict):
        return "pin"
    pinned = bool(task.get("keep_worktree") or pin.get("retention_disposition") == "retained")
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
        if archived and (not isinstance(task.get("run_nonce"), str) or not task["run_nonce"] or record.get("run_nonce") != task["run_nonce"]):
            return "manifest_identity"
        records[manifest.removesuffix(".manifest.json")] = record
    held = set()
    for child in children:
        if child not in records and not child.endswith(".manifest.json"):
            return "missing_manifest"
        if child.startswith("held-") and child in records:
            if records[child].get("schema") != "runtime-held-work.v1":
                return "held"
            if not manifest_release_proven(task, pin, records[child], batch, child):
                held.add(child)
    retained = {child for child, record in records.items() if record.get("retention_disposition") == "retained" and not manifest_release_proven(task, pin, record, batch, child)}
    released = None
    if pinned or held or retained:
        released = release_reason(task, release_cutoff)
        if not released:
            return "pin" if pinned else "held" if held else "pin"
        if any(not isinstance(task.get("run_nonce"), str) or not task["run_nonce"] or record.get("run_nonce") != task["run_nonce"] for record in records.values()):
            return "manifest_identity"
    for child, record in records.items():
        if released and (pinned or child in held or child in retained):
            continue
        stamp = record.get("preserved_at") or record.get("recorded_at") or record.get("created_at")
        if not isinstance(stamp, str):
            return "timestamp_unknown"
        preserved = datetime.fromisoformat(stamp)
        if preserved.tzinfo is None:
            return "timestamp_unknown"
        if preserved >= cutoff:
            return "fresh"
    return released


def child_set(fd: int) -> tuple:
    """Bind classification to child names and manifest identities and timestamps."""
    children = []
    for name in sorted(os.listdir(fd)):
        identity = None
        if name.endswith(".manifest.json"):
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            identity = (info.st_dev, info.st_ino, info.st_mtime_ns)
        children.append((name, identity))
    return tuple(children)


def expire_entry(root: int, name: str, batch: Path, keep_list: Path | None, keep: set[str] | None, cutoff_ns: int, apply: bool, allow_empty: bool) -> dict:
    row = {"name": name, "bytes": 0, "newest_mtime_ns": None}
    snapshots = []
    for removing in (False, True) if apply else (False,):
        try:
            info = os.stat(name, dir_fd=root, follow_symlinks=False)
            newest, size = [info.st_mtime_ns], info.st_size
            row["bytes"] = size
            reason = "symlink" if stat.S_ISLNK(info.st_mode) else None
            if stat.S_ISDIR(info.st_mode):
                child = open_directory_component(root, name)
                try:
                    if fd_mount_id(child) is None or fd_mount_id(child) != fd_mount_id(root):
                        raise ValueError("mount_boundary")
                    size, unsafe = measure(child, newest=newest)
                    reason = "symlink_or_special" if unsafe else None
                finally:
                    os.close(child)
            elif not stat.S_ISREG(info.st_mode):
                reason = reason or "not_regular"
            row.update(bytes=size, newest_mtime_ns=newest[0])
        except (OSError, ValueError, ComponentOpenError):
            row.update(result="skipped:age_unreadable", reason="age_unreadable", newest_mtime_ns=None)
            return row
        if removing:
            try:
                keep = keep_names(keep_list or batch / "preserved-keep.txt")
            except FileNotFoundError:
                keep = set() if keep_list is None and allow_empty else None
            except (OSError, ValueError, ComponentOpenError, UnicodeError):
                keep = None
        reason = reason or ("keep_list_unreadable" if keep is None else "keep_list" if name in keep else None)
        reason = reason or ("fresh" if newest[0] >= cutoff_ns else None)
        snapshot = (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns, size, newest[0])
        if removing and snapshots[0] != snapshot:
            reason = reason or "changed_before_removal"
        if reason:
            return {**row, "result": f"skipped:{reason}", "reason": reason}
        snapshots.append(snapshot)
    if apply:
        try:
            if stat.S_ISDIR(info.st_mode):
                _remove_invocation_dir(root, name, namespace=batch / "preserved", expected_dev=info.st_dev, expected_ino=info.st_ino)
            else:
                os.unlink(name, dir_fd=root)
        except (OSError, ContainmentError) as exc:
            return {**row, "result": f"error:{getattr(exc, 'errno', None) or errno.EIO}", "reason": "removal_failed"}
    return {**row, "result": "deleted" if apply else "skipped:dry_run", "reason": "expired"}


def run(batch: Path, keep_list: Path | None, reports: Path, *, apply: bool = False, allow_empty_keep_list: bool = False, expire_older_than_hours: int | None = None) -> int:
    root = directory(batch / "preserved")
    try:
        try:
            keep = keep_names(keep_list or batch / "preserved-keep.txt")
        except FileNotFoundError:
            keep = set() if keep_list is None and (not apply or allow_empty_keep_list) else None
            if keep is None:
                detail = "explicit path is absent" if keep_list is not None else "default path is absent; --apply requires --allow-empty-keep-list"
                print(f"keep-list unreadable: {detail}", file=sys.stderr)
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
        release_cutoff = datetime.now(UTC) - timedelta(days=RELEASE_AGE_DAYS)
        cutoff_ns = time.time_ns() - expire_older_than_hours * 3600 * 10**9 if expire_older_than_hours is not None else 0
        with os.fdopen(receipt_fd, "w", encoding="utf-8") as receipt:
            for name in sorted(os.listdir(root)):
                if expire_older_than_hours is not None:
                    row = expire_entry(root, name, batch, keep_list, keep, cutoff_ns, apply, allow_empty_keep_list)
                    receipt.write(json.dumps({**row, "decision": row["result"].split(":")[0]}) + "\n")
                    receipt.flush()
                    os.fsync(receipt.fileno())
                    counts[row["result"]] += 1
                    sizes[row["result"]] += row["bytes"]
                    continue
                size, result, released = 0, "skipped:unknown", None
                try:
                    info = os.stat(name, dir_fd=root, follow_symlinks=False)
                    size = info.st_size
                    if not stat.S_ISDIR(info.st_mode):
                        reason = "symlink" if stat.S_ISLNK(info.st_mode) else "not_directory"
                    else:
                        child = open_directory_component(root, name)
                        try:
                            classified = child_set(child)
                            size, unsafe = measure(child)
                            reason = "symlink_or_special" if unsafe else None
                            reason = reason or ("keep_list_unreadable" if keep is None else "keep_list" if name in keep else None)
                            task_before = None
                            with contextlib.suppress(OSError, ValueError, ComponentOpenError):
                                task_before = task_record(batch, name)
                            reason = reason or eligible(child, name, batch, cutoff, release_cutoff)
                        finally:
                            os.close(child)
                    if reason and reason.startswith("released:"):
                        released, reason = reason, None
                    result = f"skipped:{reason}" if reason else released or "skipped:dry_run"
                    if not reason and apply:
                        child = open_directory_component(root, name)
                        try:
                            if child_set(child) != classified:
                                result, released = "skipped:changed_during_scan", None
                            else:
                                try:
                                    current_task = task_record(batch, name)
                                    try:
                                        current_keep = keep_names(keep_list or batch / "preserved-keep.txt")
                                    except FileNotFoundError:
                                        if keep_list is not None or not allow_empty_keep_list:
                                            raise
                                        current_keep = set()
                                    changed = current_task != task_before or name in current_keep
                                except (OSError, ValueError, ComponentOpenError):
                                    changed = True
                                if changed:
                                    result, released = "skipped:changed_before_removal", None
                                else:
                                    _remove_invocation_dir(root, name, namespace=batch / "preserved", expected_dev=info.st_dev, expected_ino=info.st_ino)
                                    result = "deleted"
                        finally:
                            os.close(child)
                except (OSError, ContainmentError) as exc:
                    result = f"error:{getattr(exc, 'errno', None) or errno.EIO}"
                except (ValueError, TypeError, KeyError, ComponentOpenError):
                    result = "skipped:unreadable_or_invalid_record"
                receipt.write(json.dumps({"name": name, "bytes": size, "result": result, **({"reason": released} if released else {})}) + "\n")
                receipt.flush()
                os.fsync(receipt.fileno())
                counts[result] += 1
                sizes[result] += size
        print(json.dumps({"mode": "apply" if apply else "dry-run", "counts": counts, "bytes": sizes, "receipt": str(reports / receipt_name)}))
        return int(keep is None or "skipped:keep_list_unreadable" in counts or any(key.startswith("error:") for key in counts))
    finally:
        os.close(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete direct preserved task entries with verified times older than 3 days.\nUse --expire-older-than-hours N for age-only residue expiry without proof rules.\nDefault evidence retention keeps unknown times and live tasks. Default: DRY-RUN.\nOrdinary manifests need old ISO 8601 preservation times; held/pinned entries need terminal task identity, old finished_at and read-only or pushed/landed proof.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.preserved_retention\n  .venv/bin/python -m scripts.hygiene.preserved_retention --apply\nOutputs: one JSON-line receipt per entry under batch_state/reports/; one stdout summary.\nMissing explicit keep-lists refuse all deletion. An absent default is empty only in dry-run; --apply refuses it unless --allow-empty-keep-list is passed.\nOnly --apply deletes; Git ancestry checks are local and PR probes are read-only. Receipts include lstat bytes and typed release reasons.\nExit codes: 0 scan complete (skips allowed); 1 I/O/deletion error or unreadable keep-list; 2 invalid arguments/configuration.\nRelated: C-2428; docs/runbooks/tmp-retention.md. Without backstop, unknown provenance is kept; RELEASE_AGE_DAYS configures held/pin age (default 3 days).",
    )
    parser.add_argument("--batch-root", type=Path, help="State root (default: primary checkout batch_state; example fixture/batch_state).")
    parser.add_argument("--keep-list", type=Path, help="Plain entry names, one per line (example keep.txt; default: batch_state/preserved-keep.txt). Explicit paths must be readable. An absent default is empty in dry-run; apply requires --allow-empty-keep-list.")
    parser.add_argument("--reports-dir", type=Path, help="Receipt directory (default: batch_state/reports; example worktree/batch_state/reports).")
    parser.add_argument("--apply", action="store_true", help="Delete eligible entries (default: dry-run, receipts only).")
    parser.add_argument("--allow-empty-keep-list", action="store_true", help="Allow --apply with an absent DEFAULT keep-list (default: off; example --apply --allow-empty-keep-list). Explicit missing or unreadable paths still refuse deletion.")
    parser.add_argument("--expire-older-than-hours", type=int, metavar="N", help="Backstop: expire entries whose newest content mtime is strictly older than N positive integer hours (example 24; default: off). Ignores task, landed, held, pin and release proof; honors keep-list and refuses symlinks. Only --apply deletes; receipts include newest_mtime_ns, decision and reason.")
    args = parser.parse_args(argv)
    if args.expire_older_than_hours is not None and args.expire_older_than_hours <= 0:
        parser.error("--expire-older-than-hours must be a positive integer")
    batch = (args.batch_root or default_batch_root()).absolute()
    try:
        return run(batch, args.keep_list, args.reports_dir or batch / "reports", apply=args.apply, allow_empty_keep_list=args.allow_empty_keep_list, expire_older_than_hours=args.expire_older_than_hours)
    except (OSError, ValueError, ComponentOpenError) as exc:
        print(f"preserved-retention: {type(exc).__name__}", file=sys.stderr)
        return 1 if isinstance(exc, OSError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
