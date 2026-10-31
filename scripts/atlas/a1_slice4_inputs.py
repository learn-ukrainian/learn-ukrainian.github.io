"""Verify the frozen remaining-inventory A1 slice-4 inputs and append-only union.

Use for #11943 slice-4 replay; never allocate identities, acquire sources or publish cards.
"""

import argparse
import copy
import hashlib
import json
import re
from functools import partial
from pathlib import Path

import yaml

from scripts.atlas import a1_slice3_inputs as previous
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import _payload_text, digest, selected_rows

SOURCE_SHA = "0398eb5caa1c6a98dccaf9275520ccb2f978a95c"
JOIN = "remaining_resolved_entry_priority_inventory_order_v1"
VERSION = "a1-slice4-v1"
MANIFEST = "registry/atlas/a1-v1-slice4.json"
COMPANION = "registry/atlas/identity/a1-v1-slice4.json"
INPUTS = "registry/atlas/a1-v1-slice4-inputs.json"
INPUTS_SHA256 = "c3d85031e708005e8018c097cd35ce83b985f9ceda5e5b1a8659e61706f660e8"
MANIFEST_SHA256 = "9d8dc2693765f87adbf01decc72542c8225e942f0c60aa9bed4cdc982d6b38b4"
# Independent raw-byte pins for the already-checked-in portable inputs. The
# snapshot and manifest repeat these pins; neither can replace this layer.
FILE_SHA256 = {
    "registry/atlas/a1-v1-inventory.json": "4cbcb769f0e8379d43a2cd86e48ef353e2328e0b5a895b410f540547cc409a59",
    "registry/atlas/a1-v1-slice2.json": "d8a45ed57a824cf0c7cb94cfd40eb689f50957b64c39d647baeb06521d506015",
    "registry/atlas/a1-v1-slice3-plan-inputs.json": "5d48a9632825f3f110843792214612c733a17fc4bd23a11d2046166f674f3b0d",
    "registry/atlas/a1-v1-slice3.json": "9ff22f62cd50485fe68b1f33504e56c58761d0d352f47ab5a3f64f365438d5fd",
    "registry/atlas/identity/a1-v1-slice2.json": "b1ea5099207618dc3879eb517e28867c174b629126ae2b0e8b9d8629ce564e52",
    "registry/atlas/identity/a1-v1-slice3.json": "f4de91773ffa6e59e953c7ea0645205f06d55a146b88403665cef0fe57647419",
    "registry/atlas/identity/registry.json": "681be77e60edbe621ca68e680db2bffbbd9e99267b011fb0515e090fe8d8a06d",
}


def select(inventory, slice3, snapshot):
    """Retain every occurrence, whole plan reference and original entry identity."""
    arc = json.loads(snapshot["files"]["site/src/data/arc-a1.json"])
    words = yaml.safe_load(snapshot["files"]["curriculum/l2-uk-en/evidence/a1/_words.registry.yaml"])
    words = {word["id"]: word for word in words}
    terms = set()
    for position in arc["positions"][:8]:
        plan = yaml.safe_load(snapshot["files"][
            "curriculum/l2-uk-en/lesson-plans/a1/" + position["slug"] + ".yaml"])
        cards.require(plan["arc_ref"]["position"] == position["position"], "plan_position_mismatch")
        for lesson in plan["lessons"]:
            for role in ("core", "incidental", "recycled"):
                for ref in lesson.get("inventory", {}).get("vocabulary", {}).get(role, []):
                    item = ref if isinstance(ref, dict) else words[ref]
                    lemma = item.get("lemma", item.get("text"))
                    cards.require(isinstance(lemma, str) and bool(lemma), "plan_vocabulary_unresolved")
                    terms.add(previous.key(lemma))
    second = {row["id"] for row in selected_rows(inventory)}
    third = set(slice3["row_card_ids"])
    cards.require(len(second) == 19 and len(third) == 177 and not second & third,
                  "slice4_prior_selection_drift")
    groups, ineligible, remaining = {}, {}, []
    for index, row in enumerate(inventory["rows"]):
        if row["id"] in second | third:
            continue
        remaining.append(row)
        mapping = row["mapping"]
        eligible = mapping["resolution"] == "resolved" and mapping["kind"] in {"lemma", "name"}
        if not eligible or any(mapping.get(k) in (None, "") for k in ("entry_id", "lemma", "pos")):
            ineligible[mapping["kind"]] = ineligible.get(mapping["kind"], 0) + 1
            continue
        entry = groups.setdefault(mapping["entry_id"], {
            "entry_id": mapping["entry_id"], "first_index": index, "kind": mapping["kind"],
            "lemma": mapping["lemma"], "pos": mapping["pos"],
            "preferred": previous.key(mapping["lemma"]) in terms, "row_ids": []})
        cards.require((entry["lemma"], entry["kind"], entry["pos"]) ==
                      (mapping["lemma"], mapping["kind"], mapping["pos"]), "slice4_entry_disagreement")
        entry["row_ids"].append(row["id"])
    ordered = sorted(groups.values(), key=lambda g: (0 if g["preferred"] else 1,
                     g["first_index"], str(g["entry_id"])))
    selected = {row for entry in ordered[:60] for row in entry["row_ids"]}
    return {
        "schema_version": "atlas-a1-slice4-selection.v1", "source_sha": SOURCE_SHA, "join": JOIN,
        "preferred_plan_sha": previous.PLAN_SHA, "source_file_sha256": dict(FILE_SHA256),
        "original_rows": len(inventory["rows"]), "prior_selected_rows": len(second | third),
        "remaining_rows": len(remaining), "eligible_targets": len(ordered),
        "preferred_terms": len(terms), "preferred_targets": sum(g["preferred"] for g in ordered),
        "cap_deferred_targets": len(ordered[60:]), "ineligible_row_kinds": ineligible,
        "selected_targets": ordered[:60],
        "selected_row_ids": [r["id"] for r in inventory["rows"] if r["id"] in selected],
    }


def frozen_selection(root):
    snapshot = cards.load(root / INPUTS)
    cards.require(digest(snapshot) == INPUTS_SHA256, "slice4_snapshot_digest_mismatch")
    for path, expected in FILE_SHA256.items():
        cards.require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected,
                      "slice4_input_file_digest_mismatch")
    inventory = cards.load(root / "registry/atlas/a1-v1-inventory.json")
    plans = cards.load(root / previous.PLAN_INPUTS)
    cards.require(digest(plans) == previous.PLAN_INPUTS_SHA256 and plans["plan_sha"] == previous.PLAN_SHA,
                  "reviewed_plan_inputs_digest_mismatch")
    selection = select(inventory, cards.load(root / previous.MANIFEST), plans)
    cards.require(selection == snapshot, "slice4_selection_drift")
    return inventory, selection


def allocation(base, companion, pins, root):
    """Extend the exact preserved three-part union; assembly only reads this result."""
    third = cards.load(root / previous.MANIFEST)
    consumed = previous.allocation(base, cards.load(root / previous.COMPANION), third["allocation_pins"], root)
    cards.require(digest(base) == pins["base_sha256"] and digest(consumed) == pins["consumed_sha256"]
                  and digest(companion) == pins["companion_sha256"], "slice4_allocation_digest_mismatch")
    cards.require(digest(cards.load(root / "registry/atlas/identity/a1-v1-slice2.json")) ==
                  pins["slice2_companion_sha256"] and digest(cards.load(root / previous.COMPANION)) ==
                  pins["slice3_companion_sha256"], "slice4_prior_companion_digest_mismatch")
    cards.require(companion["base_sha256"] == digest(consumed)
                  and companion["schema_version"] == "atlas-a1-slice4-allocation.v1", "slice4_companion_mismatch")
    effective = copy.deepcopy(consumed)
    effective["entries"].extend(copy.deepcopy(companion["entries"]))
    entries = {entry["card_id"]: entry for entry in effective["entries"]}
    for addition in companion["senses"]:
        entries[addition["card_id"]]["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
    effective["events"].extend(copy.deepcopy(companion["events"]))
    effective["registry_version"] += 1
    cards.require(digest(effective) == pins["combined_sha256"], "slice4_union_mismatch")
    foundation.registry_check(effective)
    _, selection = frozen_selection(root)
    targets = {target["entry_id"]: target for target in selection["selected_targets"]}
    old = {entry["card_id"] for entry in consumed["entries"]}
    cards.require(not old.intersection(e["card_id"] for e in companion["entries"]), "slice4_reminted_card")
    for entry in companion["entries"]:
        events = [e for e in companion["events"] if e["kind"] == "mint" and e.get("cards") == [entry["card_id"]]]
        cards.require(len(events) == 1, "slice4_creation_mint_mismatch")
        evidence = json.loads(events[0]["evidence"])
        cards.require(evidence["key_at_creation"] == entry["key_at_creation"], "slice4_creation_key_mismatch")
        target = targets.get(evidence["entry_id"])
        key = entry["key_at_creation"]
        cards.require(target is not None and (key["spelling"], key["pos"]) == (target["lemma"], target["pos"]),
                      "slice4_creation_entry_mismatch")
        cards.require(entry["card_kind"] == ("proper_name" if target["kind"] == "name" else "lexeme"),
                      "slice4_creation_kind_mismatch")
        cards.require(any(k["source_id"] == "vesum" and k["key"] == f"vesum:entry:{target['entry_id']}"
                          for k in key["source_keys"]), "slice4_creation_source_mismatch")
    for record in companion["source_records"]:
        for correspondence in record["correspondence"]:
            cards.require(any(a["kind"] == "uid" and a["key"] == correspondence["locator"]
                              and a["snapshot_id"] == correspondence["snapshot_id"] for a in record["aliases"]),
                          "slice4_source_correspondence_mismatch")
    return effective


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _canonical_grammar(analysis, target):
    """Distinguish citation readings from syncretic forms of the same entry."""
    if (analysis.get("entry_id"), analysis.get("lemma"), analysis.get("pos"),
            analysis.get("word_form")) != (target["entry_id"], target["lemma"],
                                           target["pos"], target["lemma"]):
        return False
    tags = analysis["tags"].split(":")
    if tags[0] != target["pos"]:
        return False
    if target["pos"] == "noun":
        # Plural-only headwords retain p:...:ns; indeclinables use the
        # singular nominative reading, not an arbitrary identical case form.
        return "v_naz" in tags and (("p" in tags) == ("ns" in tags))
    if target["pos"] == "adj":
        return "m" in tags and "v_naz" in tags
    if target["pos"] == "verb":
        return "inf" in tags
    return target["pos"] == "adv"


def _validate_grammar(claim, record, target):
    cards.require(record["source_id"] == "vesum", "slice4_grammar_requires_vesum")
    match = re.fullmatch(r"/clean_analyses/(\d+)/tags", claim["pointer"])
    cards.require(match is not None, "slice4_grammar_pointer_not_analysis")
    analyses = record["payload"]["clean_analyses"]
    candidates = [i for i, analysis in enumerate(analyses) if _canonical_grammar(analysis, target)]
    cards.require(len(candidates) == 1, "slice4_grammar_canonical_reading_ambiguous")
    index = int(match[1])
    cards.require(claim["entry_id"] == target["entry_id"] and index == candidates[0],
                  "slice4_grammar_not_canonical_headword")
    analysis = analyses[index]
    cards.require(claim["span"] == [0, len(analysis["tags"])], "slice4_grammar_partial_tags")
    required = {(f"/clean_analyses/{index}/{field}", 0, len(analysis[field]))
                for field in ("word_form", "lemma", "pos")}
    supplied = {(span["pointer"], *span["span"]) for span in claim.get("supporting_spans", [])}
    cards.require(required <= supplied, "slice4_grammar_binding_receipts_missing")


def validate_inputs(inv, registry, additions, spec, sources, pins, *, root, selection):
    cards.require(digest(inv) == spec["inventory_sha256"] and digest(sources) == spec["sources_sha256"],
                  "slice4_input_drift")
    cards.require(sources["inventory_sha256"] == digest(inv), "source_inventory_mismatch")
    effective = allocation(registry, additions, pins, root)
    selected = [r for r in inv["rows"] if r["id"] in spec["row_card_ids"]]
    cards.require([r["id"] for r in selected] == selection["selected_row_ids"], "slice4_row_selection_mismatch")
    cards.require(sorted(set(spec["row_card_ids"].values())) == spec["card_ids"], "slice4_card_mapping_mismatch")
    for target in selection["selected_targets"]:
        identities = {spec["row_card_ids"][r] for r in target["row_ids"]}
        cards.require(len(identities) == 1, "slice4_entry_card_disagreement")
        identity = next(iter(identities))
        entry = next(e for e in effective["entries"] if e["card_id"] == identity)
        cards.require((entry["key_at_creation"]["spelling"], entry["key_at_creation"]["pos"]) ==
                      (target["lemma"], target["pos"]), "slice4_row_card_identity_mismatch")
    for record in sources["records"].values():
        call = sources["calls"][record["call_key"]]
        cards.require(digest(call["response"]) == record["response_sha256"] and call["tool"] == record["tool"]
                      and call["arguments"] == record["arguments"], "tool_response_digest_mismatch")
    claims = list(spec["claims"])
    for attempts in spec["stress_attempts"].values():
        for attempt in attempts:
            cards.require(attempt["evidence_call"] in sources["calls"], "slice4_stress_call_missing")
            if attempt["state"] == "supported":
                claim = attempt["claim"]
                record = sources["records"][claim["record_key"]]
                cards.require(record["call_key"] == attempt["evidence_call"]
                              and record["source_id"] == attempt["source_id"], "slice4_stress_reference_mismatch")
                claims.append(claim)
        chosen, _ = cards.choose_stress(attempts)
        if chosen:
            cards.require(sources["records"][chosen["record_key"]]["source_id"] in {"ulif", "sum20"},
                          "slice4_stress_authority")
    grammar_targets = {}
    for row in selected:
        identity = spec["row_card_ids"][row["id"]]
        target = {key: row["mapping"][key] for key in ("entry_id", "lemma", "pos")}
        cards.require(grammar_targets.get(identity, target) == target, "slice4_grammar_target_disagreement")
        grammar_targets[identity] = target
    for claim in claims:
        record = sources["records"][claim["record_key"]]
        if claim["field"] == "grammatical_label":
            cards.require(claim["card_id"] in grammar_targets, "slice4_grammar_target_missing")
            _validate_grammar(claim, record, grammar_targets[claim["card_id"]])
        if claim["field"] == "definition_uk":
            cards.require(record["source_id"] in {"sum20", "vts_busel_slovnyk_me", "ulif"},
                          "slice4_meaning_authority")
        for span in [claim, *claim.get("alternative_forms", []), *claim.get("supporting_spans", [])]:
            text = _payload_text(record["payload"], span["pointer"])
            start, end = span["span"]
            cards.require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), "invalid_span")
            quotation = text[start:end]
            literals = _strings(sources["calls"][record["call_key"]]["response"])
            if record["source_id"] == "vts_busel_slovnyk_me":
                literals = (literal.split("Джерело:", 1)[0].split("Значення в інших", 1)[0]
                            for literal in literals)
            cards.require(any(quotation in literal for literal in literals),
                          "slice4_quotation_outside_tool_response")
    return effective, selected


def load_batch(root):
    manifest = cards.load(root / MANIFEST)
    cards.require(digest(manifest) == MANIFEST_SHA256, "reviewed_manifest_digest_mismatch")
    inventory, selection = frozen_selection(root)
    cards.require(selection == manifest["selection"] and manifest["source_file_sha256"] == FILE_SHA256,
                  "slice4_manifest_selection_drift")
    cards.require(len(selection["selected_row_ids"]) == 191 and len(selection["selected_targets"]) == 60,
                  "slice4_denominator_mismatch")
    third = cards.load(root / previous.MANIFEST)
    prior = {r["id"]: {"state": "delivered_slice2", "card_id": r["mapping"]["pilot"]["card_id"]}
             for r in selected_rows(inventory)}
    prior.update({rid: {"state": "delivered_slice3", "card_id": cid} for rid, cid in third["row_card_ids"].items()})
    def eligible(mapping):
        return mapping["resolution"] == "resolved" and mapping["kind"] in {"lemma", "name"} and all(
            mapping.get(k) not in (None, "") for k in ("entry_id", "lemma", "pos"))
    ledger = {r["id"]: prior.get(r["id"], {
        "state": "cap_deferred_slice4" if eligible(r["mapping"]) else "ineligible_slice4", "card_id": None})
        for r in inventory["rows"] if r["id"] not in manifest["row_card_ids"]}
    context = cards.BatchContext(VERSION, MANIFEST, COMPANION, manifest["row_card_ids"],
                                manifest["identity_methods"], partial(validate_inputs, root=root, selection=selection),
                                row_ledger=ledger, residual_owners=manifest["field_residual_owners"])
    return manifest, inventory, cards.load(root / "registry/atlas/identity/registry.json"), cards.load(root / COMPANION), context


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_slice4_inputs --check-selection
Outputs: fixed selection counts on stdout; no writes, allocation or historical Git reads.
Exit codes: 0 verified; 1 refused inputs; 2 usage error.
Related: #11943; scripts.atlas.a1_word_cards --batch slice4
""")
    parser.add_argument("--check-selection", action="store_true", required=True,
                        help="Verify the frozen 191-row/60-target selection; no default write mode")
    parser.parse_args(argv)
    try:
        _, selection = frozen_selection(Path(__file__).resolve().parents[2])
        print(json.dumps({"source_sha": SOURCE_SHA, "join": JOIN, "rows": len(selection["selected_row_ids"]),
                          "cards": len(selection["selected_targets"])}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("A1 slice4 refused: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
