"""Isolate the process-global status cache between API tests.

Pytest shortens very long test names onto one temporary directory. A snapshot
keyed only by that directory would otherwise be served to the next case.

Per-account Claude rows (#10630) ask the provider who owns a directory's
credentials. No API test reaches the provider: the question is refused unless a
test answers it with a fixture, and a background revalidation a test started is
waited for while that test's patches still hold.

The probe refuses a sandbox inside Git, and the pre-push gate runs pytest with
its base temp inside the Git common directory, so every fixture path is truly
inside Git there (#10646). The sandbox's Git check judges only the directories
a test builds below ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _judge_git_below_tmp_path(tmp_path, monkeypatch):
    from scripts.api import claude_account_usage

    boundary = tmp_path.resolve()

    def inside_git(path: Path) -> bool:
        return any(
            claude_account_usage._git_tree(directory)
            for directory in (path, *path.parents)
            if directory.is_relative_to(boundary)
        )

    monkeypatch.setattr(claude_account_usage, "_inside_git", inside_git)


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
