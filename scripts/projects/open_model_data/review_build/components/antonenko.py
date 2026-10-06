"""Host-only row batches and dual offset selections; no semantic parser or census."""

import json
import re
from pathlib import Path

from ..attribution import Attribution
from ..bindings import normalize
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import require
from ..output import OutputGuard

SOURCE = "antonenko_style_guide"
STORE = "antonenko-adjudication"
MODELS = {"sol": "gpt-6.1-sol", "opus": "claude-opus-5-5"}
BATCH_SIZE = 20


def selector(area, slot, **kwargs):
    return {"area": area, "slot": slot, **kwargs}


def book_locator(row):
    """Page zero is not a printed page. Never invent a missing section."""
    if type(row.get("page")) is int and row["page"] > 0:
        return f"page {row['page']}"
    return str(row.get("section") or "").strip()


def citation(row, field="text", *, source=SOURCE, store="sources.db", table="style_guide", locator=None):
    return Citation(
        source,
        store,
        table,
        f"id={row['id']}",
        field,
        locator if locator is not None else book_locator(row),
        digest(row[field].encode()),
    )


def quoted(row, slot, span=None, witnesses=()):
    text = row["text"] if span is None else row["text"][slice(*span)]
    return Value(slot, text, (citation(row), *witnesses), span, "verbatim")


def batches(rows, batch_size=BATCH_SIZE):
    """Copy complete located rows in deterministic ~20-row, content-addressed batches."""
    require(type(batch_size) is int and batch_size > 0, "adjudication_batch_size")
    located = sorted((r for r in rows if book_locator(r)), key=lambda r: r["id"])
    require(len({r["id"] for r in located}) == len(located), "adjudication_rows")
    result = []
    for i in range(0, len(located), batch_size):
        body = {
            "schema": "antonenko-span-batch.v1",
            "seats": MODELS,
            "offsets": "Unicode character indices; start inclusive, end exclusive",
            "selection": "Select only forms this row names as wrong and their named replacements; otherwise pairs=[].",
            "rows": [
                {
                    "row_id": r["id"],
                    "locator": book_locator(r),
                    "text": r["text"],
                    "row_text_sha256": digest(r["text"].encode()),
                }
                for r in located[i : i + batch_size]
            ],
        }
        result.append({**body, "batch_sha256": digest(canonical(body))})
    return result


def write_packets(rows, root, batch_size=BATCH_SIZE):
    """CLI-independent writer. The common guard refuses public/repository output."""
    packets = batches(rows, batch_size)
    with OutputGuard(Path(root)) as guard:
        for p in packets:
            guard.write(f"{p['batch_sha256']}.json", canonical(p) + b"\n")
    return {"batches": len(packets), "rows": sum(len(p["rows"]) for p in packets)}


def _pairs(pairs, text):
    require(isinstance(pairs, list), "adjudication_pairs")
    result = []
    for pair in pairs:
        require(isinstance(pair, dict) and set(pair) == {"rejected", "recommended"}, "adjudication_direction")
        spans = []
        for role in ("rejected", "recommended"):
            span = pair[role]
            require(isinstance(span, dict) and set(span) == {"start", "end"}, "adjudication_span")
            start, end = span["start"], span["end"]
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), "adjudication_span")
            spans.append((start, end))
        left, right = spans
        require(left[1] <= right[0] or right[1] <= left[0], "adjudication_span")
        require(text[slice(*left)] != text[slice(*right)], "adjudication_span")
        result.append((left, right))
    require(len(set(result)) == len(result), "adjudication_pairs")
    return sorted(result)


def validate_receipts(batch, receipts):
    """Validate both seat artifacts, then reconcile each row without writing text.

    Valid selection differences withhold the whole row; malformed/single-seat
    submissions refuse. Model/task identifiers are driver-controlled provenance,
    not cryptographic proof of execution.
    """
    require(batch.get("schema") == "antonenko-span-batch.v1", "adjudication_batch")
    body = {k: v for k, v in batch.items() if k != "batch_sha256"}
    require(digest(canonical(body)) == batch.get("batch_sha256") and batch.get("seats") == MODELS, "adjudication_stale")
    require(isinstance(batch.get("rows"), list) and bool(batch["rows"]), "adjudication_rows")
    for row in batch["rows"]:
        require(
            isinstance(row, dict) and set(row) == {"row_id", "locator", "text", "row_text_sha256"}, "adjudication_rows"
        )
        require(
            type(row["row_id"]) is int
            and isinstance(row["text"], str)
            and isinstance(row["locator"], str)
            and bool(row["locator"].strip()),
            "adjudication_rows",
        )
        require(row["row_text_sha256"] == digest(row["text"].encode()), "adjudication_stale")
    rows = {r["row_id"]: r for r in batch["rows"]}
    require(len(rows) == len(batch["rows"]), "adjudication_rows")
    require(isinstance(receipts, dict) and set(receipts) == set(MODELS), "adjudication_seats")
    selections, tasks = {}, []
    for seat, model in MODELS.items():
        receipt = receipts[seat]
        require(
            isinstance(receipt, dict) and set(receipt) == {"schema", "model", "task_id", "batch_sha256", "rows"},
            "adjudication_receipt",
        )
        require(
            receipt["schema"] == "antonenko-span-receipt.v1" and receipt["model"] == model, "adjudication_provenance"
        )
        require(isinstance(receipt["task_id"], str) and bool(receipt["task_id"].strip()), "adjudication_provenance")
        require(receipt["batch_sha256"] == batch["batch_sha256"], "adjudication_stale")
        require(isinstance(receipt["rows"], list), "adjudication_rows")
        selected = {}
        for item in receipt["rows"]:
            require(isinstance(item, dict) and set(item) == {"row_id", "row_text_sha256", "pairs"}, "adjudication_rows")
            key = item["row_id"]
            require(type(key) is int and key in rows and key not in selected, "adjudication_rows")
            row = rows[key]
            require(
                item["row_text_sha256"] == row["row_text_sha256"] == digest(row["text"].encode()), "adjudication_stale"
            )
            selected[key] = _pairs(item["pairs"], row["text"])
        require(set(selected) == set(rows), "adjudication_rows")
        selections[seat] = selected
        tasks.append(receipt["task_id"])
    require(len(set(tasks)) == 2, "adjudication_provenance")
    return {
        key: {
            "pairs": selections["sol"][key] if selections["sol"][key] == selections["opus"][key] else [],
            "reason": "adjudication_disagreement"
            if selections["sol"][key] != selections["opus"][key]
            else ("ok" if selections["sol"][key] else "no_pair_named"),
        }
        for key in rows
    }


class ReceiptStore:
    """Pin raw seat bytes, revalidate both selections against cited rows on every read."""

    def __init__(self):
        self.reader = None
        self.root = None
        self.inputs = {}
        self.decisions = {}
        self.documents = {}
        self.records = {}

    def configure(self, ctx):
        if self.reader is ctx.reader:
            return
        self.reader, self.root = ctx.reader, ctx.request.get("antonenko_receipts")
        self.inputs, self.decisions, self.documents, self.records = {}, {}, {}, {}
        for batch in batches(ctx.reader.iter_rows("sources.db", "style_guide")):
            sha = batch["batch_sha256"]
            raw = {}
            if self.root is not None:
                with OutputGuard(Path(self.root)) as guard:
                    for seat in MODELS:
                        name = f"{sha}.{seat}.json"
                        if (guard.path / name).exists():
                            raw[seat] = guard.read(name)
                            self.inputs[name] = digest(raw[seat])
            if not raw:
                for row in batch["rows"]:
                    self.decisions[row["row_id"]] = {"reason": "adjudication_pending", "pairs": []}
                continue
            receipts = {seat: json.loads(content) for seat, content in raw.items()}
            self.decisions.update(validate_receipts(batch, receipts))
            self.documents[sha] = (batch, raw)

    def get(self, row):
        return self.decisions.get(row["id"], {"reason": "locator_unavailable", "pairs": []})

    def admit(self, row, left, right):
        key = digest(canonical([row["id"], left, right]))
        batch, raw = next(
            (b, raw) for b, raw in self.documents.values() if any(r["row_id"] == row["id"] for r in b["rows"])
        )
        receipt = {
            "id": key,
            "pair": f"id={row['id']}",
            "book_id": row["id"],
            "source": row["source"],
            "rejected_form": row["text"][slice(*left)],
            "recommended_form": row["text"][slice(*right)],
            "rejected_key": normalize(row["text"][slice(*left)], "unstress_nfc"),
            "recommended_key": normalize(row["text"][slice(*right)], "unstress_nfc"),
            "rejected_span": left,
            "recommended_span": right,
            "sol": "APPROVE",
            "opus": "APPROVE",
            "batch_sha256": batch["batch_sha256"],
            "row_text_sha256": digest(row["text"].encode()),
            **{f"{seat}_sha256": digest(content) for seat, content in raw.items()},
        }
        self.records[key] = receipt
        return receipt

    def row(self, table, row_key):
        require(table in {"C6b", "C7"} and row_key.startswith("id="), "row_unavailable")
        result = self.records.get(row_key[3:])
        require(result is not None, "row_unavailable")
        batch, raw = self.documents[result["batch_sha256"]]
        require(all(digest(content) == result[f"{seat}_sha256"] for seat, content in raw.items()), "adjudication_stale")
        # Reconstruct packet rows from this transaction, independently of derived values.
        live = {r["id"]: r for r in self.reader.iter_rows("sources.db", "style_guide")}
        require(
            all(
                r["text"] == live[r["row_id"]]["text"] and r["locator"] == book_locator(live[r["row_id"]])
                for r in batch["rows"]
            ),
            "adjudication_stale",
        )
        decisions = validate_receipts(batch, {s: json.loads(b) for s, b in raw.items()})
        row = live[result["book_id"]]
        require(result["row_text_sha256"] == digest(row["text"].encode()), "adjudication_stale")
        require(result["pair"] == f"id={row['id']}" and result["source"] == row["source"], "adjudication_stale")
        require(result["sol"] == result["opus"] == "APPROVE", "adjudication_provenance")
        require(
            (result["rejected_span"], result["recommended_span"]) in decisions[result["book_id"]]["pairs"],
            "adjudication_direction",
        )
        return result

    def units(self, query):
        require(False, "unit_query")

    def all_rows(self, table):
        return [self.row(table, f"id={key}") for key in self.records]

    def file_hashes(self):
        return dict(self.inputs)


RECEIPTS = ReceiptStore()


def receipt_citation(receipt, component, field):
    return citation(receipt, field, store=STORE, table=component, locator=f"adjudication {receipt['pair']}")


class HeldBibliographyAdapter:
    """Resolve only complete held bibliographic fields, never guessed editions."""

    def resolve(self, form, cited, row, reader):
        require(
            isinstance(form, str) and not re.search(r"<[^>]*>|\b(?:cite|insert|supply|fill)\b", form, re.I),
            "attribution_unresolved",
        )
        held = row.get("bibliography")
        require(isinstance(held, str) and held == form and bool(held.strip()), "attribution_unresolved")
        require(bool(row.get("bibliography_evidence")), "attribution_unresolved")
        return Attribution(held, form)


BOOK_ADAPTER = HeldBibliographyAdapter()
SUM11_ADAPTER = HeldBibliographyAdapter()
ULIF_ADAPTER = HeldBibliographyAdapter()
VESUM_ADAPTER = HeldBibliographyAdapter()


def common_spec(operation, unit):
    return {
        "operations": [operation],
        "operation_specs": {
            operation: {
                "unit_query": {"kind": "sql", "store": "sources.db", "sql": "SELECT id FROM style_guide"},
                "frozen_count": 342,
                "unit_id": unit,
            }
        },
        "unit_grain": "style_guide row; C7 records derive only from jointly selected pairs",
        "annotation_layer": "source_text_and_dual_adjudication",
        "reference_multiplicity": "one record per agreed offset pair in a row",
        "unit_multiplicity": "records",
        "reasons": {
            "accepted": ["ok"],
            "rejected": [],
            "withheld": [
                "adjudication_pending",
                "adjudication_disagreement",
                "no_pair_named",
                "locator_unavailable",
                "attribution_unresolved",
                "catalog_inapplicable",
                "ulif_unattested",
                "vesum_unattested",
                "sum11_markers_unavailable",
            ],
            "excluded": ["not_sum11_headword"],
        },
    }


def candidate(component, operation, row, slots, context, response, reason="ok"):
    outcome = "accepted" if reason == "ok" else ("excluded" if reason == "not_sum11_headword" else "withheld")
    return Candidate(
        component,
        str(row["id"]),
        outcome,
        reason,
        () if outcome == "accepted" else (reason,),
        operation,
        tuple(slots),
        tuple(context),
        tuple(response),
        ("c7_opt_in", "soviet_colonization_context") if component == "C7" else (),
    )


def packet_files(ctx, component):
    return {
        f"{component}/adjudication-packets/{p['batch_sha256']}.json": canonical(p) + b"\n"
        for p in batches(ctx.reader.iter_rows("sources.db", "style_guide"))
    }
