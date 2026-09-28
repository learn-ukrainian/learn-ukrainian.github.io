#!/usr/bin/env python3
"""Freeze P1's additive dialect/regional protection amendment (#7426).

The amendment is deliberately separate from P1 v1.  It reads only P1's
committed metadata artifact, adds one denominator-visible protected stratum,
and never opens source/evidence bodies or creates a dataset record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data.companion_publication import publish_bound_companion
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR

DATA = REGISTRY_OPEN_MODEL_DATA_DIR
P1 = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
OUTPUT = DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
PINNED_P1_MANIFEST_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
# Frozen-contract generator provenance independently pinned to 55d0ed1515.
FROZEN_GENERATOR_SHA256 = "3201e5b748505b9ea30e4a011312fabf6445936e2f327aa0067be4bcd56bcab4"
SCHEMA_VERSION = "phase3_p1_dialect_regional_protection_amendment_v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def artifact(path: Path) -> dict[str, str]:
    logical = (
        "data/projects/open_model_data/" + path.relative_to(DATA).as_posix()
        if path.is_relative_to(DATA)
        else path.relative_to(ROOT).as_posix()
    )
    digest = FROZEN_GENERATOR_SHA256 if path.resolve() == Path(__file__).resolve() else sha256_file(path)
    return {"path": logical, "sha256": digest}


def read_p1() -> dict[str, Any]:
    if sha256_file(P1) != PINNED_P1_MANIFEST_SHA256:
        raise ValueError("p1_artifact_sha_drift")
    value = json.loads(P1.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "phase3_p1_universe_freeze_v1":
        raise ValueError("p1_schema_drift")
    if value.get("controlling_outcome_sha256") != OUTCOME_SHA256 or value.get("text_free") is not True:
        raise ValueError("p1_outcome_or_text_free_drift")
    return value


def build_amendment() -> dict[str, Any]:
    p1 = read_p1()
    base_cells = p1.get("required_cell_manifest", {}).get("cells")
    if not isinstance(base_cells, list) or len(base_cells) != 15:
        raise ValueError("p1_denominator_drift")
    additive_cell = {
        "cell_id": "protection.source_attested_ukrainian_dialect_or_regional_form.dialect_or_regional_form.protected_dialect_or_regional",
        "language_identity": "source_attested_ukrainian_dialect_or_regional_form",
        "context_role": "dialect_or_regional_form",
        "phenomenon": "dialect_or_regional_identity",
        "role": "protected_dialect_or_regional",
        "status": "coverage_blocked",
        "protection_required": True,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": "INVENTORIED",
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "base_p1_manifest": artifact(P1),
        "amendment": {
            "amendment_version": "v1",
            "kind": "additive_dialect_regional_protection",
            "base_p1_rewritten": False,
            "base_required_cell_count": len(base_cells),
            "additive_required_cell_count": 1,
            "composite_required_cell_count": len(base_cells) + 1,
            "additive_cells": [additive_cell],
        },
        "dialect_regional_protection": {
            "source_qualified_identity_required": True,
            "region_required": True,
            "register_required": True,
            "dialect_or_regional_forms_protected": True,
            "modern_correction_eligible": False,
            "automatic_normalization_to_modern_standard_ukrainian": False,
            "automatic_mapping_to_modern_national_successor": False,
            "identity_or_region_unknown_route": "coverage_blocked_or_abstention",
        },
        "safety": {
            "provider_calls": False,
            "labels_created": False,
            "dataset_rows_emitted": False,
            "gold_created": False,
            "training_performed": False,
        },
        "generator": artifact(Path(__file__)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = canonical_json(build_amendment())
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != expected:
            raise SystemExit("p1_dialect_regional_amendment_drift")
        print("p1_dialect_regional_amendment_verified")
        return 0
    if args.output.resolve() == OUTPUT.resolve():
        publish_bound_companion(
            ROOT, "open_model_evidence_indexes", "freeze_phase3_p1_dialect_regional", OUTPUT, expected
        )
    else:
        if args.output.absolute().is_relative_to(DATA) or args.output.resolve().is_relative_to(DATA):
            raise ValueError(f"unbound managed P1 amendment output: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(expected)
    print(f"wrote {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
