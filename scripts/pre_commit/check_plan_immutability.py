#!/usr/bin/env python3
"""Block staged plan edits that skip versioning or add backup snapshots."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

PLAN_PATH_RE = re.compile(r"^curriculum/[^/]+/plans/.+\.yaml$")
AUTO_FIX_TAG = "[auto-fix-plan-vocab]"
METADATA_ONLY_FIELDS = {"module", "sequence", "slug", "level", "connects_to", "prerequisites"}
YAML_BACKUP_SUFFIXES = (".yaml.bak", ".yml.bak", ".yaml.orig", ".yml.orig")


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


def _is_yaml_backup_path(path: str) -> bool:
    """True when a staged path is a YAML backup artifact."""
    return path.endswith(YAML_BACKUP_SUFFIXES)


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


def _parse_plan(content: str, label: str) -> dict:
    """Parse a plan YAML document as a mapping."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"{label}: failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{label}: expected a YAML mapping at the document root")

    return data


def _version_parts(version: str) -> tuple[int, ...] | None:
    """Parse a dotted numeric version, returning None for custom schemes."""
    parts = version.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _is_version_increment(old_version: str, new_version: str) -> bool:
    """Return true when the new version is strictly newer than the old one."""
    old_parts = _version_parts(old_version)
    new_parts = _version_parts(new_version)
    if old_parts is None or new_parts is None:
        return new_version != old_version

    width = max(len(old_parts), len(new_parts))
    return old_parts + (0,) * (width - len(old_parts)) < new_parts + (0,) * (width - len(new_parts))


def _is_metadata_only_edit(old_content: str, new_content: str) -> bool:
    """Return true when only ordering/reference metadata changed.

    Curriculum order repairs need to update plan ids and dependency links
    without inventing backup files. Content-bearing plan edits still need the
    normal version bump and previous-content snapshot.
    """
    old_plan = _parse_plan(old_content, "old plan")
    new_plan = _parse_plan(new_content, "new plan")

    for key in METADATA_ONLY_FIELDS:
        old_plan.pop(key, None)
        new_plan.pop(key, None)

    return old_plan == new_plan


def _collect_errors(repo_root: Path) -> list[str]:
    """Validate staged plan edits against the immutability rule."""
    staged = _staged_files(repo_root)
    errors: list[str] = []

    for path in staged:
        if _is_yaml_backup_path(path):
            errors.append(
                f"{path}: YAML backup artifacts are no longer tracked; bump the plan version instead"
            )

    for plan_path in staged:
        if not _is_plan_path(plan_path):
            continue

        head_spec = f"HEAD:{plan_path}"
        if not _git_blob_exists(repo_root, head_spec):
            # New plans have no previous version to compare against.
            continue

        old_content = _read_git_blob(repo_root, head_spec)
        new_content = _read_git_blob(repo_root, f":{plan_path}")
        try:
            if _is_metadata_only_edit(old_content, new_content):
                continue
        except ValueError as exc:
            errors.append(str(exc))
            continue

        try:
            old_version = _parse_version(old_content, plan_path)
            new_version = _parse_version(new_content, plan_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if not _is_version_increment(old_version, new_version):
            errors.append(f"{plan_path}: version not incremented ({old_version} -> {new_version})")

    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Enforce version bumps and block backup artifacts for staged curriculum plan edits."
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
        "Plans are versioned - content changes need an incremented `version:` field.",
        file=sys.stderr,
    )
    print(
        "Do not stage `.yaml.bak` plan backups; previous versions live in git history "
        "(`git show HEAD:<path>`).",
        file=sys.stderr,
    )
    print(
        f"Exception: metadata-only fields {sorted(METADATA_ONLY_FIELDS)} may change without a version bump.",
        file=sys.stderr,
    )
    print(
        f"Exception: pipeline auto-fix commits use `{AUTO_FIX_TAG}` tag.",
        file=sys.stderr,
    )
    print(
        "See: agents_extensions/shared/rules/non-negotiable-rules.md §7",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
