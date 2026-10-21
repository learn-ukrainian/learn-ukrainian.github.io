"""Typed L1 record interface that lexdata parsers emit (design r3 §4, §6, §10 F).

A parser is a read-only generator. For each source unit it yields a
``UnitInput`` (the unit's own L0 locator plus every L0 row it reads, its join
closure) and, when asked, a ``ParsedUnit`` of typed records. It never writes a
database and never derives keys: ``build_store`` derives every key,
``case_signal``, ``grammar_parsed``, ``norm_flags``, ``refusal_code``,
``rights_class`` and ``row_sha256`` from these records with the one
normalizer, so a transform change can re-derive them without re-reading L0.

Parser contract:
- ``iter_units`` reads only through the read-only handles it is given and lists
  in ``UnitInput.l0_rows`` every L0 row that ``parse`` will read for that unit.
- ``parse`` is deterministic and depends only on the ``UnitInput``.
- ``LexItemRecord.local_id`` is stable for the same L0 input: it anchors
  ``item_key``, which adjudications bind to across generations.
- ``raw_span`` is the verbatim dictionary span, never prose.
- Repairs are proposals only (``proposed_repairs``); ``raw_span`` stays original.

``CollectingSink`` is the stub sink importer slices target until a source
adapter is registered in ``scripts/lexdata/transforms.py``.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from scripts.lexdata import rule_tables
from scripts.lexdata.canonical import is_sha256_hex, sha256_bytes, sha256_canonical

RECORDS_INTERFACE_VERSION = "1"


class RecordError(ValueError):
    """A parser emitted a record that violates the interface contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordError(message)


def _text(value: object, name: str, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    _require(isinstance(value, str), f"{name} must be a string")


def _optional_int(value: object, name: str) -> None:
    _require(value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0),
             f"{name} must be a non-negative int or None")


def row_fingerprint(row: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON of a full L0 row (``textbooks``, sections)."""
    return sha256_canonical(dict(row))


def bytes_fingerprint(data: bytes) -> str:
    """SHA-256 of file bytes or a stored raw payload (the cache)."""
    return sha256_bytes(data)


@dataclass(frozen=True)
class L0Row:
    """One L0 row in a unit's join closure, e.g. ``sources:textbooks:chunk_id=…``."""

    locator: str
    fingerprint: str

    def __post_init__(self) -> None:
        _require(isinstance(self.locator, str) and bool(self.locator.strip()), "L0Row.locator must be non-empty")
        _require(is_sha256_hex(self.fingerprint), "L0Row.fingerprint must be 64 lowercase hex")


@dataclass(frozen=True)
class UnitInput:
    """A source unit and the L0 rows its parse reads (§6.1 ``unit_input_fingerprint``)."""

    source_id: str
    l0_locator: str
    unit_kind: str
    l0_rows: tuple[L0Row, ...]
    parent_locator: str | None = None
    payload: Any = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        _require(isinstance(self.source_id, str) and bool(self.source_id.strip()), "source_id must be non-empty")
        _require(isinstance(self.l0_locator, str) and bool(self.l0_locator.strip()), "l0_locator must be non-empty")
        _require(self.unit_kind in rule_tables.UNIT_KINDS, f"unknown unit_kind {self.unit_kind!r}")
        _require(isinstance(self.l0_rows, tuple) and bool(self.l0_rows), "l0_rows must be a non-empty tuple")
        _require(all(isinstance(row, L0Row) for row in self.l0_rows), "l0_rows must hold L0Row values")
        _require(len({row.locator for row in self.l0_rows}) == len(self.l0_rows), "duplicate L0 locator")
        _text(self.parent_locator, "parent_locator", allow_none=True)

    @property
    def unit_input_fingerprint(self) -> str:
        """SHA-256 over the sorted (locator, fingerprint) pairs of the join closure."""
        return sha256_canonical(sorted([row.locator, row.fingerprint] for row in self.l0_rows))


@dataclass(frozen=True)
class LineRecord:
    """One line of a line-grain unit. Only its SHA-256 and disposition are stored."""

    line_no: int
    raw_line: str = field(repr=False)
    disposition: str

    def __post_init__(self) -> None:
        _require(isinstance(self.line_no, int) and self.line_no >= 0, "line_no must be a non-negative int")
        _text(self.raw_line, "raw_line")
        _require(rule_tables.is_line_disposition(self.disposition),
                 f"unknown line disposition {self.disposition!r}")


@dataclass(frozen=True)
class ProposedRepair:
    """A repair proposal for review; never applied to ``raw_span`` or keys."""

    proposer: str
    kind: str
    proposed: str

    def __post_init__(self) -> None:
        for name in ("proposer", "kind", "proposed"):
            value = getattr(self, name)
            _require(isinstance(value, str) and bool(value.strip()), f"ProposedRepair.{name} must be non-empty")

    def as_json(self) -> dict[str, str]:
        return {"kind": self.kind, "proposed": self.proposed, "proposer": self.proposer}


@dataclass(frozen=True)
class SenseRecord:
    sense_no: int
    gloss_raw: str
    applies_to: str = "self"

    def __post_init__(self) -> None:
        _require(isinstance(self.sense_no, int) and self.sense_no >= 1, "sense_no must be >= 1")
        _text(self.gloss_raw, "gloss_raw")
        _require(self.applies_to in rule_tables.SENSE_APPLIES_TO, f"unknown applies_to {self.applies_to!r}")


@dataclass(frozen=True)
class ExampleRecord:
    ex_no: int
    uk_raw: str | None
    en_raw: str | None = None

    def __post_init__(self) -> None:
        _require(isinstance(self.ex_no, int) and self.ex_no >= 1, "ex_no must be >= 1")
        _text(self.uk_raw, "uk_raw", allow_none=True)
        _text(self.en_raw, "en_raw", allow_none=True)
        _require(self.uk_raw is not None or self.en_raw is not None, "an example needs uk_raw or en_raw")


@dataclass(frozen=True)
class VerbFormRecord:
    aspect: str | None
    tense: str | None
    person_number: str | None
    form_raw: str

    def __post_init__(self) -> None:
        for name in ("aspect", "tense", "person_number"):
            _text(getattr(self, name), name, allow_none=True)
        _text(self.form_raw, "form_raw")


@dataclass(frozen=True)
class GovernmentRecord:
    pattern_raw: str

    def __post_init__(self) -> None:
        _text(self.pattern_raw, "pattern_raw")


@dataclass(frozen=True)
class LexItemRecord:
    """One L1 leaf (§4). Exactly one L2 link is made per leaf.

    ``parent`` names another item's ``local_id`` in the same unit (a list
    parent); ``member_index`` is required with it. ``grammar_labels`` are the
    label tokens the parser split from ``grammar_raw``; F maps them through
    ``rule_tables.GRAMMAR_LABELS``. ``parser_refusal`` must be a catalog code.
    """

    local_id: str
    raw_span: str
    role: str
    line_no: int | None = None
    span_start: int | None = None
    span_end: int | None = None
    parent: str | None = None
    member_index: int | None = None
    grammar_raw: str | None = None
    grammar_labels: tuple[str, ...] = ()
    homonym_marker: str | None = None
    proposed_repairs: tuple[ProposedRepair, ...] = ()
    parser_refusal: str | None = None
    senses: tuple[SenseRecord, ...] = ()
    examples: tuple[ExampleRecord, ...] = ()
    verb_forms: tuple[VerbFormRecord, ...] = ()
    governments: tuple[GovernmentRecord, ...] = ()

    def __post_init__(self) -> None:
        _require(isinstance(self.local_id, str) and bool(self.local_id.strip()), "local_id must be non-empty")
        _text(self.raw_span, "raw_span")
        _require(self.role in rule_tables.ROLES, f"unknown role {self.role!r}")
        for name in ("line_no", "span_start", "span_end", "member_index"):
            _optional_int(getattr(self, name), name)
        if self.span_start is not None or self.span_end is not None:
            _require(self.span_start is not None and self.span_end is not None
                     and self.span_start <= self.span_end, "span_start/span_end must be an ordered pair")
        _require((self.parent is None) == (self.member_index is None),
                 "parent and member_index are set together")
        _require(self.parent != self.local_id, "an item cannot be its own parent")
        _text(self.grammar_raw, "grammar_raw", allow_none=True)
        _require(isinstance(self.grammar_labels, tuple) and all(isinstance(x, str) for x in self.grammar_labels),
                 "grammar_labels must be a tuple of strings")
        _text(self.homonym_marker, "homonym_marker", allow_none=True)
        _require(self.parser_refusal is None or rule_tables.is_refusal_code(self.parser_refusal),
                 f"unknown refusal code {self.parser_refusal!r}")
        for name, kind in (("proposed_repairs", ProposedRepair), ("senses", SenseRecord),
                           ("examples", ExampleRecord), ("verb_forms", VerbFormRecord),
                           ("governments", GovernmentRecord)):
            value = getattr(self, name)
            _require(isinstance(value, tuple) and all(isinstance(x, kind) for x in value),
                     f"{name} must be a tuple of {kind.__name__}")
        _require(len({s.sense_no for s in self.senses}) == len(self.senses), "duplicate sense_no")
        _require(len({e.ex_no for e in self.examples}) == len(self.examples), "duplicate ex_no")


@dataclass(frozen=True)
class ParsedUnit:
    """Everything a parser emits for one unit."""

    unit: UnitInput
    disposition: str
    items: tuple[LexItemRecord, ...] = ()
    lines: tuple[LineRecord, ...] = ()

    def __post_init__(self) -> None:
        _require(isinstance(self.unit, UnitInput), "unit must be a UnitInput")
        _require(rule_tables.is_unit_disposition(self.disposition),
                 f"unknown unit disposition {self.disposition!r}")
        _require(isinstance(self.items, tuple) and all(isinstance(i, LexItemRecord) for i in self.items),
                 "items must be a tuple of LexItemRecord")
        _require(isinstance(self.lines, tuple) and all(isinstance(r, LineRecord) for r in self.lines),
                 "lines must be a tuple of LineRecord")
        line_numbers = [line.line_no for line in self.lines]
        _require(len(set(line_numbers)) == len(line_numbers), "duplicate line_no")
        ids = [item.local_id for item in self.items]
        _require(len(set(ids)) == len(ids), "duplicate local_id")
        by_id = {item.local_id: item for item in self.items}
        for item in self.items:
            if item.parent is not None:
                _require(item.parent in by_id, f"unknown parent {item.parent!r}")
            if self.lines and item.line_no is not None:
                _require(item.line_no in set(line_numbers), f"item line {item.line_no} has no LineRecord")
        for item in self.items:  # parent chains are finite
            seen: set[str] = set()
            cursor: LexItemRecord | None = item
            while cursor is not None and cursor.parent is not None:
                _require(cursor.local_id not in seen, "parent cycle")
                seen.add(cursor.local_id)
                cursor = by_id[cursor.parent]
        members: dict[str, set[int]] = {}
        for item in self.items:
            if item.parent is not None and item.member_index is not None:
                bucket = members.setdefault(item.parent, set())
                _require(item.member_index not in bucket, "duplicate member_index under one parent")
                bucket.add(item.member_index)
        if self.disposition != "imported":
            _require(not self.items, "a refused or out-of-scope unit emits no items")

    def ordered_items(self) -> list[LexItemRecord]:
        """Items with every parent before its children (stable otherwise)."""
        by_id = {item.local_id: item for item in self.items}
        placed: set[str] = set()
        out: list[LexItemRecord] = []

        def place(item: LexItemRecord) -> None:
            if item.local_id in placed:
                return
            if item.parent is not None:
                place(by_id[item.parent])
            placed.add(item.local_id)
            out.append(item)

        for item in self.items:
            place(item)
        return out


@dataclass(frozen=True)
class SelectionSnapshot:
    """§6.6 input snapshot for one source: query, row count, aggregate digest."""

    query: str
    row_count: int
    digest: str

    def __post_init__(self) -> None:
        _text(self.query, "query")
        _require(isinstance(self.row_count, int) and self.row_count >= 0, "row_count must be >= 0")
        _require(is_sha256_hex(self.digest), "digest must be 64 lowercase hex")

    def as_json(self) -> dict[str, object]:
        return {"digest": self.digest, "query": self.query, "row_count": self.row_count}


def selection_digest(fingerprints: Iterable[str]) -> str:
    """Aggregate digest of the selected row fingerprints (order-independent)."""
    return sha256_canonical(sorted(fingerprints))


@runtime_checkable
class SourceAdapter(Protocol):
    """A read-only parser for one source, registered in ``transforms.SOURCES``.

    ``l0`` maps a logical store id (``"sources"``, ``"vesum"``) to a read-only
    handle opened through ``scripts.lib.readonly_sqlite.open_readonly``.
    """

    source_id: str
    parser_id: str
    stores: tuple[str, ...]

    def snapshot(self, l0: Mapping[str, Any]) -> SelectionSnapshot: ...

    def iter_units(self, l0: Mapping[str, Any]) -> Iterable[UnitInput]: ...

    def parse(self, unit: UnitInput) -> ParsedUnit: ...


class RecordSink(Protocol):
    def emit(self, parsed: ParsedUnit) -> None: ...


class CollectingSink:
    """Stub sink: validates and keeps parsed units in memory; writes nothing."""

    def __init__(self) -> None:
        self.units: list[ParsedUnit] = []

    def emit(self, parsed: ParsedUnit) -> None:
        _require(isinstance(parsed, ParsedUnit), "emit expects a ParsedUnit")
        keys = {(unit.unit.source_id, unit.unit.l0_locator) for unit in self.units}
        _require((parsed.unit.source_id, parsed.unit.l0_locator) not in keys, "duplicate unit locator")
        self.units.append(parsed)

    def __iter__(self) -> Iterator[ParsedUnit]:
        return iter(self.units)

    def counts(self) -> dict[str, int]:
        return {
            "units": len(self.units),
            "items": sum(len(unit.items) for unit in self.units),
            "lines": sum(len(unit.lines) for unit in self.units),
        }


def drain(adapter: SourceAdapter, l0: Mapping[str, Any], sink: RecordSink) -> int:
    """Run an adapter into a sink (dry runs and importer tests). Returns units emitted."""
    count = 0
    for unit in adapter.iter_units(l0):
        _require(unit.source_id == adapter.source_id, "unit source_id differs from its adapter")
        parsed = adapter.parse(unit)
        _require(parsed.unit == unit, "parse returned a different unit")
        sink.emit(parsed)
        count += 1
    return count
