"""Hermetic checks for Windows storage copy/verify scripts (text-level proofs)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WINDOWS_DIR = REPO_ROOT / "scripts" / "storage" / "windows"
COPY_SCRIPT = WINDOWS_DIR / "Copy-BulkSourcesFromDrive.ps1"
VERIFY_SCRIPT = WINDOWS_DIR / "Verify-BulkSources.ps1"


@pytest.fixture(scope="module")
def copy_text() -> str:
    return COPY_SCRIPT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def verify_text() -> str:
    return VERIFY_SCRIPT.read_text(encoding="utf-8")


def test_scripts_exist() -> None:
    assert COPY_SCRIPT.is_file()
    assert VERIFY_SCRIPT.is_file()


def test_copy_uses_rclone_copy_not_sync(copy_text: str) -> None:
    # Primary invocation is rclone copy (first positional arg).
    assert re.search(r"""['\"]copy['\"]""", copy_text)
    assert "rclone" in copy_text.lower() or "Rclone" in copy_text
    # Forbidden destructive *invocations* (comments may say "never sync/purge").
    forbidden = [
        r"\brclone\.exe\s+sync\b",
        r"\brclone\s+sync\b",
        r"""['\"]sync['\"]""",
        r"""['\"]purge['\"]""",
        r"--delete(?:-during|-after|-before)?\b",
        r"\bRemove-Item\b",
        r"\brmdir\b",
    ]
    for pattern in forbidden:
        assert re.search(pattern, copy_text, flags=re.IGNORECASE) is None, pattern
    # Documented non-destructive posture.
    assert "never" in copy_text.lower() and "sync" in copy_text.lower()


def test_copy_resolves_destination_via_get_smbshare_local_ntfs(copy_text: str) -> None:
    assert "Get-SmbShare" in copy_text
    assert "DriveFormat" in copy_text
    assert "NTFS" in copy_text
    assert "StartsWith('\\\\')" in copy_text or 'StartsWith("\\\\")' in copy_text
    # Share name is conventional; no frozen Phase 3 run IDs.
    assert "UkrainianData" in copy_text
    assert "phase3-storage-migration" not in copy_text.lower()
    assert "20260815" not in copy_text


def test_copy_is_resumable_idempotent_flags(copy_text: str) -> None:
    # checksum + copy semantics skip identical files; retries support resume.
    assert "--checksum" in copy_text
    assert "--retries" in copy_text
    assert "BULK_COPY_COMPLETE" in copy_text
    # Copy must not mint the success receipt itself.
    assert "BULK_SOURCES_VERIFIED" not in copy_text
    assert "Set-Content" not in copy_text or "receipt" not in copy_text.lower()


def test_verify_receipt_only_after_success(verify_text: str) -> None:
    assert "Get-SmbShare" in verify_text
    assert "NTFS" in verify_text
    assert "BULK_SOURCES_VERIFIED" in verify_text
    assert "BULK_SOURCES_VERIFY_FAILED" in verify_text
    # Receipt write is gated on $passed / success path.
    assert re.search(r"if\s*\(\s*-not\s*\$passed\s*\)", verify_text)
    assert "Set-Content" in verify_text
    # Ensure failure path exits before success receipt language.
    fail_idx = verify_text.index("BULK_SOURCES_VERIFY_FAILED")
    success_write_idx = verify_text.index("Set-Content")
    # There may be only one Set-Content (success receipt). Failure must exit 1.
    assert "exit 1" in verify_text
    assert fail_idx < success_write_idx
    # No deletion of payload.
    assert re.search(r"\bRemove-Item\b", verify_text) is None
    assert re.search(r"\brclone\s+sync\b", verify_text, flags=re.IGNORECASE) is None


def test_verify_rejects_unc_and_requires_markers(verify_text: str) -> None:
    assert "literary_texts" in verify_text
    assert "textbook_chunks" in verify_text
    assert "not UNC" in verify_text or "refuse network" in verify_text.lower()
    assert "reparse" in verify_text.lower()
    assert "phase3-storage-migration" not in verify_text.lower()
    assert "3187bdff0d41ed213e9d653e2f53b49bd46086f6f5f7daa49a47217ad71b24ec" not in verify_text


def test_verify_destination_is_local_ntfs_derived_from_drive_format(
    verify_text: str,
) -> None:
    """Receipt field must come from DriveFormat, not a hardcoded $true."""
    assert "DriveFormat" in verify_text
    assert re.search(
        r"\$destinationIsLocalNtfs\s*=\s*\(\s*\$payloadDrive\.DriveFormat\s+-ceq\s*'NTFS'\s*\)",
        verify_text,
    )
    assert re.search(
        r"destination_is_local_ntfs\s*=\s*\$destinationIsLocalNtfs",
        verify_text,
    )
    # Must not hardcode the receipt boolean independently of the format check.
    assert not re.search(
        r"destination_is_local_ntfs\s*=\s*\$true\b",
        verify_text,
    )
    # Fail closed when the payload root is not NTFS.
    assert "not backed by local NTFS" in verify_text


def test_no_operator_secrets_or_hosts(copy_text: str, verify_text: str) -> None:
    blob = copy_text + "\n" + verify_text
    assert "kriszpc" not in blob.lower()
    assert "@gmail.com" not in blob.lower()
    assert re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", blob) is None
    assert re.search(
        r"(?:/Users|/home)/[A-Za-z0-9._-]+/projects/learn-ukrainian",
        blob,
    ) is None
