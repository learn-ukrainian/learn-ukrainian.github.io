"""Synthetic proof for Cycle 007 durable sealed-packet resume custody."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compile_throughput as throughput
from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

_COMPILER_TEST_PATH = Path(__file__).with_name("test_phase3_cycle007_evidence_compiler.py")
_SPEC = importlib.util.spec_from_file_location("cycle007_compiler_test_helpers", _COMPILER_TEST_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)

_RUNNER_PATH = Path(__file__).parents[1] / "batch_state" / "phase3-compile-cycle007-evidence-v1.py"
_RUNNER_SPEC = importlib.util.spec_from_file_location("cycle007_compile_runner", _RUNNER_PATH)
assert _RUNNER_SPEC is not None and _RUNNER_SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_RUNNER_SPEC)
_RUNNER_SPEC.loader.exec_module(_RUNNER)


def _client(tmp_path: Path) -> compiler.LocalMcpSourcesClient:
    tmp_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    files = _HELPERS._stub_client_files(tmp_path)
    transport = _HELPERS._passing_transport(identity_files=files)
    return compiler.LocalMcpSourcesClient(transport=transport, **files)


def _row(unit_id: str) -> dict[str, object]:
    return _HELPERS._row(unit_id, "слово")


def _inputs() -> tuple[list[list[dict[str, object]]], list[bool], list[dict[str, object]]]:
    packets = [[_row("unit-1")], [_row("unit-2")]]
    flags = [False, False]
    bindings = [compiler._default_packet_binding(index, rows) for index, rows in enumerate(packets, start=1)]
    return packets, flags, bindings


def _run(
    tmp_path: Path,
    output: Path,
    *,
    interrupt_after_packet: int | None = None,
    interrupt_after_install: bool = False,
) -> dict[str, object]:
    packets, flags, bindings = _inputs()
    client = _client(tmp_path)
    try:
        return compiler.compile_sidecar_bundle_resumable(
            packets,
            client,
            output,
            residual_lane_packets=flags,
            packet_bindings=bindings,
            source_package_binding=None,
            _interrupt_after_packet=interrupt_after_packet,
            _interrupt_after_install=interrupt_after_install,
        )
    finally:
        client.close()


def _private_parent(tmp_path: Path, name: str) -> Path:
    parent = tmp_path / name
    parent.mkdir(mode=0o700)
    return parent


def _append_legacy_identity_calls(
    output: Path,
    *,
    count: int,
    response_sha256: str | None = None,
) -> None:
    root = throughput.resume_root_for(output)
    receipt = throughput.read_progress(root / throughput.PROGRESS_NAME)
    records = list(receipt["mcp_call_records"])
    identity = next(record for record in records if record["tool"] == "mcp_server_identity")
    for _ in range(count):
        records.append(
            {
                "ordinal": len(records) + 1,
                "tool": identity["tool"],
                "arguments_sha256": identity["arguments_sha256"],
                "response_sha256": response_sha256 or identity["response_sha256"],
            }
        )
    commitment, next_ordinal = throughput.extend_serial_call_commitment(
        throughput.initial_call_commitment(),
        records,
        starting_ordinal=1,
    )
    assert next_ordinal == len(records) + 1
    attestation = dict(receipt["mcp_transport_attestation"])
    attestation["tool_call_count"] = len(records)
    counts_by_tool = dict(attestation["counts_by_tool"])
    counts_by_tool["mcp_server_identity"] += count
    attestation["counts_by_tool"] = dict(sorted(counts_by_tool.items()))
    attestation["server_identity_call_count"] += count
    attestation["ordered_call_commitment_sha256"] = commitment
    receipt["mcp_call_records"] = records
    receipt["mcp_transport_attestation"] = attestation
    receipt["progress_sha256"] = contract.sha256_value(
        {key: value for key, value in receipt.items() if key != "progress_sha256"}
    )
    throughput.write_progress(root, receipt)


def test_runner_temporarily_admits_only_reviewed_resume_root(tmp_path: Path) -> None:
    package = _private_parent(tmp_path, "package")
    output = package / "evidence"
    root = throughput.resume_root_for(output)
    root.mkdir(mode=0o700)
    original = _RUNNER.materializer.OUTPUT_TOP_LEVEL

    with _RUNNER._admit_reviewed_resume_root(package, output):
        assert original | {root.name} == _RUNNER.materializer.OUTPUT_TOP_LEVEL
    assert original == _RUNNER.materializer.OUTPUT_TOP_LEVEL


def test_runner_admission_preserves_strict_compiler_and_allows_actual_compile(tmp_path: Path) -> None:
    source = _HELPERS._write_cycle005_fixture(tmp_path)
    package = tmp_path / "cycle007-package"
    _RUNNER.materializer.materialize(source, package, fixture=True)
    output = package / "evidence"
    throughput.resume_root_for(output).mkdir(mode=0o700)
    client = _HELPERS.SyntheticSourcesClient()

    with pytest.raises(compiler.contract.EvidenceContractError, match="manifest_binding_drift"):
        compiler._validate_cycle007_materialization(
            package,
            source / "label-manifest.json",
            fixture=True,
        )

    with _RUNNER._admit_reviewed_resume_root(package, output):
        manifest = compiler.compile_cycle007_package(
            package,
            source / "label-manifest.json",
            client,
            output,
            fixture=True,
        )
    assert manifest["packet_count"] == 2
    assert manifest["row_count"] == 4


def test_runner_normalizes_legacy_identity_calls_without_changing_frozen_modules(tmp_path: Path) -> None:
    straight_parent = _private_parent(tmp_path, "straight-normalized")
    resumed_parent = _private_parent(tmp_path, "resumed-normalized")
    straight = straight_parent / "evidence"
    resumed = resumed_parent / "evidence"
    _run(tmp_path / "client-straight-normalized", straight)
    with pytest.raises(RuntimeError):
        _run(tmp_path / "client-first-normalized", resumed, interrupt_after_packet=1)
    _append_legacy_identity_calls(resumed, count=2)

    client = _client(tmp_path / "client-second-normalized")
    try:
        _RUNNER._normalize_resume_identity_ledger(resumed, client)
        progress = throughput.read_progress(
            throughput.resume_root_for(resumed) / throughput.PROGRESS_NAME
        )
        assert progress["mcp_transport_attestation"]["server_identity_call_count"] == 0
        assert all(record["tool"] != "mcp_server_identity" for record in progress["mcp_call_records"])
        packets, flags, bindings = _inputs()
        compiler.compile_sidecar_bundle_resumable(
            packets,
            client,
            resumed,
            residual_lane_packets=flags,
            packet_bindings=bindings,
            source_package_binding=None,
        )
    finally:
        client.close()

    for packet_index in (1, 2):
        name = throughput.sidecar_filename(packet_index)
        assert (straight / name).read_bytes() == (resumed / name).read_bytes()
    resumed_manifest = json.loads((resumed / "manifest.json").read_text())
    assert resumed_manifest["packet_count"] == 2
    assert resumed_manifest["row_count"] == 2
    assert resumed_manifest["mcp_transport_attestation"]["server_identity_call_count"] == 1


def test_runner_leaves_missing_progress_window_for_frozen_compiler_to_self_heal(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "missing-progress")
    output = parent / "evidence"
    throughput.resume_root_for(output).mkdir(mode=0o700)
    client = _client(tmp_path / "client-missing-progress")
    try:
        _RUNNER._normalize_resume_identity_ledger(output, client)
        packets, flags, bindings = _inputs()
        manifest = compiler.compile_sidecar_bundle_resumable(
            packets,
            client,
            output,
            residual_lane_packets=flags,
            packet_bindings=bindings,
            source_package_binding=None,
        )
    finally:
        client.close()

    assert manifest["packet_count"] == 2
    assert manifest["row_count"] == 2
    assert output.is_dir()
    assert not throughput.resume_root_for(output).exists()


def test_runner_normalization_rejects_concurrent_owner_before_rewriting_progress(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "normalizer-lock")
    output = parent / "evidence"
    with pytest.raises(RuntimeError):
        _run(tmp_path / "client-first-lock", output, interrupt_after_packet=1)
    progress_path = throughput.resume_root_for(output) / throughput.PROGRESS_NAME
    before = progress_path.read_bytes()

    client = _client(tmp_path / "client-second-lock")
    try:
        with throughput.exclusive_resume_lock(throughput.resume_root_for(output)):
            with pytest.raises(throughput.ThroughputResumeError, match="compiler_lock_held"):
                _RUNNER._normalize_resume_identity_ledger(output, client)
    finally:
        client.close()
    assert progress_path.read_bytes() == before


def test_runner_rejects_legacy_identity_drift_before_rewriting_progress(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "identity-drift")
    output = parent / "evidence"
    with pytest.raises(RuntimeError):
        _run(tmp_path / "client-first-drift", output, interrupt_after_packet=1)
    _append_legacy_identity_calls(output, count=1, response_sha256="d" * 64)
    progress_path = throughput.resume_root_for(output) / throughput.PROGRESS_NAME
    before = progress_path.read_bytes()

    client = _client(tmp_path / "client-second-drift")
    try:
        with pytest.raises(_RUNNER.RunnerError, match="resume_identity_drift"):
            _RUNNER._normalize_resume_identity_ledger(output, client)
    finally:
        client.close()
    assert progress_path.read_bytes() == before


@pytest.mark.parametrize("entry_type", ("file", "symlink"))
def test_runner_rejects_non_directory_resume_metadata(
    tmp_path: Path,
    entry_type: str,
) -> None:
    package = _private_parent(tmp_path, "package")
    output = package / "evidence"
    root = throughput.resume_root_for(output)
    if entry_type == "file":
        root.touch(mode=0o600)
    else:
        root.symlink_to(tmp_path / "outside")

    with pytest.raises(_RUNNER.RunnerError, match="resume_metadata_invalid"):
        with _RUNNER._admit_reviewed_resume_root(package, output):
            pass


def test_runner_rejects_resume_metadata_with_wrong_mode(tmp_path: Path) -> None:
    package = _private_parent(tmp_path, "package")
    output = package / "evidence"
    root = throughput.resume_root_for(output)
    root.mkdir(mode=0o755)

    with pytest.raises(_RUNNER.RunnerError, match="resume_metadata_invalid"):
        with _RUNNER._admit_reviewed_resume_root(package, output):
            pass


def test_runner_rejects_resume_metadata_with_wrong_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _private_parent(tmp_path, "package")
    output = package / "evidence"
    root = throughput.resume_root_for(output)
    root.mkdir(mode=0o700)
    real_lstat = Path.lstat

    def _wrong_owner_lstat(path: Path):
        info = real_lstat(path)
        if path == root:
            values = list(info)
            values[4] = os.geteuid() + 1
            return os.stat_result(values)
        return info

    monkeypatch.setattr(Path, "lstat", _wrong_owner_lstat)
    with pytest.raises(_RUNNER.RunnerError, match="resume_metadata_invalid"):
        with _RUNNER._admit_reviewed_resume_root(package, output):
            pass


def test_resume_is_serial_only() -> None:
    assert throughput.packet_loop_is_serial() is True
    assert throughput.bound_packet_workers(1) == 1
    with pytest.raises(throughput.ThroughputResumeError, match="packet_workers_not_authorized"):
        throughput.bound_packet_workers(2, authorized=True)


def test_progress_recomputes_hash_only_call_ledger_and_rejects_tamper(tmp_path: Path) -> None:
    client = _client(tmp_path)
    attestation = client.transport_attestation()
    records = client.transport_call_records()
    identity = throughput.build_resume_identity(
        {
            "tokenizer_id": compiler.TOKENIZER_ID,
            "tokenizer_version": compiler.TOKENIZER_VERSION,
            "code_hashes": compiler.CODE_HASHES,
            **{key: client.server_identity()[key] for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256")},
        },
        source_package_binding=None,
        packet_bindings=[],
        residual_lane_packets=[],
        target_packet_count=2,
        target_row_count=2,
    )
    receipt = throughput.build_progress_receipt(
        sealed_packet_count=0,
        target_packet_count=2,
        target_row_count=2,
        last_sealed_sidecar_sha256=None,
        last_sealed_sidecar_id=None,
        resume_identity=identity,
        mcp_transport_attestation=attestation,
        mcp_call_records=records,
    )
    dumped = contract.canonical_json(receipt)
    assert "слово" not in dumped
    assert "http://" not in dumped
    assert receipt["activation_state"] == throughput.ACTIVATION_STATE

    tampered = json.loads(json.dumps(receipt))
    tampered["mcp_call_records"][0]["response_sha256"] = "f" * 64
    unsigned = {key: value for key, value in tampered.items() if key != "progress_sha256"}
    tampered["progress_sha256"] = contract.sha256_value(unsigned)
    with pytest.raises(throughput.ThroughputResumeError, match="transport_commitment_drift"):
        throughput.validate_progress_receipt(
            tampered,
            identity,
            expected_transport=str(attestation["transport"]),
            expected_endpoint_sha256=str(attestation["endpoint_sha256"]),
            expected_tool_set_sha256=str(attestation["required_tool_set_sha256"]),
        )
    drifted_identity = {**identity, "target_row_count": 3}
    with pytest.raises(throughput.ThroughputResumeError, match="identity_drift"):
        throughput.validate_progress_receipt(
            receipt,
            drifted_identity,
            expected_transport=str(attestation["transport"]),
            expected_endpoint_sha256=str(attestation["endpoint_sha256"]),
            expected_tool_set_sha256=str(attestation["required_tool_set_sha256"]),
        )
    client.close()


def test_recursive_private_key_rejection(tmp_path: Path) -> None:
    client = _client(tmp_path)
    attestation = dict(client.transport_attestation())
    records = client.transport_call_records()
    records[0]["nested"] = {"prompt": "forbidden"}
    with pytest.raises(throughput.ThroughputResumeError, match="call_record_invalid"):
        throughput.build_progress_receipt(
            sealed_packet_count=0,
            target_packet_count=2,
            target_row_count=2,
            last_sealed_sidecar_sha256=None,
            last_sealed_sidecar_id=None,
            resume_identity={"x": 1},
            mcp_transport_attestation=attestation,
            mcp_call_records=records,
        )
    client.close()


def test_preplaced_symlink_and_mode_drift_fail_closed(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    output = parent / "evidence"
    root = throughput.resume_root_for(output)
    target = _private_parent(tmp_path, "target")
    root.symlink_to(target, target_is_directory=True)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_symlink"):
        throughput.prepare_resume_root(output)
    root.unlink()
    root.mkdir(mode=0o755)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_mode_drift"):
        throughput.prepare_resume_root(output)


def test_owner_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = _private_parent(tmp_path, "private")
    current_uid = os.geteuid()
    monkeypatch.setattr(throughput.os, "geteuid", lambda: current_uid + 1)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_owner_drift"):
        throughput.prepare_resume_root(parent / "evidence")


def test_compiler_level_lock_rejects_concurrent_owner(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    root, _ = throughput.prepare_resume_root(parent / "evidence")
    with throughput.exclusive_resume_lock(root):
        with pytest.raises(throughput.ThroughputResumeError, match="compiler_lock_held"):
            with throughput.exclusive_resume_lock(root):
                pass


def test_foreign_resume_root_entry_fails_closed(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    root, _ = throughput.prepare_resume_root(parent / "evidence")
    foreign = root / "foreign"
    foreign.write_text("x", encoding="utf-8")
    foreign.chmod(0o600)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_foreign_entry"):
        throughput.inspect_resume_root(root)


def test_one_interrupted_progress_temp_is_discarded(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    root, _ = throughput.prepare_resume_root(parent / "evidence")
    interrupted = root / ".progress.json.interrupted"
    interrupted.write_text("{", encoding="utf-8")
    interrupted.chmod(0o600)
    throughput.inspect_resume_root(root)
    assert not interrupted.exists()


def test_multiple_interrupted_progress_temps_fail_closed(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    root, _ = throughput.prepare_resume_root(parent / "evidence")
    for suffix in ("one", "two"):
        interrupted = root / f".progress.json.{suffix}"
        interrupted.write_text("{", encoding="utf-8")
        interrupted.chmod(0o600)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_temp_invalid"):
        throughput.inspect_resume_root(root)


def test_crash_after_seal_resumes_without_recompiling_prefix(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "resume")
    output = parent / "evidence"
    with pytest.raises(RuntimeError, match="synthetic_interrupt_after_seal"):
        _run(tmp_path / "client-a", output, interrupt_after_packet=1)
    root = throughput.resume_root_for(output)
    assert (root / "bundle" / "sidecar-0001.json").is_file()
    first_bytes = (root / "bundle" / "sidecar-0001.json").read_bytes()

    manifest = _run(tmp_path / "client-b", output)
    assert manifest["packet_count"] == 2
    assert manifest["row_count"] == 2
    assert (output / "sidecar-0001.json").read_bytes() == first_bytes
    assert not root.exists()


def test_one_trailing_uncommitted_sidecar_is_discarded(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "resume")
    output = parent / "evidence"
    with pytest.raises(RuntimeError):
        _run(tmp_path / "client-a", output, interrupt_after_packet=1)
    bundle = throughput.bundle_dir_for(output)
    trailing = bundle / "sidecar-0002.json"
    trailing.write_bytes((bundle / "sidecar-0001.json").read_bytes())
    trailing.chmod(0o600)
    manifest = _run(tmp_path / "client-b", output)
    assert manifest["packet_count"] == 2
    assert json.loads((output / "sidecar-0002.json").read_text())["packet_index"] == 2


def test_gap_and_multiple_atomic_temps_fail_closed(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "resume")
    output = parent / "evidence"
    _, bundle = throughput.prepare_resume_root(output)
    for name in ("sidecar-0001.json", "sidecar-0003.json"):
        path = bundle / name
        path.write_text("{}", encoding="utf-8")
        path.chmod(0o600)
    with pytest.raises(throughput.ThroughputResumeError, match="sealed_prefix_gap"):
        throughput.inspect_sealed_prefix(bundle)

    for path in list(bundle.iterdir()):
        path.unlink()
    for suffix in ("one", "two"):
        temporary = bundle / f".sidecar-0001.json.{suffix}"
        temporary.write_text("{", encoding="utf-8")
        temporary.chmod(0o600)
    with pytest.raises(throughput.ThroughputResumeError, match="resume_temp_invalid"):
        throughput.inspect_sealed_prefix(bundle)


def test_crash_after_atomic_install_is_repaired(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "repair")
    output = parent / "evidence"
    with pytest.raises(RuntimeError, match="synthetic_interrupt_after_install"):
        _run(tmp_path / "client-a", output, interrupt_after_install=True)
    root = throughput.resume_root_for(output)
    assert output.is_dir()
    assert root.is_dir()
    manifest = _run(tmp_path / "client-b", output)
    assert manifest["packet_count"] == 2
    assert not root.exists()


def test_crash_during_cleanup_cannot_strand_installed_output(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "repair")
    output = parent / "evidence"
    with pytest.raises(RuntimeError, match="synthetic_interrupt_after_install"):
        _run(tmp_path / "client-a", output, interrupt_after_install=True)
    root = throughput.resume_root_for(output)
    tombstone = root.with_name(f"{root.name}.cleanup")
    os.rename(root, tombstone)
    (tombstone / throughput.PROGRESS_NAME).unlink()

    manifest = _run(tmp_path / "client-b", output)
    assert manifest["packet_count"] == 2
    assert output.is_dir()
    assert not root.exists()
    assert not tombstone.exists()


def test_runner_allows_private_installed_output_for_idempotent_validation(tmp_path: Path) -> None:
    package = _private_parent(tmp_path, "package")
    source_manifest = package / "label-manifest.json"
    source_manifest.write_text("{}", encoding="utf-8")
    source_manifest.chmod(0o600)
    output = package / "evidence"
    output.mkdir(mode=0o700)
    assert _RUNNER._validate_paths(package, source_manifest, output) == (package, source_manifest, output)


def test_straight_and_resumed_sidecars_are_byte_identical(tmp_path: Path) -> None:
    straight_parent = _private_parent(tmp_path, "straight")
    resumed_parent = _private_parent(tmp_path, "resumed")
    straight = straight_parent / "evidence"
    resumed = resumed_parent / "evidence"
    _run(tmp_path / "client-straight", straight)
    with pytest.raises(RuntimeError):
        _run(tmp_path / "client-first", resumed, interrupt_after_packet=1)
    _run(tmp_path / "client-second", resumed)
    for packet_index in (1, 2):
        name = throughput.sidecar_filename(packet_index)
        assert (straight / name).read_bytes() == (resumed / name).read_bytes()
    straight_manifest = json.loads((straight / "manifest.json").read_text())
    resumed_manifest = json.loads((resumed / "manifest.json").read_text())
    assert straight_manifest["mcp_transport_attestation"] != resumed_manifest["mcp_transport_attestation"]


def test_invalid_existing_output_without_resume_metadata_is_refused(tmp_path: Path) -> None:
    parent = _private_parent(tmp_path, "private")
    output = parent / "evidence"
    output.mkdir(mode=0o700)
    with pytest.raises(contract.EvidenceContractError, match="bundle shape drift"):
        _run(tmp_path / "client", output)
