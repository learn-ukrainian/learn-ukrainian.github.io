"""Closed rule tables and the label -> grammar_parsed derivation (design r3 §4, §5.3)."""

from __future__ import annotations

import json

from scripts.lexdata import records, rule_tables
from scripts.lexdata.derive import derive_leaf
from scripts.lexdata.normalize import normalize_span


def test_labels_map_through_the_closed_table_only() -> None:
    assert rule_tables.map_grammar_labels(["ж."]) == {
        "labels": ["ж."], "fields": {"gender": "feminine", "pos": "noun"}, "unmapped": [], "conflicts": []}
    unmapped = rule_tables.map_grammar_labels(["незмінюване слово", "невідома мітка", " "])
    assert unmapped["fields"] == {} and unmapped["unmapped"] == ["незмінюване слово", "невідома мітка"]
    both = rule_tables.map_grammar_labels(["ч.", "ж.", "ч."])
    assert both["labels"] == ["ч.", "ж."]
    assert both["fields"] == {"pos": "noun"} and both["conflicts"] == ["gender"]


def test_dispositions_are_closed() -> None:
    assert rule_tables.is_unit_disposition("imported")
    assert rule_tables.is_unit_disposition("refused:truncated_source")
    assert rule_tables.is_unit_disposition("out_of_scope:prose")
    assert not rule_tables.is_unit_disposition("out_of_scope:")
    assert not rule_tables.is_unit_disposition("refused:made_up")
    assert rule_tables.is_line_disposition("refused:stress_invalid")
    assert not rule_tables.is_line_disposition("entry ")


def test_table_contents_are_canonical_and_complete() -> None:
    contents = rule_tables.table_contents()
    assert set(contents["refusal_codes"]) == set(rule_tables.REFUSAL_CODES)
    assert contents["grammar_labels"]["незмінюване слово"] is None
    json.dumps(contents, sort_keys=True)


def test_derive_leaf_maps_labels_and_prefers_the_parser_refusal() -> None:
    locator = "sources:t:id=1"
    unit = records.UnitInput("fixture", locator, "page", (records.L0Row(locator, "a" * 64),))
    item = records.LexItemRecord("h", "шуба", "headword", grammar_raw="ж.", grammar_labels=("ж.",))
    fields = derive_leaf(unit, item, normalizer=normalize_span, rights_class="x", importer_version="p/1")
    assert json.loads(fields["grammar_parsed"])["fields"] == {"gender": "feminine", "pos": "noun"}
    refused = records.LexItemRecord(
        "r", "шуба", "headword", parser_refusal="truncated_source",
        proposed_repairs=(records.ProposedRepair("fixture", "rejoin", "шуба"),))
    fields = derive_leaf(unit, refused, normalizer=normalize_span, rights_class="x", importer_version="p/1")
    assert fields["refusal_code"] == "truncated_source" and fields["key_fold"] is None
    assert json.loads(fields["proposed_repairs"]) == [{"kind": "rejoin", "proposed": "шуба", "proposer": "fixture"}]
    assert fields["raw_span"] == "шуба"
