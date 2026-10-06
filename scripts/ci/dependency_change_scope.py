#!/usr/bin/env python3
"""Dependency-input changed-path scope for the CI dependency-audit job (#9871).

The dependency-audit job runs this helper after checkout to decide whether the
diff touches a declared dependency input
(``scripts/ci/dependency_change_denominator.json``). No dependency input
changed -> exit 0 with ``run=false`` and a loud "not applicable: no dependency
input changed" line in the log and step summary; the remaining job steps skip
and the job still ends ``success`` so CI Gate keeps requiring ``success``.
Any uncertainty (missing base SHA, unresolvable merge-base, git diff failure)
fails closed to ``run``: the full audit executes exactly as before.

PR / merge_group events use merge-base range semantics against the *event*
head SHA (not the synthetic merge-commit checkout), mirroring
``frontend_change_scope.py`` (#6917 / #6930). Push keeps linear two-dot
``before..after``. Added, modified, deleted and renamed (either side) paths
all count.

Stdlib only so GitHub runners can invoke it with system ``python3`` before
``actions/setup-python``.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

DENOMINATOR_REL = "scripts/ci/dependency_change_denominator.json"

# pull_request / merge_group: only the branch side of the fork counts.
# push / schedule / workflow_dispatch: linear before..after two-dot.
_MERGE_BASE_EVENTS = frozenset({"pull_request", "merge_group"})

GIT_DIFF_TIMEOUT_SECONDS = 30
GIT_MERGE_BASE_TIMEOUT_SECONDS = 30

NOT_APPLICABLE_LINE = "not applicable: no dependency input changed"

_GLOB_CHARS = frozenset("*?[")


class MergeBaseError(RuntimeError):
    """Raised when ``git merge-base`` cannot resolve (shallow clone, missing refs)."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def denominator_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DENOMINATOR_REL


def load_denominator(path: Path | None = None) -> dict:
    target = path or denominator_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{target}: expected a JSON object")
    paths = data.get("paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
        raise ValueError(f"{target}: 'paths' must be a non-empty list of strings")
    version = data.get("version")
    if version is None or version == "":
        raise ValueError(f"{target}: missing 'version'")
    return data


def _is_glob(pattern: str) -> bool:
    return any(char in _GLOB_CHARS for char in pattern)


def path_in_denominator(path: str, patterns: Sequence[str]) -> bool:
    """Return True when a repo-relative POSIX path matches any denominator entry.

    Entries are exact paths, prefixes ending in ``/``, or fnmatch globs. A glob
    without a slash matches only root-level files so ``requirements*.txt``
    cannot reach into subdirectories; a glob with a slash matches the full path.
    """
    text = PurePosixPath(path).as_posix()
    for pattern in patterns:
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if text == prefix or text.startswith(pattern):
                return True
        elif _is_glob(pattern):
            if "/" in pattern:
                if fnmatch.fnmatchcase(text, pattern):
                    return True
            elif "/" not in text and fnmatch.fnmatchcase(text, pattern):
                return True
        elif text == pattern:
            return True
    return False


def matching_paths(changed: Iterable[str], patterns: Sequence[str]) -> list[str]:
    return sorted({path for path in changed if path_in_denominator(path, patterns)})


def range_mode_for_event(event_name: str) -> str:
    """Map ``github.event_name`` to diff range mode."""
    return "merge-base" if (event_name or "").strip() in _MERGE_BASE_EVENTS else "two-dot"


def two_dot_range(base: str, head: str = "HEAD") -> str:
    """Linear ``base..head`` tree/range diff for push events."""
    if ".." in base:
        return base
    return f"{base}..{head}"


def git_merge_base(base: str, head: str, *, cwd: Path | None = None) -> str:
    """Return the merge-base SHA, or raise ``MergeBaseError`` if unresolvable."""
    try:
        result = subprocess.run(
            ["git", "merge-base", base, head],
            check=True,
            capture_output=True,
            text=True,
            # Prefer process cwd (CI checkout / test fixture) over this file's tree.
            cwd=cwd or Path.cwd(),
            timeout=GIT_MERGE_BASE_TIMEOUT_SECONDS,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit={exc.returncode}"
        raise MergeBaseError(detail) from exc
    except subprocess.TimeoutExpired as exc:
        raise MergeBaseError(f"timed out after {exc.timeout}s") from exc
    mb = (result.stdout or "").strip()
    if not mb:
        raise MergeBaseError("empty merge-base")
    return mb


def resolve_git_range(
    base: str,
    head: str = "HEAD",
    *,
    mode: str = "merge-base",
    cwd: Path | None = None,
) -> str:
    """Build the ``git diff`` range for the event mode.

    ``merge-base``: ``$(git merge-base base head)..head`` (PR / merge_group).
    ``two-dot``: ``base..head`` (push linear history).
    """
    if mode == "two-dot":
        return two_dot_range(base, head)
    if "..." in base:
        return base
    mb = git_merge_base(base, head, cwd=cwd)
    return f"{mb}..{head}"


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def _parse_name_status_z(raw: bytes) -> list[str]:
    """Decode ``git diff --name-status -M -z`` bytes into changed paths.

    Renames and copies contribute both sides: renaming a dependency input away
    or renaming another file onto one must both run the audit.
    """
    tokens = [token for token in raw.split(b"\0") if token]
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        status = _decode(tokens[index])
        index += 1
        if status[:1] in {"R", "C"}:
            # Rename/copy records carry old and new path; either side counts.
            sides = tokens[index : index + 2]
            paths.extend(_decode(side) for side in sides)
            index += len(sides)
        elif index < len(tokens):
            paths.append(_decode(tokens[index]))
            index += 1
    return sorted(set(paths))


def changed_paths(git_range: str, *, cwd: Path | None = None) -> list[str]:
    # core.quotePath=false + -z: non-ASCII / quote / backslash names stay literal
    # (default quotePath C-quotes them and breaks denominator matching).
    # -M turns on rename detection so a renamed manifest is seen on both sides.
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--name-status",
            "-M",
            "-z",
            git_range,
        ],
        check=True,
        capture_output=True,
        cwd=cwd or Path.cwd(),
        timeout=GIT_DIFF_TIMEOUT_SECONDS,
    )
    return _parse_name_status_z(result.stdout)


def decision_line(
    *,
    decision: str,
    version: object,
    changed_count: int,
    matched_count: int,
    reason: str = "",
) -> str:
    line = (
        f"dependency-scope: decision={decision} denominator_version={version} "
        f"changed_files={changed_count} matched={matched_count}"
    )
    if reason:
        line = f"{line} reason={reason}"
    return line


def write_github_output(run: bool, path: Path | None = None) -> None:
    output = path
    if output is None:
        raw = os.environ.get("GITHUB_OUTPUT")
        if not raw:
            return
        output = Path(raw)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"run={'true' if run else 'false'}\n")


def write_step_summary(lines: Sequence[str], path: Path | None = None) -> None:
    summary = path
    if summary is None:
        raw = os.environ.get("GITHUB_STEP_SUMMARY")
        if not raw:
            return
        summary = Path(raw)
    with summary.open("a", encoding="utf-8") as handle:
        handle.write("## Dependency change scope (#9871)\n\n")
        for line in lines:
            handle.write(f"`{line}`\n")


def decide_from_changed(
    changed: Sequence[str],
    *,
    denominator: dict | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Return (run, decision lines, matched paths) for a changed-path set."""
    data = denominator or load_denominator()
    matched = matching_paths(changed, list(data["paths"]))
    run = bool(matched)
    line = decision_line(
        decision="run" if run else "not_applicable",
        version=data["version"],
        changed_count=len(changed),
        matched_count=len(matched),
    )
    lines = [line]
    if not run:
        lines.append(NOT_APPLICABLE_LINE)
    return run, lines, matched


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Decide whether a diff touches a declared dependency input and emit run=true|false.\n"
            "Use from the CI dependency-audit scope step before the full audit; not a general diff tool."
        ),
        epilog=(
            "Examples:\n"
            '  .venv/bin/python scripts/ci/dependency_change_scope.py --event pull_request --base "$BASE_SHA" --head "$HEAD_SHA"\n'
            '  .venv/bin/python scripts/ci/dependency_change_scope.py --event push --base "$PUSH_BEFORE"\n'
            "\n"
            "Outputs:\n"
            "  Prints a dependency-scope decision line on stdout; appends run=true|false to\n"
            "  $GITHUB_OUTPUT and a summary section to $GITHUB_STEP_SUMMARY when those are set.\n"
            "\n"
            "Exit codes:\n"
            "  Always 0. Any uncertainty (missing base SHA, unresolvable merge-base, git diff\n"
            "  failure or timeout) fails closed to run=true so the full audit still executes.\n"
            "\n"
            "Related:\n"
            "  Denominator: scripts/ci/dependency_change_denominator.json (#9871).\n"
            "  Consumer: the dependency-audit job in .github/workflows/ci.yml.\n"
            "  Sibling: scripts/ci/frontend_change_scope.py (#6917 / #6930) uses the same pattern."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base",
        default="",
        help=(
            "base SHA/ref to diff against (pull_request.base.sha || merge_group.base_sha || "
            "push before). Default: '' — an empty or all-zero base fails closed to run=true."
        ),
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help=(
            "head SHA/ref (pull_request.head.sha || merge_group.head_sha || github.sha); "
            "must be the event head, not the PR merge-commit checkout HEAD. Default: HEAD."
        ),
    )
    parser.add_argument(
        "--event",
        default="",
        help=(
            "github.event_name: pull_request|merge_group use merge-base range semantics, "
            "anything else uses linear two-dot. Default: '' (treated as push)."
        ),
    )
    parser.add_argument(
        "--denominator",
        type=Path,
        default=None,
        help=f"denominator JSON listing dependency inputs. Default: {DENOMINATOR_REL}.",
    )
    args = parser.parse_args(argv)

    denominator = load_denominator(args.denominator)
    base = (args.base or "").strip()
    head = (args.head or "HEAD").strip() or "HEAD"
    mode = range_mode_for_event(args.event)

    def fail_closed(reason: str, *, stderr: bool = False) -> int:
        # Fail closed on any uncertainty: the audit runs, never silently skipped.
        line = decision_line(
            decision="run",
            version=denominator["version"],
            changed_count=-1,
            matched_count=-1,
            reason=reason,
        )
        print(line, file=sys.stderr if stderr else sys.stdout)
        write_step_summary([line])
        write_github_output(True)
        return 0

    if not base or set(base) == {"0"}:
        return fail_closed("missing_base_sha")

    try:
        git_range = resolve_git_range(base, head, mode=mode)
        changed = changed_paths(git_range)
    except MergeBaseError:
        return fail_closed(f"merge_base_unresolvable mode={mode}", stderr=True)
    except subprocess.CalledProcessError as exc:
        return fail_closed(f"git_diff_failed exit={exc.returncode}", stderr=True)
    except subprocess.TimeoutExpired as exc:
        return fail_closed(f"git_diff_failed timeout={exc.timeout}s", stderr=True)

    run, lines, _matched = decide_from_changed(changed, denominator=denominator)
    for line in lines:
        print(line)
    write_step_summary(lines)
    write_github_output(run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
