"""Synthetic tests for inert Cycle 007 compile-throughput scaffolding.

No private packet text, no network, no Foundry activation. Production
compiler and runner stay unwired.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compile_throughput as throughput
from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

_COMPILER_TEST_PATH = Path(__file__).with_name("test_phase3_cycle007_evidence_compiler.py")
_SPEC = importlib.util.spec_from_file_location("cycle007_compiler_test_helpers", _COMPILER_TEST_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_COMPILER_TESTS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_COMPILER_TESTS)
SyntheticSourcesClient = _COMPILER_TESTS.SyntheticSourcesClient
_row = _COMPILER_TESTS._row


def _expected_identity(client: SyntheticSourcesClient) -> dict[str, object]:
    identity = client.server_identity()
    return {
        "tokenizer_id": compiler.TOKENIZER_ID,
        "tokenizer_version": compiler.TOKENIZER_VERSION,
        "code_hashes": compiler.CODE_HASHES,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
    }


def _seal_packet(staging: Path, packet_index: int, client: SyntheticSourcesClient) -> dict[str, object]:
    sidecar = compiler.compile_packet_sidecar(packet_index, [_row(f"unit-{packet_index}")], client)
    path = staging / throughput.sidecar_filename(packet_index)
    digest = throughput.write_private_json(path, sidecar)
    return {"sidecar": sidecar, "sha256": digest, "path": path}


def test_production_compiler_and_runner_stay_unwired_and_serial() -> None:
    assert throughput.production_wiring_is_inactive() is True
    assert throughput.packet_loop_is_serial() is True
    assert throughput.bound_packet_workers(1) == 1
    with pytest.raises(throughput.ThroughputScaffoldingError, match="packet_workers_not_authorized"):
        throughput.bound_packet_workers(2)
    with pytest.raises(throughput.ThroughputScaffoldingError, match="packet_workers_out_of_range"):
        throughput.bound_packet_workers(0)
    with pytest.raises(throughput.ThroughputScaffoldingError, match="packet_workers_out_of_range"):
        throughput.bound_packet_workers(throughput.MAX_REVIEWED_PACKET_WORKERS + 1)
    assert throughput.bound_packet_workers(2, authorized=True) == 2


def test_empty_or_missing_staging_resumes_at_packet_one(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    missing = tmp_path / "absent"
    assert throughput.resume_next_packet_index(missing, expected) == 1

    staging = tmp_path / "staging"
    staging.mkdir(mode=0o700)
    assert throughput.resume_next_packet_index(staging, expected) == 1


def test_sealed_prefix_resumes_after_last_validated_packet(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    staging = tmp_path / "staging"
    first = _seal_packet(staging, 1, client)
    second = _seal_packet(staging, 2, client)
    throughput.assert_private_modes(staging)

    progress = throughput.build_progress_receipt(
        sealed_packet_count=2,
        target_packet_count=4,
        target_row_count=4,
        last_sealed_sidecar_sha256=str(second["sha256"]),
        last_sealed_sidecar_id=str(second["sidecar"]["sidecar_id"]),
        expected_identity=expected,
        ordered_call_commitment_sha256=throughput.initial_call_commitment(),
        tool_call_count=0,
        counts_by_tool={},
    )
    dumped = contract.canonical_json(progress)
    assert "unit-1" not in dumped
    assert "Привіт" not in dumped
    assert progress["text_free"] is True
    assert progress["activation_state"] == "scaffolding_only"
    assert set(progress) == throughput.PROGRESS_REQUIRED_KEYS

    assert throughput.resume_next_packet_index(staging, expected, progress=progress, target_packet_count=4) == 3
    assert first["sidecar"]["packet_index"] == 1


def test_gap_identity_drift_and_foreign_files_fail_closed(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    staging = tmp_path / "staging"
    _seal_packet(staging, 1, client)
    _seal_packet(staging, 3, client)
    with pytest.raises(throughput.ThroughputScaffoldingError, match="sealed_prefix_gap"):
        throughput.resume_next_packet_index(staging, expected)

    clean = tmp_path / "clean"
    _seal_packet(clean, 1, client)
    drifted = dict(expected)
    drifted["sources_db_sha256"] = "d" * 64
    with pytest.raises(throughput.ThroughputScaffoldingError, match="identity_drift"):
        throughput.resume_next_packet_index(clean, drifted)

    (clean / "notes.txt").write_text("x", encoding="utf-8")
    with pytest.raises(throughput.ThroughputScaffoldingError, match="staging_foreign_file"):
        throughput.resume_next_packet_index(clean, expected)


def test_incomplete_temp_sidecar_is_discarded_and_not_counted(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    staging = tmp_path / "staging"
    _seal_packet(staging, 1, client)
    leftover = staging / ".sidecar-0002.json.partial"
    leftover.write_text("{", encoding="utf-8")

    assert throughput.resume_next_packet_index(staging, expected) == 2
    assert leftover.exists() is False
    assert (staging / "sidecar-0001.json").is_file()


def test_progress_receipt_rejects_private_keys_and_hash_drift() -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    receipt = throughput.build_progress_receipt(
        sealed_packet_count=0,
        last_sealed_sidecar_sha256=None,
        last_sealed_sidecar_id=None,
        expected_identity=expected,
        ordered_call_commitment_sha256=throughput.initial_call_commitment(),
        tool_call_count=0,
        counts_by_tool={},
    )
    with pytest.raises(throughput.ThroughputScaffoldingError, match="progress_not_text_free"):
        throughput._reject_private_progress_keys({**receipt, "unit_id": "unit-1"})

    tampered = dict(receipt)
    tampered["sealed_packet_count"] = 1
    with pytest.raises(throughput.ThroughputScaffoldingError, match="progress_hash_drift"):
        throughput.validate_progress_receipt(tampered, expected)


def test_progress_mismatch_against_sealed_bytes_fails_closed(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    expected = _expected_identity(client)
    staging = tmp_path / "staging"
    sealed = _seal_packet(staging, 1, client)
    progress = throughput.build_progress_receipt(
        sealed_packet_count=1,
        target_packet_count=4,
        target_row_count=4,
        last_sealed_sidecar_sha256="a" * 64,
        last_sealed_sidecar_id=str(sealed["sidecar"]["sidecar_id"]),
        expected_identity=expected,
        ordered_call_commitment_sha256=throughput.initial_call_commitment(),
        tool_call_count=0,
        counts_by_tool={},
    )
    with pytest.raises(throughput.ThroughputScaffoldingError, match="progress_last_sidecar_mismatch"):
        throughput.resume_next_packet_index(staging, expected, progress=progress, target_packet_count=4)


def test_serial_call_chain_matches_local_sources_client_recipe() -> None:
    first = {
        "tool": "verify_words",
        "arguments_sha256": contract.sha256_value({"words": ["a"]}),
        "response_sha256": contract.sha256_text("found:1"),
    }
    second = {
        "tool": "check_modern_form",
        "arguments_sha256": contract.sha256_value({"word": "a"}),
        "response_sha256": contract.sha256_text("{}"),
    }
    direct, next_ordinal = throughput.extend_serial_call_commitment(
        throughput.initial_call_commitment(),
        [first, second],
        starting_ordinal=1,
    )
    stepwise, mid = throughput.extend_serial_call_commitment(
        throughput.initial_call_commitment(),
        [first],
        starting_ordinal=1,
    )
    resumed, final_ordinal = throughput.extend_serial_call_commitment(stepwise, [second], starting_ordinal=mid)
    assert direct == resumed
    assert next_ordinal == final_ordinal == 3
    assert len(direct) == 64


def test_compile_sidecar_bundle_still_refuses_existing_output(tmp_path: Path) -> None:
    client = SyntheticSourcesClient()
    output_dir = tmp_path / "sidecars"
    compiler.compile_sidecar_bundle([[_row("unit-1")]], client, output_dir)
    with pytest.raises(contract.EvidenceContractError):
        compiler.compile_sidecar_bundle([[_row("unit-1")]], client, output_dir)
