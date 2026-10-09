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
from itertools import chain
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MONITORED_CHECKOUT_PATHS: tuple[str, ...] = (
    "site/src/data/lexicon-manifest.json",
    "logs/mcp-sources-requests.jsonl",
)

# Two small, known default outputs: inspect only these at test boundaries.
# The complete watched set is still checked once at session completion.
ATTRIBUTED_CHECKOUT_PATHS: tuple[str, ...] = (
    ".claude/agents/curriculum-writer.md",
    "data/corpus_audit/section_extraction_report.md",
)

# Root -> (watched immediate children, live-runtime exclusions relative to root).
# Watch .claude/ and .codex/ fully except runtime entries and the non-owned
# orphans in scripts/deploy_orphan_paths.sh. Keep .agent/ allowlisted because
# its top level holds live leases and audits; .agents/ watches deployed skills.
# Exclusions are root-anchored and pruned before traversal.
MONITORED_CHECKOUT_TREES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    ".claude": (
        ("*",),
        ("*-epic", "worktrees", "settings.local.json", "scheduled_tasks.lock"),
    ),
    ".codex": (
        ("*",),
        ("*-epic", "worktrees", "settings.local.json", "retired-skills"),
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
        (
            "corpus_audit",  # Section-extraction tests write reports here.
            "embeddings",  # Sources rebuilds reserve a manifest and wiki shard.
        ),
        (),  # Other data files are watched only if git-tracked (see below).
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


def _is_unwatched_runtime_path(relpath: str) -> bool:
    """Keep untracked live state and coverage data out of the Git-status check."""
    parts = Path(relpath).parts
    # pytest-cov writes a root-level data file, optionally with a parallel suffix.
    if len(parts) == 1:
        return parts[0] == ".coverage" or parts[0].startswith(".coverage.")
    if len(parts) < 2:
        return False
    root, child = parts[:2]
    if root == "data":
        watched, _ = MONITORED_CHECKOUT_TREES[root]
        return not any(fnmatchcase(child, pattern) for pattern in watched)
    if root in (".claude", ".codex", ".agent"):
        _, excluded = MONITORED_CHECKOUT_TREES[root]
        return any(fnmatchcase(child, pattern) for pattern in excluded)
    return False


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
        self._test_violations: list[str] = []
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
            for path, code in self._before_porcelain.items()
            if not (code.startswith("??") and _is_unwatched_runtime_path(path))
        }
        self._before_logs = self._log_signatures()
        self._before_tree_files = self._tree_signatures()

    def _tree_signatures(self) -> dict[str, tuple[int, int]]:
        """Watch deploy/data files cheaply, without reading large corpus payloads."""
        signatures = {}
        paths = (
            path
            for rel_root, (watched, excluded) in MONITORED_CHECKOUT_TREES.items()
            for path in _walk_files(self.root / rel_root, watched, excluded)
        )
        if self._is_git_repo:
            tracked = subprocess.run(
                ["git", "ls-files", "-z", "--", "data"],
                cwd=self.root, capture_output=True, check=True, timeout=30,
            )
            paths = chain(paths, (
                self.root / os.fsdecode(raw) for raw in tracked.stdout.split(b"\0") if raw
            ))
        for path in paths:
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
                if code.startswith("??") and _is_unwatched_runtime_path(path):
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


def _attribution_signatures(root: Path) -> dict[str, tuple[int, int] | None]:
    """Stat only the known targets; never scan trees or read corpus content."""
    signatures = {}
    for rel in ATTRIBUTED_CHECKOUT_PATHS:
        try:
            metadata = (root / rel).stat()
        except FileNotFoundError:
            signatures[rel] = None
        else:
            signatures[rel] = (metadata.st_mtime_ns, metadata.st_size) if stat.S_ISREG(metadata.st_mode) else None
    return signatures


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: Any, nextitem: Any) -> Iterator[None]:
    """Attribute known writes across a test's setup, call, and teardown."""
    guard = getattr(item.config, "_checkout_write_guard", None)
    before = _attribution_signatures(guard.root) if guard is not None else {}
    yield
    after = _attribution_signatures(guard.root) if guard is not None else {}
    for rel, old in before.items():
        new = after[rel]
        if old == new:
            continue
        action = "created" if old is None else "deleted" if new is None else "modified/appended"
        guard._test_violations.append(
            f"guarded checkout file {action}: {rel} (test: {item.nodeid})",
        )


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node: Any, error: Any) -> None:
    """Collect worker attribution before the controller's sessionfinish hook."""
    guard = getattr(node.config, "_checkout_write_guard", None)
    if guard is not None:
        guard._test_violations.extend(getattr(node, "workeroutput", {}).get("checkout_write_violations", []))


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Check for checkout mutations at test session completion."""
    guard = getattr(session.config, "_checkout_write_guard", None)
    if guard is not None:
        violations = guard._test_violations + guard.check()
        if hasattr(session.config, "workeroutput"):
            session.config.workeroutput["checkout_write_violations"] = violations
        if violations:
            session.exitstatus = 1
            terminal = session.config.pluginmanager.get_plugin("terminalreporter")
            if terminal is not None:
                terminal.write_line("ERROR: checkout mutations detected by checkout_write_guard:")
                for violation in violations:
                    terminal.write_line(f"  - {violation}")
