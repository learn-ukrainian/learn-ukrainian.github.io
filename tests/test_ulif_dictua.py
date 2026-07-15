"""Focused offline tests for the official ULIF DictUA live-query cache."""

from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

source_query = importlib.import_module("rag.source_query")
sources_db = importlib.import_module("wiki.sources_db")

FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class _Response:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.mark.parametrize("name", ["privit-paradigm.html", "hovoryty-paradigm.html"])
def test_parses_noun_and_verb_paradigms(name: str):
    paradigm = source_query._parse_ulif_paradigm(_fixture(name))

    assert paradigm is not None
    rows = paradigm["rows"]
    assert isinstance(rows, list)
    assert any("інфінітив" in cell.casefold() for row in rows for cell in row) or any(
        "називний" in cell.casefold() for row in rows for cell in row
    )
    assert "raw_html" in paradigm


def test_canonical_headword_comes_from_the_returned_article():
    assert source_query._ulif_headword(_fixture("privit-paradigm.html"), "привіту") == "приві́т"


def test_search_result_requires_exact_stress_insensitive_membership(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        _fixture("privit-paradigm.html")
    ))
    monkeypatch.setattr(source_query._SESSION, "post", lambda *args, **kwargs: _Response(
        _fixture("privit-paradigm.html")
    ))

    assert source_query._ulif_search_result_matches(
        _fixture("privit-paradigm.html"), "ПРИВІТ"
    ) is True
    not_found = source_query.ulif_lookup("привіточок")

    assert not_found["status"] == "not_found"
    cached = sources_db.get_ulif_dictua_entry("привіточок")
    assert cached is not None
    assert cached["status"] == "not_found"
    assert cached["status"] != "ok"


def test_synonym_groups_preserve_order_registers_and_citations():
    groups = source_query._parse_ulif_relation_groups(
        _fixture("privit-synonyms.html"), "synonyms"
    )

    assert len(groups) >= 3
    assert [group["source_order"] for group in groups] == list(range(len(groups)))
    assert groups[0]["terms"][0]["text"] == "ВІТА́ННЯ"
    assert "розм." in groups[0]["register_labels"]
    assert "зах." in groups[0]["register_labels"]
    assert "фам." in {label for group in groups for label in group["register_labels"]}
    assert any("Леся Українка" in citation for citation in groups[0]["citations"])
    assert groups[0]["raw_html"].startswith("<p>")


def test_phraseology_and_antonym_groups_remain_structured():
    phraseology = source_query._parse_ulif_relation_groups(
        _fixture("privit-phraseology.html"), "phraseology"
    )
    antonyms = source_query._parse_ulif_relation_groups(
        _fixture("dobryi-antonyms.html"), "antonyms"
    )

    assert phraseology[0]["terms"][0]["text"].startswith("ні одві́ту")
    assert "Леся Українка" in " ".join(phraseology[0]["citations"])
    assert antonyms[0]["rows"][0]["left"]["terms"][0]["text"] == "ДОБРИЙ"
    assert antonyms[0]["rows"][0]["right"]["terms"][0]["text"] == "ЗЛИЙ"
    assert any(row["kind"] == "relation_note" for row in antonyms[0]["rows"])


def test_wrappers_share_one_complete_cached_lookup(tmp_path, monkeypatch):
    """A first wrapper fetches all available tabs; later ones issue no POST."""
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        _fixture("hovoryty-paradigm.html")
    ))

    calls: list[dict[str, str]] = []

    def post(_url: str, data: dict[str, str], timeout: int) -> _Response:
        calls.append(data)
        if "ctl00$ContentPlaceHolder1$search.x" in data:
            return _Response(_fixture("hovoryty-paradigm.html"))
        if "ctl00$ContentPlaceHolder1$syn.x" in data:
            return _Response(_fixture("hovoryty-synonyms.html"))
        if "ctl00$ContentPlaceHolder1$phras.x" in data:
            return _Response(_fixture("privit-phraseology.html"))
        if "ctl00$ContentPlaceHolder1$ant.x" in data:
            return _Response(_fixture("dobryi-antonyms.html"))
        raise AssertionError(f"Unexpected DictUA POST: {data}")

    monkeypatch.setattr(source_query._SESSION, "post", post)

    record = source_query.query_ulif("говорити")
    assert record["status"] == "ok"
    assert {
        "source_id", "official_url", "attribution_label", "retrieved_at",
        "content_sha256", "parser_version", "status",
    } <= record.keys()
    assert record["source_id"] == "ulif_dictua"
    assert source_query.query_ulif_synonyms("говорити")["sections"]
    assert source_query.query_ulif_phraseology("говорити")["sections"]
    assert source_query.query_ulif_antonyms("говорити")["sections"]

    # Search + every available image-button tab exactly once, not once per wrapper.
    assert len(calls) == 4
    assert db_path.exists()


def test_empty_available_relation_tab_is_not_a_parse_error(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        _fixture("hovoryty-paradigm.html")
    ))

    def post(_url: str, data: dict[str, str], timeout: int) -> _Response:
        if "ctl00$ContentPlaceHolder1$search.x" in data:
            return _Response(_fixture("hovoryty-paradigm.html"))
        if "ctl00$ContentPlaceHolder1$syn.x" in data:
            return _Response(_fixture("hovoryty-synonyms.html"))
        if "ctl00$ContentPlaceHolder1$phras.x" in data:
            # The tab remains visible, but its panel has no relation groups.
            return _Response(_fixture("hovoryty-paradigm.html"))
        if "ctl00$ContentPlaceHolder1$ant.x" in data:
            return _Response(_fixture("dobryi-antonyms.html"))
        raise AssertionError(f"Unexpected DictUA POST: {data}")

    monkeypatch.setattr(source_query._SESSION, "post", post)

    record = source_query.query_ulif("говорити", source_query.ULIF_SECTIONS)
    assert record["status"] == "ok"
    assert "phraseology" not in record["sections"]


def test_transient_error_is_not_persisted_as_a_negative_cache(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)

    def offline(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(source_query, "_get", offline)
    result = source_query.ulif_lookup("привіт")

    assert result["status"] == "transient_error"
    assert not db_path.exists(), "transient failures must not create cache entries"


def test_not_found_and_parse_error_are_distinguishable_and_cached(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        _fixture("privit-paradigm.html")
    ))
    # DictUA returns 200 with an unrelated selected article for a no-match;
    # `ulif_lookup` must use the result list, not cache that article as a hit.
    monkeypatch.setattr(source_query._SESSION, "post", lambda *args, **kwargs: _Response(
        _fixture("privit-paradigm.html")
    ))

    not_found = source_query.ulif_lookup("xzxqj")
    assert not_found["status"] == "not_found"
    assert sources_db.get_ulif_dictua_entry("xzxqj")["status"] == "not_found"

    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        "<html><body>missing WebForms controls</body></html>"
    ))
    parse_error = source_query.ulif_lookup("зламане")
    assert parse_error["status"] == "parse_error"
    assert sources_db.get_ulif_dictua_entry("зламане")["status"] == "parse_error"


def test_parse_error_keeps_successful_sections_and_legacy_paradigm(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        _fixture("privit-paradigm.html")
    ))
    missing_eventvalidation = _fixture("privit-synonyms.html").replace(
        'name="__EVENTVALIDATION"', 'name="__MISSING_EVENTVALIDATION"', 1
    )

    def post(_url: str, data: dict[str, str], timeout: int) -> _Response:
        if "ctl00$ContentPlaceHolder1$search.x" in data:
            return _Response(_fixture("privit-paradigm.html"))
        if "ctl00$ContentPlaceHolder1$syn.x" in data:
            return _Response(missing_eventvalidation)
        raise AssertionError(f"Unexpected DictUA POST: {data}")

    monkeypatch.setattr(source_query._SESSION, "post", post)

    record = source_query.query_ulif("привіт", source_query.ULIF_SECTIONS)

    assert record["status"] == "parse_error"
    assert record["sections"]["synonyms"][0]["terms"][0]["text"] == "ВІТА́ННЯ"
    cached = sources_db.get_ulif_dictua_entry("привіт")
    assert cached is not None
    assert cached["status"] == "parse_error"
    assert cached["sections"]["synonyms"][0]["terms"][0]["text"] == "ВІТА́ННЯ"
    assert sources_db.resolve_ulif_dictua_raw_response(cached["raw_response_ref"])
    assert source_query.ulif_paradigm("привіт") == {
        "word": "привіт",
        "rows": record["sections"]["paradigm"]["rows"],
    }


def test_parser_version_change_retries_a_cached_parse_error(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    sources_db.store_ulif_dictua_entry(
        word="зламане",
        canonical_headword="зламане",
        sections={},
        raw_responses={"paradigm": "<html>old parser failure</html>"},
        retrieved_at="2026-07-15T00:00:00+00:00",
        parser_version="ulif-dictua-v0",
        status="parse_error",
    )
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(
        "<html><body>still missing WebForms controls</body></html>"
    ))

    result = source_query.ulif_lookup("зламане")

    assert result["status"] == "parse_error"
    assert result["parser_version"] == source_query.ULIF_PARSER_VERSION


def test_legacy_ulif_paradigm_shape_uses_the_unified_cache(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    sources_db.store_ulif_dictua_entry(
        word="привіт",
        canonical_headword="привіт",
        sections={"paradigm": {"rows": [["Називний", "приві́т"]]}},
        raw_responses={"paradigm": "<html>cached</html>"},
        retrieved_at="2026-07-15T00:00:00+00:00",
        parser_version=source_query.ULIF_PARSER_VERSION,
        status="ok",
    )
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: pytest.fail(
        "cache hit unexpectedly accessed the network"
    ))

    assert source_query.ulif_paradigm("привіт") == {
        "word": "привіт",
        "rows": [["Називний", "приві́т"]],
    }
    conn = sqlite3.connect(str(db_path))
    try:
        assert conn.execute("SELECT COUNT(*) FROM ulif_dictua_raw_responses").fetchone()[0] == 2
    finally:
        conn.close()


def test_ulif_dictionary_rows_keep_conventional_fields_and_structure(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(sources_db, "_conn", None)
    sources_db.store_ulif_dictua_entry(
        word="великий",
        canonical_headword="великий",
        sections={
            "synonyms": [{"terms": [{"text": "величезний"}]}],
            "phraseology": [{"terms": [{"text": "ні в сих ні в тих"}]}],
        },
        raw_responses={
            "synonyms": "<html>official synonym group</html>",
            "phraseology": "<html>official phraseology group</html>",
        },
        retrieved_at="2026-07-15T00:00:00+00:00",
        parser_version=source_query.ULIF_PARSER_VERSION,
        status="ok",
    )

    synonyms = sources_db.search_synonyms("великий")
    idioms = sources_db.search_idioms("великий")

    for result, kind in ((synonyms[0], "synonyms"), (idioms[0], "phraseology")):
        assert result["word"] == "великий"
        assert result["source"] == (
            "«Словники України» (Український мовно-інформаційний фонд НАН України)"
        )
        assert result["definition"] == result["text"]
        assert result["definition"].startswith("Official DictUA")
        assert result["sections"][kind][0]["terms"]
        assert result["raw_response_ref"].startswith("sha256:")
