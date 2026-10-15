"""Per-caller GitHub request counters and the landing-first budget guard (#10730, #10660).

Store: one SQLite database, :data:`COUNTER_DB` next to the client cache, in WAL
mode. The client (``scripts.common.github_client``) adds each sent request with
one ``INSERT ... ON CONFLICT DO UPDATE SET count = count + n`` in one
``BEGIN IMMEDIATE`` transaction (:func:`record`), so writers in any number of
processes serialize inside SQLite and none can overwrite another's increment. A
writer waits at most :data:`WRITE_BUSY_MS` for the lock; when the store stays
locked or cannot be written, that count is dropped and the client reports
``counter_degraded`` instead of failing or delaying the request. Counting never
touches the cache database. A row holds only the hour bucket, the rate-limit pool
(``core``, ``graphql`` or ``search``), a bounded caller tag, the count and the
last rate-limit headers seen.

Count boundary: a request is counted as soon as it is known to have left the
process, before the client parses or stores anything else, so a crash after that
point keeps the count and a request that never left counts nothing.
In-process transport: when the transport call returns, or raises an error that
only happens after sending (a timeout or a dropped connection); a refusal before
that (DNS, connection refused, any local error) counts nothing. ``gh`` process:
after it exits, one count per request in gh's own request log (``GH_DEBUG``; the
client turns on its summary form when the caller has not) that got past
connecting. gh logs a request before sending it, so ``--paginate`` logs every
page it asked for, a request cut off by a timeout still shows, and a run gh
rejected before any request (an unknown flag, missing credentials) logs none.

Guard policy: the client classifies a call as landing first. Landing calls (an
allowlist by operation: merge, enqueue, update-branch, review, verdict comments
and their readback, commit statuses, CI status, rerun of failed jobs, credential
lifecycle and the free ``rate_limit`` probe) always go to GitHub, at any
remaining budget including zero and unknown. Only non-landing calls are gated:
the client's own exhaustion gate first, then, while the ``core`` pool of the
credential scope has fewer than :data:`LANDING_RESERVE` calls left and its reset
is still ahead, a typed, value-free refusal (:func:`admit`). An unknown budget (no
row, or an expired window) refuses nothing. An optional per-caller soft cap, read
from a file that does not ship, refuses only the capped caller's non-landing
calls. The client never sleeps: a refusal is an exception the caller may retry
after ``reset_at``.

Report: ``.venv/bin/python -m scripts.common.github_budget_counters report``.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import functools
import json
import logging
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from scripts.lib.readonly_sqlite import open_readonly

LANDING_RESERVE = 500
RETENTION_SECONDS = 7 * 24 * 3600
HOUR = 3600
RESOURCES = ("core", "graphql", "search")
UNKNOWN_CALLER = "unknown"
CALLER_MAX_LENGTH = 64
CALLER_PATTERN = re.compile(r"[a-z0-9][a-z0-9._:-]{0,63}")
REASON_CORE_RESERVE = "core_below_landing_reserve"
REASON_SOFT_CAP = "caller_soft_cap"
SOFT_CAP_FILE = "caller-soft-caps.json"
SOFT_CAP_ENV = "LU_GITHUB_SOFT_CAP_FILE"
COUNTER_DB = "counters.sqlite3"
WRITE_BUSY_MS = 250  # the longest one count waits for the store's write lock before it is dropped

logger = logging.getLogger(__name__)

SCHEMA = """CREATE TABLE IF NOT EXISTS caller_counter (
    hour INTEGER NOT NULL,
    resource TEXT NOT NULL,
    caller TEXT NOT NULL,
    count INTEGER NOT NULL,
    last_remaining INTEGER,
    last_reset INTEGER,
    PRIMARY KEY(hour, resource, caller)
)"""

# --- caller identity -------------------------------------------------------------------

_process_caller: str | None = None


def valid_caller(tag) -> str:
    """Return ``tag`` when it is a bounded, lower-case identifier, else the fixed ``unknown``."""
    if isinstance(tag, str) and CALLER_PATTERN.fullmatch(tag):
        return tag
    return UNKNOWN_CALLER


def set_process_caller(tag) -> None:
    """Name this process once; an entry point calls it before its first GitHub request."""
    global _process_caller
    _process_caller = valid_caller(tag)


def process_caller() -> str | None:
    """The tag set by :func:`set_process_caller`, or ``None``."""
    return _process_caller


def derived_caller() -> str:
    """Default tag from the entry module or script name; never from request content."""
    main = sys.modules.get("__main__")
    spec = getattr(main, "__spec__", None)
    name = getattr(spec, "name", None) or Path(sys.argv[0] if sys.argv and sys.argv[0] else "").stem
    name = re.sub(r"(?:\.__main__)$", "", str(name)).lower()
    name = re.sub(r"[^a-z0-9._:-]+", "_", name).strip("._:-")[:CALLER_MAX_LENGTH]
    return valid_caller(name)


def resolve_caller(explicit=None) -> str:
    """Explicit tag, else the process tag, else the entry-module default; invalid becomes ``unknown``."""
    if explicit is not None:
        return valid_caller(explicit)
    return _process_caller or derived_caller()


def count_resource(bucket: str) -> str:
    """Fold a rate-limit bucket into the three counted pools (code search counts as search)."""
    return bucket if bucket in RESOURCES else "search" if bucket.endswith("search") else "core"


# --- landing classification ------------------------------------------------------------

_OPERATION: contextvars.ContextVar[str | None] = contextvars.ContextVar("github_operation", default=None)

# Named operations that exist only to land a PR; every request inside one is landing. The
# publisher's landing verbs (their readiness and recovery reads included) and named reads (see
# scripts.publish.github), the client's CI status reads (``gh pr checks``, ``gh pr view
# --json statusCheckRollup``), whose pull-request lookup is not landing on its own, and the
# landing flows that declare themselves with :func:`landing_flow`: the merge-queue keeper's
# cycle and verdict publication (their identity, pull-request and commit reads included).
CI_STATUS = "ci-status"
LANDING_VERBS = frozenset({"pr-merge", "pr-update-branch", "pr-review", "run-rerun"})
LANDING_FLOWS = frozenset({"merge-queue-keeper", "verdict-publication"})
LANDING_OPERATIONS = (
    LANDING_VERBS
    | LANDING_FLOWS
    | {
        "queue-snapshot",
        "queue-status",
        "queue-removal",
        "merge-facts",
        "budget",
        CI_STATUS,
    }
)

_REPO = r"repos/[^/]+/[^/]+/"
_LANDING_REST = (
    ("GET", re.compile(_REPO + r"pulls/\d+/reviews")),
    ("POST", re.compile(_REPO + r"pulls/\d+/reviews")),
    ("POST", re.compile(_REPO + r"pulls/\d+/reviews/\d+/events")),
    ("PUT", re.compile(_REPO + r"pulls/\d+/merge")),
    ("PUT", re.compile(_REPO + r"pulls/\d+/update-branch")),
    # Verdict publication and its readback: a verdict is an issue comment on the PR, and
    # recovery/verdict flows read comments, one comment and the timeline back.
    ("POST", re.compile(_REPO + r"issues/\d+/comments")),
    ("GET", re.compile(_REPO + r"issues/\d+/comments")),
    ("GET", re.compile(_REPO + r"issues/comments/\d+")),
    ("GET", re.compile(_REPO + r"issues/\d+/timeline")),
    # Commit-status write (the CF verdict's status line); reading statuses is listed below.
    ("POST", re.compile(_REPO + r"statuses/[^/]+")),
    ("GET", re.compile(_REPO + r"commits/[^/]+/(?:check-runs|check-suites|status|statuses)")),
    ("GET", re.compile(_REPO + r"check-suites/\d+/check-runs")),
    ("GET", re.compile(_REPO + r"check-runs/\d+")),
    ("POST", re.compile(_REPO + r"check-runs/\d+/rerequest")),
    ("GET", re.compile(_REPO + r"actions/runs/\d+")),
    ("GET", re.compile(_REPO + r"actions/runs/\d+/jobs")),
    ("GET", re.compile(_REPO + r"actions/jobs/\d+")),
    ("POST", re.compile(_REPO + r"actions/runs/\d+/rerun-failed-jobs")),
    ("POST", re.compile(_REPO + r"actions/jobs/\d+/rerun")),
    ("GET", re.compile(r"rate_limit")),
    # Credential lifecycle: a worker must be able to mint and drop its token to land at all.
    ("POST", re.compile(r"app/installations/\d+/access_tokens")),
    ("DELETE", re.compile(r"installation/token")),
)
_LANDING_GRAPHQL = re.compile(
    r"\b(?:enqueuePullRequest|dequeuePullRequest|enablePullRequestAutoMerge|disablePullRequestAutoMerge"
    r"|mergePullRequest|addPullRequestReview|submitPullRequestReview"
    r"|mergeQueue|isInMergeQueue|isMergeQueueEnabled|mergeQueueEntry|REMOVED_FROM_MERGE_QUEUE_EVENT)\b"
)
# ``gh`` subcommands that fall through natively and exist to land a PR. A bare
# ``run rerun`` re-runs everything, so only its ``--failed`` form is landing.
_LANDING_NATIVE = frozenset({("pr", "merge"), ("pr", "review"), ("pr", "checks"), ("run", "view")})


@contextlib.contextmanager
def operation(name):
    """Mark the requests issued inside as one named operation; inside a landing operation they stay landing."""
    current = _OPERATION.get()
    token = _OPERATION.set(current if current in LANDING_OPERATIONS else name)
    try:
        yield
    finally:
        _OPERATION.reset(token)


def is_landing(method, resource_path, graphql_query=None) -> bool:
    """True for an allowlisted landing call. Anything unrecognised is non-landing."""
    if _OPERATION.get() in LANDING_OPERATIONS:
        return True
    if resource_path == "graphql":
        return isinstance(graphql_query, str) and _LANDING_GRAPHQL.search(graphql_query) is not None
    if not isinstance(resource_path, str):
        return False
    method = str(method).upper()
    return any(verb == method and shape.fullmatch(resource_path) for verb, shape in _LANDING_REST)


def landing_flow(name):
    """Decorator: every GitHub request the decorated function makes is landing traffic.

    ``name`` must be one of :data:`LANDING_FLOWS`; the wrapper records it as ``landing_flow``.
    """
    if name not in LANDING_FLOWS:
        raise ValueError(f"unknown landing flow: {name}")

    def decorate(function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            with operation(name):
                return function(*args, **kwargs)

        wrapped.landing_flow = name
        return wrapped

    return decorate


def is_ci_status_view(arguments) -> bool:
    """True for ``gh pr view`` arguments that read the PR's CI status (``statusCheckRollup``)."""
    return any("statusCheckRollup" in str(argument) for argument in arguments)


def native_is_landing(args, api_landing=None) -> bool:
    """Classify a native ``gh`` argv; ``api_landing`` is the verdict for ``gh api`` shapes."""
    if _OPERATION.get() in LANDING_OPERATIONS:
        return True
    words = tuple(str(a) for a in args[1:3])
    if words == ("run", "rerun"):
        return "--failed" in args[3:]
    if words == ("pr", "view"):
        return is_ci_status_view(args[3:])
    if words[:1] == ("api",):
        return bool(api_landing)
    return words in _LANDING_NATIVE


# --- storage ---------------------------------------------------------------------------


def hour_start(now) -> int:
    return int(now // HOUR) * HOUR


def store_path(cache_dir) -> Path | None:
    """The counter database of a client cache directory; ``None`` when the client has no disk cache."""
    return Path(cache_dir) / COUNTER_DB if cache_dir is not None else None


def prepare(db) -> None:
    """Make a fresh writer connection bounded, WAL and schema-ready; nothing here waits longer than the bound."""
    db.isolation_level = None  # explicit transactions only: one BEGIN IMMEDIATE per count
    db.execute(f"PRAGMA busy_timeout={WRITE_BUSY_MS}")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")  # a committed count survives the process being killed
    db.execute(SCHEMA)


def _rate_headers(headers) -> tuple[int | None, int | None]:
    lowered = {str(key).lower(): value for key, value in (headers or {}).items()}
    try:
        return int(lowered["x-ratelimit-remaining"]), int(lowered["x-ratelimit-reset"])
    except (KeyError, TypeError, ValueError):
        return None, None


def record(db, now, resource, caller, requests=1, headers=None) -> None:
    """Add ``requests`` sent requests to this hour's bucket, in one transaction, and drop expired buckets.

    The last rate-limit headers seen (when ``headers`` carries them) are kept on the same row.
    """
    remaining, reset = _rate_headers(headers)
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute(
            """INSERT INTO caller_counter(hour,resource,caller,count,last_remaining,last_reset) VALUES(?,?,?,?,?,?)
            ON CONFLICT(hour,resource,caller) DO UPDATE SET count=count+excluded.count,
            last_remaining=coalesce(excluded.last_remaining,last_remaining),
            last_reset=coalesce(excluded.last_reset,last_reset)""",
            (hour_start(now), resource, caller, int(requests), remaining, reset),
        )
        db.execute("DELETE FROM caller_counter WHERE hour<?", (hour_start(now - RETENTION_SECONDS),))
        db.execute("COMMIT")
    except BaseException:
        with contextlib.suppress(sqlite3.Error):
            db.execute("ROLLBACK")
        raise


def current_count(db, now, resource, caller) -> int:
    row = db.execute(
        "SELECT count FROM caller_counter WHERE hour=? AND resource=? AND caller=?",
        (hour_start(now), resource, caller),
    ).fetchone()
    return row[0] if row else 0


def hourly_count(path, now, resource, caller) -> int:
    """This hour's count for one caller and pool, read only; a missing or unreadable store reads as 0."""
    if path is None or not Path(path).is_file():
        return 0
    try:
        db = open_readonly(path)
    except sqlite3.Error:
        return 0
    try:
        return current_count(db, now, resource, caller)
    except sqlite3.Error:
        return 0
    finally:
        db.close()


# --- soft cap --------------------------------------------------------------------------

_soft_cap_cache: dict = {}


def soft_cap_path(cache_dir) -> Path | None:
    override = os.environ.get(SOFT_CAP_ENV)
    if override:
        return Path(override)
    return Path(cache_dir) / SOFT_CAP_FILE if cache_dir is not None else None


def load_soft_caps(cache_dir) -> dict:
    """Return ``{caller: {resource: hourly_limit}}``; empty unless the file exists and enables it.

    File shape: ``{"enabled": true, "hourly_caps": {"<caller>": {"core": 300}}}``. The file
    does not ship, so the cap is disabled. A malformed file also disables it.
    """
    path = soft_cap_path(cache_dir)
    if path is None:
        return {}
    try:
        stat = path.stat()
    except OSError:
        return {}
    stamp = (str(path), stat.st_mtime_ns, stat.st_size)
    if stamp in _soft_cap_cache:
        return _soft_cap_cache[stamp]
    caps: dict = {}
    with contextlib.suppress(OSError, ValueError):
        document = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and document.get("enabled") is True:
            declared = document.get("hourly_caps")
            for caller, pools in (declared if isinstance(declared, dict) else {}).items():
                if valid_caller(caller) == caller and isinstance(pools, dict):
                    valid = {
                        pool: limit
                        for pool, limit in pools.items()
                        if pool in RESOURCES and type(limit) is int and limit >= 0
                    }
                    if valid:
                        caps[caller] = valid
    _soft_cap_cache.clear()
    _soft_cap_cache[stamp] = caps
    return caps


# --- guard -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Refusal:
    """A typed, value-free refusal: a fixed reason code and when to retry."""

    reason: str
    reset_at: int | None


def admit(db, *, scope, now, resource, caller, soft_caps=None, used=None) -> Refusal | None:
    """Refuse a non-landing request below the reserve or over its soft cap, else return ``None``.

    The client calls this only for calls it already classified as non-landing, so a
    landing call never reaches it. ``db`` is the client's cache database (its ``budget``
    table); ``used()`` returns the caller's count for this hour and pool, and is read
    only when a soft cap applies. Nothing is counted here. The core reserve only gates
    calls that spend the core pool (graphql and search have their own pools, as the
    client's per-bucket gate already assumes). Every storage error fails open: missing
    telemetry never starves a call. ``resource`` is a rate-limit bucket; it is folded
    into the counted pools.
    """
    pool = count_resource(resource)
    try:
        row = (
            db.execute("SELECT remaining,reset FROM budget WHERE scope=? AND resource='core'", (scope,)).fetchone()
            if pool == "core"
            else None
        )
        if row is not None and row[1] > now and row[0] < LANDING_RESERVE:
            return Refusal(REASON_CORE_RESERVE, row[1])
        limit = (soft_caps or {}).get(caller, {}).get(pool)
        if limit is not None and used is not None and used() >= limit:
            return Refusal(REASON_SOFT_CAP, hour_start(now) + HOUR)
    except sqlite3.Error:
        return None
    return None


# --- report ----------------------------------------------------------------------------


def top_callers(db, hour, resource, limit=10) -> list[dict]:
    """Callers of one pool in one hour bucket, busiest first (ties by name); counts only."""
    if db is None:
        return []
    rows = db.execute(
        "SELECT caller,count FROM caller_counter WHERE hour=? AND resource=? ORDER BY count DESC,caller LIMIT ?",
        (hour, resource, limit),
    ).fetchall()
    return [{"caller": caller, "count": count} for caller, count in rows]


def remaining_budget(db, now) -> dict:
    """Lowest live remaining per pool across credential scopes; only counts and a reset time."""
    out = {}
    if db is None:
        return out
    for resource, remaining, reset in db.execute(
        "SELECT resource,min(remaining),max(reset) FROM budget WHERE reset>? AND resource IN (?,?,?) GROUP BY resource",
        (now, *RESOURCES),
    ):
        out[resource] = {"remaining": remaining, "reset_at": reset}
    return out


def build_report(counts_db, budget_db, now, *, limit=10) -> dict:
    """Top callers for the current and previous hour, per pool, with the remaining budget.

    ``counts_db`` is the counter store and ``budget_db`` the client cache; ``None`` (or a
    database without the table) reads as empty.
    """
    current = hour_start(now)
    windows = {}
    for label, hour in (("current", current), ("previous", current - HOUR)):
        resources = {}
        for resource in RESOURCES:
            try:
                resources[resource] = top_callers(counts_db, hour, resource, limit)
            except sqlite3.Error:
                resources[resource] = []
        windows[label] = {"hour_start": hour, "resources": resources}
    try:
        budget = remaining_budget(budget_db, now)
    except sqlite3.Error:
        budget = {}
    return {"schema": "github-budget-callers.v1", "generated_at": int(now), "windows": windows, "budget": budget}


def _open_existing(path):
    """Read-only handle on an existing database, or ``None`` when there is none or it cannot be opened."""
    if path is None or not Path(path).is_file():
        return None
    try:
        return open_readonly(path)
    except sqlite3.Error:
        return None


def report_for(cache_dir, now=None, *, limit=10) -> dict:
    """Report from a client cache directory; missing databases or tables are an empty report."""
    now = time.time() if now is None else now
    counts_db = _open_existing(store_path(cache_dir))
    budget_db = _open_existing(Path(cache_dir) / "cache.sqlite3" if cache_dir is not None else None)
    try:
        return build_report(counts_db, budget_db, now, limit=limit)
    finally:
        for db in (counts_db, budget_db):
            if db is not None:
                db.close()


def _render(report) -> str:
    lines = []
    for label in ("current", "previous"):
        window = report["windows"][label]
        stamp = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(window["hour_start"]))
        lines.append(f"{label} hour from {stamp}")
        for resource in RESOURCES:
            budget = report["budget"].get(resource)
            left = f" (remaining {budget['remaining']})" if budget else ""
            lines.append(f"  {resource}{left}")
            lines.extend(f"    {row['count']:>7}  {row['caller']}" for row in window["resources"][resource])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.common.github_budget_counters",
        description=(
            "Show which callers spent the shared GitHub API budget in the current and previous hour.\n"
            "Use it when core remaining runs low; it only reads and never changes the database."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.common.github_budget_counters report\n"
            "  .venv/bin/python -m scripts.common.github_budget_counters report --limit 3 --json\n\n"
            "Outputs: a table (or JSON) of counts per pool and caller; no URLs, bodies or tokens.\n"
            "Exit codes: 0 report printed (empty when nothing was recorded); 2 usage error.\n"
            "Related: scripts/common/github_client.py; GET /api/github-budget/callers; issues #10730, #10660."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="print top callers per pool for the current and previous hour")
    report.add_argument("--limit", type=int, default=10, help="callers shown per pool and hour (default 10; e.g. 3)")
    report.add_argument("--json", action="store_true", help="print the JSON report the Ops API serves (default off)")
    report.add_argument("--cache-dir", default=None, help="client database directory (default: the shared client's)")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    from scripts.common import github_client

    cache_dir = Path(args.cache_dir) if args.cache_dir else github_client._cache_directory()
    document = report_for(cache_dir, limit=args.limit)
    print(json.dumps(document, indent=2) if args.json else _render(document))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
