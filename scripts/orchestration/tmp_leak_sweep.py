#!/usr/bin/env python3
"""Reap ad-hoc LU temp trees under $TMPDIR that isolation sweeps miss.

Agents and one-shot review flows leave multi-GB directories such as
``/tmp/review-6621`` (full clones) and ``/tmp/pr6591-exact-*``.  Formal
``sweep_review_temp_orphans`` only reaps ``lu-review-*`` / shielded-reviews
manifests, so these names never drain without manual intervention.

This module is age-gated, name-pattern scoped, and fails closed on liveness:
a path is deleted only when ``pgrep -f`` is negative AND a ``/proc`` walk fully
probed every process (any owner: state, command line, cwd, environment, open
descriptors) without finding a reference.  No ``/proc`` (macOS), or any process
that refuses inspection, is an unknown answer, and unknown preserves the path.
It is not a blanket ``rm -rf /tmp/*``.

Atlas/QA legacy residue (#8738): only the exact large names left by the
#8307 Atlas 410k run and the #8686 QA scratch directories are auto-deleted
(``LEGACY_EXACT_ALLOWLIST``). Every other ``atlas-<n>-*`` / ``qa-<n>-*`` entry
is inventoried in the report but never deleted here, and Atlas promotion
plans / decision YAML are always protected. The managed ``task-scratch``
namespace, the scratch roots and their ancestors are excluded from the scan;
those leases are reclaimed only by :mod:`scripts.common.task_scratch`.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.scratch import resolve_scratch_root
from scripts.common.task_scratch import NAMESPACE_DIRNAME, managed_scratch_paths
from scripts.path_safety import assert_delete_target

# 2h normal; 30m under disk pressure.
DEFAULT_MIN_AGE_S = 2 * 60 * 60
DEFAULT_PRESSURE_MIN_AGE_S = 30 * 60
DEFAULT_MIN_FREE_GB = 15.0

# Basename-only patterns for LU-owned ad-hoc temp residue.
_LEAK_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^review-\d+"),
    re.compile(r"^pr\d+"),  # pr + digits only (not pr* / process_ / protocol_)
    re.compile(r"^lu-"),
    re.compile(r"^mq-"),  # merge-queue log pulls (#7164)
    re.compile(r"^contracts-"),  # contracts-job scratch (#7164)
    re.compile(r"^learn-ukrainian-bridge-"),  # agent bridge asks (#7164)
    re.compile(r"^learn-ukrainian-"),
    re.compile(r"^atlas6507-"),
    re.compile(r"^data_test_"),
    re.compile(r"^data_debug"),
    re.compile(r"^hramatka-"),
    re.compile(r"^h409-"),
    re.compile(r"^infra-review-"),
    re.compile(r"^ci-\d+"),
    re.compile(r"^\d{4}-thog$"),
    re.compile(r"^\d{4}-fix$"),
    re.compile(r"^\d{4}-pytest"),
)

# Exact large legacy names that may be auto-deleted once age/ownership/liveness
# gates pass (#8738): the #8307 Atlas 410k outputs and the #8686 QA scratch dirs.
LEGACY_EXACT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "atlas-8307-410k-final.db",
        "atlas-8307-410k-r2.db",
        "atlas-8307-synthetic-410k.json",
        "qa-8686-ui-r2",
        "qa-8686-exercises-r2",
    }
)

# Atlas/QA families that are inventoried (reported) but never auto-deleted
# without fresh ownership proof.
_LEGACY_INVENTORY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^atlas-\d+"),
    re.compile(r"^qa-\d+"),
)

# Never deleted, never inventoried as residue: Atlas promotion plans and
# decision YAML must survive any sweep.
_PROTECTED_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"promotion", re.IGNORECASE),
    re.compile(r"decision.*\.ya?ml$", re.IGNORECASE),
    re.compile(r"\.decision\.ya?ml$", re.IGNORECASE),
)

CANDIDATE_KIND_PATTERN = "pattern"
CANDIDATE_KIND_LEGACY_EXACT = "legacy_exact"
CANDIDATE_KIND_LEGACY_INVENTORY = "legacy_inventory"

_PROC_ROOT = Path("/proc")


@dataclass(frozen=True)
class LeakCandidate:
    """One age-eligible temp path matching a known leak pattern."""

    path: Path
    age_s: float
    size_bytes: int
    kind: str = CANDIDATE_KIND_PATTERN

    @property
    def deletable(self) -> bool:
        return self.kind != CANDIDATE_KIND_LEGACY_INVENTORY


def default_tmp_roots() -> list[Path]:
    """Return distinct existing temp roots to scan (never $HOME).

    #7164: includes the disk-backed fleet scratch root (and the dispatcher's
    recorded base) alongside the legacy tmpfs locations, so residue drains
    from both old and new homes.
    """
    roots: list[Path] = []
    seen: set[Path] = set()
    raws = [str(resolve_scratch_root())]
    base_override = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT", "").strip()
    if base_override:
        raws.append(base_override)
    raws.extend([tempfile.gettempdir(), "/private/tmp", "/tmp"])
    for raw in raws:
        if not raw:
            continue
        path = Path(raw)
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            continue
        if resolved in seen:
            continue
        if not resolved.is_dir() or resolved.is_symlink():
            continue
        # Refuse to treat a home directory (or anything under it) as a tmp root.
        home = Path.home().resolve()
        try:
            resolved.relative_to(home)
            continue
        except ValueError:
            pass
        seen.add(resolved)
        roots.append(resolved)
    return roots


def name_matches_leak_pattern(name: str) -> bool:
    """Return whether a basename is an LU ad-hoc temp leak pattern."""
    return any(pattern.search(name) for pattern in _LEAK_NAME_PATTERNS)


def is_protected_name(name: str) -> bool:
    """Return whether a basename must never be swept (promotion plans, decision YAML)."""
    return any(pattern.search(name) for pattern in _PROTECTED_NAME_PATTERNS)


def classify_candidate_name(name: str) -> str | None:
    """Return the candidate kind for a basename, or ``None`` when it is not residue.

    Order matters: protected names are never residue; the exact legacy
    allowlist beats the inventory families; generic leak patterns come last.
    """
    if name == NAMESPACE_DIRNAME or is_protected_name(name):
        return None
    if name in LEGACY_EXACT_ALLOWLIST:
        return CANDIDATE_KIND_LEGACY_EXACT
    if any(pattern.search(name) for pattern in _LEGACY_INVENTORY_PATTERNS):
        return CANDIDATE_KIND_LEGACY_INVENTORY
    if name_matches_leak_pattern(name):
        return CANDIDATE_KIND_PATTERN
    return None


def excluded_scan_paths() -> set[Path]:
    """Paths the sweep must skip even when their basename matches a pattern.

    The managed task-scratch namespace, every scratch root and all of their
    ancestors: e.g. the fallback root ``<tmp>/lu-scratch`` matches ``^lu-``
    but is a root, not residue.
    """
    return managed_scratch_paths()


def free_space_gb(path: Path) -> float | None:
    """Return free space in GiB for the volume containing ``path``."""
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return usage.free / (1024**3)


def path_owned_by_self(path: Path) -> bool:
    """Return True when the entry is owned by the current effective UID."""
    try:
        return path.lstat().st_uid == os.geteuid()
    except OSError:
        return False


def _pgrep_references(path: Path) -> bool:
    """``pgrep -f`` probe; fails CLOSED (True) on any error or fatal exit code."""
    try:
        completed = subprocess.run(
            ["pgrep", "-f", str(path)],
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        # Fail closed: cannot prove unreferenced -> treat as live
        return True
    return completed.returncode != 1


def _text_references(blob: bytes, needle: str, prefix: str) -> bool:
    for raw in blob.split(b"\0"):
        try:
            text = raw.decode("utf-8", errors="surrogateescape")
        except UnicodeDecodeError:  # pragma: no cover - surrogateescape never raises
            continue
        if needle in text or prefix in text:
            return True
    return False


_PROC_DEAD_STATES = frozenset({"Z", "X"})  # zombie / dead: no cwd, fd table or environ


def _process_vanished(entry: Path) -> bool:
    """Return True only when ``/proc/<pid>`` itself is gone (the process exited)."""
    try:
        entry.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return False


def _process_state(entry: Path) -> str | None:
    """Return the scheduler state letter from ``/proc/<pid>/stat``, or ``None`` if unreadable."""
    try:
        blob = (entry / "stat").read_bytes()
    except OSError:
        return None
    _, _, tail = blob.rpartition(b")")
    fields = tail.split()
    return fields[0].decode("ascii", errors="replace") if fields else None


def _probe_process(entry: Path, needle: str, prefix: str) -> bool | None:
    """Probe one ``/proc/<pid>`` entry for a reference to ``needle``.

    Returns ``True`` when the process references the path, ``False`` only when
    every probe (state, command line, working directory, environment, open
    descriptors) was read and none referenced it, and ``None`` when any of
    them was unreadable for any reason while the process still exists. The
    process owner is never consulted: a foreign-uid process can hold a
    world-readable file open without naming it on its command line, so an
    unreadable cwd/fd table is unknown, not "no reference". The only way an
    unreadable probe becomes ``False`` is when ``/proc/<pid>`` has vanished
    (the process exited) or its state is zombie/dead, which holds nothing.
    """
    state = _process_state(entry)
    if state is None:
        return False if _process_vanished(entry) else None
    if state in _PROC_DEAD_STATES:
        return False
    try:
        cmdline = (entry / "cmdline").read_bytes()
    except OSError:
        return False if _process_vanished(entry) else None
    if _text_references(cmdline, needle, prefix):
        return True
    try:
        cwd = os.readlink(entry / "cwd")
    except OSError:
        return False if _process_vanished(entry) else None
    if cwd == needle or cwd.startswith(prefix):
        return True
    try:
        environ = (entry / "environ").read_bytes()
    except OSError:
        return False if _process_vanished(entry) else None
    if _text_references(environ, needle, prefix):
        return True
    try:
        fd_names = list((entry / "fd").iterdir())
    except OSError:
        return False if _process_vanished(entry) else None
    for fd_entry in fd_names:
        try:
            target = os.readlink(fd_entry)
        except FileNotFoundError:
            continue  # descriptor closed between listing and readlink: holds nothing now
        except OSError:
            return False if _process_vanished(entry) else None
        if target == needle or target.startswith(prefix):
            return True
    return False


def proc_references(path: Path, *, proc_root: Path | None = None) -> bool | None:
    """Scan ``/proc`` for processes that reference ``path``.

    Every process except the caller is probed the same way regardless of its
    owner: scheduler state, command line, working directory, environment and
    open file descriptors. Returns ``True`` when any reference is found,
    ``False`` only when every process was fully probed without finding one,
    and ``None`` when the answer is unknown: ``/proc`` absent or unreadable,
    or any process refused inspection of any probe for any reason
    (``EACCES``/``EPERM`` from a non-dumpable same-uid daemon, a root-owned
    service or a kernel thread, ``EIO``, ...). Unknown is never treated as
    "no reference": such a process may hold the path open. Ownership is not
    a proof of absence; a foreign-uid process can hold a world-readable
    legacy file open without naming it on its command line.

    Only two cases turn an unreadable process into "no reference": the
    ``/proc/<pid>`` directory vanished (the process exited), or its state is
    zombie/dead, which holds no cwd, descriptors or environment.

    ``proc_root`` defaults to the module's ``_PROC_ROOT`` at call time.
    """
    root = _PROC_ROOT if proc_root is None else proc_root
    if not root.is_dir():
        return None
    needle = str(path)
    prefix = needle.rstrip("/") + "/"
    my_pid = os.getpid()
    unknown = False
    try:
        entries = list(root.iterdir())
    except OSError:
        return None
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) == my_pid:
            continue
        verdict = _probe_process(entry, needle, prefix)
        if verdict:
            return True
        if verdict is None:
            unknown = True
    return None if unknown else False


LIVENESS_LIVE = "live"
LIVENESS_UNKNOWN = "unknown"
LIVENESS_CLEAR = "clear"


def path_liveness(path: Path, *, proc_root: Path | None = None) -> str:
    """Classify ``path`` as ``live``, ``unknown`` or ``clear``.

    Combines ``pgrep -f`` (command lines of every user) with the ``/proc``
    probe (state, cwd, open files, environment and command line of every
    process). Only ``clear`` permits deletion, and ``clear`` requires both a
    negative ``pgrep`` and a ``/proc`` walk in which every process was fully
    probed and none referenced the path.

    A negative ``pgrep`` alone is not proof: it only sees command lines, so a
    process holding the path as its cwd or through an open descriptor is
    invisible to it. A host without ``/proc`` (macOS) therefore returns
    ``unknown`` and preserves the path; there the legacy sweep is
    inventory-only and the managed task-scratch lifecycle is the cleanup path.
    """
    if _pgrep_references(path):
        return LIVENESS_LIVE
    verdict = proc_references(path, proc_root=proc_root)
    if verdict is None:
        return LIVENESS_UNKNOWN
    return LIVENESS_LIVE if verdict else LIVENESS_CLEAR


def path_has_live_process(path: Path) -> bool:
    """Return True unless every available probe proves ``path`` unreferenced."""
    return path_liveness(path) != LIVENESS_CLEAR


def _entry_age_s(path: Path, *, now: float) -> float | None:
    try:
        st = path.lstat()
    except OSError:
        return None
    # Use mtime only. On APFS, os.utime() refreshes ctime to "now", so
    # max(mtime, ctime) would always look young in tests and after touch-ups.
    return max(0.0, now - st.st_mtime)


def _entry_size_bytes(path: Path) -> int:
    try:
        completed = subprocess.run(
            ["du", "-sk", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return 0
    if completed.returncode != 0 or not completed.stdout.strip():
        return 0
    try:
        kib = int(completed.stdout.split()[0])
    except (TypeError, ValueError, IndexError):
        return 0
    return kib * 1024


def discover_candidates(
    tmp_roots: list[Path],
    *,
    now: float | None = None,
    min_age_s: float = DEFAULT_MIN_AGE_S,
) -> list[LeakCandidate]:
    """List age-eligible leak-pattern entries under the given tmp roots."""
    current = time.time() if now is None else now
    found: list[LeakCandidate] = []
    excluded = excluded_scan_paths()
    for root in tmp_roots:
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            kind = classify_candidate_name(child.name)
            if kind is None:
                continue
            if child in excluded or Path(os.path.abspath(str(child))) in excluded:
                continue
            try:
                st = child.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                continue
            if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
                continue
            age = _entry_age_s(child, now=current)
            if age is None or age < min_age_s:
                continue
            if not path_owned_by_self(child):
                continue
            found.append(
                LeakCandidate(
                    path=child,
                    age_s=age,
                    size_bytes=_entry_size_bytes(child),
                    kind=kind,
                )
            )
    return found


def _remove_path(path: Path, *, repo_root: Path, approved_temp_roots: tuple[Path, ...]) -> None:
    target = assert_delete_target(
        path,
        repo_root=repo_root,
        approved_temp_roots=approved_temp_roots,
    )
    if target.is_symlink() or target.is_file():
        target.unlink(missing_ok=True)
        return
    shutil.rmtree(target, ignore_errors=True)


_SKIP_REASONS = {LIVENESS_LIVE: "live_process", LIVENESS_UNKNOWN: "liveness_unknown"}


def sweep_tmp_leaks(
    *,
    apply: bool = False,
    tmp_roots: list[Path] | None = None,
    now: float | None = None,
    min_age_s: float = DEFAULT_MIN_AGE_S,
    pressure_min_age_s: float = DEFAULT_PRESSURE_MIN_AGE_S,
    min_free_gb: float = DEFAULT_MIN_FREE_GB,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Discover and optionally delete age-gated LU temp leaks.

    Returns a body-free summary suitable for scheduled hygiene receipts.
    """
    current = time.time() if now is None else now
    roots = list(tmp_roots) if tmp_roots is not None else default_tmp_roots()
    resolved_repo = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    approved_roots = tuple(roots)
    free_gb: float | None = None
    for root in roots:
        free_gb = free_space_gb(root)
        if free_gb is not None:
            break
    under_pressure = free_gb is not None and free_gb < min_free_gb
    effective_min_age = pressure_min_age_s if under_pressure else min_age_s

    candidates = discover_candidates(roots, now=current, min_age_s=effective_min_age)
    result: dict[str, Any] = {
        "apply": apply,
        "tmp_roots": [str(r) for r in roots],
        "free_gb": free_gb,
        "disk_pressure": under_pressure,
        "min_age_s": effective_min_age,
        "candidates": len(candidates),
        "roots_reaped": 0,
        "bytes_freed": 0,
        "skipped_live": 0,
        "inventory_only": 0,
        "inventory_bytes": 0,
        "errors": 0,
        "reaped": [],
        "skipped": [],
        "inventory": [],
    }

    for candidate in candidates:
        if not candidate.deletable:
            result["inventory_only"] += 1
            result["inventory_bytes"] += candidate.size_bytes
            result["inventory"].append(
                {
                    "path": str(candidate.path),
                    "bytes": candidate.size_bytes,
                    "age_s": int(candidate.age_s),
                    "kind": candidate.kind,
                    "action": "inventory_only",
                }
            )
            continue
        liveness = path_liveness(candidate.path)
        if liveness != LIVENESS_CLEAR:
            result["skipped_live"] += 1
            result["skipped"].append({"path": str(candidate.path), "reason": _SKIP_REASONS[liveness]})
            continue
        if not apply:
            result["reaped"].append(
                {
                    "path": str(candidate.path),
                    "bytes": candidate.size_bytes,
                    "age_s": int(candidate.age_s),
                    "kind": candidate.kind,
                    "action": "would_reap",
                }
            )
            continue
        # Re-check liveness immediately before deletion in apply mode
        liveness = path_liveness(candidate.path)
        if liveness != LIVENESS_CLEAR:
            result["skipped_live"] += 1
            result["skipped"].append({"path": str(candidate.path), "reason": _SKIP_REASONS[liveness]})
            continue
        try:
            size = candidate.size_bytes or _entry_size_bytes(candidate.path)
            _remove_path(
                candidate.path,
                repo_root=resolved_repo,
                approved_temp_roots=approved_roots,
            )
            # Confirm gone; if still present count as error.
            if candidate.path.exists():
                result["errors"] += 1
                result["skipped"].append({"path": str(candidate.path), "reason": "survived_remove"})
                continue
            result["roots_reaped"] += 1
            result["bytes_freed"] += size
            result["reaped"].append(
                {
                    "path": str(candidate.path),
                    "bytes": size,
                    "age_s": int(candidate.age_s),
                    "kind": candidate.kind,
                    "action": "reaped",
                }
            )
        except ValueError:
            result["errors"] += 1
            result["skipped"].append({"path": str(candidate.path), "reason": "delete_guard_refused"})
        except OSError:
            result["errors"] += 1
            result["skipped"].append({"path": str(candidate.path), "reason": "os_error"})
    return result


def _print_human(report: dict[str, Any]) -> None:
    mode = "APPLY" if report.get("apply") else "DRY-RUN"
    free = report.get("free_gb")
    free_s = f"{free:.1f} GiB free" if isinstance(free, (int, float)) else "free unknown"
    print(
        f"tmp leak sweep [{mode}]: candidates={report['candidates']} "
        f"reaped={report['roots_reaped']} skipped_live={report['skipped_live']} "
        f"errors={report['errors']} bytes_freed={report['bytes_freed']} "
        f"inventory_only={report.get('inventory_only', 0)} ({free_s})"
    )
    for item in report.get("reaped") or []:
        print(f"  {item.get('action')}: {item.get('path')} ({item.get('bytes', 0)} bytes, age={item.get('age_s')}s)")
    for item in report.get("skipped") or []:
        print(f"  skip: {item.get('path')} ({item.get('reason')})")
    for item in report.get("inventory") or []:
        print(
            f"  inventory: {item.get('path')} ({item.get('bytes', 0)} bytes, age={item.get('age_s')}s, not auto-deleted)"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete candidates (default is dry-run)",
    )
    parser.add_argument(
        "--min-age-s",
        type=float,
        default=DEFAULT_MIN_AGE_S,
        help=f"minimum age in seconds when disk is healthy (default {DEFAULT_MIN_AGE_S})",
    )
    parser.add_argument(
        "--pressure-min-age-s",
        type=float,
        default=DEFAULT_PRESSURE_MIN_AGE_S,
        help=f"minimum age under disk pressure (default {DEFAULT_PRESSURE_MIN_AGE_S})",
    )
    parser.add_argument(
        "--min-free-gb",
        type=float,
        default=DEFAULT_MIN_FREE_GB,
        help=f"free-space threshold for pressure mode (default {DEFAULT_MIN_FREE_GB})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON report instead of human summary",
    )
    args = parser.parse_args(argv)

    report = sweep_tmp_leaks(
        apply=args.apply,
        min_age_s=args.min_age_s,
        pressure_min_age_s=args.pressure_min_age_s,
        min_free_gb=args.min_free_gb,
    )
    if args.json:
        import json

        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
