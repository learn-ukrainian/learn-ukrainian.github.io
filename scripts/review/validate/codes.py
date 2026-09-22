"""Rejection codes for the active review validator.

``--help`` prints this registry. No literal code strings elsewhere in the package.
"""

from __future__ import annotations

MANIFEST_HASH_MISMATCH = "manifest_hash_mismatch"
MANIFEST_UNREADABLE = "manifest_unreadable"
RECEIPT_NOT_IN_LEDGER = "receipt_not_in_ledger"
LEDGER_UNREADABLE = "ledger_unreadable"
EXPECTED_NOT_IN_RESULT = "expected_not_in_result"
QUOTE_EMPTY = "quote_empty"
QUOTE_NOT_IN_UNIT = "quote_not_in_unit"
LOCATION_NOT_IN_LESSON = "location_not_in_lesson"
LOCATION_INCOMPLETE = "location_incomplete"
SCOPE_MISSING = "scope_missing"
UNSUPPORTED_WITHOUT_SEARCHES = "unsupported_without_searches"
UNSUPPORTED_SEVERITY_ABOVE_MINOR = "unsupported_severity_above_minor"
OUTCOME_NOT_IN_LEDGER = "outcome_not_in_ledger"
LANGUAGE_SUB_DIMENSION_MISSING = "language_sub_dimension_missing"
SUB_DIMENSION_INVALID = "sub_dimension_invalid"
CHECK_MISSING = "check_missing"
CHECK_NOT_APPLICABLE = "check_not_applicable"
FINDING_NOT_REFERENCED = "finding_not_referenced"
DANGLING_CHECK_REFERENCE = "dangling_check_reference"
DUPLICATE_FINDING_ID = "duplicate_finding_id"
EVIDENCE_BRANCH_COUNT = "evidence_branch_count"
SCHEMA_INVALID = "schema_invalid"
LESSON_UNREADABLE = "lesson_unreadable"
REVIEW_UNREADABLE = "review_unreadable"

DESCRIPTIONS: dict[str, str] = {
    MANIFEST_HASH_MISMATCH: "failure: attempt.manifest_sha256 is not the sha256 of the manifest file bytes",
    MANIFEST_UNREADABLE: "failure: the manifest file is missing or not a YAML mapping",
    RECEIPT_NOT_IN_LEDGER: "failure: a cited receipt is not in this attempt (or the previous attempt, for resolved/persisting)",
    LEDGER_UNREADABLE: "failure: the ledger or its sha256 sidecar is missing, mismatched, or malformed",
    EXPECTED_NOT_IN_RESULT: "failure: expected is not a substring of any cited receipt's stored result",
    QUOTE_EMPTY: "failure: a location quote is empty after NFC and stress-stripping",
    QUOTE_NOT_IN_UNIT: "failure: the quote does not occur inside the named tab, activity, and item",
    LOCATION_NOT_IN_LESSON: "failure: the named tab, activity, or item is not in the expanded lesson",
    LOCATION_INCOMPLETE: "failure: an exercise-tab location lacks activity or item",
    SCOPE_MISSING: "failure: an absence finding (locations: []) has no scope",
    UNSUPPORTED_WITHOUT_SEARCHES: "failure: unsupported_by_source has no search receipts",
    UNSUPPORTED_SEVERITY_ABOVE_MINOR: "failure: unsupported_by_source finding has severity above MINOR (capped at MINOR)",
    OUTCOME_NOT_IN_LEDGER: "failure: the claimed search outcome is not shown by the stored result and status",
    LANGUAGE_SUB_DIMENSION_MISSING: "failure: a language finding has no sub_dimension",

    SUB_DIMENSION_INVALID: "failure: sub_dimension is not in the taxonomy list for language",
    CHECK_MISSING: "failure: a taxonomy check for this kind is neither clean nor a list of finding ids",
    CHECK_NOT_APPLICABLE: "failure: a recap-only check is present on a review whose manifest is not a recap",
    FINDING_NOT_REFERENCED: "failure: a finding id is not listed under exactly one applicable check",
    DANGLING_CHECK_REFERENCE: "failure: a check lists a finding id that is not in findings",
    DUPLICATE_FINDING_ID: "failure: a finding id is repeated",
    EVIDENCE_BRANCH_COUNT: "failure: a finding does not have exactly one evidence branch",
    SCHEMA_INVALID: "failure: the review document does not match schemas/review-v1.schema.json",
    LESSON_UNREADABLE: "failure: the expanded lesson is missing or has no units list",
    REVIEW_UNREADABLE: "failure: the review file is missing or not a YAML mapping",
}


def help_text() -> str:
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
