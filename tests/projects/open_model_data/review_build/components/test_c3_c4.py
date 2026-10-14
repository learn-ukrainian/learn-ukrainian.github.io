"""Synthetic WP3 card-ingestion inputs; no real dictionary content is committed."""

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from scripts.projects.open_model_data.review_build.attribution import Resolver
from scripts.projects.open_model_data.review_build.components import (
    ComponentContext,
    c3_relations,
    c3_sum20_meaning,
    c4_phraseology,
    load_components,
)
from scripts.projects.open_model_data.review_build.components.wp3_sources import (
    ARTICLE,
    CITATION,
    ENTRY,
    SECTION,
    SENSE,
    STORE,
    SUM20_ADAPTER,
    ULIF_ADAPTER,
    Markup,
    anchor,
    card_unit,
    cite,
    fetch,
    identity,
    query,
    ref,
)
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader

SYNONYM = "<p><b>SYNTHETIC alpha</b> (SYNTHETIC sense one), <b>SYNTHETIC beta</b>.</p>"
ANTONYM = "<table><tr><td><b>SYNTHETIC alpha</b></td><td><b>SYNTHETIC omega</b></td></tr><tr><td>SYNTHETIC left sense.</td><td>SYNTHETIC right sense.</td></tr></table>"
PHRASE = "<p><b>SYNTHETIC idiom,</b> SYNTHETIC definition. —<i>SYNTHETIC example <b>SYNTHETIC emphasis</b></i> (SYNTHETIC author); <i>SYNTHETIC second example</i> (SYNTHETIC second author).</p>"


def insert(conn, table, **row):
    columns = ",".join('"' + key + '"' for key in row)
    conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({','.join('?' for _ in row)})", list(row.values()))


@pytest.fixture
def sources(tmp_path):
    db = tmp_path / "SYNTHETIC-sources.db"
    with sqlite3.connect(db) as conn:
        conn.executescript("""
CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, canonical_headword TEXT, homonym_index INTEGER, homonym_checked INTEGER, status TEXT, retrieved_at TEXT);
CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT);
CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, stressed_headword TEXT, pos TEXT, official_url TEXT, fetched_at TEXT, quarantine_reason TEXT);
CREATE TABLE sum20_senses (id INTEGER PRIMARY KEY, article_id INTEGER, sense_order INTEGER, definition TEXT, register_labels TEXT);
CREATE TABLE sum20_citations (id INTEGER PRIMARY KEY, article_id INTEGER, sense_ref INTEGER, "order" INTEGER, citation_text TEXT);
""")
        for key in (1, 2):
            insert(
                conn,
                ENTRY,
                id=key,
                canonical_headword="SYNTHETIC alpha",
                homonym_index=key,
                homonym_checked=1,
                status="ok",
                retrieved_at="2026-01-01T00:00:00Z",
            )
        for key, kind, html in (
            (1, "synonyms", SYNONYM),
            (2, "antonyms", ANTONYM),
            (3, "phraseology", PHRASE),
            (4, "synonyms", SYNONYM),
        ):
            insert(
                conn,
                SECTION,
                id=key,
                entry_id=2 if key == 4 else 1,
                kind=kind,
                source_order=0,
                sense_or_group_id=f"{kind}:1",
                payload_json=json.dumps({"raw_html": html}),
            )
        for key in (1, 2, 3):
            insert(
                conn,
                ARTICLE,
                id=key,
                stressed_headword=f"SYNTHETIC headword {key}",
                pos="SYNTHETIC noun",
                official_url="https://sum20ua.com/SYNTHETIC",
                fetched_at="2026-01-01",
                quarantine_reason="SYNTHETIC quarantined" if key == 3 else "",
            )
        for key, article, order in ((10, 1, 1), (11, 1, 2), (12, 2, 1), (13, 3, 1)):
            insert(
                conn,
                SENSE,
                id=key,
                article_id=article,
                sense_order=order,
                definition=f"SYNTHETIC definition {key}",
                register_labels='["SYNTHETIC label"]',
            )
        for key, sense in ((1, 1), (2, 2)):
            insert(
                conn,
                CITATION,
                id=key,
                article_id=1,
                sense_ref=sense,
                **{"order": key},
                citation_text=f"SYNTHETIC citation {key}",
            )
    return db


def units(db, module):
    with SnapshotReader({STORE: db}) as reader:
        return list(module.iter_card_units(ComponentContext(reader, {})))


def validate(db, module, unit):
    with SnapshotReader({STORE: db}) as reader:
        module.validate(ComponentContext(reader, {}), unit)


def update(db, table, key, **fields):
    with sqlite3.connect(db) as conn:
        columns = ",".join('"' + name + '"=?' for name in fields)
        conn.execute(f"UPDATE {table} SET {columns} WHERE id=?", (*fields.values(), key))


def html_update(db, key, html):
    update(db, SECTION, key, payload_json=json.dumps({"raw_html": html}))


@pytest.mark.parametrize("module", [c3_relations, c3_sum20_meaning, c4_phraseology])
def test_ingestion_projection_preserves_all_cited_units_and_dispositions(sources, module):
    stream = units(sources, module)
    with SnapshotReader({STORE: sources}) as reader:
        direct = list(module.iter_candidates(ComponentContext(reader, {})))
        assert [unit.project(ComponentContext(reader, {})) for unit in stream] == direct
    assert all(unit.candidate.outcome == "accepted" for unit in stream)
    assert all(unit.parent_key and unit.group_key and unit.source_key for unit in stream)
    assert all(not hasattr(unit, "card_id") and not hasattr(unit, "sense_id") for unit in stream)
    if module == c3_relations:
        assert [(u.source_key, u.parent_key) for u in stream] == [
            ("id=2", "ulif_dictua_entries:id=1"),
            ("id=1", "ulif_dictua_entries:id=1"),
            ("id=4", "ulif_dictua_entries:id=2"),
        ]
    elif module == c3_sum20_meaning:
        assert [(u.source_key, u.source_order) for u in stream] == [("id=10", 1), ("id=11", 2), ("id=12", 1)]
    else:
        assert [v.text for v in stream[0].candidate.response] == [
            "SYNTHETIC definition.",
            "SYNTHETIC example SYNTHETIC emphasis (SYNTHETIC author)",
            "SYNTHETIC second example (SYNTHETIC second author)",
        ]


def test_no_direct_rb1_registration():
    for component in ("C3", "C4"):
        with pytest.raises(BuildError, match="component_unavailable"):
            load_components([component])


def test_full_numbered_meanings_need_no_training_prompt_discriminator(sources):
    long_definition = "SYNTHETIC full definition. " * 1000 + "SYNTHETIC final sentence."
    with sqlite3.connect(sources) as conn:
        conn.execute("DELETE FROM sum20_citations")
        for order in range(3, 15):
            insert(
                conn,
                SENSE,
                id=100 + order,
                article_id=1,
                sense_order=order,
                definition=long_definition,
                register_labels='["SYNTHETIC label"]',
            )
    stream = units(sources, c3_sum20_meaning)
    article = [u for u in stream if u.parent_key == "sum20_articles:id=1"]
    assert [u.source_order for u in article] == list(range(1, 15))
    assert all(u.candidate.outcome == "accepted" for u in article)
    assert article[-1].candidate.response[0].text == long_definition
    assert all(u.candidate.response[0].span is None for u in article)


def test_quarantine_excluded_and_forged_admission_refused(sources):
    stream = units(sources, c3_sum20_meaning)
    assert {u.source_key for u in stream} == {"id=10", "id=11", "id=12"}
    unit = stream[0]
    update(sources, ARTICLE, 1, quarantine_reason="SYNTHETIC hold")
    assert [u.source_key for u in units(sources, c3_sum20_meaning)] == ["id=12"]
    with pytest.raises(BuildError, match="quarantined_source"):
        validate(sources, c3_sum20_meaning, unit)


@pytest.mark.parametrize("module", [c3_relations, c3_sum20_meaning, c4_phraseology])
def test_soviet_source_never_enters_modern_fields(sources, module):
    unit = units(sources, module)[0]
    c = unit.candidate
    v = c.response[0]
    assert all(
        citation.source_id in {"sum20", "ulif"}
        for u in units(sources, module)
        for v in (*u.candidate.slots, *u.candidate.context, *u.candidate.response)
        for citation in v.citations
    )
    bad = replace(v, citations=(replace(v.citations[0], source_id="sum11"),))
    with pytest.raises(BuildError, match="source_compatibility"):
        validate(sources, module, replace(unit, candidate=replace(c, response=(bad, *c.response[1:]))))


def test_rada_wrong_homonym_fixture_fails(sources):
    # Only the attested headword is Ukrainian; definitions and relationships are synthetic.
    for key in (1, 2):
        update(sources, ENTRY, key, canonical_headword="рада")
    for key in (1, 4):
        html_update(sources, key, SYNONYM.replace("SYNTHETIC alpha", "рада"))
    stream = [u for u in units(sources, c3_relations) if u.candidate.operation == "synonyms"]
    first, donor = stream
    wrong = replace(first.candidate, slots=(donor.candidate.slots[0], first.candidate.slots[1]))
    with pytest.raises(BuildError, match="binding_group"):
        validate(sources, c3_relations, replace(first, candidate=wrong))


def test_multi_group_sense_not_visible_never_position_assigned(sources):
    html = "<p><b>SYNTHETIC alpha</b>, <b>SYNTHETIC beta</b>.</p>"
    html_update(sources, 1, html)
    with sqlite3.connect(sources) as conn:
        insert(
            conn,
            SECTION,
            id=5,
            entry_id=1,
            kind="synonyms",
            source_order=1,
            sense_or_group_id="synonyms:2",
            payload_json=json.dumps({"raw_html": html}),
        )
    stream = [u for u in units(sources, c3_relations) if u.source_key in {"id=1", "id=5"}]
    assert [u.candidate.reason for u in stream] == ["sense_not_visible"] * 2
    assert all(u.candidate.outcome == "withheld" and u.candidate.slots == () for u in stream)
    for unit in stream:
        with SnapshotReader({STORE: sources}) as reader:
            assert unit.project(ComponentContext(reader, {})) == unit.candidate
        with pytest.raises(BuildError):
            validate(
                sources,
                c3_relations,
                replace(unit, candidate=replace(unit.candidate, outcome="accepted", reason="ok", evidence=())),
            )


@pytest.mark.parametrize(
    "html,reason",
    [
        ("<p>SYNTHETIC missing heading.</p>", "headword_unresolved"),
        ("<b>SYNTHETIC first</b><b>SYNTHETIC second</b>", "sense_not_visible"),
        ("<b>SYNTHETIC idiom</b><i>SYNTHETIC quote</i> (SYNTHETIC author)", "definition_unresolved"),
        ("<b>SYNTHETIC idiom</b> SYNTHETIC definition.", "citation_unresolved"),
        ("<b>SYNTHETIC idiom</b> SYNTHETIC definition.<i>SYNTHETIC quote</i> ()", "citation_unresolved"),
        (PHRASE.replace(" (SYNTHETIC second author)", ""), "citation_unresolved"),
        (PHRASE.replace("SYNTHETIC example <b>SYNTHETIC emphasis</b>", ""), "citation_unresolved"),
    ],
)
def test_c4_requires_printed_idiom_definition_and_every_author_label(sources, html, reason):
    html_update(sources, 3, html)
    unit = units(sources, c4_phraseology)[0]
    assert unit.candidate.outcome == "withheld"
    assert unit.candidate.reason == reason
    with pytest.raises(BuildError):
        validate(
            sources,
            c4_phraseology,
            replace(unit, candidate=replace(unit.candidate, outcome="accepted", reason="ok", evidence=())),
        )


@pytest.mark.parametrize("mutation", ["omit", "reorder", "cross_sense", "truncate", "metadata"])
def test_meaning_binding_rejects_missing_reordered_or_foreign_values(sources, mutation):
    with sqlite3.connect(sources) as conn:
        insert(conn, CITATION, id=3, article_id=1, sense_ref=1, **{"order": 3}, citation_text="SYNTHETIC third quote")
    first, second, _ = units(sources, c3_sum20_meaning)
    c = first.candidate
    if mutation == "omit":
        bad = replace(c, context=c.context[:-1])
    elif mutation == "reorder":
        bad = replace(c, context=(*c.context[:2], *c.context[2:][::-1]))
    elif mutation == "cross_sense":
        bad = replace(c, context=(*c.context[:-1], second.candidate.context[-1]))
    elif mutation == "truncate":
        bad = replace(c, response=(replace(c.response[0], text=c.response[0].text[:-1]),))
    else:
        with pytest.raises(BuildError, match="binding_group"):
            validate(sources, c3_sum20_meaning, replace(first, group_key="2"))
        return
    with pytest.raises(BuildError, match=r"binding_sense|quote_mismatch"):
        validate(sources, c3_sum20_meaning, replace(first, candidate=bad))


@pytest.mark.parametrize("module", [c3_relations, c3_sum20_meaning, c4_phraseology])
@pytest.mark.parametrize("mutation", ["text", "locator", "digest", "transform", "span", "extra_citation", "operation"])
def test_cited_ingestion_refuses_forged_values(sources, module, mutation):
    unit = units(sources, module)[0]
    c, v = unit.candidate, unit.candidate.response[0]
    if mutation == "text":
        v = replace(v, text="SYNTHETIC absent")
    elif mutation == "locator":
        v = replace(v, citations=(replace(v.citations[0], locator="SYNTHETIC invented"),))
    elif mutation == "digest":
        v = replace(v, citations=(replace(v.citations[0], field_sha256="0" * 64),))
    elif mutation == "transform":
        v = replace(v, transform="SYNTHETIC paraphrase")
    elif mutation == "span":
        v = replace(v, span=(-1, 2))
    elif mutation == "extra_citation":
        v = replace(v, citations=v.citations * 2)
    else:
        c = replace(c, operation="SYNTHETIC wrong")
    with pytest.raises(BuildError):
        validate(sources, module, replace(unit, candidate=replace(c, response=(v, *c.response[1:]))))


@pytest.mark.parametrize(
    "module,field,reason",
    [
        (c3_sum20_meaning, "definition", "definition_unresolved"),
        (c3_sum20_meaning, "stressed_headword", "headword_unresolved"),
        (c3_sum20_meaning, "citation_text", "citation_unresolved"),
        (c3_relations, "homonym_checked", "homonym_unchecked"),
        (c4_phraseology, "homonym_checked", "homonym_unchecked"),
        (c3_relations, "status", "parse_error"),
        (c4_phraseology, "status", "parse_error"),
        (c3_relations, "canonical_headword", "headword_unresolved"),
        (c4_phraseology, "canonical_headword", "headword_unresolved"),
    ],
)
def test_unresolved_fields_stay_withheld(sources, module, field, reason):
    table = {"definition": SENSE, "stressed_headword": ARTICLE, "citation_text": CITATION}.get(field, ENTRY)
    update(sources, table, 10 if table == SENSE else 1, **{field: 0 if field == "homonym_checked" else ""})
    stream = units(sources, module)
    assert stream[0].candidate.outcome == "withheld"
    assert stream[0].candidate.reason == reason


@pytest.mark.parametrize("module,key", [(c3_relations, 1), (c4_phraseology, 3)])
@pytest.mark.parametrize("payload", ["broken", "{}", '{"raw_html":null}', '{"raw_html":42}'])
def test_malformed_payload_accounted_without_admission(sources, module, key, payload):
    update(sources, SECTION, key, payload_json=payload)
    unit = next(u for u in units(sources, module) if u.source_key == f"id={key}")
    assert unit.candidate.outcome == "withheld" and unit.candidate.reason == "parse_error"


def test_markup_positional_spans_and_relation_boundary_failures():
    markup = Markup("<p><b>SYNTHETIC&amp; one</b> <i>SYNTHETIC one</i> <i>SYNTHETIC one</i></p><br/>")
    assert markup.text == "SYNTHETIC& one SYNTHETIC one SYNTHETIC one"
    assert [markup.text[slice(*markup.span(n))] for n in markup.tagged("i")] == ["SYNTHETIC one"] * 2
    assert len({markup.span(n) for n in markup.tagged("i")}) == 2
    entry = {"canonical_headword": "SYNTHETIC omega"}
    span, reason = c3_relations.relation_span(Markup(ANTONYM), entry, "antonyms")
    assert reason is None and Markup(ANTONYM).text[slice(*span)] == "SYNTHETIC right sense."
    assert c3_relations.relation_span(Markup(""), entry, "synonyms") == (None, "headword_unresolved")
    assert c3_relations.relation_span(Markup("<b>SYNTHETIC omega</b>"), entry, "synonyms") == (
        None,
        "sense_not_visible",
    )
    assert c3_relations.relation_span(Markup("<b>SYNTHETIC omega</b>"), entry, "antonyms") == (
        None,
        "sense_not_visible",
    )
    assert Markup("<p><b>SYNTHETIC mismatched</p>").text == "SYNTHETIC mismatched"


def test_helpers_authenticate_source_field_and_unit_identity(sources):
    with SnapshotReader({STORE: sources}) as reader:
        row = fetch(reader, SECTION, 1)
        assert anchor(row, "members").text == row["payload_json"]
        assert reader.field(cite(SECTION, row, "payload_json#/raw_html", "ulif"))[1] == SYNONYM
        assert query("SELECT id FROM ulif_dictua_sections", [1])["parameters"] == [1]
        assert identity(SECTION, "response", "members")["primary"][0]["selector"] == ref("response", "members")
        with pytest.raises(BuildError, match="row_unavailable"):
            fetch(reader, ENTRY, -1)
        with pytest.raises(BuildError, match="field_unavailable"):
            cite(SECTION, row, "id", "ulif")
        c = units(sources, c3_relations)[0].candidate
        with pytest.raises(BuildError, match="ingestion_table"):
            card_unit(ComponentContext(reader, {}), c, ENTRY)


@pytest.mark.parametrize(
    "source,table,field,adapter",
    [
        ("ulif", ENTRY, "canonical_headword", ULIF_ADAPTER),
        ("sum20", ARTICLE, "stressed_headword", SUM20_ADAPTER),
    ],
)
def test_actual_register_forms_resolve_and_refuse_foreign_sources(sources, source, table, field, adapter):
    root = Path(__file__).resolve().parents[5]
    register = yaml.safe_load((root / "docs/sources/permissions-register.yaml").read_bytes())
    form = next(row["citation"]["form"] for row in register["sources"] if row["id"] == source)
    with SnapshotReader({STORE: sources}) as reader:
        row = fetch(reader, table, 1)
        citation = cite(table, row, field, source)
        licence, attribution = Resolver(register, {source: adapter}).resolve(citation, reader)
        assert source in licence and "retrieved=" in attribution
        assert adapter.resolve(form, citation, row, reader).mapped_form == form
        for bad_form, bad_citation, bad_row in [
            ("SYNTHETIC instruction", citation, row),
            (form, replace(citation, source_id="sum11"), row),
            (form, replace(citation, table="SYNTHETIC wrong"), row),
            (form, citation, {**row, "retrieved_at": "", "fetched_at": ""}),
            (
                form,
                citation,
                {**row, "quarantine_reason": "SYNTHETIC hold", "official_url": "https://synthetic.invalid/"},
            ),
        ]:
            # ULIF does not use SUM20 quarantine or edition fields.
            if source == "ulif" and "quarantine_reason" in bad_row:
                continue
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve(bad_form, bad_citation, bad_row, reader)


def test_projection_reauthenticates_against_changed_source_snapshot(sources):
    unit = units(sources, c3_sum20_meaning)[0]
    update(sources, ARTICLE, 1, quarantine_reason="SYNTHETIC hold")
    with SnapshotReader({STORE: sources}) as reader:
        with pytest.raises(BuildError, match="quarantined_source"):
            unit.project(ComponentContext(reader, {}))


@pytest.mark.parametrize("module", [c3_relations, c4_phraseology])
def test_malformed_and_empty_html_has_no_accepted_unit(sources, module):
    key = 1 if module == c3_relations else 3
    html_update(sources, key, "")
    unit = next(u for u in units(sources, module) if u.source_key == f"id={key}")
    assert unit.candidate.reason == ("empty_source" if module == c3_relations else "headword_unresolved")
    assert unit.candidate.outcome == "withheld"


def test_phrase_projection_refuses_parent_headword_removed(sources):
    unit = units(sources, c4_phraseology)[0]
    update(sources, ENTRY, 1, canonical_headword="")
    with SnapshotReader({STORE: sources}) as reader:
        with pytest.raises(BuildError, match="headword_unresolved"):
            unit.project(ComponentContext(reader, {}))
