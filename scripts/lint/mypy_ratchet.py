#!/usr/bin/env python3
"""Ratchet mypy on scripts/: new errors fail, and the baseline only shrinks (#12642).

Identity is ``(path, error code, message)``. Line and column are not part of
it, so inserting a line above an existing error does not churn the baseline.
A message that mypy no longer reports is a stale baseline entry and fails.
Once ``origin/main`` contains the baseline, the committed multiset may only
shrink. Before that first landing, the baseline has no predecessor; it must
still equal the mypy census exactly, so entries mypy does not report fail.

Examples:
  .venv/bin/python -m scripts.lint.mypy_ratchet
  .venv/bin/python -m scripts.lint.mypy_ratchet scripts/lint/mypy_ratchet.py
  .venv/bin/python -m scripts.lint.mypy_ratchet --write-baseline

Outputs: one violation per new or stale identity on stderr, or a one-line
pass message on stdout. ``--write-baseline`` rewrites the baseline JSON.
Exit codes: 0 pass or baseline written; 1 a new error, a stale entry, growth,
or mypy could not run.
Related: #12642, scripts/hygiene/lint_source_db_writable_connects.py.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("mypy_baseline.json")
SCHEMA = "mypy-ratchet-baseline.v1"
DEFAULT_TARGET = "scripts"
MYPY_TIMEOUT_SECONDS = 600
_GIT_TIMEOUT_SECONDS = 30
_SHRINK_REFS = ("HEAD", "HEAD^", "origin/main")

# path:line:col: error: message  [code]  — column is optional.
_REPORT = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<col>\d+))?: (?P<sev>error|note): "
    r"(?P<msg>.*?)(?:  \[(?P<code>[^\]]+)\])?\s*$"
)


@dataclass(frozen=True, order=True)
class MypyError:
    """One mypy error. Line and column are intentionally absent."""

    path: str
    code: str
    message: str

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.path, self.code, self.message)


def _relative(root: Path, raw: str) -> str | None:
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError:
            return None
    text = path.as_posix()
    if text.startswith("./"):
        text = text[2:]
    if not text or text.startswith("../"):
        return None
    return text


def parse_mypy_stdout(text: str, root: Path) -> tuple[list[MypyError], list[str]]:
    """Parse an error report. Notes are ignored. Non-error junk is returned."""

    errors: list[MypyError] = []
    unparsed: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = _REPORT.match(line)
        if match is None:
            unparsed.append(line)
            continue
        if match.group("sev") != "error":
            continue
        rel = _relative(root, match.group("path"))
        code = match.group("code")
        if rel is None or not code:
            unparsed.append(line)
            continue
        errors.append(MypyError(rel, code, match.group("msg")))
    return errors, unparsed


def _covers(path: str, target: str) -> bool:
    return path == target or path.startswith(target.rstrip("/") + "/")


def _in_scope(path: str, targets: Sequence[str]) -> bool:
    return any(_covers(path, target) for target in targets)


def _normalize_targets(root: Path, paths: Sequence[str]) -> list[str]:
    targets: list[str] = []
    for raw in paths:
        rel = _relative(root, raw)
        if rel is None:
            raise ValueError(f"path is outside the tree: {raw}")
        targets.append(rel)
    return targets


def mypy_command(
    targets: Sequence[str],
    *,
    config_file: Path | None,
    incremental: bool,
) -> list[str]:
    """The production mypy invocation. Flags that change the error set stay at
    the existing ``[tool.mypy]`` defaults; ``--platform linux`` matches CI.
    """

    command = [
        sys.executable,
        "-m",
        "mypy",
        "--platform",
        "linux",
        "--show-error-codes",
        "--no-error-summary",
        "--no-color-output",
        "--hide-error-context",
        "--no-pretty",
        "--hide-absolute-path",
        "--follow-imports",
        "normal",
    ]
    if config_file is not None:
        command.extend(["--config-file", str(config_file)])
    if incremental:
        command.append("--incremental")
    else:
        command.append("--no-incremental")
    command.extend(targets)
    return command


def collect_errors(
    root: Path,
    targets: Sequence[str],
    *,
    config_file: Path | None = None,
    incremental: bool = True,
) -> tuple[list[MypyError], list[str]]:
    """Run mypy. Fatal runner failures come back as violation strings."""

    existing = [target for target in targets if (root / target).exists()]
    if not existing:
        return [], []
    command = mypy_command(existing, config_file=config_file, incremental=incremental)
    env = {**os.environ, "MYPY_FORCE_COLOR": "0"}
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=MYPY_TIMEOUT_SECONDS,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [], [f"mypy timed out after {MYPY_TIMEOUT_SECONDS}s"]
    if result.returncode not in (0, 1):
        detail = (result.stderr or result.stdout).strip()
        return [], [f"mypy failed ({result.returncode}): {detail}"]
    errors, unparsed = parse_mypy_stdout(result.stdout, root)
    if unparsed:
        return [], [f"mypy report was not parseable: {unparsed[0]}"]
    return [error for error in errors if _in_scope(error.path, targets)], []


def _counts(errors: Iterable[MypyError]) -> Counter[tuple[str, str, str]]:
    return Counter(error.identity for error in errors)


def compare(current: Sequence[MypyError], baseline: Sequence[MypyError]) -> list[str]:
    """New identities fail, and baseline identities mypy no longer reports fail."""

    current_counts = _counts(current)
    baseline_counts = _counts(baseline)
    violations: list[str] = []
    for identity in sorted(set(current_counts) | set(baseline_counts)):
        path, code, message = identity
        extra = current_counts[identity] - baseline_counts[identity]
        if extra > 0:
            suffix = f" x{extra}" if extra > 1 else ""
            violations.append(f"{path}: new {code}{suffix}: {message}")
        missing = baseline_counts[identity] - current_counts[identity]
        if missing > 0:
            suffix = f" x{missing}" if missing > 1 else ""
            violations.append(f"{path}: stale baseline {code}{suffix}: {message}")
    return violations


def _entries_from_rows(rows: object, where: str) -> list[MypyError]:
    if not isinstance(rows, list):
        raise ValueError(f"{where}: entries must be a list")
    entries: list[MypyError] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{where}: an entry is not an object")
        rel = row.get("path")
        code = row.get("code")
        message = row.get("message")
        if (
            not isinstance(rel, str)
            or not rel
            or not isinstance(code, str)
            or not code
            or not isinstance(message, str)
            or not message
        ):
            raise ValueError(f"{where}: an entry needs path, code, and message")
        if rel.startswith(("/", "\\")) or ".." in Path(rel).parts:
            raise ValueError(f"{where}: entry path is not relative: {rel}")
        entries.append(MypyError(rel, code, message))
    return entries


def _payload_entries(payload: object, where: str) -> list[MypyError]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{where}: schema must be {SCHEMA}")
    return _entries_from_rows(payload.get("entries"), where)


def load_entries(path: Path) -> list[MypyError]:
    return _payload_entries(json.loads(path.read_text(encoding="utf-8")), str(path))


def write_baseline(path: Path, entries: Sequence[MypyError]) -> None:
    payload = {
        "schema": SCHEMA,
        "mypy": importlib.metadata.version("mypy"),
        "entries": [
            {"path": error.path, "code": error.code, "message": error.message}
            for error in sorted(entries)
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _baseline_at(root: Path, ref: str, rel: str) -> list[MypyError] | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        return None
    return _payload_entries(json.loads(result.stdout), f"{ref}:{rel}")


def _is_subset(current: Sequence[MypyError], previous: Sequence[MypyError]) -> bool:
    current_counts = _counts(current)
    previous_counts = _counts(previous)
    return all(current_counts[identity] <= previous_counts[identity] for identity in current_counts)


def shrink_violations(root: Path, baseline: Path, entries: Sequence[MypyError]) -> list[str]:
    """Reject growth against a baseline that has already landed on origin/main.

    A missing ``.git`` (fixture trees) and a baseline not yet on the default
    branch have no predecessor to shrink. A ``git show`` miss skips that ref.
    """

    if not (root / ".git").exists():
        return []
    try:
        rel = baseline.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return []
    if _baseline_at(root, "origin/main", rel) is None:
        return []
    violations: list[str] = []
    for ref in _SHRINK_REFS:
        try:
            previous = _baseline_at(root, ref, rel)
        except (json.JSONDecodeError, ValueError) as exc:
            return [f"{rel}: baseline at {ref} is unreadable: {exc}"]
        if previous is None:
            continue
        if not _is_subset(entries, previous):
            violations.append(f"{rel}: baseline may only shrink; freeze/growth differs from {ref}")
    return violations


def evaluate(
    root: Path,
    baseline: Path,
    targets: Sequence[str],
    *,
    config_file: Path | None = None,
    incremental: bool = True,
) -> list[str]:
    """Return violation strings. An empty list is a pass."""

    selected = _normalize_targets(root, targets)
    py_targets = [target for target in selected if target.endswith(".py") or (root / target).is_dir()]
    # A baseline-only path (no Python) rechecks the whole scripts tree.
    scoped = py_targets or [DEFAULT_TARGET]
    current, fatal = collect_errors(
        root, scoped, config_file=config_file, incremental=incremental
    )
    if fatal:
        return fatal
    entries = load_entries(baseline)
    # A file list compares only those files. The full scripts/ census also
    # rejects a baseline entry that names something outside scripts/.
    relevant = [entry for entry in entries if _in_scope(entry.path, scoped)]
    violations: list[str] = []
    if DEFAULT_TARGET in scoped:
        violations.extend(
            f"{entry.path}: stale baseline {entry.code}: {entry.message}"
            for entry in entries
            if not _in_scope(entry.path, (DEFAULT_TARGET,))
        )
    violations.extend(compare(current, relevant))
    violations.extend(shrink_violations(root, baseline, entries))
    return violations


def _python_targets(paths: Sequence[str], root: Path) -> list[str]:
    if not paths:
        return [DEFAULT_TARGET]
    selected = _normalize_targets(root, paths)
    python = [target for target in selected if target.endswith(".py")]
    return python or [DEFAULT_TARGET]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python files to check (default: scripts/). Other paths recheck scripts/.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_PATH,
        help="Baseline JSON (default: scripts/lint/mypy_baseline.json).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Tree mypy runs in (default: repository root).",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Rewrite the baseline from the current mypy census and exit.",
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="Ignore the mypy cache. Tests use this; CI keeps the cache.",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    baseline = args.baseline if args.baseline.is_absolute() else root / args.baseline
    try:
        targets = [DEFAULT_TARGET] if args.write_baseline else _python_targets(args.paths, root)
        if args.write_baseline:
            current, fatal = collect_errors(
                root, targets, incremental=not args.no_incremental
            )
            if fatal:
                print("\n".join(fatal), file=sys.stderr)
                return 1
            write_baseline(baseline, current)
            print(f"Wrote {len(current)} mypy errors to {baseline.relative_to(root)}")
            return 0
        violations = evaluate(
            root, baseline, targets, incremental=not args.no_incremental
        )
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"mypy ratchet could not run: {exc}", file=sys.stderr)
        return 1
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("OK: mypy ratchet matches the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
