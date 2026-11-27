"""Five slice-2 contract tests approved in #11943 issuecomment-6536581112.

Synthetic source text exercises receipt mechanics, not Ukrainian correctness.
"""

import copy
import hashlib
import json
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.atlas import a1_card_examples as examples
from scripts.atlas import a1_card_projection as projection
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_assertion_check as assertion_check
from scripts.atlas import word_card_resolver as resolver
from scripts.atlas import word_card_sources
from scripts.atlas.a1_card_capture import _paradigm
from scripts.atlas.a1_card_receipts import Refusal, make_receipt, selected_rows
from scripts.projects.open_model_data.word_cards import dataset_projection
from scripts.wiki.sum20_mirror import SCHEMA_SQL as MIRROR_SCHEMA
from scripts.wiki.sum20_official import ensure_sum20_official_schema, parse_sum20_article, upsert_sum20_article

ROOT = Path(__file__).resolve().parents[2]
TARGET = "wc_6bt62wd6zzzf"
SENSE = "ws_000000000001"
OTHER_SENSE = "ws_000000000002"
VTS = "vts_busel_slovnyk_me"
ACUTE = "\u0301"
SELECTED = [
    ("a1-finale", 23, "wc_5b36dst0her6", 429081),
    ("around-the-city", 6, "wc_qpcdgkctp7ne", 425814),
    ("checkpoint-communication", 21, "wc_vq34ms5wtfev", 441799),
    ("checkpoint-places", 14, "wc_qpcdgkctp7ne", 425814),
    ("emergencies", 13, "wc_ppr39m6qsr4e", 423800),
    ("euphony", 11, "wc_qpcdgkctp7ne", 425814),
    ("food-and-drink", 28, TARGET, 436914),
    ("holidays", 18, "wc_n1g44brn5vs2", 428619),
    ("i-eat-i-drink", 31, TARGET, 436914),
    ("i-eat-i-drink", 32, TARGET, 436914),
    ("i-want-i-can", 34, "wc_08svjhdbe0fq", 428572),
    ("linking-ideas", 11, "wc_8mhjfw05sm0t", 421145),
    ("linking-ideas", 18, "wc_da7t5vpprjw3", 441309),
    ("my-city", 6, "wc_qpcdgkctp7ne", 425814),
    ("my-morning", 29, "wc_0r1cdw5z36cd", 423808),
    ("my-story", 15, "wc_5b36dst0her6", 429081),
    ("weather", 7, "wc_5btr8jkdzvd1", 442128),
    ("where-is-it", 4, "wc_qpcdgkctp7ne", 425814),
    ("where-to", 16, "wc_qpcdgkctp7ne", 425814),
]


def test_full_data_refuses_pos_matching_paradigm_mismatched_entry():
    slot = ("v_rod", "s")
    homonym = {"head": "test-head", "aspect": None, "candidates": [41],
               "paradigm": {"slots": {slot: {"forms": ["source-form"]}}}}
    target = {"pos": "noun", "aspect": None, "stress": set(),
              "slots": {slot: {"forms": ["other-form"]}}}
    assert projection.bound_ulif({9: homonym}, {41: target}, 41) is None
    target["slots"][slot]["forms"] = ["source-form"]
    assert projection.bound_ulif({9: homonym}, {41: target}, 41) == 9


def test_full_data_parity_does_not_silently_drop_a_section_or_legacy_value():
    payloads = [
        ("fixture", "enrichment", "meaning", "VTS label", {"definitions": ["literal", "unknown"]}),
        ("fixture", "enrichment", "proverbs", "Proverb source", {"items": ["saying", ""]}),
        ("competing", "enrichment", "meaning", "VTS label", {"definitions": ["literal"]}),
    ]
    values = [{"field": "definition_uk", "source_label": "VTS label", "value": "literal"}]
    ledger = projection.parity(payloads, values, "fixture")
    assert [(row["slug"], row["section"], row["counts"]) for row in ledger] == [
        ("fixture", "meaning", {"admitted": 1, "withheld": 1}),
        ("fixture", "proverbs", {"withheld": 1, "missing": 1}),
        ("competing", "meaning", {"withheld": 1}),
    ]
    assert [item["pointer"] for item in ledger[0]["values"]] == ["/definitions/0", "/definitions/1"]
    assert ledger[2]["values"][0]["reason"] == "atlas_slug_unbound"


def test_full_data_sum11_is_labelled_context_and_never_counts_as_evidence():
    register = {"sources": [{"id": "sum11", "fields_used": ["russification_quote"]}]}
    field = "soviet_colonization_context"
    assert assertion_check.check_entry_projection(
        field, "sum11", "context", register, source_label="СУМ-11",
    ) == "context_only"
    assert assertion_check.check_entry_projection(
        "definition_uk", "sum11", "entry", register, source_label="СУМ-11",
    ) != "supported"
    row = {"definition": "Historical quotation.", "sovietization_risk": 0, "sovietization_keywords": ""}
    context = projection.soviet_context(row)
    assert context["red_flag"] is True
    value = {"field": field, "value": context, "source_label": "СУМ-11", "scope": "context"}
    card = {"lemma": "fixture", "values": [value]}
    html = projection.render_card(card)
    assert '<details class="occupation-context">' in html
    assert "Soviet-era dictionary, occupation context" in html
    assert "Historical quotation." in html
    assert "<strong>Risk" not in html
    context["sovietization_risk"] = 1
    assert "<strong>Risk 1</strong>" in projection.render_card(card)


@pytest.fixture
def gap_fill_card(monkeypatch):
    row = {"id": 2, "entry_id": 41, "word_form": "fixture", "lemma": "fixture",
           "pos": "noun", "tags": "noun:inanim:m:v_naz", "source_comment": ""}
    monkeypatch.setattr(projection, "ulif_candidates", lambda *_: {
        9: {"head": "fixture", "row": {"id": 9}, "aspect": None,
            "candidates": [41], "reason": None, "paradigm": {"slots": {}},
            "forms": [{"is_lemma": True, "is_invariable": False, "form_stressed": "fixture",
                       "form_unstressed": "fixture", "id": 99, "entry_id": 9, "variant_order": 0,
                       "grammatical_tags": "[]", "unmapped_labels": "[]", "marked_asterisk": 0,
                       "preposition": ""}]},
    })
    monkeypatch.setattr(projection, "entry_witnesses", lambda *_: None)
    monkeypatch.setattr(projection, "secondary_witnesses", lambda *_: None)
    monkeypatch.setattr(projection.meanings, "candidates", lambda *_, **__: {
        "sum20": [], "sum20_slovnyk_mirror": [], projection.VTS: [],
    })
    sources = SimpleNamespace(vesum_forms=lambda _: [row], _use=lambda *_: None,
                              sources=SimpleNamespace(execute=lambda *_: []))
    register = {"sources": [
        {"id": "vesum", "name": "VESUM", "fields_used": ["pos", "morph_tags", "word_forms"]},
        {"id": "puls", "name": "PULS register", "fields_used": ["cefr_level"]},
    ]}

    def build(puls_rows=(), *, unique_card=True):
        return projection.card_values(sources, "fixture", 41, register, puls_rows, unique_card)

    return build


def test_full_data_refuses_fill_from_non_bound_entry(gap_fill_card):
    row = {"id": 7, "word": "fixture", "level": "A1", "source": "PULS citation",
           "pos": "дієслово (док.)", "guideword": ""}
    for candidate, unique_card, reason in (
        (row, True, "entry_witness_grammar_mismatch"),
        ({**row, "pos": "іменник"}, False, "entry_witness_unbound"),
    ):
        _, values, observations, holds = gap_fill_card([candidate], unique_card=unique_card)
        assert not any(item["field"] == "cefr" for item in values)
        assert "required_cefr" in holds
        assert [item["reason"] for item in observations if item["source"] == "puls"] == [reason]
    row = {"word": "fixture", "source_url": "https://slovnyk.me/dict/ukreng/fixture"}
    assert projection.literal_ukreng_glosses(row, "other English", "fixture") == (
        [], "bilingual_ukreng_article_mismatch",
    )
    assert projection.literal_ukreng_glosses(row, "fixture I first II second", "fixture") == (
        [], "bilingual_homonym_partition_unresolved",
    )


def test_full_data_uncaptured_vts_stays_held_with_reason(gap_fill_card):
    _, values, observations, holds = gap_fill_card()
    fields = projection.field_ledger(values, observations, holds)
    assert fields["definition_uk"] == {
        "outcome": "held", "reasons": ["required_definition_uk"],
        "sources_searched": {
            "sum20": {"admitted": 0, "reasons": {"capture_absent": 1}},
            "sum20_slovnyk_mirror": {"admitted": 0, "reasons": {"capture_absent": 1}},
            VTS: {"admitted": 0, "reasons": {"ВТС not captured": 1}},
        },
    }
    html = projection.render_card({
        "lemma": "fixture", "status": "held", "values": values,
        "holds": [{"reason": reason} for reason in holds], "gap_ledger": fields,
    })
    assert "<li>ВТС not captured</li>" in html


def test_full_data_every_filled_value_carries_its_source_label(gap_fill_card):
    row = {"id": 7, "word": "fixture", "level": "A1", "pos": "іменник", "guideword": ""}
    other = {**row, "id": 8, "source": "PULS citation"}
    _, values, observations, _ = gap_fill_card([{**row, "source": None}, other])
    assert [(value["field"], value["source_label"]) for value in values] == [
        ("pos", "VESUM"), ("gender", "VESUM"), ("paradigm", "VESUM"), ("cefr", "PULS citation"),
    ]
    assert [item["reason"] for item in observations if item["source"] == "puls"] == [
        "source_label_missing",
    ]


def _headword_stress_card(monkeypatch, homonyms, *, lemma="абека", target=41, ulif_anchor=None, register=None):
    vesum_rows = [
        {"id": 2, "entry_id": 41, "word_form": lemma, "lemma": lemma,
         "pos": "noun", "tags": "noun:inanim:f:v_naz", "source_comment": ""},
        {"id": 3, "entry_id": 41, "word_form": "абеки", "lemma": lemma,
         "pos": "noun", "tags": "noun:inanim:f:v_rod", "source_comment": ""},
    ]
    monkeypatch.setattr(projection, "ulif_candidates", lambda *_: homonyms)
    monkeypatch.setattr(projection, "entry_witnesses", lambda *_: None)
    monkeypatch.setattr(projection, "secondary_witnesses", lambda *_: None)
    monkeypatch.setattr(projection.meanings, "candidates", lambda *_, **__: {
        "sum20": [], "sum20_slovnyk_mirror": [], projection.VTS: [],
    })
    sources = SimpleNamespace(vesum_forms=lambda _: vesum_rows, _use=lambda *_: None,
                              sources=SimpleNamespace(execute=lambda *_: []))
    if register is None:
        register = {"sources": [
            {"id": "vesum", "name": "VESUM", "fields_used": ["pos", "morph_tags", "word_forms"]},
            {"id": "ulif", "name": "ULIF DictUA", "fields_used": ["stress", "paradigm"]},
        ]}
    return projection.card_values(sources, lemma, target, register, [], True, ulif_anchor)


def _ulif_homonym(entry_id, head, *, candidates=(41,), slot_form="абеку", authenticated=True):
    replay = ({"canonical_headword": head, "content_sha256": "fixture-sha",
               "forms": [{"is_lemma": True, "form_stressed": head}]}
              if authenticated else None)
    cand_list = list(candidates) if candidates is not None else None
    return {
        "row": {"id": entry_id, "normalized_query": head.replace(ACUTE, ""), "canonical_headword": head,
                "grammatical_label": "іменник жіночого роду", "homonym_index": 1,
                "homonym_checked": 1, "status": "ok", "content_sha256": "fixture-sha",
                "raw_response_ref": "sha256:fixture-raw", "sense_gloss": ""},
        "head": head, "aspect": None, "candidates": cand_list,
        "reason": None if authenticated else "ulif_raw_identity_mismatch",
        "raw": {}, "replay": replay,
        "paradigm": {"slots": {("v_rod", "s"): {"forms": [slot_form]}}},
        "forms": [
            {"is_lemma": True, "is_invariable": False, "form_stressed": head,
             "form_unstressed": head.replace(ACUTE, ""), "id": entry_id * 10, "entry_id": entry_id,
             "variant_order": 0, "grammatical_tags": "[]", "unmapped_labels": "[]",
             "marked_asterisk": 0, "preposition": ""},
            {"is_lemma": False, "is_invariable": False, "form_stressed": slot_form,
             "form_unstressed": slot_form, "id": entry_id * 10 + 1, "entry_id": entry_id,
             "variant_order": 0, "grammatical_tags": '["v_rod","s"]', "unmapped_labels": "[]",
             "marked_asterisk": 0, "preposition": ""},
        ],
    }


def test_headword_stress_fills_when_paradigm_slots_differ(monkeypatch):
    """Defect class: paradigm slot difference blocking ULIF headword stress."""
    stressed = f"а{ACUTE}бека"
    _, values, observations, holds = _headword_stress_card(monkeypatch, {9: _ulif_homonym(9, stressed)})
    assert "required_stress" not in holds
    assert [v["value"] for v in values if v["field"] == "stress"] == [stressed]
    # Paradigm-form stress keeps its stricter whole-paradigm correspondence rule.
    assert [v for v in values if v["field"] == "paradigm" and v["source_id"] == "ulif"] == []
    assert any(o["field"] == "identity" and o["reason"] == "ulif_vesum_correspondence_unresolved" for o in observations)
    # A doublet headword shows both accepted stresses in rendered HTML while ledger keeps verbatim ULIF form.
    doublet = f"а{ACUTE}бе{ACUTE}ка"
    expanded = _ulif_homonym(10, doublet, slot_form="абеку")
    _, d_values, _, d_holds = _headword_stress_card(monkeypatch, {10: expanded})
    assert "required_stress" not in d_holds
    assert [v["value"] for v in d_values if v["field"] == "stress"] == [doublet]
    assert [v for v in d_values if v["field"] == "paradigm" and v["source_id"] == "ulif"] == []
    html = projection.render_card({"lemma": "абека", "status": "held", "values": d_values, "holds": []})
    assert f"а{ACUTE}бека / абе{ACUTE}ка" in html
    assert doublet not in html


def test_headword_stress_homonym_pair_with_different_stresses_stays_held(monkeypatch):
    """Defect class: different-stress same-POS ULIF homonyms guessing a stress."""
    # Even when one homonym matches the VESUM paradigm ("абеки") and bound_ulif selects it,
    # a competing same-POS homonym with a different stress still holds headword stress.
    homonyms = {
        9: _ulif_homonym(9, f"а{ACUTE}бека", slot_form="абеки"),
        10: _ulif_homonym(10, f"абе{ACUTE}ка", slot_form="абеку"),
    }
    _, values, observations, holds = _headword_stress_card(monkeypatch, homonyms)
    assert "required_stress" in holds
    assert [v for v in values if v["field"] == "stress"] == []
    stress_obs = [(o["reason"], o["locator"]) for o in observations if o["field"] == "stress" and o["source"] == "ulif"]
    assert stress_obs == [
        ("ulif_homonym_stress_ambiguous", "ulif_dictua_entries:9/canonical_headword"),
        ("ulif_homonym_stress_ambiguous", "ulif_dictua_entries:10/canonical_headword"),
    ]
    # An unauthenticated competitor also fails closed on the full-match and frozen-anchor branches.
    anchor = _ulif_homonym(9, f"а{ACUTE}бека", slot_form="абеки")["row"]
    unauth = {9: _ulif_homonym(9, f"а{ACUTE}бека", slot_form="абеки"),
              11: _ulif_homonym(11, "", candidates=(), authenticated=False)}
    for card_target, card_anchor in ((41, None), (41, anchor), (None, anchor)):
        _, u_values, u_obs, u_holds = _headword_stress_card(
            monkeypatch, unauth, target=card_target, ulif_anchor=card_anchor,
        )
        assert "required_stress" in u_holds
        assert [v for v in u_values if v["field"] == "stress"] == []
        assert any(o["reason"] == "ulif_competitor_unauthenticated" for o in u_obs if o["field"] == "stress")


def test_headword_stress_carries_ulif_source_label_and_locator(monkeypatch):
    """Defect class: missing ULIF source attribution or locator on filled headword stress."""
    stressed = f"а{ACUTE}бека"
    _, values, _, _ = _headword_stress_card(monkeypatch, {9: _ulif_homonym(9, stressed)})
    stress = [v for v in values if v["field"] == "stress"]
    assert len(stress) == 1
    assert (stress[0]["source_id"], stress[0]["source_label"], stress[0]["locator"]) == (
        "ulif", "ULIF DictUA", "ulif_dictua_entries:9/canonical_headword",
    )
    # Matching-POS homonyms with identical stress record every agreeing ULIF entry in the locator,
    # including when one homonym matched the full VESUM paradigm.
    same_stress = {9: _ulif_homonym(9, stressed, slot_form="абеки"),
                   10: _ulif_homonym(10, stressed, slot_form="абеку")}
    _, same_values, _, same_holds = _headword_stress_card(monkeypatch, same_stress)
    assert "required_stress" not in same_holds
    same = [v for v in same_values if v["field"] == "stress"]
    assert len(same) == 1
    assert (same[0]["source_label"], same[0]["locator"]) == (
        "ULIF DictUA", "ulif_dictua_entries:9,10/canonical_headword",
    )
    html = projection.render_card({"lemma": "абека", "status": "held", "values": stress, "holds": []})
    assert "<small>ULIF DictUA</small>" in html and stressed in html


FROZEN_HEAD = "fi" + ACUTE + "xture"


def frozen_homonym(**changes):
    row = {"id": 9, "normalized_query": "fixture", "canonical_headword": FROZEN_HEAD,
           "grammatical_label": "іменник чоловічого роду", "sense_gloss": "", "homonym_index": 1,
           "homonym_checked": 1, "status": "ok", "content_sha256": "a" * 64,
           "raw_response_ref": "sha256:" + "b" * 64}
    replay = {"canonical_headword": FROZEN_HEAD, "content_sha256": "a" * 64,
              "forms": [{"is_lemma": True, "form_stressed": FROZEN_HEAD}]}
    homonym = {"row": row, "head": FROZEN_HEAD, "aspect": None, "candidates": [41], "reason": None,
               "paradigm": None, "forms": None, "replay": replay}
    for key, value in changes.items():
        (replay if key.startswith("replay_") else row)[key.removeprefix("replay_")] = value
    return {9: homonym}, dict(row)


def test_frozen_ulif_stress_refuses_replay_that_differs_from_the_frozen_entry():
    """Defect class: stress copied from a ULIF entry that is not the card's frozen entry."""
    homonyms, anchor = frozen_homonym()
    assert projection.anchored_entry(homonyms, anchor, "fixture") == 9
    assert projection.anchored_entry(homonyms, anchor, "Fixture") is None
    for change in ({"content_sha256": "c" * 64}, {"raw_response_ref": "sha256:" + "d" * 64},
                   {"homonym_index": 2}, {"replay_content_sha256": "c" * 64},
                   {"replay_canonical_headword": "fixtu" + ACUTE + "re"},
                   {"replay_forms": [{"is_lemma": True, "form_stressed": "fixture"}]}):
        changed, _ = frozen_homonym(**change)
        assert projection.anchored_entry(changed, anchor, "fixture") is None, change
    unstressed, frozen = frozen_homonym(canonical_headword="fixture", replay_canonical_headword="fixture",
                                        replay_forms=[{"is_lemma": True, "form_stressed": "fixture"}])
    unstressed[9]["head"] = "fixture"
    assert projection.anchored_entry(unstressed, frozen, "fixture") is None


def test_vts_partition_with_a_competing_homonym_stays_held(monkeypatch):
    """Defect class: a ВТС definition bound while another same-spelling homonym competes."""
    part = {"text": "definition", "head": FROZEN_HEAD, "pos": "noun", "aspect": None, "reason": None,
            "partition": "article", "locator": "vts:fixture", "row": {"dictionary_label": "ВТС"}}
    monkeypatch.setattr(projection.meanings, "candidates", lambda *_, **__: {
        "sum20": [], "sum20_slovnyk_mirror": [], projection.VTS: [part]})
    homonyms, _ = frozen_homonym()
    rival = {**homonyms[9], "row": {**homonyms[9]["row"], "id": 10}}
    name = {**rival, "head": "Fi" + ACUTE + "xture", "candidates": [],
            "row": {**rival["row"], "canonical_headword": "Fi" + ACUTE + "xture",
                    "grammatical_label": "власна назва"}}

    def outcome(competitor, common):
        added, reported = [], []
        projection.modern_meanings(
            None, "fixture", {**homonyms, 10: competitor}, 9, set(),
            lambda field, source, locator, *_, **__: added.append((field, locator)),
            lambda field, source, reason, *_: reported.append((field, source, reason)), common=common)
        return added, [item for item in reported if item[1] == projection.VTS]

    assert outcome(rival, True) == ([], [("definition_uk", projection.VTS, "unbound_partition")])
    assert outcome(name, False) == ([], [("definition_uk", projection.VTS, "unbound_partition")])
    assert outcome(name, True) == ([("definition_uk", "vts:fixture")], [])


def test_frozen_entry_fills_carry_their_source_label_and_locator(monkeypatch):
    """Defect class: a filled stress or definition without its source label and locator."""
    homonyms, anchor = frozen_homonym()
    part = {"text": "definition", "head": FROZEN_HEAD, "pos": "noun", "aspect": None, "reason": None,
            "partition": "article", "locator": "vts:fixture", "row": {"dictionary_label": "ВТС label"}}
    monkeypatch.setattr(projection, "ulif_candidates", lambda *_: homonyms)
    monkeypatch.setattr(projection, "entry_witnesses", lambda *_: None)
    monkeypatch.setattr(projection, "secondary_witnesses", lambda *_: None)
    monkeypatch.setattr(projection.meanings, "candidates", lambda *_, **__: {
        "sum20": [], "sum20_slovnyk_mirror": [], projection.VTS: [part]})
    row = {"id": 2, "entry_id": 41, "word_form": "fixture", "lemma": "fixture",
           "pos": "noun", "tags": "noun:inanim:m:v_naz", "source_comment": ""}
    sources = SimpleNamespace(vesum_forms=lambda _: [row], _use=lambda *_: None,
                              sources=SimpleNamespace(execute=lambda *_: []))
    register = {"sources": [
        {"id": "vesum", "name": "VESUM", "fields_used": ["pos", "morph_tags", "word_forms"]},
        {"id": "ulif", "name": "ULIF", "fields_used": ["stress"]},
        {"id": VTS, "name": "ВТС", "fields_used": ["meaning"]},
    ]}
    _, values, observations, _ = projection.card_values(sources, "fixture", 41, register, [], True, anchor)
    filled = [(value["field"], value["source_label"], value["locator"], value["value"], value["source_key"])
              for value in values if value["field"] in {"stress", "definition_uk"}]
    assert filled == [
        ("stress", "ULIF", "ulif_dictua_entries:9/canonical_headword", FROZEN_HEAD, None),
        ("definition_uk", "ВТС label", "vts:fixture", "definition", "article"),
    ]
    assert ("identity", "ulif_vesum_correspondence_unresolved") in [
        (item["field"], item["reason"]) for item in observations]


@pytest.fixture
def mirror_card(monkeypatch):
    mirror_definition = "Пристрій для освітлення."
    head = "ліхта́р"
    numbered = f"1. {mirror_definition}"
    article = f"ліхтар {head.upper()}, я́, ч. {numbered}"
    staged = {"headword": head.upper(), "entry_type": "monosemous",
              "senses": [{"sense_num": 1, "raw_text": numbered, "definition": numbered[1:]}]}
    with sqlite3.connect(":memory:") as conn:
        conn.row_factory = sqlite3.Row
        ensure_sum20_official_schema(conn)
        conn.executescript(MIRROR_SCHEMA)
        conn.execute("""
            INSERT INTO sum20_mirror_imports
            (id, generation, rule_version, staging_sha256, staging_records, checkpoint_count,
             checkpoint_last_url, checkpoint_updated_at, official_digest, relation_counts, imported_at)
            VALUES (1, 'fixture', 'sum20-mirror-rule-v1', 'fixture', 1, 1,
                    'https://slovnyk.me/dict/newsum/ліхтар', '2026-10-12', 'fixture', '{}', '2026-10-12')
        """)
        conn.execute("CREATE TABLE slovnyk_me_entries (id, dictionary_slug, normalized_word)")
        conn.execute("""
            INSERT INTO sum20_mirror_articles
            (mirror_url, source_url, mirror, lemma, headword, normalized_lookup_key,
             title, article_text, senses_json, fetched_at, content_sha256, import_id)
            VALUES ('https://slovnyk.me/dict/newsum/ліхтар', 'https://slovnyk.me/dict/newsum/ліхтар',
                    'slovnyk.me', 'ліхтар', 'ліхтар', 'ліхтар', 'ліхтар', ?, ?, '2026-10-12', ?, 1)
        """, (article, json.dumps(staged, ensure_ascii=False), hashlib.sha256(article.encode()).hexdigest()))
        sources = word_card_sources.PilotSources(conn, conn, conn)
        forms = [{"entry_id": 41, "word_form": "ліхтар", "lemma": "ліхтар", "pos": "noun",
                  "id": 2, "tags": "noun:inanim:m:v_naz", "source_comment": head}]
        monkeypatch.setattr(sources, "vesum_forms", lambda _: forms)
        monkeypatch.setattr(projection, "ulif_candidates", lambda *_: {
            9: {"head": "ліхтар", "row": {"id": 9, "grammatical_label": "іменник"},
                "candidates": [41], "reason": None, "forms": [], "aspect": None, "paradigm": {"slots": {}}},
        })
        monkeypatch.setattr(projection, "bound_ulif", lambda *_: 9)
        monkeypatch.setattr(projection, "ulif_groups", lambda *_: None)
        monkeypatch.setattr(projection, "entry_witnesses", lambda *_: None)
        monkeypatch.setattr(projection, "secondary_witnesses", lambda *_: None)
        register = {"sources": [
            {"id": "sum20", "name": "Official edition", "fields_used": ["stressed_headword", "definition_text"]},
            {"id": "sum20_slovnyk_mirror", "name": "Mirror", "permission_status": "pending-expert-contact",
             "fields_used": ["definition_text", "stressed_headword"]},
        ]}

        def run(*, official=False):
            if official:
                html = ('<article><div class="ENTRY"><span class="WORD">ЛІХТА́Р</span>'
                        '<span class="LPART">я́, ч.</span>'
                        '<div class="INTF"><span class="FORMULA">Переносний світильник.</span></div>'
                        '</div></article>')
                upsert_sum20_article(conn, parse_sum20_article(html, 5), fetched_at="2026-09-22")
            return projection.card_values(sources, "ліхтар", 41, register, [], True)

        yield run


def test_full_data_bound_mirror_fills_definition_and_stress_with_copy_label(mirror_card):
    _, values, observations, holds = mirror_card()
    label = "Словник української мови у 20 томах — копія slovnyk.me (newsum); не звірено з офіційним виданням"
    assert [(row["field"], row["value"], row["source_label"]) for row in values] == [
        ("stress", "ліхта́р", label),
        ("definition_uk", "Пристрій для освітлення.", label),
    ]
    ledger = projection.field_ledger(values, observations, holds)
    assert ledger["definition_uk"]["outcome"] == "filled"
    assert ledger["definition_uk"]["sources_searched"]["sum20_slovnyk_mirror"]["admitted"] == 1


def test_full_data_captured_official_article_wins_over_differing_mirror(mirror_card):
    _, values, _, _ = mirror_card(official=True)
    assert [(row["field"], row["source_id"], row["value"]) for row in values] == [
        ("stress", "sum20", "ЛІХТА́Р"),
        ("definition_uk", "sum20", "Переносний світильник."),
    ]


@pytest.fixture
def example_search():
    # Literal primer sentence from Захарійчук, grade one, part 1, chunk s0054.
    # The stores, identities and source levels below are owned by this test.
    sentence = "Ми будемо сумувати!"
    with sqlite3.connect(":memory:") as conn:
        conn.executescript("""
            CREATE TABLE textbooks (id, chunk_id, source_file, title, text, grade);
            CREATE TABLE literary_texts (id, chunk_id, source_file, text, author, work, work_id,
                                         source_url, language_period, genre);
            CREATE TABLE forms_all (id, entry_id, word_form, lemma, pos, tags, word_form_folded);
            CREATE TABLE form_markers (form_id, marker);
        """)
        conn.execute("INSERT INTO textbooks VALUES (1,'fixture-chunk','fixture','Page 3',?,'1')", (sentence,))
        conn.executemany("INSERT INTO forms_all VALUES (?,?,?,?,?,?,?)", [
            (1, 10, "ми", "ми", "noun", "noun:pron", "ми"),
            (2, 20, "будемо", "бути", "verb", "verb:imperf:futr", "будемо"),
            (3, 30, "сумувати", "сумувати", "verb", "verb:imperf:inf", "сумувати"),
            (4, 40, "жив", "жити", "verb", "verb:imperf:past:m", "жив"),
            (5, 50, "він", "він", "noun", "noun:pron:pers:3:v_naz", "він"),
            (6, 60, "щодня", "щодня", "adv", "adv", "щодня"),
            (7, 70, "грає", "грати", "verb", "verb:imperf:pres:s:3", "грає"),
            (8, 80, "у", "у", "prep", "prep", "у"),
            (9, 90, "футбол", "футбол", "noun", "noun:inanim:m:v_zna", "футбол"),
        ])
        inputs = word_card_sources.PilotSources(conn, conn, conn)
        register = {"sources": [{"id": "textbooks", "name": "Textbooks", "fields_used": ["example_sentence"]}]}
        books = {"fixture": {"kind": "textbook", "grade": 1, "year": 2025, "author": "Author", "title": "Book"}}
        sense = {"field": "definition_uk", "source_id": VTS, "source_key": "article", "value": "One sense.",
                 "locator": "fixture-definition"}

        def run(entry=30, pos="verb", definition="One sense.", level="A1", text=sentence,
                lemma="сумувати", form="сумувати", function_word=False, *, literary=False):
            conn.execute("UPDATE textbooks SET text=?", ("" if literary else text,))
            reading_register = register
            if literary:
                conn.execute("DELETE FROM literary_texts")
                conn.execute("""
                    INSERT INTO literary_texts VALUES
                    (1,'chunk-1','ukrlib-fixture',?,'Literary author','Literary work','work-1',NULL,'modern','prose'),
                    (2,'chunk-2','unregistered-fixture',?,'Other author','Other work','work-2',NULL,'modern','prose')
                """, (text, text))
                reading_register = {"sources": [*register["sources"],
                    {"id": "literary_corpus", "name": "Literary corpus", "fields_used": ["example_sentence"],
                     "permission_status": "pending-expert-contact"}]}
            levels = {
                "бути": [{"word": "бути", "pos": "дієслово (недок.)", "guideword": "", "level": level}],
                "грати": [{"word": "грати", "pos": "дієслово (недок.)", "guideword": "", "level": "A1"}],
                "футбол": [{"word": "футбол", "pos": "іменник", "guideword": "", "level": "A1"}],
            }
            if function_word:
                levels["у"] = [{"word": "у, в", "pos": "прийменник", "guideword": "", "level": "A1"}]
            senses = examples.bound_senses([{**sense, "value": definition}], VTS, inputs)
            gap = examples.ExampleGap(lemma, entry, pos, frozenset({form}), senses)
            examples.search_corpora([gap], inputs, reading_register, books, levels)
            return gap

        yield run


def test_literary_example_requires_one_bound_sense_and_cites_author_and_work(example_search):
    gap = example_search(literary=True)
    assert [(row["value"], row["source_label"], row["evidence"]["sense_locator"]) for row in gap.values] == [
        ("Ми будемо сумувати!", "Literary author · Literary work", "fixture-definition"),
    ]
    html = projection.render_card({"lemma": gap.lemma, "values": gap.values})
    assert "<q>Ми будемо сумувати!</q>" in html
    assert 'Literary author · Literary work · <a href="https://www.ukrlib.com.ua/"' in html
    assert ("literary_corpus", "duplicate source sentence") not in gap.attempts
    ambiguous = example_search(literary=True, definition="First. || Second.")
    assert ambiguous.values == []
    assert ambiguous.attempts["literary_corpus", "example sense not decidable by code"] == (
        1, "literary_texts:ukrlib-fixture:chunk-1:1 [text:0:19]",
    )


def test_example_refuses_a_different_vesum_entry_or_part_of_speech(example_search):
    confirmed = example_search().values
    assert len(confirmed) == 1
    assert confirmed[0]["source_label"] == "Author · Book (2025) · Page 3"
    assert confirmed[0]["value"] == "Ми будемо сумувати!"
    assert confirmed[0]["evidence"]["normalization"] == {"whitespace": False, "stress_marks": False}
    assert confirmed[0]["locator"] == "textbooks:fixture:fixture-chunk:1 [text:0:19]"
    for entry, pos in ((31, "verb"), (30, "noun")):
        gap = example_search(entry=entry, pos=pos)
        assert gap.values == []
        assert ("textbooks", "example target entry or part of speech unresolved") in gap.attempts


def test_example_corpus_candidate_for_a_multisense_entry_stays_held(example_search):
    for definition in ("1》 First. 2》 Second.", "First. || Second."):
        gap = example_search(definition=definition)
        assert gap.values == []
        assert gap.attempts["textbooks", "example sense not decidable by code"] == (
            1, "textbooks:fixture:fixture-chunk:1 [text:0:19]",
        )


def test_example_rejects_length_and_out_of_level_words_with_reason(example_search):
    # Verbatim sentence from the same two-part primer, part 2 chunk s0076.
    long_sentence = "У хаті на високій горі жив дядько Йой."
    gap = example_search(entry=40, text=long_sentence, lemma="жити", form="жив")
    assert gap.values == []
    assert ("textbooks", "example exceeds word limit") in gap.attempts
    gap = example_search(level="B1")
    assert gap.values == []
    reason = ("textbooks", "example word outside verified A1–A2")
    assert reason in gap.attempts
    # Literal Большакова grade-two sentence from part 2, chunk s0056.
    sentence = "Він щодня грає у футбол."
    args = {"entry": 60, "pos": "adv", "lemma": "щодня", "form": "щодня", "text": sentence}
    gap = example_search(**args)
    assert gap.values == []
    assert reason in gap.attempts
    assert [value["value"] for value in example_search(**args, function_word=True).values] == [sentence]


@pytest.mark.parametrize("chunk", [
    # Layouts from the census of the full textbook pool (PR #13427 finding F4:
    # "У середу я планую ? ." in Вашуленко, grade two, row 80494).
    "Ми будемо сумувати ?",
    "Ми будемо сумувати ! .",
    "Ми будемо ___ сумувати!",
    "Ми будемо ( ) сумувати!",
    "Ми будемо сумувати!\n_______",
    "Ми будемо сумувати? . . . . . 12",
    "Ми будемо сумувати!\n?\n?",
    "Ми будемо сумувати!\n.\n.\nРозкажи.",
    "Ми будемо сумувати! . . . . Тема",
    "5. Ми будемо сумувати!",
    "107.1. Ми будемо сумувати!",
    "63°. Ми будемо сумувати!",
    "ІІ. Ми будемо сумувати!",
    "25 І. Ми будемо сумувати!",
    "Крок 2. Ми будемо сумувати!",
    "§ 2. Ми будемо сумувати!",
    "Я ?\n.\nМи будемо сумувати!",
    "Б Ми будемо сумувати!",
    "В Ми будемо сумувати!",
    "Б Ми будемо раді.\nВ Ми будемо сумувати!\nГ Ми будемо співати.",
])
def test_exercise_fragment_is_not_admitted_as_an_example(example_search, chunk):
    """Defect class: exercise fragment admitted as an example.

    A detached mark, a blank, an item label, an option letter or an empty
    answer slot marks a task item. The otherwise eligible fixture sentence
    must stay held with the complete-sentence reason.
    """
    gap = example_search(text=chunk)
    assert gap.values == []
    assert ("textbooks", "example needs context or is not a complete sentence") in gap.attempts


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def mint(number, kind, identity, evidence):
    return {"event_id": f"ie_{900000 + number}", "kind": kind, "build_id": "fixture-slice2",
            "to": [identity], "evidence": encoded(evidence).decode("utf-8")}


def pinned_union(base, companion):
    """Calculate the expected literal append independently of the allocation validator."""
    effective = copy.deepcopy(base)
    for addition in companion["senses"]:
        for entry in effective["entries"]:
            if entry["card_id"] == addition["card_id"]:
                entry["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"] += copy.deepcopy(companion["source_records"])
    effective["events"] += copy.deepcopy(companion["events"])
    effective["registry_version"] += bool(companion["senses"] or companion["source_records"])
    return {"base_sha256": sha(base), "companion_sha256": sha(companion), "combined_sha256": sha(effective)}


def recipe(field, record_key="vts:яйце", pointer="/article", text="A literal definition.", sense_id=SENSE):
    if record_key in {"vts", "ulif", "vesum", "sum20", "mirror"}:
        record_key += ":яйце"
    claim = {"card_id": TARGET, "entry_id": 436914, "field": field, "record_key": record_key,
             "pointer": pointer, "span": [0, len(text)]}
    if sense_id is not None:
        claim.update(sense_id=sense_id, source_sense_key="fixture:sense:1", scope_key=field)
    return claim


def add_scope(manifest, claim):
    manifest["scopes"][claim["scope_key"]] = {
        "record_key": claim["record_key"], "source_sense_key": claim["source_sense_key"],
        "span": claim["span"][:], "card_id": claim["card_id"], "sense_id": claim["sense_id"],
        "pointer": claim["pointer"],
    }


@pytest.fixture
def batch():
    inventory = json.loads((ROOT / "registry/atlas/a1-v1-inventory.json").read_text())
    base = json.loads((ROOT / "registry/atlas/identity/registry.json").read_text())
    companion = {"schema_version": "atlas-a1-slice2-allocation.v1", "base_sha256": sha(base),
                 "senses": [], "source_records": [], "events": []}
    for index, sense_id in enumerate((SENSE, OTHER_SENSE), 1):
        evidence = {"card_id": TARGET, "source_id": VTS, "source_sense_key": f"fixture:sense:{index}"}
        companion["senses"].append({"card_id": TARGET, "sense": {"sense_id": sense_id, "order": index + 1,
                                                                  "state": "active"},
                                    "event": mint(index, "sense_mint", sense_id, evidence)})
    sources = {"inventory_sha256": sha(inventory), "calls": {}, "records": {}}
    literal = {
        "vts:яйце": (VTS, "query_slovnyk_me", "served_dictionary", {
            "source_entry_id": 77, "homonym": 1,
            "article": "A literal definition.\nadjacent label\nДжерело: fixture footer",
            "example": "An exact cited sentence.", "register": "formal", "synonym": "paired-term",
            "antonym": "opposite-term", "collocation": "paired phrase"}),
        "ulif:яйце": ("ulif", "query_ulif_records", "official", {"entry_id": 8077, "headword": "яйце" + ACUTE}),
        "vesum:яйце": ("vesum", "inspect_lemma", "official", {"clean_analyses": [
            {"entry_id": 436914, "word_form": "fixture-form", "tags": "noun:n:v_naz"}]}),
        "sum20:яйце": ("sum20", "query_sum20", "official", {"headword": "яйце" + ACUTE}),
        "mirror:яйце": ("sum20_slovnyk_mirror", "query_sum20", "mirror", {"headword": "яйце" + ACUTE,
                                                                 "article": "A mirror definition."}),
        "balla": ("balla", "translate_en_uk", "dictionary", {
            "direction": "en-uk", "hits": [{"word": "English fixture gloss", "definition": "fixture-pair"}]}),
    }
    source_record_ids = {}
    for index, (key, (source, tool, role, payload)) in enumerate(literal.items(), 10):
        arguments = ({"words": ["яйце"]} if tool == "query_ulif_records" else
                     {"lemma": "яйце"} if tool == "inspect_lemma" else
                     {"word": "яйце"} if tool in {"query_slovnyk_me", "query_sum20"} else
                     {"query": "fixture"})
        sources["calls"][key] = {"tool": tool, "arguments": arguments, "response": copy.deepcopy(payload)}
        record = {"source_id": source, "snapshot_id": f"fixture:{key}:snapshot:1", "locator": f"fixture:{key}:row:77",
                  "source_url": f"https://example.invalid/{key}/77", "retrieved_at": "2026-01-01T00:00:00Z",
                  "content_sha256": sha(payload), "parser_version": "fixture-v1", "payload": payload,
                  "tool": tool, "arguments": arguments, "response_sha256": sha(payload), "call_key": key,
                  "source_role": role}
        sources["records"][key] = record
        identity = f"sr_{index:012d}"
        source_record_ids[key] = identity
        companion["source_records"].append({"source_record_id": identity, "source_id": source,
            "aliases": [{"kind": "table_row", "key": record["locator"], "snapshot_id": record["snapshot_id"]}],
            "correspondence": [{"snapshot_id": record["snapshot_id"], "status": "unique", "locator": record["locator"]}]})
        companion["events"].append(mint(index, "source_record_mint", identity,
            {"source_id": source, "snapshot_id": record["snapshot_id"], "locator": record["locator"]}))
    card_ids = sorted({card for _, _, card, _ in SELECTED})
    definition = recipe("definition_uk")
    form = recipe("paradigm", "vesum", "/clean_analyses/0/word_form", "fixture-form", None)
    form["slot"] = "noun:n:v_naz"
    stress = recipe("stress", "ulif", "/headword", "яйце" + ACUTE, None)
    manifest = {"card_ids": card_ids, "denominator": {"all_rows": 2144, "selected_rows": 19},
        "inventory_sha256": sha(inventory), "sources_sha256": sha(sources), "claims": [definition, form],
        "stress_attempts": {card: [{"source_id": source, "state": "not_found"} for source in
                                    ("ulif", "sum20", VTS)] for card in card_ids},
        "scopes": {}, "example_approvals": {}, "field_residuals": {}, "field_dependencies": {},
        "held_units": [], "source_record_ids": source_record_ids}
    manifest["stress_attempts"][TARGET][0].update(state="supported", claim=stress)
    add_scope(manifest, definition)
    pins = pinned_union(base, companion)
    manifest["allocation_pins"] = pins
    register = {"schema_version": 2, "sources": [{"id": source, "appears_in": ["internal"]}
                for source in sorted({record["source_id"] for record in sources["records"].values()})]}
    return {"inventory": inventory, "base": base, "companion": companion, "manifest": manifest,
            "sources": sources, "pins": pins, "register": register}


def assemble(batch):
    return cards.build(**batch)


def target(result):
    return next(card for card in result["cards"] if card["card_id"] == TARGET)


def account(result, field, sense_id=None, card_id=TARGET):
    return next(row for row in result["accounting"] if
                (row["card_id"], row["sense_id"], row["field"]) == (card_id, sense_id, field))


def values(result, field, sense_id=None):
    return [a["value"] for a in target(result)["assertions"]
            if a["field"] == field and a["subject"]["id"] == (sense_id or TARGET)]


def refresh(batch, key):
    if key in {"vts", "ulif", "vesum", "sum20", "mirror"}:
        key += ":яйце"
    record = batch["sources"]["records"][key]
    batch["sources"]["calls"][record["call_key"]]["response"] = copy.deepcopy(record["payload"])
    record["response_sha256"] = sha(record["payload"])
    record["content_sha256"] = sha(record["payload"])
    batch["manifest"]["sources_sha256"] = sha(batch["sources"])


def set_stress(batch, source, text):
    key = ("vts" if source == VTS else source) + ":яйце"
    batch["sources"]["records"][key]["payload"]["headword"] = text
    refresh(batch, key)
    claim = recipe("stress", key, "/headword", text, None)
    for attempt in batch["manifest"]["stress_attempts"][TARGET]:
        attempt["state"] = "supported" if attempt["source_id"] == source else "not_found"
        if attempt["source_id"] == source:
            attempt["claim"] = claim
    return claim


def example_claim(batch):
    claim = recipe("examples", pointer="/example", text="An exact cited sentence.")
    batch["manifest"]["claims"].append(claim)
    add_scope(batch["manifest"], claim)
    return claim


def approve_example(batch, claim):
    receipt = make_receipt(claim["record_key"], batch["sources"]["records"][claim["record_key"]],
                           claim["pointer"], claim["span"], claim["entry_id"], claim["source_sense_key"])
    batch["manifest"]["example_approvals"][receipt["receipt_id"]] = {
        "receipt_sha256": sha(receipt), "entry_id": 436914, "sense_id": SENSE,
        "reviewer_family": "google", "verdict": "APPROVE", "record": "fixture-independent-review",
        "quotation": "An exact cited sentence.", "span": claim["span"][:],
        "source_sense_key": "fixture:sense:1", "sources_sha256": sha(batch["sources"])}


def test_frozen_batch_register_pin_projects_without_losing_fields(batch, tmp_path):
    """A release must consume the batch's register pin and refuse changed terms."""
    register = batch["register"]
    for source in register["sources"]:
        source.update(appears_in=["internal", "site", "dataset"],
                      citation={"form": "Fixture dictionary attribution"},
                      terms={"licence": {"name": "Fixture licence"}})
    register_path = tmp_path / "register.yaml"
    register_path.write_text(yaml.safe_dump(register))
    card = target(assemble(batch))
    original = encoded(card)
    release = dataset_projection.create_release(
        [card], release_version="v0.1.1-fixture", register_path=register_path,
        allow_candidates=True,
    )
    row = json.loads(release.dataset)
    assert row["status"] == "CANDIDATE"
    assert row["card_id"] == TARGET
    assert row["card_version"] == card["build"]["card_version"]
    assert {field["field"]: field["value"] for field in row["fields"]} == {
        "definition_uk": "A literal definition.",
        "paradigm": {"slot": "noun:n:v_naz", "forms": ["fixture-form"],
                     "entry_id": 436914, "tags": "noun:n:v_naz"},
        "stress": "яйце" + ACUTE,
    }
    assert len(row["fields"]) == 3
    for field in row["fields"]:
        source = {"definition_uk": VTS, "paradigm": "vesum", "stress": "ulif"}[field["field"]]
        assertion = next(a for a in card["assertions"] if a["assertion_id"] == field["assertion_id"])
        assert field["subject"] == assertion["subject"]
        assert field["citation"] == {
            "source_id": source, "snapshot_id": assertion["snapshot_id"],
            "locator": assertion["locator"], "source_record_id": assertion["source_record_id"],
            "source_record_key": assertion["source_record_key"],
            "licence_ref": {"register_source_id": source, "register_version": 2,
                            "appears_in": ["internal", "site", "dataset"]},
            "attribution": "Fixture dictionary attribution", "licence": {"name": "Fixture licence"},
            "terms_ref": f"docs/sources/permissions-register.yaml#sources/{source}/terms",
        }
    assert encoded(card) == original
    register["sources"][0]["terms"]["licence"]["name"] = "Changed terms"
    register_path.write_text(yaml.safe_dump(register))
    with pytest.raises(dataset_projection.ProjectionRefusal, match="Projection register differs from card register"):
        dataset_projection.create_release(
            [card], release_version="v0.1.1-fixture", register_path=register_path,
            allow_candidates=True,
        )


def test_site_projection_preserves_site_only_fields_without_exporting_them(batch, tmp_path):
    """Site-authorized definitions must survive preview without entering datasets."""
    register = batch["register"]
    for source in register["sources"]:
        source.update(appears_in=["internal", "site"] if source["id"] == VTS else
                      ["internal", "site", "dataset"],
                      citation={"form": "Fixture dictionary attribution"},
                      terms={"licence": {"name": "Fixture licence"}})
    register_path = tmp_path / "register.yaml"
    register_path.write_text(yaml.safe_dump(register))
    card = target(assemble(batch))
    options = {"release_version": "v0.1.1-fixture", "register_path": register_path,
               "allow_candidates": True}
    dataset = dataset_projection.create_release([card], **options)
    site = dataset_projection.create_release([card], scope="site", **options)
    dataset_row, site_row = (json.loads(release.dataset) for release in (dataset, site))
    assert {f["field"] for f in dataset_row["fields"]} == {"paradigm", "stress"}
    assert {f["field"] for f in site_row["fields"]} == {"definition_uk", "paradigm", "stress"}
    meaning = next(f for f in site_row["fields"] if f["field"] == "definition_uk")
    assert meaning["value"] == "A literal definition."
    assert meaning["citation"]["source_id"] == VTS
    assert meaning["citation"]["licence_ref"] == {
        "register_source_id": VTS, "register_version": 2, "appears_in": ["internal", "site"],
    }
    assert {f["field"]: f for f in site_row["fields"] if f["field"] != "definition_uk"} == {
        f["field"]: f for f in dataset_row["fields"]}
    assert site_row["card_id"] == dataset_row["card_id"] == TARGET
    assert site_row["card_version"] == dataset_row["card_version"] == card["build"]["card_version"]
    assert site_row["status"] == dataset_row["status"] == "CANDIDATE"
    assert dataset.manifest["source_breakdown"][VTS]["filter_reasons"] == {"dataset_scope_absent": 1}
    assert site.manifest["source_breakdown"][VTS]["filter_reasons"] == {}
    assert dataset.manifest["scope"] == "dataset"
    assert site.manifest["scope"] == "site"


def test_reviewed_lesson_links_require_exact_source_row_and_card_version(tmp_path, monkeypatch):
    """A spelling match cannot replace the frozen source row or a reviewed version."""
    from scripts.generate_mdx.core import generate_mdx

    relative = "curriculum/l2-uk-en/a1-v1/fixture/vocabulary.yaml"
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    items = [{"word": "same", "translation": "first"},
             {"word": "same", "translation": "second"}, {"word": "unresolved"}]
    original = yaml.safe_dump(items).encode()
    source.write_bytes(original)
    version = "cv_" + "1" * 24
    other = "wc_qpcdgkctp7ne"
    inventory = {"freeze": {"files": [{"path": relative,
                    "sha256": hashlib.sha256(original).hexdigest()}]},
                 "rows": [{"id": f"{relative}#/{i}", "source": item} for i, item in enumerate(items)]}
    batch = {"cards": [{"card_id": key, "build": {"card_version": version}}
                       for key in (TARGET, other)],
             "rows": [{"inventory_row_id": f"{relative}#/{i}", "card_id": key}
                      for i, key in enumerate((TARGET, other))]}
    released = tuple({"card_id": key, "card_version": version, "card_kind": "lexeme",
                      "fields": [{"field": "spelling", "value": "same",
                                  "subject": {"kind": "card", "id": key}}]}
                     for key in (TARGET, other))
    monkeypatch.setattr(cards, "ROOT", tmp_path)
    links = cards.LessonCardLinks(inventory, (batch,), released, {TARGET: version})
    hrefs, observations = links.for_vocabulary(source, items)
    assert hrefs == {0: f"/lexicon-v2/word/same/#entry-{TARGET}"}
    assert [r["reason"] for r in observations] == [None, "independent_review_pending", "row_card_unresolved"]
    assert [r["inventory_row_id"] for r in observations] == [f"{relative}#/{i}" for i in range(3)]
    lesson = "---\ntitle: Fixture\nslug: fixture\n---\n# Fixture\n\nLiteral fixture content.\n"
    options = {"vocab_items": items, "level": "a1", "vocabulary_source": source}
    baseline = generate_mdx(lesson, 1, **options)
    report = []
    rendered = generate_mdx(lesson, 1, word_card_links=links, word_card_link_report=report, **options)
    assert f"/lexicon-v2/word/same/#entry-{TARGET}" in rendered
    assert f"entry-{other}" not in rendered
    assert report == observations
    unreviewed = cards.LessonCardLinks(inventory, (batch,), released, {})
    assert generate_mdx(lesson, 1, word_card_links=unreviewed, **options) == baseline
    changed = copy.deepcopy(items)
    changed[0]["translation"] = "different row"
    assert links.for_vocabulary(source, changed)[0] == {}
    source.write_bytes(original + b"\n")
    assert links.for_vocabulary(source, items)[0] == {}
    source.write_bytes(original)
    wrong_source = tmp_path / "another.yaml"
    wrong_source.write_bytes(original)
    assert links.for_vocabulary(wrong_source, items)[0] == {}
    stale = cards.LessonCardLinks(inventory, (batch,), released, {TARGET: "cv_" + "2" * 24})
    assert stale.for_vocabulary(source, items)[0] == {}
    padded = copy.deepcopy(released[0])
    padded["fields"][0]["value"] = " same "
    decomposed = copy.deepcopy(released[0])
    decomposed["fields"][0]["value"] = unicodedata.normalize("NFD", "й")
    for row in (padded, decomposed):
        refused = cards.LessonCardLinks(inventory, (batch,), (row, released[1]), {TARGET: version})
        hrefs, observations = refused.for_vocabulary(source, items)
        assert hrefs == {}
        assert observations[0]["reason"] == "learner_page_unavailable"


def test_reconciles_frozen_rows_and_preserves_pilot_identities(batch):
    """Catch dropped occurrences, reminted identities and self-authenticating allocation swaps."""
    protected = ["registry/atlas/a1-v1-inventory.json", "registry/atlas/identity/registry.json",
                 "registry/atlas/pilot/pilot-v1.json", "registry/atlas/pilot/pilot-v1.register-pin.json",
                 "registry/atlas/pilot/batch1_manifest.json"]
    before = {path: (ROOT / path).read_bytes() for path in protected}
    frozen_inputs = encoded(batch)
    selected = selected_rows(batch["inventory"])
    assert [(row["id"], row["mapping"]["pilot"]["card_id"], row["mapping"]["entry_id"]) for row in selected] == [
        (f"curriculum/l2-uk-en/a1-v1/{lesson}/vocabulary.yaml#/{index}", card, entry)
        for lesson, index, card, entry in SELECTED]
    result = assemble(batch)
    assert Counter(row["state"] for row in result["rows"]) == {"card_produced": 19, "deferred_outside_slice2": 2125}
    assert len(result["rows"]) == len({row["inventory_row_id"] for row in result["rows"]}) == 2144
    assert len(result["cards"]) == 11
    assert sorted(card["card_id"] for card in result["cards"]) == sorted({card for _, _, card, _ in SELECTED})
    assert [row["mapping"] for row in result["rows"]] == [row["mapping"] for row in batch["inventory"]["rows"]]
    assert [row["inventory_row_id"] for row in result["rows"] if row["card_id"] == TARGET] == [
        "curriculum/l2-uk-en/a1-v1/food-and-drink/vocabulary.yaml#/28",
        "curriculum/l2-uk-en/a1-v1/i-eat-i-drink/vocabulary.yaml#/31",
        "curriculum/l2-uk-en/a1-v1/i-eat-i-drink/vocabulary.yaml#/32"]
    original = {entry["card_id"]: entry for entry in batch["base"]["entries"]}
    for card in result["cards"]:
        prior = original[card["card_id"]]
        assert card["key_at_creation"] == prior["key_at_creation"]
        assert [sense["sense_id"] for sense in card["senses"]][:len(prior["senses"])] == [
            sense["sense_id"] for sense in prior["senses"]]
    assert values(result, "definition_uk", SENSE) == ["A literal definition."]
    assert account(result, "mwe_form")["state"] == "not_applicable"
    for kind in ("sense", "record", "alias", "snapshot", "event", "missing_event", "duplicate_event",
                 "coherent_sense", "coherent_record"):
        bad = copy.deepcopy(batch)
        companion = bad["companion"]
        if kind == "sense":
            companion["senses"][0]["sense"]["sense_id"], companion["senses"][1]["sense"]["sense_id"] = OTHER_SENSE, SENSE
        elif kind == "record":
            companion["source_records"][0]["source_record_id"] = companion["source_records"][1]["source_record_id"]
        elif kind == "alias":
            companion["source_records"][0]["aliases"][0]["key"] = "fixture:substitute"
        elif kind == "snapshot":
            companion["source_records"][0]["correspondence"][0]["snapshot_id"] = "substitute-snapshot"
        elif kind == "event":
            companion["senses"][0]["event"]["evidence"] = encoded({"card_id": TARGET,
                "source_id": VTS, "source_sense_key": "fixture:sense:2"}).decode()
        elif kind == "missing_event":
            companion["events"].pop()
        elif kind == "duplicate_event":
            companion["events"].append(copy.deepcopy(companion["events"][0]))
        elif kind == "coherent_sense":
            for addition, identity in zip(companion["senses"], (OTHER_SENSE, SENSE), strict=True):
                addition["sense"]["sense_id"] = identity
                addition["event"]["to"] = [identity]
        else:
            first, second = companion["source_records"][:2]
            first["source_record_id"], second["source_record_id"] = second["source_record_id"], first["source_record_id"]
            companion["events"][0]["to"] = [first["source_record_id"]]
            companion["events"][1]["to"] = [second["source_record_id"]]
        bad["pins"]["companion_sha256"] = sha(companion)
        with pytest.raises(Refusal, match="combined_digest_mismatch" if kind.startswith("coherent") else None):
            assemble(bad)
    assert encoded(batch) == frozen_inputs
    assert {path: (ROOT / path).read_bytes() for path in protected} == before


def test_rejects_wrong_lexeme_sense_span_and_source_role(batch):
    """Catch cross-lexeme/sense receipts, overwide definitions, footer capture and false official attribution."""
    valid = assemble(batch)
    assert values(valid, "definition_uk", SENSE) == ["A literal definition."]
    assert account(valid, "definition_uk", OTHER_SENSE)["state"] == "empty"
    assert account(valid, "definition_uk", OTHER_SENSE)["reason"] == "source_sense_claim_unresolved"
    wrong_record = copy.deepcopy(batch)
    wrong_record["manifest"]["stress_attempts"][TARGET][0]["claim"]["record_key"] = "sum20:яйце"
    wrong_record["sources"]["records"]["sum20:яйце"]["arguments"]["word"] = "foreign"
    refresh(wrong_record, "sum20")
    with pytest.raises(Refusal, match="lemma_query_mismatch"):
        assemble(wrong_record)
    for field, member, literal in (("spelling", "lemma", "foreign"), ("pos", "pos", "noun"),
                                   ("gender", "gender", "n")):
        bad = copy.deepcopy(batch)
        bad["sources"]["records"]["vesum:яйце"]["payload"]["clean_analyses"].append(
            {"entry_id": 425814, "lemma": "foreign", "pos": "noun", "gender": "n"})
        refresh(bad, "vesum")
        bad["manifest"]["claims"].append(recipe(field, "vesum", "/clean_analyses/1/" + member,
                                                literal, None))
        with pytest.raises(Refusal, match="form_entry_mismatch"):
            assemble(bad)
    bad_pointer = copy.deepcopy(batch)
    bad_pointer["manifest"]["scopes"]["definition_uk"]["pointer"] = "/example"
    with pytest.raises(Refusal, match="scope_pointer_mismatch"):
        assemble(bad_pointer)
    overlap = copy.deepcopy(batch)
    duplicate = copy.deepcopy(overlap["manifest"]["claims"][0])
    duplicate.update(sense_id=OTHER_SENSE, source_sense_key="fixture:sense:2", scope_key="other")
    overlap["manifest"]["claims"].append(duplicate)
    add_scope(overlap["manifest"], duplicate)
    with pytest.raises(Refusal, match="overlapping_definition_spans"):
        assemble(overlap)
    for kind, reason in (("lexeme", "claim_lexeme_mismatch"), ("sense", "scope_subject_mismatch"),
                         ("adjacent", "outside_sense_span"), ("whole_article", "outside_sense_span"),
                         ("hash", "source_snapshot_drift"), ("footer", "dictionary_footer")):
        bad = copy.deepcopy(batch)
        claim = bad["manifest"]["claims"][0]
        if kind == "lexeme":
            claim["entry_id"] = 425814
        elif kind == "sense":
            claim["sense_id"] = OTHER_SENSE
        elif kind == "adjacent":
            claim["span"] = [22, 36]
        elif kind == "whole_article":
            claim["span"][1] = len(bad["sources"]["records"]["vts:яйце"]["payload"]["article"])
        elif kind == "hash":
            bad["sources"]["records"]["vts:яйце"]["content_sha256"] = "f" * 64
        else:
            claim["span"] = [37, len(bad["sources"]["records"]["vts:яйце"]["payload"]["article"])]
            bad["manifest"]["scopes"]["definition_uk"]["span"] = claim["span"][:]
        with pytest.raises(Refusal, match=reason):
            assemble(bad)
    mirror = copy.deepcopy(batch)
    claim = mirror["manifest"]["claims"][0]
    claim.update(record_key="mirror:яйце", span=[0, 20])
    add_scope(mirror["manifest"], claim)
    mirror_result = assemble(mirror)
    assert values(mirror_result, "definition_uk", SENSE) == ["A mirror definition."]
    assert next(a for a in target(mirror_result)["assertions"] if a["field"] == "definition_uk")["source_id"] == "sum20_slovnyk_mirror"
    mirror["sources"]["records"]["mirror:яйце"]["source_role"] = "official"
    mirror["manifest"]["sources_sha256"] = sha(mirror["sources"])
    with pytest.raises(Refusal):
        assemble(mirror)
    for kind in ("entry", "sense", "value", "receipt_subject"):
        altered = copy.deepcopy(valid)
        assertion = next(a for a in target(altered)["assertions"] if a["field"] == "definition_uk")
        rid = altered["assertion_receipts"][assertion["assertion_id"]][0]
        receipt = next(r for r in altered["receipts"] if r["receipt_id"] == rid)
        if kind == "value":
            assertion["value"] = "A substituted displayed definition."
        elif kind == "receipt_subject":
            assertion["subject"]["id"] = OTHER_SENSE
        else:
            receipt["entry_id" if kind == "entry" else "sense_key"] = 425814 if kind == "entry" else "fixture:sense:2"
            receipt["receipt_id"] = "wr_" + sha({key: value for key, value in receipt.items() if key != "receipt_id"})
            altered["assertion_receipts"][assertion["assertion_id"]] = [receipt["receipt_id"]]
        target(altered)["build"]["card_version"] = resolver.card_version(target(altered))
        with pytest.raises(Refusal):
            cards.verify(altered, batch["sources"], batch["manifest"])


def test_soviet_normative_as_modern_is_refused_on_every_assertion_path(batch):
    """#12658 AC7: a registered Soviet source cannot supply any modern facet."""
    result = assemble(batch)
    for card in result["cards"]:
        for assertion in card["assertions"]:
            bad = copy.deepcopy(result)
            modified = next(a for c in bad["cards"] for a in c["assertions"]
                            if a["assertion_id"] == assertion["assertion_id"])
            modified["source_id"] = "sum11"
            changed_card = next(c for c in bad["cards"] if c["card_id"] == card["card_id"])
            changed_card["build"]["card_version"] = resolver.card_version(changed_card)
            with pytest.raises(Refusal, match="soviet_normative_as_modern"):
                cards.verify(bad, batch["sources"], batch["manifest"])


def test_stress_fallback_and_forms_require_independent_receipts(batch):
    """Catch skipped stress authorities, discarded doublets and foreign-entry or unreceipted accented forms."""
    for source, text in (("ulif", "яйце" + ACUTE), ("sum20", "яйце" + ACUTE), (VTS, "яйце" + ACUTE)):
        case = copy.deepcopy(batch)
        chosen = set_stress(case, source, text)
        result = assemble(case)
        assert values(result, "stress") == [text]
        assert values(result, "paradigm") == [{"slot": "noun:n:v_naz", "forms": ["fixture-form"],
                                                "entry_id": 436914, "tags": "noun:n:v_naz"}]
        receipt = next(r for r in result["receipts"] if r["quotation"] == text)
        assert receipt["source_id"] == source
        assert receipt["span"] == [0, len(text)]
        assert cards.choose_stress(case["manifest"]["stress_attempts"][TARGET]) == (chosen, None)
    precedence = copy.deepcopy(batch)
    attempts = precedence["manifest"]["stress_attempts"][TARGET]
    attempts[1].update(state="supported", claim={"sentinel": "lower authority"})
    assert values(assemble(precedence), "stress") == ["яйце" + ACUTE]
    variants = copy.deepcopy(batch)
    # Synthetic doublet payload tests receipt mechanics, not the word's normative stress.
    set_stress(variants, "ulif", "я" + ACUTE + "йце" + ACUTE)
    assert values(assemble(variants), "stress") == [["я" + ACUTE + "йце", "яйце" + ACUTE]]
    foreign_stress = copy.deepcopy(batch)
    set_stress(foreign_stress, "ulif", "foreign" + ACUTE)
    with pytest.raises(Refusal, match="stress_lemma_mismatch"):
        assemble(foreign_stress)
    for state in ("ambiguous", "conflict"):
        case = copy.deepcopy(batch)
        set_stress(case, VTS, "яйце" + ACUTE)
        case["manifest"]["stress_attempts"][TARGET][0]["state"] = state
        result = assemble(case)
        assert values(result, "stress") == []
        assert (account(result, "stress")["state"], account(result, "stress")["reason"]) == (
            "empty", "higher_priority_stress_" + state)
    for kind, reason in (("entry", "form_entry_mismatch"), ("slot", "form_slot_mismatch"),
                         ("accent", "accented_form_requires_stress")):
        case = copy.deepcopy(batch)
        analysis = case["sources"]["records"]["vesum:яйце"]["payload"]["clean_analyses"][0]
        if kind == "entry":
            analysis["entry_id"] = 425814
        elif kind == "slot":
            case["manifest"]["claims"][1]["slot"] = "noun:n:v_rod"
        else:
            analysis["word_form"] = "form1" + ACUTE
            case["manifest"]["claims"][1]["span"] = [0, len(analysis["word_form"])]
        refresh(case, "vesum")
        with pytest.raises(Refusal, match=reason):
            assemble(case)
    accented = copy.deepcopy(batch)
    accented["sources"]["records"]["vesum:яйце"]["payload"]["clean_analyses"][0]["word_form"] = "form1" + ACUTE
    accented["manifest"]["claims"][1].update(span=[0, 6], stress_receipt="wr_" + "0" * 64)
    refresh(accented, "vesum")
    with pytest.raises(Refusal):
        assemble(accented)
    supported = copy.deepcopy(batch)
    stress_claim = set_stress(supported, "ulif", "яйце" + ACUTE)
    stress_receipt = make_receipt("ulif:яйце", supported["sources"]["records"]["ulif:яйце"], "/headword", [0, 5], 436914)
    supported["sources"]["records"]["vesum:яйце"]["payload"]["clean_analyses"][0]["word_form"] = "яйце" + ACUTE
    supported["manifest"]["claims"][1].update(span=[0, 5], stress_receipt=stress_receipt["receipt_id"])
    refresh(supported, "vesum")
    result = assemble(supported)
    assert values(result, "paradigm") == [{"slot": "noun:n:v_naz", "forms": ["яйце" + ACUTE],
                                           "entry_id": 436914, "tags": "noun:n:v_naz"}]
    assert values(result, "stress") == ["яйце" + ACUTE]
    form_receipts = account(result, "paradigm")["receipt_ids"]
    stress_receipts = account(result, "stress")["receipt_ids"]
    assert stress_receipts == [stress_receipt["receipt_id"]]
    assert len(form_receipts) == 1 and form_receipts[0] != stress_receipts[0]
    assert cards.choose_stress(supported["manifest"]["stress_attempts"][TARGET]) == (stress_claim, None)
    delivered = assemble(batch)
    assertion = next(a for a in target(delivered)["assertions"] if a["field"] == "paradigm")
    assertion["value"]["forms"] = ["foreign-form"]
    target(delivered)["build"]["card_version"] = resolver.card_version(target(delivered))
    with pytest.raises(Refusal):
        cards.verify(delivered, batch["sources"], batch["manifest"])

    # Synthetic ULIF and VESUM rows supply independent receipts in canonical slot order.
    form = {"entry_id": 20, "variant_order": 1, "grammatical_tags": '["v_rod","s"]',
            "unmapped_labels": "[]", "preposition": "", "marked_asterisk": 0,
            "is_lemma": 0, "is_invariable": 0, "form_unstressed": "абв", "form_stressed": f"а{ACUTE}бв"}
    ulif = [
        dict(form, id=1),
        dict(form, id=2, is_lemma=1, form_stressed=f"а{ACUTE}бе{ACUTE}", form_unstressed="абе"),
        dict(form, id=3, grammatical_tags='["v_naz","s"]', form_stressed=f"а{ACUTE}бе", form_unstressed="абе"),
    ]
    vesum = [
        {"id": 5, "entry_id": 30, "lemma": "абе", "word_form": "где", "tags": "noun:m:v_rod"},
        {"id": 6, "entry_id": 30, "lemma": "абе", "word_form": "абе", "tags": "noun:m:v_naz"},
    ]
    snapshots = {"ulif": "fixture-ulif", "vesum": "fixture-vesum"}
    stress, paradigm = _paradigm(ulif, vesum, snapshots, None, "entry_fingerprint")
    assert stress[0]["value"] == {"form": f"а{ACUTE}бе{ACUTE}", "readings": [f"а{ACUTE}бе", f"абе{ACUTE}"]}
    assert stress[0]["receipt"]["locator"] == "ulif:ulif_forms:id:2"
    assert [(slot["slot"], slot["comparison"]) for slot in paradigm["slots"]] == [
        ("v_naz.s", "agrees"), ("v_rod.s", "differs"),
    ]
    difference = paradigm["slots"][1]
    assert difference["ulif"][0]["value"]["form"] == f"а{ACUTE}бв"
    assert difference["ulif"][0]["receipt"]["entry_id"] == 20
    assert difference["vesum"][0]["value"] == {"form": "где", "tags": "noun:m:v_rod"}
    assert difference["vesum"][0]["receipt"]["locator"] == "vesum:forms_all:id:5"
    _, unbound = _paradigm(ulif, [], snapshots, "homonym_correspondence_unresolved",
                           "entry_fingerprint")
    assert {slot["comparison"] for slot in unbound["slots"]} == {"unresolved"}

    for tags, vesum_tags, expected_slot in (
        ('["v_naz"]', "numr:p:v_naz", "v_naz.p"),
        ('["v_naz","m"]', "noun:m:v_naz", "v_naz.s.m"),
    ):
        _, aligned = _paradigm([dict(ulif[2], grammatical_tags=tags)],
                               [dict(vesum[1], tags=vesum_tags)], snapshots, None, "entry_fingerprint")
        assert [(slot["slot"], slot["comparison"]) for slot in aligned["slots"]] == [(expected_slot, "agrees")]
    _, mixed_number = _paradigm([dict(ulif[2], grammatical_tags='["v_naz"]')],
                                [vesum[1], dict(vesum[1], id=7, tags="noun:p:v_naz")],
                                snapshots, None, "entry_fingerprint")
    assert [(slot["slot"], slot["comparison"], slot["reason"]) for slot in mixed_number["slots"]] == [
        (slot, "unresolved", "ulif_slot_number_unresolved") for slot in ("v_naz", "v_naz.s", "v_naz.p")
    ]

    _, mixed_granularity = _paradigm(
        [dict(ulif[2], grammatical_tags='["v_naz","m"]'),
         dict(ulif[0], grammatical_tags='["v_naz","f"]')],
        [dict(vesum[1], tags="numr:p:v_naz"),
         dict(vesum[1], id=8, word_form="абв", tags="numr:p:v_naz")],
        snapshots, None, "entry_fingerprint",
    )
    assert {slot["slot"]: (slot["comparison"], slot["reason"]) for slot in mixed_granularity["slots"]} == {
        slot: ("unresolved", "ulif_slot_granularity_unresolved") for slot in ("v_naz.m", "v_naz.f", "v_naz.p")
    }
    assert [w["value"]["form"] for slot in mixed_granularity["slots"] for w in slot["vesum"]] == ["абе", "абв"]


def test_unreviewed_examples_and_unaligned_rich_fields_stay_empty(batch):
    """Catch suitability bypass, rewritten examples, cross-sense rich fields and reversed bilingual matches."""
    claim = example_claim(batch)
    batch["manifest"]["field_residuals"]["examples"] = "independent_a1_review_pending"
    rich = {"register": ("/register", "formal"), "synonyms": ("/synonym", "paired-term"),
            "antonyms": ("/antonym", "opposite-term"), "collocations": ("/collocation", "paired phrase"),
            "gloss_en": ("/hits/0/word", "English fixture gloss")}
    for field in rich:
        batch["manifest"]["field_residuals"][field] = "source_sense_alignment_unresolved"
        batch["manifest"]["field_dependencies"][field] = "reviewed correspondence for fixture:sense:1"
    pending = assemble(batch)
    assert values(pending, "examples", SENSE) == []
    assert pending["pending_examples"][0]["receipt"]["quotation"] == "An exact cited sentence."
    assert account(pending, "examples", SENSE)["reason"] == "independent_a1_review_pending"
    for field in rich:
        residual = account(pending, field, SENSE)
        assert (residual["state"], residual["reason"], residual["dependency"], residual["owner"]) == (
            "empty", "source_sense_alignment_unresolved", "reviewed correspondence for fixture:sense:1", "Atlas coordinator")
        assert values(pending, field, SENSE) == []
    approve_example(batch, claim)
    approved = assemble(batch)
    assert values(approved, "examples", SENSE) == ["An exact cited sentence."]
    assert account(approved, "examples", SENSE)["state"] == "supported"
    for kind in ("wrong_sense", "wrong_digest", "wrong_reviewer"):
        bad = copy.deepcopy(batch)
        approval = next(iter(bad["manifest"]["example_approvals"].values()))
        approval[{"wrong_sense": "sense_id", "wrong_digest": "receipt_sha256", "wrong_reviewer": "reviewer_family"}[kind]] = {
            "wrong_sense": OTHER_SENSE, "wrong_digest": "f" * 64, "wrong_reviewer": "openai"}[kind]
        with pytest.raises(Refusal, match="example_review_binding_mismatch"):
            assemble(bad)
    rewritten = copy.deepcopy(batch)
    rewritten["sources"]["records"]["vts:яйце"]["payload"]["example"] = "An invented replacement."
    refresh(rewritten, "vts")
    assert values(assemble(rewritten), "examples", SENSE) == []
    aligned = copy.deepcopy(batch)
    for field, (pointer, literal) in rich.items():
        candidate = recipe(field, "balla" if field == "gloss_en" else "vts", pointer, literal)
        if field == "gloss_en":
            candidate.update(translation_direction="en-uk",
                usage_pair={"pointer": "/hits/0/definition", "span": [0, 12]},
                supporting_spans=[{"pointer": "/hits/0/definition", "span": [0, 12]}])
        aligned["manifest"]["claims"].append(candidate)
        add_scope(aligned["manifest"], candidate)
    accepted = assemble(aligned)
    for field, (_, literal) in rich.items():
        assert values(accepted, field, SENSE) == [literal]
        assert account(accepted, field, SENSE)["state"] == "supported"
    wrong_sense = copy.deepcopy(aligned)
    wrong_sense["manifest"]["claims"][-1]["sense_id"] = OTHER_SENSE
    with pytest.raises(Refusal, match="scope_subject_mismatch"):
        assemble(wrong_sense)
    reversed_pair = copy.deepcopy(aligned)
    reversed_pair["manifest"]["claims"][-1]["translation_direction"] = "uk-en"
    with pytest.raises(Refusal):
        assemble(reversed_pair)
    unreceipted_pair = copy.deepcopy(aligned)
    unreceipted_pair["manifest"]["claims"][-1]["usage_pair"] = {"pointer": "/missing", "span": [0, 1]}
    with pytest.raises(Refusal, match="bilingual_pair_not_receipted"):
        assemble(unreceipted_pair)
    other_hit = copy.deepcopy(aligned)
    gloss = other_hit["manifest"]["claims"][-1]
    gloss["supporting_spans"][0]["pointer"] = "/hits/1/definition"
    gloss["usage_pair"]["pointer"] = "/hits/1/definition"
    with pytest.raises(Refusal, match="bilingual_pair_outside_hit"):
        assemble(other_hit)


def test_replay_is_deterministic_and_refuses_input_drift(batch, tmp_path, monkeypatch, capsys):
    """Catch nondeterministic output, source writes and accepted partial output after snapshot drift."""
    fixture_root = tmp_path / "inputs"
    paths = {cards.MANIFEST: batch["manifest"], cards.COMPANION: batch["companion"],
             "registry/atlas/a1-v1-inventory.json": batch["inventory"],
             "registry/atlas/identity/registry.json": batch["base"],
             "docs/sources/permissions-register.yaml": batch["register"], "sources.json": batch["sources"]}
    for relative, content in paths.items():
        path = fixture_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded(content) + b"\n")
    before = {relative: (fixture_root / relative).read_bytes() for relative in paths}
    monkeypatch.setattr(cards, "ROOT", fixture_root)
    monkeypatch.setattr(cards, "MANIFEST_SHA256", sha(batch["manifest"]))
    source_path = fixture_root / "sources.json"
    first, second, rejected = (tmp_path / name for name in ("first.json", "second.json", "rejected.json"))
    for output in (first, second):
        assert cards.main(["--sources", str(source_path), "--output", str(output)]) == 0
        counts = json.loads(capsys.readouterr().out)
        assert (counts["cards"], counts["rows"]) == (11, 2144)
    assert first.read_bytes() == second.read_bytes()
    assert values(json.loads(first.read_bytes()), "definition_uk", SENSE) == ["A literal definition."]
    assert cards.main(["--sources", str(source_path), "--output", str(first), "--check"]) == 0
    capsys.readouterr()
    for kind in ("field_state", "row_mapping", "receipt_ids"):
        tampered = json.loads(first.read_bytes())
        row = next(row for row in tampered["accounting"] if row["state"] == "empty")
        if kind == "field_state":
            row["state"] = "supported"
        elif kind == "receipt_ids":
            row["receipt_ids"] = ["wr_" + "0" * 64]
        else:
            tampered["rows"][0]["mapping"] = {"kind": "unresolved"}
        rejected.write_bytes(encoded(tampered) + b"\n")
        assert cards.main(["--sources", str(source_path), "--output", str(rejected), "--check"]) == 1
        assert "delivered_output_mismatch" in capsys.readouterr().err
    rejected.unlink()
    assert {relative: (fixture_root / relative).read_bytes() for relative in paths} == before
    changed = copy.deepcopy(batch["sources"])
    changed["records"]["vts:яйце"]["payload"]["article"] = "Changed consumed bytes."
    source_path.write_bytes(encoded(changed) + b"\n")
    source_after_drift = source_path.read_bytes()
    accepted_before = first.read_bytes()
    for output in (rejected, first):
        assert cards.main(["--sources", str(source_path), "--output", str(output)]) == 1
        assert "source_snapshot_drift" in capsys.readouterr().err
    assert not rejected.exists()
    assert first.read_bytes() == accepted_before
    assert source_path.read_bytes() == source_after_drift
    assert {relative: (fixture_root / relative).read_bytes() for relative in paths if relative != "sources.json"} == {
        relative: content for relative, content in before.items() if relative != "sources.json"}
