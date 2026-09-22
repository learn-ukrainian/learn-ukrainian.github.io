"""Outcome code registry for learner state and immersion band (issue #8414).

One constant per code (failure, not_checked, report).
The CLI's --help lists them all via help_text().
No literal code strings elsewhere in this package.
"""

from __future__ import annotations

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
PENDING_STRESS = "pending_stress"

# --- Reports -----------------------------------------------------------------
UNTAUGHT_FORMS = "untaught_forms"

# --- Not Checked -------------------------------------------------------------
LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED = "lesson_structural_minimums_not_calibrated"

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
    PENDING_STRESS: "failure: resolved form has pending stress in word store",
    UNTAUGHT_FORMS: "report: forms whose grammatical category is not yet taught at this position",
    LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED: (
        "not_checked: lesson-level structural minimums are uncalibrated (module minimums apply)"
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
        PENDING_STRESS,
    }
)

REPORT_CODES = frozenset({UNTAUGHT_FORMS})

NOT_CHECKED_CODES = frozenset({LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED})


def help_text() -> str:
    """Every registered code, one per line, for the CLI's --help."""
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
