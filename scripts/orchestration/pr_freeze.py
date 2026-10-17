"""Open-PR freeze for new implementation dispatches.

While the public repository has ``threshold`` or more open pull requests
other than those by ``app/dependabot``, a new write-capable dispatch that
would open a new PR is refused. Work on an existing PR stays allowed:
``--pr``, a ``--branch`` that already has an open PR, or a reused ``--cwd``
or explicit ``--worktree`` path. ``--force-new`` alone does not prove branch
continuation. Read-only work, reviews and other repositories are unaffected.
A ``--branch`` with no open PR counts as new.

The decision path runs one GitHub search::

    repo:<repo> is:pr is:open -author:app/dependabot

That search ``total_count`` is the counted number compared with the threshold.
There is no second search, no subtraction, and no per-item login check. The
unfiltered open total is not fetched. The length of the returned page is not
a count. ``FreezeDecision.open_prs`` is that counted number.

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
# The only author the decision search excludes. The qualifier is
# ``-author:app/dependabot`` on the single open-PR search.
EXCLUDED_AUTHOR_LOGIN = "app/dependabot"


@dataclass(frozen=True)
class OpenPrCounts:
    """Counted open pull requests from the one decision search.

    ``counted`` is the search ``total_count`` the freeze compares with the
    threshold. ``total`` carries that same number: the unfiltered open total
    is not fetched.
    """

    total: int
    counted: int


@dataclass(frozen=True)
class FreezeDecision:
    refused: bool
    open_prs: int | None
    threshold: int
    warning: str | None = None
    total_open: int | None = None

    def refusal_line(self, repo: str) -> str:
        total = self.total_open if self.total_open is not None else self.open_prs
        counted = self.open_prs
        return (
            f"dispatch refused: {total} open PRs in {repo} ({counted} counted, freeze at {self.threshold}). "
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


def _require_total_count(data: Any) -> int:
    """Search ``total_count``. Never the length of the returned page."""
    if not isinstance(data, dict):
        raise RuntimeError("no total_count in response")
    if data.get("incomplete_results") is True:
        raise RuntimeError("incomplete open-pr search")
    count = data.get("total_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise RuntimeError("no total_count in response")
    return count


def _open_pr_search_endpoint(repo: str) -> str:
    """The one decision-path search for ``repo``.

    The query is ``repo:<repo> is:pr is:open -author:app/dependabot``.
    """
    query = f"repo:{repo} is:pr is:open -author:{EXCLUDED_AUTHOR_LOGIN}"
    return f"search/issues?q={quote(query, safe='')}&per_page=1"


def fetch_open_pr_count(repo: str) -> OpenPrCounts:
    """Counted open pull requests for ``repo``.

    Issues one search and returns its ``total_count``. That number is what
    the freeze compares with the threshold. Items on the page are not
    inspected, and the unfiltered open total is not fetched.
    """
    counted = _require_total_count(_gh_get(_open_pr_search_endpoint(repo)))
    return OpenPrCounts(total=counted, counted=counted)


def _as_counts(value: Any) -> OpenPrCounts:
    """Normalize a fetch result. An int is that search's counted total."""
    if isinstance(value, OpenPrCounts):
        if value.total < 0 or value.counted < 0 or value.counted > value.total:
            raise RuntimeError("invalid open-pr counts")
        return value
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("unexpected open-pr count")
    return OpenPrCounts(total=value, counted=value)


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
    fetch: Callable[[str], int | OpenPrCounts] = fetch_open_pr_count,
    cache_file: Path | None = None,
    ttl_s: float = DEFAULT_CACHE_S,
    now: Callable[[], float] = time.time,
) -> OpenPrCounts:
    path = cache_file or _cache_path(repo)
    try:
        cached = json.loads(path.read_text())
        counted = cached.get("count")
        total = cached.get("total")
        if (
            isinstance(counted, int)
            and not isinstance(counted, bool)
            and isinstance(total, int)
            and not isinstance(total, bool)
            and 0 <= counted <= total
            and now() - float(cached["at"]) < ttl_s
        ):
            return OpenPrCounts(total=total, counted=counted)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    counts = _as_counts(fetch(repo))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps({"count": counts.counted, "total": counts.total, "at": now()}))
        tmp.replace(path)
    except OSError:
        pass
    return counts


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


def _decision(
    *,
    refused: bool,
    counts: OpenPrCounts,
    threshold: int,
    warning: str | None = None,
) -> FreezeDecision:
    return FreezeDecision(
        refused=refused,
        open_prs=counts.counted,
        total_open=counts.total,
        threshold=threshold,
        warning=warning,
    )


def evaluate(
    repo: str,
    *,
    branch: str | None = None,
    environ: Mapping[str, str] | None = None,
    fetch: Callable[[str], int | OpenPrCounts] | None = None,
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
        counts = cached_open_pr_count(repo, fetch=fetch, cache_file=cache_file, ttl_s=_cache_s(env))
    except Exception:
        return FreezeDecision(
            refused=False,
            open_prs=None,
            threshold=threshold,
            warning="open-PR freeze check skipped: open_pr_count_unavailable",
        )
    if counts.counted < threshold:
        return _decision(refused=False, counts=counts, threshold=threshold)
    if branch:
        try:
            if has_open_pr(repo, branch):
                return _decision(refused=False, counts=counts, threshold=threshold)
        except Exception:
            return _decision(
                refused=False,
                counts=counts,
                threshold=threshold,
                warning="open-PR freeze check skipped: branch_pr_lookup_unavailable",
            )
    return _decision(refused=True, counts=counts, threshold=threshold)
