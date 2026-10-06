"""Source-bound WP6 packets and dual-seat receipts; no automatic semantic verdict.

C7's pre-adjudication domain is a census of potential rejected headwords, not a
claim that every headword is rejected by the book. Each distinct exact SUM-11
headword in a book row has one unit, anchored at its first whole-token span.
The independent file unit query uses a character scanner, rather than the
extractor's regex. Dual review decides rejection, recommendation and calque
status. Private receipt files are supplied by the accountable driver.
"""

import json
import re
from dataclasses import asdict
from pathlib import Path

from ..attribution import Attribution
from ..bindings import normalize
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import require
from ..output import OutputGuard

SOURCE = "antonenko_style_guide"
STORE = "antonenko-adjudication"
TOKEN = re.compile(r"[^\W\d_]+(?:['’ʼ][^\W\d_]+)*")
MODELS = {"sol": "gpt-6.1-sol", "opus": "claude-opus-5-5"}
FAMILIES = {"sol": "openai", "opus": "anthropic"}


def selector(area, slot, **kwargs):
    return {"area": area, "slot": slot, **kwargs}


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


def book_locator(row):
    """Page zero is not a printed page. Never invent a missing section."""
    if type(row.get("page")) is int and row["page"] > 0:
        return f"page {row['page']}"
    return str(row.get("section") or "").strip()


def quoted(row, slot, span=None, witnesses=()):
    text = row["text"] if span is None else row["text"][slice(*span)]
    return Value(slot, text, (citation(row), *witnesses), span, "verbatim")


def token_spans(text):
    """First exact occurrence of each token; no lowercasing of source bytes."""
    result = {}
    for match in TOKEN.finditer(text):
        result.setdefault(match.group(), match.span())
    return result


def scan_tokens(text):
    """Independent census scanner, intentionally separate from regex extraction."""
    result, i = {}, 0

    def letter(char):
        return char.isalnum() and not char.isdecimal() and char != "_"

    while i < len(text):
        if not letter(text[i]):
            i += 1
            continue
        start = i
        while i < len(text):
            if letter(text[i]) or (text[i] in "'’ʼ" and i + 1 < len(text) and letter(text[i + 1])):
                i += 1
            else:
                break
        result.setdefault(text[start:i], (start, i))
    return result


def form_unit(row, span):
    return canonical([["sources.db", "style_guide", f"id={row['id']}", list(span)]]).decode()


def packet(row, component, *, form_span=None):
    """Every text-bearing member is copied from the cited source, never authored."""
    unit = str(row["id"]) if form_span is None else form_unit(row, form_span)
    body = {
        "schema": "antonenko-adjudication-packet.v1",
        "component": component,
        "unit_id": unit,
        "pair_id": f"id={row['id']}",
        "source_citation": asdict(citation(row)),
        "passage_file": f"passages/{row['id']}.json",
        "source_text_sha256": digest(row["text"].encode()),
        "candidate_span": None if form_span is None else list(form_span),
        "candidate_form": None if form_span is None else row["text"][slice(*form_span)],
        "review_seats": MODELS,
        "requirements": [
            "Read the cited whole passage; authenticate both members and their direction using exact spans.",
            "Use sources tools on the structured guide and full-book prose; tool quotes are required.",
            "C6b: authenticate calque status and the author's explicit replacement, not just cooccurrence.",
            "C7: authenticate book rejection plus SUM-11 rejected-side and ULIF/VESUM recommended-side witnesses.",
            "Each seat uses a distinct fresh session. Disagreement or insufficient evidence withholds.",
            "Return only APPROVE, REJECT or UNSUPPORTED; never supply new Ukrainian text.",
        ],
    }
    return {**body, "packet_sha256": digest(canonical(body))}


class ReceiptStore:
    """Private driver-controlled receipts. Hashes bind verdicts to exact packets.

    This validates artifact provenance, not a cryptographic model identity. The
    driver is responsible for routing/attesting the named subscription seats.
    Missing receipts never become approval. A changed passage or span invalidates
    approval. Source text and receipt inputs are pinned by the framework.
    """

    def __init__(self):
        self.reader = None
        self.root = None
        self.cache = {}
        self.inputs = {}

    def configure(self, ctx):
        if self.reader is ctx.reader:
            return
        self.reader = ctx.reader
        self.root = ctx.request.get("antonenko_receipts")
        self.cache, self.inputs = {}, {}

    def units(self, query):
        require(query.get("kind") == "antonenko_candidate_headwords.v1", "unit_query")
        require(self.reader is not None, "unit_query")
        headwords = set(
            self.reader.query_values({"kind": "sql", "store": "sources.db", "sql": "SELECT word FROM sum11"})
        )
        return sorted(
            form_unit(row, span)
            for row in self.reader.iter_rows("sources.db", "style_guide")
            for form, span in scan_tokens(row["text"]).items()
            if form in headwords
        )

    def get(self, row, component, span=None):
        expected = packet(row, component, form_span=span)
        key = digest(expected["unit_id"].encode())
        cache_key = (component, key)
        if cache_key in self.cache:
            return self.cache[cache_key]
        if self.root is None:
            self.cache[cache_key] = None
            return None
        # Reading uses exactly the same private path/mode/no-symlink guard as output.
        with OutputGuard(Path(self.root)) as guard:
            name = f"{component}/{key}.json"
            target = guard.path / name
            if not target.exists():
                self.cache[cache_key] = None
                return None
            raw = guard.read(name)
        self.inputs[name] = digest(raw)
        data = json.loads(raw)
        require(data.get("schema") == "antonenko-adjudication-receipt.v1", "adjudication_receipt")
        require(
            data.get("pair_id") == expected["pair_id"]
            and data.get("component") == component
            and data.get("unit_id") == expected["unit_id"]
            and data.get("packet_sha256") == expected["packet_sha256"]
            and data.get("source_text_sha256") == expected["source_text_sha256"],
            "adjudication_stale",
        )
        left, right = data.get("rejected_span"), data.get("recommended_span")
        require(
            all(
                isinstance(s, list)
                and len(s) == 2
                and all(type(n) is int for n in s)
                and 0 <= s[0] < s[1] <= len(row["text"])
                for s in (left, right)
            ),
            "adjudication_span",
        )
        require(left != right and row["text"][slice(*left)] != row["text"][slice(*right)], "adjudication_span")
        if span is not None:
            require(left == list(span), "adjudication_direction")
        sessions = []
        for seat, model in MODELS.items():
            verdict = data.get(seat)
            require(
                isinstance(verdict, dict)
                and verdict.get("model") == model
                and verdict.get("family") == FAMILIES[seat]
                and verdict.get("verdict") in {"APPROVE", "REJECT", "UNSUPPORTED"}
                and verdict.get("packet_sha256") == expected["packet_sha256"]
                and verdict.get("rejected_span") == left
                and verdict.get("recommended_span") == right
                and bool(verdict.get("tool_evidence"))
                and isinstance(verdict.get("harness"), str)
                and bool(verdict["harness"])
                and isinstance(verdict.get("task_id"), str)
                and bool(verdict["task_id"])
                and isinstance(verdict.get("session_id"), str)
                and bool(verdict["session_id"]),
                "adjudication_provenance",
            )
            require(verdict["task_id"].rsplit("/", 1)[-1] != "impl-rb1-wp6c", "self_review_detected")
            if component == "C6b":
                require(
                    verdict.get("calque") is data.get("calque") and type(data.get("calque")) is bool,
                    "adjudication_provenance",
                )
            sessions.append(verdict["session_id"])
        require(len(set(sessions)) == 2, "self_review_detected")
        receipt = {
            "id": key,
            "pair": data["pair_id"],
            "book_id": row["id"],
            "source": row["source"],
            "rejected_form": row["text"][slice(*left)],
            "recommended_form": row["text"][slice(*right)],
            "rejected_key": normalize(row["text"][slice(*left)], "unstress_nfc"),
            "recommended_key": normalize(row["text"][slice(*right)], "unstress_nfc"),
            "sol": data["sol"]["verdict"],
            "opus": data["opus"]["verdict"],
            "calque": data.get("calque") is True,
            "rejected_span": tuple(left),
            "recommended_span": tuple(right),
        }
        self.cache[cache_key] = receipt
        return receipt

    def row(self, table, row_key):
        require(table in {"C6b", "C7"} and row_key.startswith("id="), "row_unavailable")
        result = self.cache.get((table, row_key[3:]))
        require(result is not None, "row_unavailable")
        return result

    def all_rows(self, table):
        return [r for (component, _), r in self.cache.items() if component == table and r is not None]

    def file_hashes(self):
        return dict(self.inputs)


RECEIPTS = ReceiptStore()


def receipt_citation(receipt, component, field):
    return citation(receipt, field, store=STORE, table=component, locator=f"adjudication {receipt['pair']}")


class HeldBibliographyAdapter:
    """Only resolve register forms against actual held bibliographic fields.

    Current book rows do not hold edition/year and SUM-11 does not hold volume /
    page. These adapters intentionally withhold until holdings/register work
    supplies a complete exact bibliography, rather than guessing an edition.
    """

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


def common_spec(operation, query, count, unit):
    return {
        "operations": [operation],
        "operation_specs": {operation: {"unit_query": query, "frozen_count": count, "unit_id": unit}},
        "unit_grain": "style_guide row"
        if operation == "book_calque_replacement"
        else "potential rejected headword per style_guide row, first exact span; semantic rejected census awaits adjudication",
        "annotation_layer": "source_text_and_dual_adjudication",
        "reference_multiplicity": "one jointly approved replacement per accounting unit",
        "reasons": {
            "accepted": ["ok"],
            "rejected": [],
            "withheld": [
                "adjudication_pending",
                "adjudication_unsupported",
                "not_calque",
                "locator_unavailable",
                "attribution_unresolved",
                "catalog_inapplicable",
                "ulif_unattested",
                "vesum_unattested",
                "sum11_markers_unavailable",
            ],
            "excluded": [],
        },
    }


def candidate(component, unit, operation, row, slots, context, response, receipt):
    outcome, reason = "accepted", "ok"
    if not book_locator(row):
        outcome, reason = "withheld", "locator_unavailable"
    elif receipt is None:
        outcome, reason = "withheld", "adjudication_pending"
    elif "REJECT" in {receipt["sol"], receipt["opus"]}:
        # REJECT is not structural positive evidence that the source is wrong.
        outcome, reason = "withheld", "adjudication_unsupported"
    elif "UNSUPPORTED" in {receipt["sol"], receipt["opus"]}:
        outcome, reason = "withheld", "adjudication_unsupported"
    elif component == "C6b" and not receipt["calque"]:
        outcome, reason = "withheld", "not_calque"
    return Candidate(
        component,
        unit,
        outcome,
        reason,
        () if outcome == "accepted" else (reason,),
        operation,
        tuple(slots),
        tuple(context),
        tuple(response),
        ("c7_opt_in", "soviet_colonization_context") if component == "C7" else (),
    )


def packet_files(ctx, component, spans):
    result = {}
    for row, span in spans:
        p = packet(row, component, form_span=span)
        key = digest(p["unit_id"].encode())
        result[f"{component}/adjudication-packets/{key}.json"] = canonical(p) + b"\n"
        result[f"{component}/passages/{row['id']}.json"] = (
            canonical({"citation": asdict(citation(row)), "text": row["text"], "author": row["source"]}) + b"\n"
        )
    return result
