# Fleet Task Identity Contract

Every replacement task carries one `task-identity.v1` envelope from prepare
through confirmation. The full `semantic_title` is immutable continuity data;
the bounded `visible_title` is display text. Issue-backed titles use
`#<issue> — <semantic title>`. Otherwise they use
`<task family> — <semantic title>`.

Reject blank, generic, UUID-only, lineage-only, rollover-only, and
generation-only semantic titles. Bound visible titles before a native call;
Codex uses its 60-character limit. Never use soft or prefix readback matching.

The same visible title must appear in the dispatch record, handoff brief,
lease ledger, replacement inbox/bootstrap, monitor output, and final receipt.
Identifiers remain metadata and never replace the visible title.

`terminal_goal` is typed: `merge`, `deploy`, or `certify`. New callers must
choose one explicitly. `unknown` exists only for deterministic migration of a
legacy identity-less lease and must never be emitted by an explicit envelope.
An issue-backed identity also requires its one stream epic.

Title lifecycle boundaries are durable and idempotent:

1. Bind the exact replacement task ID.
2. If the harness supports native title mutation and exact readback, persist
   the native acknowledgement, then reconcile the exact task ID and exact
   title as raw strings. Whitespace or other normalization is forbidden.
   Acknowledgement alone is not reconciliation. Once a successful
   acknowledgement or exact readback is durable, a later failed retry cannot
   regress it.
3. If the harness lacks native mutation or exact readback, record
   `native_mutation_supported: false`, `attempted: false`, and the complete
   fallback carrier list. Never fabricate a rename or readback.
4. Resume and confirm only after exact reconciliation or the honest fallback.

Persist the complete identity receipt before the lease, then write the lease
last as the transaction commit marker. A receipt left ahead by a lease-write
failure is a derived projection and may be repaired from the committed lease;
the lease must never point to a missing or unvalidated receipt path.

Identity-less lease-v2 packets receive deterministic conservative backfill
with migration provenance. Lease-v1 still requires its explicit migration.
Multiple live packets remain fail-closed: list every exact candidate and a
safe exact-ID next action; never choose by directory order, age, or title.
Monitor `/api/orient` exposes this read-only projection as `rollovers`; it does
not select a packet or maintain a separate registry.
