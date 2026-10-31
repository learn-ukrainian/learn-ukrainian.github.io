"""Read and verify the approved first-eight-plan A1 card batch.

Use for #11943 slice 3 selection and assembly inputs, never to allocate IDs or publish cards.
"""

import argparse
import copy
import hashlib
import json
import unicodedata
from functools import partial
from pathlib import Path

import yaml

from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas.a1_card_receipts import digest, selected_rows, validate_allocation

PLAN_SHA = "e7a9ac497da8bbeba5531937a4c8543369462942"
MANIFEST = "registry/atlas/a1-v1-slice3.json"
COMPANION = "registry/atlas/identity/a1-v1-slice3.json"
PLAN_INPUTS = "registry/atlas/a1-v1-slice3-plan-inputs.json"
PLAN_INPUTS_SHA256 = "bdaaab21adf8aa678921fa785f24fb9075f7e037fab22508d62c94791d85b91a"
MANIFEST_SHA256 = "b59e14203ef9656e51a2d878b6a77296397b5651f1c013931e7adf0ce91ad454"
VERSION = "a1-slice3-v1"
JOIN = "reviewed_plan_vocabulary_to_inventory_mapping_lemma_v1"


def key(value):
    return unicodedata.normalize("NFC", value).replace("\u0301", "").strip().casefold()


def select(inventory, arc, plans, words):
    """Join explicit plan vocabulary to established inventory lemmas, retaining all occurrences."""
    registry = {item["id"]: item for item in words}
    terms = {}
    for position in arc["positions"][:8]:
        plan = plans[position["slug"]]
        cards.require(plan["arc_ref"]["position"] == position["position"], "plan_position_mismatch")
        for lesson in plan["lessons"]:
            for role in ("core", "incidental", "recycled"):
                for ordinal, value in enumerate(lesson.get("inventory", {}).get("vocabulary", {}).get(role, [])):
                    item = value if isinstance(value, dict) else registry[value]
                    lemma = item.get("lemma", item.get("text"))
                    cards.require(isinstance(lemma, str) and bool(lemma), "plan_vocabulary_unresolved")
                    terms.setdefault(key(lemma), []).append({"position": position["position"],
                        "lesson": lesson["n"], "role": role, "ordinal": ordinal, "lemma": lemma})
    excluded = {row["id"] for row in selected_rows(inventory)}
    rows = [row for row in inventory["rows"] if row["id"] not in excluded
            and row["mapping"].get("lemma") and key(row["mapping"]["lemma"]) in terms]
    groups = {}
    for row in rows:
        mapping = row["mapping"]
        cards.require(mapping["resolution"] == "resolved" and mapping["kind"] in {"lemma", "name"},
                      "joined_identity_unresolved")
        identity = mapping["entry_id"]
        group = groups.setdefault(identity, {"lemma": mapping["lemma"], "entry_id": identity,
            "kind": mapping["kind"], "pos": mapping["pos"], "rows": [],
            "first_use": terms[key(mapping["lemma"])][0]})
        cards.require((group["lemma"], group["kind"], group["pos"]) ==
                      (mapping["lemma"], mapping["kind"], mapping["pos"]), "joined_entry_disagreement")
        group["rows"].append(row["id"])
    ordered = sorted(groups.values(), key=lambda g: (g["first_use"]["position"], g["first_use"]["lesson"],
        list(terms).index(key(g["lemma"])), g["entry_id"]))
    return {"join": JOIN, "plan_sha": PLAN_SHA, "plan_terms": len(terms),
            "row_ids": [r["id"] for r in rows], "targets": ordered[:60], "cap_deferred": ordered[60:],
            "slice2_row_ids": sorted(excluded)}


def frozen_selection(root):
    """Read verbatim approved Git inputs without depending on checkout history."""
    snapshot = cards.load(root / PLAN_INPUTS)
    cards.require(digest(snapshot) == PLAN_INPUTS_SHA256, "reviewed_plan_inputs_digest_mismatch")
    cards.require(snapshot["plan_sha"] == PLAN_SHA, "reviewed_plan_input_revision_mismatch")

    def frozen(path):
        return snapshot["files"][path].encode("utf-8")

    arc = json.loads(frozen("site/src/data/arc-a1.json"))
    plans, pins = {}, {}
    for item in arc["positions"][:8]:
        path = "curriculum/l2-uk-en/lesson-plans/a1/" + item["slug"] + ".yaml"
        raw = frozen(path)
        plans[item["slug"]] = yaml.safe_load(raw)
        pins[path] = hashlib.sha256(raw).hexdigest()
    word_path = "curriculum/l2-uk-en/evidence/a1/_words.registry.yaml"
    raw = frozen(word_path)
    pins[word_path] = hashlib.sha256(raw).hexdigest()
    inventory = cards.load(root / "registry/atlas/a1-v1-inventory.json")
    return inventory, select(inventory, arc, plans, yaml.safe_load(raw)), pins


def allocation(base, companion, pins, root):
    """Append the reviewed slice-3 additions to the exact unchanged slice-2 union."""
    previous = cards.load(root / "registry/atlas/a1-v1-slice2.json")
    consumed = validate_allocation(base, cards.load(root / "registry/atlas/identity/a1-v1-slice2.json"),
                                   previous["allocation_pins"])
    cards.require(digest(consumed) == pins["consumed_sha256"] and digest(companion) == pins["companion_sha256"],
                  "slice3_allocation_digest_mismatch")
    cards.require(companion["base_sha256"] == digest(consumed)
                  and companion["schema_version"] == "atlas-a1-slice3-allocation.v1", "slice3_companion_mismatch")
    effective = copy.deepcopy(consumed)
    effective["entries"].extend(copy.deepcopy(companion["entries"]))
    entries = {entry["card_id"]: entry for entry in effective["entries"]}
    for addition in companion["senses"]:
        entries[addition["card_id"]]["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
    effective["events"].extend(copy.deepcopy(companion["events"]))
    effective["registry_version"] += 1
    cards.require(digest(effective) == pins["combined_sha256"], "slice3_union_mismatch")
    foundation.registry_check(effective)
    occupied = {e["card_id"] for e in consumed["entries"]}
    cards.require(not occupied.intersection(e["card_id"] for e in companion["entries"]), "slice3_reminted_card")
    for entry in companion["entries"]:
        events = [e for e in companion["events"] if e["kind"] == "mint" and e.get("cards") == [entry["card_id"]]]
        cards.require(len(events) == 1 and json.loads(events[0]["evidence"])["key_at_creation"] ==
                      entry["key_at_creation"], "slice3_creation_key_mismatch")
        evidence = json.loads(events[0]["evidence"])
        inventory = cards.load(root / "registry/atlas/a1-v1-inventory.json")
        witnesses = [r["mapping"] for r in inventory["rows"]
                     if r["mapping"].get("entry_id") == evidence["entry_id"]]
        cards.require(bool(witnesses) and all((m["lemma"], m["pos"]) ==
                      (entry["key_at_creation"]["spelling"], entry["key_at_creation"]["pos"])
                      for m in witnesses), "slice3_creation_entry_mismatch")
        cards.require(any(k["source_id"] == "vesum" and k["key"] == f"vesum:entry:{evidence['entry_id']}"
                          for k in entry["key_at_creation"]["source_keys"]), "slice3_creation_source_mismatch")
    for record in companion["source_records"]:
        for correspondence in record["correspondence"]:
            cards.require(any(a["kind"] == "uid" and a["key"] == correspondence["locator"]
                              and a["snapshot_id"] == correspondence["snapshot_id"] for a in record["aliases"]),
                          "slice3_source_correspondence_mismatch")
    return effective


def validate_inputs(inv, registry, additions, spec, sources, pins, *, root, selection):
    cards.require(digest(inv) == spec["inventory_sha256"] and digest(sources) == spec["sources_sha256"],
                  "slice3_input_drift")
    cards.require(sources["inventory_sha256"] == digest(inv), "source_inventory_mismatch")
    effective = allocation(registry, additions, pins, root)
    selected = [r for r in inv["rows"] if r["id"] in spec["row_card_ids"]]
    cards.require([r["id"] for r in selected] == selection["row_ids"], "slice3_row_selection_mismatch")
    cards.require(sorted(set(spec["row_card_ids"].values())) == spec["card_ids"], "slice3_card_mapping_mismatch")
    for record in sources["records"].values():
        call = sources["calls"][record["call_key"]]
        cards.require(digest(call["response"]) == record["response_sha256"] and call["tool"] == record["tool"]
                      and call["arguments"] == record["arguments"], "tool_response_digest_mismatch")
    for claim in spec["claims"]:
        if claim["field"] == "definition_uk":
            cards.require(sources["records"][claim["record_key"]]["source_id"] in
                          {"sum20", "vts_busel_slovnyk_me", "ulif"}, "slice3_meaning_authority")
    for attempts in spec["stress_attempts"].values():
        chosen, _ = cards.choose_stress(attempts)
        if chosen:
            cards.require(sources["records"][chosen["record_key"]]["source_id"] in {"ulif", "sum20"},
                          "slice3_stress_authority")
    return effective, selected


def load_batch(root):
    manifest = cards.load(root / MANIFEST)
    cards.require(digest(manifest) == MANIFEST_SHA256, "reviewed_manifest_digest_mismatch")
    inventory, selection, plan_pins = frozen_selection(root)
    cards.require(selection == manifest["selection"] and plan_pins == manifest["plan_file_sha256"],
                  "slice3_selection_drift")
    cards.require(len(selection["row_ids"]) == 177 and len(selection["targets"]) == 45
                  and not selection["cap_deferred"], "slice3_denominator_mismatch")
    base = cards.load(root / "registry/atlas/identity/registry.json")
    companion = cards.load(root / COMPANION)


    context = cards.BatchContext(VERSION, MANIFEST, COMPANION, manifest["row_card_ids"],
                                 manifest["identity_methods"],
                                 partial(validate_inputs, root=root, selection=selection))
    return manifest, inventory, base, companion, context


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_slice3_inputs --check-selection
Outputs: selection counts and fixed input hashes on stdout; no writes or allocation.
Exit codes: 0 selection verified; 1 refused inputs; 2 usage error.
Related: #11943, scripts.atlas.a1_word_cards --batch slice3
""")
    parser.add_argument("--check-selection", action="store_true", required=True,
                        help="Verify the pinned eight-plan selection and print counts; no default write mode")
    parser.parse_args(argv)
    try:
        _, _, _, _, context = load_batch(Path(__file__).resolve().parents[2])
        print(json.dumps({"plan_sha": PLAN_SHA, "join": JOIN, "rows": len(context.row_card_ids),
                          "cards": len(set(context.row_card_ids.values()))}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("A1 slice3 refused: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
