"""Age and uncertainty classification for ordinary Fleet finalization alerts."""

from __future__ import annotations

import math
import os
from datetime import UTC, datetime

FINALIZE_AGE_ENV = "LU_NEEDS_FINALIZE_MAX_AGE_MINUTES"
DEFAULT_FINALIZE_AGE_MINUTES = 30.0


def _string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timestamp(value: object) -> datetime:
    if not _string(value):
        raise ValueError("finalization timestamp must be an ISO-8601 timestamp with timezone")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("finalization timestamp must be an ISO-8601 timestamp with timezone") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("finalization timestamp must include a timezone")
    return stamp


def finalization_age(task: dict, *, now: datetime | None = None) -> dict:
    """Classify age and uncertainty for ordinary inbox alerts."""
    clock = now if now is not None else datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("finalization clock must include a timezone")
    configured = os.environ.get(FINALIZE_AGE_ENV, str(DEFAULT_FINALIZE_AGE_MINUTES))
    try:
        threshold = float(configured)
        valid = math.isfinite(threshold) and threshold > 0
    except (ValueError, TypeError, OverflowError):
        threshold, valid = None, False
    age, state, terminal = None, "unknown", None
    try:
        terminal = _timestamp(task.get("finished_at"))
        seconds = (clock - terminal).total_seconds()
        if seconds >= 0:
            age, state = seconds / 60, "known"
        else:
            state = "future"
    except (ValueError, TypeError, OverflowError):
        pass
    return {
        "age_minutes": age,
        "age_state": state,
        "terminal": terminal.isoformat() if state == "known" else None,
        "threshold_minutes": threshold if valid else None,
        "configuration": "valid" if valid else "unknown",
        "attention": not valid or age is None or age > threshold,
    }
