"""Independent execution/admission gates and fail-closed release readiness."""

from __future__ import annotations

import json
import os
from pathlib import Path

from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.child_runtime import _verified_file, load_profile
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, digest

EXECUTION_SWITCH = "HRAMATKA_V4_EXECUTION_ENABLED"
ADMISSION_SWITCH = "HRAMATKA_V4_ADMISSION_ENABLED"


def require_execution_enabled() -> None:
    if os.environ.get(EXECUTION_SWITCH, "0") != "1":
        raise OperationRefused("execution_disabled")


def require_admission_enabled() -> tuple[dict, str]:
    if os.environ.get(ADMISSION_SWITCH, "0") != "1":
        raise OperationRefused("admission_disabled")
    policy, policy_digest = trust.load_production_trust_policy()
    if any(not any(not key.get("revoked", False) for key in ring.values()) for ring in policy["keyrings"].values()):
        raise OperationRefused("active_trust_policy_required")
    return policy, policy_digest


def qualification_path() -> Path:
    # Existing systemd credential namespace, populated only after actual-unit canaries.
    return Path("/run/credentials/hramatka-api.service/v4-unit-qualification.json")


def require_readiness() -> None:
    from learn_ukrainian_v4_runtime.provenance import verify_current_identity

    try:
        identity = verify_current_identity()
        profile = load_profile()
        _verified_file(profile["bwrap"], profile["bwrap_sha256"])
        _, policy_digest = trust.load_production_trust_policy()
        qualification = json.loads(qualification_path().read_bytes())
        if (
            qualification.get("schema") != "hramatka-v4-actual-unit-qualification.v1"
            or qualification.get("unit") != "hramatka-api.service"
            or qualification.get("sources_unit") != "learn-ukrainian-sources.service"
            or qualification.get("package_manifest_sha256") != identity["release_manifest_sha256"]
            or qualification.get("trust_policy_sha256") != policy_digest
            or qualification.get("child_profile_sha256")
            != digest(
                __import__("learn_ukrainian_v4_runtime.child_runtime", fromlist=["profile_path"])
                .profile_path()
                .read_bytes()
            )
            or set(qualification.get("canaries", {}))
            != {"bwrap", "unit_hardening", "credential_separation", "scoped_database_roles"}
            or any(value is not True for value in qualification["canaries"].values())
        ):
            raise OperationRefused("actual_unit_qualification_required")
        for credential in ("v4-control-dsn", "v4-fleet_execution", "v4-sources_verifier", "v4-a3_reference"):
            path = qualification_path().parent / credential
            if not path.is_file() or path.is_symlink() or path.stat().st_mode & 0o077:
                raise OperationRefused("scoped_custody_required")
    except (OSError, KeyError, ValueError) as exc:
        raise OperationRefused("readiness_unproved") from exc
