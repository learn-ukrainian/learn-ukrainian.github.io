#!/usr/bin/env python3
"""Freeze #7428's six modern Cyrillic-contact channel dispositions.

This is deliberately a text-free, metadata-only boundary.  It records the
six P1 cells and why none can be promoted while P2's qualified-human registry
remains nonadmitting.  It neither selects a source unit nor creates a case,
correction target, label, provider request, gold record, or training row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
P1_PATH = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P1_AMENDMENT_PATH = DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
P2_PATH = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
FIREWALL_PATH = DATA / "evidence/phase3_scope_circularity_firewall_v1.json"
SCHEMA_PATH = DATA / "contracts/phase3_modern_contact_channels_v1.schema.json"
OUTPUT_PATH = DATA / "admission/phase3_modern_contact_channels_v1.json"

SCHEMA_VERSION = "phase3_modern_contact_channels_v1"
OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
P1_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
P1_AMENDMENT_SHA256 = "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa"
P2_SHA256 = "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3"
FIREWALL_SHA256 = "4470448c6d0f665196375cf28255d7c092148700a99934b2d0dd1f43a8a3e24c"
COMPOSITE_INPUT_SHA256 = "83b59c6b62fff0beaf68dec7c3ca40b70033693dc19c50f26d27c553265352b0"

MODERN_CLASSES = (
    "russian",
    "belarusian",
    "bulgarian",
    "macedonian",
    "serbian_cyrillic",
    "montenegrin_cyrillic",
)
MODERN_CELL_IDS = tuple(
    f"modern.{language}.unmarked.contact_interference.source_backed_correction" for language in MODERN_CLASSES
)
PROTECTED_CONTEXT_ROLES = (
    "quotation",
    "code_switch",
    "transliteration",
    "metalinguistic_example",
    "name_title",
    "dialect_or_regional_form",
    "historical_text",
    "ambiguous_noisy",
)


class ModernContactChannelsError(ValueError):
    """A frozen dependency or generated disposition is not safe."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(Path(path).read_bytes())
    except OSError as exc:
        raise ModernContactChannelsError(f"cannot read required artifact: {path}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ModernContactChannelsError(message)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModernContactChannelsError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _artifact(path: Path, expected_sha256: str) -> dict[str, str]:
    actual = sha256_file(path)
    require(actual == expected_sha256, f"{path.name} hash drift")
    return {"logical_path": path.relative_to(ROOT).as_posix(), "sha256": actual}


def _validate_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    p1 = _read_json(P1_PATH, "P1 universe freeze")
    amendment = _read_json(P1_AMENDMENT_PATH, "P1 dialect amendment")
    p2 = _read_json(P2_PATH, "P2 canonical contract")
    firewall = _read_json(FIREWALL_PATH, "#7427 evaluation firewall")
    for value, name, schema_version in (
        (p1, "P1 universe freeze", "phase3_p1_universe_freeze_v1"),
        (amendment, "P1 dialect amendment", "phase3_p1_dialect_regional_protection_amendment_v1"),
        (p2, "P2 canonical contract", "phase3_p2_canonical_contracts_v1"),
        (firewall, "#7427 evaluation firewall", "phase3_scope_circularity_firewall_v1"),
    ):
        require(
            value.get("schema_version") == schema_version
            and value.get("text_free") is True
            and value.get("controlling_outcome_sha256") == OUTCOME_SHA256,
            f"{name} binding drift",
        )
    require(p1.get("status") == "INVENTORIED", "P1 status drift")
    require(amendment.get("status") == "INVENTORIED", "P1 amendment status drift")
    require(p2.get("status") == "FROZEN_METADATA_ONLY", "P2 status drift")
    require(firewall.get("status") == "FROZEN_METADATA_ONLY", "#7427 status drift")

    language_universe = p1.get("language_universe")
    cells = p1.get("required_cell_manifest", {}).get("cells")
    require(isinstance(language_universe, dict) and isinstance(cells, list), "P1 source or cell shape drift")
    require(
        tuple(language_universe.get("modern_contact_classes", ())) == MODERN_CLASSES
        and language_universe.get("modern_contact_classes_exhaustive") is True
        and language_universe.get("script_is_language_identity") is False,
        "P1 modern language universe drift",
    )
    cell_map = {cell.get("cell_id"): cell for cell in cells if isinstance(cell, dict)}
    require(len(cells) == 15 and set(cell_id for cell_id in cell_map if cell_id in MODERN_CELL_IDS) == set(MODERN_CELL_IDS), "P1 modern cell denominator drift")
    for language, cell_id in zip(MODERN_CLASSES, MODERN_CELL_IDS, strict=True):
        require(
            cell_map[cell_id]
            == {
                "cell_id": cell_id,
                "language_identity": language,
                "context_role": "unmarked_modern_ukrainian",
                "phenomenon": "contact_interference",
                "role": "source_backed_correction",
                "status": "coverage_blocked",
                "protection_required": False,
            },
            f"P1 modern cell drift: {language}",
        )

    p1_binding = p2.get("p1_binding")
    adjudication = p2.get("adjudication_contract")
    require(isinstance(p1_binding, dict) and isinstance(adjudication, dict), "P2 binding shape drift")
    require(
        p1_binding.get("source_unit_count") == 57
        and p1_binding.get("unknown_rights_blocker_count") == 39
        and p1_binding.get("required_cell_count") == 15
        and p1_binding.get("composite_required_cell_count") == 16
        and p1_binding.get("composite_input_sha256") == COMPOSITE_INPUT_SHA256,
        "P2 denominator drift",
    )
    require(
        adjudication
        == {
            "registry_status": "FROZEN_NONADMITTING",
            "semantic_case_admission_permitted": False,
            "required_adjudicator_qualification": {
                "actor_kind": "human",
                "authority_kind": "source_qualified_human_adjudication",
                "qualification_status": "registered_source_qualified_human",
            },
            "required_adjudication_record": {
                "record_identity_rule": "sha256_canonical_adjudication_metadata",
                "record_sha256_required": True,
                "source_qualified_identity_bound": True,
                "evidence_ref_ids_bound": True,
            },
            "adjudication_registry_sha256": None,
        },
        "P2 nonadmitting authority contract drift",
    )
    require(
        amendment.get("amendment", {}).get("base_required_cell_count") == 15
        and amendment.get("amendment", {}).get("additive_required_cell_count") == 1
        and amendment.get("amendment", {}).get("composite_required_cell_count") == 16,
        "P1 amendment denominator drift",
    )
    require(
        firewall.get("denominator")
        == {
            "source_units": 57,
            "unknown_rights_blockers": 39,
            "base_required_cells": 15,
            "composite_required_cells": 16,
            "coverage_blocked_cells": 14,
            "not_applicable_cells": 2,
            "rule_slots_R": 0,
            "canonical_order_required": True,
            "membership_hash_required": True,
        }
        and firewall.get("cycle007", {}).get("private_binding_state") == "BOUND"
        and firewall.get("cycle007", {}).get("state") == "evaluation_only",
        "#7427 merged firewall denominator drift",
    )
    return p1, amendment, p2, firewall


def _channel(language_identity: str, cell_id: str) -> dict[str, Any]:
    return {
        "cell_id": cell_id,
        "language_identity": language_identity,
        "language_identity_basis": "source_qualified_not_script_inferred",
        "script_identity_rule": "cyrillic_script_is_not_language_identity",
        "context_role": "unmarked_modern_ukrainian",
        "phenomenon": "contact_interference",
        "role": "source_backed_correction",
        "status": "coverage_blocked",
        "source_blocker": {
            "source_unit_identity_sha256": None,
            "source_artifact_sha256": None,
            "provenance_status": "source_qualified_evidence_not_bound",
            "rights_status": "unknown_rights_blocker",
            "source_disposition": "coverage_blocked",
        },
        "adjudication_blocker": {
            "registry_status": "FROZEN_NONADMITTING",
            "semantic_case_admission_permitted": False,
            "adjudication_registry_sha256": None,
            "source_qualified_human_record_sha256": None,
            "model_proposal_may_promote": False,
        },
        "protected_context_roles": list(PROTECTED_CONTEXT_ROLES),
    }


def build_contract() -> dict[str, Any]:
    """Build the exact, nonadmitting #7428 disposition contract."""
    _validate_inputs()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION",
        "text_free": True,
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "bindings": {
            "p1": _artifact(P1_PATH, P1_SHA256),
            "p1_dialect_regional_amendment": _artifact(P1_AMENDMENT_PATH, P1_AMENDMENT_SHA256),
            "p2": _artifact(P2_PATH, P2_SHA256),
            "phase3_scope_circularity_firewall": _artifact(FIREWALL_PATH, FIREWALL_SHA256),
            "composite_denominator": {
                "base_required_cell_count": 15,
                "additive_required_cell_count": 1,
                "composite_required_cell_count": 16,
                "composite_input_sha256": COMPOSITE_INPUT_SHA256,
                "modern_channel_cell_count": 6,
                "unknown_rights_blocker_count": 39,
                "rule_slots_R": 0,
            },
        },
        "channels": [
            _channel(language, cell_id) for language, cell_id in zip(MODERN_CLASSES, MODERN_CELL_IDS, strict=True)
        ],
        "protected_context_roles": list(PROTECTED_CONTEXT_ROLES),
        "safety_counters": {
            "correction_targets_emitted": 0,
            "dataset_rows_emitted": 0,
            "labels_created": 0,
            "gold_created": 0,
            "provider_requests": 0,
            "training_rows_emitted": 0,
        },
        "claims": {
            "all_six_channels_coverage_blocked": True,
            "script_is_not_language_identity": True,
            "model_proposals_are_nonadmitting": True,
            "source_qualified_human_authority_registered": False,
            "source_qualified_human_adjudication_present": False,
        },
        "generator": {
            "logical_path": "scripts/projects/open_model_data/phase3_modern_contact_channels.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
    }
    body["receipt_sha256"] = sha256_bytes(canonical_bytes(body))
    return body


def validate_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed unless a value is the exact current deterministic contract."""
    schema = _read_json(SCHEMA_PATH, "modern contact channel schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    require(not errors, f"schema violation: {errors[0].message if errors else ''}")
    expected = build_contract()
    require(dict(value) == expected, "modern contact channel contract drift")
    require(value.get("receipt_sha256") == sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"})), "receipt hash drift")
    return expected


def write_output(path: Path = OUTPUT_PATH) -> dict[str, Any]:
    value = build_contract()
    payload = canonical_bytes(value)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, destination)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze #7428 modern Cyrillic-contact channel dispositions.")
    parser.add_argument("--check", action="store_true", help="verify the checked-in deterministic admission receipt")
    args = parser.parse_args(argv)
    expected = build_contract()
    if args.check:
        return 0 if OUTPUT_PATH.exists() and OUTPUT_PATH.read_bytes() == canonical_bytes(expected) else 1
    write_output()
    print(json.dumps({"ok": True, "channel_count": 6, "status": expected["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
