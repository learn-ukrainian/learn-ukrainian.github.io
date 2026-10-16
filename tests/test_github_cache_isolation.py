"""Regression tests for the shared GitHub cache: isolation, reset clamp, and the sweep."""

import logging
import math
import os
import sqlite3
from pathlib import Path

import pytest

from scripts.common import github_client as gh
from tests.common.github_cache_isolation import isolate_github_client_cache, production_github_cache_directory


@pytest.fixture(autouse=True)
def _isolate_github_client_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


def _client(tmp_path, now):
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append(endpoint)
        return gh.Response(
            200,
            {"X-RateLimit-Remaining": "5000", "X-RateLimit-Reset": str(now + 30)},
            b'{"ok":true}',
        )

    store = gh.GitHubClient(
        cache_dir=tmp_path / "cache",
        env={"GH_TOKEN": "unit-token"},
        clock=lambda: now,
        transport=transport,
    )
    return store, calls


def _rows(store):
    with store._db() as db:
        return db.execute(
            "SELECT resource, remaining, reset FROM budget WHERE scope=? ORDER BY resource",
            (store.scope,),
        ).fetchall()


def test_client_without_cache_dir_stays_on_the_test_override():
    store = gh.GitHubClient(env={"GH_REPO": "o/r", "PATH": os.environ.get("PATH", "")})
    assert store.cache_dir.resolve() == Path(os.environ["LU_GITHUB_CACHE_DIR"]).resolve()
    production = production_github_cache_directory()
    assert production is None or store.cache_dir.resolve() != Path(production).resolve()


def test_production_cache_connect_is_refused():
    """The guard raises before sqlite opens the shared cache.

    Reverting the autouse fixture removes ``guards_production_github_cache``,
    so this assertion fails before ``connect`` is called.
    """
    assert getattr(gh.sqlite3.connect, "guards_production_github_cache", False)
    production = production_github_cache_directory()
    assert production is not None
    with pytest.raises(AssertionError, match="production GitHub cache"):
        gh.sqlite3.connect(Path(production) / "cache.sqlite3")


@pytest.mark.parametrize(
    "reset",
    [4_000_000_000, math.nan, math.inf, "4000000000", -5, 0, True],
)
def test_store_budget_refuses_implausible_resets(tmp_path, reset):
    """Reverting the write clamp stores these values and this assertion fails."""
    now = 1_700_000_000
    store, _calls = _client(tmp_path, now)
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 77, reset, now=now)
    assert _rows(store) == []


def test_far_future_reset_already_stored_does_not_refuse(tmp_path, caplog):
    """Reverting the read clamp refuses this call with core_below_landing_reserve."""
    now = 1_700_000_000
    store, calls = _client(tmp_path, now)
    gh._IMPLAUSIBLE_RESET_LOGGED = False
    with store._db() as db:
        db.execute("INSERT INTO budget VALUES (?,?,?,?)", (store.scope, "core", 77, 4_000_000_000))
    with caplog.at_level(logging.DEBUG, logger="scripts.common.github_client"):
        result = store.request("GET", "user")
        again = store.request("GET", "user")
    assert result.error is None and again.error is None and calls == ["user", "user"]
    records = [record for record in caplog.records if "ignoring implausible GitHub budget reset" in record.message]
    assert len(records) == 1 and records[0].levelno == logging.DEBUG


@pytest.mark.parametrize("reset", [math.nan, math.inf, "not-a-reset", -5, 0])
def test_implausible_reset_already_stored_does_not_refuse(tmp_path, reset, caplog):
    """Reverting the read clamp refuses, raises, or admits without the debug log."""
    now = 1_700_000_000
    store, calls = _client(tmp_path, now)
    gh._IMPLAUSIBLE_RESET_LOGGED = False
    with store._db() as db:
        db.execute("INSERT INTO budget VALUES (?,?,?,?)", (store.scope, "core", 77, reset))
    with caplog.at_level(logging.DEBUG, logger="scripts.common.github_client"):
        result = store.request("GET", "user")
    assert result.error is None and calls == ["user"]
    assert any("ignoring implausible GitHub budget reset" in record.message for record in caplog.records)


def test_past_reset_is_stored_and_does_not_refuse(tmp_path):
    now = 1_700_000_000
    past = now - 50
    store, calls = _client(tmp_path, now)
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 0, past, now=now)
    assert _rows(store) == [("core", 0, past)]
    assert store.request("GET", "user").error is None and calls == ["user"]


def test_reset_exactly_at_horizon_still_keeps_the_landing_reserve(tmp_path):
    """A reset two hours out is still a window. Dropping it would admit this call."""
    now = 1_700_000_000
    horizon = now + gh.BUDGET_RESET_HORIZON_SECONDS
    store, calls = _client(tmp_path, now)
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 77, horizon, now=now)
    result = store.request("GET", "user")
    assert result.error == "github_rate_limited" and result.reason == "core_below_landing_reserve"
    assert result.reset_at == horizon and calls == []


def test_healthy_low_core_budget_still_refuses(tmp_path):
    now = 1_700_000_000
    reset = now + 60
    store, calls = _client(tmp_path, now)
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 77, reset, now=now)
    result = store.request("GET", "user")
    assert _rows(store) == [("core", 77, reset)]
    assert result.error == "github_rate_limited" and result.reason == "core_below_landing_reserve"
    assert result.reset_at == reset and calls == []


def test_implausible_budget_rows_lists_reset_and_remaining_only(tmp_path):
    """Reverting the sweep (or its bounds) changes this exact list."""
    now = 1_700_000_000
    horizon = now + gh.BUDGET_RESET_HORIZON_SECONDS
    path = tmp_path / "cache.sqlite3"
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE budget (scope TEXT, resource TEXT, remaining INTEGER, reset INTEGER,"
        " PRIMARY KEY(scope, resource))"
    )
    db.executemany(
        "INSERT INTO budget VALUES (?,?,?,?)",
        [
            ("scope", "far", 77, 4_000_000_000),
            ("scope", "negative-remaining", -1, now + 10),
            ("scope", "above-limit", gh.MAX_BUDGET_REMAINING + 1, now + 10),
            ("scope", "at-limit", gh.MAX_BUDGET_REMAINING, horizon),
            ("scope", "healthy", 77, now + 60),
            ("scope", "past", 10, now - 5),
            ("scope", "zero", 10, 0),
            ("scope", "text", 10, "not-a-reset"),
        ],
    )
    db.commit()
    before = db.execute("SELECT COUNT(*) FROM budget").fetchone()
    found = gh.implausible_budget_rows(db, now=now)
    after = db.execute("SELECT COUNT(*) FROM budget").fetchone()
    db.close()
    assert before == after == (8,)
    assert [(row["resource"], row["reasons"]) for row in found] == [
        ("above-limit", ("remaining",)),
        ("far", ("reset",)),
        ("negative-remaining", ("remaining",)),
        ("text", ("reset",)),
        ("zero", ("reset",)),
    ]
    ro = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        assert gh.implausible_budget_rows(ro, now=now) == found
    finally:
        ro.close()
