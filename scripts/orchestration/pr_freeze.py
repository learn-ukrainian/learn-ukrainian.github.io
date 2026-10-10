"""Open-PR freeze for new implementation dispatches.

While the public repository has ``threshold`` or more open pull requests, a
new write-capable dispatch that would open a new PR is refused. Work on an
existing PR stays allowed: ``--pr``, a ``--branch`` that already has an open
PR, a reused ``--cwd`` or explicit ``--worktree`` path, and ``--force-new``
continuations of an existing task. Read-only work, reviews and other
repositories are unaffected. A ``--branch`` with no open PR counts as new.

``LU_OPEN_PR_FREEZE_THRESHOLD`` overrides the threshold (default 15; ``0``
disables the check). The count comes from the GitHub REST search API and is
cached briefly (``LU_OPEN_PR_FREEZE_CACHE_S``, default 60s). When the count or
the branch's PR cannot be fetched the check fails open with a warning.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

DEFAULT_THRESHOLD = 15
DEFAULT_CACHE_S = 60.0
THRESHOLD_ENV = "LU_OPEN_PR_FREEZE_THRESHOLD"
CACHE_ENV = "LU_OPEN_PR_FREEZE_CACHE_S"
WRITE_MODES = frozenset({"workspace-write", "danger"})


@dataclass(frozen=True)
class FreezeDecision:
    refused: bool
    open_prs: int | None
    threshold: int
    warning: str | None = None

    def refusal_line(self, repo: str) -> str:
        return (
            f"dispatch refused: {self.open_prs} open PRs in {repo} (freeze at {self.threshold}). "
            "New implementation jobs that open a PR are paused. Land your own open PRs first "
            "(fix, get CF, queue them); pushes and fixes to existing PRs are still allowed."
        )


def threshold_from_env(environ: Mapping[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    raw = (env.get(THRESHOLD_ENV) or "").strip()
    if not raw:
        return DEFAULT_THRESHOLD
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_THRESHOLD
    return max(value, 0)


def _cache_s(environ: Mapping[str, str]) -> float:
    try:
        return max(float(environ.get(CACHE_ENV, DEFAULT_CACHE_S)), 0.0)
    except ValueError:
        return DEFAULT_CACHE_S


def _cache_path(repo: str) -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "learn-ukrainian" / f"open-pr-count-{repo.replace('/', '__')}.json"


def _gh_get(endpoint: str) -> Any:
    try:
        from scripts.common import github_client
    except ImportError:  # pragma: no cover - flat script path
        from common import github_client  # type: ignore

    proc = github_client.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "").strip()[:200] or f"gh api rc {proc.returncode}")
    return json.loads(proc.stdout)


def fetch_open_pr_count(repo: str) -> int:
    """Open PR count for ``repo`` via the REST search endpoint."""
    data = _gh_get(f"search/issues?q=repo:{repo}+is:pr+is:open&per_page=1")
    count = data.get("total_count") if isinstance(data, dict) else None
    if not isinstance(count, int):
        raise RuntimeError("no total_count in response")
    return count


def branch_has_open_pr(repo: str, branch: str) -> bool:
    """True when ``branch`` is the head of an open PR in ``repo``."""
    owner = repo.split("/", 1)[0]
    head = quote(f"{owner}:{branch}", safe="")
    data = _gh_get(f"repos/{repo}/pulls?state=open&per_page=1&head={head}")
    if not isinstance(data, list):
        raise RuntimeError("unexpected pulls response")
    return bool(data)


def cached_open_pr_count(
    repo: str,
    *,
    fetch: Callable[[str], int] = fetch_open_pr_count,
    cache_file: Path | None = None,
    ttl_s: float = DEFAULT_CACHE_S,
    now: Callable[[], float] = time.time,
) -> int:
    path = cache_file or _cache_path(repo)
    try:
        cached = json.loads(path.read_text())
        if isinstance(cached.get("count"), int) and now() - float(cached["at"]) < ttl_s:
            return int(cached["count"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    count = fetch(repo)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps({"count": count, "at": now()}))
        tmp.replace(path)
    except OSError:
        pass
    return count


def opens_new_pr(
    *,
    mode: str,
    repo_role: str,
    pr: int | None,
    cwd: str | None,
    review: bool,
    reused_worktree: bool = False,
    continuation: bool = False,
) -> bool:
    """True for a write-capable public dispatch that may open a new PR.

    ``--branch`` is not decided here: :func:`evaluate` exempts it only when the
    branch already has an open PR.
    """
    return (
        mode in WRITE_MODES
        and repo_role == "public-monorepo"
        and pr is None
        and not cwd
        and not review
        and not reused_worktree
        and not continuation
    )


def evaluate(
    repo: str,
    *,
    branch: str | None = None,
    environ: Mapping[str, str] | None = None,
    fetch: Callable[[str], int] | None = None,
    has_open_pr: Callable[[str, str], bool] | None = None,
    cache_file: Path | None = None,
) -> FreezeDecision:
    env = os.environ if environ is None else environ
    threshold = threshold_from_env(env)
    if threshold == 0:
        return FreezeDecision(refused=False, open_prs=None, threshold=0)
    fetch = fetch or fetch_open_pr_count
    has_open_pr = has_open_pr or branch_has_open_pr
    try:
        count = cached_open_pr_count(repo, fetch=fetch, cache_file=cache_file, ttl_s=_cache_s(env))
    except Exception as exc:
        return FreezeDecision(
            refused=False,
            open_prs=None,
            threshold=threshold,
            warning=f"open-PR freeze check skipped: could not count open PRs ({exc})",
        )
    if count < threshold:
        return FreezeDecision(refused=False, open_prs=count, threshold=threshold)
    if branch:
        try:
            if has_open_pr(repo, branch):
                return FreezeDecision(refused=False, open_prs=count, threshold=threshold)
        except Exception as exc:
            return FreezeDecision(
                refused=False,
                open_prs=count,
                threshold=threshold,
                warning=f"open-PR freeze check skipped: could not look up the PR for {branch} ({exc})",
            )
    return FreezeDecision(refused=True, open_prs=count, threshold=threshold)
