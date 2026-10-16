"""Find a per-run Cursor MCP config that a dispatch's commits or index would record (#10837).

``.cursor/mcp.json`` is tracked and holds URL servers only. A Cursor dispatch
rewrites it for the length of the run (a review attempt's stdio server, or an
author's write-safe ``sources`` launch, both naming host paths) and restores it
afterwards, so a commit made during the run could record the rewritten copy.
The dispatch worker runs :func:`recorded_config_problems` after restoring the
file and fails the run when it reports anything.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CURSOR_MCP_PATH = ".cursor/mcp.json"
ALLOWED_SERVER_KEYS = frozenset({"url", "type"})
_GIT_TIMEOUT_S = 30


def config_problems(blob: bytes) -> list[str]:
    """Why a recorded ``.cursor/mcp.json`` is refused; empty when every server is URL-only."""
    try:
        data = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["not valid UTF-8 JSON"]
    if not isinstance(data, dict) or set(data) != {"mcpServers"} or not isinstance(data["mcpServers"], dict):
        return ["the file must hold exactly one mcpServers object"]
    problems: list[str] = []
    for name, server in sorted(data["mcpServers"].items()):
        if not isinstance(server, dict):
            problems.append(f"server {name!r} is not an object")
        elif extra := sorted(set(server) - ALLOWED_SERVER_KEYS):
            problems.append(f"server {name!r} carries per-run keys {extra}")
        elif not isinstance(server.get("url"), str):
            problems.append(f"server {name!r} has no url")
    return problems


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=_GIT_TIMEOUT_S, check=False)


def head(repo: Path) -> str:
    """The commit the run starts from; raises when the checkout has none."""
    shown = _git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    if shown.returncode != 0:
        raise RuntimeError(f"cannot read HEAD in {repo} for the {CURSOR_MCP_PATH} guard")
    return shown.stdout.decode("utf-8").strip()


def recorded_config_problems(repo: Path, start: str) -> list[str]:
    """Problems in every version the run recorded: each commit since ``start`` that changes the file, then a staged change.

    A version without the file (a deletion) is not a leak. A git failure is reported as a problem,
    so the guard fails closed.
    """
    try:
        listed = _git(repo, "rev-list", f"{start}..HEAD", "--", CURSOR_MCP_PATH)
        if listed.returncode != 0:
            return [f"git rev-list {start[:12]}..HEAD failed"]
        versions = [(commit[:12], commit) for commit in listed.stdout.decode("utf-8").split()]
        staged = _git(repo, "diff", "--cached", "--name-only", "--", CURSOR_MCP_PATH)
        if staged.returncode != 0:
            return ["git diff --cached failed"]
        if staged.stdout.strip():
            versions.append(("index", ""))
        problems: list[str] = []
        for label, revision in versions:
            shown = _git(repo, "show", f"{revision}:{CURSOR_MCP_PATH}")
            if shown.returncode == 0:
                problems.extend(f"{CURSOR_MCP_PATH} at {label}: {problem}" for problem in config_problems(shown.stdout))
        return problems
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"{CURSOR_MCP_PATH} guard could not run git: {type(exc).__name__}"]
