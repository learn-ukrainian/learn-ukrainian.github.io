"""Open-PR freeze for new implementation dispatches.

While the public repository has ``threshold`` or more open pull requests, a
new write-capable dispatch that would open a new PR is refused. Work on an
existing PR stays allowed: ``--pr``, a ``--branch`` that already has an open
PR, or a reused ``--cwd`` or explicit ``--worktree`` path. ``--force-new``
alone does not prove branch continuation. Read-only work, reviews and other
repositories are unaffected. A ``--branch`` with no open PR counts as new.

``LU_OPEN_PR_FREEZE_THRESHOLD`` overrides the threshold (default 15; ``0``
disables the check). The count comes from the GitHub REST search API and is
cached briefly (``LU_OPEN_PR_FREEZE_CACHE_S``, default 60s). Every count and branch
list enters a decision through one strict validator (:func:`valid_count`,
:func:`parse_search_count`, :func:`parse_branch_pulls`): a live read, a cached read and an
injected reader alike. A cache record that fails it is a miss followed by a live read. When the
count or the branch's PR cannot be fetched (a rate refusal, a failed read, or empty or
malformed output) the decision is *unavailable*: ``refused`` is ``None`` (not ``False``) and
``warning`` names the reason. The caller owns what to do with an unknown admission; the PR
count is never guessed.
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
    """``refused`` is True/False when known and ``None`` when the lookup was unavailable."""

    refused: bool | None
    open_prs: int | None
    threshold: int
    warning: str | None = None

    @property
    def unavailable(self) -> bool:
        return self.refused is None

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


class InvalidPayload(ValueError):
    """A GitHub payload or cache record that is not exactly the shape the freeze decision needs."""


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def valid_count(value: Any) -> int:
    """The only way an open-PR count enters a decision: an exact int that is not bool and is >= 0.

    Live reads, cached reads and injected readers all pass through here; anything else raises.
    """
    if not _is_exact_int(value) or value < 0:
        raise InvalidPayload("open-PR count is not a non-negative int")
    return value


def parse_search_count(data: Any) -> int:
    """Open PR count from a REST search document, or raise :class:`InvalidPayload`.

    Search may time out server-side and return a partial count flagged incomplete; a count that
    is not known to be complete (``incomplete_results`` exactly ``False``) is not a count.
    """
    if not isinstance(data, dict):
        raise InvalidPayload("search response is not an object")
    count = valid_count(data.get("total_count"))
    if data.get("incomplete_results") is not False:
        raise InvalidPayload("search results incomplete or unflagged")
    return count


def parse_branch_pulls(data: Any) -> bool:
    """Whether the branch heads an open PR, from a ``pulls?per_page=1`` list, or raise.

    The request asks for one element, so the list holds at most one, and each element names a
    positive int PR number; an error object, a scalar or a ``0``/negative number is not a pull.
    """
    if not isinstance(data, list) or len(data) > 1:
        raise InvalidPayload("pulls response is not a list of at most one pull")
    for pull in data:
        number = pull.get("number") if isinstance(pull, dict) else None
        if not _is_exact_int(number) or number < 1:
            raise InvalidPayload("pull element has no positive int number")
    return bool(data)


def valid_exists(value: Any) -> bool:
    """An injected branch lookup must answer with a real bool."""
    if not isinstance(value, bool):
        raise InvalidPayload("branch lookup did not return a bool")
    return value


def fetch_open_pr_count(repo: str) -> int:
    """Open PR count for ``repo`` via the REST search endpoint."""
    return parse_search_count(_gh_get(f"search/issues?q=repo:{repo}+is:pr+is:open&per_page=1"))


def branch_has_open_pr(repo: str, branch: str) -> bool:
    """True when ``branch`` is the head of an open PR in ``repo``."""
    owner = repo.split("/", 1)[0]
    head = quote(f"{owner}:{branch}", safe="")
    return parse_branch_pulls(_gh_get(f"repos/{repo}/pulls?state=open&per_page=1&head={head}"))


def _fresh_cached_count(path: Path, ttl_s: float, now: Callable[[], float]) -> int | None:
    """The cached count when the record is a valid, unexpired ``{"count", "at"}``; else None (a miss)."""
    try:
        cached = json.loads(path.read_text())
        if not isinstance(cached, dict):
            return None
        at = cached["at"]
        if isinstance(at, bool) or not isinstance(at, (int, float)):
            return None
        age = now() - at
        if not 0 <= age < ttl_s:
            return None
        return valid_count(cached["count"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def cached_open_pr_count(
    repo: str,
    *,
    fetch: Callable[[str], int] = fetch_open_pr_count,
    cache_file: Path | None = None,
    ttl_s: float = DEFAULT_CACHE_S,
    now: Callable[[], float] = time.time,
) -> int:
    path = cache_file or _cache_path(repo)
    cached = _fresh_cached_count(path, ttl_s, now)
    if cached is not None:
        return cached
    count = valid_count(fetch(repo))
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
    except Exception:
        return FreezeDecision(
            refused=None,
            open_prs=None,
            threshold=threshold,
            warning="open-PR freeze check skipped: open_pr_count_unavailable",
        )
    if count < threshold:
        return FreezeDecision(refused=False, open_prs=count, threshold=threshold)
    if branch:
        try:
            if valid_exists(has_open_pr(repo, branch)):
                return FreezeDecision(refused=False, open_prs=count, threshold=threshold)
        except Exception:
            return FreezeDecision(
                refused=None,
                open_prs=count,
                threshold=threshold,
                warning="open-PR freeze check skipped: branch_pr_lookup_unavailable",
            )
    return FreezeDecision(refused=True, open_prs=count, threshold=threshold)
