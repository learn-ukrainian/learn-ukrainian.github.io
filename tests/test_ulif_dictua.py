"""Focused offline tests for the official ULIF DictUA live-query cache."""

from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

source_query = importlib.import_module("rag.source_query")
sources_db = importlib.import_module("wiki.sources_db")
ulif_parse = importlib.import_module("lexicon.runner.ulif_dictua_parse")
ulif_store = importlib.import_module("lexicon.runner.ulif_dictua_store")
homonym_report = importlib.import_module("lexicon.tools.report_ulif_homonym_suspects")

FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _without_paradigm(html: str) -> str:
    """Keep a valid matched DictUA page while removing its inflection table."""
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        labels = table.get_text(" ", strip=True).casefold()
        if table.find("table") is None and ("називний" in labels or "інфінітив" in labels):
            table.decompose()
    return str(soup)


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


def test_confirmed_relation_only_headword_is_complete_without_paradigm(tmp_path, monkeypatch):
    """An adverb-like headword must not be failed solely for lacking inflection."""
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    search_html = _without_paradigm(_fixture("privit-paradigm.html"))
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(search_html))

    def post(_url: str, data: dict[str, str], timeout: int) -> _Response:
        if "ctl00$ContentPlaceHolder1$search.x" in data:
            return _Response(search_html)
        if "ctl00$ContentPlaceHolder1$syn.x" in data:
            return _Response(_fixture("privit-synonyms.html"))
        if "ctl00$ContentPlaceHolder1$phras.x" in data:
            return _Response(_fixture("privit-phraseology.html"))
        raise AssertionError(f"Unexpected DictUA POST: {data}")

    monkeypatch.setattr(source_query._SESSION, "post", post)

    record = source_query.query_ulif("привіт", ("paradigm", "synonyms"))
    assert record["status"] == "ok"
    assert "paradigm" not in record["sections"]
    assert record["sections"]["synonyms"][0]["sense_or_group_id"] == "synonyms:1"
    assert record["content_sha256"]
    assert record["parser_version"] == "ulif-dictua-v2"


def test_confirmed_but_content_empty_headword_fails_closed(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(source_query, "ULIF_REQUEST_DELAY_SECONDS", 0)
    empty_html = _without_paradigm(_fixture("privit-paradigm.html"))
    monkeypatch.setattr(source_query, "_get", lambda *args, **kwargs: _Response(empty_html))
    monkeypatch.setattr(
        source_query._SESSION,
        "post",
        lambda *args, **kwargs: _Response(empty_html),
    )

    record = source_query.query_ulif("привіт", source_query.ULIF_SECTIONS)

    assert record["status"] == "parse_error"
    assert record["sections"] == {}
    assert sources_db.get_ulif_dictua_entry("привіт")["status"] == "parse_error"


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


_VESUM_TAG_FRAGMENTS = frozenset({
    "v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly",
    "s", "p", "m", "f", "n", "1", "2", "3",
    "inf", "impr", "futr", "pres", "past",
    "adjp", "actv", "pasv", "advp", "impers",
    "noun", "verb", "adj", "adv", "imperf", "perf",
})

_OLD_ULIF_ENTRIES = """
CREATE TABLE ulif_dictua_entries (
    id INTEGER PRIMARY KEY,
    normalized_query TEXT NOT NULL UNIQUE,
    canonical_headword TEXT NOT NULL DEFAULT '',
    raw_response_ref TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    response_sha256 TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'transient_error', 'parse_error'))
);
"""


def _forms(name: str, homonym_index: int = 1, register_position: str = ""):
    return ulif_parse.parse_ulif_entry(
        _fixture(name),
        homonym_index=homonym_index,
        register_position=register_position,
    )


def _tagged(entry: dict, stressed: str) -> list[dict]:
    return [row for row in entry["forms"] if row["form_stressed"] == stressed]


def test_ulif_label_table_maps_only_attested_vesum_fragments():
    assert ulif_parse.lookup_ulif_label("вищий ступінь") is None
    for label, mapping in ulif_parse.ULIF_LABEL_TAGS.items():
        assert set(mapping.tags) <= _VESUM_TAG_FRAGMENTS, label
        assert mapping.role


def test_zamok_result_list_groups_homonyms_by_stress_and_capitalisation():
    rows = ulif_parse.parse_register_list(_fixture("zamok-tsearch.html"))
    group = ulif_parse.homonym_group(rows, "замок")

    assert len(rows) == 25
    assert [row["stressed"] for row in group] == ["За́мок", "за́мок", "замо́к"]
    assert [row["homonym_index"] for row in group] == [1, 2, 3]
    assert [row["row_index"] for row in group] == [4, 5, 6]
    assert rows[0]["unstressed"].casefold() != "замок"
    assert rows[-1]["unstressed"].casefold() != "замок"
    assert all(not row["stressed"][-1].isdigit() for row in group)


def test_zamok_entry_pages_print_no_homonym_number_and_distinct_keys():
    entries = [
        _forms("zamok-entry-1.html", 1, "4"),
        _forms("zamok-entry-2.html", 2, "5"),
        _forms("zamok-entry-3.html", 3, "6"),
    ]
    assert [entry["entry_key"] for entry in entries] == ["замок#1", "замок#2", "замок#3"]
    assert [entry["canonical_headword"] for entry in entries] == ["За́мок", "за́мок", "замо́к"]
    assert {entry["printed_homonym_number"] for entry in entries} == {None}
    assert [entry["sense_gloss"] for entry in entries] == [
        "(населений пункт в Україні)",
        "(будівля)",
        "(пристрій для замикання тощо)",
    ]
    assert {entry["grammatical_label"] for entry in entries} == {"іменник чоловічого роду"}
    assert entries[0]["register_position"] == "4"


def test_zamok_lock_has_mobile_stress_locative_preposition_and_vocative_star():
    entry = _forms("zamok-entry-3.html", 3, "6")
    nominative = _tagged(entry, "замо́к")
    genitive = _tagged(entry, "замка́")
    locative = [row for row in entry["forms"] if row["preposition"] == "на/у" and row["form_stressed"] == "замку́"]
    vocative = [row for row in entry["forms"] if row["marked_asterisk"] and row["form_stressed"] == "замку́"]

    assert nominative[1]["stress_vowel_indices"] == [3]
    assert genitive[0]["stress_vowel_indices"] == [4]
    assert nominative[1]["stress_vowel_indices"] != genitive[0]["stress_vowel_indices"]
    assert locative[0]["form_stressed"] == "замку́"
    assert "на/у" not in locative[0]["form_stressed"]
    assert locative[0]["grammatical_tags"] == ["v_mis", "s"]
    assert vocative[0]["form_stressed"] == "замку́"
    assert not vocative[0]["form_stressed"].endswith("*")
    assert vocative[0]["grammatical_tags"] == ["v_kly", "s"]
    dative = [row for row in entry["forms"] if row["grammatical_tags"] == ["v_dav", "s"]]
    assert [row["variant_order"] for row in dative] == [1, 2]
    assert [row["form_stressed"] for row in dative] == ["замку́", "замко́ві"]


def test_fixture_cells_keep_each_attested_preposition_out_of_the_form():
    """Every preposition prefix that actually occurs in the fixtures is a field."""
    seen: set[str] = set()
    for path in sorted(FIXTURES.glob("*.html")):
        entry = ulif_parse.parse_ulif_entry(path.read_text(encoding="utf-8"), homonym_index=1)
        for row in entry["forms"]:
            preposition = row["preposition"]
            if not preposition:
                continue
            seen.add(preposition)
            assert preposition not in row["form_stressed"]
            assert preposition not in row["form_unstressed"]
            assert not row["form_stressed"].startswith(preposition)
    assert seen == {"на/у"}


@pytest.mark.parametrize(
    ("prefix", "form"),
    [
        ("на/у", "замку́"),
        ("у/в", "лісі́"),
        ("в/у", "шко́лі"),
        ("на", "столі́"),
        ("в", "мі́сті"),
        ("у", "лі́сі"),
        ("по", "шляху́"),
    ],
)
def test_accepted_preposition_prefixes_stay_out_of_the_form(prefix: str, form: str):
    rows = ulif_parse._split_cell_surface(f"{prefix} {form}")
    assert rows[0]["preposition"] == prefix
    assert rows[0]["form_stressed"] == form
    assert prefix not in rows[0]["form_unstressed"]


def test_hovoryty_sections_rowspan_and_adverbial_participles():
    entry = _forms("hovoryty-paradigm.html")
    assert _tagged(entry, "говорі́мо")[0]["grammatical_tags"] == ["impr", "p", "1"]
    assert _tagged(entry, "говорі́м")[0]["variant_order"] == 2
    assert _tagged(entry, "говори́тиму")[0]["grammatical_tags"] == ["futr", "s", "1"]
    assert ":".join(_tagged(entry, "говори́тиму")[0]["grammatical_tags"]) == "futr:s:1"
    assert ":".join(_tagged(entry, "говорі́мо")[0]["grammatical_tags"]) == "impr:p:1"
    assert _tagged(entry, "говори́в")[0]["grammatical_tags"] == ["past", "m", "s"]
    plural = _tagged(entry, "говори́ли")
    assert len(plural) == 1
    assert plural[0]["grammatical_tags"] == ["past", "p"]
    assert "m" not in plural[0]["grammatical_tags"]
    assert _tagged(entry, "гово́рячи")[0]["grammatical_tags"] == ["pres", "advp"]
    assert _tagged(entry, "говори́вши")[0]["grammatical_tags"] == ["past", "advp"]
    assert _tagged(entry, "гово́рений")[0]["grammatical_tags"] == ["past", "adjp", "pasv"]
    assert entry["forms"][0]["is_lemma"] is True
    assert entry["forms"][0]["is_invariable"] is False


def test_dobryi_adjective_paradigm_keeps_gender_columns_and_variants():
    entry = _forms("dobryi-paradigm.html")
    nominative = [
        row for row in entry["forms"]
        if row["grammatical_tags"][:1] == ["v_naz"] and not row["is_lemma"]
    ]
    assert [row["form_stressed"] for row in nominative] == ["до́брий", "до́бра", "до́бре", "до́брі"]
    assert nominative[0]["grammatical_tags"] == ["v_naz", "s", "m"]
    assert nominative[3]["grammatical_tags"] == ["v_naz", "p"]
    accusative = [
        row for row in entry["forms"]
        if row["grammatical_tags"] == ["v_zna", "s", "m"]
    ]
    assert [row["variant_order"] for row in accusative] == [1, 2]
    assert [row["form_stressed"] for row in accusative] == ["до́брий", "до́брого"]


def test_duzhe_invariable_entry_emits_only_the_base_row():
    entry = _forms("duzhe.html")
    assert entry["is_invariable"] is True
    assert len(entry["forms"]) == 1
    base = entry["forms"][0]
    assert base["form_stressed"] == "ду́же"
    assert base["form_unstressed"] == "дуже"
    assert base["is_lemma"] is True
    assert base["is_invariable"] is True
    assert base["grammatical_tags"] == ["adv"]
    assert base["pedagogical_stressed_form"] == "ду́же"


def test_number_precedes_person_in_one_normaliser():
    assert ulif_parse.canonical_grammatical_tags(["futr", "1", "s"]) == ["futr", "s", "1"]
    assert ulif_parse.canonical_grammatical_tags(["impr", "1", "p"]) == ["impr", "p", "1"]
    assert ulif_parse.canonical_grammatical_tags(["past", "m", "s"]) == ["past", "m", "s"]


def test_unknown_header_is_kept_raw_and_dual_stress_uses_pedagogical_form():
    html = """
    <html><body>
    <td id="ContentPlaceHolder1_article">
      <span class="word_style">роби́ти </span>
      <span class="gram_style">– дієслово недоконаного виду</span>
      <table>
        <tr><td>інфінітив</td><td colspan="2">роби́ти</td></tr>
        <tr><td colspan="3">Вищий ступінь</td></tr>
        <tr><td colspan="3">ро́збі́р</td></tr>
      </table>
    </td></body></html>
    """
    entry = ulif_parse.parse_ulif_entry(html, homonym_index=1)
    unknown = _tagged(entry, "ро́збі́р")[0]
    assert unknown["unmapped_labels"] == ["Вищий ступінь"]
    assert unknown["grammatical_tags"] == []
    assert unknown["dual_stress_flag"] is True
    assert unknown["form_stressed"] == "ро́збі́р"
    assert unknown["pedagogical_stressed_form"] == "розбі́р"
    assert unknown["stress_vowel_indices"] == [1, 4]


def test_migration_on_a_db_copy_keeps_rows_and_flags_them_unchecked(tmp_path):
    source = tmp_path / "legacy.db"
    conn = sqlite3.connect(source)
    conn.executescript(_OLD_ULIF_ENTRIES + """
        CREATE TABLE ulif_dictua_sections (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            source_order INTEGER NOT NULL,
            sense_or_group_id TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL
        );
    """)
    conn.executemany(
        """
        INSERT INTO ulif_dictua_entries
            (normalized_query, canonical_headword, raw_response_ref, retrieved_at,
             response_sha256, parser_version, status)
        VALUES (?, ?, '', '2026-09-01T00:00:00+00:00', ?, 'ulif-dictua-v2', 'ok')
        """,
        [("замок", "за́мок", "a" * 64), ("дуже", "ду́же", "b" * 64)],
    )
    conn.execute(
        """
        INSERT INTO ulif_dictua_sections
            (entry_id, kind, source_order, sense_or_group_id, payload_json)
        VALUES (1, 'paradigm', 0, 'paradigm:1', '{}')
        """
    )
    before = conn.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0]
    sections_before = conn.execute("SELECT COUNT(*) FROM ulif_dictua_sections").fetchone()[0]
    conn.commit()
    conn.close()

    copy_path = tmp_path / "legacy-copy.db"
    copy_path.write_bytes(source.read_bytes())
    copy = sqlite3.connect(copy_path)
    assert sources_db.migrate_ulif_dictua_entries(copy) is True
    after = copy.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0]
    sections_after = copy.execute("SELECT COUNT(*) FROM ulif_dictua_sections").fetchone()[0]
    flags = copy.execute(
        """
        SELECT homonym_index, homonym_checked, content_sha256, sense_gloss
        FROM ulif_dictua_entries ORDER BY id
        """
    ).fetchall()
    assert sources_db.migrate_ulif_dictua_entries(copy) is False
    after_second = copy.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0]
    copy.execute(
        """
        INSERT INTO ulif_dictua_entries
            (normalized_query, homonym_index, canonical_headword, status)
        VALUES ('замок', 2, 'замо́к', 'ok')
        """
    )
    joined = copy.execute(
        """
        SELECT entries.normalized_query
        FROM ulif_dictua_sections AS sections
        JOIN ulif_dictua_entries AS entries ON entries.id = sections.entry_id
        """
    ).fetchone()[0]
    copy.close()

    assert before == 2
    assert after == before
    assert after_second == before
    assert sections_before == sections_after == 1
    assert flags == [(1, 0, "a" * 64, ""), (1, 0, "b" * 64, "")]
    assert joined == "замок"


def _sqlite_master_bytes(path: Path) -> bytes:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name, sql"
        ).fetchall()
    finally:
        conn.close()
    return "\n".join(repr(row) for row in rows).encode()


def _write_old_ulif_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(_OLD_ULIF_ENTRIES + """
        CREATE TABLE ulif_dictua_sections (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            source_order INTEGER NOT NULL,
            sense_or_group_id TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL
        );
    """)
    conn.execute(
        """
        INSERT INTO ulif_dictua_entries
            (normalized_query, canonical_headword, raw_response_ref, retrieved_at,
             response_sha256, parser_version, status)
        VALUES ('замок', 'За́мок', '', '2026-09-01T00:00:00+00:00', ?, 'ulif-dictua-v2', 'ok')
        """,
        ("c" * 64,),
    )
    conn.execute(
        """
        INSERT INTO ulif_dictua_sections
            (entry_id, kind, source_order, sense_or_group_id, payload_json)
        VALUES (1, 'paradigm', 0, 'paradigm:1', '{}')
        """
    )
    conn.commit()
    conn.close()
    return path


def test_read_connection_does_not_migrate_an_old_schema(tmp_path, monkeypatch):
    db_path = _write_old_ulif_db(tmp_path / "old.db")
    before = _sqlite_master_bytes(db_path)

    def fail(*_args, **_kwargs):
        raise AssertionError("read path must not create or migrate the schema")

    monkeypatch.setattr(sources_db, "ensure_ulif_dictua_schema", fail)
    monkeypatch.setattr(sources_db, "migrate_ulif_dictua_entries", fail)
    conn = sources_db._ulif_dictua_conn(db_path, create=False)
    assert conn is not None
    conn.close()
    entry = sources_db.get_ulif_dictua_entry("замок", db_path=db_path)
    listed = sources_db.get_ulif_dictua_entries("замок", db_path=db_path)

    assert _sqlite_master_bytes(db_path) == before
    assert entry is not None
    assert entry["status"] == "ok"
    assert entry["homonym_index"] == 1
    assert entry["canonical_headword"] == "За́мок"
    assert entry["sense_gloss"] == ""
    assert entry["grammatical_label"] == ""
    assert [row["homonym_index"] for row in listed] == [1]
    assert sources_db.get_ulif_dictua_entry("замок", homonym_index=2, db_path=db_path) is None


def test_migration_failure_between_copy_and_rename_keeps_the_original_table(tmp_path):
    source = _write_old_ulif_db(tmp_path / "legacy.db")
    copy_path = tmp_path / "legacy-copy.db"
    copy_path.write_bytes(source.read_bytes())
    copy = sqlite3.connect(copy_path)
    original_sql = copy.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'ulif_dictua_entries'"
    ).fetchone()[0]
    original_rows = copy.execute(
        "SELECT * FROM ulif_dictua_entries ORDER BY id"
    ).fetchall()

    class _FailBeforeDrop:
        def __init__(self, inner: sqlite3.Connection) -> None:
            self._inner = inner

        def __getattr__(self, name: str):
            return getattr(self._inner, name)

        def __setattr__(self, name: str, value: object) -> None:
            if name == "_inner":
                object.__setattr__(self, name, value)
                return
            setattr(self._inner, name, value)

        def execute(self, sql, *args, **kwargs):
            compact = " ".join(str(sql).split()).casefold()
            if compact == "drop table ulif_dictua_entries":
                raise sqlite3.OperationalError("simulated failure before rename")
            return self._inner.execute(sql, *args, **kwargs)

    with pytest.raises(sqlite3.OperationalError, match="simulated failure before rename"):
        sources_db.migrate_ulif_dictua_entries(_FailBeforeDrop(copy))  # type: ignore[arg-type]
    copy.close()

    check = sqlite3.connect(copy_path)
    survived_sql = check.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'ulif_dictua_entries'"
    ).fetchone()[0]
    survived_rows = check.execute("SELECT * FROM ulif_dictua_entries ORDER BY id").fetchall()
    leftover = check.execute(
        "SELECT name FROM sqlite_master WHERE name = 'ulif_dictua_entries_mig'"
    ).fetchone()
    check.close()
    assert survived_sql == original_sql
    assert survived_rows == original_rows
    assert leftover is None


def test_migrate_cli_is_idempotent(tmp_path, capsys):
    db_path = _write_old_ulif_db(tmp_path / "cli.db")
    assert sources_db.main(["--migrate", "--db", str(db_path)]) == 0
    assert capsys.readouterr().out.strip() == "migrated"
    assert sources_db.main(["--migrate", "--db", str(db_path)]) == 0
    assert capsys.readouterr().out.strip() == "already current"
    conn = sqlite3.connect(db_path)
    gloss = {
        row[1] for row in conn.execute("PRAGMA table_info(ulif_dictua_entries)")
    }
    conn.close()
    assert "sense_gloss" in gloss


def test_runner_store_keeps_homonym_identity_off_the_legacy_dump_table(tmp_path):
    conn = sqlite3.connect(tmp_path / "runner.db")
    ulif_store.upsert_runner_ulif_entry(
        conn,
        normalized_query="замок",
        homonym_index=1,
        canonical_headword="за́мок",
        grammatical_label="іменник чоловічого роду (будівля)",
        content_sha256="abc",
        register_position="5",
        homonym_checked=1,
    )
    ulif_store.upsert_runner_ulif_entry(
        conn,
        normalized_query="замок",
        homonym_index=2,
        canonical_headword="замо́к",
        register_position="6",
    )
    rows = conn.execute(
        """
        SELECT homonym_index, canonical_headword, register_position, homonym_checked
        FROM ulif_dictua_entries ORDER BY homonym_index
        """
    ).fetchall()
    conn.close()
    assert rows == [(1, "за́мок", "5", 1), (2, "замо́к", "6", 0)]

    legacy = sqlite3.connect(tmp_path / "dump.db")
    legacy.execute("CREATE TABLE ulif_entries (lemma TEXT PRIMARY KEY)")
    with pytest.raises(RuntimeError, match="ulif_entries"):
        ulif_store.ensure_runner_ulif_entries(legacy)
    legacy.close()


def test_sources_db_stores_two_homonyms_for_one_spelling(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", db_path)
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="за́мок",
        sections={},
        raw_responses={},
        retrieved_at="2026-09-21T00:00:00+00:00",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(будівля)",
        register_position="5",
        homonym_checked=1,
    )
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="замо́к",
        sections={},
        raw_responses={},
        retrieved_at="2026-09-21T00:00:00+00:00",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=2,
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(пристрій для замикання тощо)",
        register_position="6",
        homonym_checked=1,
    )
    ambiguous = sources_db.get_ulif_dictua_entry("ЗАМОК")
    first = sources_db.get_ulif_dictua_entry("замок", homonym_index=1)
    second = sources_db.get_ulif_dictua_entry("замок", homonym_index=2)
    listed = sources_db.get_ulif_dictua_entries("замок")
    assert ambiguous is not None and first is not None and second is not None
    assert ambiguous["status"] == "ambiguous"
    assert ambiguous["entries"] == [
        {
            "homonym_index": 1,
            "canonical_headword": "за́мок",
            "grammatical_label": "іменник чоловічого роду",
            "sense_gloss": "(будівля)",
        },
        {
            "homonym_index": 2,
            "canonical_headword": "замо́к",
            "grammatical_label": "іменник чоловічого роду",
            "sense_gloss": "(пристрій для замикання тощо)",
        },
    ]
    assert [row["homonym_index"] for row in listed] == [1, 2]
    assert first["status"] == "ok"
    assert first["homonym_index"] == 1
    assert first["canonical_headword"] == "за́мок"
    assert first["sense_gloss"] == "(будівля)"
    assert second["canonical_headword"] == "замо́к"
    assert second["sense_gloss"] == "(пристрій для замикання тощо)"
    assert second["register_position"] == "6"
    assert second["homonym_checked"] == 1
    sources_db.store_ulif_dictua_entry(
        word="стіл",
        canonical_headword="стіл",
        sections={},
        raw_responses={},
        retrieved_at="2026-09-21T00:00:00+00:00",
        parser_version="ulif-dictua-v2",
        status="ok",
    )
    single = sources_db.get_ulif_dictua_entry("стіл")
    assert single is not None
    assert single["status"] == "ok"
    assert single["homonym_index"] == 1


def test_homonym_suspect_report_combines_trie_vesum_and_capitalisation():
    rows = homonym_report.collect_suspects(
        [("замок", "за́мок"), ("бостон", "Бо́стон"), ("стіл", "стіл")],
        vesum_comments={"замок"},
        stress_position_sets=lambda spelling: {(1,), (3,)} if spelling == "замок" else {(1,)},
    )
    assert rows == [("бостон", "capitalisation"), ("замок", "trie_stress,vesum_comment")]
