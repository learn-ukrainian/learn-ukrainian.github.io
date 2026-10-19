"""Frozen, source-only universe builds and independent reconciliation (#10516).

Candidates come from the source assembler. This module never generates language,
grants reviews, or exports cards. A checkpoint is private work, not acceptance.
"""

from __future__ import annotations

import hashlib
import platform
import shutil
import sqlite3
import sys
from contextlib import closing
from contextvars import Context
from pathlib import Path

from scripts.atlas import word_card_certification as cert
from scripts.atlas import word_card_golden_set as gold
from scripts.atlas.word_card_assembly import require_host_only

DIMENSIONS = ("spellings", "lexemes", "senses", "mwes", "forms")
CHECKS = ("source_fidelity", "scope", "citations", "withdrawals", "reimports",
          "resumed_builds", "homonyms", "senses", "mwes")
NULL_TEXT = {"anyOf": [gold.TEXT, {"type": "null"}]}
INVENTORY = gold.obj({
    "schema_version": {"const": "word-card-universe-inventory.v1"},
    "accepted_by": gold.ACTOR,
    "members": gold.array(gold.obj({
        "member_id": gold.TEXT,
        **{name: gold.array(gold.TEXT, 0) for name in DIMENSIONS},
        "card_ids": gold.array(gold.TEXT, 0),
        "evidence": gold.array(gold.REF),
    })),
    "strata": gold.array(gold.obj({"unit_key": gold.SHA, "stratum": gold.TEXT})),
})
DISPOSITION = gold.obj({
    "unit_key": gold.SHA, "status": {"enum": ["mapped", "unresolved", "excluded"]},
    "cards": gold.array(gold.REF, 0), "reason": gold.TEXT,
    "owner": NULL_TEXT, "dependency": NULL_TEXT, "evidence": gold.array(gold.REF),
})
PLAN = gold.obj({"schema_version": {"const": "word-card-universe-plan.v1"},
                 "dispositions": gold.array(DISPOSITION)})
LIMITS = gold.obj({"batch_units": gold.COUNT, "max_card_bytes": gold.COUNT,
                   "min_free_bytes": gold.COUNT})
SPEC = gold.obj({
    "schema_version": {"const": "word-card-universe-spec.v1"},
    "author": gold.ACTOR, "source_spec": gold.REF, "inventory": gold.REF,
    "plan": gold.REF, "certifications": gold.array(gold.REF),
    "limits": LIMITS, "runtime_sha256": gold.SHA, "resource_acceptance": gold.REF,
})
RESOURCE = gold.obj({
    "schema_version": {"const": "word-card-universe-resources.v1"},
    "inputs_sha256": gold.SHA, "source_unit_count": gold.COUNT,
    "limits": LIMITS, "accepted_by": gold.ACTOR,
    "peak_rss_bytes": gold.COUNT, "rss_budget_bytes": gold.COUNT,
    "interrupted_after": gold.array(gold.COUNT),
    "uninterrupted": gold.REF, "resumed": gold.REF, "evidence": gold.array(gold.REF),
})
INSPECTION = gold.obj({
    "unit_key": gold.SHA, "check": {"enum": list(CHECKS)},
    "verdict": {"enum": ["pass", "not_applicable"]},
    "reason": gold.TEXT, "evidence": gold.array(gold.REF),
})
RECONCILIATION = gold.obj({
    "schema_version": {"const": "word-card-universe-reconciliation.v1"},
    "spec_sha256": gold.SHA, "source_unit_count": gold.COUNT,
    "dispositions_sha256": gold.SHA, "cards_sha256": gold.SHA,
    "accepted_by": gold.ACTOR, "inspections": gold.array(INSPECTION),
})


def unit_key(link: dict) -> str:
    """Retain source range, homonym, sense, path, and occurrence in identity."""
    gold.validate(link, gold.accounting.LINK, "source-unit link")
    return cert.digest(link)


def input_binding(spec: dict) -> str:
    """Resource trials bind all build inputs, without a circular proof digest."""
    return cert.digest({key: spec[key] for key in
                        ("author", "source_spec", "inventory", "plan", "certifications", "limits", "runtime_sha256")})


def runtime_fingerprint() -> str:
    """Bind resource trials to the current interpreter, SQLite and OS runtime."""
    return cert.digest({"python": sys.version, "sqlite": sqlite3.sqlite_version,
                        "system": platform.system(), "release": platform.release(), "machine": platform.machine()})


def _document(ref: dict, base: Path, schema: dict, label: str) -> dict:
    value = gold.decode(gold.reference(ref, base))
    gold.validate(value, schema, label)
    return value


def _independent(actor: dict, author: dict) -> None:
    gold.require(actor["id"] != author["id"] and actor["family"] != author["family"],
                 "Independent acceptance required")


def _evidence(refs: list[dict], base: Path) -> None:
    for ref in refs:
        gold.reference(ref, base)


def _stream_digest(values) -> str:
    result = hashlib.sha256()
    for value in values:
        result.update(gold.canonical(value))
    return result.hexdigest()


def _enumerate(source_spec: dict, base: Path) -> tuple[dict, dict]:
    # This replays source indexes, stage accounting, complete-data acceptance,
    # and the lexical membership index. It does not consume held-out answers.
    universe, _ = gold.complete_data(source_spec, base)
    manifest = gold.decode(gold.reference(source_spec["inputs"]["source_manifest"], base))
    units = {}
    for source_range in manifest["ranges"]:
        gold.require(source_range["membership"] == "KNOWN", "Unknown source denominator")
        for row in source_range["units"]:
            link = {"range_id": source_range["range_id"], "identity": row["identity"]}
            key = unit_key(link)
            gold.require(key not in units, "Duplicate source unit")
            units[key] = {"source_unit": link, "sha256": row["sha256"], "members": []}
    members = {row["member_id"]: row for row in universe["members"]}
    gold.require(len(members) == len(universe["members"]), "Duplicate lexical member")
    for member in members.values():
        for link in member["source_units"]:
            key = unit_key(link)
            gold.require(key in units, "Lexical member outside source denominator")
            units[key]["members"].append(member["member_id"])
    gold.require(bool(units), "Empty source denominator")
    return units, members


def _inventory(ref: dict, base: Path, units: dict, members: dict, author: dict) -> dict:
    document = _document(ref, base, INVENTORY, "frozen lexical inventory")
    _independent(document["accepted_by"], author)
    inventory_base = (base / ref["path"]).parent
    rows = document["members"]
    gold.require(len(rows) == len(members) and {row["member_id"] for row in rows} == set(members),
                 "Missing or duplicate lexical inventory member")
    card_identities = {}
    for row in rows:
        gold.require(bool(row["spellings"]), "Missing source spelling inventory")
        identity = (tuple(sorted(row["lexemes"])), tuple(sorted(row["mwes"])))
        if row["card_ids"]:
            gold.require(0 < len(row["lexemes"]) + len(row["mwes"]) <= len(row["card_ids"]),
                         "Supportable lexical identities collapsed")
        for card_id in row["card_ids"]:
            gold.require(card_id not in card_identities or card_identities[card_id] == identity,
                         "Distinct lexical identities share a card")
            card_identities[card_id] = identity
        _evidence(row["evidence"], inventory_base)
    strata = document["strata"]
    gold.require(len(strata) == len(units) and {row["unit_key"] for row in strata} == set(units),
                 "Missing or duplicate source stratum")
    for row in strata:
        units[row["unit_key"]]["stratum"] = row["stratum"]
    return document


def _plan(spec: dict, base: Path, units: dict, inventory: dict, source_spec: dict) -> tuple[dict, dict, dict]:
    document = _document(spec["plan"], base, PLAN, "frozen disposition plan")
    plan_base = (base / spec["plan"]["path"]).parent
    rows = document["dispositions"]
    gold.require(len(rows) == len(units) and {row["unit_key"] for row in rows} == set(units),
                 "Missing, extra or duplicate disposition")
    receipts, eligible = {}, {}
    for ref in spec["certifications"]:
        receipt = cert.verify_certification_receipt(ref, base)
        certification_spec = _document(receipt["spec"], (base / ref["path"]).parent,
                                       cert.CERTIFICATION_SPEC, "certification specification")
        gold.require(certification_spec["complete_data_receipt"]["sha256"] ==
                     source_spec["inputs"]["complete_data_receipt"]["sha256"],
                     "Certification covers another source universe")
        receipts[ref["sha256"]] = receipt["cards"]
        for key, value in receipt["cards"].items():
            gold.require(key not in eligible or eligible[key] == value, "Conflicting certifications")
            eligible[key] = value
    cards, dispositions = {}, {}
    member_cards = {row["member_id"]: set(row["card_ids"]) for row in inventory["members"]}
    with cert.certification_run():
        for row in rows:
            _evidence(row["evidence"], plan_base)
            if row["status"] == "mapped":
                gold.require(bool(row["cards"]) and row["owner"] is None and row["dependency"] is None,
                             "Mapped unit needs cards and no hidden residual")
                ids = []
                for ref in row["cards"]:
                    gold.require((plan_base / ref["path"]).stat().st_size <= spec["limits"]["max_card_bytes"],
                                 "Card exceeds resource limit")
                    raw = gold.reference(ref, plan_base)
                    card = gold.decode(raw)
                    cert.load_certified_card_for_export(card)
                    gold.require(bool(card["assertions"]) and all(
                        assertion["producer"]["kind"] == "source_extract"
                        and all(assertion.get(key) for key in ("source_id", "snapshot_id", "locator"))
                        for assertion in card["assertions"]), "Only cited source-extract assertions are admitted")
                    card_id = card["card_id"]
                    gold.require(eligible.get(card_id) == cert.digest(card), "Card outside frozen certifications")
                    gold.require(card_id not in cards or gold.canonical(cards[card_id]) == gold.canonical(card),
                                 "Conflicting card identity")
                    cards[card_id] = card
                    ids.append(card_id)
                gold.require(len(set(ids)) == len(ids), "Duplicate mapped card")
                expected = set().union(*(member_cards[key] for key in units[row["unit_key"]]["members"]))
                gold.require(set(ids) == expected, "Card mapping differs from accepted lexical identity")
            else:
                gold.require(not row["cards"] and row["owner"] is not None and row["dependency"] is not None,
                             "Residual requires owner, dependency and no cards")
                ids = []
            dispositions[row["unit_key"]] = {
                **{key: row[key] for key in ("unit_key", "status", "reason", "owner", "dependency", "evidence")},
                "card_ids": sorted(ids), "source": units[row["unit_key"]],
                "card_hashes": {key: cert.digest(cards[key]) for key in sorted(ids)},
            }
    return dispositions, cards, receipts


def _resources(spec: dict, base: Path, count: int, output_sha: str) -> None:
    ref = spec["resource_acceptance"]
    proof = _document(ref, base, RESOURCE, "full-scale resource acceptance")
    proof_base = (base / ref["path"]).parent
    _independent(proof["accepted_by"], spec["author"])
    gold.require(proof["inputs_sha256"] == input_binding(spec)
                 and proof["source_unit_count"] == count and proof["limits"] == spec["limits"],
                 "Resource trial does not cover frozen full scale")
    gold.require(proof["peak_rss_bytes"] <= proof["rss_budget_bytes"], "Resource budget exceeded")
    gold.require(all(point < count for point in proof["interrupted_after"]), "Invalid interruption trial")
    for name in ("uninterrupted", "resumed"):
        # File hashing is streaming; full-scale output need not be read into RAM.
        trial = proof[name]
        with (proof_base / trial["path"]).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        gold.require(actual == trial["sha256"] == output_sha, "Full-scale resume output mismatch")
    _evidence(proof["evidence"], proof_base)


def _load(path: Path, expected: str, *, resource_trial: bool = False) -> dict:
    _, spec = gold.read(path, expected)
    gold.validate(spec, SPEC, "frozen universe specification")
    gold.require(spec["runtime_sha256"] == runtime_fingerprint(), "Resource runtime changed")
    base = path.parent
    source_spec = _document(spec["source_spec"], base, gold.SPEC, "complete source specification")
    source_base = (base / spec["source_spec"]["path"]).parent
    units, members = _enumerate(source_spec, source_base)
    inventory = _inventory(spec["inventory"], base, units, members, spec["author"])
    _independent(inventory["accepted_by"], source_spec["roles"]["assembler"])
    dispositions, cards, receipts = _plan(spec, base, units, inventory, source_spec)
    expected_cards = {key for member in inventory["members"] for key in member["card_ids"]}
    gold.require(set(cards) == expected_cards, "Supportable identity has no mapped card")
    output_sha = _stream_digest(dispositions[key] for key in sorted(dispositions))
    if not resource_trial:
        _resources(spec, base, len(units), output_sha)
    return {"spec": spec, "units": units, "inventory": inventory, "dispositions": dispositions,
            "cards": cards, "certifications": receipts, "dispositions_sha256": output_sha,
            "cards_sha256": _stream_digest(cards[key] for key in sorted(cards))}


def freeze_inventory(spec_path: Path, spec_sha256: str) -> dict:
    """Replay prerequisites before any checkpoint is created; return frozen counts.

    Pins, taxonomy and acceptance adapters are supplied by the independent
    steward. Hashes do not authenticate the steward or attest linguistic quality.
    """
    loaded = Context().run(_load, spec_path, spec_sha256)
    return {"spec_sha256": spec_sha256, "counts": _counts(loaded),
            "dispositions_sha256": loaded["dispositions_sha256"], "cards_sha256": loaded["cards_sha256"]}


def _counts(loaded: dict) -> dict:
    rows = loaded["inventory"]["members"]
    return {"source_units": len(loaded["units"]), "lexical_members": len(rows),
            **{name: len({value for row in rows for value in row[name]}) for name in DIMENSIONS},
            "cards": len(loaded["cards"])}


def _checkpoint(connection: sqlite3.Connection, expected: str) -> None:
    connection.execute("PRAGMA synchronous=FULL")
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS metadata (spec_sha256 TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS units (unit_key TEXT PRIMARY KEY, payload BLOB NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS cards (card_id TEXT PRIMARY KEY, payload BLOB NOT NULL)")
        rows = connection.execute("SELECT spec_sha256 FROM metadata").fetchall()
        if not rows:
            gold.require(connection.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 0
                         and connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == 0,
                         "Unbound checkpoint data")
            connection.execute("INSERT INTO metadata VALUES (?)", (expected,))
        else:
            gold.require(rows == [(expected,)], "Checkpoint belongs to another freeze")


def _verify_rows(connection: sqlite3.Connection, loaded: dict, *, complete: bool) -> int:
    count = 0
    seen_units = set()
    for key, payload in connection.execute("SELECT unit_key, payload FROM units"):
        gold.require(key not in seen_units and key in loaded["dispositions"]
                     and payload == gold.canonical(loaded["dispositions"][key]),
                     "Corrupt or extra checkpoint unit")
        seen_units.add(key)
        count += 1
    if complete:
        gold.require(count == len(loaded["units"]), "Incomplete checkpoint accounting")
    seen = set()
    for key, payload in connection.execute("SELECT card_id, payload FROM cards"):
        gold.require(key not in seen and key in loaded["cards"] and payload == gold.canonical(loaded["cards"][key]),
                     "Corrupt or extra checkpoint card")
        seen.add(key)
    needed = {card for key, in connection.execute("SELECT unit_key FROM units")
              for card in loaded["dispositions"][key]["card_ids"]}
    gold.require(seen == needed, "Checkpoint card accounting mismatch")
    return count


def build(spec_path: Path, spec_sha256: str, checkpoint: Path, *, max_units: int | None = None,
          resource_trial: bool = False) -> dict:
    """Commit bounded batches atomically. Every invocation replays current authority.

    max_units is a cooperative interruption boundary, not a smaller denominator.
    No publishable cards or completion proof are returned, even on the final batch.
    resource_trial permits measuring this implementation before resource acceptance;
    it waives no source or certification check. Reconciliation still requires resources.
    """
    gold.require(max_units is None or (type(max_units) is int and max_units > 0), "Invalid interruption limit")
    gold.require(type(resource_trial) is bool, "Invalid resource trial mode")
    require_host_only([checkpoint, *(Path(str(checkpoint) + suffix) for suffix in ("-journal", "-wal", "-shm"))])
    # A caller's export context must not retain authority across separate builds.
    loaded = Context().run(_load, spec_path, spec_sha256, resource_trial=resource_trial)
    limits = loaded["spec"]["limits"]
    gold.require(shutil.disk_usage(checkpoint.parent).free >= limits["min_free_bytes"], "Insufficient checkpoint space")
    with closing(sqlite3.connect(checkpoint)) as connection:
        _checkpoint(connection, spec_sha256)
        completed = _verify_rows(connection, loaded, complete=False)
        pending = [key for key in sorted(loaded["units"])
                   if connection.execute("SELECT 1 FROM units WHERE unit_key = ?", (key,)).fetchone() is None]
        allowance = len(pending) if max_units is None else min(max_units, len(pending))
        for offset in range(0, allowance, limits["batch_units"]):
            gold.require(shutil.disk_usage(checkpoint.parent).free >= limits["min_free_bytes"],
                         "Insufficient checkpoint space")
            batch = pending[offset:min(offset + limits["batch_units"], allowance)]
            with connection:
                for key in batch:
                    row = loaded["dispositions"][key]
                    for card_id in row["card_ids"]:
                        connection.execute("INSERT OR IGNORE INTO cards VALUES (?, ?)",
                                           (card_id, gold.canonical(loaded["cards"][card_id])))
                    connection.execute("INSERT INTO units VALUES (?, ?)", (key, gold.canonical(row)))
            completed += len(batch)
    status = "BUILT_UNRECONCILED" if completed == len(loaded["units"]) else "INTERRUPTED"
    if resource_trial:
        status = "RESOURCE_TRIAL_" + status
    return {"status": status, "spec_sha256": spec_sha256,
            "source_units": len(loaded["units"]), "accounted_units": completed}


def reconcile(spec_path: Path, spec_sha256: str, checkpoint: Path,
              independent_proof: dict, proof_base: Path) -> dict:
    """Re-enumerate source-side inputs, verify every stored row, and bind held-out inspection.

    This returns private accounting evidence. Export must still use the Phase 5
    boundary afresh; reconciliation does not change the review ledger.
    """
    loaded = Context().run(_load, spec_path, spec_sha256)
    proof = _document(independent_proof, proof_base, RECONCILIATION, "independent reconciliation")
    _independent(proof["accepted_by"], loaded["spec"]["author"])
    gold.require(proof["spec_sha256"] == spec_sha256 and proof["source_unit_count"] == len(loaded["units"])
                 and proof["dispositions_sha256"] == loaded["dispositions_sha256"]
                 and proof["cards_sha256"] == loaded["cards_sha256"], "Independent reconciliation binding mismatch")
    coverage = set()
    for inspection in proof["inspections"]:
        key = inspection["unit_key"]
        gold.require(key in loaded["units"], "Inspection outside frozen denominator")
        unit = loaded["units"][key]
        coverage.add((unit["source_unit"]["range_id"], unit["stratum"], inspection["check"]))
        _evidence(inspection["evidence"], (proof_base / independent_proof["path"]).parent)
    needed = {(unit["source_unit"]["range_id"], unit["stratum"], check)
              for unit in loaded["units"].values() for check in CHECKS}
    gold.require(coverage == needed, "Missing source or failure-stratum inspection")
    # Read-only opening prevents a missing checkpoint from becoming an empty DB.
    with closing(sqlite3.connect(checkpoint.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        gold.require(connection.execute("SELECT spec_sha256 FROM metadata").fetchall() == [(spec_sha256,)],
                     "Checkpoint belongs to another freeze")
        _verify_rows(connection, loaded, complete=True)
    partitions = {state: sum(row["status"] == state for row in loaded["dispositions"].values())
                  for state in ("mapped", "unresolved", "excluded")}
    gold.require(sum(partitions.values()) == len(loaded["units"]), "Source conservation failed")
    residuals = [{"unit_key": key, "status": row["status"], "reason": row["reason"],
                  "owner": row["owner"], "dependency": row["dependency"]}
                 for key, row in sorted(loaded["dispositions"].items()) if row["status"] != "mapped"]
    return {"schema_version": "word-card-universe-receipt.v1", "status": "RECONCILED",
            "spec_sha256": spec_sha256, "counts": _counts(loaded), "partitions": partitions,
            "missing_units": 0, "duplicate_units": 0,
            "dispositions_sha256": loaded["dispositions_sha256"], "cards_sha256": loaded["cards_sha256"],
            "certifications": loaded["certifications"], "independent_proof": independent_proof,
            "by_source": _partitions(loaded, source=True), "by_stratum": _partitions(loaded, source=False),
            "residuals": residuals, "programme_completion": "UNRESOLVED", "export_authorized": False}


def _partitions(loaded: dict, *, source: bool) -> dict:
    groups = {}
    for row in loaded["dispositions"].values():
        key = row["source"]["source_unit"]["range_id"] if source else row["source"]["stratum"]
        counts = groups.setdefault(key, {"source_units": 0, "mapped": 0, "unresolved": 0, "excluded": 0})
        counts["source_units"] += 1
        counts[row["status"]] += 1
    return dict(sorted(groups.items()))
