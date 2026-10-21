"""Fixture parser for lexdata tests: one unit per ``fixture_words`` row.

Registered through the test transform binding; it imports only the record
interface, so its transform closure is itself plus ``scripts/lexdata``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scripts.lexdata import records

FIXTURE_SOURCE = "fixture_words"
FIXTURE_PARSER = "fixture_parser"


class FixtureAdapter:
    """One unit per fixture_words row; ``a, b`` becomes a list parent with members."""

    source_id = FIXTURE_SOURCE
    parser_id = FIXTURE_PARSER
    stores = ("sources",)

    def __init__(self, drift_after_first_snapshot: bool = False) -> None:
        self._snapshots = 0
        self._drift = drift_after_first_snapshot

    def _rows(self, l0: Mapping[str, Any]) -> list[tuple[int, str]]:
        return l0["sources"].execute("SELECT id, word FROM fixture_words ORDER BY id").fetchall()

    def snapshot(self, l0: Mapping[str, Any]) -> records.SelectionSnapshot:
        self._snapshots += 1
        prints = [records.row_fingerprint({"id": i, "word": w}) for i, w in self._rows(l0)]
        if self._drift and self._snapshots > 1:
            prints.append("f" * 64)
        return records.SelectionSnapshot("SELECT id, word FROM fixture_words ORDER BY id", len(prints),
                                         records.selection_digest(prints))

    def iter_units(self, l0: Mapping[str, Any]):
        for row_id, word in self._rows(l0):
            locator = f"sources:fixture_words:id={row_id}"
            yield records.UnitInput(FIXTURE_SOURCE, locator, "chunk",
                                    (records.L0Row(locator, records.row_fingerprint({"id": row_id, "word": word})),),
                                    payload=word)

    def parse(self, unit: records.UnitInput) -> records.ParsedUnit:
        word = unit.payload
        if ", " in word:
            items = [records.LexItemRecord("p", word, "headword")]
            items += [records.LexItemRecord(f"m{n}", member, "variant", parent="p", member_index=n)
                      for n, member in enumerate(word.split(", "), 1)]
            return records.ParsedUnit(unit, "imported", tuple(items))
        return records.ParsedUnit(unit, "imported", (records.LexItemRecord(
            "h", word, "headword", senses=(records.SenseRecord(1, "gloss"),)),))
