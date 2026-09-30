"""Regression guard to ensure tests never write into repository checkout.

Monitors repository checkout state to prevent tests from modifying tracked files
or creating/appending checkout artifacts (e.g., site/src/data/lexicon-manifest.json,
logs/mcp-sources-requests.jsonl), including ignored deploy targets and data outputs.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MONITORED_CHECKOUT_PATHS: tuple[str, ...] = (
    "site/src/data/lexicon-manifest.json",
    "logs/mcp-sources-requests.jsonl",
)

# Root -> (watched immediate children, live-runtime exclusions relative to root).
# Agent roots are allowlisted to deploy outputs from scripts/deploy_prompts.sh;
# other scratch/driver state is outside the watched set. Exclusions are pruned
# before traversal, so continuous writers do not affect the session baseline.
MONITORED_CHECKOUT_TREES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    ".claude": (
        ("agents", "skills", "rules", "hooks", "settings*.json"),
        ("*-epic",),  # Live lane-driver briefs, handoffs and state.
    ),
    ".codex": (
        ("agents", "skills", "rules", "hooks", "settings*.json", "config.toml", "hooks.json"),
        (),
    ),
    ".agent": (
        ("agents", "skills", "rules", "hooks", "settings*.json"),
        (
            "sessions",  # Active harness session records.
            "runtime",  # Live process/driver state.
            "thread-rollovers",  # Continuity packets written by running lanes.
        ),
    ),
    ".gemini": (("agents", "skills", "rules", "hooks", "settings*.json"), ()),
    ".agents": (("skills",), ()),
    "data": (
        ("*",),
        (
            "telemetry",  # Continuously updated service/agent observations.
            "lexicon/cache",  # Live dictionary lookup cache.
        ),
    ),
}

EXEMPT_DIR_PARTS: frozenset[str] = frozenset(
    {
        ".pytest_cache",
        ".pytest_breadcrumbs",
        "__pycache__",
        ".hypothesis",
        ".mypy_cache",
        ".ruff_cache",
    }
)


class CheckoutWriteError(AssertionError):
    """Raised when an operation or test writes into the repository checkout."""


@dataclass(frozen=True)
class _FileSig:
    exists: bool
    size: int = 0
    sha256: str = ""


def _hash_file(path: Path) -> _FileSig:
    if not path.is_file():
        return _FileSig(exists=False)
    try:
        data = path.read_bytes()
        return _FileSig(exists=True, size=len(data), sha256=hashlib.sha256(data).hexdigest())
    except OSError:
        return _FileSig(exists=False)


def _is_exempt_path(relpath: str) -> bool:
    parts = set(Path(relpath).parts)
    return bool(parts & EXEMPT_DIR_PARTS)


def _walk_files(
    root: Path, watched: tuple[str, ...] = ("*",), excluded: tuple[str, ...] = (),
) -> Iterator[Path]:
    """Prune root-relative runtime paths and tolerate vanishing directories."""
    def onerror(error: OSError) -> None:
        if not isinstance(error, FileNotFoundError):
            raise error

    def included(path: Path) -> bool:
        relative = path.relative_to(root)
        rel = relative.as_posix()
        return (
            (len(relative.parts) > 1 or any(fnmatchcase(path.name, pattern) for pattern in watched))
            # fnmatch's '*' crosses '/', so anchor exclusions to their depth.
            # A top-level '*-epic' must not hide skills/drive-epic/SKILL.md.
            and not any(
                rel.count("/") == pattern.count("/") and fnmatchcase(rel, pattern)
                for pattern in excluded
            )
            and not _is_exempt_path(rel)
        )

    for parent, directories, files in os.walk(root, onerror=onerror):
        directory = Path(parent)
        directories[:] = [name for name in directories if included(directory / name)]
        for name in files:
            if included(directory / name):
                yield directory / name


class CheckoutWriteGuard:
    """Guard against checkout modifications during test execution.

    Takes a baseline snapshot of the checkout on enter/start, accounts for
    pre-existing changes and sparse files, and checks that no tracked files are
    altered and no guarded artifacts are created or modified.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.root = (repo_root or PROJECT_ROOT).resolve()
        self._before_monitored: dict[str, _FileSig] = {}
        self._before_porcelain: dict[str, str] = {}
        self._before_tracked_sigs: dict[str, _FileSig] = {}
        self._before_logs: dict[str, _FileSig] = {}
        self._before_tree_files: dict[str, tuple[int, int]] = {}
        self._is_git_repo = (self.root / ".git").exists()
        self.snapshot()

    def _query_git_porcelain(self) -> dict[str, str]:
        if not self._is_git_repo:
            return {}
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if res.returncode != 0:
                return {}
        except OSError:
            return {}

        statuses: dict[str, str] = {}
        for line in res.stdout.splitlines():
            if len(line) < 4:
                continue
            code = line[:2]
            path_str = line[3:].strip()
            if " -> " in path_str:
                path_str = path_str.split(" -> ")[1].strip()
            if path_str:
                statuses[path_str] = code
        return statuses

    def snapshot(self) -> None:
        """Capture the baseline state of the repository."""
        self._before_monitored = {
            rel: _hash_file(self.root / rel) for rel in MONITORED_CHECKOUT_PATHS
        }
        self._before_porcelain = self._query_git_porcelain()
        self._before_tracked_sigs = {
            path: _hash_file(self.root / path)
            for path in self._before_porcelain
        }
        self._before_logs = self._log_signatures()
        self._before_tree_files = self._tree_signatures()

    def _tree_signatures(self) -> dict[str, tuple[int, int]]:
        """Watch deploy/data files cheaply, without reading large corpus payloads."""
        signatures = {}
        for rel_root, (watched, excluded) in MONITORED_CHECKOUT_TREES.items():
            for path in _walk_files(self.root / rel_root, watched, excluded):
                rel = path.relative_to(self.root).as_posix()
                try:
                    file_stat = path.stat()
                except FileNotFoundError:
                    continue
                if stat.S_ISREG(file_stat.st_mode):
                    signatures[rel] = (file_stat.st_mtime_ns, file_stat.st_size)
        return signatures

    def _log_signatures(self) -> dict[str, _FileSig]:
        """Include ignored, pre-existing logs in the session baseline."""
        return {
            path.relative_to(self.root).as_posix(): _hash_file(path)
            for path in _walk_files(self.root / "logs")
            if path.is_file()
        }

    def check(self) -> list[str]:
        """Compare current checkout state against baseline and return violations."""
        violations: list[str] = []

        after_tree_files = self._tree_signatures()
        for rel in sorted(self._before_tree_files.keys() | after_tree_files.keys()):
            if rel not in self._before_tree_files:
                violations.append(f"guarded checkout file created: {rel}")
            elif rel not in after_tree_files:
                violations.append(f"guarded checkout file deleted: {rel}")
            elif self._before_tree_files[rel] != after_tree_files[rel]:
                violations.append(f"guarded checkout file modified/appended: {rel}")

        # 1. Monitored checkout artifacts (manifest, sources request log)
        for rel in MONITORED_CHECKOUT_PATHS:
            before_sig = self._before_monitored.get(rel, _FileSig(exists=False))
            after_sig = _hash_file(self.root / rel)

            if not before_sig.exists and after_sig.exists:
                violations.append(f"guarded checkout artifact created: {rel}")
            elif before_sig.exists and not after_sig.exists:
                violations.append(f"guarded checkout artifact deleted: {rel}")
            elif before_sig.exists and after_sig.exists and before_sig.sha256 != after_sig.sha256:
                violations.append(f"guarded checkout artifact modified/appended: {rel}")

        # Compare all logs, including ignored files, against their real baseline.
        for rel, after_sig in self._log_signatures().items():
            if rel in MONITORED_CHECKOUT_PATHS:
                continue
            before_sig = self._before_logs.get(rel)
            if before_sig is None:
                violations.append(f"unexpected file created in checkout logs/: {rel}")
            elif before_sig != after_sig:
                violations.append(f"pre-existing checkout log modified/appended: {rel}")

        # 2. Git status against baseline (tracked changes and non-exempt untracked files)
        if self._is_git_repo:
            after_porcelain = self._query_git_porcelain()
            for path, code in after_porcelain.items():
                if _is_exempt_path(path):
                    continue

                if path not in self._before_porcelain:
                    # Brand new change that was not in baseline
                    if code.startswith("??"):
                        violations.append(f"untracked checkout file created: {path}")
                    else:
                        violations.append(f"tracked file modified: {path} (status: {code})")
                else:
                    # File was in baseline; check if it was mutated during test
                    before_sig = self._before_tracked_sigs.get(path, _FileSig(exists=False))
                    after_sig = _hash_file(self.root / path)
                    if before_sig.exists and after_sig.exists and before_sig.sha256 != after_sig.sha256:
                        violations.append(f"pre-existing file mutated during test: {path}")

        return violations

    def verify(self) -> None:
        """Raise CheckoutWriteError if any checkout write occurred."""
        violations = self.check()
        if violations:
            msg = "Checkout write violation(s) detected:\n" + "\n".join(f"  - {v}" for v in violations)
            raise CheckoutWriteError(msg)

    def __enter__(self) -> CheckoutWriteGuard:
        self.snapshot()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            self.verify()


def pytest_sessionstart(session: Any) -> None:
    """Baseline once per normal session, loaded through tests/conftest.py."""
    session.config._checkout_write_guard = CheckoutWriteGuard()


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Check for checkout mutations at test session completion."""
    guard = getattr(session.config, "_checkout_write_guard", None)
    if guard is not None:
        violations = guard.check()
        if violations:
            session.exitstatus = 1
            terminal = session.config.pluginmanager.get_plugin("terminalreporter")
            if terminal is not None:
                terminal.write_line("ERROR: checkout mutations detected by checkout_write_guard:")
                for violation in violations:
                    terminal.write_line(f"  - {violation}")
