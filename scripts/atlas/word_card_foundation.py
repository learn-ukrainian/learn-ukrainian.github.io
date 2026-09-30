"""Pilot-only source freeze and legacy identity bootstrap (#9293).

Immutable row captures are the reusable source inputs; no lexical matching.
"""

import argparse
import copy
import fcntl
import hashlib
import json
import re
import secrets
import sqlite3
import sys
from contextlib import ExitStack, suppress
from pathlib import Path

import jsonschema
import yaml

from scripts.curriculum.evidence.lock import atomic_write

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs/sources/permissions-register.yaml"
ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
ROW_BASIS = "sha256 canonical UTF-8 JSON of entire literal selected row, not whole database"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key; remove conflicting fields")
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)


def write(path, value):
    # One complete logical record per line, rather than compressing whole arrays.
    def render(value, depth=0):
        indent = "  " * depth
        if isinstance(value, dict) and any(isinstance(v, list | dict) for v in value.values()):
            return "{\n" + ",\n".join(indent + "  " + json.dumps(k) + ": " + render(v, depth + 1) for k, v in value.items()) + "\n" + indent + "}"
        if isinstance(value, list) and value:
            return "[\n" + ",\n".join(indent + "  " + canonical(row).decode() for row in value) + "\n" + indent + "]"
        return canonical(value).decode()
    atomic_write(path, (render(value) + "\n").encode())


def schema(value, name):
    validator = jsonschema.Draft202012Validator(load(ROOT / "schemas" / name))
    require(not next(validator.iter_errors(value), None), f"Invalid {name}; restore required schema fields")


def readonly(stack, path):
    require(path.is_absolute() and path.is_file(), "Source DB must be an existing absolute file")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    stack.callback(connection.close)
    stack.enter_context(connection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")
    return connection


def rows(connection, table, key):
    require(bool(key) and all(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", n) for n in [table, *key]),
            "Invalid row selector; use literal table and column names")
    where = " AND ".join(f'"{column}" = ?' for column in key)
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" WHERE {where}', tuple(key.values()))]


def strings(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(strings(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(strings(v) for v in value))
    return {value} if isinstance(value, str) else set()


def isolation(inputs, heldout):
    if heldout is None:
        return "unverified"
    membership = load(heldout)
    require(set(membership) == {"heldout", "replay"}, "Membership requires heldout/replay key lists only")
    require(all(isinstance(v, list) and all(isinstance(k, str) and k for k in v) for v in membership.values()),
            "Membership keys must be nonempty strings")
    boundary = set(membership["heldout"])
    require(boundary and not boundary.intersection(membership["replay"]), "Heldout and replay must be disjoint")
    # Follow identity/alias references to fixed point without treating source labels as identities.
    groups = []
    def visit(value):
        if isinstance(value, str) and value.lstrip()[:1] in {"[", "{"}:
            with suppress(json.JSONDecodeError):
                visit(json.loads(value))
        if isinstance(value, dict):
            if "source_record_id" in value or "card_id" in value:
                creation = value.get("key_at_creation", {})
                group = {a["key"] for a in value.get("aliases", [])} | set(creation.get("source_keys", []))
                group |= {a["alias"] for a in creation.get("aliases", [])}
                group |= {value.get("source_record_id", ""), value.get("card_id", "")}
                group.discard("")
                groups.append(group)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(inputs)
    while True:
        expanded = boundary | set().union(*(g for g in groups if g & boundary))
        if expanded == boundary:
            break
        boundary = expanded
    def inspect(value):
        if isinstance(value, str) and value.lstrip()[:1] in {"[", "{"}:
            with suppress(json.JSONDecodeError):
                inspect(json.loads(value))
        if isinstance(value, dict):
            require(not any(k.startswith(("expected", "adjudicated")) for k in value),
                    "Held-out expected answers are forbidden in admitted inputs")
            adjudication = value.get("kind") in {"identity", "split", "merge", "resolve", "variant", "sense_map"}
            adjudication |= any(k in value for k in ("overlay_id", "settled_by", "mapping", "merged_into", "split_into"))
            require(not (adjudication and strings(value) & boundary),
                    "Held-out adjudicated mapping touches a membership key or indirect alias; remove it")
            for item in value.values():
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
    inspect(inputs)
    return "checked"


def selection_check(selection, registered):
    require(selection["schema_version"] == "atlas-pilot-selection-candidate.v2", "Unsupported selection schema")
    records, units = selection["source_records"], selection["units"]
    locators = [r["locator"] for r in records]
    require(len(set(locators)) == len(records), "Duplicate selected rows; retain distinct literal locators")
    require(len({u["unit_key"] for u in units}) == len(units), "Duplicate candidate units")
    require(len({u["anchor_locator"] for u in units}) == len(units), "Duplicate source-supported anchor partitions")
    for record in records:
        require(record["source_id"] in registered, "Unregistered source; update approved register first")
        require(record["row_key"] and record["table"] and record["locator"], "Missing row metadata")
        require(all(record["raw_row"].get(k) == v for k, v in record["row_key"].items()), "Row selector disagrees with literal capture")
        locator = ("atlas0:enrichment:" + record["row_key"]["slug"] + "/" + record["row_key"]["section"] if record["table"] == "enrichment" else f'{record["source_id"]}:{record["table"]}:id:{record["row_key"]["id"]}')
        require(record["locator"] == locator, "Literal locator disagrees with source row selector")
        require(record["content_fingerprint_basis"] == ROW_BASIS, "Label digest as selected-row, not full DB")
        require(digest(record["raw_row"]) == record["content_sha256"], "Changed selected bytes; re-admit the input")
        require(record["snapshot_id"] == "selected-row@sha256:" + record["content_sha256"], "Invalid selected-row snapshot")
        require(record["source_content_sha256"] == record["raw_row"].get("content_sha256"), "Source content hash mismatch")
        require(record.get("database", "sources") in {"sources", "atlas", "vesum"}, "Unknown source database")
        if record["source_id"] == "ulif" and record["table"] == "ulif_dictua_entries":
            raw = record["raw_row"]
            require(raw["homonym_checked"] == 1 and raw["status"] == "ok" and raw["parser_version"], "ULIF row lacks mandatory checked provenance")
            require(raw["retrieved_at"] and raw["content_sha256"] and raw["raw_response_ref"], "Missing ULIF provenance")
        if record["source_id"] == "ukrainian_word_stress":
            require(record["lineage_status"] == "unknown" and record["lineage_basis"], "Preserve unknown lineage explicitly")
    for unit in units:
        require(unit["entry_type"] in {"lexeme_candidate", "mwe_candidate"}, "Unknown candidate kind")
        require(unit["counting_basis"] and unit["cefr_basis"] and unit["atlas_mapping_basis"], "Missing partition or mapping basis")
        require(unit["supplementary_correspondence"] == "unresolved", "No cross-source matching in foundation")
        require(unit["anchor_locator"] in unit["source_record_keys"] and set(unit["source_record_keys"]) <= set(locators), "Missing source reference")
    require(set(locators) == set().union(*(set(u["source_record_keys"]) for u in units)), "Unreferenced source record")
    counts = {"units": len(units), "source_records": len(records), "atlas_articles": len({u["atlas_slug"] for u in units if u["atlas_slug"]})}
    require(counts == selection["denominator"] and counts["units"] == 150, "Pilot denominator drift; require exactly 150 admitted units")
    return counts


def manifest_check(manifest):
    require(manifest["schema_version"] == "atlas-word-card-foundation.v1", "Unsupported frozen manifest")
    require(manifest["manifest_sha256"] == digest({k: v for k, v in manifest.items() if k != "manifest_sha256"}), "Changed manifest bytes/content; restore admitted freeze")
    require(manifest["rules_version"] == "rules-v1-draft" and manifest["normaliser_version"] == "norm-v1", "Unapproved rules or normaliser version")
    register = yaml.safe_load(REGISTER.read_bytes())
    schema(register, "permissions-register.schema.json")
    require(file_digest(REGISTER) == manifest["selection"]["source_register_sha256"], "Register fingerprint mismatch; re-admit before reuse")
    require(digest(manifest["selection"]) == manifest["selection_content_sha256"], "Selection content fingerprint mismatch")
    original = (json.dumps(manifest["selection"], ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    require(hashlib.sha256(original).hexdigest() == manifest["selection_file_sha256"], "Admitted selection bytes changed; preserve original serialization")
    counts = selection_check(manifest["selection"], {s["id"] for s in register["sources"]})
    require(manifest["admission"]["admission"] == "APPROVE" and manifest["admission"]["candidate_sha256"] == manifest["selection_file_sha256"], "Missing source admission")
    require(manifest["admission"]["author_seat_distinct"] and manifest["admission"]["review_family"] == "google" and manifest["admission"]["denominator"] == counts, "Require independent source admission with exact denominators")
    inventory = manifest["legacy_articles"]
    require({a["raw_row"]["slug"] for a in inventory} == {u["atlas_slug"] for u in manifest["selection"]["units"] if u["atlas_slug"]}, "Legacy inventory mismatch")
    require(len(inventory) == counts["atlas_articles"], "Duplicate legacy inventory")
    for article in inventory:
        require(article["content_sha256"] == digest(article["raw_row"]), "Changed legacy article capture")
        require(all(a["target_slug"] == article["raw_row"]["slug"] for a in article["aliases"]), "Alias target outside inventory")
        require(len({canonical(a) for a in article["aliases"]}) == len(article["aliases"]), "Duplicate legacy aliases")
    require(manifest["counts"] == counts | {"legacy_alias_rows": sum(len(a["aliases"]) for a in inventory)}, "Incorrect separate denominators")
    require(set(manifest["database_file_sha256"]) == {"sources", "atlas", "vesum"} and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in manifest["database_file_sha256"].values()), "Missing frozen DB fingerprints")
    return counts


def freeze(args):
    selection = load(args.selection)
    receipts = list(args.selection.parent.glob("*source-admission-receipt.json"))
    require(len(receipts) == 1, "Place one driver source-admission-receipt.json beside selection")
    receipt = load(receipts[0])
    require(receipt["admission"] == "APPROVE" and receipt["candidate_sha256"] == file_digest(args.selection), "Driver admission does not bind selected bytes")
    require(file_digest(Path(receipt["review_report_path"])) == receipt["review_report_sha256"], "Admission report fingerprint mismatch")
    register = yaml.safe_load(args.source_register.read_bytes())
    schema(register, "permissions-register.schema.json")
    require(file_digest(args.source_register) == selection["source_register_sha256"], "Source register fingerprint mismatch")
    counts = selection_check(selection, {s["id"] for s in register["sources"]})
    isolation([selection, receipt, register], args.heldout_manifest)
    databases = {n: getattr(args, n + "_db") for n in ("sources", "atlas", "vesum")}
    inputs = [*databases.values(), args.selection, args.source_register, receipts[0], Path(receipt["review_report_path"])]
    require(args.output.resolve() not in {p.resolve() for p in inputs}, "Output must be separate from every input/source file")
    before = {n: file_digest(p) for n, p in databases.items()}
    inventory = []
    with ExitStack() as stack:
        connections = {n: readonly(stack, p) for n, p in databases.items()}
        for record in selection["source_records"]:
            actual = rows(connections[record.get("database", "sources")], record["table"], record["row_key"])
            require(actual == [record["raw_row"]], "Selected literal row mismatch; stop and re-admit source version")
        for slug in sorted({u["atlas_slug"] for u in selection["units"] if u["atlas_slug"]}):
            articles = rows(connections["atlas"], "articles", {"slug": slug})
            require(len(articles) == 1, "Missing or duplicate legacy article; no invented mappings")
            inventory.append({"raw_row": articles[0], "content_sha256": digest(articles[0]),
                              "aliases": sorted(rows(connections["atlas"], "aliases", {"target_slug": slug}), key=canonical)})
        require(before == {n: file_digest(p) for n, p in databases.items()}, "Source file mutation detected; no freeze written")
    admission = {k: v for k, v in receipt.items() if not k.endswith("path") and k != "independent_raw_row_proof"}
    manifest = {"schema_version": "atlas-word-card-foundation.v1", "selection": selection,
                "selection_file_sha256": file_digest(args.selection), "selection_content_sha256": digest(selection),
                "admission": admission, "database_file_sha256": before, "rules_version": args.rules_version,
                "normaliser_version": args.normaliser_version, "counts": counts | {"legacy_alias_rows": sum(len(a["aliases"]) for a in inventory)},
                "legacy_articles": inventory}
    manifest["manifest_sha256"] = digest(manifest)
    manifest_check(manifest)
    isolation(manifest, args.heldout_manifest)
    write(args.output, manifest)
    return manifest


def registry_check(registry):
    schema(registry, "word-card-identity-registry-v1.schema.json")
    identities = [e["card_id"] for e in registry["entries"]] + [r["source_record_id"] for r in registry["source_records"]]
    identities += [s["sense_id"] for e in registry["entries"] for s in e["senses"]]
    require(len(identities) == len(set(identities)), "Reused identity; restore prior registry")
    ids = set(identities)
    require(len({e["event_id"] for e in registry["events"]}) == len(registry["events"]), "Duplicate history event")
    minted = []
    for event in registry["events"]:
        references = event.get("cards", []) + event.get("from", []) + event.get("to", [])
        require(set(references) <= ids, "History references missing identity")
        if event["kind"] in {"mint", "sense_mint", "source_record_mint"}:
            targets = event.get("cards", []) if event["kind"] == "mint" else event.get("to", [])
            require(len(targets) == 1 and event["evidence"] and event["build_id"], "Inconsistent mint history")
            require(targets[0].startswith({"mint": "wc_", "sense_mint": "ws_", "source_record_mint": "sr_"}[event["kind"]]), "Wrong mint identity type")
            minted.extend(targets)
    require(len(minted) == len(ids) and set(minted) == ids, "Missing or duplicate mint history")
    graph = {e["card_id"]: e.get("split_into", []) + ([e["merged_into"]] if "merged_into" in e else []) for e in registry["entries"]}
    def acyclic(node, trail):
        require(node in ids and node not in trail, "Missing or cyclic identity reference")
        for target in graph.get(node, []):
            acyclic(target, trail | {node})
    for node in graph:
        acyclic(node, set())
    keys = [canonical(e["key_at_creation"]) for e in registry["entries"]]
    require(len(set(keys)) == len(keys), "Duplicate creation key allocated twice")
    observations = []
    for record in registry["source_records"]:
        aliases = record["aliases"]
        require(len({canonical(a) for a in aliases}) == len(aliases), "Duplicate alias history")
        require(len({c["snapshot_id"] for c in record["correspondence"]}) == len(record["correspondence"]), "Duplicate correspondence history")
        for c in record["correspondence"]:
            require(any(a["snapshot_id"] == c["snapshot_id"] for a in aliases), "Correspondence has no observed aliases")
            if c["status"] == "unique":
                require(any(a["key"] == c["locator"] and a["snapshot_id"] == c["snapshot_id"] for a in aliases), "Unique correspondence lacks locator alias")
                observations.append((record["source_id"], c["snapshot_id"], c["locator"]))
    require(len(set(observations)) == len(observations), "Source row allocated twice")


def aliases(record):
    raw, snapshot = record["raw_row"], record["snapshot_id"]
    evidence = [("table_row", record["locator"]), ("content", record["content_sha256"])]
    if raw.get("register_position"):
        evidence.append(("register_position", raw["register_position"]))
    if "normalized_query" in raw and "canonical_headword" in raw:
        evidence.append(("query_headword_label", "#".join(str(raw[k]) for k in ("normalized_query", "canonical_headword", "grammatical_label"))))
    return [{"kind": kind, "key": key, "snapshot_id": snapshot} for kind, key in evidence]


def allocation_check(manifest, registry, complete=True):
    registry_check(registry)
    build = "pilot@sha256:" + manifest["manifest_sha256"]
    cards, sources = [], []
    for article in manifest["legacy_articles"]:
        key = "atlas0:slug:" + article["raw_row"]["slug"]
        matches = [e for e in registry["entries"] if key in e["key_at_creation"].get("source_keys", [])]
        require(len(matches) <= 1, "Legacy alias maps to multiple initial allocations")
        if matches:
            require(matches[0]["key_at_creation"] == {"source_keys": [key], "aliases": article["aliases"]}, "Legacy alias capture/history mismatch")
            cards.append(matches[0]["card_id"])
    for record in manifest["selection"]["source_records"]:
        matches = [r for r in registry["source_records"] if r["source_id"] == record["source_id"] and any(c.get("locator") == record["locator"] and c["snapshot_id"] == record["snapshot_id"] for c in r["correspondence"])]
        require(len(matches) <= 1, "Source row has multiple allocations")
        if matches:
            require(all(a in matches[0]["aliases"] for a in aliases(record)), "Inconsistent source alias history")
            sources.append(matches[0]["source_record_id"])
    finished = len(cards) == manifest["counts"]["atlas_articles"] and len(sources) == manifest["counts"]["source_records"]
    minted = {i for e in registry["events"] if e["build_id"] == build for i in e.get("cards", []) + e.get("to", [])}
    require(minted <= set(cards + sources), "Allocation history exceeds frozen pilot inventory")
    require(finished or not (complete or any(e["build_id"] == build for e in registry["events"])), "Partial allocation; restore the atomic prior registry")
    return cards, sources


def allocate(args, manifest):
    require(args.registry.resolve() != args.manifest.resolve(), "Registry output must be separate from frozen manifest")
    args.registry.parent.mkdir(parents=True, exist_ok=True)
    with args.registry.with_suffix(".lock").open("a") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX)
        registry = load(args.registry) if args.registry.exists() else {"schema_version": "1", "registry_version": 1, "entries": [], "source_records": [], "events": []}
        isolation([manifest, registry], args.heldout_manifest)
        _cards, sources = allocation_check(manifest, registry, False)
        original = copy.deepcopy(registry)
        occupied = strings(registry)
        build = "pilot@sha256:" + manifest["manifest_sha256"]
        def mint(prefix):
            identity = prefix + "".join(secrets.choice(ALPHABET) for _ in range(12))
            require(identity not in occupied, "Random identifier reuse; allocation refused without write")
            occupied.add(identity)
            return identity
        def event(kind, identity, evidence):
            number = max([int(e["event_id"][3:]) for e in registry["events"]], default=0) + 1
            registry["events"].append({"event_id": f"ie_{number:04d}", "kind": kind, "build_id": build,
                                       "cards" if kind == "mint" else "to": [identity], "evidence": evidence})
        for article in manifest["legacy_articles"]:
            key = "atlas0:slug:" + article["raw_row"]["slug"]
            if not any(key in e["key_at_creation"].get("source_keys", []) for e in registry["entries"]):
                identity = mint("wc_")
                registry["entries"].append({"card_id": identity, "card_kind": "mwe" if article["raw_row"]["entry_type"] == "multiword_term" else "lexeme", "state": "active", "key_at_creation": {"source_keys": [key], "aliases": article["aliases"]}, "created_in_build": build, "senses": []})
                event("mint", identity, key)
        for record in manifest["selection"]["source_records"]:
            if not any(r["source_record_id"] in sources and any(c.get("locator") == record["locator"] and c["snapshot_id"] == record["snapshot_id"] for c in r["correspondence"]) for r in registry["source_records"]):
                identity = mint("sr_")
                registry["source_records"].append({"source_record_id": identity, "source_id": record["source_id"], "aliases": aliases(record), "correspondence": [{"snapshot_id": record["snapshot_id"], "status": "unique", "locator": record["locator"], "matched_by": "direct observation of full literal selected row"}]})
                event("source_record_mint", identity, record["locator"])
        if registry != original:
            registry["registry_version"] += bool(args.registry.exists())
            allocation_check(manifest, registry)
            isolation([manifest, registry], args.heldout_manifest)
            write(args.registry, registry)
        return registry


def main(argv=None):
    epilog = ("Examples (PROJECT_PYTHON = shared project interpreter): PROJECT_PYTHON -m scripts.atlas.word_card_foundation verify --manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json\n"
              "Outputs: freeze writes a manifest; allocate atomically replaces the registry; verify writes nothing. Sources are read-only.\n"
              "Exit codes: 0 operation succeeded (never certification); 1 source/data refusal; 2 usage error.\n"
              "Related: docs/atlas/word-cards/migration.md, #9293; no default input/output paths.")
    parser = argparse.ArgumentParser(description="Freeze admitted sources and bootstrap persistent pilot identities.\nUse for preparation, never matcher or product certification.", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("freeze", "allocate", "verify"):
        command = commands.add_parser(operation, description=f"{operation.title()} pilot foundation inputs; normal data/source refusals exit 1.", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
        names = ("selection", "sources-db", "atlas-db", "vesum-db", "source-register", "rules-version", "normaliser-version", "output") if operation == "freeze" else ("manifest", "registry")
        for name in names:
            detail = "VERSION (rules-v1-draft or norm-v1)" if name.endswith("version") else "FILE (explicit path, no default)"
            command.add_argument("--" + name, required=True, type=str if name.endswith("version") else Path, help=f"{name}: {detail}; selection needs a sibling *source-admission-receipt.json with report hash/path")
        command.add_argument("--heldout-manifest", type=Path, help='Optional membership JSON {"heldout":["source:key"],"replay":[]}; default absent means isolation unverified')
        if operation == "verify":
            command.add_argument("--for-evaluation", action="store_true", help="Request evaluation admission (default false); refused pending authenticated operator authority and thresholds")
    args = parser.parse_args(argv)
    try:
        manifest = freeze(args) if args.operation == "freeze" else load(args.manifest)
        manifest_check(manifest)
        registry = allocate(args, manifest) if args.operation == "allocate" else load(args.registry) if args.operation == "verify" else None
        checked = isolation([manifest, registry], args.heldout_manifest)
        if args.operation == "verify":
            allocation_check(manifest, registry)
            require(not args.for_evaluation, "Evaluation refused: authenticated operator authority/signature and acceptance thresholds are not established; Gate 2 remains open")
        unresolved = [u["unit_key"] for u in manifest["selection"]["units"] if not u["atlas_slug"]]
        print(json.dumps({"operation": args.operation, "counts": manifest["counts"], "unresolved_card_mappings": unresolved, "supplementary_correspondence": "unresolved", "heldout_isolation": checked, "evaluation_readiness": "unknown"}, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as error:
        print("REFUSED: " + str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else "REFUSED: invalid or inaccessible input; check schema, required metadata and readable source files", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
