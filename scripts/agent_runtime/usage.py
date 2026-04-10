"""Shared usage logger for the agent runtime.

Every invocation through ``runner.invoke()`` writes exactly one JSONL record
here. The file layout reuses ``batch_state/api_usage/`` so the existing
``/api/batch/usage`` endpoint at ``scripts/api/main.py:152`` surfaces
per-agent + per-entrypoint cost data with zero new plumbing.

File layout::

    batch_state/api_usage/usage_<agent>-<entrypoint>_YYYY-MM-DD.jsonl

Examples::

    batch_state/api_usage/usage_codex-bridge_2026-04-10.jsonl
    batch_state/api_usage/usage_gemini-dispatch_2026-04-10.jsonl
    batch_state/api_usage/usage_claude-delegate_2026-04-10.jsonl

Atomicity: we use ``os.open(O_APPEND | O_CREAT | O_WRONLY)`` + single
``os.write()`` per line, bypassing Python's buffered I/O entirely. POSIX
guarantees ``write(2)`` with ``O_APPEND`` is atomic across concurrent writers
for payloads smaller than ``PIPE_BUF`` (typically 4KB). Our JSONL records
are always < 2KB so we're well inside the guarantee. No filelock dependency.

Headroom check: ``has_headroom(agent, model)`` scans the last 15 minutes
of records scoped by ``(agent, model)`` and returns False if any record
has ``outcome == "rate_limited"`` within that window. The runner calls
this pre-invocation and raises ``RateLimitedError`` if headroom is False
— saves the quota slot that would otherwise be burned on a known-rate-
limited call. The window was reduced from 5h to 15min on 2026-04-10
after a transient 429 false-locked the quota for 5 hours on real
builds; see ``_RATE_LIMIT_WINDOW_S`` for the full story.

Issue: #1184. Supersedes standalone #1183.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Rate-limit window in seconds. We reduced this from 5h to 15min in
# 2026-04-10 (#1185 follow-up) after a single transient "No capacity
# available" 429 at 12:08 falsely locked the entire quota for 5 hours,
# blocking heal-pipeline runs that would otherwise have succeeded.
#
# Philosophy:
#   - True quota exhaustion IS rare for us (Google AI Pro subscription,
#     not API key rate limits). When it does happen, a 15-minute cool-off
#     is plenty — the next call just confirms the state.
#   - Transient server-capacity issues are common and clear in seconds.
#     The CLI retries them internally. We must not block on them.
#   - A 15-minute window means a stale false-positive self-heals in
#     under a quarter hour without any manual intervention.
_RATE_LIMIT_WINDOW_S = 15 * 60

# In-process cache of rate-limit state, keyed by (agent, model). When a
# call returns outcome="rate_limited", we stamp the timestamp here so
# subsequent calls in the same process short-circuit immediately without
# re-reading the JSONL file.
_RATE_LIMIT_CACHE: dict[tuple[str, str], float] = {}


def _usage_dir() -> Path:
    """Return the batch_state/api_usage/ directory, creating it if missing."""
    # Resolve relative to repo root so this works from any cwd.
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "batch_state" / "api_usage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _usage_file(agent: str, entrypoint: str, day: datetime | None = None) -> Path:
    """Return the daily JSONL path for (agent, entrypoint)."""
    if day is None:
        day = datetime.now(UTC)
    date_str = day.strftime("%Y-%m-%d")
    return _usage_dir() / f"usage_{agent}-{entrypoint}_{date_str}.jsonl"


def write_record(record: dict[str, Any]) -> None:
    """Append one JSONL record atomically.

    Required fields in ``record``:
        ts, agent, entrypoint, model, outcome

    The function does NOT validate the schema — adapters and runner are
    responsible for building correct records. We only handle the write.

    Atomicity: ``os.open`` + ``os.write`` in one call, bypassing Python's
    buffered I/O. Safe under concurrent writers within POSIX PIPE_BUF.

    If the write fails for any reason (permission denied, disk full, etc.),
    we log a warning to stderr and continue — usage logging is observability,
    not correctness; losing a record is preferable to crashing the caller.
    """
    try:
        path = _usage_file(record["agent"], record["entrypoint"])
        line = (json.dumps(record, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)

        # Update in-process rate-limit cache if this was a rate-limit event.
        # (Gemini review finding #3: use the record's own ts, not wall-clock
        # at write time. Writing a delayed record would otherwise poison the
        # cache by starting the 5h block window from "now" instead of the
        # actual event time. Also honor the newest event when multiple writers
        # race on the same (agent, model) key.)
        if record.get("outcome") == "rate_limited":
            key = (record["agent"], record["model"])
            ts_str = record.get("ts")
            event_ts: float = time.time()  # safe fallback
            if ts_str:
                with contextlib.suppress(ValueError, AttributeError):
                    event_ts = datetime.fromisoformat(
                        str(ts_str).replace("Z", "+00:00")
                    ).timestamp()
            existing = _RATE_LIMIT_CACHE.get(key)
            if existing is None or event_ts > existing:
                _RATE_LIMIT_CACHE[key] = event_ts
    except Exception as exc:  # pragma: no cover — degraded mode only
        # Best-effort: print to stderr but don't fail the caller. The agent
        # call itself already succeeded or failed at this point; we're only
        # trying to persist a telemetry row.
        import sys
        print(
            f"[usage] WARNING: failed to write record: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )


def has_headroom(agent: str, model: str) -> tuple[bool, str]:
    """Check whether (agent, model) has quota headroom for a new call.

    Returns:
        (True, "")  — no recent rate-limit in the 15-minute window, proceed.
        (False, reason) — a rate-limit occurred within 15 minutes; caller
            should raise RateLimitedError immediately without burning a
            quota slot.

    Implementation:
        1. Check in-process cache first (fast path, zero I/O).
        2. Fall through to reading today's JSONL files scoped by
           (agent, model), looking for any rate_limited record within
           the last 15 minutes.

    Window history: originally 5 hours, reduced to 15 minutes on
    2026-04-10 after a transient 429 false-locked the entire quota for
    a full five hours. See ``_RATE_LIMIT_WINDOW_S``.
    """
    now = time.time()

    # Fast path: in-process cache
    cache_key = (agent, model)
    cached_ts = _RATE_LIMIT_CACHE.get(cache_key)
    if cached_ts is not None and (now - cached_ts) < _RATE_LIMIT_WINDOW_S:
        age_s = now - cached_ts
        return False, f"rate_limited {int(age_s)}s ago (in-process cache)"
    elif cached_ts is not None:
        # Cache entry expired; clear it
        _RATE_LIMIT_CACHE.pop(cache_key, None)

    # Slow path: scan JSONL files for this (agent, *) and filter by model inside.
    # To survive system clock jumps where old rate limit records might be in files
    # with dates that don't match the currently shifted clock, we glob all files
    # for the agent and rely on the file mtime + the absolute `ts` inside the record.
    cutoff = now - _RATE_LIMIT_WINDOW_S
    usage_dir = _usage_dir()
    most_recent_rate_limit_ts: float | None = None

    for file_path in usage_dir.glob(f"usage_{agent}-*.jsonl"):
        try:
            # Skip files whose modification time is entirely before the cutoff
            if file_path.stat().st_mtime < cutoff:
                continue

            with open(file_path, encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue  # truncated or corrupted line; skip
                    if rec.get("model") != model:
                        continue
                    if rec.get("outcome") != "rate_limited":
                        continue
                    ts_str = rec.get("ts")
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                    except (ValueError, AttributeError):
                        continue
                    if ts >= cutoff and (
                        most_recent_rate_limit_ts is None
                        or ts > most_recent_rate_limit_ts
                    ):
                        most_recent_rate_limit_ts = ts
        except OSError:
            continue  # file disappeared mid-scan or permission denied; skip

    if most_recent_rate_limit_ts is not None:
        age_s = int(now - most_recent_rate_limit_ts)
        return False, f"rate_limited {age_s}s ago (disk scan)"

    return True, ""


def _reset_rate_limit_cache_for_tests() -> None:
    """Clear the in-process rate-limit cache. Tests only."""
    _RATE_LIMIT_CACHE.clear()
