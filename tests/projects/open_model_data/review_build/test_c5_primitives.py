"""Generic span SQL and whole-field gates, using SYNTHETIC source text only."""

import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import transform
from tests.projects.open_model_data.review_build.conftest import selector


@pytest.mark.parametrize(
    "body,expected,reasons",
    [
        ("FIRST, SECOND", ["FIRST", "SECOND"], ["ok", "ok"]),
        ("FIRST-\nPART, SECOND", ["FIRST-\nPART", "SECOND"], ["ok", "ok"]),
        ("FIRST (inner, comma), SECOND", ["FIRST (inner, comma)", "SECOND"], ["ok", "ok"]),
        ('"a phrase, with comma"', ['"a phrase, with comma"'], ["ok"]),
        ("«a phrase: with, comma»", ["«a phrase: with, comma»"], ["ok"]),
        (
            "1) a clause, which continues; 2) another clause",
            ["a clause, which continues", "another clause"],
            ["example_boundary_ambiguous", "example_boundary_ambiguous"],
        ),
        (
            "1. first, with comma\n2. second, with comma",
            ["first, with comma", "second, with comma"],
            ["example_boundary_ambiguous", "example_boundary_ambiguous"],
        ),
        (
            "a) first, with comma\nb) second, with comma",
            ["first, with comma", "second, with comma"],
            ["example_boundary_ambiguous", "example_boundary_ambiguous"],
        ),
        (
            "1) First sentence. Another sentence, still the example; 2) SECOND",
            ["First sentence. Another sentence, still the example", "SECOND"],
            ["example_boundary_ambiguous", "ok"],
        ),
        ("a clause, which continues", ["a clause, which continues"], ["example_boundary_ambiguous"]),
        ("FIRST PHRASE, SECOND PHRASE", ["FIRST PHRASE, SECOND PHRASE"], ["example_boundary_ambiguous"]),
        ("FIRST, e.g. SECOND", ["FIRST, e.g. SECOND"], ["example_boundary_ambiguous"]),
        ("J. ALPHA, BETA", ["J. ALPHA, BETA"], ["example_boundary_ambiguous"]),
        ('"first, second", "third, fourth"', ['"first, second", "third, fourth"'], ["example_boundary_ambiguous"]),
        ("FIRST (unclosed, SECOND", ["FIRST (unclosed, SECOND"], ["example_boundary_ambiguous"]),
        ("FIRST), SECOND", ["FIRST), SECOND"], ["example_boundary_ambiguous"]),
        ("FIRST, SECOND with prose tail", ["FIRST, SECOND with prose tail"], ["example_boundary_ambiguous"]),
        ("FIRST,, SECOND", ["FIRST,, SECOND"], ["example_boundary_ambiguous"]),
        (
            "FIRST, SECOND; THIRD PHRASE, FOURTH",
            ["FIRST", "SECOND", "THIRD PHRASE, FOURTH"],
            ["ok", "ok", "example_boundary_ambiguous"],
        ),
        ("FIRST'PART, SECOND", ["FIRST'PART", "SECOND"], ["ok", "ok"]),
        ("FIRST’PART, SECOND", ["FIRST’PART", "SECOND"], ["ok", "ok"]),
    ],
)
def test_printed_example_boundaries_are_verbatim(body, expected, reasons):
    text = "SYNTHETIC examples: " + body + "."
    decisions = bindings.example_boundaries(text)
    assert [text[slice(*span)] for span, _ in decisions] == expected
    assert [reason for _, reason in decisions] == reasons
    assert bindings.example_items(text) == [span for span, _ in decisions]


def test_nested_colon_cannot_introduce_a_second_list():
    text = 'SYNTHETIC examples: "first: alpha, beta"; SECOND.'
    assert len(bindings.example_regions(text)) == 1
    assert [text[slice(*span)] for span, _ in bindings.example_boundaries(text)] == ['"first: alpha, beta"', "SECOND"]


def test_empty_groups_and_rule_boundaries():
    text = "SYNTHETIC examples: FIRST, SECOND; ; THIRD. Rule continues: FOURTH, FIFTH."
    assert [text[slice(*span)] for span, _ in bindings.example_boundaries(text)] == [
        "FIRST",
        "SECOND",
        "THIRD",
        "FOURTH",
        "FIFTH",
    ]


@pytest.mark.parametrize("body", ["FIRST, Prof. SECOND, THIRD", "FIRST, abbreviation. SECOND", "FIRST: SECOND, THIRD"])
def test_dotted_or_colon_continuation_cannot_license_a_truncated_example(body):
    text = "SYNTHETIC examples: " + body + "."
    decisions = bindings.example_boundaries(text)
    assert decisions[0][1] == "example_boundary_ambiguous"
    assert not any(
        reason == "ok" and text[slice(*span)] in {"Prof", "abbreviation", "FIRST"} for span, reason in decisions
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "SYNTHETIC rule conditions: a) in sentences with direct speech; b) in another condition.",
            ["in sentences with direct speech", "in another condition"],
        ),
        (
            "SYNTHETIC combinations: 1) ?! (label), !? (label); 2) ...?.",
            ["?! (label), !? (label)", "...?"],
        ),
        ("SYNTHETIC examples: 1) FIRST, SECOND; 2) THIRD, FOURTH.", ["FIRST, SECOND", "THIRD, FOURTH"]),
    ],
)
def test_numbered_rule_conditions_and_multi_example_groups_are_withheld(text, expected):
    decisions = bindings.example_boundaries(text)
    assert [text[slice(*span)] for span, _ in decisions] == expected
    assert all(reason == "example_boundary_ambiguous" for _, reason in decisions)


@pytest.mark.parametrize(
    "body",
    [
        "FIRST, SECOND, THIRD (A. Writer)",
        "FIRST, SECOND; THIRD, FOURTH (A. Writer)",
        "FIRST, SECOND (Writer)",
        "FIRST (Capitalized label), SECOND",
    ],
)
def test_word_lists_inside_a_cited_sentence_are_not_standalone_examples(body):
    text = "SYNTHETIC example sentence: " + body + "."
    decisions = bindings.example_boundaries(text)
    assert decisions == [((text.index(body), text.index(body) + len(body)), "example_boundary_ambiguous")]


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


@pytest.mark.parametrize(
    "body",
    [
        "1) FIRST — SECOND, THIRD — FOURTH; 2) FIFTH",
        "1) FIRST — SECOND.; 2) THIRD",
        "1) A rule clause, if the words meet a condition; 2) SECOND",
    ],
)
def test_numbered_explicit_introduction_cannot_admit_groups_punctuation_or_rule_clauses(body):
    text = "SYNTHETIC наприклад: " + body + "."
    decisions = bindings.example_boundaries(text)
    assert decisions[0][1] == "example_boundary_ambiguous"
    assert decisions[1][1] == "ok"


@pytest.mark.parametrize(
    "body",
    [
        "FIRST (див. ще § 42), SECOND",
        "FIRST, SECOND (пор. § 42)",
        '"phrase (see § 42)"',
        "FIRST (reference), SECOND",
        "FIRST (див. примітку), SECOND",
    ],
)
def test_editorial_parentheses_are_counted_and_withheld_without_rewriting(body):
    text = "SYNTHETIC examples: " + body + "."
    decisions = bindings.example_boundaries(text)
    affected = [span for span, reason in decisions if reason == "example_boundary_ambiguous"]
    assert len(affected) == 1
    assert "(" in text[slice(*affected[0])]
    assert any(
        reason == "ok" and text[slice(*span)] in {"FIRST", "SECOND"} for span, reason in decisions
    ) or body.startswith('"')
    assert bindings.example_items(text) == [span for span, _ in decisions]


@pytest.mark.parametrize(
    "body",
    [
        "FIRST (і second), THIRD",
        "FIRST (category), SECOND",
        "FIRST (inner, comma), SECOND",
        '1) FIRST; 2) "complete phrase, with comma"',
    ],
)
def test_grammatical_variants_categories_and_supported_numbered_paths_remain_verbatim(body):
    text = "SYNTHETIC examples: " + body + "."
    decisions = bindings.example_boundaries(text)
    assert len(decisions) == 2 and all(reason == "ok" for _, reason in decisions)
