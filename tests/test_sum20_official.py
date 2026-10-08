"""Offline parser, crawl-state, and lookup coverage for official СУМ-20."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ingest import sum20_official_ingest
from rag.source_query import query_sum20 as source_query_sum20
from scripts.lexicon import enrich_manifest as enrich_manifest_module
from wiki import sources_db
from wiki import sum20_official as official_module
from wiki.sum20_official import (
    DEFAULT_USER_AGENT,
    FetchOutcome,
    Sum20ParseError,
    ensure_sum20_official_schema,
    fetch_sum20_wordid,
    parse_sum20_article,
    upsert_sum20_article,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sum20_official"

# Verbatim article bytes from the wordid36 diagnostic (raw source SHA-256
# b541be9473a98aefe1aed1ab8a99805ec85c225e265657b8c7401abcb1ecb468).
WORDID36_HTML = (
    "<article>\r\n"
    "            \r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "<div>\r\n"
    '     <div class="ENTRY"> <div class="WORD">АБІССИ́НЕЦЬ</div> <div class="LINK">див. <div c'
    'lass="LINKTXT">абісси́нці</div>.</div></div><div class="LINKENTRY"> <div class="ENTRY"> <d'
    'iv class="WORD">АБІССИ́НЦІ</div><div class="LPART"><b>,</b> ів, <i>мн. (одн.</i> <b>абісси'
    '́нець,</b> нця, <i>ч.;</i> <b>абісси́нка,</b> и, <i>ж.), заст.</i></div> <div class="INTF"'
    '><div class="FORMULA">Колишня назва населення Ефіопії; ефіопи</div>. <div class="ILL"> <di'
    'v class="ILLTXT">Від свого заснування, тобто з кінця ХVIII століття, Одеса була (і залишає'
    "ться) інтернаціональним містом, у якому уживалися (і уживаються) греки і євреї, молдавани "
    "і росіяни, українці і болгари, абіссинці, німці, поляки, чехи та громадяни ще добрих шести"
    '-семи десятків різних національностей</div> <div class="ILLSRC">(із журн.)</div>.</div></d'
    "iv></div></div>\r\n"
    "    \r\n"
    "</div>\r\n"
    " \r\n"
    "        </article>"
)


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


def test_parser_preserves_verbatim_wordid36_reference_without_borrowing_fields() -> None:
    article = parse_sum20_article(WORDID36_HTML, 36)

    assert article.wordid == 36
    assert article.headword == "АБІССИНЕЦЬ"
    assert article.stressed_headword == "АБІССИ́НЕЦЬ"
    assert article.normalized_lookup_key == "абіссинець"
    assert article.grammar == article.pos == ""
    assert article.senses == article.citations == []
    assert article.article_html == WORDID36_HTML
    assert article.content_sha256 == "eabbdab7e7b3367a83816c9ba866f5d55c3938535ef551eb40d65862a844f4a7"
    assert "див. абісси́нці" in article.article_text
    assert "Колишня назва населення Ефіопії; ефіопи" in article.article_text
    assert "Від свого заснування" in article.article_text


# Synthetic ownership sentinels exercise markup contracts, not language claims.
PRIMARY_WORD = '<div class="WORD">PRIMARY</div>'
REFERENCE = '<div class="LINK">see <span class="LINKTXT">tárget</span>.</div>'
TARGET_SENSE = (
    '<div class="INTF"><div class="FORMULA">target definition</div>'
    '<div class="PARAM">target label</div><div class="ILL">'
    '<div class="ILLTXT">target citation</div><div class="ILLSRC">target author</div></div></div>'
)
TARGET_ENTRY = (
    '<div class="ENTRY"><div class="WORD">TARGET</div><div class="LPART">target grammar</div>' + TARGET_SENSE + "</div>"
)
LINKED = '<div class="LINKENTRY">' + TARGET_ENTRY + "</div>"


@pytest.mark.parametrize("layout", ["sibling", "reordered", "nested", "wrapped", "nested-in-link"])
def test_reference_target_is_not_a_primary_field_in_any_layout(layout: str) -> None:
    if layout == "nested":
        body = '<div class="ENTRY">' + LINKED + PRIMARY_WORD + REFERENCE + "</div>"
    elif layout == "nested-in-link":
        body = '<div class="ENTRY">' + PRIMARY_WORD + REFERENCE.replace("</div>", LINKED + "</div>") + "</div>"
    else:
        primary = '<div class="ENTRY">' + PRIMARY_WORD + REFERENCE + "</div>"
        body = LINKED + primary if layout == "reordered" else primary + LINKED
        if layout == "wrapped":
            body = "<section>" + body + "</section>"
    source = "<article>" + body + "</article>"

    article = parse_sum20_article(source, 36)

    assert article.headword == "PRIMARY"
    assert article.grammar == article.pos == ""
    assert article.senses == article.citations == []
    assert article.article_html == source
    assert all(text in article.article_text for text in ("tárget", "TARGET", "target citation"))


def test_reference_uses_existing_lookup_normalization_and_target_definition_ownership() -> None:
    primary = '<div class="ENTRY">' + PRIMARY_WORD + REFERENCE.replace("tárget", "  ta`rget  ")
    primary += '<div class="INTF"><div class="FORMULA"> </div></div></div>'
    linked = LINKED.replace(">TARGET<", ">TA’RGET<").replace('class="INTF"', 'class="INTN"')

    article = parse_sum20_article("<article>" + primary + linked + "</article>", 36)

    assert article.headword == "PRIMARY"
    assert article.senses == article.citations == []


@pytest.mark.parametrize("placement", ["sibling", "sense", "formula", "word", "grammar", "illustration"])
def test_normal_primary_fields_exclude_linked_senses_and_text(placement: str) -> None:
    def field(class_name: str, text: str, slot: str) -> str:
        return f'<div class="{class_name}">{text}{LINKED if placement == slot else ""}</div>'

    primary = '<div class="ENTRY">' + field("WORD", "PRIMARY", "word") + field("LPART", "primary grammar", "grammar")
    primary += '<div class="INTF">' + field("FORMULA", "primary definition", "formula")
    primary += '<div class="PARAM">primary label</div><div class="ILL">'
    primary += field("ILLTXT", "primary citation", "illustration") + '<div class="ILLSRC">primary author</div></div>'
    primary += (LINKED if placement == "sense" else "") + "</div>"
    primary += '<div class="INTN"><div class="FORMULA">second definition</div></div></div>'
    source = "<article>" + primary + (LINKED if placement == "sibling" else "") + "</article>"

    article = parse_sum20_article(source, 36)

    assert article.headword == "PRIMARY"
    assert article.grammar == "primary grammar"
    assert [sense.definition for sense in article.senses] == ["primary definition", "second definition"]
    assert article.senses[0].register_labels == ["primary label"]
    assert [citation.citation_text for citation in article.citations] == ["primary citation"]
    assert article.citations[0].sense_ref == 1
    assert article.citations[0].parsed_bib_fields == {"author": "primary author"}
    assert "target definition" in article.article_text


@pytest.mark.parametrize(
    ("primary", "linked"),
    [
        (PRIMARY_WORD, ""),
        (PRIMARY_WORD + REFERENCE, ""),
        (PRIMARY_WORD + REFERENCE, '<div class="LINKENTRY"></div>'),
        (PRIMARY_WORD + REFERENCE, LINKED.replace('class="WORD"', 'class="OTHER"')),
        (PRIMARY_WORD + REFERENCE, LINKED.replace(">TARGET<", "> <")),
        (PRIMARY_WORD + REFERENCE, LINKED.replace(">TARGET<", ">MISMATCH<")),
        (PRIMARY_WORD + REFERENCE, LINKED.replace(TARGET_SENSE, "")),
        (PRIMARY_WORD + REFERENCE, LINKED.replace("target definition", " ")),
        (PRIMARY_WORD + REFERENCE.replace("tárget", " "), LINKED),
        (PRIMARY_WORD + '<span class="LINKTXT">target</span>', LINKED),
        (PRIMARY_WORD + REFERENCE + REFERENCE, LINKED),
        (PRIMARY_WORD + REFERENCE + '<span class="LINKTXT">target</span>', LINKED),
        (PRIMARY_WORD + REFERENCE, LINKED + LINKED),
        (PRIMARY_WORD + REFERENCE, '<div class="LINKENTRY">' + TARGET_ENTRY + TARGET_ENTRY + "</div>"),
        (PRIMARY_WORD + REFERENCE, LINKED.replace(">TARGET<", '>TARGET</div><div class="WORD">TARGET<')),
        (PRIMARY_WORD + REFERENCE, LINKED.replace(TARGET_SENSE, '<div class="LINKENTRY">' + TARGET_ENTRY + "</div>")),
        (PRIMARY_WORD + REFERENCE.replace('<span class="LINKTXT">tárget</span>', ""), LINKED),
    ],
    ids=[
        "ordinary-senseless",
        "missing-target",
        "empty-container",
        "missing-target-word",
        "empty-target-word",
        "mismatch",
        "missing-target-sense",
        "empty-target-definition",
        "empty-linktext",
        "orphan-linktext",
        "multiple-links",
        "multiple-linktexts",
        "multiple-containers",
        "multiple-targets",
        "multiple-target-words",
        "nested-target-only-definition",
        "missing-linktext",
    ],
)
def test_parser_refuses_unproven_reference_associations(primary: str, linked: str) -> None:
    source = '<article><div class="ENTRY">' + primary + "</div>" + linked + "</article>"
    with pytest.raises(Sum20ParseError, match="no definition senses"):
        parse_sum20_article(source, 36)


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ("", "no .ENTRY"),
        (LINKED, "no .ENTRY"),
        ('<div class="ENTRY">' + REFERENCE + LINKED + "</div>", "no headword"),
        ('<div class="ENTRY"><div class="WORD"> </div>' + REFERENCE + "</div>" + LINKED, "no headword"),
        ('<div class="ENTRY">' + PRIMARY_WORD * 2 + REFERENCE + "</div>" + LINKED, "ambiguous primary headwords"),
        (
            '<div class="ENTRY">' + PRIMARY_WORD + REFERENCE + '</div><div class="ENTRY"></div>' + LINKED,
            "ambiguous primary .ENTRY",
        ),
        (
            '<div class="ENTRY">' + PRIMARY_WORD + '<div class="ENTRY">' + PRIMARY_WORD + "</div></div>",
            "ambiguous primary .ENTRY",
        ),
    ],
)
def test_parser_refuses_missing_or_ambiguous_primary_identity(body: str, error: str) -> None:
    with pytest.raises(Sum20ParseError, match=error):
        parse_sum20_article("<article>" + body + "</article>", 36)


@pytest.mark.parametrize("row_factory", [None, sqlite3.Row])
def test_version_mismatch_replaces_borrowed_fields_and_children_preserving_provenance(
    row_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = row_factory
    try:
        ensure_sum20_official_schema(conn)
        article = parse_sum20_article(WORDID36_HTML, 36)
        target = parse_sum20_article("<article>" + TARGET_ENTRY + "</article>", 36)
        # Reproduce v1-derived linked fields under exactly the same source bytes.
        contaminated = replace(target, article_html=article.article_html, article_text=article.article_text)
        stored_time = "2026-10-07T00:00:00+00:00"
        monkeypatch.setattr(
            official_module, "utc_now", lambda: pytest.fail("offline reparse must keep stored fetched_at")
        )
        with conn:
            assert upsert_sum20_article(conn, contaminated, fetched_at=stored_time)
            conn.execute("UPDATE sum20_articles SET parser_version = 'sum20_official_v1', quarantine_reason = 'hold'")
        before_id = conn.execute("SELECT id FROM sum20_articles").fetchone()[0]
        with conn:
            assert upsert_sum20_article(conn, article, fetched_at=stored_time)
        row = conn.execute(
            "SELECT id, headword, grammar, pos, definition_text, fetched_at, parser_version, quarantine_reason,"
            " article_html, article_text, content_sha256, official_url FROM sum20_articles"
        ).fetchone()
        assert tuple(row) == (
            before_id,
            article.headword,
            "",
            "",
            "",
            stored_time,
            official_module.PARSER_VERSION,
            "hold",
            WORDID36_HTML,
            article.article_text,
            article.content_sha256,
            "https://sum20ua.com/?wordid=36",
        )
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0
        assert (
            conn.execute("SELECT rowid FROM sum20_articles_fts WHERE sum20_articles_fts MATCH 'definition'").fetchall()
            == []
        )
        with conn:
            assert not upsert_sum20_article(conn, article, fetched_at=stored_time)
        assert conn.execute("SELECT fetched_at FROM sum20_articles").fetchone()[0] == stored_time
    finally:
        conn.close()


def test_fresh_retrieval_refreshes_timestamp_for_unchanged_html(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = sqlite3.connect(":memory:")
    try:
        ensure_sum20_official_schema(conn)
        article = parse_sum20_article(WORDID36_HTML, 36)
        with conn:
            assert upsert_sum20_article(conn, article, fetched_at="2026-10-07T00:00:00+00:00")
        monkeypatch.setattr(official_module, "utc_now", lambda: "2026-10-08T00:00:00+00:00")
        with conn:
            assert not upsert_sum20_article(conn, article)
        assert conn.execute("SELECT fetched_at FROM sum20_articles").fetchone()[0] == "2026-10-08T00:00:00+00:00"
    finally:
        conn.close()


def test_changed_html_replaces_children_atomically() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        ensure_sum20_official_schema(conn)
        old = parse_sum20_article("<article>" + TARGET_ENTRY + "</article>", 36)
        new = parse_sum20_article(WORDID36_HTML, 36)
        stored_time = "2026-10-07T00:00:00+00:00"
        with conn:
            assert upsert_sum20_article(conn, old, fetched_at=stored_time)
        conn.execute(
            "CREATE TRIGGER refuse_child_delete BEFORE DELETE ON sum20_citations BEGIN SELECT RAISE(ABORT, 'child failure'); END"
        )
        with pytest.raises(sqlite3.IntegrityError, match="child failure"), conn:
            upsert_sum20_article(conn, new, fetched_at=stored_time)
        assert conn.execute("SELECT headword, article_html FROM sum20_articles").fetchone() == (
            old.headword,
            old.article_html,
        )
        assert conn.execute("SELECT definition FROM sum20_senses").fetchone()[0] == "target definition"
        assert conn.execute("SELECT citation_text FROM sum20_citations").fetchone()[0] == "target citation"
        conn.execute("DROP TRIGGER refuse_child_delete")
        with conn:
            assert upsert_sum20_article(conn, new, fetched_at=stored_time)
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0
    finally:
        conn.close()


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


@pytest.mark.parametrize("valid_reference", [True, False])
def test_ingest_reference_stores_only_primary_fields_and_stops_on_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_reference: bool
) -> None:
    db_path = tmp_path / "staging.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = 35")
    source = WORDID36_HTML if valid_reference else WORDID36_HTML.replace('class="LINKTXT"', 'class="OTHER"')
    session = _FakeSession([_FakeResponse(200, source)])
    requested: list[int] = []

    def offline_fetch(wordid: int, **kwargs: object) -> FetchOutcome:
        requested.append(wordid)
        return fetch_sum20_wordid(wordid, session=session, **kwargs)

    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", offline_fetch)
    counts = sum20_official_ingest.ingest_wordids(db_path, limit=1 if valid_reference else 2, delay_s=0, retries=0)

    assert requested == [36]
    assert counts["ok"] == int(valid_reference)
    assert counts["parse_error"] == int(not valid_reference)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint").fetchone()[0] == (
            36 if valid_reference else 35
        )
        assert conn.execute("SELECT wordid, status FROM sum20_crawl_outcomes").fetchone() == (
            36,
            "ok" if valid_reference else "parse_error",
        )
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0
        if valid_reference:
            row = conn.execute("SELECT headword, grammar, definition_text, article_html FROM sum20_articles").fetchone()
            assert row == ("АБІССИНЕЦЬ", "", "", WORDID36_HTML)
        else:
            assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] == 0


def test_official_reference_row_has_no_definition_card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        upsert_sum20_article(conn, parse_sum20_article(WORDID36_HTML, 36), fetched_at="2026-10-07T00:00:00+00:00")
    records = sources_db.query_sum20("абіссинець", db_path=db_path)
    assert len(records) == 1
    assert records[0]["senses"] == records[0]["citations"] == []
    assert "див. абісси́нці" in records[0]["article_text"]
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)
    assert enrich_manifest_module._sum20_definition_card("абіссинець") is None


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


@pytest.mark.parametrize(
    "failure,exit_code",
    [
        (FetchOutcome("transient_error", error_text="HTTP 503", http_status=503), 1),
        (FetchOutcome("transient_error", error_text="HTTP 401", http_status=401, terminal=True), 3),
        (FetchOutcome("transient_error", error_text="HTTP 403", http_status=403, terminal=True), 3),
        (FetchOutcome("parse_error", error_text="unusable article", http_status=200, terminal=True), 4),
    ],
)
def test_ingest_keeps_transient_failures_out_of_the_negative_cache(
    tmp_path: Path, monkeypatch, failure, exit_code
) -> None:
    db_path = tmp_path / "sources.db"
    outcomes = iter([FetchOutcome("not_found"), failure])
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
        transient = conn.execute("SELECT status, error_text FROM sum20_crawl_outcomes WHERE wordid = 51").fetchone()
    finally:
        conn.close()
    assert counts == {
        "ok": 0,
        "unchanged": 0,
        "not_found": 1,
        "transient_error": int(failure.status == "transient_error"),
        "parse_error": int(failure.status == "parse_error"),
    }
    assert checkpoint == 50
    assert transient == (failure.status, failure.error_text)
    assert counts.exit_code == exit_code
    monkeypatch.setattr(sum20_official_ingest, "ingest_wordids", lambda *_args, **_kwargs: counts)
    assert sum20_official_ingest.main(["--db", str(db_path)]) == exit_code


def _fixture_sources_db(tmp_path: Path, *, include_article: bool, create_schema: bool = True) -> Path:
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    try:
        if create_schema:
            ensure_sum20_official_schema(conn)
        if create_schema and include_article:
            article = parse_sum20_article((FIXTURES / "wordid-5.html").read_text(encoding="utf-8"), 5)
            upsert_sum20_article(conn, article, fetched_at="2026-07-15T10:00:00+00:00")
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_definition_card_prefers_official_row_without_network(tmp_path: Path, monkeypatch) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=True)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)

    def fail_live_fetch(*_args, **_kwargs):
        raise AssertionError("official СУМ-20 row must prevent a slovnyk.me fetch")

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fail_live_fetch)

    card = enrich_manifest_module._sum20_definition_card("абажу́р")

    assert card == {
        "id": "sum20",
        "source": "Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства ім. О. О. Потебні)",
        "source_pill": "СУМ-20",
        "note": "сучасний тлумачний словник",
        "definitions": [
            "Частина світильника, звичайно у вигляді ковпака, признач. для зосередження і відбиття "
            "світла та захисту очей від його впливу"
        ],
        "source_url": "https://sum20ua.com/?wordid=5",
    }


def test_definition_card_falls_back_to_existing_slovnyk_path_when_official_row_absent(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    calls: list[tuple[str, str, str]] = []

    def fake_live_fetch(lemma: str, lookup_word: str, slug: str):
        calls.append((lemma, lookup_word, slug))
        return {
            "word": "АБАЖУ́Р",
            "text": "АБАЖУ́Р, а, ч. Лампа з ковпаком.",
            "source_url": "https://slovnyk.me/dict/newsum/абажур",
        }

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fake_live_fetch)

    card = enrich_manifest_module._sum20_definition_card("абажу́р")

    assert card is not None
    assert card["definitions"] == [", а, ч. Лампа з ковпаком."]
    assert calls == [("абажу́р", "абажур", "newsum")]


def test_definition_card_falls_back_when_official_table_is_missing(tmp_path: Path, monkeypatch) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False, create_schema=False)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    monkeypatch.setattr(
        enrich_manifest_module,
        "_fetch_slovnyk_entry",
        lambda *_args, **_kwargs: {
            "word": "АБАЖУ́Р",
            "text": "АБАЖУ́Р, а, ч. Лампа з ковпаком.",
        },
    )

    card = enrich_manifest_module._sum20_definition_card("абажу́р")

    assert card is not None
    assert card["id"] == "sum20"


def test_definition_card_keeps_none_when_official_and_slovnyk_rows_are_absent(tmp_path: Path, monkeypatch) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)

    assert enrich_manifest_module._sum20_definition_card("абажу́р") is None


def test_query_sum20_has_no_live_mirror_path() -> None:
    source_query = (Path("scripts/rag/source_query.py")).read_text(encoding="utf-8")
    mcp_server = (Path(".mcp/servers/sources/server.py")).read_text(encoding="utf-8")

    assert "slovnyk.me/dict/newsum" not in source_query
    assert "slovnyk.me/dict/newsum" not in mcp_server
    assert "def query_sum20" in source_query
    assert "sdb.query_sum20" in mcp_server


def test_fetch_sends_the_project_user_agent_not_the_requests_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """sum20ua.com refuses ``python-requests/*`` with 403; the identifying agent must be sent (#5228)."""
    session = requests.Session()
    sent: dict[str, str] = {}

    def fake_get(url: str, **_kwargs: object) -> _FakeResponse:
        sent.update(session.headers)
        return _FakeResponse(404)

    monkeypatch.setattr(session, "get", fake_get)
    fetch_sum20_wordid(1, session=session, retries=0)

    assert sent["User-Agent"] == DEFAULT_USER_AGENT
    assert sent["Accept"] == "text/html,application/xhtml+xml"


def test_fetch_keeps_a_caller_supplied_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "caller-agent/2.0"
    monkeypatch.setattr(session, "get", lambda url, **_kwargs: _FakeResponse(404))
    fetch_sum20_wordid(1, session=session, retries=0)

    assert session.headers["User-Agent"] == "caller-agent/2.0"


@pytest.mark.parametrize("code", [401, 403, 201, 302, 400, 499, 600])
def test_official_first_terminal_response_never_retries(code):
    session = _FakeSession([_FakeResponse(code)])
    sleeps = []
    result = fetch_sum20_wordid(5, session=session, retries=7, sleep=sleeps.append)
    assert result.status == "transient_error"
    assert result.terminal
    assert result.http_status == code
    assert result.error_text == f"HTTP {code}"
    assert not sleeps


@pytest.mark.parametrize("terminal", [401, 403, 200])
def test_official_retry_then_terminal_stop(terminal):
    session = _FakeSession([_FakeResponse(503), _FakeResponse(terminal, "<article></article>")])
    sleeps = []
    result = fetch_sum20_wordid(5, session=session, retries=7, sleep=sleeps.append)
    assert result.terminal and result.http_status == terminal
    assert result.status == ("parse_error" if terminal == 200 else "transient_error")
    assert sleeps == [2]


@pytest.mark.parametrize("terminal", [3, 4])
def test_legacy_terminal_exit_precedes_prior_failure(monkeypatch, terminal):
    counts = sum20_official_ingest.IngestCounts(
        ok=0, unchanged=0, not_found=0, transient_error=1, parse_error=int(terminal == 4)
    )
    counts.exit_code = terminal
    monkeypatch.setattr(sum20_official_ingest, "ingest_wordids", lambda *_args, **_kwargs: counts)
    assert sum20_official_ingest.main([]) == terminal


def test_legacy_ingest_help_and_failure_exit(monkeypatch, capsys):
    parser = sum20_official_ingest.build_parser()
    help_text = parser.format_help()
    assert "unbounded foreground" in help_text
    assert "Exit codes:" in help_text and "unconditional restart" in help_text
    monkeypatch.setattr(
        sum20_official_ingest,
        "ingest_wordids",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("invalid limit")),
    )
    assert sum20_official_ingest.main([]) == 1
    assert "failed" in capsys.readouterr().err
