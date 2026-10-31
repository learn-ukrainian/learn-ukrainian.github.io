"""Three #11943 slice-4 tests approved in issuecomment-6543101302.

Synthetic text proves receipt mechanics only; independent review proves the real cards.
"""

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
from collections import Counter
from functools import partial
from pathlib import Path

import pytest

from scripts.atlas import a1_slice4_inputs as inputs
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import Refusal, canonical, digest, selected_rows, validate_allocation

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("slice3_receipt_mechanics",
                                             Path(__file__).with_name("test_a1_word_cards_slice3.py"))
slice3 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(slice3)
mechanics = slice3.mechanics


def test_slice4_frozen_selection_refuses_drift_and_preserves_191_rows_60_entries(monkeypatch, capsys, tmp_path):
    """Catch row loss, changed ordering/exclusions/entry identity, pin drift and dependence on old Git objects."""
    expected = {"cards": 60, "rows": 191, "join": "remaining_resolved_entry_priority_inventory_order_v1",
                "source_sha": "0398eb5caa1c6a98dccaf9275520ccb2f978a95c"}
    assert inputs.main(["--check-selection"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    inventory, selection = inputs.frozen_selection(ROOT)
    assert digest(selection) == "c3d85031e708005e8018c097cd35ce83b985f9ceda5e5b1a8659e61706f660e8"
    assert (selection["original_rows"], selection["prior_selected_rows"], selection["remaining_rows"],
            selection["eligible_targets"], selection["cap_deferred_targets"], selection["preferred_targets"],
            selection["preferred_terms"]) == (2144, 196, 1948, 659, 599, 0, 84)
    assert selection["ineligible_row_kinds"] == {
        "phrase": 272, "ambiguous": 149, "name": 18, "unresolved": 20, "slash_alternatives": 4}
    assert [t["entry_id"] for t in selection["selected_targets"]] == [
        406467, 82422, 376940, 186992, 192553, 163594, 161722, 82385, 188280, 161650,
        180042, 28683, 150970, 292394, 406358, 288308, 289933, 161525, 422190, 204813,
        70080, 330413, 285033, 262017, 378248, 162570, 334224, 10756, 23312, 187818,
        17025, 308350, 150918, 64973, 371920, 200835, 1559, 389885, 208868, 382610,
        166795, 371580, 283601, 411582, 25953, 87402, 99875, 97787, 157054, 157359,
        303252, 325891, 222512, 219768, 308917, 187623, 158130, 199761, 128908, 258576]
    assert sum(len(t["row_ids"]) for t in selection["selected_targets"]) == 191
    assert len(set(selection["selected_row_ids"])) == 191
    selected = set(selection["selected_row_ids"])
    assert [r["id"] for r in inventory["rows"] if r["id"] in selected] == selection["selected_row_ids"]
    assert {t["lemma"]: len(t["row_ids"]) for t in selection["selected_targets"] if t["kind"] == "name"} == {"Карпати": 2}
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, timeout=30)
    assert subprocess.run(["git", "-C", str(tmp_path), "cat-file", "-e", inputs.SOURCE_SHA],
                          capture_output=True, timeout=30).returncode != 0
    for path in [*inputs.FILE_SHA256, inputs.INPUTS]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    monkeypatch.setattr(inputs, "__file__", str(tmp_path / "scripts/atlas/a1_slice4_inputs.py"))
    assert inputs.main(["--check-selection"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    path = "registry/atlas/a1-v1-inventory.json"
    (tmp_path / path).write_bytes((tmp_path / path).read_bytes() + b"\n")
    assert inputs.main(["--check-selection"]) == 1
    assert "slice4_input_file_digest_mismatch" in capsys.readouterr().out
    monkeypatch.setattr(inputs, "FILE_SHA256", {**inputs.FILE_SHA256,
        path: hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()})
    assert inputs.main(["--check-selection"]) == 1
    assert "slice4_selection_drift" in capsys.readouterr().out
    altered = copy.deepcopy(inventory)
    target = next(r for r in altered["rows"] if r["id"] == selection["selected_targets"][1]["row_ids"][1])
    target["mapping"]["pos"] = "verb"
    with pytest.raises(Refusal, match="slice4_entry_disagreement"):
        inputs.select(altered, cards.load(ROOT / inputs.previous.MANIFEST),
                      cards.load(ROOT / inputs.previous.PLAN_INPUTS))


def test_slice4_allocation_preserves_prior_ids_and_refuses_remapping():
    """Catch changed prior identities/history, duplicate remint and coherent foreign correspondence."""
    manifest, _, base, companion, context = inputs.load_batch(ROOT)
    third = cards.load(ROOT / inputs.previous.MANIFEST)
    consumed = inputs.previous.allocation(base, cards.load(ROOT / inputs.previous.COMPANION),
                                         third["allocation_pins"], ROOT)
    effective = inputs.allocation(base, companion, manifest["allocation_pins"], ROOT)
    assert canonical(effective) == canonical(slice3.appended_union(consumed, companion))
    assert len(companion["entries"]) == 58
    assert len(context.row_card_ids) == 191
    assert Counter(row["state"] for row in context.row_ledger.values()) == {
        "delivered_slice2": 19, "delivered_slice3": 177, "cap_deferred_slice4": 1294, "ineligible_slice4": 463}
    assert {a["entry_id"]: cid for cid, a in manifest["identity_adjudications"].items()} == {
        422190: "wc_yd5ekty2j7kb", 17025: "wc_xbw7msqev2mz"}
    by_card = {e["card_id"]: e for e in effective["entries"]}
    for entry in consumed["entries"]:
        observed = copy.deepcopy(by_card[entry["card_id"]])
        observed["senses"] = observed["senses"][:len(entry["senses"])]
        assert canonical(observed) == canonical(entry)
    for field, key in (("events", "event_id"), ("source_records", "source_record_id")):
        observed = {item[key]: item for item in effective[field]}
        assert all(canonical(observed[item[key]]) == canonical(item) for item in consumed[field])
    for mutation, reason in (("creation", "slice4_creation_entry_mismatch"),
                             ("duplicate", "Reused identity; restore prior registry"),
                             ("correspondence", "slice4_source_correspondence_mismatch")):
        altered = copy.deepcopy(companion)
        if mutation == "creation":
            entry = altered["entries"][0]
            entry["key_at_creation"]["spelling"] = "foreign-fixture-identity"
            event = next(e for e in altered["events"] if e.get("cards") == [entry["card_id"]])
            evidence = json.loads(event["evidence"])
            evidence["key_at_creation"] = copy.deepcopy(entry["key_at_creation"])
            event["evidence"] = canonical(evidence).decode()
        elif mutation == "duplicate":
            altered["entries"].append(copy.deepcopy(altered["entries"][0]))
        else:
            altered["source_records"][0]["correspondence"][0]["locator"] = "fixture:foreign-locator"
        pins = {**manifest["allocation_pins"], "companion_sha256": digest(altered),
                "combined_sha256": digest(slice3.appended_union(consumed, altered))}
        with pytest.raises((Refusal, foundation.Refusal)) as refusal:
            inputs.allocation(base, altered, pins, ROOT)
        assert str(refusal.value) == reason


def test_slice4_receipt_replay_refuses_foreign_quotes_and_unapproved_examples(monkeypatch, tmp_path, capsys):
    """Catch source substitution, wrong spans/senses, unapproved examples and altered CLI output."""
    batch = mechanics.batch.__wrapped__()
    monkeypatch.setattr(inputs, "allocation", lambda base, companion, pins, root:
                        validate_allocation(base, companion, pins))
    rows = selected_rows(batch["inventory"])
    row_cards = {r["id"]: r["mapping"]["pilot"]["card_id"] for r in rows}
    batch["manifest"].update(row_card_ids=row_cards, identity_methods={cid: "overlay" for cid in row_cards.values()})
    for attempts in batch["manifest"]["stress_attempts"].values():
        for attempt in attempts:
            attempt["evidence_call"] = {"ulif": "ulif:яйце", "sum20": "sum20:яйце", mechanics.VTS: "vts:яйце"}[attempt["source_id"]]
    selection = {"selected_row_ids": [r["id"] for r in rows], "selected_targets": []}
    context = cards.BatchContext(inputs.VERSION, inputs.MANIFEST, inputs.COMPANION, row_cards,
        batch["manifest"]["identity_methods"], partial(inputs.validate_inputs, root=ROOT, selection=selection))
    form = next(claim for claim in batch["manifest"]["claims"] if claim["field"] == "paradigm")
    form["supporting_spans"] = [{"pointer": "/clean_analyses/0/tags", "span": [0, 12]}]
    example = mechanics.example_claim(batch)
    pending = cards.build(**batch, batch=context)
    assert pending["schema_version"] == "atlas-a1-slice4-build.v1"
    assert mechanics.values(pending, "examples", mechanics.SENSE) == []
    assert cards.complete_chains(pending) == []
    assert pending["pending_examples"][0]["receipt"]["quotation"] == "An exact cited sentence."
    target_form = next(a for a in mechanics.target(pending)["assertions"] if a["field"] == "paradigm")
    receipt_ids = pending["assertion_receipts"][target_form["assertion_id"]]
    receipts = {r["receipt_id"]: r for r in pending["receipts"]}
    assert [receipts[rid]["quotation"] for rid in receipt_ids] == ["fixture-form", "noun:n:v_naz"]
    forged = copy.deepcopy(batch)
    forged["sources"]["records"]["vts:яйце"]["payload"]["example"] = "An invented replacement."
    forged["manifest"]["sources_sha256"] = digest(forged["sources"])
    with pytest.raises(Refusal, match="slice4_quotation_outside_tool_response"):
        cards.build(**forged, batch=context)
    wrong = copy.deepcopy(batch)
    wrong["manifest"]["claims"][-1]["span"] = [0, 9999]
    with pytest.raises(Refusal, match="invalid_span"):
        cards.build(**wrong, batch=context)
    wrong = copy.deepcopy(batch)
    wrong["manifest"]["scopes"]["examples"]["source_sense_key"] = "fixture:other-sense"
    with pytest.raises(Refusal, match="sense_scope_mismatch"):
        cards.build(**wrong, batch=context)
    wrong = copy.deepcopy(batch)
    mechanics.set_stress(wrong, mechanics.VTS, "яйце" + mechanics.ACUTE)
    with pytest.raises(Refusal, match="slice4_stress_authority"):
        cards.build(**wrong, batch=context)
    mechanics.approve_example(batch, example)
    approved = cards.build(**batch, batch=context)
    assert cards.complete_chains(approved) == ["wc_6bt62wd6zzzf"]
    assert mechanics.values(approved, "definition_uk", mechanics.SENSE) == ["A literal definition."]
    assert mechanics.values(approved, "examples", mechanics.SENSE) == ["An exact cited sentence."]
    register = tmp_path / "docs/sources/permissions-register.yaml"
    register.parent.mkdir(parents=True)
    register.write_bytes(canonical(batch["register"]) + b"\n")
    source_path = tmp_path / "sources.json"
    source_path.write_bytes(canonical(batch["sources"]) + b"\n")
    monkeypatch.setattr(cards, "ROOT", tmp_path)
    monkeypatch.setattr(inputs, "load_batch", lambda _: (batch["manifest"], batch["inventory"], batch["base"], batch["companion"], context))
    output = tmp_path / "batch.json"
    args = ["--batch", "slice4", "--sources", str(source_path), "--output", str(output), "--require-chain"]
    assert cards.main(args) == 0
    summary = json.loads(capsys.readouterr().out)
    assert (summary["cards"], summary["rows"], summary["complete_chain_cards"]) == (11, 2144, ["wc_6bt62wd6zzzf"])
    assert output.read_bytes() == canonical(approved) + b"\n"
    assert cards.main([*args, "--check"]) == 0
    capsys.readouterr()
    changed = cards.load(output)
    changed["rows"][0]["mapping"] = {"kind": "foreign"}
    output.write_bytes(canonical(changed) + b"\n")
    assert cards.main([*args, "--check"]) == 1
    assert "delivered_output_mismatch" in capsys.readouterr().err
