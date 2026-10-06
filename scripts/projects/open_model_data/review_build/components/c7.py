"""C7 opt-in candidate census. Semantic rejection requires both review seats.

The frozen pre-adjudication count is a candidate denominator; it does not claim
to measure the subset of forms the book actually rejects. That subset is unknown
until adjudication. No SUM-11-only candidate is shipped as modern evidence.
"""

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
    form_unit,
    packet_files,
    quoted,
    receipt_citation,
    selector,
    token_spans,
)

OPERATION = "modern_norm_selection"
UNIT_QUERY = {"kind": "antonenko_candidate_headwords.v1", "store": STORE}
FROZEN_COUNT = 20162  # Read-only source-token × row candidate census, 2026-10-06.
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
        # The target quotes the book's exact span; it is not backed by SUM-11.
        {"op": "same_row", "values": [RECOMMENDED, TARGET]},
    ],
}


def form_rows(ctx):
    headwords = set(ctx.reader.query_values({"kind": "sql", "store": "sources.db", "sql": "SELECT word FROM sum11"}))
    for row in ctx.reader.iter_rows("sources.db", "style_guide"):
        for form, span in token_spans(row["text"]).items():
            if form in headwords:
                yield row, span


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
        ids = ctx.reader.query_values(
            {
                "kind": "sql",
                "store": store,
                "sql": f'SELECT id FROM "{table}" WHERE "{column}"=? ORDER BY id',
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
            UNIT_QUERY,
            FROZEN_COUNT,
            {
                "format": "citation.v1",
                "primary": [{"selector": REJECTED, "store": "sources.db", "table": "style_guide", "span": True}],
            },
        )
        self.spec["operation_specs"][OPERATION]["binding"] = BINDING
        self.spec["context_serializer"] = "json_array"
        self.adapters = {SOURCE: BOOK_ADAPTER, "sum11": SUM11_ADAPTER, "ulif": ULIF_ADAPTER, "vesum": VESUM_ADAPTER}
        self.files = {STORE: RECEIPTS}

    def iter_candidates(self, ctx):
        RECEIPTS.configure(ctx)
        for row, span in form_rows(ctx):
            unit = form_unit(row, span)
            receipt = RECEIPTS.get(row, "C7", span)
            rejected = quoted(row, "rejected", span)
            context, response = (rejected,), ()
            missing = None
            if receipt is not None:
                right = row["text"][slice(*receipt["recommended_span"])]
                left_witness = witnesses(ctx, rejected.text)[0]
                _, ulif, vesum = witnesses(ctx, right)
                if ulif is None:
                    missing = "ulif_unattested"
                elif vesum is None:
                    missing = "vesum_unattested"
                elif (
                    left_witness is None
                    or left_witness[0].get("sovietization_risk") is None
                    or left_witness[0].get("sovietization_keywords") is None
                ):
                    missing = "sum11_markers_unavailable"
                else:
                    rejected = replace(rejected, citations=(*rejected.citations, left_witness[1]))
                    recommended = quoted(
                        row,
                        "recommended",
                        receipt["recommended_span"],
                        (ulif[1], vesum[1], receipt_citation(receipt, "C7", "recommended_form")),
                    )
                    context = tuple(
                        sorted((rejected, recommended), key=lambda v: digest((unit + "\0" + v.text).encode()))
                    )
                    response = (replace(recommended, slot="modern_form", citations=(recommended.citations[0],)),)
            c = candidate("C7", unit, OPERATION, row, (), context, response, receipt)
            if missing is not None and c.outcome == "accepted":
                c = replace(c, outcome="withheld", reason=missing, evidence=(missing,))
            yield c

    def artifact_files(self, ctx):
        return packet_files(ctx, "C7", form_rows(ctx))


COMPONENT = ContrastComponent()
