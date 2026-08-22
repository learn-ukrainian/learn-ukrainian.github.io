#!/usr/bin/env python3
"""Synthetic tests for the Cycle 007 controller."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract


def _load_controller() -> Any:
    path = ROOT / "batch_state" / "phase3-run-cycle007-controller-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_controller", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CTRL = _load_controller()


def put(path: Path, value: Any) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    data = CTRL.canonical(value)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return data


def put_raw(path: Path, value: bytes) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    path.write_bytes(value)
    os.chmod(path, 0o600)
    return value


def make_controller_fixtures(root: Path) -> tuple[Path, Path, Path, dict[str, Path]]:
    package = root / "package"
    package.mkdir(parents=True, mode=0o700)
    os.chmod(package, 0o700)

    # 1. Custody receipt
    custody_val = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "amendment_reference": "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
        "source_custody_receipt_raw_sha256": CTRL.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": CTRL.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": CTRL.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "identity_union_commitment_sha256": "5" * 64,
        "ordered_packet_commitment_sha256": "6" * 64,
        "packet_count": 204,
        "row_count": 10159,
        "text_free": True,
    }
    custody_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(custody_val))
    custody_bytes = put(package / "custody-receipt.json", custody_val)
    custody_sha = CTRL.digest(custody_bytes)

    # 2. Manifest
    manifest_val = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": custody_sha,
        "packet_count": 204,
        "row_count": 10159,
        "packets": [],
        "text_free": True,
    }
    manifest_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(manifest_val))
    manifest_bytes = put(package / "manifest.json", manifest_val)
    manifest_sha = CTRL.digest(manifest_bytes)

    # 3. Evidence manifest
    ev_manifest_val = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": CTRL.CYCLE,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_sha256": "e" * 64},
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
        "packet_count": 204,
        "row_count": 10159,
        "network_lookups_performed": 0,
        "sidecars": [],
        "source_package_binding": None,
    }
    ev_manifest_val["manifest_sha256"] = contract.sha256_value(ev_manifest_val)
    ev_manifest_bytes = put(package / "evidence-manifest.json", ev_manifest_val)
    ev_manifest_sha = CTRL.digest(ev_manifest_bytes)

    # 4. Canary receipt
    canary_receipt_val = {
        "schema_version": CTRL.CANARY_RECEIPT_SCHEMA,
        "evaluation_cycle_id": CTRL.CYCLE,
        "ok": True,
        "execution_mode": "synthetic",
        "exact_model": CTRL.GEMINI_MODEL,
        "harness": "agy",
        "real_provider_attested": True,
        "text_free": True,
    }
    canary_receipt_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(canary_receipt_val))
    canary_receipt_path = root / "canary-receipt.json"
    canary_bytes = put(canary_receipt_path, canary_receipt_val)
    canary_sha = CTRL.digest(canary_bytes)

    # 5. Code paths
    code_paths: dict[str, Path] = {}
    for label, path in CTRL.REQUIRED_CODE_PATHS.items():
        code_paths[label] = path

    # Create dummy runners for the other stages
    for label in ("compare_runner", "audit_runner", "adjudicate_runner", "resolve_runner", "certify_runner"):
        dummy = root / f"dummy_{label}.py"
        dummy.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        dummy.chmod(0o755)
        code_paths[label] = dummy

    code_hashes = {label: CTRL.sha256(path) for label, path in code_paths.items()}

    # 6. Preflight receipt
    preflight_val = {
        "schema_version": "phase3_cycle007_preflight_receipt_v1",
        "amendment_sha256": CTRL.AMENDMENT_SHA256,
        "package_custody_receipt_sha256": custody_sha,
        "package_manifest_sha256": manifest_sha,
        "package_evidence_manifest_sha256": ev_manifest_sha,
        "public_canary_receipt_sha256": canary_sha,
        "code_hashes": code_hashes,
        "backup_receipt_sha256": "7" * 64,
        "review_hashes": {"source_authority_review": "8" * 64, "scope_circularity_review": "9" * 64},
        "ci_proof_bindings": {"ci_proof": "a" * 64},
        "sources_endpoint_identity": {
            "server_code_sha256": "f" * 64,
            "sources_db_sha256": "1" * 64,
            "vesum_db_sha256": "2" * 64,
        },
        "text_free": True,
    }
    preflight_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(preflight_val))
    preflight_path = root / "preflight-receipt.json"
    put(preflight_path, preflight_val)

    return package, preflight_path, canary_receipt_path, code_paths


def test_preflight_valid(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    assert proof["ok"] is True
    assert proof["text_free"] is True


def test_preflight_fails_on_hash_drift(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    # Mutate custody receipt
    put(pkg / "custody-receipt.json", {"schema_version": "phase3_cycle007_custody_receipt_v1"})
    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, canary_path)


def test_status_action(tmp_path: Path) -> None:
    pkg, _preflight_path, _canary_path, _code_paths = make_controller_fixtures(tmp_path)
    st = CTRL.status(pkg)
    assert st["completed_stages"] == []
    assert st["stopped"] is False
    assert st["ready"] is False
    assert st["text_free"] is True


def test_plan_action_gemini(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    res = CTRL.run_stage(
        pkg,
        "gemini",
        None,
        proof["preflight_receipt_sha256"],
        dry_run=True,
        concurrency=1,
        expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
        expected_custody_sha256=proof["expected_custody_sha256"],
        expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
        expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
        code_paths=code_paths,
    )
    assert res["ok"] is True
    assert res["stage"] == "gemini"
    assert res["concurrency"] == 1


def test_stage_sequence_enforced(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    # Try running grok before gemini
    with pytest.raises(CTRL.ControllerError, match="noncontiguous_stage_order"):
        CTRL.run_stage(
            pkg,
            "grok",
            code_paths["grok_runner"],
            proof["preflight_receipt_sha256"],
            dry_run=False,
            concurrency=1,
            code_paths=code_paths,
        )


def test_stop_present_blocks_stages(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    # Create stop file
    stop_dir = pkg / "label-output-gemini-cycle007-v1"
    stop_dir.mkdir(parents=True, mode=0o700)
    (stop_dir / "provider-stop.json").write_text("{}")

    with pytest.raises(CTRL.ControllerError, match="provider_stop_present"):
        CTRL.run_stage(
            pkg,
            "gemini",
            None,
            proof["preflight_receipt_sha256"],
            dry_run=True,
            concurrency=1,
            expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
            expected_custody_sha256=proof["expected_custody_sha256"],
            expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
            expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
            code_paths=code_paths,
        )


def test_concurrency_drift_rejected(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    with pytest.raises(CTRL.ControllerError, match="concurrency_drift"):
        CTRL.run_stage(
            pkg,
            "gemini",
            None,
            proof["preflight_receipt_sha256"],
            dry_run=True,
            concurrency=2,
            expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
            expected_custody_sha256=proof["expected_custody_sha256"],
            expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
            expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
            code_paths=code_paths,
        )


def test_certify_requires_operator_inspected_count(tmp_path: Path) -> None:
    pkg, preflight_path, canary_path, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, canary_path)
    # Mark prior stages complete
    for stage in CTRL.STAGES[:-1]:
        CTRL._seal(pkg, stage, proof["preflight_receipt_sha256"])

    with pytest.raises(CTRL.ControllerError, match="operator_inspected_count_required"):
        CTRL.run_stage(
            pkg,
            "certify",
            code_paths["certify_runner"],
            proof["preflight_receipt_sha256"],
            dry_run=True,
            concurrency=1,
            code_paths=code_paths,
            operator_inspected_count=None,
        )


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="controller_test_"))
    try:
        test_preflight_valid(tmp / "t1")
        test_preflight_fails_on_hash_drift(tmp / "t2")
        test_status_action(tmp / "t3")
        test_plan_action_gemini(tmp / "t4")
        test_stage_sequence_enforced(tmp / "t5")
        test_stop_present_blocks_stages(tmp / "t6")
        test_concurrency_drift_rejected(tmp / "t7")
        test_certify_requires_operator_inspected_count(tmp / "t8")
        print(
            json.dumps(
                {"ok": True, "synthetic_only": True, "provider_calls": 0, "text_free": True},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
