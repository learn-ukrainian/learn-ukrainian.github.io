#!/usr/bin/env python3
"""Lint scripts/ (and services.sh) for raw ``rm -rf`` invocations (#6013).

Python deleters must go through ``assert_delete_target``. Shell ``rm -rf`` is
still used for a small set of already-scoped lockdirs/caches; those paths are
allowlisted here rather than rewritten. New unscoped ``rm -rf`` lines fail.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Match ``rm -rf``, ``rm -fr``, and compact flag forms such as ``rm -rfv``.
_RM_RF_RE = re.compile(r"(?:^|[\s;|&])rm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b")

# Exact ``path:line`` allowlist for already-scoped shell cleanups. Do not expand
# this to cover new recursive deletes — route those through a guarded helper.
_ALLOWLIST: frozenset[str] = frozenset(
    {
        # services.sh: restart lockdir reclaim/release + Astro/Vite cache dirs
        # (scoped under $PIDS_DIR / $PROJECT_ROOT/site/…). Do not rewrite.
        "services.sh:119",
        "services.sh:138",
        "services.sh:617",
        "services.sh:627",
        "services.sh:631",
        # Scratch-dir EXIT traps for one-shot installer scripts.
        "scripts/entire/install_kimi_external_agent.sh:18",
        "scripts/entire/install_fleet_external_agent.sh:36",
        # Actionlint download cleanup (scoped under a local temp dir).
        "scripts/audit/check_workflows.sh:50",
    }
)

_SCAN_GLOBS: tuple[str, ...] = (
    "scripts/**/*.sh",
    "scripts/**/*.bash",
    "services.sh",
)

# Test harnesses may use ``rm -rf`` under their own temp roots.
_SKIP_PATH_PREFIXES: tuple[str, ...] = (
    "scripts/audit/test_",
    "tests/",
)


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def iter_scan_paths(repo_root: Path | None = None) -> list[Path]:
    root = (repo_root or REPO_ROOT).resolve()
    found: list[Path] = []
    for pattern in _SCAN_GLOBS:
        found.extend(root.glob(pattern))
    unique = sorted({path.resolve() for path in found if path.is_file()})
    return [
        path
        for path in unique
        if not any(_rel(path, root).startswith(prefix) for prefix in _SKIP_PATH_PREFIXES)
    ]


def find_raw_rm_rf(repo_root: Path | None = None) -> list[tuple[str, str]]:
    """Return ``(path:line, snippet)`` findings not covered by the allowlist."""
    root = (repo_root or REPO_ROOT).resolve()
    findings: list[tuple[str, str]] = []
    for path in iter_scan_paths(root):
        rel = _rel(path, root)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if not _RM_RF_RE.search(line):
                continue
            key = f"{rel}:{line_no}"
            if key in _ALLOWLIST:
                continue
            findings.append((key, line.strip()))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    findings = find_raw_rm_rf()
    if not findings:
        print("OK: no unscoped raw rm -rf in scripts/ or services.sh")
        return 0
    print("Unscoped raw rm -rf (route through a guarded deleter or allowlist):", file=sys.stderr)
    for key, snippet in findings:
        print(f"  {key}: {snippet}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
