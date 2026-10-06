"""C6b: one accounting row, one record per dual-selected replacement pair."""

from ..contract import Value
from .antonenko import (
    BOOK_ADAPTER,
    RECEIPTS,
    SOURCE,
    STORE,
    candidate,
    citation,
    common_spec,
    packet_files,
    quoted,
    receipt_citation,
    selector,
)

OPERATION = "book_calque_replacement"
EXPRESSION = selector("slots", "expression")
TARGET = selector("response", "replacement")
PASSAGE = selector("context", "passage")
AUTHOR = selector("context", "author")
RECEIPT = selector("slots", "expression", citation=1)
BINDING = {
    "schema": "binding-spec.v1",
    "rules": [
        {"op": "same_row", "values": [EXPRESSION, TARGET, PASSAGE, AUTHOR]},
        {"op": "equal", "values": [EXPRESSION, {**RECEIPT, "field": "rejected_form"}]},
        {"op": "equal", "values": [TARGET, {**TARGET, "citation": 1, "field": "recommended_form"}]},
        {"op": "equal", "values": [{**EXPRESSION, "field": "id"}, {**RECEIPT, "field": "book_id"}]},
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
                "primary": [{"selector": EXPRESSION, "store": "sources.db", "table": "style_guide", "key": "id"}],
                "separator": ";",
            },
        )
        self.spec["operation_specs"][OPERATION]["binding"] = BINDING
        self.adapters = {SOURCE: BOOK_ADAPTER}
        self.files = {STORE: RECEIPTS}

    def iter_candidates(self, ctx):
        RECEIPTS.configure(ctx)
        for row in ctx.reader.iter_rows("sources.db", "style_guide"):
            decision = RECEIPTS.get(row)
            context = (
                quoted(row, "passage"),
                Value("author", row["source"], (citation(row, "source"),), None, "verbatim"),
            )
            if decision["reason"] != "ok":
                yield candidate("C6b", OPERATION, row, (quoted(row, "expression"),), context, (), decision["reason"])
                continue
            for left, right in decision["pairs"]:
                receipt = RECEIPTS.admit(row, left, right)
                expression = quoted(row, "expression", left, (receipt_citation(receipt, "C6b", "rejected_form"),))
                target = quoted(row, "replacement", right, (receipt_citation(receipt, "C6b", "recommended_form"),))
                yield candidate("C6b", OPERATION, row, (expression,), context, (target,))

    def artifact_files(self, ctx):
        return packet_files(ctx, "C6b")


COMPONENT = BookCalqueComponent()
