"""Typed L1 record interface and stub sink (design r3 §10 F, item 1)."""

from __future__ import annotations

import pytest

from scripts.lexdata import records as r
from scripts.lexdata.canonical import sha256_canonical

FP = "a" * 64


def unit(locator: str = "sources:t:id=1", rows: tuple[r.L0Row, ...] | None = None) -> r.UnitInput:
    return r.UnitInput("fixture", locator, "chunk", rows or (r.L0Row(locator, FP),))


def test_unit_input_fingerprint_covers_join_closure_order_free() -> None:
    a, b = r.L0Row("sources:t:id=1", FP), r.L0Row("sources:s:id=9", "b" * 64)
    one = r.UnitInput("fixture", "sources:t:id=1", "section", (a, b))
    two = r.UnitInput("fixture", "sources:t:id=1", "section", (b, a))
    assert one.unit_input_fingerprint == two.unit_input_fingerprint
    changed = r.UnitInput("fixture", "sources:t:id=1", "section", (a, r.L0Row("sources:s:id=9", "c" * 64)))
    assert changed.unit_input_fingerprint != one.unit_input_fingerprint
    assert one.unit_input_fingerprint == sha256_canonical(sorted([[a.locator, a.fingerprint], [b.locator, b.fingerprint]]))


def test_row_fingerprint_is_canonical() -> None:
    assert r.row_fingerprint({"b": 1, "a": "х"}) == r.row_fingerprint({"a": "х", "b": 1})
    assert r.bytes_fingerprint(b"x") == "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"


@pytest.mark.parametrize("kwargs,message", [
    ({"role": "lemma"}, "unknown role"),
    ({"parent": "p"}, "set together"),
    ({"parser_refusal": "made_up"}, "unknown refusal code"),
    ({"span_start": 3, "span_end": 1}, "ordered pair"),
    ({"local_id": " "}, "local_id"),
])
def test_lex_item_rejects_contract_violations(kwargs, message) -> None:
    base = {"local_id": "i1", "raw_span": "шуба", "role": "headword"}
    with pytest.raises(r.RecordError, match=message):
        r.LexItemRecord(**{**base, **kwargs})


def test_parsed_unit_orders_parents_and_rejects_bad_structure() -> None:
    child = r.LexItemRecord("c1", "в", "variant", parent="p", member_index=1)
    parent = r.LexItemRecord("p", "у, в", "headword")
    parsed = r.ParsedUnit(unit(), "imported", (child, parent))
    assert [item.local_id for item in parsed.ordered_items()] == ["p", "c1"]
    with pytest.raises(r.RecordError, match="unknown parent"):
        r.ParsedUnit(unit(), "imported", (child,))
    twin = r.LexItemRecord("c2", "у", "variant", parent="p", member_index=1)
    with pytest.raises(r.RecordError, match="duplicate member_index"):
        r.ParsedUnit(unit(), "imported", (parent, child, twin))
    with pytest.raises(r.RecordError, match="no items"):
        r.ParsedUnit(unit(), "refused:truncated_source", (parent,))
    with pytest.raises(r.RecordError, match="unknown unit disposition"):
        r.ParsedUnit(unit(), "refused:made_up")
    with pytest.raises(r.RecordError, match="no LineRecord"):
        r.ParsedUnit(unit(), "imported", (r.LexItemRecord("x", "шуба", "headword", line_no=4),),
                     (r.LineRecord(1, "шуба", "entry"),))


def test_line_dispositions_are_closed() -> None:
    assert r.LineRecord(1, "Урок 1", "lesson_heading").disposition == "lesson_heading"
    assert r.LineRecord(2, "x", "refused:homoglyph_mixed_script")
    with pytest.raises(r.RecordError):
        r.LineRecord(3, "x", "prose")
    assert "raw_line" not in repr(r.LineRecord(1, "private prose", "prose_excluded"))


class _Adapter:
    source_id = "fixture"
    parser_id = "fixture_parser"
    stores = ()

    def snapshot(self, l0):
        return r.SelectionSnapshot("SELECT 1", 2, r.selection_digest([FP, FP]))

    def iter_units(self, l0):
        yield unit("u1")
        yield unit("u2")

    def parse(self, item):
        return r.ParsedUnit(item, "imported", (r.LexItemRecord("h", "шуба", "headword"),))


def test_stub_sink_collects_and_refuses_duplicates() -> None:
    adapter = _Adapter()
    assert isinstance(adapter, r.SourceAdapter)
    sink = r.CollectingSink()
    assert r.drain(adapter, {}, sink) == 2
    assert sink.counts() == {"units": 2, "items": 2, "lines": 0}
    with pytest.raises(r.RecordError, match="duplicate unit"):
        sink.emit(sink.units[0])
