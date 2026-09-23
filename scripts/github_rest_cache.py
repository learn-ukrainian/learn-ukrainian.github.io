"""Shared GitHub REST cache for Monitor and Work pollers.

List and per-PR reads go through ``gh api`` with ``If-None-Match``. A 304
returns the cached body and does not replace it. Failures are not stored.
Both ``scripts.api.main`` and ``scripts.work.sources_public`` use
:func:`shared_cache` so one process keeps a single ETag map.

Projected dicts keep only the fields those consumers read. The shapes match
the ``gh --json`` objects the collectors already understood: ``createdAt``,
``isDraft``, ``headRefOid``, ``statusCheckRollup``, and ``reviewDecision``.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

# (path, request headers, timeout seconds) -> (status, response headers, body)
RestTransport = Callable[[str, dict[str, str], float], tuple[int, dict[str, str], bytes]]

_MAX_PAGES = 15
_CHECK_RUN_PAGES = 5
_DETAIL_WORKERS = 8


class GitHubRestError(RuntimeError):
    """A GitHub REST read failed. Never written into the ETag cache."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubRestTimeout(Exception):
    """The REST deadline elapsed. Not a :class:`TimeoutError` (orient maps those separately)."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(f"GitHub REST timed out after {timeout}s")


@dataclass
class RestResult:
    status: int
    body: Any
    etag: str | None
    link_next: str | None
    not_modified: bool


@dataclass
class _CacheEntry:
    etag: str
    body: Any
    link_next: str | None


def _link_next(header: str | None) -> str | None:
    if not header:
        return None
    for part in header.split(","):
        if 'rel="next"' not in part and "rel=next" not in part:
            continue
        start = part.find("<")
        end = part.find(">", start + 1)
        if start >= 0 and end > start:
            return part[start + 1 : end]
    return None


def _parse_http_message(raw: bytes) -> tuple[int, dict[str, str], bytes]:
    separator = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n"
    head, _, body = raw.partition(separator)
    lines = head.decode("utf-8", errors="replace").splitlines()
    if not lines or not lines[0].startswith("HTTP/"):
        raise GitHubRestError("gh api returned no HTTP status line")
    status_parts = lines[0].split()
    if len(status_parts) < 2 or not status_parts[1].isdigit():
        raise GitHubRestError(f"gh api returned an unreadable status line: {lines[0]}")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        key, sep, value = line.partition(":")
        if sep:
            headers[key.strip().lower()] = value.strip()
    return int(status_parts[1]), headers, body


def _gh_api_transport(path: str, headers: dict[str, str], timeout: float) -> tuple[int, dict[str, str], bytes]:
    """GET ``path`` via ``gh api -i``. HTTP 304 is a result, not a failure."""
    cmd = ["gh", "api", "--method", "GET", "-i", path]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise GitHubRestTimeout(timeout) from exc
    except (FileNotFoundError, OSError) as exc:
        raise GitHubRestError(f"{type(exc).__name__}: {exc}") from exc

    raw = proc.stdout or b""
    if not raw.startswith(b"HTTP/"):
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise GitHubRestError(err or f"gh api failed (exit {proc.returncode})")
    status, resp_headers, body = _parse_http_message(raw)
    if status in {200, 304, 404}:
        return status, resp_headers, body
    err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
    raise GitHubRestError(err or f"GitHub REST {status} for {path}", status=status)


class GitHubRestCache:
    """Process-local ETag cache. Errors leave the previous entry in place."""

    def __init__(self, transport: RestTransport | None = None) -> None:
        self._transport = transport or _gh_api_transport
        self._entries: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def cached_body(self, path: str) -> Any:
        with self._lock:
            entry = self._entries.get(path)
            return None if entry is None else entry.body

    def get_json(self, path: str, *, timeout: float) -> RestResult:
        """Conditional GET.

        200 replaces the cache. 304 returns the cached body and does not replace
        it. 404 is returned and not cached. Any other failure raises and is not
        cached.
        """
        if timeout <= 0:
            raise GitHubRestTimeout(timeout)
        with self._lock:
            current = self._entries.get(path)
            etag = None if current is None else current.etag
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag

        status, resp_headers, body = self._transport(path, headers, timeout)
        resp_headers = {key.lower(): value for key, value in resp_headers.items()}
        new_etag = resp_headers.get("etag")
        link_next = _link_next(resp_headers.get("link"))

        if status == 304:
            with self._lock:
                cached = self._entries.get(path)
                if cached is None:
                    raise GitHubRestError("304 without a cached body", status=304)
                # A rotated validator must be replayed next time; the body stays.
                if new_etag and new_etag != cached.etag:
                    cached = _CacheEntry(etag=new_etag, body=cached.body, link_next=cached.link_next)
                    self._entries[path] = cached
                return RestResult(
                    status=304,
                    body=cached.body,
                    etag=cached.etag,
                    link_next=cached.link_next,
                    not_modified=True,
                )

        if status == 404:
            return RestResult(status=404, body=None, etag=None, link_next=None, not_modified=False)

        if status != 200:
            raise GitHubRestError(f"GitHub REST {status} for {path}", status=status)

        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubRestError(f"invalid GitHub JSON: {exc}") from exc

        if new_etag:
            with self._lock:
                self._entries[path] = _CacheEntry(etag=new_etag, body=parsed, link_next=link_next)
        return RestResult(
            status=200,
            body=parsed,
            etag=new_etag,
            link_next=link_next,
            not_modified=False,
        )


_SHARED = GitHubRestCache()


def shared_cache() -> GitHubRestCache:
    """The one cache Monitor orient and the Work projection share."""
    return _SHARED


def _time_left(deadline: float, timeout: float) -> float:
    left = deadline - time.monotonic()
    if left <= 0:
        raise GitHubRestTimeout(timeout)
    return left


def _iter_list_pages(cache: GitHubRestCache, path: str, *, deadline: float, timeout: float):
    url: str | None = path
    for _ in range(_MAX_PAGES):
        if not url:
            return
        result = cache.get_json(url, timeout=_time_left(deadline, timeout))
        if result.status == 404:
            raise GitHubRestError(f"GitHub REST 404 for {url}", status=404)
        if not isinstance(result.body, list):
            raise GitHubRestError(f"expected a JSON list from {url}")
        yield result.body
        url = result.link_next


def _names(raw: Any, key: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return out
    for entry in raw:
        if isinstance(entry, dict) and entry.get(key):
            out.append({key: str(entry[key])})
    return out


def project_issue(raw: dict[str, Any]) -> dict[str, Any]:
    """REST issue → the fields Work and orient actually read."""
    state = raw.get("state")
    return {
        "number": raw.get("number"),
        "title": raw.get("title"),
        "labels": _names(raw.get("labels"), "name"),
        "body": raw.get("body") if isinstance(raw.get("body"), str) else None,
        "createdAt": raw.get("created_at"),
        "updatedAt": raw.get("updated_at"),
        "assignees": _names(raw.get("assignees"), "login"),
        "url": raw.get("html_url"),
        "state": str(state).upper() if isinstance(state, str) and state else None,
    }


def derive_review_decision(reviews: list[dict[str, Any]], requested_reviewers: Any) -> str:
    """REST has no ``reviewDecision``. Latest review per author, then pending requests.

    ``CHANGES_REQUESTED`` wins. An outstanding requested reviewer keeps the PR at
    ``REVIEW_REQUIRED`` even when someone else has approved. Otherwise one
    ``APPROVED`` review is ``APPROVED``.
    """
    latest: dict[str, str] = {}
    for review in reviews:
        user = review.get("user")
        login = user.get("login") if isinstance(user, dict) else None
        state = str(review.get("state") or "").upper()
        if isinstance(login, str) and login and state:
            latest[login] = state
    deciding = {state for state in latest.values() if state in {"APPROVED", "CHANGES_REQUESTED"}}
    if "CHANGES_REQUESTED" in deciding:
        return "CHANGES_REQUESTED"
    pending = False
    if isinstance(requested_reviewers, list):
        pending = any(isinstance(entry, dict) and entry.get("login") for entry in requested_reviewers)
    if pending:
        return "REVIEW_REQUIRED"
    if "APPROVED" in deciding:
        return "APPROVED"
    return "REVIEW_REQUIRED"


def _project_check_run(run: dict[str, Any]) -> dict[str, Any]:
    conclusion = run.get("conclusion")
    return {
        "name": run.get("name"),
        "status": str(run.get("status") or "").upper(),
        "conclusion": str(conclusion).upper() if isinstance(conclusion, str) and conclusion else None,
        "startedAt": run.get("started_at"),
        "completedAt": run.get("completed_at"),
    }


def _project_status(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "context": status.get("context"),
        "state": str(status.get("state") or "").upper(),
        "createdAt": status.get("created_at"),
        "updatedAt": status.get("updated_at"),
    }


def _project_review(review: dict[str, Any]) -> dict[str, Any]:
    commit_id = review.get("commit_id")
    return {
        "state": str(review.get("state") or "").upper(),
        "commit": {"oid": commit_id} if isinstance(commit_id, str) and commit_id else None,
    }


def _project_comment(comment: dict[str, Any]) -> dict[str, Any]:
    return {
        "body": comment.get("body") if isinstance(comment.get("body"), str) else None,
        "createdAt": comment.get("created_at"),
    }


def project_pull_request(
    raw: dict[str, Any],
    *,
    pull: dict[str, Any] | None,
    check_runs: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    comments: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """REST pull + conditional detail → the fields Work and idle-PR orient read."""
    detail = pull if isinstance(pull, dict) else {}
    head = raw.get("head") if isinstance(raw.get("head"), dict) else {}
    state = raw.get("state")
    mergeable = detail.get("mergeable_state")
    requested = detail.get("requested_reviewers")
    if requested is None:
        requested = raw.get("requested_reviewers")
    rollup: list[dict[str, Any]] = [_project_check_run(run) for run in check_runs if isinstance(run, dict)]
    rollup.extend(_project_status(status) for status in statuses if isinstance(status, dict))
    projected_reviews = [_project_review(review) for review in reviews if isinstance(review, dict)]
    projected_comments = [_project_comment(comment) for comment in comments or [] if isinstance(comment, dict)]
    return {
        "number": raw.get("number"),
        "title": raw.get("title"),
        "state": str(state).upper() if isinstance(state, str) and state else None,
        "isDraft": bool(raw.get("draft")),
        "headRefName": head.get("ref"),
        "headRefOid": head.get("sha"),
        "updatedAt": raw.get("updated_at"),
        "createdAt": raw.get("created_at"),
        "reviewDecision": derive_review_decision(
            [review for review in reviews if isinstance(review, dict)],
            requested,
        ),
        "reviews": projected_reviews,
        "comments": projected_comments,
        "statusCheckRollup": rollup,
        "mergeStateStatus": str(mergeable).upper() if isinstance(mergeable, str) and mergeable else None,
        "labels": _names(raw.get("labels"), "name"),
        "assignees": _names(raw.get("assignees"), "login"),
        "url": raw.get("html_url"),
    }


def list_open_issues(
    repo: str,
    *,
    limit: int,
    timeout: float,
    cache: GitHubRestCache | None = None,
) -> list[dict[str, Any]]:
    """Open issues only (the REST issues list also returns pull requests)."""
    store = cache or shared_cache()
    if limit <= 0:
        return []
    path = f"repos/{repo}/issues?state=open&per_page=100&sort=created&direction=desc"
    deadline = time.monotonic() + timeout
    projected: list[dict[str, Any]] = []
    for page in _iter_list_pages(store, path, deadline=deadline, timeout=timeout):
        for item in page:
            if not isinstance(item, dict) or "pull_request" in item:
                continue
            projected.append(project_issue(item))
            if len(projected) >= limit:
                return projected
    return projected


def _list_body(
    cache: GitHubRestCache,
    path: str,
    *,
    deadline: float,
    timeout: float,
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in _iter_list_pages(cache, path, deadline=deadline, timeout=timeout):
        for item in page:
            if isinstance(item, dict):
                rows.append(item)
            if len(rows) >= limit:
                return rows
    return rows


def _check_runs(
    cache: GitHubRestCache,
    repo: str,
    sha: str,
    *,
    deadline: float,
    timeout: float,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for page in range(1, _CHECK_RUN_PAGES + 1):
        result = cache.get_json(
            f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page={page}",
            timeout=_time_left(deadline, timeout),
        )
        if result.status == 404 or not isinstance(result.body, dict):
            raise GitHubRestError(f"check runs unavailable for {sha}", status=result.status)
        chunk = result.body.get("check_runs") or []
        if not isinstance(chunk, list):
            raise GitHubRestError(f"check runs payload was not a list for {sha}")
        runs.extend(item for item in chunk if isinstance(item, dict))
        total = result.body.get("total_count")
        if not isinstance(total, int) or len(runs) >= total or not chunk:
            break
    return runs


def _detail_one(
    cache: GitHubRestCache,
    repo: str,
    raw: dict[str, Any],
    *,
    deadline: float,
    timeout: float,
    include_comments: bool,
) -> dict[str, Any]:
    number = raw.get("number")
    head = raw.get("head") if isinstance(raw.get("head"), dict) else {}
    sha = head.get("sha")
    if not isinstance(number, int) or isinstance(number, bool) or not isinstance(sha, str) or not sha:
        raise GitHubRestError("open pull request is missing number or head sha")
    pull = cache.get_json(f"repos/{repo}/pulls/{number}", timeout=_time_left(deadline, timeout))
    if pull.status not in {200, 304} or not isinstance(pull.body, dict):
        raise GitHubRestError(f"pull request {number} detail unavailable", status=pull.status)
    runs = _check_runs(cache, repo, sha, deadline=deadline, timeout=timeout)
    status = cache.get_json(f"repos/{repo}/commits/{sha}/status", timeout=_time_left(deadline, timeout))
    if status.status not in {200, 304} or not isinstance(status.body, dict):
        raise GitHubRestError(f"commit status unavailable for {sha}", status=status.status)
    statuses = status.body.get("statuses") or []
    if not isinstance(statuses, list):
        raise GitHubRestError(f"commit status payload was not a list for {sha}")
    reviews = _list_body(
        cache,
        f"repos/{repo}/pulls/{number}/reviews?per_page=100",
        deadline=deadline,
        timeout=timeout,
        limit=100,
    )
    comments: list[dict[str, Any]] | None = None
    if include_comments:
        comments = _list_body(
            cache,
            f"repos/{repo}/issues/{number}/comments?per_page=100",
            deadline=deadline,
            timeout=timeout,
            limit=100,
        )
    return project_pull_request(
        raw,
        pull=pull.body,
        check_runs=runs,
        statuses=[item for item in statuses if isinstance(item, dict)],
        reviews=reviews,
        comments=comments,
    )


def list_open_prs(
    repo: str,
    *,
    limit: int,
    timeout: float,
    cache: GitHubRestCache | None = None,
    include_comments: bool = False,
) -> list[dict[str, Any]]:
    """Open pulls. Check runs, reviews, and mergeability are one conditional read per open PR."""
    store = cache or shared_cache()
    if limit <= 0:
        return []
    path = f"repos/{repo}/pulls?state=open&per_page=100&sort=created&direction=desc"
    deadline = time.monotonic() + timeout
    raw = _list_body(store, path, deadline=deadline, timeout=timeout, limit=limit)
    if not raw:
        return []
    workers = max(1, min(_DETAIL_WORKERS, len(raw)))

    def _one(item: dict[str, Any]) -> dict[str, Any]:
        return _detail_one(
            store,
            repo,
            item,
            deadline=deadline,
            timeout=timeout,
            include_comments=include_comments,
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_one, raw))


def issue_states(
    repo: str,
    numbers: list[int],
    *,
    timeout: float,
    cache: GitHubRestCache | None = None,
) -> dict[int, str]:
    """Lifecycle for specific issue numbers. 404 and errors are omitted and not cached.

    A timeout returns the states already read. Callers treat omissions as unknown.
    """
    store = cache or shared_cache()
    found: dict[int, str] = {}
    deadline = time.monotonic() + timeout
    for number in numbers:
        try:
            left = _time_left(deadline, timeout)
        except GitHubRestTimeout:
            break
        try:
            result = store.get_json(f"repos/{repo}/issues/{number}", timeout=left)
        except GitHubRestTimeout:
            break
        except GitHubRestError:
            continue
        if result.status == 404 or not isinstance(result.body, dict):
            continue
        state = str(result.body.get("state") or "").lower()
        if state in {"open", "closed"}:
            found[number] = state
    return found
