"""C6b: one accounting unit per selected pair, with no answer-bearing context."""

from copy import deepcopy

from .antonenko import (
    ACCEPTED_REASONS,
    BOOK_ADAPTER,
    RECEIPTS,
    SOURCE,
    STORE,
    candidate,
    common_spec,
    packet_files,
    quoted,
    receipt_citation,
    selector,
)

OPERATION = "book_calque_replacement"
COMPATIBILITY = [
    {
        "store": store,
        "table": table,
        "source_id": SOURCE,
        "role": "modern",
        "source_column": "source",
        "source_values": ["Антоненко-Давидович"],
    }
    for store, table in (("sources.db", "style_guide"), (STORE, "C6b"))
]
EXPRESSION = selector("slots", "expression")
TARGET = selector("response", "replacement")
RECEIPT = selector("slots", "expression", citation=1)
BINDING = {
    "schema": "binding-spec.v1",
    "rules": [
        {"op": "same_row", "values": [EXPRESSION, TARGET]},
        {"op": "equal", "values": [EXPRESSION, {**RECEIPT, "field": "rejected_form"}]},
        {"op": "equal", "values": [TARGET, {**TARGET, "citation": 1, "field": "recommended_form"}]},
        {"op": "equal", "values": [{**EXPRESSION, "field": "id"}, {**RECEIPT, "field": "book_id"}]},
        {
            "op": "equal",
            "values": [{**selector("slots", "accounting_unit"), "field": "id"}, {**RECEIPT, "field": "id"}],
        },
        {"op": "span_equal", "value": EXPRESSION, "receipt": {**RECEIPT, "field": "rejected_span"}},
        {"op": "span_equal", "value": TARGET, "receipt": {**RECEIPT, "field": "recommended_span"}},
        {"op": "literal", "values": [{**RECEIPT, "field": "eligible"}], "expected": True},
    ],
}


class BookCalqueComponent:
    def __init__(self):
        self.spec = common_spec(
            OPERATION,
            {
                "primary": [
                    {"selector": selector("slots", "accounting_unit"), "store": STORE, "table": "C6b", "key": "id"}
                ],
                "separator": ";",
            },
        )
        self.spec["operation_specs"][OPERATION]["binding"] = BINDING
        self.spec["compatibility"] = deepcopy(COMPATIBILITY)
        self.adapters = {SOURCE: BOOK_ADAPTER}
        self.files = {STORE: RECEIPTS}

    def iter_candidates(self, ctx):
        RECEIPTS.configure(ctx)
        for row in ctx.reader.iter_rows("sources.db", "style_guide"):
            for unit in RECEIPTS.row_units(row):
                if unit["reason"] not in ACCEPTED_REASONS:
                    yield candidate("C6b", OPERATION, row, (), (), (), unit["reason"], unit)
                    continue
                left, right = unit["rejected_span"], unit["recommended_span"]
                receipt = RECEIPTS.admit(row, left, right)
                expression = quoted(row, "expression", left, (receipt_citation(receipt, "C6b", "rejected_form"),))
                target = quoted(row, "replacement", right, (receipt_citation(receipt, "C6b", "recommended_form"),))
                yield candidate("C6b", OPERATION, row, (expression,), (), (target,), unit=unit)

    def mutation_fixtures(self, ctx, candidates, gate):
        from dataclasses import asdict

        from ..contract import canonical
        from ..errors import require
        from . import MutationFixture

        require(gate.reader is ctx.reader, "mutation_context")
        # Remove a complete source row from both the adapter and candidate
        # domains. Equal derived domains must not hide missing census coverage.
        book_id = next(iter(RECEIPTS.records.values()))["book_id"]
        removed = {key: row for key, row in RECEIPTS.records.items() if row["book_id"] == book_id}
        remaining = [c for c in candidates if c.unit_id not in removed]

        def missing_row():
            try:
                for key in removed:
                    del RECEIPTS.records[key]
                gate.run(remaining)
            finally:
                RECEIPTS.records.update(removed)

        yield MutationFixture(
            "missing_source_row", canonical([asdict(c) for c in remaining]), "census_coverage", missing_row
        )
        for reason in ("inverse_pair_in_row", "duplicate_in_row", "subsumed_span", "recommended_unattested"):
            unit = next((row for row in RECEIPTS.records.values() if row["reason"] == reason), None)
            if unit is None:
                continue

            row = next(r for r in ctx.reader.iter_rows("sources.db", "style_guide") if r["id"] == unit["book_id"])
            expression = quoted(
                row, "expression", unit["rejected_span"], (receipt_citation(unit, "C6b", "rejected_form"),)
            )
            target = quoted(
                row, "replacement", unit["recommended_span"], (receipt_citation(unit, "C6b", "recommended_form"),)
            )
            forged = candidate("C6b", OPERATION, row, (expression,), (), (target,), "agreed", unit)
            stream = [forged if c.unit_id == unit["id"] else c for c in candidates]

            def unsafe_admission(stream=stream):
                gate.run(stream)

            yield MutationFixture(reason, canonical(asdict(forged)), "binding_literal", unsafe_admission)

    def artifact_files(self, ctx):
        from ..contract import canonical

        return {**packet_files(ctx, "C6b"), "C6b/recommended-lookups.json": canonical(RECEIPTS.lookups) + b"\n"}


COMPONENT = BookCalqueComponent()
