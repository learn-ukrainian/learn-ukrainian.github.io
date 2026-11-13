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

The same isolation is applied from ``tests/conftest.py``. A file collected
directly under ``tests/`` makes pytest scan that package again, and the new
``tests/api`` directory node does not receive the fixtures bound to the first
node. The parent fixture covers that node; these fixtures cover the first one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import judge_api_git_below_tmp_path, refuse_api_claude_provider, reset_api_status_caches


@pytest.fixture(autouse=True)
def _judge_git_below_tmp_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    judge_api_git_below_tmp_path(tmp_path, monkeypatch)


@pytest.fixture(autouse=True)
def _isolate_status_ttl_cache(monkeypatch: pytest.MonkeyPatch):
    reset_api_status_caches()
    refuse_api_claude_provider(monkeypatch)
    yield
    reset_api_status_caches()
