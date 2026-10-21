"""Tests for scripts/ocr/_credentials.py — the file-backed credential loader.

These are SECURITY tests. Every test pins one behavior of the loader that
prevents a class of secret leak. If you find yourself loosening a check
("just accept 0644 — it's convenient"), STOP — file a security review
first. The whole point of this module is to refuse weak file permissions.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.ocr._credentials import (
    CredentialEmpty,
    CredentialError,
    CredentialInsecure,
    CredentialNotFound,
    load_credential,
)

SECRET = "test-mistral-api-key-XXXX"  # deliberately fake-looking; if gitleaks ever flags this, switch to "x" * 32


def _write_secret(path: Path, value: str = SECRET, mode: int = 0o600) -> Path:
    """Create a secret file with the requested mode. Caller owns cleanup."""
    path.write_text(value, encoding="utf-8")
    path.chmod(mode)
    return path


def test_load_credential_happy_path(tmp_path: Path) -> None:
    """A 0600 file with one line returns the trimmed value."""
    secret = _write_secret(tmp_path / "key", value=SECRET + "\n")
    assert load_credential(secret) == SECRET


def test_load_credential_rejects_world_readable(tmp_path: Path) -> None:
    """0644 is the default for `echo > file` on a fresh umask 0022 host.

    This is the failure mode #M-5 was designed to prevent: a casually-created
    secret file with default permissions exposes the key to every account
    on the box. The loader MUST refuse.
    """
    secret = _write_secret(tmp_path / "key", mode=0o644)
    with pytest.raises(CredentialInsecure) as exc:
        load_credential(secret)
    # The error message must include the path (so the user can fix it) but
    # NOT the secret value.
    assert str(secret) in str(exc.value)
    assert SECRET not in str(exc.value)


def test_load_credential_missing_file(tmp_path: Path) -> None:
    """Helpful error message includes the expected path + fix-it hints."""
    with pytest.raises(CredentialNotFound) as exc:
        load_credential(tmp_path / "no-such-key")
    assert "no-such-key" in str(exc.value)
    # Must include create-it instructions so the user is not stuck.
    assert "chmod 600" in str(exc.value) or "install -m 0600" in str(exc.value)


def test_load_credential_empty_file(tmp_path: Path) -> None:
    """A 0-byte file is treated as missing-credential, not silent-success."""
    secret = tmp_path / "key"
    secret.touch()
    secret.chmod(0o600)
    with pytest.raises(CredentialEmpty):
        load_credential(secret)


def test_load_credential_rejects_multiline(tmp_path: Path) -> None:
    """If user pastes a JSON blob by accident, refuse — don't send as Bearer."""
    secret = _write_secret(tmp_path / "key", value="line1\nline2\n")
    with pytest.raises(CredentialError) as exc:
        load_credential(secret)
    assert "single line" in str(exc.value).lower() or "multiple lines" in str(exc.value).lower()


def test_load_credential_error_message_never_includes_secret(tmp_path: Path) -> None:
    """Belt-and-suspenders: across every error path, error text never contains the value.

    Loops through all four expected failure modes and asserts SECRET is not
    in the exception string. The secret is what we're trying to protect; any
    code change that puts it in a log message regresses the entire module.
    """
    # missing
    missing = tmp_path / "absent"
    try:
        load_credential(missing)
    except CredentialError as exc:
        assert SECRET not in str(exc)

    # insecure mode
    insecure = _write_secret(tmp_path / "wide", mode=0o644)
    try:
        load_credential(insecure)
    except CredentialError as exc:
        assert SECRET not in str(exc)

    # empty
    empty = tmp_path / "empty"
    empty.touch()
    empty.chmod(0o600)
    try:
        load_credential(empty)
    except CredentialError as exc:
        assert SECRET not in str(exc)

    # multiline
    multi = _write_secret(tmp_path / "multi", value="a\nb")
    try:
        load_credential(multi)
    except CredentialError as exc:
        assert SECRET not in str(exc)


@pytest.mark.skipif(
    os.geteuid() == 0,
    reason="root can read everything; the uid-mismatch refusal is irrelevant",
)
def test_load_credential_refuses_foreign_owned_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a file owned by a different uid via patching os.getuid.

    Real chown across uids requires root, so we monkeypatch instead. The
    behavior we're locking in: even if mode is 0600, if the file is owned
    by someone else, refuse. (Defends against a malicious admin who chown'd
    a file into your "secret" directory to substitute their own key.)
    """
    secret = _write_secret(tmp_path / "key")
    real_uid = os.getuid()
    monkeypatch.setattr("os.getuid", lambda: real_uid + 1)
    with pytest.raises(CredentialInsecure) as exc:
        load_credential(secret)
    assert "uid" in str(exc.value).lower()
