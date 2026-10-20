"""CTO pilot-v1 regression fixture (#8977 / #8981, OO-38).

Names are copied from the task's 13-card inventory. The common lemma and tags
in the case fixture are verbatim VESUM values verified through Sources MCP.
"""

import copy

import pytest

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_verify as verify
from tests.test_word_card_assembly import LABEL_F, World, make_inputs

HOMOGRAPHS = (
    "Мама", "Баран", "Любов", "Банк", "Базар", "Бар", "Новий",
    "Батьківщина", "Шуба", "Бандура", "Бабуся", "Бабин",
)


def card(spelling, kind):
    return {
        "card_kind": kind,
        "key_at_creation": {"spelling": spelling},
        "links": [],
        "assertions": [{"source_id": "puls", "field": "cefr", "status": "active",
                        "mapping": {"confidence": "high"}}],
    }


@pytest.fixture
def pilot_cards():
    names = {f"name-{i}": card(word, "proper_name") for i, word in enumerate((*HOMOGRAPHS, "ЮНЕСКО"))}
    lexemes = {f"lexeme-{i}": card(word.lower(), "lexeme") for i, word in enumerate(HOMOGRAPHS)}
    return names | lexemes


def test_pilot_excludes_all_twelve_common_word_homographs(pilot_cards):
    selected = wa.learner_cards(pilot_cards)
    assert set(selected) == {"name-12", *(f"lexeme-{i}" for i in range(12))}
    assert [c["key_at_creation"]["spelling"] for c in selected.values()
            if c["card_kind"] == "proper_name"] == ["ЮНЕСКО"]


def test_homograph_exclusion_overrides_allowlist_and_source_scope(pilot_cards, monkeypatch):
    monkeypatch.setattr(wa, "LEARNER_PROPER_NAME_ALLOWLIST", frozenset((*HOMOGRAPHS, "ЮНЕСКО")))
    selected = wa.learner_cards(pilot_cards)
    assert set(selected) == {"name-12", *(f"lexeme-{i}" for i in range(12))}


def test_source_scope_alone_does_not_admit_unlisted_names(pilot_cards):
    names = {key: value for key, value in pilot_cards.items() if value["card_kind"] == "proper_name"}
    assert set(wa.learner_cards(names)) == {"name-12"}


@pytest.mark.parametrize("change", ["suppressed", "rejected", "ambiguous", "unresolved", "absent"])
def test_allowlisted_name_still_requires_usable_source_scope(pilot_cards, change):
    name = copy.deepcopy(pilot_cards["name-12"])
    scope = name["assertions"][0]
    if change == "suppressed":
        scope["status"] = "suppressed"
    elif change == "rejected":
        scope["review"] = {"status": "rejected"}
    elif change == "ambiguous":
        scope["mapping"]["ambiguous"] = True
    elif change == "unresolved":
        scope["mapping"]["confidence"] = "unresolved"
    else:
        name["assertions"] = []
    assert wa.learner_cards({"name-12": name}) == {}


def case_world():
    world = World()
    world.ulif(1, "батьківщина", "Батьківщина", LABEL_F,
               rows=[("називний", "Батьківщина", "")])
    world.vesum_form(101, "батьківщина", "батьківщина", "noun:inanim:f:v_naz")
    # An exact-case proper entry must never supply common-noun evidence.
    world.vesum_form(102, "Батьківщина", "Батьківщина", "noun:inanim:f:v_naz:prop")
    world.finish({})
    return world


@pytest.fixture
def case_inputs(tmp_path, monkeypatch):
    # Independent frozen allocation for this one-card regression, as in the
    # existing assembly fixtures. Never derive the expected pin from a build.
    monkeypatch.setattr(allocator, "ASSEMBLY_ALLOCATION_DIGEST",
                        "dc024726c75deee7b04b2a31da66ab39ba78efdb485f25384546a8a8f97969be")
    world = case_world()
    try:
        yield make_inputs(world, tmp_path)
    finally:
        for connection in (world.sources, world.vesum, world.raw):
            connection.close()


def test_assembly_normalizes_common_spelling_to_vesum_lemma(case_inputs):
    result = wa.build(case_inputs)
    built = next(iter(result["cards"].values()))
    assert built["key_at_creation"]["spelling"] == "Батьківщина"
    spellings = [a for a in built["assertions"] if a["field"] == "spelling"]
    assert {(a["source_id"], a["value"], a["value_norm"]) for a in spellings} == {
        ("ulif", "Батьківщина", "батьківщина"),
    }
    assert built["fields"]["spelling"]["values"][0]["value_norm"] == "батьківщина"
    assert all(verify.Resolver(case_inputs).check(built, a) is None for a in spellings)
    assert "vesum_forms:батьківщина" in case_inputs.sources.consumed
    assert verify.matched_vesum_entry(case_inputs, case_inputs.units[0]) is None


def test_vesum_spelling_lookup_separates_common_and_proper_entries(case_inputs):
    common = wa.vesum_spelling_rows(case_inputs.sources, "Батьківщина", "noun", False)
    proper = wa.vesum_spelling_rows(case_inputs.sources, "Батьківщина", "noun", True)
    assert {(r["entry_id"], r["lemma"]) for r in common} == {(101, "батьківщина")}
    assert {(r["entry_id"], r["lemma"]) for r in proper} == {(102, "Батьківщина")}
    assert wa.vesum_spelling_rows(case_inputs.sources, "Батьківщина", "adj", False) == []


def test_lexeme_spelling_preserves_exact_vesum_case(case_inputs):
    # Synthetic same-class capitalized lemma: spelling follows the source case,
    # rather than unconditionally lowercasing every lexeme.
    case_inputs.sources.vesum.execute("UPDATE forms_all SET tags='noun:inanim:f:v_naz' WHERE entry_id=102")
    built = next(iter(wa.build(case_inputs)["cards"].values()))
    assert built["fields"]["spelling"]["values"][0]["value_norm"] == "Батьківщина"


def test_excluded_names_remain_accounted_for(pilot_cards, tmp_path):
    ledger = wa.Ledger()
    for key in pilot_cards:
        ledger.start(key, key)
    result = {"cards": pilot_cards, "ledger": ledger, "build_id": "fixture",
              "block": {"inputs": {}, "rules_version": "fixture"}, "takedown": []}
    wa.write_output(tmp_path, result, {})
    written = foundation.load(tmp_path / "ledger.json")
    assert set(written["excluded_cards"]) == {f"name-{i}" for i in range(12)}
    assert set(written["cards"]) == set(pilot_cards)
    assert {path.stem for path in (tmp_path / "cards").glob("*.json")} == {
        "name-12", *(f"lexeme-{i}" for i in range(12)),
    }
