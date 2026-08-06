#!/usr/bin/env python3
"""Compile cleared Phase 3 source units into private rule-author packets.

This is a deliberately narrow, local-only boundary.  It consumes an explicit
steward allowlist and source material supplied by the caller.  It never opens a
held-out seal, learns a complement set, calls a model, or makes a Ukrainian
normative decision.  Packet files can contain rights-limited source spans and
are therefore accepted only below an ignored ``batch_state`` directory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_near_duplicate as near_duplicate
from scripts.projects.open_model_data import phase3_source_universe as source_universe

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
SCHEMA_PATH = CONTRACTS / "phase3_rule_author_packet_bundle_v1.schema.json"
CLEARANCE_SCHEMA_PATH = CONTRACTS / "phase3_heldout_partition_bundle_v1.schema.json"
SCRIPT_PATH = "scripts/projects/open_model_data/phase3_rule_author_packets.py"
IMPLEMENTATION_VERSION = "phase3_rule_author_packet_compiler_v1"
COMBINED_CONTRACT_SHA256 = "bf387adaeb180d11ade272819d77e1eb3d3fdecc43982fff9c775039c9e0bed7"
MAX_ITEMS = 24
MAX_UTF8_BYTES = 196_608
# The canonical steward receipt currently clears only UA-GEC units.  The packet
# schema already carries the other planned source families, but this compiler
# must fail closed until those families receive their own steward-sealed author
# clearances rather than inferring a public/non-heldout complement.
AUTHOR_FAMILIES = frozenset({"ua_gec"})
LEDGER_RECEIPT = "source-universe-freeze-receipt.json"
SHA256 = re.compile(r"^[a-f0-9]{64}$")


class PacketCompilerError(ValueError):
    """Inputs do not establish a safe author-facing packet boundary."""


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically for every identity and byte limit."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(namespace: str, value: Mapping[str, Any]) -> str:
    return f"{namespace}:{sha256_bytes(canonical_json(value).encode('utf-8'))}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PacketCompilerError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketCompilerError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise PacketCompilerError(f"invalid JSONL input at {path}:{line_number}") from exc
                require(isinstance(value, dict), f"JSONL row must be an object at {path}:{line_number}")
                yield value
    except OSError as exc:
        raise PacketCompilerError(f"cannot read JSONL input: {path}") from exc


def _validator(name: str) -> Draft202012Validator:
    if name == "clearance":
        canonical = read_json(CLEARANCE_SCHEMA_PATH)
        Draft202012Validator.check_schema(canonical)
        return Draft202012Validator(
            {"$schema": canonical["$schema"], "$defs": canonical["$defs"], "$ref": "#/$defs/authorClearanceReceipt"}
        )
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    # Embedded resources have stable external IDs for consumers.  This compiler
    # validates the bundle as one local document, so remove only those nested
    # resource boundaries to keep root-local ``#/$defs`` references resolvable.
    schema = _local_schema(schema)
    # The subschemas use root-local refs.  Validate a wrapper retaining the
    # definitions rather than validating the subschema as an isolated resource.
    wrapper = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{name}"}
    return Draft202012Validator(wrapper)


def _local_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(schema))
    for definition in value.get("$defs", {}).values():
        if isinstance(definition, dict):
            definition.pop("$id", None)
    return value


def validate(value: Mapping[str, Any], name: str, label: str) -> None:
    errors = sorted(_validator(name).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise PacketCompilerError(f"{label} schema violation at {location}: {errors[0].message}")
    if name == "ruleAuthorResponse":
        for proposal in value.get("proposals", []):
            if isinstance(proposal, Mapping) and isinstance(proposal.get("matcher"), Mapping):
                require(
                    proposal.get("mechanism") == proposal["matcher"].get("kind"),
                    "proposal mechanism and typed matcher kind differ",
                )


def _sha(value: object, label: str) -> str:
    require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"invalid SHA-256: {label}")
    return value


def _output_is_private(path: Path) -> None:
    """Prevent accidentally writing raw source spans to tracked locations."""
    resolved = path.resolve()
    require("batch_state" in resolved.parts, "packet output must be under ignored batch_state")
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError:
        return
    ignored = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-q", "--", str(relative)],
        check=False,
        capture_output=True,
    )
    require(ignored.returncode == 0, "packet output path is not ignored by Git")


def receipt_body_sha256(receipt: Mapping[str, Any]) -> str:
    """Reproduce the steward's body hash without loading any private seal."""
    body = canonical_json({key: value for key, value in receipt.items() if key != "receipt_sha256"}) + "\n"
    return sha256_bytes(body.encode("utf-8"))


def _derive_role_actor(role_contract: Mapping[str, Any], expected_role: str) -> dict[str, str]:
    """Derive a current actor from the role contract; never accept it in clearance."""
    seats = role_contract.get("seats")
    bindings = role_contract.get("task_bindings")
    require(isinstance(seats, list) and isinstance(bindings, list), "role contract lacks seats or task bindings")
    assigned = [
        seat
        for seat in seats
        if isinstance(seat, Mapping)
        and seat.get("role_id") == expected_role
        and seat.get("assignment_state") == "assigned_verified"
        and seat.get("controller_identity_attested") is True
        and isinstance(seat.get("controller_identity_id"), str)
    ]
    require(len(assigned) == 1, f"role contract lacks one assigned {expected_role} seat")
    controller = str(assigned[0]["controller_identity_id"])
    matching = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping)
        and binding.get("role_id") == expected_role
        and binding.get("controller_identity_id") == controller
        and isinstance(binding.get("reserved_task_id"), str)
        and binding.get("status") in {"identity_attested_pre_artifact", "combined_contract_text_approved_pre_artifact"}
    ]
    require(len(matching) == 1, f"role contract lacks one active {expected_role} task binding")
    return {
        "controller_identity_id": controller,
        "role_id": expected_role,
        "task_id": str(matching[0]["reserved_task_id"]),
    }


def _validate_steward_binding(role_contract: Mapping[str, Any], role_binding: Mapping[str, Any]) -> dict[str, str]:
    require(role_binding.get("role_id") == "heldout_steward", "clearance role binding is not heldout steward")
    controller = role_binding.get("controller_identity_id")
    attestation_task = role_binding.get("attestation_task_id")
    require(
        isinstance(controller, str) and isinstance(attestation_task, str),
        "clearance steward role binding is incomplete",
    )
    seats = role_contract.get("seats")
    bindings = role_contract.get("task_bindings")
    require(isinstance(seats, list) and isinstance(bindings, list), "role contract lacks seats or task bindings")
    seat_ok = any(
        isinstance(seat, Mapping)
        and seat.get("role_id") == "heldout_steward"
        and seat.get("seat_id") == role_binding.get("seat_id")
        and seat.get("assignment_state") == "assigned_verified"
        and seat.get("controller_identity_id") == controller
        and seat.get("controller_identity_attested") is True
        for seat in seats
    )
    task_ok = any(
        isinstance(binding, Mapping)
        and binding.get("role_id") == "heldout_steward"
        and binding.get("controller_identity_id") == controller
        and binding.get("reserved_task_id") == attestation_task
        and binding.get("status") in {"identity_attested_pre_artifact", "combined_contract_text_approved_pre_artifact"}
        for binding in bindings
    )
    require(seat_ok and task_ok, "role contract does not bind heldout steward receipt")
    return {"controller_identity_id": controller, "role_id": "heldout_steward", "task_id": attestation_task}


def validate_clearance(
    clearance: Mapping[str, Any],
    *,
    clearance_sha256: str,
    receipt_sha256: str,
    evaluation_path: Path,
    coverage_path: Path,
    role_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a steward receipt without looking for or deriving heldout identities."""
    validate(clearance, "clearance", "clearance")
    require(receipt_body_sha256(clearance) == clearance.get("receipt_sha256"), "clearance receipt body hash drift")
    bindings = clearance["input_bindings"]
    require(
        bindings.get("combined_contract_sha256") == COMBINED_CONTRACT_SHA256,
        "clearance combined-contract binding drift",
    )
    require(bindings.get("source_universe_receipt_sha256") == receipt_sha256, "clearance source-freeze binding drift")
    require(
        bindings.get("evaluation_contract_sha256") == sha256_file(evaluation_path),
        "clearance evaluation-contract binding drift",
    )
    require(
        bindings.get("coverage_contract_sha256") == sha256_file(coverage_path),
        "clearance coverage-contract binding drift",
    )
    require(bindings.get("role_contract_sha256") == sha256_file(role_path), "clearance role-contract binding drift")
    role_contract = read_json(role_path)
    evaluation = read_json(evaluation_path)
    steward = _validate_steward_binding(role_contract, clearance["role_binding"])
    author = _derive_role_actor(role_contract, "rule_author_extractor")
    require(
        steward["controller_identity_id"] != author["controller_identity_id"],
        "steward and rule author controller identities must be distinct",
    )
    acl = role_contract.get("heldout_acl")
    require(isinstance(acl, Mapping), "role contract heldout ACL missing")
    require("heldout_steward" in set(acl.get("pre_release_read_roles", [])), "steward lacks pre-release heldout access")
    require(
        "rule_author_extractor" in set(acl.get("forbidden_roles", []))
        and "rule_author_extractor" not in set(acl.get("pre_release_read_roles", []))
        and "rule_author_extractor" not in set(acl.get("post_release_scorer_roles", [])),
        "rule author is not excluded by heldout ACL",
    )
    author_seat = next(seat for seat in role_contract["seats"] if seat.get("role_id") == "rule_author_extractor")
    require(
        "read_heldout_text_locators_fingerprints_labels" in set(author_seat.get("must_not", [])),
        "rule-author heldout prohibition drift",
    )
    require(
        evaluation.get("heldout_access", {}).get("author_extractor_forbidden") is True,
        "evaluation contract permits author heldout access",
    )
    policy = near_duplicate.policy_for_governed_use(
        "public_canary_neighbour_exclusion",
        expected_fingerprint=str(bindings["near_duplicate_policy_fingerprint_sha256"]),
    )
    require(
        evaluation.get("near_duplicate_policy", {}).get("policy_fingerprint_sha256")
        == policy["policy_fingerprint_sha256"],
        "evaluation near-duplicate policy binding drift",
    )
    _sha(clearance_sha256, "clearance file")
    return role_contract, evaluation


def _load_frozen_units(source_universe_dir: Path) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, Any], str]:
    receipt_path = source_universe_dir / LEDGER_RECEIPT
    receipt = read_json(receipt_path)
    receipt_sha = sha256_file(receipt_path)
    require(receipt.get("schema_version") == "phase3_source_universe_freeze_v1", "wrong source-universe receipt")
    require(receipt.get("text_free") is True, "source-universe receipt is not text-free")
    frozen: dict[str, dict[str, dict[str, Any]]] = {}
    families = receipt.get("families")
    require(isinstance(families, list), "source-universe receipt lacks family ledgers")
    for family in families:
        if not isinstance(family, Mapping) or family.get("family_id") not in AUTHOR_FAMILIES:
            continue
        ledger_file, ledger_sha = family.get("ledger_file"), family.get("ledger_sha256")
        require(isinstance(ledger_file, str) and isinstance(ledger_sha, str), "author family lacks frozen ledger")
        ledger_path = source_universe_dir / ledger_file
        require(sha256_file(ledger_path) == ledger_sha, f"frozen ledger hash drift: {family['family_id']}")
        rows: dict[str, dict[str, Any]] = {}
        for row in iter_jsonl(ledger_path):
            unit_id, unit_sha = row.get("unit_id"), row.get("unit_sha256")
            require(isinstance(unit_id, str) and isinstance(unit_sha, str), "frozen ledger row lacks unit identity")
            require(unit_id not in rows, "frozen ledger contains duplicate unit ID")
            rows[unit_id] = row
        frozen[str(family["family_id"])] = rows
    return frozen, receipt, receipt_sha


def _unsafe_test_unit(row: Mapping[str, Any]) -> bool:
    values = (row.get("unit_id"), row.get("partition"), row.get("split"), row.get("source_locator"), row.get("locator"))
    return any(
        isinstance(value, str) and (value == "test" or "/test" in value or value.startswith("test/"))
        for value in values
    )


def _source_document_identity(row: Mapping[str, Any], family_id: str) -> str:
    if family_id == "ua_gec":
        source_record = row.get("source_record")
        require(isinstance(source_record, Mapping), "UA-GEC item lacks exact source record")
        doc_id = source_record.get("doc_id")
        require(isinstance(doc_id, (str, int)) and str(doc_id), "UA-GEC item lacks raw doc_id")
        # Annotation layer and partition deliberately do not participate.
        return "ua_gec_document:" + sha256_bytes(str(doc_id).encode("utf-8"))
    source = row.get("source_document_id", row.get("source_file", row.get("source_locator")))
    require(isinstance(source, str) and source, "source item lacks document identity")
    return f"{family_id}_document:" + sha256_bytes(source.encode("utf-8"))


def _item_from_row(row: Mapping[str, Any], clearance_sha: str, policy_sha: str) -> dict[str, Any]:
    family_id = row.get("family_id")
    require(family_id in AUTHOR_FAMILIES, "source row has non-author family")
    source_record = row.get("source_record")
    require(isinstance(source_record, Mapping), "source row lacks exact frozen source record")
    normalized_record = source_universe._normal(source_record)
    require(isinstance(normalized_record, Mapping), "source record normalization failed")
    require(not _unsafe_test_unit({**row, **normalized_record}), "test unit is forbidden from rule-author packets")
    for exclusion_flag in ("ua_eval", "public_canary_neighbour"):
        require(
            exclusion_flag not in row or row.get(exclusion_flag) is False,
            "source row is evaluation or canary-neighbour material",
        )
    unit_id, unit_sha = row.get("unit_id"), row.get("unit_sha256")
    require(isinstance(unit_id, str) and isinstance(unit_sha, str), "source row lacks frozen unit identity")
    source_id = normalized_record.get("id")
    require(isinstance(source_id, int), "UA-GEC source record lacks integer id")
    require(
        unit_id
        == source_universe._opaque_id(
            "unit.ua_gec",
            {"table": "ua_gec_errors", "identity": {"id": source_id}},
        ),
        "source record does not reproduce frozen unit ID",
    )
    require(
        unit_sha == source_universe._unit_hash(normalized_record),
        "source record does not reproduce frozen unit hash",
    )
    text = row.get("source_text")
    corrected_text = row.get("corrected_text")
    require(
        isinstance(text, str)
        and text
        and text == normalized_record.get("error")
        and isinstance(corrected_text, str)
        and corrected_text == normalized_record.get("correct"),
        "source row does not preserve the exact human correction pair",
    )
    start, end = row.get("span_start", 0), row.get("span_end", len(text))
    require(
        isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text), "invalid exact source span"
    )
    span = text[start:end]
    supplied_sha = row.get("source_sha256", sha256_bytes(span.encode("utf-8")))
    require(supplied_sha == sha256_bytes(span.encode("utf-8")), "source span hash drift")
    locator = row.get("locator", row.get("source_locator"))
    require(isinstance(locator, (str, Mapping)), "source row lacks immutable locator")
    layer = normalized_record.get("error_type")
    partition = normalized_record.get("partition")
    require(
        isinstance(layer, str) and layer and isinstance(partition, str) and partition, "source metadata is malformed"
    )
    annotator = normalized_record.get("annotator_id")
    source_lang = normalized_record.get("source_lang")
    is_native = normalized_record.get("is_native")
    require(
        isinstance(annotator, str)
        and annotator
        and isinstance(source_lang, str)
        and source_lang
        and isinstance(is_native, int),
        "UA-GEC correction provenance is malformed",
    )
    frozen = {"family_id": family_id, "unit_id": unit_id, "unit_sha256": unit_sha}
    identity = {"frozen_unit": frozen, "source_sha256": supplied_sha, "start": start, "end": end}
    candidate_signals = row.get("candidate_signals", [])
    require(
        isinstance(candidate_signals, list) and all(isinstance(signal, str) and signal for signal in candidate_signals),
        "candidate signals are malformed",
    )
    return {
        "schema_version": "phase3_rule_author_source_item_v1",
        "source_item_id": stable_id("rule_author_source", identity),
        "family_id": family_id,
        "frozen_unit": frozen,
        "source_document_identity": _source_document_identity(
            {**row, "source_record": normalized_record}, family_id
        ),
        "locator": {
            "kind": "local_immutable_locator",
            "opaque_locator_sha256": sha256_bytes(canonical_json(locator).encode("utf-8")),
        },
        "source_span": {"start": start, "end": end},
        "source_sha256": supplied_sha,
        "source_text": span,
        "corrected_text": corrected_text,
        "metadata": {
            "annotation_layer": layer,
            "partition": partition,
            "annotator_identity_sha256": sha256_bytes(annotator.encode("utf-8")),
            "is_native": is_native,
            "source_lang": source_lang,
        },
        "candidate_signals": sorted(set(candidate_signals)),
        "clearance_sha256": clearance_sha,
        "near_duplicate_policy_fingerprint_sha256": policy_sha,
    }


def _packet_byte_count(items: list[dict[str, Any]]) -> int:
    return len(canonical_json(items).encode("utf-8"))


def _pack(items: list[dict[str, Any]], clearance_sha: str, policy_sha: str, query_sha: str) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    doc_counts: Counter[str] = Counter()
    textbook_counts: Counter[str] = Counter()
    for item in items:
        document = item["source_document_identity"]
        document_limit = 2 if item["family_id"] == "ua_gec" else MAX_ITEMS
        textbook_limit = 4 if item["family_id"] == "school_textbooks" else MAX_ITEMS
        candidate = [*current, item]
        would_exceed = len(candidate) > MAX_ITEMS or _packet_byte_count(candidate) > MAX_UTF8_BYTES
        would_cap = doc_counts[document] >= document_limit or textbook_counts[document] >= textbook_limit
        if current and (would_exceed or would_cap):
            packets.append(_make_packet(len(packets) + 1, current, clearance_sha, policy_sha, query_sha))
            current, doc_counts, textbook_counts = [], Counter(), Counter()
        # A unit can be larger than the cap.  Preserve it exactly as a singleton.
        if not current and _packet_byte_count([item]) > MAX_UTF8_BYTES:
            packets.append(_make_packet(len(packets) + 1, [item], clearance_sha, policy_sha, query_sha))
            continue
        current.append(item)
        doc_counts[document] += 1
        if item["family_id"] == "school_textbooks":
            textbook_counts[document] += 1
    if current:
        packets.append(_make_packet(len(packets) + 1, current, clearance_sha, policy_sha, query_sha))
    return packets


def _make_packet(
    ordinal: int, items: list[dict[str, Any]], clearance_sha: str, policy_sha: str, query_sha: str
) -> dict[str, Any]:
    byte_count = _packet_byte_count(items)
    identity = {
        "ordinal": ordinal,
        "item_ids": [item["source_item_id"] for item in items],
        "clearance_sha256": clearance_sha,
        "query_plan_sha256": query_sha,
    }
    packet = {
        "schema_version": "phase3_rule_author_packet_v1",
        "packet_id": stable_id("rule_author_packet", identity),
        "ordinal": ordinal,
        "clearance_sha256": clearance_sha,
        "near_duplicate_policy_fingerprint_sha256": policy_sha,
        "query_plan_sha256": query_sha,
        "byte_count": byte_count,
        "oversize_singleton": len(items) == 1 and byte_count > MAX_UTF8_BYTES,
        "items": items,
    }
    require(packet["oversize_singleton"] or byte_count <= MAX_UTF8_BYTES, "packet byte limit exceeded")
    validate(packet, "packet", "packet")
    return packet


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(canonical_json(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _query_plan_sha256() -> str:
    query_plan = {
        "families": sorted(AUTHOR_FAMILIES),
        "selection": "explicit_steward_clearance_allowlist_only",
        "no_heldout_read": True,
        "no_complement_inference": True,
    }
    return sha256_bytes(canonical_json(query_plan).encode("utf-8"))


def _validated_source_items(
    *,
    sources_path: Path,
    clearance: Mapping[str, Any],
    clearance_sha: str,
    frozen: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    allowed = {(item["family_id"], item["unit_id"]): item["unit_sha256"] for item in clearance["cleared_units"]}
    require(len(allowed) == len(clearance["cleared_units"]), "clearance has duplicate cleared unit")
    require(clearance["cleared_unit_count"] == len(allowed), "clearance cleared-unit count drift")
    policy_sha = str(clearance["input_bindings"]["near_duplicate_policy_fingerprint_sha256"])
    source_items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in iter_jsonl(sources_path):
        item = _item_from_row(row, clearance_sha, policy_sha)
        key = (item["family_id"], item["frozen_unit"]["unit_id"])
        require(key in allowed, "source row is not explicitly cleared")
        require(allowed[key] == item["frozen_unit"]["unit_sha256"], "clearance unit hash drift")
        ledger = frozen.get(key[0], {})
        require(
            key[1] in ledger and ledger[key[1]].get("unit_sha256") == item["frozen_unit"]["unit_sha256"],
            "source row does not match frozen source unit",
        )
        require(key not in seen, "multiple source rows for one cleared unit are forbidden")
        seen.add(key)
        validate(item, "sourceItem", "source item")
        source_items.append(item)
    require(
        seen == set(allowed), "clearance units must be represented exactly once; no complement inference is permitted"
    )
    source_items.sort(key=lambda item: (item["family_id"], item["frozen_unit"]["unit_id"], item["source_item_id"]))
    return source_items


def build(
    *,
    clearance_path: Path,
    source_universe_dir: Path,
    sources_path: Path,
    evaluation_path: Path,
    coverage_path: Path,
    role_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Build private packets from explicit allowlisted frozen units only."""
    _output_is_private(output_path)
    clearance = read_json(clearance_path)
    frozen, receipt, receipt_sha = _load_frozen_units(source_universe_dir)
    clearance_sha = sha256_file(clearance_path)
    validate_clearance(
        clearance,
        clearance_sha256=clearance_sha,
        receipt_sha256=receipt_sha,
        evaluation_path=evaluation_path,
        coverage_path=coverage_path,
        role_path=role_path,
    )
    policy_sha = str(clearance["input_bindings"]["near_duplicate_policy_fingerprint_sha256"])
    source_items = _validated_source_items(
        sources_path=sources_path,
        clearance=clearance,
        clearance_sha=clearance_sha,
        frozen=frozen,
    )
    query_sha = _query_plan_sha256()
    packets = _pack(source_items, clearance_sha, policy_sha, query_sha)
    compiler = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "script_sha256": sha256_file(ROOT / SCRIPT_PATH),
        "query_plan_sha256": query_sha,
        "max_items": MAX_ITEMS,
        "max_utf8_bytes": MAX_UTF8_BYTES,
    }
    identity = {
        "clearance_sha256": clearance_sha,
        "packet_ids": [packet["packet_id"] for packet in packets],
        "compiler": compiler,
    }
    bundle = {
        "schema_version": "phase3_rule_author_packet_bundle_v1",
        "bundle_id": stable_id("rule_author_bundle", identity),
        "clearance": {"receipt_sha256": clearance["receipt_sha256"], "file_sha256": clearance_sha},
        "source_freeze": {"receipt_sha256": receipt_sha, "merged_main_sha": receipt["merged_main_sha"]},
        "evaluation_contract_sha256": sha256_file(evaluation_path),
        "coverage_contract_sha256": sha256_file(coverage_path),
        "role_contract_sha256": sha256_file(role_path),
        "near_duplicate_policy_fingerprint_sha256": policy_sha,
        "compiler": compiler,
        "packets": packets,
    }
    schema = _local_schema(read_json(SCHEMA_PATH))
    errors = sorted(Draft202012Validator(schema).iter_errors(bundle), key=lambda item: list(item.path))
    if errors:
        raise PacketCompilerError(f"bundle schema violation: {errors[0].message}")
    _atomic_json(output_path, bundle)
    return bundle


def verify(
    *,
    bundle_path: Path,
    clearance_path: Path,
    source_universe_dir: Path,
    sources_path: Path,
    evaluation_path: Path,
    coverage_path: Path,
    role_path: Path,
    response_path: Path | None = None,
    review_path: Path | None = None,
) -> dict[str, Any]:
    """Verify bundle closure and optional non-authoritative response/review files."""
    bundle = read_json(bundle_path)
    schema = _local_schema(read_json(SCHEMA_PATH))
    errors = sorted(Draft202012Validator(schema).iter_errors(bundle), key=lambda item: list(item.path))
    require(not errors, f"bundle schema violation: {errors[0].message if errors else ''}")
    clearance = read_json(clearance_path)
    frozen, receipt, receipt_sha = _load_frozen_units(source_universe_dir)
    clearance_sha = sha256_file(clearance_path)
    validate_clearance(
        clearance,
        clearance_sha256=clearance_sha,
        receipt_sha256=receipt_sha,
        evaluation_path=evaluation_path,
        coverage_path=coverage_path,
        role_path=role_path,
    )
    require(
        bundle["clearance"] == {"receipt_sha256": clearance["receipt_sha256"], "file_sha256": clearance_sha},
        "bundle clearance binding drift",
    )
    require(
        bundle["source_freeze"] == {"receipt_sha256": receipt_sha, "merged_main_sha": receipt["merged_main_sha"]},
        "bundle source-freeze binding drift",
    )
    expected_items = _validated_source_items(
        sources_path=sources_path,
        clearance=clearance,
        clearance_sha=clearance_sha,
        frozen=frozen,
    )
    bundled_items = [item for packet in bundle["packets"] for item in packet["items"]]
    require(bundled_items == expected_items, "bundle source items differ from re-admitted steward-cleared sources")
    require(
        bundle["evaluation_contract_sha256"] == sha256_file(evaluation_path), "bundle evaluation-contract binding drift"
    )
    require(bundle["coverage_contract_sha256"] == sha256_file(coverage_path), "bundle coverage-contract binding drift")
    require(bundle["role_contract_sha256"] == sha256_file(role_path), "bundle role-contract binding drift")
    role_contract = read_json(role_path)
    author_actor = _derive_role_actor(role_contract, "rule_author_extractor")
    reviewer_actor = _derive_role_actor(role_contract, "ukrainian_source_reviewer")
    expected_compiler = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "script_sha256": sha256_file(ROOT / SCRIPT_PATH),
        "query_plan_sha256": _query_plan_sha256(),
        "max_items": MAX_ITEMS,
        "max_utf8_bytes": MAX_UTF8_BYTES,
    }
    require(bundle["compiler"] == expected_compiler, "bundle compiler identity drift")
    for packet in bundle["packets"]:
        size = _packet_byte_count(packet["items"])
        require(size == packet["byte_count"], "packet byte count drift")
        require(packet["oversize_singleton"] or size <= MAX_UTF8_BYTES, "packet byte cap violated")
        require(len(packet["items"]) <= MAX_ITEMS, "packet item cap violated")
        ua_docs = Counter(item["source_document_identity"] for item in packet["items"] if item["family_id"] == "ua_gec")
        textbook_docs = Counter(
            item["source_document_identity"] for item in packet["items"] if item["family_id"] == "school_textbooks"
        )
        require(max(ua_docs.values(), default=0) <= 2, "UA-GEC document cap violated")
        require(max(textbook_docs.values(), default=0) <= 4, "textbook document cap violated")
        for item in packet["items"]:
            require(
                sha256_bytes(item["source_text"].encode("utf-8")) == item["source_sha256"], "source text hash drift"
            )
            source_identity = {
                "frozen_unit": item["frozen_unit"],
                "source_sha256": item["source_sha256"],
                "start": item["source_span"]["start"],
                "end": item["source_span"]["end"],
            }
            require(
                item["source_item_id"] == stable_id("rule_author_source", source_identity), "source-item identity drift"
            )
        packet_identity = {
            "ordinal": packet["ordinal"],
            "item_ids": [item["source_item_id"] for item in packet["items"]],
            "clearance_sha256": bundle["clearance"]["file_sha256"],
            "query_plan_sha256": bundle["compiler"]["query_plan_sha256"],
        }
        require(packet["packet_id"] == stable_id("rule_author_packet", packet_identity), "packet identity drift")
    bundle_identity = {
        "clearance_sha256": bundle["clearance"]["file_sha256"],
        "packet_ids": [packet["packet_id"] for packet in bundle["packets"]],
        "compiler": bundle["compiler"],
    }
    require(bundle["bundle_id"] == stable_id("rule_author_bundle", bundle_identity), "bundle identity drift")
    response_sha = None
    response: Mapping[str, Any] | None = None
    proposal_by_id: dict[str, Mapping[str, Any]] = {}
    if response_path is not None:
        response = read_json(response_path)
        validate(response, "ruleAuthorResponse", "rule-author response")
        require(
            {key: response["author"][key] for key in ("role_id", "controller_identity_id", "task_id")} == author_actor,
            "response author does not match current role contract",
        )
        packets_by_hash = {sha256_bytes(canonical_json(packet).encode("utf-8")): packet for packet in bundle["packets"]}
        require(response["packet_sha256"] in packets_by_hash, "response does not bind a packet in this bundle")
        bound_packet = packets_by_hash[response["packet_sha256"]]
        bound_items = {item["source_item_id"]: item for item in bound_packet["items"]}
        proposals = response.get("proposals", [])
        proposal_by_id = {proposal["proposal_id"]: proposal for proposal in proposals}
        require(
            len(proposal_by_id) == len(proposals),
            "rule-author response contains duplicate proposal IDs",
        )
        for proposal in proposals:
            source_item = bound_items.get(proposal["source_item_id"])
            require(source_item is not None, "rule-author proposal does not bind a source item in its packet")
            require(
                proposal["source_span"] == source_item["source_span"],
                "rule-author proposal source span differs from its packet source item",
            )
        response_sha = sha256_file(response_path)
    if review_path is not None:
        require(response_sha is not None, "review verification requires a response")
        review = read_json(review_path)
        validate(review, "reviewDecision", "Ukrainian review decision")
        require(review["reviewer"] == reviewer_actor, "reviewer does not match current Ukrainian reviewer role")
        require(
            review["reviewer"]["controller_identity_id"] != response["author"]["controller_identity_id"],
            "Ukrainian reviewer must be independent of rule author",
        )
        require(review["reviewed_payload_sha256"] == response_sha, "review does not bind response payload")
        decisions = review["proposal_decisions"]
        decision_by_id = {decision["proposal_id"]: decision for decision in decisions}
        require(
            len(decision_by_id) == len(decisions),
            "Ukrainian review contains duplicate proposal decisions",
        )
        require(
            set(decision_by_id) == set(proposal_by_id),
            "Ukrainian review must decide every proposal exactly once",
        )
        for proposal_id, decision in decision_by_id.items():
            proposal = proposal_by_id[proposal_id]
            canonical = decision.get("canonical_reviewed_rule")
            if decision["decision"] in {"accepted", "revise"}:
                require(isinstance(canonical, Mapping), "accepted/revised decision lacks canonical reviewed rule")
                require(
                    decision["canonical_reviewed_rule_sha256"]
                    == sha256_bytes(canonical_json(canonical).encode("utf-8")),
                    "canonical reviewed rule hash drift",
                )
                require(
                    canonical.get("proposal_id") == proposal_id
                    and canonical.get("source_item_id") == proposal.get("source_item_id")
                    and canonical.get("source_span") == proposal.get("source_span"),
                    "canonical reviewed rule retargets its author proposal or source span",
                )
                require(
                    decision["source_role_decision"]
                    == {
                        "primary": canonical.get("primary_source_role"),
                        "secondary": canonical.get("secondary_source_roles"),
                    }
                    and decision["claim_type_decision"] == canonical.get("claim_type")
                    and decision["phenomenon_decision"] == canonical.get("phenomenon")
                    and decision["mechanism_decision"] == canonical.get("mechanism"),
                    "canonical reviewed rule disagrees with explicit Ukrainian decisions",
                )
        expected_overall = (
            "revise"
            if any(item["decision"] == "revise" for item in decisions)
            else "accepted"
            if any(item["decision"] == "accepted" for item in decisions)
            else "rejected"
        )
        require(review["decision"] == expected_overall, "overall Ukrainian review decision drift")
        require(
            review["canonical_reviewed_payload_sha256"] == sha256_bytes(canonical_json(decisions).encode("utf-8")),
            "review canonical payload hash drift",
        )
    return {
        "ok": True,
        "packets": len(bundle["packets"]),
        "response_verified": response_path is not None,
        "review_verified": review_path is not None,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile private cleared Phase 3 rule-author packets (no model calls)."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build", help="build a private packet bundle")
    build_parser.add_argument("--clearance", required=True, type=Path)
    build_parser.add_argument("--source-universe-dir", required=True, type=Path)
    build_parser.add_argument("--sources", required=True, type=Path)
    build_parser.add_argument("--evaluation-contract", required=True, type=Path)
    build_parser.add_argument("--coverage-contract", required=True, type=Path)
    build_parser.add_argument("--role-contract", required=True, type=Path)
    build_parser.add_argument("--output", required=True, type=Path)
    verify_parser = commands.add_parser("verify", help="verify a private packet bundle and optional response/review")
    verify_parser.add_argument("--bundle", required=True, type=Path)
    verify_parser.add_argument("--clearance", required=True, type=Path)
    verify_parser.add_argument("--source-universe-dir", required=True, type=Path)
    verify_parser.add_argument("--sources", required=True, type=Path)
    verify_parser.add_argument("--evaluation-contract", required=True, type=Path)
    verify_parser.add_argument("--coverage-contract", required=True, type=Path)
    verify_parser.add_argument("--role-contract", required=True, type=Path)
    verify_parser.add_argument("--response", type=Path)
    verify_parser.add_argument("--review", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            bundle = build(
                clearance_path=args.clearance,
                source_universe_dir=args.source_universe_dir,
                sources_path=args.sources,
                evaluation_path=args.evaluation_contract,
                coverage_path=args.coverage_contract,
                role_path=args.role_contract,
                output_path=args.output,
            )
            print(canonical_json({"ok": True, "bundle_id": bundle["bundle_id"], "packets": len(bundle["packets"])}))
        else:
            print(
                canonical_json(
                    verify(
                        bundle_path=args.bundle,
                        clearance_path=args.clearance,
                        source_universe_dir=args.source_universe_dir,
                        sources_path=args.sources,
                        evaluation_path=args.evaluation_contract,
                        coverage_path=args.coverage_contract,
                        role_path=args.role_contract,
                        response_path=args.response,
                        review_path=args.review,
                    )
                )
            )
    except PacketCompilerError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
