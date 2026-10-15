"""Independent integrity checks and takedown rehearsal for assembled pilot cards (#8981).

`verify` re-reads every cited locator from the held sources (read-only) and re-derives what it can from the
frozen inputs; it does not trust the assembler's own bookkeeping. `rehearse` runs the withdrawal / rollback
contract of schema.md §12-§13: a suppression selector removes the dependent assertions everywhere, the rebuild
under the same selectors is stable, and lifting the selector restores the previous bytes.

Neither command certifies linguistic correctness: a green run proves mechanics, never meaning.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas.allocate_pilot_identities import label_pos
from scripts.atlas.word_card_resolver import aid, public_projection

SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "word-card-v1.schema.json"
DISPOSITIONS = frozenset({
    "asserted", "held", "source_absent", "not_in_frozen_inputs", "not_applicable", "unresolved",
})
LOCATOR = re.compile(r"^(?P<head>[a-z0-9_]+(?::[a-z0-9_]+)*:(?:id|entry):\d+|atlas0:enrichment:[^ ]+)"
                     r"(?::slot:(?P<slot>[A-Za-z0-9_.*~+]+))?(?: \[(?P<part>.+)\])?$")


def plain_text(raw_html: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw_html))


def sense_gloss_parts(gloss: str) -> list[str]:
    if not (gloss.startswith("(") and gloss.endswith(")")):
        return []
    return [p.strip() for p in gloss[1:-1].split(";")]


class Resolver:
    """Resolve one assertion's locator against the held sources and report whether the cited value is there."""

    def __init__(self, inputs: wa.Inputs):
        self.inputs = inputs
        self.sources = inputs.sources

    def row(self, table: str, row_id: int):
        out = self.sources.sources.execute(f'SELECT * FROM "{table}" WHERE id=?', (row_id,)).fetchone()
        return src.row_dict(out) if out else None

    def check(self, card: dict, a: dict) -> str | None:
        """None when the locator resolves and carries the value; otherwise a closed reason code."""
        locator = a["locator"]
        match = LOCATOR.match(locator)
        if not match:
            return "locator_grammar"
        head, slot, part = match.group("head"), match.group("slot"), match.group("part") or ""
        kind = head.split(":")
        value = a["value"]
        if head.startswith("ulif:ulif_dictua_entries:id:"):
            row = self.row("ulif_dictua_entries", int(kind[-1]))
            if row is None:
                return "row_missing"
            return self.entry_value(a, row, part, card)
        if head.startswith("ulif:ulif_dictua_sections:id:"):
            row = self.row("ulif_dictua_sections", int(kind[-1]))
            if row is None:
                return "row_missing"
            return self.section_value(a, row, part)
        if head.startswith("ulif:ulif_forms:entry:"):
            return self.forms_value(a, int(kind[-1]), slot)
        if head.startswith("vesum:entry:"):
            return self.vesum_value(a, int(kind[-1]), part, card["key_at_creation"]["spelling"])
        if head.startswith("puls:puls_cefr:id:"):
            row = self.row("puls_cefr", int(kind[-1]))
            return None if row and row["level"] == value else "value_mismatch"
        if head.startswith("frazeolohichnyi:frazeolohichnyi:id:"):
            row = self.row("frazeolohichnyi", int(kind[-1]))
            if row is None:
                return "row_missing"
            return None if src.nfc(wa.aggregator_form(row["word"])) == src.nfc(value) else "value_mismatch"
        if head.startswith("atlas0:enrichment:"):
            record = self.inputs.records.get(head)
            if record is None:
                return "row_missing"
            return None if src.nfc(json.loads(record["raw_row"]["payload_json"])["form"]) == src.nfc(value) \
                else "value_mismatch"
        return "locator_unsupported"

    def entry_value(self, a, row, part, card):
        field, value = a["field"], a["value"]
        if part == "canonical_headword":
            head = row["canonical_headword"]
            if src.unstressed(head) != src.unstressed(card["key_at_creation"]["spelling"]):
                return "value_mismatch"
            if field == "spelling":
                return None if src.unstressed(head) == value else "value_mismatch"
            if field == "stress":
                readings = src.stress_forms(head)
                return None if (value if isinstance(value, list) else [value]) == readings else "value_mismatch"
            return "field_unsupported"
        if part == "grammatical_label":
            label = row["grammatical_label"]
            checks = {
                "grammatical_label": value == label,
                "pos": label_pos(label) == value,
                "gender": wa.parse_gender(label) == value,
                "aspect": wa.parse_aspect(label) == value,
            }
            return None if checks.get(field) else "value_mismatch"
        match = re.fullmatch(r"sense_gloss\[(\d+)\]", part)
        if match:
            parts = sense_gloss_parts(row["sense_gloss"])
            index = int(match.group(1))
            return None if index < len(parts) and parts[index] == value else "value_mismatch"
        return "locator_part"

    def section_value(self, a, row, part):
        if part.startswith("payload_json#/raw_html"):
            text = squeezed(plain_text(json.loads(row["payload_json"])["raw_html"]))
        else:
            return "locator_part"
        value = a["value"]
        pieces = [value["members"], value.get("discriminator")] if isinstance(value, dict) else [value]
        if a["field"] == "mwe_form":
            return None if wa.squeeze(value) and wa.squeeze(value) in text else "value_mismatch"
        for piece in pieces:
            if piece and wa.squeeze(piece) not in text:
                return "value_mismatch"
        return None

    def forms_value(self, a, entry_id, slot):
        value = a["value"]
        rows = {r["id"]: r for r in self.sources.sources.execute(
            f"SELECT * FROM ulif_forms WHERE id IN ({','.join('?' * len(value['row_ids']))})", value["row_ids"])}
        if len(rows) != len(value["row_ids"]):
            return "row_missing"
        tokens = set(slot.split("."))
        for row in rows.values():
            if row["entry_id"] != entry_id or row["marked_asterisk"]:
                return "value_mismatch"
            row_slot = src.ulif_slot(json.loads(row["grammatical_tags"]))
            if row_slot is None or not tokens <= set(row_slot) | {"*"}:
                return "value_mismatch"
        stressed = sorted({src.nfc(r["form_stressed"]) for r in rows.values()})
        return None if stressed == sorted(value["forms"]) else "value_mismatch"

    def vesum_value(self, a, entry_id, part, lemma):
        # forms_all is indexed by lemma, not by entry; the lemma of an assertion's entry is the card's spelling.
        rows = [r for r in self.sources.vesum_forms(lemma) if r["entry_id"] == entry_id]
        if not rows:
            return "row_missing"
        field, value = a["field"], a["value"]
        if part == "lemma":
            return None if any(r["lemma"] == value for r in rows) else "value_mismatch"
        if part == "pos":
            return None if any(r["pos"] == value for r in rows) else "value_mismatch"
        if part == "source_comment":
            stresses = set()
            for r in rows:
                for token in re.split(r"[\s;,()]+", r["source_comment"] or ""):
                    if src.ACUTE in token:
                        stresses.add(src.nfc(token))
            wanted = value if isinstance(value, list) else [value]
            return None if set(wanted) <= stresses else "value_mismatch"
        if part == "tags":
            tokens = {t for r in rows for t in r["tags"].split(":")}
            if field == "gender":
                return None if set(value) <= tokens else "value_mismatch"
            if field == "aspect":
                return None if (wa.vesum_aspect([{"tags": r["tags"]} for r in rows]) == value) else "value_mismatch"
        if part.startswith("slot "):
            forms = {src.nfc(r["word_form"]) for r in rows}
            tags = {r["tags"] for r in rows}
            return None if set(value["forms"]) <= forms and set(value["tags"]) <= tags else "value_mismatch"
        return "locator_part"


def squeezed(text: str) -> str:
    return wa.squeeze(text)


def verify(inputs: wa.Inputs, result: dict, again: dict | None = None) -> dict:
    """Run every integrity check; returns {check: {passed, ...}} and never raises on a failed check."""
    cards = result["cards"]
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    report: dict = {}

    schema_errors = Counter()
    for card in cards.values():
        for error in validator.iter_errors(card):
            schema_errors[error.message[:80]] += 1
    report["schema"] = {"passed": not schema_errors, "cards": len(cards), "errors": dict(schema_errors)}

    unit_cards = {inputs.entry_by_unit[u["unit_key"]]["card_id"] for u in inputs.units}
    senses_ok = all(
        {s["sense_id"] for s in c["senses"]} == {s["sense_id"] for e in inputs.registry["entries"]
                                                  if e["card_id"] == c["card_id"] for s in e["senses"]}
        for c in cards.values())
    report["conservation"] = {
        "passed": set(cards) == unit_cards and len(cards) == len(inputs.units) and senses_ok
        and set(result["ledger"].cards) == unit_cards,
        "units": len(inputs.units), "cards": len(cards), "ledger_cards": len(result["ledger"].cards),
    }

    registry_sr = {sr["source_record_id"]: sr for sr in inputs.registry["source_records"]}
    id_errors, register_errors, lineage_errors, sr_errors, forbidden = Counter(), Counter(), Counter(), Counter(), 0
    cited_records = set()
    for card in cards.values():
        for a in card["assertions"]:
            if a.get("status") != "active":
                continue
            expected = aid(a["source_id"], a["snapshot_id"], a["locator"], a["subject"], a["field"], a["value_norm"],
                           a["extraction_version"])
            id_errors["id"] += expected != a["assertion_id"]
            register_errors["source"] += a["source_id"] not in inputs.register
            register_errors["version"] += a["licence_ref"]["register_version"] != inputs.register_version
            group, tier = wa.LINEAGE[a["source_id"]]
            lineage_errors["lineage"] += (a["independence_group"], a["tier"]) != (group, tier)
            if a.get("source_record_id"):
                cited_records.add(a["source_record_id"])
                sr_errors["unknown"] += a["source_record_id"] not in registry_sr
                sr_errors["source"] += registry_sr.get(a["source_record_id"], {}).get("source_id") != a["source_id"]
            forbidden += a["source_id"] == "sum11" and a["field"] != "russification_exposed"
    report["assertion_identity"] = {"passed": not any(id_errors.values()), "errors": dict(id_errors)}
    report["register_lineage"] = {"passed": not any(register_errors.values()) and not any(lineage_errors.values()),
                                  "errors": {**register_errors, **lineage_errors}}
    frozen = {sr["source_record_id"] for sr in inputs.registry["source_records"]
              if any(c.get("locator") in inputs.records for c in sr["correspondence"])}
    report["source_records"] = {"passed": not any(sr_errors.values()) and frozen <= cited_records and not forbidden,
                                "frozen": len(frozen), "cited": len(frozen & cited_records),
                                "errors": dict(sr_errors), "sum11_outside_russification": forbidden}

    resolver = Resolver(inputs)
    locator_errors = Counter()
    checked = 0
    for card in cards.values():
        for a in card["assertions"]:
            if a.get("status") != "active":
                continue
            checked += 1
            problem = resolver.check(card, a)
            if problem:
                locator_errors[f"{a['source_id']}:{a['field']}:{problem}"] += 1
    report["locators"] = {"passed": not locator_errors, "checked": checked, "errors": dict(locator_errors)}

    ledger_errors = Counter()
    for card_id, item in result["ledger"].cards.items():
        card = cards[card_id]
        fields = set(item["fields"])
        kind = "mwe" if card["card_kind"] == "mwe" else "lexeme"
        required = set((wa.MWE_FIELDS if kind == "mwe" else wa.CARD_FIELDS) + wa.SENSE_FIELDS)
        ledger_errors["missing_field"] += len(required - fields)
        asserted = {a["field"] for a in card["assertions"] if a["status"] == "active"}
        for name, d in item["fields"].items():
            ledger_errors["bad_disposition"] += d["disposition"] not in DISPOSITIONS
            if d["disposition"] == "asserted" and name not in asserted:
                ledger_errors["asserted_without_assertion"] += 1
    report["ledger"] = {"passed": not any(ledger_errors.values()), "errors": dict(ledger_errors)}

    if again is not None:
        first = {k: foundation.digest(v) for k, v in cards.items()}
        second = {k: foundation.digest(v) for k, v in again["cards"].items()}
        report["determinism"] = {"passed": first == second, "cards": len(first)}

    projection_errors = 0
    for card in cards.values():
        if foundation.digest(public_projection(card)) != foundation.digest(card):
            projection_errors += 1
    report["public_projection"] = {"passed": projection_errors == 0, "differing_cards": projection_errors}
    report["passed"] = all(v["passed"] for v in report.values() if isinstance(v, dict))
    return report


def rehearse(inputs: wa.Inputs) -> dict:
    """Withdrawal and rollback rehearsal against the frozen pilot (schema.md §12-§13, #8980 contract)."""
    baseline = wa.build(inputs)
    rehearsal_units = [u for u in inputs.units if "withdrawal_rehearsal_candidate" in u["categories"]]
    out = {"units": [u["unit_key"] for u in rehearsal_units], "scenarios": {}}
    selectors = []
    for unit in rehearsal_units:
        record = inputs.record_ids[("ulif", unit["anchor_locator"])]
        selectors.append(("source_record", {
            "kind": "source_record", "source_id": "ulif", "source_record_id": record["source_record_id"],
            "alias_at_creation": record["aliases"][0]["key"], "on_ambiguous": "suppress_all_candidates"}))
    selectors.append(("source", {"kind": "source", "source_id": "ukrainian_word_stress"}))
    for name, selector in selectors:
        suppressions = {"schema_version": "1", "entries": [{
            "suppression_id": f"sup-rehearsal-{name}",
            "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
            "date": "2026-10-15", "selector": selector, "scope": ["site", "dataset", "internal"],
            "applies_to": {"reharvest": True, "rollback": True}}]}
        withdrawn = wa.build(inputs, suppressions)
        stable = wa.build(inputs, suppressions)  # rollback: same previous inputs, selectors still applied
        lifted = wa.build(inputs, None)
        reached = withdrawn["takedown"][0]
        suppressed_ids = set(reached["assertions"])
        leaks = 0
        field_changes = Counter()
        for card_id in reached["cards"]:
            before, after = baseline["cards"][card_id], withdrawn["cards"][card_id]
            public = public_projection(after)
            text = json.dumps(public, ensure_ascii=False)
            for a in after["assertions"]:
                if a["assertion_id"] in suppressed_ids:
                    leaks += a["locator"] in text or any(
                        a["assertion_id"] in v["assertion_ids"] for f in (*public["fields"].values(),
                        *(x for s in public["senses"] for x in s["fields"].values())) for v in f["values"])
            for field, resolution in before["fields"].items():
                now = public["fields"].get(field)
                if now is None or now["state"] != resolution["state"]:
                    field_changes[f"{field}:{resolution['state']}->{now['state'] if now else 'absent'}"] += 1
            leaks += any(a.get("value") is not None and a.get("status") == "suppressed" and "value" in a
                         for a in public["assertions"] if set(a) != {"assertion_id", "status", "suppression_ref"})
        out["scenarios"][name] = {
            "assertions_suppressed": len(suppressed_ids),
            "cards_reached": reached["cards"],
            "field_state_changes": dict(field_changes),
            "suppressed_values_in_public_projection": leaks,
            "card_states": dict(Counter(c["state"] for c in withdrawn["cards"].values())),
            "rebuild_with_selectors_identical": _digest(withdrawn) == _digest(stable),
            "lifted_selector_restores_baseline": _digest(lifted) == _digest(baseline),
            "withdrawn_differs_from_baseline": _digest(withdrawn) != _digest(baseline),
        }
    out["passed"] = bool(out["scenarios"]) and all(
        s["assertions_suppressed"] > 0 and s["suppressed_values_in_public_projection"] == 0
        and s["rebuild_with_selectors_identical"] and s["lifted_selector_restores_baseline"]
        and s["withdrawn_differs_from_baseline"] for s in out["scenarios"].values())
    return out


def _digest(result: dict) -> str:
    return foundation.digest({k: result["cards"][k] for k in sorted(result["cards"])})
