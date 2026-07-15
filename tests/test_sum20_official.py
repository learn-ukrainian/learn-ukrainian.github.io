"""Offline parser, crawl-state, and lookup coverage for official СУМ-20."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ingest import sum20_official_ingest
from rag.source_query import query_sum20 as source_query_sum20
from wiki.sum20_official import (
    FetchOutcome,
    Sum20ParseError,
    ensure_sum20_official_schema,
    fetch_sum20_wordid,
    parse_sum20_article,
    upsert_sum20_article,
)

from wiki import sources_db

FIXTURES = Path(__file__).parent / "fixtures" / "sum20_official"


@pytest.mark.parametrize(
    ("wordid", "stressed_headword"),
    [
        (5, "АБАЖУ́Р"),
        (6, "АБАЖУ́РНИЙ"),
        (7, "АБАЖУ́РЧИК"),
        (8, "АБА́К"),
        (9, "АБА́КА"),
        (10, "АБА́Т"),
        (11, "АБАТИ́СА"),
        (12, "АБА́ТСТВО"),
    ],
)
def test_parser_reads_each_captured_official_fixture(wordid: int, stressed_headword: str) -> None:
    article = parse_sum20_article((FIXTURES / f"wordid-{wordid}.html").read_text(encoding="utf-8"), wordid)

    assert article.stressed_headword == stressed_headword
    assert article.headword not in article.stressed_headword
    assert article.senses
    assert article.content_sha256


def test_parser_preserves_grammar_citations_and_ordered_multiple_senses() -> None:
    abajur = parse_sum20_article((FIXTURES / "wordid-5.html").read_text(encoding="utf-8"), 5)
    abac = parse_sum20_article((FIXTURES / "wordid-8.html").read_text(encoding="utf-8"), 8)

    assert abajur.headword == "АБАЖУР"
    assert abajur.stressed_headword == "АБАЖУ́Р"
    assert abajur.grammar == "а, ч."
    assert abajur.pos == "ч."
    assert abajur.senses[0].definition.startswith("Частина світильника")
    assert [citation.parsed_bib_fields["author"] for citation in abajur.citations[:2]] == [
        "М. Коцюбинський",
        "Леся Українка",
    ]
    assert [sense.sense_order for sense in abac.senses] == [1, 2]
    assert [sense.register_labels for sense in abac.senses] == [["іст."], ["архт."]]
    assert abac.senses[1].definition == "Те саме, що аба́ка."


def test_parser_rejects_non_article_html() -> None:
    with pytest.raises(Sum20ParseError, match="<article>"):
        parse_sum20_article("<html><body>blocked</body></html>", 99)


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "", headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class _FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = iter(responses)
        self.headers: dict[str, str] = {}

    def get(self, *_args, **_kwargs):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_fetch_statuses_never_turn_transient_or_parse_failures_into_misses() -> None:
    not_found = fetch_sum20_wordid(999, session=_FakeSession([_FakeResponse(404)]), retries=0)
    transient_delays: list[float] = []
    transient = fetch_sum20_wordid(
        999,
        session=_FakeSession([_FakeResponse(503), _FakeResponse(503)]),
        retries=1,
        retry_backoff_s=1.5,
        sleep=transient_delays.append,
    )
    malformed = fetch_sum20_wordid(
        999,
        session=_FakeSession([_FakeResponse(200, "<html>not an article</html>")]),
        retries=0,
    )

    assert not_found.status == "not_found"
    assert transient.status == "transient_error"
    assert transient_delays == [1.5]
    assert malformed.status == "parse_error"


def test_offline_query_returns_all_records_with_official_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_sum20_official_schema(conn)
        article = parse_sum20_article((FIXTURES / "wordid-5.html").read_text(encoding="utf-8"), 5)
        duplicate_homograph = replace(article, wordid=105)
        with conn:
            assert upsert_sum20_article(conn, article, fetched_at="2026-07-15T10:00:00+00:00")
            assert upsert_sum20_article(conn, duplicate_homograph, fetched_at="2026-07-15T10:01:00+00:00")

        fts_matches = conn.execute(
            "SELECT rowid FROM sum20_articles_fts WHERE sum20_articles_fts MATCH ?",
            ("світильника",),
        ).fetchall()
        assert len(fts_matches) == 2
    finally:
        conn.close()

    records = sources_db.query_sum20("абажу́р", db_path=db_path)
    source_query_records = source_query_sum20("абажур", db_path=str(db_path))

    assert [record["source_record_id"] for record in records] == ["5", "105"]
    assert source_query_records == records
    for record in records:
        assert record["source_id"] == "sum20_official"
        assert record["official_url"] == f"https://sum20ua.com/?wordid={record['source_record_id']}"
        assert record["retrieved_at"]
        assert record["content_sha256"]
        assert record["parser_version"]
        assert record["status"] == "ok"
        assert record["attribution_label"] == (
            "Словник української мови у 20 томах (УМІФ НАН України; "
            "Інститут мовознавства ім. О. О. Потебні НАН України)"
        )
        assert "slovnyk.me" not in json.dumps(record, ensure_ascii=False)


def test_ingest_keeps_transient_failures_out_of_the_negative_cache(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sources.db"
    outcomes = iter([FetchOutcome("not_found"), FetchOutcome("transient_error", error_text="HTTP 503")])
    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", lambda *_args, **_kwargs: next(outcomes))

    counts = sum20_official_ingest.ingest_wordids(
        db_path,
        start_wordid=50,
        limit=2,
        delay_s=0,
        sleep=lambda _seconds: None,
    )

    conn = sqlite3.connect(db_path)
    try:
        checkpoint = conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint WHERE singleton = 1").fetchone()[0]
        transient = conn.execute("SELECT status FROM sum20_crawl_outcomes WHERE wordid = 51").fetchone()[0]
    finally:
        conn.close()
    assert counts == {"ok": 0, "unchanged": 0, "not_found": 1, "transient_error": 1, "parse_error": 0}
    assert checkpoint == 50
    assert transient == "transient_error"


def test_query_sum20_has_no_live_mirror_path() -> None:
    source_query = (Path("scripts/rag/source_query.py")).read_text(encoding="utf-8")
    mcp_server = (Path(".mcp/servers/sources/server.py")).read_text(encoding="utf-8")

    assert "slovnyk.me/dict/newsum" not in source_query
    assert "slovnyk.me/dict/newsum" not in mcp_server
    assert "def query_sum20" in source_query
    assert "sdb.query_sum20" in mcp_server
