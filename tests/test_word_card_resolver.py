"""Field resolution rules added for keyed declared sets and card-subject sense evidence (schema.md §6, §8.1)."""

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


def test_sense_field_asserted_on_the_card_is_retained_never_a_card_field():
    card = {
        "card_id": "wc_x", "senses": [], "links": [],
        "assertions": [assertion("ulif", "G-ULIF", 1, "synonyms", "група", mapping={
            "confidence": "unresolved", "basis": "sense", "ambiguous": True}),
            assertion("ulif", "G-ULIF", 1, "spelling", "слово")],
    }
    resolver._recompute(card)
    assert set(card["fields"]) == {"spelling"}
