"""Assemble an approved fixed A1 receipt batch, with complete row and field accounting.

Use for #11943 slices 2–4, never for certification, publication or expanding their denominators.
"""

import argparse
import copy
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_resolver as resolver
from scripts.atlas import word_card_sources as source_rules
from scripts.atlas.a1_card_receipts import (
    Refusal,
    canonical,
    digest,
    make_receipt,
    require_lemma_call,
    selected_rows,
    validate_allocation,
    verify_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "registry/atlas/a1-v1-slice2.json"
COMPANION = "registry/atlas/identity/a1-v1-slice2.json"
MANIFEST_SHA256 = "0a1f990cede86d08e3683851883908514296d33a02763e83f5f0852808b7eebc"
VERSION = "a1-slice2-v1"
CARD_FIELDS = (*assembly.CARD_FIELDS, "mwe_form", "mwe_frame")
SENSE_FIELDS = assembly.SENSE_FIELDS
STRESS_ORDER = ("ulif", "sum20", "vts_busel_slovnyk_me")


@dataclass(frozen=True)
class BatchContext:
    """Bind a separately approved batch to its fixed inputs and identities."""

    version: str
    manifest_ref: str
    companion_ref: str
    row_card_ids: Mapping[str, str]
    identity_methods: Mapping[str, str]
    validate_inputs: Callable[[dict, dict, dict, dict, dict, dict], tuple[dict, list[dict]]]
    row_ledger: Mapping[str, Mapping] | None = None
    residual_owners: Mapping[str, str] | None = None


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def selected_assertions(resolution):
    value = resolution.get("selected")
    return [value] if isinstance(value, str) else value or []


def load(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate_json_key")
            out[key] = value
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Refusal("nonfinite_json")))


def choose_stress(attempts):
    """Return the first authority's explicit reading; uncertainty cannot be bypassed."""
    require(len({a["source_id"] for a in attempts}) == len(attempts), "duplicate_stress_authority")
    by_source = {a["source_id"]: a for a in attempts}
    for source in STRESS_ORDER:
        require(source in by_source, "missing_stress_attempt")
        attempt = by_source[source]
        if attempt["state"] in {"ambiguous", "conflict"}:
            return None, "higher_priority_stress_" + attempt["state"]
        if attempt["state"] == "supported":
            return attempt["claim"], None
        require(attempt["state"] in {"not_found", "unavailable", "unmarked"}, "invalid_stress_attempt")
    return None, "no_explicit_stress_receipt"


def _inputs(inventory, base, companion, manifest, sources, pins):
    require(digest(inventory) == manifest["inventory_sha256"], "inventory_digest_mismatch")
    require(digest(sources) == manifest["sources_sha256"], "source_snapshot_drift")
    require(sources["inventory_sha256"] == digest(inventory), "source_inventory_mismatch")
    effective = validate_allocation(base, companion, pins)
    rows = selected_rows(inventory)
    require(len(inventory["rows"]) == manifest["denominator"]["all_rows"] == 2144, "inventory_row_count")
    require(len(rows) == manifest["denominator"]["selected_rows"] == 19, "selected_row_count")
    card_ids = sorted({r["mapping"]["pilot"]["card_id"] for r in rows})
    require(card_ids == manifest["card_ids"] and len(card_ids) == 11, "selected_card_count")
    for record in sources["records"].values():
        call = sources["calls"][record["call_key"]]
        require(digest(call["response"]) == record["response_sha256"], "tool_response_digest_mismatch")
        require(call["tool"] == record["tool"] and call["arguments"] == record["arguments"], "tool_call_mismatch")
        if record["source_id"] == "sum20_slovnyk_mirror":
            require(record.get("source_role") in {"mirror", "mirror_only", "disagrees", "official_unavailable"},
                    "mirror_role_invalid")
    return effective, rows


def _receipt_for(claim, records):
    record = records[claim["record_key"]]
    return make_receipt(claim["record_key"], record, claim["pointer"], claim["span"],
                        claim["entry_id"], claim.get("source_sense_key"))


def _supporting_receipts(claim, records):
    return [make_receipt(claim["record_key"], records[claim["record_key"]], item["pointer"], item["span"],
                         claim["entry_id"], claim.get("source_sense_key"))
            for item in claim.get("supporting_spans", [])]


def _lexeme(claim, receipt, record, lemma):
    if record["source_id"] not in {"balla", "textbooks"}:
        require(claim["record_key"].rsplit(":", 1)[-1] == lemma, "record_lemma_mismatch")
        require_lemma_call(record, lemma)
    if record["source_id"] == "vesum":
        for item in [claim, *claim.get("alternative_forms", []), *claim.get("supporting_spans", [])]:
            match = re.match(r"/clean_analyses/(0|[1-9][0-9]*)/", item["pointer"])
            require(match is not None, "form_pointer_not_analysis")
            analysis = record["payload"]["clean_analyses"][int(match[1])]
            require(analysis["entry_id"] == claim["entry_id"], "form_entry_mismatch")
    if claim["field"] == "stress":
        require(source_rules.norm_v1(receipt["quotation"].replace(source_rules.ACUTE, "")) == source_rules.norm_v1(lemma),
                "stress_lemma_mismatch")


def _definition_scopes(manifest):
    spans = defaultdict(list)
    for claim in manifest["claims"]:
        if claim["field"] == "definition_uk":
            scope = manifest["scopes"][claim["scope_key"]]
            require(scope["span"] == claim["span"], "outside_sense_span")
            spans[claim["record_key"], claim["pointer"]].append(claim["span"])
    for group in spans.values():
        ordered = sorted(group)
        require(all(left[1] <= right[0] for left, right in pairwise(ordered)),
                "overlapping_definition_spans")


def _claim_value(claim, receipt, record):
    value = receipt["quotation"]
    if claim["field"] == "register" and claim.get("segments"):
        values = [value]
        for segment in claim["segments"]:
            values.append(make_receipt(claim["record_key"], record, segment["pointer"], segment["span"],
                                       claim["entry_id"], claim["source_sense_key"])["quotation"])
        return values, "|".join(source_rules.norm_v1(v) for v in values)
    if claim["field"] == "paradigm":
        require(record["source_id"] == "vesum", "form_requires_vesum")
        forms = []
        for item in [claim, *claim.get("alternative_forms", [])]:
            match = re.fullmatch(r"/clean_analyses/(\d+)/word_form", item["pointer"])
            require(match is not None, "form_pointer_not_analysis")
            analysis = record["payload"]["clean_analyses"][int(match[1])]
            require(analysis["entry_id"] == claim["entry_id"], "form_entry_mismatch")
            require(analysis["tags"] == claim["slot"], "form_slot_mismatch")
            require(item["span"] == [0, len(analysis["word_form"])], "partial_form")
            require(source_rules.ACUTE not in analysis["word_form"] or claim.get("stress_receipt"),
                    "accented_form_requires_stress")
            forms.append(analysis["word_form"])
        require(len(forms) == len(set(forms)), "duplicate_slot_form")
        return {"slot": claim["slot"], "forms": forms, "entry_id": claim["entry_id"],
                "tags": claim["slot"]}, claim["slot"] + "=" + "|".join(sorted(source_rules.norm_v1(v) for v in forms))
    if claim["field"] == "stress":
        require(record["source_id"] in STRESS_ORDER, "invalid_stress_source")
        require(source_rules.ACUTE in value, "stress_not_explicit")
        readings = source_rules.stress_forms(value)
        return readings if len(readings) > 1 else readings[0], "|".join(source_rules.norm_v1(v) for v in readings)
    return value, source_rules.norm_v1(value)


def _form_stress(claim, receipt, sources, manifest):
    if claim["field"] != "paradigm" or source_rules.ACUTE not in receipt["quotation"]:
        return
    stress, _ = choose_stress(manifest["stress_attempts"][claim["card_id"]])
    require(stress is not None, "accented_form_requires_stress")
    evidence = _receipt_for(stress, sources["records"])
    require(claim.get("stress_receipt") == evidence["receipt_id"]
            and evidence["entry_id"] == claim["entry_id"]
            and source_rules.norm_v1(evidence["quotation"]) == source_rules.norm_v1(receipt["quotation"]),
            "accented_form_requires_stress")


def _scope(claim, manifest, receipt, *, batch=None, record=None):
    field = claim["field"]
    if field in {"gloss_en", "english_gloss"}:
        require(claim.get("translation_direction") == "en-uk" and bool(claim.get("usage_pair")),
                "bilingual_direction_or_pair_unresolved")
        pair = claim["usage_pair"]
        supports = claim.get("supporting_spans", [])
        require(isinstance(pair, dict) and pair in supports, "bilingual_pair_not_receipted")
        hit = re.fullmatch(r"(/hits/(?:0|[1-9][0-9]*))/word", claim["pointer"])
        require(hit is not None and all(s["pointer"] == hit[1] + "/definition" for s in supports),
                "bilingual_pair_outside_hit")
    if field in {"definition_uk", "register", "sense_label", "examples", "gloss_en", "synonyms", "antonyms", "collocations"}:
        scope = manifest["scopes"].get(claim.get("scope_key"))
        require(scope is not None, "sense_scope_missing")
        require(scope["record_key"] == claim["record_key"]
                and scope["source_sense_key"] == claim["source_sense_key"], "sense_scope_mismatch")
        require(scope["pointer"] == claim["pointer"], "scope_pointer_mismatch")
        a, b = receipt["span"]
        if field == "register" and "label_spans" in scope:
            require(all({"pointer": item["pointer"], "span": item["span"]} in scope["label_spans"]
                        for item in [claim, *claim.get("segments", [])]), "outside_label_span")
        else:
            require(scope["span"][0] <= a < b <= scope["span"][1], "outside_sense_span")
        require(scope["card_id"] == claim["card_id"] and scope["sense_id"] == claim["sense_id"], "scope_subject_mismatch")
    if field == "definition_uk":
        if receipt["source_id"] == "ulif":
            require(batch is not None and batch.version in {"a1-slice3-v1", "a1-slice4-v1"}, "meaning_source_invalid")
            require(record is not None and receipt["payload_pointer"] == "/sense_gloss"
                    and isinstance(record["payload"].get("sense_gloss"), str)
                    and receipt["span"] == [0, len(record["payload"]["sense_gloss"])]
                    and receipt["quotation"] == record["payload"]["sense_gloss"], "ulif_definition_not_exact")
        else:
            require(receipt["source_id"] in {"sum20", "sum20_slovnyk_mirror", "vts_busel_slovnyk_me"}, "meaning_source_invalid")
        require("Джерело:" not in receipt["quotation"] and "Значення в інших" not in receipt["quotation"], "dictionary_footer")


def build(inventory, base, companion, manifest, sources, pins, register, *, batch=None):
    """Pure assembly from independently frozen inputs; identity allocation is never performed here."""
    validate_inputs = _inputs if batch is None else batch.validate_inputs
    effective, selected = validate_inputs(inventory, base, companion, manifest, sources, pins)
    version = VERSION if batch is None else batch.version
    manifest_ref = MANIFEST if batch is None else batch.manifest_ref
    companion_ref = COMPANION if batch is None else batch.companion_ref
    batch_name = version.removeprefix("a1-").removesuffix("-v1")
    row_card_ids = ({r["id"]: r["mapping"]["pilot"]["card_id"] for r in selected}
                    if batch is None else batch.row_card_ids)
    _definition_scopes(manifest)
    records = sources["records"]
    entry_by_card = {row_card_ids[r["id"]]: r["mapping"]["entry_id"] for r in selected}
    lemma_by_card = {row_card_ids[r["id"]]: r["mapping"]["lemma"] for r in selected}
    row_ids = defaultdict(list)
    for row in selected:
        row_ids[row_card_ids[row["id"]]].append(row["id"])
    allocated = {e["card_id"]: e for e in effective["entries"]}
    identity_methods = ({row_card_ids[r["id"]]: next(c["match"]["method"] for c in r["mapping"]["pilot"]["candidates"]
                        if c["card_id"] == row_card_ids[r["id"]]) for r in selected}
                        if batch is None else batch.identity_methods)
    source_ids = {(r["source_id"], c["snapshot_id"], c["locator"]): r for r in effective["source_records"]
                  for c in r["correspondence"] if c["status"] == "unique"}
    register_sources = {s["id"]: s for s in register["sources"]}
    cards, receipts, assertion_receipts, pending = {}, {}, {}, []
    for card_id in manifest["card_ids"]:
        entry = allocated[card_id]
        senses = []
        additions = {a["sense"]["sense_id"]: json.loads(a["event"]["evidence"]) for a in companion["senses"]
                     if a["card_id"] == card_id}
        for sense in entry["senses"]:
            evidence = additions.get(sense["sense_id"])
            senses.append({**sense, "merged_into": None, "fields": {}, "sense_map": [] if evidence is None else [{
                "source_id": evidence["source_id"], "source_sense_key": evidence["source_sense_key"],
                "mapped_by": version}], **({"seeded_from": evidence["source_id"]} if evidence else {})})
        cards[card_id] = {
            "schema_version": "1", "card_id": card_id, "card_kind": entry["card_kind"], "state": "active",
            "merged_into": None, "split_into": None, "key_at_creation": copy.deepcopy(entry["key_at_creation"]),
            "identity": {"confidence": "high", "method": identity_methods[card_id],
                         "decided_by": "rules:" + version, "source_keys": copy.deepcopy(entry["key_at_creation"]["source_keys"])},
            "senses": senses, "links": [], "fields": {}, "assertions": [], "overlay_applied": [],
            "quality": {"identity_confidence": "high", "extraction_confidence_min": "high",
                        "linguistic_review": {"status": "none"}, "practice_eligibility": []}, "build": {},
        }
    claims = [c for c in manifest["claims"] if c["field"] != "stress"]
    stress_reasons = {}
    for card_id in manifest["card_ids"]:
        claim, reason = choose_stress(manifest["stress_attempts"][card_id])
        if claim:
            claims.append(claim)
        else:
            stress_reasons[card_id] = reason
    for claim in claims:
        card_id = claim["card_id"]
        require(card_id in cards and claim["entry_id"] == entry_by_card[card_id], "claim_lexeme_mismatch")
        subject_id = claim.get("sense_id", card_id)
        require(subject_id == card_id or subject_id in {s["sense_id"] for s in cards[card_id]["senses"]}, "unallocated_sense")
        record = records[claim["record_key"]]
        receipt = _receipt_for(claim, records)
        _lexeme(claim, receipt, record, lemma_by_card[card_id])
        _scope(claim, manifest, receipt, batch=batch, record=record)
        _form_stress(claim, receipt, sources, manifest)
        if claim["field"] == "examples":
            approval = manifest["example_approvals"].get(receipt["receipt_id"])
            if not approval:
                pending.append({"card_id": card_id, "sense_id": subject_id, "field": "examples",
                                "receipt": receipt, "reason": "independent_a1_review_pending"})
                continue
            require(approval["receipt_sha256"] == digest(receipt) and approval["entry_id"] == claim["entry_id"]
                    and approval["sense_id"] == subject_id and approval["reviewer_family"] == "google"
                    and approval["verdict"] == "APPROVE", "example_review_binding_mismatch")
        value, norm = _claim_value(claim, receipt, record)
        source = record["source_id"]
        require(source in register_sources, "unregistered_source")
        group, tier = assembly.LINEAGE.get(source, ("G-" + source + "?", 2))
        sr = source_ids.get((source, record["snapshot_id"], record["locator"]))
        require(sr is not None, "source_record_unallocated")
        subject = {"kind": "card" if subject_id == card_id else "sense", "id": subject_id}
        assertion_id = resolver.aid(source, record["snapshot_id"], receipt["locator"] + receipt["payload_pointer"]
                                    + ":" + ":".join(map(str, receipt["span"])), subject, claim["field"], norm, version)
        assertion = {
            "assertion_id": assertion_id, "subject": subject, "field": claim["field"], "value": value,
            "value_norm": norm, "source_id": source, "snapshot_id": record["snapshot_id"],
            "locator": receipt["locator"] + receipt["payload_pointer"] + ":" + ":".join(map(str, receipt["span"])),
            "extraction_version": version, "extraction_confidence": "high",
            "producer": {"kind": "source_extract", "name": "A1 fixed-batch extractor", "version": version},
            "review": {"status": "none"}, "licence_ref": {"register_source_id": source,
                "register_version": register["schema_version"], "appears_in": register_sources[source].get("appears_in", [])},
            "independence_group": group, "tier": tier, "status": "active",
            "mapping": {"confidence": "high", "basis": "sense" if subject_id != card_id else "entry"},
            "source_record_id": sr["source_record_id"], "source_record_key": sr["aliases"][0]["key"],
        }
        if claim["field"] == "examples":
            assertion["review"] = {"status": "reviewed", "lane": "ukrainian", "record": approval["record"]}
        cards[card_id]["assertions"].append(assertion)
        receipts[receipt["receipt_id"]] = receipt
        supporting = _supporting_receipts(claim, records)
        for support in supporting:
            receipts[support["receipt_id"]] = support
        assertion_receipts[assertion_id] = [receipt["receipt_id"], *(r["receipt_id"] for r in supporting)]
    accounting = []
    build_inputs = {
        "S": {"batch": {"ref": "host-only Sources bundle", "content_sha256": digest(sources)}},
        "V": {"vesum": {"ref": "AC-01 VESUM import", "content_sha256": digest(inventory["sources"]["vesum_pipeline_identity"])}},
        "I": {"allocation": {"ref": companion_ref, "content_sha256": pins["combined_sha256"]}},
        "O": {"batch": {"ref": manifest_ref, "content_sha256": digest(manifest)}},
        "R": {"extractor": {"ref": "scripts/atlas/a1_word_cards.py", "version": version},
              "register": {"ref": "docs/sources/permissions-register.yaml", "content_sha256": digest(register)}}}
    for card_id, card in cards.items():
        card["assertions"].sort(key=lambda a: a["assertion_id"])
        resolver._recompute(card)
        card["build"] = {"build_id": version + "@sha256:" + digest(build_inputs), "rules_version": version,
                         "inputs": copy.deepcopy(build_inputs), "card_version": resolver.card_version(card)}
        subjects = [(card, CARD_FIELDS)] + [(s, SENSE_FIELDS) for s in card["senses"]]
        if batch is not None and not card["senses"]:
            subjects.append((card, SENSE_FIELDS))
        for subject, names in subjects:
            sid = subject.get("sense_id", card_id)
            for field in names:
                resolution = subject["fields"].get(field, {})
                ids = selected_assertions(resolution)
                state = "conflict" if resolution.get("state") == "conflict" else "supported" if ids else "empty"
                reason = None
                if sid == card_id and field in {"mwe_form", "mwe_frame"}:
                    state, reason = "not_applicable", "lexeme_not_mwe"
                elif sid == card_id and field == "aspect" and card["key_at_creation"]["pos"] != "verb":
                    state, reason = "not_applicable", "nonverb_has_no_aspect"
                elif sid == card_id and field == "gender" and card["key_at_creation"]["pos"] not in {"noun", "adj"}:
                    state, reason = "not_applicable", "no_lexical_gender_for_this_pos"
                elif not ids:
                    reason = stress_reasons.get(card_id) if field == "stress" else None
                    reason = reason or manifest["field_residuals"].get(f"{card_id}/{sid}/{field}",
                        manifest["field_residuals"].get(field, "source_sense_claim_unresolved"))
                owners = batch.residual_owners or {} if batch is not None else {}
                owner = owners.get(f"{card_id}/{sid}/{field}", owners.get(field, "Atlas coordinator"))
                accounting.append({"inventory_row_ids": row_ids[card_id], "card_id": card_id,
                    "card_version": card["build"]["card_version"], "sense_id": None if sid == card_id else sid,
                    "field": field, "state": state, "assertion_ids": ids,
                    "receipt_ids": sorted({rid for aid in ids for rid in assertion_receipts[aid]}),
                    "reason": reason, "dependency": None if state == "supported" else
                    manifest["field_dependencies"].get(field, "exact source claim and reviewed sense correspondence"),
                    "owner": None if state == "supported" else owner})
    selected_ids = {r["id"] for r in selected}
    previous_ids = {r["id"] for r in selected_rows(inventory)} if batch is not None else set()
    rows = [{"inventory_row_id": r["id"], "mapping": copy.deepcopy(r["mapping"]),
             "state": "card_produced" if r["id"] in selected_ids else
             "delivered_slice2" if r["id"] in previous_ids else "deferred_outside_" + batch_name,
             "card_id": row_card_ids[r["id"]] if r["id"] in selected_ids else
             r["mapping"]["pilot"]["card_id"] if r["id"] in previous_ids else None,
             "owner": "Atlas coordinator"} for r in inventory["rows"]]
    if batch is not None and batch.row_ledger is not None:
        for row in rows:
            if row["inventory_row_id"] not in selected_ids:
                row.update(batch.row_ledger[row["inventory_row_id"]])
    result = {"schema_version": "atlas-" + version.removesuffix("-v1") + "-build.v1", "cards": list(cards.values()),
              "receipts": list(receipts.values()), "assertion_receipts": assertion_receipts,
              "accounting": accounting, "rows": rows, "pending_examples": pending,
              "held_units": manifest["held_units"], "inputs_sha256": digest(build_inputs)}
    verify(result, sources, manifest, batch=batch)
    return result


def verify(result, sources, manifest, *, batch=None):
    """Check delivered bytes against receipts and conservation, without rebuilding cards."""
    _definition_scopes(manifest)
    version = VERSION if batch is None else batch.version
    selected_count = 19 if batch is None else len(batch.row_card_ids)
    require(len(result["rows"]) == 2144 and len({r["inventory_row_id"] for r in result["rows"]}) == 2144, "row_conservation")
    require(sum(r["state"] == "card_produced" for r in result["rows"]) == selected_count, "row_selection_mismatch")
    require(sorted(c["card_id"] for c in result["cards"]) == manifest["card_ids"], "card_conservation")
    receipts = {r["receipt_id"]: r for r in result["receipts"]}
    accounts = {(r["card_id"], r["sense_id"], r["field"]): r for r in result["accounting"]}
    require(len(accounts) == len(result["accounting"]), "duplicate_field_accounting")
    claims = [c for c in manifest["claims"] if c["field"] != "stress"]
    for attempts in manifest["stress_attempts"].values():
        claim, _ = choose_stress(attempts)
        if claim:
            claims.append(claim)
    expected, expected_pending = {}, []
    lemmas = {c["card_id"]: c["key_at_creation"]["spelling"] for c in result["cards"]}
    for claim in claims:
        receipt = _receipt_for(claim, sources["records"])
        _lexeme(claim, receipt, sources["records"][claim["record_key"]], lemmas[claim["card_id"]])
        _scope(claim, manifest, receipt, batch=batch, record=sources["records"][claim["record_key"]])
        _form_stress(claim, receipt, sources, manifest)
        if claim["field"] == "examples" and receipt["receipt_id"] not in manifest["example_approvals"]:
            expected_pending.append(receipt["receipt_id"])
            continue
        value, norm = _claim_value(claim, receipt, sources["records"][claim["record_key"]])
        subject = {"kind": "sense" if "sense_id" in claim else "card", "id": claim.get("sense_id", claim["card_id"])}
        locator = receipt["locator"] + receipt["payload_pointer"] + ":" + ":".join(map(str, receipt["span"]))
        aid = resolver.aid(receipt["source_id"], receipt["snapshot_id"], locator, subject, claim["field"], norm, version)
        require(aid not in expected, "duplicate_claim")
        expected[aid] = (claim, receipt, value, norm, subject, locator)
    require(sorted(r["receipt"]["receipt_id"] for r in result["pending_examples"]) == sorted(expected_pending),
            "pending_example_mismatch")
    observed = set()
    for card in result["cards"]:
        require(card["build"]["card_version"] == resolver.card_version(card), "card_version_mismatch")
        for assertion in card["assertions"]:
            aid = assertion["assertion_id"]
            require(aid in expected and aid not in observed, "unexpected_or_duplicate_assertion")
            observed.add(aid)
            claim, expected_receipt, value, norm, subject, locator = expected[aid]
            require(claim["card_id"] == card["card_id"] and assertion["subject"] == subject
                    and assertion["field"] == claim["field"], "assertion_subject_mismatch")
            require(assertion["value"] == value and assertion["value_norm"] == norm,
                    "assertion_value_mismatch")
            require(assertion["locator"] == locator, "assertion_locator_mismatch")
            require(assertion["source_record_id"] == manifest["source_record_ids"][claim["record_key"]],
                    "assertion_source_record_mismatch")
            ids = result["assertion_receipts"].get(assertion["assertion_id"])
            require(ids == [expected_receipt["receipt_id"],
                            *(r["receipt_id"] for r in _supporting_receipts(claim, sources["records"]))],
                    "assertion_receipt_missing")
            for rid in ids:
                require(rid in receipts, "receipt_missing")
                receipt = receipts[rid]
                verify_receipt(receipt, sources["records"], claim["entry_id"], claim.get("source_sense_key"))
                require(assertion["source_id"] == receipt["source_id"]
                        and assertion["snapshot_id"] == receipt["snapshot_id"], "assertion_source_mismatch")
        projected = copy.deepcopy(card)
        resolver._recompute(projected)
        require(card["fields"] == projected["fields"]
                and all(a["fields"] == b["fields"] for a, b in zip(card["senses"], projected["senses"], strict=True)),
                "field_resolution_mismatch")
        subjects = [(card, CARD_FIELDS)] + [(s, SENSE_FIELDS) for s in card["senses"]]
        if batch is not None and not card["senses"]:
            subjects.append((card, SENSE_FIELDS))
        for subject, fields in subjects:
            for field in fields:
                row = accounts.get((card["card_id"], subject.get("sense_id"), field))
                require(row is not None, "field_accounting_missing")
                selected = selected_assertions(subject["fields"].get(field, {}))
                require(row["assertion_ids"] == selected, "field_accounting_mismatch")
                if row["state"] in {"empty", "conflict"}:
                    require(not selected and all(row[k] for k in ("reason", "dependency", "owner")), "residual_incomplete")
    require(observed == set(expected), "missing_assertion")
    by_field = defaultdict(set)
    for card in result["cards"]:
        for assertion in card["assertions"]:
            by_field[assertion["field"]].update(result["assertion_receipts"][assertion["assertion_id"]])
    return {"cards": len(result["cards"]), "rows": len(result["rows"]), "receipts": len(receipts),
            "fields": dict(Counter(r["state"] for r in result["accounting"])),
            "receipts_per_field": {field: len(by_field[field]) for field in sorted(set(CARD_FIELDS + SENSE_FIELDS))},
            "assertions_per_field": dict(Counter(a["field"] for c in result["cards"] for a in c["assertions"]))}


def complete_chains(result):
    return [card["card_id"] for card in result["cards"]
            if all(selected_assertions(card["fields"].get(f, {})) for f in ("stress", "paradigm"))
            and any(all(selected_assertions(sense["fields"].get(f, {})) for f in ("definition_uk", "examples"))
                    for sense in card["senses"])]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_word_cards --sources batch_state/a1/sources.json --output batch_state/a1/cards.json
  .venv/bin/python -m scripts.atlas.a1_word_cards --sources batch_state/a1/sources.json --output batch_state/a1/cards.json --check
  .venv/bin/python -m scripts.atlas.a1_word_cards --batch slice3 --sources batch_state/a1/slice3-sources.json --output batch_state/a1/slice3-cards.json
Outputs: host-only card/receipt/accounting bundle; no source-store writes, allocation, certification or deploy.
Exit codes: 0 verified output; 1 refused input or evidence; 2 usage error.
Related: #11943, docs/atlas/word-cards/a1-v1-inventory.md
""")
    parser.add_argument("--batch", choices=("slice2", "slice3", "slice4"), default="slice2",
                        help="Approved fixed batch to assemble or check (default: slice2), e.g. slice4")
    parser.add_argument("--sources", type=Path, required=True, help="Frozen host-only Sources bundle, e.g. batch_state/a1/sources.json")
    parser.add_argument("--output", type=Path, required=True, help="Ignored output JSON inside this worktree, e.g. batch_state/a1/cards.json")
    parser.add_argument("--check", action="store_true", help="Verify an existing output without rewriting it (default: off)")
    parser.add_argument("--require-chain", action="store_true",
                        help="Refuse unless an actual card has meaning, stress, VESUM forms and an approved example (default: off)")
    args = parser.parse_args(argv)
    try:
        batch = None
        if args.batch == "slice4":
            from scripts.atlas.a1_slice4_inputs import load_batch

            manifest, inventory, base, companion, batch = load_batch(ROOT)
        elif args.batch == "slice3":
            from scripts.atlas.a1_slice3_inputs import load_batch

            manifest, inventory, base, companion, batch = load_batch(ROOT)
        else:
            manifest = load(ROOT / MANIFEST)
            require(digest(manifest) == MANIFEST_SHA256, "reviewed_manifest_digest_mismatch")
            inventory = load(ROOT / "registry/atlas/a1-v1-inventory.json")
            base = load(ROOT / "registry/atlas/identity/registry.json")
            companion = load(ROOT / COMPANION)
        sources = load(args.sources)
        validate_inputs = _inputs if batch is None else batch.validate_inputs
        effective, _ = validate_inputs(inventory, base, companion, manifest, sources, manifest["allocation_pins"])
        foundation.registry_check(effective)
        assembly.require_host_only([args.output])
        if args.check:
            result = load(args.output)
            rebuilt = build(inventory, base, companion, manifest, sources, manifest["allocation_pins"],
                            foundation.load_register(ROOT / "docs/sources/permissions-register.yaml"), batch=batch)
            require(args.output.read_bytes() == canonical(rebuilt) + b"\n", "delivered_output_mismatch")
        else:
            result = build(inventory, base, companion, manifest, sources, manifest["allocation_pins"],
                           foundation.load_register(ROOT / "docs/sources/permissions-register.yaml"), batch=batch)
        counts = verify(result, sources, manifest, batch=batch)
        for card in result["cards"]:
            foundation.schema(card, "word-card-v1.schema.json")
        counts["complete_chain_cards"] = complete_chains(result)
        require(not args.require_chain or bool(counts["complete_chain_cards"]), "reviewed_full_receipt_chain_pending")
        if not args.check:
            projections = {args.output: result,
                args.output.with_name(args.output.stem + ".cards.json"): result["cards"],
                args.output.with_name(args.output.stem + ".receipts.json"): {
                    "receipts": result["receipts"], "assertion_receipts": result["assertion_receipts"]},
                args.output.with_name(args.output.stem + ".rows.json"): result["rows"],
                args.output.with_name(args.output.stem + ".residuals.json"): {
                    "accounting": result["accounting"], "held_units": result["held_units"],
                    "pending_examples": result["pending_examples"]}}
            assembly.require_host_only(list(projections))
            for path, value in projections.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(canonical(value) + b"\n")
        print(json.dumps(counts, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, foundation.Refusal) as error:
        reason = str(error) if isinstance(error, Refusal) else type(error).__name__
        print("A1 cards refused: " + reason, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
