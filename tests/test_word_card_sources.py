"""Source-side rules of pilot word-card assembly: stress readings, paradigm slots, identity matching.

Synthetic rows only: Latin placeholder lemmas with combining acute, so no dictionary content is committed.
"""

import json
import sqlite3

import pytest

from scripts.atlas import word_card_sources as src

A = src.ACUTE


def ulif_row(row_id, entry_id, tags, form, stressed=None, **extra):
    row = {"id": row_id, "entry_id": entry_id, "entry_key": f"e#{entry_id}", "form_unstressed": form,
           "form_stressed": stressed or form, "stress_vowel_indices": "[]", "grammatical_tags": json.dumps(tags),
           "unmapped_labels": "[]", "variant_order": 1, "preposition": "", "marked_asterisk": 0, "is_lemma": 0,
           "is_invariable": 0, "dual_stress_flag": 0, "pedagogical_stressed_form": stressed or form,
           "source_page_sha256": "", "parser_version": "ulif-forms-v4", "source_entry_fingerprint": ""}
    row.update(extra)
    return row


def vesum_row(row_id, entry_id, lemma, form, tags, comment=None, pos="noun"):
    return {"id": row_id, "entry_id": entry_id, "word_form": form, "lemma": lemma, "pos": pos, "tags": tags,
            "source_comment": comment}


def test_stress_forms_doublet_and_compound():
    assert src.stress_forms(f"по{A}ми{A}лка") == [f"по{A}милка", f"поми{A}лка"]
    assert src.stress_forms(f"вря{A}ди-году{A}") == [f"вря{A}ди-году{A}"]
    assert src.stress_forms("проста") == ["проста"]
    # Each hyphen part declares its own doublet; the readings are the product, in a stable order.
    assert len(src.stress_forms(f"по{A}ми{A}лка-по{A}ми{A}лка")) == 4


def test_norm_v1_keeps_stress_and_cuts_trailing_punctuation():
    assert src.norm_v1(f"  Фо{A}о  Бар. ") == f"фо{A}о бар"


def test_ulif_slot_ignores_header_rows_and_non_slot_tokens():
    assert src.ulif_slot(["v_naz", "s"]) == ("v_naz", "s")
    assert src.ulif_slot(["noun", "m"]) == ("m",)  # header tokens are filtered by is_lemma, not by vocabulary
    assert src.ulif_slot(["adv"]) is None
    assert src.slot_name(("pres", "s", "1")) == "pres.s.1"


def test_vesum_slot_adds_implicit_singular_and_drops_gender_for_nouns():
    assert src.vesum_slot(["noun", "inanim", "m", "v_naz"], keep_gender=False) == ("v_naz", "s")
    assert src.vesum_slot(["adj", "m", "v_naz"], keep_gender=True) == ("v_naz", "s", "m")
    assert src.vesum_slot(["verb", "imperf", "past", "m"], keep_gender=True) == ("past", "s", "m")
    assert src.vesum_slot(["adv"], keep_gender=False) is None


def test_ulif_paradigm_withholds_asterisk_preposition_and_unmapped_slots():
    forms = [
        ulif_row(1, 7, ["v_naz", "s"], "a"),
        ulif_row(2, 7, ["v_kly", "s"], "b", marked_asterisk=1),
        ulif_row(3, 7, ["v_mis", "s"], "c", preposition="na/u"),
        ulif_row(4, 7, ["v_oru", "s"], "d", unmapped_labels='["label"]'),
        ulif_row(5, 7, ["noun", "m"], "head", is_lemma=1),
    ]
    paradigm = src.ulif_paradigm(forms)
    slots = {src.slot_name(k): v for k, v in paradigm["slots"].items()}
    assert slots["v_naz.s"]["withheld"] == []
    assert slots["v_mis.s"]["withheld"] == ["preposition_bound"]
    assert slots["v_oru.s"]["withheld"] == ["unmapped_label"]
    # An asterisk-only slot has no certain form: it leaves the form sets and is reported separately.
    assert "v_kly.s" not in slots
    assert [src.slot_name(k) for k in paradigm["uncertain_only"]] == ["v_kly.s"]
    assert "head" not in {f for item in slots.values() for f in item["forms"]}


def test_asterisk_form_never_joins_the_slot_form_set():
    forms = [ulif_row(1, 7, ["v_naz", "s"], "a"), ulif_row(2, 7, ["v_naz", "s"], "z", marked_asterisk=1)]
    slot = src.ulif_paradigm(forms)["slots"][("v_naz", "s")]
    assert slot["forms"] == ["a"]
    assert slot["uncertain"] == ["z"]
    assert slot["withheld"] == ["asterisk_marked"]


def test_compare_paradigms_classes():
    def par(**slots):
        return {"slots": {("v_" + k, "s"): {"forms": sorted(v)} for k, v in slots.items()}}

    assert src.compare_paradigms(par(), par())["relation"] == "empty"
    equal = src.compare_paradigms(par(naz=["а"], rod=["б"]), par(naz=["а"], rod=["б"]))
    assert equal["relation"] == "equal"
    variant = src.compare_paradigms(par(naz=["а", "х"]), par(naz=["а"]))
    assert variant["relation"] == "compatible" and set(variant["slots"].values()) == {"ulif_extra_variant"}
    assert src.compare_paradigms(par(naz=["а"]), par(naz=["б"]))["relation"] == "differs"
    # No shared slot is not a match.
    assert src.compare_paradigms(par(naz=["а"]), par(rod=["а"]))["relation"] == "differs"
    # A slot only one side prints is not a disagreement.
    extra = src.compare_paradigms(par(naz=["а"], rod=["б"]), par(naz=["а"]))
    assert extra["relation"] == "compatible" and extra["slots"][("v_rod", "s")] == "ulif_only_slot"


def test_common_dims_and_projection_merge_unstated_dimensions():
    ulif = {"slots": {("v_naz",): {"forms": ["a"], "withheld": [], "rows": [1], "stressed": ["a"], "uncertain": []},
                      ("v_rod",): {"forms": ["b"], "withheld": [], "rows": [2], "stressed": ["b"], "uncertain": []}}}
    vesum = {"slots": {("v_naz", "p"): {"forms": {"a"}, "tags": {"t"}}, ("v_rod", "p"): {"forms": {"b"}, "tags": {"t"}}}}
    dims = src.common_dims(ulif, vesum)
    assert dims == {"case"}
    assert set(src.project(vesum, dims)["slots"]) == {("v_naz",), ("v_rod",)}
    assert src.compare_paradigms(ulif, vesum)["relation"] == "equal"


def test_projection_keeps_a_row_printed_without_a_dimension_both_sides_state():
    # A verb's participle row has no number; the інше rows do. The dimension stays, so the row is its own slot.
    ulif = {"slots": {("past", "s", "m"): {"forms": ["a"]}, ("past",): {"forms": ["part"]}}}
    vesum = {"slots": {("past", "s", "m"): {"forms": {"a"}}}}
    result = src.compare_paradigms(ulif, vesum)
    assert result["relation"] == "compatible"
    assert result["slots"][("past",)] == "ulif_only_slot"


def test_vesum_paradigm_variant_tagged_forms_are_their_own_proposition():
    rows = [
        vesum_row(1, 5, "ікс", "ікс", "noun:inanim:m:v_naz"),
        vesum_row(2, 5, "ікс", "іксікс", "noun:inanim:m:v_naz:arch"),
        vesum_row(3, 5, "ікс", "ґрець", "noun:inanim:m:v_zna:ranim"),
    ]
    entry = src.vesum_paradigm(rows, keep_gender=False)[5]
    slots = {src.slot_name(k): v["forms"] for k, v in entry["slots"].items()}
    assert slots == {"v_naz.s": {"ікс"}, "v_naz.s~arch": {"іксікс"}, "v_zna.s": {"ґрець"}}


def test_vesum_comment_stress_is_read_only_for_the_lemma():
    rows = [vesum_row(1, 5, "альфа", "альфа", "noun:inanim:m:v_naz", comment=f"а{A}льфа (note)"),
            vesum_row(2, 5, "альфа", "альфу", "noun:inanim:m:v_rod", comment="xv2")]
    assert src.vesum_paradigm(rows, keep_gender=False)[5]["stress"] == {f"а{A}льфа"}


def homonym(head, forms):
    return {"head": head, "paradigm": src.ulif_paradigm(forms)}


def vesum_entry(slots, stress=()):
    return {"slots": {tuple(k.split(".")): {"forms": set(v), "tags": set()} for k, v in slots.items()},
            "stress": set(stress), "pos": "noun", "flags": set()}


def forms_for(entry_id, naz, rod):
    return [ulif_row(entry_id * 10 + 1, entry_id, ["v_naz", "s"], naz), ulif_row(entry_id * 10 + 2, entry_id,
                                                                                  ["v_rod", "s"], rod)]


def test_identity_unique_match_is_high():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]})})
    assert (match["confidence"], match["method"], match["vesum_entry"]) == ("high", "unique_match", 10)


def test_identity_paradigm_separates_homographs():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи")), 2: homonym("альфа", forms_for(2, "альфа", "альфу"))}
    vesum = {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]}),
             11: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфу"]})}
    first, second = src.match_identity(1, ulif, vesum), src.match_identity(2, ulif, vesum)
    assert (first["vesum_entry"], first["method"], first["confidence"]) == (10, "paradigm_only", "high")
    assert (second["vesum_entry"], second["confidence"]) == (11, "high")


def test_identity_stress_and_paradigm_when_vesum_comment_names_the_stress():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи")), 2: homonym(f"альфа{A}", forms_for(2, "альфа", "альфу"))}
    vesum = {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]}, stress=[f"а{A}льфа"]),
             11: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфу"]}, stress=[f"альфа{A}"])}
    match = src.match_identity(1, ulif, vesum)
    assert (match["method"], match["confidence"], match["vesum_entry"]) == ("stress_and_paradigm", "high", 10)


def test_identity_dictionary_division_is_medium():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи")), 2: homonym("альфа", forms_for(2, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]})})
    assert (match["confidence"], match["method"], match["vesum_entry"]) == ("medium", "paradigm_only", 10)
    assert any("dictionary-division" in note for note in match["notes"])


def test_identity_stress_only_when_paradigms_agree_but_stress_differs():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи")), 2: homonym(f"альфа{A}", forms_for(2, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]})})
    assert (match["confidence"], match["method"]) == ("medium", "stress_only")


def test_identity_unresolved_when_paradigm_differs_or_vesum_is_ambiguous():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи"))}
    differs = src.match_identity(1, ulif, {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["інше"]})})
    assert (differs["confidence"], differs["vesum_entry"]) == ("unresolved", None)
    both = {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]}), 11: vesum_entry({"v_naz": ["альфа"],
                                                                                      "v_rod": ["альфи"]})}
    ambiguous = src.match_identity(1, ulif, both)
    assert ambiguous["confidence"] == "unresolved" and ambiguous["candidates"] == [10, 11]
    none = src.match_identity(1, ulif, {})
    assert (none["confidence"], none["method"]) == ("medium", "unresolved")


def test_identity_vesum_stress_contradiction_excludes_the_entry():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи"))}
    vesum = {10: vesum_entry({"v_naz": ["альфа"], "v_rod": ["альфи"]}, stress=[f"альфа{A}"])}
    assert src.match_identity(1, ulif, vesum)["confidence"] == "unresolved"


def test_write_extract_copies_rows_verbatim_for_entries_and_siblings(tmp_path):
    source = sqlite3.connect(":memory:")
    source.executescript("""
CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT, canonical_headword TEXT);
CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, payload_json TEXT);
CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, headword TEXT);
CREATE TABLE sum20_senses (id INTEGER PRIMARY KEY, article_id INTEGER);
CREATE TABLE sum20_citations (id INTEGER PRIMARY KEY, article_id INTEGER);
INSERT INTO ulif_dictua_entries VALUES (1,'q','h1'),(2,'q','h2'),(3,'інше','h3');
INSERT INTO ulif_dictua_sections VALUES (10,1,'synonyms','{}'),(11,2,'synonyms','{}'),(12,3,'synonyms','{}');
INSERT INTO sum20_articles VALUES (1,'x');
""")
    out = tmp_path / "extract.sqlite"
    counts = src.write_extract(source, [1], out)
    assert counts["ulif_dictua_entries"] == 2  # the sibling homonym travels with the pilot entry
    assert counts["ulif_dictua_sections"] == 2
    assert counts["sum20_articles"] == 1
    copy = sqlite3.connect(out)
    assert [r[0] for r in copy.execute("SELECT id FROM ulif_dictua_entries ORDER BY id")] == [1, 2]


@pytest.mark.parametrize("value,expected", [("Fóo", "Fóo"), ("é", "é")])
def test_nfc_is_idempotent_for_combining_marks(value, expected):
    assert src.nfc(src.nfc(value)) == src.nfc(expected)
