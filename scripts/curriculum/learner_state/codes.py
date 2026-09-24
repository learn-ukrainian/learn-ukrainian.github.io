"""Outcome code registry for learner state and immersion band (issue #8414).

One constant per code (failure, not_checked, report).
The CLI's --help lists them all via help_text().
No literal code strings elsewhere in this package.
"""

from __future__ import annotations

from scripts.curriculum.evidence import codes as evidence_codes

# --- Failures: input and plan discovery --------------------------------------
PLAN_NOT_FOUND = "plan_not_found"
PLAN_YAML_INVALID = "plan_yaml_invalid"
PRIOR_PLANS_MISSING = "prior_plans_missing"
POSITION_NOT_FOUND = "position_not_found"
LESSON_NOT_FOUND = "lesson_not_found"

# --- Failures: base layer contract -------------------------------------------
BASE_LAYER_MISSING = "base_layer_missing"
BASE_LAYER_UNRESOLVED = "base_layer_unresolved"

# --- Failures: learner state rules -------------------------------------------
BARE_LEMMA = "bare_lemma"

# --- Failures: immersion band ------------------------------------------------
ARC_BAND_TABLE_MISSING = "arc_band_table_missing"
ULP_DERIVATION_DISABLED = "ulp_derivation_disabled"
ULP_IMMERSION_DERIVATION_DISABLED = ULP_DERIVATION_DISABLED
CUMULATIVE_CORE_COUNT_MISSING = "cumulative_core_count_missing"
CUMULATIVE_COUNT_MISSING = CUMULATIVE_CORE_COUNT_MISSING

# --- Failures: Part 2 inventory gate (registered for Part 2 SSOT) ------------
LEMMA_OUTSIDE_STATE = "lemma_outside_state"
CORE_NOT_INTRODUCED = "core_not_introduced"
RECYCLED_NOT_USED = "recycled_not_used"
TAUGHT_FORM_ABSENT = "taught_form_absent"
TOKEN_UNRESOLVED = "token_unresolved"
GLOSS_RECORD_MISSING = "gloss_record_missing"
PENDING_STRESS = "pending_stress"

# --- Failures: expanded document ---------------------------------------------
EXPANDED_DOCUMENT_MISSING = "expanded_document_missing"
EXPANDED_DOCUMENT_MISMATCH = "expanded_document_mismatch"
INPUT_HASH_MISSING = "input_hash_missing"

# --- Failures: observed index and resolutions receipts -----------------------
RESOLUTIONS_NOT_FOUND = "resolutions_not_found"
RESOLUTIONS_INVALID = "resolutions_invalid"
OBSERVED_SCHEMA_INVALID = "observed_schema_invalid"
OBSERVED_YAML_INVALID = "observed_yaml_invalid"
LOCK_MISMATCH = evidence_codes.LOCK_MISMATCH
UNKNOWN_TAB = "unknown_tab"

# --- Reports -----------------------------------------------------------------
UNTAUGHT_FORMS = "untaught_forms"
STRESS_CERTAIN_IDENTITY_OPEN = "stress_certain_identity_open"

# --- Not Checked -------------------------------------------------------------
LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED = "lesson_structural_minimums_not_calibrated"
INTRODUCING_STEP_NOT_LOCATABLE = "introducing_step_not_locatable"
WAIVER_PRIOR_PLANS_MISSING = "prior_plans_missing_waived"

# --- Descriptions for --help and reporting -----------------------------------
DESCRIPTIONS: dict[str, str] = {
    PLAN_NOT_FOUND: "failure: requested module plan file does not exist",
    PLAN_YAML_INVALID: "failure: module plan file is not valid YAML",
    PRIOR_PLANS_MISSING: "failure: missing plan(s) for earlier arc position(s)",
    POSITION_NOT_FOUND: "failure: requested arc position does not exist in arc",
    LESSON_NOT_FOUND: "failure: requested lesson number does not exist in plan",
    BASE_LAYER_MISSING: "failure: _base.request.yaml or its records are missing",
    BASE_LAYER_UNRESOLVED: "failure: base layer request line matched zero or multiple word store records",
    BARE_LEMMA: "failure (rule 1): bare Ukrainian lemma found in state instead of word store ID",
    ARC_BAND_TABLE_MISSING: "failure: arc position has no band_key defined in _arc.yaml",
    ULP_DERIVATION_DISABLED: "failure: USE_ULP_IMMERSION_DERIVATION is disabled for A1 immersion calculation",
    CUMULATIVE_CORE_COUNT_MISSING: "failure: cumulative_core_count is required for A1 immersion band computation",
    LEMMA_OUTSIDE_STATE: "failure: token resolves to a lemma outside allowed learner state",
    CORE_NOT_INTRODUCED: "failure: core vocabulary item declared in plan is not introduced in lesson",
    RECYCLED_NOT_USED: "failure: recycled vocabulary item declared in plan is not used in lesson",
    TAUGHT_FORM_ABSENT: "failure: taught form declared in plan does not appear in a teaching position",
    TOKEN_UNRESOLVED: "failure: token is outside allowlist or unclassifiable in resolution stream",
    GLOSS_RECORD_MISSING: "failure: gloss token refers to a record absent from word store",
    PENDING_STRESS: "failure: resolved form has pending stress in word store",
    EXPANDED_DOCUMENT_MISSING: "failure: expanded document file does not exist or failed to load",
    EXPANDED_DOCUMENT_MISMATCH: "failure: expanded document sha256 disagrees with receipts inputs or lock",
    INPUT_HASH_MISSING: "failure: in-memory stream has no inputs for hash verification",
    RESOLUTIONS_NOT_FOUND: "failure: lesson resolutions receipts file does not exist",
    RESOLUTIONS_INVALID: "failure: lesson resolutions receipts file is invalid or tampered",
    OBSERVED_SCHEMA_INVALID: "failure: observed index document breaks learner-observed-v1 schema",
    OBSERVED_YAML_INVALID: "failure: observed index YAML is invalid",
    LOCK_MISMATCH: "failure: file bytes disagree with lock sidecar",
    UNKNOWN_TAB: "failure: token occurrence has unknown tab outside urok|slovnyk|vpravy|resursy",
    UNTAUGHT_FORMS: "report: forms whose grammatical category is not yet taught at this position",
    STRESS_CERTAIN_IDENTITY_OPEN: ("report: several records share one stressed spelling; non-blocking open question"),
    LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED: (
        "not_checked: lesson-level structural minimums are uncalibrated (module minimums apply)"
    ),
    INTRODUCING_STEP_NOT_LOCATABLE: (
        "not_checked: introducing step cannot be located until expanded-document units carry step id"
    ),
    WAIVER_PRIOR_PLANS_MISSING: (
        "not_checked: missing plan(s) for earlier arc position(s) waived"
    ),
}

FAILURE_CODES = frozenset(
    {
        PLAN_NOT_FOUND,
        PLAN_YAML_INVALID,
        PRIOR_PLANS_MISSING,
        POSITION_NOT_FOUND,
        LESSON_NOT_FOUND,
        BASE_LAYER_MISSING,
        BASE_LAYER_UNRESOLVED,
        BARE_LEMMA,
        ARC_BAND_TABLE_MISSING,
        ULP_DERIVATION_DISABLED,
        CUMULATIVE_CORE_COUNT_MISSING,
        LEMMA_OUTSIDE_STATE,
        CORE_NOT_INTRODUCED,
        RECYCLED_NOT_USED,
        TAUGHT_FORM_ABSENT,
        TOKEN_UNRESOLVED,
        GLOSS_RECORD_MISSING,
        PENDING_STRESS,
        EXPANDED_DOCUMENT_MISSING,
        EXPANDED_DOCUMENT_MISMATCH,
        INPUT_HASH_MISSING,
        RESOLUTIONS_NOT_FOUND,
        RESOLUTIONS_INVALID,
        OBSERVED_SCHEMA_INVALID,
        OBSERVED_YAML_INVALID,
        LOCK_MISMATCH,
        UNKNOWN_TAB,
    }
)

REPORT_CODES = frozenset({UNTAUGHT_FORMS, STRESS_CERTAIN_IDENTITY_OPEN})

NOT_CHECKED_CODES = frozenset(
    {
        LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED,
        INTRODUCING_STEP_NOT_LOCATABLE,
        WAIVER_PRIOR_PLANS_MISSING,
    }
)


def help_text() -> str:
    """Every registered code, one per line, for the CLI's --help."""
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
