"""Pilot/golden source freeze and legacy identity bootstrap (#9293, #9862).

Literal captures prove snapshot integrity; intrinsic aliases are evidence,
never lexical equivalence. Changed snapshots need later correspondence.
"""

import argparse
import fcntl
import hashlib
import json
import re
import secrets
import sqlite3
import sys
import unicodedata
from contextlib import ExitStack, contextmanager
from pathlib import Path

import jsonschema
import yaml

from scripts.common.repo_root import main_checkout_root
from scripts.curriculum.evidence.lock import atomic_write
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.promote_teacher_lesson_intake import _POS_MAP

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs/sources/permissions-register.yaml"
ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
ROW_BASIS = "sha256 canonical UTF-8 JSON of entire literal selected row, not whole database"
REGISTER_ENTRIES_BASIS = (
    "sha256 canonical UTF-8 JSON of {sources: referenced register entries sorted by id, "
    "legal_references: cited terms.legal_refs objects resolved by id and sorted by id}"
)
HEX = r"[0-9a-f]{64}"
PROSE = ("note", "matched_by", "hold", "match_note")  # Provenance prose; attributes and scope labels never link.
# Input role: (native paths whose whole field set a validator fixes, None meaning every object; excluded inventory
# arrays). List items are None in paths. Role-less inputs read no native key and exclude nothing.
ROLES = {None: (None, set()), "register": (None, set()), "receipt": ({("denominator",)}, set()),
         "registry": (None, {("entries",), ("source_records",), ("events",)}),
         "manifest": ({(), ("admission",), ("admission", "denominator"), ("counts",), ("database_file_sha256",),
                       ("database_wal_sha256",), ("selection", "denominator"), ("selection", "source_records", None,
                       "row_key"), ("legacy_articles", None), ("legacy_articles", None, "metadata")},
                      {("selection", "units"), ("selection", "source_records"), ("legacy_articles",)})}
ADMISSION_FIELDS = {
    "admission", "candidate_sha256", "review_report_sha256", "review_family",
    "author_seat_distinct", "denominator", "checked_at", "review_task_id",
    "review_run_nonce", "review_model", "review_harness", "author_task_id",
}
MANIFEST_FIELDS = {
    "schema_version", "selection", "selection_file_sha256", "selection_content_sha256",
    "admission", "database_file_sha256", "database_wal_sha256", "rules_version",
    "normaliser_version", "counts", "legacy_articles", "manifest_sha256",
}
# Reviewed matching metadata, not a spelling-only correspondence rule.
POS_BINDINGS = {259013: 421145, 263932: 426804, 267658: 436957}
POS_REVIEW = "a06ca1e43f16bbb53643ec25978df7354c06259b641773e73aca16c6bf2d1f05"
POS_TOOLS = "10670390c58be3cc01f168dbbbfbdfebcbf5f6c655d2210fa4184ca22d6d55f5"


class Refusal(ValueError):
    """Only fixed, privacy-safe diagnostics may cross the CLI boundary."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def canonical(value, sort_keys=True):
    return json.dumps(value, ensure_ascii=False, sort_keys=sort_keys,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def parse(value):
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = item
        return result
    parsed = json.loads(value, object_pairs_hook=pairs)
    canonical(parsed)  # Reject nonfinite numbers and invalid Unicode, even in unused fields.
    return parsed


def load(path):
    return parse(path.read_bytes())


def write(path, value):
    # Arrays retain one complete logical record per line for inventory review.
    def render(item, depth=0):
        indent = "  " * depth
        if isinstance(item, dict) and any(isinstance(v, list | dict) for v in item.values()):
            fields = [indent + "  " + json.dumps(k) + ": " + render(v, depth + 1)
                      for k, v in item.items()]
            return "{\n" + ",\n".join(fields) + "\n" + indent + "}"
        if isinstance(item, list) and item:
            return "[\n" + ",\n".join(indent + "  " + canonical(row, False).decode() for row in item) + "\n" + indent + "]"
        return canonical(item, False).decode()
    atomic_write(path, (render(value) + "\n").encode())


def schema(value, name):
    validator = jsonschema.Draft202012Validator(load(ROOT / "schemas" / name))
    require(not next(validator.iter_errors(value), None), "Invalid " + name)


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional),
            "Invalid object fields")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def hex_digest(value):
    return isinstance(value, str) and re.fullmatch(HEX, value) is not None


def readonly(stack, path):
    require(path.is_absolute() and path.is_file(), "Source DB must be an existing absolute file")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    stack.callback(connection.close)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")
    return connection


def fingerprints(databases):
    main, wal = {}, {}
    for name, path in databases.items():
        main[name] = file_digest(path)
        sidecar = Path(str(path) + "-wal")
        wal[name] = file_digest(sidecar) if sidecar.exists() and sidecar.stat().st_size else None
    return main, wal


def rows(connection, table, key):
    require(isinstance(key, dict) and key and
            all(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", n) for n in [table, *key]),
            "Invalid row selector")
    where = " AND ".join(f'"{column}" = ?' for column in key)
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" WHERE {where}', tuple(key.values()))]


def walk(value, decoded=False, trail=(), at=(None, ()), scan=False):
    # Trail: enclosing objects, native or decoded, outermost first, each with its decoding and (role, native path).
    yield value, decoded, trail, at
    if isinstance(value, str) and value.lstrip()[:1] in {"[", "{", '"'}:
        try:
            parsed = parse(value)
        except json.JSONDecodeError:
            return
        yield from walk(parsed, True, trail, scan=scan)
    (role, path), (closed, excluded) = at, ROLES[at[0]]
    if isinstance(value, dict):  # Decoded keys count; only a context scan reads open native objects' keys.
        for key in value if decoded or (scan and closed is not None and path not in closed) else ():
            yield from walk(key, decoded, (*trail, (value, decoded, at)), scan=scan)
        for key, item in value.items():
            yield from walk(item, decoded, (*trail, (value, decoded, at)), (role, (*path, key)), scan)
    elif isinstance(value, list) and not (scan and path in excluded):
        for item in value:
            yield from walk(item, decoded, trail, (role, (*path, None)), scan)


def source_keys(entry):
    return {k["key"] for k in entry.get("key_at_creation", {}).get("source_keys", [])}


def isolation(inputs, heldout, roles=(), pilot=None):  # Roles name the inputs after the first, which has the manifest role.
    first = inputs[0]  # A first input without a selection object is itself read as the selection.
    places = [("manifest", () if isinstance(first, dict) and isinstance(first.get("selection"), dict) else
               ("selection",)), *((role, ()) for role in roles)] + [(None, ())] * len(inputs)
    objects = [node for item, at in zip(inputs, places, strict=False) for node in walk(item, at=at)]
    for value, *_ in objects:
        if isinstance(value, dict):
            require(not any(k.startswith(("expected", "adjudicated")) for k in value),
                    "Held-out expected answers are forbidden in admitted inputs")
    if heldout is None:
        return "unverified"
    membership = load(heldout)
    fields(membership, {"heldout", "replay"})
    require(all(isinstance(v, list) and all(nonempty(k) for k in v) and len(set(v)) == len(v)
                for v in membership.values()), "Membership keys must be unique nonempty strings")
    boundary, replay = set(membership["heldout"]), set(membership["replay"])
    require(boundary and not boundary & replay, "Heldout and replay must be disjoint")
    groups, owners, pilot_keys = [], {}, set()
    pilot_objects = {id(v) for v, *_ in walk(pilot)} if pilot is not None else set()
    records = [r for v, *_ in objects if isinstance(v, dict) and isinstance(v.get("source_records"), list)
               for r in v["source_records"] if "raw_row" in r]
    # Joint manifests may capture the same literal row. Keep every owner view below, but count a shared
    # literal parent once for the typed dependency; distinct captures still fail the single-parent gate.
    records = list({(r["source_id"], r["table"], canonical(r["raw_row"])): r for r in records}.values())
    def cited(value, keys, decoded=False, at=(None, ()), scan=False):  # Shared recogniser: every known key, nested too.
        texts = [t for t, *_ in walk(value, decoded, (), at, scan) if isinstance(t, str)]
        return {k for t in texts for k in keys if k in t and re.search(rf"(?<![\w:/#-]){re.escape(k)}(?![\w:/#-])", t)}
    # Closure inventory: identities (card/sense/source-record ids, mint cards/to) and structured keys (aliases, locators,
    # candidates, creation/unit keys, legacy slugs/aliases, mint endpoints, POS-review anchors, a paradigm's admitted
    # parent) link; PROSE and mint evidence only via cited known keys. Every object that forms a group is an owner.
    for value, decoded, *_ in objects:
        if not isinstance(value, dict):
            continue
        group, notes = set(), []
        if "source_record_id" in value:
            group |= {value["source_record_id"]} | {a["key"] for a in value.get("aliases", [])}
            group |= {k for c in value.get("correspondence", []) for k in [c.get("locator"), *c.get("candidates", [])]}
            notes += [[d.get(f) for f in PROSE] for d in value.get("aliases", []) + value.get("correspondence", [])]
        if "card_id" in value:  # Owned senses and every creation source key; mwe_key is <source_locator>|<normalised form>.
            creation = value.get("key_at_creation", {})
            group |= {value["card_id"], *source_keys(value), *(s["sense_id"] for s in value.get("senses", [])),
                     creation.get("paradigm_key"), creation.get("mwe_key", "").rpartition("|")[0]}
            notes += [[d.get(f) for f in PROSE] for d in creation.get("source_keys", [])]
        if value.get("kind") in {"mint", "sense_mint", "source_record_mint"}:  # Evidence is provenance, never a key.
            group |= {*value.get("cards", []), *value.get("from", []), *value.get("to", [])}
            notes += [value.get("evidence")]
        if "unit_key" in value:
            group |= {value["unit_key"], value["anchor_locator"], *value["source_record_keys"]}
            if value["atlas_slug"]:
                group.add("atlas0:slug:" + value["atlas_slug"])
        if "locator" in value and "raw_row" in value:
            group |= {value["locator"]} | {a["key"] for a in aliases(value, records)}
            group.add(paradigm_parent(value, records).get("locator"))  # Typed dependency: closure only, never an alias.
        if "metadata" in value and "aliases" in value:
            group |= {"atlas0:slug:" + value["metadata"]["slug"], (value.get("pos_review") or {}).get("anchor_locator")}
            group |= {a["alias"] for a in value["aliases"]}
        if group:
            owners[id(value)] = len(groups), value, decoded
            groups.append((group - {None, ""}, notes, decoded))
            if id(value) in pilot_objects:
                pilot_keys |= group - {None, ""}
    known = set().union(*(g for g, *_ in groups))
    groups = [group | cited(notes, known, decoded) for group, notes, decoded in groups]
    require(boundary | replay <= known, "Unresolved membership keys; isolation cannot be checked")
    while True:
        expanded = boundary | set().union(*(g for g in groups if g & boundary))
        if expanded == boundary:
            break
        boundary = expanded
    require(not boundary & replay, "Heldout/replay overlap after conservative alias closure")
    require(not boundary & pilot_keys, "Heldout/pilot overlap after conservative alias closure")
    for value, decoded, trail, at in objects:  # Adjudication markers are scanned with the same recogniser, never linked.
        if not isinstance(value, dict):
            continue
        adjudication = value.get("kind") in {"identity", "split", "merge", "resolve", "variant", "sense_map"}
        adjudication |= any(k in value for k in ("overlay_id", "settled_by", "mapping", "merged_into", "split_into"))
        adjudication |= "event_id" in value and value.get("kind") not in {"mint", "sense_mint", "source_record_mint"}
        if adjudication:
            require(not cited(value, boundary, decoded),
                    "Held-out adjudicated mapping touches a membership key or indirect alias")
            # A marker also marks every enclosing owner (itself included): refuse a closure-held or citing owner.
            for index, owner, owned in [owners[id(o)] for o, *_ in (*trail, (value,)) if id(o) in owners]:
                require(not groups[index] & boundary and not cited(owner, boundary, owned),
                        "Held-out adjudicated mapping touches a marked owner's closure or text")
            # Then its context: every enclosing object to the input root, its own included, minus inventory arrays.
            require(not any(cited(o, boundary, d, place, True) for o, d, place in (*trail, (value, decoded, at))),
                    "Held-out adjudicated mapping touches its enclosing context")
    return "checked"


def paradigm_parent(record, records):  # The one cross-record relation: a ULIF paradigm's single admitted parent row.
    if (record["source_id"], record["table"]) != ("ulif", "ulif_dictua_sections"):
        return {}
    require(type(record["raw_row"]["entry_id"]) is int, "Invalid paradigm parent locator")
    parents = [r for r in records if r["source_id"] == "ulif" and
               r["table"] == "ulif_dictua_entries" and r["raw_row"]["id"] == record["raw_row"]["entry_id"]]
    require(len(parents) == 1, "Paradigm requires exactly one admitted parent")
    return parents[0]


def intrinsic(record, records):
    raw, source, table = record["raw_row"], record["source_id"], record["table"]
    if (source, table) == ("ulif", "ulif_dictua_entries"):
        return "query_headword_label", "ulif:record:" + "#".join(
            raw[k] for k in ("normalized_query", "canonical_headword", "grammatical_label"))
    if (source, table) == ("puls", "puls_cefr"):
        return "table_row", "puls:record:" + "/".join(raw[k] for k in ("word", "pos", "level"))
    if (source, table) == ("frazeolohichnyi", "frazeolohichnyi"):
        require(nonempty(raw["word"]), "Invalid phrase-dictionary word")
        return "table_row", "frazeolohichnyi:record:" + raw["word"]
    if (source, table) == ("ukrainian_word_stress", "enrichment"):
        payload = parse(raw["payload_json"])
        fields(payload, {"form", "source"})
        require(all(nonempty(v) for v in payload.values()) and
                payload["source"] == raw["source"] == "ukrainian-word-stress" and raw["section"] == "stress",
                "Invalid stress tuple")
        return "table_row", "ukrainian_word_stress:record:stress:v1:sha256:" + digest(payload)
    require((source, table) == ("ulif", "ulif_dictua_sections"), "Missing approved source-key contract")
    payload = parse(raw["payload_json"])
    kind = raw["kind"]
    require(kind in {"paradigm", "phraseology"}, "Missing approved ULIF section-kind contract")
    common = {"raw_html", "raw_response_ref", "sense_or_group_id", "source_order"}
    fields(payload, common | ({"rows"} if kind == "paradigm" else
                              {"citations", "register_labels", "terms", "text"}))
    if kind == "paradigm":
        matrix = payload["rows"]
        require(isinstance(matrix, list) and matrix and all(isinstance(r, list) and r for r in matrix) and
                all(len(r) == len(matrix[0]) and all(isinstance(c, str) for c in r) for r in matrix),
                "Invalid paradigm matrix")
    else:
        require(nonempty(payload["text"]) and isinstance(payload["terms"], list) and
                all(isinstance(t, dict) and set(t) == {"raw_html", "text"} and
                    all(isinstance(v, str) for v in t.values()) for t in payload["terms"]) and
                all(isinstance(payload[k], list) and all(isinstance(v, str) for v in payload[k])
                    for k in ("citations", "register_labels")), "Invalid phraseology payload")
    require(nonempty(payload["raw_html"]) and
            nonempty(payload["raw_response_ref"]) and re.fullmatch("sha256:" + HEX, payload["raw_response_ref"]) and
            nonempty(payload["sense_or_group_id"]) and
            re.fullmatch(kind + r":[1-9][0-9]*", payload["sense_or_group_id"]) and
            type(payload["source_order"]) is int and payload["source_order"] >= 0 and
            type(raw["source_order"]) is int and raw["source_order"] == payload["source_order"] and
            raw["sense_or_group_id"] == payload["sense_or_group_id"], "Invalid " + kind + " discriminator")
    parent_row = paradigm_parent(record, records)["raw_row"]
    parent = {k: parent_row[k] for k in ("content_sha256", "normalized_query", "canonical_headword",
                                      "grammatical_label", "homonym_index")}
    require(hex_digest(parent["content_sha256"]) and nonempty(parent["normalized_query"]) and
            all(isinstance(parent[k], str) for k in ("canonical_headword", "grammatical_label")) and
            type(parent["homonym_index"]) is int and parent["homonym_index"] > 0, "Invalid paradigm parent")
    return "table_row", "ulif:record:" + kind + ":v1:sha256:" + digest(
        {"parent": parent, "kind": kind, "payload": payload})


def aliases(record, records):
    kind, key = intrinsic(record, records)
    evidence = [(kind, key)]
    if record["source_content_sha256"] is not None:
        require(hex_digest(record["source_content_sha256"]), "Invalid source content digest")
        evidence.append(("content", record["source_id"] + ":content:" + record["source_content_sha256"]))
    if record["raw_row"].get("register_position"):
        evidence.append(("register_position", "ulif:register:" + record["raw_row"]["register_position"]))
    return [{"kind": k, "key": v, "snapshot_id": record["snapshot_id"]} for k, v in evidence]


def selection_check(selection, registered):
    require(selection["schema_version"] == "atlas-pilot-selection-candidate.v2", "Unsupported selection schema")
    kind = selection.get("kind", "pilot")
    require(kind in {"pilot", "golden"}, "Unsupported manifest kind")
    if kind == "golden":
        require(type(selection.get("case_count")) is int and selection["case_count"] == 220,
                "Golden denominator drift; require frozen case count 220")
    else:
        require("case_count" not in selection, "Pilot cannot declare a golden case count")
    records, units = selection["source_records"], selection["units"]
    require(isinstance(records, list) and isinstance(units, list), "Invalid selection inventory")
    locators = [r["locator"] for r in records]
    require(len(set(locators)) == len(records), "Duplicate selected rows")
    require(len({u["unit_key"] for u in units}) == len(units), "Duplicate candidate units")
    require(len({u["anchor_locator"] for u in units}) == len(units), "Duplicate source-supported anchor partitions")
    tuple_keys = []
    for record in records:
        require(record["source_id"] in registered, "Unregistered source; update approved register first")
        raw, key = record["raw_row"], record["row_key"]
        require(isinstance(raw, dict) and isinstance(key, dict) and key, "Invalid row selector")
        require(all(raw.get(k) == v and type(raw.get(k)) is type(v) for k, v in key.items()),
                "Row selector disagrees with literal capture")
        if record["table"] == "enrichment":
            fields(key, {"slug", "section"})
            locator = "atlas0:enrichment:" + key["slug"] + "/" + key["section"]
        else:
            fields(key, {"id"})
            require(type(key["id"]) is int, "Invalid integer row locator")
            locator = f'{record["source_id"]}:{record["table"]}:id:{key["id"]}'
        require(record["locator"] == locator, "Literal locator disagrees with source row selector")
        require(record["content_fingerprint_basis"] == ROW_BASIS, "Label digest as literal-row, not full DB")
        require(digest(raw) == record["content_sha256"], "Changed selected bytes; re-admit the input")
        require(record.get("snapshot_id") == "selected-row@sha256:" + record["content_sha256"], "Invalid row snapshot")
        require(record["source_content_sha256"] == raw.get("content_sha256"), "Source content hash mismatch")
        require(record.get("database", "sources") in {"sources", "atlas", "vesum"}, "Unknown source database")
        if record["table"] == "ulif_dictua_entries":
            require(type(raw["homonym_checked"]) is int and raw["homonym_checked"] == 1 and
                    raw["status"] == "ok" and nonempty(raw["parser_version"]), "ULIF lacks checked provenance")
            require(nonempty(raw["retrieved_at"]) and hex_digest(raw["content_sha256"]) and
                    nonempty(raw["raw_response_ref"]), "Missing ULIF provenance")
        if record["source_id"] == "ukrainian_word_stress":
            require(record["lineage_status"] == "unknown" and nonempty(record["lineage_basis"]),
                    "Preserve unknown lineage explicitly")
        evidence = aliases(record, records)
        if record["table"] in {"enrichment", "ulif_dictua_sections"}:
            tuple_keys.append(evidence[0]["key"])
    require(len(set(tuple_keys)) == len(tuple_keys), "Duplicate intrinsic tuple or digest collision; allocation ambiguous")
    for unit in units:
        require(nonempty(unit["unit_key"]) and unit["entry_type"] in {"lexeme_candidate", "mwe_candidate"},
                "Unknown candidate kind")
        require(all(nonempty(unit[k]) for k in ("counting_basis", "cefr_basis", "atlas_mapping_basis")),
                "Missing partition or mapping basis")
        require(unit["supplementary_correspondence"] == "unresolved", "No cross-source matching in foundation")
        require(isinstance(unit["source_record_keys"], list) and
                unit["anchor_locator"] in unit["source_record_keys"]
                and set(unit["source_record_keys"]) <= set(locators), "Missing source reference")
        require(unit["atlas_slug"] is None or nonempty(unit["atlas_slug"]), "Invalid legacy mapping")
    require(set(locators) == set().union(*(set(u["source_record_keys"]) for u in units)), "Unreferenced source record")
    counts = {"units": len(units), "source_records": len(records),
              "atlas_articles": len({u["atlas_slug"] for u in units if u["atlas_slug"]})}
    require(counts == selection["denominator"] and all(type(v) is int for v in selection["denominator"].values())
            and counts["units"] == (220 if kind == "golden" else 150),
            "Golden denominator drift; require exactly 220 cases" if kind == "golden" else
            "Pilot denominator drift; require exactly 150 admitted units")
    return counts


def admission_check(receipt, counts, selection_hash):
    fields(receipt, {"admission", "candidate_sha256", "review_report_sha256", "review_family",
                     "author_seat_distinct", "denominator"}, ADMISSION_FIELDS)
    require(receipt["admission"] == "APPROVE" and receipt["candidate_sha256"] == selection_hash and
            hex_digest(receipt["review_report_sha256"]), "Missing source admission")
    require(receipt["author_seat_distinct"] is True and receipt["review_family"] == "google" and
            receipt["denominator"] == counts and all(type(v) is int for v in receipt["denominator"].values()),
            "Require independent source admission with exact denominators")
    require(all(isinstance(v, str) for k, v in receipt.items() if k not in {"author_seat_distinct", "denominator"}),
            "Invalid admission provenance types")


def creation_key(article):
    metadata = article["metadata"]
    return {"spelling": unicodedata.normalize("NFC", strip_acute_stress(metadata["lemma"])),
            "pos": article["coarse_pos"], "source_keys": [{"source_id": "atlas0",
                             "key": "atlas0:slug:" + metadata["slug"]}]}


def legacy_capture(raw, legacy_aliases, selection, vesum):
    metadata = {k: raw[k] for k in ("slug", "lemma", "entry_type", "pos")}
    require(raw["entry_type"] in {"lemma", "multiword_term", "expression", "phraseologism"}, "Unknown legacy card kind")
    require(nonempty(raw["lemma"]), "Missing legacy spelling")
    label = (raw["pos"] or "").split(":")[0]
    # Reuse the established Atlas/VESUM POS vocabulary conversion; never a default noun.
    converted = {school: coarse for coarse, school in _POS_MAP.items() if coarse != school}
    expected = converted.get(label, label)
    expected = {"infinitive": "verb"}.get(expected, expected)
    proof = []
    if raw["entry_type"] == "lemma":
        anchors = [r for r in selection["source_records"] if r["table"] == "ulif_dictua_entries" and
                   r["locator"] in {u["anchor_locator"] for u in selection["units"] if u["atlas_slug"] == raw["slug"]}]
        binding = next((r for r in anchors if r["raw_row"]["id"] in POS_BINDINGS), None)
        if binding:
            proof = rows(vesum, "forms_all",
                         {"entry_id": POS_BINDINGS[binding["raw_row"]["id"]], "lemma": raw["lemma"]})
        else:
            proof = rows(vesum, "forms_all", {"lemma": raw["lemma"]})
            proof = [r for r in proof if (":pron:" in r["tags"] if label == "pronoun" else r["pos"] == expected)]
        require(proof and len({r["pos"] for r in proof}) == 1, "Unresolved source-backed coarse POS; no guessing")
        expected = proof[0]["pos"]
        proof = sorted({canonical({k: r[k] for k in ("entry_id", "lemma", "pos", "tags")}) for r in proof})
        proof = [parse(r) for r in proof]
    require(expected in set(_POS_MAP) - {"adjective", "adverb", "preposition", "numeral", "pronoun"},
            "Unresolved source-backed coarse POS; no guessing")
    return {"metadata": metadata, "coarse_pos": expected, "pos_evidence": proof,
            "pos_review": {"anchor_locator": binding["locator"], "report_sha256": POS_REVIEW,
                           "tools_sha256": POS_TOOLS} if raw["entry_type"] == "lemma" and binding else None,
            "literal_row_sha256": digest(raw), "literal_row_fingerprint_basis": ROW_BASIS,
            "metadata_sha256": digest(metadata), "aliases": sorted(legacy_aliases, key=canonical)}


def register_entries_digest(register, source_ids):
    ids = set(source_ids)
    entries = [s for s in register["sources"] if s["id"] in ids]
    require(len(entries) == len(ids) and {s["id"] for s in entries} == ids,
            "Missing or duplicate referenced register source")
    legal_ids = {ref for entry in entries for ref in entry["terms"].get("legal_refs", [])}
    legal_refs = [ref for ref in register["legal_references"] if ref["id"] in legal_ids]
    require(len(legal_refs) == len(legal_ids) and {ref["id"] for ref in legal_refs} == legal_ids,
            "Missing or duplicate cited register legal reference")
    return digest({"sources": sorted(entries, key=lambda s: s["id"]),
                   "legal_references": sorted(legal_refs, key=lambda ref: ref["id"])})


def register_pin_check(manifest, register, manifest_path, counts):
    path = manifest_path.with_suffix(".register-pin.json") if manifest_path is not None else None
    if path is None or not path.exists():
        require(file_digest(REGISTER) == manifest["selection"]["source_register_sha256"],
                "Register fingerprint mismatch; re-admit and re-freeze before reuse")
        return
    pin = load(path)
    fields(pin, {"schema_version", "manifest_sha256", "legacy_source_register_sha256", "basis", "source_ids", "pins"})
    require(pin["schema_version"] == "atlas-pilot-register-pin.v1" and pin["basis"] == REGISTER_ENTRIES_BASIS and
            hex_digest(pin["manifest_sha256"]) and hex_digest(pin["legacy_source_register_sha256"]),
            "Invalid register pin metadata")
    require(pin["manifest_sha256"] == manifest["manifest_sha256"] and
            pin["legacy_source_register_sha256"] == manifest["selection"]["source_register_sha256"],
            "Register pin binding mismatch")
    source_ids = sorted({r["source_id"] for r in manifest["selection"]["source_records"]})
    require(pin["source_ids"] == source_ids, "Register pin source ids mismatch")
    require(isinstance(pin["pins"], list) and pin["pins"], "Invalid register pin history")
    for index, entry in enumerate(pin["pins"]):
        fields(entry, {"entries_sha256", "reason", "recorded"} | ({"admission"} if index else set()))
        require(hex_digest(entry["entries_sha256"]) and nonempty(entry["reason"]) and nonempty(entry["recorded"]),
                "Invalid register pin history")
        if index:
            admission_check(entry["admission"], counts, entry["entries_sha256"])
    require(register_entries_digest(register, source_ids) == pin["pins"][-1]["entries_sha256"],
            "Register fingerprint mismatch; re-admit and re-freeze before reuse")


def manifest_check(manifest, manifest_path=None):
    fields(manifest, MANIFEST_FIELDS, {"kind"})
    require(manifest.get("kind", "pilot") == manifest["selection"].get("kind", "pilot"),
            "Manifest kind disagrees with selection")
    require(manifest["schema_version"] == "atlas-word-card-foundation.v1", "Unsupported frozen manifest")
    require(manifest["manifest_sha256"] == digest({k: v for k, v in manifest.items() if k != "manifest_sha256"}),
            "Changed manifest bytes/content; restore admitted freeze")
    require(manifest["rules_version"] == "rules-v1-draft" and manifest["normaliser_version"] == "norm-v1",
            "Unapproved rules or normaliser version")
    register = yaml.safe_load(REGISTER.read_bytes())
    schema(register, "permissions-register.schema.json")
    require(digest(manifest["selection"]) == manifest["selection_content_sha256"], "Selection content fingerprint mismatch")
    original = (json.dumps(manifest["selection"], ensure_ascii=False, indent=2) + "\n").encode()
    require(hashlib.sha256(original).hexdigest() == manifest["selection_file_sha256"], "Admitted selection bytes changed")
    counts = selection_check(manifest["selection"], {s["id"] for s in register["sources"]})
    register_pin_check(manifest, register, manifest_path, counts)
    admission_check(manifest["admission"], counts, manifest["selection_file_sha256"])
    inventory = manifest["legacy_articles"]
    require({a["metadata"]["slug"] for a in inventory} ==
            {u["atlas_slug"] for u in manifest["selection"]["units"] if u["atlas_slug"]}, "Legacy inventory mismatch")
    require(len(inventory) == counts["atlas_articles"], "Duplicate legacy inventory")
    for article in inventory:
        fields(article, {"metadata", "metadata_sha256", "coarse_pos", "pos_evidence", "pos_review",
                         "literal_row_sha256", "literal_row_fingerprint_basis", "aliases"})
        fields(article["metadata"], {"slug", "lemma", "entry_type", "pos"})
        require(article["literal_row_fingerprint_basis"] == ROW_BASIS and hex_digest(article["literal_row_sha256"]),
                "Invalid full literal legacy fingerprint")
        require(article["metadata_sha256"] == digest(article["metadata"]), "Changed legacy metadata projection")
        require(nonempty(article["coarse_pos"]) and
                all(p["pos"] == article["coarse_pos"] and p["lemma"] == article["metadata"]["lemma"]
                    for p in article["pos_evidence"]), "Inconsistent POS evidence")
        require(all(a["target_slug"] == article["metadata"]["slug"] for a in article["aliases"]),
                "Alias target outside inventory")
        require(len({canonical(a) for a in article["aliases"]}) == len(article["aliases"]), "Duplicate legacy aliases")
    require(manifest["counts"] == counts | {"legacy_alias_rows": sum(len(a["aliases"]) for a in inventory)} and
            all(type(v) is int for v in manifest["counts"].values()), "Incorrect separate denominators")
    for key in ("database_file_sha256", "database_wal_sha256"):
        fields(manifest[key], {"sources", "atlas", "vesum"})
        require(all(hex_digest(h) or (key == "database_wal_sha256" and h is None) for h in manifest[key].values()),
                "Missing frozen DB/WAL file fingerprints")
    return counts


def output_check(output, inputs):
    require(output.resolve() not in {p.resolve() for p in inputs if p is not None},
            "Output must be separate from every input/source/heldout file")


def freeze(args):
    selection = load(args.selection)
    receipts = list(args.selection.parent.glob("*source-admission-receipt.json"))
    require(len(receipts) == 1, "Place one driver source-admission-receipt.json beside selection")
    receipt = load(receipts[0])
    require(file_digest(Path(receipt["review_report_path"])) == receipt["review_report_sha256"],
            "Admission report fingerprint mismatch")
    register = yaml.safe_load(args.source_register.read_bytes())
    schema(register, "permissions-register.schema.json")
    require(file_digest(args.source_register) == selection["source_register_sha256"], "Source register fingerprint mismatch")
    counts = selection_check(selection, {s["id"] for s in register["sources"]})
    admission = {k: receipt[k] for k in sorted(ADMISSION_FIELDS) if k in receipt}
    admission_check(admission, counts, file_digest(args.selection))
    isolation([selection, receipt, register], None, ("receipt", "register"))
    databases = {n: getattr(args, n + "_db") for n in ("sources", "atlas", "vesum")}
    sidecars = [Path(str(p) + suffix) for p in databases.values() for suffix in ("-wal", "-shm")]
    output_check(args.output, [*databases.values(), *sidecars, args.selection, args.source_register, receipts[0],
                              Path(receipt["review_report_path"]), args.heldout_manifest])
    before = fingerprints(databases)
    inventory = []
    with ExitStack() as stack:
        connections = {n: readonly(stack, p) for n, p in databases.items()}
        for record in selection["source_records"]:
            actual = rows(connections[record.get("database", "sources")], record["table"], record["row_key"])
            require(actual == [record["raw_row"]] and [digest(row) for row in actual] == [record["content_sha256"]],
                    "Selected literal row mismatch; stop and re-admit source version")
        for slug in sorted({u["atlas_slug"] for u in selection["units"] if u["atlas_slug"]}):
            articles = rows(connections["atlas"], "articles", {"slug": slug})
            require(len(articles) == 1, "Missing or duplicate legacy article; no invented mappings")
            inventory.append(legacy_capture(articles[0], rows(connections["atlas"], "aliases", {"target_slug": slug}),
                                            selection, connections["vesum"]))
    require(before == fingerprints(databases), "Source file/WAL mutation detected; no freeze written")
    manifest = {"schema_version": "atlas-word-card-foundation.v1", "selection": selection,
                "selection_file_sha256": file_digest(args.selection), "selection_content_sha256": digest(selection),
                "admission": admission, "database_file_sha256": before[0], "database_wal_sha256": before[1],
                "rules_version": args.rules_version, "normaliser_version": args.normaliser_version,
                "counts": counts | {"legacy_alias_rows": sum(len(a["aliases"]) for a in inventory)},
                "legacy_articles": inventory}
    if selection.get("kind") is not None:
        manifest["kind"] = selection["kind"]
    manifest["manifest_sha256"] = digest(manifest)
    manifest_check(manifest)
    isolation([manifest, receipt, register], args.heldout_manifest, ("receipt", "register"))
    with locked(args.output):
        if args.output.exists():
            require(digest(load(args.output)) == digest(manifest), "Immutable manifest exists with different content")
        else:
            write(args.output, manifest)
    return manifest


def registry_check(registry):
    schema(registry, "word-card-identity-registry-v1.schema.json")
    card_schema = load(ROOT / "schemas/word-card-v1.schema.json")
    validator = jsonschema.Draft202012Validator(card_schema)
    for entry in registry["entries"]:
        errors = validator.descend(entry["key_at_creation"], card_schema["properties"]["key_at_creation"])
        require(not next(errors, None), "Invalid card key_at_creation")
    identities = [e["card_id"] for e in registry["entries"]] + [r["source_record_id"] for r in registry["source_records"]]
    identities += [s["sense_id"] for e in registry["entries"] for s in e["senses"]]
    require(len(identities) == len(set(identities)), "Reused identity; restore prior registry")
    ids = set(identities)
    require(len({e["event_id"] for e in registry["events"]}) == len(registry["events"]), "Duplicate history event")
    minted = []
    for event in registry["events"]:
        require(set(event.get("cards", []) + event.get("from", []) + event.get("to", [])) <= ids,
                "History references missing identity")
        if event["kind"] in {"mint", "sense_mint", "source_record_mint"}:
            targets = event.get("cards", []) if event["kind"] == "mint" else event.get("to", [])
            require(len(targets) == 1 and nonempty(event["evidence"]) and nonempty(event["build_id"]),
                    "Inconsistent mint history")
            prefix = {"mint": "wc_", "sense_mint": "ws_", "source_record_mint": "sr_"}[event["kind"]]
            require(targets[0].startswith(prefix), "Wrong mint identity type")
            minted.extend(targets)
    require(len(minted) == len(ids) and set(minted) == ids, "Missing or duplicate mint history")
    graph = {e["card_id"]: e.get("split_into", []) + ([e["merged_into"]] if "merged_into" in e else [])
             for e in registry["entries"]}
    def acyclic(node, trail):
        require(node in ids and node not in trail, "Missing or cyclic identity reference")
        for target in graph.get(node, []):
            acyclic(target, trail | {node})
    for node in graph:
        acyclic(node, set())
    require(len({canonical(e["key_at_creation"]) for e in registry["entries"]}) == len(registry["entries"]),
            "Duplicate creation key allocated twice")
    observations = []
    for record in registry["source_records"]:
        require(len({canonical(a) for a in record["aliases"]}) == len(record["aliases"]), "Duplicate alias history")
        require(len({c["snapshot_id"] for c in record["correspondence"]}) == len(record["correspondence"]),
                "Duplicate correspondence history")
        for c in record["correspondence"]:
            require(any(a["snapshot_id"] == c["snapshot_id"] for a in record["aliases"]),
                    "Correspondence has no observed aliases")
            if c["status"] == "unique":
                observations.append((record["source_id"], c["snapshot_id"], c["locator"]))
    require(len(set(observations)) == len(observations), "Source row allocated twice")


def allocation_check(manifest, registry, complete=True):
    registry_check(registry)
    build = "pilot@sha256:" + manifest["manifest_sha256"]
    require(not registry["events"] or any(e["build_id"] == build for e in registry["events"]),
            "New or changed snapshot requires correspondence; no allocation")
    cards, sources = [], []
    def bound(identity, kind, evidence):
        events = [e for e in registry["events"] if e["kind"] == kind and
                  identity in e.get("cards", []) + e.get("to", [])]
        require(len(events) == 1 and events[0]["evidence"] == evidence and events[0]["build_id"] == build,
                "Identity differs from original mint evidence/build/type")
    for article in manifest["legacy_articles"]:
        key = "atlas0:slug:" + article["metadata"]["slug"]
        matches = [e for e in registry["entries"] if key in source_keys(e)]
        require(len(matches) <= 1, "Legacy alias maps to multiple initial allocations")
        if matches:
            entry = matches[0]
            require(entry["key_at_creation"] == creation_key(article), "Legacy creation evidence mismatch")
            kind = "mwe" if article["metadata"]["entry_type"] != "lemma" else "lexeme"
            require(entry["card_kind"] == kind and entry["created_in_build"] == build, "Changed card mint provenance")
            bound(entry["card_id"], "mint", key)
            cards.append(entry["card_id"])
    records = manifest["selection"]["source_records"]
    snapshots, expected = {r["snapshot_id"] for r in records}, {}
    for record in records:
        matches = [r for r in registry["source_records"] if r["source_id"] == record["source_id"] and
                   any(c.get("locator") == record["locator"] and c["snapshot_id"] == record["snapshot_id"] and
                       c["status"] == "unique" for c in r["correspondence"])]
        require(len(matches) <= 1, "Source row has multiple allocations")
        if matches:
            expected[matches[0]["source_record_id"]] = aliases(record, records)
            require(all(a in matches[0]["aliases"] for a in expected[matches[0]["source_record_id"]]),
                    "Inconsistent source alias history")
            bound(matches[0]["source_record_id"], "source_record_mint", record["locator"])
            sources.append(matches[0]["source_record_id"])
    # Aliases under this freeze's snapshots must be exactly the bound row's; other snapshots are retained history.
    require(all(a in expected.get(r["source_record_id"], []) for r in registry["source_records"]
                for a in r["aliases"] if a["snapshot_id"] in snapshots), "Frozen-snapshot alias differs from its bound row")
    minted = {i for e in registry["events"] if e["build_id"] == build and e["kind"] in {"mint", "sense_mint", "source_record_mint"}
              for i in e.get("cards", []) + e.get("to", [])}
    require(minted <= set(cards + sources), "Allocation history exceeds frozen pilot inventory")
    require((len(cards) == manifest["counts"]["atlas_articles"] and
             len(sources) == manifest["counts"]["source_records"]) or not (complete or registry["events"]),
            "Partial allocation; restore atomic prior registry")
    return cards, sources


@contextmanager
def locked(output):
    """Keep the mutex inode in approved ignored storage; never unlink it."""
    root = main_checkout_root(ROOT) / "batch_state/locks/word-card-foundation"
    root.mkdir(parents=True, exist_ok=True)
    path = root / (hashlib.sha256(str(output.resolve()).encode()).hexdigest() + ".lock")
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def allocate(args, manifest):
    output_check(args.registry, [args.manifest, args.heldout_manifest])
    with locked(args.registry):
        registry = load(args.registry) if args.registry.exists() else {
            "schema_version": "1", "registry_version": 1, "entries": [], "source_records": [], "events": []}
        isolation([manifest, registry], args.heldout_manifest, ("registry",))
        cards, sources = allocation_check(manifest, registry, False)
        build = "pilot@sha256:" + manifest["manifest_sha256"]
        occupied = {e["card_id"] for e in registry["entries"]} | {r["source_record_id"] for r in registry["source_records"]}
        def mint(prefix):
            identity = prefix + "".join(secrets.choice(ALPHABET) for _ in range(12))
            require(identity not in occupied, "Random identifier reuse; allocation refused without write")
            occupied.add(identity)
            return identity
        def event(kind, identity, evidence):
            number = max([int(e["event_id"][3:]) for e in registry["events"]], default=0) + 1
            registry["events"].append({"event_id": f"ie_{number:04d}", "kind": kind, "build_id": build,
                                       "cards" if kind == "mint" else "to": [identity], "evidence": evidence})
        if not cards and not sources:
            for article in manifest["legacy_articles"]:
                identity = mint("wc_")
                registry["entries"].append({"card_id": identity,
                    "card_kind": "mwe" if article["metadata"]["entry_type"] != "lemma" else "lexeme",
                    "state": "active", "key_at_creation": creation_key(article), "created_in_build": build, "senses": []})
                event("mint", identity, "atlas0:slug:" + article["metadata"]["slug"])
            records = manifest["selection"]["source_records"]
            for record in records:
                identity = mint("sr_")
                registry["source_records"].append({"source_record_id": identity, "source_id": record["source_id"],
                    "aliases": aliases(record, records), "correspondence": [{"snapshot_id": record["snapshot_id"],
                        "status": "unique", "locator": record["locator"], "matched_by": "direct observation in initial snapshot"}]})
                event("source_record_mint", identity, record["locator"])
            registry["registry_version"] += int(args.registry.exists())
            allocation_check(manifest, registry)
            isolation([manifest, registry], args.heldout_manifest, ("registry",))
            write(args.registry, registry)
        return registry


def main(argv=None):
    epilog = (
        "Example (PROJECT_PYTHON = shared interpreter):\n"
        "  PROJECT_PYTHON -m scripts.atlas.word_card_foundation verify --manifest pilot.json --registry registry.json\n"
        "  PROJECT_PYTHON -m scripts.atlas.word_card_foundation verify --manifest pilot.json --manifest golden.json "
        "--registry registry.json --heldout-manifest pools.json\n"
        "Outputs: freeze writes an immutable manifest; allocate atomically replaces the registry; verify writes nothing.\n"
        "Sources are read-only; literal row hashes and main/WAL file hashes have separate evidential roles.\n"
        "Exit codes: 0 operation succeeded (never certification); 1 source/data refusal; 2 usage error.\n"
        "Related: docs/atlas/word-cards/migration.md, #9293; no default input/output paths."
    )
    parser = argparse.ArgumentParser(
        description="Freeze admitted pilot/golden inputs and allocate pilot identities; preparation only, never evaluation.",
        epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("freeze", "allocate", "verify"):
        command = commands.add_parser(operation,
            description=f"{operation.title()} foundation inputs; normal data/source refusals exit 1.",
            epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
        names = ("selection", "sources-db", "atlas-db", "vesum-db", "source-register", "rules-version",
                 "normaliser-version", "output") if operation == "freeze" else ("manifest", "registry")
        for name in names:
            detail = "VERSION (rules-v1-draft or norm-v1)" if name.endswith("version") else "FILE (explicit path, no default)"
            command.add_argument("--" + name, required=True, type=str if name.endswith("version") else Path,
                **({"action": "append"} if operation == "verify" and name == "manifest" else {}),
                help=("Repeat for pilot and golden together; golden membership requires the pilot closure" if
                      operation == "verify" and name == "manifest" else
                      f"{name}: {detail}; selection needs a sibling *source-admission-receipt.json with report hash/path"))
        command.add_argument("--heldout-manifest", type=Path,
            help='Optional membership JSON {"heldout":["source:key"],"replay":[]}; default absent means isolation unverified')
        if operation == "verify":
            command.add_argument("--for-evaluation", action="store_true",
                help="Request evaluation admission (default false); refused pending authenticated operator authority and thresholds")
    args = parser.parse_args(argv)
    try:
        paths = args.manifest if args.operation == "verify" else []
        manifests = [load(path) for path in paths]
        for item, path in zip(manifests, paths, strict=True):
            manifest_check(item, path)
        if args.operation == "verify":
            require(1 <= len(manifests) <= 2, "Verify requires one manifest or a pilot/golden pair")
            kinds = [m.get("kind", "pilot") for m in manifests]
            require(len(manifests) == 1 or set(kinds) == {"pilot", "golden"},
                    "Joint verify requires exactly one pilot and one golden manifest")
            require(not args.heldout_manifest or "golden" not in kinds or "pilot" in kinds,
                    "Golden heldout verification requires the pilot manifest")
        manifest = manifests[0] if manifests else (
            freeze(args) if args.operation == "freeze" else load(args.manifest))
        if args.operation != "verify":
            manifest_check(manifest, args.manifest if args.operation != "freeze" else None)
        require(args.operation != "allocate" or manifest.get("kind", "pilot") == "pilot",
                "Golden cases are not pilot identity allocations")
        registry = allocate(args, manifest) if args.operation == "allocate" else (
            load(args.registry) if args.operation == "verify" else None)
        if args.operation == "verify":
            registry_check(registry)
            for item in manifests:
                if item.get("kind", "pilot") == "pilot":
                    allocation_check(item, registry)
            require(not args.for_evaluation, "Evaluation refused: authenticated operator authority/signature and "
                    "acceptance thresholds are not established; Gate 2 remains open")
        pilot = next((m for m in manifests if m.get("kind", "pilot") == "pilot"), None)
        checked = isolation([*manifests, registry] if manifests else [manifest, registry], args.heldout_manifest,
                            (*("manifest" for _ in manifests[1:]), "registry"),
                            pilot=pilot if len(manifests) == 2 else None)
        unresolved = [u["unit_key"] for u in manifest["selection"]["units"] if not u["atlas_slug"]]
        # Only this build's identities are verified; other builds' events are retained, unverified history.
        foreign = None if registry is None else sum(
            e["build_id"] != "pilot@sha256:" + manifest["manifest_sha256"] for e in registry["events"])
        print(json.dumps({"operation": args.operation, "counts": manifest["counts"], "foreign_build_events": foreign,
                          "unresolved_card_mappings": unresolved, "supplementary_correspondence": "unresolved",
                          "heldout_isolation": checked, "evaluation_readiness": "unknown"}, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, AttributeError, IndexError,
            RecursionError, yaml.YAMLError) as error:
        message = str(error) if isinstance(error, Refusal) else "Invalid or inaccessible input; check schema and readable sources"
        print("REFUSED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
