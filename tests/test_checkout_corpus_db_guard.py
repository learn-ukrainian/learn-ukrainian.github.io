"""No test may create ``data/sources.db`` or ``data/vesum.db`` in the checkout (#9158).

A read-write ``sqlite3.connect`` creates a missing file. In CI (no corpus) a
module-level probe in ``tests/test_citation_resolution_invariant.py`` created
an empty ``data/sources.db`` while the shard was being collected, and later
tests in the shard took it for the real corpus database. These tests cover the
two guards in ``tests.conftest`` and the read-only openers that caused it.
Every checkout here is a throwaway directory in ``tmp_path``.
"""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import tests.conftest as guard
from scripts.wiki import source_attribution


@pytest.fixture
def checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A checkout with a ``data/`` directory and no corpus databases."""
    root = tmp_path / "checkout"
    (root / "data").mkdir(parents=True)
    monkeypatch.setattr(guard, "_REPO_ROOT", root)
    return root


@pytest.mark.parametrize("name", guard._CHECKOUT_CORPUS_DBS)
@pytest.mark.parametrize(
    "uri_query",
    [None, "?mode=rwc", "?mode=memory&mode=rwc", "?mode=rwc%00", "?mode=memory&mode=rwc%00"],
    ids=["plain-path", "uri-rwc", "uri-memory-then-rwc", "uri-rwc-nul", "uri-memory-then-rwc-nul"],
)
def test_connect_that_creates_a_corpus_db_fails_the_test_and_leaves_no_file(
    checkout: Path, name: str, uri_query: str | None
) -> None:
    target = checkout / name

    with pytest.raises(pytest.fail.Exception, match="created"):
        if uri_query is None:
            sqlite3.connect(str(target))
        else:
            sqlite3.connect(f"{target.as_uri()}{uri_query}", uri=True)

    assert not target.exists()


@pytest.mark.parametrize("query", ["?mode=ro", "?mode=rw"])
def test_non_creating_uri_connect_to_a_missing_db_raises_sqlite_error_and_creates_nothing(
    checkout: Path, query: str
) -> None:
    target = checkout / "data" / "sources.db"

    with pytest.raises(sqlite3.OperationalError):
        sqlite3.connect(f"{target.as_uri()}{query}", uri=True)

    assert not target.exists()


def test_memory_mode_connect_opens_in_memory_and_creates_nothing(checkout: Path) -> None:
    query = "?mode=memory"
    target = checkout / "data" / "sources.db"

    connection = sqlite3.connect(f"{target.as_uri()}{query}", uri=True)
    connection.execute("CREATE TABLE t (x)")
    connection.close()

    assert not target.exists()


def test_refusal_is_not_swallowed_by_a_broad_except(checkout: Path) -> None:
    def reader() -> None:
        with contextlib.suppress(Exception):
            sqlite3.connect(str(checkout / "data" / "sources.db"))

    with pytest.raises(pytest.fail.Exception):
        reader()


def test_read_write_connect_to_an_existing_db_and_to_other_paths_passes(checkout: Path, tmp_path: Path) -> None:
    existing = checkout / "data" / "sources.db"
    existing.touch()
    with contextlib.closing(sqlite3.connect(f"{existing.as_uri()}?mode=rw", uri=True)) as connection:
        connection.execute("CREATE TABLE t (x)")
    assert existing.stat().st_size > 0

    elsewhere = tmp_path / "scratch" / "sources.db"
    elsewhere.parent.mkdir()
    sqlite3.connect(str(elsewhere)).close()
    assert elsewhere.exists()


def _session(**config_attrs: object) -> SimpleNamespace:
    return SimpleNamespace(config=SimpleNamespace(**config_attrs), exitstatus=pytest.ExitCode.OK)


def test_session_that_creates_a_corpus_db_fails_and_names_it(
    checkout: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    session = _session()
    guard.pytest_sessionstart(session)
    (checkout / "data" / "vesum.db").write_bytes(b"")  # a subprocess the audit hook cannot see

    guard._enforce_no_checkout_corpus_db_created(session)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "data/vesum.db" in capsys.readouterr().out


def test_session_passes_when_the_corpus_db_existed_at_start(checkout: Path) -> None:
    (checkout / "data" / "sources.db").write_bytes(b"real corpus")
    session = _session()
    guard.pytest_sessionstart(session)

    guard._enforce_no_checkout_corpus_db_created(session)

    assert session.exitstatus == pytest.ExitCode.OK


def test_xdist_worker_takes_no_corpus_db_snapshot(checkout: Path) -> None:
    session = _session(workerinput={})
    guard.pytest_sessionstart(session)
    (checkout / "data" / "sources.db").write_bytes(b"")

    guard._enforce_no_checkout_corpus_db_created(session)

    assert session.exitstatus == pytest.ExitCode.OK


@pytest.fixture
def corpus_less_attribution(checkout: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """``scripts.wiki.source_attribution`` resolving into a checkout without a corpus."""
    monkeypatch.delenv(source_attribution.ENV_SOURCES_DB, raising=False)
    monkeypatch.setattr(source_attribution, "PROJECT_ROOT", checkout)
    monkeypatch.setattr(source_attribution, "DEFAULT_DB_PATH", checkout / "data" / "sources.db")
    return checkout / "data" / "sources.db"


def test_connect_sources_db_is_read_only_and_never_creates_the_db(corpus_less_attribution: Path) -> None:
    with pytest.raises(sqlite3.OperationalError):
        source_attribution.connect_sources_db()

    assert not corpus_less_attribution.exists()


def test_resolve_chunk_attribution_without_a_corpus_falls_back_and_creates_nothing(
    corpus_less_attribution: Path,
) -> None:
    attribution = source_attribution.resolve_chunk_attribution("textbook_grade3_s0001", "textbooks")

    assert attribution["title"] == "textbook_grade3_s0001"
    assert not corpus_less_attribution.exists()
