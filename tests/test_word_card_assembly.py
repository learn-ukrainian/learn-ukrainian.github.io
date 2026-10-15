"""Pilot word-card assembly over a synthetic world: assertions, resolution, identity, withdrawal, rollback.

The world is built in memory from placeholder Cyrillic tokens and real grammatical-label terms; no dictionary
content is committed. Production reads the frozen pilot manifest; here `Inputs` is constructed directly, so the
tests cover assembly and verification, not the foundation's authentication (tests/test_word_card_foundation.py).
"""

import copy
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.atlas import word_card_verify as verify
from scripts.atlas.allocate_pilot_identities import BUILD_PREFIX

A = src.ACUTE
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "word-card-v1.schema.json").read_text())
MANIFEST_SHA = "7" * 64
BUILD = BUILD_PREFIX + MANIFEST_SHA
ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
SNAP = "selected-row@sha256:"

ENTRY_DDL = """CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_index INTEGER,
 canonical_headword TEXT, grammatical_label TEXT, sense_gloss TEXT, content_sha256 TEXT, register_position TEXT,
 homonym_checked INTEGER, raw_response_ref TEXT, retrieved_at TEXT, response_sha256 TEXT, parser_version TEXT,
 status TEXT)"""
SECTION_DDL = """CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT,
 source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT)"""
FORMS_DDL = """CREATE TABLE ulif_forms (id INTEGER PRIMARY KEY, entry_id INTEGER, entry_key TEXT, form_unstressed TEXT,
 form_stressed TEXT, stress_vowel_indices TEXT, grammatical_tags TEXT, unmapped_labels TEXT, variant_order INTEGER,
 preposition TEXT, marked_asterisk INTEGER, is_lemma INTEGER, is_invariable INTEGER, dual_stress_flag INTEGER,
 pedagogical_stressed_form TEXT, source_page_sha256 TEXT, parser_version TEXT, source_entry_fingerprint TEXT)"""
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


def form_row(row_id, entry_id, tags, form, stressed=None, **extra):
    row = {"id": row_id, "entry_id": entry_id, "entry_key": f"e#{entry_id}", "form_unstressed": form,
           "form_stressed": stressed or form, "stress_vowel_indices": "[]", "grammatical_tags": json.dumps(tags),
           "unmapped_labels": "[]", "variant_order": 1, "preposition": "", "marked_asterisk": 0, "is_lemma": 0,
           "is_invariable": 0, "dual_stress_flag": 0, "pedagogical_stressed_form": stressed or form,
           "source_page_sha256": "", "parser_version": "ulif-forms-v4", "source_entry_fingerprint": ""}
    row.update(extra)
    return row


def insert(conn, table, row):
    cols = ",".join(row)
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({','.join('?' * len(row))})", list(row.values()))


def synonym_html(head, lead, *others):
    members = ", ".join(f"<b>{o}</b>" for o in others)
    return f"<p><b>{head}</b> ({lead}), {members}.</p>"


def antonym_html(head, other, left, right):
    return (f"<table><tr><td><b>{head}</b></td><td><b>{other}</b></td></tr>"
            f"<tr><td>{left}.</td><td>{right}.</td></tr></table>")


def phrase_html(idiom, definition, quote, author):
    return f"<p><b>{idiom}.</b> {definition}. —<i>{quote}</i> ({author}).</p>"


class World:
    """Sources, VESUM, frozen manifest, registry and the units, assembled in memory."""

    def __init__(self):
        self.sources = sqlite3.connect(":memory:")
        self.vesum = sqlite3.connect(":memory:")
        self.records, self.units, self.entries, self.sr, self.events = [], [], [], [], []
        self.counter = 0
        self.sources.executescript(";".join((ENTRY_DDL, SECTION_DDL, FORMS_DDL, *SUM20_DDL)) + ";")
        self.sources.execute("CREATE TABLE ulif_forms_failures (id INTEGER PRIMARY KEY, entry_id INTEGER, reason TEXT,"
                             " locator TEXT)")
        self.sources.execute("CREATE TABLE puls_cefr (id INTEGER PRIMARY KEY, word TEXT, guideword TEXT, level TEXT, "
                             "pos TEXT, type TEXT, text TEXT, source TEXT)")
        self.sources.execute("CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, definition TEXT, "
                             "text TEXT, source TEXT)")
        self.vesum.executescript(
            "CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, word_form TEXT, lemma TEXT, pos TEXT, "
            "tags TEXT, source_comment TEXT, word_form_folded TEXT, lemma_folded TEXT);"
            "CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);"
            "CREATE TABLE vesum_build_metadata (key TEXT PRIMARY KEY, value TEXT);"
            f"INSERT INTO vesum_build_metadata VALUES ('canonical_jsonl_sha256', '{'5' * 64}');")
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

    def ulif(self, entry_id, query, head, label, gloss="", homonym=1, forms=(), sections=(), puls=None, extra=()):
        raw = {"id": entry_id, "normalized_query": query, "homonym_index": homonym, "canonical_headword": head,
               "grammatical_label": label, "sense_gloss": gloss, "content_sha256": "c" * 64,
               "register_position": f"1:{entry_id}", "homonym_checked": 1, "raw_response_ref": "sha256:" + "d" * 64,
               "retrieved_at": "2026-01-01T00:00:00Z", "response_sha256": "d" * 64, "parser_version": "ulif-dictua-v2",
               "status": "ok"}
        insert(self.sources, "ulif_dictua_entries", raw)
        for row in forms:
            insert(self.sources, "ulif_forms", row)
        for number, (kind, html) in enumerate(sections, start=1):
            insert(self.sources, "ulif_dictua_sections",
                   {"id": entry_id * 100 + number, "entry_id": entry_id, "kind": kind, "source_order": number - 1,
                    "sense_or_group_id": f"{kind}:{number}", "payload_json": json.dumps({"raw_html": html})})
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
        self.add_card(unit, "lexeme", {"spelling": src.unstressed(head), "pos": None}, gloss)
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

    def add_card(self, unit, kind, key, gloss):
        number = self.next()
        card_id = opaque("wc_", number)
        source = unit["anchor_locator"].split(":")[0]
        key = {**key, "source_keys": [{"source_id": source, "key": unit["unit_key"], "snapshot_id": "s"},
                                      {"source_id": source, "key": unit["anchor_locator"], "snapshot_id": "s"}]}
        senses = []
        if kind == "mwe" or not gloss:
            parts = [("unsplit", unit["anchor_locator"] + "#unsplit", None)]
        else:
            parts = [("active", f"ulif:entry:{self.records[-1]['raw_row']['id']} sense_gloss[{i}]", p.strip())
                     for i, p in enumerate(gloss[1:-1].split(";"))]
        for order, (state, source_unit, literal) in enumerate(parts, start=1):
            sense_id = opaque("ws_", self.next())
            senses.append({"sense_id": sense_id, "order": order, "state": state})
            self.events.append({"event_id": f"ie_{self.next():04d}", "kind": "sense_mint", "build_id": BUILD,
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
    w.vesum_form(101, "альфа", "альфа", "noun:inanim:m:v_naz", f"а{A}льфа (перша)")
    w.vesum_form(101, "альфа", "альфи", "noun:inanim:m:v_rod", f"а{A}льфа (перша)")
    w.vesum_form(102, "альфа", "альфа", "noun:inanim:m:v_naz", f"альфа{A} (друга)")
    w.vesum_form(102, "альфа", "альфу", "noun:inanim:m:v_rod", f"альфа{A} (друга)")
    w.ulif(1, "альфа", f"а{A}льфа", LABEL_M, "(перше; друге)", homonym=1, puls=("A2", "іменник"), forms=[
        form_row(10, 1, ["noun", "m"], "альфа", f"а{A}льфа", is_lemma=1),
        form_row(11, 1, ["v_naz", "s"], "альфа", f"а{A}льфа"),
        form_row(12, 1, ["v_rod", "s"], "альфи", f"а{A}льфи"),
        form_row(13, 1, ["v_mis", "s"], "альфі", f"а{A}льфі", preposition="на"),
        form_row(14, 1, ["v_kly", "s"], "альфо", f"а{A}льфо", marked_asterisk=1)])
    w.ulif(2, "альфа", f"альфа{A}", LABEL_M, "(інше)", homonym=2, forms=[
        form_row(20, 2, ["noun", "m"], "альфа", f"альфа{A}", is_lemma=1),
        form_row(21, 2, ["v_naz", "s"], "альфа", f"альфа{A}"),
        form_row(22, 2, ["v_rod", "s"], "альфу", f"альфу{A}")],
        sections=[("synonyms", synonym_html(f"альфа{A}", "ключове значення", "синонім"))])
    # One word: a two-form dative against VESUM's one, an archaic VESUM variant, two unaligned synonym groups.
    w.vesum_form(103, "бета", "бета", "noun:inanim:f:v_naz")
    w.vesum_form(103, "бета", "бети", "noun:inanim:f:v_rod")
    w.vesum_form(103, "бета", "бету", "noun:inanim:f:v_dav")
    w.vesum_form(103, "бета", "бетою", "noun:inanim:f:v_oru:arch")
    w.vesum_form(103, "бета", "бетою2", "noun:inanim:f:v_oru")
    w.ulif(3, "бета", "бета", LABEL_F, "", forms=[
        form_row(30, 3, ["noun", "f"], "бета", is_lemma=1),
        form_row(31, 3, ["v_naz", "s"], "бета"),
        form_row(32, 3, ["v_rod", "s"], "бети"),
        form_row(33, 3, ["v_dav", "s"], "бето"),
        form_row(34, 3, ["v_dav", "s"], "бету", variant_order=2),
        form_row(35, 3, ["v_oru", "s"], "бетою2")], puls=("B1", "іменник"), sections=[
            ("synonyms", synonym_html("бета", "перше", "один")),
            ("synonyms", synonym_html("бета", "друге", "два")),
            ("antonyms", antonym_html("бета", "анти", "ліве", "праве"))])
    # Doublet head, no VESUM entry, one sense and one synonym group: aligned by the one-unit rule.
    w.ulif(4, "гама", f"го{A}ло{A}ва", LABEL_F, "(єдине)", forms=[
        form_row(40, 4, ["v_naz", "s"], "голова")], sections=[
            ("synonyms", synonym_html(f"го{A}ло{A}ва", "єдине", "сіль"))])
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
    w.ulif(5, "дельта", f"де{A}льта", "прислівник", "", forms=[form_row(50, 5, ["adv"], "дельта", is_lemma=1)],
           extra=[uws])
    # A host entry whose phraseology repeats one aggregator record and quotes another.
    w.vesum_form(106, "ета", "ета", "noun:inanim:f:v_naz")
    w.ulif(6, "ета", "ета", LABEL_F, "", forms=[form_row(60, 6, ["v_naz", "s"], "ета")], sections=[
        ("phraseology", phrase_html("перша фраза", "Означення першої фрази", "Цитата першої фрази", "Автор Один")),
        ("phraseology", phrase_html("друга фраза", "Інше означення", "Інша цитата", "Автор Два"))])
    w.mwe(1, "<ID>1</ID>|<fna>перша фраза</fna>|<fras>}}|перша фраза {{</fras>}}",
          "пер[']ш[/']а фраза. Означення першої фрази. Цитата першої фрази (Автор Один).")
    w.mwe(2, "друга фраза {{</fras>}}", "друга фраза. Зовсім інший текст (Автор Три).")
    w.finish({"ulif:partition:дельта:5": "adv"})
    return w


def make_inputs(w, scratch):
    manifest = {"manifest_sha256": MANIFEST_SHA, "rules_version": "rules-v1-draft", "normaliser_version": "norm-v1",
                "selection": {"units": w.units, "source_records": w.records},
                "database_file_sha256": {"sources": "a" * 64, "atlas": "b" * 64, "vesum": "c" * 64}}
    registry = {"schema_version": 1, "registry_version": 2, "entries": w.entries, "source_records": w.sr,
                "events": w.events}
    register = {"schema_version": 2, "sources": [
        {"id": s, "appears_in": ["internal", "site", "dataset"]}
        for s in ("ulif", "vesum", "puls", "frazeolohichnyi", "ukrainian_word_stress")]}
    extract = scratch / "extract.sqlite"
    entry_ids = sorted(r["raw_row"]["id"] for r in w.records if r["table"] == "ulif_dictua_entries")
    src.write_extract(w.sources, entry_ids, extract)
    hashes = {"vesum_canonical": "5" * 64, "registry_file": "e" * 64, "register_entries": "f" * 64,
              "sources_file": "a" * 64, "atlas_file": "b" * 64, "manifest": MANIFEST_SHA, "frozen_rows_verified": 0}
    sources = src.PilotSources(w.sources, w.vesum)
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


def test_every_card_is_schema_valid_and_one_per_unit(result, inputs):
    validator = Draft202012Validator(SCHEMA)
    assert len(result["cards"]) == len(inputs.units) == 8
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


def test_paradigm_slots_withheld_variants_and_archaic_forms(result):
    card = card_of(result, "бета")
    slots = {a["value"]["slot"]: a for a in assertions(card, "paradigm", source_id="ulif")}
    assert set(slots) == {"v_naz.s", "v_rod.s", "v_dav.s", "v_oru.s"}
    # ULIF lists two datives, VESUM one: a declared set with a member observed is a variant, not a conflict.
    paradigm = card["fields"]["paradigm"]
    assert paradigm["propositions"]["v_dav.s"]["state"] == "variant"
    assert paradigm["propositions"]["v_naz.s"]["state"] == "verified"
    # The archaic VESUM instrumental is its own single-source proposition; the base slot is not disturbed.
    assert paradigm["propositions"]["v_oru.s~arch"]["state"] == "single-source"
    assert paradigm["propositions"]["v_oru.s"]["state"] == "verified"


def test_asterisk_and_preposition_slots_are_held_not_asserted(result):
    card = card_of(result, "альфа", nth=0)
    slots = {a["value"]["slot"] for a in assertions(card, "paradigm", source_id="ulif")}
    assert slots == {"v_naz.s", "v_rod.s"}
    held = {(h["slot"], h["reason"]) for h in result["ledger"].cards[card["card_id"]]["held"]
            if h["kind"] == "paradigm_slot"}
    assert held == {("v_mis.s", "preposition_bound"), ("v_kly.s", "asterisk_marked")}


def test_dual_stress_head_is_a_declared_variant_without_overlay(result):
    card = card_of(result, "голова")
    assert card["fields"]["stress"]["state"] == "variant"
    assert card["fields"]["stress"]["values"][0]["declared_set"] is True
    # No VESUM entry exists for the spelling: the card follows the checked ULIF division, medium at most.
    assert (card["identity"]["confidence"], card["identity"]["method"]) == ("medium", "unresolved")
    assert not [k for k in card["identity"]["source_keys"] if k["source_id"] == "vesum"]


def test_source_stress_conflict_is_never_auto_resolved(result):
    card = card_of(result, "дельта")
    assert card["fields"]["stress"]["state"] == "conflict" and card["fields"]["stress"]["selected"] is None
    values = {v["value_norm"] for v in card["fields"]["stress"]["values"]}
    assert values == {f"де{A}льта", f"дельта{A}"}
    uws = assertions(card, "stress", source_id="ukrainian_word_stress")[0]
    assert (uws["independence_group"], uws["tier"]) == ("G-ULIF", 2)


def test_relation_groups_align_only_by_the_one_unit_rule(result):
    aligned = card_of(result, "голова")
    (sense,) = aligned["senses"]
    assert sense["fields"]["synonyms"]["state"] == "single-source"
    assert any(m["source_sense_key"].startswith("ulif:section:") for m in sense["sense_map"])
    multi = card_of(result, "бета")
    # Two groups against one sense: retained on the card subject, non-voting, never a card field or a position pick.
    unaligned = assertions(multi, "synonyms")
    assert len(unaligned) == 2 and all(a["subject"]["kind"] == "card" for a in unaligned)
    assert all(a["mapping"]["confidence"] == "unresolved" and a["mapping"]["ambiguous"] for a in unaligned)
    assert "synonyms" not in multi["fields"]
    # The single antonym group of a one-sense card is the one unit on both sides.
    assert multi["senses"][0]["fields"]["antonyms"]["state"] == "single-source"
    assert result["ledger"].cards[multi["card_id"]]["fields"]["synonyms"]["disposition"] == "unresolved"


def test_two_sense_card_with_one_group_stays_unaligned(result):
    first = card_of(result, "альфа", nth=0)
    assert first["senses"][0]["state"] == "active" and len(first["senses"]) == 2
    second = card_of(result, "альфа", nth=1)
    assert second["senses"][0]["fields"]["synonyms"]["state"] == "single-source"


def test_sense_ids_and_seeds_come_from_the_registry(result, inputs):
    first = card_of(result, "альфа", nth=0)
    registry_ids = [s["sense_id"] for e in inputs.registry["entries"] if e["card_id"] == first["card_id"]
                    for s in e["senses"]]
    assert [s["sense_id"] for s in first["senses"]] == registry_ids
    labels = [s["fields"]["sense_label"]["values"][0]["value_norm"] for s in first["senses"]]
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


def selector_for(inputs, locator):
    record = inputs.record_ids[("ulif", locator)]
    return {"kind": "source_record", "source_id": "ulif", "source_record_id": record["source_record_id"],
            "on_ambiguous": "suppress_all_candidates"}


def suppression(selector, name="sup-1"):
    return {"schema_version": "1", "entries": [{
        "suppression_id": name, "issue": "https://example.invalid/8980", "date": "2026-10-15", "selector": selector,
        "scope": ["site"], "applies_to": {"reharvest": True, "rollback": True}}]}


def test_source_record_withdrawal_recomputes_and_tombstones(inputs, result):
    locator = next(u["anchor_locator"] for u in inputs.units if u["literal_head"] == f"а{A}льфа")
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
    spelling = {"kind": "assertion_content", "source_id": "ulif", "field": "spelling", "subject_spelling": "альфа",
                "value_norm": "альфа", "normaliser_version": "norm-v1"}
    withdrawn = wa.build(inputs, suppression(spelling))
    link = card_of(withdrawn, "альфа", nth=0)["links"][0]
    assert link["state"] == "suppressed"


def test_card_becomes_suppressed_when_every_assertion_is_withdrawn(inputs):
    only = next(u for u in inputs.units if u["literal_head"] == "ета")
    # Withdraw ULIF and VESUM for the host entry: a card with nothing left is suppressed, not empty.
    entries = [{**suppression({"kind": "source", "source_id": s}, f"sup-{s}")["entries"][0]} for s in
               ("ulif", "vesum", "puls")]
    withdrawn = wa.build(inputs, {"schema_version": "1", "entries": entries})
    card = withdrawn["cards"][inputs.entry_by_unit[only["unit_key"]]["card_id"]]
    assert card["state"] == "suppressed"


def test_verify_passes_and_catches_a_forged_locator(inputs, result):
    again = wa.build(inputs)
    report = verify.verify(inputs, result, again)
    assert report["passed"], report
    assert report["locators"]["checked"] > 50
    forged = copy.deepcopy(result)
    victim = next(c for c in forged["cards"].values() if c["key_at_creation"]["spelling"] == "бета")
    target = next(a for a in victim["assertions"] if a["field"] == "grammatical_label")
    target["value"] = "прислівник"
    bad = verify.verify(inputs, forged, again)
    assert bad["passed"] is False
    assert bad["assertion_identity"]["passed"] is False or bad["locators"]["passed"] is False


def test_rehearsal_reports_every_withdrawal_check(world, tmp_path):
    inputs = make_inputs(world, tmp_path)
    for unit in inputs.units:
        if unit["literal_head"] == f"а{A}льфа":
            unit["categories"] = ["withdrawal_rehearsal_candidate"]
    outcome = verify.rehearse(inputs)
    assert outcome["passed"], outcome
    assert set(outcome["scenarios"]) == {"source_record", "source"}


def test_card_subject_sense_field_needs_a_non_voting_mapping(result):
    validator = Draft202012Validator(SCHEMA)
    card = copy.deepcopy(card_of(result, "бета"))
    assert list(validator.iter_errors(card)) == []
    unaligned = next(a for a in card["assertions"] if a["field"] == "synonyms")
    unaligned["mapping"] = {"confidence": "high", "basis": "sense"}
    assert any("high" in e.message for e in validator.iter_errors(card))
    del unaligned["mapping"]
    assert list(validator.iter_errors(card))


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


def test_cards_are_refused_inside_the_repository_unless_ignored(tmp_path):
    root = Path(wa.__file__).resolve().parents[2]
    with pytest.raises(wa.AssemblyError):
        wa.require_host_only(root / "docs" / "atlas" / "word-cards" / "cards-output")
    wa.require_host_only(tmp_path / "cards")  # outside the repository: fine
    wa.require_host_only(root / "batch_state" / "reports" / "x")  # inside but git-ignored: fine


def host_stores_available():
    try:
        return all(wa.store_path(name, None).exists() for name in ("sources", "vesum", "atlas"))
    except foundation.Refusal:
        return False


@pytest.mark.skipif(not host_stores_available(), reason="held sources are host-only")
def test_host_pilot_builds_and_verifies_end_to_end(tmp_path):
    """Host-only product proof: the frozen pilot assembles, every locator resolves, rebuild is identical."""
    root = Path(wa.__file__).resolve().parents[2]
    args = ["--manifest", "registry/atlas/pilot/pilot-v1.json", "--registry", "registry/atlas/identity/registry.json",
            "--register", "docs/sources/permissions-register.yaml", "--output", str(tmp_path / "pilot")]
    for operation in ("build", "verify"):
        run = subprocess.run([sys.executable, "-m", "scripts.atlas.word_card_assembly", operation, *args],
                             cwd=root, capture_output=True, text=True, check=False, timeout=600)
        assert run.returncode == 0, run.stderr[-500:]
    report = json.loads(run.stdout)
    assert report["passed"] is True
    assert report["conservation"]["cards"] == 150
    shutil.rmtree(tmp_path / "pilot")
