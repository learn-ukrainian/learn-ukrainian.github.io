"""Independent integrity checks and takedown rehearsal for assembled pilot cards (#8981).

`verify` re-audits its inputs against the frozen identity allocation, checks every supplied card's identity, senses
and sense maps against that allocation, re-reads every cited locator from the held sources (read-only),
re-authenticates derived ULIF forms against the held raw pages and re-derives what it can from the frozen inputs; it
does not trust the assembler's bookkeeping and never rebuilds the output it checks. Retained evidence is checked
whole: suppressed assertions keep their identity, record, register and locator and must be accounted for by the
takedown report, while the public projection must carry them only as tombstones. `rehearse` runs the withdrawal /
rollback contract of schema.md §12-§13: selectors reach the same assertions in any order, structured values are
withdrawn by their exact proposition, a withdrawn build verifies, the rebuild under the same selectors is stable,
and lifting the selectors restores the previous bytes.

Neither command certifies linguistic correctness: a green run proves mechanics, never meaning.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas.allocate_pilot_identities import label_pos
from scripts.atlas.word_card_resolver import aid, card_version, public_projection, resolve

SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "word-card-v1.schema.json"
DISPOSITIONS = frozenset({
    "asserted", "held", "source_absent", "not_in_frozen_inputs", "not_applicable", "unresolved",
})
LOCATOR = re.compile(r"^(?P<head>[a-z0-9_]+(?::[a-z0-9_]+)*:(?:id|entry):\d+|atlas0:enrichment:[^ ]+)"
                     r"(?::slot:(?P<slot>[A-Za-z0-9_.]+))?(?: \[(?P<part>.+)\])?$")
TOMBSTONE_KEYS = {"assertion_id", "status", "suppression_ref"}


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
        """The cited rows must be authenticated rows of the entry (held raw page parse), in exactly this slot."""
        if self.sources.forms_status(entry_id) is not None:
            return "forms_unauthenticated"
        value = a["value"]
        rows = {r["id"]: r for r in self.sources.forms(entry_id)}
        if not set(value["row_ids"]) <= set(rows):
            return "row_missing"
        cited = [rows[i] for i in value["row_ids"]]
        for row in cited:
            row_slot = src.ulif_slot(json.loads(row["grammatical_tags"]))
            if row["is_lemma"] or row_slot is None or src.slot_name(row_slot) != slot:
                return "value_mismatch"
        stressed = sorted({src.nfc(r["form_stressed"]) for r in cited if not r["marked_asterisk"]})
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
                return None if (wa.vesum_aspect(rows) == value) else "value_mismatch"
        if part.startswith("slot "):
            # Exactly the forms of the rows printing these tags: a slot never drops or adds a VESUM form.
            tags = set(value["tags"])
            if not tags <= {r["tags"] for r in rows}:
                return "value_mismatch"
            forms = {src.nfc(r["word_form"]) for r in rows if r["tags"] in tags}
            return None if forms == set(value["forms"]) else "value_mismatch"
        return "locator_part"


def squeezed(text: str) -> str:
    return wa.squeeze(text)


def relation_conservation(inputs: wa.Inputs, cards: dict) -> dict:
    """Every accepted C3 relation unit appears exactly once, on the sense the one-unit rule or the registry's
    `unsplit` holding sense names, with its payload, locator and source record; none sits on a card subject."""
    errors, total, aligned, held = Counter(), 0, 0, 0
    placed = Counter()
    for card in cards.values():
        for a in card["assertions"]:
            if a["field"] in wa.RELATION_FIELDS and a["source_id"] == "ulif":
                if a["subject"]["kind"] != "sense":
                    errors["card_subject"] += 1
                placed[(card["card_id"], a["field"], a["locator"].split(" ")[0])] += 1
    seen = set()
    for unit in inputs.units:
        if unit["entry_type"] != "lexeme_candidate":
            continue
        entry = inputs.entry_by_unit[unit["unit_key"]]
        card = cards[entry["card_id"]]
        by_kind = wa.relation_units(inputs.wp3_units, inputs.records[unit["anchor_locator"]]["raw_row"]["id"])
        for kind, units in by_kind.items():
            target = wa.aligned_sense(entry["senses"], units)
            for u in units:
                if u.candidate.outcome != "accepted":
                    continue
                total += 1
                locator = f"ulif:ulif_dictua_sections:id:{u.source_key.rpartition('=')[2]}"
                key = (card["card_id"], kind, locator)
                seen.add(key)
                found = [a for a in card["assertions"] if a["field"] == kind and a["locator"].split(" ")[0] == locator]
                if len(found) != 1 or placed[key] != 1:
                    errors["not_exactly_once"] += 1
                    continue
                a = found[0]
                members = next(v for v in u.candidate.response if v.slot == "members")
                errors["payload"] += a["value"]["members"] != members.text
                expected = target or wa.holding_sense(entry["senses"])
                errors["placement"] += expected is None or a["subject"] != {"kind": "sense", "id": expected["sense_id"]}
                errors["mapping"] += a["mapping"]["confidence"] != ("high" if target else "unresolved")
                aligned += target is not None
                held += target is None
    errors["unexpected"] += sum(1 for key in placed if key not in seen)
    return {"passed": not any(errors.values()), "units": total, "aligned": aligned, "held_unsplit": held,
            "errors": {k: v for k, v in errors.items() if v}}


def live_relation_maps(card: dict) -> dict[str, list[dict]]:
    """Sense id -> the sense-map units its LIVE relation assertions justify, read from the supplied card only."""
    by_sense = defaultdict(list)
    for a in card["assertions"]:
        if a["subject"]["kind"] == "sense" and a["field"] in wa.RELATION_FIELDS and a["status"] == "active":
            section = re.search(r"id:(\d+)", a["locator"]).group(1)
            rule = wa.SENSE_RULE_ALIGNED if a["mapping"]["confidence"] == "high" else wa.SENSE_RULE_HOLDING
            unit = {"source_id": "ulif", "source_sense_key": f"ulif:section:{section}", "mapped_by": rule}
            if unit not in by_sense[a["subject"]["id"]]:
                by_sense[a["subject"]["id"]].append(unit)
    return {k: sorted(v, key=lambda u: u["source_sense_key"]) for k, v in by_sense.items()}


def identity_binding(inputs: wa.Inputs, cards: dict) -> dict:
    """Every supplied card against the freshly audited allocation (#8981 R3-F1), never against a rebuilt output.

    The card inventory is exactly the allocated cards under their own ids; each card keeps its allocated kind,
    complete creation key, redirects and its registry senses (ids, order, state) with the seed provenance and
    registry sense-map units their mint evidence names. Live sense-map units are exactly those the card's live
    relation assertions justify, and every assertion's subject is the card or one of its own senses. `inventory`,
    `dictionary_key` and `malformed` mean the per-card checks below cannot address the cards.
    """
    errors = Counter()
    expected = {inputs.entry_by_unit[u["unit_key"]]["card_id"]: inputs.entry_by_unit[u["unit_key"]]
                for u in inputs.units}
    try:
        errors["inventory"] += set(cards) != set(expected)
        errors["dictionary_key"] += sum(card["card_id"] != key for key, card in cards.items())
        for card_id, entry in expected.items():
            card = cards.get(card_id)
            if card is None:
                continue
            errors["card_kind"] += card["card_kind"] != entry["card_kind"]
            errors["key_at_creation"] += card["key_at_creation"] != entry["key_at_creation"]
            errors["redirect"] += (card["merged_into"], card["split_into"]) != (
                entry.get("merged_into"), entry.get("split_into"))
            errors["sense_inventory"] += [(s["sense_id"], s["order"], s["state"]) for s in card["senses"]] != [
                (s["sense_id"], s["order"], s["state"]) for s in entry["senses"]]
            owned = {s["sense_id"] for s in entry["senses"]}
            live = live_relation_maps(card)
            for row in card["senses"]:
                event = inputs.sense_events.get(row["sense_id"]) if row["sense_id"] in owned else None
                if event is None:
                    errors["sense_owner"] += 1
                    continue
                errors["redirect"] += row["merged_into"] is not None
                seeded = event["source_unit"] if row["state"] == "active" and event.get("literal_gloss_unit") else None
                errors["seeded_from"] += row.get("seeded_from") != (seeded and "ulif_sense_gloss:" + seeded)
                source = "ulif" if event["source_unit"].startswith("ulif:") else "frazeolohichnyi"
                registry_units = [{"source_id": source, "source_sense_key": event["source_unit"],
                                   "mapped_by": "registry:" + event.get("rules_version", "")}]
                errors["registry_sense_map"] += [
                    u for u in row["sense_map"] if u["mapped_by"].startswith("registry:")] != registry_units
                errors["live_sense_map"] += [
                    u for u in row["sense_map"] if not u["mapped_by"].startswith("registry:")] != live.get(
                    row["sense_id"], [])
            errors["live_sense_map"] += bool(set(live) - {s["sense_id"] for s in card["senses"]})
            errors["assertion_subject"] += sum(
                not ((a["subject"]["kind"] == "card" and a["subject"]["id"] == card_id)
                     or (a["subject"]["kind"] == "sense" and a["subject"]["id"] in owned))
                for a in card["assertions"])
    except (KeyError, TypeError, AttributeError):  # a card without the fields its identity needs
        errors["malformed"] += 1
    return {"passed": not any(errors.values()), "errors": {k: v for k, v in errors.items() if v}}


UNADDRESSABLE = frozenset({"inventory", "dictionary_key", "malformed"})


def matched_vesum_entry(inputs: wa.Inputs, unit: dict) -> int | None:
    """Re-derive identity.md §4's entry from the allocated unit and held sources, never the supplied card."""
    if unit["entry_type"] != "lexeme_candidate":
        return None
    entry = inputs.entry_by_unit[unit["unit_key"]]
    raw = inputs.records[unit["anchor_locator"]]["raw_row"]
    proper = entry["card_kind"] == "proper_name"
    homonyms = wa.class_homonyms(inputs, raw, unit, proper)
    keep_gender = any(len(slot) > 1 and any(t in src.GENDERS for t in slot)
                      for h in homonyms.values() if h["paradigm"] for slot in h["paradigm"]["slots"])
    key = entry["key_at_creation"]
    rows = inputs.sources.vesum_forms(key["spelling"])
    entries = src.vesum_paradigm([r for r in rows if r["pos"] == key["pos"]], keep_gender)
    candidates = {eid: e for eid, e in entries.items() if ("prop" in e["flags"]) == proper}
    return src.match_identity(raw["id"], homonyms, candidates)["vesum_entry"]


def source_routes(inputs: wa.Inputs, unit: dict, entry: dict, assertion: dict) -> list[tuple[str, str, str]]:
    """Permitted (locator head, frozen record locator, assertion snapshot) for an allocated subject.

    Start at creation/mint evidence, never the supplied locator or record id. Derived forms and section
    extracts have their own snapshots and can cite an entry record rather than the extracted section.
    VESUM is supplemental evidence with no persistent record in this allocation.
    """
    source, field = assertion["source_id"], assertion["field"]
    anchor = inputs.records[unit["anchor_locator"]]
    own = [inputs.records[k] for k in unit["source_record_keys"]]
    if source in {"puls", "ukrainian_word_stress", "frazeolohichnyi"}:
        permitted = {"puls": "cefr", "ukrainian_word_stress": "stress", "frazeolohichnyi": "mwe_form"}
        return [(r["locator"], r["locator"], r["snapshot_id"]) for r in own
                if r["source_id"] == source and field == permitted[source]
                and (source != "puls" or wa.puls_matches_identity(
                    r["raw_row"], entry["key_at_creation"]["spelling"], entry["card_kind"] == "proper_name",
                    anchor["raw_row"].get("grammatical_label", "")))
                and assertion["subject"] == {"kind": "card", "id": entry["card_id"]}]
    if source != "ulif":
        return []
    if unit["entry_type"] == "lexeme_candidate":
        entry_id = anchor["raw_row"]["id"]
        if field in {"spelling", "stress", "pos", "grammatical_label", "gender", "aspect"}:
            if assertion["subject"] != {"kind": "card", "id": entry["card_id"]}:
                return []
            record = anchor
            if field in {"spelling", "stress"} and not anchor["raw_row"]["canonical_headword"]:
                record = next(r for r in own if r["table"] == "ulif_dictua_sections")
            return [(record["locator"], record["locator"], anchor["snapshot_id"])]
        if field == "sense_label":
            event = inputs.sense_events.get(assertion["subject"]["id"], {})
            index = re.search(r"sense_gloss\[(\d+)\]$", event.get("source_unit", ""))
            if assertion["subject"]["kind"] != "sense" or not index:
                return []
            locator = f"{anchor['locator']} [sense_gloss[{index.group(1)}]]"
            return [(locator, anchor["locator"], anchor["snapshot_id"])]
        if field == "paradigm":
            if assertion["subject"] != {"kind": "card", "id": entry["card_id"]}:
                return []
            record = next((r for r in own if r["table"] == "ulif_dictua_sections"), anchor)
            snapshot = "ulif-forms@sha256:" + foundation.digest(inputs.sources.forms(entry_id))
            return [(f"ulif:ulif_forms:entry:{entry_id}", record["locator"], snapshot)]
        if field in wa.RELATION_FIELDS:
            return [(f"ulif:ulif_dictua_sections:id:{u.source_key.rpartition('=')[2]}", anchor["locator"],
                     "ulif-section@sha256:" + next(v for v in u.candidate.response
                                                   if v.slot == "members").citations[0].field_sha256)
                    for u in inputs.wp3_units if u.parent_key == f"ulif_dictua_entries:id={entry_id}"
                    and u.candidate.operation == field and u.candidate.outcome == "accepted"]
        return []
    if field not in {"mwe_form", "definition_uk", "examples"}:
        return []
    subject = {"kind": "card", "id": entry["card_id"]} if field == "mwe_form" else {
        "kind": "sense", "id": entry["senses"][0]["sense_id"]}
    if assertion["subject"] != subject:
        return []
    # A same-spelling idiom alone is insufficient: its definition and quotation must be in this frozen body.
    body = wa.squeeze(wa.strip_aggregator_markup(anchor["raw_row"]["definition"]))
    routes = []
    for u in inputs.wp3_units:
        c = u.candidate
        if c.operation != "idiom_definition" or c.outcome != "accepted":
            continue
        idiom = next((v for v in c.slots if v.slot == "idiom"), None)
        definition = next((v for v in c.response if v.slot == "definition"), None)
        citations = [v for v in c.response if v.slot == "citation"]
        if idiom is None or definition is None or wa.normalize_mwe_form(idiom.text) != wa.normalize_mwe_form(
                unit["literal_head"]) or wa.squeeze(definition.text) not in body or not any(
                wa.squeeze(v.text) in body for v in citations):
            continue
        routes.append((f"ulif:ulif_dictua_sections:id:{u.source_key.rpartition('=')[2]}",
                       f"ulif:ulif_dictua_entries:id:{u.parent_key.rpartition('=')[2]}",
                       "ulif-section@sha256:" + definition.citations[0].field_sha256))
    return routes


def _stored_proposition(field: str, value_norm: str, structured: bool, normalise) -> tuple | str:
    """A proposition read from a STORED `value_norm` (the assembler regenerates it from the raw value instead):
    a paradigm slot is its slot plus its unstressed form set, a declared set its member set, else the text."""
    if field == "paradigm":
        slot, _, forms = value_norm.partition("=")
        return slot, frozenset(normalise(src.unstressed(f)) for f in forms.split("|"))
    if structured:
        return frozenset(normalise(m) for m in value_norm.split("|"))
    return normalise(value_norm)


def intended_matches(selector: dict, inventory: dict, records: dict) -> set[str] | None:
    """The assertion ids a declared selector is meant to reach, worked out independently of the assembler from
    the original inventory (`assertion_id -> (assertion, card spelling)`) and the registry's source records.
    None when the selector is inconsistent or unevaluable, which no withdrawn build may carry."""
    kind = selector["kind"]
    if kind == "source":
        return {i for i, (a, _) in inventory.items() if a["source_id"] == selector["source_id"]}
    if kind == "source_record":
        record = records.get(selector["source_record_id"])
        if record is None or record["source_id"] != selector["source_id"] or (
                "alias_at_creation" in selector
                and selector["alias_at_creation"] not in {x["key"] for x in record["aliases"]}):
            return None
        return {i for i, (a, _) in inventory.items() if a["source_id"] == selector["source_id"]
                and a.get("source_record_id") == selector["source_record_id"]}
    if kind == "assertion_id":
        fallback = intended_matches(selector["fallback"], inventory, records)
        if selector["assertion_id"] not in inventory:
            return fallback
        # While the id exists it alone is withdrawn, and its fallback must describe it.
        return {selector["assertion_id"]} if fallback and selector["assertion_id"] in fallback else None
    if kind == "assertion_content":
        normalise = wa.NORMALISERS.get(selector["normaliser_version"])
        if normalise is None:
            return None
        out = set()
        for i, (a, spelling) in inventory.items():
            if (a["source_id"], a["field"]) != (selector["source_id"], selector["field"]) or \
                    src.nfc(spelling) != src.nfc(selector["subject_spelling"]):
                continue
            structured = isinstance(a["value"], list)
            if "value_norm" not in selector or _stored_proposition(
                    a["field"], selector["value_norm"], structured, normalise) == _stored_proposition(
                    a["field"], a["value_norm"], structured, normalise):
                out.add(i)
        return out
    return None


def withdrawal(cards: dict, takedown: list[dict], suppressions: dict | None, source_records: list[dict],
               record_bindings: dict[str, str] | None = None) -> dict:
    """Suppressed provenance: every suppressed assertion is credited by the takedown entry it names, every
    credited assertion is retained and suppressed, the takedown covers exactly the declared selectors, and each
    selector reached exactly the assertions it was meant to (`intended_matches`, worked out independently)."""
    errors = Counter()
    entries = {t["suppression_id"]: t for t in takedown}
    declared = (suppressions or {}).get("entries", [])
    errors["takedown_vs_selectors"] += sorted(entries) != sorted(e["suppression_id"] for e in declared)
    inventory = {a["assertion_id"]: (dict(a, source_record_id=record_bindings.get(a["assertion_id"]))
                                   if record_bindings is not None else a, card["key_at_creation"]["spelling"])
                 for card in cards.values() for a in card["assertions"]}
    records = {sr["source_record_id"]: sr for sr in source_records}
    intended_union = set()
    for e in declared:
        intended = intended_matches(e["selector"], inventory, records)
        errors["selector_inconsistent"] += intended is None
        intended = intended or set()
        intended_union |= intended
        credited = entries.get(e["suppression_id"], {})
        errors["selector_scope"] += set(credited.get("assertions", [])) != intended
    errors["suppressed_outside_selectors"] += {
        i for i, (a, _) in inventory.items() if a["status"] == "suppressed"} != intended_union
    retained = {}
    for card in cards.values():
        for a in card["assertions"]:
            retained[(card["card_id"], a["assertion_id"])] = a
            if a["status"] == "suppressed":
                entry = entries.get(a.get("suppression_ref"))
                errors["unknown_suppression_ref"] += entry is None
                if entry is not None:
                    errors["ref_not_credited"] += a["assertion_id"] not in entry["assertions"]
                    errors["ref_not_smallest"] += a["suppression_ref"] != min(
                        t for t, e in entries.items() if a["assertion_id"] in e["assertions"]
                        and card["card_id"] in e["cards"])
            elif a["status"] != "active":
                errors["status"] += 1
    for entry in takedown:
        reached = [retained.get((c, i)) for c in entry["cards"] for i in entry["assertions"]
                   if (c, i) in retained]
        errors["credited_missing"] += len({i for i in entry["assertions"]} - {a["assertion_id"] for a in reached})
        errors["credited_active"] += sum(1 for a in reached if a["status"] != "suppressed")
        errors["empty_selector"] += not entry["assertions"]
    return {"passed": not any(errors.values()), "suppressed": sum(a["status"] == "suppressed" for a in retained.values()),
            "selectors": len(takedown), "errors": {k: v for k, v in errors.items() if v}}


def public_tombstones(card: dict) -> list[str]:
    """Independent checks of one card's public projection; returns closed reason codes."""
    public = public_projection(card)
    problems = []
    suppressed = {a["assertion_id"]: a for a in card["assertions"] if a["status"] == "suppressed"}
    live = {a["assertion_id"] for a in card["assertions"] if a["status"] == "active"}
    if not suppressed:
        return [] if foundation.digest(public) == foundation.digest(card) else ["untouched_card_differs"]
    for a in public["assertions"]:
        if a["assertion_id"] in suppressed:
            if set(a) != TOMBSTONE_KEYS or a["suppression_ref"] != suppressed[a["assertion_id"]]["suppression_ref"]:
                problems.append("tombstone_shape")
        elif a["assertion_id"] not in live:
            problems.append("unknown_assertion")
    if {a["assertion_id"] for a in public["assertions"]} != set(suppressed) | live:
        problems.append("assertion_inventory")
    resolutions = [*public["fields"].items(), *((f, r) for s in public["senses"] for f, r in s["fields"].items())]
    for _field, res in resolutions:
        cited = {i for v in res["values"] for i in v["assertion_ids"]}
        selected = res["selected"] if isinstance(res["selected"], list) else [res["selected"]] if res["selected"] else []
        if (cited | set(selected)) & set(suppressed):
            problems.append("withdrawn_value_in_resolution")
    for field in public["fields"]:
        survivors = [a for a in card["assertions"] if a["status"] == "active"]
        if survivors and public["fields"][field] != resolve(card["assertions"], field, card["card_id"]) | (
                {"level_policy": public["fields"][field]["level_policy"]} if "level_policy" in public["fields"][field]
                else {}):
            problems.append("resolution_not_recomputed")
    text = json.dumps({k: v for k, v in public.items() if k != "assertions"}, ensure_ascii=False)
    for a in suppressed.values():
        if a["locator"] in text:
            problems.append("withdrawn_locator_in_public")
        if a["field"] in wa.RELATION_FIELDS and any(
                f"ulif:section:{re.search(r'id:(\d+)', a['locator']).group(1)}" == u["source_sense_key"]
                and not u["mapped_by"].startswith("registry:") for s in public["senses"] for u in s["sense_map"]):
            problems.append("withdrawn_unit_in_sense_map")
    for link in public["links"]:
        if link["state"] == "active" and set(link["assertion_ids"]) & set(suppressed):
            problems.append("link_on_withdrawn_evidence")
    if public["build"]["card_version"] != card_version(public):
        problems.append("card_version")
    if (public["state"] == "suppressed") != (not live):
        problems.append("card_state")
    return sorted(set(problems))


def verify(inputs: wa.Inputs, result: dict, again: dict | None = None, suppressions: dict | None = None) -> dict:
    """Run every integrity check; returns {check: {passed, ...}} and never raises on a failed check.

    Inputs whose allocation or views differ from the frozen allocation give one failed `input_allocation` check and
    nothing else; supplied cards that cannot be addressed by their allocated ids stop after `identity_binding`.
    """
    try:
        inputs.check_allocation()
    except foundation.Refusal:
        return {"input_allocation": {"passed": False, "errors": {"allocation_refused": 1}}, "passed": False}
    cards = result["cards"]
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    report: dict = {"input_allocation": {"passed": True}}

    schema_errors = Counter()
    for card in cards.values():
        for error in validator.iter_errors(card):
            schema_errors[error.message[:80]] += 1
    report["schema"] = {"passed": not schema_errors, "cards": len(cards), "errors": dict(schema_errors)}
    report["identity_binding"] = identity_binding(inputs, cards)
    if UNADDRESSABLE & set(report["identity_binding"]["errors"]):
        report["passed"] = False
        return report

    unit_cards = {inputs.entry_by_unit[u["unit_key"]]["card_id"] for u in inputs.units}
    senses_ok = all(
        [s["sense_id"] for s in c["senses"]] == [s["sense_id"] for e in inputs.registry["entries"]
                                                  if e["card_id"] == c["card_id"] for s in e["senses"]]
        for c in cards.values())
    report["conservation"] = {
        "passed": set(cards) == unit_cards and len(cards) == len(inputs.units) and senses_ok
        and set(result["ledger"].cards) == unit_cards,
        "units": len(inputs.units), "cards": len(cards), "ledger_cards": len(result["ledger"].cards),
    }
    report["relation_units"] = relation_conservation(inputs, cards)

    registry_sr = {sr["source_record_id"]: sr for sr in inputs.registry["source_records"]}
    # Each frozen row's persistent record, read from the registry's correspondence in the row's OWN snapshot.
    binding = {}
    for record in inputs.manifest["selection"]["source_records"]:
        owners = [sr for sr in inputs.registry["source_records"] if sr["source_id"] == record["source_id"] and any(
            c["snapshot_id"] == record["snapshot_id"] and c.get("locator") == record["locator"]
            and c["status"] == "unique" for c in sr["correspondence"])]
        binding[record["locator"]] = (owners[0]["source_record_id"], record["snapshot_id"]) if len(owners) == 1 else None
    id_errors, register_errors, lineage_errors, sr_errors, forbidden = Counter(), Counter(), Counter(), Counter(), 0
    cited_records, record_bindings = set(), {}
    unit_of = {inputs.entry_by_unit[u["unit_key"]]["card_id"]: u for u in inputs.units}
    for card in cards.values():
        unit = unit_of[card["card_id"]]
        vesum_entry = matched_vesum_entry(inputs, unit) if any(
            a["source_id"] == "vesum" for a in card["assertions"]) else None
        # Retained evidence is checked whole: a suppressed assertion keeps its identity, record and lineage.
        for a in card["assertions"]:
            expected = aid(a["source_id"], a["snapshot_id"], a["locator"], a["subject"], a["field"], a["value_norm"],
                           a["extraction_version"])
            id_errors["id"] += expected != a["assertion_id"]
            register_errors["source"] += a["source_id"] not in inputs.register
            register_errors["version"] += a["licence_ref"]["register_version"] != inputs.register_version
            group, tier = wa.LINEAGE[a["source_id"]]
            lineage_errors["lineage"] += (a["independence_group"], a["tier"]) != (group, tier)
            if a["source_id"] == "vesum":
                sr_errors["locator_outside_subject"] += not a["locator"].startswith("vesum:entry:") or (
                    a["subject"] != {"kind": "card", "id": card["card_id"]}) or card["card_kind"] == "mwe"
                sr_errors["snapshot_binding"] += a["snapshot_id"] != "vesum@" + inputs.hashes["vesum_canonical"][:16]
                sr_errors["unexpected_attribution"] += "source_record_id" in a or "source_record_key" in a
                match = LOCATOR.fullmatch(a["locator"])
                sr_errors["vesum_entry_mismatch"] += vesum_entry is None or match is None or (
                    match.group("head") != f"vesum:entry:{vesum_entry}")
            else:
                routes = source_routes(inputs, unit, inputs.entry_by_unit[unit["unit_key"]], a)
                match = LOCATOR.fullmatch(a["locator"])
                head = match.group("head") if match else None
                routes = sorted({r for r in routes if r[0] in {head, a["locator"]}})
                sr_errors["locator_outside_subject"] += len(routes) != 1
                sr_errors["missing_attribution"] += not a.get("source_record_id") or not a.get("source_record_key")
                if len(routes) == 1:
                    _, record_locator, snapshot = routes[0]
                    bound = binding.get(record_locator)
                    sr_errors["unbound_frozen_row"] += bound is None
                    if bound:
                        record_bindings[a["assertion_id"]] = bound[0]
                        sr_errors["snapshot_binding"] += (a.get("source_record_id"), a["snapshot_id"]) != (
                            bound[0], snapshot)
                        sr_errors["key_outside_snapshot"] += a.get("source_record_key") not in {
                            x["key"] for x in registry_sr[bound[0]]["aliases"] if x["snapshot_id"] == bound[1]}
            if a.get("source_record_id"):
                cited_records.add(a["source_record_id"])
                sr_errors["unknown"] += a["source_record_id"] not in registry_sr
                sr_errors["source"] += registry_sr.get(a["source_record_id"], {}).get("source_id") != a["source_id"]
            forbidden += a["source_id"] == "sum11" and a["field"] != "russification_exposed"
    report["assertion_identity"] = {"passed": not any(id_errors.values()), "errors": dict(id_errors)}
    report["register_lineage"] = {"passed": not any(register_errors.values()) and not any(lineage_errors.values()),
                                  "errors": {**register_errors, **lineage_errors}}
    frozen = {bound[0] for bound in binding.values() if bound}
    sr_errors["unbound_frozen_row"] += sum(bound is None for bound in binding.values())
    # A frozen record no assertion cites must be accounted for by a ledger hold naming it (refused evidence), and a
    # hold may name only a frozen record of the card's own allocated unit.
    held = set()
    for card_id, item in result["ledger"].cards.items():
        own = {binding[k][0] for k in unit_of[card_id]["source_record_keys"] if binding.get(k)} \
            if card_id in unit_of else set()
        for h in item["held"]:
            if h.get("source_record_id"):
                held.add(h["source_record_id"])
                sr_errors["held_unbound"] += h["source_record_id"] not in own
    report["source_records"] = {"passed": not any(sr_errors.values()) and frozen <= cited_records | held
                                and not forbidden,
                                "frozen": len(frozen), "cited": len(frozen & cited_records),
                                "held": len((frozen - cited_records) & held),
                                "errors": dict(sr_errors), "sum11_outside_russification": forbidden}

    resolver = Resolver(inputs)
    locator_errors = Counter()
    checked = 0
    for card in cards.values():
        for a in card["assertions"]:
            checked += 1
            problem = resolver.check(card, a)
            if problem:
                locator_errors[f"{a['source_id']}:{a['field']}:{problem}"] += 1
    report["locators"] = {"passed": not locator_errors, "checked": checked, "errors": dict(locator_errors)}

    report["withdrawal"] = withdrawal(cards, result["takedown"], suppressions, inputs.registry["source_records"],
                                      record_bindings)
    report["withdrawal"]["source_bindings_valid"] = report["source_records"]["passed"]
    report["withdrawal"]["passed"] &= report["source_records"]["passed"]
    withdrawn_fields = {f for t in result["takedown"] for f in t["fields"]}
    ledger_errors = Counter()
    for card_id, item in result["ledger"].cards.items():
        card = cards[card_id]
        fields = set(item["fields"])
        kind = "mwe" if card["card_kind"] == "mwe" else "lexeme"
        required = set((wa.MWE_FIELDS if kind == "mwe" else wa.CARD_FIELDS) + wa.SENSE_FIELDS)
        ledger_errors["missing_field"] += len(required - fields)
        retained = {a["field"] for a in card["assertions"]}
        live = {a["field"] for a in card["assertions"] if a["status"] == "active"}
        for name, d in item["fields"].items():
            ledger_errors["bad_disposition"] += d["disposition"] not in DISPOSITIONS
            if d["disposition"] == "asserted":
                # Extraction accounting stays; a field whose every assertion was withdrawn must be in the takedown.
                ledger_errors["asserted_without_assertion"] += name not in retained
                ledger_errors["withdrawn_unaccounted"] += name in retained and name not in live and \
                    f"{card_id}:{name}" not in withdrawn_fields
    report["ledger"] = {"passed": not any(ledger_errors.values()), "errors": dict(ledger_errors)}

    if again is not None:
        first = {k: foundation.digest(v) for k, v in cards.items()}
        second = {k: foundation.digest(v) for k, v in again["cards"].items()}
        report["determinism"] = {"passed": first == second and result["build_id"] == again["build_id"],
                                 "cards": len(first)}

    projection = Counter()
    for card in cards.values():
        for problem in public_tombstones(card):
            projection[problem] += 1
    report["public_projection"] = {"passed": not projection, "errors": dict(projection),
                                   "withdrawn_cards": sum(1 for c in cards.values() if any(
                                       a["status"] == "suppressed" for a in c["assertions"]))}
    report["passed"] = all(v["passed"] for v in report.values() if isinstance(v, dict))
    return report


def _semantic(result: dict) -> str:
    """Card content without the build block: equal whenever the same assertions are withdrawn the same way."""
    return foundation.digest({k: {f: v for f, v in c.items() if f != "build"} for k, c in sorted(result["cards"].items())})


def _suppression(name: str, selector: dict) -> dict:
    return {"suppression_id": f"sup-rehearsal-{name}",
            "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
            "date": "2026-10-15", "selector": selector, "scope": ["site", "dataset", "internal"],
            "applies_to": {"reharvest": True, "rollback": True}}


def rehearsal_selectors(inputs: wa.Inputs, baseline: dict) -> list[tuple[str, list[dict]]]:
    """The rehearsal scenarios: record and source withdrawals, an overlapping pair, structured content selectors
    (a declared stress set and a paradigm slot) and an assertion-id selector whose id no longer exists."""
    scenarios = []
    rehearsal_units = [u for u in inputs.units if "withdrawal_rehearsal_candidate" in u["categories"]]
    record_entries = []
    for number, unit in enumerate(rehearsal_units, start=1):
        record = inputs.record_ids[("ulif", unit["anchor_locator"])]
        record_entries.append(_suppression(f"source_record-{number}", {
            "kind": "source_record", "source_id": "ulif", "source_record_id": record["source_record_id"],
            "alias_at_creation": record["aliases"][0]["key"], "on_ambiguous": "suppress_all_candidates"}))
    if record_entries:
        scenarios.append(("source_record", record_entries))
        whole = _suppression("ulif", {"kind": "source", "source_id": "ulif"})
        scenarios.append(("overlap_source_then_record", [whole, record_entries[0]]))
        scenarios.append(("overlap_record_then_source", [record_entries[0], whole]))
    scenarios.append(("source", [_suppression("source", {"kind": "source", "source_id": "ukrainian_word_stress"})]))
    cards = sorted(baseline["cards"].values(), key=lambda c: c["card_id"])
    structured = {
        "content_stress_set": next(((c, a) for c in cards for a in c["assertions"]
                                    if a["field"] == "stress" and isinstance(a["value"], list)), None),
        "content_paradigm_slot": next(((c, a) for c in cards for a in c["assertions"]
                                       if a["field"] == "paradigm" and a["source_id"] == "ulif"), None),
    }
    for name, found in structured.items():
        if found is None:
            continue
        card, a = found
        content = {"kind": "assertion_content", "source_id": a["source_id"], "field": a["field"],
                   "subject_spelling": card["key_at_creation"]["spelling"], "value_norm": a["value_norm"],
                   "normaliser_version": inputs.manifest["normaliser_version"]}
        scenarios.append((name, [_suppression(name, content)]))
        if name == "content_paradigm_slot":
            # An assertion id that no longer exists (re-extraction changed it): the pinned content still withdraws.
            scenarios.append(("assertion_id_fallback", [_suppression("id-fallback", {
                "kind": "assertion_id", "assertion_id": "wa_" + "0" * 24, "fallback": content})]))
    return scenarios


def rehearse(inputs: wa.Inputs) -> dict:
    """Withdrawal and rollback rehearsal against the frozen pilot (schema.md §12-§13, #8980 contract)."""
    baseline = wa.build(inputs)
    scenarios = rehearsal_selectors(inputs, baseline)
    out = {"units": [u["unit_key"] for u in inputs.units if "withdrawal_rehearsal_candidate" in u["categories"]],
           "scenarios": {}}
    for name, entries in scenarios:
        suppressions = {"schema_version": "1", "entries": entries}
        withdrawn = wa.build(inputs, suppressions)
        stable = wa.build(inputs, suppressions)  # rollback / reimport: same inputs, current selectors applied
        lifted = wa.build(inputs, None)
        checks = verify(inputs, withdrawn, stable, suppressions)
        suppressed_ids = {a["assertion_id"] for c in withdrawn["cards"].values() for a in c["assertions"]
                          if a["status"] == "suppressed"}
        out["scenarios"][name] = {
            "selectors": len(entries),
            "assertions_suppressed": len(suppressed_ids),
            "credited_per_selector": {t["suppression_id"]: len(t["assertions"]) for t in withdrawn["takedown"]},
            "cards_reached": sorted({c for t in withdrawn["takedown"] for c in t["cards"]}),
            "card_states": dict(Counter(c["state"] for c in withdrawn["cards"].values())),
            "withdrawn_build_verifies": checks["passed"],
            "verify_failures": sorted(k for k, v in checks.items() if isinstance(v, dict) and not v["passed"]),
            "rebuild_with_selectors_identical": _digest(withdrawn) == _digest(stable),
            "lifted_selector_restores_baseline": _digest(lifted) == _digest(baseline),
            "withdrawn_differs_from_baseline": _semantic(withdrawn) != _semantic(baseline),
            "semantic_digest": _semantic(withdrawn),
        }
    pairs = [("overlap_source_then_record", "overlap_record_then_source")]
    out["order_independent"] = all(
        out["scenarios"][a]["semantic_digest"] == out["scenarios"][b]["semantic_digest"]
        for a, b in pairs if a in out["scenarios"])
    out["passed"] = bool(out["scenarios"]) and out["order_independent"] and all(
        s["assertions_suppressed"] > 0 and s["withdrawn_build_verifies"]
        and s["rebuild_with_selectors_identical"] and s["lifted_selector_restores_baseline"]
        and s["withdrawn_differs_from_baseline"] for s in out["scenarios"].values())
    return out


def _digest(result: dict) -> str:
    return foundation.digest({k: result["cards"][k] for k in sorted(result["cards"])})
