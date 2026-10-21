"""Snapshot, attribute and fingerprint primary-checkout dirt per shell call (#11253).

``guard-primary-checkout-write.py`` decides from the text of a shell command,
so a launched script that ``cd``s into the primary checkout and redirects to a
relative path writes there unseen. This module backs a second, observational
layer: ``audit-primary-checkout-dirt.py`` takes a snapshot of the protected
primary checkout's ``git status`` before each shell call and compares it after
the call. Paths that were not dirty before and are dirty after are attributed
to that call in a record kept outside the repository; paths already dirty
before the call are never attributed to it. Git-ignored paths never appear,
because ``git status`` omits them.

Attribution is temporal: a path is attributed to every call whose window saw
it appear, so a concurrent writer (another session or the operator) can be
attributed to an overlapping call. The cleanup command therefore refuses a
file that another session's record also claims, and any file whose identity or
content changed after the record was written.

Threat model: this is a safety net for honest-agent mistakes plus attribution.
A malicious process running as the same user can bypass or falsify it (edit
the state directory, write between snapshots, or skip the hooks entirely).

Cost: two ``git status --porcelain=v1 -z --untracked-files=all`` runs per shell
call, with ``GIT_OPTIONAL_LOCKS=0`` so the probe never rewrites the index. Each
run is bounded by :data:`GIT_TIMEOUT_S` and :data:`MAX_ENTRIES`; only new
untracked entries are fingerprinted, at most :data:`MAX_FINGERPRINTS` of them,
and only files up to :data:`MAX_HASH_BYTES` are hashed.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import subprocess
import time
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.guardrails import worktree_containment as wc

SCHEMA = "primary-dirt-audit.v1"
STATE_NAMESPACE = ("learn-ukrainian", "primary-dirt-audit")
GIT_TIMEOUT_S = 3.0
MAX_ENTRIES = 20_000
MAX_FINGERPRINTS = 200
MAX_HASH_BYTES = 8 * 1024 * 1024
MAX_COMMAND_CHARS = 4000
SNAPSHOT_TTL_S = 6 * 3600
MAX_GC_PER_CALL = 500


class AuditError(RuntimeError):
    """A snapshot or record could not be taken; the call is unauditable."""


# ---------------------------------------------------------------------------
# state directory
# ---------------------------------------------------------------------------


def state_dir(environ: Mapping[str, str] | None = None) -> Path:
    """``$XDG_STATE_HOME/learn-ukrainian/primary-dirt-audit``; relative values are ignored per XDG."""
    env = os.environ if environ is None else environ
    configured = env.get("XDG_STATE_HOME", "")
    if configured and Path(configured).is_absolute():
        base = Path(configured)
    else:
        base = Path(env.get("HOME") or Path.home()) / ".local" / "state"
    return base.joinpath(*STATE_NAMESPACE)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise AuditError(f"audit state path is not a real directory: {path}")
    return path


def key(*parts: str) -> str:
    """Filesystem-safe digest of untrusted identifiers (session and tool-use ids)."""
    return hashlib.sha256("\0".join(parts).encode("utf-8", "surrogateescape")).hexdigest()[:32]


def snapshot_path(state: Path, session_id: str, tool_use_id: str) -> Path:
    return state / "snapshots" / f"{key(session_id, tool_use_id)}.json"


def session_records_dir(state: Path, session_id: str) -> Path:
    return state / "records" / key(session_id)


def write_json_atomic(path: Path, data: object) -> None:
    _ensure_dir(path.parent)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def append_jsonl(path: Path, data: object) -> None:
    _ensure_dir(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# git probes (read-only; never take optional locks in the primary)
# ---------------------------------------------------------------------------


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = sanitized_git_env()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            errors="surrogateescape",
            check=False,
            env=env,
            timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise AuditError(f"git {args[0]} exceeded {GIT_TIMEOUT_S:g}s in {root}") from exc
    except OSError as exc:
        raise AuditError(f"git unavailable: {exc}") from exc


def status_entries(root: Path, pathspec: str | None = None) -> dict[str, str]:
    """Map each dirty, non-ignored path under ``root`` to its porcelain ``XY`` code."""
    args = ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"]
    if pathspec is not None:
        args += ["--", f":(literal){pathspec}"]
    proc = _git(root, *args)
    if proc.returncode != 0:
        raise AuditError(f"git status failed in {root}: {(proc.stderr or proc.stdout).strip()}")
    entries: dict[str, str] = {}
    for raw in proc.stdout.split("\0"):
        if len(raw) < 4:
            continue
        entries[raw[3:]] = raw[:2]
        if len(entries) > MAX_ENTRIES:
            raise AuditError(f"primary checkout {root} has more than {MAX_ENTRIES} dirty entries")
    return entries


def is_tracked(root: Path, relpath: str) -> bool:
    proc = _git(root, "ls-files", "-z", "--cached", "--", f":(literal){relpath}")
    if proc.returncode != 0:
        raise AuditError(f"git ls-files failed in {root}: {proc.stderr.strip()}")
    return bool(proc.stdout.strip("\0"))


def protected_primary_roots(candidates: Iterable[str | Path | None]) -> list[Path]:
    """Distinct primary checkout roots on a protected branch owning any candidate path."""
    roots: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        try:
            root = wc.resolve_main_root(candidate)
            if root not in roots and wc.is_protected_branch(root):
                roots.append(root)
        except Exception:
            continue
    return roots


# ---------------------------------------------------------------------------
# no-follow filesystem access below a root
# ---------------------------------------------------------------------------


def split_relpath(relpath: object) -> list[str] | None:
    """Components of a safe repository-relative path, or None when it could escape."""
    if not isinstance(relpath, str) or not relpath or "\0" in relpath or relpath.startswith("/"):
        return None
    parts = relpath.split("/")
    if any(part in {"", ".", "..", ".git"} for part in parts):
        return None
    return parts


def open_parent(root: Path, parts: list[str]) -> int:
    """Open the parent directory of ``parts`` below ``root`` without following any symlink.

    Raises ``OSError`` (``ELOOP``/``ENOTDIR`` for a symlinked or non-directory
    component, ``ENOENT`` when a component is gone).
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(root, flags)
    try:
        for part in parts[:-1]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
    except BaseException:
        os.close(fd)
        raise
    return fd


def _kind(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    return "other"


def _sha256_at(dir_fd: int, name: str, expected: os.stat_result) -> str | None:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    fd = os.open(name, flags, dir_fd=dir_fd)
    try:
        current = os.fstat(fd)
        if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
            return None
        digest = hashlib.sha256()
        remaining = MAX_HASH_BYTES + 1
        while remaining > 0:
            chunk = os.read(fd, min(1 << 20, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
        return None if remaining <= 0 else digest.hexdigest()
    finally:
        os.close(fd)


def fingerprint(root: Path, relpath: str) -> dict[str, object] | None:
    """Identity and content of ``root/relpath`` read without following symlinks, or None."""
    parts = split_relpath(relpath)
    if parts is None:
        return None
    try:
        dir_fd = open_parent(root, parts)
    except OSError:
        return None
    try:
        info = os.stat(parts[-1], dir_fd=dir_fd, follow_symlinks=False)
        result: dict[str, object] = {
            "kind": _kind(info.st_mode),
            "dev": info.st_dev,
            "ino": info.st_ino,
            "size": info.st_size,
            "mtime_ns": info.st_mtime_ns,
            "sha256": None,
        }
        if result["kind"] == "file" and info.st_size <= MAX_HASH_BYTES:
            result["sha256"] = _sha256_at(dir_fd, parts[-1], info)
        return result
    except OSError:
        return None
    finally:
        os.close(dir_fd)


# ---------------------------------------------------------------------------
# hook phases
# ---------------------------------------------------------------------------


def take_snapshot(state: Path, session_id: str, tool_use_id: str, candidates: Iterable[str | Path | None]) -> dict:
    """Record the dirty entries of every protected primary root before a shell call."""
    roots: dict[str, dict[str, str]] = {}
    errors: dict[str, str] = {}
    for root in protected_primary_roots(candidates):
        try:
            roots[str(root)] = status_entries(root)
        except AuditError as exc:
            errors[str(root)] = str(exc)
    snapshot = {
        "schema": SCHEMA,
        "session_id": session_id,
        "tool_use_id": tool_use_id,
        "created_at": utc_now(),
        "roots": roots,
        "errors": errors,
    }
    write_json_atomic(snapshot_path(state, session_id, tool_use_id), snapshot)
    return snapshot


def collect_stale_snapshots(state: Path, now: float | None = None) -> int:
    """Delete snapshots whose post phase never ran (denied or cancelled calls)."""
    directory = state / "snapshots"
    if not directory.is_dir():
        return 0
    cutoff = (time.time() if now is None else now) - SNAPSHOT_TTL_S
    removed = 0
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            if index >= MAX_GC_PER_CALL:
                break
            try:
                if entry.is_file(follow_symlinks=False) and entry.stat(follow_symlinks=False).st_mtime < cutoff:
                    os.unlink(entry.path)
                    removed += 1
            except OSError:
                continue
    return removed


def _load_snapshot(path: Path, session_id: str, tool_use_id: str) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (
        not isinstance(data, dict)
        or data.get("schema") != SCHEMA
        or data.get("session_id") != session_id
        or data.get("tool_use_id") != tool_use_id
        or not isinstance(data.get("roots"), dict)
    ):
        return None
    return data


def finish_call(
    state: Path,
    *,
    session_id: str,
    tool_use_id: str,
    command: str,
    cwd: str,
    hook_event: str,
    tool_name: str,
    candidates: Iterable[str | Path | None],
    environ: Mapping[str, str] | None = None,
) -> dict:
    """Compare against the pre-call snapshot and write one record per dirtied root.

    Returns ``{"records": [...], "unaudited": {root: reason}}``. A record is
    written only for a root that gained at least one dirty path.
    """
    env = os.environ if environ is None else environ
    path = snapshot_path(state, session_id, tool_use_id)
    snapshot = _load_snapshot(path, session_id, tool_use_id)
    result: dict[str, object] = {"records": [], "unaudited": {}}
    unaudited: dict[str, str] = result["unaudited"]  # type: ignore[assignment]
    records: list[dict] = result["records"]  # type: ignore[assignment]

    if snapshot is None:
        for root in protected_primary_roots(candidates):
            try:
                dirty = status_entries(root)
            except AuditError as exc:
                unaudited[str(root)] = str(exc)
                continue
            if dirty:
                unaudited[str(root)] = (
                    f"pre-call snapshot missing; {len(dirty)} dirty entries cannot be attributed to this call"
                )
        return result

    for root_text, reason in (snapshot.get("errors") or {}).items():
        unaudited[str(root_text)] = f"pre-call snapshot failed: {reason}"

    truncated = len(command) > MAX_COMMAND_CHARS
    for root_text, before in snapshot["roots"].items():
        root = Path(root_text)
        try:
            after = status_entries(root)
        except AuditError as exc:
            unaudited[root_text] = str(exc)
            continue
        new_paths = sorted(set(after) - set(before))
        changed = sorted(p for p in set(after) & set(before) if after[p] != before[p])
        if not new_paths:
            continue
        entries = []
        for index, relpath in enumerate(new_paths):
            xy = after[relpath]
            kind = "untracked" if xy == "??" else "tracked"
            with_fingerprint = kind == "untracked" and index < MAX_FINGERPRINTS
            entries.append(
                {
                    "path": relpath,
                    "xy": xy,
                    "kind": kind,
                    "fingerprint": fingerprint(root, relpath) if with_fingerprint else None,
                }
            )
        record = {
            "schema": SCHEMA,
            "record_id": f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}-{secrets.token_hex(4)}",
            "session_id": session_id,
            "tool_use_id": tool_use_id,
            "hook_event_name": hook_event,
            "tool_name": tool_name,
            "x_agent": env.get("LU_X_AGENT_TRAILER", ""),
            "command": command[:MAX_COMMAND_CHARS],
            "command_truncated": truncated,
            "cwd": cwd,
            "primary_root": root_text,
            "snapshot_taken_at": snapshot.get("created_at"),
            "created_at": utc_now(),
            "entries": entries,
            "status_changed": [{"path": p, "before": before[p], "after": after[p]} for p in changed],
        }
        write_json_atomic(session_records_dir(state, session_id) / f"{record['record_id']}.json", record)
        append_jsonl(
            state / "audit.jsonl",
            {
                "event": "primary_dirt_attributed",
                "record_id": record["record_id"],
                "session_id": session_id,
                "tool_use_id": tool_use_id,
                "primary_root": root_text,
                "paths": new_paths[:50],
                "path_count": len(new_paths),
                "at": record["created_at"],
            },
        )
        records.append(record)
    path.unlink(missing_ok=True)
    return result


def load_record(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("schema") == SCHEMA else None


def iter_records(state: Path) -> Iterable[tuple[Path, dict]]:
    """Every readable record in the state directory, across all sessions."""
    base = state / "records"
    if not base.is_dir() or base.is_symlink():
        return
    for session_dir in sorted(base.iterdir()):
        if session_dir.is_symlink() or not session_dir.is_dir():
            continue
        for record_path in sorted(session_dir.glob("*.json")):
            if record_path.is_symlink():
                continue
            record = load_record(record_path)
            if record is not None:
                yield record_path, record
