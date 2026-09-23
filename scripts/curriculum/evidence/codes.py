"""Outcome registry for the word store. CLI consumers render DESCRIPTIONS in help."""

INVALID_REQUEST = "invalid_request"
SOURCE_UNAVAILABLE = "source_unavailable"
SOURCE_CHANGED = "source_changed"
UNKNOWN_TAG = "unknown_tag"
LOCK_MISMATCH = "lock_mismatch"
REGISTRY_MISMATCH = "registry_mismatch"
FORM_MISMATCH = "form_mismatch"
STRESS_MISMATCH = "stress_mismatch"
UNCHECKED_ULIF = "unchecked_ulif"
UNRESOLVED_CITED = "unresolved_cited"
LEARNER_MARKER = "learner_marker"
PENDING_STRESS = "pending_stress"
PENDING_ULIF = "pending_ulif"
UNRESOLVED_ENTRY = "unresolved_entry"
OVERRIDE_PRESENT = "override_present"
NOT_CHECKED = "not_checked"
GLOSS_MISMATCH = "gloss_mismatch"
CEFR_MISMATCH = "cefr_mismatch"
SPAN_MISMATCH = "span_mismatch"
UNSUPPORTED_DROPPED = "unsupported_dropped"
CHUNK_ID_MOVED = "chunk_id_moved"
QUOTE_MISMATCH = "quote_mismatch"
ERROR_MISMATCH = "error_mismatch"
STANDARD_MISMATCH = "standard_mismatch"
WORDS_FIELD_FORBIDDEN = "words_field_forbidden"
OPEN_UNSUPPORTED = "open_unsupported"

DESCRIPTIONS = {
    INVALID_REQUEST: "failure: the request is invalid",
    SOURCE_UNAVAILABLE: "failure: a required source is unavailable",
    SOURCE_CHANGED: "warning (failure under --strict): source content changed",
    UNKNOWN_TAG: "not_checked: a VESUM atom has no declared mapping",
    LOCK_MISMATCH: "failure: file bytes disagree with the lock",
    REGISTRY_MISMATCH: "failure: ids or identities disagree with the ledger",
    FORM_MISMATCH: "failure: a source no longer lists a form or its tags",
    STRESS_MISMATCH: "failure: stored stress differs from the current source",
    UNCHECKED_ULIF: "failure: ULIF evidence comes from an unchecked spelling group",
    UNRESOLVED_CITED: "failure: a plan cites an unresolved entry",
    LEARNER_MARKER: "failure: an excluded form is marked learner-usable",
    PENDING_STRESS: "open: a form needs sourced stress",
    PENDING_ULIF: "open: the ULIF spelling group is not checked",
    UNRESOLVED_ENTRY: "open: an entry requires an explicit source choice",
    OVERRIDE_PRESENT: "report: the oracle applied an exact-form override",
    NOT_CHECKED: "report: a fact could not be checked",
    GLOSS_MISMATCH: "failure: stored gloss differs from the source",
    CEFR_MISMATCH: "failure: stored CEFR level differs from the source",
    SPAN_MISMATCH: "failure: span does not match source chunk exactly once",
    UNSUPPORTED_DROPPED: "failure: unsupported id from previous build dropped",
    CHUNK_ID_MOVED: "report: quote text found in source file but chunk id moved",
    QUOTE_MISMATCH: "failure: quote text no longer found in source file",
    ERROR_MISMATCH: "failure: error row differs from source",
    STANDARD_MISMATCH: "failure: standard text or file hash differs from source",
    WORDS_FIELD_FORBIDDEN: "failure: pack contains forbidden words field",
    OPEN_UNSUPPORTED: "open (failure under --strict): unsupported claim remains open",
}

EXCLUDING_MARKERS = frozenset({"alt", "arch", "bad", "dialect", "obsc", "slang", "subst", "vulg"})


def help_text() -> str:
    """Shared help text for the future build/verify CLI."""
    return "\n".join(f"{code}: {description}" for code, description in DESCRIPTIONS.items())
