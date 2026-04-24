#!/usr/bin/env python3
"""Block staged plan edits that skip versioning or backup snapshots."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

PLAN_PATH_RE = re.compile(r"^curriculum/[^/]+/plans/.+\.yaml$")
AUTO_FIX_TAG = "[auto-fix-plan-vocab]"


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git command from the target repository."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def _repo_root() -> Path:
    """Resolve the repository root from the current working directory."""
    result = _run_git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip())


def _staged_files(repo_root: Path) -> list[str]:
    """Return staged file paths relative to the repository root."""
    result = _run_git(repo_root, "diff", "--cached", "--name-only", "--diff-filter=AM")
    return [line for line in result.stdout.splitlines() if line]


def _is_plan_path(path: str) -> bool:
    """True when the staged path is a curriculum plan YAML file."""
    return bool(PLAN_PATH_RE.match(path))


def _git_blob_exists(repo_root: Path, spec: str) -> bool:
    """Return whether a git object spec resolves successfully."""
    result = subprocess.run(
        ["git", "cat-file", "-e", spec],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _read_git_blob(repo_root: Path, spec: str) -> str:
    """Read text content from a git object spec."""
    result = _run_git(repo_root, "show", spec)
    return result.stdout


def _read_commit_message(repo_root: Path, commit_msg_file: str | None) -> str:
    """Read the in-flight commit message when it is available."""
    if commit_msg_file:
        path = Path(commit_msg_file)
    else:
        result = _run_git(repo_root, "rev-parse", "--git-path", "COMMIT_EDITMSG")
        path = repo_root / result.stdout.strip()

    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_version(content: str, label: str) -> str:
    """Extract the plan version from YAML content."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"{label}: failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{label}: expected a YAML mapping at the document root")

    version = data.get("version")
    if version is None or str(version).strip() == "":
        raise ValueError(f"{label}: missing version field")

    return str(version).strip()


def _collect_errors(repo_root: Path) -> list[str]:
    """Validate staged plan edits against the immutability rule."""
    staged = _staged_files(repo_root)
    staged_set = set(staged)
    errors: list[str] = []

    for plan_path in staged:
        if not _is_plan_path(plan_path):
            continue

        head_spec = f"HEAD:{plan_path}"
        if not _git_blob_exists(repo_root, head_spec):
            # New plans have no previous version to compare against.
            continue

        try:
            old_version = _parse_version(_read_git_blob(repo_root, head_spec), plan_path)
            new_version = _parse_version(_read_git_blob(repo_root, f":{plan_path}"), plan_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if old_version == new_version:
            errors.append(f"{plan_path}: version not bumped (still {old_version})")

        bak_path = f"{plan_path}.bak"
        if bak_path not in staged_set:
            errors.append(f"{plan_path}: missing {bak_path} backup in same commit")
            continue

        try:
            bak_version = _parse_version(_read_git_blob(repo_root, f":{bak_path}"), bak_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if bak_version != old_version:
            errors.append(
                f"{bak_path}: should contain old version {old_version}, found {bak_version}"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Enforce version bumps and backups for staged curriculum plan edits."
    )
    parser.add_argument(
        "commit_msg_file",
        nargs="?",
        help="Path to COMMIT_EDITMSG from the commit-msg hook stage.",
    )
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    if AUTO_FIX_TAG in _read_commit_message(repo_root, args.commit_msg_file):
        return 0

    errors = _collect_errors(repo_root)
    if not errors:
        return 0

    print(
        "Plans are versioned - any change needs a bumped version and a `.bak` of the previous.",
        file=sys.stderr,
    )
    print(
        f"Exception: pipeline auto-fix commits use `{AUTO_FIX_TAG}` tag.",
        file=sys.stderr,
    )
    print(
        "See: claude_extensions/rules/non-negotiable-rules.md §7",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
