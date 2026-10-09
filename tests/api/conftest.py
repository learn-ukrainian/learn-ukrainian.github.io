"""Isolate the process-global status cache between API tests.

Pytest shortens very long test names onto one temporary directory. A snapshot
keyed only by that directory would otherwise be served to the next case.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_status_ttl_cache():
    from scripts.api.state_helpers import cache_invalidate

    cache_invalidate()
    yield
    cache_invalidate()
