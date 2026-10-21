"""Offline parser, crawl-state, and lookup coverage for official СУМ-20."""

from __future__ import annotations

import hashlib
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


@pytest.fixture(autouse=True)
def isolated_store_roots(monkeypatch, tmp_path):
    from scripts.lexicon import sum20_lookup

    monkeypatch.setattr(sum20_lookup, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("LEXDATA_DB_PATH", raising=False)
    monkeypatch.delenv("LU_LEXDATA_DB", raising=False)
    monkeypatch.delenv("LU_SOURCES_DB", raising=False)


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


# Verbatim primary article from the cached wordid 172 HTTP 200 response.
# Response: 20506 bytes, SHA-256
# 8cbbce1587e37a9977f0f60208cef5466829caa14050ffdaf1eb70695da2b584.
# Article: 429 UTF-8 bytes, SHA-256
# 19fad8367cd02f70bf0b8f6f8bc5afb9d77748c1e476d06c30ef3f15c90d6034.
WORDID172_HTML = (
    "<article>\r\n"
    "            \r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "<div>\r\n"
    '     <div class="ENTRY"> <div class="WORD">А́ВГІЇВ</div><div class="LPART"><b>,</b> ієва, ієве:</div> <div class="PHRF"><div class="PHRSYM">&#9671;</div> <div class="PHRASE"><div class="PHRTXT">А́вгієві ста́йні (коню́шні)</div> <div class="LINK">див. <div class="LINKTXT">ста́йня</div>.</div></div></div>\r\n'
    "    \r\n"
    "</div>\r\n"
    " \r\n"
    "        </article>"
)


# Verbatim article from the cached wordid 461 HTTP 200 response (#10242).
# Response: 21193 bytes, SHA-256
# 68fc4fd95ab41eee19f3c7a2d91995dab6f2088194b2ddbf4fc78b521ad9897b.
# Article: 1116 UTF-8 bytes, SHA-256
# 1336a79e6e27d163b25b3417e010d89c07f6f74bb1a97e8078e9d3954cd5b938.
# Preserve CRLF and the observed unbalanced div tags; do not reserialize.
WORDID461_HTML = (
    "<article>\r\n"
    "            \r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "<div>\r\n"
    '     <div class="ENTRY"> <div class="WORD">АДА́МІВ</div><div class="LPART"><b>,</b> мова, мове:</div> <div class="PHRF"><div class="PHRSYM">&#9651;</div> <div class="PHRASE"><div class="PHRTXT">Ада́мова голова́</div> <div class="LINK">див. <div class="LINKTXT">голова́</div>;</div></div> <div class="PHRASE"><div class="PHRTXT">Ада́мове я́блуко</div> <div class="LINK">див. <div class="LINKTXT">я́блуко</div></div></div><div class="PHRF"><div class="PHRSYM">&#9671;</div> <div class="PHRASE"><div class="PHRTXT">Ада́мове ребе́рце</div> <div class="LINK">див. <div class="LINKTXT">ребе́рце</div>;</div></div> <div class="PHRASE"><div class="PHRTXT">Ада́мові ді́ти</div> <div class="LINK">див. <div class="LINKTXT">ді́ти<div class="BUX">1</div>;</div></div></div> <div class="PHRASE"><div class="PHRTXT">Ада́мові слі́зки</div> <div class="LINK">див. <div class="LINKTXT">слі́зка</div>.</div></div></div>\r\n'
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


def test_parser_preserves_verbatim_wordid172_phrase_reference() -> None:
    article = parse_sum20_article(WORDID172_HTML, 172)

    assert article.wordid == 172
    assert article.headword == "АВГІЇВ"
    assert article.stressed_headword == "А́ВГІЇВ"
    assert article.normalized_lookup_key == "авгіїв"
    assert article.grammar == "ієва, ієве:"
    assert article.pos == ""
    assert article.article_html == WORDID172_HTML
    assert len(article.article_html.encode("utf-8")) == 429
    assert article.content_sha256 == "19fad8367cd02f70bf0b8f6f8bc5afb9d77748c1e476d06c30ef3f15c90d6034"
    assert article.article_text == "А́ВГІЇВ , ієва, ієве: ◇ А́вгієві ста́йні (коню́шні) див. ста́йня ."
    assert article.senses == article.citations == []


WORDID461_TEXT = (
    "АДА́МІВ , мова, мове: △ Ада́мова голова́ див. голова́ ; Ада́мове я́блуко див. я́блуко "
    "◇ Ада́мове ребе́рце див. ребе́рце ; Ада́мові ді́ти див. ді́ти 1 ; Ада́мові слі́зки див. слі́зка ."
)


def test_parser_preserves_verbatim_wordid461_grouped_phrase_references() -> None:
    article = parse_sum20_article(WORDID461_HTML, 461)

    assert article.wordid == 461
    assert article.headword == "АДАМІВ"
    assert article.stressed_headword == "АДА́МІВ"
    assert article.normalized_lookup_key == "адамів"
    assert article.grammar == "мова, мове:"
    assert article.pos == ""
    assert article.article_html == WORDID461_HTML
    assert len(article.article_html.encode("utf-8")) == 1116
    assert article.content_sha256 == "1336a79e6e27d163b25b3417e010d89c07f6f74bb1a97e8078e9d3954cd5b938"
    assert article.article_html.count("<div") == 29
    assert article.article_html.count("</div>") == 27
    assert article.article_text == WORDID461_TEXT
    assert article.senses == article.citations == []


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

PHRASE_FIELDS = {
    "LPART": '<div class="LPART">primary grammar</div>',
    "PHRSYM": '<div class="PHRSYM">◇</div>',
    "PHRTXT": '<div class="PHRTXT">primary phrase</div>',
    "LINKTXT": '<div class="LINKTXT">target</div>',
}
PHRASE_FIELDS["LINK"] = '<div class="LINK">see ' + PHRASE_FIELDS["LINKTXT"] + ".</div>"
PHRASE_FIELDS["PHRASE"] = '<div class="PHRASE">' + PHRASE_FIELDS["PHRTXT"] + PHRASE_FIELDS["LINK"] + "</div>"
PHRASE_FIELDS["PHRF"] = '<div class="PHRF">' + PHRASE_FIELDS["PHRSYM"] + PHRASE_FIELDS["PHRASE"] + "</div>"
PHRASE_REFERENCE_HTML = (
    '<article><div class="ENTRY">' + PRIMARY_WORD + PHRASE_FIELDS["LPART"] + PHRASE_FIELDS["PHRF"] + "</div></article>"
)

# Distinct phrases deliberately share a target. These are markup sentinels,
# with no invented Ukrainian wording or lexical normalization.
SECOND_PHRASE = PHRASE_FIELDS["PHRASE"].replace("primary phrase", "second phrase")
NESTED_GROUP = PHRASE_FIELDS["PHRF"].replace("primary phrase", "nested phrase")
GROUPED_REFERENCE_HTML = PHRASE_REFERENCE_HTML.replace(
    PHRASE_FIELDS["PHRASE"], PHRASE_FIELDS["PHRASE"] + SECOND_PHRASE + NESTED_GROUP
)


@pytest.mark.parametrize("layout", ["multiple", "siblings", "deeper", "formatting", "distinct-source-text"])
def test_grouped_phrase_reference_accepts_owned_distinct_units(layout: str) -> None:
    source = GROUPED_REFERENCE_HTML
    if layout == "siblings":
        source = PHRASE_REFERENCE_HTML.replace(PHRASE_FIELDS["PHRF"], PHRASE_FIELDS["PHRF"] + NESTED_GROUP)
    elif layout == "deeper":
        deeper = NESTED_GROUP.replace("nested phrase", "deeper phrase")
        source = source.replace(NESTED_GROUP, NESTED_GROUP[:-6] + deeper + "</div>")
    elif layout == "formatting":
        source = source.replace("target</div>", 'ta<b>rg</b>et<div class="BUX"><i>1</i></div></div>')
        source = source.replace("primary phrase", "<b>primary</b> phrase")
    elif layout == "distinct-source-text":
        source = source.replace("second phrase", "prímary phrase")
    article = parse_sum20_article(source, 461)
    assert article.headword == "PRIMARY"
    assert article.grammar == "primary grammar"
    assert article.article_html == source
    assert article.senses == article.citations == []


@pytest.mark.parametrize("class_name", ["PHRSYM", "PHRASE", "PHRTXT", "LINK", "LINKTXT"])
@pytest.mark.parametrize("mutation", ["missing", "empty", "misplaced", "multiple", "wrapped", "combined"])
def test_nested_group_rejects_incomplete_or_ambiguous_ownership(class_name: str, mutation: str) -> None:
    field = PHRASE_FIELDS[class_name].replace("primary phrase", "nested phrase")
    replacement = ""
    if mutation == "empty":
        replacement = f'<div class="{class_name}"> </div>'
    elif mutation == "multiple":
        replacement = field + field
    elif mutation == "wrapped":
        replacement = "<section>" + field + "</section>"
    elif mutation == "combined":
        replacement = field.replace(f'class="{class_name}"', f'class="{class_name} OTHER"')
    source = GROUPED_REFERENCE_HTML.replace(NESTED_GROUP, NESTED_GROUP.replace(field, replacement))
    if mutation == "misplaced":
        source = source.replace("</article>", field + "</article>")
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize("class_name", ["PHRF", "PHRASE", "PHRTXT", "LINK", "LINKTXT", "PHRSYM"])
@pytest.mark.parametrize("owner", ["WORD", "LPART", "PHRTXT", "LINKTXT"])
def test_grouped_phrase_reference_rejects_fields_under_formatting_or_wrong_owner(class_name: str, owner: str) -> None:
    field = PHRASE_FIELDS[class_name].replace("primary phrase", "foreign phrase")
    source = GROUPED_REFERENCE_HTML.replace(f'class="{owner}">', f'class="{owner}"><b>{field}</b>', 1)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize(
    "marker",
    [
        '<div class="BUX"> </div>',
        '<div class="BUX OTHER">1</div>',
        '<div class="BUX">1</div><div class="BUX">2</div>',
        '<b><div class="BUX">1</div></b>',
    ],
)
def test_grouped_phrase_reference_rejects_invalid_reference_formatting(marker: str) -> None:
    source = GROUPED_REFERENCE_HTML.replace("target</div>", "target" + marker + "</div>", 1)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize(
    "target",
    ['<div class="BUX">1</div>', ' <b> </b><div class="BUX">1</div> ', " \t\r\n ", ' \t<div class="BUX">1</div>\r\n '],
)
def test_grouped_phrase_reference_rejects_formatting_without_a_target(target: str) -> None:
    source = GROUPED_REFERENCE_HTML.replace(PHRASE_FIELDS["LINKTXT"], '<div class="LINKTXT">' + target + "</div>", 1)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize("owner", ["ENTRY", "WORD", "LPART", "PHRF", "PHRSYM", "PHRASE", "PHRTXT", "LINK"])
def test_grouped_phrase_reference_rejects_bux_outside_linktxt(owner: str) -> None:
    source = GROUPED_REFERENCE_HTML.replace(f'class="{owner}">', f'class="{owner}"><div class="BUX">1</div>', 1)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize(
    "extra",
    [TARGET_ENTRY, LINKED, '<div class="INTF"></div>', '<div class="INTN"></div>', '<div class="FORMULA"></div>'],
)
@pytest.mark.parametrize("placement", ["outside", "nested", "reference"])
def test_grouped_phrase_reference_rejects_foreign_entries_and_definition_markers(extra: str, placement: str) -> None:
    anchor = {"outside": "</article>", "nested": NESTED_GROUP, "reference": PHRASE_FIELDS["LINKTXT"]}[placement]
    source = GROUPED_REFERENCE_HTML.replace(anchor, extra + anchor, 1)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-group",
        "duplicate-phrase",
        "group-in-phrase",
        "group-in-marker",
        "empty-group",
        "nested-only-group",
        "wrapped-group",
        "orphan-marker",
    ],
)
def test_grouped_phrase_reference_rejects_malformed_group_boundaries(mutation: str) -> None:
    replacement = {
        "duplicate-group": NESTED_GROUP * 2,
        "duplicate-phrase": NESTED_GROUP.replace("nested phrase", "primary phrase"),
        "group-in-phrase": '<div class="PHRASE">' + NESTED_GROUP + "</div>",
        "group-in-marker": '<div class="PHRSYM">' + NESTED_GROUP + "</div>",
        "empty-group": '<div class="PHRF"></div>',
        "nested-only-group": '<div class="PHRF">' + PHRASE_FIELDS["PHRSYM"] + NESTED_GROUP + "</div>",
        "wrapped-group": "<section>" + NESTED_GROUP + "</section>",
        "orphan-marker": NESTED_GROUP + PHRASE_FIELDS["PHRSYM"],
    }[mutation]
    source = GROUPED_REFERENCE_HTML.replace(NESTED_GROUP, replacement)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 461)


def test_phrase_reference_preserves_primary_fields_with_inline_formatting() -> None:
    source = PHRASE_REFERENCE_HTML.replace("primary phrase", "<b>primary</b> phrase")
    article = parse_sum20_article(source, 172)

    assert article.headword == "PRIMARY"
    assert article.grammar == "primary grammar"
    assert article.pos == ""
    assert article.article_html == source
    assert article.article_text == "PRIMARY primary grammar ◇ primary phrase see target ."
    assert article.senses == article.citations == []


@pytest.mark.parametrize("class_name", PHRASE_FIELDS)
@pytest.mark.parametrize("mutation", ["missing", "empty", "misplaced", "multiple"])
def test_phrase_reference_rejects_incomplete_or_ambiguous_fields(class_name: str, mutation: str) -> None:
    field = PHRASE_FIELDS[class_name]
    if mutation == "empty":
        source = PHRASE_REFERENCE_HTML.replace(field, f'<div class="{class_name}"> </div>')
    elif mutation == "multiple":
        source = PHRASE_REFERENCE_HTML.replace(field, field + field)
    else:
        source = PHRASE_REFERENCE_HTML.replace(field, "")
        if mutation == "misplaced":
            source = source.replace("</article>", field + "</article>")

    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 172)


@pytest.mark.parametrize("class_name", ["INTF", "INTN", "FORMULA"])
@pytest.mark.parametrize("placement", ["primary", "phrase", "reference"])
def test_phrase_reference_rejects_even_empty_owned_definition_markers(class_name: str, placement: str) -> None:
    marker = f'<div class="{class_name}"> </div>'
    anchor = {"primary": PRIMARY_WORD, "phrase": PHRASE_FIELDS["PHRTXT"], "reference": PHRASE_FIELDS["LINKTXT"]}[
        placement
    ]
    source = PHRASE_REFERENCE_HTML.replace(anchor, anchor + marker)

    with pytest.raises(Sum20ParseError, match="no definition senses"):
        parse_sum20_article(source, 172)


@pytest.mark.parametrize(
    "extra",
    [
        '<div class="ENTRY"></div>',
        TARGET_ENTRY,
        '<div class="LINKENTRY"></div>',
        '<div class="LINKENTRY">' + PHRASE_FIELDS["LINK"] + "</div>",
        LINKED,
        LINKED.replace(">TARGET<", ">MISMATCH<"),
        '<div class="ILL"><div class="ILLTXT">orphan citation</div></div>',
    ],
    ids=[
        "empty-foreign-entry",
        "defined-foreign-entry",
        "empty-target",
        "foreign-reference",
        "matching-defined-target",
        "mismatched-defined-target",
        "orphan-citation",
    ],
)
@pytest.mark.parametrize("placement", ["outside", "inside"])
def test_phrase_reference_rejects_foreign_or_extra_evidence(extra: str, placement: str) -> None:
    if placement == "inside":
        source = PHRASE_REFERENCE_HTML.replace(PRIMARY_WORD, PRIMARY_WORD + extra)
    else:
        source = PHRASE_REFERENCE_HTML.replace("</article>", extra + "</article>")

    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 172)


@pytest.mark.parametrize("class_name", PHRASE_FIELDS)
def test_phrase_reference_rejects_combined_evidence_classes(class_name: str) -> None:
    source = PHRASE_REFERENCE_HTML.replace(f'class="{class_name}"', f'class="{class_name} OTHER"')
    with pytest.raises(Sum20ParseError, match="no definition senses"):
        parse_sum20_article(source, 172)


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


@pytest.mark.parametrize("article_kind", ["valid_reference", "malformed_reference", "recursive"])
def test_ingest_reference_stores_only_primary_fields_and_stops_on_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, article_kind: str
) -> None:
    valid_reference = article_kind == "valid_reference"
    db_path = tmp_path / "staging.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = 35")
    source = WORDID36_HTML if valid_reference else WORDID36_HTML.replace('class="LINKTXT"', 'class="OTHER"')
    if article_kind == "recursive":
        source = "<article>" + "<div>" * 1200 + TARGET_ENTRY + "</div>" * 1200 + "</article>"
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
    assert counts.exit_code == (0 if valid_reference else 4)
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


@pytest.mark.parametrize("valid", [True, False], ids=["cached-172", "malformed-172"])
def test_ingest_phrase_reference_advances_only_the_valid_source_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid: bool
) -> None:
    db_path = tmp_path / "staging.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = 171")
    source = WORDID172_HTML if valid else WORDID172_HTML.replace('class="PHRTXT"', 'class="OTHER"')
    session = _FakeSession([_FakeResponse(200, source)])
    requested: list[int] = []

    def offline_fetch(wordid: int, **kwargs: object) -> FetchOutcome:
        requested.append(wordid)
        return fetch_sum20_wordid(wordid, session=session, **kwargs)

    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", offline_fetch)
    counts = sum20_official_ingest.ingest_wordids(db_path, limit=1 if valid else 2, delay_s=0, retries=0)

    assert requested == [172]
    assert counts == {
        "ok": int(valid),
        "unchanged": 0,
        "not_found": 0,
        "transient_error": 0,
        "parse_error": int(not valid),
    }
    assert counts.exit_code == (0 if valid else 4)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint").fetchone()[0] == (172 if valid else 171)
        assert conn.execute("SELECT wordid, status FROM sum20_crawl_outcomes").fetchone() == (
            172,
            "ok" if valid else "parse_error",
        )
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0
        if valid:
            row = conn.execute(
                "SELECT wordid, headword, stressed_headword, grammar, pos, definition_text, article_html, article_text,"
                " content_sha256, parser_version FROM sum20_articles"
            ).fetchone()
            assert row == (
                172,
                "АВГІЇВ",
                "А́ВГІЇВ",
                "ієва, ієве:",
                "",
                "",
                WORDID172_HTML,
                "А́ВГІЇВ , ієва, ієве: ◇ А́вгієві ста́йні (коню́шні) див. ста́йня .",
                "19fad8367cd02f70bf0b8f6f8bc5afb9d77748c1e476d06c30ef3f15c90d6034",
                official_module.PARSER_VERSION,
            )
        else:
            assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] == 0


def test_official_phrase_reference_row_has_no_definition_card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        upsert_sum20_article(conn, parse_sum20_article(WORDID172_HTML, 172), fetched_at="2026-10-09T00:00:00+00:00")
    records = sources_db.query_sum20("авгіїв", db_path=db_path)
    assert len(records) == 1
    assert records[0]["senses"] == records[0]["citations"] == []
    assert records[0]["article_text"] == "А́ВГІЇВ , ієва, ієве: ◇ А́вгієві ста́йні (коню́шні) див. ста́йня ."
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
    assert enrich_manifest_module._sum20_official_definition_card("авгіїв") is None
    # The general consumer has an independent fallback; keep it unavailable
    # offline so this regression proves only the ingested source unit's output.
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_vesum_base_lemma", lambda *_args: None)
    assert enrich_manifest_module._sum20_definition_card("авгіїв") is None


@pytest.mark.parametrize("case", ["cached-461", "malformed-461", "terminal-403", "observed-404"])
def test_fetch_and_ingest_grouped_reference_preserves_resume_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    db_path = tmp_path / "staging.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = 460")
    http_status = {"terminal-403": 403, "observed-404": 404}.get(case, 200)
    source = WORDID461_HTML
    if case == "malformed-461":
        source = source.replace('class="LINKTXT"', 'class="OTHER"', 1)
    session = _FakeSession([_FakeResponse(http_status, source)])
    requested: list[int] = []
    outcomes: list[FetchOutcome] = []

    def offline_fetch(wordid: int, **kwargs: object) -> FetchOutcome:
        requested.append(wordid)
        result = fetch_sum20_wordid(wordid, session=session, **kwargs)
        outcomes.append(result)
        return result

    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", offline_fetch)
    stopped = case in {"malformed-461", "terminal-403"}
    counts = sum20_official_ingest.ingest_wordids(db_path, limit=2 if stopped else 1, delay_s=0, retries=0)
    expected_status = {
        "cached-461": "ok",
        "malformed-461": "parse_error",
        "terminal-403": "transient_error",
        "observed-404": "not_found",
    }[case]
    assert requested == [461]  # Terminal failures must never request 462.
    assert outcomes[0].status == expected_status
    assert outcomes[0].http_status == http_status
    assert outcomes[0].terminal == stopped
    assert counts == {
        key: int(key == expected_status) for key in ("ok", "unchanged", "not_found", "transient_error", "parse_error")
    }
    assert counts.exit_code == {"malformed-461": 4, "terminal-403": 3}.get(case, 0)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint").fetchone()[0] == (460 if stopped else 461)
        assert conn.execute("SELECT wordid, status FROM sum20_crawl_outcomes").fetchone() == (461, expected_status)
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0
        if case == "cached-461":
            row = conn.execute(
                "SELECT wordid, headword, stressed_headword, grammar, pos, definition_text, article_html, "
                "article_text, content_sha256, parser_version, official_url FROM sum20_articles"
            ).fetchone()
            assert row == (
                461,
                "АДАМІВ",
                "АДА́МІВ",
                "мова, мове:",
                "",
                "",
                WORDID461_HTML,
                WORDID461_TEXT,
                "1336a79e6e27d163b25b3417e010d89c07f6f74bb1a97e8078e9d3954cd5b938",
                official_module.PARSER_VERSION,
                "https://sum20ua.com/?wordid=461",
            )
        else:
            assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] == 0


def test_official_grouped_reference_has_no_definition_card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        upsert_sum20_article(conn, parse_sum20_article(WORDID461_HTML, 461), fetched_at="2026-10-09T00:00:00+00:00")
    records = sources_db.query_sum20("адамів", db_path=db_path)
    assert len(records) == 1
    assert records[0]["source_record_id"] == "461"
    assert records[0]["article_text"] == WORDID461_TEXT
    assert records[0]["senses"] == records[0]["citations"] == []
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
    assert enrich_manifest_module._sum20_official_definition_card("адамів") is None
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_vesum_base_lemma", lambda *_args: None)
    assert enrich_manifest_module._sum20_definition_card("адамів") is None


@pytest.mark.parametrize(
    "target",
    [pytest.param(".", id="period"), pytest.param(";", id="semicolon"), pytest.param("\u200b", id="zero-width-space")],
)
def test_grouped_reference_nonlexical_target_preserves_source_without_definition_card(
    target: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mutate only one cached reference. These are synthetic markup sentinels,
    # not evidence that the official source contains these target variants.
    source = WORDID461_HTML.replace(
        '<div class="LINKTXT">голова́</div>', f'<div class="LINKTXT">{target}<div class="BUX">1</div></div>', 1
    )
    expected_text = WORDID461_TEXT.replace("див. голова́ ;", f"див. {target} 1 ;", 1)
    article = parse_sum20_article(source, 461)
    assert article.article_html == source
    assert article.article_text == expected_text
    assert article.content_sha256 == hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert article.senses == article.citations == []

    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        assert upsert_sum20_article(conn, article, fetched_at="2026-10-09T00:00:00+00:00")
        assert conn.execute(
            "SELECT article_html, article_text, content_sha256, definition_text FROM sum20_articles"
        ).fetchone() == (source, expected_text, article.content_sha256, "")
        assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone()[0] == 0

    records = sources_db.query_sum20("адамів", db_path=db_path)
    assert len(records) == 1
    assert records[0]["source_record_id"] == "461"
    assert records[0]["article_text"] == expected_text
    assert records[0]["content_sha256"] == article.content_sha256
    assert records[0]["senses"] == records[0]["citations"] == []
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
    assert enrich_manifest_module._sum20_official_definition_card("адамів") is None
    # Isolate the stored row from independent online and morphology fallbacks.
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_vesum_base_lemma", lambda *_args: None)
    assert enrich_manifest_module._sum20_definition_card("адамів") is None


def test_official_reference_row_has_no_definition_card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        upsert_sum20_article(conn, parse_sum20_article(WORDID36_HTML, 36), fetched_at="2026-10-07T00:00:00+00:00")
    records = sources_db.query_sum20("абіссинець", db_path=db_path)
    assert len(records) == 1
    assert records[0]["senses"] == records[0]["citations"] == []
    assert "див. абісси́нці" in records[0]["article_text"]
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
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
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))

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


def test_definition_card_does_not_fall_back_when_official_row_absent(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False)
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
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

    assert card is None
    assert calls == []


def test_definition_card_does_not_fall_back_when_official_table_is_missing(tmp_path: Path, monkeypatch) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False, create_schema=False)
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
    monkeypatch.setattr(
        enrich_manifest_module,
        "_fetch_slovnyk_entry",
        lambda *_args, **_kwargs: {
            "word": "АБАЖУ́Р",
            "text": "АБАЖУ́Р, а, ч. Лампа з ковпаком.",
        },
    )

    card = enrich_manifest_module._sum20_definition_card("абажу́р")

    assert card is None


def test_definition_card_keeps_none_when_official_and_slovnyk_rows_are_absent(tmp_path: Path, monkeypatch) -> None:
    db_path = _fixture_sources_db(tmp_path, include_article=False)
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
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


def test_official_parser_recursion_stops_one_request(monkeypatch):
    source = "<article>" + "<div>" * 1200 + TARGET_ENTRY + "</div>" * 1200 + "</article>"
    assert parse_sum20_article("<article>" + TARGET_ENTRY + "</article>", 5).headword == "TARGET"
    with pytest.raises(RecursionError):
        parse_sum20_article(source, 5)
    session = _FakeSession([_FakeResponse(200, source), _FakeResponse(404)])
    get = session.get
    calls = []

    def counted_get(*args, **kwargs):
        calls.append((args, kwargs))
        return get(*args, **kwargs)

    monkeypatch.setattr(session, "get", counted_get)
    sleeps = []
    result = fetch_sum20_wordid(5, session=session, retries=7, sleep=sleeps.append)
    assert result == FetchOutcome("parse_error", error_text="unusable article", http_status=200, terminal=True)
    assert len(calls) == 1
    assert not sleeps


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


# Response SHA-256: 1b83ffbb50717e1770a1acf702fc7ee37f095a88a368dfa9c2d5831ebb4bbe85
# Article SHA-256: 2c0a7fb9fefad0fa23fc17b1982352ec6aaf98c16579231c4dd2a1f457fc8791
WORDID2354_HTML = (
    "<article>\r\n"
    "            \r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "<div>\r\n"
    '     <div class="ENTRY"> <div class="WORD">БА́КИ<div class="UX">2</div></div><div class="LPART"><b>,</b> ів, <i>мн.</i>:</div> <div class="PHRF"><div class="PHRSYM">&#9671;</div> <div class="PHRASE"><div class="PHRTXT">Відби́ло ба́ки (па́м\'ять)</div> <div class="LINK">див. <div class="LINKTXT">відбива́ти</div>;</div></div> <div class="PHRASE"><div class="PHRTXT">Забива́ти / заби́ти ба́ки</div> <div class="LINK">див. <div class="LINKTXT">забива́ти</div>.</div></div></div>\r\n'
    "    \r\n"
    "</div>\r\n"
    " \r\n"
    "        </article>"
)


# Response SHA-256: b4238efeb1e73404af16b4cb23856d67dc2cffdb03641f722015c143afb70b62
# Article SHA-256: 3a06d33644865c6cad81c8320b71870e4f26c465de65c3a2982ea79094381d9d
WORDID1521_HTML = (
    "<article>\r\n"
    "            \r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "\r\n"
    "<div>\r\n"
    '     <div class="ENTRY"> <div class="WORD">АРГОНА́ВТ<div class="UX">1</div></div> <div class="LINK">див. <div class="LINKTXT">аргона́вти<div class="BUX">1</div>.</div></div></div><div class="LINKENTRY"> <div class="ENTRY"> <div class="WORD">АРГОНА́ВТИ<div class="UX">1</div></div><div class="LPART"><b>,</b> ів, <i>мн. (одн.</i> <b>аргона́вт,</b> а, <i>ч.).</i></div> <div class="INTF"><div class="INTNUM">1</div>. <div class="FORMULA">У грецькій міфології – герої, які здійснили далекий морський похід на кораблі “Арго” в Колхіду по золоте руно</div>. <div class="ILL"> <div class="ILLTXT">Там аргонавтів весло не плескалось в нерушеній хвилі, Не мандрувала там Медея-зрадниця</div> <div class="ILLSRC">(М. Зеров)</div>;</div> <div class="ILL"> <div class="ILLTXT">Саме кентавр Хірон вказав аргонавтам дорогу в Колхіду, коли вони пустилися в мандри по золоте руно</div> <div class="ILLSRC">(із журн.)</div>;</div> <div class="ILL"> * У порівн.  <div class="ILLTXT">Як аргонавти в давнину, покинемо свій дім</div> <div class="ILLSRC">(Ю. Яновський)</div>.</div></div><div class="INTN"><div class="INTNUM">2</div>. <div class="PARAM">перен.</div> <div class="FORMULA">Відважні мореплавці, які подорожують у невідомі країни, шукаючи багатства, пригод і т. ін</div>. <div class="ILL"> <div class="ILLTXT">Аргонавти без човна, Що по горах пішки лазять І не руна золотого, А з ведмедя шкури хочуть</div> <div class="ILLSRC">(Леся Українка)</div>;</div> <div class="SHD"><div class="SHDNUM">//&nbsp;</div><div class="PARAM">перен.</div> <div class="FORMULA">Учасники наукової експедиції, мандрівники</div>.</div> <div class="ILL"> <div class="ILLTXT">– Наша зміна, – сказав я. – Зоряні мрійники. Майбутні космонавти. Аргонавти всесвіту</div> <div class="ILLSRC">(А. Крижанівський)</div>.</div></div></div></div>\r\n'
    "    \r\n"
    "</div>\r\n"
    " \r\n"
    "        </article>"
)


def test_parser_preserves_verbatim_wordid2354_marked_phrase_reference() -> None:
    source = WORDID2354_HTML
    assert len(source.encode("utf-8")) == 627
    assert (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        == "2c0a7fb9fefad0fa23fc17b1982352ec6aaf98c16579231c4dd2a1f457fc8791"
    )
    article = parse_sum20_article(source, 2354)
    assert article.headword == "БАКИ 2"
    assert article.stressed_headword == "БА́КИ 2"
    assert article.normalized_lookup_key == "баки 2"
    assert article.grammar == "ів, мн.:"
    assert article.pos == "мн."
    current_observed_literal = (
        "БА́КИ 2 , ів, мн.: ◇ Відби́ло ба́ки (па́м'ять) див. відбива́ти ; Забива́ти / заби́ти ба́ки див. забива́ти ."
    )
    assert article.article_text == current_observed_literal
    assert article.article_html == source
    assert article.senses == article.citations == []


def test_parser_preserves_verbatim_wordid1521_marked_word_reference() -> None:
    source = WORDID1521_HTML
    assert len(source.encode("utf-8")) == 2533
    assert (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        == "3a06d33644865c6cad81c8320b71870e4f26c465de65c3a2982ea79094381d9d"
    )
    article = parse_sum20_article(source, 1521)
    assert article.headword == "АРГОНАВТ 1"
    assert article.stressed_headword == "АРГОНА́ВТ 1"
    assert article.normalized_lookup_key == "аргонавт 1"
    assert article.grammar == ""
    assert article.pos == ""
    current_observed_literal = "АРГОНА́ВТ 1 див. аргона́вти 1 . АРГОНА́ВТИ 1 , ів, мн. (одн. аргона́вт, а, ч.). 1 . У грецькій міфології – герої, які здійснили далекий морський похід на кораблі “Арго” в Колхіду по золоте руно . Там аргонавтів весло не плескалось в нерушеній хвилі, Не мандрувала там Медея-зрадниця (М. Зеров) ; Саме кентавр Хірон вказав аргонавтам дорогу в Колхіду, коли вони пустилися в мандри по золоте руно (із журн.) ; * У порівн. Як аргонавти в давнину, покинемо свій дім (Ю. Яновський) . 2 . перен. Відважні мореплавці, які подорожують у невідомі країни, шукаючи багатства, пригод і т. ін . Аргонавти без човна, Що по горах пішки лазять І не руна золотого, А з ведмедя шкури хочуть (Леся Українка) ; // перен. Учасники наукової експедиції, мандрівники . – Наша зміна, – сказав я. – Зоряні мрійники. Майбутні космонавти. Аргонавти всесвіту (А. Крижанівський) ."
    assert article.article_text == current_observed_literal
    assert article.article_html == source
    assert article.senses == article.citations == []


# English structural sentinels keep authentic article literals untouched.
MARKED_PRIMARY = '<div class="WORD">PRIMARY<div class="UX">1</div></div>'
MARKED_TARGET = '<div class="WORD">TARGET<div class="UX">1</div></div>'
MARKED_LINKTXT = '<div class="LINKTXT">target<div class="BUX">1</div>.</div>'
MARKED_LINK = '<div class="LINK">see ' + MARKED_LINKTXT + "</div>"
MARKED_LINKED = '<div class="LINKENTRY"><div class="ENTRY">' + MARKED_TARGET + TARGET_SENSE + "</div></div>"
MARKED_WORD_HTML = (
    '<article><div class="ENTRY">' + MARKED_PRIMARY + MARKED_LINK + "</div>" + MARKED_LINKED + "</article>"
)
MARKED_PHRASE_HTML = PHRASE_REFERENCE_HTML.replace(PRIMARY_WORD, MARKED_PRIMARY)

INVALID_MARKED_WORDS = [
    pytest.param('<div class="WORD"><div class="UX">1</div></div>', id="marker-only"),
    pytest.param('<div class="WORD"> <div class="UX">1</div> </div>', id="whitespace-only"),
    pytest.param('<div class="WORD"><div class="UX">1</div>PRIMARY</div>', id="lexical-after-marker"),
    pytest.param(MARKED_PRIMARY + PRIMARY_WORD, id="two-words"),
    pytest.param(MARKED_PRIMARY.replace("</div></div>", '</div><div class="UX">1</div></div>'), id="duplicate-ux"),
    pytest.param(MARKED_PRIMARY.replace(">1<", "> <"), id="empty-ux"),
    pytest.param(MARKED_PRIMARY.replace('class="UX"', 'class="UX OTHER"'), id="combined-ux"),
    pytest.param('<div class="WORD">PRIMARY<span><div class="UX">1</div></span></div>', id="wrapped-ux"),
    pytest.param(MARKED_PRIMARY.replace('class="UX"', 'class="BUX"'), id="bux-under-word"),
    pytest.param(MARKED_PRIMARY.replace('class="UX"', 'class="OTHER"'), id="foreign-child"),
    pytest.param(MARKED_PRIMARY.replace(">1<", '><span class="OTHER">1</span><'), id="foreign-under-ux"),
    pytest.param(MARKED_PRIMARY.replace(">1<", '><span class="ENTRY">1</span><'), id="entry-under-ux"),
    pytest.param(MARKED_PRIMARY.replace("PRIMARY", '<span class="LINKENTRY">hidden</span>'), id="hidden-lexical"),
    pytest.param(MARKED_PRIMARY.replace("PRIMARY", '<span class="FORMULA">hidden</span>'), id="definition-lexical"),
    pytest.param(MARKED_PRIMARY.replace("PRIMARY", '<span class="ILLTXT">hidden</span>'), id="citation-lexical"),
    pytest.param(MARKED_PRIMARY.replace('class="WORD"', 'class="WORD OTHER"'), id="combined-word"),
]


@pytest.mark.parametrize("word", INVALID_MARKED_WORDS)
def test_marked_phrase_reference_refuses_invalid_ownership(word: str) -> None:
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(MARKED_PHRASE_HTML.replace(MARKED_PRIMARY, word), 2354)


@pytest.mark.parametrize("word", INVALID_MARKED_WORDS)
@pytest.mark.parametrize("owner", ["primary", "target"])
def test_marked_word_reference_refuses_invalid_ownership(word: str, owner: str) -> None:
    if owner == "target":
        word = word.replace("PRIMARY", "TARGET")
    source = MARKED_WORD_HTML.replace(MARKED_PRIMARY if owner == "primary" else MARKED_TARGET, word)
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 1521)


@pytest.mark.parametrize("owner", ["LINK", "LINKTXT", "LPART", "PHRF", "PHRASE", "PHRTXT", "outside-entry"])
@pytest.mark.parametrize("path", ["phrase", "word"])
def test_marked_reference_refuses_misplaced_primary_markers(owner: str, path: str) -> None:
    source = MARKED_PHRASE_HTML if path == "phrase" else MARKED_WORD_HTML
    extra = '<div class="UX">1</div>'
    if owner == "outside-entry":
        source = source.replace("</article>", extra + "</article>")
    else:
        needle = f'<div class="{owner}">'
        if needle in source:
            source = source.replace(needle, needle + extra, 1)
        else:
            source = source.replace(MARKED_PRIMARY, MARKED_PRIMARY + needle + extra + "</div>")
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 1521)


INVALID_MARKED_REFERENCES = [
    pytest.param('<div class="LINKTXT"><div class="BUX">1</div>.</div>', id="no-lexical-target"),
    pytest.param('<div class="LINKTXT">.</div>', id="period-only"),
    pytest.param(MARKED_LINKTXT.replace(">1<", "> <"), id="empty-bux"),
    pytest.param(MARKED_LINKTXT.replace(">1<", ">2<"), id="marker-mismatch"),
    pytest.param(MARKED_LINKTXT.replace(">1<", ">01<"), id="leading-zero-mismatch"),
    pytest.param(MARKED_LINKTXT.replace("</div>.", '</div><div class="BUX">1</div>.'), id="duplicate-bux"),
    pytest.param(MARKED_LINKTXT.replace('class="BUX"', 'class="BUX OTHER"'), id="combined-bux"),
    pytest.param('<div class="LINKTXT">target<span><div class="BUX">1</div></span>.</div>', id="wrapped-bux"),
    pytest.param(MARKED_LINKTXT.replace(">1<", '><span class="OTHER">1</span><'), id="classed-bux-descendant"),
    pytest.param(MARKED_LINKTXT.replace(">1<", '><span class="UX">1</span><'), id="ux-under-bux"),
    pytest.param(MARKED_LINKTXT.replace('class="BUX"', 'class="UX"'), id="ux-under-linktxt"),
    pytest.param(MARKED_LINKTXT.replace("target", "wrong"), id="wrong-target"),
    pytest.param(MARKED_LINKTXT.replace("target", ".target"), id="leading-period"),
    pytest.param(MARKED_LINKTXT.replace("target", "tar.get"), id="interior-period"),
    pytest.param(MARKED_LINKTXT.replace("target", "target."), id="period-before-bux"),
    pytest.param(MARKED_LINKTXT.replace("target", '<span class="OTHER">target</span>'), id="foreign-target-text"),
    pytest.param(MARKED_LINKTXT.replace("target", '<span class="ENTRY">target</span>'), id="hidden-target-text"),
    pytest.param(MARKED_LINKTXT.replace("target", '<span class="LINKENTRY">target</span>'), id="linked-target-text"),
    pytest.param(MARKED_LINKTXT.replace('<div class="BUX">1</div>', ""), id="unmarked-period"),
    *[
        pytest.param(MARKED_LINKTXT.replace("</div>.", "</div>" + suffix), id="suffix-" + name)
        for name, suffix in [
            ("double-dot", ".."),
            ("ellipsis", "..."),
            ("semicolon", ";"),
            ("colon", ":"),
            ("comma", ","),
            ("lexical", ". extra"),
            ("unicode-dot", "．"),
            ("wrapped-dot", "<i>.</i>"),
            ("wrapped-whitespace", " <i> </i>."),
            ("foreign-dot", '<span class="OTHER">.</span>'),
        ]
    ],
]


@pytest.mark.parametrize("reference", INVALID_MARKED_REFERENCES)
def test_marked_word_reference_refuses_ambiguous_marker_or_punctuation(reference: str) -> None:
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(MARKED_WORD_HTML.replace(MARKED_LINKTXT, reference), 1521)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-link",
        "empty-link",
        "duplicate-link",
        "missing-linktxt",
        "empty-linktxt",
        "duplicate-linktxt",
        "orphan-linktxt",
        "combined-link",
        "combined-linktxt",
        "duplicate-container",
        "duplicate-target-entry",
        "missing-target-word",
        "empty-target-word",
        "missing-target-marker",
        "missing-definition",
        "empty-definition",
        "nested-definition",
        "unrelated-definition",
        "extra-primary-entry",
        "stray-primary-bux",
        "stray-primary-ux",
        "stray-link-tail-bux",
        "stray-target-ux",
        "stray-target-bux",
    ],
)
def test_marked_word_reference_refuses_invalid_association(mutation: str) -> None:
    source = MARKED_WORD_HTML
    replacements = {
        "missing-link": (MARKED_LINK, ""),
        "empty-link": (MARKED_LINK, '<div class="LINK"> </div>'),
        "duplicate-link": (MARKED_LINK, MARKED_LINK * 2),
        "missing-linktxt": (MARKED_LINKTXT, ""),
        "empty-linktxt": (MARKED_LINKTXT, '<div class="LINKTXT"> </div>'),
        "duplicate-linktxt": (MARKED_LINKTXT, MARKED_LINKTXT * 2),
        "orphan-linktxt": (MARKED_LINK, '<div class="LINK">see</div>' + MARKED_LINKTXT),
        "combined-link": ('class="LINK"', 'class="LINK OTHER"'),
        "combined-linktxt": ('class="LINKTXT"', 'class="LINKTXT OTHER"'),
        "duplicate-container": (MARKED_LINKED, MARKED_LINKED * 2),
        "duplicate-target-entry": (MARKED_LINKED, MARKED_LINKED.replace(TARGET_SENSE, TARGET_SENSE + TARGET_ENTRY)),
        "missing-target-word": (MARKED_TARGET, ""),
        "empty-target-word": (MARKED_TARGET, '<div class="WORD"> </div>'),
        "missing-target-marker": (MARKED_TARGET, '<div class="WORD">TARGET</div>'),
        "missing-definition": (TARGET_SENSE, ""),
        "empty-definition": (TARGET_SENSE, '<div class="INTF"><div class="FORMULA"> </div></div>'),
        "nested-definition": (TARGET_SENSE, '<div class="ENTRY">' + TARGET_SENSE + "</div>"),
        "unrelated-definition": (MARKED_LINKED, MARKED_LINKED.replace(TARGET_SENSE, "") + TARGET_SENSE),
        "extra-primary-entry": (MARKED_PRIMARY, MARKED_PRIMARY + '<div class="ENTRY">' + PRIMARY_WORD + "</div>"),
        "stray-primary-bux": (MARKED_PRIMARY, MARKED_PRIMARY + '<div class="BUX">1</div>'),
        "stray-primary-ux": (MARKED_PRIMARY, MARKED_PRIMARY + '<div class="UX">1</div>'),
        "stray-link-tail-bux": (
            MARKED_LINK,
            MARKED_LINK.replace(MARKED_LINKTXT, MARKED_LINKTXT + '<div class="BUX">1</div>'),
        ),
        "stray-target-ux": (MARKED_TARGET, MARKED_TARGET + '<div class="UX">1</div>'),
        "stray-target-bux": (MARKED_TARGET, MARKED_TARGET + '<div class="BUX">1</div>'),
    }
    old, new = replacements[mutation]
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source.replace(old, new), 1521)


@pytest.mark.parametrize(
    "layout",
    [
        "period",
        "whitespace",
        "inline-marker",
        "inline-lexical",
        "unmarked-primary",
        "exact",
        "link-tail-period",
        "wrapped-linktxt",
    ],
)
def test_marked_reference_preserves_valid_layouts(layout: str) -> None:
    source = MARKED_WORD_HTML
    if layout == "wrapped-linktxt":
        source = source.replace(MARKED_LINKTXT, "<span>" + MARKED_LINKTXT + "</span>")
    elif layout == "whitespace":
        source = source.replace(">1<", "> 1 <").replace("</div>.", "</div> \t . \n")
    elif layout == "inline-marker":
        source = source.replace(">1<", "><i>1</i><")
    elif layout == "inline-lexical":
        source = source.replace(">PRIMARY<", "><i>PRIMARY</i><").replace(">target<", "><b>target</b><")
    elif layout == "unmarked-primary":
        source = source.replace(MARKED_PRIMARY, PRIMARY_WORD)
    elif layout == "exact":
        source = source.replace("</div>.", "</div>")
    elif layout == "link-tail-period":
        source = source.replace(MARKED_LINKTXT, MARKED_LINKTXT.replace("</div>.", "</div>") + ".")
    article = parse_sum20_article(source, 1521)
    assert article.headword == ("PRIMARY" if layout == "unmarked-primary" else "PRIMARY 1")
    assert article.normalized_lookup_key == ("primary" if layout == "unmarked-primary" else "primary 1")
    assert article.senses == article.citations == []
    assert article.article_html == source


def test_defined_marked_word_preserves_existing_identity() -> None:
    source = (
        '<article><div class="ENTRY"><div class="WORD">PRÍMARY<div class="UX">2</div></div>'
        + TARGET_SENSE
        + "</div></article>"
    )
    article = parse_sum20_article(source, 5)
    assert article.headword == "PRIMARY 2"
    assert article.stressed_headword == "PRÍMARY 2"
    assert article.normalized_lookup_key == "primary 2"
    assert [sense.definition for sense in article.senses] == ["target definition"]
    assert [citation.citation_text for citation in article.citations] == ["target citation"]


@pytest.mark.parametrize(
    "wordid,source,key,bare,headword,stressed,grammar,pos,digest",
    [
        (
            2354,
            WORDID2354_HTML,
            "баки 2",
            "баки",
            "БАКИ 2",
            "БА́КИ 2",
            "ів, мн.:",
            "мн.",
            "2c0a7fb9fefad0fa23fc17b1982352ec6aaf98c16579231c4dd2a1f457fc8791",
        ),
        (
            1521,
            WORDID1521_HTML,
            "аргонавт 1",
            "аргонавт",
            "АРГОНАВТ 1",
            "АРГОНА́ВТ 1",
            "",
            "",
            "3a06d33644865c6cad81c8320b71870e4f26c465de65c3a2982ea79094381d9d",
        ),
    ],
    ids=["2354", "1521"],
)
def test_marked_reference_ingest_and_consumers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wordid: int,
    source: str,
    key: str,
    bare: str,
    headword: str,
    stressed: str,
    grammar: str,
    pos: str,
    digest: str,
) -> None:
    from scripts.lexicon.sum20_lookup import lookup_sum20_cached

    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = ?", (wordid - 1,))
    session = _FakeSession([_FakeResponse(200, source), _FakeResponse(200, source)])
    requested: list[int] = []

    def offline_fetch(requested_wordid: int, **kwargs: object) -> FetchOutcome:
        requested.append(requested_wordid)
        return fetch_sum20_wordid(requested_wordid, session=session, **kwargs)

    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", offline_fetch)
    for repeat in (False, True):
        counts = sum20_official_ingest.ingest_wordids(db_path, start_wordid=wordid, limit=1, delay_s=0, retries=0)
        assert counts == {
            "ok": int(not repeat),
            "unchanged": int(repeat),
            "not_found": 0,
            "transient_error": 0,
            "parse_error": 0,
        }
        assert counts.exit_code == 0
        with sqlite3.connect(db_path) as conn:
            assert conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint").fetchone() == (wordid,)
            assert conn.execute("SELECT wordid, status FROM sum20_crawl_outcomes").fetchall() == [(wordid, "ok")]
            assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone() == (1,)
            assert conn.execute("SELECT COUNT(*) FROM sum20_senses").fetchone() == (0,)
            assert conn.execute("SELECT COUNT(*) FROM sum20_citations").fetchone() == (0,)
            assert conn.execute(
                "SELECT wordid, headword, stressed_headword, normalized_lookup_key, grammar, pos, definition_text, article_html, content_sha256, parser_version FROM sum20_articles"
            ).fetchone() == (
                wordid,
                headword,
                stressed,
                key,
                grammar,
                pos,
                "",
                source,
                digest,
                "sum20_official_v4",
            )
            conn.row_factory = sqlite3.Row
            for query in (key, bare):
                rows = lookup_sum20_cached(query, conn)
                assert len(rows) == 1
                assert rows[0]["wordid"] == wordid
                assert rows[0]["headword"] == headword
                assert rows[0]["definition"] == ""
                assert rows[0]["senses"] == []
        records = sources_db.query_sum20(key, db_path=db_path)
        assert len(records) == 1
        assert source_query_sum20(key, db_path=str(db_path)) == records
        assert sources_db.query_sum20(bare, db_path=db_path) == []
        assert source_query_sum20(bare, db_path=str(db_path)) == []
        record = records[0]
        assert record["headword"] == headword
        assert record["stressed_headword"] == stressed
        assert record["senses"] == record["citations"] == []
        assert record["source_id"] == "sum20_official"
        assert record["source_record_id"] == str(wordid)
        assert record["official_url"] == f"https://sum20ua.com/?wordid={wordid}"
        assert record["content_sha256"] == digest
        assert record["parser_version"] == "sum20_official_v4"
        assert record["status"] == "ok"
        assert record["retrieved_at"]
        assert record["attribution_label"] == official_module.SUM20_ATTRIBUTION_LABEL
    assert requested == [wordid, wordid]
    monkeypatch.setenv("LU_SOURCES_DB", str(db_path))
    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_vesum_base_lemma", lambda *_args: None)
    for query in (key, bare):
        assert enrich_manifest_module._sum20_official_definition_card(query) is None
        assert enrich_manifest_module._sum20_definition_card(query) is None


@pytest.mark.parametrize(
    "wordid,source",
    [
        pytest.param(
            2354,
            WORDID2354_HTML.replace('<div class="UX">2</div>', '<div class="UX">2</div><div class="UX">2</div>', 1),
            id="duplicate_primary_ux_phrase",
        ),
        pytest.param(
            1521,
            WORDID1521_HTML.replace('<div class="BUX">1</div>', '<div class="BUX">2</div>', 1),
            id="bux_ux_mismatch_period",
        ),
    ],
)
def test_marked_reference_ingest_stops_before_second_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wordid: int,
    source: str,
) -> None:
    db_path = tmp_path / "staging.db"
    with sqlite3.connect(db_path) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute("UPDATE sum20_crawl_checkpoint SET last_wordid = ?", (wordid - 1,))
    session = _FakeSession([_FakeResponse(200, source), _FakeResponse(200, WORDID36_HTML)])
    requested: list[int] = []

    def offline_fetch(requested_wordid: int, **kwargs: object) -> FetchOutcome:
        requested.append(requested_wordid)
        return fetch_sum20_wordid(requested_wordid, session=session, **kwargs)

    monkeypatch.setattr(sum20_official_ingest, "fetch_sum20_wordid", offline_fetch)
    counts = sum20_official_ingest.ingest_wordids(db_path, limit=2, delay_s=0, retries=0)
    assert requested == [wordid]
    assert counts == {"ok": 0, "unchanged": 0, "not_found": 0, "transient_error": 0, "parse_error": 1}
    assert counts.exit_code == 4
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT last_wordid FROM sum20_crawl_checkpoint").fetchone() == (wordid - 1,)
        assert conn.execute("SELECT wordid, status FROM sum20_crawl_outcomes").fetchall() == [(wordid, "parse_error")]
        for table in ("sum20_articles", "sum20_senses", "sum20_citations"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (0,)


@pytest.mark.parametrize("layout", ["direct", "whitespace", "inline-ux", "inline-lexical", "inline-bux"])
def test_marked_phrase_reference_preserves_owned_markers(layout: str) -> None:
    source = MARKED_PHRASE_HTML
    if layout == "whitespace":
        source = source.replace(">1<", "> 1 <")
    elif layout == "inline-ux":
        source = source.replace(">1<", "><i>1</i><")
    elif layout == "inline-lexical":
        source = source.replace(">PRIMARY<", "><i>PRIMARY</i><")
    elif layout == "inline-bux":
        source = source.replace(
            PHRASE_FIELDS["LINKTXT"], '<div class="LINKTXT">target<div class="BUX"><i>1</i></div></div>'
        )
    article = parse_sum20_article(source, 2354)
    assert article.headword == "PRIMARY 1"
    assert article.normalized_lookup_key == "primary 1"
    assert article.senses == article.citations == []
    assert article.article_html == source


def test_marked_phrase_presence_prevents_word_reference_fallback() -> None:
    source = MARKED_PHRASE_HTML.replace('class="PHRTXT"', 'class="OTHER"').replace("</article>", LINKED + "</article>")
    with pytest.raises(Sum20ParseError, match="no definition senses"):
        parse_sum20_article(source, 2354)


@pytest.mark.parametrize("marker_only", [False, True], ids=["empty-markers", "marker-only-fields"])
def test_marked_word_reference_refuses_matching_but_empty_association(marker_only: bool) -> None:
    source = MARKED_WORD_HTML
    if marker_only:
        source = source.replace("target<div", "<div").replace("TARGET<div", "<div")
    else:
        source = source.replace(">1<", "><")
    with pytest.raises(Sum20ParseError):
        parse_sum20_article(source, 1521)
