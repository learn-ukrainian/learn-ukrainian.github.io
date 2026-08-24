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

# Exact ``(path, stripped snippet, max_occurrences)`` allowlist for already-scoped
# shell cleanups. Matched by content, not line number, so insertions above an
# entry do not re-break the lint. Do not expand this to cover new recursive
# deletes — route those through a guarded helper.
_ALLOWLIST: tuple[tuple[str, str, int], ...] = (
    # services.sh: restart lockdir reclaim/release + Astro/Vite cache dirs
    # (scoped under $PIDS_DIR / $PROJECT_ROOT/site/…). Do not rewrite.
    ("services.sh", "rm -rf \"$lockdir\" 2>/dev/null || true", 2),
    ("services.sh", "rm -rf \"$vite_cache_dir\"", 1),
    ("services.sh", "rm -rf \"$dist_dir\"", 1),
    ("services.sh", "rm -rf \"$astro_dir\"", 1),
    # Scratch-dir EXIT traps for one-shot installer scripts.
    ("scripts/entire/install_kimi_external_agent.sh", "trap 'rm -rf \"${scratch_dir}\"' EXIT", 1),
    ("scripts/entire/install_fleet_external_agent.sh", "trap 'rm -rf \"${scratch_dir}\"' EXIT", 1),
    # Actionlint download cleanup (scoped under a local temp dir).
    (
        "scripts/audit/check_workflows.sh",
        "cleanup() { [[ -n \"$_DOWNLOAD_DIR\" ]] && rm -rf \"$_DOWNLOAD_DIR\"; return 0; }",
        1,
    ),
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


def _allowlist_lookup() -> dict[tuple[str, str], int]:
    return {(path, snippet): max_count for path, snippet, max_count in _ALLOWLIST}


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
    allowlist = _allowlist_lookup()
    usage: dict[tuple[str, str], int] = {}
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
            stripped = line.strip()
            content_key = (rel, stripped)
            max_allowed = allowlist.get(content_key)
            if max_allowed is not None:
                usage[content_key] = usage.get(content_key, 0) + 1
                if usage[content_key] <= max_allowed:
                    continue
            findings.append((f"{rel}:{line_no}", stripped))
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
