"""Public Work control-plane projection (read-only foundation)."""

from __future__ import annotations

SCHEMA_VERSION = "work-projection.v1"
SOURCE_PUBLIC = "public-monitor"
SOURCE_PRIVATE = "private-local-adapter"
WORK_ID_PREFIX = "wp1"

__all__ = [
    "SCHEMA_VERSION",
    "SOURCE_PRIVATE",
    "SOURCE_PUBLIC",
    "WORK_ID_PREFIX",
]
