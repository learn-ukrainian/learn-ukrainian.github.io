#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 operator resolutions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
RES_PATH = HERE / "phase3-apply-cycle007-operator-resolutions-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


res_mod = _load_module(RES_PATH, "res_mod")


def _setup_resolution_package(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)

    clean_rows = [{"unit_id": "u-1", "unit_sha256": "1" * 64}]

    # Packet
    clean_dir = pkg / "clean_label"
    clean_dir.mkdir(parents=True, mode=0o700)
    p1 = clean_dir / "packet-0001.json"
    p1.write_text(json.dumps({"rows": clean_rows}) + "\n")
    p1.chmod(0o600)

    # Custody & Manifest
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
    }
    (pkg / "custody-receipt.json").write_text(json.dumps(custody) + "\n")
    (pkg / "custody-receipt.json").chmod(0o600)

    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest) + "\n")
    (pkg / "manifest.json").chmod(0o600)

    # Comparison output
    comp_dir = pkg / res_mod.COMPARE_OUTPUT / "clean_label"
    comp_dir.mkdir(parents=True, mode=0o700)
    (comp_dir / "clean-consensus-0001.json").write_text(json.dumps({"records": []}) + "\n")
    (comp_dir / "clean-consensus-0001.json").chmod(0o600)
    (comp_dir / "risk-consensus-0001.json").write_text(json.dumps({"records": []}) + "\n")
    (comp_dir / "risk-consensus-0001.json").chmod(0o600)

    # Adjudication output
    adj_dir = pkg / res_mod.ADJUDICATION_OUTPUT / "final" / "clean_label"
    adj_dir.mkdir(parents=True, mode=0o700)
    (adj_dir / "labels-0001.json").write_text(json.dumps({"labels": []}) + "\n")
    (adj_dir / "labels-0001.json").chmod(0o600)

    unresolved_record = {
        "source_row": clean_rows[0],
        "grok_label": {
            "unit_id": "u-1",
            "unit_sha256": "1" * 64,
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": [],
        },
        "gemini_label": {
            "unit_id": "u-1",
            "unit_sha256": "1" * 64,
            "decision_code": "reject_fragment_or_too_short",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        },
    }
    (adj_dir / "unresolved-0001.json").write_text(json.dumps({"records": [unresolved_record]}) + "\n")
    (adj_dir / "unresolved-0001.json").chmod(0o600)

    return pkg, clean_rows


def _make_authorization(pkg: Path, authorizations: list[dict[str, Any]]) -> Path:
    auth_doc = {
        "schema_version": "phase3_cycle007_operator_resolution_authorization_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": res_mod.digest((pkg / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": res_mod.digest((pkg / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": res_mod.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "authorizations": authorizations,
    }
    auth_p = pkg / "auth.json"
    auth_p.write_text(json.dumps(auth_doc) + "\n")
    auth_p.chmod(0o600)
    return auth_p


def test_operator_resolution_success(tmp_path):
    pkg, _rows = _setup_resolution_package(tmp_path)
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": "u-1",
                "unit_sha256": "1" * 64,
                "selection": "grok",
                "source_bound_rationale": "Grok label agrees with Slovnyk normative entry",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )

    auths = res_mod.validate_authorization_file(auth_p, pkg)
    assert ("u-1", "1" * 64) in auths

    result = res_mod.resolve_packet(pkg, "clean_label", 1, auths)
    assert result["unresolved_remaining_count"] == 0

    final_labels_p = pkg / res_mod.RESOLUTION_OUTPUT / "final" / "clean_label" / "labels-0001.json"
    final_data = json.loads(final_labels_p.read_text())
    assert len(final_data["labels"]) == 1
    assert final_data["labels"][0]["decision_code"] == "agree"


def test_operator_resolution_tamper_detection(tmp_path):
    pkg, _rows = _setup_resolution_package(tmp_path)
    # Missing source_authority_reference
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": "u-1",
                "unit_sha256": "1" * 64,
                "selection": "grok",
                "source_bound_rationale": "Missing authority reference",
            }
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg)
    assert exc.value.failure_code == "authorization_tamper_detected"


def test_operator_resolution_candidate_invention_rejected(tmp_path):
    pkg, _rows = _setup_resolution_package(tmp_path)
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": "u-1",
                "unit_sha256": "1" * 64,
                "selection": "invented_third_model",
                "source_bound_rationale": "Invalid",
                "source_authority_reference": "ref",
            }
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg)
    assert exc.value.failure_code == "authorization_tamper_detected"


def test_operator_resolution_missing_authorization(tmp_path):
    pkg, _rows = _setup_resolution_package(tmp_path)
    # Empty authorizations
    auth_p = _make_authorization(pkg, [])
    auths = res_mod.validate_authorization_file(auth_p, pkg)

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths)
    assert exc.value.failure_code == "missing_authorization"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
