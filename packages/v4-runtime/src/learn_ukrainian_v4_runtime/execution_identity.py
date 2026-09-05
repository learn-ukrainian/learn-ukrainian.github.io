"""The private verified vendor manifest anchors current execution identity.

The startup adapter supplies a verifier, never an HTTP caller. It must run the
existing private vendor verification and compare wheel/installed digests before
returning this proof. No public argument chooses a provenance registry or path.
"""

from __future__ import annotations

import re
from typing import Protocol

from learn_ukrainian_v4_runtime.operation_auth import OperationRefused
from learn_ukrainian_v4_runtime.provenance import verify_current_identity


class VerifiedReleaseProvider(Protocol):
    def verify(self, installed_identity: dict) -> dict:
        """Return current identity plus wheel_sha256 after private vendor verification."""
        ...


def execution_identity(provider: VerifiedReleaseProvider) -> dict:
    current = verify_current_identity()
    verified = provider.verify(current)
    validate_execution_identity(verified)
    if {key: value for key, value in verified.items() if key != "wheel_sha256"} != current:
        raise OperationRefused("verified_vendor_install_mismatch")
    return verified


def validate_execution_identity(proof: dict) -> None:
    expected = {
        "public_commit",
        "package_version",
        "wheel_sha256",
        "release_manifest_sha256",
        "provenance_manifest_sha256",
        "installed_files",
    }
    if not isinstance(proof, dict) or set(proof) != expected:
        raise OperationRefused("execution_release_identity_required")
    if not isinstance(proof["public_commit"], str) or not re.fullmatch("[a-f0-9]{40}", proof["public_commit"]):
        raise OperationRefused("execution_public_commit")
    if not isinstance(proof["package_version"], str) or not proof["package_version"]:
        raise OperationRefused("execution_package_version")
    for name in ("wheel_sha256", "release_manifest_sha256", "provenance_manifest_sha256"):
        if not isinstance(proof[name], str) or not re.fullmatch("[a-f0-9]{64}", proof[name]):
            raise OperationRefused("execution_release_digest")
    files = proof["installed_files"]
    if not isinstance(files, dict) or not {
        "release_manifest.json",
        "_build_identity.py",
        "provenance/v1/manifest.json",
    } <= set(files):
        raise OperationRefused("execution_installed_files")
    from learn_ukrainian_v4_runtime.resources import safe_relative

    for name, sha in files.items():
        safe_relative(name)
        if not isinstance(sha, str) or not re.fullmatch("[a-f0-9]{64}", sha):
            raise OperationRefused("execution_installed_digest")
    if (
        files["release_manifest.json"] != proof["release_manifest_sha256"]
        or files["provenance/v1/manifest.json"] != proof["provenance_manifest_sha256"]
    ):
        raise OperationRefused("execution_manifest_binding")

    current = verify_current_identity()
    if {key: value for key, value in proof.items() if key != "wheel_sha256"} != current:
        raise OperationRefused("execution_identity_does_not_match_installed_release")
