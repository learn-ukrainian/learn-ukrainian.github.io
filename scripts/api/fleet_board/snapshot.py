"""Read roster and harness snapshots.

Locations come from ``FLEET_*`` variables. An unset variable is
``not_configured``. A snapshot older than twice its own interval is
``stale``. Screen-text fields are dropped before any other use.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .sources import SourceReport, read_location, report

STALE_INTERVAL_MULTIPLE = 2
SCREEN_TEXT_KEYS = frozenset(
    {
        "pane_text",
        "screen",
        "screen_text",
        "terminal",
        "terminal_text",
        "scrollback",
        "caption",
        "output",
    }
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_timestamp(value: object) -> datetime | None:
    """UTC timestamp, or None when the value is not one."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def as_timestamp(value: object) -> str | None:
    """Normalize a timestamp to whole UTC seconds, or None."""
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def mapping(value: object) -> dict[str, Any]:
    """A dict with screen-text keys removed. Anything else is empty."""
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items() if key not in SCREEN_TEXT_KEYS}


def finite_number(value: object) -> float | None:
    """A finite non-negative number. Booleans and missing values are None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _age_seconds(generated_at: datetime, now: datetime) -> float | None:
    age = (now - generated_at).total_seconds()
    if not math.isfinite(age) or age < 0:
        return None
    return age


def freshness(document: Mapping[str, Any], now: datetime) -> tuple[str, float | None]:
    """``ok`` or ``stale`` when the snapshot can be aged, else ``unavailable``."""
    generated_at = parse_timestamp(document.get("generated_at"))
    interval_s = finite_number(document.get("interval_s"))
    if generated_at is None or interval_s is None or interval_s <= 0:
        return "unavailable", None
    age_s = _age_seconds(generated_at, now)
    if age_s is None:
        return "unavailable", None
    if age_s > STALE_INTERVAL_MULTIPLE * interval_s:
        return "stale", age_s
    return "ok", age_s


def load_snapshot(
    *,
    source_name: str,
    env_var: str,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> tuple[SourceReport, dict[str, Any] | None]:
    """Read one JSON snapshot. Never raises and never returns the location."""
    if read_location(env_var, environ) is None:
        return report(source_name, "not_configured"), None
    clock = now or utc_now()
    try:
        location = read_location(env_var, environ)
        if location is None:
            return report(source_name, "not_configured"), None
        raw = json.loads(Path(location).read_text(encoding="utf-8"))
    except Exception:
        return report(source_name, "unavailable"), None
    document = mapping(raw)
    if not document and not isinstance(raw, dict):
        return report(source_name, "unavailable"), None
    status, age_s = freshness(document, clock)
    if status == "unavailable":
        return report(source_name, "unavailable"), document or None
    return report(source_name, status, age_s=age_s), document
