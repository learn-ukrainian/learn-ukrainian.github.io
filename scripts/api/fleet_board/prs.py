"""Open pull-request pipeline for the fleet board.

GitHub reads go through the shared GitHub client (REST, plus one queue-membership
query for the field REST does not provide). Keeper hold, flake grant, and check
state come from the keeper's own helpers. A short-lived cache keeps repeat
reads off the network. Source failures stay inside the envelope.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.github_client import GitHubClient
from scripts.orchestration.integration_sweep import TRUSTED_ASSOCIATIONS, lookup_verdict, parse_marker
from scripts.orchestration.merge_queue_keeper import (
    KeeperError,
    _check_state,
    _codeql_rows,
    _evaluate_checks,
    _hold,
    _latest,
    _load,
    _requeue_grants,
    _requeue_hold,
)

from .activity import (
    PrActivity,
    ThroughputEvent,
    attention_rows,
    build_stats,
    hours_idle,
    lane_from_ref,
    read_stale_state,
)
from .envelope import envelope
from .sources import SourceReport, read_location, report

GITHUB_SOURCE = "github"
MQ_SOURCE = "mq_state"
REPO_ENV = "FLEET_GITHUB_REPO"
STALE_MIN_ENV = "FLEET_PR_STALE_MIN"
CACHE_TTL_ENV = "FLEET_GITHUB_READ_TTL"
DEFAULT_STALE_MIN = 60
DEFAULT_CACHE_TTL_S = 15.0
MAX_CACHE_TTL_S = 120.0
MQ_FRESH_S = 120.0
REQUEST_TIMEOUT_S = 20.0
MAX_PAGES = 10

REQUEUE_FILE = "requeue.json"
KEEPER_FILES = ("keeper.json", "merge_queue_keeper.json")
ALERT_FILE = "stale-approved.json"

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_EPIC_MARK = re.compile(r"(?i)(?:^|[^A-Za-z0-9_])epic[:/]([A-Za-z0-9][A-Za-z0-9_-]{0,40})")
_CLOSING = re.compile(r"(?i)(?:^|[^A-Za-z0-9_])(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d{1,7})\b")
_MERGE_STATE = {
    "clean": "CLEAN",
    "blocked": "BLOCKED",
    "behind": "BEHIND",
    "dirty": "DIRTY",
    "unstable": "UNSTABLE",
    "draft": "DRAFT",
}
_CLEAN_STATES = frozenset({"CLEAN", "BLOCKED", "BEHIND", "UNSTABLE"})
_AT_HEAD = frozenset({"APPROVED", "CHANGES_REQUESTED", "BLOCKED"})
_STATE_FILTERS = frozenset(
    {
        "open",
        "stale",
        "stale_green",
        "held",
        "red",
        "green",
        "pending",
        "queued",
        "not_queued",
        "dropped",
    }
)


class GithubReadError(Exception):
    """A GitHub list read failed. The message is never copied into a response."""


@dataclass(frozen=True)
class Pull:
    number: int
    title: str
    draft: bool
    head_sha: str
    head_ref: str
    base_ref: str
    labels: tuple[dict[str, str], ...]
    body: str
    merge_state: str | None
    epics: tuple[str, ...]
    commit_at: str | None = None


@dataclass(frozen=True)
class GithubView:
    repo: str
    login: str | None
    default_branch: str | None
    pulls: tuple[Pull, ...]
    comments: Mapping[int, tuple[dict[str, Any], ...] | None]
    checks: Mapping[str, tuple[dict[str, Any], ...] | None]
    files: Mapping[int, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    queued: Mapping[int, bool] = field(default_factory=dict)
    queue_failed: bool = False
    age_s: float = 0.0
    stale: bool = False
    failed: bool = False


@dataclass(frozen=True)
class MqSnapshot:
    usable: bool
    keeper: Mapping[str, Any]
    grants: dict[str, dict[str, Any]] | None
    since: Mapping[str, str]


@dataclass(frozen=True)
class _Fetched:
    view: GithubView
    fetched_at: float


_cache_lock = threading.Lock()
_cache: dict[str, _Fetched] = {}


def clear_github_cache() -> None:
    with _cache_lock:
        _cache.clear()


def utc_now() -> datetime:
    return datetime.now(UTC)


def _client() -> GitHubClient:
    return GitHubClient()


def _parse_time(value: str) -> datetime | None:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _stamp(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = _parse_time(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _bounded_int(raw: str | None, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    if value < 0:
        return default
    return value


def stale_after_min(environ: Mapping[str, str] | None = None) -> int:
    source = os.environ if environ is None else environ
    return _bounded_int(source.get(STALE_MIN_ENV), DEFAULT_STALE_MIN)


def _cache_ttl(environ: Mapping[str, str] | None, override: float | None) -> float:
    if override is not None:
        return override
    source = os.environ if environ is None else environ
    raw = source.get(CACHE_TTL_ENV)
    if raw is None or not str(raw).strip():
        return DEFAULT_CACHE_TTL_S
    try:
        value = float(str(raw).strip())
    except ValueError:
        return DEFAULT_CACHE_TTL_S
    if value < 0 or value > MAX_CACHE_TTL_S:
        return DEFAULT_CACHE_TTL_S
    return value


def resolve_repo(environ: Mapping[str, str] | None = None) -> str | None:
    """Owner/name from the board setting, else the GitHub client's own variable."""
    source = os.environ if environ is None else environ
    for key in (REPO_ENV, "GH_REPO", "GITHUB_REPOSITORY"):
        raw = source.get(key)
        if raw is None:
            continue
        value = raw.strip()
        if _REPO.fullmatch(value):
            return value
    return None


def _link_next(headers: Mapping[str, str] | None) -> str | None:
    if not isinstance(headers, Mapping):
        return None
    link = headers.get("link") or headers.get("Link") or ""
    if not isinstance(link, str):
        return None
    for part in link.split(","):
        if 'rel="next"' not in part and "rel=next" not in part:
            continue
        start = part.find("<")
        end = part.find(">", start + 1)
        if start >= 0 and end > start:
            return part[start + 1 : end]
    return None


def _request(client: Any, method: str, endpoint: str, *, payload: dict[str, Any] | None = None) -> Any:
    try:
        return client.request(method, endpoint, payload=payload, timeout=REQUEST_TIMEOUT_S, allow_stale=True)
    except Exception as exc:
        raise GithubReadError from exc


def _observe(result: Any, age: float, stale: bool) -> tuple[float, bool]:
    try:
        seen = float(getattr(result, "age_seconds", 0) or 0)
    except (TypeError, ValueError):
        seen = 0.0
    if seen < 0:
        seen = 0.0
    return max(age, seen), stale or bool(getattr(result, "stale", False))


def _get_json(client: Any, endpoint: str) -> tuple[Any, float, bool]:
    result = _request(client, "GET", endpoint)
    if getattr(result, "error", None):
        raise GithubReadError
    age, stale = _observe(result, 0.0, False)
    return result.value, age, stale


def _pages(client: Any, endpoint: str) -> tuple[list[dict[str, Any]], float, bool]:
    rows: list[dict[str, Any]] = []
    age = 0.0
    stale = False
    url: str | None = endpoint
    for _ in range(MAX_PAGES):
        if url is None:
            break
        result = _request(client, "GET", url)
        if getattr(result, "error", None):
            raise GithubReadError
        age, stale = _observe(result, age, stale)
        body = result.value
        if not isinstance(body, list):
            raise GithubReadError
        rows.extend(item for item in body if isinstance(item, dict))
        url = _link_next(getattr(result, "headers", None))
        if url is None:
            return rows, age, stale
    raise GithubReadError


def _check_runs(client: Any, repo: str, sha: str) -> tuple[tuple[dict[str, Any], ...] | None, float, bool]:
    runs: list[dict[str, Any]] = []
    age = 0.0
    stale = False
    url: str | None = f"repos/{repo}/commits/{sha}/check-runs?per_page=100"
    total: int | None = None
    for _ in range(MAX_PAGES):
        if url is None:
            break
        try:
            result = _request(client, "GET", url)
        except GithubReadError:
            return None, age, stale
        if getattr(result, "error", None) or not isinstance(result.value, dict):
            return None, age, stale
        age, stale = _observe(result, age, stale)
        chunk = result.value.get("check_runs")
        page_total = result.value.get("total_count")
        if not isinstance(chunk, list) or type(page_total) is not int:
            return None, age, stale
        total = page_total
        for item in chunk:
            if not isinstance(item, dict):
                continue
            if not isinstance(item.get("head_sha"), str):
                item = {**item, "head_sha": sha}
            runs.append(item)
        url = _link_next(getattr(result, "headers", None))
        if url is None:
            if len(runs) != total:
                return None, age, stale
            return tuple(runs), age, stale
    return None, age, stale


def _optional_object(client: Any, endpoint: str) -> tuple[dict[str, Any] | None, float, bool]:
    try:
        value, age, stale = _get_json(client, endpoint)
    except GithubReadError:
        return None, 0.0, False
    if isinstance(value, dict):
        return value, age, stale
    return None, age, stale


def _merge_state(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    return _MERGE_STATE.get(raw.casefold(), "UNKNOWN")


def _labels(raw: Any) -> tuple[dict[str, str], ...] | None:
    if not isinstance(raw, list):
        return None
    labels: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            return None
        labels.append({"name": item["name"]})
    return tuple(labels)


def _epic_tokens(*texts: str) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in (*_EPIC_MARK.finditer(text), *_CLOSING.finditer(text)):
            token = match.group(1)
            key = token.casefold()
            if key in seen:
                continue
            seen.add(key)
            found.append(token)
    return tuple(found)


def _pull_from_rest(raw: Mapping[str, Any]) -> Pull | None:
    number = raw.get("number")
    title = raw.get("title")
    head = raw.get("head") if isinstance(raw.get("head"), Mapping) else None
    base = raw.get("base") if isinstance(raw.get("base"), Mapping) else None
    draft = raw.get("draft")
    labels = _labels(raw.get("labels"))
    if (
        type(number) is not int
        or number < 1
        or not isinstance(title, str)
        or not isinstance(draft, bool)
        or head is None
        or base is None
        or not isinstance(head.get("sha"), str)
        or not head["sha"]
        or not isinstance(head.get("ref"), str)
        or not head["ref"]
        or not isinstance(base.get("ref"), str)
        or not base["ref"]
        or labels is None
    ):
        return None
    body = raw.get("body") if isinstance(raw.get("body"), str) else ""
    label_text = " ".join(item["name"] for item in labels)
    return Pull(
        number=number,
        title=title,
        draft=draft,
        head_sha=head["sha"],
        head_ref=head["ref"],
        base_ref=base["ref"],
        labels=labels,
        body=body,
        merge_state=_merge_state(raw.get("mergeable_state")),
        epics=_epic_tokens(label_text, title, body),
    )


def _files(client: Any, repo: str, number: int) -> tuple[dict[str, Any], ...] | None:
    try:
        rows, _age, _stale = _pages(client, f"repos/{repo}/pulls/{number}/files?per_page=100")
    except GithubReadError:
        return None
    return tuple(rows)


class _FileSource:
    def __init__(self, files: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> None:
        self._files = list(files)

    def files(self, _number: int) -> list[dict[str, Any]]:
        return self._files


def _ci_state(
    number: int,
    head: str,
    checks: tuple[dict[str, Any], ...] | None,
    files: tuple[dict[str, Any], ...] | None,
) -> str:
    if checks is None:
        return "CI-unknown"
    rows = list(checks)
    try:
        state = _check_state(rows, head)
        if state == "CodeQL-pending" and _codeql_rows(rows, head) and files is not None:
            state = _evaluate_checks(_FileSource(files), number, head, rows)
    except KeeperError:
        return "CI-unknown"
    return state


def _ci_label(state: str) -> str | None:
    if state == "ok":
        return "green"
    if state.startswith("CI-red-"):
        return "red"
    if state == "CI-unknown":
        return None
    if state.startswith("CI-pending-") or state == "CodeQL-pending":
        return "pending"
    return None


def _commit_stamp(client: Any, repo: str, sha: str) -> tuple[str | None, float, bool]:
    payload, age, stale = _optional_object(client, f"repos/{repo}/commits/{sha}")
    if not isinstance(payload, dict):
        return None, age, stale
    commit = payload.get("commit")
    if not isinstance(commit, dict):
        return None, age, stale
    for key in ("committer", "author"):
        person = commit.get(key)
        if isinstance(person, dict) and isinstance(person.get("date"), str):
            stamp = _stamp(person["date"])
            if stamp is not None:
                return stamp, age, stale
    return None, age, stale


def _failing_check_names(
    number: int,
    head: str,
    checks: tuple[dict[str, Any], ...] | None,
    files: tuple[dict[str, Any], ...] | None,
) -> list[str]:
    """Names of required checks at ``head`` that finished without succeeding."""
    if checks is None:
        return []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in checks:
        if not isinstance(row, dict) or row.get("head_sha") != head or not isinstance(row.get("name"), str):
            return []
        grouped.setdefault(row["name"], []).append(row)
    required = ["CI Gate", *[name for name in grouped if name.startswith("Analyze (")]]
    failed: list[str] = []
    for name in required:
        group = grouped.get(name, [])
        if not group:
            continue
        latest = _latest(group)
        if latest.get("status") == "completed" and latest.get("conclusion") != "success":
            failed.append(name)
    state = _ci_state(number, head, checks, files)
    if state.startswith("CI-red-"):
        name = state.removeprefix("CI-red-")
        if name not in failed:
            failed.append(name)
    return sorted(set(failed))


def _verdict_at(comments: tuple[dict[str, Any], ...] | None, login: str | None) -> datetime | None:
    """When the latest trusted cross-family verdict comment was recorded."""
    if comments is None or not login:
        return None
    latest: datetime | None = None
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        body = comment.get("body")
        if not isinstance(body, str) or parse_marker(body) is None:
            continue
        author = comment.get("user")
        author_login = author.get("login") if isinstance(author, dict) else None
        if author_login != login or comment.get("author_association") not in TRUSTED_ASSOCIATIONS:
            continue
        created = _parse_time(comment["created_at"]) if isinstance(comment.get("created_at"), str) else None
        updated = _parse_time(comment["updated_at"]) if isinstance(comment.get("updated_at"), str) else None
        if created is None or updated is None or created != updated:
            continue
        if latest is None or created > latest:
            latest = created
    return latest


def _gate_label(checks: tuple[dict[str, Any], ...] | None, head: str) -> str | None:
    if checks is None:
        return None
    rows: list[dict[str, Any]] = []
    for row in checks:
        if not isinstance(row, dict) or row.get("head_sha") != head or not isinstance(row.get("name"), str):
            return None
        if row["name"] == "CI Gate":
            rows.append(row)
    if not rows:
        return "pending"
    latest = _latest(rows)
    if latest.get("status") != "completed":
        return "pending"
    if latest.get("conclusion") != "success":
        return "red"
    return "green"


def _fetch_github(repo: str, client: Any) -> GithubView:
    pulls_raw, age, stale = _pages(client, f"repos/{repo}/pulls?state=open&per_page=100&sort=created&direction=desc")
    failed = False
    user, user_age, user_stale = _optional_object(client, "user")
    age, stale = max(age, user_age), stale or user_stale
    login = user.get("login").strip() if isinstance(user, dict) and isinstance(user.get("login"), str) else None
    if not login:
        login = None
    repository, repo_age, repo_stale = _optional_object(client, f"repos/{repo}")
    age, stale = max(age, repo_age), stale or repo_stale
    default_branch = repository.get("default_branch") if isinstance(repository, dict) else None
    if not isinstance(default_branch, str) or not default_branch:
        default_branch = None

    pulls: list[Pull] = []
    comments: dict[int, tuple[dict[str, Any], ...] | None] = {}
    checks: dict[str, tuple[dict[str, Any], ...] | None] = {}
    files: dict[int, tuple[dict[str, Any], ...]] = {}
    commit_at: dict[str, str | None] = {}
    for raw in pulls_raw:
        if raw.get("mergeable_state") is None and type(raw.get("number")) is int:
            detail, detail_age, detail_stale = _optional_object(client, f"repos/{repo}/pulls/{raw['number']}")
            age, stale = max(age, detail_age), stale or detail_stale
            if detail is not None:
                raw = {**raw, **detail}
        pull = _pull_from_rest(raw)
        if pull is None:
            failed = True
            continue
        if pull.head_sha not in commit_at:
            stamp, commit_age, commit_stale = _commit_stamp(client, repo, pull.head_sha)
            age, stale = max(age, commit_age), stale or commit_stale
            commit_at[pull.head_sha] = stamp
        pull = replace(pull, commit_at=commit_at[pull.head_sha])
        pulls.append(pull)
        try:
            comment_rows, comment_age, comment_stale = _pages(
                client, f"repos/{repo}/issues/{pull.number}/comments?per_page=100"
            )
            age, stale = max(age, comment_age), stale or comment_stale
            comments[pull.number] = tuple(comment_rows)
        except GithubReadError:
            comments[pull.number] = None
            failed = True
        check_rows, check_age, check_stale = _check_runs(client, repo, pull.head_sha)
        age, stale = max(age, check_age), stale or check_stale
        checks[pull.head_sha] = check_rows
        if check_rows is None:
            failed = True
            continue
        state = _check_state(list(check_rows), pull.head_sha)
        if state == "CodeQL-pending" and _codeql_rows(list(check_rows), pull.head_sha):
            listed = _files(client, repo, pull.number)
            if listed is None:
                failed = True
            else:
                files[pull.number] = listed

    queued, queue_failed, queue_age, queue_stale = _queue_flags(client, repo)
    age, stale = max(age, queue_age), stale or queue_stale
    if queue_failed:
        failed = True
    return GithubView(
        repo=repo,
        login=login,
        default_branch=default_branch,
        pulls=tuple(pulls),
        comments=comments,
        checks=checks,
        files=files,
        queued=queued,
        queue_failed=queue_failed,
        age_s=age,
        stale=stale,
        failed=failed,
    )


def _queue_flags(client: Any, repo: str) -> tuple[dict[int, bool], bool, float, bool]:
    owner, name = repo.split("/", 1)
    query = (
        "query($owner:String!,$name:String!,$cursor:String){"
        "repository(owner:$owner,name:$name){"
        "pullRequests(states:OPEN,first:100,after:$cursor){"
        "pageInfo{hasNextPage endCursor} nodes{number isInMergeQueue}"
        "}}}"
    )
    flags: dict[int, bool] = {}
    cursor: str | None = None
    age = 0.0
    stale = False
    for _ in range(MAX_PAGES):
        try:
            result = _request(
                client,
                "POST",
                "graphql",
                payload={"query": query, "variables": {"owner": owner, "name": name, "cursor": cursor}},
            )
        except GithubReadError:
            return {}, True, age, stale
        age, stale = _observe(result, age, stale)
        if getattr(result, "error", None) or not isinstance(result.value, dict) or result.value.get("errors"):
            return {}, True, age, stale
        repository = (result.value.get("data") or {}).get("repository")
        connection = repository.get("pullRequests") if isinstance(repository, dict) else None
        if not isinstance(connection, dict):
            return {}, True, age, stale
        nodes = connection.get("nodes")
        page = connection.get("pageInfo")
        if not isinstance(nodes, list) or not isinstance(page, dict):
            return {}, True, age, stale
        for node in nodes:
            number = node.get("number") if isinstance(node, dict) else None
            queued = node.get("isInMergeQueue") if isinstance(node, dict) else None
            if type(number) is not int or not isinstance(queued, bool):
                return {}, True, age, stale
            flags[number] = queued
        if not page.get("hasNextPage"):
            return flags, False, age, stale
        cursor = page.get("endCursor")
        if not isinstance(cursor, str) or not cursor:
            return {}, True, age, stale
    return {}, True, age, stale


def load_github_view(
    repo: str,
    *,
    client: Any = None,
    now: float | None = None,
    ttl: float | None = None,
    environ: Mapping[str, str] | None = None,
) -> GithubView:
    """Read one repository, reusing a short-lived result when ``client`` is omitted."""
    if client is not None:
        return _fetch_github(repo, client)
    moment = time.monotonic() if now is None else now
    window = _cache_ttl(environ, ttl)
    with _cache_lock:
        cached = _cache.get(repo)
        if cached is not None and moment - cached.fetched_at < window:
            age = max(cached.view.age_s, moment - cached.fetched_at)
            return replace(cached.view, age_s=age)
    view = _fetch_github(repo, _client())
    if not view.failed:
        with _cache_lock:
            _cache[repo] = _Fetched(view, moment)
    return view


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _alert_since(payload: Any) -> dict[str, str] | None:
    if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("approved"), dict):
        return None
    times: dict[str, str] = {}
    for key, value in payload["approved"].items():
        if not isinstance(key, str) or not isinstance(value, dict):
            return None
        since = value.get("since")
        if not isinstance(since, str) or _parse_time(since) is None:
            return None
        times[key] = since
    return times


def _file_age(path: Path, now: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    return max(0.0, (now - modified).total_seconds())


def read_mq_state(
    environ: Mapping[str, str] | None = None,
    *,
    now: datetime | None = None,
) -> tuple[SourceReport, MqSnapshot]:
    """Keeper state, requeue gate, and stale-approved times from ``FLEET_MQ_STATE_DIR``."""
    empty = MqSnapshot(False, {}, None, {})
    location = read_location("FLEET_MQ_STATE_DIR", environ)
    if location is None:
        return report(MQ_SOURCE, "not_configured"), empty
    root = Path(location)
    moment = now or utc_now()
    try:
        if not root.is_dir():
            return report(MQ_SOURCE, "unavailable"), empty
        keeper_path = next((root / name for name in KEEPER_FILES if (root / name).is_file()), None)
        keeper = _load(keeper_path) if keeper_path is not None else {"queued": {}, "drops": {}}
        gate = root / REQUEUE_FILE
        grants = _requeue_grants(gate if gate.is_file() else None)
        alert = root / ALERT_FILE
        since: dict[str, str] = {}
        if alert.is_file():
            parsed = _alert_since(_read_json(alert))
            if parsed is None:
                return report(MQ_SOURCE, "unavailable"), empty
            since = parsed
        watched = [path for path in (keeper_path, gate if gate.is_file() else None) if path is not None]
        ages = [_file_age(path, moment) for path in watched]
    except (OSError, ValueError, KeeperError):
        return report(MQ_SOURCE, "unavailable"), empty
    # The alert file is written once, when a head becomes ready. Its age is the
    # ready time, so freshness follows the keeper and the requeue gate.
    age = max(ages) if ages else 0.0
    status = "stale" if ages and age > MQ_FRESH_S else "ok"
    return report(MQ_SOURCE, status, age_s=age), MqSnapshot(True, keeper, grants, since)


def _drop_count(keeper: Mapping[str, Any], drop_key: str) -> int:
    raw = keeper.get("drops", {}).get(drop_key, 0) if isinstance(keeper.get("drops"), Mapping) else 0
    return raw if type(raw) is int else 0


def _keeper_hold(
    pull: Pull,
    drop_key: str,
    mq: MqSnapshot,
) -> tuple[bool | None, str | None]:
    hold = _hold({"title": pull.title, "labels": list(pull.labels)})
    if hold is True:
        return True, "hold"
    if hold is None:
        return None, "hold-unknown"
    if not mq.usable:
        return False, None
    if drop_key in mq.keeper.get("squash_revoked", {}):
        return True, "squash-text-blocked"
    reason = _requeue_hold(drop_key, _drop_count(mq.keeper, drop_key), mq.grants, mq.keeper)
    if reason:
        return True, reason
    return False, None


def _flake(drop_key: str, mq: MqSnapshot) -> dict[str, Any] | None:
    if not mq.usable:
        return None
    row: Mapping[str, Any] = {}
    if isinstance(mq.grants, dict):
        raw = mq.grants.get(drop_key)
        if isinstance(raw, dict):
            row = raw
    decision = row.get("decision")
    if decision not in {"grant", "deny"}:
        decision = None
    requeued = mq.keeper.get("requeued", {})
    used = isinstance(requeued, Mapping) and drop_key in requeued
    recorded = requeued.get(drop_key) if isinstance(requeued, Mapping) else None
    at = row.get("at") if isinstance(row.get("at"), str) else None
    if at is None and isinstance(recorded, str):
        at = recorded
    if decision is None and not used:
        return None
    return {
        "decision": decision or "grant",
        "used": used,
        "at": _stamp(at),
    }


def _mq_status(pull: Pull, view: GithubView, mq: MqSnapshot, drop_key: str) -> str | None:
    if view.queue_failed or pull.number not in view.queued:
        return None
    if view.queued[pull.number] is True:
        return "queued"
    if not mq.usable:
        return "not_queued"
    queued = mq.keeper.get("queued", {})
    previous = queued.get(str(pull.number)) if isinstance(queued, Mapping) else None
    ejected = previous == pull.head_sha or _drop_count(mq.keeper, drop_key) >= 1
    return "dropped" if ejected else "not_queued"


def _cf(pull: Pull, view: GithubView) -> dict[str, Any]:
    comments = view.comments.get(pull.number)
    if comments is None or not view.login:
        return {"verdict": "unknown", "at_head": False}
    verdict = lookup_verdict(comments, pull.head_sha, view.login)
    return {"verdict": verdict.state, "at_head": verdict.state in _AT_HEAD}


def _clean(pull: Pull) -> bool:
    return pull.draft is False and pull.merge_state in _CLEAN_STATES


def _ready_minutes(
    pull: Pull,
    *,
    ci: str | None,
    cf: Mapping[str, Any],
    mq_status: str | None,
    hold: bool | None,
    mq: MqSnapshot,
    now: datetime,
    threshold: int,
) -> tuple[str | None, bool, int | None]:
    eligible = (
        mq.usable
        and hold is False
        and ci == "green"
        and cf.get("verdict") == "APPROVED"
        and cf.get("at_head") is True
        and mq_status in {"not_queued", "dropped"}
        and _clean(pull)
    )
    if not eligible:
        return None, False, None
    raw = mq.since.get(f"{pull.number}:{pull.head_sha}")
    opened = _parse_time(raw) if isinstance(raw, str) else None
    if opened is None:
        return None, False, None
    minutes = int((now - opened).total_seconds() // 60)
    if minutes < 0:
        minutes = 0
    return _stamp(raw), minutes >= threshold, minutes


def _stacked(pull: Pull, by_head: Mapping[str, dict[str, Any]], default_branch: str | None) -> dict[str, Any] | None:
    if not default_branch or pull.base_ref == default_branch or pull.base_ref == pull.head_ref:
        return None
    base = by_head.get(pull.base_ref)
    if base is None or base["number"] == pull.number:
        return {"number": None, "ref": pull.base_ref, "state": None, "mq": None}
    return {"number": base["number"], "ref": pull.base_ref, "state": "open", "mq": base["mq"]}


def _plain_blocker(pull: Pull, cf: Mapping[str, Any], failed: list[str]) -> dict[str, Any]:
    if pull.merge_state == "DIRTY":
        return {"kind": "conflict"}
    if failed:
        return {"kind": "failing_check", "checks": failed}
    if cf.get("verdict") == "CHANGES_REQUESTED" and cf.get("at_head") is True:
        return {"kind": "cf_changes"}
    return {"kind": "none"}


def _stacked_blocker(
    pull: Pull,
    by_head: Mapping[str, dict[str, Any]],
    recorded: PrActivity | None,
) -> dict[str, Any]:
    base = by_head.get(pull.base_ref)
    if base is not None and base["number"] != pull.number:
        return {"kind": "stacked_base", "number": base["number"], "state": "open"}
    if recorded is not None and recorded.base_state is not None:
        return {"kind": "stacked_base", "number": recorded.base_number, "state": recorded.base_state}
    return {"kind": "stacked_base", "number": None, "state": "unmerged"}


def assemble_prs(
    view: GithubView,
    mq: MqSnapshot,
    *,
    now: datetime | None = None,
    stale_min: int | None = None,
    activity: Mapping[int, PrActivity] | None = None,
) -> list[dict[str, Any]]:
    """One row per open pull request. An older-head approval does not count.

    A pull request whose base is not ``main`` is stacked and is never ready.
    """
    moment = now or utc_now()
    threshold = DEFAULT_STALE_MIN if stale_min is None else stale_min
    recorded = activity or {}
    rows: list[tuple[Pull, dict[str, Any]]] = []
    for pull in sorted(view.pulls, key=lambda item: item.number):
        drop_key = f"{pull.number}:{pull.head_sha}"
        checks = view.checks.get(pull.head_sha)
        files = view.files.get(pull.number)
        ci = _ci_label(_ci_state(pull.number, pull.head_sha, checks, files))
        gate = _gate_label(checks, pull.head_sha)
        cf = _cf(pull, view)
        queue = _mq_status(pull, view, mq, drop_key)
        hold, reason = _keeper_hold(pull, drop_key, mq)
        ready_since, stale_green, minutes = _ready_minutes(
            pull,
            ci=ci,
            cf=cf,
            mq_status=queue,
            hold=hold,
            mq=mq,
            now=moment,
            threshold=threshold,
        )
        note = recorded.get(pull.number)
        failed = _failing_check_names(pull.number, pull.head_sha, checks, files)
        idle, idle_24h, idle_48h = hours_idle(
            moment,
            _parse_time(pull.commit_at) if isinstance(pull.commit_at, str) else None,
            _verdict_at(view.comments.get(pull.number), view.login),
            note.commit_at if note is not None else None,
            note.cf_at if note is not None else None,
            note.merge_event_at if note is not None else None,
        )
        owner = note.owner_lane if note is not None and note.owner_lane else lane_from_ref(pull.head_ref)
        rows.append(
            (
                pull,
                {
                    "number": pull.number,
                    "repo": view.repo,
                    "title": pull.title,
                    "draft": pull.draft,
                    "head_sha": pull.head_sha,
                    "epics": list(pull.epics),
                    "ci": ci,
                    "cf": cf,
                    "gate": gate,
                    "mq": queue,
                    "keeper": {"hold": hold, "reason": reason},
                    "flake_grant": _flake(drop_key, mq),
                    "ready_since": ready_since,
                    "stale_green": stale_green,
                    "minutes": minutes,
                    "stacked_base": None,
                    "hours_idle": idle,
                    "blocker": _plain_blocker(pull, cf, failed),
                    "owner_lane": owner,
                    "idle_24h": idle_24h,
                    "idle_48h": idle_48h,
                },
            )
        )
    by_head: dict[str, dict[str, Any]] = {}
    for pull, item in rows:
        by_head.setdefault(pull.head_ref, item)
    for pull, item in rows:
        item["stacked_base"] = _stacked(pull, by_head, view.default_branch)
        if pull.base_ref != "main":
            item["blocker"] = _stacked_blocker(pull, by_head, recorded.get(pull.number))
            item["ready_since"] = None
            item["stale_green"] = False
            item["minutes"] = None
    return [item for _pull, item in rows]


def _github_report(view: GithubView) -> SourceReport:
    if view.failed:
        return report(GITHUB_SOURCE, "unavailable")
    if view.stale:
        return report(GITHUB_SOURCE, "stale", age_s=view.age_s)
    return report(GITHUB_SOURCE, "ok", age_s=view.age_s)


def collect_pipeline(
    *,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], tuple[SourceReport, ...], tuple[ThroughputEvent, ...]]:
    moment = now or utc_now()
    mq_report, mq = read_mq_state(environ, now=moment)
    stale_report, stale = read_stale_state(environ, now=moment)
    activity = stale.activity if stale.usable else {}
    events = stale.events if stale.usable else ()
    repo = resolve_repo(environ)
    if repo is None:
        return [], (report(GITHUB_SOURCE, "not_configured"), mq_report, stale_report), events
    try:
        view = load_github_view(repo, environ=environ)
    except GithubReadError:
        return [], (report(GITHUB_SOURCE, "unavailable"), mq_report, stale_report), events
    rows = assemble_prs(view, mq, now=moment, stale_min=stale_after_min(environ), activity=activity)
    return rows, (_github_report(view), mq_report, stale_report), events


def _epic_key(value: str) -> str:
    text = value.strip().casefold()
    if text.startswith("epic:"):
        text = text[5:]
    return text


def _matches_epic(row: Mapping[str, Any], epic: str) -> bool:
    wanted = _epic_key(epic)
    if not wanted:
        return True
    return any(_epic_key(token) == wanted for token in row.get("epics", []))


def _matches_state(row: Mapping[str, Any], state: str) -> bool:
    if state == "open":
        return True
    if state in {"stale", "stale_green"}:
        return row.get("stale_green") is True
    if state == "held":
        keeper = row.get("keeper")
        return isinstance(keeper, Mapping) and keeper.get("hold") is True
    if state in {"red", "green", "pending"}:
        return row.get("ci") == state
    if state in {"queued", "not_queued", "dropped"}:
        return row.get("mq") == state
    return False


def filter_prs(
    rows: list[dict[str, Any]],
    *,
    epic: str | None = None,
    state: str | None = None,
) -> list[dict[str, Any]]:
    selected = rows
    if epic is not None and epic.strip():
        selected = [row for row in selected if _matches_epic(row, epic)]
    if state is not None and state.strip():
        token = state.strip().casefold()
        if token not in _STATE_FILTERS:
            return []
        selected = [row for row in selected if _matches_state(row, token)]
    return selected


def _pipeline_sources() -> tuple[SourceReport, SourceReport, SourceReport]:
    return (
        report(GITHUB_SOURCE, "unavailable"),
        report(MQ_SOURCE, "unavailable"),
        report("stale_prs", "unavailable"),
    )


def _safe_body(name: str, data: dict[str, Any]) -> dict[str, Any]:
    try:
        return envelope(name, data, _pipeline_sources())
    except Exception:
        return {
            "schema": f"fleet.v1.{name}",
            "generated_at": "1970-01-01T00:00:00Z",
            "sources": [item.as_dict() for item in _pipeline_sources()],
            "data": data,
        }


def read_prs(*, epic: str | None = None, state: str | None = None) -> dict[str, Any]:
    try:
        rows, sources, _events = collect_pipeline()
        return envelope("prs", {"prs": filter_prs(rows, epic=epic, state=state)}, sources)
    except Exception:
        return _safe_body("prs", {"prs": []})


def read_pr(number: int) -> dict[str, Any]:
    try:
        rows, sources, _events = collect_pipeline()
        found = next((row for row in rows if row["number"] == number), None)
        return envelope("pr", {"pr": found}, sources)
    except Exception:
        return _safe_body("pr", {"pr": None})


def read_now() -> dict[str, Any]:
    try:
        rows, sources, _events = collect_pipeline()
        return envelope("now", {"attention": attention_rows(rows)}, sources)
    except Exception:
        return _safe_body("now", {"attention": []})


def read_stats() -> dict[str, Any]:
    try:
        moment = utc_now()
        rows, sources, events = collect_pipeline(now=moment)
        return envelope("stats", build_stats(rows, events, now=moment), sources)
    except Exception:
        return _safe_body("stats", {"window_days": 14, "by_repo": [], "by_lane": []})
