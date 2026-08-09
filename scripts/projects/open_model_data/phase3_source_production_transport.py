#!/usr/bin/env python3
"""Run the private, resumable Phase 3 v2.1 all-family source-production lane.

The transport exposes only author-cleared source units to Gemini, preserves raw
provider output before parsing, routes a frozen subset to the independent Ukrainian
source reviewer, and assembles the exact text-free input consumed by
``phase3_source_dispositions.py``.  It never opens sealed held-out labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
DEFAULT_SCHEMA = CONTRACTS / "phase3_source_production_transport_v1.schema.json"
DEFAULT_DISPOSITION_SCHEMA = CONTRACTS / "phase3_source_disposition_input_v1.schema.json"
DEFAULT_AUTHOR_PROMPT = CONTRACTS / "phase3_source_author_prompt_v1.md"
DEFAULT_REVIEW_PROMPT = CONTRACTS / "phase3_source_review_prompt_v1.md"
DEFAULT_ROLE_CONTRACT = (
    ROOT / "data/projects/open_model_data/evidence/correction_protection_functional_role_contract_v2_1.json"
)

BASE_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
AMENDMENT_SHA256 = "ae36a961318b2a0a494837314929efd9849b4e6a6fa299b3d8dde17261777f5b"
COMBINED_SHA256 = "2f3ef840325d917b9f2763188627ad69d1b4e45b804860499a134586b112a907"

FAMILY_TOTALS = {
    "antonenko_style_guide": 342,
    "antonenko_textbook_representation": 169,
    "calque_inventory": 58,
    "other_normative_style_inventory": 0,
    "pravopys_2019_complete": 1_090,
    "pravopys_2026_complete": 1_466,
    "school_textbooks": 54_979,
    "ua_gec": 8_937,
}
AUTHOR_TOTALS = {
    "antonenko_style_guide": 209,
    "antonenko_textbook_representation": 0,
    "calque_inventory": 40,
    "other_normative_style_inventory": 0,
    "pravopys_2019_complete": 685,
    "pravopys_2026_complete": 907,
    "school_textbooks": 35_075,
    "ua_gec": 6_896,
}
EVALUATION_TOTALS = {
    "antonenko_style_guide": 58,
    "antonenko_textbook_representation": 0,
    "calque_inventory": 7,
    "other_normative_style_inventory": 0,
    "pravopys_2019_complete": 178,
    "pravopys_2026_complete": 235,
    "school_textbooks": 8_005,
    "ua_gec": 909,
}
QUARANTINE_TOTALS = {
    family: FAMILY_TOTALS[family] - AUTHOR_TOTALS[family] - EVALUATION_TOTALS[family]
    for family in FAMILY_TOTALS
}
EXPECTED_TOTAL = 67_041
EXPECTED_AUTHOR = 43_812
EXPECTED_EVALUATION = 9_392
EXPECTED_QUARANTINE = 13_837
EXPECTED_HELDOUT_LABELS = 2_000

AUTHOR = {
    "role_id": "rule_author_extractor",
    "task_id": "phase3-v2-1-rule-author-extraction",
    "provider": "google",
    "exact_model": "gemini-3.6-flash-high",
    "model_family": "gemini",
    "harness": "agy",
}
REVIEWER = {
    "role_id": "ukrainian_source_reviewer",
    "task_id": "phase3-v2-1-ukrainian-source-review",
    "provider": "xai",
    "exact_model": "grok-4.5",
    "model_family": "xai",
    "harness": "opencode",
}
SMALL_REVIEW_FAMILIES = frozenset(
    {"antonenko_style_guide", "calque_inventory", "pravopys_2019_complete", "pravopys_2026_complete"}
)
LARGE_REVIEW_FAMILIES = frozenset({"school_textbooks", "ua_gec"})
SOURCE_ROLES = frozenset(
    {
        "explicit_rule",
        "correct_example",
        "incorrect_example",
        "corrected_example",
        "editing_exercise",
        "answer_key",
        "distractor",
        "quotation",
        "historical_or_literary_excerpt",
        "metalinguistic_mention",
        "ordinary_narration",
        "ambiguous_or_ocr",
    }
)
CLAIM_TYPES = frozenset(
    {
        "prescriptive_rule",
        "human_correction_pair",
        "style_preference",
        "acceptable_variant",
        "historical_advice",
        "attestation_only",
        "unresolved",
    }
)
CANDIDATE_CLASSES = frozenset(
    {"rule_bearing", "error_correction", "editing_exercise", "contrast", "metalinguistic_candidate"}
)
DISPOSITION_CODES = frozenset(
    {
        "converted",
        "not_rule_bearing",
        "duplicate_representation",
        "superseded_or_historical",
        "blocked_with_reason",
    }
)
CONSUMER_VIEWS = frozenset(
    {"supervised_pair", "preference", "protection", "filtering", "review", "automatic", "research_only"}
)
MECHANISMS = frozenset(
    {
        "literal",
        "lemma_morphology",
        "phrase_collocation",
        "government_valency",
        "syntax",
        "semantic_contextual",
        "orthography",
        "punctuation",
    }
)
SHA256 = re.compile(r"^[a-f0-9]{64}$")
MAX_ITEMS = 48
MAX_UTF8_BYTES = 196_608


class SourceProductionError(ValueError):
    """The private production or review boundary is incomplete or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceProductionError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceProductionError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    _regular(path, label)
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SourceProductionError(f"invalid {label} JSONL at line {line_number}") from exc
            require(isinstance(value, dict), f"{label} row {line_number} is not an object")
            rows.append(value)
    return rows


def _reject_symlink_components(path: Path, label: str) -> None:
    current = path.absolute()
    while True:
        if current.exists():
            require(not current.is_symlink(), f"{label} contains a symlink: {current}")
        if current.parent == current:
            return
        current = current.parent


def _regular(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    require(path.is_file() and not path.is_symlink(), f"{label} is not a regular file: {path}")


def _private_root(path: Path, *, create: bool) -> Path:
    _reject_symlink_components(path, "private root")
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path, 0o700)
    require(path.is_dir() and not path.is_symlink(), "private root is not a real directory")
    require(path.stat().st_mode & 0o077 == 0, "private root permissions must be 0700")
    return path.resolve()


def _write_private(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    _reject_symlink_components(path, "private output")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    require(path.stat().st_mode & 0o077 == 0, "private file permissions must be 0600")
    return sha256_file(path)


def _write_private_json(path: Path, value: Any) -> str:
    return _write_private(path, (canonical_json(value) + "\n").encode("utf-8"))


def _write_private_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    payload = "".join(canonical_json(dict(row)) + "\n" for row in rows).encode("utf-8")
    return _write_private(path, payload)


def _assert_nonoverlap(outputs: Sequence[Path], inputs: Sequence[Path]) -> None:
    resolved_inputs = [path.resolve() for path in inputs]
    for output in outputs:
        resolved = output.resolve(strict=False)
        for source in resolved_inputs:
            require(resolved != source and source not in resolved.parents, "output overlaps an input")


def _schema(path: Path) -> dict[str, Any]:
    value = _read_json(path, "transport schema")
    Draft202012Validator.check_schema(value)
    return value


def _validate(value: Mapping[str, Any], schema_path: Path, definition: str) -> None:
    schema = _schema(schema_path)
    ref = {"$schema": schema["$schema"], "$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}
    errors = sorted(Draft202012Validator(ref).iter_errors(dict(value)), key=lambda error: list(error.path))
    require(not errors, f"{definition} schema violation: {errors[0].message if errors else ''}")


def _validate_document(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _schema(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(dict(value)), key=lambda error: list(error.path))
    require(not errors, f"{label} schema violation: {errors[0].message if errors else ''}")


def _self_hash(value: Mapping[str, Any], field: str = "receipt_sha256") -> str:
    body = {key: item for key, item in value.items() if key != field}
    return sha256_value(body)


def _newline_body_hash(value: Mapping[str, Any], field: str = "receipt_sha256") -> str:
    body = {key: item for key, item in value.items() if key != field}
    return sha256_bytes((canonical_json(body) + "\n").encode("utf-8"))


def _role_bindings(path: Path) -> tuple[dict[str, Any], str, str]:
    contract = _read_json(path, "functional role contract")
    try:
        verified = functional_roles.verify_value(contract)
        author = functional_roles.binding_for_role(verified, AUTHOR["role_id"])
        reviewer = functional_roles.binding_for_role(verified, REVIEWER["role_id"])
    except functional_roles.FunctionalRoleError as exc:
        raise SourceProductionError(str(exc)) from exc
    require(author["task_id"] == AUTHOR["task_id"] and reviewer["task_id"] == REVIEWER["task_id"], "role task drift")
    by_role = {row["role_id"]: row for row in verified["functional_roles"]}
    for expected in (AUTHOR, REVIEWER):
        actual = by_role[expected["role_id"]]
        require(
            all(actual[key] == expected[key] for key in ("role_id", "task_id", "exact_model", "model_family", "harness")),
            f"{expected['role_id']} execution lane drift",
        )
    require(
        functional_roles.tasks_conflict(verified, AUTHOR["task_id"], REVIEWER["task_id"]),
        "author-to-source-review edge is missing",
    )
    return verified, sha256_file(path), functional_roles.conflict_graph_sha256(verified)


def _expected(overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    if overrides is None:
        return {
            "family_totals": FAMILY_TOTALS,
            "author_totals": AUTHOR_TOTALS,
            "evaluation_totals": EVALUATION_TOTALS,
            "quarantine_totals": QUARANTINE_TOTALS,
            "total": EXPECTED_TOTAL,
            "author": EXPECTED_AUTHOR,
            "evaluation": EXPECTED_EVALUATION,
            "quarantine": EXPECTED_QUARANTINE,
            "heldout_labels": EXPECTED_HELDOUT_LABELS,
        }
    result = dict(overrides)
    required = {
        "family_totals", "author_totals", "evaluation_totals", "quarantine_totals",
        "total", "author", "evaluation", "quarantine", "heldout_labels",
    }
    require(set(result) == required, "expected-total override fields drift")
    return result


def _counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row["family_id"]) for row in rows))


def _load_inputs(
    *,
    materialization_jsonl: Path,
    materialization_receipt_path: Path,
    source_freeze_receipt_path: Path,
    evaluation_partition_receipt_path: Path,
    partition_manifest_path: Path,
    author_clearance_path: Path,
    quarantine_path: Path,
    heldout_label_receipt_path: Path,
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    materialization_receipt = _read_json(materialization_receipt_path, "materialization receipt")
    require(materialization_receipt.get("text_free") is True and materialization_receipt.get("no_leakage") is True, "unsafe materialization receipt")
    require(materialization_receipt.get("private_record_count") == expected["total"], "materialization total drift")
    require(materialization_receipt.get("private_jsonl_sha256") == sha256_file(materialization_jsonl), "materialization hash drift")
    require(
        materialization_receipt.get("receipt_sha256") == _newline_body_hash(materialization_receipt),
        "materialization self-hash drift",
    )
    source_freeze = _read_json(source_freeze_receipt_path, "source freeze receipt")
    require(source_freeze.get("text_free") is True, "source freeze is not text-free")
    require(
        materialization_receipt.get("source_universe_receipt_sha256") == sha256_file(source_freeze_receipt_path),
        "materialization/source-freeze binding drift",
    )
    freeze_families = {
        row["family_id"]: row for row in source_freeze.get("families", []) if isinstance(row, Mapping)
    }
    require(set(freeze_families) >= set(expected["family_totals"]), "source freeze lacks a mandatory family")

    partition_receipt = _read_json(evaluation_partition_receipt_path, "evaluation partition receipt")
    require(partition_receipt.get("text_free") is True, "evaluation partition receipt is not text-free")
    aggregates = partition_receipt.get("aggregates")
    expected_aggregates = {
        "author_cleared_total": expected["author"],
        "input_total": expected["total"],
        "quarantined_total": expected["quarantine"],
        "sealed_evaluation_total": expected["evaluation"],
    }
    require(
        isinstance(aggregates, Mapping)
        and all(aggregates.get(key) == value for key, value in expected_aggregates.items())
        and set(aggregates) <= set(expected_aggregates) | {"clean_modern_candidate_total"},
        "evaluation partition aggregates drift",
    )
    artifacts = partition_receipt.get("artifact_hashes", {})
    require(artifacts.get("author_clearance_sha256") == sha256_file(author_clearance_path), "clearance hash drift")
    require(artifacts.get("partition_manifest_sha256") == sha256_file(partition_manifest_path), "partition hash drift")
    require(artifacts.get("quarantine_sha256") == sha256_file(quarantine_path), "quarantine hash drift")

    heldout = _read_json(heldout_label_receipt_path, "heldout-label public receipt")
    require(
        heldout.get("schema_version") == "phase3_heldout_label_public_receipt_v1"
        and heldout.get("text_free") is True
        and heldout.get("complete") is True
        and heldout.get("row_count") == expected["heldout_labels"],
        "heldout labels are not completely frozen",
    )
    require(heldout.get("receipt_sha256") == _newline_body_hash(heldout), "heldout-label receipt self-hash drift")

    materialized = _read_jsonl(materialization_jsonl, "materialization")
    author = _read_jsonl(author_clearance_path, "author clearance")
    evaluation = _read_jsonl(partition_manifest_path, "evaluation partition")
    quarantine = _read_jsonl(quarantine_path, "quarantine")
    require(len(materialized) == expected["total"], "materialization row total drift")
    require(len(author) == expected["author"] and len(evaluation) == expected["evaluation"] and len(quarantine) == expected["quarantine"], "partition row totals drift")
    require(_counts(materialized) == {key: value for key, value in expected["family_totals"].items() if value}, "materialization family counts drift")
    require(_counts(author) == {key: value for key, value in expected["author_totals"].items() if value}, "author family counts drift")
    require(_counts(evaluation) == {key: value for key, value in expected["evaluation_totals"].items() if value}, "evaluation family counts drift")
    require(_counts(quarantine) == {key: value for key, value in expected["quarantine_totals"].items() if value}, "quarantine family counts drift")

    by_id: dict[str, dict[str, Any]] = {}
    for row in materialized:
        required = {
            "family_id", "unit_id", "unit_sha256", "frozen_locator", "frozen_locator_sha256",
            "document_or_edition_identity", "source_text", "source_text_sha256", "source_record",
        }
        require(set(row) == required, "materialization row fields drift")
        unit_id = row["unit_id"]
        require(isinstance(unit_id, str) and unit_id not in by_id, "duplicate or invalid materialized unit")
        require(row["family_id"] in expected["family_totals"], "unknown materialized family")
        require(row["source_text_sha256"] == sha256_bytes(str(row["source_text"]).encode("utf-8")), "source text hash drift")
        require(row["frozen_locator_sha256"] == sha256_value(row["frozen_locator"]), "frozen locator hash drift")
        by_id[unit_id] = row
    sets: dict[str, set[str]] = {}
    for name, rows in (("author", author), ("evaluation", evaluation), ("quarantine", quarantine)):
        seen: set[str] = set()
        for row in rows:
            unit_id = row.get("unit_id")
            require(isinstance(unit_id, str) and unit_id in by_id and unit_id not in seen, f"invalid {name} unit binding")
            source = by_id[unit_id]
            require(row.get("family_id") == source["family_id"] and row.get("unit_sha256") == source["unit_sha256"], f"{name} unit hash drift")
            if name == "evaluation":
                require(row.get("reason") == "evaluation_only", "evaluation reason drift")
                require(row.get("frozen_locator_sha256") == source["frozen_locator_sha256"], "evaluation locator hash drift")
                require(row.get("source_text_sha256") == source["source_text_sha256"], "evaluation text hash drift")
            seen.add(unit_id)
        sets[name] = seen
    require(not (sets["author"] & sets["evaluation"] or sets["author"] & sets["quarantine"] or sets["evaluation"] & sets["quarantine"]), "partition overlap")
    require(sets["author"] | sets["evaluation"] | sets["quarantine"] == set(by_id), "partition is not a full complement")
    return {
        "materialized": materialized,
        "by_id": by_id,
        "author": author,
        "evaluation": evaluation,
        "quarantine": quarantine,
        "source_freeze": source_freeze,
        "freeze_families": freeze_families,
        "receipts": {
            "materialization_receipt_sha256": sha256_file(materialization_receipt_path),
            "materialization_jsonl_sha256": sha256_file(materialization_jsonl),
            "source_freeze_receipt_sha256": sha256_file(source_freeze_receipt_path),
            "evaluation_partition_receipt_sha256": sha256_file(evaluation_partition_receipt_path),
            "partition_manifest_sha256": sha256_file(partition_manifest_path),
            "author_clearance_sha256": sha256_file(author_clearance_path),
            "quarantine_sha256": sha256_file(quarantine_path),
            "heldout_label_receipt_sha256": sha256_file(heldout_label_receipt_path),
            "heldout_label_receipt_body_sha256": heldout["receipt_sha256"],
        },
    }


def _identity(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "family_id": str(row["family_id"]),
        "unit_id": str(row["unit_id"]),
        "unit_sha256": str(row["unit_sha256"]),
        "locator_sha256": str(row["frozen_locator_sha256"]),
        "source_text_sha256": str(row["source_text_sha256"]),
    }


def _author_item(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "identity": _identity(row),
        "document_or_edition_identity": row["document_or_edition_identity"],
        "frozen_locator": row["frozen_locator"],
        "source_text": row["source_text"],
        "source_record": row["source_record"],
    }


def _pack_items(items: Sequence[Mapping[str, Any]], *, item_limit: int, byte_limit: int, lane: str) -> list[dict[str, Any]]:
    require(item_limit > 0 and byte_limit > 0, "invalid packet bounds")
    packets: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for source in items:
        item = dict(source)
        candidate = [*current, item]
        if current and (len(candidate) > item_limit or len(canonical_json(candidate).encode("utf-8")) > byte_limit):
            packets.append(_packet(len(packets) + 1, current, lane))
            current = []
        current.append(item)
        if len(canonical_json(current).encode("utf-8")) > byte_limit:
            require(len(current) == 1, "packet byte limit exceeded")
            packets.append(_packet(len(packets) + 1, current, lane, oversize=True))
            current = []
    if current:
        packets.append(_packet(len(packets) + 1, current, lane))
    return packets


def _packet(index: int, items: Sequence[Mapping[str, Any]], lane: str, oversize: bool = False) -> dict[str, Any]:
    identities = [item["identity"] for item in items]
    packet_id = f"phase3_source_{lane}_packet:{sha256_value({'index': index, 'identities': identities})}"
    return {
        "schema_version": f"phase3_source_production_{lane}_packet_v1",
        "packet_id": packet_id,
        "packet_index": index,
        "identity_order": identities,
        "oversize_singleton": oversize,
        "items": list(items),
    }


def prepare(
    *,
    materialization_jsonl: Path,
    materialization_receipt_path: Path,
    source_freeze_receipt_path: Path,
    evaluation_partition_receipt_path: Path,
    partition_manifest_path: Path,
    author_clearance_path: Path,
    quarantine_path: Path,
    heldout_label_receipt_path: Path,
    private_dir: Path,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    author_prompt_path: Path = DEFAULT_AUTHOR_PROMPT,
    review_prompt_path: Path = DEFAULT_REVIEW_PROMPT,
    schema_path: Path = DEFAULT_SCHEMA,
    item_limit: int = MAX_ITEMS,
    byte_limit: int = MAX_UTF8_BYTES,
    expected_totals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare the immutable author packet set and deterministic complements."""
    inputs = (
        materialization_jsonl, materialization_receipt_path, source_freeze_receipt_path,
        evaluation_partition_receipt_path, partition_manifest_path, author_clearance_path,
        quarantine_path, heldout_label_receipt_path, role_contract_path, author_prompt_path,
        review_prompt_path, schema_path,
    )
    for path in inputs:
        _regular(path, "prepare input")
    _assert_nonoverlap((private_dir,), inputs)
    expected = _expected(expected_totals)
    roles, role_sha, graph_sha = _role_bindings(role_contract_path)
    loaded = _load_inputs(
        materialization_jsonl=materialization_jsonl,
        materialization_receipt_path=materialization_receipt_path,
        source_freeze_receipt_path=source_freeze_receipt_path,
        evaluation_partition_receipt_path=evaluation_partition_receipt_path,
        partition_manifest_path=partition_manifest_path,
        author_clearance_path=author_clearance_path,
        quarantine_path=quarantine_path,
        heldout_label_receipt_path=heldout_label_receipt_path,
        expected=expected,
    )
    root = _private_root(private_dir, create=True)
    author_ids = {row["unit_id"] for row in loaded["author"]}
    author_items = [_author_item(row) for row in loaded["materialized"] if row["unit_id"] in author_ids]
    author_items.sort(key=lambda row: (row["identity"]["family_id"], row["identity"]["unit_id"]))
    packets = _pack_items(author_items, item_limit=item_limit, byte_limit=byte_limit, lane="author")
    packet_entries: list[dict[str, Any]] = []
    for packet in packets:
        path = root / "author" / "packets" / f"{packet['packet_index']:05d}.json"
        packet_hash = _write_private_json(path, packet)
        packet_entries.append(
            {
                "packet_index": packet["packet_index"],
                "packet_id": packet["packet_id"],
                "packet_sha256": packet_hash,
                "item_count": len(packet["items"]),
                "relative_path": str(path.relative_to(root)),
            }
        )
    deterministic: list[dict[str, Any]] = []
    for source, code, reason in (
        (loaded["evaluation"], "evaluation_only", "evaluation_partition_member"),
        (loaded["quarantine"], "blocked_with_reason", None),
    ):
        for row in source:
            item = loaded["by_id"][row["unit_id"]]
            reason_code = reason or str(row["reason"])
            deterministic.append(
                {
                    **_identity(item),
                    "frozen_locator": item["frozen_locator"],
                    "disposition_code": code,
                    "reason_code": reason_code,
                    "reason_predicate_sha256": sha256_value(
                        {"partition": code, "reason": reason_code, "unit_id": item["unit_id"]}
                    ),
                }
            )
    deterministic.sort(key=lambda row: (row["family_id"], row["unit_id"]))
    deterministic_hash = _write_private_jsonl(root / "deterministic-partition-dispositions.jsonl", deterministic)
    bindings = {
        "base_contract_sha256": BASE_SHA256,
        "amendment_sha256": AMENDMENT_SHA256,
        "combined_contract_sha256": COMBINED_SHA256,
        "functional_role_contract_sha256": role_sha,
        "conflict_graph_sha256": graph_sha,
        "evaluation_cycle_id": roles["evaluation_cycle"]["evaluation_cycle_id"],
        "author_prompt_sha256": sha256_file(author_prompt_path),
        "review_prompt_sha256": sha256_file(review_prompt_path),
        "transport_schema_sha256": sha256_file(schema_path),
        **loaded["receipts"],
        "deterministic_partition_dispositions_sha256": deterministic_hash,
    }
    manifest = {
        "schema_version": "phase3_source_production_manifest_v1",
        "bindings": bindings,
        "denominator": expected,
        "author": AUTHOR,
        "reviewer": REVIEWER,
        "packet_bounds": {"item_limit": item_limit, "byte_limit": byte_limit},
        "author_packet_count": len(packet_entries),
        "author_packets": packet_entries,
        "author_identity_set_sha256": sha256_value([item["identity"] for item in author_items]),
        "source_freeze_family_bindings": {
            family: {
                "ledger_sha256": loaded["freeze_families"][family]["ledger_sha256"],
                "unit_count": expected["family_totals"][family],
            }
            for family in sorted(expected["family_totals"])
        },
        "created_at": _now(),
    }
    manifest["manifest_sha256"] = sha256_value(manifest)
    _validate(manifest, schema_path, "manifest")
    _write_private_json(root / "manifest.json", manifest)
    return manifest


def _manifest(path: Path, schema_path: Path) -> tuple[dict[str, Any], Path]:
    manifest = _read_json(path, "source-production manifest")
    definition = (
        "reviewManifest"
        if manifest.get("schema_version") == "phase3_source_production_review_manifest_v1"
        else "manifest"
    )
    _validate(manifest, schema_path, definition)
    require(manifest["manifest_sha256"] == _self_hash(manifest, "manifest_sha256"), "manifest self-hash drift")
    root = _private_root(path.parent, create=False)
    require(path.resolve().parent == root, "manifest must be at the private root")
    return manifest, root


def _strict_response(raw: bytes, label: str) -> dict[str, Any]:
    text = raw.decode("utf-8").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        require(len(lines) >= 3 and lines[-1].strip() == "```", f"malformed {label} code fence")
        text = "\n".join(lines[1:-1])
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:].lstrip("\r\n ")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceProductionError(f"invalid {label} JSON") from exc
    require(isinstance(value, dict), f"{label} response is not an object")
    return value


def _validate_provider_invocation(
    receipt: Mapping[str, Any], actor: Mapping[str, str], packet_id: str, raw_sha256: str
) -> None:
    required = {
        "schema_version", "actor", "packet_id", "raw_sha256", "command_sha256",
        "stdout_sha256", "stderr_sha256", "exit_code", "started_at", "completed_at",
    }
    require(set(receipt) == required, "provider invocation receipt fields drift")
    require(receipt["schema_version"] == "phase3_source_production_provider_invocation_v1", "provider invocation schema drift")
    require(receipt["actor"] == dict(actor) and receipt["packet_id"] == packet_id, "provider invocation actor/packet drift")
    require(receipt["raw_sha256"] == raw_sha256 and receipt["exit_code"] == 0, "provider invocation did not produce the preserved raw response")
    require(all(SHA256.fullmatch(str(receipt[name])) for name in ("raw_sha256", "command_sha256", "stdout_sha256", "stderr_sha256")), "provider invocation hash missing")


def _subprocess_invoke(command: list[str], prompt: bytes) -> tuple[int, bytes, bytes]:
    result = subprocess.run(command, cwd=ROOT, input=prompt, capture_output=True, check=False)
    return result.returncode, result.stdout, result.stderr


def _prompt_with_response_contract(prompt: bytes, schema_path: Path, lane: str) -> bytes:
    """Append the exact machine-enforced response contract seen by the parser."""
    schema = _read_json(schema_path, "source-production transport schema")
    definitions = schema.get("$defs")
    require(isinstance(definitions, Mapping), "transport schema definitions missing")
    response_name = "reviewResponse" if lane == "review" else "authorResponse"
    required_names = ("identity", "artifact", "decision", response_name)
    require(all(isinstance(definitions.get(name), Mapping) for name in required_names), "response contract definitions missing")
    response_contract = {name: definitions[name] for name in required_names}
    suffix = (
        "\n\n# Exact machine-enforced response contract\n\n"
        "The JSON Schema definitions below are authoritative for output shape. "
        "Return every required field with exactly these names; `additionalProperties: false` "
        "means aliases, renamed fields, wrapper omissions, and extra fields are rejected. "
        "Copy `packet_id` and the complete `identity_order` from the attached packet.\n\n"
        + canonical_json(response_contract)
        + "\n"
    )
    return prompt + suffix.encode("utf-8")


def _run_packets(
    *,
    manifest_path: Path,
    lane: str,
    prompt_path: Path,
    schema_path: Path,
    start: int,
    end: int | None,
    invoke: Callable[[list[str], bytes], tuple[int, bytes, bytes]] | None,
) -> dict[str, Any]:
    manifest, root = _manifest(manifest_path, schema_path)
    if lane == "review":
        require(manifest["schema_version"] == "phase3_source_production_review_manifest_v1", "review run requires review manifest")
        packet_count = manifest["review_packet_count"]
        actor, command_name = REVIEWER, "ask-opencode"
        expected_prompt_hash = manifest["bindings"]["review_prompt_sha256"]
    else:
        require(manifest["schema_version"] == "phase3_source_production_manifest_v1", "author run requires source manifest")
        packet_count = manifest["author_packet_count"]
        actor, command_name = AUTHOR, "ask-agy"
        expected_prompt_hash = manifest["bindings"]["author_prompt_sha256"]
    _regular(prompt_path, f"{lane} prompt")
    require(sha256_file(prompt_path) == expected_prompt_hash, f"{lane} prompt hash drift")
    require(sha256_file(schema_path) == manifest["bindings"]["transport_schema_sha256"], "transport schema hash drift")
    prompt = _prompt_with_response_contract(prompt_path.read_bytes(), schema_path, lane)
    last = packet_count if end is None else end
    require(1 <= start <= last <= packet_count, f"invalid {lane} run range")
    runner = invoke or _subprocess_invoke
    completed = 0
    skipped = 0
    for index in range(start, last + 1):
        record_path = root / lane / "records" / f"{index:05d}.json"
        if record_path.is_file():
            skipped += 1
            continue
        packet = _packet_for(manifest, root, index, lane)
        entry = (manifest["review_packets"] if lane == "review" else manifest["author_packets"])[index - 1]
        packet_path = root / entry["relative_path"]
        command = [
            ".venv/bin/python", "scripts/ai_agent_bridge/__main__.py", command_name, "-",
            "--task-id", actor["task_id"], "--to-model", actor["exact_model"],
            "--data", str(packet_path), "--no-timeout",
        ]
        if lane == "author":
            command.append("--stdout-only")
        started_at = _now()
        exit_code, stdout, stderr = runner(command, prompt)
        completed_at = _now()
        log_dir = root / lane / "provider-logs"
        stdout_hash = _write_private(log_dir / f"{index:05d}.stdout", stdout)
        stderr_hash = _write_private(log_dir / f"{index:05d}.stderr", stderr)
        raw = stdout
        raw_path = root / lane / "incoming" / f"{index:05d}.raw"
        raw_hash = _write_private(raw_path, raw)
        invocation = {
            "schema_version": "phase3_source_production_provider_invocation_v1",
            "actor": dict(actor),
            "packet_id": packet["packet_id"],
            "raw_sha256": raw_hash,
            "command_sha256": sha256_value(command),
            "stdout_sha256": stdout_hash,
            "stderr_sha256": stderr_hash,
            "exit_code": exit_code,
            "started_at": started_at,
            "completed_at": completed_at,
        }
        invocation_path = root / lane / "invocations" / f"{index:05d}.json"
        _write_private_json(invocation_path, invocation)
        require(exit_code == 0, f"{lane} provider invocation failed for packet {index}")
        if lane == "author":
            ingest_author(
                manifest_path=manifest_path, packet_index=index, raw_response_path=raw_path,
                provider_invocation_receipt_path=invocation_path, schema_path=schema_path,
            )
        else:
            ingest_review(
                review_manifest_path=manifest_path, packet_index=index, raw_response_path=raw_path,
                provider_invocation_receipt_path=invocation_path, schema_path=schema_path,
            )
        completed += 1
    return {"lane": lane, "packet_count": packet_count, "completed": completed, "skipped": skipped}


def run_author(
    *, manifest_path: Path, prompt_path: Path = DEFAULT_AUTHOR_PROMPT,
    schema_path: Path = DEFAULT_SCHEMA, start: int = 1, end: int | None = None,
    invoke: Callable[[list[str], bytes], tuple[int, bytes, bytes]] | None = None,
) -> dict[str, Any]:
    """Run a resumable range of exact Gemini author packets."""
    return _run_packets(
        manifest_path=manifest_path, lane="author", prompt_path=prompt_path,
        schema_path=schema_path, start=start, end=end, invoke=invoke,
    )


def run_review(
    *, review_manifest_path: Path, prompt_path: Path = DEFAULT_REVIEW_PROMPT,
    schema_path: Path = DEFAULT_SCHEMA, start: int = 1, end: int | None = None,
    invoke: Callable[[list[str], bytes], tuple[int, bytes, bytes]] | None = None,
) -> dict[str, Any]:
    """Run a resumable range of exact Grok source-review packets."""
    return _run_packets(
        manifest_path=review_manifest_path, lane="review", prompt_path=prompt_path,
        schema_path=schema_path, start=start, end=end, invoke=invoke,
    )


def _packet_for(manifest: Mapping[str, Any], root: Path, index: int, lane: str) -> dict[str, Any]:
    entries = manifest["author_packets"] if lane == "author" else manifest["review_packets"]
    require(isinstance(index, int) and 1 <= index <= len(entries), f"invalid {lane} packet index")
    entry = entries[index - 1]
    require(entry["packet_index"] == index, f"{lane} packet order drift")
    path = root / entry["relative_path"]
    packet = _read_json(path, f"{lane} packet")
    require(sha256_file(path) == entry["packet_sha256"] and packet["packet_id"] == entry["packet_id"], f"{lane} packet hash drift")
    return packet


def _validate_artifact(artifact: Mapping[str, Any]) -> None:
    required = {
        "phenomenon", "mechanism", "matcher", "incorrect_pattern", "replacements", "scope",
        "exceptions", "controls", "protections", "abstentions", "evidence_refs", "dissent_or_alternatives",
    }
    require(set(artifact) == required, "converted artifact fields drift")
    require(isinstance(artifact["phenomenon"], str) and artifact["phenomenon"], "artifact phenomenon missing")
    require(artifact["mechanism"] in MECHANISMS, "artifact mechanism drift")
    require(isinstance(artifact["matcher"], Mapping) and artifact["matcher"], "artifact matcher missing")
    for name in ("replacements", "exceptions", "controls", "protections", "abstentions", "evidence_refs", "dissent_or_alternatives"):
        require(isinstance(artifact[name], list) and all(isinstance(item, str) for item in artifact[name]), f"artifact {name} malformed")
    require(isinstance(artifact["incorrect_pattern"], str) and isinstance(artifact["scope"], str), "artifact text fields malformed")


def _validate_decision(decision: Mapping[str, Any], identity: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "unit_id", "unit_sha256", "disposition_code", "primary_source_role", "secondary_source_roles",
        "claim_type", "candidate_classes", "artifact", "consumer_views", "rationale",
    }
    require(set(decision) == required, "author decision fields drift")
    require(decision["unit_id"] == identity["unit_id"] and decision["unit_sha256"] == identity["unit_sha256"], "author decision retargeted a unit")
    require(decision["disposition_code"] in DISPOSITION_CODES, "author disposition code drift")
    require(decision["primary_source_role"] in SOURCE_ROLES, "source role drift")
    secondary = decision["secondary_source_roles"]
    require(isinstance(secondary, list) and len(secondary) == len(set(secondary)) and set(secondary) <= SOURCE_ROLES, "secondary roles drift")
    require(decision["claim_type"] in CLAIM_TYPES, "claim type drift")
    candidates = decision["candidate_classes"]
    require(isinstance(candidates, list) and len(candidates) == len(set(candidates)) and set(candidates) <= CANDIDATE_CLASSES, "candidate classes drift")
    require(identity["family_id"] == "school_textbooks" or candidates == [], "candidate classes are textbook-only")
    views = decision["consumer_views"]
    require(isinstance(views, list) and len(views) == len(set(views)) and set(views) <= CONSUMER_VIEWS, "consumer views drift")
    require(isinstance(decision["rationale"], str) and decision["rationale"], "unit-specific rationale missing")
    if decision["disposition_code"] == "converted":
        require(isinstance(decision["artifact"], Mapping) and views, "converted decision lacks artifact or view")
        _validate_artifact(decision["artifact"])
    else:
        require(decision["artifact"] is None and views == [], "nonconverted decision carries artifact or view")
    if identity["family_id"] == "pravopys_2026_complete":
        require(decision["disposition_code"] != "superseded_or_historical", "2026 unit cannot be superseded/historical")
    return dict(decision)


def ingest_author(
    *, manifest_path: Path, packet_index: int, raw_response_path: Path,
    provider_invocation_receipt_path: Path, schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Preserve and validate one immutable Gemini response."""
    manifest, root = _manifest(manifest_path, schema_path)
    packet = _packet_for(manifest, root, packet_index, "author")
    _regular(raw_response_path, "raw author response")
    raw = raw_response_path.read_bytes()
    raw_target = root / "author" / "raw" / f"{packet_index:05d}.raw"
    raw_hash = _write_private(raw_target, raw)
    invocation = _read_json(provider_invocation_receipt_path, "author provider invocation receipt")
    _validate_provider_invocation(invocation, AUTHOR, packet["packet_id"], raw_hash)
    response = _strict_response(raw, "author")
    _validate(response, schema_path, "authorResponse")
    require(response["packet_id"] == packet["packet_id"] and response["identity_order"] == packet["identity_order"], "author response packet/order drift")
    require(len(response["decisions"]) == len(packet["identity_order"]), "author response decision count drift")
    decisions = [_validate_decision(row, identity) for row, identity in zip(response["decisions"], packet["identity_order"], strict=True)]
    normalized = {**response, "decisions": decisions}
    response_hash = _write_private_json(root / "author" / "responses" / f"{packet_index:05d}.json", normalized)
    record = {
        "schema_version": "phase3_source_production_author_transport_v1",
        "packet_index": packet_index,
        "packet_id": packet["packet_id"],
        "packet_sha256": manifest["author_packets"][packet_index - 1]["packet_sha256"],
        "raw_sha256": raw_hash,
        "response_sha256": response_hash,
        "invocation_receipt_sha256": sha256_file(provider_invocation_receipt_path),
        "actor": AUTHOR,
        "completed_at": _now(),
    }
    _write_private_json(root / "author" / "records" / f"{packet_index:05d}.json", record)
    return record


def _all_author_decisions(manifest: Mapping[str, Any], root: Path, schema_path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    decisions: list[dict[str, Any]] = []
    items: dict[str, dict[str, Any]] = {}
    for index in range(1, manifest["author_packet_count"] + 1):
        packet = _packet_for(manifest, root, index, "author")
        response_path = root / "author" / "responses" / f"{index:05d}.json"
        record_path = root / "author" / "records" / f"{index:05d}.json"
        response = _read_json(response_path, "author response")
        record = _read_json(record_path, "author transport")
        _validate(response, schema_path, "authorResponse")
        require(record["response_sha256"] == sha256_file(response_path), "author response custody drift")
        require(isinstance(record.get("invocation_receipt_sha256"), str), "author provider invocation proof missing")
        for item, decision, identity in zip(packet["items"], response["decisions"], packet["identity_order"], strict=True):
            validated = _validate_decision(decision, identity)
            decisions.append({"identity": identity, "decision": validated})
            items[identity["unit_id"]] = item
    require(len(decisions) == manifest["denominator"]["author"], "author output is incomplete")
    return decisions, items


def _review_selection(decisions: Sequence[Mapping[str, Any]], escalated_families: frozenset[str]) -> set[str]:
    selected: set[str] = set()
    nonconverted: dict[str, list[Mapping[str, Any]]] = {family: [] for family in LARGE_REVIEW_FAMILIES}
    for row in decisions:
        identity, decision = row["identity"], row["decision"]
        family, unit_id = identity["family_id"], identity["unit_id"]
        if decision["disposition_code"] == "converted" or family in SMALL_REVIEW_FAMILIES:
            selected.add(unit_id)
        elif family in LARGE_REVIEW_FAMILIES:
            nonconverted[family].append(row)
        else:
            selected.add(unit_id)
    for family, rows in nonconverted.items():
        if family in escalated_families:
            selected.update(row["identity"]["unit_id"] for row in rows)
            continue
        ranked = sorted(
            rows,
            key=lambda row: (
                sha256_value({"purpose": "source-review-nonhit", "family": family, "unit_id": row["identity"]["unit_id"]}),
                row["identity"]["unit_id"],
            ),
        )
        selected.update(row["identity"]["unit_id"] for row in ranked[: min(1000, len(ranked))])
    return selected


def prepare_review(
    *,
    manifest_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    item_limit: int = 24,
    byte_limit: int = MAX_UTF8_BYTES,
    escalated_families: Sequence[str] = (),
) -> dict[str, Any]:
    """Freeze independent Grok review packets after all Gemini packets exist."""
    manifest, root = _manifest(manifest_path, schema_path)
    escalated = frozenset(escalated_families)
    require(escalated <= LARGE_REVIEW_FAMILIES, "invalid source-review escalation family")
    decisions, items = _all_author_decisions(manifest, root, schema_path)
    selected = _review_selection(decisions, escalated)
    review_items = []
    for row in decisions:
        unit_id = row["identity"]["unit_id"]
        if unit_id in selected:
            review_items.append({**items[unit_id], "author_decision": row["decision"]})
    review_items.sort(key=lambda row: (row["identity"]["family_id"], row["identity"]["unit_id"]))
    packets = _pack_items(review_items, item_limit=item_limit, byte_limit=byte_limit, lane="review")
    entries: list[dict[str, Any]] = []
    for packet in packets:
        path = root / "review" / "packets" / f"{packet['packet_index']:05d}.json"
        packet_hash = _write_private_json(path, packet)
        entries.append(
            {
                "packet_index": packet["packet_index"],
                "packet_id": packet["packet_id"],
                "packet_sha256": packet_hash,
                "item_count": len(packet["items"]),
                "relative_path": str(path.relative_to(root)),
            }
        )
    review_manifest = {
        **manifest,
        "schema_version": "phase3_source_production_review_manifest_v1",
        "source_manifest_sha256": sha256_file(manifest_path),
        "review_policy": {
            "all_converted": True,
            "all_small_family_intents": True,
            "large_family_nonconverted_sample_formula": "min(1000,nonconverted_total)",
            "any_sample_miss_requires_full_family_review": True,
            "escalated_families": sorted(escalated),
        },
        "review_selection_sha256": sha256_value(sorted(selected)),
        "review_selected_count": len(selected),
        "review_packet_count": len(entries),
        "review_packets": entries,
        "created_at": _now(),
    }
    review_manifest.pop("manifest_sha256", None)
    review_manifest["manifest_sha256"] = sha256_value(review_manifest)
    _validate(review_manifest, schema_path, "reviewManifest")
    _write_private_json(root / "review-manifest.json", review_manifest)
    return review_manifest


def ingest_review(
    *, review_manifest_path: Path, packet_index: int, raw_response_path: Path,
    provider_invocation_receipt_path: Path, schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Preserve and validate one immutable Grok source-review response."""
    manifest, root = _manifest(review_manifest_path, schema_path)
    require(manifest["schema_version"] == "phase3_source_production_review_manifest_v1", "not a review manifest")
    packet = _packet_for(manifest, root, packet_index, "review")
    _regular(raw_response_path, "raw review response")
    raw = raw_response_path.read_bytes()
    raw_hash = _write_private(root / "review" / "raw" / f"{packet_index:05d}.raw", raw)
    invocation = _read_json(provider_invocation_receipt_path, "review provider invocation receipt")
    _validate_provider_invocation(invocation, REVIEWER, packet["packet_id"], raw_hash)
    response = _strict_response(raw, "review")
    _validate(response, schema_path, "reviewResponse")
    require(response["packet_id"] == packet["packet_id"] and response["identity_order"] == packet["identity_order"], "review response packet/order drift")
    require(len(response["reviews"]) == len(packet["identity_order"]), "review decision count drift")
    normalized_reviews: list[dict[str, Any]] = []
    for review, item, identity in zip(response["reviews"], packet["items"], packet["identity_order"], strict=True):
        require(review["unit_id"] == identity["unit_id"] and review["unit_sha256"] == identity["unit_sha256"], "review retargeted a unit")
        require(review["outcome"] in {"confirmed", "revised"}, "review outcome drift")
        decision = _validate_decision(review["decision"], identity)
        if review["outcome"] == "confirmed":
            require(decision == item["author_decision"], "confirmed review changed the author decision")
        else:
            require(decision != item["author_decision"], "revised review did not change the decision")
        normalized_reviews.append({**review, "decision": decision})
    normalized = {**response, "reviews": normalized_reviews}
    response_hash = _write_private_json(root / "review" / "responses" / f"{packet_index:05d}.json", normalized)
    record = {
        "schema_version": "phase3_source_production_review_transport_v1",
        "packet_index": packet_index,
        "packet_id": packet["packet_id"],
        "packet_sha256": manifest["review_packets"][packet_index - 1]["packet_sha256"],
        "raw_sha256": raw_hash,
        "response_sha256": response_hash,
        "invocation_receipt_sha256": sha256_file(provider_invocation_receipt_path),
        "actor": REVIEWER,
        "completed_at": _now(),
    }
    _write_private_json(root / "review" / "records" / f"{packet_index:05d}.json", record)
    return record


def _all_reviews(manifest: Mapping[str, Any], root: Path, schema_path: Path) -> dict[str, dict[str, Any]]:
    reviews: dict[str, dict[str, Any]] = {}
    for index in range(1, manifest["review_packet_count"] + 1):
        packet = _packet_for(manifest, root, index, "review")
        response_path = root / "review" / "responses" / f"{index:05d}.json"
        record_path = root / "review" / "records" / f"{index:05d}.json"
        response = _read_json(response_path, "review response")
        record = _read_json(record_path, "review transport")
        _validate(response, schema_path, "reviewResponse")
        require(record["response_sha256"] == sha256_file(response_path), "review response custody drift")
        require(isinstance(record.get("invocation_receipt_sha256"), str), "review provider invocation proof missing")
        for item, review, identity in zip(packet["items"], response["reviews"], packet["identity_order"], strict=True):
            require(review["unit_id"] == identity["unit_id"], "review order drift")
            reviews[identity["unit_id"]] = {**review, "author_decision": item["author_decision"]}
    require(len(reviews) == manifest["review_selected_count"], "review output is incomplete")
    return reviews


def _action_receipt(
    *, actor: Mapping[str, str], role_contract: Mapping[str, Any], role_contract_sha256: str,
    conflict_graph_sha256: str, action_kind: str, input_sha256: str, output_sha256: str,
    started_at: str, completed_at: str,
) -> dict[str, Any]:
    identity = {
        "role_id": actor["role_id"], "task_id": actor["task_id"], "input_manifest_sha256": input_sha256,
        "evaluation_cycle_id": role_contract["evaluation_cycle"]["evaluation_cycle_id"],
        "output_sha256": output_sha256, "status": "completed",
    }
    return {
        "receipt_id": "phase3_functional_action:" + sha256_value(identity),
        **dict(actor),
        "action_kind": action_kind,
        "input_manifest_sha256": input_sha256,
        "output_sha256": output_sha256,
        "evaluation_cycle_id": role_contract["evaluation_cycle"]["evaluation_cycle_id"],
        "base_contract_sha256": BASE_SHA256,
        "amendment_sha256": AMENDMENT_SHA256,
        "combined_contract_sha256": COMBINED_SHA256,
        "functional_role_contract_sha256": role_contract_sha256,
        "conflict_graph_sha256": conflict_graph_sha256,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "completed",
    }


def _disposition(identity: Mapping[str, str], decision: Mapping[str, Any]) -> dict[str, Any]:
    base = {
        "unit_id": identity["unit_id"],
        "unit_sha256": identity["unit_sha256"],
        "locator_sha256": identity["locator_sha256"],
        "disposition_code": decision["disposition_code"],
    }
    if decision["disposition_code"] == "converted":
        artifact_hash = sha256_value(decision["artifact"])
        canonical_identity = f"rule.{artifact_hash}"
        view = decision["consumer_views"][0]
        return {
            **base,
            "canonical_identity": canonical_identity,
            "source_role": decision["primary_source_role"],
            "claim_type": decision["claim_type"],
            "evidence_locator_sha256s": [identity["locator_sha256"]],
            "consumer_view": {"view_id": f"view.{view}", "view_sha256": sha256_value({"rule": artifact_hash, "view": view})},
            "predicate_sha256": sha256_value(decision["artifact"]["matcher"]),
            "artifact_sha256": artifact_hash,
        }
    row = {
        **base,
        "nonconversion": {
            "reason_code": decision["disposition_code"],
            "unit_specific_locator_sha256": identity["locator_sha256"],
            "unit_specific_rationale_sha256": sha256_bytes(decision["rationale"].encode("utf-8")),
        },
    }
    if identity["family_id"] == "antonenko_textbook_representation" and decision["disposition_code"] == "duplicate_representation":
        row["representation_source_identity"] = "source_identity.antonenko_davydovych_yak_my_hovorymo_v1"
    return row


def assemble(
    *,
    review_manifest_path: Path,
    reviewed_input_path: Path,
    source_review_receipt_path: Path,
    public_receipt_path: Path,
    textbook_classifications_path: Path,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
    disposition_schema_path: Path = DEFAULT_DISPOSITION_SCHEMA,
) -> dict[str, Any]:
    """Assemble reviewed exact dispositions; fail closed on any missing review or escalation."""
    manifest, root = _manifest(review_manifest_path, schema_path)
    require(manifest["schema_version"] == "phase3_source_production_review_manifest_v1", "not a review manifest")
    _assert_nonoverlap(
        (reviewed_input_path, source_review_receipt_path, public_receipt_path, textbook_classifications_path),
        (review_manifest_path, role_contract_path, schema_path, disposition_schema_path),
    )
    decisions, items = _all_author_decisions(manifest, root, schema_path)
    reviews = _all_reviews(manifest, root, schema_path)
    reviewed_decisions: dict[str, dict[str, Any]] = {}
    escalation_required: set[str] = set()
    selected = set(reviews)
    for row in decisions:
        identity, author_decision = row["identity"], row["decision"]
        unit_id, family = identity["unit_id"], identity["family_id"]
        review = reviews.get(unit_id)
        if author_decision["disposition_code"] == "converted" or family in SMALL_REVIEW_FAMILIES:
            require(review is not None, "load-bearing author output lacks source review")
        if review is not None:
            reviewed_decisions[unit_id] = review["decision"]
            if (
                family in LARGE_REVIEW_FAMILIES
                and author_decision["disposition_code"] != "converted"
                and review["outcome"] == "revised"
            ):
                escalation_required.add(family)
        else:
            reviewed_decisions[unit_id] = author_decision
    already_escalated = set(manifest["review_policy"]["escalated_families"])
    require(not (escalation_required - already_escalated), "source-review miss requires full large-family nonhit review")
    for family in already_escalated:
        expected_ids = {
            row["identity"]["unit_id"] for row in decisions
            if row["identity"]["family_id"] == family and row["decision"]["disposition_code"] != "converted"
        }
        require(expected_ids <= selected, "escalated family review is incomplete")

    deterministic = _read_jsonl(root / "deterministic-partition-dispositions.jsonl", "deterministic dispositions")
    dispositions_by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in manifest["denominator"]["family_totals"]}
    artifacts: list[dict[str, Any]] = []
    textbook: list[dict[str, Any]] = []
    for row in decisions:
        identity = row["identity"]
        decision = reviewed_decisions[identity["unit_id"]]
        dispositions_by_family[identity["family_id"]].append(_disposition(identity, decision))
        if decision["disposition_code"] == "converted":
            artifacts.append(
                {
                    "unit_id": identity["unit_id"],
                    "unit_sha256": identity["unit_sha256"],
                    "artifact_sha256": sha256_value(decision["artifact"]),
                    "artifact": decision["artifact"],
                    "consumer_views": decision["consumer_views"],
                }
            )
        if identity["family_id"] == "school_textbooks":
            source = items[identity["unit_id"]]
            textbook.append(
                {
                    "unit_id": identity["unit_id"],
                    "unit_sha256": identity["unit_sha256"],
                    "locator": source["frozen_locator"],
                    "candidate_classes": sorted(decision["candidate_classes"]),
                }
            )
    for row in deterministic:
        dispositions_by_family[row["family_id"]].append(
            {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "locator_sha256": row["locator_sha256"],
                "disposition_code": row["disposition_code"],
                "nonconversion": {
                    "reason_code": row["reason_code"],
                    "unit_specific_locator_sha256": row["locator_sha256"],
                    "reason_predicate_sha256": row["reason_predicate_sha256"],
                },
            }
        )
        if row["family_id"] == "school_textbooks":
            textbook.append(
                {
                    "unit_id": row["unit_id"],
                    "unit_sha256": row["unit_sha256"],
                    "locator": row["frozen_locator"],
                    "candidate_classes": [],
                }
            )
    families = []
    for family in sorted(dispositions_by_family):
        rows = sorted(dispositions_by_family[family], key=lambda item: item["unit_id"])
        require(len(rows) == manifest["denominator"]["family_totals"][family], f"final family count drift: {family}")
        families.append(
            {
                "family_id": family,
                "ledger_sha256": manifest["source_freeze_family_bindings"][family]["ledger_sha256"],
                "unit_count": manifest["denominator"]["family_totals"][family],
                "dispositions": rows,
            }
        )
    require(sum(len(family["dispositions"]) for family in families) == manifest["denominator"]["total"], "final disposition denominator drift")
    role_contract, role_sha, graph_sha = _role_bindings(role_contract_path)
    family_sha = sha256_value(families)
    started_at = manifest["created_at"]
    completed_at = _now()
    author_input_sha = sha256_value({"source_freeze_receipt_sha256": manifest["bindings"]["source_freeze_receipt_sha256"]})
    author_action = _action_receipt(
        actor=AUTHOR, role_contract=role_contract, role_contract_sha256=role_sha,
        conflict_graph_sha256=graph_sha, action_kind="source_disposition_proposal",
        input_sha256=author_input_sha, output_sha256=family_sha, started_at=started_at, completed_at=completed_at,
    )
    review_input_sha = sha256_value(
        {
            "source_freeze_receipt_sha256": manifest["bindings"]["source_freeze_receipt_sha256"],
            "disposition_families_sha256": family_sha,
            "author_action_receipt_id": author_action["receipt_id"],
        }
    )
    review_action = _action_receipt(
        actor=REVIEWER, role_contract=role_contract, role_contract_sha256=role_sha,
        conflict_graph_sha256=graph_sha, action_kind="source_disposition_review",
        input_sha256=review_input_sha, output_sha256=sha256_value({"verdict": "APPROVE"}),
        started_at=started_at, completed_at=completed_at,
    )
    source_review_receipt = {
        "schema_version": "phase3_source_disposition_review_receipt_v2_1",
        "text_free": True,
        "reviewer_role_id": REVIEWER["role_id"],
        "task_id": REVIEWER["task_id"],
        "source_freeze_receipt_sha256": manifest["bindings"]["source_freeze_receipt_sha256"],
        "disposition_families_sha256": family_sha,
        "verdict": "APPROVE",
        "action_receipt": review_action,
    }
    _write_private_json(source_review_receipt_path, source_review_receipt)
    reviewed_input = {
        "schema_version": "phase3_source_disposition_input_v2_1",
        "text_free": True,
        "phase3_v2_contract_sha256": BASE_SHA256,
        "phase3_v2_1_amendment_sha256": AMENDMENT_SHA256,
        "combined_contract_sha256": COMBINED_SHA256,
        "producer_task_id": "phase3-v2-1-disposition-ledger-production",
        "source_freeze_receipt_sha256": manifest["bindings"]["source_freeze_receipt_sha256"],
        "role_contract_sha256": role_sha,
        "conflict_graph_sha256": graph_sha,
        "author_binding": {"role_id": AUTHOR["role_id"], "task_id": AUTHOR["task_id"], "action_receipt": author_action},
        "source_review_binding": {
            "role_id": REVIEWER["role_id"], "task_id": REVIEWER["task_id"],
            "receipt_sha256": sha256_file(source_review_receipt_path),
        },
        "families": families,
    }
    if manifest["denominator"]["total"] == EXPECTED_TOTAL:
        _validate_document(reviewed_input, disposition_schema_path, "reviewed disposition input")
    _write_private_json(reviewed_input_path, reviewed_input)
    textbook.sort(key=lambda row: row["unit_id"])
    require(len(textbook) == manifest["denominator"]["family_totals"].get("school_textbooks", 0), "textbook classification denominator drift")
    _write_private_jsonl(textbook_classifications_path, textbook)
    _write_private_jsonl(root / "assembled" / "reviewed-rule-artifacts.jsonl", artifacts)
    public = {
        "schema_version": "phase3_source_production_public_receipt_v1",
        "text_free": True,
        "bindings": manifest["bindings"],
        "manifest_sha256": sha256_file(review_manifest_path),
        "family_sha256": family_sha,
        "denominator": {
            "input_total": manifest["denominator"]["total"],
            "author_produced_total": manifest["denominator"]["author"],
            "source_review_selected_total": len(reviews),
            "source_review_revised_total": sum(
                review["outcome"] == "revised" for review in reviews.values()
            ),
            "evaluation_only_total": manifest["denominator"]["evaluation"],
            "quarantined_total": manifest["denominator"]["quarantine"],
            "converted_total": sum(
                1 for family in families for row in family["dispositions"] if row["disposition_code"] == "converted"
            ),
        },
        "review_coverage": manifest["review_policy"],
        "review_complete": True,
    }
    public["receipt_sha256"] = sha256_value(public)
    _validate(public, schema_path, "publicReceipt")
    _public_safe(public)
    _write_private_json(public_receipt_path, public)
    return public


def _public_safe(value: Any) -> None:
    forbidden = {
        "unit_id", "unit_sha256", "source_text", "source_record", "frozen_locator",
        "identity_order", "packet_id", "artifact", "rationale", "labels",
    }
    if isinstance(value, Mapping):
        require(not (set(value) & forbidden), "public receipt leaks private data")
        for child in value.values():
            _public_safe(child)
    elif isinstance(value, list):
        for child in value:
            _public_safe(child)


def _config(path: Path) -> dict[str, Any]:
    return _read_json(path, "command configuration")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("prepare", "run-author", "ingest-author", "prepare-review", "run-review", "ingest-review", "assemble"),
    )
    parser.add_argument("--input", required=True, type=Path, help="Strict JSON command configuration")
    args = parser.parse_args(argv)
    config = _config(args.input)
    try:
        if args.command == "prepare":
            result = prepare(**{key: Path(value) if key.endswith("_path") or key.endswith("_jsonl") or key == "private_dir" else value for key, value in config.items()})
        elif args.command == "run-author":
            result = run_author(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
        elif args.command == "ingest-author":
            result = ingest_author(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
        elif args.command == "prepare-review":
            result = prepare_review(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
        elif args.command == "run-review":
            result = run_review(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
        elif args.command == "ingest-review":
            result = ingest_review(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
        else:
            result = assemble(**{key: Path(value) if key.endswith("_path") else value for key, value in config.items()})
    except (KeyError, TypeError, SourceProductionError) as exc:
        parser.error(str(exc))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
