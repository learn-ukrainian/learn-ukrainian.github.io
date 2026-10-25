"""Field resolution rules for keyed declared sets and held sense evidence (schema.md §6, §8.1)."""

from scripts.atlas import word_card_resolver as resolver


def assertion(source, group, tier, field, value_norm, subject="wc_x", kind="card", mapping=None):
    a = {
        "assertion_id": resolver.aid(source, "snap", f"loc:{value_norm}", {"kind": kind, "id": subject}, field,
                                     value_norm, "v1"),
        "subject": {"kind": kind, "id": subject}, "field": field, "value": value_norm, "value_norm": value_norm,
        "source_id": source, "snapshot_id": "snap", "locator": f"loc:{value_norm}", "extraction_version": "v1",
        "extraction_confidence": "high", "producer": {"kind": "source_extract", "name": "t"},
        "review": {"status": "none"}, "licence_ref": {"register_source_id": source, "register_version": 2},
        "independence_group": group, "tier": tier, "status": "active",
    }
    if mapping:
        a["mapping"] = mapping
    return a


def paradigm(source, group, value_norm):
    return assertion(source, group, 1, "paradigm", value_norm)


def test_keyed_slot_with_two_forms_is_a_declared_set_not_a_conflict():
    result = resolver.resolve([paradigm("ulif", "G-ULIF", "v_dav.s=а|б"), paradigm("vesum", "G-VESUM", "v_dav.s=а")],
                              "paradigm", "wc_x")
    assert result["state"] == "variant"
    assert result["propositions"]["v_dav.s"]["state"] == "variant"
    assert {v["value_norm"] for v in result["values"]} == {"v_dav.s=а|б", "v_dav.s=а"}
    declared = next(v for v in result["values"] if v["value_norm"] == "v_dav.s=а|б")
    assert declared["declared_set"] is True


def test_keyed_declared_sets_must_be_equal_to_corroborate():
    equal = resolver.resolve([paradigm("ulif", "G-ULIF", "v_dav.s=а|б"), paradigm("vesum", "G-VESUM", "v_dav.s=б|а")],
                             "paradigm", "wc_x")
    assert equal["state"] == "variant"
    assert equal["independence_groups_agreeing"] == 2
    unequal = resolver.resolve(
        [paradigm("ulif", "G-ULIF", "v_dav.s=а|б"), paradigm("vesum", "G-VESUM", "v_dav.s=а|б|в")], "paradigm", "wc_x")
    assert unequal["state"] == "conflict" and unequal["selected"] is None


def test_keyed_single_forms_keep_the_per_slot_resolution():
    result = resolver.resolve(
        [paradigm("ulif", "G-ULIF", "v_naz.s=а"), paradigm("vesum", "G-VESUM", "v_naz.s=а"),
         paradigm("ulif", "G-ULIF", "v_rod.s=б")], "paradigm", "wc_x")
    assert result["propositions"]["v_naz.s"]["state"] == "verified"
    assert result["propositions"]["v_rod.s"]["state"] == "single-source"
    assert result["state"] == "single-source"


def test_unresolved_sense_evidence_is_retained_and_never_votes():
    held = assertion("ulif", "G-ULIF", 1, "synonyms", "група", subject="ws_x", kind="sense",
                     mapping={"confidence": "unresolved", "basis": "sense", "ambiguous": True})
    card = {"card_id": "wc_x", "links": [], "senses": [{"sense_id": "ws_x", "fields": {}}],
            "assertions": [held, assertion("ulif", "G-ULIF", 1, "spelling", "слово")]}
    resolver._recompute(card)
    assert set(card["fields"]) == {"spelling"}
    synonyms = card["senses"][0]["fields"]["synonyms"]
    assert synonyms["state"] == "unverified" and synonyms["selected"] is None
    assert synonyms["non_voting"] == [{"assertion_id": held["assertion_id"], "reason": "mapping unresolved"}]
    # Display every source-labelled value without lending tier-3 material a vote.
    modern = assertion("ulif", "G-ULIF", 1, "definition_uk", "source article")
    legacy = assertion("atlas0", "G-PROJECT", 3, "definition_uk", "legacy article")
    duplicate = assertion("atlas0", "G-PROJECT", 3, "definition_uk", "source article")
    original = resolver.resolve([modern], "definition_uk", "wc_x")
    projected = resolver.resolve([modern, legacy, duplicate], "definition_uk", "wc_x")
    assert projected["selected"] == original["selected"] == modern["assertion_id"]
    assert projected["state"] == original["state"] == "single-source"
    assert projected["independence_groups_agreeing"] == 1
    by_value = {v["value_norm"]: v for v in projected["values"]}
    assert set(by_value) == {"source article", "legacy article"}
    assert by_value["source article"]["assertion_ids"] == sorted(
        [modern["assertion_id"], duplicate["assertion_id"]])
    assert by_value["source article"]["independence_groups"] == ["G-ULIF"]
    assert by_value["legacy article"]["assertion_ids"] == [legacy["assertion_id"]]
    assert by_value["legacy article"]["mapping_evidenced"] is False
    only_legacy = resolver.resolve([legacy, duplicate], "definition_uk", "wc_x")
    assert only_legacy["state"] == "unverified"
    assert {v["value_norm"]: v["assertion_ids"] for v in only_legacy["values"]} == {
        "source article": [duplicate["assertion_id"]], "legacy article": [legacy["assertion_id"]]}
    assert only_legacy["independence_groups_agreeing"] == 0
