"""Outcome code registry for the plan validator (issue #8412, Briefs A and B).

One constant per failure code, per note code and per not_checked code, each
with a one-line description. Nothing else in this package spells a code as a
string literal; the CLI's --help lists them all via help_text(). Every code
here is produced by at least one test fixture.
"""

A1_REFERENCE_WORD_MISSING = "a1_reference_word_missing"
A1_REFERENCE_EXCEPTION_INVALID = "a1_reference_exception_invalid"
A1_REFERENCE_INVALID = "a1_reference_invalid"
A1_REFERENCE_CLOSED_CLASS_A1 = "closed_class_a1"

# --- input and loader failures -------------------------------------------
PLAN_NOT_FOUND = "plan_not_found"
PLAN_YAML_INVALID = "plan_yaml_invalid"
PLAN_OUTSIDE_LESSON_PLANS = "plan_outside_lesson_plans"
NOT_A_PLAN = "not_a_plan"
PLAN_SLUG_MISMATCH = "plan_slug_mismatch"
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
PACK_PATH_MISMATCH = "pack_path_mismatch"
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

# --- true-false placement (R-19) -------------------------------------------
TRUE_FALSE_NOT_POST_TEXT = "true_false_not_post_text"
TRUE_FALSE_OVER_TEXT_COUNT = "true_false_over_text_count"
TRUE_FALSE_RUN = "true_false_run"

# --- workbook presence (issue #8889 r5 §A1) ---------------------------------
WORKBOOK_ACTIVITY_MISSING = "workbook_activity_missing"

# --- activity placement table (issue #8889 r5 §B2) --------------------------
PLACEMENT_TABLE_UNAVAILABLE = "placement_table_unavailable"
ACTIVITY_PLACEMENT_FORBIDDEN = "activity_placement_forbidden"
ACTIVITY_PLACEMENT_NOT_ALLOWED = "activity_placement_not_allowed"

# --- rule 4, cross-plan part: earlier plans and earlier positions ----------
POSITION_CLAIMED_TWICE = "position_claimed_twice"
PRIOR_PLAN_UNREADABLE = "prior_plan_unreadable"
PRIOR_PLANS_MISSING = "prior_plans_missing"
USED_NOT_INTRODUCED_EARLIER = "used_not_introduced_earlier"

# --- rule 5: the plan matches the arc --------------------------------------
ARC_UNAVAILABLE = "arc_unavailable"
ARC_REF_UNKNOWN = "arc_ref_unknown"
ARC_SLUG_MISMATCH = "arc_slug_mismatch"
ARC_LETTERS_MISMATCH = "arc_letters_mismatch"
LETTER_INTRODUCED_TWICE = "letter_introduced_twice"
LETTERS_IN_NON_LITERACY_PLAN = "letters_in_non_literacy_plan"

# --- grammar registry (lesson-plans/<level>/_grammar.yaml) ------------------
REGISTRY_YAML_INVALID = "registry_yaml_invalid"
REGISTRY_MALFORMED = "registry_malformed"
REGISTRY_DUPLICATE_ID = "registry_duplicate_id"
REGISTRY_ID_MALFORMED = "registry_id_malformed"
GRAMMAR_ID_NOT_REGISTERED = "grammar_id_not_registered"
GRAMMAR_ID_WRONG_POSITION = "grammar_id_wrong_position"
GRAMMAR_POINT_MISMATCH = "grammar_point_mismatch"
SUPERSEDED_GRAMMAR_INTRODUCED = "superseded_grammar_introduced"
SUPERSEDED_GRAMMAR_USED = "superseded_grammar_used"
SUPERSEDED_BY_UNKNOWN = "superseded_by_unknown"
SUPERSEDED_BY_SUPERSEDED = "superseded_by_superseded"
REGISTRY_MISSING = "registry_missing"

# --- --strict: waiver refusal and append-only over git history ---------------
REGISTRY_APPEND_ONLY_VIOLATION = "registry_append_only_violation"
MERGE_BASE_UNAVAILABLE = "merge_base_unavailable"

# --- scope sidecar (lesson-plans/<level>/_scope/<slug>.yaml) -----------------
SCOPE_SIDECAR_MISSING = "scope_sidecar_missing"
SCOPE_SIDECAR_STALE = "scope_sidecar_stale"

# --- module title check ------------------------------------------------------
TITLE_LETTER_ENUMERATION_MISMATCH = "title_letter_enumeration_mismatch"

# --- review-checkable plan defects (issue #9487, review_gates.py) -----------
DUPLICATE_ACTIVITY_FOCUS = "duplicate_activity_focus"
LISTENING_QUIZ_SINGLE_KEY = "listening_quiz_single_key"
INCIDENTAL_NOT_DECODABLE = "incidental_not_decodable"
# second-round review gates C7–C14 (issue #9487)
RECAP_STORY_MISSING = "recap_story_missing"
RECAP_COMPREHENSION_NOT_ON_STORY = "recap_comprehension_not_on_story"
RECAP_COMPREHENSION_AFTER_PRODUCTION = "recap_comprehension_after_production"
FOCUS_EVIDENCE_NOT_IN_STEPS = "focus_evidence_not_in_steps"
STEP_WORD_NOT_DECODABLE = "step_word_not_decodable"
RECYCLED_WORD_NOT_DECODABLE_IN_PRINT = "recycled_word_not_decodable_in_print"
ODD_ONE_OUT_ROW_INVALID = "odd_one_out_row_invalid"
QUOTE_HOST_PRIVATE_USE = "quote_host_private_use"
QUOTE_HOST_TRANSCRIPTION_SYMBOL = "quote_host_transcription_symbol"
QUOTE_HOST_WATERMARK = "quote_host_watermark"
QUOTE_HOST_TOKEN_NOT_IN_VESUM = "quote_host_token_not_in_vesum"
COMPUTED_KEY_SINGLE_VALUE = "computed_key_single_value"
DUPLICATE_LESSON_VIDEO = "duplicate_lesson_video"
# third-round review gates C15–C20 (issue #9487)
ADJACENT_STEP_SAME_DISPLAY = "adjacent_step_same_display"
VIDEO_USE_PIPELINE_TOKEN = "video_use_pipeline_token"
VIDEO_USE_STEP_MISMATCH = "video_use_step_mismatch"
SENTENCE_NOT_DECODABLE_AT_HOST = "sentence_not_decodable_at_host"
WORD_MODEL_WITHOUT_SEGMENT = "word_model_without_segment"
# fourth-round review gates C21–C28 (issue #9487)
MODELED_PRINT_NOT_DECODABLE = "modeled_print_not_decodable"
CHOICE_BINARY_KEYS_REPEATED = "choice_binary_keys_repeated"
CONSTRUCTION_DISTRACTOR_FORMS_WORD = "construction_distractor_forms_word"
RECYCLED_CATEGORY_NOT_IN_LIST = "recycled_category_not_in_list"
PRACTICE_STEP_EMPTY = "practice_step_empty"
COMPREHENSION_TARGET_NOT_IN_HOST = "comprehension_target_not_in_host"
COMPREHENSION_TARGET_UNKNOWN = "comprehension_target_unknown"
LETTER_WITHOUT_RECORDING = "letter_without_recording"
TEACH_WORD_NOT_IN_INVENTORY = "teach_word_not_in_inventory"

# --- notes (never fail the run) ---------------------------------------------
# mechanical plan gates M1, M3, M5 (issue #9138) report here or as not_checked, never as failures
STEP_LETTER_NOT_PRACTISED = "step_letter_not_practised"
TOKEN_NOT_ALLOWED = "token_not_allowed"
CORE_CEFR_ABOVE_MODULE = "core_cefr_above_module"
CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW = "closing_shape_b_needs_plan_review"
# review-checkable gates C4–C6 (issue #9487) that read a proxy or a pedagogical choice
INCIDENTAL_LEMMA_NOT_DECODABLE = "incidental_lemma_not_decodable"
HEARD_WORD_WITHOUT_VIDEO = "heard_word_without_video"
EARLIER_CORE_NOT_RECYCLED = "earlier_core_not_recycled"
ODD_ONE_OUT_FEATURE_NOT_COMPUTED = "odd_one_out_feature_not_computed"
STEP_WORD_LEMMA_NOT_DECODABLE = "step_word_lemma_not_decodable"
COMPUTED_KEY_FORM_DEPENDENT = "computed_key_form_dependent"
ADJACENT_STEP_DISPLAY_RECALL = "adjacent_step_display_recall"
INCIDENTAL_NOT_USED = "incidental_not_used"
SENTENCE_DECODABLE_EARLIER = "sentence_decodable_earlier"
CHOICE_BINARY_KEYS_SHARED = "choice_binary_keys_shared"
CONSTRUCTION_DISTRACTOR_CUED = "construction_distractor_cued"
ANAGRAM_LETTERS_FORM_OTHER_WORD = "anagram_letters_form_other_word"
COMPREHENSION_TARGET_ONLY_TRANSCRIBED = "comprehension_target_only_transcribed"
LETTER_TEACHER_MODELED_ONLY = "letter_teacher_modeled_only"
# C1 and C18 read targets and options from prose (review_gates.py docstring), so they only note
NAMED_BEFORE_INTRODUCTION_UNVERIFIED = "named_before_introduction_unverified"
CHOICE_OPTION_UNVERIFIED = "choice_option_unverified"
MODELED_PRINT_TEACHER_FRAME = "modeled_print_teacher_frame"
# C26 does not decide a word named in an ambiguous sentence or whose host set it cannot resolve, so it only notes
COMPREHENSION_TARGET_UNVERIFIED = "comprehension_target_unverified"

# --- not_checked (never fail the run, always reported) ----------------------
MINUTES_CONSTANTS_UNDEFINED = "minutes_constants_undefined"
ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY = "arc_has_no_structured_grammar_or_vocabulary"
TITLE_QUANTITIES_NOT_PARSED = "title_quantities_not_parsed"
INTRODUCED_EARLIER_UNVERIFIED = "introduced_earlier_unverified"
PENDING_PROMOTION = "pending_promotion"
PLACEMENT_LEVEL_NOT_COVERED = "placement_level_not_covered"
TOKEN_UNRESOLVED = "token_unresolved"
MECHANICAL_RULE_NOT_CHECKED = "mechanical_rule_not_checked"
# not_checked outside --strict, a failure under --strict (C12, C23, #9487)
VESUM_UNAVAILABLE = "vesum_unavailable"

# Structured activity declarations (#9541); optional-field policy notes become failures in PR2.
TARGET_NOT_AVAILABLE = "target_not_available"
CHOICE_OPTION_NOT_DECODABLE = "choice_option_not_decodable"
OPTIONS_NOT_NFC = "options_not_nfc"
LEARNER_READ_WORD_NOT_NFC = "learner_read_word_not_nfc"
OPTIONS_MISSING = "options_missing"
OPTIONS_FORBIDDEN = "options_forbidden"
LEARNER_READ_REF_NOT_PRINTABLE = "learner_read_ref_not_printable"
LEARNER_READ_WORD_NOT_IN_PRINT = "learner_read_word_not_in_print"

A1_RECAP_MIGRATION_REQUIRED = "a1_recap_migration_required"
RECAP_TASK_INVALID = "recap_task_invalid"
RECAP_TASK_QUOTED_UKRAINIAN = "recap_task_quoted_ukrainian"
RECAP_TASK_INVENTORY = "recap_task_inventory"
RECAP_TASK_ORDER = "recap_task_order"
RECAP_TASK_PRINT = "recap_task_print"
ORIENTATION_CORE_WORDS = "orientation_core_words"

DESCRIPTIONS = {
    A1_RECAP_MIGRATION_REQUIRED: "legacy A1 recap requires retirement/migration by #10108",
    RECAP_TASK_INVALID: "practical recap task violates its structural contract",
    RECAP_TASK_QUOTED_UKRAINIAN: "quoted Ukrainian requires taught-form and construction review",
    RECAP_TASK_INVENTORY: "recap uses unknown or unavailable inventory",
    RECAP_TASK_ORDER: "recap task is duplicated or placed outside its closing step",
    RECAP_TASK_PRINT: "recap print is undeclared, unprintable or undecodable",
    ORIENTATION_CORE_WORDS: "orientation introduces core vocabulary",
    A1_REFERENCE_WORD_MISSING: "C29 (#9582): A1 introduced vocabulary missing from the reference; advisory until #9541 PR2",
    A1_REFERENCE_EXCEPTION_INVALID: "C29 (#9582): invalid typed reference exception; never exempts other gates",
    A1_REFERENCE_INVALID: "C29 (#9582): invalid reference input or enforcement configuration (failure)",
    A1_REFERENCE_CLOSED_CLASS_A1: "C29 (#9582): inventory-absent closed-class word has a class-specific A1 attestation (note)",
    PLAN_NOT_FOUND: "failure: the plan file does not exist",
    PLAN_YAML_INVALID: "failure: the plan file is not valid YAML",
    PLAN_OUTSIDE_LESSON_PLANS: "failure: plans live under curriculum/l2-uk-en/lesson-plans/<level>/, nowhere else",
    NOT_A_PLAN: "failure: a name beginning with _ is not a plan (§2a)",
    PLAN_SLUG_MISMATCH: "failure (§2a): the plan file name, the requested slug and the plan's slug field differ; a plan is <slug>.yaml",
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
    PACK_PATH_MISMATCH: "failure (rule 3): the --pack override does not match the plan's evidence_ref.path",
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
    TRUE_FALSE_NOT_POST_TEXT: "failure (R-19): a true-false activity is outside the practice of a text-hosting step and outside consolidation of a lesson that has one",
    TRUE_FALSE_OVER_TEXT_COUNT: "failure (R-19): true-false activities in practice and consolidation together outnumber the lesson's text-hosting steps",
    TRUE_FALSE_RUN: "failure (R-19): two true-false activities are adjacent in consolidation",
    WORKBOOK_ACTIVITY_MISSING: "failure (issue #8889 r5 §A1): a non-recap lesson has no placement: workbook activity",
    PLACEMENT_TABLE_UNAVAILABLE: "failure (issue #8889 r5 §B2): scripts/curriculum/validate/placement_table.yaml is missing or malformed",
    ACTIVITY_PLACEMENT_FORBIDDEN: "failure (issue #8889 r5 §B2): an activity's type is forbidden at this level by the generated placement table",
    ACTIVITY_PLACEMENT_NOT_ALLOWED: "failure (issue #8889 r5 §B2): an activity's placement (inline/workbook) is not the one the placement table allows for its type at this level",
    DUPLICATE_ACTIVITY_FOCUS: "failure (gate C2, #9487): two or more activities of one lesson carry the same focus text (whitespace collapsed)",
    LISTENING_QUIZ_SINGLE_KEY: "failure (gate C3, #9487): an activity declaring kind: listening cites videos whose models (letters and words) hold exactly one target, so every item has the same key",
    INCIDENTAL_NOT_DECODABLE: "failure (gate C4, #9487): in a letter-stage module, an incidental word none of whose word-store spellings can be read with the letters taught through its lesson",
    INCIDENTAL_LEMMA_NOT_DECODABLE: "note (gate C4, #9487): an incidental lemma needs a letter not taught through its lesson while another form of its record is readable; the plan does not bind the form, so the plan review confirms it",
    HEARD_WORD_WITHOUT_VIDEO: "note (gate C5, #9487): a teach-text clause says a word id is heard, and no video the step cites lists it in models.words; 'heard' is read from prose, so the plan review confirms it",
    EARLIER_CORE_NOT_RECYCLED: "note (gate C6, #9487): core records of earlier positions that no recycled list of the module names, listed with their lemma and position",
    RECAP_STORY_MISSING: "failure (gate C7, #9487): a recap lesson declares no first-person story, i.e. no dialogue block with exactly one speaker, the narrator (A1 arc D4, plan schema §2b)",
    RECAP_COMPREHENSION_NOT_ON_STORY: "failure (gate C7, #9487): a recap lesson has no kind: comprehension activity, or one whose declared host is not its story block (host: {kind: dialogue})",
    RECAP_COMPREHENSION_AFTER_PRODUCTION: "failure (gate C8, #9487): in a recap lesson an activity other than an unscored observe is linked (steps, practice order, consolidation) before a comprehension activity",
    FOCUS_EVIDENCE_NOT_IN_STEPS: "failure (gate C9, #9487): an activity focus names a pack record that no step of its lesson cites as evidence and that is not the activity's own model or error_refs, so the writer never receives it (R-26)",
    STEP_WORD_NOT_DECODABLE: "failure (gate C10, #9487): in a letter-stage module, a word a step introduces or uses has no word-store spelling readable with the letters taught so far, and no video the lesson cites lists it in models.words",
    RECYCLED_WORD_NOT_DECODABLE_IN_PRINT: "failure (gate C10, #9487): a recycled word a step uses is not readable with the letters taught so far, and the video that models it is cited by the lesson but not by that step",
    ODD_ONE_OUT_ROW_INVALID: "failure (gate C11, #9487): an odd-one-out row (a quote-host line of three or more words) does not have exactly one member differing in the feature the focus states (initial or final letter, syllables, letter count)",
    QUOTE_HOST_PRIVATE_USE: "failure (gate C12, #9487): a quote host's bytes carry a private-use code point",
    QUOTE_HOST_TRANSCRIPTION_SYMBOL: "failure (gate C12, #9487): a quote host's transcription bracket holds a character that is not a Cyrillic letter, combining mark, space, prime, apostrophe, | , - or length mark",
    QUOTE_HOST_WATERMARK: "failure (gate C12, #9487): a quote host's bytes carry a web address (a publisher watermark)",
    QUOTE_HOST_TOKEN_NOT_IN_VESUM: "failure (gate C12, #9487): a quote host prints a word of two or more vowels that is neither a word-store spelling nor a VESUM form (an OCR fragment, a split word, or a word VESUM does not list)",
    COMPUTED_KEY_SINGLE_VALUE: "failure (gate C13, #9487): an activity whose key is computed from its target form (count-syllables) has one key value across all its targets",
    DUPLICATE_LESSON_VIDEO: "failure (gate C14, #9487): two video entries of one lesson resolve to the same recording (YouTube id or URL, and segment)",
    ADJACENT_STEP_SAME_DISPLAY: "failure (gate C15, #9487): two adjacent steps of one lesson both display the same text, exercise or example record (a display directive in the teach text, or a needs: quote step's text evidence), and the second does not call it a recall; steps are binding (plan schema §7 decision 1), so the writer prints it twice",
    VIDEO_USE_PIPELINE_TOKEN: "failure (gate C17, #9487): the description the assembler prints for a lesson video in Ресурси (the plan's videos[].use, else the pack record's use) holds pipeline wording: segment:, null, driver-owned, timecode, timed segment, acoustic proof or a record id",
    VIDEO_USE_STEP_MISMATCH: "failure (gate C17, #9487): a lesson video's printed description names a step that does not exist in the lesson or does not cite that video in its evidence",
    SENTENCE_NOT_DECODABLE_AT_HOST: "failure (gate C19, #9487): in a letter-stage module, an example sentence a step cites needs a letter not taught through that lesson",
    WORD_MODEL_WITHOUT_SEGMENT: "failure (gate C20, #9487): a video the lesson cites models words or phrases (models.words) but binds no segment, so the learner is sent to the whole recording for them",
    MODELED_PRINT_NOT_DECODABLE: "failure (gate C21, #9487): in a letter-stage module, a step's teach text (or an activity focus) sends the teacher and learner to the exact print of a pack record that holds words needing letters not taught by that step",
    CHOICE_BINARY_KEYS_REPEATED: "failure (gate C22, #9487): three or more choice activities of one lesson declare the same two-member key set",
    CONSTRUCTION_DISTRACTOR_FORMS_WORD: "failure (gate C23, #9487): a pick-syllables row with another syllable of the activity in a blanked slot forms a word-store spelling or VESUM form other than the key, and the focus states no cue that selects the key",
    RECYCLED_CATEGORY_NOT_IN_LIST: "failure (gate C24, #9487): a lesson's rationale or job says it recycles a category (or quoted word) whose word records are not in the lesson's recycled list or inventory",
    PRACTICE_STEP_EMPTY: "failure (gate C25, #9487): a practice step links no activity, needs no block, hosts no dialogue and carries no paradigm, so the writer must produce an empty section",
    COMPREHENSION_TARGET_NOT_IN_HOST: "failure (gate C26, #9487): a comprehension activity hosted only on quotes or recordings names a word record that no host quote prints and no host recording models",
    COMPREHENSION_TARGET_UNKNOWN: "failure (gate C26, #9487): a comprehension activity focus names a W-… id the level word store does not hold",
    LETTER_WITHOUT_RECORDING: "failure (gate C27, #9487): a step introduces a letter that no recording the lesson cites declares in models.letters, and the step records no teacher model for it",
    TEACH_WORD_NOT_IN_INVENTORY: "failure (gate C28, #9487): a step's teach text names a word id outside the lesson's inventory and the planned prior learner state, so the writer's word packet lacks it",
    STEP_WORD_LEMMA_NOT_DECODABLE: "note (gate C10, #9487): a word a step introduces or uses has a lemma needing letters not taught so far and no recording the lesson cites, while another form of its record is readable; the plan does not bind the form, so the plan review confirms it",
    ODD_ONE_OUT_FEATURE_NOT_COMPUTED: "note (gate C11, #9487): an odd-one-out activity draws rows from a quote host, and its focus states no feature the gate computes; the plan review confirms each row has exactly one odd member",
    COMPUTED_KEY_FORM_DEPENDENT: "note (gate C13, #9487): a count-syllables activity's bound forms and lemmas share one key; another key needs a form the plan does not bind",
    ADJACENT_STEP_DISPLAY_RECALL: "note (gate C15, #9487): two adjacent steps display the same record and the second calls it a recall (recall, again, already displayed); the plan review confirms the repeat is intended",
    INCIDENTAL_NOT_USED: "note (gate C16, #9487): an incidental record whose id and spellings appear in no step, activity or dialogue of its lesson nor in a pack record they cite; Словник would list a word the lesson never uses",
    SENTENCE_DECODABLE_EARLIER: "note (gate C19, #9487): an example sentence is decodable in an earlier lesson (or position) than the one hosting it; the plan review confirms the placement and any rationale that ties it to the host's letters",
    CHOICE_BINARY_KEYS_SHARED: "note (gate C22, #9487): two choice activities of one lesson declare the same two-member key set; the plan review confirms their operations differ",
    CONSTRUCTION_DISTRACTOR_CUED: "note (gate C23, #9487): a construction item's other completion forms an attested word, and the focus says its stems carry a cue (gloss, picture) that selects the key; the plan review confirms the cue",
    ANAGRAM_LETTERS_FORM_OTHER_WORD: "note (gate C23, #9487): an anagram target's letters also spell another VESUM or word-store form; most are rare inflected or archaic forms, so the plan review confirms none is a word an A1 learner could build instead",
    COMPREHENSION_TARGET_ONLY_TRANSCRIBED: "note (gate C26, #9487): a quote-hosted comprehension activity names a word record no host prints in spelling, and a host holds a transcription that may show it; the plan review confirms the host shows each word the items ask about",
    COMPREHENSION_TARGET_UNVERIFIED: "note (gate C26, #9487): a comprehension activity names a word record no resolvable host of its own holds, and the plan does not decide whether that is an error: the word is named only in focus sentences with exclusion wording or naming another activity, or a host is a dialogue (drafted by the writer) or another unresolvable record, or no host is declared outside sentences naming another activity, or a host is declared in a sentence naming another activity; the plan review confirms every word the items ask about is in the host",
    LETTER_TEACHER_MODELED_ONLY: "note (gate C27, #9487): a step introduces a letter that no cited recording models, and its teach text records the teacher modelling that letter instead; the plan review confirms no recording is available",
    STEP_LETTER_NOT_PRACTISED: "note (gate M1, #9138): a step introduces a letter that no activity in its practice names in its focus; a focus can describe the practice without the glyph, so the plan review confirms it",
    TOKEN_NOT_ALLOWED: "note (gate M3, #9138): a quoted Ukrainian token in a step's teach text or an activity's focus resolves only to word records outside the lesson's allowed set; the plan review confirms it is intended",
    CORE_CEFR_ABOVE_MODULE: "note (gate M5, #9138): a core lemma's word-store CEFR level is above the module's level; the plan sets no CEFR ceiling, so the plan review confirms it is intended (for example the module's own metalanguage)",
    CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW: "note (rule 1b): the teach + closes_with_recap closing shape is used; the plan review must confirm it",
    POSITION_CLAIMED_TWICE: "failure (rule 4): two plan files claim the same arc position",
    PRIOR_PLAN_UNREADABLE: "failure (rule 4): a sibling plan file cannot be read, so earlier introductions cannot be trusted",
    PRIOR_PLANS_MISSING: "failure (rule 4): an earlier arc position has no plan file; --allow-missing-prior turns exactly this into the waiver 'waived: prior_plans_missing'",
    USED_NOT_INTRODUCED_EARLIER: "failure (rule 4): a used or recycled id was introduced in no earlier lesson of this plan and no earlier position's plan",
    ARC_UNAVAILABLE: "failure (rule 5): lesson-plans/<level>/_arc.yaml is missing, invalid or stale (regenerate with generate_arc.py --write)",
    ARC_REF_UNKNOWN: "failure (rule 5): arc_ref.level/arc_ref.position does not exist in the level arc",
    ARC_SLUG_MISMATCH: "failure (rule 5): the plan's slug differs from the arc slug at its position",
    ARC_LETTERS_MISMATCH: "failure (rule 5): the union of the lessons' phonetics.letters differs from the arc position's letters (missing and extra are reported separately)",
    LETTER_INTRODUCED_TWICE: "failure (rule 5): a letter is introduced by two lessons of the plan",
    LETTERS_IN_NON_LITERACY_PLAN: "failure (rule 5): the arc position carries no letters, so phonetics.letters and introduces.letters must be empty everywhere",
    REGISTRY_YAML_INVALID: "failure (§2a): lesson-plans/<level>/_grammar.yaml is not valid YAML",
    REGISTRY_MALFORMED: "failure (§2a): the grammar registry is not a list of { id, point, introduced_at: { position, lesson } } records",
    REGISTRY_DUPLICATE_ID: "failure (§2a): a grammar id appears twice in the registry",
    REGISTRY_ID_MALFORMED: "failure (§2a): a registry id is not G-<level>-<nnn>",
    GRAMMAR_ID_NOT_REGISTERED: "failure (§2a): the plan introduces a grammar id the registry does not assign at all",
    GRAMMAR_ID_WRONG_POSITION: "failure (§2a): the registry assigns the introduced id to a different position or lesson",
    GRAMMAR_POINT_MISMATCH: "failure (§2a): the plan's point string differs from the registry record's point",
    SUPERSEDED_GRAMMAR_INTRODUCED: "failure (§2a): the plan introduces a grammar id the registry marks superseded",
    SUPERSEDED_GRAMMAR_USED: "failure (§2a): a step uses a grammar id the registry marks superseded",
    SUPERSEDED_BY_UNKNOWN: "failure (§2a): superseded_by names an id that does not exist in the registry",
    SUPERSEDED_BY_SUPERSEDED: "failure (§2a): superseded_by names an id that is itself superseded",
    REGISTRY_MISSING: "failure (§2a): the plan introduces grammar but lesson-plans/<level>/_grammar.yaml does not exist; the message says how to add the record",
    REGISTRY_APPEND_ONLY_VIOLATION: "failure (--strict, §2a): the registry differs from its merge-base version beyond appending records or adding superseded_by",
    MERGE_BASE_UNAVAILABLE: "failure (--strict, §2a): no merge base with origin/main can be computed (shallow clone); fetch full history",
    SCOPE_SIDECAR_MISSING: "failure (§2a): the generated scope sidecar _scope/<slug>.yaml does not exist; run plan-validate --write-scope",
    SCOPE_SIDECAR_STALE: "failure (§2a): the scope sidecar differs byte for byte from a fresh generation; the diff is quoted",
    TITLE_LETTER_ENUMERATION_MISMATCH: "failure (§2a): a run of enumerated single letters in the module title/subtitle differs from the scope letter list",
    MINUTES_CONSTANTS_UNDEFINED: "not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)",
    ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY: "not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)",
    TITLE_QUANTITIES_NOT_PARSED: "not_checked: digit quantities in the title/subtitle are not parsed; any ASCII digits found are quoted (§2a)",
    INTRODUCED_EARLIER_UNVERIFIED: "not_checked: the id is not introduced in the plans that exist; earlier positions are missing under a waiver, so introduction cannot be verified",
    PENDING_PROMOTION: "not_checked (--provisional-pack only): evidence_ref.sha256 differs from the provisional pack's sha256; both hashes are recorded and plan-promote sets it after the plan review approves",
    TOKEN_UNRESOLVED: "not_checked (gate M3, #9138): a Ukrainian token in a step's teach text or an activity's focus resolves to no word-store record, or is spelled like a taught syllable and matches only out-of-allowlist words (a syllable or sound is not a word); a person confirms it",
    VESUM_UNAVAILABLE: "not_checked, and a failure under --strict (gates C12, C23, #9487): VESUM could not be read, so the gate's lookup is undecided; findings the gate decided from the word store and the pack are still reported, and strict validation (plan-promote) never passes an undecided gate; only a run that declares an environment without VESUM (--not-checked-when-unavailable vesum; CI, whose runner has none) keeps it a printed not_checked line under --strict",
    NAMED_BEFORE_INTRODUCTION_UNVERIFIED: "note (gate C1, #9487): a word id named in a dialogue's target_grammar, or in the focus of an activity in a step's practice, is introduced by a later step of the lesson, or by no step up to that one and is outside the lesson's allowed set; the text is prose, so whether it presents or scores the word is not read from it; the message quotes the sentence and the plan review confirms",
    CHOICE_OPTION_UNVERIFIED: "note (gate C18, #9487): in a letter-stage module, a fill-in or quiz focus names a word with a letter not taught through its lesson that no recording the lesson cites models; the plan has no option field, so whether the learner sees it as an option is not read from the prose; the message quotes the sentence and the plan review confirms",
    MODELED_PRINT_TEACHER_FRAME: "note (gate C21, #9487): a directive to model a record's exact print whose untaught words may be the frame the plan says the teacher reads; the plan review confirms",
    MECHANICAL_RULE_NOT_CHECKED: "not_checked (gates M1, M3, M5, #9138; C1, C3–C6, C10, C18, C19, C21, C27, C28, #9487): a gate applied to the plan but its input was unavailable (arc, base layer, earlier plans, CEFR level); VESUM is vesum_unavailable; the message names the gate and the reason",
    PLACEMENT_LEVEL_NOT_COVERED: "not_checked (issue #8889 r5 §B2): this level is not covered by the generated placement table (CORE fresh-build levels only); the placement rule is not checked",
    TARGET_NOT_AVAILABLE: "failure (C1): a declared target is unknown, outside the allowed set or introduced later",
    CHOICE_OPTION_NOT_DECODABLE: "failure (C18): a printed option needs an untaught letter at its step; recordings do not exempt print",
    OPTIONS_NOT_NFC: "failure: declared option text must already be NFC, with exact case preserved",
    LEARNER_READ_WORD_NOT_NFC: "failure: learner_reads selector words must already be NFC, with exact case preserved",
    OPTIONS_MISSING: "note (PR1): quiz and fill-in require an options declaration",
    OPTIONS_FORBIDDEN: "note (PR1): unscored types forbid an options declaration, including an empty one",
    LEARNER_READ_REF_NOT_PRINTABLE: "failure (C21): learner_reads references a record without printable pack text",
    LEARNER_READ_WORD_NOT_IN_PRINT: "failure (C21): a learner_reads selection does not occur in the record's exact print",
}

NOTE_CODES = frozenset(
    {
        A1_REFERENCE_CLOSED_CLASS_A1,
        OPTIONS_MISSING,
        OPTIONS_FORBIDDEN,
        CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW,
        STEP_LETTER_NOT_PRACTISED,
        TOKEN_NOT_ALLOWED,
        CORE_CEFR_ABOVE_MODULE,
        INCIDENTAL_LEMMA_NOT_DECODABLE,
        HEARD_WORD_WITHOUT_VIDEO,
        EARLIER_CORE_NOT_RECYCLED,
        ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
        STEP_WORD_LEMMA_NOT_DECODABLE,
        COMPUTED_KEY_FORM_DEPENDENT,
        ADJACENT_STEP_DISPLAY_RECALL,
        INCIDENTAL_NOT_USED,
        SENTENCE_DECODABLE_EARLIER,
        CHOICE_BINARY_KEYS_SHARED,
        CONSTRUCTION_DISTRACTOR_CUED,
        ANAGRAM_LETTERS_FORM_OTHER_WORD,
        COMPREHENSION_TARGET_ONLY_TRANSCRIBED,
        LETTER_TEACHER_MODELED_ONLY,
        NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
        CHOICE_OPTION_UNVERIFIED,
        MODELED_PRINT_TEACHER_FRAME,
        COMPREHENSION_TARGET_UNVERIFIED,
    }
)
NOT_CHECKED_CODES = frozenset(
    {
        MINUTES_CONSTANTS_UNDEFINED,
        ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY,
        TITLE_QUANTITIES_NOT_PARSED,
        INTRODUCED_EARLIER_UNVERIFIED,
        PENDING_PROMOTION,
        PLACEMENT_LEVEL_NOT_COVERED,
        TOKEN_UNRESOLVED,
        MECHANICAL_RULE_NOT_CHECKED,
        VESUM_UNAVAILABLE,
    }
)

#: Waiver identities. A waiver is printed as ``waived: <code>`` and is never a
#: clean pass; --strict refuses every waiver flag.
WAIVER_PRIOR_PLANS_MISSING = PRIOR_PLANS_MISSING
WAIVER_CODES = frozenset({WAIVER_PRIOR_PLANS_MISSING})


def help_text() -> str:
    """Every registered code, one per line, for the CLI's --help."""
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
