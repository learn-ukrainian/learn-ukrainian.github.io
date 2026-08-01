"""Issue-stream auditor — every open GH issue must belong to exactly one stream epic.

Registry: scripts/config/issue_streams.yaml (streams → epic issue numbers).
Membership: native GitHub sub-issue of a stream epic, OR (fallback while the
native migration is pending) a ``#N`` reference in a stream epic's body.

Usage:
  .venv/bin/python -m scripts.orchestration.issue_stream_audit           # human summary
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --json    # machine output
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --check   # exit 1 on orphans
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --from-cache --max-age 3600
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --migrate # body refs → native sub-issues

Cache: batch_state/issue_stream_audit.json (gitignored runtime state) — written on
every live run; the session-setup hook and /api/state/issues-health read it.

GH incident #4708: manual epic checklists rot (fixed-but-open issues, auto-closed
issues orphaning scope). This gate makes drift visible at every cold start.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import math
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import yaml

from scripts.api.config import LIVE_REPO_ROOT

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "scripts" / "config" / "issue_streams.yaml"
CACHE_PATH = ROOT / "batch_state" / "issue_stream_audit.json"
ISSUE_REF_RE = re.compile(r"#(\d{2,6})\b")

# ADR-011 P4 — private keys added to the cache report for the strict adoption
# gate/observability. They carry an exact effective issue→epic membership index
# and the bounded open-issue set; both are stripped from the public
# ``/api/issues/streams`` response (see ``issues_router.strip_private_index``).
PRIVATE_CACHE_KEYS = ("effective_membership", "open_issue_numbers")

# A resolver proving issue N is a live child of stream epic E, offline, from a
# fresh cache. Signature mirrors P1's ``check_research_registry.MembershipResolver``.
MembershipResolver = Callable[[int, int], bool]

# --------------------------------------------------------------------------- #
# #6145 — truthful refresh state sidecar (#4707).
#
# The refresh worker is explicitly detached and single-flight for both the
# stale-fallback and ``?fresh=true`` paths. Runtime-only state lives in two
# gitignored sidecars under ``batch_state/``:
#
#   REFRESH_STATE_PATH — JSON state machine (phase, outcome, cooldown, …)
#   REFRESH_LOCK_PATH  — cross-process ``flock`` advisory lock
#
# The scheduler takes the lock, atomically writes ``scheduled`` with a fresh
# opaque ``run_id``, spawns the worker, and releases. The worker acquires and
# HOLDS the lock for the entire audit, verifies ``run_id``, writes ``running``,
# then atomically writes the terminal outcome before release. A stale ``run_id``
# can never overwrite a newer run. A scheduled worker that never starts or a
# ``running`` state observed with a free lock is reconciled to
# ``failed/worker_lost`` after a short deterministic grace.
# --------------------------------------------------------------------------- #
REFRESH_STATE_PATH = ROOT / "batch_state" / "issue_stream_audit_refresh.json"
REFRESH_LOCK_PATH = ROOT / "batch_state" / "issue_stream_audit_refresh.lock"

# Grace for the spawn→acquire race: the scheduler writes ``scheduled``, spawns
# the worker, and releases the lock. The worker subprocess then acquires it.
# During that gap a concurrent ``read_refresh_state`` may briefly observe
# ``scheduled`` — it must not immediately reconcile to ``worker_lost``.
SCHEDULED_GRACE_S = 15

# Deterministic cooldown after an automatic failure: default/stale requests
# will not re-schedule until this many seconds have elapsed. Explicit
# ``?fresh=true`` bypasses the cooldown but is still single-flight.
FAILURE_COOLDOWN_S = 60

_VALID_PHASES = ("idle", "scheduled", "running")
_VALID_OUTCOMES = ("none", "succeeded", "failed")
_VALID_FAILURE_CODES = (
    "spawn_failed",
    "worker_lost",
    "source_unavailable",
    "source_timeout",
    "source_error",
    "cache_write_failed",
    "audit_failed",
)


# --------------------------------------------------------------------------- #
# #6145 — refresh state machine: validation, atomic I/O, locking
# --------------------------------------------------------------------------- #
def _default_refresh_state() -> dict:
    """The canonical idle state used when the sidecar is missing or malformed."""
    return {
        "schema_version": 1,
        "run_id": None,
        "phase": "idle",
        "requested_at": None,
        "started_at": None,
        "last_outcome": "none",
        "last_outcome_at": None,
        "failure_code": None,
        "cooldown_until": None,
    }


def _is_finite_epoch(val: object) -> bool:
    """True for a real (non-bool) int/float >= 0 suitable as a UTC epoch."""
    return (
        isinstance(val, (int, float))
        and not isinstance(val, bool)
        and math.isfinite(val)
        and val >= 0
    )


def _validate_refresh_state(raw: object) -> dict | None:
    """Structurally + semantically validate the raw sidecar payload.

    Returns a normalized dict on success, or ``None`` when the payload is
    malformed — the caller MUST treat ``None`` as ``_default_refresh_state()``.
    A malformed/missing sidecar never claims active work.
    """
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        return None
    phase = raw.get("phase")
    if phase not in _VALID_PHASES:
        return None
    outcome = raw.get("last_outcome", "none")
    if outcome not in _VALID_OUTCOMES:
        return None
    failure_code = raw.get("failure_code")
    if failure_code is not None and failure_code not in _VALID_FAILURE_CODES:
        return None
    run_id = raw.get("run_id")
    if run_id is not None and not (isinstance(run_id, str) and run_id):
        return None
    requested_at = raw.get("requested_at")
    started_at = raw.get("started_at")
    last_outcome_at = raw.get("last_outcome_at")
    cooldown_until = raw.get("cooldown_until")
    for val in (requested_at, started_at, last_outcome_at, cooldown_until):
        if val is not None and not _is_finite_epoch(val):
            return None
    normalized = {
        "schema_version": 1,
        "run_id": run_id if isinstance(run_id, str) else None,
        "phase": phase,
        "requested_at": requested_at if _is_finite_epoch(requested_at) else None,
        "started_at": started_at if _is_finite_epoch(started_at) else None,
        "last_outcome": outcome,
        "last_outcome_at": last_outcome_at if _is_finite_epoch(last_outcome_at) else None,
        "failure_code": failure_code if failure_code in _VALID_FAILURE_CODES else None,
        "cooldown_until": cooldown_until if _is_finite_epoch(cooldown_until) else None,
    }
    if phase == "idle":
        if (
            normalized["run_id"] is not None
            or normalized["requested_at"] is not None
            or normalized["started_at"] is not None
        ):
            return None
    elif normalized["run_id"] is None or normalized["requested_at"] is None:
        return None
    if phase == "scheduled" and normalized["started_at"] is not None:
        return None
    if phase == "running" and normalized["started_at"] is None:
        return None
    if outcome == "none":
        if normalized["last_outcome_at"] is not None or failure_code is not None:
            return None
    elif normalized["last_outcome_at"] is None:
        return None
    if outcome == "failed" and failure_code is None:
        return None
    if outcome != "failed" and failure_code is not None:
        return None
    if outcome != "failed" and normalized["cooldown_until"] is not None:
        return None
    return normalized


def _read_refresh_state_raw() -> object | None:
    """Read the raw sidecar JSON (fail-safe to ``None``)."""
    try:
        return json.loads(REFRESH_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_refresh_state_atomic(state: dict) -> None:
    """Atomically replace the sidecar via temp-file + ``os.replace``.

    The temp file lives in the same directory so ``os.replace`` is an atomic
    rename on the same filesystem. A crash mid-write leaves the previous
    state intact; a reader never observes partial JSON.
    """
    REFRESH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(state, ensure_ascii=False)
    fd, tmp = tempfile.mkstemp(
        dir=str(REFRESH_STATE_PATH.parent),
        prefix=".issue_stream_audit_refresh.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(REFRESH_STATE_PATH))
    except Exception:
        if fd >= 0:
            with contextlib.suppress(OSError):
                os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# --------------------------------------------------------------------------- #
# Cross-process locking (``flock`` — advisory, macOS/Linux)
# --------------------------------------------------------------------------- #
def _try_lock_nb() -> int | None:
    """Non-blocking ``LOCK_EX`` acquire. Returns an fd on success, ``None``
    when the lock is held by another process (or the file can't be opened)."""
    fd: int | None = None
    try:
        REFRESH_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(REFRESH_LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o600)
        os.fchmod(fd, 0o600)
    except OSError:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (BlockingIOError, OSError):
        with contextlib.suppress(OSError):
            os.close(fd)
        return None


def _release_lock(fd: int) -> None:
    with contextlib.suppress(OSError):
        fcntl.flock(fd, fcntl.LOCK_UN)
    with contextlib.suppress(OSError):
        os.close(fd)


def _acquire_lock_blocking(timeout_s: float) -> int | None:
    """Bounded blocking acquire of the refresh lock.

    The scheduler releases the lock immediately after spawning the worker, so
    the worker should acquire it within milliseconds. A bounded retry avoids
    an indefinite hang if the scheduler crashed while holding the lock.
    """
    deadline = time.monotonic() + timeout_s
    while True:
        fd = _try_lock_nb()
        if fd is not None:
            return fd
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.05)


# --------------------------------------------------------------------------- #
# Reconciliation
# --------------------------------------------------------------------------- #
def _apply_worker_lost(state: dict, *, failure_at: float) -> None:
    """Mutate ``state`` in place to a terminal ``worker_lost`` outcome."""
    fail_ts = int(failure_at)
    state["phase"] = "idle"
    state["run_id"] = None
    state["requested_at"] = None
    state["started_at"] = None
    state["last_outcome"] = "failed"
    state["failure_code"] = "worker_lost"
    state["last_outcome_at"] = fail_ts
    state["cooldown_until"] = fail_ts + FAILURE_COOLDOWN_S


def _reconcile_state(raw: dict, *, now: float, lock_is_free: bool) -> dict:
    """Compute the effective state.

    ``lock_is_free=True``: the caller already holds the refresh lock (scheduler
    or worker context). Any ``running`` state is inherently stale because the
    caller has the lock the worker would need — reconcile without probing.

    ``lock_is_free=False``: another process owns the lock, so a valid active
    state is left unchanged.
    """
    state = dict(raw)
    phase = state.get("phase", "idle")

    if phase == "scheduled":
        requested_at = state.get("requested_at")
        if _is_finite_epoch(requested_at) and now - requested_at > SCHEDULED_GRACE_S:
            _apply_worker_lost(state, failure_at=int(requested_at + SCHEDULED_GRACE_S))

    elif phase == "running" and lock_is_free:
        _apply_worker_lost(state, failure_at=int(now))

    cooldown = state.get("cooldown_until")
    if _is_finite_epoch(cooldown) and now >= cooldown:
        state["cooldown_until"] = None

    return state


# --------------------------------------------------------------------------- #
# Public read + view
# --------------------------------------------------------------------------- #
def read_refresh_state(*, now: float | None = None) -> dict:
    """Read, validate, and reconcile the refresh state. Fail-safe to idle.

    This is the bounded state-observation path used by the router for
    cache-hit responses. It takes the cross-process lock only long enough to
    reconcile and, when possible, persist a lost-worker or expired-cooldown
    transition.
    """
    t = now if now is not None else time.time()
    fd = _try_lock_nb()
    if fd is None:
        raw = _validate_refresh_state(_read_refresh_state_raw())
        return raw if raw is not None else _default_refresh_state()
    try:
        raw = _validate_refresh_state(_read_refresh_state_raw())
        if raw is None:
            return _default_refresh_state()
        reconciled = _reconcile_state(raw, now=t, lock_is_free=True)
        if reconciled != raw:
            # The observed projection remains truthful even if a filesystem
            # fault prevents persisting reconciliation. The next scheduler
            # will retry under the same lock and report a bounded API error if
            # it cannot persist a new run.
            with contextlib.suppress(OSError):
                _write_refresh_state_atomic(reconciled)
        return reconciled
    finally:
        _release_lock(fd)


def public_refresh_view(state: dict) -> dict:
    """Build the public ``refresh`` contract from internal state.

    Never exposes ``run_id``, ``schema_version``, lock paths, PID, exception
    text, or any internal detail. ``retry_after`` maps to the internal
    ``cooldown_until``.
    """
    return {
        "phase": state.get("phase", "idle"),
        "requested_at": state.get("requested_at"),
        "started_at": state.get("started_at"),
        "last_outcome": state.get("last_outcome", "none"),
        "last_outcome_at": state.get("last_outcome_at"),
        "failure_code": state.get("failure_code"),
        "retry_after": state.get("cooldown_until"),
    }


# --------------------------------------------------------------------------- #
# Scheduler + worker
# --------------------------------------------------------------------------- #
def _venv_python() -> str:
    """Path to the live checkout's venv for the detached worker.

    The supervised API imports this module from an immutable release snapshot,
    which intentionally has no ``.venv``.  The supervisor-provided live root
    owns the approved interpreter while ``ROOT`` remains the worker's snapshot
    cwd so the detached process executes the exact deployed code.
    """
    return str(LIVE_REPO_ROOT / ".venv" / "bin" / "python")


def _spawn_worker(run_id: str) -> bool:
    """Spawn the detached refresh worker subprocess. Returns True on success."""
    try:
        subprocess.Popen(
            [
                _venv_python(),
                "-m", "scripts.orchestration.issue_stream_audit",
                "--refresh-worker", run_id,
            ],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        return True
    except OSError:
        return False


def _classify_failure(exc: Exception) -> str:
    """Map an audit exception to a failure code from the allowlist.

    ``FileNotFoundError``/``PermissionError`` (subclasses of ``OSError``) are
    checked before the generic ``OSError`` branch so a missing ``gh`` binary
    is classified as ``source_unavailable`` rather than ``cache_write_failed``.
    """
    if isinstance(exc, subprocess.TimeoutExpired):
        return "source_timeout"
    if isinstance(exc, (FileNotFoundError, PermissionError)):
        return "source_unavailable"
    if isinstance(exc, json.JSONDecodeError):
        return "source_error"
    if isinstance(exc, RuntimeError):
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            return "source_timeout"
        return "source_error"
    if isinstance(exc, OSError):
        return "cache_write_failed"
    return "audit_failed"


def schedule_refresh(*, force: bool = False) -> dict:
    """Single-flight refresh scheduler for both stale-fallback and
    ``?fresh=true`` paths.

    Takes the lock, atomically writes ``scheduled`` with a fresh opaque
    ``run_id``, spawns the detached worker, and releases. The worker then
    acquires and holds the lock for the entire audit.

    ``force=True`` (explicit ``?fresh=true``) bypasses the automatic cooldown
    but is still single-flight — an active run is observed, not duplicated.

    Returns the reconciled internal state *after* scheduling (or observing an
    active run). The caller builds the public view via
    :func:`public_refresh_view`.
    """
    now = time.time()
    fd = _try_lock_nb()
    if fd is None:
        # Lock held by a scheduler or worker — an active run is in progress.
        raw = _validate_refresh_state(_read_refresh_state_raw())
        if raw is None:
            raw = _default_refresh_state()
        return raw

    try:
        raw = _validate_refresh_state(_read_refresh_state_raw())
        if raw is None:
            raw = _default_refresh_state()
        reconciled = _reconcile_state(raw, now=now, lock_is_free=True)
        if reconciled != raw:
            _write_refresh_state_atomic(reconciled)

        # Active run in progress — the spawn→acquire race: the scheduler that
        # wrote ``scheduled`` released the lock, the worker hasn't acquired it
        # yet, and we briefly took it. Don't schedule another; the existing
        # run will proceed once we release.
        if reconciled["phase"] == "scheduled":
            return reconciled

        # ``running`` can't survive free-lock reconciliation.
        assert reconciled["phase"] == "idle"

        # Cooldown gate for automatic requests.
        cooldown = reconciled.get("cooldown_until")
        if not force and _is_finite_epoch(cooldown) and now < cooldown:
            return reconciled

        run_id = secrets.token_hex(8)
        ts = int(now)
        scheduled: dict = {
            "schema_version": 1,
            "run_id": run_id,
            "phase": "scheduled",
            "requested_at": ts,
            "started_at": None,
            "last_outcome": reconciled.get("last_outcome", "none"),
            "last_outcome_at": reconciled.get("last_outcome_at"),
            "failure_code": reconciled.get("failure_code")
            if reconciled.get("last_outcome") == "failed"
            else None,
            # A retry is now active, so an earlier terminal failure no longer
            # has a future retry gate even though its outcome remains visible.
            "cooldown_until": None,
        }
        _write_refresh_state_atomic(scheduled)

        if not _spawn_worker(run_id):
            fail_ts = int(time.time())
            scheduled.update(
                phase="idle",
                run_id=None,
                requested_at=None,
                last_outcome="failed",
                last_outcome_at=fail_ts,
                failure_code="spawn_failed",
                cooldown_until=fail_ts + FAILURE_COOLDOWN_S,
            )
            _write_refresh_state_atomic(scheduled)

        return scheduled
    finally:
        _release_lock(fd)


def _run_refresh_worker(run_id: str) -> int:
    """Detached refresh worker — invoked via ``--refresh-worker RUN_ID``.

    Acquires the lock (bounded retry for the spawn→acquire gap), verifies
    ``run_id``, writes ``running``, runs the full audit, and atomically
    writes the terminal outcome before releasing. A stale ``run_id`` (a newer
    scheduler superseded us) causes an immediate no-op exit.
    """
    fd = _acquire_lock_blocking(timeout_s=SCHEDULED_GRACE_S)
    if fd is None:
        return 1

    try:
        raw = _validate_refresh_state(_read_refresh_state_raw())
        if raw is None:
            raw = _default_refresh_state()
        # run_id mismatch → a newer run superseded us; do nothing.
        if raw.get("run_id") != run_id:
            return 0

        running = dict(raw)
        running["phase"] = "running"
        running["started_at"] = int(time.time())
        _write_refresh_state_atomic(running)

        try:
            run_audit()
        except Exception as exc:
            code = _classify_failure(exc)
            fail_ts = int(time.time())
            current = _validate_refresh_state(_read_refresh_state_raw())
            if current is None or current.get("run_id") != run_id:
                return 0
            _write_refresh_state_atomic({
                "schema_version": 1,
                "run_id": None,
                "phase": "idle",
                "requested_at": None,
                "started_at": None,
                "last_outcome": "failed",
                "last_outcome_at": fail_ts,
                "failure_code": code,
                "cooldown_until": fail_ts + FAILURE_COOLDOWN_S,
            })
            return 1

        current = _validate_refresh_state(_read_refresh_state_raw())
        if current is None or current.get("run_id") != run_id:
            return 0
        ok_ts = int(time.time())
        _write_refresh_state_atomic({
            "schema_version": 1,
            "run_id": None,
            "phase": "idle",
            "requested_at": None,
            "started_at": None,
            "last_outcome": "succeeded",
            "last_outcome_at": ok_ts,
            "failure_code": None,
            "cooldown_until": None,
        })
        return 0
    finally:
        _release_lock(fd)


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, list[int]]:
    """Return {stream_key: [epic_numbers]}."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    streams = doc.get("streams") or {}
    registry: dict[str, list[int]] = {}
    for key, spec in streams.items():
        epics = [int(n) for n in (spec.get("epics") or [])]
        if not epics:
            raise ValueError(f"stream {key!r} has no epics")
        registry[key] = epics
    if not registry:
        raise ValueError("issue_streams.yaml defines no streams")
    return registry


def _gh_json(args: list[str], timeout_s: float = 30.0, *, cwd: Path = ROOT):
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=timeout_s, cwd=cwd
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def fetch_open_issues(repo_root: Path = ROOT) -> list[dict]:
    return _gh_json(
        ["issue", "list", "--state", "open", "--limit", "500",
         "--json", "number,title"],
        cwd=repo_root,
    )


# Keyed by resolved repo root so a closeout invocation configured for one
# checkout never reuses another checkout's owner/name (a caller auditing two
# different worktrees in the same process must not cross-contaminate).
_REPO_CACHE: dict[str, tuple[str, str]] = {}


def _repo_owner_name(repo_root: Path = ROOT) -> tuple[str, str]:
    """Resolve the actual owner/name once per repo root — GraphQL -f fields do
    NOT expand the gh {owner}/{repo} placeholders (REST paths do). Caught by
    live probe."""
    key = str(repo_root)
    if key not in _REPO_CACHE:
        data = _gh_json(["repo", "view", "--json", "owner,name"], cwd=repo_root)
        _REPO_CACHE[key] = (data["owner"]["login"], data["name"])
    return _REPO_CACHE[key]


# GraphQL subIssues pagination (item 7, PR #4998 corrective pass): an "exact"
# authority cache must not silently truncate an epic's children at one page.
# Two separate query documents (rather than one query with a nullable $cursor)
# because ``gh api graphql`` always sends ``-f`` variables as strings, and an
# empty-string cursor is not the same as an omitted/null ``after`` argument to
# GitHub's API.
_SUBISSUES_FIRST_PAGE_QUERY = (
    "query=query($owner:String!,$name:String!,$number:Int!){"
    "repository(owner:$owner,name:$name){issue(number:$number){body "
    "subIssues(first:100){nodes{number} pageInfo{hasNextPage endCursor}}}}}"
)
_SUBISSUES_NEXT_PAGE_QUERY = (
    "query=query($owner:String!,$name:String!,$number:Int!,$cursor:String!){"
    "repository(owner:$owner,name:$name){issue(number:$number){"
    "subIssues(first:100, after:$cursor){nodes{number} pageInfo{hasNextPage endCursor}}}}}"
)
# Bounded failure ceiling: 50 pages * 100/page = 5,000 children max. Stops a
# buggy/adversarial API that always reports ``hasNextPage: true`` from looping
# forever, while remaining far above any real epic's child count.
_MAX_SUBISSUE_PAGES = 50


def _fetch_subissues_page(epic: int, cursor: str | None, repo_root: Path = ROOT) -> dict:
    """One GraphQL page of ``issue.subIssues`` (+ ``body`` on the first page)."""
    owner, name = _repo_owner_name(repo_root)
    if cursor is None:
        args = [
            "-F", "number=" + str(epic),
            "-f", f"owner={owner}", "-f", f"name={name}",
            "-f", _SUBISSUES_FIRST_PAGE_QUERY,
        ]
    else:
        args = [
            "-F", "number=" + str(epic),
            "-f", f"owner={owner}", "-f", f"name={name}",
            "-f", f"cursor={cursor}",
            "-f", _SUBISSUES_NEXT_PAGE_QUERY,
        ]
    data = _gh_json(["api", "graphql", *args], cwd=repo_root)
    return (data.get("data") or {}).get("repository", {}).get("issue") or {}


def _paginate_subissues(
    epic: int, fetch_page: Callable[[int, str | None], dict]
) -> tuple[set[int], str]:
    """Drive cursor pagination over ``fetch_page`` and return (native, body).

    ``fetch_page`` is injected so this is testable without any network or
    ``gh`` subprocess — see ``tests/test_issue_stream_audit.py``. Bounded by
    ``_MAX_SUBISSUE_PAGES``: a page with no ``endCursor`` (or ``hasNextPage``
    false) stops the loop, and the hard page ceiling is a belt-and-suspenders
    guard against a runaway/adversarial response.
    """
    native: set[int] = set()
    body = ""
    cursor: str | None = None
    for page in range(_MAX_SUBISSUE_PAGES):
        issue = fetch_page(epic, cursor)
        if page == 0:
            body = issue.get("body") or ""
        sub_issues = issue.get("subIssues") or {}
        native.update(
            n["number"] for n in (sub_issues.get("nodes") or [])
            if isinstance(n, dict) and isinstance(n.get("number"), int)
        )
        page_info = sub_issues.get("pageInfo") or {}
        next_cursor = page_info.get("endCursor")
        if not page_info.get("hasNextPage") or not next_cursor:
            break
        cursor = next_cursor
    return native, body


def fetch_epic_membership(epic: int, repo_root: Path = ROOT) -> tuple[set[int], set[int]]:
    """Return (native_sub_issue_numbers, body_reference_numbers) for one epic.

    Native sub-issues are paginated (see ``_paginate_subissues``) so an epic
    with more than 100 children is not silently truncated to its first page.
    """
    native, body = _paginate_subissues(
        epic, lambda e, c: _fetch_subissues_page(e, c, repo_root)
    )
    refs = {int(m) for m in ISSUE_REF_RE.findall(body)}
    return native, refs


def classify(
    open_issues: list[dict],
    registry: dict[str, list[int]],
    membership: dict[int, tuple[set[int], set[int]]],
) -> dict:
    """Pure classification — unit-testable without network."""
    epic_numbers = {e for epics in registry.values() for e in epics}
    stream_of_epic = {e: key for key, epics in registry.items() for e in epics}

    native_epics: dict[int, set[int]] = {}
    body_epics: dict[int, set[int]] = {}
    for epic, (native, refs) in membership.items():
        for n in native:
            native_epics.setdefault(n, set()).add(epic)
        for n in refs:
            body_epics.setdefault(n, set()).add(epic)
    native_linked = set(native_epics)
    # Native sub-issue links are DELIBERATE membership; body refs are the
    # migration fallback. Once an issue has any native link, prose mentions in
    # other epics' bodies must not multi-home it. Ambiguity is judged on the
    # EFFECTIVE EPIC set, not the distinct stream names it maps to — two native
    # epics in the SAME stream are still two owners and must be ambiguous, not
    # silently collapsed to "one stream, therefore fine" (codex/gemini review).
    owning_epics: dict[int, set[int]] = {
        n: (native_epics.get(n) or body_epics.get(n) or set())
        for n in set(native_epics) | set(body_epics)
    }

    open_numbers = {i["number"] for i in open_issues}
    titles = {i["number"]: i["title"] for i in open_issues}

    orphans = sorted(
        n for n in open_numbers if n not in epic_numbers and not owning_epics.get(n)
    )
    multi_homed = sorted(
        n for n in open_numbers
        if n not in epic_numbers and len(owning_epics.get(n, ())) > 1
    )
    body_only = sorted(
        n for n in open_numbers
        if n not in epic_numbers and owning_epics.get(n) and n not in native_linked
    )
    missing_epics = sorted(e for e in epic_numbers if e not in open_numbers)

    return {
        "generated_at": int(time.time()),
        "open_total": len(open_numbers),
        "streams": {k: sorted(v) for k, v in registry.items()},
        "orphans": [{"number": n, "title": titles[n]} for n in orphans],
        "multi_homed": [
            {
                "number": n,
                "title": titles[n],
                "streams": sorted({stream_of_epic[e] for e in owning_epics[n]}),
            }
            for n in multi_homed
        ],
        "pending_native_link": body_only,
        "closed_or_missing_epics": missing_epics,
        # The invariant is EXACTLY ONE EFFECTIVE EPIC — multi-homed violates it
        # (codex F1), including two epics that happen to share one stream.
        "ok": not orphans and not missing_epics and not multi_homed,
        # ADR-011 P4 private index (stripped from the public API): the exact
        # effective issue→epic membership, native winning over body refs, plus the
        # bounded open-issue set. Carries enough state to reject closed (absent
        # key), wrong (epic not in ``epics``), and ambiguous (``unique_stream``
        # false — more than one effective epic, even within one stream) ownership
        # without any live network call.
        "effective_membership": _effective_membership(
            epic_numbers, stream_of_epic, membership
        ),
        "open_issue_numbers": sorted(open_numbers),
    }


def _effective_membership(
    epic_numbers: set[int],
    stream_of_epic: dict[int, str],
    membership: dict[int, tuple[set[int], set[int]]],
) -> dict[str, dict]:
    """Exact effective issue→epic index over EVERY native/body-linked child a
    stream epic returns, regardless of open/closed state. Native links win over
    body refs; only the epics themselves are excluded. One entry per owned
    issue — open or closed.

    Record OWNERSHIP proof (ADR-011 P4) can be historical: a closed
    implementation issue is still uniquely owned by the epic that tracked it,
    and ``make_membership_resolver`` must keep proving that after the issue
    closes. Open-state gating belongs only to issue-CONSUMER health, which is
    validated separately against ``open_issue_numbers`` in
    ``make_issue_resolver`` — closed ownership is valid, a closed ``consumer.
    kind: issue`` is dead (codex/gemini review, PR #4998 corrective pass).

    ``unique_stream`` means EXACT membership: exactly one effective epic — not
    merely one distinct stream *name*. Two epics that happen to live in the same
    stream are still two owners and must NOT resolve as unique (codex/gemini
    review on PR #4998): a resolver built from this index must fail closed for
    that case exactly as it does for a genuine cross-stream multi-home.
    """
    native_epics: dict[int, set[int]] = {}
    body_epics: dict[int, set[int]] = {}
    for epic, (native, refs) in membership.items():
        for n in native:
            native_epics.setdefault(n, set()).add(epic)
        for n in refs:
            body_epics.setdefault(n, set()).add(epic)
    index: dict[str, dict] = {}
    for n in sorted(set(native_epics) | set(body_epics)):
        if n in epic_numbers:
            continue
        via = "native" if native_epics.get(n) else "body"
        epics = sorted(native_epics.get(n) or body_epics.get(n))
        streams = sorted({stream_of_epic[e] for e in epics})
        index[str(n)] = {
            "epics": epics,
            "streams": streams,
            "via": via,
            "unique_stream": len(epics) == 1,
        }
    return index


def run_audit(repo_root: Path | None = None) -> dict:
    """Run one live audit, scoped to ``repo_root`` (defaults to this module's
    own checkout, ``ROOT``, preserving the plain-CLI default behavior).

    Every input — the stream registry, ``gh`` execution cwd for open-issue and
    epic-membership fetches, and the cache the report is written to — uses the
    SAME resolved root, so a caller auditing a non-default checkout (e.g. a
    closeout invocation bound to another worktree) never validates membership
    against, or writes a cache into, this module's own repo instead.
    """
    root = repo_root.resolve() if repo_root is not None else ROOT
    registry = load_registry(root / "scripts" / "config" / "issue_streams.yaml")
    open_issues = fetch_open_issues(root)
    membership = {
        epic: fetch_epic_membership(epic, root)
        for epics in registry.values()
        for epic in epics
    }
    report = classify(open_issues, registry, membership)
    cache_path = root / "batch_state" / "issue_stream_audit.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def read_cache(max_age_s: int) -> dict | None:
    try:
        report = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if time.time() - report.get("generated_at", 0) > max_age_s:
        return None
    return report


# --------------------------------------------------------------------------- #
# ADR-011 P4 — strict adoption gate inputs (fresh cache only; never network)
# --------------------------------------------------------------------------- #
# Cache authority window: a membership cache is trusted for at most
# ``max_age_s`` (default 3600s, matching the auditor's own session-setup
# refresh cadence) AFTER ``generated_at``, and rejected outright if
# ``generated_at`` is more than ``CACHE_FUTURE_SKEW_S`` ahead of wall-clock —
# clock skew or a corrupted/hand-edited timestamp must not be read as "still
# fresh forever" just because the age computes negative.
CACHE_FUTURE_SKEW_S = 300

_VALID_VIA = frozenset({"native", "body"})


def _is_positive_int(value: object) -> bool:
    """True for a JSON int that is a real positive integer — excludes bool
    (``isinstance(True, int)`` is True in Python) and any non-int type."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_membership_entry(entry: object) -> bool:
    """Structurally + semantically validate one ``effective_membership`` entry.

    Every field is checked against the exact shape ``_effective_membership``
    produces: a non-empty list of positive-int epics, a list of non-empty
    stream-name strings, a known ``via``, and a ``unique_stream`` bool that is
    internally consistent with the epic count (exactly one effective epic —
    codex/gemini review). A cache that claims ``unique_stream: true`` for two
    epics (or vice versa) is corrupted/adversarial and must fail closed.
    """
    if not isinstance(entry, dict):
        return False
    epics = entry.get("epics")
    streams = entry.get("streams")
    via = entry.get("via")
    unique = entry.get("unique_stream")
    if not isinstance(epics, list) or not epics or not all(_is_positive_int(e) for e in epics):
        return False
    if not isinstance(streams, list) or not streams or not all(
        isinstance(s, str) and s for s in streams
    ):
        return False
    if via not in _VALID_VIA:
        return False
    if not isinstance(unique, bool):
        return False
    return unique == (len(epics) == 1)


def _valid_membership_index(index: object) -> bool:
    if not isinstance(index, dict):
        return False
    for key, entry in index.items():
        if not (isinstance(key, str) and key.isdigit() and int(key) > 0):
            return False
        if not _valid_membership_entry(entry):
            return False
    return True


def _valid_open_numbers(value: object) -> bool:
    return isinstance(value, list) and all(_is_positive_int(n) for n in value)


def validate_membership_report(report: object, max_age_s: int) -> dict | None:
    """Validate an already-fetched (in-memory) audit report and return it, or
    ``None`` if it fails closed.

    Same freshness/shape rules as :func:`read_membership_index` — extracted so
    a caller carrying one fresh live ``run_audit()`` snapshot through a single
    observation (task_lifecycle's canonical membership validator) can apply
    the exact same fail-closed semantics as the file-cache path below, without
    a second round trip through disk.
    """
    if not isinstance(report, dict):
        return None

    generated_at = report.get("generated_at")
    if isinstance(generated_at, bool) or not isinstance(generated_at, (int, float)):
        return None
    if not math.isfinite(generated_at):
        return None
    age = time.time() - generated_at
    if age > max_age_s or age < -CACHE_FUTURE_SKEW_S:
        return None

    index = report.get("effective_membership")
    if not _valid_membership_index(index):
        return None
    open_numbers = report.get("open_issue_numbers")
    if open_numbers is not None and not _valid_open_numbers(open_numbers):
        return None
    return report


def read_membership_index(max_age_s: int, *, cache_path: Path | None = None) -> dict | None:
    """Return the effective issue→epic membership index from a FRESH cache.

    Fails **closed** to ``None`` — never raises, never returns a truthy-but-bogus
    value — when the cache is missing, unreadable, not a mapping, stale (older
    than ``max_age_s``), materially future-skewed (``generated_at`` more than
    ``CACHE_FUTURE_SKEW_S`` ahead of wall-clock, or non-finite/non-numeric/bool),
    was written by a pre-P4 auditor that lacks the index, or carries a
    structurally/semantically malformed ``effective_membership`` or
    ``open_issue_numbers`` (non-positive-int keys/values, unknown ``via``, a
    ``unique_stream`` bool inconsistent with its epic count, etc.). This never
    reaches GitHub: the strict adoption gate consumes a cache produced by a
    separate live auditor run, so discovery/gate paths stay offline and
    non-mutating.
    """
    path = cache_path if cache_path is not None else CACHE_PATH
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return validate_membership_report(report, max_age_s)


def make_membership_resolver(report: dict) -> MembershipResolver:
    """Build a ``(issue, epic) → bool`` resolver over a fresh cache report.

    Returns ``True`` only when the issue is an owned member (present in the
    index — open OR closed, since record ownership is historical proof, not a
    liveness claim), belongs to exactly one EFFECTIVE EPIC (``unique_stream`` —
    exact membership, not merely one stream name), and the requested ``epic`` is
    one of its effective epics. Rejects absent/orphan, wrong-epic, and ambiguous
    (more than one effective epic, even within a single stream) ownership —
    every failure mode fails closed. Issue *consumer* liveness (which DOES
    require the issue to be open) is a separate proof — see ``make_issue_resolver``.
    """
    index = report.get("effective_membership") or {}

    def _resolve(issue: int, epic: int) -> bool:
        entry = index.get(str(issue))
        if not isinstance(entry, dict) or not entry.get("unique_stream"):
            return False
        return int(epic) in (entry.get("epics") or [])

    return _resolve


def make_issue_resolver(report: dict) -> Callable[[str], bool]:
    """Build a consumer ``issue`` resolver.

    ``True`` only when the ref names an OPEN issue that is ALSO uniquely owned
    by exactly one effective epic/stream in the fresh membership index. Being in
    the bounded open-issue set alone is not enough — an unowned (orphaned) or
    ambiguously multi-homed open issue is not trustworthy "adopted" evidence
    (codex/gemini review on PR #4998: adopted issue consumers must be open *and*
    uniquely owned, the same proof the ownership gate itself uses). Non-digit
    refs fail closed.
    """
    open_set = {int(n) for n in (report.get("open_issue_numbers") or [])}
    index = report.get("effective_membership") or {}

    def _resolve(ref: str) -> bool:
        if not (ref.isdigit() and int(ref) in open_set):
            return False
        entry = index.get(ref)
        return isinstance(entry, dict) and bool(entry.get("unique_stream"))

    return _resolve


def _node_id(number: int) -> str:
    data = _gh_json([
        "api", f"repos/{{owner}}/{{repo}}/issues/{number}", "--jq", "{node_id}"
    ])
    return data["node_id"]


def migrate(report: dict) -> int:
    """Create native sub-issue links for pending body-only references.

    Ambiguous cases — body-referenced from MORE THAN ONE stream — are skipped
    (codex F2): GitHub's single-parent constraint would otherwise make the
    winner order-dependent instead of deliberate. Resolve them manually.
    """
    registry = load_registry()
    ambiguous = {m["number"] for m in report.get("multi_homed", [])}
    if ambiguous:
        print(
            "skipping ambiguous multi-homed (resolve manually): "
            + ", ".join(f"#{n}" for n in sorted(ambiguous)),
            file=sys.stderr,
        )
    created = 0
    for stream_key, epics in registry.items():
        for epic in epics:
            native, refs = fetch_epic_membership(epic)
            pending = sorted(
                refs - native - ambiguous
                - {e for es in registry.values() for e in es}
            )
            if not pending:
                continue
            epic_node = _node_id(epic)
            for n in pending:
                if n not in {x if isinstance(x, int) else x["number"]
                             for x in report.get("pending_native_link", [])}:
                    continue
                try:
                    child_node = _node_id(n)
                    _gh_json([
                        "api", "graphql",
                        "-f",
                        "query=mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,"
                        "subIssueId:$c}){issue{number}}}",
                        "-f", f"p={epic_node}", "-f", f"c={child_node}",
                    ])
                    created += 1
                    print(f"linked #{n} → epic #{epic} ({stream_key})")
                except RuntimeError as exc:
                    print(f"WARN: link #{n} → #{epic} failed: {exc}", file=sys.stderr)
    return created


def human_summary(report: dict) -> str:
    lines = [
        f"open issues: {report['open_total']} · streams: {len(report['streams'])}"
        f" · ok: {report['ok']}"
    ]
    if report["orphans"]:
        lines.append(f"ORPHANS ({len(report['orphans'])} — no stream epic):")
        lines += [f"  #{o['number']} {o['title'][:80]}" for o in report["orphans"]]
    if report["multi_homed"]:
        lines.append(f"multi-homed ({len(report['multi_homed'])}):")
        lines += [
            f"  #{m['number']} in {', '.join(m['streams'])}" for m in report["multi_homed"]
        ]
    if report["pending_native_link"]:
        lines.append(
            f"pending native sub-issue link: {len(report['pending_native_link'])}"
            " (run --migrate)"
        )
    if report["closed_or_missing_epics"]:
        lines.append(f"⚠️ stream epics not open: {report['closed_or_missing_epics']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="exit 1 unless ok")
    parser.add_argument("--from-cache", action="store_true")
    parser.add_argument("--max-age", type=int, default=3600)
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--refresh-worker", metavar="RUN_ID", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.refresh_worker:
        return _run_refresh_worker(args.refresh_worker)

    report = read_cache(args.max_age) if args.from_cache else None
    if report is None:
        if args.from_cache and args.check:
            # Hook path: never block a session start on the network.
            print("issue-stream audit: no fresh cache (run the auditor to refresh)")
            return 0
        report = run_audit()

    if args.migrate:
        created = migrate(report)
        print(f"created {created} native sub-issue link(s)")
        report = run_audit()

    print(json.dumps(report, ensure_ascii=False, indent=1) if args.json
          else human_summary(report))
    return 0 if (report["ok"] or not args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
