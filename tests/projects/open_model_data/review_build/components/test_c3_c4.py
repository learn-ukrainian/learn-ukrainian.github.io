"""SYNTHETIC WP3 sources only; never load real dictionary rows in tests."""

import copy
import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import (
    ComponentContext,
    admission_policy,
    c3_relations,
    load_components,
    merge_adapters,
)
from scripts.projects.open_model_data.review_build.components.c3 import COMPONENT as C3
from scripts.projects.open_model_data.review_build.components.c4 import COMPONENT as C4
from scripts.projects.open_model_data.review_build.components.wp3_sources import (
    ARTICLE,
    CITATION,
    ENTRY,
    SECTION,
    SENSE,
    STORE,
    ULIF_ADAPTER,
    Markup,
    anchor,
    cite,
    fetch,
    section_value,
    value,
)
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import transform

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


def candidates(db, component):
    with SnapshotReader({STORE: db}) as reader:
        return list(component.iter_candidates(ComponentContext(reader, {})))


def gate(db, cs, operation, stream):
    spec = copy.deepcopy(cs.spec)
    spec["operations"] = [operation]
    spec["operation_specs"] = {operation: spec["operation_specs"][operation]}
    with SnapshotReader({STORE: db}) as reader:
        spec["operation_specs"][operation]["frozen_count"] = len(
            reader.units(spec["operation_specs"][operation]["unit_query"])
        )
    catalog_path = Path(__file__).resolve().parents[5] / "registry/projects/open_model_data/instruction_catalog.yaml"
    catalog = Catalog(yaml.safe_load(catalog_path.read_bytes()))
    entries = [
        {"id": s, "citation": {"form": "SYNTHETIC bibliography"}, "terms": {"licence": {"name": "SYNTHETIC licence"}}}
        for s in ("ulif", "sum20")
    ]
    with SnapshotReader({STORE: db}) as reader:
        g = Gate(
            reader,
            catalog,
            Resolver({"sources": entries}, {s: SyntheticAdapter() for s in ("ulif", "sum20")}),
            {stream[0].component: spec},
        )
        return g.run(stream)


def test_registered_components_share_adapter_and_independent_denominators(sources):
    assert load_components(["C3", "C4"]) == {"C3": C3, "C4": C4}
    assert merge_adapters(C3.adapters, C4.adapters)["ulif"] is ULIF_ADAPTER
    with SnapshotReader({STORE: sources}) as reader:
        for component in (C3, C4):
            stream = list(component.iter_candidates(ComponentContext(reader, {})))
            for op, spec in component.spec["operation_specs"].items():
                assert set(reader.units(spec["unit_query"])) == {c.unit_id for c in stream if c.operation == op}
    assert {op: s["frozen_count"] for op, s in C3.spec["operation_specs"].items()} == {
        "synonyms": 75955,
        "antonyms": 2103,
        "sense_definition": 168,
    }
    assert C4.spec["operation_specs"]["idiom_definition"]["frozen_count"] == 8133


@pytest.mark.parametrize("op", ["synonyms", "antonyms", "sense_definition"])
def test_c3_accept_paths(sources, op):
    stream = [c for c in candidates(sources, C3) if c.operation == op]
    assert all(c.outcome == "accepted" for c in stream)
    records, report = gate(sources, C3, op, stream)
    assert len(records) == len(stream)
    assert report["accounting"]["C3"]["withheld"] == 0
    if op == "sense_definition":
        assert {c.unit_id for c in stream} == {"10", "11", "12"}
        assert all(c.unit_id != "13" for c in stream)
        assert [v.text for v in stream[0].context if v.slot == "sense_citations"] == ["SYNTHETIC citation 1"]
        assert next(r for r in records if r["response"] == "SYNTHETIC definition 12")["catalog_line_id"].startswith(
            "C3.sense_definition.0"
        )


def test_c4_accept_target_has_definition_and_author_labelled_citations(sources):
    stream = candidates(sources, C4)
    records, _ = gate(sources, C4, "idiom_definition", stream)
    response = json.loads(records[0]["response"])
    assert response[0] == "SYNTHETIC definition."
    assert response[1:] == [
        "SYNTHETIC example SYNTHETIC emphasis (SYNTHETIC author)",
        "SYNTHETIC second example (SYNTHETIC second author)",
    ]


def test_wrong_homonym_relation_must_fail_despite_same_surface(sources):
    stream = [c for c in candidates(sources, C3) if c.operation == "synonyms"]
    first, donor = stream
    mutated = replace(first, slots=(donor.slots[0], first.slots[1]))
    with pytest.raises(BuildError, match="binding_group"):
        gate(sources, C3, "synonyms", [mutated, donor])


def test_wrong_group_sense_and_phrase_definition_must_fail(sources):
    stream = [c for c in candidates(sources, C3) if c.operation == "synonyms"]
    first, donor = stream
    with pytest.raises(BuildError, match=r"binding_group|binding_row"):
        gate(sources, C3, "synonyms", [replace(first, slots=(first.slots[0], donor.slots[1])), donor])
    phrase = candidates(sources, C4)[0]
    with SnapshotReader({STORE: sources}) as reader:
        other = section_value(fetch(reader, SECTION, 1), "definition")
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        gate(sources, C4, "idiom_definition", [replace(phrase, response=(other, *phrase.response[1:]))])


@pytest.mark.parametrize(
    "bad", ["absent_quote", "wrong_span", "empty_locator", "paraphrase_transform", "reasoning", "missing_unit"]
)
def test_generic_must_fail_fixtures(sources, bad):
    stream = candidates(sources, C4)
    c = stream[0]
    v = c.slots[0]
    if bad == "missing_unit":
        # Retain measured denominator, remove the sole independently counted unit.
        with SnapshotReader({STORE: sources}) as reader:
            spec = copy.deepcopy(C4.spec)
            spec["operation_specs"]["idiom_definition"]["frozen_count"] = 1
            assert reader.units(spec["operation_specs"]["idiom_definition"]["unit_query"]) == ["3"]
            g = Gate(
                reader,
                Catalog(
                    {
                        "schema_version": "instruction-catalog.v1",
                        "version": "1",
                        "status": "reviewed_rb1",
                        "components": {"C4": {"instructions": []}},
                    }
                ),
                Resolver({"sources": []}, {}),
                {"C4": spec},
            )
            with pytest.raises(BuildError, match="missing_unit"):
                g.run([])
        return
    if bad == "absent_quote":
        v = replace(v, text="SYNTHETIC absent")
    if bad == "wrong_span":
        v = replace(v, span=(1, 2))
    if bad == "empty_locator":
        v = replace(v, citations=(replace(v.citations[0], locator=""),))
    if bad == "paraphrase_transform":
        v = replace(v, transform="SYNTHETIC paraphrase")
    if bad == "reasoning":
        with sqlite3.connect(sources) as conn:
            conn.execute(
                "UPDATE ulif_dictua_sections SET payload_json=? WHERE id=3",
                (json.dumps({"raw_html": PHRASE.replace("SYNTHETIC idiom", "Step 1 SYNTHETIC idiom")}),),
            )
        stream = candidates(sources, C4)
        c = stream[0]
        v = c.slots[0]
    errors = {
        "absent_quote": "quote_mismatch",
        "wrong_span": "quote_mismatch",
        "empty_locator": "empty_locator",
        "paraphrase_transform": "unknown_transform",
        "reasoning": "reasoning_text",
    }
    with pytest.raises(BuildError, match=errors[bad]):
        gate(sources, C4, "idiom_definition", [replace(c, slots=(v,))])


def test_multi_group_without_visible_discriminator_is_withheld(sources):
    html = "<p><b>SYNTHETIC alpha</b>, <b>SYNTHETIC beta</b>.</p>"
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE ulif_dictua_sections SET payload_json=? WHERE id=1", (json.dumps({"raw_html": html}),))
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
    stream = [c for c in candidates(sources, C3) if c.operation == "synonyms"]
    assert [c.reason for c in stream if c.unit_id in ("1", "5")] == ["sense_not_visible"] * 2
    assert gate(sources, C3, "synonyms", stream)[1]["accounting"]["C3"]["withheld"] == 2


def test_sum20_cross_sense_citation_and_missing_citation_must_fail(sources):
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    first, second, last = stream
    wrong = next(v for v in second.context if v.slot == "sense_citations")
    bad = replace(first, context=tuple(wrong if v.slot == "sense_citations" else v for v in first.context))
    with pytest.raises(BuildError, match="binding_group"):
        gate(sources, C3, "sense_definition", [bad, second, last])
    bad = replace(first, context=tuple(v for v in first.context if v.slot != "sense_citations"))
    with pytest.raises(BuildError, match="binding_sequence"):
        gate(sources, C3, "sense_definition", [bad, second, last])


def test_sum20_quarantine_cannot_be_added_as_accepted(sources):
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    with SnapshotReader({STORE: sources}) as reader:
        row = fetch(reader, SENSE, 13)
        c = replace(stream[-1], unit_id="13", response=(value(SENSE, row, "definition", "sum20", "definition"),))
    with pytest.raises(BuildError, match="missing_unit"):
        gate(sources, C3, "sense_definition", [*stream, c])


@pytest.mark.parametrize(
    "kind,html,reason",
    [
        ("synonyms", "", "empty_source"),
        ("synonyms", "<p><b>SYNTHETIC foreign</b>, <b>SYNTHETIC other</b></p>", "headword_unresolved"),
        ("antonyms", "<table><tr><td><b>SYNTHETIC alpha</b></td></tr></table>", "sense_not_visible"),
        ("phraseology", "<p><b>SYNTHETIC idiom</b> SYNTHETIC definition.</p>", "citation_unresolved"),
        (
            "phraseology",
            "<p><b>SYNTHETIC idiom</b><i>SYNTHETIC quote</i> (SYNTHETIC author)</p>",
            "definition_unresolved",
        ),
        (
            "phraseology",
            "<p><b>SYNTHETIC idiom</b> SYNTHETIC definition.<b>SYNTHETIC another idiom</b><i>SYNTHETIC quote</i> (SYNTHETIC author)</p>",
            "sense_not_visible",
        ),
    ],
)
def test_unsupported_source_shapes_withhold(sources, kind, html, reason):
    key = {"synonyms": 1, "antonyms": 2, "phraseology": 3}[kind]
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE ulif_dictua_sections SET payload_json=? WHERE id=?", (json.dumps({"raw_html": html}), key))
    stream = candidates(sources, C4 if kind == "phraseology" else C3)
    c = next(
        c
        for c in stream
        if c.unit_id == str(key) and c.operation == ("idiom_definition" if kind == "phraseology" else kind)
    )
    assert c.outcome == "withheld" and c.reason == reason and c.evidence


def test_unchecked_and_parse_error_entries_withhold(sources):
    for column, val, reason in [("homonym_checked", 0, "homonym_unchecked"), ("status", "parse_error", "parse_error")]:
        with sqlite3.connect(sources) as conn:
            conn.execute("UPDATE ulif_dictua_entries SET homonym_checked=1,status='ok'")
            conn.execute(f"UPDATE ulif_dictua_entries SET {column}=? WHERE id=1", (val,))
        assert {c.reason for c in candidates(sources, C4)} == {reason}
        assert {
            c.reason
            for c in candidates(sources, C3)
            if c.operation in ("synonyms", "antonyms") and c.unit_id in ("1", "2")
        } == {reason}


def test_malformed_payload_preserves_accounting_anchor(sources):
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE ulif_dictua_sections SET payload_json='SYNTHETIC invalid JSON' WHERE id=3")
    stream = candidates(sources, C4)
    assert stream[0].reason == "parse_error"
    assert gate(sources, C4, "idiom_definition", stream)[1]["accounting"]["C4"]["withheld"] == 1


def test_sum20_missing_and_indistinguishable_context_withhold(sources):
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE sum20_citations SET citation_text='SYNTHETIC same example'")
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    assert {c.reason for c in stream if c.unit_id in ("10", "11")} == {"context_not_discriminating"}
    with sqlite3.connect(sources) as conn:
        conn.execute("DELETE FROM sum20_citations")
    assert {
        c.reason for c in candidates(sources, C3) if c.operation == "sense_definition" and c.unit_id in ("10", "11")
    } == {"sense_not_visible"}


def test_markup_offsets_match_framework_without_added_whitespace():
    html = "<p>  <b>SYNTHETIC <a>alpha</a></b>,\n<i>SYNTHETIC&nbsp; quote</i> (SYNTHETIC author) </p>"
    markup = Markup(html)
    assert markup.text == transform("ulif_html_text@1", html).text
    assert markup.text[slice(*markup.span(markup.tagged("b")[0]))] == "SYNTHETIC alpha"
    assert markup.text[slice(*markup.span(markup.tagged("i")[0]))] == "SYNTHETIC quote"
    assert Markup("<br/><p>SYNTHETIC</p>").text == "SYNTHETIC"


def test_attribution_maps_complete_forms_and_refuses_unmapped_metadata(sources):
    # Bibliography forms are SYNTHETIC; only the mechanism's expected digest is
    # overridden, never any real dictionary text copied to this fixture.
    from scripts.projects.open_model_data.review_build.components.wp3_sources import Sum20Adapter, UlifAdapter
    from scripts.projects.open_model_data.review_build.contract import digest

    ulif = UlifAdapter()
    sum20 = Sum20Adapter()
    forms = {
        ulif: "SYNTHETIC bibliography (entry reference and retrieval date per field)",
        sum20: "SYNTHETIC bibliography — official edition only, never a mirror (docs/best-practices/atlas-source-presentation.md).",
    }
    with SnapshotReader({STORE: sources}) as reader:
        for adapter, table, source in ((ulif, SECTION, "ulif"), (sum20, SENSE, "sum20")):
            form = forms[adapter]
            adapter.FORM_SHA = digest(form.encode())
            row = fetch(reader, table, 1 if table == SECTION else 10)
            c = cite(table, row, "payload_json" if table == SECTION else "definition", source)
            result = adapter.resolve(form, c, row, reader)
            assert result.mapped_form == form and result.bibliography.startswith("SYNTHETIC bibliography")
            assert "retrieved=" in result.bibliography
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve("SYNTHETIC <insert bibliography>", c, row, reader)
        row = fetch(reader, ARTICLE, 3)
        with pytest.raises(BuildError, match="attribution_unresolved"):
            sum20.resolve(forms[sum20], cite(ARTICLE, row, "stressed_headword", "sum20"), row, reader)
        assert reader.snapshots()


def test_shared_helpers_refuse_unavailable_rows_and_use_whole_payload_anchor(sources):
    with SnapshotReader({STORE: sources}) as reader:
        with pytest.raises(BuildError, match="row_unavailable"):
            fetch(reader, ENTRY, 999)
        row = fetch(reader, SECTION, 1)
        assert anchor(row, "unit").text == row["payload_json"]
        assert (
            section_value(row, "unit").text
            == transform("ulif_html_text@1", json.loads(row["payload_json"])["raw_html"]).text
        )


@pytest.mark.parametrize(
    "table,column,new_value,reason",
    [
        (ARTICLE, "stressed_headword", "", "headword_unresolved"),
        (SENSE, "definition", "", "definition_unresolved"),
        (CITATION, "citation_text", "", "citation_unresolved"),
    ],
)
def test_missing_meaning_fields_withhold(sources, table, column, new_value, reason):
    with sqlite3.connect(sources) as conn:
        conn.execute(f"UPDATE {table} SET {column}=?", (new_value,))
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    assert any(c.reason == reason and c.outcome == "withheld" and c.evidence for c in stream)
    gate(sources, C3, "sense_definition", stream)


def test_pos_from_another_article_must_fail(sources):
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    wrong = next(v for v in stream[-1].context if v.slot == "pos")
    bad = replace(stream[0], context=tuple(wrong if v.slot == "pos" else v for v in stream[0].context))
    with pytest.raises(BuildError, match="binding_group"):
        gate(sources, C3, "sense_definition", [bad, *stream[1:]])


def test_antonym_selects_headwords_own_column_and_refuses_missing_definition():
    entry = {"canonical_headword": "SYNTHETIC omega"}
    markup = Markup(ANTONYM)
    span, reason = c3_relations.relation_span(markup, entry, "antonyms")
    assert reason is None and markup.text[slice(*span)] == "SYNTHETIC right sense."
    markup = Markup(ANTONYM.replace("SYNTHETIC right sense.", ""))
    assert c3_relations.relation_span(markup, entry, "antonyms") == (None, "sense_not_visible")


def test_markup_entities_nested_and_repeated_spans_remain_positional():
    markup = Markup("<p><b>SYNTHETIC&amp; one</b> <i>SYNTHETIC one</i> <i>SYNTHETIC one</i></p>")
    assert len({markup.span(n) for n in markup.tagged("i")}) == 2
    assert markup.text.startswith("SYNTHETIC& one")
    assert Markup("<p><b>SYNTHETIC mismatched</p>").text == "SYNTHETIC mismatched"
    assert Markup("<p><b>SYNTHETIC alpha</b></p><unknown/>").text == "SYNTHETIC alpha"


def test_attribution_refuses_missing_dates_foreign_urls_and_instruction_forms(sources):
    from scripts.projects.open_model_data.review_build.components.wp3_sources import Sum20Adapter, UlifAdapter
    from scripts.projects.open_model_data.review_build.contract import digest

    adapters = [
        (
            UlifAdapter(),
            ENTRY,
            "ulif",
            "canonical_headword",
            "SYNTHETIC bibliography (entry reference and retrieval date per field)",
        ),
        (
            Sum20Adapter(),
            ARTICLE,
            "sum20",
            "stressed_headword",
            "SYNTHETIC bibliography — official edition only, never a mirror (docs/best-practices/atlas-source-presentation.md).",
        ),
    ]
    with SnapshotReader({STORE: sources}) as reader:
        for adapter, table, source, field, form in adapters:
            adapter.FORM_SHA = digest(form.encode())
            row = fetch(reader, table, 1)
            citation = cite(table, row, field, source)
            assert adapter.resolve(form, citation, row, reader).mapped_form == form
            bad = {**row, "retrieved_at": "", "fetched_at": ""}
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve(form, citation, bad, reader)
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve(form, replace(citation, table="SYNTHETIC wrong"), row, reader)
            adapter.FORM_SHA = digest(b"SYNTHETIC insert bibliography")
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve("SYNTHETIC insert bibliography", citation, row, reader)
        sum20, table, source, field, form = adapters[-1]
        sum20.FORM_SHA = digest(form.encode())
        row = fetch(reader, ARTICLE, 1)
        with pytest.raises(BuildError, match="attribution_unresolved"):
            sum20.resolve(
                form, cite(ARTICLE, row, field, source), {**row, "official_url": "https://synthetic.invalid/"}, reader
            )


def test_reordered_same_sense_citations_must_fail(sources):
    with sqlite3.connect(sources) as conn:
        insert(
            conn, CITATION, id=3, article_id=1, sense_ref=1, **{"order": 3}, citation_text="SYNTHETIC citation three"
        )
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    first = stream[0]
    fixed = [v for v in first.context if v.slot != "sense_citations"]
    citations = [v for v in first.context if v.slot == "sense_citations"]
    assert [v.text for v in citations] == ["SYNTHETIC citation 1", "SYNTHETIC citation three"]
    with pytest.raises(BuildError, match="binding_sequence"):
        gate(sources, C3, "sense_definition", [replace(first, context=tuple([*fixed, *citations[::-1]])), *stream[1:]])


def test_independent_applicability_refuses_indistinguishable_source_context(sources):
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE sum20_citations SET citation_text='SYNTHETIC identical examples'")
    stream = [c for c in candidates(sources, C3) if c.operation == "sense_definition"]
    first = replace(stream[0], outcome="accepted", reason="ok", evidence=())
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        gate(sources, C3, "sense_definition", [first, *stream[1:]])


def test_registered_policy_union_preserves_source_roles_and_quarantine():
    policy, corpus = admission_policy({"C3": C3.spec, "C4": C4.spec})
    assert corpus is None
    assert len(policy) == 5
    assert all(row["role"] == "modern" and row["sensitive"] is None for row in policy)
    assert next(row for row in policy if row["table"] == ARTICLE)["quarantine"] == "quarantine_reason"
    assert C4.spec["compatibility"] == [row for row in C3.spec["compatibility"] if row["source_id"] == "ulif"]


def test_registered_cli_uses_v2_locations_and_component_policy(sources, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    register = tmp_path / "SYNTHETIC-register.yaml"
    register.write_text(
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "id": source,
                        "citation": {"form": "SYNTHETIC bibliography"},
                        "terms": {"licence": {"name": "SYNTHETIC licence"}},
                    }
                    for source in ("ulif", "sum20")
                ]
            }
        )
    )
    request = tmp_path / "SYNTHETIC-request.json"
    request.write_text(
        json.dumps(
            {
                "schema": "omd-review-request.v2",
                "databases": {STORE: str(sources)},
                "catalog": str(
                    Path(__file__).resolve().parents[5] / "registry/projects/open_model_data/instruction_catalog.yaml"
                ),
                "register": str(register),
                "ua_gec": {"root": str(tmp_path / "SYNTHETIC-unused-corpus")},
            }
        )
    )
    loaded = {}
    with SnapshotReader({STORE: sources}) as reader:
        for component_id, component in (("C3", C3), ("C4", C4)):
            spec = copy.deepcopy(component.spec)
            for operation in spec["operation_specs"].values():
                operation["frozen_count"] = len(reader.units(operation["unit_query"]))
            loaded[component_id] = SimpleNamespace(
                spec=spec,
                files={},
                adapters={source: SyntheticAdapter() for source in component.adapters},
                iter_candidates=component.iter_candidates,
            )
    # Components sharing a source must use exactly one adapter object.
    loaded["C4"].adapters["ulif"] = loaded["C3"].adapters["ulif"]
    out = tmp_path / "SYNTHETIC-cli-output"
    args = ["--config", str(request), "--out", str(out), "--components", "C3", "C4"]
    for command, status in (("build", "built"), ("verify", "verified")):
        assert cli.main([command, *args], _test_components=loaded) == 0
        assert json.loads(capsys.readouterr().out)["status"] == status
    manifest = json.loads((out / "manifest.json").read_bytes())
    assert manifest["operation_accounting"]["C3.sense_definition"]["accepted"] == 3
    assert manifest["operation_accounting"]["C4.idiom_definition"]["accepted"] == 1
    assert len(json.loads((out / "mutation-fixtures/results.json").read_bytes())) == 5
    for invalid in (
        {"schema": "omd-review-request.v1"},
        {"compatibility": C3.spec["compatibility"]},
        {"corpus": {"store": STORE}},
        {"components": {"C3": C3.spec}},
    ):
        original = json.loads(request.read_bytes())
        request.write_text(json.dumps({**original, **invalid}))
        assert cli.main(["build", *args], _test_components=loaded) == 1
        error = json.loads(capsys.readouterr().err)["error"]
        assert error == ("request_schema" if "schema" in invalid else "request_policy_key")
        request.write_text(json.dumps(original))
