"""Offline canonical СУМ-20 reader contract (#10655).

Public lookups read one local store. A miss is empty and never becomes a live
fetch, even when ``write=True``. ``data/lexdata.db`` wins when it already holds
``sum20_articles``; otherwise the read-only official sources collection is used.
Staging files are not a third store. ``LEXDATA_DB_PATH`` never falls back.
"""

from __future__ import annotations

import sqlite3
import urllib.request
from pathlib import Path

import pytest
import requests

from scripts.lexicon import sum20_lookup
from scripts.lexicon.sum20_lookup import (
    lookup_decolonized_heteronym_evidence,
    lookup_sum20_articles,
    lookup_sum20_cached,
)
from scripts.wiki import sources_db
from scripts.wiki.sum20_official import (
    PARSER_VERSION,
    Sum20DatabaseSelection,
    ensure_sum20_official_schema,
    normalize_sum20_lookup,
    select_sum20_database,
)

_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "lexicon" / "sum20_lookup.py"
_FORBIDDEN_SOURCE_TOKENS = (
    "requests",
    "httpx",
    "urlopen",
    "BeautifulSoup",
    "fetch_and_cache_sum20",
    "sum20ua.com",
)


def _forbid_network(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Replace HTTP entry points so any live call fails the test."""
    calls: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("offline СУМ-20 lookup attempted a network request")

    monkeypatch.setattr(requests, "get", forbidden)
    monkeypatch.setattr(requests.api, "get", forbidden)
    monkeypatch.setattr(requests.Session, "request", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    return calls


def _isolate_store_resolution(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    """Point default resolution at ``repo`` and ignore the real sources file."""
    monkeypatch.delenv("LEXDATA_DB_PATH", raising=False)
    monkeypatch.delenv("SOURCES_DB_PATH", raising=False)
    monkeypatch.setattr(sum20_lookup, "REPO_ROOT", repo)
    sum20_lookup._resolve_primary_checkout.cache_clear()


def _seed_articles(tmp_path: Path, *, with_sum11: bool = False, name: str = "sources.db") -> Path:
    """One synthetic stored article. The gloss is fixture text, not a citation."""
    db = tmp_path / name
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    ensure_sum20_official_schema(conn)
    conn.execute(
        """
        INSERT INTO sum20_articles (
            wordid, normalized_lookup_key, headword, stressed_headword, pos, grammar,
            article_html, article_text, definition_text, official_url, fetched_at,
            content_sha256, parser_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            42,
            normalize_sum20_lookup("вода"),
            "ВОДА",
            "ВОДА́",
            "ж.",
            "и, ж.",
            "<article>synthetic</article>",
            "ВОДА — synthetic article 42",
            "synthetic stored definition",
            "https://example.invalid/sum20/42",
            "2026-10-20T00:00:00+00:00",
            "synthetic-digest",
            PARSER_VERSION,
        ),
    )
    article_id = conn.execute("SELECT id FROM sum20_articles WHERE wordid = 42").fetchone()
    assert article_id is not None
    conn.execute(
        """
        INSERT INTO sum20_senses (article_id, sense_order, definition, register_labels)
        VALUES (?, 1, ?, ?)
        """,
        (article_id[0], "synthetic stored definition", "[]"),
    )
    if with_sum11:
        conn.execute(
            """
            CREATE TABLE sum11 (
                word TEXT,
                definition TEXT,
                text TEXT,
                sovietization_risk INTEGER,
                sovietization_keywords TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO sum11 (word, definition, text, sovietization_risk, sovietization_keywords)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("вода", "synthetic occupation gloss", "synthetic text", 3, "ідеологія, радянський"),
        )
    conn.commit()
    conn.close()
    return db


def _insert_article(conn: sqlite3.Connection, wordid: int, key: str, definition: str) -> None:
    conn.execute(
        """
        INSERT INTO sum20_articles (
            wordid, normalized_lookup_key, headword, stressed_headword, pos, grammar,
            article_html, article_text, definition_text, official_url, fetched_at,
            content_sha256, parser_version
        ) VALUES (?, ?, ?, ?, '', '', '<article>synthetic</article>', ?, ?, ?, ?, ?, ?)
        """,
        (
            wordid,
            normalize_sum20_lookup(key),
            key.upper(),
            key.upper(),
            definition,
            definition,
            f"https://example.invalid/sum20/{wordid}",
            "2026-10-20T00:00:00+00:00",
            f"digest-{wordid}",
            PARSER_VERSION,
        ),
    )


def _expected_article(article_id: int) -> dict[str, object]:
    return {
        "id": article_id,
        "wordid": 42,
        "headword": "ВОДА",
        "stressed_headword": "ВОДА́",
        "pos": "ж.",
        "grammar": "и, ж.",
        "definition": "synthetic stored definition",
        "senses": [
            {
                "sense_order": 1,
                "definition": "synthetic stored definition",
                "register_labels": [],
            }
        ],
        "url": "https://example.invalid/sum20/42",
    }


def test_reader_source_has_no_live_client() -> None:
    source = _MODULE_PATH.read_text(encoding="utf-8")
    present = [token for token in _FORBIDDEN_SOURCE_TOKENS if token in source]
    assert present == []


def test_unknown_lemma_is_a_local_miss(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _forbid_network(monkeypatch)
    db = _seed_articles(tmp_path)
    before = db.read_bytes()

    assert lookup_sum20_articles("неіснуючеслово", db) == []
    assert lookup_sum20_articles("неіснуючеслово", db, write=True) == []
    bundle = lookup_decolonized_heteronym_evidence("неіснуючеслово", db, write=True)

    assert bundle == {
        "lemma": "неіснуючеслово",
        "modern_sum20": [],
        "soviet_colonization_context": None,
    }
    assert calls == []
    assert db.read_bytes() == before


def test_write_true_on_a_missing_database_creates_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _forbid_network(monkeypatch)
    missing = tmp_path / "absent.db"

    assert lookup_sum20_articles("вода", missing, write=True) == []
    assert lookup_decolonized_heteronym_evidence("вода", missing, write=True) == {
        "lemma": "вода",
        "modern_sum20": [],
        "soviet_colonization_context": None,
    }
    assert calls == []
    assert not missing.exists()


def test_known_lemma_returns_the_stored_article_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _forbid_network(monkeypatch)
    db = _seed_articles(tmp_path)
    before = db.read_bytes()
    with sqlite3.connect(db) as conn:
        article_id = conn.execute("SELECT id FROM sum20_articles WHERE wordid = 42").fetchone()[0]
    expected = [_expected_article(article_id)]

    plain = lookup_sum20_articles("вода", db)
    accented = lookup_sum20_articles("во\u0301да", db, write=True)
    again = lookup_sum20_articles("ВОДА", db, write=False)

    assert plain == accented == again == expected
    assert calls == []
    assert db.read_bytes() == before


def test_heteronym_bundle_reads_both_local_layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _forbid_network(monkeypatch)
    db = _seed_articles(tmp_path, with_sum11=True)
    before = db.read_bytes()
    with sqlite3.connect(db) as conn:
        article_id = conn.execute("SELECT id FROM sum20_articles WHERE wordid = 42").fetchone()[0]

    first = lookup_decolonized_heteronym_evidence("Вода", db)
    second = lookup_decolonized_heteronym_evidence("Вода", db, write=True)

    assert first == second
    assert first["lemma"] == "Вода"
    assert first["modern_sum20"] == [_expected_article(article_id)]
    context = first["soviet_colonization_context"]
    assert isinstance(context, dict)
    assert context["source"] == "СУМ-11 (1970–1980)"
    assert context["red_flag"] is True
    assert context["definition"] == "synthetic occupation gloss"
    assert context["sovietization_risk"] == 3
    assert context["keywords"] == ["ідеологія", "радянський"]
    assert "СУМ-11" in str(context["historical_note"])
    assert calls == []
    assert db.read_bytes() == before


def test_database_without_the_article_table_is_an_empty_miss(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _forbid_network(monkeypatch)
    bare = tmp_path / "bare.db"
    sqlite3.connect(bare).close()

    assert lookup_sum20_articles("вода", bare) == []
    assert lookup_sum20_articles("вода", bare, write=True) == []
    assert calls == []


def test_prefix_match_keeps_homonym_labels_and_exact_query_does_not(tmp_path: Path) -> None:
    db = tmp_path / "articles.db"
    conn = sqlite3.connect(db)
    ensure_sum20_official_schema(conn)
    _insert_article(conn, 1, "вода", "synthetic base")
    _insert_article(conn, 2, "вода 2", "synthetic homonym")
    conn.commit()
    conn.row_factory = sqlite3.Row
    try:
        prefixed = [row["wordid"] for row in lookup_sum20_cached("вода", conn, prefix=True)]
        exact = [row["wordid"] for row in lookup_sum20_cached("вода", conn, prefix=False)]
    finally:
        conn.close()

    assert prefixed == [1, 2]
    assert exact == [1]
    assert [row["wordid"] for row in lookup_sum20_articles("вода", db)] == [1, 2]
    assert [int(row["source_record_id"]) for row in sources_db.query_sum20("вода", db_path=db)] == [1]


def test_lexdata_with_articles_replaces_the_sources_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    sources = _seed_articles(tmp_path / "data")
    lexdata = tmp_path / "data" / "lexdata.db"
    conn = sqlite3.connect(lexdata)
    ensure_sum20_official_schema(conn)
    _insert_article(conn, 7, "вода", "synthetic canonical definition")
    conn.commit()
    conn.close()

    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)
    rows = lookup_sum20_articles("вода")
    records = sources_db.query_sum20("вода")

    assert [row["wordid"] for row in rows] == [7]
    assert [int(record["source_record_id"]) for record in records] == [7]
    assert sources.is_file()


def test_lexdata_without_the_article_table_falls_back_to_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    sources = _seed_articles(tmp_path / "data")
    empty = tmp_path / "data" / "lexdata.db"
    sqlite3.connect(empty).close()

    assert [row["wordid"] for row in lookup_sum20_articles("вода")] == [42]
    assert sources.is_file()


def test_exclusive_lexdata_override_does_not_read_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    sources = _seed_articles(tmp_path / "data")
    before = sources.read_bytes()
    missing = tmp_path / "missing-lexdata.db"
    monkeypatch.setenv("LEXDATA_DB_PATH", str(missing))

    def refuse_sources() -> Path:
        raise AssertionError("exclusive SUM-20 override fell back to sources")

    monkeypatch.setattr(sum20_lookup, "_resolve_sources_db", refuse_sources)
    assert lookup_sum20_articles("вода", write=True) == []
    assert not missing.exists()
    assert sources.read_bytes() == before


def test_blank_lexdata_override_is_an_empty_miss(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    _seed_articles(tmp_path / "data")
    monkeypatch.setenv("LEXDATA_DB_PATH", " ")
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)

    def refuse_open(*_args: object, **_kwargs: object) -> sqlite3.Connection:
        raise AssertionError("blank LEXDATA_DB_PATH opened a database")

    monkeypatch.setattr(sources_db, "_get_conn_for", refuse_open)
    assert lookup_sum20_articles("вода") == []
    assert sources_db.query_sum20("вода") == []


def test_staging_database_is_not_a_lookup_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    _seed_articles(tmp_path / "data")
    staging = tmp_path / "data" / "sum20_staging.db"
    conn = sqlite3.connect(staging)
    ensure_sum20_official_schema(conn)
    _insert_article(conn, 99, "вода", "synthetic staging-only definition")
    conn.commit()
    conn.close()

    assert [row["wordid"] for row in lookup_sum20_articles("вода")] == [42]


def test_default_bundle_splits_canonical_sum20_from_sources_sum11(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    sources = _seed_articles(tmp_path / "data", with_sum11=True)
    # Move the modern article out of sources so only lexdata can supply it.
    lexdata = tmp_path / "data" / "lexdata.db"
    sources.replace(lexdata)
    bare = tmp_path / "data" / "sources.db"
    conn = sqlite3.connect(bare)
    conn.execute(
        """
        CREATE TABLE sum11 (
            word TEXT, definition TEXT, text TEXT,
            sovietization_risk INTEGER, sovietization_keywords TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO sum11 VALUES (?, ?, ?, ?, ?)",
        ("вода", "synthetic occupation gloss", "synthetic text", 3, "ідеологія"),
    )
    conn.commit()
    conn.close()

    bundle = lookup_decolonized_heteronym_evidence("вода")
    assert [row["wordid"] for row in bundle["modern_sum20"]] == [42]
    assert bundle["soviet_colonization_context"]["keywords"] == ["ідеологія"]


def test_select_sum20_database_ignores_a_worktree_shadow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEXDATA_DB_PATH", raising=False)
    repo = tmp_path / ".worktrees" / "grok" / "task"
    shadow = repo / "data" / "lexdata.db"
    shadow.parent.mkdir(parents=True)
    shadow.write_bytes(b"shadow-not-sqlite")
    primary = tmp_path / "data" / "lexdata.db"
    primary.parent.mkdir()
    primary.write_bytes(b"primary-bytes")
    probed: list[Path] = []

    def probe(path: Path) -> bool:
        probed.append(path)
        return path.resolve() == primary.resolve()

    selection = select_sum20_database(repo, article_table_present=probe)
    assert selection.exclusive is False
    assert selection.path is not None
    assert selection.path.resolve() == primary.resolve()
    assert [path.resolve() for path in probed] == [primary.resolve()]


def test_select_sum20_database_keeps_sources_when_lexdata_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LEXDATA_DB_PATH", raising=False)
    calls: list[Path] = []

    def probe(path: Path) -> bool:
        calls.append(path)
        return True

    selection = select_sum20_database(tmp_path, article_table_present=probe)
    assert selection == Sum20DatabaseSelection(path=None, exclusive=False)
    assert calls == []


def test_query_sum20_exclusive_file_does_not_fall_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    monkeypatch.setenv("LEXDATA_DB_PATH", str(empty))
    opened: list[object] = []
    original = sources_db._get_conn_for

    def wrapped(db_path: object = None) -> sqlite3.Connection:
        opened.append(db_path)
        return original(db_path)

    monkeypatch.setattr(sources_db, "_get_conn_for", wrapped)
    assert sources_db.query_sum20("вода") == []
    assert opened == [empty]
