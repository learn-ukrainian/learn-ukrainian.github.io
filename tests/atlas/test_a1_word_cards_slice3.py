"""Three approved #11943 slice-3 contracts; source text tests receipt mechanics only."""

import copy
import importlib.util
import json
from collections import Counter
from dataclasses import replace
from functools import partial
from pathlib import Path

import pytest

from scripts.atlas import a1_slice3_inputs as inputs
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import Refusal, canonical, digest, selected_rows, validate_allocation

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("slice2_receipt_mechanics", Path(__file__).with_name("test_a1_word_cards.py"))
mechanics = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mechanics)


def appended_union(consumed, companion):
    """Compute literal append pins independently of the slice-3 allocation validator."""
    effective = copy.deepcopy(consumed)
    effective["entries"].extend(copy.deepcopy(companion["entries"]))
    for addition in companion["senses"]:
        entry = next(e for e in reversed(effective["entries"]) if e["card_id"] == addition["card_id"])
        entry["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
    effective["events"].extend(copy.deepcopy(companion["events"]))
    effective["registry_version"] += 1
    return effective


def fixture_context(batch):
    rows = selected_rows(batch["inventory"])
    row_card_ids = {row["id"]: row["mapping"]["pilot"]["card_id"] for row in rows}
    methods = {row_card_ids[row["id"]]: next(candidate["match"]["method"]
               for candidate in row["mapping"]["pilot"]["candidates"]
               if candidate["card_id"] == row_card_ids[row["id"]]) for row in rows}
    batch["manifest"].update(row_card_ids=row_card_ids, identity_methods=methods)
    validator = partial(inputs.validate_inputs, root=ROOT, selection={"row_ids": [row["id"] for row in rows]})
    return cards.BatchContext("a1-slice3-v1", inputs.MANIFEST, inputs.COMPANION, row_card_ids, methods, validator)


def test_reviewed_plan_join_freezes_177_rows_and_45_targets(monkeypatch, capsys):
    """Catch selection drift, lost proper names, pilot reuse and changed pinned plan bytes."""
    assert inputs.PLAN_SHA == "e7a9ac497da8bbeba5531937a4c8543369462942"
    assert inputs.main(["--check-selection"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "plan_sha": "e7a9ac497da8bbeba5531937a4c8543369462942",
        "join": "reviewed_plan_vocabulary_to_inventory_mapping_lemma_v1", "rows": 177, "cards": 45}
    inventory, selection, _ = inputs.frozen_selection(ROOT)
    assert len(selection["row_ids"]) == len(set(selection["row_ids"])) == 177
    assert len(selection["targets"]) == 45
    assert selection["cap_deferred"] == []
    assert [target["entry_id"] for target in selection["targets"]] == [
        436573, 386161, 92026, 39972, 239760, 381081, 239112, 187809, 187816,
        151545, 159689, 376091, 376093, 195009, 382151, 337323, 202885, 382533,
        96584, 357755, 101943, 356837, 29314, 14322, 97383, 51684, 275822,
        94974, 397241, 164577, 397247, 397281, 397346, 98276, 436942, 168709,
        383748, 59992, 60367, 65760, 65771, 373931, 184106, 187738, 348397]
    assert {target["lemma"]: (target["entry_id"], len(target["rows"]))
            for target in selection["targets"] if target["kind"] == "name"} == {
        "Іван": (151545, 3), "Канада": (159689, 2), "Україна": (397241, 5), "Київ": (164577, 9)}
    assert Counter(target["kind"] for target in selection["targets"]) == {"lemma": 41, "name": 4}
    assert Counter(row["mapping"]["kind"] for row in inventory["rows"]
                   if row["id"] in selection["row_ids"]) == {"lemma": 158, "name": 19}
    previous = {f"curriculum/l2-uk-en/a1-v1/{slug}/vocabulary.yaml#/{ordinal}"
                for slug, ordinal, _, _ in mechanics.SELECTED}
    assert len(previous) == 19
    assert set(selection["slice2_row_ids"]) == previous
    assert previous.isdisjoint(selection["row_ids"])
    original = inputs.subprocess.check_output

    def changed_plan(command, *args, **kwargs):
        raw = original(command, *args, **kwargs)
        if command[-1].endswith("/my-family.yaml"):
            return raw + b"\n# changed pinned plan bytes\n"
        return raw

    monkeypatch.setattr(inputs.subprocess, "check_output", changed_plan)
    assert inputs.main(["--check-selection"]) == 1
    assert "slice3_selection_drift" in capsys.readouterr().out


def test_slice3_allocation_preserves_consumed_ids_and_refuses_remapping():
    """Catch prior-ID edits and semantic remapping even with freshly recomputed digest pins."""
    manifest, _, base, companion, _ = inputs.load_batch(ROOT)
    previous = cards.load(ROOT / cards.MANIFEST)
    consumed = validate_allocation(base, cards.load(ROOT / cards.COMPANION), previous["allocation_pins"])
    effective = inputs.allocation(base, companion, manifest["allocation_pins"], ROOT)
    assert canonical(effective) == canonical(appended_union(consumed, companion))
    by_card = {entry["card_id"]: entry for entry in effective["entries"]}
    for old in consumed["entries"]:
        preserved = copy.deepcopy(by_card[old["card_id"]])
        preserved["senses"] = preserved["senses"][:len(old["senses"])]
        assert canonical(preserved) == canonical(old)
    for member, identity in (("events", "event_id"), ("source_records", "source_record_id")):
        observed = {item[identity]: item for item in effective[member]}
        assert all(canonical(observed[item[identity]]) == canonical(item) for item in consumed[member])
    assert companion["entries"] and companion["source_records"]
    for mutation in ("creation_key", "duplicate_id", "source_correspondence"):
        altered = copy.deepcopy(companion)
        if mutation == "creation_key":
            entry = altered["entries"][0]
            entry["key_at_creation"]["spelling"] = "foreign-fixture-identity"
            event = next(event for event in altered["events"]
                         if event["kind"] == "mint" and event.get("cards") == [entry["card_id"]])
            evidence = json.loads(event["evidence"])
            evidence["key_at_creation"] = copy.deepcopy(entry["key_at_creation"])
            event["evidence"] = canonical(evidence).decode()
        elif mutation == "duplicate_id":
            altered["entries"].append(copy.deepcopy(altered["entries"][0]))
        else:
            source = altered["source_records"][0]
            source["correspondence"][0]["locator"] = "fixture:foreign-correspondence"
            event = next(event for event in altered["events"]
                         if event.get("to") == [source["source_record_id"]])
            evidence = json.loads(event["evidence"])
            evidence["locator"] = "fixture:foreign-correspondence"
            event["evidence"] = canonical(evidence).decode()
        pins = {**manifest["allocation_pins"], "companion_sha256": digest(altered),
                "combined_sha256": digest(appended_union(consumed, altered))}
        with pytest.raises((Refusal, foundation.Refusal)) as refusal:
            inputs.allocation(base, altered, pins, ROOT)
        assert str(refusal.value) == {
            "creation_key": "slice3_creation_entry_mismatch",
            "duplicate_id": "Reused identity; restore prior registry",
            "source_correspondence": "slice3_source_correspondence_mismatch"}[mutation]


def test_slice3_authorities_and_reviewed_chain_replay(monkeypatch, tmp_path, capsys):
    """Catch forbidden authorities, foreign forms, review bypass and changed delivered bytes."""
    batch = mechanics.batch.__wrapped__()
    name_record = copy.deepcopy(batch["sources"]["records"]["ulif:яйце"])
    name_record.update(snapshot_id="fixture:ulif:Київ:snapshot:1", locator="fixture:ulif:Київ:row:13603",
                       source_url="https://example.invalid/ulif/13603", arguments={"words": ["Київ"]},
                       payload={"entry_id": 13603, "headword": "Ки́їв"}, call_key="ulif:Київ")
    name_record.update(content_sha256=digest(name_record["payload"]),
                       response_sha256=digest(name_record["payload"]))
    name_claim = {"entry_id": 164577, "field": "stress", "record_key": "ulif:Київ",
                  "pointer": "/headword", "span": [0, 5]}
    name_receipt = cards._receipt_for(name_claim, {"ulif:Київ": name_record})
    cards._lexeme(name_claim, name_receipt, name_record, "Київ")
    assert name_receipt["quotation"] == "Ки́їв"
    assert (name_receipt["record_key"], name_receipt["entry_id"], name_record["payload"]["entry_id"]) == (
        "ulif:Київ", 164577, 13603)
    assert name_receipt["arguments"] == {"words": ["Київ"]}
    assert cards._claim_value(name_claim, name_receipt, name_record)[0] == "Ки́їв"
    with pytest.raises(Refusal, match="record_lemma_mismatch"):
        cards._lexeme({**name_claim, "record_key": "ulif:київ"}, name_receipt, name_record, "Київ")
    with pytest.raises(Refusal, match="entry_mismatch"):
        cards.verify_receipt(name_receipt, {"ulif:Київ": name_record}, 425814)
    monkeypatch.setattr(inputs, "allocation", lambda base, companion, pins, root:
                        validate_allocation(base, companion, pins))
    ulif = batch["sources"]["records"]["ulif:яйце"]
    ulif["payload"]["sense_gloss"] = "A literal ULIF sense gloss."
    mechanics.refresh(batch, "ulif")
    definition = batch["manifest"]["claims"][0]
    definition.update(record_key="ulif:яйце", pointer="/sense_gloss", span=[0, 27])
    mechanics.add_scope(batch["manifest"], definition)
    context = fixture_context(batch)
    result = cards.build(**batch, batch=context)
    assert result["schema_version"] == "atlas-a1-slice3-build.v1"
    assert mechanics.values(result, "definition_uk", mechanics.SENSE) == ["A literal ULIF sense gloss."]
    assert mechanics.values(result, "stress") == ["яйце" + mechanics.ACUTE]
    assert mechanics.values(result, "paradigm") == [{"slot": "noun:n:v_naz", "forms": ["fixture-form"],
                                                   "entry_id": 436914, "tags": "noun:n:v_naz"}]
    assert cards.verify(result, batch["sources"], batch["manifest"], batch=context)["cards"] == 11
    target = mechanics.target(result)
    assert target["build"]["rules_version"] == "a1-slice3-v1"
    assert target["build"]["inputs"]["I"]["allocation"]["ref"] == "registry/atlas/identity/a1-v1-slice3.json"
    assert target["build"]["inputs"]["O"]["batch"]["ref"] == "registry/atlas/a1-v1-slice3.json"
    no_sense_effective, no_sense_rows = context.validate_inputs(
        batch["inventory"], batch["base"], batch["companion"], batch["manifest"], batch["sources"], batch["pins"])
    next(entry for entry in no_sense_effective["entries"] if entry["card_id"] == "wc_n1g44brn5vs2")["senses"] = []
    no_sense_context = replace(context, validate_inputs=lambda *_: (no_sense_effective, no_sense_rows))
    no_sense_result = cards.build(**batch, batch=no_sense_context)
    assert next(card for card in no_sense_result["cards"] if card["card_id"] == "wc_n1g44brn5vs2")["senses"] == []
    sense_fields = {"definition_uk", "gloss_en", "sense_label", "register", "synonyms", "antonyms",
                    "examples", "russification_exposed", "collocations"}
    empty_rows = [row for row in no_sense_result["accounting"]
                  if row["card_id"] == "wc_n1g44brn5vs2" and row["field"] in sense_fields]
    assert len(empty_rows) == 9
    assert {row["field"]: (row["sense_id"], row["state"], row["reason"], row["dependency"], row["owner"])
            for row in empty_rows} == {field: (None, "empty", "source_sense_claim_unresolved",
        "exact source claim and reviewed sense correspondence", "Atlas coordinator") for field in sense_fields}
    assert all(row["assertion_ids"] == [] and row["receipt_ids"] == [] for row in empty_rows)
    mirror = copy.deepcopy(batch)
    claim = mirror["manifest"]["claims"][0]
    claim.update(record_key="mirror:яйце", pointer="/article", span=[0, 20])
    mechanics.add_scope(mirror["manifest"], claim)
    with pytest.raises(Refusal, match="slice3_meaning_authority"):
        cards.build(**mirror, batch=fixture_context(mirror))
    vts = copy.deepcopy(batch)
    mechanics.set_stress(vts, mechanics.VTS, "яйце" + mechanics.ACUTE)
    with pytest.raises(Refusal, match="slice3_stress_authority"):
        cards.build(**vts, batch=fixture_context(vts))
    foreign = copy.deepcopy(batch)
    foreign["sources"]["records"]["vesum:яйце"]["payload"]["clean_analyses"][0]["entry_id"] = 425814
    mechanics.refresh(foreign, "vesum")
    with pytest.raises(Refusal, match="form_entry_mismatch"):
        cards.build(**foreign, batch=fixture_context(foreign))
    example = mechanics.example_claim(batch)
    pending = cards.build(**batch, batch=context)
    assert mechanics.values(pending, "examples", mechanics.SENSE) == []
    assert pending["pending_examples"][0]["reason"] == "independent_a1_review_pending"
    assert cards.complete_chains(pending) == []
    mechanics.approve_example(batch, example)
    approved = cards.build(**batch, batch=context)
    assert mechanics.values(approved, "examples", mechanics.SENSE) == ["An exact cited sentence."]
    assert cards.complete_chains(approved) == ["wc_6bt62wd6zzzf"]
    rewritten = copy.deepcopy(batch)
    rewritten["sources"]["records"]["vts:яйце"]["payload"]["example"] = "An invented replacement."
    mechanics.refresh(rewritten, "vts")
    assert mechanics.values(cards.build(**rewritten, batch=fixture_context(rewritten)),
                            "examples", mechanics.SENSE) == []
    root = tmp_path / "inputs"
    register_path = root / "docs/sources/permissions-register.yaml"
    register_path.parent.mkdir(parents=True)
    register_path.write_bytes(canonical(batch["register"]) + b"\n")
    source_path = root / "sources.json"
    source_path.write_bytes(canonical(batch["sources"]) + b"\n")
    monkeypatch.setattr(cards, "ROOT", root)
    monkeypatch.setattr(inputs, "load_batch", lambda root:
                        (batch["manifest"], batch["inventory"], batch["base"], batch["companion"], context))
    output = tmp_path / "cards.json"
    arguments = ["--batch", "slice3", "--sources", str(source_path), "--output", str(output), "--require-chain"]
    assert cards.main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["complete_chain_cards"] == ["wc_6bt62wd6zzzf"]
    before = output.read_bytes()
    assert before == canonical(approved) + b"\n"
    assert cards.main([*arguments, "--check"]) == 0
    capsys.readouterr()
    assert output.read_bytes() == before
    tampered = cards.load(output)
    tampered["rows"][0]["mapping"] = {"kind": "substituted"}
    output.write_bytes(canonical(tampered) + b"\n")
    assert cards.main([*arguments, "--check"]) == 1
    assert "delivered_output_mismatch" in capsys.readouterr().err
    batch["manifest"]["example_approvals"].clear()
    incomplete_output = tmp_path / "incomplete.json"
    arguments[arguments.index("--output") + 1] = str(incomplete_output)
    assert cards.main(arguments) == 1
    assert "reviewed_full_receipt_chain_pending" in capsys.readouterr().err
    assert not incomplete_output.exists()
