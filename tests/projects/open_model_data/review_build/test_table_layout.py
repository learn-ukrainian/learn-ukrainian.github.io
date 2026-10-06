"""Synthetic-only regression tests for generic table association bindings."""

import json
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build.bindings import check
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Candidate, Citation, Value, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.table_layout import layout

POLICY = {
    "labels": {
        "singular": {"role": "number", "tags": ["s"]},
        "plural": {"role": "number", "tags": ["p"]},
        "case": {"role": "axis", "tags": []},
        "genitive": {"role": "case", "tags": ["gen"]},
        "future": {"role": "tense", "tags": ["future"]},
        "participle": {"role": "verbform", "tags": ["part"]},
        "masculine": {"role": "gender", "tags": ["m"]},
        "person": {"role": "person", "tags": ["1"]},
    },
    "data_classes": ["data"],
    "stress_marker": "\u0301",
    "column_roles": ["number", "gender"],
    "row_exclusive_roles": ["case", "verbform"],
    "axis_labels": ["case"],
    "section_roles": ["tense", "verbform"],
    "subsection_role": "verbform",
    "row_roles": ["case", "gender", "person"],
    "gender_role": "gender",
    "plural_tag": "p",
    "number_tags": ["s", "p"],
    "person_tags": ["1", "2", "3"],
}


def payload(rows):
    html = (
        "<table>" + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows) + "</table>"
    )
    return {"raw_html": html, "rows": rows}


def test_physical_cells_and_plural_gender_skip():
    p = payload([["case", "singular", "plural"], ["genitive", "SYNTHETIC-one", "SYNTHETIC-many"]])
    cells = layout(p, POLICY)
    assert [a.tags for a in cells] == [("gen", "s"), ("gen", "p")]
    assert cells[0].row.pointer == "/rows/1/0"
    assert cells[1].columns[0].pointer == "/rows/0/2"
    assert cells[0].cell.pointer == "/rows/1/1"
    p = payload([["singular", "plural"], ["masculine", "SYNTHETIC-many"]])
    p["raw_html"] = p["raw_html"].replace("<td>SYNTHETIC-many", '<td class="data">SYNTHETIC-many')
    assert layout(p, POLICY)[0].tags == ("p",)


def test_stacked_headers_spans_parent_subsection_and_person_order():
    p = {
        "raw_html": '<table><tr><td colspan="2">future</td></tr><tr><td colspan="2">participle</td></tr>'
        "<tr><td>case</td><td>singular</td></tr><tr><td>person</td><td>SYNTHETIC</td></tr></table>",
        "rows": [["future"], ["participle"], ["case", "singular"], ["person", "SYNTHETIC"]],
    }
    a = layout(p, POLICY)[0]
    assert a.tags == ("future", "part", "s", "1")
    assert [c.text for c in a.sections] == ["future", "participle"]
    p = {
        "raw_html": '<table><tr><td rowspan="2">case</td><td>singular</td></tr>'
        "<tr><td>masculine</td></tr><tr><td>genitive</td><td>SYNTHETIC</td></tr></table>",
        "rows": [["case", "singular"], ["masculine"], ["genitive", "SYNTHETIC"]],
    }
    assert [c.pointer for c in layout(p, POLICY)[0].columns] == ["/rows/0/1", "/rows/1/0"]


@pytest.mark.parametrize("mutation", ["rows", "overlap", "empty", "multiple"])
def test_table_authentication_refuses(mutation):
    p = payload([["case", "singular"], ["genitive", "SYNTHETIC"]])
    if mutation == "rows":
        p["rows"][0][1] = "SYNTHETIC-forged"
    elif mutation == "overlap":
        p["raw_html"] = '<table><tr><td>A</td><td rowspan="2">B</td></tr><tr><td colspan="2">C</td></tr></table>'
    elif mutation == "empty":
        p["raw_html"] = "<table><tr><td></td></tr></table>"
    else:
        p["raw_html"] += "<table></table>"
    with pytest.raises(BuildError, match="table_authentication"):
        layout(p, POLICY)


def test_dynamic_positional_headers_preserve_empty_levels_and_order():
    c = Candidate(
        "C2",
        "SYNTHETIC",
        "accepted",
        "ok",
        (),
        "agreed_form",
        tuple(Value(n, t, (), None, "verbatim") for n, t in [("column_0", "first"), ("column_1", "second")]),
        (),
        (),
        (),
    )
    serializer = {
        "slot": {
            "id": "c2-header-cells.v2",
            "section": {"prefix": "section_"},
            "row": {"slot": "row", "optional": True},
            "column": {"prefix": "column_"},
        }
    }
    assert json.loads(Catalog.rendered_slots(c, serializer)["slot"]) == [[], "", ["first", "second"]]
    with pytest.raises(BuildError, match="serializer"):
        Catalog.rendered_slots(replace(c, slots=(c.slots[1],)), serializer)


def test_projected_form_witnesses_remain_individually_bound():
    rows = {
        "id=1": {"form": "SYNTHETIC-a", "tags": '["gen","s"]'},
        "id=2": {"form": "SYNTHETIC-a", "tags": "noun:m:gen:s"},
        "id=3": {"form": "SYNTHETIC-b", "tags": '["gen","s"]'},
        "id=4": {"form": "SYNTHETIC-b", "tags": "noun:f:gen:s"},
    }

    class Reader:
        def row(self, c):
            return rows[c.row_key]

        def field(self, c):
            value = rows[c.row_key][c.field]
            return value, value

    def cite(i):
        return Citation(
            "synthetic",
            "synthetic.db",
            "units",
            f"id={i}",
            "form",
            "SYNTHETIC",
            digest(rows[f"id={i}"]["form"].encode()),
        )

    values = tuple(Value("form", rows[f"id={i}"]["form"], (cite(i), cite(i + 1)), None, "verbatim") for i in (1, 3))
    c = Candidate("C2", "SYNTHETIC", "accepted", "ok", (), "agreed_form", (), (), values, ())
    left = {"area": "response", "slot": "form", "match": "all"}
    right = {**left, "citation": 1}
    spec = {
        "schema": "binding-spec.v1",
        "rules": [
            {
                "op": "form_agreement",
                "values": [left, right],
                "left_tags": {"field": "tags"},
                "right_tags": {"field": "tags"},
                "tag_projection": {
                    "vocabulary": ["gen", "s", "m", "f"],
                    "separator": ":",
                    "ignore_when": {"noun": ["m", "f"]},
                },
            }
        ],
    }
    assert check(c, spec, Reader(), {}) == {"form_agreement"}
    rows["id=4"]["tags"] = "noun:f:gen:p"
    with pytest.raises(BuildError, match="binding_agreement"):
        check(c, spec, Reader(), {})
    rows["id=4"]["tags"] = "noun:f:gen:s"
    with pytest.raises(BuildError, match="binding_agreement"):
        check(replace(c, response=(values[0], replace(values[1], citations=(cite(3), cite(2))))), spec, Reader(), {})


@pytest.mark.parametrize("mutation", [None, "wrong_header", "missing_variant", "wrong_entry", "wrong_tags"])
def test_declarative_table_binding_recomputes_association(mutation):
    p = payload([["case", "singular", "plural"], ["genitive", "SYNTHETIC-a, SYNTHETIC-b", "SYNTHETIC-many"]])
    source = {
        "id=1": {"entry_id": 10, "tags": '["gen","s"]', "form": "SYNTHETIC-a"},
        "id=2": {"entry_id": 10, "payload": json.dumps(p)},
    }

    def cite(i, field):
        return Citation("synthetic", "synthetic.db", "units", f"id={i}", field, "SYNTHETIC", digest(b"SYNTHETIC"))

    class Reader:
        def row(self, c):
            return source[c.row_key]

    anchor = Value("anchor", "SYNTHETIC-a", (cite(1, "form"),), None, "verbatim")
    row = Value("row", "genitive", (cite(2, "payload#/rows/1/0"),), None, "verbatim")
    col = Value("column_0", "singular", (cite(2, "payload#/rows/0/1"),), None, "verbatim")
    response = tuple(Value("form", t, (cite(1, "form"),), None, "verbatim") for t in ("SYNTHETIC-a", "SYNTHETIC-b"))
    c = Candidate("C2", "SYNTHETIC", "accepted", "ok", (), "agreed_form", (anchor, row, col), (), response, ())
    rule = {
        "op": "table_binding",
        "anchor": {"area": "slots", "slot": "anchor"},
        "table": {"area": "slots", "slot": "row"},
        "entry_field": "entry_id",
        "tags_field": "tags",
        "section_prefix": "section_",
        "row_slot": "row",
        "column_prefix": "column_",
        "variant_separator": ",",
        "policy": POLICY,
        "values": [{"area": "response", "slot": "form", "match": "all"}],
    }
    if mutation == "wrong_header":
        c = replace(c, slots=(anchor, row, replace(col, text="plural", citations=(cite(2, "payload#/rows/0/2"),))))
    elif mutation == "missing_variant":
        c = replace(c, response=response[:1])
    elif mutation == "wrong_entry":
        source["id=2"]["entry_id"] = 11
    elif mutation == "wrong_tags":
        source["id=1"]["tags"] = '["gen","p"]'
    spec = {"schema": "binding-spec.v1", "rules": [rule]}
    if mutation:
        with pytest.raises(BuildError, match="binding_table"):
            check(c, spec, Reader(), {})
    else:
        assert check(c, spec, Reader(), {}) == {"table_binding"}
