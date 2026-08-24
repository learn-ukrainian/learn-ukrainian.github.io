"""Unit tests for subprocess timeout bounds in scripts/projects/open_model_data/ (#7213 slice 7)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _completed(
    args: list[str] | None = None,
    returncode: int = 0,
    stdout: str | bytes = "",
    stderr: str | bytes = "",
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=args or [],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# 1. gemma_hardware_probe.py
# ---------------------------------------------------------------------------
def test_gemma_hardware_probe_require_hf_auth_timeout() -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        ghp.require_hf_auth("huggingface-cli")

    assert len(calls) == 1
    assert calls[0]["timeout"] == ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["huggingface-cli", "auth"], ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS),
    ):
        with pytest.raises(ghp.HardwareProbeError, match="Hugging Face authentication is not configured"):
            ghp.require_hf_auth("huggingface-cli")


def test_gemma_hardware_probe_require_no_provider_attempt_timeout() -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="[]")

    with patch("subprocess.run", side_effect=fake_run):
        ghp.require_no_provider_attempt(hf_cli="huggingface-cli", authorization_sha256="abc")

    assert len(calls) == 1
    assert calls[0]["timeout"] == ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["huggingface-cli", "jobs"], ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS),
    ):
        with pytest.raises(ghp.HardwareProbeError, match="cannot establish the provider-side paid-attempt state"):
            ghp.require_no_provider_attempt(hf_cli="huggingface-cli", authorization_sha256="abc")


def test_gemma_hardware_probe_launch_job_timeout() -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="job 617061706170617061706170 created")

    with patch("scripts.projects.open_model_data.gemma_hardware_probe.require_hf_auth"):
        with patch("subprocess.run", side_effect=fake_run):
            job_id = ghp.launch_job(["huggingface-cli", "jobs", "launch"])
            assert job_id == "617061706170617061706170"

        assert len(calls) == 1
        assert calls[0]["timeout"] == ghp.DEFAULT_HF_LAUNCH_TIMEOUT_SECONDS

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(["huggingface-cli", "jobs"], ghp.DEFAULT_HF_LAUNCH_TIMEOUT_SECONDS),
        ):
            with pytest.raises(ghp.HardwareProbeError, match="Hugging Face Job launch failed"):
                ghp.launch_job(["huggingface-cli", "jobs", "launch"])


def test_gemma_hardware_probe_collect_job_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "logs" in cmd:
            receipt_payload = {"schema_version": "gemma_hardware_probe_receipt_v1", "provider_job": {"job_id": "617061706170617061706170"}}
            return _completed(cmd, returncode=0, stdout=f"{ghp.RECEIPT_MARKER}{json.dumps(receipt_payload)}\n")
        return _completed(cmd, returncode=0, stdout="""[{"id": "617061706170617061706170"}]""")

    hf_cli = tmp_path / "hf_cli"
    hf_cli.write_text("#!/bin/sh\n", encoding="utf-8")
    hf_cli.chmod(0o755)
    auth_path = tmp_path / "auth.json"

    with patch("scripts.projects.open_model_data.gemma_hardware_probe.validate_plan_authorization", return_value=({}, "abc")), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.read_json", return_value={}), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.require_hf_auth"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.validate_schema"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.reconcile_provider_receipt", return_value=({"provider_job": {"job_id": "617061706170617061706170"}}, {})), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.write_atomic"), \
         patch("subprocess.run", side_effect=fake_run):
        res = ghp.collect_job(
            job_id="617061706170617061706170",
            hf_cli=hf_cli,
            authorization_path=auth_path,
            output_directory=tmp_path / "out",
        )
        assert res["provider_job"]["job_id"] == "617061706170617061706170"

    assert len(calls) == 4
    assert calls[0]["timeout"] == ghp.DEFAULT_HF_JOBS_WAIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS
    assert calls[2]["timeout"] == ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS
    assert calls[3]["timeout"] == ghp.DEFAULT_HF_CLI_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.gemma_hardware_probe.validate_plan_authorization", return_value=({}, "abc")), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.read_json", return_value={}), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.require_hf_auth"), \
         patch(
             "subprocess.run",
             side_effect=subprocess.TimeoutExpired(["huggingface-cli", "jobs", "wait"], ghp.DEFAULT_HF_JOBS_WAIT_TIMEOUT_SECONDS),
         ):
        with pytest.raises(ghp.HardwareProbeError, match="provider evidence collection failed"):
            ghp.collect_job(
                job_id="617061706170617061706170",
                hf_cli=hf_cli,
                authorization_path=auth_path,
                output_directory=tmp_path / "out",
            )


def test_gemma_hardware_probe_cuda_evidence_timeout() -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="535.183.01\n")

    torch_mock = MagicMock()
    torch_mock.version.cuda = "12.2"
    with patch.dict("sys.modules", {"torch": torch_mock}), patch("subprocess.run", side_effect=fake_run):
        runtime, driver = ghp._cuda_evidence()
        assert runtime == "12.2"
        assert driver == "535.183.01"

    assert len(calls) == 1
    assert calls[0]["timeout"] == ghp.DEFAULT_NVIDIA_SMI_TIMEOUT_SECONDS

    with patch.dict("sys.modules", {"torch": torch_mock}), patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["nvidia-smi"], ghp.DEFAULT_NVIDIA_SMI_TIMEOUT_SECONDS),
    ):
        with pytest.raises(ghp.HardwareProbeError, match="cannot resolve the NVIDIA driver version"):
            ghp._cuda_evidence()


def test_gemma_hardware_probe_main_launch_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import gemma_hardware_probe as ghp

    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}", encoding="utf-8")
    auth_path = tmp_path / "auth.json"
    auth_path.write_text("{}", encoding="utf-8")
    hf_cli = tmp_path / "hf_cli"
    hf_cli.write_text("#!/bin/sh\n", encoding="utf-8")
    hf_cli.chmod(0o755)

    written_records: list[tuple[Any, dict]] = []

    def fake_write_atomic(path, value):
        written_records.append((path, value))

    with patch("sys.argv", ["gemma_hardware_probe.py", "launch", "--plan", str(plan_path), "--authorization", str(auth_path), "--hf-cli", str(hf_cli)]), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.validate_plan_authorization", return_value=({}, "auth_sha")), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.require_hf_auth"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.require_no_provider_attempt"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.build_hf_job_command", return_value=["huggingface-cli", "jobs", "launch"]), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.create_authorized_runner_snapshot", return_value=tmp_path / "runner.py"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.verify_authorized_runner_snapshot"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.claim_paid_attempt"), \
         patch("scripts.projects.open_model_data.gemma_hardware_probe.write_atomic", side_effect=fake_write_atomic), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["huggingface-cli", "jobs"], ghp.DEFAULT_HF_LAUNCH_TIMEOUT_SECONDS)):
        rc = ghp.main()
        assert rc == 2

    attempt_writes = [val for path, val in written_records if path == ghp.ATTEMPT_LEDGER_PATH]
    assert len(attempt_writes) == 2, f"expected 2 attempt ledger writes, got {len(attempt_writes)}"
    assert attempt_writes[0]["status"] == "authorized_snapshot_verified_before_provider_call"
    assert attempt_writes[1]["status"] == "provider_launch_failed_no_retry_authorized"


# ---------------------------------------------------------------------------
# 2. inventory_existing_assets.py
# ---------------------------------------------------------------------------
def test_inventory_existing_assets_run_git_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import inventory_existing_assets as iea

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="commit1\n")

    with patch("subprocess.run", side_effect=fake_run):
        out = iea._run_git(tmp_path, "rev-parse", "HEAD")
        assert out == "commit1\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == iea.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], iea.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(subprocess.TimeoutExpired):
            iea._run_git(tmp_path, "rev-parse", "HEAD")


# ---------------------------------------------------------------------------
# 3. phase3_audit_entropy.py
# ---------------------------------------------------------------------------
def test_phase3_audit_entropy_git_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_audit_entropy as pae

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=b"hash123\n")

    with patch("subprocess.run", side_effect=fake_run):
        res = pae._git(tmp_path, "rev-parse", "HEAD")
        assert res == b"hash123\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == pae.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], pae.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(pae.AuditEntropyError, match="required local git object is unavailable"):
            pae._git(tmp_path, "rev-parse", "HEAD", check=True)
        assert pae._git(tmp_path, "rev-parse", "HEAD", check=False) == b""
        assert pae._git_ok(tmp_path, "rev-parse", "HEAD") is False


# ---------------------------------------------------------------------------
# 4. phase3_disposition_audit.py
# ---------------------------------------------------------------------------
def test_phase3_disposition_audit_git_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_disposition_audit as pda

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="output")

    with patch("subprocess.run", side_effect=fake_run):
        res = pda._git(tmp_path, ["rev-parse", "HEAD"])
        assert res == "output"

    assert len(calls) == 1
    assert calls[0]["timeout"] == pda.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], pda.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(pda.AuditError, match="cannot execute git for entropy binding"):
            pda._git(tmp_path, ["rev-parse", "HEAD"])


# ---------------------------------------------------------------------------
# 5. phase3_donnu_2023_morphemics_word_formation_intake.py
# ---------------------------------------------------------------------------
def test_phase3_donnu_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_donnu_2023_morphemics_word_formation_intake as donnu

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_donnu_2023_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert donnu._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == donnu.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_donnu_2023_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], donnu.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(donnu.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            donnu._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 6. phase3_evaluation_context_manifest.py
# ---------------------------------------------------------------------------
def test_phase3_evaluation_context_manifest_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_evaluation_context_manifest as ecm

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_evaluation_context_manifest.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert ecm._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == ecm.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_evaluation_context_manifest.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], ecm.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(ecm.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            ecm._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 7. phase3_evaluation_reproduction.py
# ---------------------------------------------------------------------------
def test_phase3_evaluation_reproduction_verify_outsider_commit_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_evaluation_reproduction as er

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="abcdef1234567890abcdef1234567890abcdef12\n")

    with patch("subprocess.run", side_effect=fake_run):
        er._verify_outsider_commit(tmp_path, "abcdef1234567890abcdef1234567890abcdef12")

    assert len(calls) == 1
    assert calls[0]["timeout"] == er.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], er.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(er.EvaluationReproductionError, match="cannot inspect artifact-root Git commit"):
            er._verify_outsider_commit(tmp_path, "abcdef1234567890abcdef1234567890abcdef12")


# ---------------------------------------------------------------------------
# 8. phase3_linguistic_canary.py
# ---------------------------------------------------------------------------
def test_phase3_linguistic_canary_verify_pinned_corpus_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_linguistic_canary as plc
    from scripts.projects.open_model_data import phase3_linguistic_representation as rep

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=f"{plc.UA_GEC_COMMIT}\n")

    with patch("subprocess.run", side_effect=fake_run):
        # Empty packets battery
        res = plc.verify_pinned_corpus({"packets": []}, tmp_path)
        assert res["commit"] == plc.UA_GEC_COMMIT

    assert len(calls) == 1
    assert calls[0]["timeout"] == plc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], plc.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(rep.LinguisticRepresentationError, match="cannot verify UA-GEC checkout commit"):
            plc.verify_pinned_corpus({"packets": []}, tmp_path)


# ---------------------------------------------------------------------------
# 10. phase3_pliush_2005_canonical_grammar_intake.py
# ---------------------------------------------------------------------------
def test_phase3_pliush_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_pliush_2005_canonical_grammar_intake as pliush

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_pliush_2005_canonical_grammar_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert pliush._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == pliush.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_pliush_2005_canonical_grammar_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], pliush.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(pliush.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            pliush._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 11. phase3_pravopys_evaluation_context.py
# ---------------------------------------------------------------------------
def test_phase3_pravopys_evaluation_context_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_pravopys_evaluation_context as pec

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_pravopys_evaluation_context.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert pec._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == pec.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_pravopys_evaluation_context.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], pec.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(pec.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            pec._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 12. phase3_recovery_contracts.py
# ---------------------------------------------------------------------------
def test_phase3_recovery_contracts_locate_shared_batch_state_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_recovery_contracts as prc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=str(tmp_path / ".git"))

    with patch("subprocess.run", side_effect=fake_run):
        prc.locate_shared_batch_state(tmp_path)

    assert len(calls) == 1
    assert calls[0]["timeout"] == prc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], prc.DEFAULT_GIT_TIMEOUT_SECONDS)):
        assert prc.locate_shared_batch_state(tmp_path) is None


# ---------------------------------------------------------------------------
# 13. phase3_rule_author_packets.py
# ---------------------------------------------------------------------------
def test_phase3_rule_author_packets_output_is_private_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_rule_author_packets as rap

    batch_file = tmp_path / "batch_state" / "output.json"

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("scripts.projects.open_model_data.phase3_rule_author_packets.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        rap._output_is_private(batch_file)

    assert len(calls) == 1
    assert calls[0]["timeout"] == rap.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_rule_author_packets.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], rap.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(rap.PacketCompilerError, match="packet output path is not ignored by Git"):
            rap._output_is_private(batch_file)


# ---------------------------------------------------------------------------
# 14. phase3_rule_author_runner.py
# ---------------------------------------------------------------------------
def test_phase3_rule_author_runner_run_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_rule_author_runner as rar

    bundle_path = tmp_path / "bundle.json"
    role_path = tmp_path / "role.json"
    private_dir = tmp_path / "private"
    private_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_dir.chmod(0o700)
    receipt_path = tmp_path / "receipt.json"

    prompt_file = private_dir / "prompts" / "00001.md"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_bytes(b"prompt text")
    prompt_file.chmod(0o600)

    manifest = {
        "packets": [
            {
                "packet_id": "p1",
                "record": "records/1.json",
                "raw": "raw/1.raw",
                "prompt": "prompts/00001.md",
                "prompt_sha256": rar.sha256_bytes(b"prompt text"),
                "task_id": "t1",
                "actor": "a1",
                "packet_index": 1,
            }
        ]
    }

    recorded_errors: list[str | None] = []

    def fake_record(entry, manifest, root, *, execution_error=None):
        recorded_errors.append(execution_error)
        return {"status": "failed", "execution_error": execution_error}

    with patch("scripts.projects.open_model_data.phase3_rule_author_runner.prepare", return_value=manifest), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner.command_for", return_value=["bridge"]), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner._record", side_effect=fake_record), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner._assert_tree"), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner._safe_receipt_path", return_value=receipt_path), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner._receipt", return_value={"complete": False, "canary": False, "failed_count": 1, "unparsed_count": 1}), \
         patch("scripts.projects.open_model_data.phase3_rule_author_runner._write_public_receipt"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["bridge"], 30.0)):
        receipt = rar.run(
            bundle_path=bundle_path,
            role_path=role_path,
            private_dir=private_dir,
            receipt_path=receipt_path,
            exact_model="gemini-3.6-flash-high",
        )
        assert receipt["failed_count"] == 1
    assert recorded_errors == ["bridge_timeout:TimeoutExpired"]


# ---------------------------------------------------------------------------
# 15. phase3_school_parent_section_context.py
# ---------------------------------------------------------------------------
def test_phase3_school_parent_section_context_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_school_parent_section_context as spsc

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_school_parent_section_context.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert spsc._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == spsc.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_school_parent_section_context.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], spsc.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(spsc.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            spsc._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 16. phase3_source_universe.py
# ---------------------------------------------------------------------------
def test_phase3_source_universe_verify_merged_main_binding_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_source_universe as su

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "rev-parse" in cmd:
            return _completed(cmd, returncode=0, stdout=b"abcdef1234567890abcdef1234567890abcdef12\n")
        if "show" in cmd:
            return _completed(cmd, returncode=0, stdout=b"script bytes")
        return _completed(cmd, returncode=0)

    script_file = tmp_path / su.FREEZER_SCRIPT_PATH
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_bytes(b"script bytes")

    with patch("scripts.projects.open_model_data.phase3_source_universe.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        res = su._verify_merged_main_binding("abcdef1234567890abcdef1234567890abcdef12")
        assert res["implementation_version"] == su.FREEZER_IMPLEMENTATION_VERSION

    assert len(calls) == 2
    assert calls[0]["timeout"] == su.DEFAULT_GIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == su.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_source_universe.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], su.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(su.FreezeError, match="unable to verify merged-main binding"):
            su._verify_merged_main_binding("abcdef1234567890abcdef1234567890abcdef12")


def test_phase3_source_universe_extract_pdf_pages_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_source_universe as su

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"dummy pdf")
    pdftotext = tmp_path / "pdftotext"
    pdftotext.write_text("#!/bin/sh\n", encoding="utf-8")
    pdftotext.chmod(0o755)

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=b"Page 1\x0cPage 2\x0c")

    with patch("subprocess.run", side_effect=fake_run):
        pages = su.extract_pdf_pages(pdf_file, pdftotext)
        assert pages == ["Page 1", "Page 2"]

    assert len(calls) == 1
    assert calls[0]["timeout"] == su.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["pdftotext"], su.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS)):
        with pytest.raises(su.FreezeError, match=r"pdftotext failed for sample\.pdf"):
            su.extract_pdf_pages(pdf_file, pdftotext)


# ---------------------------------------------------------------------------
# 18. phase3_ua_gec_complete_context.py
# ---------------------------------------------------------------------------
def test_phase3_ua_gec_complete_context_checkout_commit_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_ua_gec_complete_context as ugc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "rev-parse" in cmd:
            return _completed(cmd, returncode=0, stdout=f"{ugc.UA_GEC_COMMIT}\n")
        if "status" in cmd:
            return _completed(cmd, returncode=0, stdout="")
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        commit = ugc._checkout_commit(tmp_path)
        assert commit == ugc.UA_GEC_COMMIT

    assert len(calls) == 2
    assert calls[0]["timeout"] == ugc.DEFAULT_GIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == ugc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], ugc.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(ugc.UaGecCompleteContextError, match="cannot verify UA-GEC checkout commit"):
            ugc._checkout_commit(tmp_path)

    def fake_run_rev_parse_only(cmd, **kwargs):
        if "rev-parse" in cmd:
            return _completed(cmd, returncode=0, stdout=f"{ugc.UA_GEC_COMMIT}\n")
        raise subprocess.TimeoutExpired(["git", "status"], ugc.DEFAULT_GIT_TIMEOUT_SECONDS)

    with patch("subprocess.run", side_effect=fake_run_rev_parse_only):
        with pytest.raises(ugc.UaGecCompleteContextError, match="cannot verify UA-GEC checkout cleanliness"):
            ugc._checkout_commit(tmp_path)


# ---------------------------------------------------------------------------
# 17. phase3_university_content_audit_freeze.py
# ---------------------------------------------------------------------------
def test_phase3_university_content_audit_freeze_validate_drive_backup_timeout(tmp_path: Path) -> None:
    import contextlib

    from scripts.projects.open_model_data import phase3_university_content_audit_freeze as ucaf

    backup_file = tmp_path / "backup.gz"
    backup_file.write_bytes(b"dummy")

    post_backup = {
        "backup": {
            "google_drive_upload_verified": True,
            "google_drive_uploading": False,
            "google_drive_item_id": "drive_id_123",
            "path": str(backup_file),
            "compressed_sha256": ucaf.sha256_file(backup_file),
            "decompressed_sha256": "abc",
        }
    }

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive_id_123\n")

    with patch("subprocess.run", side_effect=fake_run), patch("gzip.open"):
        # We test that timeout is passed to xattr
        with contextlib.suppress(Exception):
            ucaf._validate_drive_backup(post_backup)

    assert len(calls) == 1
    assert calls[0]["timeout"] == ucaf.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], ucaf.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(ucaf.UniversityContentAuditFreezeError, match="post-live database backup lacks Drive provider metadata"):
            ucaf._validate_drive_backup(post_backup)


# ---------------------------------------------------------------------------
# 18. phase3_v2_compatibility.py
# ---------------------------------------------------------------------------
def test_phase3_v2_compatibility_tracked_evidence_paths_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_v2_compatibility as v2c

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="file1\nfile2\n")

    with patch("scripts.projects.open_model_data.phase3_v2_compatibility.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        paths = v2c._tracked_evidence_paths()
        assert paths == {"file1", "file2"}

    assert len(calls) == 1
    assert calls[0]["timeout"] == v2c.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_v2_compatibility.ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], v2c.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(v2c.CompatibilityError, match="cannot enumerate tracked evidence"):
            v2c._tracked_evidence_paths()


# ---------------------------------------------------------------------------
# 19. phase3_vspu_2025_morphemics_word_formation_intake.py
# ---------------------------------------------------------------------------
def test_phase3_vspu_2025_morphemics_word_formation_intake_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_vspu_2025_morphemics_word_formation_intake as vmfi

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_vspu_2025_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert vmfi._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == vmfi.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_vspu_2025_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], vmfi.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(vmfi.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            vmfi._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 20. phase3_vspu_db_cutover.py
# ---------------------------------------------------------------------------
def test_phase3_vspu_db_cutover_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_vspu_db_cutover as vdc

    target_file = tmp_path / "Library/CloudStorage/GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert vdc._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == vdc.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], vdc.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(vdc.DriveIdentityPendingError, match="private artifact lacks Google Drive provider identity"):
            vdc._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 21. phase3_vspu_post_ingest_audit.py
# ---------------------------------------------------------------------------
def test_phase3_vspu_post_ingest_audit_uploaded_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_vspu_post_ingest_audit as vpia

    target_file = tmp_path / "file.jsonl"
    target_file.write_text("{}", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="1\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert vpia._uploaded(target_file) is True

    assert len(calls) == 1
    assert calls[0]["timeout"] == vpia.DEFAULT_MDLS_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["mdls"], vpia.DEFAULT_MDLS_TIMEOUT_SECONDS)):
        with pytest.raises(vpia.VspuPostIngestAuditError, match="cannot read Google Drive upload state"):
            vpia._uploaded(target_file)


# ---------------------------------------------------------------------------
# 22. phase3_vspu_source_materialization.py
# ---------------------------------------------------------------------------
def test_phase3_vspu_source_materialization_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_vspu_source_materialization as vsm

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_vspu_source_materialization.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert vsm._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == vsm.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_vspu_source_materialization.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], vsm.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(vsm.VspuSourceMaterializationError, match="private JSONL lacks Google Drive provider identity"):
            vsm._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 23. phase3_zhdu_2026_lexicology_phraseology_intake.py
# ---------------------------------------------------------------------------
def test_phase3_zhdu_2026_lexicology_phraseology_intake_drive_item_id_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_zhdu_2026_lexicology_phraseology_intake as zpi

    target_file = tmp_path / "GoogleDrive-test" / "My Drive" / "file.pdf"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("dummy", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="drive-item-123\n")

    with patch("scripts.projects.open_model_data.phase3_zhdu_2026_lexicology_phraseology_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=fake_run):
        assert zpi._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == zpi.DEFAULT_XATTR_TIMEOUT_SECONDS

    with patch("scripts.projects.open_model_data.phase3_zhdu_2026_lexicology_phraseology_intake.CLOUD_STORAGE_ROOT", tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], zpi.DEFAULT_XATTR_TIMEOUT_SECONDS)):
        with pytest.raises(zpi.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            zpi._drive_item_id(target_file)


# ---------------------------------------------------------------------------
# 24. verify_phase3_source_universe_freeze.py
# ---------------------------------------------------------------------------
def test_verify_phase3_source_universe_freeze_git_bytes_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as vsu

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=b"data")

    with patch("subprocess.run", side_effect=fake_run):
        out = vsu._git_bytes(tmp_path, ["cat-file", "-p", "HEAD"], "test")
        assert out == b"data"

    assert len(calls) == 1
    assert calls[0]["timeout"] == vsu.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], vsu.DEFAULT_GIT_TIMEOUT_SECONDS)):
        with pytest.raises(vsu.IntegrityError, match="unable to run git for test"):
            vsu._git_bytes(tmp_path, ["cat-file", "-p", "HEAD"], "test")
