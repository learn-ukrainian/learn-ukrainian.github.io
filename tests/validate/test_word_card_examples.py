"""Word-card v1 schema (#8978, round 2): the worked examples validate, their ids are reproducible,
removing one source recomputes a field's surviving value and quality state (AC-03), and the
resolver behaves per the contract in the cases the design review reproduced (declared doublet
alone, doublet plus one member, worst extraction confidence, rejected-only assertion).

Spec: docs/atlas/word-cards/schema.md (§8 field resolution, §7.2 links, §12 suppression), worked-examples.md.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = REPO_ROOT / "schemas"
SCHEMA = SCHEMAS / "word-card-v1.schema.json"
EXAMPLES = REPO_ROOT / "docs" / "atlas" / "word-cards" / "examples"
GENERATOR = EXAMPLES / "build_examples.py"
COMPANIONS = {
    "identity-registry": "word-card-identity-registry-v1.schema.json",
    "overlay": "word-card-overlay-v1.schema.json",
    "suppression-selectors": "word-card-suppression-v1.schema.json",
    "derivations": "word-card-derivation-v1.schema.json",
}
SUBJECT = "wc_test00000000"


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
    assert len(files) >= 11, "expected the committed worked-example cards"
    return files


def _card(name: str) -> dict:
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def _errors(validator: Draft202012Validator, instance: dict) -> list[str]:
    return [f"{list(e.path)}: {e.message}" for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))]


# ---------------------------------------------------------------- schema validity and reproducibility


@pytest.mark.parametrize("path", _example_files(), ids=lambda p: p.stem)
def test_example_validates_against_schema(path: Path, validator: Draft202012Validator) -> None:
    assert not _errors(validator, json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("name", sorted(COMPANIONS))
def test_companion_instances_validate(name: str) -> None:
    schema = json.loads((SCHEMAS / COMPANIONS[name]).read_text(encoding="utf-8"))
    instance = json.loads((EXAMPLES / "companion" / f"{name}.json").read_text(encoding="utf-8"))
    assert not _errors(Draft202012Validator(schema), instance)


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
        assert card["card_id"] in {e["id"] for e in link["endpoints"]}


def test_generator_reproduces_committed_examples(gen) -> None:
    """The build is deterministic: regenerating yields the committed files byte for byte."""
    cards, companions = gen.build_all()
    assert len(cards) == len(_example_files())
    for name, card in cards.items():
        assert card == _card(name), name
    for name, obj in companions.items():
        assert obj == json.loads((EXAMPLES / "companion" / f"{name}.json").read_text(encoding="utf-8")), name


def test_source_record_keys_are_content_derived_not_row_ids() -> None:
    """Every ULIF/VESUM entry assertion carries a durable source_record_key that is not the local row id (§12.1)."""
    seen = 0
    for path in _example_files():
        for a in _card(path.stem)["assertions"]:
            if a.get("status") == "suppressed":
                continue
            if a["locator"].startswith(("ulif:entry:", "vesum:entry:")):
                seen += 1
                assert ":entry:" not in a["source_record_key"], a["locator"]
                assert a["source_record_key"].startswith(a["source_id"] + ":record:")
    assert seen > 20


# ---------------------------------------------------------------- states in the examples


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
    # a single unit on the source side (Караванський) is not aligned to a sense by itself (§6)
    assert any(m["source_id"] == "synonyms_karavansky" for m in unsplit[0]["sense_map"])


def test_extraction_confidence_min_is_the_worst_confidence() -> None:
    """Astra case 3: the idiom mixes high/medium/low extraction confidence; the card summary must be `low`."""
    idiom = _card("idiom-buduvaty-povitriani-zamky")
    assert {a["extraction_confidence"] for a in idiom["assertions"]} == {"high", "medium", "low"}
    assert idiom["quality"]["extraction_confidence_min"] == "low"
    assert _card("vriady-hody-conflict")["quality"]["extraction_confidence_min"] == "high"


# ---------------------------------------------------------------- resolver contract (Astra cases 1, 2, 4)


def _doublet(gen, **kw):
    return gen.A(
        "card",
        SUBJECT,
        "stress",
        "xv2 броня́; бро́ня",
        value_norm="броня́|бро́ня",
        source="vesum",
        snapshot=gen.VESUM_SNAP,
        locator="vesum:entry:30497 source_comment",
        xconf="medium",
        **kw,
    )


def _member(gen, value, source="ulif", **kw):
    snap = gen.ULIF_SNAP if source == "ulif" else gen.ATLAS0_SNAP
    return gen.A("card", SUBJECT, "stress", value, source=source, snapshot=snap, locator=f"{source}:x:{value}", **kw)


def test_declared_doublet_alone_is_variant(gen) -> None:
    res = gen.resolve([_doublet(gen)], "stress", SUBJECT)
    assert res["state"] == "variant"
    assert res["values"][0]["declared_set"] is True and res["values"][0]["value_norm"] == "броня́|бро́ня"
    assert res["comparison"] == "scalar"


def test_declared_doublet_plus_one_member_is_variant(gen) -> None:
    res = gen.resolve([_doublet(gen), _member(gen, "броня́")], "stress", SUBJECT)
    assert res["state"] == "variant"
    assert {v["value_norm"] for v in res["values"]} == {"броня́", "броня́|бро́ня"}
    assert len(res["selected"]) == 2  # both assertions are shown as correct


def test_declared_doublet_plus_both_members_is_variant(gen) -> None:
    res = gen.resolve([_doublet(gen), _member(gen, "броня́"), _member(gen, "бро́ня", source="kaikki")], "stress", SUBJECT)
    assert res["state"] == "variant"


def test_declared_doublet_not_containing_the_observed_value_is_conflict(gen) -> None:
    res = gen.resolve([_doublet(gen), _member(gen, "бро́ня́")], "stress", SUBJECT)
    assert res["state"] == "conflict" and res["selected"] is None


def test_rejected_only_assertion_shows_nothing(gen) -> None:
    """Astra case 4: a reviewed-and-rejected assertion never becomes the shown single-source value."""
    rejected = _member(gen, "броня́", review={"status": "rejected", "lane": "gemini-agy", "record": "example"})
    res = gen.resolve([rejected], "stress", SUBJECT)
    assert res["state"] == "unverified" and res["selected"] is None and res["values"] == []
    assert res["non_voting"] == [{"assertion_id": rejected["assertion_id"], "reason": "review rejected"}]
    assert res["mapping_evidenced"] is False


def test_rejected_assertion_does_not_corroborate(gen) -> None:
    rejected = _member(
        gen, "броня́", source="kaikki", review={"status": "rejected", "lane": "gemini-agy", "record": "x"}
    )
    res = gen.resolve([_member(gen, "броня́"), rejected], "stress", SUBJECT)
    assert res["state"] == "single-source" and res["independence_groups_agreeing"] == 1
    assert rejected["assertion_id"] not in res["values"][0]["assertion_ids"]


def test_text_fields_are_parallel_propositions_never_conflict(gen) -> None:
    """Two different definitions from two sources are two propositions, not a contradiction (§8.1)."""
    sense_id = "ws_test00000000"
    a = gen.A(
        "sense",
        sense_id,
        "definition_uk",
        "Укріплене житло феодала",
        source="vts",
        snapshot=gen.ATLAS0_SNAP,
        locator="atlas0:x/1",
    )
    b = gen.A(
        "sense",
        sense_id,
        "definition_uk",
        "Великий поміщицький будинок; палац.",
        source="ulif",
        snapshot=gen.ULIF_SNAP,
        locator="ulif:x/2",
    )
    res = gen.resolve([a, b], "definition_uk", sense_id)
    assert res["comparison"] == "text" and res["state"] == "single-source"
    assert len(res["values"]) == 2 and res["selected"] == b["assertion_id"]  # tier 1 shown first, ВТС retained


def test_keyed_paradigm_conflicts_only_inside_a_slot(gen) -> None:
    rod_u = gen.A(
        "card",
        SUBJECT,
        "paradigm",
        ["родовий", "за́мку"],
        value_norm="rod.sg=замку",
        source="ulif",
        snapshot=gen.ULIF_SNAP,
        locator="ulif:x rows[1]",
    )
    rod_v = gen.A(
        "card",
        SUBJECT,
        "paradigm",
        {"v_rod_sg": "замку"},
        value_norm="rod.sg=замку",
        source="vesum",
        snapshot=gen.VESUM_SNAP,
        locator="vesum:x forms",
    )
    dav_v = gen.A(
        "card",
        SUBJECT,
        "paradigm",
        {"v_dav_sg": "замкові"},
        value_norm="dav.sg=замкові",
        source="vesum",
        snapshot=gen.VESUM_SNAP,
        locator="vesum:x forms dav",
    )
    res = gen.resolve([rod_u, rod_v, dav_v], "paradigm", SUBJECT)
    assert (
        res["comparison"] == "keyed" and res["state"] == "single-source"
    )  # a slot given by one source is not a conflict
    rod_x = gen.A(
        "card",
        SUBJECT,
        "paradigm",
        ["родовий", "замка́"],
        value_norm="rod.sg=замка",
        source="ulif",
        snapshot=gen.ULIF_SNAP,
        locator="ulif:y rows[1]",
    )
    assert gen.resolve([rod_u, rod_v, rod_x], "paradigm", SUBJECT)["state"] == "conflict"


# ---------------------------------------------------------------- ambiguous evidence and eligibility (Astra gap 4)


def test_ambiguous_spelling_level_evidence_never_satisfies_eligibility() -> None:
    for name, mode in (("zamok-castle", "stress"), ("zamok-lock", "stress"), ("kliuch-1", "meaning")):
        card = _card(name)
        cefr = card["fields"]["cefr"]
        assert cefr["state"] == "single-source" and cefr["mapping_evidenced"] is False
        assert cefr["independence_groups_evidenced"] == 0
        puls = next(a for a in card["assertions"] if a["source_id"] == "puls")
        assert puls["mapping"] == {**puls["mapping"], "basis": "spelling", "ambiguous": True}
        entry = next(e for e in card["quality"]["practice_eligibility"] if e["mode"] == mode)
        assert entry["eligible"] is False and any("mapping_evidenced=false" in r for r in entry["reasons"])
    kliuch = _card("kliuch-1")
    meaning = next(e for e in kliuch["quality"]["practice_eligibility"] if e["mode"] == "meaning")
    assert kliuch["identity"]["confidence"] == "medium" and any("identity medium" in r for r in meaning["reasons"])


def test_unambiguous_corroboration_is_counted_separately(gen) -> None:
    castle = _card("zamok-castle")
    assert castle["fields"]["stress"]["mapping_evidenced"] is True
    assert castle["fields"]["stress"]["independence_groups_evidenced"] == 3
    kliuch = _card(
        "kliuch-1"
    )  # kaikki stress is ambiguous across the two ключ cards: it displays, it does not evidence
    assert kliuch["fields"]["stress"]["independence_groups_agreeing"] == 2
    assert kliuch["fields"]["stress"]["independence_groups_evidenced"] == 1


# ---------------------------------------------------------------- links (Astra gap 6)


def test_links_are_canonical_records_with_evidence() -> None:
    imperf, perf = _card("vybihaty-imperf"), _card("vybihty-perf")
    assert imperf["links"] == perf["links"], "one aspect_pair record, embedded identically on both cards"
    (rec,) = imperf["links"]
    assert [e["role"] for e in rec["endpoints"]] == ["imperfective", "perfective"]
    castle, lock = _card("zamok-castle"), _card("zamok-lock")
    shared = [l for l in castle["links"] if {e["id"] for e in l["endpoints"]} == {castle["card_id"], lock["card_id"]}]
    assert shared and shared[0] in lock["links"]
    for path in _example_files():
        for l in _card(path.stem)["links"]:
            assert l["state"] == "active" and l["assertion_ids"], f"{path.stem}: link without evidence"
            if l["basis"] == "derived":
                assert l["derived_by"].startswith("rules:")


def test_link_without_evidence_is_suppressed(gen) -> None:
    rec = gen.link("homograph_of", [{"id": gen.CASTLE}, {"id": gen.LOCK}], [])
    assert rec["state"] == "suppressed"
    assert (
        rec["link_id"] == gen.link("homograph_of", [{"id": gen.LOCK}, {"id": gen.CASTLE}], [])["link_id"]
    )  # symmetric


# ---------------------------------------------------------------- split vs redirect (Astra gap 2)


def test_split_card_is_one_to_many_and_schema_enforces_the_invariants(validator: Draft202012Validator) -> None:
    legacy = _card("zamok-legacy-split")
    assert legacy["state"] == "split" and legacy["merged_into"] is None
    assert legacy["split_into"] == [_card("zamok-castle")["card_id"], _card("zamok-lock")["card_id"]]
    assert not _errors(validator, legacy)
    bad = copy.deepcopy(legacy)
    bad["split_into"] = bad["split_into"][:1]
    assert _errors(validator, bad), "a split needs at least two successors"
    bad = copy.deepcopy(legacy)
    bad["state"], bad["split_into"], bad["merged_into"] = "redirected", None, None
    assert _errors(validator, bad), "redirected without merged_into must be rejected"
    bad = copy.deepcopy(legacy)
    bad["state"], bad["split_into"], bad["merged_into"] = "redirected", None, bad["split_into"][0]
    assert not _errors(validator, bad)
    bad = copy.deepcopy(legacy)
    bad["state"], bad["split_into"], bad["merged_into"] = "active", None, _card("zamok-castle")["card_id"]
    assert _errors(validator, bad), "an active card cannot carry merged_into"


# ---------------------------------------------------------------- suppression (AC-03, Astra gap 3)


def _suppress(card: dict, source_id: str, field: str) -> list[dict]:
    assertions = copy.deepcopy(card["assertions"])
    hit = 0
    for a in assertions:
        if a["source_id"] == source_id and a["field"] == field:
            a["status"] = "suppressed"
            a["suppression_ref"] = "sup-example-takedown"
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
        overlay={"kind": "resolve", "assertion_id": ulif_stress, "overlay_id": "ovl-2026-09-28-0002"},
    )
    assert by_overlay["state"] == "single-source" and by_overlay["resolution_ref"] == "ovl-2026-09-28-0002"
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
    stress = bronia["fields"]["stress"]
    assert all(vesum[0]["assertion_id"] not in v["assertion_ids"] for v in stress["values"])
    assert {"assertion_id": vesum[0]["assertion_id"], "reason": "mapping low"} in stress["non_voting"]


def test_public_projection_carries_suppressed_assertions_as_tombstones(gen, validator: Draft202012Validator) -> None:
    vriady = _card("vriady-hody-conflict")
    vriady["assertions"] = _suppress(vriady, "ukrainian_word_stress", "stress")
    public = gen.public_projection(vriady)
    stones = [a for a in public["assertions"] if a["status"] == "suppressed"]
    assert stones == [
        {"assertion_id": stones[0]["assertion_id"], "status": "suppressed", "suppression_ref": "sup-example-takedown"}
    ]
    assert "вряди́-го́ди" not in json.dumps([a for a in public["assertions"]], ensure_ascii=False).replace(
        "вряди́-годи́", ""
    )
    assert not _errors(validator, public)
