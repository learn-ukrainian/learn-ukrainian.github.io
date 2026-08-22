#!/usr/bin/env python3
"""Synthetic and adversarial tests for the hardened Cycle 007 controller."""

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

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
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


def make_controller_fixtures(root: Path) -> tuple[Path, Path, Path, Path, dict[str, Path]]:
    package = root / "package"
    package.mkdir(parents=True, mode=0o700)
    os.chmod(package, 0o700)
    for provider, lanes in CTRL.LABEL_PROMPT_PATHS.items():
        for lane, relative in lanes.items():
            put_raw(package / relative, f"reviewed {provider} {lane} prompt\n".encode())

    # Create dummy live executables and point controller to them
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    dummy_agy = bin_dir / "agy"
    dummy_agy.write_text("""#!/usr/bin/env python3
import sys
sys.exit(0)
""")
    dummy_agy.chmod(0o755)

    dummy_grok = bin_dir / "grok"
    dummy_grok.write_text("""#!/usr/bin/env python3
import sys
sys.exit(0)
""")
    dummy_grok.chmod(0o755)

    CTRL.AGY = dummy_agy
    CTRL.GROK = dummy_grok
    agy_exe_sha = CTRL.sha256(dummy_agy)
    grok_exe_sha = CTRL.sha256(dummy_grok)

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

    # 3. Evidence manifest (at evidence/manifest.json)
    ev_manifest_val = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": CTRL.CYCLE,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": compiler.CODE_HASHES,
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
        "packet_count": 204,
        "row_count": 10159,
        "network_lookups_performed": 0,
        "sidecars": [],
        "source_package_binding": None,
        "mcp_transport_attestation": {
            "schema_version": "phase3_cycle007_mcp_transport_attestation_v1",
            "transport": "synthetic",
            "endpoint_sha256": CTRL.digest(CTRL.MCP_ENDPOINT.encode("utf-8")),
            "required_tool_set_sha256": CTRL._expected_mcp_tool_set_sha256(),
            "tool_call_count": 1,
            "counts_by_tool": {"mcp_server_identity": 1},
            "server_identity_call_count": 1,
            "ordered_call_commitment_sha256": "3" * 64,
        },
    }
    ev_manifest_val["manifest_sha256"] = contract.sha256_value(ev_manifest_val)
    ev_manifest_bytes = put(package / "evidence" / "manifest.json", ev_manifest_val)
    ev_manifest_sha = CTRL.digest(ev_manifest_bytes)

    sources_identity = {
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "sources_db_bytes": 1024,
        "vesum_db_sha256": "2" * 64,
        "vesum_db_bytes": 2048,
    }

    # 4. Gemini canary receipt
    gemini_canary_val = {
        "schema_version": "phase3_cycle007_gemini_public_canary_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "amendment_sha256": CTRL.AMENDMENT_SHA256,
        "ok": True,
        "execution_mode": "real",
        "exact_model": CTRL.GEMINI_MODEL,
        "model_family": "google",
        "harness": "agy",
        "provider_call_count": 1,
        "fixture_hashes": CTRL._public_fixture_hashes(),
        "sidecar_hashes": {"sidecar_id": "cycle007_sidecar:" + "e" * 64, "sidecar_raw_sha256": "b" * 64},
        "prompt_hashes": {"prompt_sha256": "a" * 64},
        "code_hashes": {
            "compiler_sha256": CTRL.sha256(CTRL.EVIDENCE_COMPILER),
            "validator_sha256": CTRL.sha256(CTRL.REQUIRED_CODE_PATHS["label_validator"]),
            "evidence_validator_sha256": CTRL.sha256(CTRL.EVIDENCE_VALIDATOR),
            "evidence_contract_sha256": CTRL.sha256(CTRL.EVIDENCE_CONTRACT),
            "canary_runner_sha256": CTRL.sha256(CTRL.CANARY_RUNNER),
        },
        "executable_sha256": agy_exe_sha,
        "response_hashes": {
            "raw_stream_sha256": CTRL.digest(b"gemini-canary-raw"),
            "labels_raw_sha256": "5" * 64,
        },
        "sources_endpoint_identity": sources_identity,
        "sources_mcp_used": True,
        "valid_evidence_ids": True,
        "russian_surzhyk_trap_rejected": True,
        "heritage_control_preserved": True,
        "provenance_basis": {
            "init_model": CTRL.GEMINI_MODEL,
            "result_status": "SUCCESS",
            "challenge_sha256": "6" * 64,
            "raw_stream_sha256": CTRL.digest(b"gemini-canary-raw"),
        },
        "text_free": True,
    }
    gemini_canary_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(gemini_canary_val))
    gemini_canary_path = root / "gemini-canary-receipt.json"
    gemini_canary_bytes = put(gemini_canary_path, gemini_canary_val)
    put_raw(gemini_canary_path.with_name(gemini_canary_path.name + ".raw"), b"gemini-canary-raw")
    gemini_canary_sha = CTRL.digest(gemini_canary_bytes)

    # 5. Grok canary receipt
    grok_canary_val = {
        "schema_version": "phase3_cycle007_grok_public_canary_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "amendment_sha256": CTRL.AMENDMENT_SHA256,
        "ok": True,
        "execution_mode": "real",
        "exact_model": CTRL.GROK_MODEL,
        "model_family": "xai",
        "harness": "native_grok",
        "provider_call_count": 1,
        "fixture_hashes": CTRL._public_fixture_hashes(),
        "sidecar_hashes": {"sidecar_id": "cycle007_sidecar:" + "e" * 64, "sidecar_raw_sha256": "b" * 64},
        "prompt_hashes": {"prompt_sha256": "a" * 64},
        "code_hashes": {
            "compiler_sha256": CTRL.sha256(CTRL.EVIDENCE_COMPILER),
            "validator_sha256": CTRL.sha256(CTRL.REQUIRED_CODE_PATHS["label_validator"]),
            "evidence_validator_sha256": CTRL.sha256(CTRL.EVIDENCE_VALIDATOR),
            "evidence_contract_sha256": CTRL.sha256(CTRL.EVIDENCE_CONTRACT),
            "canary_runner_sha256": CTRL.sha256(CTRL.CANARY_RUNNER),
        },
        "executable_sha256": grok_exe_sha,
        "response_hashes": {
            "response_raw_sha256": CTRL.digest(b"grok-canary-raw"),
            "labels_raw_sha256": "8" * 64,
        },
        "sources_endpoint_identity": sources_identity,
        "sources_mcp_used": True,
        "valid_evidence_ids": True,
        "russian_surzhyk_trap_rejected": True,
        "heritage_control_preserved": True,
        "provenance_basis": {
            "challenge_sha256": "6" * 64,
            "response_raw_sha256": CTRL.digest(b"grok-canary-raw"),
        },
        "text_free": True,
    }
    grok_canary_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(grok_canary_val))
    grok_canary_path = root / "grok-canary-receipt.json"
    grok_canary_bytes = put(grok_canary_path, grok_canary_val)
    put_raw(grok_canary_path.with_name(grok_canary_path.name + ".raw"), b"grok-canary-raw")
    grok_canary_sha = CTRL.digest(grok_canary_bytes)

    # 6. Code paths
    code_paths: dict[str, Path] = {}
    for label, path in CTRL.REQUIRED_CODE_PATHS.items():
        code_paths[label] = path

    # Create dummy runners for the downstream stages
    for label in ("compare_runner", "audit_runner", "adjudicate_runner", "resolve_runner", "certify_runner"):
        dummy = (root / f"dummy_{label}.py").resolve()
        dummy.write_text("""#!/usr/bin/env python3
import sys
sys.exit(0)
""")
        dummy.chmod(0o755)
        code_paths[label] = dummy
        CTRL.REQUIRED_CODE_PATHS[label] = dummy

    code_hashes = {label: CTRL.sha256(path) for label, path in code_paths.items()}

    # 7. Preflight receipt
    preflight_val = {
        "schema_version": "phase3_cycle007_preflight_receipt_v1",
        "amendment_sha256": CTRL.AMENDMENT_SHA256,
        "package_custody_receipt_sha256": custody_sha,
        "package_manifest_sha256": manifest_sha,
        "package_evidence_manifest_sha256": ev_manifest_sha,
        "gemini_canary_receipt_sha256": gemini_canary_sha,
        "grok_canary_receipt_sha256": grok_canary_sha,
        "code_hashes": code_hashes,
        "label_prompt_sha256s": CTRL._label_prompt_sha256s(package),
        "backup_receipt_sha256": "7" * 64,
        "review_hashes": {"source_authority_review": "8" * 64, "scope_circularity_review": "9" * 64},
        "ci_proof_bindings": {"ci_proof": "a" * 64},
        "sources_endpoint_identity": sources_identity,
        "text_free": True,
    }
    preflight_val["receipt_sha256"] = CTRL.digest(CTRL.canonical(preflight_val))
    preflight_path = root / "preflight-receipt.json"
    put(preflight_path, preflight_val)

    return package, preflight_path, gemini_canary_path, grok_canary_path, code_paths


def test_preflight_valid(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    assert proof["ok"] is True
    assert proof["text_free"] is True
    assert proof["expected_custody_sha256"]
    assert proof["expected_label_manifest_sha256"]
    assert proof["expected_evidence_manifest_sha256"]
    assert proof["sources_endpoint_identity"]


def test_preflight_persists_canonical_receipts_under_control(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)

    control_dir = pkg / "control"
    assert (control_dir / "preflight-receipt.json").exists()
    assert (control_dir / "gemini-canary-receipt.json").exists()
    assert (control_dir / "grok-canary-receipt.json").exists()

    assert CTRL._read_json(control_dir / "preflight-receipt.json") == CTRL._read_json(preflight_path)
    assert CTRL._read_json(control_dir / "gemini-canary-receipt.json") == CTRL._read_json(gemini_canary)
    assert CTRL._read_json(control_dir / "grok-canary-receipt.json") == CTRL._read_json(grok_canary)


def test_preflight_rejects_symlinked_control_directory(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (pkg / "control").symlink_to(outside, target_is_directory=True)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_noncanonical_canary_bytes(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    value = CTRL._read_json(gemini_canary)
    gemini_canary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    gemini_canary.chmod(0o600)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_forged_canary_code_hash(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    value = CTRL._read_json(gemini_canary)
    value["code_hashes"]["canary_runner_sha256"] = "0" * 64
    value["receipt_sha256"] = CTRL.digest(
        CTRL.canonical({key: item for key, item in value.items() if key != "receipt_sha256"})
    )
    put(gemini_canary, value)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_unfrozen_extra_code_path(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    extra = tmp_path / "extra.py"
    extra.write_text("pass\n")
    code_paths["extra_runner"] = extra

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_synthetic_canary_receipt(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    val = CTRL._read_json(gemini_canary)
    val["execution_mode"] = "synthetic"
    val["receipt_sha256"] = CTRL.digest(CTRL.canonical({k: v for k, v in val.items() if k != "receipt_sha256"}))
    put(gemini_canary, val)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_fails_on_alias_fields_in_canary_receipt(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    val = CTRL._read_json(gemini_canary)
    # Substitute canonical field with old alias field
    del val["sources_mcp_used"]
    val["sources_mcp_roundtrip"] = True
    val["receipt_sha256"] = CTRL.digest(CTRL.canonical({k: v for k, v in val.items() if k != "receipt_sha256"}))
    put(gemini_canary, val)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_fails_on_omitted_field_in_canary_receipt(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    val = CTRL._read_json(grok_canary)
    del val["russian_surzhyk_trap_rejected"]
    val["receipt_sha256"] = CTRL.digest(CTRL.canonical({k: v for k, v in val.items() if k != "receipt_sha256"}))
    put(grok_canary, val)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_fails_on_source_identity_divergence(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    val = CTRL._read_json(grok_canary)
    val["sources_endpoint_identity"]["sources_db_sha256"] = "9" * 64
    val["receipt_sha256"] = CTRL.digest(CTRL.canonical({k: v for k, v in val.items() if k != "receipt_sha256"}))
    put(grok_canary, val)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_fails_on_executable_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    val = CTRL._read_json(gemini_canary)
    val["executable_sha256"] = "0" * 64
    val["receipt_sha256"] = CTRL.digest(CTRL.canonical({k: v for k, v in val.items() if k != "receipt_sha256"}))
    put(gemini_canary, val)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_canary_raw_artifact_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    gemini_canary.with_name(gemini_canary.name + ".raw").write_bytes(b"forged raw response")
    gemini_canary.with_name(gemini_canary.name + ".raw").chmod(0o600)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_nonhex_source_endpoint_hash(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    value = CTRL._read_json(gemini_canary)
    value["sources_endpoint_identity"]["server_code_sha256"] = "z" * 64
    value["receipt_sha256"] = CTRL.digest(
        CTRL.canonical({key: item for key, item in value.items() if key != "receipt_sha256"})
    )
    put(gemini_canary, value)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_requires_transport_attestation(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    evidence_path = pkg / "evidence" / "manifest.json"
    evidence = CTRL._read_json(evidence_path)
    del evidence["mcp_transport_attestation"]
    evidence["manifest_sha256"] = contract.sha256_value(
        {key: item for key, item in evidence.items() if key != "manifest_sha256"}
    )
    put(evidence_path, evidence)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_preflight_rejects_forged_evidence_contract_code_hash(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    value = CTRL._read_json(gemini_canary)
    value["code_hashes"]["evidence_contract_sha256"] = "0" * 64
    value["receipt_sha256"] = CTRL.digest(
        CTRL.canonical({key: item for key, item in value.items() if key != "receipt_sha256"})
    )
    put(gemini_canary, value)

    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_audit_stage_cli_receives_expected_agy_executable_sha(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    cmds, _ = CTRL._commands_for_stage(
        pkg,
        "audit",
        code_paths["audit_runner"],
        code_paths=code_paths,
        expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
        expected_grok_executable_sha256=proof["expected_grok_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=proof["expected_custody_sha256"],
        expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
        expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
    )
    assert len(cmds) == 1
    assert "--expected-agy-executable-sha" in cmds[0]
    idx = cmds[0].index("--expected-agy-executable-sha")
    assert cmds[0][idx + 1] == proof["expected_agy_executable_sha256"]


def test_gemini_cli_receives_expected_prompt_sha(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    original = CTRL.gemini_missing_ranges
    CTRL.gemini_missing_ranges = lambda *_args: {"clean_label": [(1, 1)], "residual_label": []}
    try:
        cmds, _ = CTRL._commands_for_stage(
            pkg,
            "gemini",
            None,
            code_paths=code_paths,
            expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
            expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
            expected_custody_sha256=proof["expected_custody_sha256"],
            expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
            expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
        )
        prompt_idx = cmds[0].index("--expected-label-prompt-sha")
        assert cmds[0][prompt_idx + 1] == proof["expected_label_prompt_sha256s"]["gemini"]["clean_label"]
    finally:
        CTRL.gemini_missing_ranges = original


def test_preflight_rejects_label_prompt_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    prompt = pkg / CTRL.LABEL_PROMPT_PATHS["gemini"]["clean_label"]
    put_raw(prompt, b"unreviewed replacement prompt\n")
    with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
        CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)


def test_grok_cli_receives_lane_specific_reviewed_prompt_sha(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    original = CTRL.grok_missing_ranges
    CTRL.grok_missing_ranges = lambda *_args: {"clean_label": [], "residual_label": [(1, 1)]}
    try:
        commands, _ = CTRL._commands_for_stage(
            pkg,
            "grok",
            code_paths["grok_runner"],
            code_paths=code_paths,
            expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
            expected_grok_executable_sha256=proof["expected_grok_executable_sha256"],
            expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
            expected_custody_sha256=proof["expected_custody_sha256"],
            expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
            expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
        )
        prompt_idx = commands[0].index("--expected-label-prompt-sha")
        assert commands[0][prompt_idx + 1] == proof["expected_label_prompt_sha256s"]["grok"]["residual_label"]
    finally:
        CTRL.grok_missing_ranges = original


def test_resolve_command_wires_external_authority_paths(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    authority_root = tmp_path / "authority"
    nonce_ledger = tmp_path / "nonces"
    authority_root.mkdir(mode=0o700)
    nonce_ledger.mkdir(mode=0o700)
    authorization = authority_root / "authorization.json"
    attestation = authority_root / "attestation.json"
    commands, _ = CTRL._commands_for_stage(
        pkg,
        "resolve",
        code_paths["resolve_runner"],
        code_paths=code_paths,
        expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
        expected_grok_executable_sha256=proof["expected_grok_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=proof["expected_custody_sha256"],
        expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
        expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
        resolution_authorization=authorization,
        resolution_authority_attestation=attestation,
        resolution_authority_root=authority_root,
        resolution_nonce_ledger=nonce_ledger,
    )
    assert commands == [
        [
            str(CTRL.PRIMARY_PYTHON),
            str(code_paths["resolve_runner"]),
            "--package",
            str(pkg),
            "--all",
            "--authorization",
            str(authorization),
            "--authority-attestation",
            str(attestation),
            "--authority-root",
            str(authority_root),
            "--nonce-ledger",
            str(nonce_ledger),
        ]
    ]


def test_status_action(tmp_path: Path) -> None:
    pkg, _preflight_path, _gemini_canary, _grok_canary, _code_paths = make_controller_fixtures(tmp_path)
    st = CTRL.status(pkg)
    assert st["completed_stages"] == []
    assert st["stopped"] is False
    assert st["ready"] is False
    assert st["text_free"] is True


def test_status_rejects_forged_stage_seal_content(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    CTRL._seal(pkg, "gemini", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    seal = pkg / "control" / "stage-gemini.complete.json"
    value = CTRL._read_json(seal)
    value["stage"] = "grok"
    put(seal, value)

    with pytest.raises(CTRL.ControllerError, match="invalid_stage_seal"):
        CTRL.status(pkg)


def test_status_rejects_broken_stage_chain(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    CTRL._seal(pkg, "gemini", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    CTRL._seal(pkg, "grok", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    seal = pkg / "control" / "stage-gemini.complete.json"
    value = CTRL._read_json(seal)
    unsigned = {key: item for key, item in value.items() if key != "seal_sha256"}
    unsigned["python_executable_sha256"] = "a" * 64
    unsigned["seal_sha256"] = CTRL.digest(
        CTRL.canonical({key: item for key, item in unsigned.items() if key != "seal_sha256"})
    )
    put(seal, unsigned)

    with pytest.raises(CTRL.ControllerError, match="invalid_stage_seal"):
        CTRL.status(pkg)


def test_status_rejects_preflight_receipt_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    CTRL._seal(pkg, "gemini", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    control_preflight = pkg / "control" / "preflight-receipt.json"
    value = CTRL._read_json(control_preflight)
    value["backup_receipt_sha256"] = "f" * 64
    put(control_preflight, value)

    with pytest.raises(CTRL.ControllerError, match="invalid_stage_seal"):
        CTRL.status(pkg)


def test_status_rejects_interpreter_hash_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    CTRL._seal(pkg, "gemini", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    drifted = tmp_path / "drifted-status-python"
    drifted.write_bytes(b"different interpreter")
    drifted.chmod(0o755)
    original = CTRL.PRIMARY_PYTHON
    CTRL.PRIMARY_PYTHON = drifted
    try:
        with pytest.raises(CTRL.ControllerError, match="invalid_stage_seal"):
            CTRL.status(pkg)
    finally:
        CTRL.PRIMARY_PYTHON = original


def test_stage_rejects_python_interpreter_hash_drift(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    CTRL._seal(pkg, "gemini", proof["preflight_receipt_sha256"], proof["expected_python_executable_sha256"])
    drifted = tmp_path / "drifted-python"
    drifted.write_bytes(b"different interpreter")
    drifted.chmod(0o755)
    original = CTRL.PRIMARY_PYTHON
    CTRL.PRIMARY_PYTHON = drifted
    try:
        with pytest.raises(CTRL.ControllerError, match="preflight_binding_drift"):
            CTRL.run_stage(
                pkg,
                "grok",
                code_paths["grok_runner"],
                proof["preflight_receipt_sha256"],
                dry_run=True,
                concurrency=1,
                expected_python_executable_sha256=proof["expected_python_executable_sha256"],
                code_paths=code_paths,
            )
    finally:
        CTRL.PRIMARY_PYTHON = original


def test_stage_sequence_enforced(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    with pytest.raises(CTRL.ControllerError, match="noncontiguous_stage_order"):
        CTRL.run_stage(
            pkg,
            "grok",
            code_paths["grok_runner"],
            proof["preflight_receipt_sha256"],
            dry_run=False,
            concurrency=1,
            expected_python_executable_sha256=proof["expected_python_executable_sha256"],
            expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
            code_paths=code_paths,
        )


def test_stop_present_blocks_stages(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
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
            expected_python_executable_sha256=proof["expected_python_executable_sha256"],
            expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
            expected_custody_sha256=proof["expected_custody_sha256"],
            expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
            expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
            code_paths=code_paths,
        )


def test_downstream_stages_revalidation_and_sealing(tmp_path: Path) -> None:
    pkg, preflight_path, gemini_canary, grok_canary, code_paths = make_controller_fixtures(tmp_path)
    proof = CTRL.preflight(pkg, preflight_path, code_paths, gemini_canary, grok_canary)
    cust_sha = proof["expected_custody_sha256"]
    man_sha = proof["expected_label_manifest_sha256"]
    ev_sha = proof["expected_evidence_manifest_sha256"]
    agy_sha = proof["expected_agy_executable_sha256"]

    CTRL._seal(
        pkg,
        "gemini",
        proof["preflight_receipt_sha256"],
        proof["expected_python_executable_sha256"],
    )
    CTRL._seal(
        pkg,
        "grok",
        proof["preflight_receipt_sha256"],
        proof["expected_python_executable_sha256"],
    )

    # 1. Setup compare stage receipt
    compare_receipt = {
        "schema_version": "phase3_cycle007_dual_label_batch_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "custody_receipt_raw_sha256": cust_sha,
        "manifest_raw_sha256": man_sha,
        "text_free": True,
    }
    compare_receipt["receipt_sha256"] = CTRL.digest(CTRL.canonical(compare_receipt))
    put(pkg / "dual-label-output-cycle007-v1" / "batch-receipt.json", compare_receipt)
    for lane, count in CTRL.LANES.items():
        for i in range(1, count + 1):
            put(
                pkg / "dual-label-output-cycle007-v1" / lane / f"receipt-{i:04d}.json",
                {"schema_version": "phase3_cycle007_dual_label_packet_receipt_v1", "text_free": True},
            )

    res_compare = CTRL.run_stage(
        pkg,
        "compare",
        code_paths["compare_runner"],
        proof["preflight_receipt_sha256"],
        dry_run=False,
        concurrency=1,
        expected_python_executable_sha256=proof["expected_python_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=cust_sha,
        expected_label_manifest_sha256=man_sha,
        expected_evidence_manifest_sha256=ev_sha,
        code_paths=code_paths,
    )
    assert res_compare["ok"] is True

    # 2. Setup audit stage receipt
    audit_receipt = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "passed": True,
        "terminal_findings_count": 0,
        "custody_receipt_raw_sha256": cust_sha,
        "manifest_raw_sha256": man_sha,
        "text_free": True,
    }
    audit_receipt["receipt_sha256"] = CTRL.digest(CTRL.canonical(audit_receipt))
    put(pkg / "consensus-audit-cycle007-v1" / "batch-receipt.json", audit_receipt)
    put(
        pkg / "consensus-audit-cycle007-v1" / "clean-audit-receipt.json",
        {"terminal_findings_count": 0, "text_free": True},
    )
    put(
        pkg / "consensus-audit-cycle007-v1" / "risk-review-receipt.json",
        {"terminal_findings_count": 0, "text_free": True},
    )

    res_audit = CTRL.run_stage(
        pkg,
        "audit",
        code_paths["audit_runner"],
        proof["preflight_receipt_sha256"],
        dry_run=False,
        concurrency=1,
        expected_agy_executable_sha256=agy_sha,
        expected_python_executable_sha256=proof["expected_python_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=cust_sha,
        expected_label_manifest_sha256=man_sha,
        expected_evidence_manifest_sha256=ev_sha,
        code_paths=code_paths,
    )
    assert res_audit["ok"] is True

    # 3. Setup adjudicate stage receipt
    adj_receipt = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_batch_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "custody_receipt_raw_sha256": cust_sha,
        "manifest_raw_sha256": man_sha,
        "text_free": True,
    }
    adj_receipt["receipt_sha256"] = CTRL.digest(CTRL.canonical(adj_receipt))
    put(pkg / "dual-label-adjudication-cycle007-v1" / "batch-receipt.json", adj_receipt)
    for lane, count in CTRL.LANES.items():
        for i in range(1, count + 1):
            put(
                pkg / "dual-label-adjudication-cycle007-v1" / "final" / lane / f"receipt-{i:04d}.json",
                {"schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1", "text_free": True},
            )

    res_adj = CTRL.run_stage(
        pkg,
        "adjudicate",
        code_paths["adjudicate_runner"],
        proof["preflight_receipt_sha256"],
        dry_run=False,
        concurrency=1,
        expected_agy_executable_sha256=agy_sha,
        expected_python_executable_sha256=proof["expected_python_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=cust_sha,
        expected_label_manifest_sha256=man_sha,
        expected_evidence_manifest_sha256=ev_sha,
        code_paths=code_paths,
    )
    assert res_adj["ok"] is True

    # 4. Setup resolve stage receipt
    res_receipt = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "unresolved_remaining_count": 0,
        "custody_receipt_raw_sha256": cust_sha,
        "manifest_raw_sha256": man_sha,
        "text_free": True,
    }
    res_receipt["receipt_sha256"] = CTRL.digest(CTRL.canonical(res_receipt))
    put(pkg / "dual-label-final-cycle007-v1" / "batch-receipt.json", res_receipt)
    for lane, count in CTRL.LANES.items():
        for i in range(1, count + 1):
            put(
                pkg / "dual-label-final-cycle007-v1" / "final" / lane / f"receipt-{i:04d}.json",
                {
                    "schema_version": "phase3_cycle007_operator_resolution_packet_receipt_v1",
                    "unresolved_remaining_count": 0,
                    "text_free": True,
                },
            )

    res_res = CTRL.run_stage(
        pkg,
        "resolve",
        code_paths["resolve_runner"],
        proof["preflight_receipt_sha256"],
        dry_run=False,
        concurrency=1,
        expected_python_executable_sha256=proof["expected_python_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=cust_sha,
        expected_label_manifest_sha256=man_sha,
        expected_evidence_manifest_sha256=ev_sha,
        code_paths=code_paths,
    )
    assert res_res["ok"] is True

    # 5. Setup certify stage receipt
    cert_receipt = {
        "schema_version": "phase3_cycle007_label_completion_receipt_v1",
        "evaluation_cycle_id": CTRL.CYCLE,
        "amendment_sha256": CTRL.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": cust_sha,
        "manifest_raw_sha256": man_sha,
        "evidence_manifest_raw_sha256": ev_sha,
        "source_custody_receipt_raw_sha256": CTRL.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": CTRL.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": CTRL.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "unresolved_remaining_count": 0,
        "terminal_findings_count": 0,
        "text_free": True,
    }
    cert_receipt["receipt_sha256"] = CTRL.digest(CTRL.canonical(cert_receipt))
    put(pkg / "dual-label-final-cycle007-v1" / "certification-receipt.json", cert_receipt)

    res_cert = CTRL.run_stage(
        pkg,
        "certify",
        code_paths["certify_runner"],
        proof["preflight_receipt_sha256"],
        dry_run=False,
        concurrency=1,
        expected_python_executable_sha256=proof["expected_python_executable_sha256"],
        expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
        expected_custody_sha256=cust_sha,
        expected_label_manifest_sha256=man_sha,
        expected_evidence_manifest_sha256=ev_sha,
        code_paths=code_paths,
    )
    assert res_cert["ok"] is True

    st = CTRL.status(pkg)
    assert st["ready"] is True
    assert st["completed_stages"] == list(CTRL.STAGES)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="controller_test_"))
    try:
        test_preflight_valid(tmp / "t1")
        test_preflight_persists_canonical_receipts_under_control(tmp / "t2")
        test_preflight_rejects_synthetic_canary_receipt(tmp / "t3")
        test_preflight_fails_on_alias_fields_in_canary_receipt(tmp / "t4")
        test_preflight_fails_on_omitted_field_in_canary_receipt(tmp / "t5")
        test_preflight_fails_on_source_identity_divergence(tmp / "t6")
        test_preflight_fails_on_executable_drift(tmp / "t7")
        test_preflight_rejects_canary_raw_artifact_drift(tmp / "t8")
        test_preflight_rejects_nonhex_source_endpoint_hash(tmp / "t9")
        test_preflight_requires_transport_attestation(tmp / "t10")
        test_preflight_rejects_forged_evidence_contract_code_hash(tmp / "t11")
        test_audit_stage_cli_receives_expected_agy_executable_sha(tmp / "t12")
        test_gemini_cli_receives_expected_prompt_sha(tmp / "t13")
        test_status_action(tmp / "t14")
        test_status_rejects_forged_stage_seal_content(tmp / "t15")
        test_status_rejects_broken_stage_chain(tmp / "t16")
        test_status_rejects_preflight_receipt_drift(tmp / "t17")
        test_status_rejects_interpreter_hash_drift(tmp / "t18")
        test_stage_rejects_python_interpreter_hash_drift(tmp / "t19")
        test_stage_sequence_enforced(tmp / "t20")
        test_stop_present_blocks_stages(tmp / "t21")
        test_downstream_stages_revalidation_and_sealing(tmp / "t22")
        print(
            json.dumps(
                {"ok": True, "controller_tests_passed": 22, "text_free": True},
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
