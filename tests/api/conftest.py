"""Isolate the process-global status cache between API tests.

Pytest shortens very long test names onto one temporary directory. A snapshot
keyed only by that directory would otherwise be served to the next case.

Per-account Claude rows (#10630) ask the provider who owns a directory's
credentials. No API test reaches the provider: the question is refused unless a
test answers it with a fixture, and a background revalidation a test started is
waited for while that test's patches still hold.
"""

from __future__ import annotations

import pytest


def _no_provider(_token: str) -> str:
    from scripts.api.claude_account_usage import ClaudeAccountRefused

    raise ClaudeAccountRefused("claude_account_identity_unavailable")


@pytest.fixture(autouse=True)
def _isolate_status_ttl_cache(monkeypatch):
    from scripts.api import claude_account_usage
    from scripts.api.state_helpers import cache_invalidate

    cache_invalidate()
    claude_account_usage._reset_for_tests()
    monkeypatch.setattr(claude_account_usage, "_claude_selected_identity", _no_provider)
    yield
    cache_invalidate()
    claude_account_usage._reset_for_tests()
