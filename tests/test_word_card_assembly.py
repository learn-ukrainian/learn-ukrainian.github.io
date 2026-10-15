"""Pilot word-card assembly over a synthetic world: assertions, resolution, identity, sense placement, withdrawal,
rollback, verification and host-only output containment.

The world is built in memory from placeholder Cyrillic tokens and real grammatical-label terms; no dictionary
content is committed. Its ULIF forms are the existing parser's output for minimal held raw pages, so every build
authenticates them exactly as production does. Production reads the frozen pilot manifest; here `Inputs` is
constructed directly, so the tests cover assembly and verification, not the foundation's authentication
(tests/test_word_card_foundation.py).
"""

import copy
import json
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas import word_card_verify as verify
from scripts.atlas.allocate_pilot_identities import BUILD_PREFIX, HOLDING_BUILD_PREFIX
from scripts.common.git_context import sanitized_git_env
from scripts.guardrails import worktree_containment as containment
from tests.test_word_card_sources import (
    ENTRY_DDL,
    FAILURES_DDL,
    FORMS_DDL,
    SECTION_DDL,
    VESUM_DDL,
    add_entry,
    insert,
    raw_cache,
)

A = src.ACUTE
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "word-card-v1.schema.json").read_text())
MANIFEST_SHA = "7" * 64
BUILD = BUILD_PREFIX + MANIFEST_SHA
HOLDING_BUILD = HOLDING_BUILD_PREFIX + MANIFEST_SHA
ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
SNAP = "selected-row@sha256:"

SUM20_DDL = (
    """CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, wordid INTEGER, headword TEXT, stressed_headword TEXT,
 pos TEXT, grammar TEXT, article_html TEXT, official_url TEXT, fetched_at TEXT, quarantine_reason TEXT)""",
    "CREATE TABLE sum20_senses (id INTEGER PRIMARY KEY, article_id INTEGER, sense_order INTEGER, definition TEXT, "
    "register_labels TEXT)",
    "CREATE TABLE sum20_citations (id INTEGER PRIMARY KEY, article_id INTEGER, sense_ref INTEGER, \"order\" INTEGER, "
    "citation_text TEXT)",
)
LABEL_M = "іменник чоловічого роду"
LABEL_F = "іменник жіночого роду"


def opaque(prefix, number):
    return prefix + "".join(ALPHABET[(number >> (5 * i)) % 32] for i in range(11, -1, -1))


def synonym_html(head, lead, *others):
    members = ", ".join(f"<b>{o}</b>" for o in others)
    return f"<p><b>{head}</b> ({lead}), {members}.</p>"


def antonym_html(head, other, left, right):
    return (f"<table><tr><td><b>{head}</b></td><td><b>{other}</b></td></tr>"
            f"<tr><td>{left}.</td><td>{right}.</td></tr></table>")


def phrase_html(idiom, definition, quote, author):
    return f"<p><b>{idiom}.</b> {definition}. —<i>{quote}</i> ({author}).</p>"


class World:
    """Sources, raw cache, VESUM, frozen manifest, registry and the units, assembled in memory."""

    def __init__(self):
        self.sources = sqlite3.connect(":memory:")
        self.vesum = sqlite3.connect(":memory:")
        self.raw = raw_cache()
        self.records, self.units, self.entries, self.sr, self.events = [], [], [], [], []
        self.counter = 0
        self.sources.executescript(";".join((ENTRY_DDL, SECTION_DDL, FORMS_DDL, FAILURES_DDL, *SUM20_DDL)) + ";")
        self.sources.execute("CREATE TABLE puls_cefr (id INTEGER PRIMARY KEY, word TEXT, guideword TEXT, level TEXT, "
                             "pos TEXT, type TEXT, text TEXT, source TEXT)")
        self.sources.execute("CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, definition TEXT, "
                             "text TEXT, source TEXT)")
        self.vesum.executescript(VESUM_DDL + f"INSERT INTO vesum_build_metadata VALUES ('canonical_jsonl_sha256', "
                                             f"'{'5' * 64}');")
        self.vesum_id = 0

    def next(self):
        self.counter += 1
        return self.counter

    def vesum_form(self, entry, lemma, form, tags, comment=None, pos="noun"):
        self.vesum_id += 1
        self.vesum.execute("INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?,?)",
                           (self.vesum_id, entry, form, lemma, pos, tags, comment, form, lemma))

    def record(self, source, table, raw, locator=None, **extra):
        locator = locator or f"{source}:{table}:id:{raw['id']}"
        digest = foundation.digest(raw)
        rec = {"source_id": source, "table": table, "row_key": {"id": raw["id"]}, "locator": locator, "raw_row": raw,
               "snapshot_id": SNAP + digest, "content_sha256": digest, **extra}
        self.records.append(rec)
        number = self.next()
        sr_id = opaque("sr_", number)
        self.sr.append({"source_record_id": sr_id, "source_id": source,
                        "aliases": [{"kind": "table_row", "key": f"{source}:row:{raw['id']}",
                                     "snapshot_id": rec["snapshot_id"]}],
                        "correspondence": [{"snapshot_id": rec["snapshot_id"], "status": "unique",
                                            "locator": locator}]})
        return rec

    def ulif(self, entry_id, query, head, label, gloss="", homonym=1, rows=(), sections=(), puls=None, extra=(),
             kind="lexeme", holding=False):
        raw = add_entry(self.sources, self.raw, entry_id, query, head, label, gloss, homonym, rows, sections)
        anchor = self.record("ulif", "ulif_dictua_entries", raw)
        keys = [anchor["locator"]]
        if puls:
            row = {"id": 1000 + entry_id, "word": query, "guideword": "", "level": puls[0], "pos": puls[1],
                   "type": "значення", "text": f"{query} ({puls[0]})", "source": "PULS"}
            insert(self.sources, "puls_cefr", row)
            keys.append(self.record("puls", "puls_cefr", row)["locator"])
        for rec in extra:
            keys.append(rec["locator"])
        unit = {"unit_key": f"ulif:partition:{query}:{entry_id}", "anchor_locator": anchor["locator"],
                "entry_type": "lexeme_candidate", "literal_head": head, "source_record_keys": keys,
                "categories": ["ordinary_control_candidate"], "atlas_slug": None}
        self.units.append(unit)
        self.add_card(unit, kind, {"spelling": src.unstressed(head), "pos": None}, gloss, holding)
        return unit

    def mwe(self, row_id, word, definition):
        raw = {"id": row_id, "word": word, "definition": definition, "text": word + ": " + definition,
               "source": "Фразеологічний словник"}
        insert(self.sources, "frazeolohichnyi", raw)
        rec = self.record("frazeolohichnyi", "frazeolohichnyi", raw)
        form = wa.aggregator_form(word)
        unit = {"unit_key": f"frazeolohichnyi:{row_id}", "anchor_locator": rec["locator"], "entry_type": "mwe_candidate",
                "literal_head": form, "source_record_keys": [rec["locator"]],
                "categories": ["source_phraseology_candidate"], "atlas_slug": None}
        self.units.append(unit)
        self.add_card(unit, "mwe", {"spelling": form, "pos": "phrase"}, None)
        return unit

    def add_card(self, unit, kind, key, gloss, holding=False):
        number = self.next()
        card_id = opaque("wc_", number)
        source = unit["anchor_locator"].split(":")[0]
        key = {**key, "source_keys": [{"source_id": source, "key": unit["unit_key"], "snapshot_id": "s"},
                                      {"source_id": source, "key": unit["anchor_locator"], "snapshot_id": "s"}]}
        senses = []
        if kind == "mwe" or not gloss:
            parts = [("unsplit", unit["anchor_locator"] + "#unsplit", None, BUILD)]
        else:
            parts = [("active", f"ulif:entry:{self.records[-1]['raw_row']['id']} sense_gloss[{i}]", p.strip(), BUILD)
                     for i, p in enumerate(gloss[1:-1].split(";"))]
        if holding:  # the registry's append-only holding sense (allocate_pilot_identities --append-holding)
            parts.append(("unsplit", unit["anchor_locator"] + "#unsplit", None, HOLDING_BUILD))
        for order, (state, source_unit, literal, build) in enumerate(parts, start=1):
            sense_id = opaque("ws_", self.next())
            senses.append({"sense_id": sense_id, "order": order, "state": state})
            self.events.append({"event_id": f"ie_{self.next():04d}", "kind": "sense_mint", "build_id": build,
                                "to": [sense_id], "evidence": json.dumps({
                                    "source_unit": source_unit, "literal_gloss_unit": literal,
                                    "rules_version": "rules-v1-draft"})})
        self.entries.append({"card_id": card_id, "card_kind": kind, "state": "active", "key_at_creation": key,
                             "created_in_build": BUILD, "senses": senses})

    def finish(self, pos_by_unit):
        for entry, unit in zip(self.entries, self.units, strict=True):
            entry["key_at_creation"]["pos"] = pos_by_unit.get(unit["unit_key"], entry["key_at_creation"]["pos"] or "noun")
        self.sources.commit()
        self.vesum.commit()


def build_world():
    w = World()
    # Homograph pair: one VESUM entry each, separated by genitive and by the stress printed in the comment.
    for form, tags in (("альфа", "v_naz"), ("альфи", "v_rod"), ("альфі", "v_mis")):
        w.vesum_form(101, "альфа", form, f"noun:inanim:m:{tags}", f"а{A}льфа (перша)")
    for form, tags in (("альфа", "v_naz"), ("альфу", "v_rod"), ("альфі", "v_mis")):
        w.vesum_form(102, "альфа", form, f"noun:inanim:m:{tags}", f"альфа{A} (друга)")
    # Two active senses and one synonym group: the group cannot be aligned; it waits on the holding sense.
    w.ulif(1, "альфа", f"а{A}льфа", LABEL_M, "(перше; друге)", homonym=1, puls=("A2", "іменник"), holding=True,
           rows=[("називний", f"а{A}льфа", ""), ("родовий", f"а{A}льфи", ""), ("місцевий", f"на а{A}льфі", ""),
                 ("кличний", f"а{A}льфо*", "")],
           sections=[("synonyms", synonym_html(f"а{A}льфа", "перше значення", "синонімодин"))])
    w.ulif(2, "альфа", f"альфа{A}", LABEL_M, "(інше)", homonym=2,
           rows=[("називний", f"альфа{A}", ""), ("родовий", f"альфу{A}", ""), ("місцевий", f"на альфі{A}", "")],
           sections=[("synonyms", synonym_html(f"альфа{A}", "ключове значення", "синонім"))])
    # One word whose ULIF and VESUM paradigms overlap but differ (two datives against one, an extra VESUM
    # instrumental): the whole-set rule leaves VESUM unattached; unaligned groups wait on the unsplit sense.
    w.vesum_form(103, "бета", "бета", "noun:inanim:f:v_naz")
    w.vesum_form(103, "бета", "бети", "noun:inanim:f:v_rod")
    w.vesum_form(103, "бета", "бету", "noun:inanim:f:v_dav")
    w.vesum_form(103, "бета", "бетою", "noun:inanim:f:v_oru:arch")
    w.vesum_form(103, "бета", "бетоюх", "noun:inanim:f:v_oru")
    w.ulif(3, "бета", "бета", LABEL_F, "", puls=("B1", "іменник"),
           rows=[("називний", "бета", ""), ("родовий", "бети", ""), ("давальний", "бето, бету", ""),
                 ("орудний", "бетоюх", "")],
           sections=[("synonyms", synonym_html("бета", "перше", "один")),
                     ("synonyms", synonym_html("бета", "друге", "два")),
                     ("antonyms", antonym_html("бета", "анти", "ліве", "праве"))])
    # Doublet head, no VESUM entry, one sense and one synonym group: aligned by the one-unit rule.
    w.ulif(4, "гама", f"го{A}ло{A}ва", LABEL_F, "(єдине)", rows=[("називний", "голова", "")],
           sections=[("synonyms", synonym_html(f"го{A}ло{A}ва", "єдине", "сіль"))])
    # Adverb with a migrated stress row that disagrees with the ULIF headword.
    uws_raw = {"filled_at": None, "payload_json": json.dumps({"form": f"дельта{A}", "source": "ukrainian-word-stress"},
                                                            ensure_ascii=False),
               "phase": "migration", "section": "stress", "slug": "дельта", "source": "ukrainian-word-stress"}
    digest = foundation.digest(uws_raw)
    uws = {"source_id": "ukrainian_word_stress", "table": "enrichment", "row_key": {"slug": "дельта", "section": "stress"},
           "locator": "atlas0:enrichment:дельта/stress", "raw_row": uws_raw, "snapshot_id": SNAP + digest,
           "content_sha256": digest, "database": "atlas"}
    w.records.append(uws)
    w.sr.append({"source_record_id": opaque("sr_", w.next()), "source_id": "ukrainian_word_stress",
                 "aliases": [{"kind": "table_row", "key": "uws:row:1", "snapshot_id": uws["snapshot_id"]}],
                 "correspondence": [{"snapshot_id": uws["snapshot_id"], "status": "unique", "locator": uws["locator"]}]})
    w.vesum_form(105, "дельта", "дельта", "adv", pos="adv")
    w.ulif(5, "дельта", f"де{A}льта", "прислівник", "", extra=[uws])
    # A host entry whose phraseology repeats one aggregator record and quotes another; a single antonym group on
    # its unsplit-only card is held unresolved (an unsplit sense is never an active sense to align to).
    w.vesum_form(106, "ета", "ета", "noun:inanim:f:v_naz")
    w.ulif(6, "ета", "ета", LABEL_F, "", rows=[("називний", "ета", "")], sections=[
        ("phraseology", phrase_html("перша фраза", "Означення першої фрази", "Цитата першої фрази", "Автор Один")),
        ("phraseology", phrase_html("друга фраза", "Інше означення", "Інша цитата", "Автор Два")),
        ("antonyms", antonym_html("ета", "антиета", "ліве", "праве"))])
    # A proper name whose spelling VESUM knows only as a common noun: that evidence never attaches.
    w.vesum_form(107, "Ета", "Ета", "noun:inanim:f:v_naz")
    w.ulif(7, "ета", f"Е{A}та", "прізвище", "", homonym=2, rows=[("називний", f"Е{A}та", "")], kind="proper_name")
    w.mwe(1, "<ID>1</ID>|<fna>перша фраза</fna>|<fras>}}|перша фраза {{</fras>}}",
          "пер[']ш[/']а фраза. Означення першої фрази. Цитата першої фрази (Автор Один).")
    w.mwe(2, "друга фраза {{</fras>}}", "друга фраза. Зовсім інший текст (Автор Три).")
    w.finish({"ulif:partition:дельта:5": "adv"})
    return w


def make_inputs(w, scratch, registry=None):
    manifest = {"manifest_sha256": MANIFEST_SHA, "rules_version": "rules-v1-draft", "normaliser_version": "norm-v1",
                "selection": {"units": w.units, "source_records": w.records},
                "database_file_sha256": {"sources": "a" * 64, "atlas": "b" * 64, "vesum": "c" * 64}}
    registry = registry or {"schema_version": 1, "registry_version": 3, "entries": w.entries, "source_records": w.sr,
                            "events": w.events}
    register = {"schema_version": 2, "sources": [
        {"id": s, "appears_in": ["internal", "site", "dataset"]}
        for s in ("ulif", "vesum", "puls", "frazeolohichnyi", "ukrainian_word_stress")]}
    scratch.mkdir(parents=True, exist_ok=True)
    extract = scratch / "extract.sqlite"
    entry_ids = sorted(r["raw_row"]["id"] for r in w.records if r["table"] == "ulif_dictua_entries")
    extracted = src.write_extract(w.sources, entry_ids, extract)
    hashes = {"vesum_canonical": "5" * 64, "registry_file": "e" * 64, "register_entries": "f" * 64,
              "sources_file": "a" * 64, "atlas_file": "b" * 64, "manifest": MANIFEST_SHA, "frozen_rows_verified": 0,
              "extract_rows": extracted["tables"], "extract_sha256": extracted["content_sha256"]}
    sources = src.PilotSources(w.sources, w.vesum, w.raw)
    return wa.Inputs(manifest, registry, register, sources, hashes, wa.wp3_card_units(extract, set(entry_ids)))


@pytest.fixture(scope="module")
def world():
    return build_world()


@pytest.fixture
def inputs(world, tmp_path):
    return make_inputs(world, tmp_path)


@pytest.fixture
def result(inputs):
    return wa.build(inputs)


def card_of(result, key, *, nth=0):
    cards = [c for c in result["cards"].values() if c["key_at_creation"]["spelling"] == key]
    cards.sort(key=lambda c: c["key_at_creation"]["source_keys"][0]["key"])
    return cards[nth]


def assertions(card, field, **match):
    return [a for a in card["assertions"] if a["field"] == field and all(a.get(k) == v for k, v in match.items())]


def unit_by_head(inputs, head):
    return next(u for u in inputs.units if u["literal_head"] == head)


def strip_build(result):
    return {k: {f: v for f, v in c.items() if f != "build"} for k, c in result["cards"].items()}


def test_every_card_is_schema_valid_and_one_per_unit(result, inputs):
    validator = Draft202012Validator(SCHEMA)
    assert len(result["cards"]) == len(inputs.units) == 9
    for card in result["cards"].values():
        assert list(validator.iter_errors(card)) == []


def test_assembly_is_deterministic(inputs, result):
    again = wa.build(inputs)
    assert {k: foundation.digest(v) for k, v in again["cards"].items()} == {
        k: foundation.digest(v) for k, v in result["cards"].items()}
    assert again["build_id"] == result["build_id"]


def test_homographs_are_separated_by_paradigm_and_stress_and_linked(result):
    first, second = card_of(result, "альфа", nth=0), card_of(result, "альфа", nth=1)
    assert first["identity"]["method"] == "stress_and_paradigm" and first["identity"]["confidence"] == "high"
    assert first["fields"]["stress"]["state"] == "verified"
    assert first["fields"]["spelling"]["state"] == "verified"
    vesum_entries = {k["key"] for c in (first, second) for k in c["identity"]["source_keys"] if k["source_id"] == "vesum"}
    assert vesum_entries == {"vesum:entry:101", "vesum:entry:102"}
    links = [link for link in first["links"] if link["type"] == "homograph_of"]
    assert len(links) == 1 and links[0] == second["links"][0]
    assert links[0]["state"] == "active" and links[0]["basis"] == "derived" and links[0]["assertion_ids"]


def test_puls_level_is_spelling_ambiguous_on_a_shared_spelling_only(result):
    first = card_of(result, "альфа", nth=0)
    (cefr,) = assertions(first, "cefr")
    assert cefr["mapping"]["ambiguous"] is True and cefr["mapping"]["basis"] == "spelling"
    assert first["fields"]["cefr"]["values"][0]["mapping_evidenced"] is False
    (single,) = assertions(card_of(result, "бета"), "cefr")
    assert "ambiguous" not in single["mapping"]
    assert card_of(result, "бета")["fields"]["cefr"]["values"][0]["mapping_evidenced"] is True


def test_overlapping_paradigms_stay_unresolved_with_the_mismatch_visible(result):
    card = card_of(result, "бета")
    assert (card["identity"]["confidence"], card["identity"]["method"]) == ("unresolved", "unresolved")
    assert not [a for a in card["assertions"] if a["source_id"] == "vesum"]
    (held,) = [h for h in result["ledger"].cards[card["card_id"]]["held"] if h["kind"] == "identity"]
    assert held["candidates"] == ["vesum:entry:103"]
    assert held["evidence"]["vesum:entry:103"]["paradigm"] == "differs"
    # ULIF's own two datives remain its declared set, in its own slot.
    paradigm = card["fields"]["paradigm"]
    assert paradigm["propositions"]["v_dav.s"]["state"] == "variant"
    slots = {a["value"]["slot"] for a in assertions(card, "paradigm", source_id="ulif")}
    assert slots == {"v_naz.s", "v_rod.s", "v_dav.s", "v_oru.s"}


def test_asterisk_and_preposition_slots_are_held_not_asserted(result):
    card = card_of(result, "альфа", nth=0)
    slots = {a["value"]["slot"] for a in assertions(card, "paradigm", source_id="ulif")}
    assert slots == {"v_naz.s", "v_rod.s"}
    held = {(h["slot"], h["reason"]) for h in result["ledger"].cards[card["card_id"]]["held"]
            if h["kind"] == "paradigm_slot"}
    assert held == {("v_mis.s", "preposition_bound"), ("v_kly.s", "asterisk_marked")}


def test_vesum_slots_keep_source_forms_and_tags(result):
    card = card_of(result, "альфа", nth=0)
    vesum = {a["value"]["slot"]: a["value"] for a in assertions(card, "paradigm", source_id="vesum")}
    assert set(vesum) == {"v_naz.s", "v_rod.s", "v_mis.s"}
    assert vesum["v_rod.s"] == {"slot": "v_rod.s", "forms": ["альфи"], "tags": ["noun:inanim:m:v_rod"]}


def test_dual_stress_head_is_a_declared_variant_without_overlay(result):
    card = card_of(result, "голова")
    assert card["fields"]["stress"]["state"] == "variant"
    assert card["fields"]["stress"]["values"][0]["declared_set"] is True
    # No VESUM entry exists for the spelling: the card follows the checked ULIF division, medium at most.
    assert (card["identity"]["confidence"], card["identity"]["method"]) == ("medium", "unresolved")
    assert not [k for k in card["identity"]["source_keys"] if k["source_id"] == "vesum"]


def test_source_stress_conflict_is_never_auto_resolved(result):
    card = card_of(result, "дельта")
    assert card["identity"]["method"] == "unique_match"  # two invariable paradigms are equal
    assert card["fields"]["stress"]["state"] == "conflict" and card["fields"]["stress"]["selected"] is None
    values = {v["value_norm"] for v in card["fields"]["stress"]["values"]}
    assert values == {f"де{A}льта", f"дельта{A}"}
    uws = assertions(card, "stress", source_id="ukrainian_word_stress")[0]
    assert (uws["independence_group"], uws["tier"]) == ("G-ULIF", 2)


def test_proper_name_never_takes_common_noun_evidence(result):
    card = card_of(result, "Ета")
    assert card["card_kind"] == "proper_name"
    assert not [a for a in card["assertions"] if a["source_id"] == "vesum"]
    assert (card["identity"]["confidence"], card["identity"]["method"]) == ("medium", "unresolved")


def test_relation_groups_align_only_to_one_active_sense_and_one_unit(result):
    aligned = card_of(result, "голова")
    (sense,) = aligned["senses"]
    assert sense["fields"]["synonyms"]["state"] == "single-source"
    assert {"source_id": "ulif", "source_sense_key": "ulif:section:401", "mapped_by": wa.SENSE_RULE_ALIGNED} in \
        sense["sense_map"]
    second = card_of(result, "альфа", nth=1)
    assert second["senses"][0]["fields"]["synonyms"]["state"] == "single-source"
    # Nothing is ever asserted on the card subject for a sense-level field.
    for card in result["cards"].values():
        assert not [a for a in card["assertions"] if a["subject"]["kind"] == "card" and a["field"] in wa.SENSE_FIELDS]


def test_unaligned_groups_wait_whole_on_the_unsplit_sense(result):
    multi = card_of(result, "бета")
    (hold,) = multi["senses"]
    assert hold["state"] == "unsplit"
    held = [a for a in multi["assertions"] if a["field"] in wa.RELATION_FIELDS]
    assert len(held) == 3 and all(a["subject"] == {"kind": "sense", "id": hold["sense_id"]} for a in held)
    assert all(a["mapping"]["confidence"] == "unresolved" and a["mapping"]["ambiguous"] for a in held)
    assert all(a["source_record_id"] and a["locator"].endswith("[payload_json#/raw_html]") for a in held)
    assert {m["source_sense_key"] for m in hold["sense_map"] if m["mapped_by"] == wa.SENSE_RULE_HOLDING} == {
        "ulif:section:301", "ulif:section:302", "ulif:section:303"}
    # Held units never vote: the sense resolution is unverified and names them.
    assert hold["fields"]["synonyms"]["state"] == "unverified" and len(hold["fields"]["synonyms"]["non_voting"]) == 2
    ledger = result["ledger"].cards[multi["card_id"]]["fields"]
    assert ledger["synonyms"]["disposition"] == "unresolved" and ledger["synonyms"]["held_unsplit"] == 2


def test_one_group_on_an_unsplit_only_card_is_held_not_aligned(result):
    card = card_of(result, "ета")
    (antonym,) = assertions(card, "antonyms")
    assert antonym["mapping"]["confidence"] == "unresolved"
    assert card["senses"][0]["fields"]["antonyms"]["state"] == "unverified"


def test_two_active_senses_use_the_registry_holding_sense(result, inputs):
    first = card_of(result, "альфа", nth=0)
    states = [s["state"] for s in first["senses"]]
    assert states == ["active", "active", "unsplit"]
    (group,) = assertions(first, "synonyms")
    assert group["subject"]["id"] == first["senses"][2]["sense_id"]
    assert [s["sense_id"] for s in first["senses"]] == [
        s["sense_id"] for e in inputs.registry["entries"] if e["card_id"] == first["card_id"] for s in e["senses"]]


def test_missing_holding_sense_is_refused_never_minted(world, tmp_path):
    registry = copy.deepcopy({"schema_version": 1, "registry_version": 2, "entries": world.entries,
                              "source_records": world.sr, "events": world.events})
    holding_ids = {e["to"][0] for e in registry["events"] if e["build_id"] == HOLDING_BUILD}
    for entry in registry["entries"]:
        entry["senses"] = [s for s in entry["senses"] if s["sense_id"] not in holding_ids]
    registry["events"] = [e for e in registry["events"] if e["build_id"] != HOLDING_BUILD]
    with pytest.raises(wa.MissingAllocation):
        wa.build(make_inputs(world, tmp_path, registry))


def test_needs_holding_sense_rule():
    class Unit:
        def __init__(self, outcome="accepted"):
            self.candidate = type("C", (), {"outcome": outcome})()
    active, unsplit = {"sense_id": "a", "state": "active"}, {"sense_id": "u", "state": "unsplit"}
    assert wa.needs_holding_sense([active], {"synonyms": [Unit(), Unit()]})
    assert not wa.needs_holding_sense([active], {"synonyms": [Unit()]})
    assert wa.needs_holding_sense([active, dict(active, sense_id="b")], {"synonyms": [Unit()]})
    assert not wa.needs_holding_sense([unsplit], {"synonyms": [Unit(), Unit()]})
    assert wa.needs_holding_sense([active], {"synonyms": [Unit(), Unit("withheld")]})  # two units of the kind
    assert wa.aligned_sense([unsplit], [Unit()]) is None  # an unsplit sense is never aligned to


def test_sense_ids_and_seeds_come_from_the_registry(result, inputs):
    first = card_of(result, "альфа", nth=0)
    labels = [s["fields"]["sense_label"]["values"][0]["value_norm"] for s in first["senses"][:2]]
    assert labels == ["перше", "друге"]
    assert first["senses"][0]["seeded_from"].startswith("ulif_sense_gloss:")


def test_aggregator_forms_with_and_without_fna(result):
    forms = {a["value"] for c in result["cards"].values() for a in assertions(c, "mwe_form", source_id="frazeolohichnyi")}
    assert forms == {"перша фраза", "друга фраза"}


def test_same_record_phraseology_attaches_definition_and_example(result):
    card = card_of(result, "перша фраза")
    (sense,) = card["senses"]
    definition = sense["fields"]["definition_uk"]
    assert definition["state"] == "single-source"
    assert definition["values"][0]["value_norm"] == "означення першої фрази"
    assert [v["value_norm"] for v in sense["fields"]["examples"]["values"]] == ["цитата першої фрази (автор один)"]
    # ULIF and the aggregator share a lineage: never two groups.
    assert card["fields"]["mwe_form"]["values"][0]["independence_groups"] == ["G-ULIF"]


def test_same_form_with_a_different_record_is_held_not_merged(result):
    card = card_of(result, "друга фраза")
    held = [h for h in result["ledger"].cards[card["card_id"]]["held"] if h["kind"] == "ulif_phraseology"]
    assert held and held[0]["reason"] == "same_form_different_record"
    assert not card["senses"][0]["fields"]


def test_unmatched_phraseology_is_accounted(result):
    accepted = [u for u in result["ledger"].unattached if u["outcome"] == "accepted"]
    # The second host idiom has the printed form of an allocated card but not its record: it stays unattached.
    assert len(accepted) == 1 and accepted[0]["entry"] == 6


def test_missing_modern_meaning_is_explicit_never_filled(result):
    card = card_of(result, "бета")
    entry = result["ledger"].cards[card["card_id"]]["fields"]["definition_uk"]
    assert entry["disposition"] == "source_absent"
    assert not [a for a in card["assertions"] if a["field"] == "definition_uk"]
    assert result["ledger"].cards[card["card_id"]]["fields"]["russification_exposed"]["disposition"] == \
        "not_in_frozen_inputs"


def test_ledger_covers_every_applicable_field(result):
    for card_id, item in result["ledger"].cards.items():
        card = result["cards"][card_id]
        names = set(wa.MWE_FIELDS if card["card_kind"] == "mwe" else wa.CARD_FIELDS) | set(wa.SENSE_FIELDS)
        assert names <= set(item["fields"])


def test_unallocated_card_is_refused(inputs):
    broken = copy.copy(inputs)
    broken.registry = {**inputs.registry, "entries": inputs.registry["entries"][1:]}
    with pytest.raises(foundation.Refusal):
        wa.build(broken)


def test_assertion_without_registry_sense_evidence_is_refused(inputs):
    broken = copy.copy(inputs)
    broken.sense_events = {}
    with pytest.raises(wa.AssemblyError):
        wa.build(broken)


# --- consumed inputs and derived-form authentication (AC-P01) ---------------------------------------------

def test_mutated_form_with_zeroed_fingerprint_is_refused_and_changes_identity(tmp_path):
    clean = build_world()
    baseline = wa.build(make_inputs(clean, tmp_path / "a"))
    mutated = build_world()
    mutated.sources.execute("UPDATE ulif_forms SET form_unstressed='SYNTHETIC', form_stressed='SYNTHETIC', "
                            "source_entry_fingerprint=? WHERE entry_id=3 AND form_unstressed='бети'", ("0" * 64,))
    result = wa.build(make_inputs(mutated, tmp_path / "b"))
    card = card_of(result, "бета")
    assert not assertions(card, "paradigm", source_id="ulif")
    assert "SYNTHETIC" not in json.dumps(result["cards"], ensure_ascii=False)
    held = [h for h in result["ledger"].cards[card["card_id"]]["held"] if h["kind"] == "paradigm"]
    assert held[0]["reason"] == "forms_unauthenticated" and held[0]["detail"] == "stale_source_snapshot"
    assert result["build_id"] != baseline["build_id"]


def test_forms_with_preserved_fingerprints_but_changed_content_are_refused(tmp_path):
    mutated = build_world()
    mutated.sources.execute("UPDATE ulif_forms SET form_unstressed='SYNTHETIC' WHERE entry_id=3 "
                            "AND form_unstressed='бети'")
    inputs = make_inputs(mutated, tmp_path)
    result = wa.build(inputs)
    card = card_of(result, "бета")
    assert not assertions(card, "paradigm", source_id="ulif")
    assert inputs.sources.forms_status(3) == "content_mismatch"
    report = verify.verify(inputs, result)
    assert report["passed"], report  # the refused rows are held, not cited; their section record is accounted


def test_refused_sibling_forms_make_the_competing_match_unresolved(tmp_path):
    mutated = build_world()
    mutated.sources.execute("UPDATE ulif_forms SET source_entry_fingerprint=? WHERE entry_id=2", ("0" * 64,))
    result = wa.build(make_inputs(mutated, tmp_path))
    assert card_of(result, "альфа", nth=0)["identity"]["confidence"] == "unresolved"


def test_consistent_supplemental_change_changes_build_identity(tmp_path):
    baseline = wa.build(make_inputs(build_world(), tmp_path / "a"))
    changed = build_world()
    # A VESUM row for a spelling the build queried and found absent: absence evidence is a consumed input.
    changed.vesum_form(999, "голова", "голова", "noun:inanim:f:v_naz")
    result = wa.build(make_inputs(changed, tmp_path / "b"))
    assert result["build_id"] != baseline["build_id"]
    assert result["consumed"]["vesum_forms:голова"] != baseline["consumed"]["vesum_forms:голова"]
    assert result["block"]["inputs"]["S"]["consumed"]["content_sha256"] != \
        baseline["block"]["inputs"]["S"]["consumed"]["content_sha256"]


# --- suppression ---------------------------------------------------------------------------------------------

def selector_for(inputs, locator):
    record = inputs.record_ids[("ulif", locator)]
    return {"kind": "source_record", "source_id": "ulif", "source_record_id": record["source_record_id"],
            "on_ambiguous": "suppress_all_candidates"}


def entry(selector, name="sup-1"):
    return {"suppression_id": name, "issue": "https://example.invalid/8980", "date": "2026-10-15",
            "selector": selector, "scope": ["site"], "applies_to": {"reharvest": True, "rollback": True}}


def suppression(selector, name="sup-1"):
    return {"schema_version": "1", "entries": [entry(selector, name)]}


def content(field, spelling, value_norm=None, source="ulif", normaliser="norm-v1"):
    out = {"kind": "assertion_content", "source_id": source, "field": field, "subject_spelling": spelling,
           "normaliser_version": normaliser}
    if value_norm is not None:
        out["value_norm"] = value_norm
    return out


def test_source_record_withdrawal_recomputes_and_tombstones(inputs, result):
    locator = unit_by_head(inputs, f"а{A}льфа")["anchor_locator"]
    withdrawn = wa.build(inputs, suppression(selector_for(inputs, locator)))
    card = card_of(withdrawn, "альфа", nth=0)
    suppressed = [a for a in card["assertions"] if a["status"] == "suppressed"]
    assert suppressed and all(a["suppression_ref"] == "sup-1" for a in suppressed)
    # ULIF stress is gone; the VESUM comment stress remains and is now the only voice.
    assert card["fields"]["stress"]["state"] == "single-source"
    public = verify.public_projection(card)
    text = json.dumps(public, ensure_ascii=False)
    for a in suppressed:
        assert a["locator"] not in text
        stub = next(x for x in public["assertions"] if x["assertion_id"] == a["assertion_id"])
        assert set(stub) == {"assertion_id", "status", "suppression_ref"}
    # The withdrawn synonym group leaves the holding sense's map too.
    assert not [m for s in public["senses"] for m in s["sense_map"] if m["mapped_by"] == wa.SENSE_RULE_HOLDING]
    # Lifting the selector restores the previous bytes: rollback needs no other state.
    assert foundation.digest(wa.build(inputs, None)["cards"]) == foundation.digest(result["cards"])
    again = wa.build(inputs, suppression(selector_for(inputs, locator)))
    assert foundation.digest(again["cards"]) == foundation.digest(withdrawn["cards"])


def test_source_withdrawal_resolves_a_conflict_to_the_remaining_source(inputs):
    withdrawn = wa.build(inputs, suppression({"kind": "source", "source_id": "ukrainian_word_stress"}))
    card = card_of(withdrawn, "дельта")
    assert card["fields"]["stress"]["state"] == "single-source"
    assert withdrawn["takedown"][0]["cards"] == [card["card_id"]]
    assert len(withdrawn["takedown"][0]["assertions"]) == 1


def test_homograph_link_is_suppressed_when_its_evidence_goes(inputs):
    withdrawn = wa.build(inputs, suppression(content("spelling", "альфа", "альфа")))
    link = card_of(withdrawn, "альфа", nth=0)["links"][0]
    assert link["state"] == "suppressed"


def test_card_becomes_suppressed_when_every_assertion_is_withdrawn(inputs):
    only = unit_by_head(inputs, "ета")
    # Withdraw ULIF and VESUM for the host entry: a card with nothing left is suppressed, not empty.
    entries = [entry({"kind": "source", "source_id": s}, f"sup-{s}") for s in ("ulif", "vesum", "puls")]
    withdrawn = wa.build(inputs, {"schema_version": "1", "entries": entries})
    card = withdrawn["cards"][inputs.entry_by_unit[only["unit_key"]]["card_id"]]
    assert card["state"] == "suppressed"


def test_overlapping_selectors_reach_the_same_assertions_in_either_order(inputs):
    record = entry(selector_for(inputs, unit_by_head(inputs, f"а{A}льфа")["anchor_locator"]), "sup-b-record")
    whole = entry({"kind": "source", "source_id": "ulif"}, "sup-a-ulif")
    forward = wa.build(inputs, {"schema_version": "1", "entries": [whole, record]})
    reverse = wa.build(inputs, {"schema_version": "1", "entries": [record, whole]})
    assert strip_build(forward) == strip_build(reverse)
    credit = {t["suppression_id"]: set(t["assertions"]) for t in forward["takedown"]}
    assert credit["sup-b-record"] and credit["sup-b-record"] <= credit["sup-a-ulif"]  # overlap credited to both
    # The single reference is the smallest matching id, whatever the order.
    refs = {a["suppression_ref"] for c in reverse["cards"].values() for a in c["assertions"]
            if a["assertion_id"] in credit["sup-b-record"]}
    assert refs == {"sup-a-ulif"}
    # A selector that matches nothing in the original inventory still refuses.
    with pytest.raises(wa.AssemblyError, match="matches no assertion"):
        wa.build(inputs, {"schema_version": "1", "entries": [whole, entry(content("stress", "немає"), "sup-c")]})


def test_structured_values_are_withdrawn_by_their_exact_proposition(inputs, result):
    doublet = card_of(result, "голова")
    (stress,) = assertions(doublet, "stress", source_id="ulif")
    assert isinstance(stress["value"], list)
    members = stress["value_norm"].split("|")
    for value_norm in (stress["value_norm"], "|".join(reversed(members))):  # set order never matters
        withdrawn = wa.build(inputs, suppression(content("stress", "голова", value_norm)))
        assert withdrawn["takedown"][0]["assertions"] == [stress["assertion_id"]]
    # One member is not the declared set.
    with pytest.raises(wa.AssemblyError, match="matches no assertion"):
        wa.build(inputs, suppression(content("stress", "голова", members[0])))
    first = card_of(result, "альфа", nth=0)
    slot = next(a for a in assertions(first, "paradigm", source_id="ulif") if a["value"]["slot"] == "v_rod.s")
    withdrawn = wa.build(inputs, suppression(content("paradigm", "альфа", slot["value_norm"])))
    assert withdrawn["takedown"][0]["assertions"] == [slot["assertion_id"]]
    for wrong in (content("paradigm", "альфа", "v_naz.s=альфи"), content("paradigm", "бета", slot["value_norm"]),
                  content("paradigm", "альфа", slot["value_norm"], source="puls"),
                  content("stress", "альфа", slot["value_norm"])):
        with pytest.raises(wa.AssemblyError, match="matches no assertion"):
            wa.build(inputs, suppression(wrong))


def test_assertion_id_selector_falls_back_to_pinned_content_after_an_id_change(inputs, result):
    first = card_of(result, "альфа", nth=0)
    slot = next(a for a in assertions(first, "paradigm", source_id="ulif") if a["value"]["slot"] == "v_naz.s")
    fallback = content("paradigm", "альфа", slot["value_norm"])
    selector = {"kind": "assertion_id", "assertion_id": "wa_" + "0" * 24, "fallback": fallback}
    withdrawn = wa.build(inputs, suppression(selector))
    assert slot["assertion_id"] in withdrawn["takedown"][0]["assertions"]
    # An unavailable pinned normaliser fails closed, even when the id itself would match.
    pinned = {"kind": "assertion_id", "assertion_id": slot["assertion_id"],
              "fallback": dict(fallback, normaliser_version="norm-v9")}
    with pytest.raises(wa.AssemblyError, match="normaliser"):
        wa.build(inputs, suppression(pinned))


def test_every_exact_value_norm_selects_its_own_assertion(result):
    for card in result["cards"].values():
        for a in card["assertions"]:
            selector = content(a["field"], card["key_at_creation"]["spelling"], a["value_norm"], a["source_id"])
            assert wa.selector_matches(selector, a, card["key_at_creation"]["spelling"]), a["assertion_id"]


# --- verification ------------------------------------------------------------------------------------------

def test_verify_passes_and_catches_a_forged_locator(inputs, result):
    again = wa.build(inputs)
    report = verify.verify(inputs, result, again)
    assert report["passed"], report
    assert report["locators"]["checked"] > 50
    assert report["relation_units"] == {"passed": True, "units": 7, "aligned": 2, "held_unsplit": 5, "errors": {}}
    forged = copy.deepcopy(result)
    victim = next(c for c in forged["cards"].values() if c["key_at_creation"]["spelling"] == "бета")
    target = next(a for a in victim["assertions"] if a["field"] == "grammatical_label")
    target["value"] = "прислівник"
    bad = verify.verify(inputs, forged, again)
    assert bad["passed"] is False
    assert bad["assertion_identity"]["passed"] is False or bad["locators"]["passed"] is False


def test_verify_rejects_a_relation_unit_moved_to_the_card(inputs, result):
    moved = copy.deepcopy(result)
    card = card_of(moved, "бета")
    unit = next(a for a in card["assertions"] if a["field"] == "synonyms")
    unit["subject"] = {"kind": "card", "id": card["card_id"]}
    assert verify.verify(inputs, moved)["relation_units"]["passed"] is False


@pytest.mark.parametrize("selectors", [
    lambda i: [entry(selector_for(i, unit_by_head(i, f"а{A}льфа")["anchor_locator"]))],
    lambda i: [entry({"kind": "source", "source_id": "ukrainian_word_stress"})],
    lambda i: [entry({"kind": "source", "source_id": "ulif"}, "sup-a"),
               entry(selector_for(i, unit_by_head(i, f"а{A}льфа")["anchor_locator"]), "sup-b")],
    lambda i: [entry(content("stress", "голова", f"го{A}лова|голо{A}ва"))],
])
def test_withdrawn_builds_verify(inputs, selectors):
    suppressions = {"schema_version": "1", "entries": selectors(inputs)}
    withdrawn = wa.build(inputs, suppressions)
    report = verify.verify(inputs, withdrawn, wa.build(inputs, suppressions), suppressions)
    assert report["passed"], {k: v for k, v in report.items() if isinstance(v, dict) and not v["passed"]}
    assert report["public_projection"]["withdrawn_cards"] >= 1


def withdrawn_alpha(inputs):
    suppressions = suppression(selector_for(inputs, unit_by_head(inputs, f"а{A}льфа")["anchor_locator"]))
    return wa.build(inputs, suppressions), suppressions


def test_forged_or_deleted_suppressed_provenance_fails(inputs):
    withdrawn, suppressions = withdrawn_alpha(inputs)
    forged = copy.deepcopy(withdrawn)
    victim = next(a for c in forged["cards"].values() for a in c["assertions"] if a["status"] == "suppressed")
    victim["suppression_ref"] = "sup-forged"
    assert verify.verify(inputs, forged, None, suppressions)["withdrawal"]["passed"] is False
    deleted = copy.deepcopy(withdrawn)
    card = next(c for c in deleted["cards"].values() if any(a["status"] == "suppressed" for a in c["assertions"]))
    card["assertions"] = [a for a in card["assertions"] if a["status"] != "suppressed"]
    assert verify.verify(inputs, deleted, None, suppressions)["passed"] is False
    tampered = copy.deepcopy(withdrawn)
    victim = next(a for c in tampered["cards"].values() for a in c["assertions"] if a["status"] == "suppressed")
    victim["value_norm"] = "інше"
    assert verify.verify(inputs, tampered, None, suppressions)["assertion_identity"]["passed"] is False
    # A takedown that does not cover the declared selectors is refused.
    assert verify.verify(inputs, withdrawn, None, None)["withdrawal"]["passed"] is False


def test_withdrawn_evidence_leaking_into_the_public_projection_fails(inputs, monkeypatch):
    withdrawn, suppressions = withdrawn_alpha(inputs)
    real = verify.public_projection

    def leaky(card):
        public = real(card)
        for a in card["assertions"]:
            if a["status"] == "suppressed":
                public["identity"]["notes"].append(a["locator"])
                public["assertions"] = [a if x["assertion_id"] == a["assertion_id"] else x for x in public["assertions"]]
        return public

    monkeypatch.setattr(verify, "public_projection", leaky)
    report = verify.verify(inputs, withdrawn, None, suppressions)
    assert report["public_projection"]["passed"] is False
    assert {"tombstone_shape", "withdrawn_locator_in_public"} <= set(report["public_projection"]["errors"])


def test_rollback_with_current_selectors_never_revives_withdrawn_evidence(inputs):
    withdrawn, suppressions = withdrawn_alpha(inputs)
    reimport = wa.build(inputs, suppressions)  # previous inputs, current selectors (schema.md §12.1)
    assert foundation.digest(reimport["cards"]) == foundation.digest(withdrawn["cards"])
    assert all(a["status"] == "suppressed" for c in reimport["cards"].values() for a in c["assertions"]
               if a["assertion_id"] in withdrawn["takedown"][0]["assertions"])


def test_rehearsal_reports_every_withdrawal_check(world, tmp_path):
    inputs = make_inputs(world, tmp_path)
    for unit in inputs.units:
        if unit["literal_head"] == f"а{A}льфа":
            unit["categories"] = ["withdrawal_rehearsal_candidate"]
    outcome = verify.rehearse(inputs)
    assert outcome["passed"], outcome
    assert outcome["order_independent"] is True
    assert set(outcome["scenarios"]) == {
        "source_record", "source", "overlap_source_then_record", "overlap_record_then_source", "content_stress_set",
        "content_paradigm_slot", "assertion_id_fallback"}
    assert all(s["withdrawn_build_verifies"] for s in outcome["scenarios"].values())


def test_label_rules():
    assert wa.label_part_of_speech("множинний іменник") == "іменник"
    assert wa.label_part_of_speech("прізвище") == "іменник"
    assert wa.label_part_of_speech("дієслово недоконаного виду") == "дієслово"
    assert wa.label_part_of_speech("абревіатура") is None
    assert wa.parse_gender("іменник чоловічого або жіночого роду, істота") == ["f", "m"]
    assert wa.parse_gender("множинний іменник") == []
    assert wa.parse_aspect("дієслово недоконаного виду") == "imperf"
    assert wa.parse_aspect("дієслово доконаного виду") == "perf"
    assert wa.parse_aspect("дієслово недоконаного і доконаного виду") == "both"
    assert wa.parse_aspect("іменник") is None


def test_allocator_label_helpers_are_the_rules_assembly_reuses():
    from scripts.atlas.allocate_pilot_identities import is_proper_name, label_pos

    assert label_pos("числівник порядковий") == "adj"  # VESUM treats ordinals as adjectives
    assert label_pos("займенник") is None  # decided from VESUM tags, never from the label
    assert is_proper_name("прізвище", "Шуба", "") is True
    assert is_proper_name("іменник жіночого роду", "Ріка", "(річка в Україні)") is True
    assert is_proper_name("іменник жіночого роду", "ріка", "(річка в Україні)") is False


# --- host-only output containment (AC-P06) -------------------------------------------------------------------

def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                   check=True, capture_output=True, text=True, timeout=60, env=sanitized_git_env())


@pytest.fixture
def checkouts(tmp_path):
    """A disposable primary checkout with an internal dispatch worktree and an external sibling worktree."""
    primary = tmp_path / "primary"
    primary.mkdir()
    git(primary, "init", "-q", "-b", "main")
    (primary / ".gitignore").write_text("scratch/\n.worktrees/\n")
    (primary / "tracked.txt").write_text("x\n")
    git(primary, "add", ".")
    git(primary, "commit", "-q", "-m", "init")
    current = primary / ".worktrees" / "dispatch" / "agent" / "task"
    git(primary, "worktree", "add", "-q", "-b", "task", str(current))
    sibling = tmp_path / "elsewhere" / "sibling"
    git(primary, "worktree", "add", "-q", "-b", "sibling", str(sibling))
    external = tmp_path / "external-scratch"
    external.mkdir()
    return {"primary": primary, "current": current, "sibling": sibling, "external": external}


def test_output_is_written_only_to_host_scratch_or_ignored_paths_of_this_checkout(checkouts):
    current = checkouts["current"]
    wa.require_host_only([checkouts["external"] / "cards" / "x.json"], current)
    wa.require_host_only([current / "scratch" / "out" / "cards" / "x.json"], current)
    for protected in (current / "docs" / "out", current / "tracked.txt", checkouts["primary"] / "docs" / "out",
                      checkouts["primary"] / "scratch" / "out", checkouts["sibling"] / "scratch" / "out",
                      checkouts["sibling"] / "docs"):
        with pytest.raises(wa.AssemblyError):
            wa.require_host_only([protected / "ledger.json"], current)


def test_symlinked_destinations_resolve_before_the_decision(checkouts):
    current, external = checkouts["current"], checkouts["external"]
    link = external / "into-sibling"
    link.symlink_to(checkouts["sibling"], target_is_directory=True)
    with pytest.raises(wa.AssemblyError):
        wa.require_host_only([link / "scratch" / "cards"], current)
    # A host directory whose cards subdirectory points into the primary checkout is refused too.
    output = external / "out"
    output.mkdir()
    (output / "cards").symlink_to(checkouts["primary"], target_is_directory=True)
    with pytest.raises(wa.AssemblyError):
        wa.write_host_only(output, {"report.json": {}}, {"wc_x": {}}, current)
    assert not (checkouts["primary"] / "wc_x.json").exists() and not (output / "report.json").exists()


def test_refused_output_creates_and_deletes_nothing(checkouts):
    current, primary = checkouts["current"], checkouts["primary"]
    target = primary / "docs" / "cards-output"
    with pytest.raises(wa.AssemblyError):
        wa.write_host_only(target, {"report.json": {}}, {"wc_x": {}}, current)
    assert not target.exists()
    sentinel_dir = primary / "keep" / "cards"
    sentinel_dir.mkdir(parents=True)
    sentinel = sentinel_dir / "wc_old.json"
    sentinel.write_text("{}")
    with pytest.raises(wa.AssemblyError):
        wa.write_host_only(primary / "keep", {"report.json": {}}, {"wc_x": {}}, current)
    assert sentinel.read_text() == "{}" and not (primary / "keep" / "report.json").exists()


def test_allowed_output_replaces_stale_cards(checkouts):
    output = checkouts["external"] / "build"
    (output / "cards").mkdir(parents=True)
    (output / "cards" / "wc_stale.json").write_text("{}")
    wa.write_host_only(output, {"report.json": {"n": 1}}, {"wc_new": {"card_id": "wc_new"}}, checkouts["current"])
    assert sorted(p.name for p in (output / "cards").iterdir()) == ["wc_new.json"]
    assert json.loads((output / "report.json").read_text()) == {"n": 1}


def test_discovery_uncertainty_fails_closed(checkouts, monkeypatch, tmp_path):
    monkeypatch.setattr(containment, "registered_worktrees", lambda root: [])
    with pytest.raises(wa.AssemblyError, match="registered worktrees"):
        wa.require_host_only([checkouts["external"] / "x"], checkouts["current"])
    monkeypatch.undo()
    lone = tmp_path / "not-a-repo"
    lone.mkdir()
    with pytest.raises(wa.AssemblyError):
        wa.require_host_only([checkouts["external"] / "x"], lone)


def test_ignore_check_errors_fail_closed(checkouts, monkeypatch):
    real = subprocess.run

    def broken(argv, *args, **kwargs):
        if "check-ignore" in argv:
            return subprocess.CompletedProcess(argv, 128, "", "fatal")
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(wa.subprocess, "run", broken)
    with pytest.raises(wa.AssemblyError, match="ignore rules"):
        wa.require_host_only([checkouts["current"] / "scratch" / "x"], checkouts["current"])


def test_cli_rehearse_and_build_writes_are_guarded(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(wa, "require_host_only", lambda paths, anchor=None: calls.append([Path(p) for p in paths]))
    wa.write_host_only(tmp_path / "rehearse", {"takedown-rehearsal.json": {"passed": True}})
    assert calls and tmp_path / "rehearse" / "takedown-rehearsal.json" in calls[0]
    calls.clear()
    result = {"build_id": "b", "ledger": wa.Ledger(), "block": {"inputs": {}, "rules_version": "r"}, "takedown": [],
              "cards": {"wc_x": {}}}
    wa.write_output(tmp_path / "build", result, {})
    assert tmp_path / "build" / "cards" / "wc_x.json" in calls[0]


@pytest.fixture
def host_scratch():
    """Host scratch outside every checkout of this repository. pytest's tmp_path may live inside the repository's
    git directory (the pre-push gate puts its basetemp there), which the guard rightly refuses."""
    base = Path(tempfile.gettempdir()).resolve()
    if base.is_relative_to(containment.resolve_main_root(Path(wa.__file__))):
        pytest.skip("the temporary directory is inside the repository; no host scratch is available")
    with tempfile.TemporaryDirectory(prefix="word-card-host-") as scratch:
        yield Path(scratch)


def test_this_repository_refuses_tracked_destinations(host_scratch):
    root = Path(wa.__file__).resolve().parents[2]
    with pytest.raises(wa.AssemblyError):
        wa.require_host_only([root / "docs" / "atlas" / "word-cards" / "cards-output" / "ledger.json"])
    wa.require_host_only([host_scratch / "cards" / "x.json"])  # outside the repository: fine
    wa.require_host_only([root / "batch_state" / "reports" / "probe" / "cards" / "x.json"])  # ignored here: fine


def host_stores_available():
    try:
        return all(wa.store_path(name, None).exists() for name in ("sources", "vesum", "atlas")) and \
            wa.raw_cache_path(wa.store_path("sources", None)).exists()
    except foundation.Refusal:
        return False


@pytest.mark.skipif(not host_stores_available(), reason="held sources are host-only")
def test_host_pilot_builds_and_verifies_end_to_end(host_scratch, capsys, monkeypatch):
    """Host-only product proof through the real CLI: the frozen pilot assembles over the canonical read-only
    stores, every locator resolves, derived forms authenticate, relation units are conserved, rebuild is identical."""
    root = Path(wa.__file__).resolve().parents[2]
    monkeypatch.chdir(root)
    monkeypatch.delenv("LU_ULIF_RAW_CACHE", raising=False)
    stores = [arg for name in ("sources", "vesum", "atlas") for arg in (f"--{name}-db", str(wa.store_path(name, None)))]
    inputs = ["--manifest", "registry/atlas/pilot/pilot-v1.json", "--registry", "registry/atlas/identity/registry.json",
              "--register", "docs/sources/permissions-register.yaml", *stores]
    args = [*inputs, "--output", str(host_scratch / "pilot")]
    assert wa.main(["build", *args]) == 0
    built = json.loads(capsys.readouterr().out)
    assert built["cards"] == 150 and built["relation_units"]["total"] == 158
    assert built["relation_units"]["on_card_subject"] == 0 and built["heldout_isolation"] == "unverified"
    assert wa.main(["verify", *args]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] is True
    assert report["conservation"]["cards"] == 150
    assert report["relation_units"]["units"] == 158
    assert report["source_records"]["frozen"] == report["source_records"]["cited"] + report["source_records"]["held"]
    # A protected destination is refused before anything is written.
    refused = root / "docs" / "atlas" / "word-cards" / "cards-output"
    assert wa.main(["build", *inputs, "--output", str(refused)]) == 1
    assert not refused.exists()
    shutil.rmtree(host_scratch / "pilot")
