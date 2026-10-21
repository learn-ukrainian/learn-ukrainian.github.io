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


def test_no_operator_secrets_or_hosts(copy_text: str, verify_text: str) -> None:
    blob = copy_text + "\n" + verify_text
    assert "kriszpc" not in blob.lower()
    assert "@gmail.com" not in blob.lower()
    assert re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", blob) is None
    assert re.search(
        r"(?:/Users|/home)/[A-Za-z0-9._-]+/projects/learn-ukrainian",
        blob,
    ) is None
