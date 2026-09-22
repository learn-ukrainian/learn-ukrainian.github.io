"""Outcome code registry for the single-plan validator (issue #8412, Brief A).

One constant per failure code, per note code and per not_checked code, each
with a one-line description. Nothing else in this package spells a code as a
string literal; the CLI's --help lists them all via help_text(). Every code
here is produced by at least one test fixture — codes that only Brief B can
produce (waivers, arc-side not_checked) are registered there, not here.
"""

# --- input and loader failures -------------------------------------------
PLAN_NOT_FOUND = "plan_not_found"
PLAN_YAML_INVALID = "plan_yaml_invalid"
PLAN_OUTSIDE_LESSON_PLANS = "plan_outside_lesson_plans"
NOT_A_PLAN = "not_a_plan"
V1_PLAN = "v1_plan"
REMOVED_V1_FIELD = "removed_v1_field"
SCOPE_KEY_IN_PLAN = "scope_key_in_plan"
SCHEMA_VIOLATION = "schema_violation"

# --- pack and word store failures ----------------------------------------
PACK_NOT_FOUND = "pack_not_found"
PACK_YAML_INVALID = "pack_yaml_invalid"
PACK_MALFORMED = "pack_malformed"
PACK_WORDS_LIST_PRESENT = "pack_words_list_present"
DUPLICATE_PACK_ID = "duplicate_pack_id"
PACK_LOCK_MISMATCH = "pack_lock_mismatch"
PACK_HASH_MISMATCH = "pack_hash_mismatch"
WORDS_NOT_FOUND = "words_not_found"
WORDS_YAML_INVALID = "words_yaml_invalid"
WORDS_MALFORMED = "words_malformed"
DUPLICATE_WORD_ID = "duplicate_word_id"
WORDS_LOCK_MISMATCH = "words_lock_mismatch"

# --- rule 1 (lessons, closing shape, kinds) -------------------------------
LESSONS_EMPTY = "lessons_empty"
LESSON_N_NOT_CONTIGUOUS = "lesson_n_not_contiguous"
CLOSING_SHAPE_INVALID = "closing_shape_invalid"
CLOSES_WITH_RECAP_NOT_LAST = "closes_with_recap_not_last"
TEACH_STEP_OUTSIDE_TEACH_LESSON = "teach_step_outside_teach_lesson"
NON_TEACH_LESSON_INTRODUCES = "non_teach_lesson_introduces"
CHECKPOINT_STEP_KIND = "checkpoint_step_kind"
INTRODUCES_ON_NON_TEACH_STEP = "introduces_on_non_teach_step"

# --- inventory equals declared introductions ------------------------------
INTRODUCED_TWICE = "introduced_twice"
INVENTORY_INTRODUCTION_MISMATCH = "inventory_introduction_mismatch"

# --- within-lesson order and recycled (the single-plan part of rule 4) ----
USES_BEFORE_INTRODUCTION = "uses_before_introduction"
USES_NOT_RECYCLED = "uses_not_recycled"
RECYCLED_NOT_USED = "recycled_not_used"
RECYCLED_INTRODUCED_HERE = "recycled_introduced_here"

# --- rule 3 (evidence resolves; pack is the locked one) --------------------
UNKNOWN_PACK_ID = "unknown_pack_id"
UNKNOWN_WORD_ID = "unknown_word_id"

# --- rule 6 (steps and activities) -----------------------------------------
TEACH_STEP_WITHOUT_PRACTICE = "teach_step_without_practice"
UNKNOWN_ACTIVITY_ID = "unknown_activity_id"
DUPLICATE_ACTIVITY_ID = "duplicate_activity_id"
DUPLICATE_STEP_ID = "duplicate_step_id"
UNKNOWN_ACTIVITY_TYPE = "unknown_activity_type"
ACTIVITY_SCHEMA_UNAVAILABLE = "activity_schema_unavailable"
ACTIVITY_SCHEMA_MALFORMED = "activity_schema_malformed"

# --- rule 7 (no Ukrainian facts in a plan) ---------------------------------
LEMMA_MISMATCH = "lemma_mismatch"
UNKNOWN_FORM_TAG = "unknown_form_tag"
INCIDENTAL_FORMS_PRESENT = "incidental_forms_present"
CYRILLIC_IN_DISALLOWED_FIELD = "cyrillic_in_disallowed_field"
STRESS_MARK_IN_PLAN = "stress_mark_in_plan"

# --- revision 9 fields ------------------------------------------------------
DIALOGUE_STEP_MISSING = "dialogue_step_missing"
DIALOGUE_STEP_UNKNOWN = "dialogue_step_unknown"
SPEAKER_EVIDENCE_MISSING = "speaker_evidence_missing"
NEED_KIND_UNSATISFIED = "need_kind_unsatisfied"
DUPLICATE_PARADIGM_ID = "duplicate_paradigm_id"
ERROR_REFS_MISSING = "error_refs_missing"
ERROR_REFS_FORBIDDEN = "error_refs_forbidden"
ERROR_REF_NOT_ERROR_RECORD = "error_ref_not_error_record"

# --- notes (never fail the run) ---------------------------------------------
CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW = "closing_shape_b_needs_plan_review"

# --- not_checked (never fail the run, always reported) ----------------------
MINUTES_CONSTANTS_UNDEFINED = "minutes_constants_undefined"
WORD_TARGET_NOT_CALIBRATED = "word_target_not_calibrated"
LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED = "lesson_activity_minimums_not_calibrated"
CROSS_PLAN_RULES_PENDING = "cross_plan_rules_pending"

DESCRIPTIONS = {
    PLAN_NOT_FOUND: "failure: the plan file does not exist",
    PLAN_YAML_INVALID: "failure: the plan file is not valid YAML",
    PLAN_OUTSIDE_LESSON_PLANS: "failure: plans live under curriculum/l2-uk-en/lesson-plans/<level>/, nowhere else",
    NOT_A_PLAN: "failure: a name beginning with _ is not a plan (§2a)",
    V1_PLAN: "failure: v1 plans are not read or converted (§7.4)",
    REMOVED_V1_FIELD: "failure: a v1 field was removed from the plan; the message says where it moved",
    SCOPE_KEY_IN_PLAN: "failure: scope is a generated sidecar (_scope/<slug>.yaml), never a plan key (§2a)",
    SCHEMA_VIOLATION: "failure: the plan fails schemas/module-plan-v2.schema.json",
    PACK_NOT_FOUND: "failure: the module evidence pack does not exist",
    PACK_YAML_INVALID: "failure: the pack file is not valid YAML",
    PACK_MALFORMED: "failure: a pack record list is malformed (not a list, or a record without an id)",
    PACK_WORDS_LIST_PRESENT: "failure: a module pack holds no words: list; words live in the level word store (§3)",
    DUPLICATE_PACK_ID: "failure: a record id appears twice in the module pack",
    PACK_LOCK_MISMATCH: "failure: the pack file's bytes disagree with its .lock sidecar",
    PACK_HASH_MISMATCH: "failure: the pack file's sha256 disagrees with the plan's evidence_ref.sha256",
    WORDS_NOT_FOUND: "failure: the level word store does not exist",
    WORDS_YAML_INVALID: "failure: the word store file is not valid YAML",
    WORDS_MALFORMED: "failure: a word record is malformed (missing id, lemma or forms)",
    DUPLICATE_WORD_ID: "failure: a word id appears twice in the level word store",
    WORDS_LOCK_MISMATCH: "failure: the word store's bytes disagree with its .lock sidecar",
    LESSONS_EMPTY: "failure (rule 1): lessons is empty",
    LESSON_N_NOT_CONTIGUOUS: "failure (rule 1): lesson n values are not 1..N contiguous",
    CLOSING_SHAPE_INVALID: "failure (rule 1): the module closes in neither allowed shape (recap lesson, or teach + closes_with_recap)",
    CLOSES_WITH_RECAP_NOT_LAST: "failure (rule 1): closes_with_recap appears on a lesson that is not the last",
    TEACH_STEP_OUTSIDE_TEACH_LESSON: "failure (§2a): a teach step exists outside a teach lesson",
    NON_TEACH_LESSON_INTRODUCES: "failure (§2a): a practice/recap/checkpoint lesson has a non-empty phonetics, grammar or vocabulary.core",
    CHECKPOINT_STEP_KIND: "failure (§2a): a checkpoint lesson has a step that is not practice",
    INTRODUCES_ON_NON_TEACH_STEP: "failure (§2a): a practice or recap step carries a non-empty introduces",
    INTRODUCED_TWICE: "failure (§2a): an item is introduced by two steps of the same lesson",
    INVENTORY_INTRODUCTION_MISMATCH: "failure (§2a): the lesson inventory and the union of its steps' introduces differ",
    USES_BEFORE_INTRODUCTION: "failure (rule 4, single-plan part): a step uses an id a later step of the same lesson introduces",
    USES_NOT_RECYCLED: "failure (§2a): a used vocabulary id is neither introduced by the lesson nor listed in recycled",
    RECYCLED_NOT_USED: "failure (§2a): a recycled id is used by no step",
    RECYCLED_INTRODUCED_HERE: "failure (§2a): a recycled id is introduced by the same lesson",
    UNKNOWN_PACK_ID: "failure (rule 3): an evidence/model/error_refs id does not exist in the module pack",
    UNKNOWN_WORD_ID: "failure (rule 3): a W-… id does not exist in the level word store",
    TEACH_STEP_WITHOUT_PRACTICE: "failure (rule 6): a teach step lists no practice activity",
    UNKNOWN_ACTIVITY_ID: "failure (rule 6): a referenced activity id is not defined in the lesson",
    DUPLICATE_ACTIVITY_ID: "failure (rule 6): an activity id appears twice in the same lesson",
    DUPLICATE_STEP_ID: "failure (rule 6): a step id appears twice in the same lesson",
    UNKNOWN_ACTIVITY_TYPE: "failure (rule 6): an activity type is not in the level allowlist",
    ACTIVITY_SCHEMA_UNAVAILABLE: "failure (rule 6): schemas/activities-<level>.schema.json is missing; no fallback to another level",
    ACTIVITY_SCHEMA_MALFORMED: "failure (rule 6): an activity definition key lacks the -<level> suffix; no fallback to another level",
    LEMMA_MISMATCH: "failure (rule 7): an inventory lemma differs from the word-store record's lemma",
    UNKNOWN_FORM_TAG: "failure (rule 7): a forms tag does not exist in the word-store record",
    INCIDENTAL_FORMS_PRESENT: "failure (rule 7, r8): an incidental entry carries forms; incidental words are not taught or drilled",
    CYRILLIC_IN_DISALLOWED_FIELD: "failure (rule 7): Cyrillic text in a field outside the allowed prose list",
    STRESS_MARK_IN_PLAN: "failure (rule 7): U+0301 or U+0300 in the plan file; stress lives in the word store",
    DIALOGUE_STEP_MISSING: "failure (r9): a dialogue block carries no step id",
    DIALOGUE_STEP_UNKNOWN: "failure (r9): a dialogue's step id is not a step of the same lesson",
    SPEAKER_EVIDENCE_MISSING: "failure (r9): a dialogue speaker carries no word-store evidence id",
    NEED_KIND_UNSATISFIED: "failure (r9): a step's needs entry has no matching evidence record in the step",
    DUPLICATE_PARADIGM_ID: "failure (r9): a paradigm id appears twice in the same lesson",
    ERROR_REFS_MISSING: "failure (r9): an error-correction activity carries no error_refs",
    ERROR_REFS_FORBIDDEN: "failure (r9): error_refs on an activity whose type is not error-correction",
    ERROR_REF_NOT_ERROR_RECORD: "failure (r9): an error_refs id exists in the pack but is not an E- error record",
    CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW: "note (rule 1b): the teach + closes_with_recap closing shape is used; the plan review must confirm it",
    MINUTES_CONSTANTS_UNDEFINED: "not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)",
    WORD_TARGET_NOT_CALIBRATED: "not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)",
    LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED: "not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)",
    CROSS_PLAN_RULES_PENDING: "not_checked: rules 4 and 5, the grammar registry, the scope sidecar and the title check are Brief B",
}

NOTE_CODES = frozenset({CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW})
NOT_CHECKED_CODES = frozenset(
    {
        MINUTES_CONSTANTS_UNDEFINED,
        WORD_TARGET_NOT_CALIBRATED,
        LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED,
        CROSS_PLAN_RULES_PENDING,
    }
)


def help_text() -> str:
    """Every registered code, one per line, for the CLI's --help."""
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
