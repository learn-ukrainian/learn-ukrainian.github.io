"""Verify the frozen remaining-inventory A1 slice-5 inputs and append-only union.

Use for #11943 slice-5 replay; never allocate identities, acquire sources or publish cards.
"""

import argparse
import copy
import hashlib
import json
from functools import partial
from pathlib import Path

import yaml

from scripts.atlas import a1_slice3_inputs as slice3_inputs
from scripts.atlas import a1_slice4_inputs as previous
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import _payload_text, digest, selected_rows

SOURCE_SHA = "0398eb5caa1c6a98dccaf9275520ccb2f978a95c"
JOIN = "remaining_resolved_entry_priority_inventory_order_v1"
VERSION = "a1-slice5-v1"
MANIFEST = "registry/atlas/a1-v1-slice5.json"
COMPANION = "registry/atlas/identity/a1-v1-slice5.json"
INPUTS = "registry/atlas/a1-v1-slice5-inputs.json"
INPUTS_SHA256 = "584d3fa472b7973fbe896e9317437b101f11a46fbf635896780551fffcaacc14"
MANIFEST_SHA256 = "488fddc742cca6e0ec0288b027267f0a614ea2d32dedc15bfc320c65778967af"
# Independent raw-byte pins for the already-checked-in portable inputs. The
# snapshot and manifest repeat these pins; neither can replace this layer.
FILE_SHA256 = {
    "registry/atlas/a1-v1-inventory.json": "4cbcb769f0e8379d43a2cd86e48ef353e2328e0b5a895b410f540547cc409a59",
    "registry/atlas/a1-v1-slice2.json": "d8a45ed57a824cf0c7cb94cfd40eb689f50957b64c39d647baeb06521d506015",
    "registry/atlas/a1-v1-slice3-plan-inputs.json": "5d48a9632825f3f110843792214612c733a17fc4bd23a11d2046166f674f3b0d",
    "registry/atlas/a1-v1-slice3.json": "9ff22f62cd50485fe68b1f33504e56c58761d0d352f47ab5a3f64f365438d5fd",
    "registry/atlas/a1-v1-slice4-inputs.json": "046f2fcbdfcb1fd53d8f4e50b643b89641d1f216d1a451501a7f9fa6a1df1fe0",
    "registry/atlas/a1-v1-slice4.json": "cc96b91315c9922d836ddbff3b18a5254be199b200f847dd7dec242006915c77",
    "registry/atlas/identity/a1-v1-slice2.json": "b1ea5099207618dc3879eb517e28867c174b629126ae2b0e8b9d8629ce564e52",
    "registry/atlas/identity/a1-v1-slice3.json": "f4de91773ffa6e59e953c7ea0645205f06d55a146b88403665cef0fe57647419",
    "registry/atlas/identity/a1-v1-slice4.json": "4ce137435bf6c3d59100a8acd2e5afac7540e4dda7303cd50635a9a5a531f663",
    "registry/atlas/identity/registry.json": "681be77e60edbe621ca68e680db2bffbbd9e99267b011fb0515e090fe8d8a06d"
}


def select(inventory, slice3, slice4, snapshot):
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
                    terms.add(slice3_inputs.key(lemma))
    second = {row["id"] for row in selected_rows(inventory)}
    third = set(slice3["row_card_ids"])
    cards.require(len(second) == 19 and len(third) == 177 and not second & third,
                  "slice5_prior_selection_drift")
    fourth = set(slice4["selected_row_ids"])
    cards.require(len(fourth) == 191 and not fourth & (second | third), "slice5_prior_selection_drift")
    prior = second | third | fourth
    groups, ineligible, remaining = {}, {}, []
    for index, row in enumerate(inventory["rows"]):
        if row["id"] in prior:
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
            "preferred": slice3_inputs.key(mapping["lemma"]) in terms, "row_ids": []})
        cards.require((entry["lemma"], entry["kind"], entry["pos"]) ==
                      (mapping["lemma"], mapping["kind"], mapping["pos"]), "slice5_entry_disagreement")
        entry["row_ids"].append(row["id"])
    ordered = sorted(groups.values(), key=lambda g: (0 if g["preferred"] else 1,
                     g["first_index"], str(g["entry_id"])))
    selected = {row for entry in ordered[:60] for row in entry["row_ids"]}
    cards.require(sum(g["preferred"] for g in ordered) == 0, "slice5_preferred_target_drift")
    return {
        "schema_version": "atlas-a1-slice5-selection.proposal.v1", "source_sha": SOURCE_SHA, "method": JOIN,
        "original_rows": len(inventory["rows"]), "prior_selected_rows": len(prior),
        "remaining_rows": len(remaining), "eligible_targets": len(ordered),
        "deferred_target_count": len(ordered[60:]), "ineligible_row_kinds": ineligible,
        "selected_targets": ordered[:60],
        "selected_row_ids": [r["id"] for r in inventory["rows"] if r["id"] in selected],
        "prior_slice4_selection_sha256": digest(slice4),
        "notes": "Prior S4 exclusion is allocation selection only, not review or delivered certification. No prior card/source changed.",
    }


def frozen_selection(root):
    snapshot = cards.load(root / INPUTS)
    cards.require(digest(snapshot) == INPUTS_SHA256, "slice5_snapshot_digest_mismatch")
    for path, expected in FILE_SHA256.items():
        cards.require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected,
                      "slice5_input_file_digest_mismatch")
    inventory = cards.load(root / "registry/atlas/a1-v1-inventory.json")
    plans = cards.load(root / slice3_inputs.PLAN_INPUTS)
    cards.require(digest(plans) == slice3_inputs.PLAN_INPUTS_SHA256 and plans["plan_sha"] == slice3_inputs.PLAN_SHA,
                  "reviewed_plan_inputs_digest_mismatch")
    _, fourth = previous.frozen_selection(root)
    selection = select(inventory, cards.load(root / slice3_inputs.MANIFEST), fourth, plans)
    cards.require(selection == snapshot, "slice5_selection_drift")
    return inventory, selection


def allocation(base, companion, pins, root):
    """Extend the exact preserved four-part union; assembly only reads this result."""
    third = cards.load(root / previous.MANIFEST)
    consumed = previous.allocation(base, cards.load(root / previous.COMPANION), third["allocation_pins"], root)
    cards.require(digest(base) == pins["base_sha256"] and digest(consumed) == pins["consumed_sha256"]
                  and digest(companion) == pins["companion_sha256"], "slice5_allocation_digest_mismatch")
    cards.require(digest(cards.load(root / "registry/atlas/identity/a1-v1-slice2.json")) ==
                  pins["slice2_companion_sha256"] and digest(cards.load(root / previous.COMPANION)) ==
                  pins["slice4_companion_sha256"]
                  and digest(cards.load(root / slice3_inputs.COMPANION)) == pins["slice3_companion_sha256"], "slice5_prior_companion_digest_mismatch")
    cards.require(companion["base_sha256"] == digest(consumed)
                  and companion["schema_version"] == "atlas-a1-slice5-allocation.v1", "slice5_companion_mismatch")
    effective = copy.deepcopy(consumed)
    effective["entries"].extend(copy.deepcopy(companion["entries"]))
    entries = {entry["card_id"]: entry for entry in effective["entries"]}
    for addition in companion["senses"]:
        entries[addition["card_id"]]["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
    effective["events"].extend(copy.deepcopy(companion["events"]))
    effective["registry_version"] += 1
    cards.require(digest(effective) == pins["combined_sha256"], "slice5_union_mismatch")
    foundation.registry_check(effective)
    _, selection = frozen_selection(root)
    targets = {target["entry_id"]: target for target in selection["selected_targets"]}
    old = {entry["card_id"] for entry in consumed["entries"]}
    cards.require(not old.intersection(e["card_id"] for e in companion["entries"]), "slice5_reminted_card")
    for entry in companion["entries"]:
        events = [e for e in companion["events"] if e["kind"] == "mint" and e.get("cards") == [entry["card_id"]]]
        cards.require(len(events) == 1, "slice5_creation_mint_mismatch")
        evidence = json.loads(events[0]["evidence"])
        cards.require(evidence["key_at_creation"] == entry["key_at_creation"], "slice5_creation_key_mismatch")
        target = targets.get(evidence["entry_id"])
        key = entry["key_at_creation"]
        cards.require(target is not None and (key["spelling"], key["pos"]) == (target["lemma"], target["pos"]),
                      "slice5_creation_entry_mismatch")
        cards.require(entry["card_kind"] == ("proper_name" if target["kind"] == "name" else "lexeme"),
                      "slice5_creation_kind_mismatch")
        cards.require(any(k["source_id"] == "vesum" and k["key"] == f"vesum:entry:{target['entry_id']}"
                          for k in key["source_keys"]), "slice5_creation_source_mismatch")
    for record in companion["source_records"]:
        for correspondence in record["correspondence"]:
            cards.require(any(a["kind"] == "uid" and a["key"] == correspondence["locator"]
                              and a["snapshot_id"] == correspondence["snapshot_id"] for a in record["aliases"]),
                          "slice5_source_correspondence_mismatch")
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


def response_text(call):
    return "\n".join(c["text"] for c in call["response"]["content"] if c["type"] == "text")


def response_payload(record, call):
    """Derive the consumed representation from the captured runtime reply."""
    source = record["source_id"]
    text = response_text(call)
    if source == "vesum":
        return json.loads(text.split("- Raw payload: ", 1)[1])
    if source == "ulif":
        entries = json.loads(text)["records"][0]["entries"]
        matches = [e for e in entries if record["locator"] == f"ulif:entry:{e['entry_id']}"]
        cards.require(len(matches) == 1, "slice5_ulif_locator_mismatch")
        return matches[0]
    if source == "vts_busel_slovnyk_me":
        cards.require(call["tool"] == "query_slovnyk_me" and call["arguments"]["dict"] == "vts",
                      "slice5_vts_call_mismatch")
        return {"text": text.split("\n\n", 1)[1].split("Джерело:", 1)[0].rstrip()}
    if source == "textbooks":
        return call["response"]["structuredContent"]["hits"][0]
    cards.require(source in {"puls", "grac", "heritage"}, "slice5_unexpected_source")
    return call["response"].get("structuredContent") or {"text": text}


def validate_inputs(inv, registry, additions, spec, sources, pins, *, root, selection):
    cards.require(digest(inv) == spec["inventory_sha256"] and digest(sources) == spec["sources_sha256"],
                  "slice5_input_drift")
    cards.require(sources["inventory_sha256"] == digest(inv), "source_inventory_mismatch")
    effective = allocation(registry, additions, pins, root)
    selected = [r for r in inv["rows"] if r["id"] in spec["row_card_ids"]]
    cards.require([r["id"] for r in selected] == selection["selected_row_ids"], "slice5_row_selection_mismatch")
    cards.require(sorted(set(spec["row_card_ids"].values())) == spec["card_ids"], "slice5_card_mapping_mismatch")
    for target in selection["selected_targets"]:
        identities = {spec["row_card_ids"][r] for r in target["row_ids"]}
        cards.require(len(identities) == 1, "slice5_entry_card_disagreement")
        identity = next(iter(identities))
        entry = next(e for e in effective["entries"] if e["card_id"] == identity)
        cards.require((entry["key_at_creation"]["spelling"], entry["key_at_creation"]["pos"]) ==
                      (target["lemma"], target["pos"]), "slice5_row_card_identity_mismatch")
    for record in sources["records"].values():
        call = sources["calls"][record["call_key"]]
        cards.require(digest(call["response"]) == record["response_sha256"] and call["tool"] == record["tool"]
                      and call["arguments"] == record["arguments"], "tool_response_digest_mismatch")
        cards.require(call["runtime_tool"] == "mcp__sources__" + call["tool"]
                      and not call["response"].get("isError"), "slice5_runtime_call_mismatch")
        cards.require(response_payload(record, call) == record["payload"], "slice5_payload_outside_response")
    for card_id, adjudication in spec["identity_adjudications"].items():
        entry = next(e for e in effective["entries"] if e["card_id"] == card_id)
        ulif = sources["records"][adjudication["ulif_record"]]["payload"]
        vesum = sources["records"][adjudication["vesum_record"]]["payload"]
        cards.require(ulif["entry_id"] == adjudication["ulif_entry_id"] and any(
            k["source_id"] == "ulif" and k["key"] == f"ulif:ulif_dictua_entries:id:{ulif['entry_id']}"
            for k in entry["key_at_creation"]["source_keys"]), "slice5_reused_identity_mismatch")
        cards.require(any(a["entry_id"] == adjudication["entry_id"]
                          and a["lemma"] == entry["key_at_creation"]["spelling"]
                          and a["pos"] == entry["key_at_creation"]["pos"]
                          for a in vesum["clean_analyses"]), "slice5_reused_entry_mismatch")
    claims = list(spec["claims"])
    for attempts in spec["stress_attempts"].values():
        for attempt in attempts:
            cards.require(attempt["evidence_call"] in sources["calls"], "slice5_stress_call_missing")
            if attempt["state"] == "supported":
                claim = attempt["claim"]
                record = sources["records"][claim["record_key"]]
                cards.require(record["call_key"] == attempt["evidence_call"]
                              and record["source_id"] == attempt["source_id"], "slice5_stress_reference_mismatch")
                claims.append(claim)
        chosen, _ = cards.choose_stress(attempts)
        if chosen:
            cards.require(sources["records"][chosen["record_key"]]["source_id"] in cards.STRESS_ORDER,
                          "slice5_stress_authority")
    for claim in claims:
        record = sources["records"][claim["record_key"]]
        if claim["field"] == "definition_uk":
            cards.require(record["source_id"] in {"sum20", "vts_busel_slovnyk_me"},
                          "slice5_meaning_authority")
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
                          "slice5_quotation_outside_tool_response")
    return effective, selected


def load_batch(root):
    manifest = cards.load(root / MANIFEST)
    cards.require(digest(manifest) == MANIFEST_SHA256, "reviewed_manifest_digest_mismatch")
    inventory, selection = frozen_selection(root)
    cards.require(selection == manifest["selection"] and manifest["source_file_sha256"] == FILE_SHA256,
                  "slice5_manifest_selection_drift")
    cards.require(len(selection["selected_row_ids"]) == 289 and len(selection["selected_targets"]) == 60,
                  "slice5_denominator_mismatch")
    third = cards.load(root / slice3_inputs.MANIFEST)
    fourth = cards.load(root / previous.MANIFEST)
    prior = {r["id"]: {"state": "delivered_slice2", "card_id": r["mapping"]["pilot"]["card_id"]}
             for r in selected_rows(inventory)}
    prior.update({rid: {"state": "delivered_slice3", "card_id": cid} for rid, cid in third["row_card_ids"].items()})
    prior.update({rid: {"state": "allocated_slice4_unreviewed", "card_id": cid}
                  for rid, cid in fourth["row_card_ids"].items()})
    def eligible(mapping):
        return mapping["resolution"] == "resolved" and mapping["kind"] in {"lemma", "name"} and all(
            mapping.get(k) not in (None, "") for k in ("entry_id", "lemma", "pos"))
    ledger = {r["id"]: prior.get(r["id"], {
        "state": "cap_deferred_slice5" if eligible(r["mapping"]) else "ineligible_slice5", "card_id": None})
        for r in inventory["rows"] if r["id"] not in manifest["row_card_ids"]}
    context = cards.BatchContext(VERSION, MANIFEST, COMPANION, manifest["row_card_ids"],
                                manifest["identity_methods"], partial(validate_inputs, root=root, selection=selection),
                                row_ledger=ledger, residual_owners=manifest["field_residual_owners"])
    return manifest, inventory, cards.load(root / "registry/atlas/identity/registry.json"), cards.load(root / COMPANION), context


def verify_projections(output, result):
    """Check every delivered sibling against the same rebuilt canonical output."""
    projections = {"cards": result["cards"],
                   "receipts": {"receipts": result["receipts"], "assertion_receipts": result["assertion_receipts"]},
                   "rows": result["rows"],
                   "residuals": {k: result[k] for k in ("accounting", "held_units", "pending_examples")}}
    for suffix, expected in projections.items():
        path = output.with_name(output.stem + "." + suffix + ".json")
        cards.require(cards.load(path) == expected, "slice5_projection_mismatch:" + suffix)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_slice5_inputs --check-selection
Outputs: fixed selection counts on stdout; no writes, allocation or historical Git reads.
Exit codes: 0 verified; 1 refused inputs; 2 usage error.
Related: #11943; scripts.atlas.a1_word_cards --batch slice5
""")
    parser.add_argument("--check-selection", action="store_true", required=True,
                        help="Verify the frozen 289-row/60-target selection; no default write mode")
    parser.parse_args(argv)
    try:
        _, selection = frozen_selection(Path(__file__).resolve().parents[2])
        print(json.dumps({"source_sha": SOURCE_SHA, "join": JOIN, "rows": len(selection["selected_row_ids"]),
                          "cards": len(selection["selected_targets"])}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("A1 slice5 refused: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
