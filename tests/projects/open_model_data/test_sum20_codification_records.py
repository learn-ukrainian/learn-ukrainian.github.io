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
        conn.execute("CREATE TABLE sum20_articles (headword TEXT, quarantine_reason TEXT)")
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 2
        conn.execute("INSERT INTO sum20_articles VALUES ('fixture', 'synthetic quarantine')")
        committed["OTHER"].pop("official_url")
        records.ensure_reproducible_sum20_table(conn)
        assert conn.execute("SELECT COUNT(*) FROM reproducible_sum20_articles").fetchone()[0] == 0


@pytest.mark.parametrize("phrase", [False, True])
def test_caller_labels_vts_provenance_as_vts(monkeypatch, phrase):
    term = "fixture phrase" if phrase else "fixture"
    monkeypatch.setattr(
        records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": _record(url="https://slovnyk.me/dict/vts/fixture")}
    )
    monkeypatch.setattr(
        cases,
        "EXPLICIT_SOURCE_EVIDENCE",
        {
            "synthetic": {
                "authority": "СУМ-20",
                "source": "СУМ-20",
                "target_term": term,
                "article": "ABSENT" if phrase else "FIXTURE",
                "supporting_passage": "synthetic evidence",
                "locus": "synthetic locus",
            }
        },
    )
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.executemany(
            "INSERT INTO forms_all VALUES (?, ?, 'noun', '', 'synthetic')",
            [(word, word) for word in term.split()],
        )
        result = cases.query_source_evidence(
            "synthetic", term, "", "СУМ-20", "synthetic", sources.cursor(), vesum.cursor(), []
        )
        assert result["source"] == "ВТС"


def test_caller_withholds_record_without_provenance(monkeypatch):
    monkeypatch.setattr(records, "COMMITTED_SUM20_RECORDS", {"FIXTURE": _record(url="")})
    monkeypatch.setattr(
        cases,
        "EXPLICIT_SOURCE_EVIDENCE",
        {"synthetic": {"authority": "СУМ-20", "target_term": "fixture", "article": "FIXTURE"}},
    )
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture', 'fixture', 'noun', '', 'synthetic')")
        with pytest.raises(ValueError, match="Lexical evidence missing"):
            cases.query_source_evidence(
                "synthetic", "fixture", "", "СУМ-20", "synthetic", sources.cursor(), vesum.cursor(), []
            )
