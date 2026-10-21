import copy
import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Value
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import citation, run_gate, selector


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
    assert catalog.applicable(c, variants={"with_sense"}) == ("C2.agreed_form.with",)
    c = replace(c, slots=(c.slots[0], replace(sense, text=" ")))
    with pytest.raises(BuildError):
        catalog.applicable(c)
    assert catalog.applicable(c, variants={"without_sense"}) == ("C2.agreed_form.without",)


def test_binding_engine_region_group_contiguity_and_unknown_rule(bundle):
    text = "SYNTHETIC examples: SYNTHETICexample\n1. SYNTHETIC outside"
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
    row = {**bundle["rows"][0], "source_field": text}
    original = bundle["candidates"][0]
    bundle["candidates"][0] = replace(
        original, slots=(replace(original.slots[0], text=text, citations=(citation(row),)),)
    )
    example = Value("example", "SYNTHETICexample", (citation(row),), (16, 33), "verbatim")
    candidate = replace(bundle["candidates"][0], slots=(example,))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        spec = {"schema": "binding-spec.v1", "rules": [{"op": "example_list", "values": [selector(slot="example")]}]}
        # Locate the actual source span rather than relying on the example fixture offsets.
        start = text.index("SYNTHETICexample", text.index(":"))
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


@pytest.mark.parametrize(
    "text,item,allowed",
    [
        ("SYNTHETIC examples: SYNTHETIC alpha, SYNTHETIC beta.", "SYNTHETIC alpha", False),
        (
            "SYNTHETIC examples: SYNTHETICalpha, SYNTHETICbeta. Rule SYNTHETIC prose: SYNTHETIC outside",
            "SYNTHETICbeta",
            True,
        ),
        (
            "SYNTHETIC examples: SYNTHETICalpha, SYNTHETICbeta. Rule SYNTHETIC prose: SYNTHETIC outside",
            "SYNTHETIC outside",
            False,
        ),
        ("SYNTHETIC examples: SYNTHETICalpha, SYNTHETICbeta. Rule SYNTHETIC prose", "alpha", False),
        (
            "SYNTHETIC examples: SYNTHETICalpha; SYNTHETICbeta\n2. SYNTHETIC rule: SYNTHETIC outside",
            "SYNTHETIC outside",
            False,
        ),
        (
            "SYNTHETIC examples: SYNTHETICalpha; SYNTHETICbeta. Rule SYNTHETIC examples: SYNTHETICgamma, SYNTHETICdelta.",
            "SYNTHETICdelta",
            True,
        ),
        ("SYNTHETIC examples:\n SYNTHETICalpha, SYNTHETICbeta\n3. SYNTHETIC rule", "SYNTHETICalpha", True),
    ],
)
def test_colon_regions_require_whole_items_and_exclude_later_rule_prose(bundle, text, item, allowed):
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
    start = text.index(item)
    value = Value(
        "example",
        item,
        (citation({**bundle["rows"][0], "source_field": text}),),
        (start, start + len(item)),
        "verbatim",
    )
    candidate = replace(bundle["candidates"][0], slots=(value,))
    spec = {"schema": "binding-spec.v1", "rules": [{"op": "example_list", "values": [selector(slot="example")]}]}
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        if allowed:
            assert bindings.check(candidate, spec, reader, {}) == {"example_list"}
        else:
            with pytest.raises(BuildError, match="binding_example"):
                bindings.check(candidate, spec, reader, {})
