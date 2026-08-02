"""Public, provider-neutral, body-free Entire context-link index (#6174 / ADR-018).

This package implements the local-only slice of the Entire context layer:

- a versioned, strict, body-free context-link schema (:mod:`.model`);
- a deterministic locator-ID derivation over canonical metadata;
- a caller-owned, rebuildable SQLite projection with an append-only lifecycle
  (pending / promoted / tombstoned) and idempotent admission (:mod:`.store`);
- explicit, local-only typed resolvers that map an exact Git commit SHA, an
  exact ACP conversation ID, or an exact ``(agent, lineage_id, rollover_id)``
  triple to a verified body-free canonical projection (:mod:`.resolvers`),
  failing closed for every unsupported kind;
- deterministic promoted-only recall workflows — ``search_past_work``,
  ``explain_change``, and ``prepare_handoff`` — that re-resolve every
  candidate and recompute its canonical digest before it may enter an
  LLM-facing result or handoff capsule (:mod:`.recall`);
- a provider-neutral CLI (``python -m scripts.entire_context``).

Recall, reconciliation, and Monitor reads call no Entire, GitHub, Fleet, ACP
provider, or network service and mutate no canonical authority system. The
explicit provider-status refresh is the sole Entire CLI call and writes only a
sanitized local cache. The projection is disposable and non-load-bearing.
"""

from .model import (
    SCHEMA_VERSION,
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
)
from .recall import (
    MAX_CAPSULE_BYTES,
    MAX_HANDOFF_ITEMS,
    MAX_QUERY_BYTES,
    MAX_RESULTS,
    MAX_SCAN_ROWS,
    RecallInputError,
    explain_change,
    prepare_handoff,
    search_past_work,
)
from .resolvers import (
    SUPPORTED_RESOLVER_KINDS,
    Resolution,
    ResolutionError,
    resolve_acp_conversation,
    resolve_bootstrap,
    resolve_git_commit,
    resolve_rollover,
    reverify_link,
)
from .store import AdmitOutcome, AdmitResult, ContextLinkStore

__all__ = [
    "MAX_CAPSULE_BYTES",
    "MAX_HANDOFF_ITEMS",
    "MAX_QUERY_BYTES",
    "MAX_RESULTS",
    "MAX_SCAN_ROWS",
    "SCHEMA_VERSION",
    "SUPPORTED_RESOLVER_KINDS",
    "AdmitOutcome",
    "AdmitResult",
    "ContextLink",
    "ContextLinkStore",
    "LinkKind",
    "RecallInputError",
    "Resolution",
    "ResolutionError",
    "SchemaError",
    "VerificationEvidence",
    "VerificationStatus",
    "explain_change",
    "prepare_handoff",
    "resolve_acp_conversation",
    "resolve_bootstrap",
    "resolve_git_commit",
    "resolve_rollover",
    "reverify_link",
    "search_past_work",
]
