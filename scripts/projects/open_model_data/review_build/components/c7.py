"""C7: derive opt-in contrasts exclusively from dual-selected book pairs."""

from dataclasses import replace

from ..bindings import normalize
from ..contract import digest
from .antonenko import (
    BOOK_ADAPTER,
    RECEIPTS,
    SOURCE,
    STORE,
    SUM11_ADAPTER,
    ULIF_ADAPTER,
    VESUM_ADAPTER,
    candidate,
    citation,
    common_spec,
    packet_files,
    quoted,
    receipt_citation,
    selector,
)

OPERATION = "modern_norm_selection"
REJECTED = selector("context", "rejected")
RECOMMENDED = selector("context", "recommended")
TARGET = selector("response", "modern_form")
RECEIPT = selector("context", "recommended", citation=3)
BINDING = {
    "schema": "binding-spec.v1",
    "rules": [
        {
            "op": "contrast_pair",
            "rejected": REJECTED,
            "recommended": RECOMMENDED,
            "response": TARGET,
            "book_rejected": REJECTED,
            "book_recommended": RECOMMENDED,
            "book_source": SOURCE,
            "rejected_key": {**RECEIPT, "field": "rejected_key"},
            "recommended_key": {**RECEIPT, "field": "recommended_key"},
            "sum11_source": "sum11",
            "ulif_source": "ulif",
            "vesum_source": "vesum",
            "receipt": RECEIPT,
            "pair_field": "pair",
            "sol_field": "sol",
            "opus_field": "opus",
        },
        {"op": "equal", "values": [RECOMMENDED, {**RECEIPT, "field": "recommended_form"}]},
        {"op": "equal", "values": [TARGET, RECOMMENDED]},
        {"op": "equal", "values": [REJECTED, {**RECEIPT, "field": "rejected_form"}]},
        {"op": "span_equal", "value": REJECTED, "receipt": {**RECEIPT, "field": "rejected_span"}},
        {"op": "span_equal", "value": RECOMMENDED, "receipt": {**RECEIPT, "field": "recommended_span"}},
        # The target quotes the book's exact span; it is not backed by SUM-11.
        {"op": "same_row", "values": [RECOMMENDED, TARGET]},
    ],
}


def witnesses(ctx, form):
    """Read complete witness rows only for an individually reviewed member."""
    key = normalize(form, "unstress_nfc")
    queries = (
        ("sources.db", "sum11", "word", key, "sum11", None),
        ("sources.db", "ulif_dictua_entries", "normalized_query", key, "ulif", "canonical_headword"),
        ("vesum.db", "forms_all", "word_form", key, "vesum", None),
    )
    result = []
    for store, table, column, value, source, field in queries:
        lookup = f'"{column}"'
        if table == "sum11":
            lookup = f"replace(\"{column}\", char(769), '')"
        ids = ctx.reader.query_values(
            {
                "kind": "sql",
                "store": store,
                "sql": f'SELECT id FROM "{table}" WHERE {lookup}=? ORDER BY id',
                "parameters": [value],
            }
        )
        # Read the actual stored field, not a synthesized unstressed witness.
        conn = ctx.reader.connections[store]
        rows = [dict(conn.execute(f'SELECT * FROM "{table}" WHERE id=?', (i,)).fetchone()) for i in ids]
        field = field or column
        rows = [r for r in rows if isinstance(r.get(field), str) and normalize(r[field], "unstress_nfc") == key]
        if table == "ulif_dictua_entries":
            rows = [r for r in rows if r.get("homonym_checked") == 1 and r.get("status") == "ok"]
        result.append(
            None
            if not rows
            else (
                rows[0],
                citation(
                    rows[0], field, source=source, store=store, table=table, locator=f"{table} id={rows[0]['id']}"
                ),
            )
        )
    return result


class ContrastComponent:
    def __init__(self):
        self.spec = common_spec(
            OPERATION,
            {
                "separator": ";",
                "primary": [{"selector": REJECTED, "store": "sources.db", "table": "style_guide", "key": "id"}],
            },
        )
        self.spec["operation_specs"][OPERATION]["binding"] = BINDING
        self.spec["context_serializer"] = "json_array"
        self.adapters = {SOURCE: BOOK_ADAPTER, "sum11": SUM11_ADAPTER, "ulif": ULIF_ADAPTER, "vesum": VESUM_ADAPTER}
        self.files = {STORE: RECEIPTS}

    def iter_candidates(self, ctx):
        RECEIPTS.configure(ctx)
        for row in ctx.reader.iter_rows("sources.db", "style_guide"):
            decision = RECEIPTS.get(row)
            if decision["reason"] != "ok":
                yield candidate("C7", OPERATION, row, (), (quoted(row, "rejected"),), (), decision["reason"])
                continue
            for left, right in decision["pairs"]:
                receipt = RECEIPTS.admit(row, left, right)
                rejected = quoted(row, "rejected", left)
                left_witness = witnesses(ctx, rejected.text)[0]
                _, ulif, vesum = witnesses(ctx, row["text"][slice(*right)])
                reason = "ok"
                context, response = (rejected,), ()
                if left_witness is None:
                    reason = "not_sum11_headword"
                elif ulif is None:
                    reason = "ulif_unattested"
                elif vesum is None:
                    reason = "vesum_unattested"
                elif (
                    left_witness[0].get("sovietization_risk") is None
                    or left_witness[0].get("sovietization_keywords") is None
                ):
                    reason = "sum11_markers_unavailable"
                else:
                    rejected = replace(rejected, citations=(*rejected.citations, left_witness[1]))
                    recommended = quoted(
                        row,
                        "recommended",
                        right,
                        (ulif[1], vesum[1], receipt_citation(receipt, "C7", "recommended_form")),
                    )
                    context = tuple(
                        sorted((rejected, recommended), key=lambda v: digest((receipt["id"] + "\0" + v.text).encode()))
                    )
                    response = (replace(recommended, slot="modern_form", citations=(recommended.citations[0],)),)
                yield candidate("C7", OPERATION, row, (), context, response, reason)

    def artifact_files(self, ctx):
        return packet_files(ctx, "C7")


COMPONENT = ContrastComponent()
