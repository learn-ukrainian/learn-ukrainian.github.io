"""Allocate only the admitted pilot partitions; audit against the pinned baseline.

Run from the assigned worktree with the shared project interpreter. No lexical
cross-source correspondence, source admission, or practice certification occurs.
"""

import argparse
import json
import secrets
import subprocess
import unicodedata
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

from scripts.atlas import word_card_foundation as foundation
from scripts.storage.topology import resolve_store

ROOT = Path.cwd()
MANIFEST = ROOT / "registry/atlas/pilot/pilot-v1.json"
REGISTRY = ROOT / "registry/atlas/identity/registry.json"
BASELINE = "1ada13b572387640a7e8830f2e8daff87596b90f"
BUILD_PREFIX = "pilot-identity-allocation-9402@sha256:"


def normalized(text):
    return unicodedata.normalize("NFC", text.replace("\u0301", ""))


def normalize_mwe_form(spelling: str) -> str:
    """Normalize MWE form for key_at_creation preserving intra-word hyphen and apostrophe."""
    text = unicodedata.normalize("NFC", spelling.replace("\u0301", "")).lower()
    for ap in ("’", "ʼ", "ʻ", "‘", "`", "´"):
        text = text.replace(ap, "'")
    for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015"):
        text = text.replace(dash, "-")
    chars = []
    for c in text:
        if c in ("-", "'"):
            chars.append(c)
        elif unicodedata.category(c).startswith("P"):
            continue
        else:
            chars.append(c)
    return " ".join("".join(chars).split())


def creation(unit, records, vesum):
    anchor = records[unit["anchor_locator"]]
    raw = anchor["raw_row"]
    spelling = normalized(unit["literal_head"])
    keys = [{"source_id": anchor["source_id"], "key": key,
             "snapshot_id": anchor["snapshot_id"]}
            for key in (unit["unit_key"], anchor["locator"])]
    if unit["entry_type"] == "mwe_candidate":
        form = normalize_mwe_form(spelling)
        return ("mwe", {"spelling": spelling, "pos": "phrase",
                        "mwe_key": anchor["locator"] + "|" + form,
                        "source_keys": keys}, [])
    label = raw["grammatical_label"]
    gloss = raw.get("sense_gloss", "")

    # Proper name determination
    proper = label.startswith(("прізвище", "власна назва")) or (
        spelling[:1].isupper() and any(marker in gloss for marker in (
            "населений пункт", "річка", "селище", "місто", "ім'я")))

    # Query VESUM forms for the headword spelling
    raw_proof = [dict(r) for r in vesum.execute(
        "SELECT DISTINCT entry_id, lemma, pos, tags FROM forms_all "
        "WHERE lemma=? AND word_form=lemma ORDER BY entry_id,tags", (spelling,))]

    if label == "абревіатура":
        abbr_proof = [r for r in raw_proof if ":abbr" in r["tags"]]
        if abbr_proof and all(":prop" in r["tags"] for r in abbr_proof):
            proper = True
        proof = abbr_proof
        positions = {r["pos"] for r in proof}
        assert len(positions) == 1, f"Unresolved source-backed abbreviation POS for {spelling}"
        pos = positions.pop()
    elif label == "займенник":
        proof = [r for r in raw_proof if ":pron:" in r["tags"]]
        positions = {r["pos"] for r in proof}
        assert len(positions) == 1, f"Unresolved source-backed pronoun POS for {spelling}"
        pos = positions.pop()
    else:
        pos = next((pos_candidate for prefix, pos_candidate in (
            ("іменник", "noun"), ("множинний іменник", "noun"),
            ("прізвище", "noun"), ("власна назва", "noun"),
            ("прикметник", "adj"), ("прислівник", "adv"),
            ("дієслово", "verb"), ("числівник порядковий", "adj"),
            ("числівник кількісний", "numr"), ("сполучник", "conj"),
            ("прийменник", "prep")) if label.startswith(prefix)), None)
        assert pos is not None, f"Unresolved source-backed POS label {label} for {spelling}"
        proof = [r for r in raw_proof if r["pos"] == pos]

    # For lexemes (not proper names): exclude :prop entries.
    # If the case-kept spelling only returned :prop (like Батьківщина settlement),
    # query lowercase lemma to find the common noun (e.g. батьківщина entry 18180).
    if not proper:
        common_proof = [r for r in proof if ":prop" not in r["tags"]]
        if not common_proof and spelling.lower() != spelling:
            lower_proof = [dict(r) for r in vesum.execute(
                "SELECT DISTINCT entry_id, lemma, pos, tags FROM forms_all "
                "WHERE lemma=? AND word_form=lemma AND pos=? ORDER BY entry_id,tags",
                (spelling.lower(), pos))]
            common_proof = [r for r in lower_proof if ":prop" not in r["tags"]]
        proof = common_proof

    assert proof or proper, f"Missing VESUM POS evidence for a common lexeme {spelling}"
    key = {"spelling": spelling, "stress_patterns": [unit["literal_head"]],
           "pos": pos, "source_keys": keys}
    paradigms = [records[k] for k in unit["source_record_keys"]
                 if records[k]["table"] == "ulif_dictua_sections"
                 and records[k]["raw_row"]["kind"] == "paradigm"]
    assert len(paradigms) <= 1, "Ambiguous frozen paradigm"
    if paradigms:
        key["paradigm_key"] = paradigms[0]["locator"]
        key["source_keys"].append({"source_id": "ulif", "key": paradigms[0]["locator"],
                                  "snapshot_id": paradigms[0]["snapshot_id"]})
    return "proper_name" if proper else "lexeme", key, proof


def seeds(unit, anchor, proper=False):
    gloss = anchor["raw_row"].get("sense_gloss", "")
    if not gloss:
        return [("unsplit", anchor["locator"] + "#unsplit", None)]
    assert gloss.startswith("(") and gloss.endswith(")"), "Unstructured ULIF gloss"
    if proper:
        # Proper name gloss is a disambiguator, not separate lexical senses (Finding 4).
        # Multi-clause proper-name glosses (e.g. Базар "селище в Україні; місце битви")
        # are kept as one unsplit sense.
        if ";" in gloss:
            return [("unsplit", anchor["locator"] + "#unsplit", None)]
        return [("active", f"ulif:entry:{anchor['raw_row']['id']} sense_gloss[0]", gloss[1:-1])]
    parts = [part.strip() for part in gloss[1:-1].split(";")]
    assert all(parts), "Empty source sense unit"
    return [("active", f"ulif:entry:{anchor['raw_row']['id']} sense_gloss[{i}]", part)
            for i, part in enumerate(parts)]


def run(apply):
    manifest = foundation.load(MANIFEST)
    foundation.manifest_check(manifest, MANIFEST)
    before = json.loads(subprocess.check_output(
        ["git", "show", BASELINE + ":registry/atlas/identity/registry.json"],
        timeout=30,
    ))
    registry = foundation.load(REGISTRY)
    foundation.allocation_check(manifest, registry)
    records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
    build = BUILD_PREFIX + manifest["manifest_sha256"]
    rules_version = manifest.get("rules_version", "rules-v1-draft")
    normaliser_version = manifest.get("normaliser_version", "norm-v1")
    units = manifest["selection"]["units"]
    occupied = {e["card_id"] for e in registry["entries"]} | {
        s["sense_id"] for e in registry["entries"] for s in e["senses"]} | {
        r["source_record_id"] for r in registry["source_records"]}
    number = max(int(e["event_id"][3:]) for e in registry["events"])

    def mint(prefix):
        while True:
            identity = prefix + "".join(secrets.choice(foundation.ALPHABET) for _ in range(12))
            if identity not in occupied:
                occupied.add(identity)
                return identity

    def event(kind, target, evidence):
        nonlocal number
        number += 1
        registry["events"].append({"event_id": f"ie_{number:04d}", "kind": kind,
            "build_id": build, "cards" if kind == "mint" else "to": [target],
            "evidence": foundation.canonical(evidence).decode()})

    with ExitStack() as stack:
        sources = foundation.readonly(stack, resolve_store("sources").path)
        vesum = foundation.readonly(stack, resolve_store("vesum").path)
        source_rows_checked = 0
        for record in records.values():
            if record.get("database", "sources") != "sources":
                continue
            observed = foundation.rows(sources, record["table"], record["row_key"])
            assert len(observed) == 1 and observed[0] == record["raw_row"], "Source row drift"
            source_rows_checked += 1

        if apply:
            # Re-generate pilot allocation cleanly starting from baseline
            registry["entries"] = before["entries"][:]
            registry["events"] = before["events"][:]
            registry["source_records"] = before["source_records"][:]
            occupied.clear()
            occupied.update({e["card_id"] for e in registry["entries"]} | {
                s["sense_id"] for e in registry["entries"] for s in e["senses"]} | {
                r["source_record_id"] for r in registry["source_records"]})
            number = max(int(e["event_id"][3:]) for e in registry["events"])

            for unit in units:
                anchor = records[unit["anchor_locator"]]
                kind, key, proof = creation(unit, records, vesum)
                entry = {"card_id": mint("wc_"), "card_kind": kind, "state": "active",
                         "key_at_creation": key, "created_in_build": build, "senses": []}
                registry["entries"].append(entry)
                mint_evidence = {
                    "source_partition": unit["unit_key"],
                    "anchor_locator": anchor["locator"],
                    "snapshot_id": anchor["snapshot_id"],
                    "source_row_sha256": anchor["content_sha256"],
                    "pos_evidence_only_not_lexical_correspondence": proof,
                    "supplementary_correspondence": "unresolved",
                    "paradigm_correspondence": "source-local" if "paradigm_key" in key else "unresolved",
                    "rules_version": rules_version,
                    "normaliser_version": normaliser_version,
                }
                if unit.get("atlas_slug"):
                    mint_evidence["legacy_candidate_slug"] = unit["atlas_slug"]
                event("mint", entry["card_id"], mint_evidence)

                is_proper = kind == "proper_name"
                for order, (state, source_unit, literal) in enumerate(seeds(unit, anchor, proper=is_proper), 1):
                    sense = {"sense_id": mint("ws_"), "order": order, "state": state}
                    entry["senses"].append(sense)
                    event("sense_mint", sense["sense_id"], {
                        "source_partition": unit["unit_key"],
                        "anchor_locator": anchor["locator"],
                        "source_unit": source_unit,
                        "source_row_sha256": anchor["content_sha256"],
                        "state": state,
                        "literal_gloss_unit": literal,
                        "basis": "ULIF structured sense_gloss" if literal else "unaligned source unit; no structured seed",
                        "rules_version": rules_version,
                        "normaliser_version": normaliser_version,
                    })
            registry["registry_version"] = before["registry_version"] + 1

        assert registry["entries"][:len(before["entries"])] == before["entries"]
        assert registry["events"][:len(before["events"])] == before["events"]
        assert registry["source_records"] == before["source_records"]
        assert registry["registry_version"] == before["registry_version"] + 1
        foundation.registry_check(registry)
        foundation.allocation_check(manifest, registry)
        mapping = []
        pilot_entries = [e for e in registry["entries"] if e["created_in_build"] == build]
        pilot_events = [e for e in registry["events"] if e["build_id"] == build]
        for unit in units:
            matches = [e for e in pilot_entries if unit["unit_key"] in foundation.source_keys(e)]
            assert len(matches) == 1, "Missing or shared pilot allocation"
            entry = matches[0]
            kind, key, proof = creation(unit, records, vesum)
            assert entry["card_kind"] == kind and entry["key_at_creation"] == key
            event_matches = [e for e in pilot_events if e["kind"] == "mint" and e["cards"] == [entry["card_id"]]]
            assert len(event_matches) == 1
            evidence = json.loads(event_matches[0]["evidence"])
            anchor = records[unit["anchor_locator"]]
            assert evidence["source_partition"] == unit["unit_key"]
            assert evidence["anchor_locator"] == anchor["locator"]
            assert evidence["snapshot_id"] == anchor["snapshot_id"]
            assert evidence["source_row_sha256"] == anchor["content_sha256"]
            assert evidence["pos_evidence_only_not_lexical_correspondence"] == proof
            assert evidence["rules_version"] == rules_version
            assert evidence["normaliser_version"] == normaliser_version
            if unit.get("atlas_slug"):
                assert evidence["legacy_candidate_slug"] == unit["atlas_slug"]
            expected = seeds(unit, anchor, proper=(kind == "proper_name"))
            assert len(entry["senses"]) == len(expected)
            for order, (sense, (state, source_unit, literal)) in enumerate(zip(entry["senses"], expected, strict=True), 1):
                assert sense["order"] == order and sense["state"] == state
                events = [e for e in pilot_events if e["kind"] == "sense_mint" and e["to"] == [sense["sense_id"]]]
                assert len(events) == 1
                evidence = json.loads(events[0]["evidence"])
                assert evidence["source_partition"] == unit["unit_key"] and evidence["source_unit"] == source_unit
                assert evidence["source_row_sha256"] == anchor["content_sha256"]
                assert evidence["literal_gloss_unit"] == literal and evidence["state"] == state
                assert evidence["rules_version"] == rules_version
                assert evidence["normaliser_version"] == normaliser_version
            source_ids = []
            for locator in unit["source_record_keys"]:
                record = records[locator]
                matches = [r for r in registry["source_records"] if r["source_id"] == record["source_id"] and
                           any(c.get("locator") == locator and c["snapshot_id"] == record["snapshot_id"]
                               and c["status"] == "unique" for c in r["correspondence"])]
                assert len(matches) == 1
                source_ids.append(matches[0]["source_record_id"])
            mapping.append({"unit_key": unit["unit_key"], "anchor_locator": unit["anchor_locator"],
                "card_id": entry["card_id"], "card_kind": kind, "senses": entry["senses"],
                "source_record_ids": source_ids, "supplementary_correspondence": "unresolved"})
        assert len(pilot_entries) == len(mapping) == 150
        assert len({m["card_id"] for m in mapping}) == 150
        sense_count = sum(len(m["senses"]) for m in mapping)
        assert len(pilot_events) == 150 + sense_count
        if apply:
            foundation.write(REGISTRY, registry)
        assert foundation.load(REGISTRY) == registry
        report = {"baseline_sha": BASELINE, "manifest_sha256": manifest["manifest_sha256"],
            "registry_file_sha256": foundation.file_digest(REGISTRY), "registry_version": registry["registry_version"],
            "pilot_units": 150, "allocated_pilot_cards": 150,
            "pilot_card_kinds": dict(Counter(m["card_kind"] for m in mapping)),
            "allocated_pilot_senses": sense_count,
            "sense_states": dict(Counter(s["state"] for m in mapping for s in m["senses"])),
            "preserved_legacy_cards": len(before["entries"]), "preserved_events": len(before["events"]),
            "preserved_source_records": len(before["source_records"]), "source_rows_checked_readonly": source_rows_checked,
            "unallocated_pilot_units": 0, "shared_pilot_card_ids": 0,
            "independent_heldout_proof": "not performed; author allocation audit only",
            "residual_owner": "open-model-data driver",
            "residual": "cross-family exact-head review and landing; lexical correspondence, assembly and certification remain separate"}
        foundation.write(ROOT / "batch_state/reports/9402-allocation-audit.json", report)
        foundation.write(ROOT / "batch_state/reports/9402-unit-identities.json", {"build_id": build, "units": mapping})
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    run(parser.parse_args().apply)
