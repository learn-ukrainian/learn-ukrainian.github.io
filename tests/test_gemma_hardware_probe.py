from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from scripts.projects.open_model_data import gemma_hardware_probe as probe

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
PLAN_PATH = ROOT / "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json"


def _authorization() -> dict:
    return {
        "authorization": {
            "hardware_flavor": "l40sx1",
            "maximum_provider_charge_usd": 1.8,
            "model_download_authorized": True,
            "operator_all_inclusive_ceiling_eur": 3,
            "paid_attempts": 1,
            "provider": "Hugging Face Jobs",
            "provider_job_launch_authorized": True,
            "timeout_seconds": 3600,
        },
        "boundaries": {
            "data_upload_authorized": False,
            "evaluation_data_authorized": False,
            "model_or_checkpoint_upload_authorized": False,
            "model_quality_claim_authorized": False,
            "private_job_script_transport_authorized": True,
            "publication_authorized": False,
            "stage_1_treatment_authorized": False,
            "synthetic_fixture_only": True,
            "treatment_data_authorized": False,
        },
        "operator_decision": {
            "approved": True,
            "approved_at": "2026-08-02T00:00:00Z",
            "source": "operator approval fixture for a non-paid unit test",
        },
        "plan": {
            "bytes": 2537,
            "logical_path": "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json",
            "sha256": probe.EXPECTED_PLAN_SHA256,
        },
        "probe_id": probe.PROBE_ID,
        "runner": {
            "bytes": 58901,
            "logical_path": "scripts/projects/open_model_data/gemma_hardware_probe.py",
            "sha256": "bd8f973570140b32e7e3c8f74f80f905dea4afd02cb09f2061b4f13213e32504",
        },
        "schema_version": "gemma_hardware_probe_authorization_v1",
    }


def _write_authorization(tmp_path: Path, value: dict | None = None) -> Path:
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(value or _authorization(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_committed_probe_schemas_and_plan_validate() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    for schema_name in (
        "gemma_hardware_probe_plan_v1.schema.json",
        "gemma_hardware_probe_authorization_v1.schema.json",
        "gemma_hardware_probe_receipt_v1.schema.json",
    ):
        schema = json.loads((CONTRACTS / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    schema = json.loads((CONTRACTS / "gemma_hardware_probe_plan_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(plan)
    assert probe.sha256_file(PLAN_PATH) == probe.EXPECTED_PLAN_SHA256
    assert plan["provider"] == {
        "billing_usd_per_minute": 0.03,
        "exposed_ports": False,
        "gpu_count": 1,
        "gpu_name": "NVIDIA L40S",
        "hardware_flavor": "l40sx1",
        "maximum_provider_charge_usd": 1.8,
        "paid_attempts": 1,
        "provider": "Hugging Face Jobs",
        "timeout_seconds": 3600,
    }
    assert plan["boundaries"]["treatment_data_used"] is False
    assert plan["boundaries"]["evaluation_data_used"] is False
    assert plan["claims"]["prohibited"][0] == "stage_1_treatment_completion"


def test_exact_authorization_builds_one_bounded_hf_job(tmp_path: Path) -> None:
    authorization_path = _write_authorization(tmp_path)
    fake_hf = tmp_path / "hf"
    fake_hf.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_hf.chmod(0o700)
    command = probe.build_hf_job_command(
        plan_path=PLAN_PATH,
        authorization_path=authorization_path,
        hf_cli=fake_hf,
    )
    joined = " ".join(command)
    assert command[:4] == [str(fake_hf), "jobs", "uv", "run"]
    assert command.count("--detach") == 1
    assert command[command.index("--timeout") + 1] == "3600s"
    assert command[command.index("--flavor") + 1] == "l40sx1"
    assert command[command.index("--secrets") + 1] == "HF_TOKEN"
    assert f"authorization_sha256={probe.sha256_file(authorization_path)}" in command
    assert "timeout_seconds=3600" in command
    assert "--expose" not in command
    assert "batch_state" not in joined
    assert "ua_eval_harness" not in joined
    assert command[-5:] == [
        "worker",
        "--plan-sha256",
        probe.EXPECTED_PLAN_SHA256,
        "--authorization-sha256",
        probe.sha256_file(authorization_path),
    ]
    safe = probe.safe_job_command(
        command,
        script_path=Path(probe.__file__).resolve(),
        script_placeholder="<WORKTREE_RUNNER>",
    )
    assert safe[0] == "<HF_CLI>"
    assert "<WORKTREE_RUNNER>" in safe
    assert str(Path(probe.__file__).resolve()) not in safe


def test_remote_script_path_resolves_without_parent_index_failure() -> None:
    assert probe._resolve_root(Path("/data/gemma_hardware_probe.py")) == Path("/data")


def test_authorized_runner_upload_snapshot_is_private_bound_and_drift_checked(tmp_path: Path) -> None:
    authorization_path = _write_authorization(tmp_path)
    snapshot = probe.create_authorized_runner_snapshot(
        authorization_path=authorization_path,
        output_directory=tmp_path / "runtime",
    )
    assert snapshot.read_bytes() == Path(probe.__file__).read_bytes()
    assert snapshot.stat().st_mode & 0o222 == 0
    probe.verify_authorized_runner_snapshot(
        snapshot=snapshot,
        authorization_path=authorization_path,
    )
    snapshot.chmod(0o600)
    snapshot.write_bytes(b"drift")
    with pytest.raises(probe.HardwareProbeError, match="snapshot drift"):
        probe.verify_authorized_runner_snapshot(
            snapshot=snapshot,
            authorization_path=authorization_path,
        )


def test_launch_executes_and_ledgers_the_authorized_snapshot_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorization_path = _write_authorization(tmp_path)
    fake_hf = tmp_path / "hf"
    fake_hf.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_hf.chmod(0o700)
    ledger = tmp_path / "batch/launch.json"
    global_claim = tmp_path / "global/claim.json"
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(
            returncode=0,
            stdout="id: 6a2bd1f1871c005b5352ad31",
            stderr="",
        )

    monkeypatch.setattr(probe, "ATTEMPT_LEDGER_PATH", ledger)
    monkeypatch.setattr(probe, "host_global_attempt_claim_path", lambda _: global_claim)
    monkeypatch.setattr(probe, "require_hf_auth", lambda _: None)
    monkeypatch.setattr(probe, "require_no_provider_attempt", lambda **_: None)
    monkeypatch.setattr(probe.subprocess, "run", fake_run)
    assert (
        probe.main(
            [
                "launch",
                "--authorization",
                str(authorization_path),
                "--hf-cli",
                str(fake_hf),
            ]
        )
        == 0
    )
    actual_command = calls[0]
    assert str(Path(probe.__file__).resolve()) not in actual_command
    assert any(argument.endswith(".authorized.py") for argument in actual_command)
    local_receipt = json.loads(ledger.read_text(encoding="utf-8"))
    host_receipt = json.loads(global_claim.read_text(encoding="utf-8"))
    assert local_receipt["command_source"] == "private_read_only_authorized_snapshot"
    assert "<AUTHORIZED_RUNNER_SNAPSHOT>" in local_receipt["command"]
    assert host_receipt["command"] == local_receipt["command"]
    assert host_receipt["job_id"] == "6a2bd1f1871c005b5352ad31"


def test_plan_or_authorization_drift_fails_before_provider_call(tmp_path: Path) -> None:
    authorization = _authorization()
    authorization["authorization"]["timeout_seconds"] = 7200
    authorization_path = _write_authorization(tmp_path, authorization)
    with pytest.raises(probe.HardwareProbeError, match="schema error"):
        probe.validate_plan_authorization(PLAN_PATH, authorization_path)

    runner_drift = _authorization()
    runner_drift["runner"]["sha256"] = "f" * 64
    with pytest.raises(probe.HardwareProbeError, match="schema error"):
        probe.validate_plan_authorization(PLAN_PATH, _write_authorization(tmp_path, runner_drift))

    drifted_plan = tmp_path / "plan.json"
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["provider"]["paid_attempts"] = 2
    drifted_plan.write_text(json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(probe.HardwareProbeError, match=r"schema error|runner-bound"):
        probe.validate_plan_authorization(drifted_plan, _write_authorization(tmp_path))


def test_job_id_parser_requires_exactly_one_identifier() -> None:
    assert probe.parse_job_id("Job started\nid: 6a2bd1f1871c005b5352ad31\n") == "6a2bd1f1871c005b5352ad31"
    with pytest.raises(probe.HardwareProbeError, match="exactly one"):
        probe.parse_job_id("no job here")
    with pytest.raises(probe.HardwareProbeError, match="exactly one"):
        probe.parse_job_id(f"6a2bd1f1871c005b5352ad31 {'b' * 24}")


def test_launch_fails_closed_when_hf_auth_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(returncode=1, stdout="", stderr="not logged in")

    monkeypatch.setattr(probe.subprocess, "run", fake_run)
    with pytest.raises(probe.HardwareProbeError, match="authentication is not configured"):
        probe.launch_job(["/safe/hf", "jobs", "uv", "run"])
    assert calls == [["/safe/hf", "auth", "whoami"]]


def test_launch_uses_secret_reference_not_token_value(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    results = iter(
        (
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=0, stdout="id: 6a2bd1f1871c005b5352ad31", stderr=""),
        )
    )

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        return next(results)

    monkeypatch.setattr(probe.subprocess, "run", fake_run)
    monkeypatch.setenv("HF_TOKEN", "hf_secret_must_not_appear")
    command = ["/safe/hf", "jobs", "uv", "run", "--secrets", "HF_TOKEN"]
    assert probe.launch_job(command) == "6a2bd1f1871c005b5352ad31"
    assert all("hf_secret_must_not_appear" not in argument for call in calls for argument in call)


def test_paid_attempt_claim_is_exclusive_and_durable(tmp_path: Path) -> None:
    ledger = tmp_path / "launch.json"
    first = {"status": "launch_claimed_before_provider_call", "attempt": 1}
    probe.claim_paid_attempt(ledger, first)
    assert json.loads(ledger.read_text(encoding="utf-8")) == first
    with pytest.raises(probe.HardwareProbeError, match="already exists"):
        probe.claim_paid_attempt(ledger, {"status": "duplicate"})
    assert json.loads(ledger.read_text(encoding="utf-8")) == first


def test_provider_attempt_query_blocks_reused_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def empty_run(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="[]\n", stderr="")

    monkeypatch.setattr(probe.subprocess, "run", empty_run)
    probe.require_no_provider_attempt(hf_cli="/safe/hf", authorization_sha256="a" * 64)
    assert calls[0][-3:] == ["--label", "authorization_sha256=" + "a" * 64, "--json"]

    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *_, **__: SimpleNamespace(
            returncode=0,
            stdout=json.dumps([{"id": "6a2bd1f1871c005b5352ad31"}]),
            stderr="",
        ),
    )
    with pytest.raises(probe.HardwareProbeError, match="already has a job"):
        probe.require_no_provider_attempt(hf_cli="/safe/hf", authorization_sha256="a" * 64)


def test_collector_persists_and_validates_one_job_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job_id = "6a2bd1f1871c005b5352ad31"
    authorization_path = _write_authorization(tmp_path)
    authorization_sha256 = probe.sha256_file(authorization_path)
    monkeypatch.setenv("JOB_ID", job_id)
    receipt = probe.aborted_worker_receipt(
        authorization_sha256=authorization_sha256,
        abort_reason="HardwareProbeError: synthetic unit-test abort",
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
    )
    fake_hf = tmp_path / "hf"
    fake_hf.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_hf.chmod(0o700)
    results = iter(
        (
            SimpleNamespace(returncode=2, stdout="aborted\n", stderr=""),
            SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    [
                        {
                            "durations": {"running_secs": 20},
                            "flavor": "l40sx1",
                            "id": job_id,
                            "labels": {
                                "authorization_sha256": authorization_sha256,
                                "issue": "6170",
                                "plan_sha256": probe.EXPECTED_PLAN_SHA256,
                                "probe_id": probe.PROBE_ID,
                                "timeout_seconds": "3600",
                            },
                            "status": {"stage": "ERROR"},
                        }
                    ]
                )
                + "\n",
                stderr="",
            ),
            SimpleNamespace(returncode=1, stdout="", stderr="metrics unavailable after exit"),
            SimpleNamespace(returncode=0, stdout=f"{probe.RECEIPT_MARKER}{probe.canonical_json(receipt)}\n", stderr=""),
        )
    )
    monkeypatch.setattr(probe, "require_hf_auth", lambda _: None)
    monkeypatch.setattr(probe.subprocess, "run", lambda *_, **__: next(results))
    output_directory = tmp_path / "evidence"
    collected = probe.collect_job(
        job_id=job_id,
        hf_cli=fake_hf,
        authorization_path=authorization_path,
        output_directory=output_directory,
    )
    assert collected["provider_job"]["job_status"] == "ERROR"
    assert collected["provider_job"]["provider_running_seconds"] == 20
    assert collected["provider_job"]["provider_derived_cost_usd"] == 0.01
    assert collected["provider_job"]["provider_evidence_reconciled"] is True
    assert json.loads((output_directory / "worker-receipt.json").read_text(encoding="utf-8")) == collected
    provider_evidence = json.loads((output_directory / "provider-evidence.json").read_text(encoding="utf-8"))
    assert provider_evidence["stats_command_succeeded"] is False


def test_snapshot_verification_rejects_missing_byte_and_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(probe, "SNAPSHOT_FILES", {"tiny.bin": (3, probe.sha256_bytes(b"abc"))})
    with pytest.raises(probe.HardwareProbeError, match="missing"):
        probe.verify_snapshot(tmp_path)
    target = tmp_path / "tiny.bin"
    target.write_bytes(b"ab")
    with pytest.raises(probe.HardwareProbeError, match="byte drift"):
        probe.verify_snapshot(tmp_path)
    target.write_bytes(b"abd")
    with pytest.raises(probe.HardwareProbeError, match="hash drift"):
        probe.verify_snapshot(tmp_path)
    target.write_bytes(b"abc")
    probe.verify_snapshot(tmp_path)


def test_phase_watchdog_terminates_child_at_internal_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = SimpleNamespace(
        exitcode=None,
        alive=True,
        killed=False,
        terminated=False,
    )
    process.start = lambda: None
    process.join = lambda timeout=None: None
    process.is_alive = lambda: process.alive

    def terminate() -> None:
        process.terminated = True
        process.alive = False

    def kill() -> None:
        process.killed = True
        process.alive = False

    process.terminate = terminate
    process.kill = kill
    context = SimpleNamespace(
        Queue=lambda maxsize: SimpleNamespace(),
        Process=lambda **kwargs: process,
    )
    monkeypatch.setattr(probe.multiprocessing, "get_context", lambda _: context)
    with pytest.raises(probe.HardwareProbeError, match="internal deadline"):
        probe.run_phase_process(
            model_directory=tmp_path / "model",
            checkpoint_input=None,
            checkpoint_output=tmp_path / "checkpoint",
            global_step=0,
            deadline_monotonic=probe.time.monotonic() - 1,
        )
    assert process.terminated is True
    assert process.killed is False


def test_phase_spawn_failure_does_not_claim_a_process_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = SimpleNamespace()
    process.start = lambda: (_ for _ in ()).throw(OSError("spawn failed"))
    context = SimpleNamespace(
        Queue=lambda maxsize: SimpleNamespace(),
        Process=lambda **kwargs: process,
    )
    monkeypatch.setattr(probe.multiprocessing, "get_context", lambda _: context)
    with pytest.raises(probe.PhaseExecutionError, match="could not start") as captured:
        probe.run_phase_process(
            model_directory=tmp_path / "model",
            checkpoint_input=tmp_path / "checkpoint-step-1",
            checkpoint_output=tmp_path / "checkpoint-step-2",
            global_step=1,
            deadline_monotonic=probe.time.monotonic() + 10,
        )
    assert captured.value.process_started is False


def test_phase_error_queue_preserves_step_when_marker_write_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    progress = {
        "fixture_sha256": "c" * 64,
        "global_step": 1,
        "loss": 1.25,
        "optimizer_step_performed": True,
        "tokens": 4096,
    }
    process = SimpleNamespace(exitcode=1)
    process.start = lambda: None
    process.join = lambda timeout=None: None
    process.is_alive = lambda: False
    result_queue = SimpleNamespace(
        get=lambda timeout: {
            "error": "OSError: marker fsync failed",
            "phase_evidence": progress,
        }
    )
    context = SimpleNamespace(
        Queue=lambda maxsize: result_queue,
        Process=lambda **kwargs: process,
    )
    monkeypatch.setattr(probe.multiprocessing, "get_context", lambda _: context)
    with pytest.raises(probe.PhaseExecutionError, match="marker fsync failed") as captured:
        probe.run_phase_process(
            model_directory=tmp_path / "model",
            checkpoint_input=None,
            checkpoint_output=tmp_path / "checkpoint-step-1",
            global_step=0,
            deadline_monotonic=probe.time.monotonic() + 10,
        )
    assert captured.value.process_started is True
    assert captured.value.phase_evidence == progress


def test_worker_rejects_wrong_accelerator_before_download(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCELERATOR", "a100-large")
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    with pytest.raises(probe.HardwareProbeError, match="accelerator"):
        probe.run_worker(
            plan_sha256=probe.EXPECTED_PLAN_SHA256,
            authorization_sha256="a" * 64,
        )


def test_intra_phase_failure_receipts_durable_optimizer_step_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    progress = {
        "fixture_sha256": "c" * 64,
        "global_step": 1,
        "loss": 1.25,
        "optimizer_step_performed": True,
        "tokens": 4096,
    }
    monkeypatch.setenv("ACCELERATOR", "l40sx1")
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    monkeypatch.setattr(probe, "_runtime_package_digest", lambda: "d" * 64)
    monkeypatch.setattr(
        probe,
        "_gpu_evidence",
        lambda: {"count": 1, "name": "NVIDIA L40S", "total_memory_bytes": 48 * 1024**3},
    )
    monkeypatch.setattr(probe, "_cuda_evidence", lambda: ("13.0", "580.1"))
    monkeypatch.setattr(probe, "download_snapshot", lambda _: None)
    monkeypatch.setattr(
        probe,
        "run_phase_process",
        lambda **_: (_ for _ in ()).throw(
            probe.PhaseExecutionError(
                "checkpoint write failed",
                phase_evidence=progress,
                process_started=True,
            )
        ),
    )
    monkeypatch.setattr(probe.tempfile, "mkdtemp", lambda **_: str(tmp_path / "worker-intra-phase"))
    (tmp_path / "worker-intra-phase").mkdir()

    with pytest.raises(probe.ProbeExecutionError) as captured:
        probe.run_worker(
            plan_sha256=probe.EXPECTED_PLAN_SHA256,
            authorization_sha256="a" * 64,
        )
    receipt = probe.aborted_worker_receipt(
        authorization_sha256="a" * 64,
        abort_reason=str(captured.value),
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
        partial_evidence=captured.value.partial_evidence,
    )
    _receipt_validator().validate(receipt)
    assert receipt["training_probe"]["optimizer_steps_before_checkpoint"] == 1
    assert receipt["training_probe"]["optimizer_steps_after_resume"] == 0
    assert receipt["training_probe"]["loss_before_checkpoint"] == 1.25
    assert receipt["checkpoint_resume"]["adapter"] is None
    assert receipt["checkpoint_resume"]["process_boundary"] is False
    assert receipt["throughput"]["tokens_processed"] == 4096


def test_resume_failure_receipts_the_completed_first_optimizer_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = {"bytes": 7, "sha256": "b" * 64}
    first = {
        "adapter": artifact,
        "checkpoint": artifact,
        "elapsed_seconds": 4.0,
        "fixture_sha256": "c" * 64,
        "global_step": 1,
        "loss": 1.25,
        "optimizer": artifact,
        "peak_allocated_bytes": 10,
        "peak_reserved_bytes": 20,
        "rng": artifact,
        "tokens": 4096,
    }
    phases = iter((first, probe.HardwareProbeError("resume exploded")))

    def phase(**_: object) -> dict:
        value = next(phases)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setenv("ACCELERATOR", "l40sx1")
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    monkeypatch.setattr(probe, "_runtime_package_digest", lambda: "d" * 64)
    monkeypatch.setattr(
        probe,
        "_gpu_evidence",
        lambda: {"count": 1, "name": "NVIDIA L40S", "total_memory_bytes": 48 * 1024**3},
    )
    monkeypatch.setattr(probe, "_cuda_evidence", lambda: ("13.0", "580.1"))
    monkeypatch.setattr(probe, "download_snapshot", lambda _: None)
    monkeypatch.setattr(probe, "run_phase_process", phase)
    monkeypatch.setattr(probe.tempfile, "mkdtemp", lambda **_: str(tmp_path / "worker"))
    (tmp_path / "worker").mkdir()

    with pytest.raises(probe.ProbeExecutionError) as captured:
        probe.run_worker(
            plan_sha256=probe.EXPECTED_PLAN_SHA256,
            authorization_sha256="a" * 64,
        )
    receipt = probe.aborted_worker_receipt(
        authorization_sha256="a" * 64,
        abort_reason=str(captured.value),
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
        partial_evidence=captured.value.partial_evidence,
    )
    _receipt_validator().validate(receipt)
    assert receipt["training_probe"]["optimizer_steps_before_checkpoint"] == 1
    assert receipt["training_probe"]["optimizer_steps_after_resume"] == 0
    assert receipt["training_probe"]["loss_before_checkpoint"] == 1.25
    assert receipt["facts"]["synthetic_adapter_optimizer_updates_performed"] is True
    assert receipt["checkpoint_resume"]["adapter"] == artifact
    assert receipt["checkpoint_resume"]["reload_passed"] is False
    assert json.loads((tmp_path / "worker/partial-progress.json").read_text(encoding="utf-8"))["first"] == first


def test_successful_worker_assembles_a_valid_completed_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = {"bytes": 7, "sha256": "b" * 64}
    first = {
        "adapter": artifact,
        "checkpoint": artifact,
        "elapsed_seconds": 4.0,
        "fixture_sha256": "c" * 64,
        "global_step": 1,
        "loss": 1.25,
        "optimizer": artifact,
        "peak_allocated_bytes": 10,
        "peak_reserved_bytes": 20,
        "rng": artifact,
        "tokens": 4096,
    }
    second = {
        **first,
        "elapsed_seconds": 3.0,
        "global_step": 2,
        "loss": 1.0,
        "peak_allocated_bytes": 11,
        "peak_reserved_bytes": 21,
    }
    phases = iter((first, second))
    monkeypatch.setenv("ACCELERATOR", "l40sx1")
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    monkeypatch.setattr(probe, "_runtime_package_digest", lambda: "d" * 64)
    monkeypatch.setattr(
        probe,
        "_gpu_evidence",
        lambda: {"count": 1, "name": "NVIDIA L40S", "total_memory_bytes": 48 * 1024**3},
    )
    monkeypatch.setattr(probe, "_cuda_evidence", lambda: ("13.0", "580.1"))
    monkeypatch.setattr(probe, "download_snapshot", lambda _: None)
    monkeypatch.setattr(probe, "run_phase_process", lambda **_: next(phases))
    monkeypatch.setattr(probe.tempfile, "mkdtemp", lambda **_: str(tmp_path / "worker-success"))
    (tmp_path / "worker-success").mkdir()

    receipt = probe.run_worker(
        plan_sha256=probe.EXPECTED_PLAN_SHA256,
        authorization_sha256="a" * 64,
    )
    _receipt_validator().validate(receipt)
    assert receipt["status"] == "completed"
    assert receipt["checkpoint_resume"]["process_boundary"] is True
    assert receipt["checkpoint_resume"]["reload_passed"] is True
    assert receipt["checkpoint_resume"]["adapter"] == first["adapter"]
    assert receipt["training_probe"]["optimizer_steps_before_checkpoint"] == 1
    assert receipt["training_probe"]["optimizer_steps_after_resume"] == 1
    assert receipt["throughput"]["tokens_processed"] == 8192


def test_post_second_validation_failure_receipts_both_optimizer_steps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = {"bytes": 7, "sha256": "b" * 64}
    first = {
        "adapter": artifact,
        "checkpoint": artifact,
        "elapsed_seconds": 4.0,
        "fixture_sha256": "c" * 64,
        "global_step": 1,
        "loss": 1.25,
        "optimizer": artifact,
        "peak_allocated_bytes": 10,
        "peak_reserved_bytes": 20,
        "rng": artifact,
        "tokens": 4096,
    }
    second = {
        **first,
        "elapsed_seconds": 3.0,
        "fixture_sha256": "e" * 64,
        "global_step": 2,
        "loss": 1.0,
        "peak_allocated_bytes": 11,
        "peak_reserved_bytes": 21,
    }
    phases = iter((first, second))
    monkeypatch.setenv("ACCELERATOR", "l40sx1")
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    monkeypatch.setattr(probe, "_runtime_package_digest", lambda: "d" * 64)
    monkeypatch.setattr(
        probe,
        "_gpu_evidence",
        lambda: {"count": 1, "name": "NVIDIA L40S", "total_memory_bytes": 48 * 1024**3},
    )
    monkeypatch.setattr(probe, "_cuda_evidence", lambda: ("13.0", "580.1"))
    monkeypatch.setattr(probe, "download_snapshot", lambda _: None)
    monkeypatch.setattr(probe, "run_phase_process", lambda **_: next(phases))
    monkeypatch.setattr(probe.tempfile, "mkdtemp", lambda **_: str(tmp_path / "worker-post-second"))
    (tmp_path / "worker-post-second").mkdir()

    with pytest.raises(probe.ProbeExecutionError) as captured:
        probe.run_worker(
            plan_sha256=probe.EXPECTED_PLAN_SHA256,
            authorization_sha256="a" * 64,
        )
    receipt = probe.aborted_worker_receipt(
        authorization_sha256="a" * 64,
        abort_reason=str(captured.value),
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
        partial_evidence=captured.value.partial_evidence,
    )
    _receipt_validator().validate(receipt)
    assert receipt["training_probe"]["optimizer_steps_before_checkpoint"] == 1
    assert receipt["training_probe"]["optimizer_steps_after_resume"] == 1
    assert receipt["training_probe"]["loss_after_resume"] == 1.0
    assert receipt["checkpoint_resume"]["process_boundary"] is True
    assert receipt["checkpoint_resume"]["reload_passed"] is True
    assert receipt["throughput"]["tokens_processed"] == 8192


def _receipt_validator() -> Draft202012Validator:
    schema = json.loads((CONTRACTS / "gemma_hardware_probe_receipt_v1.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_early_worker_abort_is_receipted_without_fabricated_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_ID", "6a2bd1f1871c005b5352ad31")
    receipt = probe.aborted_worker_receipt(
        authorization_sha256="a" * 64,
        abort_reason="HardwareProbeError: wrong GPU",
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
    )
    _receipt_validator().validate(receipt)
    assert receipt["status"] == "aborted"
    assert receipt["gpu"]["name"] is None
    assert receipt["environment"]["cuda_driver"] is None
    assert receipt["provider_job"]["provider_derived_cost_usd"] is None
    assert receipt["checkpoint_resume"]["adapter"] is None


def test_completed_receipt_requires_real_evidence_but_allows_pending_cost() -> None:
    artifact = {"bytes": 1, "sha256": "b" * 64}
    receipt = {
        "abort_reason": None,
        "attempt": 1,
        "authorization_sha256": "a" * 64,
        "checkpoint_resume": {
            "adapter": artifact,
            "optimizer": artifact,
            "process_boundary": True,
            "reload_passed": True,
            "rng": artifact,
        },
        "environment": {
            "cuda_driver": "580.1",
            "cuda_runtime": "13.0",
            "packages_sha256": "c" * 64,
            "python": "3.12.8",
            "runner_sha256": "d" * 64,
        },
        "facts": {
            "data_upload_performed": False,
            "evaluation_data_used": False,
            "model_or_checkpoint_upload_performed": False,
            "model_quality_evaluation_performed": False,
            "private_job_script_transport_used": True,
            "publication_performed": False,
            "purpose": "hardware_validation_non_treatment",
            "synthetic_adapter_optimizer_updates_performed": True,
            "treatment_data_used": False,
            "treatment_stage_1_performed": False,
        },
        "gpu": {
            "count": 1,
            "name": "NVIDIA L40S",
            "peak_allocated_bytes": 1,
            "peak_reserved_bytes": 1,
            "total_memory_bytes": 48 * 1024**3,
        },
        "plan": {
            "bytes": 2537,
            "logical_path": "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json",
            "sha256": probe.EXPECTED_PLAN_SHA256,
        },
        "probe_id": probe.PROBE_ID,
        "provider_job": {
            "actual_invoice_cost_eur": None,
            "actual_invoice_cost_usd": None,
            "billing_usd_per_minute": 0.03,
            "exposed_ports": False,
            "hardware_flavor": "l40sx1",
            "job_id": "6a2bd1f1871c005b5352ad31",
            "job_status": "worker_completed_pending_provider_reconciliation",
            "maximum_provider_charge_usd": 1.8,
            "provider": "Hugging Face Jobs",
            "provider_derived_cost_usd": None,
            "provider_evidence_reconciled": False,
            "provider_running_seconds": None,
            "timeout_seconds": 3600,
        },
        "runtime": {
            "ended_at": "2026-08-02T00:10:00Z",
            "provider_timeout_enforced": True,
            "started_at": "2026-08-02T00:00:00Z",
            "wall_seconds": 600,
        },
        "schema_version": "gemma_hardware_probe_receipt_v1",
        "snapshot_verification": {
            "all_files_bytes_match": True,
            "all_files_sha256_match": True,
            "manifest": {
                "bytes": 1994,
                "logical_path": "data/projects/open_model_data/treatments/gemma4_it_model_snapshot_manifest_v1.json",
                "sha256": "f0552bd6ee21764a0fc8c62b76d8458775f4f5e4969d701cf4c0d35c2f86fba1",
            },
        },
        "status": "completed",
        "throughput": {
            "elapsed_seconds": 10,
            "fixture_sha256": "e" * 64,
            "sequence_length": 4096,
            "tokens_per_second": 819.2,
            "tokens_processed": 8192,
        },
        "training_probe": {
            "adapter": "qlora_rank16_alpha32_dropout0.05",
            "loss_after_resume": 1.1,
            "loss_before_checkpoint": 1.2,
            "nonfinite_detected": False,
            "optimizer_steps_after_resume": 1,
            "optimizer_steps_before_checkpoint": 1,
            "quantization": "4bit_nf4_bf16_double_quantization",
        },
    }
    validator = _receipt_validator()
    validator.validate(receipt)
    reconciled = json.loads(json.dumps(receipt))
    reconciled["provider_job"].update(
        {
            "job_status": "COMPLETED",
            "provider_derived_cost_usd": 0.3,
            "provider_evidence_reconciled": True,
            "provider_running_seconds": 600,
        }
    )
    validator.validate(reconciled)
    receipt["provider_job"]["provider_derived_cost_usd"] = 0
    with pytest.raises(ValidationError, match="not of type 'null'"):
        validator.validate(receipt)


def test_provider_reconciliation_rejects_runner_drift() -> None:
    receipt = probe.aborted_worker_receipt(
        authorization_sha256="a" * 64,
        abort_reason="unit-test abort",
        started_at="2026-08-02T00:00:00Z",
        started_monotonic=probe.time.monotonic(),
    )
    inspection = {
        "durations": {"running_secs": 10},
        "flavor": "l40sx1",
        "id": "6a2bd1f1871c005b5352ad31",
        "labels": {
            "authorization_sha256": "a" * 64,
            "issue": "6170",
            "plan_sha256": probe.EXPECTED_PLAN_SHA256,
            "probe_id": probe.PROBE_ID,
            "timeout_seconds": "3600",
        },
        "status": {"stage": "ERROR"},
    }
    with pytest.raises(probe.HardwareProbeError, match="runner drift"):
        probe.reconcile_provider_receipt(
            receipt=receipt,
            inspection=inspection,
            job_id="6a2bd1f1871c005b5352ad31",
            authorization_sha256="a" * 64,
            authorization={"runner": {"sha256": "f" * 64}},
            wait_returncode=2,
        )


def test_atomic_writer_is_byte_stable(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    value = {"z": 1, "а": "українська"}
    probe.write_atomic(path, value)
    first = path.read_bytes()
    probe.write_atomic(path, value)
    assert path.read_bytes() == first
    assert json.loads(first) == value
