#!/usr/bin/env python3
"""PreToolUse guard — auto-heals core.bare before git operations (#2842).

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`). If the command invokes `git`, it checks core.bare
and resets it to false if it has drifted to true. This prevents mid-session
git breakages from bubbling up to the agents.

Always exits 0 to allow the actual tool invocation to proceed.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from contextlib import suppress
from pathlib import Path


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _bash_command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _is_git_command(command: str) -> bool:
    """True if `git` is invoked as the primary command or in a sub-segment."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False

    return "git" in tokens


def _project_dir() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "common" / "repo_root.py").is_file():
            return candidate
    return None


# Git reads an empty value as false and any other non-false value as true.
_GIT_FALSE = frozenset({"", "false", "no", "off", "0"})


class _Undecidable(Exception):
    """The config cannot be judged without git itself."""


def _git_dirs(project_dir: Path) -> tuple[Path, Path]:
    """Return the git dir and the shared (common) git dir of ``project_dir``."""
    dot_git = project_dir / ".git"
    if dot_git.is_dir():
        return dot_git, dot_git
    if dot_git.is_file():
        text = dot_git.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            raise _Undecidable
        git_dir = Path(text.split(":", 1)[1].strip())
        if not git_dir.is_absolute():
            git_dir = project_dir / git_dir
        common = git_dir
        commondir = git_dir / "commondir"
        if commondir.is_file():
            pointer = Path(commondir.read_text(encoding="utf-8").strip())
            common = pointer if pointer.is_absolute() else git_dir / pointer
        return git_dir, common
    if (project_dir / "HEAD").is_file():
        return project_dir, project_dir
    raise _Undecidable


def _scan_config(text: str) -> dict[str, bool]:
    """Return the effective core.bare and extensions.worktreeConfig values set in one file."""
    found: dict[str, bool] = {}
    section = ""
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if line.startswith("["):
            header, _, line = line[1:].partition("]")
            words = header.split()
            section = words[0].lower() if words else ""
            if section in {"include", "includeif"}:
                raise _Undecidable
            line = line.strip()
        if not line:
            continue
        key, sep, value = line.partition("=")
        name = f"{section}.{key.strip().lower()}"
        if name in {"core.bare", "extensions.worktreeconfig"}:
            # The last assignment wins, as in git.
            found[name] = not sep or value.strip().strip('"').lower() not in _GIT_FALSE
    return found


def _may_be_bare(project_dir: Path) -> bool:
    """False only when the git config provably keeps core.bare off.

    Reading the files in-process spares a second interpreter on every git
    command. Anything this scan cannot decide (no readable config, include
    directives) defers to the authoritative checker.
    """
    try:
        git_dir, common = _git_dirs(project_dir)
        found = _scan_config((common / "config").read_text(encoding="utf-8"))
        per_worktree = git_dir / "config.worktree"
        # With worktreeConfig on, git reads config.worktree after the shared file.
        if found.get("extensions.worktreeconfig") and per_worktree.exists():
            found |= _scan_config(per_worktree.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, _Undecidable):
        return True
    return found.get("core.bare", False)


def main() -> int:
    payload = _read_payload()
    command = _bash_command(payload)

    if not command or not _is_git_command(command):
        return 0

    project_dir = _project_dir()
    if project_dir is None or not _may_be_bare(project_dir):
        return 0

    script = project_dir / "scripts" / "audit" / "check_core_bare.py"
    try:
        if str(project_dir) not in sys.path:
            sys.path.insert(0, str(project_dir))
        from scripts.common.repo_root import project_interpreter

        python_bin = project_interpreter()
    except Exception:
        return 0

    if script.exists() and python_bin.is_file():
        with suppress(OSError):
            subprocess.run(
                [str(python_bin), str(script), "--repo", str(project_dir), "--fix", "-q"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
