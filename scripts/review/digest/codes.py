"""Outcome code registry for module digest generator (#8430 WP 15 Part R2a).

Every CLI error names one registered code. CLI consumers render DESCRIPTIONS in help.
No literal code strings elsewhere in this package.
"""

from __future__ import annotations

from scripts.curriculum.evidence import codes as evidence_codes

LOCK_MISMATCH = evidence_codes.LOCK_MISMATCH
PLAN_MISSING = "plan_missing"
PLAN_INVALID = "plan_invalid"
LESSON_NOT_IN_PLAN = "lesson_not_in_plan"
PROVENANCE_MISSING = "provenance_missing"
PROVENANCE_INVALID = "provenance_invalid"
OBSERVED_MISSING = "observed_missing"
OBSERVED_INVALID = "observed_invalid"
RESOLUTIONS_MISSING = "resolutions_missing"
RESOLUTIONS_INVALID = "resolutions_invalid"
MDX_MISSING = "mdx_missing"
UNIT_NOT_IN_PROVENANCE = "unit_not_in_provenance"
RECORD_NOT_IN_OBSERVED = "record_not_in_observed"
BYTE_DRIFT = "byte_drift"
DIGEST_SCHEMA_INVALID = "digest_schema_invalid"
DIGEST_FILE_MISSING = "digest_file_missing"
INVALID_ARGUMENT = "invalid_argument"
PATH_FORBIDDEN = "path_forbidden"

DESCRIPTIONS: dict[str, str] = {
    LOCK_MISMATCH: "failure: file bytes disagree with the lock sidecar or lock is missing",
    PLAN_MISSING: "failure: requested module plan file does not exist",
    PLAN_INVALID: "failure: module plan file is invalid YAML or breaks schema",
    LESSON_NOT_IN_PLAN: "failure: requested lesson number does not exist in module plan",
    PROVENANCE_MISSING: "failure: lesson provenance file does not exist",
    PROVENANCE_INVALID: "failure: lesson provenance file is invalid YAML or malformed",
    OBSERVED_MISSING: "failure: lesson observed state file does not exist",
    OBSERVED_INVALID: "failure: lesson observed state file is invalid YAML or breaks schema",
    RESOLUTIONS_MISSING: "failure: lesson resolutions receipts file does not exist",
    RESOLUTIONS_INVALID: "failure: lesson resolutions receipts file is invalid YAML or breaks schema",
    MDX_MISSING: "failure: lesson MDX file does not exist",
    UNIT_NOT_IN_PROVENANCE: "failure: token unit locator is not present in provenance spans",
    RECORD_NOT_IN_OBSERVED: "failure: token word record is not found in observed index records",
    BYTE_DRIFT: "failure: digest file on disk disagrees with recomputed bytes (--check)",
    DIGEST_SCHEMA_INVALID: "failure: generated digest breaks module-digest-v1 schema",
    DIGEST_FILE_MISSING: "failure: digest file or lock sidecar does not exist on disk (--check)",
    INVALID_ARGUMENT: "failure: CLI invocation arguments are invalid",
    PATH_FORBIDDEN: "failure: requested path or argument violates isolation boundaries or escapes expected root",
}


def help_text() -> str:
    """Every registered outcome code, one per line, for the CLI's --help."""
    return "\n".join(f"  {code}: {description}" for code, description in sorted(DESCRIPTIONS.items()))
