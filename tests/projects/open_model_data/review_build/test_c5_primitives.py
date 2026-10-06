"""Generic span SQL and whole-field gates, using SYNTHETIC source text only."""

import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import transform
from tests.projects.open_model_data.review_build.conftest import selector


def test_sql_span_query_is_independent_of_candidate_stream(bundle):
    text = "SYNTHETIC examples: FIRST, SECOND. Rule ends here."
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert reader.query_values(
            {
                "kind": "sql",
                "store": "sources.db",
                "sql": "SELECT json_extract(value,'$[0]') FROM units, "
                "json_each(omd_example_spans(source_field)) WHERE units.id=1",
            }
        ) == [text.index("FIRST"), text.index("SECOND")]
        with pytest.raises(sqlite3.OperationalError):
            reader.query_values({"kind": "sql", "store": "sources.db", "sql": "SELECT omd_example_spans(NULL)"})


def test_whole_field_refuses_exactly_quoted_fragment(bundle):
    candidate = bundle["candidates"][0]
    spec = {
        "schema": "binding-spec.v1",
        "rules": [
            {"op": "whole_field", "values": [selector("response", "target")]},
        ],
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.check(candidate, spec, reader, {}) == {"whole_field"}
        target = candidate.response[0]
        for value in (replace(target, text=target.text[:4], span=(0, 4)), replace(target, text="SYNTHETIC wrong")):
            with pytest.raises(BuildError, match="binding_whole_field"):
                bindings.check(replace(candidate, response=(value,)), spec, reader, {})
        for refs in ([], [selector("response", "target", field="target_field")]):
            with pytest.raises(BuildError, match="binding_whole_field"):
                bindings.check(candidate, {**spec, "rules": [{"op": "whole_field", "values": refs}]}, reader, {})


def test_dehyphenation_never_attests_only_a_marked_or_apostrophe_suffix():
    class Words:
        def is_word(self, word, policy):
            return word in {"THINGmore", "partmore", "SYNTHETICmore"}

    reader = Words()
    for raw in ("SYŃTHING-\nmore", "SYN'part-\nmore", "7SYNTHETIC-\nmore", "SYNTHETIC-\nmore7"):
        assert transform("dehyphenate@1", raw, {}, reader).text == raw
    joined = transform("dehyphenate@1", "SYNTHETIC-\nmore", {}, reader)
    assert joined.text == "SYNTHETICmore"
    assert joined.joins == ((0, 15, "SYNTHETICmore"),)


def test_pattern_absence_is_a_binding_gate(bundle):
    candidate = bundle["candidates"][0]
    spec = {
        "schema": "binding-spec.v1",
        "rules": [
            {"op": "pattern_absent", "values": [selector()], "pattern": "FORBIDDEN"},
        ],
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.check(candidate, spec, reader, {}) == {"pattern_absent"}
        bad = replace(candidate.slots[0], text="SYNTHETIC FORBIDDEN")
        with pytest.raises(BuildError, match="binding_pattern"):
            bindings.check(replace(candidate, slots=(bad,)), spec, reader, {})
        for rule in (
            {"op": "pattern_absent", "values": [], "pattern": "FORBIDDEN"},
            {"op": "pattern_absent", "values": [selector()], "pattern": ""},
        ):
            with pytest.raises(BuildError, match="binding_pattern"):
                bindings.check(candidate, {**spec, "rules": [rule]}, reader, {})


def test_binding_authenticates_citation_column_and_locator(bundle):
    candidate = bundle["candidates"][0]
    rule = {"op": "whole_field", "values": [selector()], "citation_field": "source_field"}
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {}) == {"whole_field"}
        for extra, error in (
            ({"citation_field": "target_field"}, "binding_field"),
            ({"locator_field": "source_field"}, "binding_locator"),
            ({"locator_field": "missing"}, "binding_locator"),
        ):
            with pytest.raises(BuildError, match=error):
                bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [{**rule, **extra}]}, reader, {})
