"""Reap proven-ended Claude session scratch; age never authorizes removal (#8783)."""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import shutil
import stat
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import psutil

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_SESSION_RE = re.compile(r"(?<![a-zA-Z0-9-])[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}(?![a-zA-Z0-9-])", re.I)


@dataclass(frozen=True)
class ProcessEvidence:
    live_sessions: frozenset[str] = frozenset()
    complete: bool = False


def process_evidence() -> ProcessEvidence:
    """Scan this user's processes without publishing arguments or environment.

    Inaccessible processes and Claude processes with no observable session ID
    prevent a negative ownership proof. Positive ownership always wins, even
    over a confirmed rollover. A disappearing process is not a live owner.
    """
    sessions: set[str] = set()
    complete = True
    try:
        for process in psutil.process_iter():
            try:
                if process.uids().real != os.getuid() or process.status() == psutil.STATUS_ZOMBIE:
                    continue
                args = process.cmdline()
                sessions.update(match.lower() for value in args for match in _SESSION_RE.findall(value))
                environment = process.environ()
                sessions.update(match.lower() for value in environment.values() for match in _SESSION_RE.findall(value))
                paths = [process.cwd(), *(item.path for item in process.open_files())]
                sessions.update(match.lower() for value in paths for match in _SESSION_RE.findall(value))
                is_claude = process.name() in {"claude", "claude-code"} or any(
                    {"claude", "claude-code"}.intersection(Path(arg).parts) for arg in args
                )
                # Other UUIDs in an environment are not a Claude session identity.
                identity_values = [
                    value
                    for key, value in environment.items()
                    if key in {"CLAUDE_SESSION_ID", "LEARN_UKRAINIAN_SESSION_ID", "SESSION_STREAM_SESSION_ID"}
                ]
                for index, arg in enumerate(args):
                    if arg in {"--session-id", "--resume", "-r"} and index + 1 < len(args):
                        identity_values.append(args[index + 1])
                    elif arg.startswith(("--session-id=", "--resume=")):
                        identity_values.append(arg.split("=", 1)[1])
                identity_values.extend(
                    path for path in paths if f"/claude-{os.getuid()}/" in path or path.endswith(".jsonl")
                )
                if is_claude and not any(_SESSION_RE.search(value) for value in identity_values):
                    complete = False
            except psutil.NoSuchProcess:
                continue
            except (psutil.Error, OSError):
                complete = False
    except (psutil.Error, OSError):
        complete = False
    return ProcessEvidence(frozenset(sessions), complete)


def _open_path(path: Path) -> int:
    """Open every ancestor without following symlinks, including the root."""
    absolute = Path(os.path.abspath(path))
    fd = os.open(absolute.anchor, _DIR_FLAGS)
    try:
        for part in absolute.parts[1:]:
            child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except OSError:
        os.close(fd)
        raise


def _confirmed_record(record: object) -> str | None:
    """Read the predecessor identity from a confirmed thread-handoff v2 lease."""
    if not isinstance(record, dict) or record.get("schema_version") != 2 or record.get("agent") != "claude":
        return None
    active = record.get("active") or {}
    replacement = record.get("replacement") or {}
    cleanup = record.get("cleanup") or {}
    if not all(isinstance(value, dict) for value in (active, replacement, cleanup)):
        return None
    identity = replacement.get("identity") or {}
    proof = replacement.get("canary_proof") or {}
    verdict = replacement.get("strict_verdict") or {}
    if not all(isinstance(value, dict) for value in (identity, proof, verdict)):
        return None
    session = active.get("thread_id")
    if (
        isinstance(session, str)
        and _SESSION_RE.fullmatch(session)
        and replacement.get("status") == "started"
        and replacement.get("confirmed_at")
        and isinstance(replacement.get("thread_id"), str)
        and _SESSION_RE.fullmatch(replacement["thread_id"])
        and replacement.get("thread_id") != session
        and identity.get("predecessor_task_id") == session
        and identity.get("replacement_task_id") == replacement.get("thread_id")
        and identity.get("lifecycle_state") == "confirmed"
        and proof.get("status") == "PASS"
        and verdict.get("verdict") == "PASS"
        and cleanup.get("old_automation_ready_to_delete") is True
        and cleanup.get("confirmed_at")
    ):
        return session.lower()
    return None


def confirmed_sessions(roots: Iterable[Path]) -> set[str]:
    """Read canonical Claude lineage lease.json records; ignore malformed records."""
    sessions: set[str] = set()
    for root in roots:
        try:
            root_fd = _open_path(root)
        except OSError:
            continue
        try:
            try:
                lineages = os.listdir(root_fd)
            except OSError:
                continue
            for lineage in lineages:
                try:
                    lineage_fd = os.open(lineage, _DIR_FLAGS, dir_fd=root_fd)
                    try:
                        fd = os.open("lease.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=lineage_fd)
                        with os.fdopen(fd, "rb") as source:
                            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                                continue
                            session = _confirmed_record(json.load(source))
                            if session:
                                sessions.add(session)
                    finally:
                        os.close(lineage_fd)
                except (OSError, ValueError, UnicodeError):
                    continue
        finally:
            os.close(root_fd)
    return sessions


def _tree_bytes(fd: int) -> int:
    total = 0
    for name in os.listdir(fd):
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
        elif stat.S_ISDIR(info.st_mode):
            child = os.open(name, _DIR_FLAGS, dir_fd=fd)
            try:
                total += _tree_bytes(child)
            finally:
                os.close(child)
    return total


def _reason(session: str, evidence: ProcessEvidence, confirmed: set[str]) -> str:
    if session in evidence.live_sessions:
        return "live_session"
    if session in confirmed:
        return "confirmed_rollover"
    return "process_gone" if evidence.complete else "unknown_session"


def sweep_sessions(
    root: Path | None = None,
    *,
    rollover_roots: Iterable[Path] = (),
    apply: bool = False,
    probe: Callable[[], ProcessEvidence] = process_evidence,
) -> dict:
    """Sweep root/session and root/project/session; keep unknown entries.

    Reports use relative entries locally and counts/bytes in the public summary.
    Missing roots are empty; all other per-entry errors are recorded, never fatal.
    Recheck ownership immediately before apply. Never create roots or lock files.
    """
    root = root or Path(f"/tmp/claude-{os.getuid()}")
    report: dict = {"mode": "apply" if apply else "dry-run", "entries": [], "summary": {}}
    rows = report["entries"]
    evidence = probe()
    confirmed = confirmed_sessions(rollover_roots)

    def visit(parent_fd: int, name: str, relative: str, *, project: bool = False) -> None:
        row = {"entry": relative, "bytes": 0, "action": "kept", "reason": "unknown_entry"}
        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                row["reason"] = "symlink"
            elif stat.S_ISDIR(info.st_mode):
                fd = os.open(name, _DIR_FLAGS, dir_fd=parent_fd)
                try:
                    held = os.fstat(fd)
                    if (info.st_dev, info.st_ino) != (held.st_dev, held.st_ino):
                        raise OSError(errno.ESTALE, "entry changed during open")
                    if info.st_uid != os.getuid():
                        row["reason"] = "foreign_owner"
                    elif not _SESSION_RE.fullmatch(name) and not project:
                        for child in sorted(os.listdir(fd)):
                            visit(fd, child, f"{relative}/{child}", project=True)
                        return
                    elif _SESSION_RE.fullmatch(name):
                        row["bytes"] = _tree_bytes(fd)
                        reason = _reason(name.lower(), evidence, confirmed)
                        if apply and reason in {"confirmed_rollover", "process_gone"}:
                            reason = _reason(name.lower(), probe(), confirmed)
                            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                            held = os.fstat(fd)
                            if (current.st_dev, current.st_ino) != (held.st_dev, held.st_ino):
                                reason = "entry_changed"
                            elif not shutil.rmtree.avoids_symlink_attacks:
                                reason = "unsafe_platform"
                        row["reason"] = reason
                        if reason in {"confirmed_rollover", "process_gone"}:
                            row["action"] = "would_remove"
                            if apply:
                                shutil.rmtree(name, dir_fd=parent_fd)
                                row["action"] = "removed"
                finally:
                    os.close(fd)
        except OSError as exc:
            row.update(action="error", reason=errno.errorcode.get(exc.errno or 0, "OSError"))
        rows.append(row)

    try:
        root_fd = _open_path(root)
        try:
            if root.name != f"claude-{os.getuid()}" or os.fstat(root_fd).st_uid != os.getuid():
                raise OSError(errno.EPERM, "unexpected scratch root")
            for name in sorted(os.listdir(root_fd)):
                visit(root_fd, name, name)
        finally:
            os.close(root_fd)
    except FileNotFoundError:
        pass
    except OSError as exc:
        rows.append(
            {"entry": ".", "bytes": 0, "action": "error", "reason": errno.errorcode.get(exc.errno or 0, "OSError")}
        )
    counts = Counter(row["action"] for row in rows)
    report["summary"] = {
        "entries": len(rows),
        "kept": counts["kept"],
        "would_remove": counts["would_remove"],
        "removed": counts["removed"],
        "errors": counts["error"],
        "bytes": sum(row["bytes"] for row in rows),
        "reclaimable_bytes": sum(row["bytes"] for row in rows if row["action"] in {"would_remove", "removed"}),
        "bytes_freed": sum(row["bytes"] for row in rows if row["action"] == "removed"),
        "kept_by_reason": dict(Counter(row["reason"] for row in rows if row["action"] == "kept")),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report and remove proven-ended Claude session scratch.\nUse at hygiene time; never use age as evidence of session death.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.maintenance.claude_session_scratch
  .venv/bin/python -m scripts.maintenance.claude_session_scratch --apply
Outputs:
  JSON counts/bytes on stdout; --apply deletes only proven-ended session directories.
  Live, unknown and symlink entries are kept. No report files are written.
Exit codes:
  0 report complete; 1 per-entry errors (remaining entries still processed).
Related:
  #8783; scripts/orchestration/scheduled_worktree_cleanup.py; thread_handoff.py
""",
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        default=None,
        help="Per-user scratch root; default /tmp/claude-<uid>. Example: /tmp/claude-1000",
    )
    parser.add_argument(
        "--rollover-root",
        type=Path,
        action="append",
        default=[],
        help="Claude thread-handoff lineage root; repeatable. Default: no rollover evidence. Example: .agent/thread-rollovers/claude",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Remove proven-ended scratch. Default: dry-run, no changes."
    )
    args = parser.parse_args(argv)
    report = sweep_sessions(args.temp_root, rollover_roots=args.rollover_root, apply=args.apply)
    print(json.dumps({"mode": report["mode"], **report["summary"]}, sort_keys=True))
    return int(report["summary"]["errors"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
