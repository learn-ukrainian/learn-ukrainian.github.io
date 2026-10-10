"""Short-lived payload cache for fleet board reads."""

from __future__ import annotations

import threading
import time

CACHE_TTL_S = 15.0


class PayloadCache:
    """In-process cache that can still return the last payload after the TTL."""

    def __init__(self) -> None:
        self._rows: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()

    def lookup(self, key: str, ttl_s: float) -> tuple[object, float, bool] | None:
        """Return ``(value, age_s, fresh)`` when a payload has been stored."""
        with self._lock:
            row = self._rows.get(key)
            if row is None:
                return None
            stored, value = row
            age = time.monotonic() - stored
            return value, max(0.0, age), age < ttl_s

    def store(self, key: str, value: object) -> None:
        with self._lock:
            self._rows[key] = (time.monotonic(), value)


CACHE = PayloadCache()
