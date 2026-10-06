"""C6(b): book-row census, exact-span pairs and independently signed direction."""

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
UNIT_QUERY = {"kind": "sql", "store": "sources.db", "sql": "SELECT id FROM style_guide"}
FROZEN_COUNT = 342
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
        {"op": "literal", "values": [{**RECEIPT, "field": "sol"}], "expected": "APPROVE"},
        {"op": "literal", "values": [{**RECEIPT, "field": "opus"}], "expected": "APPROVE"},
        {"op": "literal", "values": [{**RECEIPT, "field": "calque"}], "expected": True},
    ],
}


class BookCalqueComponent:
    def __init__(self):
        self.spec = common_spec(
            OPERATION,
            UNIT_QUERY,
            FROZEN_COUNT,
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
            receipt = RECEIPTS.get(row, "C6b")
            if receipt is None:
                expression = quoted(row, "expression")
                response = ()
            else:
                expression = quoted(
                    row, "expression", receipt["rejected_span"], (receipt_citation(receipt, "C6b", "rejected_form"),)
                )
                response = (
                    quoted(
                        row,
                        "replacement",
                        receipt["recommended_span"],
                        (receipt_citation(receipt, "C6b", "recommended_form"),),
                    ),
                )
            context = (
                quoted(row, "passage"),
                Value("author", row["source"], (citation(row, "source"),), None, "verbatim"),
            )
            yield candidate("C6b", str(row["id"]), OPERATION, row, (expression,), context, response, receipt)

    def artifact_files(self, ctx):
        return packet_files(ctx, "C6b", ((row, None) for row in ctx.reader.iter_rows("sources.db", "style_guide")))


COMPONENT = BookCalqueComponent()
