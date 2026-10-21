"""Unit tests for subprocess timeout bounds in scripts/projects/open_model_data/ (#7213 slice 7)."""

from __future__ import annotations

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

    with (
        patch.dict("sys.modules", {"torch": torch_mock}),
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(["nvidia-smi"], ghp.DEFAULT_NVIDIA_SMI_TIMEOUT_SECONDS),
        ),
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

    with (
        patch(
            "sys.argv",
            [
                "gemma_hardware_probe.py",
                "launch",
                "--plan",
                str(plan_path),
                "--authorization",
                str(auth_path),
                "--hf-cli",
                str(hf_cli),
            ],
        ),
        patch(
            "scripts.projects.open_model_data.gemma_hardware_probe.validate_plan_authorization",
            return_value=({}, "auth_sha"),
        ),
        patch("scripts.projects.open_model_data.gemma_hardware_probe.require_hf_auth"),
        patch("scripts.projects.open_model_data.gemma_hardware_probe.require_no_provider_attempt"),
        patch(
            "scripts.projects.open_model_data.gemma_hardware_probe.build_hf_job_command",
            return_value=["huggingface-cli", "jobs", "launch"],
        ),
        patch(
            "scripts.projects.open_model_data.gemma_hardware_probe.create_authorized_runner_snapshot",
            return_value=tmp_path / "runner.py",
        ),
        patch("scripts.projects.open_model_data.gemma_hardware_probe.verify_authorized_runner_snapshot"),
        patch("scripts.projects.open_model_data.gemma_hardware_probe.claim_paid_attempt"),
        patch("scripts.projects.open_model_data.gemma_hardware_probe.write_atomic", side_effect=fake_write_atomic),
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(["huggingface-cli", "jobs"], ghp.DEFAULT_HF_LAUNCH_TIMEOUT_SECONDS),
        ),
    ):
        rc = ghp.main()
        assert rc == 2

    attempt_writes = [val for path, val in written_records if path == ghp.ATTEMPT_LEDGER_PATH]
    assert len(attempt_writes) == 2, f"expected 2 attempt ledger writes, got {len(attempt_writes)}"
    assert attempt_writes[0]["status"] == "authorized_snapshot_verified_before_provider_call"
    assert attempt_writes[1]["status"] == "provider_launch_failed_no_retry_authorized"


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

    with (
        patch(
            "scripts.projects.open_model_data.phase3_donnu_2023_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT",
            tmp_path,
        ),
        patch("subprocess.run", side_effect=fake_run),
    ):
        assert donnu._drive_item_id(target_file) == "drive-item-123"

    assert len(calls) == 1
    assert calls[0]["timeout"] == donnu.DEFAULT_XATTR_TIMEOUT_SECONDS

    with (
        patch(
            "scripts.projects.open_model_data.phase3_donnu_2023_morphemics_word_formation_intake.CLOUD_STORAGE_ROOT",
            tmp_path,
        ),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["xattr"], donnu.DEFAULT_XATTR_TIMEOUT_SECONDS)),
    ):
        with pytest.raises(donnu.DriveIdentityPendingError, match="artifact lacks Google Drive provider identity"):
            donnu._drive_item_id(target_file)


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

    with (
        patch("scripts.projects.open_model_data.phase3_rule_author_packets.ROOT", tmp_path),
        patch("subprocess.run", side_effect=fake_run),
    ):
        rap._output_is_private(batch_file)

    assert len(calls) == 1
    assert calls[0]["timeout"] == rap.DEFAULT_GIT_TIMEOUT_SECONDS

    with (
        patch("scripts.projects.open_model_data.phase3_rule_author_packets.ROOT", tmp_path),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], rap.DEFAULT_GIT_TIMEOUT_SECONDS)),
    ):
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

    with (
        patch("scripts.projects.open_model_data.phase3_rule_author_runner.prepare", return_value=manifest),
        patch("scripts.projects.open_model_data.phase3_rule_author_runner.command_for", return_value=["bridge"]),
        patch("scripts.projects.open_model_data.phase3_rule_author_runner._record", side_effect=fake_record),
        patch("scripts.projects.open_model_data.phase3_rule_author_runner._assert_tree"),
        patch(
            "scripts.projects.open_model_data.phase3_rule_author_runner._safe_receipt_path", return_value=receipt_path
        ),
        patch(
            "scripts.projects.open_model_data.phase3_rule_author_runner._receipt",
            return_value={"complete": False, "canary": False, "failed_count": 1, "unparsed_count": 1},
        ),
        patch("scripts.projects.open_model_data.phase3_rule_author_runner._write_public_receipt"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["bridge"], 30.0)),
    ):
        receipt = rar.run(
            bundle_path=bundle_path,
            role_path=role_path,
            private_dir=private_dir,
            receipt_path=receipt_path,
            exact_model="gemini-3.6-flash-high",
        )
        assert receipt["failed_count"] == 1
    assert recorded_errors == ["bridge_timeout:TimeoutExpired"]


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

    with patch(
        "subprocess.run", side_effect=subprocess.TimeoutExpired(["pdftotext"], su.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS)
    ):
        with pytest.raises(su.FreezeError, match=r"pdftotext failed for sample\.pdf"):
            su.extract_pdf_pages(pdf_file, pdftotext)


# ---------------------------------------------------------------------------
# 18. phase3_v2_compatibility.py
# ---------------------------------------------------------------------------
def test_phase3_v2_compatibility_tracked_evidence_paths_timeout(tmp_path: Path) -> None:
    from scripts.projects.open_model_data import phase3_v2_compatibility as v2c

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="file1\nfile2\n")

    with (
        patch("scripts.projects.open_model_data.phase3_v2_compatibility.ROOT", tmp_path),
        patch("subprocess.run", side_effect=fake_run),
        patch.object(v2c, "_physical_k_path", return_value=tmp_path / "missing"),
    ):
        paths = v2c._tracked_evidence_paths(MagicMock(artifacts={}))
        assert paths == {"file1", "file2"}

    assert len(calls) == 1
    assert calls[0]["timeout"] == v2c.DEFAULT_GIT_TIMEOUT_SECONDS

    with (
        patch("scripts.projects.open_model_data.phase3_v2_compatibility.ROOT", tmp_path),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], v2c.DEFAULT_GIT_TIMEOUT_SECONDS)),
        patch.object(v2c, "_physical_k_path", return_value=tmp_path / "missing"),
    ):
        with pytest.raises(v2c.CompatibilityError, match="cannot enumerate tracked evidence"):
            v2c._tracked_evidence_paths(MagicMock(artifacts={}))


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
