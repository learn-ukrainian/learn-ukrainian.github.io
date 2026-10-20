"""Hourly, privacy-safe weekly-allowance history for the five quota slots (#11144).

``collect`` appends one allowlisted JSON line per slot from the Monitor's ``/api/state/routing-budget``.
``resets`` reports observed used-percent drops and reset-timestamp jumps with weekdays; it infers no schedule.
"""

import argparse
import collections
import datetime as dt
import fcntl
import http.client
import json
import math
import os
import stat
import sys
import urllib.request
from pathlib import Path
from typing import Any

from scripts.common.safe_open import UnsafeEntryError, safe_open_below
from scripts.common.safe_unit_install import InstallError, open_unit_dir

WINDOW = "weekly"
SLOT_PROVIDER = {slot: slot.split(":")[0] for slot in ("codex", "claude:a", "claude:b", "grok", "antigravity")}
STATUSES = ("known", "stale", "unknown")
# Fixed codes only: exception text and payload values are never persisted or printed.
REASONS = frozenset(
    {"source_unavailable", "row_missing", "value_invalid", "source_stale", "not_fresh", "source_time_invalid"}
)
FRESH_LABELS = frozenset({"ok", "fresh", "live", "current"})
ROUTING_BUDGET_PATH = "/api/state/routing-budget"
# The Monitor's own bound when a snapshot publishes no usable ``diagnostics.stale_threshold_s``
# (``scripts.api.state_router.ROUTING_BUDGET_MAX_AGE_S``; a test keeps the two equal).
ROUTING_BUDGET_MAX_AGE_S = 900.0
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
FILE_ENV = "LU_QUOTA_HISTORY_FILE"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
UNCERTAINTY = {
    "used_drop": "the reset lies between the two observations; its exact time is unknown",
    "reset_timestamp_jump": "the reported reset timestamp changed; this is not an observed reset",
}


def default_path() -> Path:
    """``$LU_QUOTA_HISTORY_FILE``, else the user-local state directory."""
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(os.environ.get(FILE_ENV) or f"{state}/learn-ukrainian/quota-history/samples.jsonl")


def _moment(value: Any) -> dt.datetime | None:
    """A timezone-aware ISO timestamp as a UTC datetime; anything else, including one whose UTC
    value falls outside the representable years 1..9999, is None."""
    if not isinstance(value, str):
        return None
    try:
        moment = dt.datetime.fromisoformat(value)
        return None if moment.tzinfo is None else moment.astimezone(dt.UTC)
    except (ValueError, OverflowError):
        return None


def _utc(value: Any) -> str | None:
    """A timezone-aware ISO timestamp as UTC ``...Z``; anything else is None."""
    moment = _moment(value)
    return None if moment is None else moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def _number(value: Any) -> float | None:
    """A finite, non-boolean JSON number as a float, else None. An integer too large for a float is None."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def _pct(value: Any) -> float | None:
    """A finite, non-boolean number in 0..100, else None."""
    number = _number(value)
    return number if number is not None and 0 <= number <= 100 else None


def _node(container: Any, *keys: str) -> dict[str, Any] | None:
    for key in keys:
        container = container.get(key) if isinstance(container, dict) else None
    return container if isinstance(container, dict) else None


def _fields(status: str, reason: str | None = None, source: Any = None, used: float | None = None, resets: Any = None):
    return {
        "source_observed_at": _utc(source),
        "used_percent": used,
        "resets_at": _utc(resets),
        "status": status,
        "reason": reason,
    }


RECORD_FIELDS = frozenset(_fields("unknown")) | {"provider", "slot", "window", "observed_at"}


def _snapshot_bounds(payload: dict[str, Any]) -> tuple[float, bool]:
    """The routing snapshot's age bound and whether the snapshot itself is past it.

    The Monitor publishes ``diagnostics.stale_threshold_s`` and ``diagnostics.data_age_s`` (source
    age plus time in its cache); past the threshold a snapshot must not authorize a lane. Like the
    Monitor, a missing or unusable threshold falls back to :data:`ROUTING_BUDGET_MAX_AGE_S`. A
    present but invalid age cannot be checked against the bound and counts as past it.
    """
    diagnostics = _node(payload, "diagnostics") or {}
    threshold = _number(diagnostics.get("stale_threshold_s"))
    if threshold is None or threshold <= 0:
        threshold = ROUTING_BUDGET_MAX_AGE_S
    raw_age = diagnostics.get("data_age_s")
    age = _number(raw_age)
    return threshold, raw_age is not None and (age is None or age > threshold)


def _slot_fields(slot: str, payload: dict[str, Any], observed: dt.datetime) -> dict[str, Any]:
    """One slot's fields. Anything not proven fresh and valid stays null.

    ``known`` needs a fresh label, an explicit ``stale: false``, a source time that is valid, not
    after ``observed`` and no older than the snapshot's age bound, and a valid value.
    Agent rows also need the snapshot itself within that threshold; the per-account Claude rows
    are re-read live by the Monitor on every request, so a stored snapshot's age does not apply.
    """
    threshold, snapshot_expired = _snapshot_bounds(payload)
    if slot.startswith("claude:"):
        row = _node(payload, "claude_accounts", slot)
        if row is None:
            return _fields("unknown", "row_missing")
        window = _node(row, "weekly") or {}
        left = _pct(window.get("left_pct"))
        used = None if left is None else 100.0 - left
        source, resets = row.get("updated"), window.get("resets_at")
        label, stale_flag = row.get("status"), row.get("stale")
        snapshot_expired = False
    else:
        # The antigravity slot reads the Monitor's aggregate ``gemini`` agent row.
        lane = "gemini" if slot == "antigravity" else slot
        meta = _node(payload, "agents", lane, "codexbar")
        if meta is None:
            return _fields("unknown", "row_missing")
        used, source, resets = _pct(meta.get("weekly_used_pct")), meta.get("fetched_at"), meta.get("weekly_resets_at")
        label, stale_flag = meta.get("freshness"), meta.get("stale")
    label = label if isinstance(label, str) else None  # an unhashable label must not reach the set test
    if stale_flag is True or str(label or "").startswith("stale"):
        return _fields("stale", "source_stale", source)
    if label not in FRESH_LABELS or stale_flag is not False:
        return _fields("unknown", "not_fresh", source)
    source_moment = _moment(source)
    if source_moment is None or source_moment > observed:
        return _fields("unknown", "source_time_invalid")
    if snapshot_expired or (observed - source_moment).total_seconds() > threshold:
        return _fields("stale", "source_stale", source)
    if used is None:
        return _fields("unknown", "value_invalid", source)
    return _fields("known", None, source, used, resets)


def collect(base: str, timeout: float, now: dt.datetime | None = None) -> list[dict[str, Any]]:
    """One bounded fetch, five rows in slot order. An unreachable Monitor yields five explicit unknowns.

    The observation time is taken after the response arrives (or is ``now``), so a source sample
    refreshed while the request was in flight is never later than it.
    """
    try:
        with urllib.request.urlopen(base + ROUTING_BUDGET_PATH, timeout=timeout) as response:
            payload = json.loads(response.read(MAX_RESPONSE_BYTES).decode("utf-8"))
    except (OSError, ValueError, RecursionError, http.client.HTTPException):
        payload = None
    moment = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC)
    observed = _utc(moment.isoformat())
    rows = []
    for slot, provider in SLOT_PROVIDER.items():
        if isinstance(payload, dict):
            fields = _slot_fields(slot, payload, moment)
        else:
            fields = _fields("unknown", "source_unavailable")
        rows.append({"provider": provider, "slot": slot, "window": WINDOW, "observed_at": observed, **fields})
    return rows


class UnsafeHistoryPathError(OSError):
    """The history path is not a private regular file in a private directory reached without a symlink.

    The message is fixed wording and never names a path.
    """

    def __init__(self) -> None:
        super().__init__("history path refused: not a private regular file in a private directory")


def _require_private(info: os.stat_result) -> None:
    """Refuse an entry another user owns or that grants any group or other permission bit."""
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise UnsafeHistoryPathError


def append(path: Path, rows: list[dict[str, Any]]) -> None:
    """Append all rows in one locked write. Never truncates, rewrites, prunes or changes permissions.

    The directory is reached one component at a time without following a symlink (missing
    components are created 0700) and must be ours and 0700-private; the file is opened through
    that descriptor with ``O_NOFOLLOW`` and must be our regular file, 0600-private. Anything else
    raises :class:`UnsafeHistoryPathError` before a byte is written.
    """
    data = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    try:
        dir_fd = open_unit_dir(path.parent, create=True, directory_mode=0o700)
    except InstallError:
        raise UnsafeHistoryPathError from None
    if dir_fd is None:  # a component vanished during the walk
        raise UnsafeHistoryPathError
    try:
        _require_private(os.fstat(dir_fd))
        fd = safe_open_below(dir_fd, path.name, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except UnsafeEntryError:
        raise UnsafeHistoryPathError from None
    finally:
        os.close(dir_fd)
    with os.fdopen(fd, "ab") as handle:
        _require_private(os.fstat(handle.fileno()))
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write(data)


def _validate(row: Any) -> dict[str, Any] | None:
    """A stored line as a typed sample, or None unless it is exactly one of our records."""
    if not isinstance(row, dict) or set(row) != RECORD_FIELDS:
        return None
    status, reason, used = row["status"], row["reason"], row["used_percent"]
    if SLOT_PROVIDER.get(row["slot"]) != row["provider"] or row["window"] != WINDOW or status not in STATUSES:
        return None
    if reason is not None and reason not in REASONS:
        return None
    parsed = {key: None if row[key] is None else _utc(row[key]) for key in ("source_observed_at", "resets_at")}
    observed = _utc(row["observed_at"])
    if observed is None or any(parsed[key] is None and row[key] is not None for key in parsed):
        return None
    if (status == "known") != (reason is None) or (status == "known") != (used is not None):
        return None
    # A known sample is one the collector proved fresh: a valid value and a source time not after the observation.
    source = parsed["source_observed_at"]
    if status == "known" and (_pct(used) is None or source is None or source > observed):
        return None
    return {**row, **parsed, "observed_at": observed}


def load(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Valid samples in file order, and the count of lines that are not valid records."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return [], 0
    parsed = []
    for line in filter(bytes.strip, raw.split(b"\n")):  # JSONL is LF-delimited; U+2028 stays inside a record
        try:
            parsed.append(_validate(json.loads(line)))
        except (TypeError, ValueError, RecursionError):  # invalid or too deeply nested JSON, or an unhashable value
            parsed.append(None)
    samples = [sample for sample in parsed if sample is not None]
    return samples, len(parsed) - len(samples)


def _weekday(stamp: str | None) -> str | None:
    return None if stamp is None else WEEKDAYS[dt.datetime.fromisoformat(stamp).weekday()]


def _event(kind: str, prev: dict[str, Any], cur: dict[str, Any]) -> dict[str, Any]:
    event = {
        "kind": kind,
        "slot": cur["slot"],
        "previous_observed_at": prev["observed_at"],
        "observed_at": cur["observed_at"],
        "observed_weekday": _weekday(cur["observed_at"]),
        "uncertainty": UNCERTAINTY[kind],
    }
    if kind == "used_drop":
        return {**event, "previous_used_percent": prev["used_percent"], "used_percent": cur["used_percent"]}
    return {
        **event,
        "previous_resets_at": prev["resets_at"],
        "resets_at": cur["resets_at"],
        "previous_resets_weekday": _weekday(prev["resets_at"]),
        "resets_weekday": _weekday(cur["resets_at"]),
    }


def analyze(samples: list[dict[str, Any]], malformed: int) -> dict[str, Any]:
    """Events between consecutive known observations of one slot, in observed-time order.

    Duplicates (same slot, source time, values) count once. Out-of-order lines are sorted into place.
    Unknown and stale samples are counted but never compared.
    """
    counts = {slot: collections.Counter() for slot in SLOT_PROVIDER}
    out_of_order, latest = 0, ""
    for sample in samples:
        out_of_order += sample["observed_at"] < latest
        latest = max(latest, sample["observed_at"])
        counts[sample["slot"]][sample["status"]] += 1
    events, seen, previous, duplicates = [], set(), {}, 0
    for sample in sorted(samples, key=lambda item: item["observed_at"]):
        if sample["status"] != "known":
            continue
        key = (sample["slot"], sample["source_observed_at"], sample["used_percent"], sample["resets_at"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        prev = previous.get(sample["slot"])
        previous[sample["slot"]] = sample
        if prev is None:
            continue
        if sample["used_percent"] < prev["used_percent"]:
            events.append(_event("used_drop", prev, sample))
        if prev["resets_at"] and sample["resets_at"] and prev["resets_at"] != sample["resets_at"]:
            events.append(_event("reset_timestamp_jump", prev, sample))
    return {
        "valid_samples": len(samples),
        "malformed_lines": malformed,
        "duplicate_samples": duplicates,
        "out_of_order_samples": out_of_order,
        "known_samples": sum(slot["known"] for slot in counts.values()),
        "slots": {name: {status: slot[status] for status in STATUSES} for name, slot in counts.items()},
        "events": events,
    }


def _render(report: dict[str, Any]) -> str:
    lines = [
        f"valid samples: {report['valid_samples']}, malformed lines: {report['malformed_lines']}, "
        f"duplicates: {report['duplicate_samples']}, out of order: {report['out_of_order_samples']}",
        *(f"  {slot}: " + " ".join(f"{k}={v}" for k, v in counts.items()) for slot, counts in report["slots"].items()),
    ]
    if report["known_samples"] == 0:
        lines.append("no known samples: this history cannot evidence any reset")
    lines.append("observed changes only; no reset schedule is inferred")
    for event in report["events"]:
        if event["kind"] == "used_drop":
            detail = f"{event['previous_used_percent']}% -> {event['used_percent']}%"
        else:
            detail = f"reset {event['previous_resets_at']} ({event['previous_resets_weekday']})"
            detail += f" -> {event['resets_at']} ({event['resets_weekday']})"
        lines.append(
            f"  {event['kind']} {event['slot']} between {event['previous_observed_at']} and "
            f"{event['observed_at']} (observed {event['observed_weekday']}): {detail}; {event['uncertainty']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.fleet.quota_history", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    collect_cmd = commands.add_parser("collect", help="append one sanitized row per slot (hourly timer)")
    collect_cmd.add_argument("--timeout", type=float, default=10.0, help="Monitor request timeout in seconds")
    resets_cmd = commands.add_parser("resets", help="report observed used-percent drops and reset jumps")
    resets_cmd.add_argument("--json", action="store_true", help="print JSON instead of text")
    for command in (collect_cmd, resets_cmd):
        command.add_argument("--file", type=Path, help=f"history file (default: ${FILE_ENV} or the user state dir)")
    args = parser.parse_args(argv)
    path = args.file or default_path()
    if args.command == "collect":
        base = os.environ.get("DELEGATE_MONITOR_API", "http://127.0.0.1:8765").rstrip("/")
        rows = collect(base, args.timeout)
        try:
            append(path, rows)
        except UnsafeHistoryPathError:
            print("quota-history: unsafe history path refused; no rows written", file=sys.stderr)
            return 1
        except OSError:
            print("quota-history: append failed; no rows written", file=sys.stderr)
            return 1
        statuses = dict(collections.Counter(row["status"] for row in rows))
        reasons = dict(collections.Counter(row["reason"] for row in rows if row["reason"]))
        print(f"quota-history: appended {len(rows)} rows; status={statuses}; reasons={reasons or 'none'}")
        return 0
    samples, malformed = load(path)
    report = analyze(samples, malformed)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else _render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
