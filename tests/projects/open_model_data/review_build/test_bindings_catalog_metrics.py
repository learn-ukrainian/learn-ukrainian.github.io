import copy
import sqlite3
from collections import Counter
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Value, record_id
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.metrics import measure, tokens
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import citation, register_data, run_gate, selector


def test_round_robin_is_exactly_balanced_and_input_order_independent(bundle):
    catalog = Catalog(bundle["catalog"])
    candidates = bundle["candidates"] * 0 + bundle["candidates"]
    applicability = {record_id(c): catalog.applicable(c) for c in candidates}
    forward = catalog.assign(candidates, applicability)
    assert forward == catalog.assign(list(reversed(candidates)), applicability)
    assert set(Counter(forward.values()).values()) == {1}
    assert list(forward) == sorted(forward)
    # Applicability sets have their own independent rotation.
    ids = list(applicability)
    applicability[ids[0]] = applicability[ids[0]][:1]
    assert catalog.assign(candidates, applicability)[ids[0]] == applicability[ids[0]][0]


def test_catalog_refuses_draft_invalid_placeholders_and_recursive_interpolation(bundle):
    bad = copy.deepcopy(bundle["catalog"])
    bad["status"] = "draft"
    with pytest.raises(BuildError, match="catalog_unreviewed"):
        Catalog(bad)
    for template in ("SYNTHETIC {missing}", "SYNTHETIC {sentence.__class__}", "SYNTHETIC {sentence!r}"):
        bad = copy.deepcopy(bundle["catalog"])
        bad["components"]["C1"]["instructions"][0]["template"] = template
        with pytest.raises(BuildError):
            Catalog(bad)
    c = bundle["candidates"][0]
    c = replace(c, slots=(replace(c.slots[0], text="SYNTHETIC {target}"),))
    cat = Catalog(bundle["catalog"])
    line = cat.applicable(c)[0]
    assert cat.render(c, line).endswith("SYNTHETIC {target}")
    with pytest.raises(BuildError):
        cat.applicable(replace(c, slots=(replace(c.slots[0], text="   "),)))
    bad = copy.deepcopy(bundle["catalog"])
    bad["components"]["C1"]["instructions"][0]["template"] = "SYNTHETIC «{sentence}»"
    cat = Catalog(bad)
    c = replace(c, slots=(replace(c.slots[0], text="SYNTHETIC «quoted»"),))
    assert bad["components"]["C1"]["instructions"][0]["id"] not in cat.applicable(c)


def test_c2_applicability_requires_source_supported_discrimination_and_safe_empty_sense(bundle):
    data = copy.deepcopy(bundle["catalog"])
    lines = data["components"].pop("C1")["instructions"][:2]
    lines[0].update(
        id="C2.agreed_form.with",
        operation="agreed_form",
        sense_variant="with_sense",
        template="SYNTHETIC {sentence}: {sense}",
        slots=["sentence", "sense"],
    )
    lines[1].update(id="C2.agreed_form.without", operation="agreed_form", sense_variant="without_sense")
    data["components"]["C2"] = {"instructions": lines}
    catalog = Catalog(data)
    c = bundle["candidates"][0]
    sense = replace(c.slots[0], slot="sense", text="SYNTHETIC sense")
    c = replace(c, component="C2", operation="agreed_form", slots=(*c.slots, sense))
    with pytest.raises(BuildError):
        catalog.applicable(c)
    assert catalog.applicable(c, discriminating=True) == ("C2.agreed_form.with",)
    c = replace(c, slots=(c.slots[0], replace(sense, text=" ")))
    with pytest.raises(BuildError):
        catalog.applicable(c)
    assert catalog.applicable(c, empty_safe=True) == ("C2.agreed_form.without",)


def test_metrics_exact_shares_and_small_denominators(bundle):
    catalog = Catalog(bundle["catalog"])
    ids = list(catalog.lines)
    report = measure(ids, catalog)
    assert report["status"] == "PASS"
    assert report["prefix1"]["top1"] == [1, 12]
    assert report["prefix4"]["top5"] == [5, 12]
    assert measure(ids[:9], catalog)["status"] == "insufficient_evidence"
    assert measure([], catalog)["status"] == "missing_coverage"
    assert measure([ids[0]] * 12, catalog)["status"] == "FAIL"
    assert measure(ids[:10] + ids[:1] * 2, catalog)["status"] == "FAIL"
    assert tokens("SYNTHETIC 'apostrophe' A’B 123 punctuation!") == ("synthetic", "apostrophe", "a’b", "punctuation")


@pytest.mark.parametrize("kind", ["prefix", "suffix", "middle", "threshold"])
def test_concentration_failures_cannot_be_hidden_by_ids_or_source_text(bundle, kind):
    data = copy.deepcopy(bundle["catalog"])
    lines = data["components"]["C1"]["instructions"]
    common = "SYNTHETIC common shared eight token instruction ending with repetition"
    for line in lines:
        if kind == "prefix":
            line["template"] = "SYNTHETIC common " + line["template"]
        elif kind == "suffix":
            line["template"] += " " + common
        elif kind == "middle":
            line["template"] = line["template"].split()[0] + " " + common + " ending " + line["template"]
    if kind == "threshold":
        data["prefix_metric"]["top1_max"] = 0.9
    cat = Catalog(data)
    if kind == "threshold":
        with pytest.raises(BuildError, match="metric_spec"):
            measure(list(cat.lines), cat)
    else:
        assert measure(list(cat.lines), cat)["status"] == "FAIL"
        bundle["catalog"] = data
        with pytest.raises(BuildError, match="instruction_concentration"):
            run_gate(bundle)


def test_binding_engine_region_group_contiguity_and_unknown_rule(bundle):
    text = "SYNTHETIC rule: SYNTHETIC example\nSYNTHETIC outside"
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
    row = {**bundle["rows"][0], "source_field": text}
    example = Value("example", "SYNTHETIC example", (citation(row),), (16, 33), "verbatim")
    candidate = replace(bundle["candidates"][0], slots=(example,))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        spec = {"schema": "binding-spec.v1", "rules": [{"op": "example_list", "values": [selector(slot="example")]}]}
        # Locate the actual source span rather than relying on the example fixture offsets.
        start = text.index("SYNTHETIC example")
        candidate = replace(candidate, slots=(replace(example, span=(start, start + len(example.text))),))
        assert "example_list" in bindings.check(candidate, spec, reader, {})
        bad = replace(candidate, slots=(replace(candidate.slots[0], span=(34, len(text))),))
        with pytest.raises(BuildError, match="binding_example"):
            bindings.check(bad, spec, reader, {})
        good = bundle["candidates"][0]
        spec["rules"] = [
            {
                "op": "one_group",
                "values": [selector(field="group_id"), selector("response", "target", field="group_id")],
            },
            {"op": "literal", "values": [selector(field="group_id")], "expected": "SYNTHETIC group"},
        ]
        assert bindings.check(good, spec, reader, {}) == {"one_group", "literal"}
        pages = replace(
            good,
            response=tuple(replace(c.response[0], slot=f"page{i}") for i, c in enumerate(bundle["candidates"][:3])),
        )
        spec["rules"] = [
            {
                "op": "contiguous_pages",
                "values": [selector("response", f"page{i}", field="id") for i in range(3)],
                "first": 1,
                "next_heading": 4,
                "source_field": "source_file",
            }
        ]
        assert bindings.check(pages, spec, reader, {}) == {"contiguous_pages"}
        spec["rules"][0]["next_heading"] = 5
        with pytest.raises(BuildError, match="binding_pages"):
            bindings.check(pages, spec, reader, {})
        spec["rules"] = [{"op": "SYNTHETIC arbitrary"}]
        with pytest.raises(BuildError, match="unknown_binding"):
            bindings.check(good, spec, reader, {})


def test_supporting_citation_needs_independent_agreement(bundle):
    c = bundle["candidates"][0]
    primary = c.response[0]
    supporting = citation(bundle["rows"][0], "target_field")
    supported = replace(primary, citations=(*primary.citations, supporting))
    bundle["candidates"][0] = replace(c, response=(supported,))
    with pytest.raises(BuildError, match="supporting_unbound"):
        run_gate(bundle)
    bundle["candidates"] = [
        replace(
            candidate,
            response=(
                replace(
                    candidate.response[0], citations=(candidate.response[0].citations[0], citation(row, "target_field"))
                ),
            ),
        )
        for candidate, row in zip(bundle["candidates"], bundle["rows"], strict=True)
    ]
    bundle["spec"]["binding"]["rules"].append(
        {
            "op": "form_agreement",
            "values": [
                selector("response", "target", field="target_field"),
                selector("response", "target", citation=1, field="target_field"),
            ],
            "left_tags": selector("response", "target", field="tags"),
            "right_tags": selector("response", "target", citation=1, field="tags"),
        }
    )
    assert len(run_gate(bundle)[0]) == 12


@pytest.mark.parametrize("mismatch", [False, True, "swapped", "adjudication"])
def test_c7_shared_pair_form_keys_and_adjudication(bundle, mismatch):
    # All strings are synthetic; this tests structural admission, not linguistic truth.
    sources = ("synthetic", "synthetic_book", "sum11", "synthetic_ulif", "synthetic_vesum", "synthetic_receipt")
    bundle["register"] = register_data(sources=sources)
    bundle["config"]["compatibility"] = [
        {"store": "sources.db", "table": "units", "source_id": s, "role": "sum11" if s == "sum11" else "modern"}
        for s in sources
    ]
    c = bundle["candidates"][0]
    row = bundle["rows"][0]
    left = Value(
        "rejected",
        row["source_field"],
        (citation(row, source="sum11"), citation(row, source="synthetic_book")),
        None,
        "verbatim",
    )
    right = Value(
        "recommended",
        row["target_field"],
        (
            citation(row, "target_field", source="synthetic_book"),
            citation(row, "target_field", source="synthetic_ulif"),
            citation(row, "target_field", source="synthetic_vesum"),
        ),
        None,
        "verbatim",
    )
    receipt = Value("receipt", row["source_field"], (citation(row, source="synthetic_receipt"),), None, "verbatim")
    c = replace(c, component="C7", context=(left, right, receipt), flags=("c7_opt_in", "soviet_colonization_context"))
    bundle["candidates"] = [c]
    bundle["spec"]["unit_query"]["sql"] += " WHERE id=1"
    bundle["spec"]["frozen_count"] = 1
    bundle["config"]["components"] = {"C7": bundle["spec"]}
    bundle["catalog"]["components"]["C7"] = bundle["catalog"]["components"].pop("C1")
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute(
            "UPDATE units SET sol='APPROVE',opus=?,pair='id=1' WHERE id=1",
            ("SYNTHETIC missing" if mismatch == "adjudication" else "APPROVE",),
        )
    pair = {
        "op": "contrast_pair",
        "rejected": selector("context", "rejected"),
        "recommended": selector("context", "recommended"),
        "response": selector("response", "target"),
        "book_rejected": selector("context", "rejected", citation=1),
        "book_recommended": selector("context", "recommended"),
        "book_source": "synthetic_book",
        "rejected_key": selector("context", "rejected", field="target_field" if mismatch is True else "source_field"),
        "recommended_key": selector("context", "recommended", citation=1, field="target_field"),
        "ulif_source": "synthetic_ulif",
        "vesum_source": "synthetic_vesum",
        "sum11_source": "sum11",
        "receipt": selector("context", "receipt"),
        "pair_field": "pair",
        "sol_field": "sol",
        "opus_field": "opus",
    }
    bundle["spec"]["binding"]["rules"] = [
        pair,
        {
            "op": "equal",
            "values": [
                selector("context", "recommended", citation=1, field="target_field"),
                selector("context", "recommended", citation=2, field="target_field"),
            ],
        },
    ]
    if mismatch == "swapped":
        bundle["candidates"][0] = replace(
            c, response=(replace(c.response[0], text=row["source_field"], citations=(citation(row),)),)
        )
    if mismatch:
        with pytest.raises(
            BuildError, match="binding_adjudication" if mismatch == "adjudication" else "binding_contrast"
        ):
            run_gate(bundle)
    else:
        assert len(run_gate(bundle)[0]) == 1


def test_a_supporting_citation_cannot_authenticate_itself(bundle):
    candidate = bundle["candidates"][0]
    other = bundle["rows"][1]
    value = replace(
        candidate.response[0], citations=(candidate.response[0].citations[0], citation(other, "target_field"))
    )
    bundle["candidates"] = [
        replace(candidate, response=(value,)),
        *[
            replace(c, outcome="excluded", reason="synthetic_excluded", evidence=("synthetic_excluded",))
            for c in bundle["candidates"][1:]
        ],
    ]
    bundle["spec"]["binding"]["rules"].append(
        {
            "op": "equal",
            "values": [selector("response", "target", citation=1), selector("response", "target", citation=1)],
        }
    )
    with pytest.raises(BuildError, match="supporting_unbound"):
        run_gate(bundle)
    bundle["spec"]["binding"]["rules"][-1]["values"][0] = selector("response", "target")
    with pytest.raises(BuildError, match="binding_equal"):
        run_gate(bundle)


def test_dynamic_page_bounds_use_independent_pinned_query(bundle):
    candidate = bundle["candidates"][0]
    pages = replace(
        candidate,
        response=tuple(replace(c.response[0], slot=f"page{i}") for i, c in enumerate(bundle["candidates"][:3])),
    )
    rule = {
        "op": "contiguous_pages",
        "values": [selector("response", f"page{i}", field="id") for i in range(3)],
        "first": selector(field="id"),
        "next_heading": {
            "query": {"kind": "sql", "store": "sources.db", "sql": "SELECT min(id) FROM units WHERE id>? + 2"},
            "parameters": [selector(field="id")],
        },
        "source_field": "source_file",
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.check(pages, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {}) == {"contiguous_pages"}
        rule["next_heading"]["query"]["sql"] = "SELECT id FROM units WHERE id>=?"
        with pytest.raises(BuildError, match="binding_pages"):
            bindings.check(pages, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {})


def test_json_array_serializer_has_only_source_values_and_fixed_separators(bundle):
    from scripts.projects.open_model_data.review_build.gate import serialize

    parts = bundle["candidates"][0].response + bundle["candidates"][1].response
    assert serialize(parts, "json_array") == '["SYNTHETIC target 1","SYNTHETIC target 2"]'
    assert serialize(parts, "text") == "SYNTHETIC target 1\nSYNTHETIC target 2"
    with pytest.raises(BuildError, match="serializer"):
        serialize(parts, "SYNTHETIC arbitrary")


def test_c2_header_cells_render_only_positional_source_text(bundle):
    data = copy.deepcopy(bundle["catalog"])
    line = data["components"].pop("C1")["instructions"][0]
    line.update(
        id="C2.agreed_form.synthetic",
        operation="agreed_form",
        template="SYNTHETIC: {sentence}; {slot}",
        slots=["sentence", "slot"],
    )
    data["components"]["C2"] = {"instructions": [line]}
    catalog = Catalog(data)
    candidate = bundle["candidates"][0]
    header = replace(candidate.slots[0], slot="header_section", text="SYNTHETIC section")
    row = replace(header, slot="header_row", text="SYNTHETIC row")
    sense = replace(header, slot="sense", text="")
    candidate = replace(
        candidate, component="C2", operation="agreed_form", slots=(*candidate.slots, header, row, sense)
    )
    serializers = {
        "slot": {"id": "c2-header-cells.v2", "section": ["header_section"], "row": "header_row", "column": []}
    }
    assert catalog.applicable(candidate, empty_safe=True, serializers=serializers) == (line["id"],)
    assert catalog.render(candidate, line["id"], serializers).endswith('[["SYNTHETIC section"],"SYNTHETIC row",[]]')
    serializers["slot"]["row"] = None
    assert catalog.render(candidate, line["id"], serializers).endswith('[["SYNTHETIC section"],"",[]]')
    serializers["slot"]["section"] = []
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        catalog.applicable(candidate, empty_safe=True, serializers=serializers)
    serializers["slot"]["section"] = ["SYNTHETIC_missing"]
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        catalog.applicable(candidate, empty_safe=True, serializers=serializers)


def test_gate_c2_applicability_reads_source_assertions(bundle):
    from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
    from scripts.projects.open_model_data.review_build.gate import Gate

    data = copy.deepcopy(bundle["catalog"])
    lines = data["components"].pop("C1")["instructions"][:2]
    lines[0].update(
        id="C2.agreed_form.with",
        operation="agreed_form",
        sense_variant="with_sense",
        template="SYNTHETIC {sentence}: {sense}",
        slots=["sentence", "sense"],
    )
    lines[1].update(id="C2.agreed_form.without", operation="agreed_form", sense_variant="without_sense")
    data["components"]["C2"] = {"instructions": lines}
    spec = bundle["spec"]
    spec["applicability"] = {
        "with_sense": [[selector(field="grade"), 1]],
        "without_sense": [[selector(field="grade"), 1], [selector(field="is_sensitive"), 0]],
    }
    c = bundle["candidates"][0]
    sense = replace(c.response[0], slot="sense")
    c = replace(c, component="C2", operation="agreed_form", slots=(*c.slots, sense))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        gate = Gate(
            reader,
            Catalog(data),
            Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
            {"C2": spec},
            bundle["config"]["compatibility"],
        )
        assert gate.applicable(c) == ("C2.agreed_form.with",)
        assert gate.applicable(replace(c, slots=(c.slots[0], replace(sense, text=" ")))) == ("C2.agreed_form.without",)
        spec["applicability"]["with_sense"][0][1] = 0
        with pytest.raises(BuildError, match="catalog_inapplicable"):
            gate.applicable(c)
        spec["applicability"]["without_sense"][0][1] = 0
        with pytest.raises(BuildError, match="catalog_inapplicable"):
            gate.applicable(replace(c, slots=(c.slots[0], replace(sense, text=""))))
