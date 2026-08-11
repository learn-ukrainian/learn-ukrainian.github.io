#!/usr/bin/env python3
"""Reap ad-hoc LU temp trees under $TMPDIR that isolation sweeps miss.

Agents and one-shot review flows leave multi-GB directories such as
``/tmp/review-6621`` (full clones) and ``/tmp/pr6591-exact-*``.  Formal
``sweep_review_temp_orphans`` only reaps ``lu-review-*`` / shielded-reviews
manifests, so these names never drain without manual intervention.

This module is age-gated, name-pattern scoped, and fail-open on live
processes.  It is not a blanket ``rm -rf /tmp/*``.
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

# 2h normal; 30m under disk pressure.
DEFAULT_MIN_AGE_S = 2 * 60 * 60
DEFAULT_PRESSURE_MIN_AGE_S = 30 * 60
DEFAULT_MIN_FREE_GB = 15.0

# Basename-only patterns for LU-owned ad-hoc temp residue.
_LEAK_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^review-\d+"),
    re.compile(r"^pr\d+"),  # pr + digits only (not pr* / process_ / protocol_)
    re.compile(r"^lu-"),
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


@dataclass(frozen=True)
class LeakCandidate:
    """One age-eligible temp path matching a known leak pattern."""

    path: Path
    age_s: float
    size_bytes: int


def default_tmp_roots() -> list[Path]:
    """Return distinct existing temp roots to scan (never $HOME)."""
    roots: list[Path] = []
    seen: set[Path] = set()
    for raw in (tempfile.gettempdir(), "/private/tmp", "/tmp"):
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


def path_has_live_process(path: Path) -> bool:
    """Best-effort check: any process whose cmdline mentions this path."""
    try:
        completed = subprocess.run(
            ["pgrep", "-f", str(path)],
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        # Fail open: cannot prove live → treat as not live for age-gated junk,
        # but still only delete pattern matches older than min_age.
        return False
    return completed.returncode == 0


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
    for root in tmp_roots:
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if not name_matches_leak_pattern(child.name):
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
                )
            )
    return found


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    shutil.rmtree(path, ignore_errors=True)


def sweep_tmp_leaks(
    *,
    apply: bool = False,
    tmp_roots: list[Path] | None = None,
    now: float | None = None,
    min_age_s: float = DEFAULT_MIN_AGE_S,
    pressure_min_age_s: float = DEFAULT_PRESSURE_MIN_AGE_S,
    min_free_gb: float = DEFAULT_MIN_FREE_GB,
) -> dict[str, Any]:
    """Discover and optionally delete age-gated LU temp leaks.

    Returns a body-free summary suitable for scheduled hygiene receipts.
    """
    current = time.time() if now is None else now
    roots = list(tmp_roots) if tmp_roots is not None else default_tmp_roots()
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
        "errors": 0,
        "reaped": [],
        "skipped": [],
    }

    for candidate in candidates:
        if path_has_live_process(candidate.path):
            result["skipped_live"] += 1
            result["skipped"].append(
                {"path": str(candidate.path), "reason": "live_process"}
            )
            continue
        if not apply:
            result["reaped"].append(
                {
                    "path": str(candidate.path),
                    "bytes": candidate.size_bytes,
                    "age_s": int(candidate.age_s),
                    "action": "would_reap",
                }
            )
            continue
        try:
            size = candidate.size_bytes or _entry_size_bytes(candidate.path)
            _remove_path(candidate.path)
            # Confirm gone; if still present count as error.
            if candidate.path.exists():
                result["errors"] += 1
                result["skipped"].append(
                    {"path": str(candidate.path), "reason": "survived_remove"}
                )
                continue
            result["roots_reaped"] += 1
            result["bytes_freed"] += size
            result["reaped"].append(
                {
                    "path": str(candidate.path),
                    "bytes": size,
                    "age_s": int(candidate.age_s),
                    "action": "reaped",
                }
            )
        except OSError:
            result["errors"] += 1
            result["skipped"].append(
                {"path": str(candidate.path), "reason": "os_error"}
            )
    return result


def _print_human(report: dict[str, Any]) -> None:
    mode = "APPLY" if report.get("apply") else "DRY-RUN"
    free = report.get("free_gb")
    free_s = f"{free:.1f} GiB free" if isinstance(free, (int, float)) else "free unknown"
    print(
        f"tmp leak sweep [{mode}]: candidates={report['candidates']} "
        f"reaped={report['roots_reaped']} skipped_live={report['skipped_live']} "
        f"errors={report['errors']} bytes_freed={report['bytes_freed']} ({free_s})"
    )
    for item in report.get("reaped") or []:
        print(
            f"  {item.get('action')}: {item.get('path')} "
            f"({item.get('bytes', 0)} bytes, age={item.get('age_s')}s)"
        )
    for item in report.get("skipped") or []:
        print(f"  skip: {item.get('path')} ({item.get('reason')})")


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
