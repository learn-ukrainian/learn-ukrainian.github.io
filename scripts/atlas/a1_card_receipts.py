"""Pure receipt binding and fixed-batch append-only allocation checks for #11943."""

import copy
import hashlib
import json
import re

SELECTED_CARD_IDS = frozenset({
    "wc_8mhjfw05sm0t", "wc_ppr39m6qsr4e", "wc_0r1cdw5z36cd", "wc_qpcdgkctp7ne",
    "wc_08svjhdbe0fq", "wc_n1g44brn5vs2", "wc_5b36dst0her6", "wc_6bt62wd6zzzf",
    "wc_da7t5vpprjw3", "wc_vq34ms5wtfev", "wc_5btr8jkdzvd1",
})
_BINDING_FIELDS = (
    "source_id", "snapshot_id", "locator", "source_url", "retrieved_at",
    "content_sha256", "parser_version", "tool", "arguments", "response_sha256",
)


class Refusal(ValueError):
    """A stable refusal reason for an invalid allocation or receipt."""


def _require(condition, reason):
    if not condition:
        raise Refusal(reason)


def canonical(obj) -> bytes:
    """Encode compact, sorted UTF-8 JSON, rejecting nonfinite numbers."""
    try:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise Refusal("invalid_json") from exc


def digest(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def selected_rows(inventory) -> list:
    """Return all resolved pilot-linked lemma occurrences in inventory order."""
    return [row for row in inventory["rows"] if row["mapping"]["kind"] == "lemma"
            and row["mapping"]["resolution"] == "resolved"
            and row["mapping"].get("pilot", {}).get("card_id") is not None]


def _unique(values, reason):
    _require(len(values) == len(set(values)), reason)


def _mint(event, kind, identity):
    _require(event["kind"] == kind and event.get("to") == [identity]
             and not event.get("cards") and not event.get("from")
             and isinstance(event["build_id"], str) and bool(event["build_id"])
             and re.fullmatch(r"ie_[0-9]{4,}", event["event_id"]), "invalid_mint")
    _require(set(event) <= {"event_id", "kind", "build_id", "to", "evidence"}, "invalid_mint")
    try:
        evidence = json.loads(event["evidence"])
    except (TypeError, ValueError) as exc:
        raise Refusal("invalid_mint_evidence") from exc
    _require(isinstance(evidence, dict), "invalid_mint_evidence")
    canonical(evidence)
    return evidence


def _source_records(records):
    locations = []
    for record in records:
        source = record["source_id"]
        _require(isinstance(source, str) and bool(source), "invalid_source_record")
        snapshots = [c["snapshot_id"] for c in record["correspondence"]]
        _unique(snapshots, "duplicate_snapshot_correspondence")
        _unique([canonical(alias) for alias in record["aliases"]], "duplicate_source_alias")
        for correspondence in record["correspondence"]:
            if correspondence["status"] == "unique":
                locations.append((source, correspondence["snapshot_id"], correspondence["locator"]))
    _unique(locations, "duplicate_source_correspondence")


def validate_allocation(base, companion, pins) -> dict:
    """Check an externally pinned union without changing any base allocation."""
    try:
        _require(digest(base) == pins["base_sha256"], "base_digest_mismatch")
        _require(digest(companion) == pins["companion_sha256"], "companion_digest_mismatch")
        _require(companion["schema_version"] == "atlas-a1-slice2-allocation.v1"
                 and companion["base_sha256"] == pins["base_sha256"], "invalid_companion")
        _require(set(companion) == {"schema_version", "base_sha256", "senses", "source_records", "events"},
                 "invalid_companion")
        effective = copy.deepcopy(base)
        entries = {entry["card_id"]: entry for entry in effective["entries"]}
        for addition in companion["senses"]:
            _require(set(addition) == {"card_id", "sense", "event"}, "invalid_sense_allocation")
            card, sense = addition["card_id"], addition["sense"]
            _require(card in SELECTED_CARD_IDS and card in entries, "unselected_card")
            _require(set(sense) == {"sense_id", "order", "state"}
                     and type(sense["order"]) is int and sense["order"] >= 1
                     and sense["state"] in {"active", "unsplit", "suppressed", "retired", "redirected"},
                     "invalid_sense_allocation")
            evidence = _mint(addition["event"], "sense_mint", sense["sense_id"])
            _require(evidence.get("card_id") == card and isinstance(evidence.get("source_sense_key"), str)
                     and bool(evidence["source_sense_key"]), "sense_mint_binding_mismatch")
            entries[card]["senses"].append(copy.deepcopy(sense))
            effective["events"].append(copy.deepcopy(addition["event"]))
        for record in companion["source_records"]:
            _require(set(record) == {"source_record_id", "source_id", "aliases", "correspondence"}
                     and bool(record["aliases"]) and bool(record["correspondence"]), "invalid_source_record")
            for alias in record["aliases"]:
                _require(set(alias) <= {"kind", "key", "snapshot_id", "note"}
                         and alias["kind"] in {"uid", "register_position", "content", "query_headword_label",
                                               "vesum_entry_form", "table_row"}
                         and all(isinstance(alias[k], str) and alias[k] for k in ("key", "snapshot_id")),
                         "invalid_source_alias")
                _require("note" not in alias or isinstance(alias["note"], str), "invalid_source_alias")
            for correspondence in record["correspondence"]:
                _require(set(correspondence) <= {"snapshot_id", "status", "locator", "matched_by"}
                         and correspondence["status"] == "unique"
                         and all(isinstance(correspondence[k], str) and correspondence[k]
                                 for k in ("snapshot_id", "locator")), "invalid_source_correspondence")
                _require("matched_by" not in correspondence or isinstance(correspondence["matched_by"], str),
                         "invalid_source_correspondence")
                _require(any(a["snapshot_id"] == correspondence["snapshot_id"] for a in record["aliases"]),
                         "source_alias_snapshot_mismatch")
            _require(all(any(c["snapshot_id"] == a["snapshot_id"] for c in record["correspondence"])
                         for a in record["aliases"]), "source_alias_snapshot_mismatch")
            events = [e for e in companion["events"] if e.get("to") == [record["source_record_id"]]]
            _require(len(events) == 1, "missing_or_duplicate_source_mint")
            evidence = _mint(events[0], "source_record_mint", record["source_record_id"])
            _require(evidence.get("source_id") == record["source_id"]
                     and any(evidence.get("snapshot_id") == c["snapshot_id"]
                             and evidence.get("locator") == c["locator"] for c in record["correspondence"]),
                     "source_mint_binding_mismatch")
        _require(len(companion["events"]) == len(companion["source_records"]), "unexpected_mint_event")
        effective["source_records"].extend(copy.deepcopy(companion["source_records"]))
        effective["events"].extend(copy.deepcopy(companion["events"]))
        identities = [(e["card_id"], "wc") for e in effective["entries"]]
        identities += [(s["sense_id"], "ws") for e in effective["entries"] for s in e["senses"]]
        identities += [(r["source_record_id"], "sr") for r in effective["source_records"]]
        _require(all(re.fullmatch(prefix + r"_[0-9a-hjkmnp-tv-z]{12}", identity)
                     for identity, prefix in identities), "invalid_identity")
        _unique([identity for identity, _ in identities], "duplicate_identity")
        _unique([e["event_id"] for e in effective["events"]], "duplicate_event")
        minted = [identity for event in effective["events"] if event["kind"] in
                  {"mint", "sense_mint", "source_record_mint"}
                  for identity in event.get("cards" if event["kind"] == "mint" else "to", [])]
        _require(sorted(minted) == sorted(identity for identity, _ in identities), "missing_or_duplicate_mint")
        _source_records(effective["source_records"])
        if companion["senses"] or companion["source_records"]:
            effective["registry_version"] += 1
        _require(digest(effective) == pins["combined_sha256"], "combined_digest_mismatch")
        return effective
    except (KeyError, TypeError, AttributeError) as exc:
        raise Refusal("invalid_allocation_shape") from exc


def _payload_text(payload, pointer):
    _require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "invalid_pointer")
    for token in pointer.split("/")[1:] if pointer else []:
        _require(not re.search(r"~(?![01])", token), "invalid_pointer")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(payload, dict):
            _require(token in payload, "pointer_not_found")
            payload = payload[token]
        elif isinstance(payload, list):
            _require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None, "invalid_pointer")
            _require(int(token) < len(payload), "pointer_not_found")
            payload = payload[int(token)]
        else:
            raise Refusal("pointer_not_found")
    _require(isinstance(payload, str), "pointer_not_text")
    return payload


def _span_text(text, span):
    _require(isinstance(span, (list, tuple)) and len(span) == 2
             and all(type(i) is int for i in span), "invalid_span")
    start, end = span
    _require(0 <= start < end <= len(text), "invalid_span")
    return text[start:end]


def make_receipt(record_key, record, pointer, span, entry_id, sense_key=None) -> dict:
    """Bind an unchanged Unicode span in a named JSON payload to its source."""
    try:
        text = _payload_text(record["payload"], pointer)
        receipt = {key: copy.deepcopy(record[key]) for key in _BINDING_FIELDS}
        if "source_role" in record:
            receipt["source_role"] = record["source_role"]
        receipt.update(record_key=record_key, payload_pointer=pointer,
                       text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                       span=list(span), quotation=_span_text(text, span), entry_id=entry_id, sense_key=sense_key)
        receipt["receipt_id"] = "wr_" + digest(receipt)
        verify_receipt(receipt, {record_key: record}, entry_id, sense_key)
        return receipt
    except (KeyError, TypeError, UnicodeError) as exc:
        raise Refusal("invalid_receipt_shape") from exc


def verify_receipt(receipt, records, entry_id, sense_key=None):
    """Refuse changed receipt content, source binding, identity or exact text."""
    try:
        content = {key: value for key, value in receipt.items() if key != "receipt_id"}
        _require(receipt["receipt_id"] == "wr_" + digest(content), "receipt_id_mismatch")
        _require(isinstance(receipt["record_key"], str) and bool(receipt["record_key"]), "invalid_record_key")
        _require(receipt["record_key"] in records, "record_not_found")
        record = records[receipt["record_key"]]
        _require(all(key in receipt and canonical(receipt[key]) == canonical(record[key])
                     for key in _BINDING_FIELDS),
                 "source_binding_mismatch")
        _require(canonical(receipt.get("source_role")) == canonical(record.get("source_role")),
                 "source_role_mismatch")
        _require(canonical(receipt["entry_id"]) == canonical(entry_id), "entry_mismatch")
        if sense_key is not None:
            _require(canonical(receipt["sense_key"]) == canonical(sense_key), "sense_mismatch")
        text = _payload_text(record["payload"], receipt["payload_pointer"])
        _require(receipt["text_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest(), "text_digest_mismatch")
        _require(_span_text(text, receipt["span"]) == receipt["quotation"], "quotation_mismatch")
    except (KeyError, TypeError, AttributeError, UnicodeError) as exc:
        raise Refusal("invalid_receipt_shape") from exc
