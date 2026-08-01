"""Public, provider-neutral, body-free Entire context-link index (#6174 / ADR-018).

This package implements the local-only slice of the Entire context layer:

- a versioned, strict, body-free context-link schema (:mod:`.model`);
- a deterministic locator-ID derivation over canonical metadata;
- a caller-owned, rebuildable SQLite projection with an append-only lifecycle
  (pending / promoted / tombstoned) and idempotent admission (:mod:`.store`);
- a provider-neutral CLI for body-free ``status``, known-ID ``lookup`` /
  ``explain``, and deterministic ``rebuild`` (``python -m scripts.entire_context``).

Nothing in this package calls Entire, GitHub, Fleet, ACP, Monitor, or the
network, and nothing here mutates any canonical authority system. The
projection is disposable and disabled/non-load-bearing by default.
"""

from .model import (
    SCHEMA_VERSION,
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
)
from .store import AdmitOutcome, AdmitResult, ContextLinkStore

__all__ = [
    "SCHEMA_VERSION",
    "AdmitOutcome",
    "AdmitResult",
    "ContextLink",
    "ContextLinkStore",
    "LinkKind",
    "SchemaError",
    "VerificationEvidence",
    "VerificationStatus",
]
