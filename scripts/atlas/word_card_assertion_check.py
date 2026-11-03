"""Shared code-first decisions over the existing A1 captures and receipts.

An exact extraction is necessary, but does not settle a contextual selection.
The caller supplies the independently pinned manifest and captured source bundle.
"""

import json
import re
import sqlite3
from collections import Counter

from scripts.atlas import word_card_sources as source_rules
from scripts.atlas.a1_card_receipts import Refusal, digest, make_receipt, verify_receipt

VERSION = "word-card-assertion-check.v1"
# Translate card facets to the permissions register's existing capability names.
FACET_CAPABILITIES = {
    "spelling": {"lemma", "headword"}, "pos": {"pos"},
    "grammatical_label": {"morph_tags", "grammatical_label"},
    "gender": {"morph_tags"}, "aspect": {"morph_tags"},
    "paradigm": {"word_forms", "paradigm"},
    "cefr": {"cefr_level"}, "stress": {"stress", "stressed_headword", "headword"},
    "definition_uk": {"definition_text", "meaning", "homonym_sense_gloss"},
    "register": {"meaning", "definition_text"}, "collocations": {"meaning", "definition_text"},
    "gloss_en": {"en_uk_translation"}, "examples": {"example_sentence", "literary_citations"},
    "synonyms": {"synonym_groups"}, "antonyms": {"antonym_pairs"},
    "russification_exposed": {"russification_quote", "russification_pair"},
}
CONTEXT_FIELDS = frozenset({"definition_uk", "register", "collocations", "gloss_en", "examples",
                            "synonyms", "antonyms", "russification_exposed"})
FEATURE_TOKENS = {
    "case": frozenset(source_rules.CASES), "number": frozenset({"s", "p"}),
    "gender": frozenset(source_rules.GENDERS), "person": frozenset(source_rules.PERSONS),
    "tense": frozenset(source_rules.TENSES),
}


def requested_slot_matches(tags, request):
    """Match each requested feature to exactly one token in a verified slot."""
    if not isinstance(tags, str) or not request or set(request) - FEATURE_TOKENS.keys():
        return False
    # Use the existing parser's explicit noun/adjective singular convention.
    tokens = set(source_rules.vesum_slot(tags.split(":"), keep_gender=True) or ())
    return all(isinstance(value, str) and value in FEATURE_TOKENS[feature]
               and tokens.intersection(FEATURE_TOKENS[feature]) == {value}
               for feature, value in request.items())


def canonical_source(source, register):
    """Resolve only exact IDs, names and aliases explicitly in the register."""
    matches = [s for s in register["sources"] if source in
               [s["id"], s.get("name"), *s.get("aliases", [])]]
    return matches[0] if len(matches) == 1 else None


def source_permission(assertion, record, register):
    """Check positive facet permission; contrast evidence never supplies a norm."""
    entry = canonical_source(assertion["source_id"], register)
    if entry is None:
        return "unresolved", "unregistered_source"
    source = canonical_source(record["source_id"], register)
    capabilities = set(entry.get("fields_used", []))
    if capabilities.intersection({"russification_quote", "russification_pair"}) or (
        source and set(source.get("fields_used", [])).intersection({"russification_quote", "russification_pair"})
    ):
        if assertion["field"] != "russification_exposed":
            return "refused", "soviet_normative_as_modern"
        return "unresolved", "historical_contrast_requires_context_review"
    if source != entry:
        return "refused", "assertion_source_mismatch"
    if not capabilities.intersection(FACET_CAPABILITIES.get(assertion["field"], set())):
        return "unresolved", "source_facet_not_permitted"
    role = record.get("source_role")
    if entry["id"] == "sum20_slovnyk_mirror":
        if role not in {"mirror", "mirror_only", "disagrees", "official_unavailable"}:
            return "refused", "mirror_role_invalid"
        if assertion["field"] == "stress":
            return "refused", "mirror_not_normative_stress"
    elif role not in {None, "official", "admitted", "served_dictionary", "dictionary"}:
        return "unresolved", "source_role_not_permitted"
    # An absent role is derived only from a registered, facet-qualified source,
    # never from a source-name substring or an assertion's claimed authority.
    return None


def _response_text(response):
    return "\n".join(item["text"] for item in response.get("content", []) if item["type"] == "text")


def authenticate_record(record, sources):
    """Bind the consumed payload and version to its captured tool response."""
    from scripts.atlas import a1_word_cards as a1

    call = sources["calls"][record["call_key"]]
    a1.require(digest(call["response"]) == record["response_sha256"]
               and call["tool"] == record["tool"] and call["arguments"] == record["arguments"],
               "tool_response_digest_mismatch")
    a1.require(not call["response"].get("isError"), "source_tool_error")
    payload = record["payload"]
    if "canonical_row_witness" in record:
        witness = record["canonical_row_witness"]
        if record["source_id"] == "ulif":
            observed = {**payload, "id": payload["entry_id"],
                        "normalized_query": json.loads(_response_text(call["response"]))["records"][0]["normalized_query"]}
        else:
            observed = payload["hits"][0]
        row = {field: observed[field] for field in witness["raw_row"]}
        a1.require(row == witness["raw_row"] and record["snapshot_id"] == "selected-row@sha256:" + digest(row),
                   "source_version_mismatch")
    else:
        a1.require(record["snapshot_id"].startswith(record["source_id"] + "@sha256:"),
                   "source_version_identity_unavailable")
        a1.require(record["snapshot_id"] == record["source_id"] + "@sha256:" + digest(payload),
                   "source_version_mismatch")
    response = call["response"]
    if response == payload or response.get("structuredContent") == payload:
        return
    source, text = record["source_id"], _response_text(response)
    if payload == {"text": text}:
        return
    if source == "vesum":
        a1.require(json.loads(text.split("- Raw payload: ", 1)[1]) == payload, "payload_outside_response")
    elif source == "ulif":
        entries = json.loads(text)["records"][0]["entries"]
        matches = [e for e in entries if e["entry_id"] == payload["entry_id"]]
        a1.require(len(matches) == 1 and matches[0] == payload, "payload_outside_response")
        a1.require(record["content_sha256"] == payload["content_sha256"]
                   and record["parser_version"] == payload["parser_version"], "source_version_mismatch")
    elif source == "vts_busel_slovnyk_me" and "row" in payload:
        # The earlier captures retain the authenticated full cached witness.
        # Its source digest is distinct from the query-response digest.
        import hashlib

        a1.require(hashlib.sha256(payload["text"].encode()).hexdigest() == record["content_sha256"]
                   == payload["row"]["content_sha256"], "source_body_digest_mismatch")
        a1.require(payload["row"]["dictionary_slug"] == "vts"
                   and record["source_url"] in text, "source_witness_mismatch")
    else:
        # Later batches already have a closed, source-specific reply reader.
        from scripts.atlas.a1_slice5_inputs import response_payload

        a1.require(response_payload(record, call) == payload, "payload_outside_response")


def _stress_decision(card, claim, record, sources, manifest):
    """Derive priority and ULIF identity from the captured body, not state labels."""
    from scripts.atlas import a1_word_cards as a1

    attempts = manifest["stress_attempts"][claim["card_id"]]
    by_source = {attempt["source_id"]: attempt for attempt in attempts}
    for authority in a1.STRESS_ORDER:
        attempt = by_source.get(authority)
        if attempt is None:
            return "unresolved", "missing_stress_attempt"
        if authority == record["source_id"]:
            break
        # A lower authority needs a captured explicit higher-priority outcome.
        call = sources["calls"].get(attempt.get("evidence_call"))
        if call is None:
            return "unresolved", "higher_priority_stress_outcome_missing"
        response = call["response"]
        body = response.get("structuredContent")
        if body is None:
            try:
                body = json.loads(_response_text(response))
            except ValueError:
                return "unresolved", "higher_priority_stress_outcome_ambiguous"
        if response.get("isError") or body.get("status") != "not_found":
            return "unresolved", "higher_priority_stress_outcome_ambiguous"
    else:
        return "refused", "invalid_stress_source"
    if record["source_id"] != "ulif":
        return "unresolved", "stress_fallback_identity_unresolved"
    payload = record["payload"]
    identity = payload.get("identity_from_raw") or {}
    if (payload.get("verified") is not True or payload.get("homonym_checked") != 1
            or identity.get("stored_matches_raw") is not True or identity.get("mismatches")
            or not identity.get("source_page_sha256")
            or identity.get("canonical_headword") != payload.get("canonical_headword")):
        return "unresolved", "stress_entry_homonym_unresolved"
    raw = _raw_ulif_entry(payload)
    if raw is None:
        return "unresolved", "stress_authenticated_raw_body_unavailable"
    if claim["pointer"] == "/canonical_headword":
        if claim["span"] != [0, len(payload["canonical_headword"])]:
            return "refused", "partial_stress_headword"
    else:
        match = re.fullmatch(r"/forms/(\d+)/form_stressed", claim["pointer"])
        if match is None:
            return "unresolved", "stress_variant_unresolved"
        form = payload["forms"][int(match[1])]
        if (not form["is_lemma"] or form["unmapped_labels"] or form["marked_asterisk"]
                or form["source_page_sha256"] != identity["source_page_sha256"]
                or claim["span"] != [0, len(form["form_stressed"])]):
            return "unresolved", "stress_variant_unresolved"
    # A unique source entry is not necessarily the selected VESUM homonym.
    # Reuse the existing paradigm/identity algorithm over the captured bodies.
    call = sources["calls"][record["call_key"]]
    entries = json.loads(_response_text(call["response"]))["records"][0]["entries"]
    vesum = sources["records"].get("vesum:" + card["key_at_creation"]["spelling"])
    if vesum is None:
        return "unresolved", "stress_vesum_identity_missing"
    authenticate_record(vesum, sources)
    homonyms = {}
    for entry in entries:
        parsed = raw if entry["entry_id"] == payload["entry_id"] else _raw_ulif_entry(entry)
        if entry.get("forms_state") != "complete" or parsed is None:
            return "unresolved", "stress_competing_identity_unresolved"
        forms = []
        for index, form in enumerate(parsed["forms"]):
            forms.append({**form, "id": index, "grammatical_tags": json.dumps(form["grammatical_tags"]),
                          "unmapped_labels": json.dumps(form["unmapped_labels"])})
        homonyms[entry["entry_id"]] = {"head": entry["canonical_headword"],
            "paradigm": source_rules.ulif_paradigm(forms,
                pronoun=entry["grammatical_label"].startswith("займенник")),
            "aspect": a1.assembly.parse_aspect(entry["grammatical_label"])}
    candidates = source_rules.vesum_paradigm(vesum["payload"]["clean_analyses"],
        keep_gender=card["key_at_creation"]["pos"] == "adj")
    match = source_rules.match_identity(payload["entry_id"], homonyms, candidates)
    if match["confidence"] != "high" or match["vesum_entry"] != claim["entry_id"]:
        return "unresolved", "stress_entry_correspondence_unresolved"
    return None


def _raw_ulif_entry(entry):
    """Read and hash captured HTML with the existing cache and parser, never a live lookup."""
    from scripts.lexicon import ulif_raw_cache
    from scripts.lexicon.runner.ulif_dictua_parse import parse_ulif_entry

    try:
        reference = entry["raw_response_ref"]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", reference):
            return None
        manifest_body = ulif_raw_cache.get(reference.removeprefix("sha256:"))
        if manifest_body is None:
            return None
        manifest = json.loads(manifest_body)
        page_ref = manifest.get("paradigm")
        if not isinstance(page_ref, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", page_ref):
            return None
        page = ulif_raw_cache.get(page_ref.removeprefix("sha256:"))
        if page is None or page_ref != "sha256:" + entry["identity_from_raw"]["source_page_sha256"]:
            return None
        parsed = parse_ulif_entry(page.decode("utf-8"), homonym_index=entry["homonym_index"])
        if any(parsed[key] != entry[key] for key in ("canonical_headword", "grammatical_label", "sense_gloss")):
            return None
        if [source_rules._comparable(row) for row in parsed["forms"]] != [
            source_rules._comparable(row) for row in entry["forms"]
        ]:
            return None
        return parsed
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
        return None


def check_assertion(card, assertion, claim, sources, manifest, receipts, receipt_ids, *, batch=None, register,
                    expected_entry_id):
    """Return one exact, reproducible disposition without changing any card."""
    from scripts.atlas import a1_word_cards as a1

    decision = {"assertion_id": assertion.get("assertion_id"), "card_id": card["card_id"],
                "field": assertion.get("field"), "status": "unresolved", "reason": "receipt_missing",
                "receipt_ids": list(receipt_ids or []), "extraction": "unresolved", "checker": VERSION}

    def finish(status, reason):
        return {**decision, "status": status, "reason": reason}

    try:
        record = sources["records"][claim["record_key"]]
        permission = source_permission(assertion, record, register)
        if permission:
            return finish(*permission)
        if not receipt_ids:
            return finish("unresolved", "receipt_missing")
        receipt = receipts[receipt_ids[0]]
        for rid in receipt_ids:
            verify_receipt(receipts[rid], sources["records"], claim["entry_id"], claim.get("source_sense_key"))
        a1.require(receipt == a1._receipt_for(claim, sources["records"]), "assertion_receipt_mismatch")
        a1.require(receipt_ids == [receipt["receipt_id"],
                   *(r["receipt_id"] for r in a1._supporting_receipts(claim, sources["records"]))],
                   "assertion_receipt_missing")
        authenticate_record(record, sources)
        lemma = card["key_at_creation"]["spelling"]
        a1._lexeme(claim, receipt, record, lemma)
        a1._scope(claim, manifest, receipt, batch=batch, record=record)
        a1._form_stress(claim, receipt, sources, manifest)
        value, norm = a1._claim_value(claim, receipt, record)
        additional = [make_receipt(claim["record_key"], record, item["pointer"], item["span"],
                                  claim["entry_id"], claim.get("source_sense_key"))
                      for item in [*claim.get("alternative_forms", []), *claim.get("segments", [])]]
        decision["additional_receipts"] = additional
        decision["receipt_ids"] = list(dict.fromkeys([*receipt_ids, *(r["receipt_id"] for r in additional)]))
        subject = {"kind": "sense" if "sense_id" in claim else "card", "id": claim.get("sense_id", card["card_id"])}
        a1.require(claim["card_id"] == card["card_id"] and assertion["subject"] == subject
                   and assertion["field"] == claim["field"], "assertion_subject_mismatch")
        a1.require(assertion["value"] == value and assertion["value_norm"] == norm, "assertion_value_mismatch")
        a1.require(assertion["snapshot_id"] == record["snapshot_id"], "assertion_source_mismatch")
        a1.require(claim["entry_id"] == expected_entry_id, "claim_lexeme_mismatch")
        locator = receipt["locator"] + receipt["payload_pointer"] + ":" + ":".join(map(str, receipt["span"]))
        a1.require(assertion["locator"] == locator, "assertion_locator_mismatch")
        a1.require(assertion["source_record_id"] == manifest["source_record_ids"][claim["record_key"]],
                   "assertion_source_record_mismatch")
        decision["extraction"] = "exact"
        if assertion["field"] in CONTEXT_FIELDS:
            return finish("unresolved", "context_selection_requires_judgment")
        if assertion["field"] == "stress":
            stress = _stress_decision(card, claim, record, sources, manifest)
            if stress:
                return finish(*stress)
        return finish("supported", "exact_source_entry_slot")
    except Refusal as exc:
        if str(exc) == "source_version_identity_unavailable":
            return finish("unresolved", str(exc))
        return finish("refused", str(exc))
    except (KeyError, IndexError, TypeError, AttributeError, ValueError) as exc:
        return finish("unresolved", "missing_or_ambiguous_input:" + type(exc).__name__)


def summarize(decisions):
    """Keep all three dispositions explicit, including zero denominators."""
    counts = Counter(row["status"] for row in decisions)
    return {status: counts[status] for status in ("supported", "unresolved", "refused")}
