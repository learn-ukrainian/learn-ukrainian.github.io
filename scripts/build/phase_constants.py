"""Canonical V6 pipeline phase order + human-friendly labels.

Extracted from ``scripts/build/v6_build.py`` (#2747 / #1863) so that
out-of-process consumers — chiefly the Monitor API's ``state_*`` modules —
can read the phase list and labels WITHOUT importing the 12K-line, OBSOLETE
``v6_build`` build entrypoint. ``v6_build`` re-imports these names for its own
internal use and for back-compat with its test suite, so the data has exactly
one source of truth here.

Pure data only — this module must never import build/runtime code (keeping it
dependency-free is what lets the API import it cheaply).
"""

# All phases in pipeline order (used by --resume and by API state reconciliation).
# ``PHASES`` is the stable public alias; ``ALL_PHASES`` is the underlying list.
# They are the same object on purpose — keep them in sync (free, identical list).
ALL_PHASES: list[str] = [
    "check", "research", "skeleton", "pre-verify", "write", "honesty-annotate",
    "exercises", "activities", "repair", "activity-pre-validate", "verify-exercises", "annotate",
    "vocab", "enrich", "verify", "review", "review-style", "stress", "publish", "audit",
]
PHASES = ALL_PHASES

# Human-friendly labels for the v6 phases. Keys match ``PHASES`` exactly; any
# phase without an explicit label falls back to its kebab-case id via
# ``PHASE_LABELS.get(name, name)``.
PHASE_LABELS: dict[str, str] = {
    "check": "Plan check",
    "research": "Research",
    "skeleton": "Skeleton",
    "pre-verify": "Pre-verify",
    "write": "Write content",
    "honesty-annotate": "Honesty annotate",
    "exercises": "Exercises",
    "activities": "Activities",
    "repair": "Repair",
    "activity-pre-validate": "Activity pre-validation",
    "verify-exercises": "Verify exercises",
    "annotate": "Annotate",
    "vocab": "Vocabulary",
    "vocab-check": "Vocabulary coverage check",
    "enrich": "Enrich",
    "verify": "Verify content",
    "review": "Review",
    "review-style": "Style review",
    "stress": "Stress marks",
    "publish": "Publish MDX",
    "audit": "Audit",
}
