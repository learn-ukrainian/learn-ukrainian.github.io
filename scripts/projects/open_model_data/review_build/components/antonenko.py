"""Host-only row batches and dual offset selections; no semantic parser or census."""

import json
import re
from pathlib import Path

from scripts.common.task_store_paths import tasks_dir

from ..attribution import Attribution
from ..bindings import normalize
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import BuildError, require
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


def validate_receipts(batch, receipts, reconciliation=None):
    """Validate complete seat selections; retain the union and agreed subset per row."""
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
    decisions = {}
    for key in rows:
        sol, opus = set(selections["sol"][key]), set(selections["opus"][key])
        decisions[key] = {
            "pairs": sorted(sol & opus),
            "disputed": sorted(sol ^ opus),
            "reason": "ok" if sol | opus else "no_pair_named",
        }
    if reconciliation:
        accepted = validate_reconciliation(batch, decisions, reconciliation)
        for key, pairs in accepted.items():
            decisions[key]["pairs"] = sorted(set(decisions[key]["pairs"]) | pairs)
            decisions[key]["disputed"] = sorted(set(decisions[key]["disputed"]) - pairs)
    return decisions


def validate_reconciliation(batch, decisions, receipts):
    """Only two explicit accepts admit an originally disputed, direction-bound pair."""
    require(set(receipts) == set(MODELS), "adjudication_seats")
    rows = {row["row_id"]: row for row in batch["rows"]}
    expected = {(key, pair) for key, row in decisions.items() for pair in row["disputed"]}
    selections, tasks = {}, []
    for seat, model in MODELS.items():
        receipt = receipts[seat]
        require(
            isinstance(receipt, dict) and set(receipt) == {"schema", "model", "task_id", "batch_sha256", "pairs"},
            "adjudication_receipt",
        )
        require(
            receipt["schema"] == "antonenko-reconcile-receipt.v1" and receipt["model"] == model,
            "adjudication_provenance",
        )
        require(isinstance(receipt["task_id"], str) and bool(receipt["task_id"].strip()), "adjudication_provenance")
        require(receipt["batch_sha256"] == batch["batch_sha256"], "adjudication_stale")
        require(isinstance(receipt["pairs"], list), "adjudication_pairs")
        selected = {}
        for item in receipt["pairs"]:
            require(
                isinstance(item, dict) and set(item) == {"row_id", "rejected", "recommended", "decision"},
                "adjudication_pairs",
            )
            key = item["row_id"]
            require(type(key) is int and key in rows, "adjudication_rows")
            pair = _pairs([{role: item[role] for role in ("rejected", "recommended")}], rows[key]["text"])[0]
            identity = (key, pair)
            require(identity in expected and identity not in selected, "adjudication_pairs")
            require(
                isinstance(item["decision"], str) and item["decision"] in {"accept", "reject"}, "adjudication_decision"
            )
            selected[identity] = item["decision"]
        require(set(selected) == expected, "adjudication_pairs")
        selections[seat] = selected
        tasks.append(receipt["task_id"])
    require(len(set(tasks)) == 2, "adjudication_provenance")
    return {
        key: {
            pair
            for row_id, pair in expected
            if row_id == key and all(selections[seat][(key, pair)] == "accept" for seat in MODELS)
        }
        for key in rows
    }


def read_json(raw):
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise BuildError("adjudication_receipt") from None


def result_receipt(raw, batch_sha256):
    """Select the unique batch-matching JSON fence; never normalize fields."""
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeError:
        raise BuildError("adjudication_receipt") from None
    blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.S)
    if not blocks:
        return read_json(text)
    payloads = [read_json(block) for block in blocks]
    matches = [p for p in payloads if isinstance(p, dict) and p.get("batch_sha256") == batch_sha256]
    require(len(matches) == 1, "adjudication_receipt")
    return matches[0]


def attestation_for(receipt, task, result):
    """Driver extractor helper: bind the extracted object to the settled dispatch output."""
    require(isinstance(receipt, dict) and isinstance(task, dict), "adjudication_provenance")
    require(
        task.get("task_id") == receipt.get("task_id") and task.get("model") == receipt.get("model"),
        "adjudication_provenance",
    )
    require(task.get("status") == "done", "adjudication_provenance")
    require(task.get("result_sha256") == digest(result), "adjudication_stale")
    require(canonical(result_receipt(result, receipt.get("batch_sha256"))) == canonical(receipt), "adjudication_stale")
    require(isinstance(task.get("finished_at"), str) and bool(task["finished_at"].strip()), "adjudication_provenance")
    return {key: task[key] for key in ("task_id", "model", "status", "result_sha256", "finished_at")}


def pair_id(row_id, left=None, right=None):
    return digest(canonical([row_id, left, right]))


def write_reconciliation_packets(rows, receipt_root, root):
    """Write only source-bound disputed pairs, host-only, without invoking either seat."""
    rows = list(rows)
    store = ReceiptStore()

    class Reader:
        def iter_rows(self, source, table):
            return iter(rows)

    from . import ComponentContext

    ctx = ComponentContext(Reader(), {"antonenko_receipts": str(receipt_root)})
    store.configure(ctx)
    packets = []
    for batch, _, _ in store.documents.values():
        disputed = []
        for row in batch["rows"]:
            for left, right in store.decisions[row["row_id"]]["disputed"]:
                disputed.append(
                    {
                        **row,
                        "rejected": {"start": left[0], "end": left[1]},
                        "recommended": {"start": right[0], "end": right[1]},
                        "rejected_text": row["text"][slice(*left)],
                        "recommended_text": row["text"][slice(*right)],
                    }
                )
        if disputed:
            packets.append(
                {"schema": "antonenko-reconcile-packet.v1", "batch_sha256": batch["batch_sha256"], "pairs": disputed}
            )
    with OutputGuard(Path(root)) as guard:
        for packet in packets:
            guard.write(f"{packet['batch_sha256']}.json", canonical(packet) + b"\n")
    return {"batches": len(packets), "pairs": sum(len(p["pairs"]) for p in packets)}


class ReceiptStore:
    """Pin selections, dispatch attestations and reconciliation; reconstruct every unit."""

    def __init__(self):
        self.reader = None
        self.root = None
        self.inputs = {}
        self.decisions = {}
        self.documents = {}
        self.records = {}

    def _load(self, guard, batch, reconciliation=False):
        raw = {}
        prefix = batch["batch_sha256"] + (".reconcile" if reconciliation else "")
        for seat in MODELS:
            name = f"{prefix}.{seat}.json"
            if not (guard.path / name).exists():
                continue
            content = guard.read(name)
            receipt = read_json(content)
            require(isinstance(receipt, dict), "adjudication_receipt")
            sidecar_name = f"{prefix}.{seat}.attestation.json"
            require((guard.path / sidecar_name).exists(), "adjudication_attestation")
            sidecar_raw = guard.read(sidecar_name)
            sidecar = read_json(sidecar_raw)
            require(
                isinstance(sidecar, dict)
                and set(sidecar) == {"task_id", "model", "status", "result_sha256", "finished_at"},
                "adjudication_attestation",
            )
            require(
                sidecar["task_id"] == receipt.get("task_id")
                and sidecar["model"] == MODELS[seat]
                and sidecar["model"] == receipt.get("model")
                and sidecar["status"] == "done",
                "adjudication_provenance",
            )
            task_id = sidecar["task_id"]
            require(isinstance(task_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", task_id), "adjudication_provenance")
            try:
                task_raw = (tasks_dir() / f"{task_id}.json").read_bytes()
                result = (tasks_dir() / f"{task_id}.result").read_bytes()
            except OSError:
                raise BuildError("adjudication_attestation") from None
            require(attestation_for(receipt, read_json(task_raw), result) == sidecar, "adjudication_provenance")
            raw[seat] = content
            for filename, data in (
                (name, content),
                (sidecar_name, sidecar_raw),
                (f"dispatch/{task_id}.json", task_raw),
                (f"dispatch/{task_id}.result", result),
            ):
                actual = digest(data)
                require(filename not in self.inputs or self.inputs[filename] == actual, "adjudication_stale")
                self.inputs[filename] = actual
        return raw

    def configure(self, ctx):
        if self.reader is ctx.reader:
            return
        self.reader, self.root = ctx.reader, ctx.request.get("antonenko_receipts")
        self.inputs, self.decisions, self.documents, self.records = {}, {}, {}, {}
        rows = list(ctx.reader.iter_rows("sources.db", "style_guide"))
        for batch in batches(rows):
            sha = batch["batch_sha256"]
            raw, reconciliation = {}, {}
            if self.root is not None:
                with OutputGuard(Path(self.root)) as guard:
                    raw = self._load(guard, batch)
                    reconciliation = self._load(guard, batch, reconciliation=True)
            require(not reconciliation or bool(raw), "adjudication_seats")
            if not raw:
                for row in batch["rows"]:
                    self.decisions[row["row_id"]] = {"reason": "adjudication_pending", "pairs": [], "disputed": []}
                continue
            self.decisions.update(
                validate_receipts(
                    batch,
                    {s: read_json(b) for s, b in raw.items()},
                    {s: read_json(b) for s, b in reconciliation.items()},
                )
            )
            self.documents[sha] = (batch, raw, reconciliation)
        for row in rows:
            decision = self.get(row)
            pairs = [(left, right, "ok") for left, right in decision["pairs"]]
            pairs += [(left, right, "adjudication_disagreement") for left, right in decision["disputed"]]
            if not pairs:
                pairs = [(None, None, decision["reason"])]
            for left, right, reason in pairs:
                key = pair_id(row["id"], left, right)
                record = {
                    "id": key,
                    "book_id": row["id"],
                    "pair": f"id={row['id']}",
                    "source": row["source"],
                    "reason": reason,
                    "rejected_span": left,
                    "recommended_span": right,
                }
                if left is not None:
                    batch, raw, reconciliation = next(
                        doc for doc in self.documents.values() if any(r["row_id"] == row["id"] for r in doc[0]["rows"])
                    )
                    record.update(
                        {
                            "rejected_form": row["text"][slice(*left)],
                            "recommended_form": row["text"][slice(*right)],
                            "rejected_key": normalize(row["text"][slice(*left)], "unstress_nfc"),
                            "recommended_key": normalize(row["text"][slice(*right)], "unstress_nfc"),
                            "sol": "APPROVE" if reason == "ok" else "WITHHOLD",
                            "opus": "APPROVE" if reason == "ok" else "WITHHOLD",
                            "batch_sha256": batch["batch_sha256"],
                            "row_text_sha256": digest(row["text"].encode()),
                            **{f"{seat}_sha256": digest(content) for seat, content in raw.items()},
                            **{f"reconcile_{seat}_sha256": digest(content) for seat, content in reconciliation.items()},
                        }
                    )
                self.records[key] = record

    def get(self, row):
        return self.decisions.get(row["id"], {"reason": "locator_unavailable", "pairs": [], "disputed": []})

    def row_units(self, row):
        return [record for record in self.records.values() if record["book_id"] == row["id"]]

    def admit(self, row, left, right):
        receipt = self.records[pair_id(row["id"], left, right)]
        require(receipt["reason"] == "ok", "adjudication_direction")
        return receipt

    def row(self, table, row_key):
        require(table in {"C6b", "C7"} and row_key.startswith("id="), "row_unavailable")
        result = self.records.get(row_key[3:])
        require(result is not None, "row_unavailable")
        if "batch_sha256" not in result:
            return result
        batch, raw, reconciliation = self.documents[result["batch_sha256"]]
        require(all(digest(content) == result[f"{seat}_sha256"] for seat, content in raw.items()), "adjudication_stale")
        require(
            all(digest(content) == result[f"reconcile_{seat}_sha256"] for seat, content in reconciliation.items()),
            "adjudication_stale",
        )
        with OutputGuard(Path(self.root)) as guard:
            require(
                self._load(guard, batch) == raw and self._load(guard, batch, True) == reconciliation,
                "adjudication_stale",
            )
        live = {r["id"]: r for r in self.reader.iter_rows("sources.db", "style_guide")}
        require(
            all(
                r["row_id"] in live
                and r["text"] == live[r["row_id"]]["text"]
                and r["locator"] == book_locator(live[r["row_id"]])
                for r in batch["rows"]
            ),
            "adjudication_stale",
        )
        decisions = validate_receipts(
            batch, {s: read_json(b) for s, b in raw.items()}, {s: read_json(b) for s, b in reconciliation.items()}
        )
        row = live[result["book_id"]]
        require(result["row_text_sha256"] == digest(row["text"].encode()), "adjudication_stale")
        require(result["pair"] == f"id={row['id']}" and result["source"] == row["source"], "adjudication_stale")
        pairs = decisions[result["book_id"]]["pairs" if result["reason"] == "ok" else "disputed"]
        require((result["rejected_span"], result["recommended_span"]) in pairs, "adjudication_direction")
        if result["reason"] == "ok":
            require(result["sol"] == result["opus"] == "APPROVE", "adjudication_provenance")
        return result

    def units(self, query):
        require(query == {"kind": "antonenko_pairs", "store": STORE}, "unit_query")
        return list(self.records)

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
                "unit_query": {"kind": "antonenko_pairs", "store": STORE},
                "census_query": {"kind": "sql", "store": "sources.db", "sql": "SELECT id FROM style_guide"},
                "frozen_count": 342,
                "unit_id": unit,
            }
        },
        "unit_grain": "selected offset pair union; one placeholder per unresolved or unlocated row",
        "annotation_layer": "source_text_and_dual_adjudication",
        "reference_multiplicity": "one record per agreed offset pair in a row",
        "unit_multiplicity": "one",
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


def candidate(component, operation, row, slots, context, response, reason="ok", unit=None):
    outcome = "accepted" if reason == "ok" else ("excluded" if reason == "not_sum11_headword" else "withheld")
    require(unit is not None, "unit_id_spec")
    accounting = Value("accounting_unit", unit["id"], (receipt_citation(unit, component, "id"),), None, "verbatim")
    return Candidate(
        component,
        unit["id"],
        outcome,
        reason,
        () if outcome == "accepted" else (reason,),
        operation,
        (*slots, accounting),
        tuple(context),
        tuple(response),
        ("c7_opt_in", "soviet_colonization_context") if component == "C7" else (),
    )


def packet_files(ctx, component):
    return {
        f"{component}/adjudication-packets/{p['batch_sha256']}.json": canonical(p) + b"\n"
        for p in batches(ctx.reader.iter_rows("sources.db", "style_guide"))
    }
