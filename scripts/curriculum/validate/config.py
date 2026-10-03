"""Staged A1 reference vocabulary policy (#9582)."""

# The #9541 PR2 plan revision changes this to "failure". Until that migration,
# C29 provides staged AC-03 evidence as notes; advisory delivery does not close AC-03.
A1_REFERENCE_ENFORCEMENT = "advisory"

# Closed operator-approved list, 2026-10-03; this exception affects only C29.
A1_REFERENCE_PHONETICS_TERMS = frozenset({"звук", "голосний", "приголосний", "літера"})
