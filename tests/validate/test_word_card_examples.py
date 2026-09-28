"""Word-card v1 schema (#8978, round 3): the worked examples validate, their ids are reproducible,
removing one source recomputes a field's surviving value and quality state (AC-03), the resolver
behaves per the contract in the cases the design review reproduced (declared doublet alone, doublet
plus one member, worst extraction confidence, rejected-only assertion, disjoint declarations, reviewed
overlay variant), evidence is counted per proposition, assembly refuses unallocated ids, the build
manifest hashes every input, source records have a persistent identity with an ambiguous hold, the
card version covers admission state, and invalidation walks source -> generated assertion -> consumer.

Spec: docs/atlas/word-cards/schema.md (§8 field resolution, §7.2 links, §11 derivations, §12 suppression,
§13 build contract), worked-examples.md.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
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


def test_source_record_identity_is_persistent_not_a_row_id_or_a_content_key() -> None:
    """Every ULIF/VESUM entry assertion carries a persistent `sr_` source_record_id allocated in the identity
    registry, plus the strongest alias as source_record_key; neither is the local row id (§12.1)."""
    registry = json.loads((EXAMPLES / "companion" / "identity-registry.json").read_text(encoding="utf-8"))
    records = {r["source_record_id"]: r for r in registry["source_records"]}
    seen = 0
    for path in _example_files():
        for a in _card(path.stem)["assertions"]:
            if a.get("status") == "suppressed":
                continue
            if a["locator"].startswith(("ulif:entry:", "vesum:entry:")):
                seen += 1
                assert re.fullmatch(r"sr_[0-9a-hjkmnp-tv-z]{12}", a["source_record_id"]), a["locator"]
                rec = records[a["source_record_id"]]
                assert rec["source_id"] == a["source_id"]
                assert a["source_record_key"] in {al["key"] for al in rec["aliases"]}
                assert ":entry:" not in a["source_record_key"], a["locator"]
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


def test_public_projection_recomputes_and_carries_suppressed_assertions_as_tombstones(
    gen, validator: Draft202012Validator
) -> None:
    """The withdrawn value must be gone from the COMPLETE public output (fields, values, senses, links,
    assertions), not only from the assertion list: the projection recomputes before it tombstones (§12.3)."""
    vriady = _card("vriady-hody-conflict")
    assert vriady["fields"]["stress"]["state"] == "conflict"
    before_version = vriady["build"]["card_version"]
    vriady["assertions"] = _suppress(vriady, "ukrainian_word_stress", "stress")
    public = gen.public_projection(vriady)
    stones = [a for a in public["assertions"] if a["status"] == "suppressed"]
    assert stones == [
        {"assertion_id": stones[0]["assertion_id"], "status": "suppressed", "suppression_ref": "sup-example-takedown"}
    ]
    whole = json.dumps(public, ensure_ascii=False)
    assert "вряди́-го́ди" not in whole.replace("вряди́-годи́", ""), "withdrawn value leaked into the public output"
    assert stones[0]["assertion_id"] not in json.dumps(public["fields"], ensure_ascii=False)
    stress = public["fields"]["stress"]
    assert stress["state"] == "single-source" and [v["value_norm"] for v in stress["values"]] == ["вряди́-годи́"]
    assert public["build"]["card_version"] != before_version, "a withdrawal is a consumer-visible change"
    assert not _errors(validator, public)


def test_public_projection_of_an_untouched_card_is_the_card(gen) -> None:
    castle = _card("zamok-castle")
    public = gen.public_projection(castle)
    assert public == castle, "recomputation is deterministic: no suppression -> identical projection and version"


# ---------------------------------------------------------------- registry vs build (Astra r2 gap 1)


def test_assembly_refuses_ids_the_frozen_registry_does_not_allocate(gen) -> None:
    identity = {"confidence": "high", "method": "unique_match", "source_keys": []}
    key = {"spelling": "x", "pos": "noun"}
    with pytest.raises(gen.MissingAllocation):
        gen.card("wc_zzzzzzzzzzzz", "lexeme", key, identity, [], [], [], [])
    with pytest.raises(gen.MissingAllocation):  # an allocated card with an unallocated sense
        gen.card(gen.VRIADY, "lexeme", key, identity, [gen.sense("ws_zzzzzzzzzzzz", 1, [])], [], [], [])
    registry = json.loads((EXAMPLES / "companion" / "identity-registry.json").read_text(encoding="utf-8"))
    allocated = {e["card_id"]: {s["sense_id"] for s in e["senses"]} for e in registry["entries"]}
    for path in _example_files():
        card = _card(path.stem)
        assert card["card_id"] in allocated
        assert {s["sense_id"] for s in card["senses"]} <= allocated[card["card_id"]]


def test_build_manifest_hashes_every_input_and_covers_every_used_source(gen) -> None:
    """S, V, I and O entries carry a 64-hex content hash; I and O hashes recompute from the committed
    companion files; every assertion's source is read from an input that is in the manifest (§13)."""
    inputs = _card("zamok-castle")["build"]["inputs"]
    for group in ("S", "V", "I", "O"):
        assert inputs[group], group
        for name, entry in inputs[group].items():
            assert re.fullmatch(r"[0-9a-f]{64}", entry["content_sha256"]), f"{group}.{name}"
    for group, name, companion in (
        ("I", "identity_registry", "identity-registry"),
        ("O", "overlay", "overlay"),
        ("O", "suppressions", "suppression-selectors"),
    ):
        committed = json.loads((EXAMPLES / "companion" / f"{companion}.json").read_text(encoding="utf-8"))
        assert inputs[group][name]["content_sha256"] == gen.sha256_of(committed), f"{group}.{name}"
    assert inputs["R"]["register"]["content_sha256"] == gen.REGISTER_SHA256
    used = set()
    for path in _example_files():
        for a in _card(path.stem)["assertions"]:
            used.add(a["source_id"])
            group, name = gen.SOURCE_INPUT[a["source_id"]]
            assert name in inputs[group], f"{a['source_id']} -> {group}.{name} missing from the manifest"
    assert {"frazeolohichnyi", "wiktionary", "ulif", "vesum", "puls"} <= used


# ---------------------------------------------------------------- source-record identity (Astra r2 gap 3)


def test_legacy_record_key_collides_and_correspondence_holds_ambiguous(gen) -> None:
    """Read-only on 2026-09-28: ULIF rows 3 and 98008 (ключ homonyms 1 and 2) have identical query, headword
    and grammatical label, so the r2 key `query#headword#label` is shared. Correspondence through that alias
    alone is an explicit ambiguous hold. `register_position` (continuity across harvests untested, Q-I6) never
    decides alone into a new snapshot: it is `held` until a content alias corroborates the row, and it never
    wins over contradictory content evidence; every historical alias of a kind keeps finding the row."""
    rec3, rec98008 = gen.SOURCE_RECORD_BY_HEAD["ulif:entry:3"], gen.SOURCE_RECORD_BY_HEAD["ulif:entry:98008"]
    al3 = {a["kind"]: a["key"] for a in rec3["aliases"]}
    al98008 = {a["kind"]: a["key"] for a in rec98008["aliases"]}
    legacy = al3["query_headword_label"]
    assert legacy == al98008["query_headword_label"]
    assert rec3["source_record_id"] != rec98008["source_record_id"]
    new_snapshot = [  # a reharvest that renumbered the rows and lost the register position
        {"locator": "ulif:entry:900001", "aliases": {"query_headword_label": legacy}},
        {"locator": "ulif:entry:900002", "aliases": {"query_headword_label": legacy}},
    ]
    held = gen.correspond(rec3, new_snapshot)
    assert held["status"] == "ambiguous" and held["candidates"] == ["ulif:entry:900001", "ulif:entry:900002"]
    selector = {"kind": "source_record", "source_id": "ulif", "source_record_id": rec3["source_record_id"]}
    assert gen.selector_targets(selector, held) == ["ulif:entry:900001", "ulif:entry:900002"]  # suppress all
    with_register = [
        dict(r, aliases={**r["aliases"], "register_position": rp})
        for r, rp in zip(new_snapshot, ("ulif:register:3662:14", "ulif:register:3662:15"), strict=True)
    ]
    # position alone singles out 900001, but its continuity into a new harvest is unproven -> held, both suppressed
    position_only = gen.correspond(rec3, with_register)
    assert position_only["status"] == "held" and position_only["matched_by"] == "register_position"
    assert gen.selector_targets(selector, position_only) == ["ulif:entry:900001", "ulif:entry:900002"]
    # the same rows re-read in the snapshot the position was observed in: direct observation, unique
    assert gen.correspond(rec3, with_register, snapshot_id=gen.ULIF_SNAP) == {
        "status": "unique",
        "matched_by": "register_position",
        "locator": "ulif:entry:900001",
    }
    # corroborated by the content digest: unique
    with_content = [
        dict(r, aliases={**r["aliases"], "content": c})
        for r, c in zip(with_register, (al3["content"], al98008["content"]), strict=True)
    ]
    unique = gen.correspond(rec3, with_content)
    assert unique == {"status": "unique", "matched_by": "register_position", "locator": "ulif:entry:900001"}
    assert gen.selector_targets(selector, unique) == ["ulif:entry:900001"]
    # Astra r3 regression (a): a reharvest keeps both records' content but SWAPS their register positions.
    # A unique position match must not win over contradictory content evidence: hold, never row 98008 alone.
    swapped = [
        dict(r, aliases={**r["aliases"], "content": c})
        for r, c in zip(with_register, (al98008["content"], al3["content"]), strict=True)
    ]
    conflict = gen.correspond(rec3, swapped)
    assert conflict["status"] == "held" and "conflicting identity evidence" in conflict["hold"]
    assert gen.selector_targets(selector, conflict) == ["ulif:entry:900001", "ulif:entry:900002"]
    assert "ulif:entry:900002" in gen.selector_targets(selector, conflict)  # row 3's content is still covered
    # Astra r3 regression (b): a corrected header APPENDS an alias; every historical alias of the kind is kept,
    # so a candidate still carrying the old key (or the old content digest) corresponds instead of `missing`.
    corrected = copy.deepcopy(rec3)
    corrected["aliases"] += [
        {
            "kind": "query_headword_label",
            "key": "ulif:record:ключ#ключ¹#іменник чоловічого роду",
            "snapshot_id": "ulif@next",
        },
        {"kind": "content", "key": "ulif:content:" + "0" * 64, "snapshot_id": "ulif@next"},
    ]
    assert gen.correspond(
        corrected, [{"locator": "ulif:entry:900001", "aliases": {"query_headword_label": legacy}}]
    ) == {
        "status": "unique",
        "matched_by": "query_headword_label",
        "locator": "ulif:entry:900001",
    }
    assert gen.correspond(corrected, [{"locator": "ulif:entry:900001", "aliases": {"content": al3["content"]}}]) == {
        "status": "unique",
        "matched_by": "content",
        "locator": "ulif:entry:900001",
    }
    assert gen.correspond(corrected, with_content)["locator"] == "ulif:entry:900001"  # the old aliases still agree
    assert (
        gen.correspond(rec3, [])["status"] == "missing" and gen.selector_targets(selector, {"status": "missing"}) == []
    )
    # the registry schema admits every status the reference implementation can return
    schema = json.loads((SCHEMAS / COMPANIONS["identity-registry"]).read_text(encoding="utf-8"))
    statuses = schema["$defs"]["source_record"]["properties"]["correspondence"]["items"]["properties"]["status"]["enum"]
    assert {"unique", "ambiguous", "held", "missing"} == set(statuses)
    v = Draft202012Validator(schema["$defs"]["source_record"]["properties"]["correspondence"]["items"])
    for result in (held, position_only, conflict, unique):
        assert not list(v.iter_errors({"snapshot_id": "ulif@next", **result})), result


def test_unproven_position_never_narrows_an_ambiguous_hold(gen) -> None:
    """Astra r4 reproduction: record 3 carries two historical register positions (the row was renumbered
    between harvests, so both keys are kept). In a new harvest the weak header key hits A, B and C; the two
    positions hit A and B. At 848fa00b the result was `ambiguous [A, B]` and C, possibly the moved original
    row, stayed unsuppressed. Position continuity into a new harvest is unproven (Q-I6), so position evidence
    may not narrow the weak-key candidate set at all: the hold covers A, B and C (fail wide, never narrow)."""
    rec3 = copy.deepcopy(gen.SOURCE_RECORD_BY_HEAD["ulif:entry:3"])
    al3 = {a["kind"]: a["key"] for a in rec3["aliases"]}
    rec3["aliases"].append({"kind": "register_position", "key": "ulif:register:3660:2", "snapshot_id": "ulif@older"})
    a, b, c = "ulif:entry:900001", "ulif:entry:900002", "ulif:entry:900003"
    weak = al3["query_headword_label"]
    rows = [
        {"locator": a, "aliases": {"register_position": al3["register_position"], "query_headword_label": weak}},
        {"locator": b, "aliases": {"register_position": "ulif:register:3660:2", "query_headword_label": weak}},
        {"locator": c, "aliases": {"register_position": "ulif:register:9999:0", "query_headword_label": weak}},
    ]
    selector = {"kind": "source_record", "source_id": "ulif", "source_record_id": rec3["source_record_id"]}
    result = gen.correspond(rec3, rows)
    assert result["status"] in ("ambiguous", "held")
    assert gen.selector_targets(selector, result) == [a, b, c], result
    # the same rows re-read in the snapshot the first position was observed in: that position is direct
    # observation and may narrow; the older position (a different snapshot) still may not, and because it
    # lands on a row the proven evidence excludes the correspondence is a conflict hold, never a guess
    observed = gen.correspond(rec3, rows, snapshot_id=gen.ULIF_SNAP)
    assert observed["status"] == "held" and a in gen.selector_targets(selector, observed)
    # with the content digest on A the proven evidence singles out A; the stale position on B is a conflict
    with_content = copy.deepcopy(rows)
    with_content[0]["aliases"]["content"] = al3["content"]
    corroborated = gen.correspond(rec3, with_content)
    assert corroborated["status"] == "held" and set(gen.selector_targets(selector, corroborated)) >= {a, b}
    # drop the stale position from the snapshot: content + position agree on A, unique
    del with_content[1]["aliases"]["register_position"]
    assert gen.correspond(rec3, with_content) == {
        "status": "unique",
        "matched_by": "register_position",
        "locator": a,
    }


def _small_world(
    position: str, content: str, n: int, stale: bool, observed: bool
) -> tuple[dict, list[dict], str | None]:
    """One re-harvest scenario. The record was minted in `ulif@s1` with a register position, a content digest and
    the weak header key; `stale` adds a second, older register position (`ulif@s0`, the row was renumbered).
    `content == "changed"` appends a corrected digest (`ulif@s2`) that row 0 now carries (the old one is gone).
    Rows r0..r{n-1} all carry the weak key; r0 is the original record. `position`: present (r0 carries the
    position), absent (no row does), moved (r1 does). The stale position lands on the last row. `observed`
    re-reads the rows in `ulif@s1`, which proves the s1 position (never the s0 one)."""
    record = {
        "source_record_id": "sr_smallworld000",
        "source_id": "ulif",
        "aliases": [
            {"kind": "register_position", "key": "pos:s1", "snapshot_id": "ulif@s1"},
            {"kind": "content", "key": "content:s1", "snapshot_id": "ulif@s1"},
            {"kind": "query_headword_label", "key": "weak", "snapshot_id": "ulif@s1"},
        ],
    }
    if stale:
        record["aliases"].append({"kind": "register_position", "key": "pos:s0", "snapshot_id": "ulif@s0"})
    if content == "changed":
        record["aliases"].append({"kind": "content", "key": "content:s2", "snapshot_id": "ulif@s2"})
    rows = [{"locator": f"r{i}", "aliases": {"query_headword_label": "weak"}} for i in range(n)]
    for i, row in enumerate(rows):
        row["aliases"]["register_position"] = f"pos:unrelated{i}"
        if content != "absent":
            row["aliases"]["content"] = f"content:unrelated{i}"
    if position == "present":
        rows[0]["aliases"]["register_position"] = "pos:s1"
    elif position == "moved":
        rows[1]["aliases"]["register_position"] = "pos:s1"
    if stale:
        rows[-1]["aliases"]["register_position"] = "pos:s0"
    if content == "present":
        rows[0]["aliases"]["content"] = "content:s1"
    elif content == "changed":
        rows[0]["aliases"]["content"] = "content:s2"
    return record, rows, ("ulif@s1" if observed else None)


def _unexcludable(record: dict, rows: list[dict], snapshot_id: str | None) -> set[str]:
    """Oracle, independent of `correspond()`: the rows the PROVEN evidence cannot exclude. Content-side keys
    are intrinsic to a row, so they are proven in any snapshot; a register position is proven only for the
    snapshot it was observed in. No proven hit, or proven hits that contradict each other, excludes nothing."""
    keys = {}
    for a in record["aliases"]:
        keys.setdefault(a["kind"], {}).setdefault(a["key"], set()).add(a["snapshot_id"])
    proven: list[set[str]] = []
    for kind, by_key in keys.items():
        found = {
            r["locator"]
            for r in rows
            if r["aliases"].get(kind) in by_key
            and (kind != "register_position" or snapshot_id in by_key[r["aliases"][kind]])
        }
        if found:
            proven.append(found)
    everything = {r["locator"] for r in rows}
    if not proven:
        return everything
    return set.intersection(*proven) or everything


def test_small_world_suppression_targets_cover_every_unexcluded_candidate(gen) -> None:
    """Exhaustive small world (Astra r4, closed as a class): for every (position present / absent / moved) x
    (content present / absent / changed) x (1..3 weak-key candidates), each with and without a stale older
    register position and each as a new harvest and as a re-read of the position's own snapshot, the
    `source_record` suppression covers every candidate the proven evidence cannot exclude. Unproven position
    evidence never narrows a candidate set, neither to one row nor to an ambiguous subset."""
    selector = {"kind": "source_record", "source_id": "ulif", "source_record_id": "sr_smallworld000"}
    evaluated = 0
    for position in ("present", "absent", "moved"):
        for content in ("present", "absent", "changed"):
            for n in (1, 2, 3):
                for stale in (False, True):
                    if position == "moved" and n < 2:
                        continue  # nowhere to move to
                    if stale and (n < 2 or (position == "moved" and n < 3)):
                        continue  # a row carries one position; the stale key needs a row of its own
                    for observed in (False, True):
                        record, rows, snapshot_id = _small_world(position, content, n, stale, observed)
                        result = gen.correspond(record, rows, snapshot_id=snapshot_id)
                        targets = set(gen.selector_targets(selector, result))
                        expected = _unexcludable(record, rows, snapshot_id)
                        label = f"position={position} content={content} n={n} stale={stale} observed={observed}"
                        assert result["status"] != "missing", label  # the weak key always hits
                        assert targets >= expected, (
                            f"{label}: {result} leaves {sorted(expected - targets)} unsuppressed"
                        )
                        assert targets <= {r["locator"] for r in rows}, label
                        if result["status"] == "unique":
                            assert expected == {result["locator"]}, f"{label}: unique decision beyond the evidence"
                        evaluated += 1
    assert evaluated == 78


def test_content_selector_survives_a_normaliser_change(gen) -> None:
    vriady = _card("vriady-hody-conflict")
    uws = next(a for a in vriady["assertions"] if a["source_id"] == "ukrainian_word_stress")
    selector = json.loads((EXAMPLES / "companion" / "suppression-selectors.json").read_text(encoding="utf-8"))[
        "entries"
    ][1]["selector"]
    assert selector["normaliser_version"] == "norm-v1" and gen.content_selector_matches(selector, uws)
    # under a later normaliser the assertion's value_norm would change (accents dropped) ...
    renormalised = dict(uws, value_norm=gen.normalise(uws["value"], "norm-v2-hypothetical"))
    assert renormalised["value_norm"] != uws["value_norm"]
    # ... and the selector still matches, because it re-normalises the raw value with its pinned version
    assert gen.content_selector_matches(selector, renormalised)
    assert not gen.content_selector_matches(selector, next(a for a in vriady["assertions"] if a["source_id"] == "ulif"))


def test_suppression_schema_rejects_an_empty_fallback_and_an_unpinned_selector() -> None:
    schema = json.loads((SCHEMAS / COMPANIONS["suppression-selectors"]).read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    committed = json.loads((EXAMPLES / "companion" / "suppression-selectors.json").read_text(encoding="utf-8"))
    assert not _errors(v, committed)
    by_kind = {e["selector"]["kind"]: e for e in committed["entries"]}
    bad = copy.deepcopy(committed)
    bad["entries"] = [copy.deepcopy(by_kind["assertion_id"])]
    bad["entries"][0]["selector"]["fallback"] = {}
    assert _errors(v, bad), "fallback: {} must be rejected"
    bad["entries"][0]["selector"]["fallback"] = {"kind": "assertion_content", "source_id": "kaikki"}
    assert _errors(v, bad), "a partial fallback must be rejected"
    bad = copy.deepcopy(committed)
    bad["entries"] = [copy.deepcopy(by_kind["assertion_content"])]
    del bad["entries"][0]["selector"]["normaliser_version"]
    assert _errors(v, bad), "a content selector without normaliser_version must be rejected"
    bad = copy.deepcopy(committed)
    bad["entries"] = [copy.deepcopy(by_kind["source_record"])]
    bad["entries"][0]["selector"] = {"kind": "source_record", "source_id": "ulif", "source_record_key": "ulif:record:x"}
    assert _errors(v, bad), "a source_record selector keyed by a derived key must be rejected"


# ---------------------------------------------------------------- per-proposition evidence (Astra r2 gap 4)


def test_keyed_evidence_is_per_proposition_not_pooled_across_slots(gen) -> None:
    """One evidenced slot plus one ambiguous-only slot: the evidenced slot says so, the ambiguous slot says so,
    and the field-level summary is false (never true because another slot was evidenced)."""
    rod = gen.A(
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
    dav = gen.A(
        "card",
        SUBJECT,
        "paradigm",
        {"v_dav_sg": "замкові"},
        value_norm="dav.sg=замкові",
        source="kaikki",
        snapshot=gen.ATLAS0_SNAP,
        locator="atlas0:x forms",
        mapping={"confidence": "medium", "basis": "spelling", "ambiguous": True},
    )
    res = gen.resolve([rod, rod_v, dav], "paradigm", SUBJECT)
    assert res["propositions"]["rod.sg"] == {
        "state": "verified",
        "selected": rod["assertion_id"],
        "mapping_evidenced": True,
        "independence_groups_evidenced": 2,
    }
    assert res["propositions"]["dav.sg"]["mapping_evidenced"] is False
    assert res["propositions"]["dav.sg"]["independence_groups_evidenced"] == 0
    assert res["mapping_evidenced"] is False and res["independence_groups_evidenced"] == 0
    assert {v["value_norm"]: v["mapping_evidenced"] for v in res["values"]} == {
        "rod.sg=замку": True,
        "dav.sg=замкові": False,
    }


def test_every_value_entry_carries_its_own_evidence() -> None:
    castle, kliuch = _card("zamok-castle"), _card("kliuch-1")
    for card in (castle, kliuch):
        for f in list(card["fields"].values()) + [f for s in card["senses"] for f in s["fields"].values()]:
            for v in f["values"]:
                assert {"mapping_evidenced", "independence_groups_evidenced"} <= set(v)
    # text class: the shown gloss is its own proposition
    assert castle["fields"]["english_gloss"]["values"][0]["mapping_evidenced"] is True  # kaikki, basis sense
    assert kliuch["fields"]["english_gloss"]["mapping_evidenced"] is False  # kaikki, spelling-ambiguous
    # scalar class: ключ stress is one proposition stated by ULIF (evidenced) and kaikki (ambiguous)
    (stress,) = kliuch["fields"]["stress"]["values"]
    assert stress["mapping_evidenced"] is True and stress["independence_groups_evidenced"] == 1


# ---------------------------------------------------------------- resolver: declarations and overlay (Astra r2 gap 5)


def _declared(gen, value_norm, source, locator):
    snap = gen.VESUM_SNAP if source == "vesum" else gen.ULIF_SNAP
    return gen.A(
        "card",
        SUBJECT,
        "stress",
        value_norm.replace("|", "; "),
        value_norm=value_norm,
        source=source,
        snapshot=snap,
        locator=locator,
        xconf="medium",
    )


def test_disjoint_or_unequal_tier1_declarations_are_a_conflict(gen) -> None:
    a_b = _declared(gen, "а́|б", "vesum", "vesum:x comment")
    c_d = _declared(gen, "в|г", "ulif", "ulif:x headword")
    res = gen.resolve([a_b, c_d], "stress", SUBJECT)
    assert res["state"] == "conflict" and res["selected"] is None
    assert {v["value_norm"] for v in res["values"]} == {"а́|б", "в|г"}
    a_b_c = _declared(gen, "а́|б|в", "ulif", "ulif:y headword")
    assert gen.resolve([a_b, a_b_c], "stress", SUBJECT)["state"] == "conflict", "partial overlap is not agreement"
    assert gen.resolve([a_b, a_b_c, _member(gen, "а́")], "stress", SUBJECT)["state"] == "conflict"


def test_equal_tier1_declarations_corroborate_a_variant(gen) -> None:
    a_b = _declared(gen, "а́|б", "vesum", "vesum:x comment")
    same = _declared(gen, "а́|б", "ulif", "ulif:x headword")
    res = gen.resolve([a_b, same, _member(gen, "а́", source="kaikki")], "stress", SUBJECT)
    assert res["state"] == "variant" and res["independence_groups_agreeing"] == 3
    assert len(res["selected"]) == 3


def test_reviewed_overlay_variant_resolves_conflicting_scalars(gen) -> None:
    """§8.2 rule 4: two disagreeing single values (or disagreeing declarations) become `variant` only through a
    reviewed, cited language-lane overlay entry naming the members; an overlay that does not cover an observed
    value leaves the field in conflict. Rule 7 (Astra r3): the overlay-declared set is a shown proposition
    with no source assertion behind it, so the field-level flags are the conjunction / minimum over ALL shown
    propositions including it — false / 0 — while each member entry keeps its own evidence."""
    ulif = _member(gen, "вряди́-годи́")
    uws = _member(gen, "вряди́-го́ди", source="kaikki")
    assert gen.resolve([ulif, uws], "stress", SUBJECT)["state"] == "conflict"
    overlay = {"kind": "variant", "overlay_id": "ovl-2026-09-28-0009", "members": ["вряди́-годи́", "вряди́-го́ди"]}
    res = gen.resolve([ulif, uws], "stress", SUBJECT, overlay=overlay)
    assert res["state"] == "variant" and res["resolution_ref"] == "ovl-2026-09-28-0009"
    assert sorted(res["selected"]) == sorted([ulif["assertion_id"], uws["assertion_id"]])
    declared = [v for v in res["values"] if v.get("declared_set")]
    assert declared == [
        {
            "value_norm": "вряди́-го́ди|вряди́-годи́",
            "assertion_ids": [],
            "independence_groups": [],
            "mapping_evidenced": False,
            "independence_groups_evidenced": 0,
            "declared_set": True,
            "declared_by": "ovl-2026-09-28-0009",
        }
    ]
    # every shown proposition is aggregated: the two members are evidenced (1 group each), the declaration is not
    members = [v for v in res["values"] if not v.get("declared_set")]
    assert len(members) == 2 and all(
        v["mapping_evidenced"] and v["independence_groups_evidenced"] == 1 for v in members
    )
    shown = members + declared
    assert res["mapping_evidenced"] is False and not all(v["mapping_evidenced"] for v in shown)
    assert res["independence_groups_evidenced"] == min(v["independence_groups_evidenced"] for v in shown) == 0
    # by contrast, a tier-1 declaring source is an assertion stating the set: the whole field is evidenced
    by_source = gen.resolve([_doublet(gen), _member(gen, "броня́")], "stress", SUBJECT)
    assert by_source["state"] == "variant" and by_source["mapping_evidenced"] is True
    assert (
        by_source["independence_groups_evidenced"]
        == min(v["independence_groups_evidenced"] for v in by_source["values"])
        == 1
    )
    narrow = {"kind": "variant", "overlay_id": "ovl-2026-09-28-0010", "members": ["вряди́-годи́", "x"]}
    assert gen.resolve([ulif, uws], "stress", SUBJECT, overlay=narrow)["state"] == "conflict"
    # disagreeing tier-1 declarations are resolved the same way; the overlay declaration still keeps the field unevidenced
    a_b, c_d = _declared(gen, "а́|б", "vesum", "vesum:x comment"), _declared(gen, "в|г", "ulif", "ulif:x headword")
    wide = {"kind": "variant", "overlay_id": "ovl-2026-09-28-0011", "members": ["а́", "б", "в", "г"]}
    wide_res = gen.resolve([a_b, c_d], "stress", SUBJECT, overlay=wide)
    assert wide_res["state"] == "variant"
    assert wide_res["mapping_evidenced"] is False and wide_res["independence_groups_evidenced"] == 0


def test_overlay_schema_requires_members_for_variant() -> None:
    schema = json.loads((SCHEMAS / COMPANIONS["overlay"]).read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    entry = {
        "overlay_id": "ovl-2026-09-28-0009",
        "kind": "variant",
        "card_id": "wc_x2j5n8sd1vpc",
        "field": "stress",
        "author": "human",
        "lane": "language",
        "date": "2026-09-28",
        "evidence": "…",
        "members": ["a", "b"],
    }
    assert not _errors(v, {"schema_version": "1", "entries": [entry]})
    assert _errors(v, {"schema_version": "1", "entries": [{k: x for k, x in entry.items() if k != "members"}]})
    assert _errors(v, {"schema_version": "1", "entries": [dict(entry, members=["a"])]})
    assert _errors(v, {"schema_version": "1", "entries": [dict(entry, lane="design")]})


# ---------------------------------------------------------------- versions and derivations (Astra r2 gap 6)


def test_card_version_covers_identity_and_admission_state(gen) -> None:
    castle = _card("zamok-castle")
    base = gen.card_version(castle)
    assert base == castle["build"]["card_version"]
    changed = copy.deepcopy(castle)
    changed["identity"]["confidence"] = "unresolved"
    assert gen.card_version(changed) != base, "identity confidence is consumer-relevant"
    changed = copy.deepcopy(castle)
    changed["quality"]["practice_eligibility"][0]["eligible"] = True
    assert gen.card_version(changed) != base, "eligibility is admission state"
    changed = copy.deepcopy(castle)
    changed["quality"]["linguistic_review"] = {"status": "reviewed", "lane": "gemini-agy"}
    assert gen.card_version(changed) != base, "review state is admission state"
    changed = copy.deepcopy(castle)
    changed["build"]["build_id"] = "another-build"
    assert gen.card_version(changed) == base, "only the build block is outside the version"


def test_derivation_id_includes_rules_version_and_configuration(gen) -> None:
    inputs = {"assertion_ids": ["wa_" + "0" * 24], "card_ids": [], "card_versions": {}}
    base = gen.derivation_id("g", "1", "rules-v1-draft", "a" * 64, inputs, "exercise", "k")
    assert base != gen.derivation_id("g", "1", "rules-v2", "a" * 64, inputs, "exercise", "k")
    assert base != gen.derivation_id("g", "1", "rules-v1-draft", "b" * 64, inputs, "exercise", "k")
    assert base != gen.derivation_id("g", "1", "rules-v1-draft", "a" * 64, inputs, "exercise", "k2")
    derivations = json.loads((EXAMPLES / "companion" / "derivations.json").read_text(encoding="utf-8"))["entries"]
    for d in derivations:
        assert d["derived_id"] == gen.derivation_id(
            d["generator"],
            d["generator_version"],
            d["rules_version"],
            d["configuration"]["sha256"],
            d["inputs"],
            d["output"]["kind"],
            d["output"]["key"],
        )


def test_invalidation_walks_source_to_generated_assertion_to_consumer(gen) -> None:
    """GRAC frequency (source) -> estimator derivation -> generated cefr assertion -> page and exercise records.
    Suppressing the frequency assertion must reach every node, through the explicit producer link."""
    armour = _card("bronia-armour")
    derivations = json.loads((EXAMPLES / "companion" / "derivations.json").read_text(encoding="utf-8"))["entries"]
    by_id = {a["assertion_id"]: a for a in armour["assertions"]}
    freq = next(a for a in armour["assertions"] if a["field"] == "frequency")
    cefr = next(a for a in armour["assertions"] if a["field"] == "cefr")
    estimator = next(d for d in derivations if d["kind"] == "generated_assertion")
    assert cefr["producer"]["derived_id"] == estimator["derived_id"]  # assertion -> producing derivation
    assert estimator["output"] == {
        "kind": "assertion",
        "key": cefr["assertion_id"],
        "content_sha256": gen.sha256_of(cefr),
    }
    assert estimator["inputs"]["assertion_ids"] == [freq["assertion_id"]]  # derivation -> source assertion
    consumers = [d for d in derivations if cefr["assertion_id"] in d["inputs"]["assertion_ids"]]
    assert {d["kind"] for d in consumers} == {"atlas_page", "exercise"}
    suppressed, invalidated = gen.transitive_invalidation({freq["assertion_id"]}, derivations, "sup-test")
    assert suppressed == {freq["assertion_id"], cefr["assertion_id"]}
    assert set(invalidated) == {d["derived_id"] for d in derivations} and set(invalidated.values()) == {"sup-test"}
    # a suppression outside the chain reaches only its direct consumer (the page reads every active assertion)
    other = next(a["assertion_id"] for a in armour["assertions"] if a["field"] == "gender")
    page = next(d for d in derivations if d["kind"] == "atlas_page")
    assert gen.transitive_invalidation({other}, derivations, "sup-x") == ({other}, {page["derived_id"]: "sup-x"})
    assert all(i in by_id for d in derivations for i in d["inputs"]["assertion_ids"])


def test_companion_derivations_agree_with_eligibility_and_carry_real_digests() -> None:
    derivations = json.loads((EXAMPLES / "companion" / "derivations.json").read_text(encoding="utf-8"))["entries"]
    armour = _card("bronia-armour")
    for d in derivations:
        assert d["output"]["content_sha256"] != "0" * 64
        assert d["configuration"]["sha256"] != "0" * 64
    exercise = next(d for d in derivations if d["kind"] == "exercise")
    stress_mode = next(e for e in armour["quality"]["practice_eligibility"] if e["mode"] == "stress")
    assert stress_mode["eligible"] is False
    assert exercise["status"] == "draft" and exercise["unpublished_reason"]
    page = next(d for d in derivations if d["kind"] == "atlas_page")
    assert page["status"] == "active" and page["inputs"]["card_versions"] == {
        armour["card_id"]: armour["build"]["card_version"]
    }


# ---------------------------------------------------------------- schema contradictions named in the r2 review


def test_review_objects_accept_approved_for_only_when_reviewed(validator: Draft202012Validator) -> None:
    castle = _card("zamok-castle")
    curated = next(a for a in castle["assertions"] if a["source_id"] == "atlas_curated")
    assert curated["review"]["status"] == "reviewed"
    ok = copy.deepcopy(castle)
    next(a for a in ok["assertions"] if a["source_id"] == "atlas_curated")["review"]["approved_for"] = ["meaning"]
    ok["quality"]["linguistic_review"] = {"status": "reviewed", "lane": "human", "approved_for": ["stress"]}
    assert not _errors(validator, ok)
    bad = copy.deepcopy(castle)
    next(a for a in bad["assertions"] if a["source_id"] == "ulif")["review"]["approved_for"] = ["meaning"]
    assert _errors(validator, bad), "approved_for with status none must be rejected"
    bad = copy.deepcopy(ok)
    next(a for a in bad["assertions"] if a["source_id"] == "atlas_curated")["review"]["approved_for"] = []
    assert _errors(validator, bad), "an empty approved_for must be rejected"
