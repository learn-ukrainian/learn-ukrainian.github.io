"""Shared GitHub REST cache for Monitor and Work pollers.

List and per-PR reads go through ``gh api`` with ``If-None-Match``. A 304
returns the cached body and does not replace it. Failures are not stored.
Both ``scripts.api.main`` and ``scripts.work.sources_public`` use
:func:`shared_cache` so one process keeps a single ETag map.

Projected dicts keep only the fields those consumers read. The shapes match
the ``gh --json`` objects the collectors already understood: ``createdAt``,
``isDraft``, ``headRefOid``, ``statusCheckRollup``, and ``reviewDecision``.
``reviewDecision`` is set only when REST proves it. A lone approval is not
``APPROVED``: branch protection's required count is not visible here.
"""

from __future__ import annotations

import contextvars
import json
import re
import subprocess
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

# (path, request headers, timeout seconds) -> (status, response headers, body)
RestTransport = Callable[[str, dict[str, str], float], tuple[int, dict[str, str], bytes]]

# Safety ceiling. Hitting it while ``Link: rel="next"`` remains is truncated,
# never a silent complete list.
_MAX_PAGES = 20
_DETAIL_WORKERS = 8
_CACHE_MAX_ENTRIES = 512
_DETAIL_TTL_S = 900.0
_DETAIL_URL = re.compile(
    r"(?:^|https://api\.github\.com/)repos/[^/]+/[^/]+/"
    r"(?:pulls/\d+(?:/reviews)?|issues/\d+(?:/comments)?|"
    r"commits/[^/?]+(?:/(?:check-runs|status))?)"
    r"(?:\?|$)"
)
_REQUEST_SEQ: contextvars.ContextVar[int] = contextvars.ContextVar("github_rest_request_seq", default=0)


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


class RestPage(list):
    """A REST collection. ``truncated`` means a later page was not read."""

    def __init__(self, items: list[Any], *, truncated: bool) -> None:
        super().__init__(items)
        self.truncated = truncated


@dataclass
class _CacheEntry:
    etag: str
    body: Any
    link_next: str | None
    seq: int
    stored_at: float
    detail: bool


class _IdentityAttempt:
    """One login lookup. Every waiter of this attempt re-raises its error."""

    def __init__(self) -> None:
        self.ready = threading.Event()
        self.error: BaseException | None = None
        self.waiters = 0


def current_request_seq() -> int:
    """Monotonic sequence of the ``get_json`` in flight on this thread."""
    return _REQUEST_SEQ.get()


def _is_detail_url(path: str) -> bool:
    """Per-PR and per-commit URLs expire. List URLs stay until the LRU evicts them."""
    return _DETAIL_URL.search(path) is not None


def _may_replace(existing: _CacheEntry | None, *, seq: int) -> bool:
    """A later-issued request wins. Response header times are not an order."""
    if existing is None:
        return True
    return seq >= existing.seq


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
    """Process-local ETag cache. Errors leave the previous entry in place.

    Keys are ``(login, url)``. The login comes from one ``GET /user`` and is
    never the token. Detail URLs expire; the map is an LRU with a hard cap.
    A response from an earlier request cannot replace a newer cached body.
    """

    def __init__(self, transport: RestTransport | None = None, *, identity: str | None = None) -> None:
        self._transport = transport or _gh_api_transport
        self._entries: OrderedDict[tuple[str, str], _CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._identity_lock = threading.Lock()
        self._identity = identity
        self._identity_attempt: _IdentityAttempt | None = None
        self._seq = 0

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _start_identity_attempt(self, timeout: float) -> _IdentityAttempt:
        """Start one login lookup. Caller holds ``_identity_lock``."""
        attempt = _IdentityAttempt()
        self._identity_attempt = attempt

        def _run() -> None:
            try:
                self._auth_identity(timeout)
            except Exception as exc:
                attempt.error = exc
            finally:
                attempt.ready.set()

        threading.Thread(target=_run, name="gh-rest-identity", daemon=True).start()
        return attempt

    def _kick_identity(self, timeout: float) -> None:
        """Start the one login lookup without blocking the data read."""
        if self._identity:
            return
        with self._identity_lock:
            if self._identity or self._identity_attempt is not None:
                return
            self._start_identity_attempt(timeout)

    def _wait_identity(self, timeout: float) -> str:
        if self._identity:
            return self._identity
        with self._identity_lock:
            if self._identity:
                return self._identity
            attempt = self._identity_attempt
            if attempt is None:
                attempt = self._start_identity_attempt(timeout)
            attempt.waiters += 1
        try:
            if not attempt.ready.wait(timeout):
                raise GitHubRestTimeout(timeout)
            if self._identity:
                return self._identity
            error = attempt.error
            if isinstance(error, Exception):
                raise error
            raise GitHubRestError("GitHub login lookup failed")
        finally:
            with self._identity_lock:
                attempt.waiters -= 1
                if (
                    attempt.waiters == 0
                    and attempt.ready.is_set()
                    and attempt.error is not None
                    and self._identity_attempt is attempt
                ):
                    self._identity_attempt = None

    def _auth_identity(self, timeout: float) -> str:
        if self._identity:
            return self._identity
        with self._identity_lock:
            if self._identity:
                return self._identity
            status, _headers, body = self._transport("user", {}, timeout)
            if status != 200:
                raise GitHubRestError("GitHub login lookup failed", status=status)
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise GitHubRestError("GitHub login lookup returned invalid JSON") from exc
            login = payload.get("login") if isinstance(payload, dict) else None
            if (
                not isinstance(login, str)
                or not login
                or login.strip() != login
                or "/" in login
                or any(c.isspace() for c in login)
            ):
                raise GitHubRestError("GitHub login lookup returned no login")
            self._identity = login
            return login

    def _expired(self, entry: _CacheEntry, now: float) -> bool:
        return entry.detail and (now - entry.stored_at) >= _DETAIL_TTL_S

    def _live_locked(self, key: tuple[str, str], now: float) -> _CacheEntry | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if self._expired(entry, now):
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return entry

    def _store_locked(self, key: tuple[str, str], entry: _CacheEntry, now: float) -> None:
        stale = [cached_key for cached_key, cached in self._entries.items() if self._expired(cached, now)]
        for cached_key in stale:
            del self._entries[cached_key]
        self._entries[key] = entry
        self._entries.move_to_end(key)
        while len(self._entries) > _CACHE_MAX_ENTRIES:
            self._entries.popitem(last=False)

    def cached_body(self, path: str) -> Any:
        with self._lock:
            if not self._identity:
                return None
            entry = self._live_locked((self._identity, path), time.monotonic())
            return None if entry is None else entry.body

    def get_json(self, path: str, *, timeout: float) -> RestResult:
        """Conditional GET.

        200 stores the body when this request is not older than the cached
        one. 304 returns the cached body and does not replace it. 404 is
        returned and not cached. Any other failure raises and is not cached.
        """
        if timeout <= 0:
            raise GitHubRestTimeout(timeout)
        known = self._identity
        if known is None:
            # Overlap the one login lookup with this read. A cold cache has no
            # validator to send, so the data request does not wait for /user.
            self._kick_identity(timeout)
        with self._lock:
            self._seq += 1
            seq = self._seq
            etag = None
            if known:
                current = self._live_locked((known, path), time.monotonic())
                etag = None if current is None else current.etag
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag

        token = _REQUEST_SEQ.set(seq)
        try:
            status, resp_headers, body = self._transport(path, headers, timeout)
        finally:
            _REQUEST_SEQ.reset(token)
        identity = known or self._wait_identity(timeout)
        key = (identity, path)
        resp_headers = {key_name.lower(): value for key_name, value in resp_headers.items()}
        new_etag = resp_headers.get("etag")
        link_next = _link_next(resp_headers.get("link"))

        if status == 304:
            with self._lock:
                cached = self._live_locked(key, time.monotonic())
                if cached is None:
                    raise GitHubRestError("304 without a cached body", status=304)
                # A rotated validator must be replayed next time; the body stays.
                # An older in-flight 304 must not roll the validator backward.
                if new_etag and new_etag != cached.etag and _may_replace(cached, seq=seq):
                    cached = _CacheEntry(
                        etag=new_etag,
                        body=cached.body,
                        link_next=cached.link_next,
                        seq=seq,
                        stored_at=cached.stored_at,
                        detail=cached.detail,
                    )
                    self._store_locked(key, cached, time.monotonic())
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
            raise GitHubRestError("invalid GitHub JSON") from exc

        if new_etag:
            with self._lock:
                existing = self._entries.get(key)
                if _may_replace(existing, seq=seq):
                    now = time.monotonic()
                    self._store_locked(
                        key,
                        _CacheEntry(
                            etag=new_etag,
                            body=parsed,
                            link_next=link_next,
                            seq=seq,
                            stored_at=now,
                            detail=_is_detail_url(path),
                        ),
                        now,
                    )
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


def _collect_pages(
    cache: GitHubRestCache,
    path: str,
    *,
    deadline: float,
    timeout: float,
    limit: int | None,
    keep: Callable[[dict[str, Any]], bool] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Follow ``Link: rel="next"`` until the list ends or ``limit`` items are kept.

    A page ceiling that still has a next link returns ``truncated=True``.
    Items rejected by ``keep`` (pull requests on the issues API) do not count
    toward ``limit`` and do not end the walk.
    """
    rows: list[dict[str, Any]] = []
    url: str | None = path
    pages = 0
    while url:
        pages += 1
        if pages > _MAX_PAGES:
            return rows, True
        result = cache.get_json(url, timeout=_time_left(deadline, timeout))
        if result.status == 404:
            raise GitHubRestError(f"GitHub REST 404 for {url}", status=404)
        if not isinstance(result.body, list):
            raise GitHubRestError(f"expected a JSON list from {url}")
        page = result.body
        for index, item in enumerate(page):
            if not isinstance(item, dict):
                continue
            if keep is not None and not keep(item):
                continue
            rows.append(item)
            if limit is not None and len(rows) >= limit:
                more_on_page = False
                for later in page[index + 1 :]:
                    if isinstance(later, dict) and (keep is None or keep(later)):
                        more_on_page = True
                        break
                return rows, more_on_page or bool(result.link_next)
        if not result.link_next:
            return rows, False
        url = result.link_next
    return rows, False


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


def review_facts(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Latest review state per reviewer, plus a count of each raw review state."""
    latest: dict[str, str] = {}
    counts: dict[str, int] = {}
    for review in reviews:
        state = str(review.get("state") or "").upper()
        if not state:
            continue
        counts[state] = counts.get(state, 0) + 1
        user = review.get("user")
        login = user.get("login") if isinstance(user, dict) else None
        if isinstance(login, str) and login:
            latest[login] = state
    return {"latest_by_reviewer": latest, "counts": counts}


def derive_review_decision(reviews: list[dict[str, Any]], requested_reviewers: Any) -> str | None:
    """REST cannot see the required approval count, so it never emits ``APPROVED``.

    ``CHANGES_REQUESTED`` is provable from a current changes-request review.
    An outstanding requested reviewer is ``REVIEW_REQUIRED``. Anything else,
    including one or more approvals, is unknown (``None``).
    """
    latest = review_facts(reviews)["latest_by_reviewer"]
    deciding = {state for state in latest.values() if state in {"APPROVED", "CHANGES_REQUESTED"}}
    if "CHANGES_REQUESTED" in deciding:
        return "CHANGES_REQUESTED"
    if isinstance(requested_reviewers, list) and any(
        isinstance(entry, dict) and entry.get("login") for entry in requested_reviewers
    ):
        return "REVIEW_REQUIRED"
    return None


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
    reviews_complete: bool = True,
    checks_complete: bool = True,
    comments_complete: bool = True,
) -> dict[str, Any]:
    """REST pull + conditional detail → the fields Work and idle-PR orient read.

    An incomplete review or check list is unknown: ``reviewDecision`` stays
    ``None`` and ``statusCheckRollup`` stays ``None``, so Work is not
    ``ON_TRACK`` and the idle-PR gate is not eligible.
    """
    detail = pull if isinstance(pull, dict) else {}
    head = raw.get("head") if isinstance(raw.get("head"), dict) else {}
    state = raw.get("state")
    mergeable = detail.get("mergeable_state")
    requested = detail.get("requested_reviewers")
    if requested is None:
        requested = raw.get("requested_reviewers")
    review_rows = [review for review in reviews if isinstance(review, dict)]
    facts = review_facts(review_rows)
    facts["complete"] = reviews_complete
    if checks_complete:
        rollup: list[dict[str, Any]] | None = [_project_check_run(run) for run in check_runs if isinstance(run, dict)]
        rollup.extend(_project_status(status) for status in statuses if isinstance(status, dict))
    else:
        rollup = None
    projected_reviews = [_project_review(review) for review in review_rows]
    if comments is None or not comments_complete:
        projected_comments = None
    else:
        projected_comments = [_project_comment(comment) for comment in comments if isinstance(comment, dict)]
    return {
        "number": raw.get("number"),
        "title": raw.get("title"),
        "state": str(state).upper() if isinstance(state, str) and state else None,
        "isDraft": bool(raw.get("draft")),
        "headRefName": head.get("ref"),
        "headRefOid": head.get("sha"),
        "updatedAt": raw.get("updated_at"),
        "createdAt": raw.get("created_at"),
        "reviewDecision": (derive_review_decision(review_rows, requested) if reviews_complete else None),
        "reviewFacts": facts,
        "reviews": projected_reviews,
        "comments": projected_comments,
        "statusCheckRollup": rollup,
        "mergeStateStatus": str(mergeable).upper() if isinstance(mergeable, str) and mergeable else None,
        "labels": _names(raw.get("labels"), "name"),
        "assignees": _names(raw.get("assignees"), "login"),
        "url": raw.get("html_url"),
    }


def _is_issue(item: dict[str, Any]) -> bool:
    return "pull_request" not in item


def list_open_issues(
    repo: str,
    *,
    limit: int,
    timeout: float,
    cache: GitHubRestCache | None = None,
) -> RestPage:
    """Open issues only (the REST issues list also returns pull requests).

    Pull requests are dropped and are not counted toward ``limit``. The
    returned page is ``truncated`` when the caller cap or the page ceiling
    leaves further issues unread.
    """
    store = cache or shared_cache()
    if limit <= 0:
        return RestPage([], truncated=False)
    path = f"repos/{repo}/issues?state=open&per_page=100&sort=created&direction=desc"
    deadline = time.monotonic() + timeout
    rows, truncated = _collect_pages(store, path, deadline=deadline, timeout=timeout, limit=limit, keep=_is_issue)
    return RestPage([project_issue(item) for item in rows], truncated=truncated)


def _list_body(
    cache: GitHubRestCache,
    path: str,
    *,
    deadline: float,
    timeout: float,
) -> tuple[list[dict[str, Any]], bool]:
    """Follow next links. The bool is completeness (False when the page cap hits)."""
    rows, truncated = _collect_pages(cache, path, deadline=deadline, timeout=timeout, limit=None)
    return rows, not truncated


def _check_runs(
    cache: GitHubRestCache,
    repo: str,
    sha: str,
    *,
    deadline: float,
    timeout: float,
) -> tuple[list[dict[str, Any]], bool]:
    """Check runs followed via ``Link: rel="next"``.

    Complete only when no next link remains and the collected count equals
    ``total_count``. An empty page is not complete on its own.
    """
    runs: list[dict[str, Any]] = []
    url: str | None = f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page=1"
    pages = 0
    total: int | None = None
    while url:
        pages += 1
        if pages > _MAX_PAGES:
            return runs, False
        result = cache.get_json(url, timeout=_time_left(deadline, timeout))
        if result.status == 404 or not isinstance(result.body, dict):
            raise GitHubRestError(f"check runs unavailable for {sha}", status=result.status)
        chunk = result.body.get("check_runs") or []
        if not isinstance(chunk, list):
            raise GitHubRestError(f"check runs payload was not a list for {sha}")
        runs.extend(item for item in chunk if isinstance(item, dict))
        page_total = result.body.get("total_count")
        if isinstance(page_total, int) and not isinstance(page_total, bool):
            total = page_total
        if not result.link_next:
            return runs, total is not None and len(runs) == total
        url = result.link_next
    return runs, False


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
    runs, checks_complete = _check_runs(cache, repo, sha, deadline=deadline, timeout=timeout)
    status = cache.get_json(f"repos/{repo}/commits/{sha}/status", timeout=_time_left(deadline, timeout))
    if status.status not in {200, 304} or not isinstance(status.body, dict):
        raise GitHubRestError(f"commit status unavailable for {sha}", status=status.status)
    statuses = status.body.get("statuses") or []
    if not isinstance(statuses, list):
        raise GitHubRestError(f"commit status payload was not a list for {sha}")
    # Combined status ``total_count`` is the full set. A short payload is unknown.
    status_total = status.body.get("total_count")
    if isinstance(status_total, int) and status_total > len(statuses):
        checks_complete = False
    reviews, reviews_complete = _list_body(
        cache,
        f"repos/{repo}/pulls/{number}/reviews?per_page=100",
        deadline=deadline,
        timeout=timeout,
    )
    comments: list[dict[str, Any]] | None = None
    comments_complete = True
    if include_comments:
        comments, comments_complete = _list_body(
            cache,
            f"repos/{repo}/issues/{number}/comments?per_page=100",
            deadline=deadline,
            timeout=timeout,
        )
    return project_pull_request(
        raw,
        pull=pull.body,
        check_runs=runs,
        statuses=[item for item in statuses if isinstance(item, dict)],
        reviews=reviews,
        comments=comments,
        reviews_complete=reviews_complete,
        checks_complete=checks_complete,
        comments_complete=comments_complete,
    )


def list_open_prs(
    repo: str,
    *,
    limit: int,
    timeout: float,
    cache: GitHubRestCache | None = None,
    include_comments: bool = False,
) -> RestPage:
    """Open pulls. Check runs, reviews, and mergeability are one conditional read per open PR.

    ``truncated`` is set when the pull list itself stopped early. An incomplete
    check or review list on one pull is unknown on that pull, not a silent
    green or approval.
    """
    store = cache or shared_cache()
    if limit <= 0:
        return RestPage([], truncated=False)
    path = f"repos/{repo}/pulls?state=open&per_page=100&sort=created&direction=desc"
    deadline = time.monotonic() + timeout
    raw, truncated = _collect_pages(store, path, deadline=deadline, timeout=timeout, limit=limit)
    if not raw:
        return RestPage([], truncated=truncated)
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
        return RestPage(list(pool.map(_one, raw)), truncated=truncated)


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

    def _one(number: int) -> tuple[int, str] | None:
        try:
            left = _time_left(deadline, timeout)
        except GitHubRestTimeout:
            return None
        try:
            result = store.get_json(f"repos/{repo}/issues/{number}", timeout=left)
        except (GitHubRestTimeout, GitHubRestError):
            return None
        if result.status == 404 or not isinstance(result.body, dict):
            return None
        state = str(result.body.get("state") or "").lower()
        if state in {"open", "closed"}:
            return number, state
        return None

    if not numbers:
        return found
    workers = max(1, min(_DETAIL_WORKERS, len(numbers)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item in pool.map(_one, numbers):
            if item is not None:
                found[item[0]] = item[1]
    return found
