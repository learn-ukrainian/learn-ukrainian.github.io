"""Small coercions and the short cache shared by fleet board readers."""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from .cache import CACHE, CACHE_TTL_S
from .sources import SourceReport, report

_NAME = re.compile(r"[A-Za-z0-9_.:-]{1,64}\Z")
_TOKEN = re.compile(r"[a-z0-9_-]{1,32}\Z")

Outcome = tuple[dict[str, Any], tuple[SourceReport, ...]]


def _env(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def _key(kind: str, location: str) -> str:
    digest = hashlib.sha256(location.encode("utf-8")).hexdigest()
    return f"{kind}:{digest}"


def _age(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value) or value < 0:
        return 0.0
    return round(value, 3)


def _done(source: str, data: dict[str, Any], status: str, age_s: float | None = None) -> Outcome:
    return data, (report(source, status, age_s=_age(age_s)),)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _json_number(value: float) -> int | float:
    if value.is_integer() and abs(value) < 2**53:
        return int(value)
    return value


def _name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if _NAME.fullmatch(text):
        return text
    return None


def _token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if _TOKEN.fullmatch(text):
        return text
    return None


def _timestamp(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cached_call(
    kind: str,
    location: str,
    load: Callable[[], Any],
    *,
    cacheable: Callable[[Any], bool],
) -> tuple[Any, str, float]:
    """Return ``(payload, hit|miss|stale, cache_age_s)``."""
    key = _key(kind, location)
    found = CACHE.lookup(key, CACHE_TTL_S)
    if found is not None and found[2]:
        return found[0], "hit", found[1]
    try:
        value = load()
    except Exception:
        if found is None:
            raise
        return found[0], "stale", found[1]
    if cacheable(value):
        CACHE.store(key, value)
    return value, "miss", 0.0
