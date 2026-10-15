"""Allocate only the admitted pilot partitions; audit against the pinned baseline.

Run from the assigned worktree with the shared project interpreter. No lexical
cross-source correspondence, source admission, or practice certification occurs.

Modes: no flag verifies the committed registry; `--apply` creates the pilot allocation on a registry that has none
(it refuses to regenerate existing identities); `--append-holding` is the append-only registry step for `unsplit`
holding senses (schema.md §6, §13): it adds one holding sense to each pilot card whose source relation units cannot
be aligned and that has none, under its own build id, keeping every existing identity and event. It is idempotent.
"""

import argparse
import copy
import json
import secrets
import subprocess
import sys
import unicodedata
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.atlas import word_card_foundation as foundation
from scripts.guardrails import worktree_containment as containment
from scripts.storage.topology import resolve_store

ROOT = Path.cwd()
MANIFEST = ROOT / "registry/atlas/pilot/pilot-v1.json"
REGISTRY = ROOT / "registry/atlas/identity/registry.json"
BASELINE = "1ada13b572387640a7e8830f2e8daff87596b90f"
# The reviewed pilot allocation (registry v2, committed in ef03828228bb, #9402 / #10641), pinned by the canonical
# content digest of its registry so the check needs no Git history: every later registry version keeps it whole.
PILOT_ALLOCATION_DIGEST = "d094872dbfaabe71cbfacaf4951138f08861f17c032d04bf0182e1ee0f312860"
BUILD_PREFIX = "pilot-identity-allocation-9402@sha256:"
HOLDING_BUILD_PREFIX = "pilot-holding-sense-allocation-8981@sha256:"
HOLDING_BASIS = "holding sense for source units that cannot be aligned to one active sense (schema.md §6)"


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


# ULIF grammatical label prefix -> VESUM coarse POS. Pronouns and abbreviations are decided from VESUM tags.
LABEL_POS = (
    ("іменник", "noun"), ("множинний іменник", "noun"), ("прізвище", "noun"), ("власна назва", "noun"),
    ("прикметник", "adj"), ("прислівник", "adv"), ("дієслово", "verb"), ("числівник порядковий", "adj"),
    ("числівник кількісний", "numr"), ("сполучник", "conj"), ("прийменник", "prep"),
)
PROPER_GLOSS_MARKERS = ("населений пункт", "річка", "селище", "місто", "ім'я")


def label_pos(label):
    """Coarse POS named by a ULIF grammatical label prefix, or None."""
    return next((pos for prefix, pos in LABEL_POS if label.startswith(prefix)), None)


def is_proper_name(label, spelling, gloss):
    """A proper name by its label, or by a capitalised head glossed as a place or a given name."""
    return label.startswith(("прізвище", "власна назва")) or (
        spelling[:1].isupper() and any(marker in gloss for marker in PROPER_GLOSS_MARKERS))


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

    proper = is_proper_name(label, spelling, gloss)

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
        pos = label_pos(label)
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


def holding_obligations(manifest, registry, sources_conn):
    """Pilot cards that need an `unsplit` holding sense: {card_id: unit locators that cannot be aligned}.

    Reads the frozen pilot entries' C3 relation units from the held sources (read-only) and applies the assembler's
    own placement check (`word_card_assembly.needs_holding_sense`) to each card's SEED senses, so allocation and
    build cannot disagree about which cards need one.
    """
    import tempfile

    from scripts.atlas import word_card_assembly as assembly
    from scripts.atlas import word_card_sources as src

    build = BUILD_PREFIX + manifest["manifest_sha256"]
    seeded = {e["to"][0] for e in registry["events"] if e["kind"] == "sense_mint" and e["build_id"] == build}
    records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
    entry_ids = sorted(r["raw_row"]["id"] for r in records.values() if r["table"] == "ulif_dictua_entries")
    with tempfile.TemporaryDirectory(prefix="pilot-holding-") as scratch:
        extract = Path(scratch) / "extract.sqlite"
        assembly.require_host_only([extract])
        src.write_extract(sources_conn, entry_ids, extract)
        units = assembly.wp3_card_units(extract, set(entry_ids))
    needs = {}
    for unit in manifest["selection"]["units"]:
        if unit["entry_type"] != "lexeme_candidate":
            continue
        entry = next(e for e in registry["entries"]
                     if unit["unit_key"] in foundation.source_keys(e) and e["created_in_build"] == build)
        seeds_only = [s for s in entry["senses"] if s["sense_id"] in seeded]
        by_kind = assembly.relation_units(units, records[unit["anchor_locator"]]["raw_row"]["id"])
        if assembly.needs_holding_sense(seeds_only, by_kind):
            needs[entry["card_id"]] = sorted(
                {f"ulif:section:{u.source_key.rpartition('=')[2]}" for us in by_kind.values() for u in us
                 if u.candidate.outcome == "accepted" and assembly.aligned_sense(seeds_only, us) is None})
    return needs


def holding_evidence(unit, anchor, held_units, rules_version, normaliser_version):
    return {"source_partition": unit["unit_key"], "anchor_locator": anchor["locator"],
            "source_unit": anchor["locator"] + "#unsplit", "source_row_sha256": anchor["content_sha256"],
            "state": "unsplit", "literal_gloss_unit": None, "basis": HOLDING_BASIS, "held_units": held_units,
            "rules_version": rules_version, "normaliser_version": normaliser_version}


def append_holding(registry, manifest, needs, mint, event):
    """Append one `unsplit` sense per obligation that has none yet; every existing identity and event is kept."""
    holding_build = HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
    records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
    by_card = {e["card_id"]: e for e in registry["entries"]}
    appended = 0
    for unit in manifest["selection"]["units"]:
        entry = next((by_card[c] for c in needs if unit["unit_key"] in foundation.source_keys(by_card[c])), None)
        if entry is None or any(s["state"] == "unsplit" for s in entry["senses"]):
            continue
        sense = {"sense_id": mint("ws_"), "order": len(entry["senses"]) + 1, "state": "unsplit"}
        entry["senses"].append(sense)
        event("sense_mint", sense["sense_id"], holding_evidence(
            unit, records[unit["anchor_locator"]], needs[entry["card_id"]], manifest.get("rules_version"),
            manifest.get("normaliser_version")), holding_build)
        appended += 1
    return appended


def reviewed_allocation(registry, manifest):
    """The reviewed v2 allocation inside `registry`: the registry without the holding epoch, proved by its digest."""
    holding_build = HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
    minted = {e["to"][0] for e in registry["events"] if e["build_id"] == holding_build}
    allocation = copy.deepcopy(registry)
    allocation["events"] = [e for e in registry["events"] if e["build_id"] != holding_build]
    for entry in allocation["entries"]:
        entry["senses"] = [s for s in entry["senses"] if s["sense_id"] not in minted]
    allocation["registry_version"] -= 1 if minted else 0
    assert foundation.digest(allocation) == PILOT_ALLOCATION_DIGEST, \
        "The registry is not the reviewed pilot allocation plus appended holding senses"
    return allocation


def holding_check(registry, manifest, needs, allocation):
    """Registry = the reviewed pilot allocation plus exactly the holding senses `needs` names, nothing else.

    `allocation` is that reviewed registry (v2). Its events are a strict prefix, its source records are unchanged,
    every entry is unchanged except for at most one appended `unsplit` sense, and the version grows by one only
    when holding senses exist. Returns the number of appended holding senses.
    """
    holding_build = HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
    records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
    count = len(allocation["events"])
    assert registry["events"][:count] == allocation["events"], "Reviewed allocation history changed"
    assert registry["source_records"] == allocation["source_records"], "Source records changed"
    assert len(registry["entries"]) == len(allocation["entries"]), "Entries added or removed"
    appended = registry["events"][count:]
    assert all(e["kind"] == "sense_mint" and e["build_id"] == holding_build for e in appended), \
        "Only holding-sense mints may follow the reviewed allocation"
    minted = {e["to"][0]: json.loads(e["evidence"]) for e in appended}
    seen = set()
    for old, new in zip(allocation["entries"], registry["entries"], strict=True):
        assert {k: v for k, v in new.items() if k != "senses"} == {k: v for k, v in old.items() if k != "senses"}
        assert new["senses"][:len(old["senses"])] == old["senses"], "An existing sense changed"
        extra = new["senses"][len(old["senses"]):]
        assert len(extra) == (1 if new["card_id"] in needs else 0), "Holding senses differ from the obligations"
        for sense in extra:
            assert sense["state"] == "unsplit" and sense["order"] == len(old["senses"]) + 1
            evidence = minted[sense["sense_id"]]
            unit = next(u for u in manifest["selection"]["units"] if u["unit_key"] in foundation.source_keys(new))
            assert evidence == holding_evidence(unit, records[unit["anchor_locator"]], needs[new["card_id"]],
                                                manifest.get("rules_version"), manifest.get("normaliser_version"))
            seen.add(sense["sense_id"])
    assert seen == set(minted), "Holding mint without its appended sense"
    assert registry["registry_version"] == allocation["registry_version"] + (1 if minted else 0)
    return len(minted)


def require_writable(path):
    """Registry and audit writes stay out of the protected primary checkout (worktree_containment)."""
    decision = containment.evaluate_write(path)
    assert decision.allowed, f"Refused write into the primary checkout ({decision.reason})"


def git_registry(commit):
    return json.loads(subprocess.check_output(
        ["git", "show", commit + ":registry/atlas/identity/registry.json"],
        timeout=30,
    ))


def run(apply, append=False, sources_db=None, vesum_db=None):
    assert not (apply and append), "--apply and --append-holding are separate registry steps"
    manifest = foundation.load(MANIFEST)
    foundation.manifest_check(manifest, MANIFEST)
    registry = foundation.load(REGISTRY)
    # The existing allocation is never regenerated: --apply only creates a pilot allocation where none exists.
    assert not (apply and any(e["created_in_build"] == BUILD_PREFIX + manifest["manifest_sha256"]
                              for e in registry["entries"])), \
        "The pilot allocation exists; --apply would replace its identities. Use --append-holding for holding senses"
    before = git_registry(BASELINE)
    foundation.allocation_check(manifest, registry)
    records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
    build = BUILD_PREFIX + manifest["manifest_sha256"]
    holding_build = HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
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

    def event(kind, target, evidence, build_id=build):
        nonlocal number
        number += 1
        registry["events"].append({"event_id": f"ie_{number:04d}", "kind": kind,
            "build_id": build_id, "cards" if kind == "mint" else "to": [target],
            "evidence": foundation.canonical(evidence).decode()})

    with ExitStack() as stack:
        sources = foundation.readonly(stack, sources_db or resolve_store("sources").path)
        vesum = foundation.readonly(stack, vesum_db or resolve_store("vesum").path)
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

        needs = holding_obligations(manifest, registry, sources)
        appended = 0
        if append:
            allocation = reviewed_allocation(registry, manifest)
            appended = append_holding(registry, manifest, needs, mint, event)
            if appended:
                registry["registry_version"] = allocation["registry_version"] + 1
        holding_minted = {e["to"][0] for e in registry["events"] if e["build_id"] == holding_build}
        holding = holding_check(registry, manifest, needs, reviewed_allocation(registry, manifest)) \
            if holding_minted else 0

        assert registry["entries"][:len(before["entries"])] == before["entries"]
        assert registry["events"][:len(before["events"])] == before["events"]
        assert registry["source_records"] == before["source_records"]
        assert registry["registry_version"] == before["registry_version"] + 1 + (1 if holding_minted else 0)
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
            seeded = entry["senses"][:len(expected)]
            assert {s["sense_id"] for s in entry["senses"][len(expected):]} <= holding_minted, "Unexplained sense"
            for order, (sense, (state, source_unit, literal)) in enumerate(zip(seeded, expected, strict=True), 1):
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
                "card_id": entry["card_id"], "card_kind": kind, "senses": seeded,
                "source_record_ids": source_ids, "supplementary_correspondence": "unresolved"})
        assert len(pilot_entries) == len(mapping) == 150
        assert len({m["card_id"] for m in mapping}) == 150
        sense_count = sum(len(m["senses"]) for m in mapping)
        assert len(pilot_events) == 150 + sense_count
        if apply or appended:
            require_writable(REGISTRY)
            foundation.write(REGISTRY, registry)
        assert foundation.load(REGISTRY) == registry
        report = {"baseline_sha": BASELINE, "manifest_sha256": manifest["manifest_sha256"],
            "registry_file_sha256": foundation.file_digest(REGISTRY), "registry_version": registry["registry_version"],
            "pilot_units": 150, "allocated_pilot_cards": 150,
            "pilot_card_kinds": dict(Counter(m["card_kind"] for m in mapping)),
            "allocated_pilot_senses": sense_count, "holding_senses": holding, "holding_appended_now": appended,
            "holding_obligations": len(needs), "holding_obligations_unmet": len(set(needs) - {
                e["card_id"] for e in registry["entries"] if any(s["sense_id"] in holding_minted for s in e["senses"])}),
            "sense_states": dict(Counter(s["state"] for m in mapping for s in m["senses"])),
            "preserved_legacy_cards": len(before["entries"]), "preserved_events": len(before["events"]),
            "preserved_source_records": len(before["source_records"]), "source_rows_checked_readonly": source_rows_checked,
            "unallocated_pilot_units": 0, "shared_pilot_card_ids": 0,
            "independent_heldout_proof": "not performed; author allocation audit only",
            "residual_owner": "open-model-data driver",
            "residual": "cross-family exact-head review and landing; lexical correspondence, assembly and certification remain separate"}
        for name, value in (("9402-allocation-audit.json", report),
                            ("9402-unit-identities.json", {"build_id": build, "units": mapping})):
            require_writable(ROOT / "batch_state/reports" / name)
            foundation.write(ROOT / "batch_state/reports" / name, value)
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="create the pilot allocation where none exists")
    mode.add_argument("--append-holding", action="store_true",
                      help="append the unsplit holding senses the build needs (append-only, idempotent)")
    parser.add_argument("--sources-db", type=Path, help="sources database (default: the primary store)")
    parser.add_argument("--vesum-db", type=Path, help="vesum database (default: the primary store)")
    arguments = parser.parse_args()
    run(arguments.apply, arguments.append_holding, arguments.sources_db, arguments.vesum_db)
