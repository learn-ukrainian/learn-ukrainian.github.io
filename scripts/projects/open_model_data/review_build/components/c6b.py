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
        {"op": "literal", "values": [{**RECEIPT, "field": "sol"}], "expected": "APPROVE"},
        {"op": "literal", "values": [{**RECEIPT, "field": "opus"}], "expected": "APPROVE"},
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

    def artifact_files(self, ctx):
        return packet_files(ctx, "C6b")


COMPONENT = BookCalqueComponent()
