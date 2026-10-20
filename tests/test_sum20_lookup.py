"""Offline canonical СУМ-20 reader contract (#10655).

Public lookups read one local store. A miss is empty and never becomes a live
fetch, even when ``write=True``. ``data/lexdata.db`` wins when it already holds
``sum20_articles``; otherwise the read-only official sources collection is used.
Staging files are not a third store. ``LEXDATA_DB_PATH`` never falls back.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.request
from pathlib import Path

import pytest
import requests

from scripts.lexdata import generation, transforms
from scripts.lexicon import sum20_lookup
from scripts.lexicon.sum20_lookup import (
    lookup_decolonized_heteronym_evidence,
    lookup_sum20_articles,
    lookup_sum20_cached,
)
from scripts.lexicon.sum20_store import Sum20StoreError, open_sources, open_sum20
from scripts.wiki import sources_db
from scripts.wiki.sum20_official import (
    PARSER_VERSION,
    ensure_sum20_official_schema,
    normalize_sum20_lookup,
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


def _publish_generation(tmp_path: Path, **overrides: object) -> None:
    """Synthetic publication metadata with the production digests."""
    from scripts.lexdata.schema import GENERATION_SCHEMA_VERSION

    meta = {
        "singleton": 1, "generation": "fixture", "status": "published",
        "generation_schema_version": GENERATION_SCHEMA_VERSION,
        "normalizer_digest": transforms.normalizer_digest(transforms.DEFAULT_BINDING),
        "l1_transform_digests": json.dumps(generation.current_transform_digests(transforms.DEFAULT_BINDING)),
        **{key: "{}" for key in (
            "input_manifest", "transform_manifest", "normalizer_manifest", "store_fingerprints", "diff_receipt"
        )},
        **overrides,
    }
    with sqlite3.connect(tmp_path) as conn:
        conn.execute("CREATE TABLE meta (" + ", ".join(f"{key}" for key in meta) + ")")
        conn.execute("INSERT INTO meta VALUES (" + ", ".join("?" for _ in meta) + ")", tuple(meta.values()))


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
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", repo)
    monkeypatch.delenv("LU_LEXDATA_DB", raising=False)
    monkeypatch.delenv("LU_SOURCES_DB", raising=False)


@pytest.fixture(autouse=True)
def isolated_store_roots(monkeypatch, tmp_path):
    _isolate_store_resolution(monkeypatch, tmp_path)


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
        "article_text": "ВОДА — synthetic article 42",
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

    with pytest.raises(Sum20StoreError, match="store_missing"):
        lookup_sum20_articles("вода", missing, write=True)
    with pytest.raises(Sum20StoreError, match="store_missing"):
        lookup_decolonized_heteronym_evidence("вода", missing, write=True)
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
    _publish_generation(lexdata)

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
    _publish_generation(empty)

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

    monkeypatch.setattr("scripts.lexicon.sum20_store.open_sources", refuse_sources)
    with pytest.raises(Sum20StoreError, match="store_missing"):
        lookup_sum20_articles("вода", write=True)
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
    with pytest.raises(Sum20StoreError, match="empty_override"):
        lookup_sum20_articles("вода")
    with pytest.raises(Sum20StoreError, match="empty_override"):
        sources_db.query_sum20("вода")


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
    _publish_generation(lexdata)
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
    _isolate_store_resolution(monkeypatch, tmp_path)
    repo = tmp_path / ".worktrees" / "grok" / "task"
    shadow = repo / "data" / "lexdata.db"
    shadow.parent.mkdir(parents=True)
    shadow.write_bytes(b"shadow-not-sqlite")
    monkeypatch.setattr("scripts.storage.topology.main_checkout_root", lambda _root: tmp_path)
    with pytest.raises(Sum20StoreError, match="worktree_local_store"):
        open_sum20(repository_root=repo)


def test_select_sum20_database_keeps_sources_when_lexdata_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    _seed_articles(tmp_path / "data")
    assert [row["wordid"] for row in lookup_sum20_articles("вода")] == [42]


def test_query_sum20_exclusive_file_does_not_fall_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate_store_resolution(monkeypatch, tmp_path)
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    monkeypatch.setenv("LEXDATA_DB_PATH", str(empty))
    with pytest.raises(Sum20StoreError, match="lexdata_unpublished"):
        sources_db.query_sum20("вода")


@pytest.mark.parametrize(("metadata", "reason"), [
    ({"status": "candidate"}, "lexdata_unpublished"),
    ({"normalizer_digest": "wrong"}, "normalizer_mismatch"),
    ({"l1_transform_digests": '{"unexpected": "digest"}'}, "lexdata_stale"),
])
def test_invalid_generation_never_falls_back(tmp_path, monkeypatch, metadata, reason):
    _isolate_store_resolution(monkeypatch, tmp_path)
    _seed_articles(tmp_path / "data")
    lexdata = _seed_articles(tmp_path, name="lexdata.db")
    _publish_generation(lexdata, **metadata)
    monkeypatch.setenv("LEXDATA_DB_PATH", str(lexdata))
    with pytest.raises(Sum20StoreError, match=reason):
        lookup_sum20_articles("вода")
    with pytest.raises(Sum20StoreError, match=reason):
        sources_db.query_sum20("вода")


@pytest.mark.parametrize("value", ["", " ", "relative.db", "file:store.db", "missing", "directory", "wrong"])
def test_invalid_exclusive_override_is_typed_and_path_free(tmp_path, monkeypatch, value):
    _isolate_store_resolution(monkeypatch, tmp_path)
    _seed_articles(tmp_path / "data")
    if value in {"missing", "directory", "wrong"}:
        target = tmp_path / value
        if value == "directory":
            target.mkdir()
        if value == "wrong":
            target.write_bytes(b"not a database")
        value = str(target)
    monkeypatch.setenv("LEXDATA_DB_PATH", value)
    for lookup in (lookup_sum20_articles, sources_db.query_sum20):
        with pytest.raises(Sum20StoreError) as exc:
            lookup("вода")
        assert str(tmp_path) not in str(exc.value)
        assert not hasattr(exc.value, "path")


def test_canonical_generation_connection_cannot_write_or_attach(tmp_path, monkeypatch):
    _isolate_store_resolution(monkeypatch, tmp_path)
    lexdata = _seed_articles(tmp_path / "data", name="lexdata.db")
    _publish_generation(lexdata)
    conn = open_sum20(repository_root=tmp_path)
    try:
        conn.execute("PRAGMA query_only=OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
        with pytest.raises(sqlite3.OperationalError, match="attached"):
            conn.execute("ATTACH ':memory:' AS other")
    finally:
        conn.close()


def test_reader_import_does_not_load_a_network_client(tmp_path):
    import subprocess
    import sys

    code = '''
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    assert name.split('.')[0] not in {'requests', 'httpx', 'aiohttp', 'urllib3'}, name
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import scripts.lexicon.sum20_lookup
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stderr


def test_enrichment_reads_canonical_store_without_network_import_or_fallback(tmp_path, monkeypatch):
    import builtins

    from scripts.lexicon import enrich_manifest

    _seed_articles(tmp_path / "data")
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"requests", "httpx", "aiohttp", "urllib3"}, name
        assert name not in {"scripts.rag.source_query", "scripts.wiki.sources_db"}, name
        return original(name, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("enrichment attempted an external fallback")

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr(enrich_manifest, "_fetch_slovnyk_entry", forbidden)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_base_row", forbidden)
    monkeypatch.setattr(enrich_manifest, "SOURCES_DB", tmp_path / "unrelated.db")
    stale = {"lookups": {"newsum": {"text": "external cached definition"}}}
    card = enrich_manifest._sum20_definition_card("вода", stale)
    assert card["definitions"] == ["synthetic stored definition"]
    assert enrich_manifest._sum20_definition_card("бракує", stale) is None
    rows = enrich_manifest._dictionary_definition_rows(None, "вода", cache=stale)
    assert [(row["source"], row["text"]) for row in rows] == [("СУМ-20", "synthetic stored definition")]
    assert enrich_manifest._dictionary_definition_rows(None, "бракує", cache=stale) == []
    assert enrich_manifest._homonym_dictionary_rows(None, "бракує", cache=stale) == []


@pytest.mark.parametrize("locality", ["network", "unknown"])
def test_reader_refuses_untrusted_locality(tmp_path, monkeypatch, locality):
    lexdata = _seed_articles(tmp_path, name="lexdata.db")
    monkeypatch.setenv("LEXDATA_DB_PATH", str(lexdata))
    monkeypatch.setattr("scripts.storage.topology._store_locality", lambda _path: locality)
    with pytest.raises(Sum20StoreError, match=f"locality_{locality}"):
        lookup_sum20_articles("вода")


def test_explicit_sources_binding_precedes_exclusive_environment(tmp_path, monkeypatch):
    db = _seed_articles(tmp_path)
    monkeypatch.setenv("LEXDATA_DB_PATH", "missing.db")
    assert lookup_sum20_articles("вода", db)[0]["wordid"] == 42


def test_sources_connection_cannot_write_or_attach(tmp_path):
    db = _seed_articles(tmp_path)
    conn = open_sources(db, repository_root=tmp_path)
    try:
        conn.execute("PRAGMA query_only=OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
        with pytest.raises(sqlite3.OperationalError, match="attached"):
            conn.execute("ATTACH ':memory:' AS other")
    finally:
        conn.close()


def test_injected_sources_binding_still_validates_locality(tmp_path, monkeypatch):
    db = _seed_articles(tmp_path)
    monkeypatch.setattr("scripts.storage.topology._store_locality", lambda _path: "network")
    with pytest.raises(Sum20StoreError, match="locality_network"):
        open_sources(db, repository_root=tmp_path)


def test_modern_lexdata_override_is_also_exclusive(tmp_path, monkeypatch):
    _seed_articles(tmp_path / "data")
    monkeypatch.setenv("LU_LEXDATA_DB", str(tmp_path / "absent.db"))
    with pytest.raises(Sum20StoreError, match="store_missing"):
        lookup_sum20_articles("вода")


def test_conflicting_overrides_are_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("LEXDATA_DB_PATH", str(tmp_path / "one.db"))
    monkeypatch.setenv("LU_LEXDATA_DB", str(tmp_path / "two.db"))
    with pytest.raises(Sum20StoreError, match="conflicting_lexdata_overrides"):
        lookup_sum20_articles("вода")


def test_exclusive_published_generation_requires_article_table(tmp_path, monkeypatch):
    empty = tmp_path / "lexdata.db"
    sqlite3.connect(empty).close()
    _publish_generation(empty)
    monkeypatch.setenv("LEXDATA_DB_PATH", str(empty))
    with pytest.raises(Sum20StoreError, match="sum20_table_missing"):
        lookup_sum20_articles("вода")


def test_sources_open_failure_is_a_path_free_typed_error(tmp_path, monkeypatch):
    db = _seed_articles(tmp_path)

    def failed_open(_path):
        raise sqlite3.OperationalError(str(tmp_path))

    monkeypatch.setattr("scripts.lexicon.sum20_store.open_readonly", failed_open)
    with pytest.raises(Sum20StoreError, match="sources_unavailable") as exc:
        open_sources(db, repository_root=tmp_path)
    assert str(tmp_path) not in str(exc.value)


def test_override_symlink_is_validated_at_its_target(tmp_path, monkeypatch):
    target = _seed_articles(tmp_path)
    _publish_generation(target)
    link = tmp_path / "link.db"
    link.symlink_to(target)
    monkeypatch.setenv("LEXDATA_DB_PATH", str(link))
    assert lookup_sum20_articles("вода")[0]["wordid"] == 42
    seen = []

    def network_target(path):
        seen.append(path)
        return "network"

    monkeypatch.setattr("scripts.storage.topology._store_locality", network_target)
    with pytest.raises(Sum20StoreError, match="locality_network"):
        lookup_sum20_articles("вода")
    assert seen == [target.resolve()]


def test_entry_enrichment_enforces_offline_even_when_environment_disables_it(tmp_path, monkeypatch):
    import os
    from contextlib import closing

    from scripts.lexicon import enrich_manifest
    from tests.test_lexicon_enrich_manifest import _conn

    _seed_articles(tmp_path / "data")
    monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "0")
    monkeypatch.setattr(enrich_manifest, "SLOVNYK_CACHE", tmp_path / "cache")
    monkeypatch.setattr(enrich_manifest, "verify_word", lambda *_args: [])
    monkeypatch.setattr(enrich_manifest, "verify_lemma", lambda *_args: [])
    monkeypatch.setattr(enrich_manifest, "classify_lemma", lambda *_args: {"classification": "unknown"})
    monkeypatch.setattr(enrich_manifest, "_polite_slovnyk_delay", lambda: None)

    def forbidden(*args, **kwargs):
        raise AssertionError("entry enrichment attempted network access")

    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr(requests.Session, "request", forbidden)
    entry = {"lemma": "вода", "pos": "noun"}
    with closing(_conn()) as conn:
        assert enrich_manifest.enrich_entry(entry, conn, {}) is True
    assert entry["enrichment"]["definition_cards"][0]["definitions"] == ["synthetic stored definition"]
    assert os.environ["LEXICON_SLOVNYK_OFFLINE"] == "0"
    assert not (tmp_path / "cache").exists()


def test_full_enrichment_passes_offline_environment_to_runner(tmp_path, monkeypatch):
    import os

    from scripts.lexicon import enrich_manifest
    from scripts.lexicon.runner import offline_engine

    monkeypatch.setenv("LEXICON_USE_RUNNER", "1")
    monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "0")
    monkeypatch.setattr(enrich_manifest, "_load_grac_frequency_cache", lambda: {})
    monkeypatch.setattr(enrich_manifest, "artifact_path", lambda *_args: tmp_path / "kaikki.json")
    seen = []

    def run(**kwargs):
        seen.append(enrich_manifest._phase1_offline_mode())
        assert enrich_manifest._phase1_offline_mode()
        return {"completed": 0, "entry_count": 0}

    monkeypatch.setattr(offline_engine, "enrich_offline_slice", run)
    assert enrich_manifest.enrich(tmp_path / "manifest.json", tmp_path / "fingerprint.json") == (0, 0)
    assert seen == [True]
    assert os.environ["LEXICON_SLOVNYK_OFFLINE"] == "0"


def _seed_mirror(tmp_path):
    path = tmp_path / "data" / "sum20_slovnyk_staging.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sum20_slovnyk_articles (lemma, headword, text, source_url, url)")
        conn.executemany("INSERT INTO sum20_slovnyk_articles VALUES (?, ?, ?, ?, ?)", [
            ("вода", "ВОДА", "mirror duplicate", "https://example.invalid/water", "water"),
            ("берег", "БЕРЕГ", "mirror-only definition", "https://example.invalid/bank", "bank"),
        ])
    return path


def test_unified_binding_official_wins_mirror_fills_and_miss_stays_local(tmp_path, monkeypatch):
    from scripts.lexicon import enrich_manifest

    db = _seed_articles(tmp_path / "data")
    with sqlite3.connect(db) as conn:
        _insert_article(conn, 99, "гора", "official-only definition")
    mirror = _seed_mirror(tmp_path)
    before = db.read_bytes(), mirror.read_bytes()
    calls = _forbid_network(monkeypatch)
    assert lookup_sum20_articles("вода")[0]["definition"] == "synthetic stored definition"
    assert lookup_sum20_articles("гора")[0]["definition"] == "official-only definition"
    assert "role" not in lookup_sum20_articles("вода")[0]
    rows = lookup_sum20_articles("БЕ\u0301РЕГ")
    assert rows == [{
        "headword": "БЕРЕГ", "definition": "mirror-only definition", "article_text": "mirror-only definition",
        "senses": [], "url": "https://example.invalid/bank", "role": "mirror_candidate",
    }]
    assert lookup_sum20_articles("бракує") == []
    card = enrich_manifest._sum20_definition_card("берег", {"lookups": {"newsum": {"text": "stale cache"}}})
    assert card["definitions"] == ["mirror-only definition"]
    assert card["role"] == "mirror_candidate"
    assert card["source_url"] == "https://example.invalid/bank"
    assert enrich_manifest._dictionary_definition_rows(None, "берег", cache={})[0]["role"] == "mirror_candidate"
    assert enrich_manifest._homonym_dictionary_rows(None, "берег")[0]["role"] == "mirror_candidate"
    # The normative official API must never promote mirror candidates.
    assert sources_db.query_sum20("берег") == []
    assert (db.read_bytes(), mirror.read_bytes()) == before
    assert calls == []


@pytest.mark.parametrize("origin_mirror", [False, True])
def test_xref_does_not_mix_official_and_mirror_roles(monkeypatch, origin_mirror):
    from scripts.lexicon import enrich_manifest as em

    monkeypatch.setattr(em, "_vesum_base_lemma", lambda word: word)
    origin = {"definitions": ["див. берег"]}
    target = {"definitions": ["synthetic target definition"]}
    (origin if origin_mirror else target)["role"] = "mirror_candidate"
    assert em._resolve_definition_xref(origin, "вода", lambda _: target) is None


@pytest.mark.parametrize("reader, text", [
    ("_definition_pointer_relations", "Те саме, що гора."),
    ("_definition_antonym_relations", "Протилежне гора."),
    ("_homonym_relations", "БЕРЕГ¹, а, ч. synthetic first. БЕРЕГ², а, ч. synthetic second."),
])
def test_mirror_relation_provenance_retains_candidate_role(tmp_path, monkeypatch, reader, text):
    from scripts.lexicon import enrich_manifest as em

    _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    with sqlite3.connect(mirror) as conn:
        conn.execute("UPDATE sum20_slovnyk_articles SET text=? WHERE lemma='берег'", (text,))
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda _: True)
    relations = getattr(em, reader)(None, "берег", cache={})
    assert len(relations) == 1
    assert relations[0]["role"] == "mirror_candidate"
    assert relations[0]["source_url"] == "https://example.invalid/bank"


def test_missing_mirror_is_a_plain_miss_and_creates_nothing(tmp_path):
    _seed_articles(tmp_path / "data")
    missing = tmp_path / "absent.db"
    assert lookup_sum20_articles("бракує") == []
    assert lookup_sum20_articles("бракує", mirror_db_path=missing) == []
    assert not missing.exists()


def test_mirror_connection_refuses_writes_and_attaches(tmp_path, monkeypatch):
    from scripts.lexicon import sum20_store

    _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    original = sum20_store.open_readonly
    inspected = []

    def inspect_connection(path):
        conn = original(path)
        if path == mirror:
            conn.execute("PRAGMA query_only=OFF")
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute("DELETE FROM sum20_slovnyk_articles")
            with pytest.raises(sqlite3.OperationalError, match="attached"):
                conn.execute("ATTACH DATABASE ':memory:' AS other")
            inspected.append(True)
        return conn

    monkeypatch.setattr(sum20_store, "open_readonly", inspect_connection)
    assert lookup_sum20_articles("берег")[0]["role"] == "mirror_candidate"
    assert inspected == [True, True]


@pytest.mark.parametrize("kind, reason", [("corrupt", "mirror_unavailable"), ("schema", "mirror_unavailable"),
                                         ("partial_schema", "mirror_unavailable"),
                                         ("network", "locality_network"), ("unknown", "locality_unknown")])
def test_invalid_mirror_is_typed_refusal_not_miss(tmp_path, monkeypatch, kind, reason):
    from scripts.storage import topology

    _seed_articles(tmp_path / "data")
    mirror = tmp_path / "mirror.db"
    if kind == "schema":
        sqlite3.connect(mirror).close()
    elif kind == "partial_schema":
        with sqlite3.connect(mirror) as conn:
            conn.execute("CREATE TABLE sum20_slovnyk_articles (lemma, url)")
    else:
        mirror.write_bytes(b"invalid sqlite")
    original = topology._store_locality
    if kind in {"network", "unknown"}:
        monkeypatch.setattr(topology, "_store_locality", lambda p: kind if p == mirror else original(p))
    # A bad mirror is not opened when official evidence already answers.
    assert lookup_sum20_articles("вода", mirror_db_path=mirror)[0]["wordid"] == 42
    with pytest.raises(Sum20StoreError, match=reason):
        lookup_sum20_articles("бракує", mirror_db_path=mirror)


def test_injected_mirror_binding_and_lexdata_precedence(tmp_path, monkeypatch):
    _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    injected = mirror.rename(tmp_path / "injected.db")
    assert lookup_sum20_articles("берег") == []
    assert lookup_sum20_articles("берег", mirror_db_path=injected)[0]["role"] == "mirror_candidate"
    lexdata = _seed_articles(tmp_path / "data", name="lexdata.db")
    with sqlite3.connect(lexdata) as conn:
        conn.execute("UPDATE sum20_articles SET definition_text='published definition'")
    _publish_generation(lexdata)
    assert lookup_sum20_articles("вода", mirror_db_path=injected)[0]["definition"] == "published definition"
    assert lookup_sum20_articles("берег", mirror_db_path=injected)[0]["role"] == "mirror_candidate"


@pytest.mark.parametrize("raw, queries", [
    ("Великдень", ("великдень", "ВЕЛИКДЕНЬ")),
    ("ООН", ("оон",)),
    ("варити / зварити", ("варити", "зварити")),
    ("Класти / Покласти", ("класти", "покласти")),
    ("П'ять", ("п’ять", "п`ять")),
    ("П’ять", ("п'ять",)),
])
def test_mirror_raw_titles_match_normalized_keys(tmp_path, raw, queries):
    db = _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    with sqlite3.connect(mirror) as conn:
        conn.execute("INSERT INTO sum20_slovnyk_articles VALUES (?, ?, ?, ?, ?)",
                     (raw, "synthetic heading", "unaltered article", "", "selected"))
    before = mirror.read_bytes()
    for query in queries:
        assert lookup_sum20_articles(query, db, mirror_db_path=mirror) == [{
            "headword": "synthetic heading", "definition": "unaltered article",
            "article_text": "unaltered article", "senses": [], "url": "selected", "role": "mirror_candidate",
        }]
    assert lookup_sum20_articles("бракує", db, mirror_db_path=mirror) == []
    assert mirror.read_bytes() == before


@pytest.mark.parametrize("query, titles, expected", [
    ("Великдень", [("ВЕЛИКДЕНЬ", "a"), ("Великдень", "z")], "z"),
    ("великдень", [("великдень / свято", "a"), ("Великдень", "z")], "z"),
    ("великдень", [("ВЕЛИКДЕНЬ", "z"), ("Великдень", "a")], "a"),
    ("варити", [("варити / зварити", "z"), ("варити / наварити", "a")], "a"),
    ("варити", [("варити", "z"), ("варити", "a")], "a"),
])
def test_mirror_match_precedence_selects_one_article(tmp_path, query, titles, expected):
    db = _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    with sqlite3.connect(mirror) as conn:
        for raw, url in titles:
            conn.execute("INSERT INTO sum20_slovnyk_articles VALUES (?, ?, ?, ?, ?)",
                         (raw, raw, url + " text", "", url))
    result = lookup_sum20_articles(query, db, mirror_db_path=mirror)
    assert len(result) == 1
    assert result[0]["url"] == expected
    assert result[0]["definition"] == expected + " text"
    assert result[0]["role"] == "mirror_candidate"


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_mirror_index_reused_and_invalidated_on_store_change(tmp_path, journal_mode):
    from scripts.lexicon import sum20_store

    db = _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    sum20_store._mirror_index.cache_clear()
    with sqlite3.connect(mirror) as conn:
        conn.execute("PRAGMA journal_mode=" + journal_mode)
        assert lookup_sum20_articles("берег", db, mirror_db_path=mirror)[0]["definition"] == "mirror-only definition"
        assert lookup_sum20_articles("берег", db, mirror_db_path=mirror)[0]["definition"] == "mirror-only definition"
        info = sum20_store._mirror_index.cache_info()
        assert (info.hits, info.misses) == (1, 1)
        conn.execute("INSERT INTO sum20_slovnyk_articles VALUES (?, ?, ?, ?, ?)",
                     ("Різдво", "Різдво", "new article", "", "new"))
        conn.commit()
        assert lookup_sum20_articles("різдво", db, mirror_db_path=mirror)[0]["definition"] == "new article"
        assert sum20_store._mirror_index.cache_info().misses == 2


def test_official_wins_over_normalized_mirror_match(tmp_path):
    db = _seed_articles(tmp_path / "data")
    mirror = _seed_mirror(tmp_path)
    with sqlite3.connect(mirror) as conn:
        conn.execute("UPDATE sum20_slovnyk_articles SET lemma='Вода' WHERE lemma='вода'")
    assert lookup_sum20_articles("вода", db, mirror_db_path=mirror)[0]["definition"] == "synthetic stored definition"
