"""Outcome registry for the token resolver (#8413 Brief B, #8431 r3 §3).

One constant per token class, failure, and report. No literal code strings
elsewhere in this package. The CLI's --help lists them all via help_text().
"""

from __future__ import annotations

from scripts.curriculum.evidence import codes as evidence_codes
from scripts.curriculum.learner_state import codes as state_codes

# --- Token classes that are not failures --------------------------------------
RESOLVED = "resolved"
STRESS_CERTAIN_IDENTITY_OPEN = "stress_certain_identity_open"
STRESS_OPEN = "stress_open"
LETTER_OR_SYLLABLE = "letter_or_syllable"
SKIPPED_PREFIX = "skipped:"

# --- Token classes that are failures (the contract's names where it has one) ---
LEMMA_OUTSIDE_STATE = state_codes.LEMMA_OUTSIDE_STATE
PENDING_STRESS = state_codes.PENDING_STRESS
TOO_MANY_CANDIDATES = "too_many_candidates"
GLOSS_OUTSIDE_LESSON = "gloss_outside_lesson"
LETTER_OUTSIDE_STATE = "letter_outside_state"
UNCLASSIFIABLE = "unclassifiable"

# --- Document, answer and receipt failures -------------------------------------
INVALID_INPUT = "invalid_input"
ACCENT_IN_INPUT = "accent_in_input"
UNKNOWN_WORD_ID = "unknown_word_id"
INVALID_ANSWER = "invalid_answer"
TOKEN_UNRESOLVED = state_codes.TOKEN_UNRESOLVED
STALE_QUESTIONS = "stale_questions"
RECEIPT_INVALID = "receipt_invalid"
LOCK_MISMATCH = evidence_codes.LOCK_MISMATCH
SOURCE_UNAVAILABLE = evidence_codes.SOURCE_UNAVAILABLE

# --- Reports --------------------------------------------------------------------
SOURCE_CHANGED = evidence_codes.SOURCE_CHANGED

# --- Surface categories (classification before resolution) ---------------------
SENTENCE_TOKEN = "sentence_token"
PROPER_NOUN = "proper_noun"
GLOSS_REF = "gloss_ref"
SKIPPED = "skipped"

# Roles assigned by the engine; skipped roles are never looked up.
SENTENCE_ROLES = frozenset(
    {"quoted_term", "narration", "dialogue_line", "instruction", "item_prompt", "item_answer", "record_print"}
)
SKIPPED_ROLES = frozenset({"error_text", "item_option", "vesum_exempt"})
ROLES = SENTENCE_ROLES | SKIPPED_ROLES | {"gloss_ref", "phonetics"}
TABS = frozenset({"urok", "slovnyk", "vpravy", "resursy"})

# A token's non-Cyrillic surface kinds that are skipped by class.
SKIPPED_KINDS = ("latin", "digits")

OPEN_CLASSES = frozenset({STRESS_CERTAIN_IDENTITY_OPEN, STRESS_OPEN})
FAILURE_CLASSES = frozenset(
    {
        LEMMA_OUTSIDE_STATE,
        PENDING_STRESS,
        TOO_MANY_CANDIDATES,
        GLOSS_OUTSIDE_LESSON,
        LETTER_OUTSIDE_STATE,
        UNCLASSIFIABLE,
    }
)
MAX_RECORDS = 5


def skipped(reason: str) -> str:
    return f"{SKIPPED_PREFIX}{reason}"


DESCRIPTIONS: dict[str, str] = {
    RESOLVED: "class: deterministic narrowing left one record (syncretic forms of it are one answer)",
    STRESS_CERTAIN_IDENTITY_OPEN: "class: several records share one stressed spelling; non-blocking question",
    STRESS_OPEN: "class: readings differ in stress; blocking question before any stress is printed",
    LETTER_OR_SYLLABLE: "class: a literacy-step letter or syllable, matched to the lesson's letters, never looked up",
    f"{SKIPPED_PREFIX}<role|kind>": "class: skipped by field role (error_text, item_option, vesum_exempt) or kind",
    LEMMA_OUTSIDE_STATE: "failure: no learner-usable form of an allowlist record spells the token",
    PENDING_STRESS: "failure: stress is pending for the only record, for every reading, or for the answered one",
    TOO_MANY_CANDIDATES: "failure: more than five allowlist records compete for one spelling",
    GLOSS_OUTSIDE_LESSON: "failure: a {{gloss:W-...}} names a record outside this lesson's core and incidental",
    LETTER_OUTSIDE_STATE: "failure: a phonetics token uses a letter outside the lesson's letters",
    UNCLASSIFIABLE: "failure: the token fits no surface category (mixed scripts, unknown letters, empty gloss ref)",
    INVALID_INPUT: "failure: the expanded document, allowlist, or answers file has the wrong shape",
    ACCENT_IN_INPUT: "failure: a combining accent appears in the expanded document",
    UNKNOWN_WORD_ID: "failure: an allowlist id has no record in the word store",
    INVALID_ANSWER: "failure: an answer names a non-candidate record, an unknown question, or repeats one",
    TOKEN_UNRESOLVED: "failure: a blocking question has no answer",
    STALE_QUESTIONS: "failure: the questions batch was built from other inputs than the current ones",
    RECEIPT_INVALID: "failure: a resolutions file breaks its schema or its internal rules",
    LOCK_MISMATCH: "failure: file bytes disagree with the lock sidecar",
    SOURCE_UNAVAILABLE: "failure: a required source is unavailable",
    SOURCE_CHANGED: "report: a stored stress differs from the oracle today (or a source changed mid-session)",
}


def help_text() -> str:
    return "\n".join(f"  {code}: {description}" for code, description in DESCRIPTIONS.items())
