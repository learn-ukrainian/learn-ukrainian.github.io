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
from contextlib import ExitStack
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas import word_card_verify as verify
from scripts.atlas.allocate_pilot_identities import BUILD_PREFIX, HOLDING_BASIS, HOLDING_BUILD_PREFIX
from scripts.atlas.word_card_resolver import _project, aid, card_version
from scripts.common.git_context import sanitized_git_env
from scripts.common.scratch import ensure_scratch_root
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
ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "word-card-v1.schema.json").read_text())
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
        self.source_record(rec, f"{source}:row:{raw['id']}")
        return rec

    def source_record(self, rec, alias):
        """The persistent record of one frozen row and its original mint (the foundation allocation)."""
        sr_id = opaque("sr_", self.next())
        self.sr.append({"source_record_id": sr_id, "source_id": rec["source_id"],
                        "aliases": [{"kind": "table_row", "key": alias, "snapshot_id": rec["snapshot_id"]}],
                        "correspondence": [{"snapshot_id": rec["snapshot_id"], "status": "unique",
                                            "locator": rec["locator"]}]})
        self.events.append({"event_id": f"ie_{self.next():04d}", "kind": "source_record_mint",
                            "build_id": "pilot@sha256:" + MANIFEST_SHA, "to": [sr_id], "evidence": rec["locator"]})

    def ulif(self, entry_id, query, head, label, gloss="", homonym=1, rows=(), sections=(), puls=None, extra=(),
             kind="lexeme", holding=()):
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

    def add_card(self, unit, kind, key, gloss, holding=()):
        """One explicit draft allocation: the card, its seed senses and (when the build needs one) the appended
        holding sense, each with its original mint evidence in the shape the allocator records."""
        number = self.next()
        card_id = opaque("wc_", number)
        anchor = next(r for r in self.records if r["locator"] == unit["anchor_locator"])
        source = unit["anchor_locator"].split(":")[0]
        key = {**key, "source_keys": [{"source_id": source, "key": unit["unit_key"], "snapshot_id": "s"},
                                      {"source_id": source, "key": unit["anchor_locator"], "snapshot_id": "s"}]}
        versions = {"rules_version": "rules-v1-draft", "normaliser_version": "norm-v1"}
        self.events.append({"event_id": f"ie_{self.next():04d}", "kind": "mint", "build_id": BUILD, "cards": [card_id],
                            "evidence": foundation.canonical({
                                "source_partition": unit["unit_key"], "anchor_locator": anchor["locator"],
                                "snapshot_id": anchor["snapshot_id"], "source_row_sha256": anchor["content_sha256"],
                                **versions}).decode()})
        senses = []
        if kind == "mwe" or not gloss:
            parts = [("unsplit", unit["anchor_locator"] + "#unsplit", None, BUILD)]
        else:
            parts = [("active", f"ulif:entry:{anchor['raw_row']['id']} sense_gloss[{i}]", p.strip(), BUILD)
                     for i, p in enumerate(gloss[1:-1].split(";"))]
        if holding:  # the registry's append-only holding sense (allocate_pilot_identities --append-holding)
            parts.append(("unsplit", unit["anchor_locator"] + "#unsplit", None, HOLDING_BUILD))
        for order, (state, source_unit, literal, build) in enumerate(parts, start=1):
            sense_id = opaque("ws_", self.next())
            senses.append({"sense_id": sense_id, "order": order, "state": state})
            basis = "ULIF structured sense_gloss" if literal else "unaligned source unit; no structured seed"
            evidence = {"source_partition": unit["unit_key"], "anchor_locator": anchor["locator"],
                        "source_unit": source_unit, "source_row_sha256": anchor["content_sha256"], "state": state,
                        "literal_gloss_unit": literal, "basis": basis, **versions}
            if build == HOLDING_BUILD:
                evidence.update(basis=HOLDING_BASIS, held_units=list(holding))
            self.events.append({"event_id": f"ie_{self.next():04d}", "kind": "sense_mint", "build_id": build,
                                "to": [sense_id], "evidence": foundation.canonical(evidence).decode()})
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
    w.ulif(1, "альфа", f"а{A}льфа", LABEL_M, "(перше; друге)", homonym=1, puls=("A2", "іменник"),
           holding=["ulif:section:101"],
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
    w.source_record(uws, "uws:row:1")
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


# The clean synthetic world is its own explicit frozen allocation, pinned by the literal digest of its identity
# projection (allocate_pilot_identities.identity_allocation_check). Frozen once; never recomputed from a candidate.
SYNTHETIC_ALLOCATION_DIGEST = "9b5263fa58ad40108255bb3342215d9fd23f92317ff83a17fc586e76e3c634d0"
# The same synthetic allocation before its holding epoch: a distinct explicit allocation (registry v2).
SYNTHETIC_WITHOUT_HOLDING_DIGEST = "2f8f83b2ff75102e32b4f5dddae01e576393528a287589716ed5184125e33cbb"


@pytest.fixture(autouse=True)
def synthetic_allocation(request, monkeypatch):
    """Pin the synthetic allocation, except for tests over the committed pilot (`committed_pilot`), which keep the
    production pin."""
    if "committed_pilot" not in request.fixturenames:
        monkeypatch.setattr(allocator, "ASSEMBLY_ALLOCATION_DIGEST", SYNTHETIC_ALLOCATION_DIGEST, raising=False)


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


def test_missing_holding_sense_is_refused_never_minted(world, tmp_path, monkeypatch):
    registry = copy.deepcopy({"schema_version": 1, "registry_version": 2, "entries": world.entries,
                              "source_records": world.sr, "events": world.events})
    holding_ids = {e["to"][0] for e in registry["events"] if e["build_id"] == HOLDING_BUILD}
    for entry in registry["entries"]:
        entry["senses"] = [s for s in entry["senses"] if s["sense_id"] not in holding_ids]
    registry["events"] = [e for e in registry["events"] if e["build_id"] != HOLDING_BUILD]
    with pytest.raises(wa.MissingAllocation):
        wa.build(make_inputs(world, tmp_path, registry))
    # Even as its own explicit allocation (pinned), a registry without the holding sense the build needs refuses.
    monkeypatch.setattr(allocator, "ASSEMBLY_ALLOCATION_DIGEST", SYNTHETIC_WITHOUT_HOLDING_DIGEST)
    with pytest.raises(wa.MissingAllocation, match="unsplit holding sense"):
        wa.build(make_inputs(world, tmp_path / "pinned", registry))


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


def test_unconsumed_database_file_changes_do_not_change_card_content(inputs, result, monkeypatch):
    monkeypatch.setitem(inputs.hashes, "sources_file", "0" * 64)
    monkeypatch.setitem(inputs.hashes, "atlas_file", "1" * 64)
    rebuilt = wa.build(inputs)
    assert rebuilt["build_id"] == result["build_id"]
    assert foundation.digest(rebuilt["cards"]) == foundation.digest(result["cards"])
    assert verify.verify(inputs, rebuilt, result)["passed"] is True

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


def alpha_ulif_spelling(result):
    return next(a for a in card_of(result, "альфа", nth=0)["assertions"]
                if a["source_id"] == "ulif" and a["field"] == "spelling")


def suppressed_ids(build):
    return sorted(a["assertion_id"] for c in build["cards"].values() for a in c["assertions"]
                  if a["status"] == "suppressed")


def test_present_assertion_id_withdraws_only_itself_whatever_its_fallback_reaches(inputs, result):
    target = alpha_ulif_spelling(result)
    fallback = content("spelling", "альфа")  # reaches the ULIF spelling of BOTH альфа homographs
    reach = wa.build(inputs, suppression(fallback))["takedown"][0]
    assert len(reach["assertions"]) == 2 and len(reach["cards"]) == 2
    s = suppression({"kind": "assertion_id", "assertion_id": target["assertion_id"], "fallback": fallback})
    withdrawn = wa.build(inputs, s)
    assert suppressed_ids(withdrawn) == [target["assertion_id"]]
    assert withdrawn["takedown"][0]["assertions"] == [target["assertion_id"]]
    assert verify.verify(inputs, withdrawn, wa.build(inputs, s), s)["passed"]
    # Mode is decided on the whole original inventory: once the id is gone the fallback reaches both cards.
    gone = suppression({"kind": "assertion_id", "assertion_id": "wa_" + "0" * 24, "fallback": fallback})
    assert suppressed_ids(wa.build(inputs, gone)) == sorted(reach["assertions"])
    # Overlapping with a source selector, either order: the same union and the same per-selector credit.
    by_id = entry(s["entries"][0]["selector"], "sup-b-id")
    whole = entry({"kind": "source", "source_id": "ulif"}, "sup-a-ulif")
    forward = wa.build(inputs, {"schema_version": "1", "entries": [by_id, whole]})
    reverse = wa.build(inputs, {"schema_version": "1", "entries": [whole, by_id]})
    assert strip_build(forward) == strip_build(reverse)
    assert {t["suppression_id"]: t["assertions"] for t in forward["takedown"]}["sup-b-id"] == [target["assertion_id"]]
    both = {"schema_version": "1", "entries": [by_id, whole]}
    assert verify.verify(inputs, forward, None, both)["withdrawal"]["passed"]


def test_present_assertion_id_whose_fallback_does_not_describe_it_is_refused(inputs, result):
    target = alpha_ulif_spelling(result)
    selector = {"kind": "assertion_id", "assertion_id": target["assertion_id"], "fallback": content("spelling", "бета")}
    with pytest.raises(wa.AssemblyError, match="fallback does not describe"):
        wa.build(inputs, suppression(selector))


def test_source_record_selector_must_agree_with_its_registry_record(inputs, result):
    good = selector_for(inputs, unit_by_head(inputs, f"а{A}льфа")["anchor_locator"])
    record = next(sr for sr in inputs.registry["source_records"] if sr["source_record_id"] == good["source_record_id"])
    with pytest.raises(wa.AssemblyError, match="source_id contradicts"):
        wa.build(inputs, suppression(dict(good, source_id="puls")))
    with pytest.raises(wa.MissingAllocation, match="does not allocate"):
        wa.build(inputs, suppression(dict(good, source_record_id="sr_" + "0" * 12)))
    with pytest.raises(wa.AssemblyError, match="alias_at_creation"):
        wa.build(inputs, suppression(dict(good, alias_at_creation="ulif:row:not-this-record")))
    pinned = suppression(dict(good, alias_at_creation=record["aliases"][0]["key"]))
    withdrawn = wa.build(inputs, pinned)
    assert {a["source_id"] for c in withdrawn["cards"].values() for a in c["assertions"]
            if a["status"] == "suppressed"} == {"ulif"}
    assert verify.verify(inputs, withdrawn, None, pinned)["withdrawal"]["passed"]


def test_verify_recomputes_each_selector_scope_without_the_assembler(inputs, result, monkeypatch):
    """The pre-repair matcher (id OR fallback, source_record id without its source) must not verify."""
    target = alpha_ulif_spelling(result)

    def unscoped(selector, assertion, spelling):
        if selector["kind"] == "assertion_id":
            return assertion["assertion_id"] == selector["assertion_id"] or unscoped(
                selector["fallback"], assertion, spelling)
        if selector["kind"] == "source_record":
            return assertion.get("source_record_id") == selector["source_record_id"]
        return original(selector, assertion, spelling)

    original = wa.selector_matches
    monkeypatch.setattr(wa, "selector_matches", unscoped)
    monkeypatch.setattr(wa, "resolve_selector", lambda selector, inventory: selector)
    monkeypatch.setattr(wa, "check_selector", lambda selector, records: None)
    over = suppression({"kind": "assertion_id", "assertion_id": target["assertion_id"],
                        "fallback": content("spelling", "альфа")})
    widened = wa.build(inputs, over)
    assert len(suppressed_ids(widened)) == 2
    report = verify.verify(inputs, widened, None, over)["withdrawal"]
    assert report["passed"] is False and {"selector_scope", "suppressed_outside_selectors"} <= set(report["errors"])
    wrong_source = suppression(dict(selector_for(inputs, unit_by_head(inputs, f"а{A}льфа")["anchor_locator"]),
                                    source_id="puls"))
    report = verify.verify(inputs, wa.build(inputs, wrong_source), None, wrong_source)["withdrawal"]
    assert report["passed"] is False and "selector_inconsistent" in report["errors"]


def test_intended_matches_reads_stored_propositions_and_refuses_what_it_cannot_evaluate(inputs, result):
    inventory = {a["assertion_id"]: (a, c["key_at_creation"]["spelling"])
                 for c in result["cards"].values() for a in c["assertions"]}
    records = {sr["source_record_id"]: sr for sr in inputs.registry["source_records"]}
    target = alpha_ulif_spelling(result)
    exact = content("spelling", "альфа", target["value_norm"] + ".")  # norm-v1 cuts trailing punctuation
    assert target["assertion_id"] in verify.intended_matches(exact, inventory, records)
    assert verify.intended_matches(content("spelling", "альфа", "інше"), inventory, records) == set()
    assert verify.intended_matches(content("spelling", "альфа", normaliser="norm-v9"), inventory, records) is None
    assert verify.intended_matches({"kind": "card"}, inventory, records) is None


def ulif_entry_records(registry):
    return [sr for sr in registry["source_records"] if sr["source_id"] == "ulif" and any(
        c.get("locator", "").startswith("ulif:ulif_dictua_entries:id:") for c in sr["correspondence"])]


def later_snapshot_registry(world):
    """A copy of the registry where a later snapshot reuses record A's row locator for record B and observes a
    stronger alias of A: history that must never rebind the frozen row or its extraction-time key."""
    registry = copy.deepcopy({"schema_version": 1, "registry_version": 3, "entries": world.entries,
                              "source_records": world.sr, "events": world.events})
    a, b = ulif_entry_records(registry)[:2]
    later = "later-snapshot@sha256:" + "f" * 64
    b["aliases"].append({"kind": "table_row", "key": "ulif:row:later-local", "snapshot_id": later})
    b["correspondence"].append({"snapshot_id": later, "status": "unique", "locator": a["correspondence"][0]["locator"]})
    a["aliases"].append({"kind": "uid", "key": "ulif:uid:later", "snapshot_id": later})
    return registry, a, b


def test_frozen_rows_bind_through_their_own_snapshot_only(world, tmp_path, result):
    registry, a, b = later_snapshot_registry(world)
    inputs = make_inputs(world, tmp_path / "later", registry)
    locator = a["correspondence"][0]["locator"]
    assert inputs.record_ids[("ulif", locator)]["source_record_id"] == a["source_record_id"]
    rebuilt = wa.build(inputs)
    cited = [x for c in rebuilt["cards"].values() for x in c["assertions"] if x["locator"].split(" ")[0] == locator]
    assert cited and {x["source_record_id"] for x in cited} == {a["source_record_id"]} != {b["source_record_id"]}
    assert "ulif:uid:later" not in {x.get("source_record_key") for c in rebuilt["cards"].values()
                                    for x in c["assertions"]}
    assert strip_build(rebuilt) == strip_build(result)  # later history changes nothing in the frozen build
    assert verify.verify(inputs, rebuilt)["passed"]


CORRESPONDENCE_DAMAGE = ["missing", "held_own", "competing_unique", "competing_hold", "alias_elsewhere"]


@pytest.mark.parametrize("damage", CORRESPONDENCE_DAMAGE)
def test_unresolved_or_competing_frozen_correspondence_refuses_before_output(world, tmp_path, damage):
    registry = copy.deepcopy({"schema_version": 1, "registry_version": 3, "entries": world.entries,
                              "source_records": world.sr, "events": world.events})
    damage_correspondence(registry, damage)
    expected = wa.MissingAllocation if damage == "missing" else wa.AssemblyError
    with pytest.raises(expected, match="own snapshot"):
        make_inputs(world, tmp_path, registry)


def damage_correspondence(registry, damage):
    """Damage the first ULIF entry record's own-snapshot correspondence; returns that record's frozen locator."""
    a, b = ulif_entry_records(registry)[:2]
    own = a["correspondence"][0]
    locator = own["locator"]
    if damage == "missing":
        a["correspondence"] = []
    elif damage == "held_own":
        own.update(status="held", candidates=[own["locator"], b["correspondence"][0]["locator"]], hold="test")
    elif damage == "competing_unique":
        b["correspondence"].append({"snapshot_id": own["snapshot_id"], "status": "unique", "locator": own["locator"]})
    elif damage == "competing_hold":
        b["correspondence"].append({"snapshot_id": own["snapshot_id"], "status": "ambiguous", "hold": "test",
                                    "candidates": [own["locator"], b["correspondence"][0]["locator"]]})
    else:
        for alias in a["aliases"]:
            alias["snapshot_id"] = "other@sha256:" + "1" * 64
    return locator


def test_verify_rejects_a_frozen_row_credited_to_another_record(inputs, result):
    a, b = ulif_entry_records(inputs.registry)[:2]
    locator = a["correspondence"][0]["locator"]
    forged = copy.deepcopy(result)
    for card in forged["cards"].values():
        for x in card["assertions"]:
            if x["locator"].split(" ")[0] == locator:
                x["source_record_id"], x["source_record_key"] = b["source_record_id"], b["aliases"][0]["key"]
    report = verify.verify(inputs, forged)["source_records"]
    assert report["passed"] is False and report["errors"]["snapshot_binding"] > 0
    rekeyed = copy.deepcopy(result)
    victim = next(x for c in rekeyed["cards"].values() for x in c["assertions"] if x["locator"].split(" ")[0] == locator)
    victim["source_record_key"] = "ulif:uid:later"
    assert verify.verify(inputs, rekeyed)["source_records"]["errors"]["key_outside_snapshot"] == 1


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
    proper = [{"tags": "noun:prop:geo"}]
    common = [{"tags": "noun:inanim:f"}]
    assert is_proper_name(LABEL_F, "Ета", "(острів)", proper) is True
    assert is_proper_name(LABEL_F, "Ета", "(спільне значення)", proper, common) is False
    assert is_proper_name(LABEL_F, "Ета", "", proper, common) is True
    assert is_proper_name(LABEL_F, "Ета", "", [], common) is True
    assert is_proper_name(LABEL_F, "Ета", "", common) is False
    assert is_proper_name(LABEL_F, "Ета", "") is False


def test_allocator_keeps_vesum_proper_head_separate_from_lowercase_common_word():
    w = build_world()
    try:
        w.vesum.row_factory = sqlite3.Row
        w.vesum_form(201, "Ета", "Ета", "noun:inanim:f:v_naz:prop:geo")
        unit = copy.deepcopy(w.units[6])
        anchor = copy.deepcopy(next(r for r in w.records if r["locator"] == unit["anchor_locator"]))
        anchor["raw_row"]["grammatical_label"] = LABEL_F
        # The same exact-case spelling also has a common analysis in the base world.
        w.vesum.execute("DELETE FROM forms_all WHERE entry_id=107")
        kind, _key, proof = allocator.creation(unit, {anchor["locator"]: anchor}, w.vesum)
        assert kind == "proper_name"
        assert {r["entry_id"] for r in proof} == {201}
    finally:
        w.sources.close()
        w.vesum.close()
        w.raw.close()


@pytest.mark.parametrize("word,pos,guide,proper,expected", [
    ("ета", "іменник", "", True, False),
    ("Ета", "іменник", "", True, False),
    ("Ета", "іменник", "(місто)", True, True),
    ("ета", "власна назва", "", True, False),
    ("Ета", "власна назва", "", True, True),
    ("Ета", "власна назва", "", False, False),
    ("ета", "іменник", "", False, True),
])
def test_puls_requires_source_evidence_for_the_same_identity(word, pos, guide, proper, expected):
    assert wa.puls_matches_identity({"word": word, "pos": pos, "guideword": guide}, "Ета", proper) is expected


def test_puls_can_scope_a_proper_abbreviation_without_admitting_its_lowercase_homonym():
    row = {"word": "АБВ", "pos": "іменник", "guideword": ""}
    assert wa.puls_matches_identity(row, "АБВ", True, "абревіатура") is True
    assert wa.puls_matches_identity(row, "АБВ", True, LABEL_F) is False
    row["word"] = "абв"
    assert wa.puls_matches_identity(row, "АБВ", True, "абревіатура") is False


def test_proper_name_does_not_receive_common_cefr_or_senses(inputs, monkeypatch):
    proper_unit = unit_by_head(inputs, f"Е{A}та")
    common_unit = unit_by_head(inputs, f"а{A}льфа")
    puls = next(k for k in common_unit["source_record_keys"] if inputs.records[k]["source_id"] == "puls")
    monkeypatch.setitem(proper_unit, "source_record_keys", [*proper_unit["source_record_keys"], puls])
    result = wa.build(inputs)
    proper = card_of(result, "Ета")
    assert not assertions(proper, "cefr")
    assert not [a for a in proper["assertions"] if a["subject"]["kind"] == "sense"]
    assert proper["card_id"] not in wa.learner_cards(result["cards"])
    assert result["ledger"].cards[proper["card_id"]]["fields"]["cefr"]["disposition"] == "held"
    assert assertions(card_of(result, "альфа"), "cefr")
    assertion = {"source_id": "puls", "field": "cefr", "subject": {"kind": "card", "id": proper["card_id"]}}
    assert verify.source_routes(inputs, proper_unit, inputs.entry_by_unit[proper_unit["unit_key"]], assertion) == []


def test_learner_release_excludes_unscoped_names_and_accounts_for_every_identity(result, host_scratch):
    output = host_scratch / "learner-release"
    report = wa.learner_accounting(result)
    wa.write_output(output, result, report)
    published = {p.stem: foundation.load(p) for p in (output / "cards").glob("*.json")}
    assert len(published) == report["cards"] == 8
    assert report["allocated_cards"] == 9 and report["excluded_cards"] == 1
    assert all(c["card_kind"] != "proper_name" for c in published.values())
    assert all(e["id"] in published for c in published.values() for link in c["links"] for e in link["endpoints"])
    assert all(c["build"]["card_version"] == card_version(_project(c)) for c in published.values())
    ledger = foundation.load(output / "ledger.json")
    assert set(published).isdisjoint(ledger["excluded_cards"])
    assert set(published) | set(ledger["excluded_cards"]) == set(ledger["cards"]) == set(result["cards"])
    assert report["field_dispositions_by_field"]["grammatical_label"] == {"asserted": 6}


def test_proper_name_needs_active_unambiguous_source_scope_to_enter_learner_set(result):
    name = copy.deepcopy(card_of(result, "Ета"))
    card_id = name["card_id"]
    scope = {"source_id": "puls", "field": "cefr", "status": "active", "mapping": {"confidence": "medium"}}
    name["assertions"].append(scope)
    assert set(wa.learner_cards({card_id: name})) == {card_id}
    scope["mapping"]["ambiguous"] = True
    assert wa.learner_cards({card_id: name}) == {}
    scope["mapping"]["ambiguous"] = False
    scope["status"] = "suppressed"
    assert wa.learner_cards({card_id: name}) == {}
    scope["status"] = "active"
    scope["review"] = {"status": "rejected"}
    assert wa.learner_cards({card_id: name}) == {}


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
              "cards": {"wc_x": {"card_kind": "lexeme", "links": []}}}
    wa.write_output(tmp_path / "build", result, {})
    assert tmp_path / "build" / "cards" / "wc_x.json" in calls[0]


@pytest.fixture
def host_scratch():
    """Host scratch outside every checkout of this repository. pytest's tmp_path may live inside the repository's
    git directory (the pre-push gate puts its basetemp there), which the guard rightly refuses."""
    base = Path(tempfile.gettempdir()).resolve()
    if base.is_relative_to(containment.resolve_main_root(Path(wa.__file__))):
        pytest.skip("the temporary directory is inside the repository; no host scratch is available")
    with tempfile.TemporaryDirectory(prefix="word-card-host-", dir=ensure_scratch_root()) as scratch:
        yield Path(scratch)


def test_this_repository_refuses_tracked_destinations(host_scratch):
    root = Path(wa.__file__).resolve().parents[2]
    with pytest.raises(wa.AssemblyError):
        wa.require_host_only([root / "docs" / "atlas" / "word-cards" / "cards-output" / "ledger.json"])
    wa.require_host_only([host_scratch / "cards" / "x.json"])  # outside the repository: fine
    wa.require_host_only([root / "batch_state" / "reports" / "probe" / "cards" / "x.json"])  # ignored here: fine


def host_stores_available():
    try:
        primary = containment.resolve_main_root(ROOT)
        return all((primary / "data" / f"{name}.db").exists() for name in ("sources", "vesum", "atlas")) and \
            wa.raw_cache_path(primary / "data/sources.db").exists()
    except foundation.Refusal:
        return False


@pytest.mark.skipif(not host_stores_available(), reason="held sources are host-only")
@pytest.mark.usefixtures("committed_pilot")  # the real pilot under the production allocation pin
def test_host_pilot_builds_and_verifies_end_to_end(host_scratch, capsys, monkeypatch):
    """Host-only product proof through the real CLI: the frozen pilot assembles over the canonical read-only
    stores, every locator resolves, derived forms authenticate, relation units are conserved, rebuild is identical."""
    root = Path(wa.__file__).resolve().parents[2]
    monkeypatch.chdir(root)
    monkeypatch.delenv("LU_ULIF_RAW_CACHE", raising=False)
    primary = containment.resolve_main_root(ROOT)
    stores = [arg for name in ("sources", "vesum", "atlas")
              for arg in (f"--{name}-db", str(primary / "data" / f"{name}.db"))]
    inputs = ["--manifest", "registry/atlas/pilot/pilot-v1.json", "--registry", "registry/atlas/identity/registry.json",
              "--register", "docs/sources/permissions-register.yaml", *stores]
    args = [*inputs, "--output", str(host_scratch / "pilot")]
    assert wa.main(["build", *args]) == 0
    built = json.loads(capsys.readouterr().out)
    assert built["cards"] == 138 and built["allocated_cards"] == 150 and built["excluded_cards"] == 12
    assert built["relation_units"]["total"] == 158
    published = [foundation.load(p) for p in (host_scratch / "pilot/cards").glob("*.json")]
    assert len(published) == 138
    names = [c for c in published if c["card_kind"] == "proper_name"]
    assert len(names) == 1 and names[0]["key_at_creation"]["spelling"] == "ЮНЕСКО"
    assert [(a["source_id"], a["value"]) for a in assertions(names[0], "cefr")] == [("puls", "B1")]
    # Source-backed capitalisation of a common learner word is retained.
    assert any(c["key_at_creation"]["spelling"] == "Батьківщина" and c["card_kind"] == "lexeme" for c in published)
    assert [c["key_at_creation"]["spelling"] for c in published
            if c["key_at_creation"]["spelling"].casefold() == "мама"] == ["мама"]
    assert built["relation_units"]["on_card_subject"] == 0 and built["heldout_isolation"] == "unverified"
    assert wa.main(["verify", *args]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] is True
    assert report["conservation"]["cards"] == 150
    assert report["on_disk"]["cards"] == 138
    assert report["relation_units"]["units"] == 158
    assert report["source_records"]["frozen"] == report["source_records"]["cited"] + report["source_records"]["held"]
    # A protected destination is refused before anything is written.
    refused = root / "docs" / "atlas" / "word-cards" / "cards-output"
    assert wa.main(["build", *inputs, "--output", str(refused)]) == 1
    assert not refused.exists()
    shutil.rmtree(host_scratch / "pilot")


# --- R3-F1: persistent identities stay bound to their frozen creation and mint evidence -----------------------

ALLOCATION_REFUSAL = "Pilot allocation differs from frozen creation/mint evidence"


def registry_copy(world):
    """A private copy of the world's registry: the module-scoped world is never mutated."""
    return copy.deepcopy({"schema_version": 1, "registry_version": 3, "entries": world.entries,
                          "source_records": world.sr, "events": world.events})


def identities(registry):
    return ([e["card_id"] for e in registry["entries"]] + [s["sense_id"] for e in registry["entries"]
                                                           for s in e["senses"]]
            + [r["source_record_id"] for r in registry["source_records"]])


def swap_card_ids(registry, left, right):
    """Exchange two allocated card ids; keys, senses, creation builds and every mint event stay where they were."""
    a, b = (next(e for e in registry["entries"] if e["card_id"] == i) for i in (left, right))
    a["card_id"], b["card_id"] = right, left


def retarget_card_id(registry, old, new):
    """Rename one card coherently: its entry and every mint event that names it."""
    next(e for e in registry["entries"] if e["card_id"] == old)["card_id"] = new
    for event in registry["events"]:
        if event.get("cards") == [old]:
            event["cards"] = [new]


def swap_source_record_ids(registry, left, right):
    """Exchange two persistent source-record ids and the targets of their own mint events (when present); source
    ids, aliases, correspondence, locators and creation evidence stay where they were."""
    swap = {left: right, right: left}
    for record in registry["source_records"]:
        record["source_record_id"] = swap.get(record["source_record_id"], record["source_record_id"])
    for event in registry["events"]:
        if event["kind"] == "source_record_mint":
            event["to"] = [swap.get(event["to"][0], event["to"][0])]


def test_r3f1_build_rejects_swapped_persistent_card_ids(world, tmp_path, inputs, result):
    assert verify.verify(inputs, result)["passed"]  # unchanged control
    first, second = [u for u in inputs.units if u["entry_type"] == "lexeme_candidate"][:2]
    left, right = (inputs.entry_by_unit[u["unit_key"]]["card_id"] for u in (first, second))
    registry = registry_copy(world)
    swap_card_ids(registry, left, right)
    # Same count, same unique identity set: only the binding of two persistent ids to their units changed.
    assert sorted(identities(registry)) == sorted(identities(inputs.registry))
    assert len(set(identities(registry))) == len(identities(registry))
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(make_inputs(world, tmp_path / "swapped", registry))
    # A coherent retarget of the entry id and its mint target is still a different allocation.
    registry = registry_copy(world)
    retarget_card_id(registry, left, opaque("wc_", 31_000))
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(make_inputs(world, tmp_path / "retargeted", registry))


def test_r3f1_build_rejects_unsplit_promotion_against_mint(world, tmp_path, inputs, result):
    unit = unit_by_head(inputs, "ета")
    entry = inputs.entry_by_unit[unit["unit_key"]]
    (sense,) = entry["senses"]
    assert sense["state"] == "unsplit" and inputs.sense_events[sense["sense_id"]]["literal_gloss_unit"] is None
    (antonym,) = assertions(result["cards"][entry["card_id"]], "antonyms")
    assert antonym["mapping"]["confidence"] == "unresolved"  # unchanged control: held, never aligned
    registry = registry_copy(world)
    promoted = next(e for e in registry["entries"] if e["card_id"] == entry["card_id"])
    promoted["senses"][0]["state"] = "active"  # the mint evidence and every creation field stay unchanged
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(make_inputs(world, tmp_path / "promoted", registry))


def test_r3f1_build_rejects_coherent_source_record_id_swap(world, tmp_path, inputs, result):
    assert verify.verify(inputs, result)["passed"]  # unchanged control
    a, b = ulif_entry_records(inputs.registry)[:2]
    for record in (a, b):
        locator = record["correspondence"][0]["locator"]
        assert inputs.record_ids[("ulif", locator)]["source_record_id"] == record["source_record_id"]
    registry = registry_copy(world)
    swap_source_record_ids(registry, a["source_record_id"], b["source_record_id"])
    assert sorted(identities(registry)) == sorted(identities(inputs.registry))
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(make_inputs(world, tmp_path / "swapped", registry))


def resign(card):
    """Recompute a forged card's mutable digests (assertion ids, card version) so only the binding is wrong."""
    for a in card["assertions"]:
        a["assertion_id"] = aid(a["source_id"], a["snapshot_id"], a["locator"], a["subject"], a["field"],
                                a["value_norm"], a["extraction_version"])
    wa._recompute(card)
    card["build"]["card_version"] = card_version(_project(card))
    return card


def rebind_card(card, new_id):
    """Give a card another id, carrying its card-subject assertions along (a coherent output rebinding)."""
    card["card_id"] = new_id
    for a in card["assertions"]:
        if a["subject"]["kind"] == "card":
            a["subject"]["id"] = new_id


def two_card_ids(inputs):
    first, second = [u for u in inputs.units if u["entry_type"] == "lexeme_candidate"][:2]
    return [inputs.entry_by_unit[u["unit_key"]]["card_id"] for u in (first, second)]


def stale_inputs(world, scratch, damage):
    """Valid inputs whose registry or one derived view is damaged after construction."""
    candidate = make_inputs(world, scratch, registry_copy(world))
    damage(candidate)
    return candidate


def swap_values(mapping, first, second):
    mapping[first], mapping[second] = mapping[second], mapping[first]


def promote_after_construction(i):
    entry = i.entry_by_unit[unit_by_head(i, "ета")["unit_key"]]
    entry["senses"][0]["state"] = "active"  # the registry's own entry object: registry and view change together


CACHE_DAMAGE = {
    "registry_card_swap": lambda i: swap_card_ids(i.registry, *two_card_ids(i)),
    "registry_promotion": promote_after_construction,
    "entry_by_unit": lambda i: swap_values(i.entry_by_unit, *[u["unit_key"] for u in i.units[:2]]),
    "sense_events": lambda i: i.sense_events.update({
        sid: {**ev, "source_unit": "forged"} for sid, ev in list(i.sense_events.items())[:1]}),
    "record_ids": lambda i: swap_values(i.record_ids, *list(i.record_ids)[:2]),
    "units_view": lambda i: setattr(i, "units", i.units[:-1]),
    "records_view": lambda i: setattr(i, "records", {
        **i.records, i.units[0]["anchor_locator"]: {**i.records[i.units[0]["anchor_locator"]], "snapshot_id": "x"}}),
    "malformed_manifest_unit": lambda i: setattr(i, "manifest", {**i.manifest, "selection": {
        **i.manifest["selection"], "units": [{k: v for k, v in u.items() if k != "anchor_locator"} for u in i.units]}}),
}


@pytest.mark.parametrize("damage", sorted(CACHE_DAMAGE))
def test_r3f1_rechecks_allocation_and_views_after_construction(world, tmp_path, result, damage):
    candidate = stale_inputs(world, tmp_path / damage, CACHE_DAMAGE[damage])
    began = []
    candidate.sources.begin = lambda: began.append(True)
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(candidate)
    assert not began  # refused before any source read
    report = verify.verify(candidate, result)
    assert report == {"input_allocation": {"passed": False, "errors": {"allocation_refused": 1}}, "passed": False}
    # The views are refused, never silently refreshed: a second attempt refuses the same way.
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        candidate.check_allocation()


def forged_report(inputs, result, edit, again=None):
    """Verify a supplied output changed by `edit` (which returns the cards it touched); inputs stay valid."""
    forged = copy.deepcopy(result)
    for card in edit(forged["cards"]):
        resign(card)
    return verify.verify(inputs, forged, again)


def forge_sense_state(cards):
    card = card_of({"cards": cards}, "ета")
    card["senses"][0]["state"] = "active"
    return [card]


def forge_sense_order(cards):
    card = card_of({"cards": cards}, "альфа", nth=0)
    card["senses"][0]["order"], card["senses"][1]["order"] = 2, 1
    return [card]


def forge_seeded_from(cards):
    card = card_of({"cards": cards}, "альфа", nth=0)
    card["senses"][0]["seeded_from"] = card["senses"][1]["seeded_from"]
    return [card]


def forge_registry_sense_map(cards):
    card = card_of({"cards": cards}, "альфа", nth=0)
    card["senses"][0]["sense_map"][0] = dict(card["senses"][1]["sense_map"][0])
    return [card]


@pytest.mark.parametrize(("forgery", "error"), [
    (forge_sense_state, "sense_inventory"), (forge_sense_order, "sense_inventory"),
    (forge_seeded_from, "seeded_from"), (forge_registry_sense_map, "registry_sense_map")])
def test_r3f1_verify_rejects_independent_sense_promotion(inputs, result, forgery, error):
    report = forged_report(inputs, result, forgery)
    assert report["passed"] is False
    assert report["identity_binding"]["passed"] is False and error in report["identity_binding"]["errors"]


def forge_dictionary_key(cards):
    card_id = card_of({"cards": cards}, "бета")["card_id"]
    cards[opaque("wc_", 31_001)] = cards.pop(card_id)
    return []


def forge_embedded_id(cards):
    card = card_of({"cards": cards}, "бета")
    del cards[card["card_id"]]
    rebind_card(card, opaque("wc_", 31_002))
    cards[card["card_id"]] = card
    return [card]


def forge_homograph_swap(cards):
    """Two cards of one spelling exchange identities; every locator still names that spelling."""
    left, right = card_of({"cards": cards}, "альфа", nth=0), card_of({"cards": cards}, "альфа", nth=1)
    left_id, right_id = left["card_id"], right["card_id"]
    rebind_card(left, right_id)
    rebind_card(right, left_id)
    cards[left_id], cards[right_id] = right, left
    return [left, right]


def forge_creation_key(cards):
    card = card_of({"cards": cards}, "голова")
    card["key_at_creation"]["pos"] = "verb"
    return [card]


def forge_creation_source_key(cards):
    card = card_of({"cards": cards}, "голова")
    card["key_at_creation"]["source_keys"][0]["key"] = card_of({"cards": cards}, "бета")[
        "key_at_creation"]["source_keys"][0]["key"]
    return [card]


def forge_card_kind(cards):
    card = card_of({"cards": cards}, "голова")
    card["card_kind"] = "proper_name"
    return [card]


def forge_sense_owner(cards):
    left, right = card_of({"cards": cards}, "бета"), card_of({"cards": cards}, "ета")
    left["senses"], right["senses"] = right["senses"], left["senses"]
    return [left, right]


@pytest.mark.parametrize(("forgery", "error"), [
    (forge_dictionary_key, "inventory"), (forge_embedded_id, "inventory"),
    (forge_homograph_swap, "key_at_creation"), (forge_creation_key, "key_at_creation"),
    (forge_creation_source_key, "key_at_creation"), (forge_card_kind, "card_kind"),
    (forge_sense_owner, "sense_inventory")])
def test_r3f1_verify_rejects_independent_card_rebinding(inputs, result, forgery, error):
    report = forged_report(inputs, result, forgery)
    assert report["passed"] is False
    assert report["identity_binding"]["passed"] is False and error in report["identity_binding"]["errors"]


def forge_registry_source_unit(cards):
    card = card_of({"cards": cards}, "бета")
    card["senses"][0]["sense_map"][0]["source_sense_key"] = "ulif:ulif_dictua_entries:id:4#unsplit"
    return [card]


def forge_rule_label(cards):
    card = card_of({"cards": cards}, "бета")
    live = next(u for u in card["senses"][0]["sense_map"] if u["mapped_by"] == wa.SENSE_RULE_HOLDING)
    live["mapped_by"] = wa.SENSE_RULE_ALIGNED
    return [card]


def forge_moved_live_map(cards):
    card = card_of({"cards": cards}, "альфа", nth=0)
    holder, first = card["senses"][2], card["senses"][0]
    moved = [u for u in holder["sense_map"] if u["mapped_by"] == wa.SENSE_RULE_HOLDING]
    holder["sense_map"] = [u for u in holder["sense_map"] if u not in moved]
    first["sense_map"] += [dict(u, mapped_by=wa.SENSE_RULE_ALIGNED) for u in moved]
    return [card]


def forge_confidence_promotion(cards):
    """A held group promoted to an aligned one, coherently in its assertion and the live sense map."""
    card = card_of({"cards": cards}, "ета")
    (antonym,) = assertions(card, "antonyms")
    antonym["mapping"] = {"confidence": "high", "basis": "sense", "note": "one active card sense and one source group"}
    for u in card["senses"][0]["sense_map"]:
        if u["mapped_by"] == wa.SENSE_RULE_HOLDING:
            u["mapped_by"] = wa.SENSE_RULE_ALIGNED
    return [card]


@pytest.mark.parametrize(("forgery", "check", "error"), [
    (forge_registry_source_unit, "identity_binding", "registry_sense_map"),
    (forge_rule_label, "identity_binding", "live_sense_map"),
    (forge_moved_live_map, "identity_binding", "live_sense_map"),
    (forge_confidence_promotion, "relation_units", "mapping")])
def test_r3f1_verify_checks_live_and_registry_sense_maps(inputs, result, forgery, check, error):
    report = forged_report(inputs, result, forgery)
    assert report["passed"] is False and report[check]["passed"] is False and error in report[check]["errors"]


def test_r3f1_withdrawn_relation_keeps_registry_provenance_and_verifies(inputs):
    withdrawn, suppressions = withdrawn_alpha(inputs)
    card = card_of(withdrawn, "альфа", nth=0)
    holder = card["senses"][2]
    assert [u["mapped_by"] for u in holder["sense_map"]] == ["registry:rules-v1-draft"]  # live map gone only
    report = verify.verify(inputs, withdrawn, None, suppressions)
    assert report["passed"], {k: v for k, v in report.items() if isinstance(v, dict) and not v["passed"]}
    assert report["identity_binding"] == {"passed": True, "errors": {}}


def frozen_record(inputs, locator):
    return inputs.record_ids[("ulif", locator)]


def forge_other_record(inputs):
    a, b = ulif_entry_records(inputs.registry)[:2]
    locator = a["correspondence"][0]["locator"]

    def edit(cards):
        touched = []
        for card in cards.values():
            for x in card["assertions"]:
                if x["locator"].split(" ")[0] == locator:
                    x["source_record_id"], x["source_record_key"] = b["source_record_id"], b["aliases"][0]["key"]
                    touched.append(card)
        return touched
    return edit


def forge_key_outside_snapshot(inputs):
    locator = ulif_entry_records(inputs.registry)[0]["correspondence"][0]["locator"]

    def edit(cards):
        card = next(c for c in cards.values() for x in c["assertions"] if x["locator"].split(" ")[0] == locator)
        next(x for x in card["assertions"] if x["locator"].split(" ")[0] == locator)["source_record_key"] = \
            "ulif:uid:later"
        return [card]
    return edit


def forge_foreign_source(inputs):
    puls = next(sr for sr in inputs.registry["source_records"] if sr["source_id"] == "puls")
    locator = ulif_entry_records(inputs.registry)[0]["correspondence"][0]["locator"]

    def edit(cards):
        card = next(c for c in cards.values() for x in c["assertions"] if x["locator"].split(" ")[0] == locator)
        victim = next(x for x in card["assertions"] if x["locator"].split(" ")[0] == locator)
        victim["source_record_id"], victim["source_record_key"] = puls["source_record_id"], puls["aliases"][0]["key"]
        return [card]
    return edit


@pytest.mark.parametrize(("forgery", "error"), [
    (forge_other_record, "snapshot_binding"), (forge_key_outside_snapshot, "key_outside_snapshot"),
    (forge_foreign_source, "source")])
def test_r3f1_verify_rejects_independent_source_record_rebinding(inputs, result, forgery, error):
    report = forged_report(inputs, result, forgery(inputs))
    assert report["passed"] is False
    assert report["source_records"]["passed"] is False and error in report["source_records"]["errors"]


def test_r3f1_output_rejects_coherent_foreign_homograph_row(inputs, result):
    assert verify.verify(inputs, result)["passed"]
    forged = copy.deepcopy(result)
    victim = alpha_ulif_spelling(forged)
    foreign = next(a for a in card_of(result, "альфа", nth=1)["assertions"]
                   if a["source_id"] == "ulif" and a["field"] == "spelling")
    for key in ("locator", "source_record_id", "source_record_key", "snapshot_id"):
        victim[key] = foreign[key]
    resign(card_of(forged, "альфа", nth=0))
    report = verify.verify(inputs, forged)  # audited inputs unchanged; no rebuilt-output oracle
    assert all(report[k]["passed"] for k in ("schema", "input_allocation", "identity_binding",
                                             "assertion_identity", "locators", "public_projection"))
    assert report["passed"] is False
    assert report["source_records"]["errors"]["locator_outside_subject"] == 1


@pytest.mark.parametrize(("source", "field"), [
    ("ulif", "spelling"), ("ulif", "paradigm"), ("ulif", "synonyms"), ("ulif", "definition_uk"),
    ("frazeolohichnyi", "mwe_form"), ("puls", "cefr"), ("vesum", "spelling")])
def test_r3f1_output_rejects_forged_snapshot(inputs, result, source, field):
    forged = copy.deepcopy(result)
    card, victim = next((c, a) for c in forged["cards"].values() for a in c["assertions"]
                        if a["source_id"] == source and a["field"] == field)
    victim["snapshot_id"] = "selected-row@sha256:" + "1" * 64
    resign(card)
    report = verify.verify(inputs, forged)
    assert all(report[k]["passed"] for k in ("schema", "assertion_identity", "locators", "public_projection"))
    assert report["passed"] is False
    assert report["source_records"]["errors"]["snapshot_binding"] == 1


@pytest.mark.parametrize("removed", [("source_record_id",), ("source_record_key",),
                                     ("source_record_id", "source_record_key")])
def test_r3f1_output_rejects_removed_persistent_attribution(inputs, result, removed):
    forged = copy.deepcopy(result)
    victim = alpha_ulif_spelling(forged)
    for key in removed:
        del victim[key]
    resign(card_of(forged, "альфа", nth=0))
    report = verify.verify(inputs, forged)
    assert report["schema"]["passed"] and report["assertion_identity"]["passed"]
    assert report["passed"] is False
    assert report["source_records"]["errors"]["missing_attribution"] == 1


def test_r3f1_output_cannot_disguise_frozen_attribution_as_supplemental_vesum(inputs, result):
    forged = copy.deepcopy(result)
    victim = alpha_ulif_spelling(forged)
    victim.update(source_id="vesum", snapshot_id="vesum@" + inputs.hashes["vesum_canonical"][:16],
                  independence_group="G-VESUM", tier=1)
    victim["licence_ref"]["register_source_id"] = "vesum"
    del victim["source_record_id"], victim["source_record_key"]
    resign(card_of(forged, "альфа", nth=0))
    report = verify.verify(inputs, forged)
    assert report["schema"]["passed"] and report["register_lineage"]["passed"]
    assert report["locators"]["passed"] and report["assertion_identity"]["passed"]
    assert report["passed"] is False
    assert report["source_records"]["errors"]["locator_outside_subject"] == 1


@pytest.mark.parametrize("field", ["spelling", "paradigm"])
def test_r3_output_rejects_foreign_vesum_homograph(inputs, result, field):
    assert verify.verify(inputs, result)["passed"]
    forged = copy.deepcopy(result)
    card = card_of(forged, "альфа", nth=0)
    foreign = next(a for a in card_of(result, "альфа", nth=1)["assertions"]
                   if a["source_id"] == "vesum" and a["field"] == field)
    assert foreign["locator"].startswith("vesum:entry:102 ")
    victim = next(a for a in card["assertions"] if a["source_id"] == "vesum" and a["field"] == field)
    victim.update(copy.deepcopy(foreign))
    victim["subject"] = {"kind": "card", "id": card["card_id"]}
    # Even a matching output identity claim cannot authorize another homograph's evidence.
    card["identity"] = copy.deepcopy(card_of(result, "альфа", nth=1)["identity"])
    resign(card)
    report = verify.verify(inputs, forged)
    assert all(report[k]["passed"] for k in ("schema", "assertion_identity", "locators", "public_projection"))
    assert report["passed"] is False and report["source_records"]["passed"] is False
    assert report["source_records"]["errors"]["vesum_entry_mismatch"] == 1


def test_r3_output_rejects_common_noun_vesum_entry_on_proper_name(inputs, result):
    assert verify.verify(inputs, result)["passed"]
    forged = copy.deepcopy(result)
    card = card_of(forged, "Ета")
    victim = next(a for a in card["assertions"] if a["source_id"] == "ulif" and a["field"] == "spelling")
    victim.update(source_id="vesum", locator="vesum:entry:107 [lemma]",
                  snapshot_id="vesum@" + inputs.hashes["vesum_canonical"][:16],
                  independence_group="G-VESUM", tier=1)
    victim["licence_ref"]["register_source_id"] = "vesum"
    del victim["source_record_id"], victim["source_record_key"]
    resign(card)
    report = verify.verify(inputs, forged)
    assert all(report[k]["passed"] for k in ("schema", "register_lineage", "assertion_identity", "locators",
                                             "public_projection"))
    assert report["passed"] is False and report["source_records"]["passed"] is False
    assert report["source_records"]["errors"]["vesum_entry_mismatch"] == 1


def test_r3f1_record_withdrawal_cannot_certify_an_escaped_assertion(inputs, result):
    target = alpha_ulif_spelling(result)
    selectors = suppression({"kind": "source_record", "source_id": "ulif",
                             "source_record_id": target["source_record_id"]})
    control = wa.build(inputs, selectors)
    assert alpha_ulif_spelling(control)["status"] == "suppressed"
    assert verify.verify(inputs, control, None, selectors)["passed"]
    forged = copy.deepcopy(result)
    victim = alpha_ulif_spelling(forged)
    del victim["source_record_id"], victim["source_record_key"]
    forged["takedown"] = wa.apply_suppressions(forged["cards"], selectors, inputs.registry["source_records"])
    for card in forged["cards"].values():
        resign(card)
    assert victim["status"] == "active"  # reproduce the previous withdrawal bypass
    report = verify.verify(inputs, forged, None, selectors)
    assert report["passed"] is False and report["withdrawal"]["passed"] is False
    assert report["source_records"]["errors"]["missing_attribution"] == 1
    assert report["withdrawal"]["errors"]["selector_scope"] == 1
    assert report["withdrawal"]["errors"]["suppressed_outside_selectors"] == 1


def test_r3f1_verify_rejects_a_rebound_held_ledger_source_record(tmp_path):
    held_world = build_world()
    held_world.sources.execute("UPDATE ulif_forms SET source_entry_fingerprint=? WHERE entry_id=3", ("0" * 64,))
    inputs = make_inputs(held_world, tmp_path)
    result = wa.build(inputs)
    card = card_of(result, "бета")
    (held,) = [h for h in result["ledger"].cards[card["card_id"]]["held"] if h.get("source_record_id")]
    assert verify.verify(inputs, result)["passed"]  # unchanged control: the refused forms' record is held
    other = frozen_record(inputs, unit_by_head(inputs, f"а{A}льфа")["anchor_locator"])["source_record_id"]
    held["source_record_id"] = other  # another card's frozen record, cited by that card
    report = verify.verify(inputs, result)
    assert report["passed"] is False and report["source_records"]["errors"].get("held_unbound") == 1


def test_r3f1_identity_verification_does_not_rebuild_output(inputs, result, monkeypatch):
    def rebuilt(*args, **kwargs):
        raise AssertionError("verification must never rebuild the output it checks")

    for name in ("build", "card_json", "refresh_sense_maps"):
        monkeypatch.setattr(wa, name, rebuilt)
    clean = verify.verify(inputs, result, None)
    assert clean["passed"] and clean["identity_binding"] == {"passed": True, "errors": {}}
    for forgery, error in ((forge_sense_state, "sense_inventory"), (forge_homograph_swap, "key_at_creation"),
                           (forge_moved_live_map, "live_sense_map")):
        report = forged_report(inputs, result, forgery)
        assert report["passed"] is False and error in report["identity_binding"]["errors"]


def test_r3f1_unchanged_draft_allocations_remain_valid(inputs, result):
    inputs.check_allocation()
    report = verify.verify(inputs, result, wa.build(inputs))
    assert report["passed"], {k: v for k, v in report.items() if isinstance(v, dict) and not v["passed"]}
    assert report["input_allocation"] == {"passed": True}
    assert report["identity_binding"] == {"passed": True, "errors": {}}
    states = {key: [s["state"] for s in card_of(result, key, nth=nth)["senses"]] for key, nth in (
        ("голова", 0), ("альфа", 0), ("бета", 0), ("ета", 0), ("перша фраза", 0), ("Ета", 0))}
    assert states == {"голова": ["active"], "альфа": ["active", "active", "unsplit"], "бета": ["unsplit"],
                      "ета": ["unsplit"], "перша фраза": ["unsplit"], "Ета": ["unsplit"]}
    assert card_of(result, "Ета")["card_kind"] == "proper_name" and card_of(result, "перша фраза")["card_kind"] == "mwe"
    (aligned,) = assertions(card_of(result, "голова"), "synonyms")
    assert aligned["mapping"]["confidence"] == "high"  # one active sense, one group
    (held,) = assertions(card_of(result, "альфа", nth=0), "synonyms")
    assert held["mapping"]["confidence"] == "unresolved"  # two active senses never align by position
    assert held["subject"]["id"] == card_of(result, "альфа", nth=0)["senses"][2]["sense_id"]
    (antonym,) = assertions(card_of(result, "ета"), "antonyms")
    assert antonym["mapping"]["confidence"] == "unresolved"  # an unsplit-only card holds its one group
    beta = result["ledger"].cards[card_of(result, "бета")["card_id"]]["fields"]
    assert beta["definition_uk"]["disposition"] == "source_absent"
    assert all(c["quality"]["practice_eligibility"] == [] for c in result["cards"].values())


def test_r3f1_verifier_allocation_failures_are_closed_reports(world, tmp_path, inputs, result):
    closed = {"input_allocation": {"passed": False, "errors": {"allocation_refused": 1}}, "passed": False}
    swapped = stale_inputs(world, tmp_path / "swapped", lambda i: swap_card_ids(i.registry, *two_card_ids(i)))
    assert verify.verify(swapped, result) == closed
    malformed = stale_inputs(world, tmp_path / "malformed", lambda i: i.registry.pop("events"))
    assert verify.verify(malformed, result) == closed
    with pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.build(malformed)
    missing = copy.deepcopy(result)
    del missing["cards"][card_of(missing, "бета")["card_id"]]
    shapeless = copy.deepcopy(result)
    del card_of(shapeless, "бета")["senses"]
    for output, error in ((missing, "inventory"), (shapeless, "malformed")):
        report = verify.verify(inputs, output)
        assert report["passed"] is False and error in report["identity_binding"]["errors"]
        assert all(v["passed"] is False for k, v in report.items() if isinstance(v, dict) and k not in (
            "input_allocation", "schema"))  # nothing past the failed identity check is reported as passed
    for report in (verify.verify(swapped, result), verify.verify(inputs, missing)):
        assert not any("\u0400" <= ch <= "\u04ff" for ch in json.dumps(report, ensure_ascii=False))


# --- R3-F1 over the committed pilot: the loader and the CLI refuse before any source read ---------------------

PILOT_TAMPERS = ["card_id_swap", "unsplit_promotion", "source_record_swap"]


class SourceOpened(Exception):
    """A source store was opened: the allocation audit did not refuse first."""


@pytest.fixture
def committed_pilot():
    """The committed frozen pilot inputs; tests using it keep the production allocation pin."""
    return {"manifest": ROOT / "registry/atlas/pilot/pilot-v1.json",
            "registry": ROOT / "registry/atlas/identity/registry.json",
            "register": ROOT / "docs/sources/permissions-register.yaml"}


@pytest.fixture
def source_sentinel(monkeypatch):
    opened = []

    def sentinel(stack, path):
        opened.append(path)
        raise SourceOpened

    monkeypatch.setattr(foundation, "readonly", sentinel)
    return opened


def tampered_pilot(committed_pilot, tamper, directory):
    """A copy of the committed registry with one known R3-F1 tamper that the foundation audit alone accepts."""
    registry, manifest = foundation.load(committed_pilot["registry"]), foundation.load(committed_pilot["manifest"])
    pilot = [e for e in registry["entries"] if e["created_in_build"] == BUILD_PREFIX + manifest["manifest_sha256"]]
    if tamper == "card_id_swap":
        swap_card_ids(registry, pilot[0]["card_id"], pilot[1]["card_id"])
    elif tamper == "unsplit_promotion":
        next(s for e in pilot for s in e["senses"] if s["state"] == "unsplit")["state"] = "active"
    else:
        a, b = [r for r in registry["source_records"] if r["source_id"] == "ulif"][:2]
        swap_source_record_ids(registry, a["source_record_id"], b["source_record_id"])
    foundation.allocation_check(manifest, registry)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "registry.json"
    path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("tamper", PILOT_TAMPERS)
def test_r3f1_loader_refuses_allocation_tampering_before_source_reads(committed_pilot, source_sentinel, tmp_path,
                                                                       tamper):
    stores = [tmp_path / f"{name}.db" for name in ("sources", "vesum", "atlas")]
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    paths = committed_pilot
    # Unchanged control: the committed allocation passes every audit and reaches the first source open.
    with ExitStack() as stack, pytest.raises(SourceOpened):
        wa.load_inputs(paths["manifest"], paths["registry"], paths["register"], *stores, stack, scratch)
    assert len(source_sentinel) == 1
    registry = tampered_pilot(committed_pilot, tamper, tmp_path / "tampered")
    with ExitStack() as stack, pytest.raises(wa.MissingAllocation, match=ALLOCATION_REFUSAL):
        wa.load_inputs(paths["manifest"], registry, paths["register"], *stores, stack, scratch)
    assert len(source_sentinel) == 1 and not any(scratch.iterdir())


@pytest.mark.parametrize("tamper", PILOT_TAMPERS)
@pytest.mark.parametrize("operation", ["build", "verify", "rehearse"])
def test_r3f1_cli_allocation_refusal_preserves_existing_output(committed_pilot, source_sentinel, tmp_path, capsys,
                                                                operation, tamper):
    registry = tampered_pilot(committed_pilot, tamper, tmp_path / "tampered")
    output = tmp_path / "out"
    (output / "cards").mkdir(parents=True)
    sentinel = output / "cards" / "wc_sentinel.json"
    sentinel.write_bytes(b'{"sentinel": true}\n')
    before = sorted(p.relative_to(output) for p in output.rglob("*"))
    stores = [arg for name in ("sources", "vesum", "atlas") for arg in (f"--{name}-db", str(tmp_path / f"{name}.db"))]
    code = wa.main([operation, "--manifest", str(committed_pilot["manifest"]), "--registry", str(registry),
                    "--register", str(committed_pilot["register"]), "--output", str(output), *stores])
    assert code == 1
    assert capsys.readouterr().err.strip() == "REFUSED: " + ALLOCATION_REFUSAL
    assert not source_sentinel
    assert sorted(p.relative_to(output) for p in output.rglob("*")) == before
    assert sentinel.read_bytes() == b'{"sentinel": true}\n'


def test_r3f1_cli_verify_rejects_independent_disk_tampering(world, host_scratch, monkeypatch, capsys):
    # Bounded local inputs: the synthetic world stands in for the loader; build, verify and on-disk checks are real.
    monkeypatch.setattr(wa, "load_inputs", lambda *args: make_inputs(world, args[7]))
    output = host_scratch / "pilot"
    stores = [arg for name in ("sources", "vesum", "atlas") for arg in (f"--{name}-db", str(host_scratch / name))]
    args = ["--manifest", "m.json", "--registry", "r.json", "--register", "g.yaml", "--output", str(output), *stores]
    assert wa.main(["build", *args]) == 0
    assert wa.main(["verify", *args]) == 0
    capsys.readouterr()
    paths = {p.stem: p for p in (output / "cards").glob("*.json")}
    built = {k: foundation.load(p) for k, p in paths.items()}

    def tamper_sense(cards):
        card = card_of({"cards": cards}, "ета")
        card["senses"][0]["state"] = "active"
        return [card]

    for edit in (tamper_sense, forge_homograph_swap):
        cards = copy.deepcopy(built)
        for card in edit(cards):
            resign(card)
        for key, card in cards.items():
            foundation.write(paths[key], card)
        assert wa.main(["verify", *args]) == 1
        report = json.loads(capsys.readouterr().out)
        assert report["passed"] is False and report["on_disk"]["passed"] is False
        for key, card in built.items():
            foundation.write(paths[key], card)
    assert wa.main(["verify", *args]) == 0
