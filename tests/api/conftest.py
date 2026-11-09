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

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

# Product tests run the installed lu_machinery API; machinery-classified tests still exercise
# the retained in-tree scripts.api copy until it is deleted (machinery-move package 3, slice B2).
# The shared autouse isolation holds for both copies until then.
_API_PACKAGES = ("lu_machinery.api", "scripts.api")


def _api_modules(name: str) -> list:
    return [importlib.import_module(f"{package}.{name}") for package in _API_PACKAGES]


@pytest.fixture(autouse=True)
def _judge_git_below_tmp_path(tmp_path, monkeypatch):
    boundary = tmp_path.resolve()

    for claude_account_usage in _api_modules("claude_account_usage"):

        def inside_git(path: Path, _module=claude_account_usage) -> bool:
            return any(
                _module._git_tree(directory)
                for directory in (path, *path.parents)
                if directory.is_relative_to(boundary)
            )

        monkeypatch.setattr(claude_account_usage, "_inside_git", inside_git)


def _no_provider_for(claude_account_usage):
    def _no_provider(directory: int, account: str) -> None:
        raise claude_account_usage.ClaudeAccountRefused("claude_account_identity_unavailable")

    return _no_provider


def _reset_status_caches() -> None:
    for state_helpers in _api_modules("state_helpers"):
        state_helpers.cache_invalidate()
    for claude_account_usage in _api_modules("claude_account_usage"):
        claude_account_usage._reset_for_tests()


@pytest.fixture(autouse=True)
def _isolate_status_ttl_cache(monkeypatch):
    _reset_status_caches()
    for claude_account_usage in _api_modules("claude_account_usage"):
        monkeypatch.setattr(
            claude_account_usage,
            "_private_usage",
            lambda _module=claude_account_usage: SimpleNamespace(prove_claude_owner=_no_provider_for(_module)),
        )
    yield
    _reset_status_caches()
