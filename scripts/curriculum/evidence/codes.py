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
}

EXCLUDING_MARKERS = frozenset({"alt", "arch", "bad", "dialect", "obsc", "slang", "subst", "vulg"})


def help_text() -> str:
    """Shared help text for the future build/verify CLI."""
    return "\n".join(f"{code}: {description}" for code, description in DESCRIPTIONS.items())
