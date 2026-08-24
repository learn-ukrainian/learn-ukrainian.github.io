"""Offline local collection for per-host project state (no network, no SSH)."""

from __future__ import annotations

import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.git_context import sanitized_git_env
from scripts.common.release_layout import is_release_root

_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_GIT_TIMEOUT_S = 4.0
_SERVICE_ORDER = ("sources", "api", "astro", "work")

ServiceStateFn = Callable[[str], str]
ListenerPidFn = Callable[[str], int | None]
ProcessCwdFn = Callable[[int], Path | None]


@dataclass(frozen=True)
class ServiceDefinition:
    name: str
    port: int
    match: str
    repo: str


SERVICE_DEFINITIONS: tuple[ServiceDefinition, ...] = (
    ServiceDefinition("sources", 8766, ".mcp/servers/sources/server.py", "learn-ukrainian"),
    ServiceDefinition("api", 8765, "scripts.api.main:app", "learn-ukrainian"),
    ServiceDefinition("astro", 4321, "astro", "learn-ukrainian"),
    ServiceDefinition("work", 8769, "-m work_projection", "sibling"),
)


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def resolve_primary_repo_root(start: Path) -> Path:
    """Return the human primary checkout (mirrors services.sh PUBLIC_PRIMARY_ROOT)."""
    start = start.resolve()
    common = _git(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common and Path(common).name == ".git":
        return Path(common).parent.resolve()
    return start


def resolve_work_private_root(primary_root: Path) -> Path:
    configured = os.environ.get("LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (primary_root.parent / "learn-ukrainian-infra-private").resolve()


def origin_main_age_s(repo_root: Path) -> float:
    fetch_head = repo_root / ".git" / "FETCH_HEAD"
    if not fetch_head.is_file():
        git_dir = _git(repo_root, "rev-parse", "--git-dir")
        if git_dir:
            fetch_head = Path(git_dir) / "FETCH_HEAD"
    if not fetch_head.is_file():
        return float("inf")
    return max(0.0, time.time() - fetch_head.stat().st_mtime)


def collect_primary_state(repo_root: Path) -> dict[str, Any] | None:
    head = _git(repo_root, "rev-parse", "HEAD")
    origin_main = _git(repo_root, "rev-parse", "refs/remotes/origin/main")
    if not origin_main:
        origin_main = _git(repo_root, "rev-parse", "origin/main")
    if not head or not origin_main or not _FULL_SHA_RE.fullmatch(head) or not _FULL_SHA_RE.fullmatch(origin_main):
        return None
    counts = _git(repo_root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    ahead, behind = 0, 0
    if counts:
        parts = counts.split()
        if len(parts) == 2:
            try:
                behind = int(parts[0])
                ahead = int(parts[1])
            except ValueError:
                ahead, behind = 0, 0
    status = _git(repo_root, "status", "--porcelain")
    dirty_count = 0
    if status is not None:
        dirty_count = sum(1 for line in status.splitlines() if line.strip())
    return {
        "head_sha": head,
        "origin_main_sha": origin_main,
        "origin_main_age_s": round(origin_main_age_s(repo_root), 2),
        "ahead": ahead,
        "behind": behind,
        "dirty_count": dirty_count,
    }


def collect_worktree_count(repo_root: Path) -> int:
    listing = _git(repo_root, "worktree", "list", "--porcelain")
    if not listing:
        return 0
    return sum(1 for line in listing.splitlines() if line.startswith("worktree "))


def classify_serving_root(cwd: Path) -> dict[str, Any]:
    resolved = cwd.resolve()
    if is_release_root(resolved):
        sha = resolved.name
        if _FULL_SHA_RE.fullmatch(sha):
            return {
                "serving_mode": "release",
                "serving_sha": sha,
                "checkout_sha": None,
            }
    head = _git(resolved, "rev-parse", "HEAD")
    if head and _FULL_SHA_RE.fullmatch(head):
        return {
            "serving_mode": "checkout",
            "serving_sha": None,
            "checkout_sha": head,
        }
    return {
        "serving_mode": "checkout",
        "serving_sha": None,
        "checkout_sha": None,
    }


def _default_listener_pid(port: int) -> int | None:
    lsof = os.environ.get("SVC_LSOF_BIN", "lsof")
    try:
        result = subprocess.run(
            [lsof, "-tiTCP:" + str(port), "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None


def _default_process_cwd(pid: int) -> Path | None:
    proc_cwd = Path(f"/proc/{pid}/cwd")
    if proc_cwd.exists():
        try:
            return proc_cwd.resolve()
        except OSError:
            return None
    lsof = os.environ.get("SVC_LSOF_BIN", "lsof")
    try:
        result = subprocess.run(
            [lsof, "-p", str(pid), "-d", "cwd", "-Fn"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in result.stdout.splitlines():
        if line.startswith("n") and len(line) > 1:
            candidate = Path(line[1:])
            if candidate.is_dir():
                return candidate.resolve()
    return None


def _cmdline_for_pid(pid: int) -> str:
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.is_file():
        try:
            raw = proc_cmdline.read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace").strip()
            if raw:
                return raw
        except OSError:
            pass
    try:
        result = subprocess.run(
            ["ps", "-o", "args=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def _default_service_state(name: str, definition: ServiceDefinition) -> str:
    pid = _default_listener_pid(definition.port)
    if pid is None:
        if name == "work":
            private = resolve_work_private_root(resolve_primary_repo_root(Path.cwd()))
            if not (private / ".git").exists() and not (private / ".git").is_file():
                return "unavailable"
            if not (private / ".venv" / "bin" / "python").is_file():
                return "unavailable"
            if not (private / "work_projection").is_dir():
                return "unavailable"
        return "stopped"
    cmdline = _cmdline_for_pid(pid)
    if definition.match not in cmdline:
        return "blocked"
    return "running"


def collect_service_row(
    definition: ServiceDefinition,
    *,
    service_state: ServiceStateFn | None = None,
    listener_pid: Callable[[str], int | None] | None = None,
    process_cwd: ProcessCwdFn | None = None,
) -> dict[str, Any]:
    state_fn = service_state or _default_service_state

    def _default_pid(name: str) -> int | None:
        for item in SERVICE_DEFINITIONS:
            if item.name == name:
                return _default_listener_pid(item.port)
        return None

    pid_fn = listener_pid or _default_pid
    cwd_fn = process_cwd or _default_process_cwd

    state = state_fn(definition.name)
    row: dict[str, Any] = {
        "name": definition.name,
        "state": state,
        "repo": definition.repo,
        "serving_mode": "checkout",
        "serving_sha": None,
        "checkout_sha": None,
    }
    if state != "running":
        return row

    pid = pid_fn(definition.name)
    if pid is None:
        return row
    cwd = cwd_fn(pid)
    if cwd is None:
        return row
    classified = classify_serving_root(cwd)
    row.update(classified)
    return row


def collect_local_document(
    host_id: str,
    *,
    repo_root: Path | None = None,
    service_state: ServiceStateFn | None = None,
    listener_pid: Callable[[str], int | None] | None = None,
    process_cwd: ProcessCwdFn | None = None,
) -> dict[str, Any] | None:
    start = (repo_root or Path.cwd()).resolve()
    primary_root = resolve_primary_repo_root(start)
    primary = collect_primary_state(primary_root)
    if primary is None:
        return None

    services = [
        collect_service_row(
            definition,
            service_state=service_state,
            listener_pid=listener_pid,
            process_cwd=process_cwd,
        )
        for definition in SERVICE_DEFINITIONS
    ]
    return {
        "host_id": host_id,
        "primary": primary,
        "worktrees": {"count": collect_worktree_count(primary_root)},
        "services": services,
        "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
