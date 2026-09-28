"""Word-card v1 schema (#8978): the worked examples validate, their ids are reproducible,
and removing one source recomputes a field's surviving value and quality state (AC-03).

Spec: docs/atlas/word-cards/schema.md (§8 field resolution), worked-examples.md.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = REPO_ROOT / "schemas" / "word-card-v1.schema.json"
EXAMPLES = REPO_ROOT / "docs" / "atlas" / "word-cards" / "examples"
GENERATOR = EXAMPLES / "build_examples.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("word_card_examples", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.fixture(scope="module")
def validator():
    return Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))


def _example_files() -> list[Path]:
    files = sorted(EXAMPLES.glob("*.json"))
    assert len(files) >= 8, "expected the committed worked-example cards"
    return files


@pytest.mark.parametrize("path", _example_files(), ids=lambda p: p.stem)
def test_example_validates_against_schema(path: Path, validator: Draft202012Validator) -> None:
    card = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(card), key=lambda e: list(e.path))
    assert not errors, "\n".join(f"{list(e.path)}: {e.message}" for e in errors)


@pytest.mark.parametrize("path", _example_files(), ids=lambda p: p.stem)
def test_assertion_ids_follow_the_formula(path: Path, gen) -> None:
    card = json.loads(path.read_text(encoding="utf-8"))
    for a in card["assertions"]:
        expected = gen.aid(
            a["source_id"],
            a["snapshot_id"],
            a["locator"],
            a["subject"],
            a["field"],
            a["value_norm"],
            a["extraction_version"],
        )
        assert a["assertion_id"] == expected, f"{path.name}: {a['field']} {a['locator']}"
        assert a["subject"]["id"] == card["card_id"] or a["subject"]["kind"] in ("sense", "link")
    for link in card["links"]:
        assert link["from"] == card["card_id"]


def test_generator_reproduces_committed_examples(gen) -> None:
    """The build is deterministic: regenerating yields the committed files byte for byte."""
    built = {
        "zamok-castle": gen.build_castle(),
        "zamok-lock": gen.build_lock(),
        "zamok-settlement": gen.build_settlement(),
        "kliuch-1": gen.build_kliuch(),
        "idiom-buduvaty-povitriani-zamky": gen.build_idiom(),
        "bronia-armour": gen.build_bronia_armour(),
        "bronia-reservation": gen.build_bronia_reserv(),
        "vriady-hody-conflict": gen.build_vriady(),
    }
    imperf, perf = gen.build_aspect_pair()
    built["vybihaty-imperf"], built["vybihty-perf"] = imperf, perf
    for name, card in built.items():
        committed = json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
        assert card == committed, name


def _card(name: str) -> dict:
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def test_states_in_the_examples() -> None:
    castle, lock, idiom = _card("zamok-castle"), _card("zamok-lock"), _card("idiom-buduvaty-povitriani-zamky")
    bronia, vriady = _card("bronia-armour"), _card("vriady-hody-conflict")
    assert castle["fields"]["stress"]["state"] == "verified"
    assert castle["fields"]["stress"]["independence_groups_agreeing"] == 3  # ULIF, VESUM, kaikki
    assert castle["fields"]["cefr"]["state"] == "single-source"  # PULS only
    assert lock["fields"]["english_gloss"]["state"] == "unverified"  # tier-3 producers only
    assert lock["fields"]["stress"]["state"] == "verified"  # ULIF paradigm + VESUM comment
    assert idiom["fields"]["mwe_form"]["state"] == "single-source"  # four assertions, one lineage group
    assert bronia["fields"]["stress"]["state"] == "verified"
    assert vriady["fields"]["stress"]["state"] == "conflict" and vriady["fields"]["stress"]["selected"] is None
    unsplit = [s for s in castle["senses"] if s["state"] == "unsplit"]
    assert len(unsplit) == 1


def _suppress(card: dict, source_id: str, field: str) -> list[dict]:
    assertions = copy.deepcopy(card["assertions"])
    hit = 0
    for a in assertions:
        if a["source_id"] == source_id and a["field"] == field:
            a["status"] = "suppressed"
            a["suppression_ref"] = "overlay:example-takedown"
            hit += 1
    assert hit, f"no {source_id} assertion for {field}"
    return assertions


def test_removing_one_source_recomputes_value_and_state(gen) -> None:
    """AC-03: verified -> single-source when kaikki is withdrawn; conflict -> single-source when the
    disagreeing source is withdrawn; suppressed when every source for the field is withdrawn."""
    bronia = _card("bronia-armour")
    before = bronia["fields"]["stress"]
    assert before["state"] == "verified" and before["values"][0]["value_norm"] == "броня́"

    after = gen.resolve(_suppress(bronia, "kaikki", "stress"), "stress", bronia["card_id"])
    assert after["state"] == "single-source"
    assert after["values"][0]["value_norm"] == "броня́"  # surviving value unchanged, corroboration lost
    assert after["values"][0]["independence_groups"] == ["G-ULIF"]

    after_ulif = gen.resolve(_suppress(bronia, "ulif", "stress"), "stress", bronia["card_id"])
    assert after_ulif["state"] == "single-source" and after_ulif["values"][0]["independence_groups"] == ["G-WIKI"]

    vriady = _card("vriady-hody-conflict")
    assert vriady["fields"]["stress"]["state"] == "conflict"
    resolved = gen.resolve(_suppress(vriady, "ukrainian_word_stress", "stress"), "stress", vriady["card_id"])
    assert resolved["state"] == "single-source" and resolved["values"][0]["value_norm"] == "вряди́-годи́"

    ulif_stress = next(
        a["assertion_id"] for a in vriady["assertions"] if a["field"] == "stress" and a["source_id"] == "ulif"
    )
    by_overlay = gen.resolve(
        vriady["assertions"],
        "stress",
        vriady["card_id"],
        overlay={"kind": "resolve", "assertion_id": ulif_stress, "overlay_id": "ovl-example-1"},
    )
    assert by_overlay["state"] == "single-source" and by_overlay["resolution_ref"] == "ovl-example-1"
    assert by_overlay["selected"] == ulif_stress and len(by_overlay["values"]) == 2  # the losing value is retained

    everything = _suppress(vriady, "ulif", "stress")
    for a in everything:
        if a["field"] == "stress":
            a["status"] = "suppressed"
    assert gen.resolve(everything, "stress", vriady["card_id"])["state"] == "suppressed"


def test_unsplit_source_row_does_not_vote(gen) -> None:
    """VESUM's one-lemma 'броня́; бро́ня' comment is retained but, mapped at low confidence, never turns the split card into a variant/conflict."""
    bronia = _card("bronia-armour")
    vesum = [a for a in bronia["assertions"] if a["source_id"] == "vesum" and a["field"] == "stress"]
    assert vesum and vesum[0]["mapping"]["confidence"] == "low" and vesum[0]["status"] == "active"
    assert all(vesum[0]["assertion_id"] not in v["assertion_ids"] for v in bronia["fields"]["stress"]["values"])
