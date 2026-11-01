"""Verify the frozen remaining-inventory A1 slice-6 inputs and append-only union.

Use for #11943 slice-6 replay; never allocate identities, acquire sources or publish cards.
"""

import argparse
import copy
import hashlib
import json
import re
from functools import partial
from pathlib import Path

import yaml

from scripts.atlas import a1_slice3_inputs as slice3_inputs
from scripts.atlas import a1_slice4_inputs as slice4_inputs
from scripts.atlas import a1_slice5_inputs as previous
from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import _payload_text, digest, selected_rows

SOURCE_SHA = "0398eb5caa1c6a98dccaf9275520ccb2f978a95c"
JOIN = "remaining_resolved_entry_priority_inventory_order_v1"
VERSION = "a1-slice6-v1"
MANIFEST = "registry/atlas/a1-v1-slice6.json"
COMPANION = "registry/atlas/identity/a1-v1-slice6.json"
INPUTS = "registry/atlas/a1-v1-slice6-inputs.json"
INPUTS_SHA256 = "05542e67e4f80c716a787558c36d8cfffce82992f2b5b065c581ae3548d10197"
MANIFEST_SHA256 = "06773a597ac30e2ffad06b2d5a5580265029e4b6f1637ecb77e3048053959cab"
# Independent raw-byte pins for the already-checked-in portable inputs. The
# snapshot and manifest repeat these pins; neither can replace this layer.
FILE_SHA256 = {
    "registry/atlas/a1-v1-inventory.json": "4cbcb769f0e8379d43a2cd86e48ef353e2328e0b5a895b410f540547cc409a59",
    "registry/atlas/a1-v1-slice2.json": "d8a45ed57a824cf0c7cb94cfd40eb689f50957b64c39d647baeb06521d506015",
    "registry/atlas/a1-v1-slice3-plan-inputs.json": "5d48a9632825f3f110843792214612c733a17fc4bd23a11d2046166f674f3b0d",
    "registry/atlas/a1-v1-slice3.json": "9ff22f62cd50485fe68b1f33504e56c58761d0d352f47ab5a3f64f365438d5fd",
    "registry/atlas/a1-v1-slice4-inputs.json": "046f2fcbdfcb1fd53d8f4e50b643b89641d1f216d1a451501a7f9fa6a1df1fe0",
    "registry/atlas/a1-v1-slice4.json": "6714055fe6cd9ff08b4c5db596ef16b24ff46992369a158eb48513f506adb149",
    "registry/atlas/a1-v1-slice5-inputs.json": "846d858cbc5024061e5e291b75ba516a9af3fd3825dba0a2b49f9411cf687837",
    "registry/atlas/a1-v1-slice5.json": "eeccc2e366430ff36616f866755eef410c3112fb6e08c2670d4fb9677b98e5e0",
    "registry/atlas/identity/a1-v1-slice2.json": "b1ea5099207618dc3879eb517e28867c174b629126ae2b0e8b9d8629ce564e52",
    "registry/atlas/identity/a1-v1-slice3.json": "f4de91773ffa6e59e953c7ea0645205f06d55a146b88403665cef0fe57647419",
    "registry/atlas/identity/a1-v1-slice4.json": "4ce137435bf6c3d59100a8acd2e5afac7540e4dda7303cd50635a9a5a531f663",
    "registry/atlas/identity/a1-v1-slice5.json": "787193aa27f6c22bc4fd76ab2b47d70e30218f77abac7aeba484aced8cab75b6",
    "registry/atlas/identity/registry.json": "681be77e60edbe621ca68e680db2bffbbd9e99267b011fb0515e090fe8d8a06d",
    "registry/atlas/pilot/pilot-v1.json": "19caa9148c76294156f12b4d1b11c11f4563ba0facac142460dd927543a7bc71"
}


def select(inventory, slice3, slice4, slice5, snapshot):
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
                  "slice6_prior_selection_drift")
    fourth = set(slice4["selected_row_ids"])
    cards.require(len(fourth) == 191 and not fourth & (second | third), "slice6_prior_selection_drift")
    fifth = set(slice5["selected_row_ids"])
    cards.require(len(fifth) == 289 and not fifth & (second | third | fourth), "slice6_prior_selection_drift")
    prior = second | third | fourth | fifth
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
                      (mapping["lemma"], mapping["kind"], mapping["pos"]), "slice6_entry_disagreement")
        entry["row_ids"].append(row["id"])
    ordered = sorted(groups.values(), key=lambda g: (0 if g["preferred"] else 1,
                     g["first_index"], str(g["entry_id"])))
    selected = {row for entry in ordered[:60] for row in entry["row_ids"]}
    cards.require(sum(g["preferred"] for g in ordered) == 0, "slice6_preferred_target_drift")
    return {
        "schema_version": "atlas-a1-slice6-selection.proposal.v1", "source_inventory_sha": SOURCE_SHA, "method": JOIN,
        "original_rows": len(inventory["rows"]), "prior_allocated_rows": len(prior),
        "remaining_rows": len(remaining), "eligible_targets": len(ordered),
        "deferred_target_count": len(ordered[60:]), "ineligible_row_kinds": ineligible,
        "selected_targets": ordered[:60],
        "selected_row_ids": [r["id"] for r in inventory["rows"] if r["id"] in selected],
        "predecessor_selection_sha256": digest(slice5),
        "predecessor_head": "42635c46f6ba27e6b539c4fa83a13b3358e9a9a9",
        "predecessor_held_pr": 12281,
        "deferred_eligible_rows": sum(len(g["row_ids"]) for g in ordered[60:]),
        "notes": "Prior S4/S5 allocation exclusion is NOT delivered/source-certified. S5 is unmerged/held; S6 integration waits predecessorMERGED and currentheadreview+CI. Current reviewed positions9to16plansabsent; sameprior approved8planjoin has0preferred remaining.",
    }


def frozen_selection(root):
    snapshot = cards.load(root / INPUTS)
    cards.require(digest(snapshot) == INPUTS_SHA256, "slice6_snapshot_digest_mismatch")
    for path, expected in FILE_SHA256.items():
        cards.require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected,
                      "slice6_input_file_digest_mismatch")
    inventory = cards.load(root / "registry/atlas/a1-v1-inventory.json")
    plans = cards.load(root / slice3_inputs.PLAN_INPUTS)
    cards.require(digest(plans) == slice3_inputs.PLAN_INPUTS_SHA256 and plans["plan_sha"] == slice3_inputs.PLAN_SHA,
                  "reviewed_plan_inputs_digest_mismatch")
    _, fourth = slice4_inputs.frozen_selection(root)
    _, fifth = previous.frozen_selection(root)
    selection = select(inventory, cards.load(root / slice3_inputs.MANIFEST), fourth, fifth, plans)
    cards.require(selection == snapshot, "slice6_selection_drift")
    return inventory, selection


def allocation(base, companion, pins, root):
    """Extend the preserved pilot and slices 2–5; assembly only reads this result."""
    third = cards.load(root / previous.MANIFEST)
    consumed = previous.allocation(base, cards.load(root / previous.COMPANION), third["allocation_pins"], root)
    cards.require(digest(base) == pins["base_sha256"] and digest(consumed) == pins["consumed_sha256"]
                  and digest(companion) == pins["companion_sha256"], "slice6_allocation_digest_mismatch")
    cards.require(digest(cards.load(root / "registry/atlas/identity/a1-v1-slice2.json")) ==
                  pins["slice2_companion_sha256"] and digest(cards.load(root / previous.COMPANION)) ==
                  pins["slice5_companion_sha256"]
                  and digest(cards.load(root / slice3_inputs.COMPANION)) == pins["slice3_companion_sha256"], "slice6_prior_companion_digest_mismatch")
    cards.require(companion["base_sha256"] == digest(consumed)
                  and companion["schema_version"] == "atlas-a1-slice6-allocation.v1", "slice6_companion_mismatch")
    effective = copy.deepcopy(consumed)
    effective["entries"].extend(copy.deepcopy(companion["entries"]))
    entries = {entry["card_id"]: entry for entry in effective["entries"]}
    for addition in companion["senses"]:
        entries[addition["card_id"]]["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
    effective["events"].extend(copy.deepcopy(companion["events"]))
    effective["registry_version"] += 1
    cards.require(digest(effective) == pins["combined_sha256"], "slice6_union_mismatch")
    foundation.registry_check(effective)
    _, selection = frozen_selection(root)
    targets = {target["entry_id"]: target for target in selection["selected_targets"]}
    old = {entry["card_id"] for entry in consumed["entries"]}
    cards.require(not old.intersection(e["card_id"] for e in companion["entries"]), "slice6_reminted_card")
    for entry in companion["entries"]:
        events = [e for e in companion["events"] if e["kind"] == "mint" and e.get("cards") == [entry["card_id"]]]
        cards.require(len(events) == 1, "slice6_creation_mint_mismatch")
        evidence = json.loads(events[0]["evidence"])
        cards.require(evidence["key_at_creation"] == entry["key_at_creation"], "slice6_creation_key_mismatch")
        target = targets.get(evidence["entry_id"])
        key = entry["key_at_creation"]
        cards.require(target is not None and (key["spelling"], key["pos"]) == (target["lemma"], target["pos"]),
                      "slice6_creation_entry_mismatch")
        cards.require(entry["card_kind"] == ("proper_name" if target["kind"] == "name" else "lexeme"),
                      "slice6_creation_kind_mismatch")
        cards.require(any(k["source_id"] == "vesum" and k["key"] == f"vesum:entry:{target['entry_id']}"
                          for k in key["source_keys"]), "slice6_creation_source_mismatch")
    for record in companion["source_records"]:
        for correspondence in record["correspondence"]:
            cards.require(any(a["kind"] == "uid" and a["key"] == correspondence["locator"]
                              and a["snapshot_id"] == correspondence["snapshot_id"] for a in record["aliases"]),
                          "slice6_source_correspondence_mismatch")
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
        matches = [e for e in entries if record["locator"] in {
            f"ulif:entry:{e['entry_id']}", f"ulif:ulif_dictua_entries:id:{e['entry_id']}"}]
        cards.require(len(matches) == 1, "slice6_ulif_locator_mismatch")
        return matches[0]
    if source == "vts_busel_slovnyk_me":
        cards.require(call["tool"] == "query_slovnyk_me" and call["arguments"]["dict"] == "vts",
                      "slice6_vts_call_mismatch")
        return {"text": text.split("\n\n", 1)[1].split("Джерело:", 1)[0].rstrip()}
    if source == "textbooks":
        return call["response"]["structuredContent"]["hits"][0]
    cards.require(source in {"puls", "grac", "heritage"}, "slice6_unexpected_source")
    return call["response"].get("structuredContent") or {"text": text}


def _canonical_morphology(analysis, target):
    """Use the landed citation rules, including nominative numeral readings."""
    if target["pos"] != "numr":
        return slice4_inputs._canonical_grammar(analysis, target)
    tags = analysis["tags"].split(":")
    return ((analysis.get("entry_id"), analysis.get("lemma"), analysis.get("pos"),
             analysis.get("word_form")) == (target["entry_id"], target["lemma"], "numr", target["lemma"])
            and tags[0] == "numr" and "v_naz" in tags)


def _validate_morphology(claim, record, target):
    """Bind scalar morphology and its identity receipts to one citation analysis."""
    cards.require(record["source_id"] == "vesum", "slice6_morphology_requires_vesum")
    match = re.fullmatch(r"/clean_analyses/(\d+)/tags", claim["pointer"])
    cards.require(match is not None, "slice6_morphology_pointer_not_analysis")
    analyses = record["payload"]["clean_analyses"]
    candidates = [i for i, analysis in enumerate(analyses) if _canonical_morphology(analysis, target)]
    cards.require(len(candidates) == 1, "slice6_morphology_canonical_reading_ambiguous")
    index = int(match[1])
    cards.require(claim["entry_id"] == target["entry_id"] and index == candidates[0],
                  "slice6_morphology_not_canonical_headword")
    analysis = analyses[index]
    if claim["field"] == "grammatical_label":
        expected = [0, len(analysis["tags"])]
    else:
        pattern = r"(?<=:)[mfn](?=:|$)" if claim["field"] == "gender" else r"(?<=:)(?:imperf|perf)(?=:|$)"
        tokens = list(re.finditer(pattern, analysis["tags"]))
        cards.require(len(tokens) == 1 and (claim["field"] != "aspect" or target["pos"] == "verb"),
                      "slice6_morphology_scalar_ambiguous")
        expected = list(tokens[0].span())
    cards.require(claim["span"] == expected, "slice6_morphology_tag_span_mismatch")
    required = {(f"/clean_analyses/{index}/{field}", 0, len(analysis[field]))
                for field in ("word_form", "lemma", "pos")}
    supplied = {(span["pointer"], *span["span"]) for span in claim.get("supporting_spans", [])}
    cards.require(required <= supplied, "slice6_morphology_binding_receipts_missing")


def validate_inputs(inv, registry, additions, spec, sources, pins, *, root, selection):
    cards.require(digest(inv) == spec["inventory_sha256"] and digest(sources) == spec["sources_sha256"],
                  "slice6_input_drift")
    cards.require(sources["inventory_sha256"] == digest(inv), "source_inventory_mismatch")
    effective = allocation(registry, additions, pins, root)
    selected = [r for r in inv["rows"] if r["id"] in spec["row_card_ids"]]
    cards.require([r["id"] for r in selected] == selection["selected_row_ids"], "slice6_row_selection_mismatch")
    cards.require(sorted(set(spec["row_card_ids"].values())) == spec["card_ids"], "slice6_card_mapping_mismatch")
    for target in selection["selected_targets"]:
        identities = {spec["row_card_ids"][r] for r in target["row_ids"]}
        cards.require(len(identities) == 1, "slice6_entry_card_disagreement")
        identity = next(iter(identities))
        entry = next(e for e in effective["entries"] if e["card_id"] == identity)
        cards.require((entry["key_at_creation"]["spelling"], entry["key_at_creation"]["pos"]) ==
                      (target["lemma"], target["pos"]), "slice6_row_card_identity_mismatch")
    for record in sources["records"].values():
        call = sources["calls"][record["call_key"]]
        cards.require(digest(call["response"]) == record["response_sha256"] and call["tool"] == record["tool"]
                      and call["arguments"] == record["arguments"], "tool_response_digest_mismatch")
        cards.require(call["runtime_tool"] == "mcp__sources__" + call["tool"]
                      and not call["response"].get("isError"), "slice6_runtime_call_mismatch")
        cards.require(response_payload(record, call) == record["payload"], "slice6_payload_outside_response")
        if "canonical_row_witness" not in record:
            cards.require(record["snapshot_id"] == record["source_id"] + "@sha256:" + digest(record["payload"]),
                          "slice6_source_snapshot_mismatch")
        if "canonical_row_witness" in record:
            witness = record["canonical_row_witness"]
            if record["source_id"] == "ulif":
                observed = dict(record["payload"])
                observed["id"] = observed["entry_id"]
                observed["normalized_query"] = json.loads(response_text(call))["records"][0]["normalized_query"]
            else:
                cards.require(record["source_id"] == "puls", "slice6_row_witness_source_mismatch")
                observed = record["payload"]["hits"][0]
            row = {field: observed[field] for field in witness["raw_row"]}
            cards.require(row == witness["raw_row"] and record["snapshot_id"] == "selected-row@sha256:" + digest(row),
                          "slice6_original_source_row_drift")
            originals = [r for r in effective["source_records"]
                         if r["source_record_id"] == witness["source_record_id"]]
            cards.require(len(originals) == 1, "slice6_original_source_identity_missing")
            original = originals[0]
            cards.require(original["source_id"] == record["source_id"] and any(
                c["snapshot_id"] == record["snapshot_id"] and c["locator"] == record["locator"]
                and c["status"] == "unique" for c in original["correspondence"]),
                "slice6_original_source_identity_mismatch")
    census = spec["source_identity_census"]
    cards.require(len(census) == len(sources["records"])
                  and {row["record_key"] for row in census} == set(sources["records"]),
                  "slice6_source_census_incomplete")
    for row in census:
        record = sources["records"][row["record_key"]]
        reuse = spec["source_record_reuses"].get(row["record_key"])
        cards.require(row["payload_sha256"] == digest(record["payload"])
                      and row["reused_identity"] == reuse
                      and row["disposition"] == ("reuse" if reuse else "new_observation"),
                      "slice6_source_census_mismatch")
        if reuse:
            cards.require(any(r["source_record_id"] == reuse["source_record_id"]
                              and r["source_id"] == record["source_id"] and any(
                                  c["snapshot_id"] == record["snapshot_id"] == reuse["snapshot_id"]
                                  and c["locator"] == record["locator"] == reuse["locator"]
                                  and c["status"] == "unique" for c in r["correspondence"])
                              for r in effective["source_records"]), "slice6_reused_source_identity_mismatch")
    for card_id, adjudication in spec["identity_adjudications"].items():
        entry = next(e for e in effective["entries"] if e["card_id"] == card_id)
        ulif = sources["records"][adjudication["ulif_record"]]["payload"]
        vesum = sources["records"][adjudication["vesum_record"]]["payload"]
        cards.require(ulif["entry_id"] == adjudication["ulif_entry_id"] and any(
            k["source_id"] == "ulif" and k["key"] == f"ulif:ulif_dictua_entries:id:{ulif['entry_id']}"
            for k in entry["key_at_creation"]["source_keys"]), "slice6_reused_identity_mismatch")
        cards.require(any(a["entry_id"] == adjudication["entry_id"]
                          and a["lemma"] == entry["key_at_creation"]["spelling"]
                          and a["pos"] == entry["key_at_creation"]["pos"]
                          for a in vesum["clean_analyses"]), "slice6_reused_entry_mismatch")
    for card_id, hold in spec.get("identity_holds", {}).items():
        entry = next(e for e in effective["entries"] if e["card_id"] == card_id)
        cards.require(all(k["source_id"] != "ulif" for k in entry["key_at_creation"]["source_keys"])
                      and not entry["senses"] and all(hold[k] for k in ("reason", "owner", "dependency")),
                      "slice6_identity_hold_incomplete")
        cards.require(not any(c["card_id"] == card_id and c["field"] in {"definition_uk", "cefr", "examples"}
                              for c in spec["claims"])
                      and cards.choose_stress(spec["stress_attempts"][card_id])[0] is None,
                      "slice6_identity_hold_has_claim")
    claims = list(spec["claims"])
    for attempts in spec["stress_attempts"].values():
        for attempt in attempts:
            cards.require(attempt["evidence_call"] in sources["calls"], "slice6_stress_call_missing")
            if attempt["state"] == "supported":
                claim = attempt["claim"]
                record = sources["records"][claim["record_key"]]
                cards.require(record["call_key"] == attempt["evidence_call"]
                              and record["source_id"] == attempt["source_id"], "slice6_stress_reference_mismatch")
                claims.append(claim)
        chosen, _ = cards.choose_stress(attempts)
        if chosen:
            cards.require(sources["records"][chosen["record_key"]]["source_id"] in cards.STRESS_ORDER,
                          "slice6_stress_authority")
    for claim in claims:
        record = sources["records"][claim["record_key"]]
        if claim["field"] in {"gender", "aspect", "grammatical_label"}:
            target = next((t for t in selection["selected_targets"] if t["entry_id"] == claim["entry_id"]), None)
            cards.require(target is not None, "slice6_morphology_entry_missing")
            _validate_morphology(claim, record, target)
        if claim["field"] == "definition_uk":
            cards.require(record["source_id"] in {"sum20", "vts_busel_slovnyk_me"},
                          "slice6_meaning_authority")
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
                          "slice6_quotation_outside_tool_response")
    return effective, selected


def load_batch(root):
    manifest = cards.load(root / MANIFEST)
    cards.require(digest(manifest) == MANIFEST_SHA256, "reviewed_manifest_digest_mismatch")
    inventory, selection = frozen_selection(root)
    cards.require(selection == manifest["selection"] and manifest["source_file_sha256"] == FILE_SHA256,
                  "slice6_manifest_selection_drift")
    cards.require(len(selection["selected_row_ids"]) == 258 and len(selection["selected_targets"]) == 60,
                  "slice6_denominator_mismatch")
    third = cards.load(root / slice3_inputs.MANIFEST)
    fourth = cards.load(root / slice4_inputs.MANIFEST)
    fifth = cards.load(root / previous.MANIFEST)
    prior = {r["id"]: {"state": "delivered_slice2", "card_id": r["mapping"]["pilot"]["card_id"]}
             for r in selected_rows(inventory)}
    prior.update({rid: {"state": "delivered_slice3", "card_id": cid} for rid, cid in third["row_card_ids"].items()})
    prior.update({rid: {"state": "allocated_slice4_unreviewed", "card_id": cid}
                  for rid, cid in fourth["row_card_ids"].items()})
    prior.update({rid: {"state": "allocated_slice5_unreviewed", "card_id": cid}
                  for rid, cid in fifth["row_card_ids"].items()})
    def eligible(mapping):
        return mapping["resolution"] == "resolved" and mapping["kind"] in {"lemma", "name"} and all(
            mapping.get(k) not in (None, "") for k in ("entry_id", "lemma", "pos"))
    ledger = {r["id"]: prior.get(r["id"], {
        "state": "cap_deferred_slice6" if eligible(r["mapping"]) else "ineligible_slice6", "card_id": None})
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
        cards.require(cards.load(path) == expected, "slice6_projection_mismatch:" + suffix)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_slice6_inputs --check-selection
Outputs: fixed selection counts on stdout; no writes, allocation or historical Git reads.
Exit codes: 0 verified; 1 refused inputs; 2 usage error.
Related: #11943; scripts.atlas.a1_word_cards --batch slice6
""")
    parser.add_argument("--check-selection", action="store_true", required=True,
                        help="Verify the frozen 258-row/60-target selection; no default write mode")
    parser.parse_args(argv)
    try:
        _, selection = frozen_selection(Path(__file__).resolve().parents[2])
        print(json.dumps({"source_inventory_sha": SOURCE_SHA, "join": JOIN, "rows": len(selection["selected_row_ids"]),
                          "cards": len(selection["selected_targets"])}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("A1 slice6 refused: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
