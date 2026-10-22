"""Sweep expired preserved evidence and old backups under batch_state by TTL (#11418).

Dry run is the default. Apply removes an entry only when it is older than its
configured TTL by the newest write anywhere below it, no unsettled task record
references it, it is not held in ``batch_state_retention.json``, its owner is
known, and it is a readable tree that is neither a symlink nor a mount point.
The task inventory and hold list are reloaded before each deletion, and an
unreadable guard preserves the entry; a hold on any archive member protects the
whole group, and only a real archive can be the protected newest one. A
removal that fails after an earlier member was deleted is reported as a
partial deletion naming the deleted members, their bytes and the failure.
The TTL numbers live in one JSON file beside this module; the shipped values
are ``UNAPPROVED`` and the apply path refuses while any value is unapproved.
Use this only for ``batch_state/preserved`` and ``batch_state/backups``: task
records, reports, branch archives, corpus and database data are out of scope.
"""

from __future__ import annotations

import argparse
import errno
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.task_store_paths import tasks_dir
from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.batch_state_retention import RETENTION_LIST, load_holds

SCHEMA = "batch-state-ttl-sweep.v1"
RECEIPT_SCHEMA = "batch-state-ttl-sweep-receipt.v1"
CONFIG = Path(__file__).with_name("batch_state_ttl_sweep.json")
UNAPPROVED = "UNAPPROVED"
QUARANTINE_PREFIX = sweep.QUARANTINE_PREFIX
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_TTL_UNAPPROVED = 4
_ARCHIVE_SUFFIXES = (".contents.sha256", ".manifest", ".tar.zst", ".tar", ".zst")


class TtlUnapproved(RuntimeError):
    """The apply path needs every configured TTL; a placeholder value refuses it."""


@dataclass(frozen=True)
class RootSpec:
    """One configured root: its TTL, owner source, and backup-only protections."""

    path: Path
    relative: str
    parts: tuple[str, ...]
    ttl_days: float | None
    owner: str | None
    keep_newest_archive: bool
    exclude_names: frozenset[str]


@dataclass
class Entry:
    """One candidate under a configured root, with its evidence and decision."""

    name: str
    members: list[Path]
    relative: str
    owner: str | None
    bytes: int | None
    newest: float
    age_days: float
    reason: str
    decision: str = "preserve"
    identities: list[tuple[int, int]] = field(default_factory=list)
    fingerprints: list[dict[str, tuple[Any, ...]] | None] = field(default_factory=list)
    deleted_members: list[str] = field(default_factory=list)
    deleted_bytes: int = 0
    failed_member: str | None = None

    def row(self) -> dict[str, Any]:
        row = {
            "path": self.relative,
            "owner": self.owner,
            "age_days": round(self.age_days, 2),
            "bytes": self.bytes,
            "reason": self.reason,
            "decision": self.decision,
            "newest_write_utc": datetime.fromtimestamp(self.newest, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            if self.newest
            else None,
        }
        if self.decision == "partial":
            row["deleted_members"] = self.deleted_members
            row["deleted_bytes"] = self.deleted_bytes
            row["failed_member"] = self.failed_member
        return row


def _positive_days(value: Any) -> float | None:
    if value == UNAPPROVED:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"ttl_days must be {UNAPPROVED} or a positive number")
    if not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError("ttl_days must be finite and positive")
    return float(value)


def load_config(path: Path, *, batch_root: Path, override: float | None = None) -> list[RootSpec]:
    """Read every root spec; ``override`` replaces each TTL for a hypothetical dry run."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"unreadable TTL configuration: {error}") from error
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("roots"), list):
        raise ValueError(f"TTL configuration must be a {SCHEMA} object with a roots list")
    if override is not None and (not math.isfinite(override) or override <= 0):
        raise ValueError("TTL override must be finite and positive")
    specs: list[RootSpec] = []
    seen: set[str] = set()
    for item in data["roots"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("each root needs a string path")
        relative = PurePosixPath(item["path"])
        if (
            relative.is_absolute()
            or len(relative.parts) < 2
            or relative.parts[0] != "batch_state"
            or any(part in {"..", "."} for part in relative.parts)
        ):
            raise ValueError(f"root must lie below batch_state/: {item['path']!r}")
        key = relative.as_posix()
        if key in seen:
            raise ValueError(f"duplicate root: {key}")
        seen.add(key)
        ttl = _positive_days(item.get("ttl_days"))
        if override is not None:
            ttl = override
        owner = item.get("owner", "manifest")
        if owner == "manifest":
            owner = None
        elif not isinstance(owner, str) or not owner.strip():
            raise ValueError(f"root {key} needs owner 'manifest' or a non-empty label")
        keep_newest = item.get("keep_newest_archive", False)
        excludes = item.get("exclude_names", [])
        if (
            not isinstance(keep_newest, bool)
            or not isinstance(excludes, list)
            or not all(isinstance(name, str) and name and "/" not in name for name in excludes)
        ):
            raise ValueError(f"root {key} has invalid keep_newest_archive or exclude_names")
        parts = relative.parts[1:]
        specs.append(
            RootSpec(
                path=batch_root.joinpath(*parts),
                relative=key,
                parts=parts,
                ttl_days=ttl,
                owner=owner,
                keep_newest_archive=keep_newest,
                exclude_names=frozenset(excludes),
            )
        )
    return specs


def config_approved(path: Path) -> bool:
    """True when every configured TTL is a number, not the ``UNAPPROVED`` placeholder."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    roots = data.get("roots") if isinstance(data, dict) else None
    return (
        isinstance(roots, list)
        and bool(roots)
        and all(isinstance(item, dict) and item.get("ttl_days") != UNAPPROVED for item in roots)
    )


def _archive_stem(name: str) -> str:
    """Strip a sidecar suffix, then the archive suffix, so one archive and its sidecars share a key."""
    stem = name
    for suffix in _ARCHIVE_SUFFIXES[:2]:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            stem = stem[: -len(suffix)]
            break
    for suffix in _ARCHIVE_SUFFIXES[2:]:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            return stem[: -len(suffix)]
    return stem


def _is_archive_member(name: str) -> bool:
    """True for an actual archive, false for a manifest or checksum sidecar."""
    return name.endswith(_ARCHIVE_SUFFIXES[2:])


def _manifest_owner(entry_path: Path) -> str | None:
    """The one owner named by every preservation manifest of an entry, or ``None``."""
    if entry_path.is_symlink():
        return None
    candidates: list[Path] = []
    if entry_path.is_dir():
        candidates.extend(sorted(entry_path.glob("*.manifest.json")))
    sibling = entry_path.with_name(entry_path.name + ".manifest.json")
    if sibling.is_file() and not sibling.is_symlink():
        candidates.append(sibling)
    owners = set()
    for manifest in candidates:
        if manifest.is_symlink() or not manifest.is_file():
            return None
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        owner = data.get("owner") or data.get("task_id") if isinstance(data, dict) else None
        if not isinstance(owner, str) or not owner.strip():
            return None
        owners.add(owner.strip())
    return owners.pop() if len(owners) == 1 else None


def _hold_applies(hold_parts: tuple[str, ...], root_parts: tuple[str, ...], name: str) -> bool:
    """A hold protects its own subtree, an ancestor root, or the whole root."""
    if hold_parts[: len(root_parts)] == root_parts:
        rest = hold_parts[len(root_parts) :]
        return not rest or rest[0] == name
    return root_parts[: len(hold_parts)] == hold_parts


def _is_held(spec: RootSpec, name: str, holds: list[dict[str, Any]]) -> bool:
    return any(_hold_applies(tuple(hold["parts"]), spec.parts, name) for hold in holds)


def _members_held(spec: RootSpec, members: list[Path], holds: list[dict[str, Any]]) -> bool:
    """A hold on any member path protects the whole group, sidecars included."""
    return any(_is_held(spec, member.name, holds) for member in members)


def _classify(
    name: str,
    members: list[Path],
    spec: RootSpec,
    *,
    now: float,
    tasks: sweep.TaskInventory,
    holds: list[dict[str, Any]],
) -> Entry:
    """Decide one entry, preserving it with a typed reason whenever a guard fails."""
    relative = f"{spec.relative}/{name}"
    entry = Entry(
        name=name, members=members, relative=relative, owner=None, bytes=None, newest=0.0, age_days=0.0, reason=""
    )
    if any(path.is_symlink() for path in members):
        entry.reason = "symlink_or_not_directory"
        return entry
    allocated = 0
    measured = True
    newest = 0.0
    problem = None
    for path in members:
        size, written, _changed, reason = sweep.tree_facts(path)
        newest = max(newest, written)
        if reason:
            problem = problem or reason
        if size is None:
            measured = False
        else:
            allocated += size
        try:
            info = path.lstat()
        except OSError:
            entry.reason = "tree_unknown"
            return entry
        entry.identities.append((info.st_dev, info.st_ino))
    entry.newest = newest
    entry.age_days = max(0.0, now - newest) / 86400 if newest else 0.0
    entry.bytes = allocated if measured else None
    if problem:
        entry.reason = problem
        return entry
    entry.owner = spec.owner if spec.owner is not None else _manifest_owner(members[0])
    if entry.owner is None:
        entry.reason = "owner_unknown"
    elif _members_held(spec, members, holds):
        entry.reason = "held"
    elif any(sweep.task_referenced(member, tasks.references) for member in members):
        entry.reason = "task_reference"
    elif not tasks.complete:
        entry.reason = "task_inventory_unknown"
    elif spec.ttl_days is None:
        entry.reason = "ttl_unapproved"
    elif entry.age_days <= spec.ttl_days:
        entry.reason = "too_young"
    else:
        entry.decision = "would_delete"
        entry.reason = "expired"
    return entry


def _root_entries(
    spec: RootSpec, *, now: float, tasks: sweep.TaskInventory, holds: list[dict[str, Any]]
) -> list[Entry]:
    """Every entry directly below one root; archive sidecars stay grouped with their archive."""
    if not spec.path.exists():
        return []
    if spec.path.is_symlink() or not spec.path.is_dir():
        raise ValueError(f"configured root is not a real directory: {spec.relative}")
    groups: dict[str, list[str]] = {}
    for name in sorted(os.listdir(spec.path)):
        if name.startswith(".") or name in spec.exclude_names:
            continue
        key = _archive_stem(name) if spec.keep_newest_archive else name
        groups.setdefault(key, []).append(name)
    entries = [
        _classify(key, [spec.path / member for member in members], spec, now=now, tasks=tasks, holds=holds)
        for key, members in groups.items()
    ]
    if spec.keep_newest_archive and entries:
        archives = [
            entry for entry in entries if any(_is_archive_member(member.name) for member in entry.members)
        ]
        if archives:
            newest = max(archives, key=lambda entry: entry.newest)
            if newest.reason in {"expired", "too_young"}:
                newest.reason = "newest_archive"
                newest.decision = "preserve"
    return entries


def _recheck(
    entry: Entry,
    spec: RootSpec,
    quarantine: sweep.Quarantine,
    *,
    now: float,
    tasks: sweep.TaskInventory,
    holds: list[dict[str, Any]],
) -> str | None:
    """Re-prove a quarantined entry: same inodes, unchanged trees, age, holds and references."""
    ttl_days = spec.ttl_days or 0.0
    for member, identity, before in zip(entry.members, entry.identities, entry.fingerprints, strict=True):
        try:
            info = os.stat(member.name, dir_fd=quarantine.fd, follow_symlinks=False)
        except OSError:
            return "identity_changed"
        if (info.st_dev, info.st_ino) != identity:
            return "identity_changed"
        held = quarantine.path / member.name
        _size, written, _changed, problem = sweep.tree_facts(held)
        if problem:
            return problem
        if now - written <= ttl_days * 86400:
            return "recent_write"
        if sweep.tree_fingerprint(held) != before:
            return "recent_write"
    if _members_held(spec, entry.members, holds):
        return "held"
    if any(sweep.task_referenced(member, tasks.references) for member in entry.members):
        return "task_reference"
    if not tasks.complete:
        return "task_inventory_unknown"
    return None


def _reload_guards(
    task_root: Path, retention_list: Path
) -> tuple[sweep.TaskInventory, list[dict[str, Any]]] | None:
    """Reload the task inventory and hold list just before a deletion.

    ``None`` means a guard could not be read, so the caller preserves instead
    of trusting the snapshot taken before the scan.
    """
    try:
        tasks = sweep.load_tasks(task_root)
        holds = load_holds(retention_list)
    except (OSError, ValueError):
        return None
    return tasks, holds


def _restore_members(entry: Entry, root_fd: int, quarantine: sweep.Quarantine, members: list[Path]) -> int:
    """Rename quarantined members back; an occupied name stays held and is an error."""
    errors = 0
    for member in reversed(members):
        try:
            sweep.rename_noreplace(quarantine.fd, member.name, root_fd, member.name)
        except OSError:
            errors += 1
            continue
        sweep._sync_rename(quarantine.fd, root_fd)
    entry.decision = "preserve"
    return errors


def _remove(
    entry: Entry,
    spec: RootSpec,
    root_fd: int,
    quarantine: sweep.Quarantine,
    *,
    now: float,
    task_root: Path,
    retention_list: Path,
    repo_root: Path,
) -> int:
    """Quarantine every member, recheck once, then let the common reaper delete it."""
    entry.fingerprints = [sweep.tree_fingerprint(member) for member in entry.members]
    if any(fingerprint is None for fingerprint in entry.fingerprints):
        entry.reason = "tree_unknown"
        return 1
    renamed: list[Path] = []
    for member, identity in zip(entry.members, entry.identities, strict=True):
        try:
            info = member.lstat()
        except OSError:
            info = None
        if info is None or (info.st_dev, info.st_ino) != identity:
            blocked = _restore_members(entry, root_fd, quarantine, renamed)
            entry.reason = "restore_blocked" if blocked else "identity_changed"
            return 1 + blocked
        try:
            sweep.rename_noreplace(root_fd, member.name, quarantine.fd, member.name)
        except OSError:
            blocked = _restore_members(entry, root_fd, quarantine, renamed)
            entry.reason = "restore_blocked" if blocked else "rename_refused"
            return 1 + blocked
        sweep._sync_rename(root_fd, quarantine.fd)
        renamed.append(member)
    guards = _reload_guards(task_root, retention_list)
    if guards is None:
        blocked = _restore_members(entry, root_fd, quarantine, renamed)
        entry.reason = "restore_blocked" if blocked else "guard_reload_failed"
        return 1 + blocked
    fresh_tasks, fresh_holds = guards
    problem = _recheck(entry, spec, quarantine, now=now, tasks=fresh_tasks, holds=fresh_holds)
    if problem:
        blocked = _restore_members(entry, root_fd, quarantine, renamed)
        entry.reason = "restore_blocked" if blocked else problem
        return 1 + blocked
    deleted_members: list[str] = []
    deleted_bytes = 0
    failed_member: str | None = None
    for member, identity in zip(entry.members, entry.identities, strict=True):
        held_path = quarantine.path / member.name
        try:
            size, _written, _changed, problem = sweep.tree_facts(held_path)
            if problem:
                raise OSError(errno.EIO, f"unreadable member tree: {problem}")
            sweep.reap_attributed_temp(
                held_path,
                repo_root=repo_root,
                temp_root=quarantine.path,
                expected_dev=identity[0],
                expected_ino=identity[1],
            )
            if os.path.lexists(held_path):
                raise OSError(errno.ENOTEMPTY, "common reaper left residue")
        except (OSError, ValueError):
            failed_member = member.name
            break
        deleted_members.append(member.name)
        deleted_bytes += size
        try:
            sweep.sync_directory(quarantine.fd)
        except OSError:
            failed_member = member.name
            break
    if failed_member is not None:
        remaining = [path for path in entry.members if os.path.lexists(quarantine.path / path.name)]
        blocked = _restore_members(entry, root_fd, quarantine, remaining)
        entry.reason = "restore_blocked" if blocked else "delete_refused"
        entry.deleted_members = deleted_members
        entry.deleted_bytes = deleted_bytes
        entry.failed_member = failed_member
        entry.decision = "partial" if deleted_members else "preserve"
        return 1 + blocked
    entry.decision = "deleted"
    entry.reason = "expired"
    return 0


def _leftovers(spec: RootSpec) -> list[dict[str, Any]]:
    """Quarantine directories a crashed run left behind; reported, never deleted."""
    if not spec.path.is_dir() or spec.path.is_symlink():
        return []
    return [
        {
            "path": f"{spec.relative}/{name}",
            "owner": None,
            "age_days": None,
            "bytes": None,
            "reason": "quarantine_leftover",
            "decision": "preserve",
            "newest_write_utc": None,
        }
        for name in sorted(os.listdir(spec.path))
        if name.startswith(QUARANTINE_PREFIX)
    ]


def _free_bytes(roots: list[Path]) -> int:
    """Free bytes over each distinct filesystem once, never double-counted by root."""
    seen: set[int] = set()
    total = 0
    for root in roots:
        device = os.stat(root).st_dev
        if device in seen:
            continue
        seen.add(device)
        info = os.statvfs(root)
        total += info.f_bavail * info.f_frsize
    return total


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        os.write(fd, (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def sweep_batch_state(
    *,
    batch_root: Path,
    config_path: Path = CONFIG,
    task_root: Path | None = None,
    retention_list: Path = RETENTION_LIST,
    apply: bool = False,
    ttl_override: float | None = None,
    receipt_path: Path | None = None,
    now: float | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Classify every configured entry; with ``apply`` remove proven ones and write a receipt.

    Raises ``TtlUnapproved`` when apply is requested while any configured TTL
    is still the ``UNAPPROVED`` placeholder, and ``ValueError`` for an apply
    ``ttl_override`` (an override is a dry-run hypothesis only).
    """
    if apply and ttl_override is not None:
        raise ValueError("--ttl-days is a dry-run hypothesis; apply uses approved configured TTLs")
    config = load_config(config_path, batch_root=batch_root, override=ttl_override)
    approved = config_approved(config_path)
    if apply and not approved:
        raise TtlUnapproved("apply refused: one or more TTL values are UNAPPROVED")
    now = time.time() if now is None else now
    task_root = task_root if task_root is not None else tasks_dir()
    tasks = sweep.load_tasks(task_root)
    holds = load_holds(retention_list)
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    if batch_root.is_symlink() or not batch_root.is_dir():
        raise ValueError("batch_state root must be a real directory")
    roots = [spec.path for spec in config if spec.path.exists()]
    free_before = _free_bytes(roots)
    rows: list[dict[str, Any]] = []
    errors = 0
    for spec in config:
        leftovers = _leftovers(spec)
        rows.extend(leftovers)
        errors += len(leftovers)
        entries = _root_entries(spec, now=now, tasks=tasks, holds=holds)
        if apply and any(entry.decision == "would_delete" for entry in entries):
            root_fd = os.open(spec.path, sweep._DIR_FLAGS)
            try:
                quarantine = sweep.open_quarantine(spec.path, root_fd)
                try:
                    for entry in entries:
                        if entry.decision == "would_delete":
                            errors += _remove(
                                entry,
                                spec,
                                root_fd,
                                quarantine,
                                now=now,
                                task_root=task_root,
                                retention_list=retention_list,
                                repo_root=repo_root,
                            )
                finally:
                    sweep.close_quarantine(quarantine, root_fd)
            finally:
                os.close(root_fd)
        rows.extend(entry.row() for entry in entries)
    free_after = _free_bytes(roots)
    deleted = [row for row in rows if row["decision"] == "deleted"]
    partial = [row for row in rows if row["decision"] == "partial"]
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "mode": "apply" if apply else "dry_run",
        "ttl_source": "override_hypothetical"
        if ttl_override is not None
        else ("approved" if approved else "unapproved"),
        "configured_ttls_approved": approved,
        "task_inventory_complete": tasks.complete,
        "batch_root": "batch_state",
        "rows": rows,
        "errors": errors,
        "counts": {
            reason: sum(row["reason"] == reason for row in rows) for reason in sorted({row["reason"] for row in rows})
        },
        "bytes_by_reason": {
            reason: sum(row["bytes"] or 0 for row in rows if row["reason"] == reason)
            for reason in sorted({row["reason"] for row in rows})
        },
        "would_delete_entries": sum(row["decision"] == "would_delete" for row in rows),
        "would_delete_bytes": sum(row["bytes"] or 0 for row in rows if row["decision"] == "would_delete"),
        "deleted_entries": len(deleted),
        "deleted_bytes_summed": sum(row["bytes"] or 0 for row in deleted),
        "partial_entries": len(partial),
        "partial_deleted_bytes": sum(row["deleted_bytes"] or 0 for row in partial),
        "free_bytes_before": free_before,
        "free_bytes_after": free_after,
        "freed_bytes_measured": max(0, free_after - free_before),
        "receipt_path": None,
    }
    if apply:
        stamp = datetime.fromtimestamp(now, UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = receipt_path or batch_root / "reports" / f"batch-state-ttl-sweep-{stamp}.json"
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "created_at": datetime.fromtimestamp(now, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ttl_source": report["ttl_source"],
            "free_bytes_before": free_before,
            "free_bytes_after": free_after,
            "freed_bytes_measured": report["freed_bytes_measured"],
            "freed_bytes_summed": report["deleted_bytes_summed"],
            "entries": deleted,
            "partial_entries": partial,
            "partial_deleted_bytes": report["partial_deleted_bytes"],
            "errors": errors,
        }
        _write_receipt(destination, receipt)
        try:
            report["receipt_path"] = destination.relative_to(batch_root).as_posix()
        except ValueError:
            report["receipt_path"] = destination.name
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the approved TTLs to preserved batch_state evidence and old backups, dry-run first.\n"
            "Use for disk pressure from batch_state/preserved and batch_state/backups; do not use it on tasks, "
            "reports, branch archives, corpus or database data, which it never reads."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.batch_state_ttl_sweep --summary\n"
            "  .venv/bin/python -m scripts.hygiene.batch_state_ttl_sweep --ttl-days 30 --summary  # hypothetical\n"
            "  .venv/bin/python -m scripts.hygiene.batch_state_ttl_sweep --apply --summary\n"
            "Outputs: stdout table, --summary counts, or --json rows; --apply writes a JSON receipt under "
            "batch_state/reports/ and deletes only expired entries after a quarantine recheck.\n"
            "Exit codes: 0 clean; 1 removal, quarantine or scan errors; 2 invalid arguments or configuration; "
            "4 apply refused because a TTL value is still UNAPPROVED.\n"
            "Related: #11418; scripts/hygiene/batch_state_ttl_sweep.json; docs/runbooks/tmp-retention.md."
        ),
    )
    parser.add_argument(
        "--batch-root",
        type=Path,
        help="batch_state directory to sweep (default: this checkout's batch_state; example /srv/batch_state).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG,
        help="Single TTL configuration file (default scripts/hygiene/batch_state_ttl_sweep.json).",
    )
    parser.add_argument(
        "--tasks",
        type=Path,
        help="Task-record directory (default shared batch_state/tasks; example fixture/tasks).",
    )
    parser.add_argument(
        "--retention-list",
        type=Path,
        default=RETENTION_LIST,
        help="Hold list (default scripts/hygiene/batch_state_retention.json).",
    )
    parser.add_argument(
        "--ttl-days",
        type=float,
        help=(
            "Dry-run only: hypothetical TTL in days applied to every root, clearly labelled; "
            "apply refuses it (example 30)."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete proven expired entries and write a receipt (default dry run; refused while any TTL is UNAPPROVED).",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Receipt path for --apply (default batch_state/reports/batch-state-ttl-sweep-<epoch>.json).",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print machine-readable rows and totals (default table).")
    output.add_argument("--summary", action="store_true", help="Print JSON counts and byte totals without entry names.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        batch_root = args.batch_root or Path(__file__).resolve().parents[2] / "batch_state"
        report = sweep_batch_state(
            batch_root=batch_root,
            config_path=args.config,
            task_root=args.tasks,
            retention_list=args.retention_list,
            apply=args.apply,
            ttl_override=args.ttl_days,
            receipt_path=args.receipt,
            repo_root=Path(__file__).resolve().parents[2],
        )
    except TtlUnapproved as error:
        print(str(error), file=sys.stderr)
        return EXIT_TTL_UNAPPROVED
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.summary:
        print(json.dumps({key: value for key, value in report.items() if key != "rows"}, sort_keys=True))
    else:
        print("| Entry | Owner | Age (days) | Bytes | Decision | Reason |")
        print("|---|---|---:|---:|---|---|")
        for row in report["rows"]:
            print(
                f"| {row['path']} | {row['owner'] or ''} | {row['age_days']} | {row['bytes']} "
                f"| {row['decision']} | {row['reason']} |"
            )
        print(
            f"mode={report['mode']} ttl_source={report['ttl_source']} errors={report['errors']} "
            f"would_delete={report['would_delete_entries']} would_delete_bytes={report['would_delete_bytes']} "
            f"deleted={report['deleted_entries']} deleted_bytes_summed={report['deleted_bytes_summed']} "
            f"free_before={report['free_bytes_before']} free_after={report['free_bytes_after']} "
            f"freed_measured={report['freed_bytes_measured']}"
        )
    return EXIT_ERROR if report["errors"] else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
