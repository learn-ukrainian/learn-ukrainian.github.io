"""Committed dictionary retrieval respects quarantine and provenance (#9840)."""

from __future__ import annotations

import sqlite3

import pytest

from scripts.projects.open_model_data import build_decolonization_cases as cases
from scripts.projects.open_model_data import sum20_codification_records as records


def _record(headword="FIXTURE", url="https://slovnyk.me/dict/newsum/fixture"):
    return {
        "headword": headword,
        "official_url": url,
        "article_text": "fixture phrase — synthetic evidence",
        "definition_text": "fixture phrase — synthetic evidence",
    }


def _hold_cache(conn, *data):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS slovnyk_me_entries "
        "(id INTEGER PRIMARY KEY, source_url TEXT, dictionary_slug TEXT, text TEXT)"
    )
    for record in data:
        slug = "vts" if "/vts/" in record["official_url"] else "newsum"
        conn.execute(
            "INSERT INTO slovnyk_me_entries (source_url, dictionary_slug, text) VALUES (?, ?, ?)",
            (record["official_url"], slug, record["article_text"]),
        )


def _healthy_dictionary_schema(conn):
    """Synthetic required held-source schemas, with no dictionary evidence."""
    conn.executescript(
        "CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, headword TEXT, normalized_lookup_key TEXT, "
        "article_text TEXT, definition_text TEXT, official_url TEXT, quarantine_reason TEXT);"
        "CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, canonical_headword TEXT, "
        "normalized_query TEXT, sense_gloss TEXT);"
        "CREATE TABLE external_articles (id INTEGER PRIMARY KEY, title TEXT, text TEXT);"
    )


@pytest.mark.parametrize(
    ("url", "source"),
    [
        ("https://slovnyk.me/dict/newsum/fixture", "СУМ-20"),
        ("https://slovnyk.me/dict/vts/fixture", "ВТС"),
        ("", None),
        ("https://example.invalid/dict/newsum/fixture", None),
        ("https://slovnyk.me/dict/sum/fixture", None),
        ("https://slovnyk.me/dict/newsum/", None),
        ("https://[invalid", None),
    ],
)
def test_record_source_uses_only_recognized_provenance(url, source):
    assert records._record_source(url) == source


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("blocked_key", ["headword", "normalized_lookup_key"])
def test_committed_record_is_withheld_by_quarantined_headword(monkeypatch, legacy, blocked_key):
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": _record()})
    with sqlite3.connect(":memory:") as conn:
        quarantine_column = "" if legacy else ", quarantine_reason TEXT DEFAULT ''"
        conn.execute(
            "CREATE TABLE sum20_articles (headword TEXT, normalized_lookup_key TEXT, parser_version TEXT"
            f"{quarantine_column})"
        )
        _hold_cache(conn, _record())
        # A live homonym must not override the quarantine for the committed entry.
        conn.execute("INSERT INTO sum20_articles (headword, parser_version) VALUES ('FIXTURE', 'official')")
        if legacy:
            conn.execute(
                f"INSERT INTO sum20_articles ({blocked_key}, parser_version) VALUES (?, ?)",
                ("fi\u0301xture", "v1-official-codification"),
            )
        else:
            conn.execute(
                f"INSERT INTO sum20_articles ({blocked_key}, parser_version, quarantine_reason) VALUES (?, ?, ?)",
                ("fi\u0301xture", "official", "synthetic quarantine"),
            )
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] == 2


def test_projection_retains_provenance_and_withholds_unprovenanced_records(monkeypatch):
    missing = _record("MISSING")
    missing.pop("official_url")
    monkeypatch.setattr(
        records,
        "COMMITTED_SUM20_RECORDS",
        {
            "SUM20": _record("SUM20"),
            "VTS": _record("VTS", "https://slovnyk.me/dict/vts/fixture"),
            "MISSING": missing,
            "UNKNOWN": _record("UNKNOWN", "https://example.invalid/fixture"),
        },
    )
    with sqlite3.connect(":memory:") as conn:
        _hold_cache(conn, _record("SUM20"), _record("VTS", "https://slovnyk.me/dict/vts/fixture"))
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute(
            "SELECT headword, source, official_url FROM reproducible_sum20_articles ORDER BY id"
        ).fetchall() == [
            ("SUM20", "СУМ-20", "https://slovnyk.me/dict/newsum/fixture"),
            ("VTS", "ВТС", "https://slovnyk.me/dict/vts/fixture"),
        ]


def test_refresh_removes_records_after_quarantine_or_provenance_changes(monkeypatch):
    committed = {"FIXTURE": _record(), "OTHER": _record("OTHER")}
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", committed)
    with sqlite3.connect(":memory:") as conn:
        _healthy_dictionary_schema(conn)
        _hold_cache(conn, *committed.values())
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 2
        conn.execute(
            "INSERT INTO sum20_articles (headword, quarantine_reason) VALUES ('fixture', 'synthetic quarantine')"
        )
        committed["OTHER"].pop("official_url")
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 0


@pytest.mark.parametrize("phrase", [False, True])
@pytest.mark.parametrize("credited_source", ["СУМ-20", "ВТС"])
def test_caller_requires_vts_credit_to_match_bound_source(monkeypatch, phrase, credited_source):
    term = "fixture phrase" if phrase else "fixture"
    monkeypatch.setattr(
        records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": _record(url="https://slovnyk.me/dict/vts/fixture")}
    )
    monkeypatch.setattr(
        cases,
        "EXPLICIT_SOURCE_EVIDENCE",
        {
            "synthetic": {
                "authority": credited_source,
                "source": credited_source,
                "target_term": term,
                "article": "ABSENT" if phrase else "FIXTURE",
                "supporting_passage": "synthetic evidence",
                "locus": "synthetic locus",
            }
        },
    )
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_dictionary_schema(sources)
        _hold_cache(sources, _record(url="https://slovnyk.me/dict/vts/fixture"))
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.executemany(
            "INSERT INTO forms_all VALUES (?, ?, 'noun', '', 'synthetic')",
            [(word, word) for word in term.split()],
        )
        if credited_source == "СУМ-20":
            with pytest.raises(cases.SourceEvidenceUnavailable, match="passage/source binding"):
                cases.query_source_evidence(
                    "synthetic", term, "", credited_source, "synthetic", sources.cursor(), vesum.cursor(), []
                )
        else:
            result = cases.query_source_evidence(
                "synthetic", term, "", credited_source, "synthetic", sources.cursor(), vesum.cursor(), []
            )
            assert result["source"] == "ВТС"
            assert result["supporting_passage"] == "synthetic evidence"


def test_caller_withholds_record_without_provenance(monkeypatch):
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": _record(url="")})
    monkeypatch.setattr(
        cases,
        "EXPLICIT_SOURCE_EVIDENCE",
        {
            "synthetic": {
                "authority": "СУМ-20",
                "source": "СУМ-20",
                "target_term": "fixture",
                "article": "FIXTURE",
                "supporting_passage": "absent",
                "locus": "synthetic",
            }
        },
    )
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_dictionary_schema(sources)
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture', 'fixture', 'noun', '', 'synthetic')")
        with pytest.raises(ValueError, match="Held source"):
            cases.query_source_evidence(
                "synthetic", "fixture", "", "СУМ-20", "synthetic", sources.cursor(), vesum.cursor(), []
            )


@pytest.mark.parametrize("change", ["missing", "article", "definition", "url", "dictionary"])
def test_url_or_partial_text_cannot_establish_held_provenance(monkeypatch, change):
    candidate = _record()
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": candidate})
    with sqlite3.connect(":memory:") as conn:
        if change != "missing":
            _hold_cache(conn, candidate)
            if change == "article":
                conn.execute("UPDATE slovnyk_me_entries SET text = 'unrelated held text'")
            elif change == "definition":
                candidate["definition_text"] = "unattested paraphrase"
            elif change == "url":
                conn.execute("UPDATE slovnyk_me_entries SET source_url = 'https://example.invalid'")
            else:
                conn.execute("UPDATE slovnyk_me_entries SET dictionary_slug = 'sum'")
        dispositions = records.committed_record_dispositions(conn)
        assert dispositions["FIXTURE"]["reason_code"] == "held_source_unproven"
        assert dispositions["FIXTURE"]["locator"] is None
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 0


@pytest.mark.parametrize("text_matches", [True, False])
def test_official_row_requires_both_verbatim_passages(monkeypatch, text_matches):
    candidate = _record()
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": candidate})
    with sqlite3.connect(":memory:") as conn:
        conn.execute(
            "CREATE TABLE sum20_articles (id INTEGER, normalized_lookup_key TEXT, headword TEXT, "
            "article_text TEXT, official_url TEXT, quarantine_reason TEXT)"
        )
        conn.execute(
            "INSERT INTO sum20_articles VALUES (42, 'fixture', 'FIXTURE', ?, 'https://sum20ua.com/?wordid=42', '')",
            (candidate["article_text"] if text_matches else "different article",),
        )
        disposition = records.committed_record_dispositions(conn)["FIXTURE"]
        assert disposition["status"] == ("substantiated" if text_matches else "withheld")
        assert disposition["locator"] == ("sum20_articles:42" if text_matches else None)


FORMERLY_KEPT_RECORDS = {
    "ТОЧКА",
    "ЧЕРГА",
    "МОВА",
    "ОКО",
    "МІСЦЕ",
    "ВИГЛЯД",
    "БАЖАННЯ",
    "СУТЬ",
    "МІРА",
    "ПОВІТРЯ",
    "ЧАС",
    "ПРИЙМАТИ",
    "ВІДІГРАВАТИ",
    "ПРАВИЙ",
    "СТЯГНЕННЯ",
    "ПОВІДОМЛЯТИ",
    "МАТИ",
    "РОБИТИ",
    "ВПАДАТИ",
    "ПАДАТИ",
}


def test_all_twenty_formerly_kept_codification_records_require_held_rows():
    # A recognized historical URL without a held row is insufficient, for every candidate.
    with sqlite3.connect(":memory:") as conn:
        dispositions = records.committed_record_dispositions(conn)
    assert len(FORMERLY_KEPT_RECORDS) == 20
    assert {key for key in FORMERLY_KEPT_RECORDS if dispositions[key]["status"] == "withheld"} == FORMERLY_KEPT_RECORDS
    assert {dispositions[key]["reason_code"] for key in FORMERLY_KEPT_RECORDS} == {"held_source_unproven"}
