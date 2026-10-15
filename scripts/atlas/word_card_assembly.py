"""Pilot word-card assembly: `build(S, V, I, O, R)` over the frozen pilot inventory (#8981, schema.md §13).

Reads the admitted pilot manifest, the frozen identity registry, the held `sources.db` / `vesum.db` and the
permissions register; emits one schema-valid card per frozen unit plus a field-accounting ledger. Every Ukrainian
value is a verbatim source value with its exact locator; nothing is generated, translated or paraphrased.

Assembly never mints identities (it refuses ids the registry does not allocate), never writes to the sources, and
is deterministic: the same inputs give byte-identical cards. Cards are host-only build output; the writer refuses
a destination inside the repository that git does not ignore, so this module can commit no card data.

Exit codes of the CLI: 0 success, 1 source/data refusal, 2 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from contextlib import ExitStack
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import yaml

from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas.allocate_pilot_identities import (
    BUILD_PREFIX,
    is_proper_name,
    label_pos,
    normalize_mwe_form,
)
from scripts.atlas.word_card_resolver import CONF_ORDER, _project, _recompute, aid, card_version

ASSEMBLER_VERSION = "pilot-assembly-v1"
ALIAS_ORDER = ("uid", "register_position", "content", "query_headword_label", "vesum_entry_form", "table_row")
# Register source id -> (independence group, tier): schema.md §9.1 (lineage lives in R until the register records it).
# ukrainian_word_stress follows the register entry (ULIF-derived stress data, 2026-10-06): one lineage with ULIF.
LINEAGE = {
    "ulif": ("G-ULIF", 1),
    "frazeolohichnyi": ("G-ULIF", 1),
    "vesum": ("G-VESUM", 1),
    "puls": ("G-PULS", 2),
    "ukrainian_word_stress": ("G-ULIF", 2),
}
GENDER_WORDS = {"чоловічого": "m", "жіночого": "f", "середнього": "n"}
# ULIF label lead words that name a PULS part of speech (PULS prints «іменник», «дієслово (недок.)», «числівник»).
LABEL_HEADS = {"іменник", "прикметник", "прислівник", "дієслово", "числівник", "сполучник", "прийменник", "займенник"}
CARD_FIELDS = (
    "spelling", "stress", "pos", "grammatical_label", "gender", "aspect", "paradigm", "cefr", "frequency",
    "heritage_status", "transliteration", "english_gloss", "spelling_variants",
)
MWE_FIELDS = ("mwe_form", "mwe_frame", "cefr", "frequency", "heritage_status", "english_gloss")
SENSE_FIELDS = (
    "definition_uk", "gloss_en", "sense_label", "register", "synonyms", "antonyms", "examples",
    "russification_exposed", "collocations",
)
# WC-S requirement -> the card/sense fields that carry it (issue #8981 §word-card-source-coverage).
REQUIREMENT_FIELDS = {
    "WC-S01": ("definition_uk", "register", "pos", "grammatical_label", "synonyms", "antonyms"),
    "WC-S02": ("examples", "collocations", "frequency"),
    "WC-S03": ("spelling", "spelling_variants"),
    "WC-S04": ("heritage_status",),
    "WC-S05": ("heritage_status",),
    "WC-S06": ("cefr",),
    "WC-S07": ("stress", "paradigm"),
    "WC-S08": ("russification_exposed",),
    "WC-S09": ("synonyms", "antonyms", "definition_uk", "sense_label", "examples", "collocations"),
    "WC-S10": ("spelling", "stress", "pos", "paradigm", "cefr", "sense_label", "synonyms", "antonyms", "examples",
               "mwe_form"),
}
# Fields no frozen pilot input can supply. The reason is a closed vocabulary; it is never "absent from the world".
NOT_IN_FROZEN_INPUTS = {
    "frequency": "no corpus frequency source (ГРАК/UberText) is in the frozen pilot S",
    "heritage_status": "no heritage/etymology source (Грінченко, ЕСУМ) is in the frozen pilot S",
    "transliteration": "no register source produces it; the migrated atlas0 aliases are generator output",
    "english_gloss": "outside the data-first slice (WORD_CARDS_DATA_PLAN.md §3)",
    "gloss_en": "outside the data-first slice (WORD_CARDS_DATA_PLAN.md §3)",
    "spelling_variants": "no spelling-variant source (Правопис 2019) is in the frozen pilot S",
    "russification_exposed": "no СУМ-11 / Антоненко contrast adjudication is in the frozen pilot S",
    "collocations": "no collocation source is in the frozen pilot S",
    "register": "no register-label source (СУМ-20 / ВТС labels) is in the frozen pilot S",
    "mwe_frame": "slot words are not separable from the aggregator entry body without an extractor",
}


class AssemblyError(foundation.Refusal):
    """Fixed, privacy-safe diagnostics only."""


class MissingAllocation(AssemblyError):
    """A card, sense or source record the frozen registry does not allocate (schema.md §13)."""


def need(condition, message):
    if not condition:
        raise AssemblyError(message)


def squeeze(text: str) -> str:
    """Letters and digits only, case-folded: containment test that ignores markup, punctuation and stress."""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFC", text.replace(src.ACUTE, "")).casefold())


def strip_aggregator_markup(text: str) -> str:
    return re.sub(r"\[/?'\]", "", text)


# --- loading -------------------------------------------------------------------------------------------

class Inputs:
    """Everything `build` reads, loaded once and read-only."""

    def __init__(self, manifest, registry, register, sources, hashes, wp3_units, heldout="unverified"):
        self.manifest = manifest
        self.registry = registry
        self.register = {s["id"]: s for s in register["sources"]}
        self.register_version = register["schema_version"]
        self.sources = sources
        self.hashes = hashes
        self.wp3_units = wp3_units
        self.heldout = heldout
        self.records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
        self.units = manifest["selection"]["units"]
        build = BUILD_PREFIX + manifest["manifest_sha256"]
        self.entry_by_unit = {}
        for unit in self.units:
            matches = [e for e in registry["entries"]
                       if unit["unit_key"] in foundation.source_keys(e) and e["created_in_build"] == build]
            need(len(matches) == 1, "Pilot unit has no single allocated card; run allocation first")
            self.entry_by_unit[unit["unit_key"]] = matches[0]
        self.record_ids = {}
        for sr in registry["source_records"]:
            for correspondence in sr["correspondence"]:
                if correspondence.get("locator") and correspondence["status"] == "unique":
                    self.record_ids[(sr["source_id"], correspondence["locator"])] = sr
        self.sense_events = {}
        for event in registry["events"]:
            if event["kind"] == "sense_mint" and event["build_id"] == build:
                self.sense_events[event["to"][0]] = json.loads(event["evidence"])


def sha_of_file(path: Path) -> str:
    return foundation.file_digest(path)


def load_inputs(manifest_path, registry_path, register_path, sources_db, vesum_db, atlas_db, stack: ExitStack,
                scratch: Path, heldout_manifest=None):
    """Load and authenticate the frozen inputs. Source rows are re-read and compared to the frozen literal rows."""
    manifest = foundation.load(manifest_path)
    foundation.manifest_check(manifest, manifest_path)
    registry = foundation.load(registry_path)
    foundation.allocation_check(manifest, registry)
    register = foundation.load_register(register_path)
    # The register file may grow after the freeze; the referenced entries are pinned, not the whole file.
    counts = foundation.selection_check(manifest["selection"], {s["id"] for s in register["sources"]})
    foundation.register_pin_check(manifest, register, manifest_path, counts)
    heldout = foundation.isolation([manifest, registry], heldout_manifest, ("registry",))
    sources_conn = foundation.readonly(stack, sources_db)
    vesum_conn = foundation.readonly(stack, vesum_db)
    atlas_conn = foundation.readonly(stack, atlas_db)
    drift = 0
    for record in manifest["selection"]["source_records"]:
        conn = atlas_conn if record.get("database") == "atlas" else sources_conn
        observed = foundation.rows(conn, record["table"], record["row_key"])
        need(observed == [record["raw_row"]] and foundation.digest(observed[0]) == record["content_sha256"],
             "Source row drift against the frozen literal row; re-admit the source version")
        drift += 1
    sources = src.PilotSources(sources_conn, vesum_conn)
    entry_ids = sorted(r["raw_row"]["id"] for r in manifest["selection"]["source_records"]
                       if r["table"] == "ulif_dictua_entries")
    extract = scratch / "pilot-wp3-extract.sqlite"
    counts = src.write_extract(sources_conn, entry_ids, extract)
    wp3 = wp3_card_units(extract, set(entry_ids))
    hashes = {
        "sources_file": sha_of_file(sources_db),
        "vesum_canonical": sources.vesum_canonical_sha(),
        "atlas_file": sha_of_file(atlas_db),
        "registry_file": sha_of_file(registry_path),
        "register_entries": foundation.register_entries_digest(
            register, sorted({r["source_id"] for r in manifest["selection"]["source_records"]})),
        "manifest": manifest["manifest_sha256"],
        "frozen_rows_verified": drift,
        "extract_rows": counts,
    }
    return Inputs(manifest, registry, register, sources, hashes, wp3, heldout)


def wp3_card_units(extract: Path, entry_ids: set[int]):
    from scripts.projects.open_model_data.review_build.components import (
        ComponentContext,
        c3_relations,
        c4_phraseology,
    )
    from scripts.projects.open_model_data.review_build.components.wp3_sources import STORE
    from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader

    kept = []
    with SnapshotReader({STORE: extract}) as reader:
        ctx = ComponentContext(reader, {})
        for module in (c3_relations, c4_phraseology):
            for unit in module.iter_card_units(ctx):
                parent = int(unit.parent_key.rpartition("=")[2])
                if parent in entry_ids:
                    kept.append(unit)
    return kept


# --- assertion construction ----------------------------------------------------------------------------

class Builder:
    """Collects the assertions of one card and keeps ids unique."""

    def __init__(self, inputs: Inputs, card_id: str):
        self.inputs = inputs
        self.card_id = card_id
        self.assertions: dict[str, dict] = {}

    def add(self, subject_kind, subject_id, field, value, value_norm, source_id, snapshot_id, locator, version,
            confidence="high", mapping=None, record=None):
        group, tier = LINEAGE[source_id]
        subject = {"kind": subject_kind, "id": subject_id}
        entry = self.inputs.register[source_id]
        a = {
            "assertion_id": aid(source_id, snapshot_id, locator, subject, field, value_norm, version),
            "subject": subject,
            "field": field,
            "value": value,
            "value_norm": value_norm,
            "source_id": source_id,
            "snapshot_id": snapshot_id,
            "locator": locator,
            "extraction_version": version,
            "extraction_confidence": confidence,
            "producer": {"kind": "source_extract", "name": f"{source_id} extractor", "version": version},
            "review": {"status": "none"},
            "licence_ref": {"register_source_id": source_id, "register_version": self.inputs.register_version,
                            "appears_in": list(entry.get("appears_in", []))},
            "independence_group": group,
            "tier": tier,
            "status": "active",
        }
        if record:
            a["source_record_id"] = record["source_record_id"]
            aliases = sorted(record["aliases"], key=lambda x: ALIAS_ORDER.index(x["kind"]) if x["kind"] in
                             ALIAS_ORDER else len(ALIAS_ORDER))
            if aliases:
                a["source_record_key"] = aliases[0]["key"]
        if mapping:
            a["mapping"] = mapping
        self.assertions.setdefault(a["assertion_id"], a)
        return a["assertion_id"]


def mapping(confidence, basis, ambiguous=False, note=None):
    out = {"confidence": confidence, "basis": basis}
    if ambiguous:
        out["ambiguous"] = True
    if note:
        out["note"] = note
    return out


# --- lexeme evidence ----------------------------------------------------------------------------------

def label_part_of_speech(label: str) -> str | None:
    """The PULS-comparable part of speech a ULIF label names: plural-only nouns and surnames are nouns."""
    if label.startswith(("множинний іменник", "прізвище", "власна назва")):
        return "іменник"
    head = label.split()[0].rstrip(",") if label else ""
    return head if head in LABEL_HEADS else None


def parse_gender(label: str) -> list[str]:
    head = label.split(",")[0]
    if "множинний" in head:
        return []
    return sorted({letter for word, letter in GENDER_WORDS.items() if word in head})


def parse_aspect(label: str) -> str | None:
    head = label.split(",")[0]
    if "недоконаного і доконаного" in head or "доконаного і недоконаного" in head:
        return "both"
    if "недоконаного" in head:
        return "imperf"
    if "доконаного" in head:
        return "perf"
    return None


def vesum_gender(lemma_rows: list[dict]) -> list[str]:
    found = set()
    for row in lemma_rows:
        tokens = row["tags"].split(":")
        if row["pos"] == "noun" and row["word_form"] == row["lemma"]:
            found.update(t for t in tokens if t in src.GENDERS)
    return sorted(found)


def vesum_aspect(rows: list[dict]) -> str | None:
    tags = {t for row in rows for t in row["tags"].split(":")}
    if {"perf", "imperf"} <= tags:
        return "both"
    if "imperf" in tags:
        return "imperf"
    if "perf" in tags:
        return "perf"
    return None


def declared(forms: list[str], proper: bool) -> str:
    cleaned = [f if proper else f.lower() for f in forms]
    return "|".join(sorted(set(cleaned)))


class Ledger:
    """Field accounting: every applicable field of every card ends in exactly one disposition."""

    def __init__(self):
        self.cards: dict[str, dict] = {}
        self.unattached: list[dict] = []

    def start(self, card_id, unit_key):
        self.cards[card_id] = {"unit_key": unit_key, "fields": {}, "held": [], "notes": []}

    def field(self, card_id, name, disposition, reason=None, **extra):
        item = {"disposition": disposition}
        if reason:
            item["reason"] = reason
        item.update(extra)
        self.cards[card_id]["fields"][name] = item

    def hold(self, card_id, kind, reason, **extra):
        self.cards[card_id]["held"].append({"kind": kind, "reason": reason, **extra})


def assemble_lexeme(inputs: Inputs, unit: dict, entry: dict, ledger: Ledger, homograph_count: Counter,
                    match_cache: dict):
    """Assertions for a ULIF-anchored lexeme or proper-name card."""
    card_id = entry["card_id"]
    key = entry["key_at_creation"]
    spelling, pos = key["spelling"], key["pos"]
    kind = entry["card_kind"]
    proper = kind == "proper_name"
    anchor = inputs.records[unit["anchor_locator"]]
    raw = anchor["raw_row"]
    entry_id = raw["id"]
    srec = inputs.record_ids[("ulif", anchor["locator"])]
    snapshot = anchor["snapshot_id"]
    b = Builder(inputs, card_id)
    sources = inputs.sources
    ledger.start(card_id, unit["unit_key"])

    # ULIF homonyms of the same class and the VESUM entries of the spelling (identity.md §4).
    class_pos = label_pos(raw["grammatical_label"])
    homonyms = {}
    for row in sources.homonyms(raw["normalized_query"]):
        same = (label_pos(row["grammatical_label"]) == class_pos
                and is_proper_name(row["grammatical_label"], row["canonical_headword"], row["sense_gloss"]) == proper
                and (class_pos is not None or row["grammatical_label"] == raw["grammatical_label"]))
        if row["id"] == entry_id or same:
            head = row["canonical_headword"] or (unit["literal_head"] if row["id"] == entry_id
                                                  else lemma_row_head(sources.forms(row["id"])))
            if head:
                homonyms[row["id"]] = {"head": head, "row": row,
                                       "paradigm": src.ulif_paradigm(sources.forms(row["id"]))}
    keep_gender = any(len(slot) > 1 and any(t in src.GENDERS for t in slot)
                      for h in homonyms.values() for slot in h["paradigm"]["slots"])
    vesum_rows = sources.vesum_forms(spelling)
    entries_all = src.vesum_paradigm([r for r in vesum_rows if r["pos"] == pos], keep_gender)
    wanted = {eid: e for eid, e in entries_all.items() if (("prop" in e["flags"]) == proper) or (
        proper and not any("prop" in x["flags"] for x in entries_all.values()))}
    cache_key = (entry_id, tuple(sorted(wanted)))
    if cache_key not in match_cache:
        match_cache[cache_key] = src.match_identity(entry_id, homonyms, wanted)
    match = match_cache[cache_key]
    vesum_entry = match["vesum_entry"]
    vsnap = "vesum@" + inputs.hashes["vesum_canonical"][:16]
    v_conf = {"high": "high", "medium": "medium"}.get(match["confidence"], "unresolved")
    v_map = mapping(v_conf, match["basis"] if match["basis"] in {"paradigm", "stress", "entry"} else "paradigm",
                    note="; ".join(match["notes"]) or None)
    v_rows = [r for r in vesum_rows if r["entry_id"] == vesum_entry] if vesum_entry else []
    v_lemma_rows = [r for r in v_rows if r["word_form"] == r["lemma"]]
    v_locator = f"vesum:entry:{vesum_entry}" if vesum_entry else None

    head_text = raw["canonical_headword"]
    recovered = not head_text
    head_record = srec
    head_locator = f"{anchor['locator']} [canonical_headword]"
    head_confidence = "high"
    if recovered:
        paradigm_record = next((inputs.records[k] for k in unit["source_record_keys"]
                                if inputs.records[k]["table"] == "ulif_dictua_sections"), None)
        need(paradigm_record is not None, "Empty ULIF headword without the frozen paradigm section")
        head_text = unit["literal_head"]
        head_locator = f"{paradigm_record['locator']} [payload_json#/raw_html first data row]"
        head_confidence = "medium"
        head_record = inputs.record_ids[("ulif", paradigm_record["locator"])]
    else:
        need(src.nfc(head_text) == src.nfc(unit["literal_head"]), "Unit head differs from the frozen ULIF headword")

    # spelling
    sp_norm = spelling if proper else spelling.lower()
    b.add("card", card_id, "spelling", spelling, sp_norm, "ulif", snapshot, head_locator, src.EXTRACTION["ulif_entry"],
          head_confidence, record=head_record)
    if v_lemma_rows:
        b.add("card", card_id, "spelling", v_lemma_rows[0]["lemma"], sp_norm, "vesum", vsnap, v_locator + " [lemma]",
              src.EXTRACTION["vesum"], "high", mapping=v_map)
    ledger.field(card_id, "spelling", "asserted")

    # stress: the stressed headword; a part printed with several marks declares a doublet.
    readings = src.stress_forms(head_text)
    b.add("card", card_id, "stress", readings if len(readings) > 1 else readings[0],
          declared(readings, proper) if len(readings) > 1 else (readings[0] if proper else readings[0].lower()),
          "ulif", snapshot, head_locator, src.EXTRACTION["ulif_entry"], head_confidence, record=head_record)
    vesum_stress = sorted(entries_all[vesum_entry]["stress"]) if vesum_entry else []
    if vesum_stress:
        b.add("card", card_id, "stress", vesum_stress if len(vesum_stress) > 1 else vesum_stress[0],
              declared(vesum_stress, proper), "vesum", vsnap, v_locator + " [source_comment]",
              src.EXTRACTION["vesum"], "high", mapping=v_map)
    for k in unit["source_record_keys"]:
        rec = inputs.records[k]
        if rec["source_id"] == "ukrainian_word_stress":
            payload = json.loads(rec["raw_row"]["payload_json"])
            form = src.nfc(payload["form"])
            b.add("card", card_id, "stress", form, form if proper else form.lower(), "ukrainian_word_stress",
                  rec["snapshot_id"], rec["locator"], src.EXTRACTION["uws"], "medium",
                  mapping=mapping("medium", "spelling", note="spelling-keyed migrated row"),
                  record=inputs.record_ids[("ukrainian_word_stress", rec["locator"])])
    ledger.field(card_id, "stress", "asserted",
                 vesum_stress="present" if vesum_stress else "no stress in VESUM for this entry")

    # pos
    label = raw["grammatical_label"]
    u_pos = label_pos(label)
    if u_pos:
        b.add("card", card_id, "pos", u_pos, u_pos, "ulif", snapshot, f"{anchor['locator']} [grammatical_label]",
              src.EXTRACTION["ulif_entry"], "high", record=srec)
    if v_rows:
        b.add("card", card_id, "pos", v_rows[0]["pos"], v_rows[0]["pos"], "vesum", vsnap, v_locator + " [pos]",
              src.EXTRACTION["vesum"], "high", mapping=v_map)
    if u_pos or v_rows:
        ledger.field(card_id, "pos", "asserted")
    else:
        ledger.field(card_id, "pos", "unresolved",
                     "the ULIF label names no part of speech and no VESUM entry is attached to this homonym")
    b.add("card", card_id, "grammatical_label", label, src.norm_v1(label), "ulif", snapshot,
          f"{anchor['locator']} [grammatical_label]", src.EXTRACTION["ulif_entry"], "high", record=srec)
    ledger.field(card_id, "grammatical_label", "asserted")

    # gender (nouns) and aspect (verbs)
    if pos == "noun":
        genders = parse_gender(label)
        if genders:
            b.add("card", card_id, "gender", genders, "|".join(genders), "ulif", snapshot,
                  f"{anchor['locator']} [grammatical_label]", src.EXTRACTION["ulif_entry"], "medium", record=srec)
        vg = vesum_gender(v_lemma_rows)
        if vg:
            b.add("card", card_id, "gender", vg, "|".join(vg), "vesum", vsnap, v_locator + " [tags]",
                  src.EXTRACTION["vesum"], "high", mapping=v_map)
        if genders or vg:
            ledger.field(card_id, "gender", "asserted")
        else:
            ledger.field(card_id, "gender", "not_applicable", "plural-only or no gender in the label")
    else:
        ledger.field(card_id, "gender", "not_applicable", "not a noun")
    if pos == "verb":
        aspect = parse_aspect(label)
        if aspect:
            b.add("card", card_id, "aspect", aspect, aspect, "ulif", snapshot,
                  f"{anchor['locator']} [grammatical_label]", src.EXTRACTION["ulif_entry"], "medium", record=srec)
        va = vesum_aspect(v_rows) if v_rows else None
        if va:
            b.add("card", card_id, "aspect", va, va, "vesum", vsnap, v_locator + " [tags]",
                  src.EXTRACTION["vesum"], "high", mapping=v_map)
        ledger.field(card_id, "aspect", "asserted" if (aspect or va) else "source_absent")
    else:
        ledger.field(card_id, "aspect", "not_applicable", "not a verb")

    # paradigm: per slot, ULIF (accepted slots) and VESUM (all of the matched entry's slots). Both sides are
    # projected onto the dimensions each prints for every slot, so one slot name means one proposition.
    paradigm = homonyms[entry_id]["paradigm"]
    vparadigm = entries_all[vesum_entry] if vesum_entry else None
    if vparadigm and paradigm["slots"] and vparadigm["slots"]:
        dims = src.common_dims(paradigm, vparadigm)
        paradigm, vparadigm = src.project(paradigm, dims), src.project(vparadigm, dims)
    # The forms are parsed from the entry's paradigm section; a frozen section record is their source record.
    section_locator = next((k for k in unit["source_record_keys"]
                            if inputs.records[k]["table"] == "ulif_dictua_sections"), None)
    forms_record = inputs.record_ids[("ulif", section_locator)] if section_locator else srec
    failed = sources.forms_failed(entry_id)
    forms_rows = sources.forms(entry_id)
    forms_snapshot = "ulif-forms@sha256:" + foundation.digest(forms_rows) if forms_rows else None
    withheld_slots = {}
    if failed:
        ledger.hold(card_id, "paradigm", "forms_entry_failed", detail=failed)
    else:
        for slot, item in sorted(paradigm["slots"].items()):
            name = src.slot_name(slot)
            if item["withheld"]:
                withheld_slots[name] = item["withheld"]
                ledger.hold(card_id, "paradigm_slot", ",".join(item["withheld"]), slot=name, source="ulif")
                continue
            b.add("card", card_id, "paradigm", {"slot": name, "forms": item["stressed"], "row_ids": item["rows"]},
                  f"{name}=" + "|".join(item["forms"]), "ulif", forms_snapshot,
                  f"ulif:ulif_forms:entry:{entry_id}:slot:{name}", src.EXTRACTION["ulif_forms"], "high",
                  record=forms_record)
        for slot in sorted(homonyms[entry_id]["paradigm"].get("uncertain_only", {})):
            ledger.hold(card_id, "paradigm_slot", "asterisk_marked", slot=src.slot_name(slot), source="ulif")
    if vparadigm:
        for slot, item in sorted(vparadigm["slots"].items()):
            name = src.slot_name(slot)
            b.add("card", card_id, "paradigm", {"slot": name, "forms": sorted(item["forms"]),
                                                "tags": sorted(item["tags"])},
                  f"{name}=" + "|".join(sorted(item["forms"])), "vesum", vsnap, f"{v_locator} [slot {name}]",
                  src.EXTRACTION["vesum"], "high", mapping=v_map)
    if paradigm["slots"] or (vparadigm and vparadigm["slots"]):
        ledger.field(card_id, "paradigm", "asserted",
                     withheld_slots=withheld_slots or None,
                     identity_match=match["method"])
    else:
        ledger.field(card_id, "paradigm", "not_applicable", "invariable: no inflection slots in ULIF or VESUM")

    # cefr: PULS is spelling-keyed; ambiguous on a spelling with several cards.
    puls_keys = [k for k in unit["source_record_keys"] if inputs.records[k]["source_id"] == "puls"]
    ambiguous = homograph_count[spelling.lower()] > 1
    for k in puls_keys:
        rec = inputs.records[k]
        row = rec["raw_row"]
        puls_pos, label_head = row["pos"].split()[0], label_part_of_speech(raw["grammatical_label"])
        guide = f"guideword present: {row['guideword']}" if row["guideword"] else None
        if label_head and puls_pos != label_head:
            conf, note = "unresolved", f"PULS part of speech {row['pos']} differs from the ULIF label"
        else:
            conf, note = "medium", guide or "spelling-keyed PULS row"
        b.add("card", card_id, "cefr", row["level"], row["level"], "puls", rec["snapshot_id"],
              f"{rec['locator']} [level]", src.EXTRACTION["puls"], "high",
              mapping=mapping(conf, "spelling", ambiguous=ambiguous, note=note),
              record=inputs.record_ids[("puls", rec["locator"])])
    ledger.field(card_id, "cefr", "asserted" if puls_keys else "source_absent",
                 spelling_ambiguous=ambiguous if puls_keys else None)

    senses(inputs, b, unit, entry, anchor, srec, ledger)
    relations(inputs, b, unit, entry, srec, ledger)
    for name in NOT_IN_FROZEN_INPUTS:
        if name in CARD_FIELDS:
            ledger.field(card_id, name, "not_in_frozen_inputs", NOT_IN_FROZEN_INPUTS[name])
    return b, match


def lemma_row_head(forms: list[dict]) -> str:
    """The stressed lemma printed in a checked entry whose header cell was not parsed (identity.md §2.2)."""
    return next((src.nfc(f["form_stressed"]) for f in forms if f["is_lemma"] and f["form_stressed"]), "")


def senses(inputs: Inputs, b: Builder, unit, entry, anchor, srec, ledger):
    """Seed-gloss sense assertions; sense ids and seeding were fixed by the registry."""
    card_id = entry["card_id"]
    for sense in entry["senses"]:
        event = inputs.sense_events[sense["sense_id"]]
        literal = event.get("literal_gloss_unit")
        if literal:
            index = re.search(r"sense_gloss\[(\d+)\]$", event["source_unit"]).group(1)
            b.add("sense", sense["sense_id"], "sense_label", literal, src.norm_v1(literal), "ulif",
                  anchor["snapshot_id"], f"{anchor['locator']} [sense_gloss[{index}]]",
                  src.EXTRACTION["ulif_entry"], "medium", record=srec)
    labelled = sum(1 for s in entry["senses"] if inputs.sense_events[s["sense_id"]].get("literal_gloss_unit"))
    ledger.field(card_id, "sense_label", "asserted" if labelled else "source_absent",
                 reason=None if labelled else "ULIF entry has no sense gloss; one unsplit sense",
                 senses=len(entry["senses"]))
    spelling = entry["key_at_creation"]["spelling"].lower()
    articles = [a for a in inputs.sources.sum20_articles() if src.unstressed(a["headword"]).lower() == spelling]
    if articles:
        ledger.field(card_id, "definition_uk", "held", "sum20_article_present_not_aligned",
                     articles=[a["wordid"] for a in articles],
                     quarantined=[a["wordid"] for a in articles if a["quarantine_reason"]])
    else:
        ledger.field(card_id, "definition_uk", "source_absent",
                     "no СУМ-20 article for the lexeme in the held crawl; ВТС is not admitted (plan §6.1)")


def relations(inputs: Inputs, b: Builder, unit, entry, srec, ledger):
    """C3 synonym/antonym groups of the entry, aligned only by the one-unit rule (schema.md §6)."""
    card_id = entry["card_id"]
    entry_id = inputs.records[unit["anchor_locator"]]["raw_row"]["id"]
    parent = f"ulif_dictua_entries:id={entry_id}"
    by_kind = defaultdict(list)
    for u in inputs.wp3_units:
        if u.parent_key == parent and u.candidate.operation in {"synonyms", "antonyms"}:
            by_kind[u.candidate.operation].append(u)
    active = [s for s in entry["senses"] if s["state"] in {"active", "unsplit"}]
    for kind in ("synonyms", "antonyms"):
        units = by_kind.get(kind, [])
        accepted = [u for u in units if u.candidate.outcome == "accepted"]
        withheld = [u for u in units if u.candidate.outcome != "accepted"]
        for u in withheld:
            ledger.hold(card_id, kind, u.candidate.reason, locator=f"ulif:ulif_dictua_sections:{u.source_key}")
        aligned = unaligned = 0
        for u in accepted:
            c = u.candidate
            members = next(v for v in c.response if v.slot == "members")
            discriminator = next((v for v in c.slots if v.slot == "sense"), None)
            section_id = int(u.source_key.rpartition("=")[2])
            locator = f"ulif:ulif_dictua_sections:id:{section_id} [payload_json#/raw_html]"
            value = {"members": members.text, "group": u.group_key, "span": list(members.span) if members.span
                     else None, "discriminator": discriminator.text if discriminator else None}
            if len(active) == 1 and len(units) == 1:
                sense = active[0]
                b.add("sense", sense["sense_id"], kind, value, src.norm_v1(members.text), "ulif",
                      "ulif-section@sha256:" + members.citations[0].field_sha256, locator,
                      src.EXTRACTION["ulif_section"], "high",
                      mapping=mapping("high", "sense", note="one card sense and one source group"), record=srec)
                aligned += 1
            else:
                b.add("card", card_id, kind, value, src.norm_v1(members.text), "ulif",
                      "ulif-section@sha256:" + members.citations[0].field_sha256, locator,
                      src.EXTRACTION["ulif_section"], "high",
                      mapping=mapping("unresolved", "sense", ambiguous=True,
                                      note=f"{len(units)} source group(s) against {len(active)} card sense(s): "
                                           "no alignment by position"), record=srec)
                unaligned += 1
        if not units:
            ledger.field(card_id, kind, "source_absent", "the entry has no ULIF section of this kind")
        else:
            ledger.field(card_id, kind, "asserted" if aligned else ("unresolved" if unaligned else "held"),
                         aligned=aligned, unaligned=unaligned, withheld=len(withheld))


# --- MWE cards ------------------------------------------------------------------------------------------

def aggregator_form(word: str) -> str:
    """The printed headword of an aggregator row: `<fna>` content when tagged, else the text before ` {{</fras>}}`."""
    tagged = re.search(r"<fna>(.*?)</fna>", word)
    if tagged:
        return tagged.group(1).strip()
    return re.sub(r"\s*\{\{</fras>\}\}\s*$", "", word).strip()


def assemble_mwe(inputs: Inputs, unit: dict, entry: dict, ledger: Ledger, idiom_units):
    card_id = entry["card_id"]
    anchor = inputs.records[unit["anchor_locator"]]
    raw = anchor["raw_row"]
    srec = inputs.record_ids[("frazeolohichnyi", anchor["locator"])]
    b = Builder(inputs, card_id)
    ledger.start(card_id, unit["unit_key"])
    form = src.nfc(aggregator_form(raw["word"]))
    need(form == src.nfc(unit["literal_head"]), "Aggregator headword differs from the frozen unit head")
    b.add("card", card_id, "mwe_form", form, src.norm_v1(form), "frazeolohichnyi", anchor["snapshot_id"],
          f"{anchor['locator']} [word]", src.EXTRACTION["frazeolohichnyi"], "high", record=srec)
    ledger.field(card_id, "mwe_form", "asserted")
    sense = entry["senses"][0]
    body = strip_aggregator_markup(raw["definition"])
    ledger.hold(card_id, "definition_uk", "entry_body_unsegmented", locator=f"{anchor['locator']} [definition]",
                detail="heading, label, numbered senses and quotations are one text; no reviewed segmenter")
    # ULIF phraseology of the pilot entries that is the same dictionary record (identity.md §9).
    wanted = normalize_mwe_form(form)
    matched = 0
    for u in idiom_units:
        c = u.candidate
        if c.outcome != "accepted":
            continue
        slot = next((v for v in c.slots if v.slot == "idiom"), None)
        definition = next((v for v in c.response if v.slot == "definition"), None)
        citations = [v for v in c.response if v.slot == "citation"]
        if slot is None or definition is None or normalize_mwe_form(slot.text) != wanted:
            continue
        squeezed = squeeze(body)
        same = squeeze(definition.text) in squeezed and any(squeeze(v.text) in squeezed for v in citations)
        section_id = int(u.source_key.rpartition("=")[2])
        if not same:
            ledger.hold(card_id, "ulif_phraseology", "same_form_different_record",
                        locator=f"ulif:ulif_dictua_sections:id:{section_id}")
            continue
        entry_id = int(u.parent_key.rpartition("=")[2])
        record = inputs.record_ids.get(("ulif", f"ulif:ulif_dictua_entries:id:{entry_id}"))
        locator = f"ulif:ulif_dictua_sections:id:{section_id} [payload_json#/raw_html]"
        snap = "ulif-section@sha256:" + definition.citations[0].field_sha256
        sense_map = mapping("high", "sense", note="same dictionary record: definition and quotation contained in "
                                                   "the aggregator entry body")
        b.add("sense", sense["sense_id"], "definition_uk", definition.text, src.norm_v1(definition.text), "ulif",
              snap, locator, src.EXTRACTION["ulif_section"], "high", mapping=sense_map, record=record)
        for v in citations:
            b.add("sense", sense["sense_id"], "examples", v.text, src.norm_v1(v.text), "ulif", snap, locator,
                  src.EXTRACTION["ulif_section"], "high", mapping=sense_map, record=record)
        b.add("card", card_id, "mwe_form", src.nfc(unstressed_idiom(slot.text)),
              src.norm_v1(unstressed_idiom(slot.text)), "ulif", snap, locator, src.EXTRACTION["ulif_section"], "low",
              record=record)
        matched += 1
    if matched:
        ledger.field(card_id, "definition_uk", "asserted", matched_ulif_records=matched)
        ledger.field(card_id, "examples", "asserted")
    else:
        ledger.field(card_id, "definition_uk", "held", "entry_body_unsegmented; no same-record ULIF phraseology")
        ledger.field(card_id, "examples", "held", "quotations are inside the unsegmented entry body")
    for name, reason in NOT_IN_FROZEN_INPUTS.items():
        if name in MWE_FIELDS:
            ledger.field(card_id, name, "not_in_frozen_inputs", reason)
    ledger.field(card_id, "sense_label", "not_applicable", "idiom card: one unsplit sense, no seed gloss")
    return b


def unstressed_idiom(text: str) -> str:
    """The printed idiom without the source's (doubled) accents and its closing full stop."""
    return src.nfc(text.replace(src.ACUTE, "")).rstrip(". ").strip()


def account_remaining_fields(ledger: Ledger, card_id: str, card_kind: str):
    """Every applicable field not decided above is a field no frozen input supplies."""
    names = (MWE_FIELDS if card_kind == "mwe" else CARD_FIELDS) + SENSE_FIELDS
    fields = ledger.cards[card_id]["fields"]
    for name in names:
        fields.setdefault(name, {"disposition": "not_in_frozen_inputs", "reason": NOT_IN_FROZEN_INPUTS.get(
            name, "no frozen pilot input supplies this field")})


# --- card assembly --------------------------------------------------------------------------------------

def card_json(inputs: Inputs, entry: dict, builder: Builder, match: dict, build_block: dict):
    """One card from its assertions: resolutions, links added later, quality and the build block."""
    assertions = sorted(builder.assertions.values(), key=lambda a: (a["field"], a["assertion_id"]))
    sense_rows = []
    for sense in entry["senses"]:
        event = inputs.sense_events[sense["sense_id"]]
        smap = [{"source_id": "ulif" if event["source_unit"].startswith("ulif:") else "frazeolohichnyi",
                 "source_sense_key": event["source_unit"], "mapped_by": "registry:" + event.get("rules_version", "")}]
        row = {"sense_id": sense["sense_id"], "order": sense["order"], "state": sense["state"], "merged_into": None,
               "sense_map": smap, "fields": {}}
        if sense["state"] == "active" and event.get("literal_gloss_unit"):
            row["seeded_from"] = "ulif_sense_gloss:" + event["source_unit"]
        sense_rows.append(row)
    # Sense-map units of aligned relation groups.
    for a in assertions:
        if a["subject"]["kind"] == "sense" and a["field"] in {"synonyms", "antonyms"}:
            for row in sense_rows:
                if row["sense_id"] == a["subject"]["id"]:
                    section = re.search(r"id:(\d+)", a["locator"]).group(1)
                    unit = {"source_id": "ulif", "source_sense_key": f"ulif:section:{section}",
                            "mapped_by": "rules:one-unit-alignment"}
                    if unit not in row["sense_map"]:
                        row["sense_map"].append(unit)
    key = entry["key_at_creation"]
    identity_keys = [dict(k) for k in key["source_keys"]]
    if match.get("vesum_entry"):
        identity_keys.append({"source_id": "vesum", "key": f"vesum:entry:{match['vesum_entry']}",
                              "match_note": f"{match['method']}; basis {match['basis']}"})
    identity = {
        "confidence": match["confidence"], "method": match["method"],
        "decided_by": f"rules:{inputs.manifest['rules_version']}/{ASSEMBLER_VERSION}",
        "source_keys": identity_keys, "notes": list(match["notes"]),
    }
    out = {
        "schema_version": "1", "card_id": entry["card_id"], "card_kind": entry["card_kind"], "state": "active",
        "merged_into": None, "split_into": None, "key_at_creation": key, "identity": identity, "senses": sense_rows,
        "links": [], "fields": {}, "assertions": assertions,
        "quality": {
            "identity_confidence": match["confidence"],
            "extraction_confidence_min": max((a["extraction_confidence"] for a in assertions), key=CONF_ORDER.index)
            if assertions else "high",
            "linguistic_review": {"status": "none"},
            "practice_eligibility": [],
        },
        "overlay_applied": [],
        "build": dict(build_block),
    }
    return out


def attach_unmatched_phraseology(inputs: Inputs, ledger: Ledger, cards: dict) -> None:
    """ULIF phraseology of the pilot entries that no allocated MWE card carries: accounted, never silently dropped."""
    matched = {a["locator"].split(" ")[0] for c in cards.values() for a in c["assertions"]
               if a["source_id"] == "ulif" and a["field"] == "definition_uk" and a["subject"]["kind"] == "sense"}
    for u in inputs.wp3_units:
        if u.candidate.operation != "idiom_definition":
            continue
        locator = f"ulif:ulif_dictua_sections:{u.source_key.replace('=', ':')}"
        if locator in matched:
            continue
        ledger.unattached.append({"kind": "phraseology", "outcome": u.candidate.outcome, "reason": u.candidate.reason,
                                  "locator": locator,
                                  "entry": int(u.parent_key.rpartition("=")[2])})


def mwe_identity():
    return {"confidence": "high", "method": "unique_match", "vesum_entry": None, "candidates": [],
            "basis": "entry", "notes": ["one aggregator entry anchors the expression (identity.md §9)"]}


def homograph_links(cards: dict[str, dict]) -> None:
    """Derived `homograph_of` links between cards with equal spelling and distinct identity (schema.md §7.2)."""
    by_spelling = defaultdict(list)
    for card in cards.values():
        if card["card_kind"] in {"lexeme", "proper_name"}:
            by_spelling[card["key_at_creation"]["spelling"].lower()].append(card)
    for group in by_spelling.values():
        group.sort(key=lambda c: c["card_id"])
        for i, left in enumerate(group):
            for right in group[i + 1:]:
                evidence = sorted(
                    a["assertion_id"] for card in (left, right) for a in card["assertions"]
                    if a["field"] == "spelling" and a["source_id"] == "ulif" and a["status"] == "active")
                endpoints = [{"id": left["card_id"]}, {"id": right["card_id"]}]
                canon = "|".join(e["id"] for e in endpoints)
                link = {
                    "link_id": "wl_" + hashlib.sha256(f"homograph_of|{canon}".encode()).hexdigest()[:24],
                    "type": "homograph_of", "endpoints": endpoints, "basis": "derived",
                    "derived_by": "rules:homograph_of equal key_at_creation.spelling ignoring case, distinct identity",
                    "assertion_ids": evidence, "state": "active" if evidence else "suppressed",
                }
                left["links"].append(link)
                right["links"].append(json.loads(json.dumps(link)))


def build_id_of(inputs: Inputs, suppressions: dict) -> str:
    material = {"manifest": inputs.manifest["manifest_sha256"], "registry": inputs.hashes["registry_file"],
                "register": inputs.hashes["register_entries"], "vesum": inputs.hashes["vesum_canonical"],
                "suppressions": foundation.digest(suppressions), "assembler": ASSEMBLER_VERSION}
    return "pilot-assembly@sha256:" + foundation.digest(material)


def build_block(inputs: Inputs, suppressions: dict, build_id: str) -> dict:
    h = inputs.hashes
    frozen_sources = inputs.manifest["database_file_sha256"]["sources"]
    frozen_atlas = inputs.manifest["database_file_sha256"]["atlas"]
    return {
        "build_id": build_id,
        "rules_version": inputs.manifest["rules_version"],
        "inputs": {
            "S": {
                "ulif": {"ref": "sources.ulif_dictua_entries + ulif_dictua_sections + ulif_forms",
                         "content_sha256": frozen_sources,
                         "note": f"whole-file digest at freeze; observed at build {h['sources_file']}. Frozen rows "
                                 "are re-read literally at every build; other rows carry their own row digests"},
                "puls": {"ref": "sources.puls_cefr", "content_sha256": frozen_sources, "note": "frozen rows only"},
                "frazeolohichnyi": {"ref": "sources.frazeolohichnyi", "content_sha256": frozen_sources,
                                    "note": "frozen rows only"},
                "atlas0": {"ref": "data/atlas.db enrichment", "content_sha256": frozen_atlas,
                           "note": f"frozen row only; observed at build {h['atlas_file']}"},
            },
            "V": {"vesum": {"ref": "data/vesum.db vesum_build_metadata.canonical_jsonl_sha256",
                            "content_sha256": h["vesum_canonical"]}},
            "I": {"identity_registry": {"ref": "registry/atlas/identity/registry.json",
                                        "version": f"registry_version {inputs.registry['registry_version']}",
                                        "content_sha256": h["registry_file"]}},
            "O": {"suppressions": {"ref": "suppression selectors",
                                   "content_sha256": foundation.digest(suppressions),
                                   "note": f"{len(suppressions.get('entries', []))} selector(s); no overlay batches"},
                  "overlay": {"ref": "registry/atlas/overlay", "content_sha256": foundation.digest({"entries": []}),
                              "note": "no overlay exists for the pilot"}},
            "R": {"rules": {"ref": "scripts/atlas/word_card_resolver.py", "version": inputs.manifest["rules_version"]},
                  "normaliser": {"ref": "norm_v1()", "version": inputs.manifest["normaliser_version"]},
                  "assembler": {"ref": "scripts/atlas/word_card_assembly.py", "version": ASSEMBLER_VERSION},
                  "register": {"ref": "docs/sources/permissions-register.yaml referenced entries",
                               "version": f"schema_version {inputs.register_version}",
                               "content_sha256": h["register_entries"],
                               "note": "digest of the pinned referenced entries; the file may grow after the freeze"}},
        },
        "card_version": "cv_" + "0" * 24,
    }


# --- suppression (takedown) ----------------------------------------------------------------------------

def selector_matches(selector: dict, assertion: dict, spelling: str, normaliser: str) -> bool:
    kind = selector["kind"]
    if kind == "source":
        return assertion["source_id"] == selector["source_id"]
    if kind == "source_record":
        return assertion.get("source_record_id") == selector["source_record_id"]
    if kind == "assertion_content":
        need(selector["normaliser_version"] == normaliser,
             "Suppression selector is pinned to a normaliser this build does not carry; re-pin it")
        value = assertion["value"]
        raw = value if isinstance(value, str) else None
        return (assertion["source_id"] == selector["source_id"] and assertion["field"] == selector["field"]
                and spelling.lower() == selector["subject_spelling"].lower() and raw is not None
                and src.norm_v1(raw) == src.norm_v1(selector["value_norm"]))
    if kind == "assertion_id":
        return assertion["assertion_id"] == selector["assertion_id"] or selector_matches(
            selector["fallback"], assertion, spelling, normaliser)
    raise AssemblyError("Unsupported suppression selector kind")


def apply_suppressions(cards: dict[str, dict], suppressions: dict, normaliser: str) -> list[dict]:
    """Mark matching assertions suppressed, then recompute resolutions, link states and card states.

    Returns the takedown report: per suppression the assertions, fields, links and cards it reached (ids only).
    """
    report = []
    for entry in suppressions.get("entries", []):
        touched = {"suppression_id": entry["suppression_id"], "assertions": [], "cards": set(), "fields": set()}
        for card in cards.values():
            spelling = card["key_at_creation"]["spelling"]
            for a in card["assertions"]:
                if a.get("status") == "active" and selector_matches(entry["selector"], a, spelling, normaliser):
                    a["status"] = "suppressed"
                    a["suppression_ref"] = entry["suppression_id"]
                    touched["assertions"].append(a["assertion_id"])
                    touched["cards"].add(card["card_id"])
                    touched["fields"].add(f"{card['card_id']}:{a['field']}")
        need(touched["assertions"], "Suppression selector matches no assertion; re-pin it before building")
        touched["assertions"] = sorted(touched["assertions"])
        touched["cards"] = sorted(touched["cards"])
        touched["fields"] = sorted(touched["fields"])
        report.append(touched)
    status = {a["assertion_id"]: a["status"] for c in cards.values() for a in c["assertions"]}
    for card in cards.values():
        for link in card["links"]:
            cited = [status.get(i) for i in link["assertion_ids"]]
            gone = any(s != "active" for s in cited) if link["basis"] == "derived" else (
                bool(cited) and all(s != "active" for s in cited))
            if gone:
                link["state"] = "suppressed"
        _recompute(card)
        live = [a for a in card["assertions"] if a["status"] == "active"]
        if card["assertions"] and not live:
            card["state"] = "suppressed"
    return report


def finish_cards(cards: dict[str, dict]) -> None:
    for card in cards.values():
        _recompute(card)
        card["build"]["card_version"] = card_version(_project(card))


# --- build ---------------------------------------------------------------------------------------------

def build(inputs: Inputs, suppressions: dict | None = None) -> dict:
    """Pure assembly over loaded inputs. Returns {cards, ledger, build_id, takedown}."""
    suppressions = suppressions or {"schema_version": "1", "entries": []}
    allocated = {e["card_id"] for e in inputs.registry["entries"]}
    need(len(inputs.units) == len(set(inputs.entry_by_unit)), "Duplicate frozen unit key")
    build_id = build_id_of(inputs, suppressions)
    block = build_block(inputs, suppressions, build_id)
    spelling_count = Counter(
        inputs.entry_by_unit[u["unit_key"]]["key_at_creation"]["spelling"].lower() for u in inputs.units
        if u["entry_type"] == "lexeme_candidate")
    ledger = Ledger()
    idiom_units = [u for u in inputs.wp3_units if u.candidate.operation == "idiom_definition"]
    cards: dict[str, dict] = {}
    match_cache: dict = {}
    for unit in inputs.units:
        entry = inputs.entry_by_unit[unit["unit_key"]]
        if entry["card_id"] not in allocated:
            raise MissingAllocation("Card is not allocated in the frozen identity registry")
        for sense in entry["senses"]:
            need(sense["sense_id"] in inputs.sense_events, "Sense without registry mint evidence")
        if unit["entry_type"] == "mwe_candidate":
            builder = assemble_mwe(inputs, unit, entry, ledger, idiom_units)
            match = mwe_identity()
        else:
            builder, match = assemble_lexeme(inputs, unit, entry, ledger, spelling_count, match_cache)
        account_remaining_fields(ledger, entry["card_id"], entry["card_kind"])
        cards[entry["card_id"]] = card_json(inputs, entry, builder, match, block)
    attach_unmatched_phraseology(inputs, ledger, cards)
    homograph_links(cards)
    finish_cards(cards)
    takedown = apply_suppressions(cards, suppressions, inputs.manifest["normaliser_version"])
    for card in cards.values():
        card["build"]["card_version"] = card_version(_project(card))
    return {"cards": cards, "ledger": ledger, "build_id": build_id, "takedown": takedown, "block": block}


# --- reports -------------------------------------------------------------------------------------------

def accounting(result: dict) -> dict:
    """Counts only: no Ukrainian text leaves the host-only output through the report."""
    cards = result["cards"]
    ledger = result["ledger"].cards
    dispositions = Counter()
    per_field = defaultdict(Counter)
    for item in ledger.values():
        for name, d in item["fields"].items():
            dispositions[d["disposition"]] += 1
            per_field[name][d["disposition"]] += 1
    states = defaultdict(Counter)
    for card in cards.values():
        for name, res in card["fields"].items():
            states[name][res["state"]] += 1
        for sense in card["senses"]:
            for name, res in sense["fields"].items():
                states[name][res["state"]] += 1
    holds = Counter()
    for item in ledger.values():
        for held in item["held"]:
            holds[(held["kind"], held["reason"])] += 1
    requirement = {}
    for rid, names in REQUIREMENT_FIELDS.items():
        c = Counter()
        for name in names:
            c.update(per_field.get(name, {}))
        requirement[rid] = dict(sorted(c.items()))
    return {
        "cards": len(cards),
        "card_kinds": dict(Counter(c["card_kind"] for c in cards.values())),
        "assertions": sum(len(c["assertions"]) for c in cards.values()),
        "assertions_by_source": dict(Counter(a["source_id"] for c in cards.values() for a in c["assertions"])),
        "identity_confidence": dict(Counter(c["identity"]["confidence"] for c in cards.values())),
        "identity_method": dict(Counter(c["identity"]["method"] for c in cards.values())),
        "field_states": {k: dict(sorted(v.items())) for k, v in sorted(states.items())},
        "field_dispositions": dict(sorted(dispositions.items())),
        "field_dispositions_by_field": {k: dict(sorted(v.items())) for k, v in sorted(per_field.items())},
        "held_units": {f"{k[0]}:{k[1]}": v for k, v in sorted(holds.items())},
        "requirement_coverage": requirement,
        "links": sum(1 for c in cards.values() for link in c["links"]) // 2,
        "unattached_phraseology": dict(Counter(
            f"{u['outcome']}:{u['reason']}" for u in result["ledger"].unattached)),
    }


# --- CLI -----------------------------------------------------------------------------------------------

def require_host_only(output: Path) -> None:
    """Cards are host-only data: refuse a destination inside the repository that git does not ignore."""
    root = Path(__file__).resolve().parents[2]
    target = output.resolve()
    if root not in (target, *target.parents):
        return
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--", str(target / "cards")],
                             check=False, capture_output=True, timeout=30).returncode == 0
    need(ignored, "Output must be outside the repository or in an ignored tree: cards are host-only data")


def write_output(output: Path, result: dict, report: dict) -> None:
    require_host_only(output)
    cards_dir = output / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    for stale in cards_dir.glob("*.json"):
        stale.unlink()
    for card_id, card in sorted(result["cards"].items()):
        foundation.write(cards_dir / f"{card_id}.json", card)
    foundation.write(output / "ledger.json", {"build_id": result["build_id"], "cards": result["ledger"].cards,
                                              "unattached": result["ledger"].unattached})
    foundation.write(output / "build-manifest.json", {"build_id": result["build_id"], "inputs": result["block"]["inputs"],
                                                      "rules_version": result["block"]["rules_version"]})
    foundation.write(output / "report.json", report)
    if result["takedown"]:
        foundation.write(output / "takedown-report.json", {"build_id": result["build_id"],
                                                           "suppressions": result["takedown"]})


def load_suppressions(path: Path | None) -> dict:
    if path is None:
        return {"schema_version": "1", "entries": []}
    data = foundation.load(path)
    foundation.schema(data, "word-card-suppression-v1.schema.json")
    return data


def store_path(name: str, explicit: Path | None) -> Path:
    """An explicit path, else the primary checkout's store; a refused or missing store stops the build."""
    from scripts.common.repo_root import main_checkout_root
    from scripts.storage.topology import StoreRefusal, resolve_store

    if explicit is not None:
        return explicit
    if name == "atlas":
        return main_checkout_root(Path(__file__).resolve().parents[2]) / "data" / "atlas.db"
    binding = resolve_store(name)
    if isinstance(binding, StoreRefusal):
        raise AssemblyError(f"The {name} store is unavailable ({binding.reason})")
    return binding.path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    help_text = {
        "build": "assemble the pilot cards into --output (host-only, ignored tree)",
        "verify": "re-read every locator, recheck identities, determinism and the on-disk cards; exit 1 on failure",
        "rehearse": "withdrawal and rollback rehearsal against the frozen pilot; writes takedown-rehearsal.json",
    }
    for name, text in help_text.items():
        command = commands.add_parser(name, help=text)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--registry", type=Path, required=True)
        command.add_argument("--register", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--suppressions", type=Path)
        command.add_argument("--heldout-manifest", type=Path)
        for store in ("sources", "vesum", "atlas"):
            command.add_argument(f"--{store}-db", type=Path, help=f"{store} database (default: the primary store)")
    args = parser.parse_args(argv)
    try:
        suppressions = load_suppressions(args.suppressions)
        with ExitStack() as stack:
            scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="word-card-assembly-")))
            inputs = load_inputs(
                args.manifest, args.registry, args.register, store_path("sources", args.sources_db),
                store_path("vesum", args.vesum_db), store_path("atlas", args.atlas_db), stack, scratch,
                args.heldout_manifest)
            result = build(inputs, suppressions)
            report = accounting(result) | {"build_id": result["build_id"], "heldout_isolation": inputs.heldout,
                                           "frozen_rows_verified": inputs.hashes["frozen_rows_verified"]}
            if args.operation == "build":
                write_output(args.output, result, report)
                print(json.dumps(report, ensure_ascii=False, sort_keys=True))
                return 0
            from scripts.atlas import word_card_verify as verifier

            if args.operation == "rehearse":
                outcome = verifier.rehearse(inputs)
                foundation.write(args.output / "takedown-rehearsal.json", outcome)
                print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
                return 0 if outcome["passed"] else 1
            outcome = verifier.verify(inputs, result, build(inputs, suppressions))
            on_disk = {p.stem: foundation.load(p) for p in (args.output / "cards").glob("*.json")}
            outcome["on_disk"] = {"passed": set(on_disk) == set(result["cards"]) and all(
                foundation.digest(on_disk[k]) == foundation.digest(v) for k, v in result["cards"].items()),
                "cards": len(on_disk)}
            outcome["passed"] = outcome["passed"] and outcome["on_disk"]["passed"]
            print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
            return 0 if outcome["passed"] else 1
    except (foundation.Refusal, ValueError, KeyError, OSError, yaml.YAMLError) as error:
        message = str(error) if isinstance(error, foundation.Refusal) else "Invalid or inaccessible input"
        print("REFUSED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
