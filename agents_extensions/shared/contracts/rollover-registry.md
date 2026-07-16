# Fleet Rollover Registry Contract

The canonical registry is a durable projection of `task-identity.v1`. It does
not create a second task identity and never uses a title as an identifier.

## Identity and storage

Each record is keyed exactly by `(agent, lineage_id, rollover_id)` and lives at:

```text
.agent/thread-rollover-registry/v1/<agent>/<lineage-id>/<rollover-id>/record.json
```

The embedded `task_identity` must validate against
`agents_extensions/shared/schemas/task-identity.v1.schema.json`. The registry
key, predecessor/replacement IDs, generation, repository, issue, epic, and
human-readable title must agree with that envelope. Provider-specific deploy
copies are generated from `agents_extensions/shared/`; they are not separate
authorities.

All mutations for one lineage use the same blocking lineage lock. Retrying the
same operation is idempotent. A different replacement ID for an already-bound
packet is a conflict, never a second successor.

## Lifecycle

Successful boundaries are ordered:

```text
PREPARED → AWAITING_NATIVE_CREATE → REPLACEMENT_CREATED → RESUMED
→ STRICT_RECALL_PASSED → CANARY_PASSED → CONFIRMED
→ PREDECESSOR_ARCHIVED → HEARTBEAT_RETIRED
```

`BLOCKED` preserves the last successful boundary. `SUPERSEDED` and
`ABANDONED_WITH_PROOF` are terminal dispositions. A mutation may not skip a
successful prerequisite. Confirmed, superseded, abandoned, archived, and
heartbeat-retired records are excluded from live-pending detection.

## Detection and audit

Exact selectors are ANDed when more than one is supplied:

- `--source-thread-id`
- `--replacement-thread-id`
- `--lineage-id`
- `--rollover-id`

One exact unique match may proceed even while unrelated packets are pending. A
generic lookup with multiple live matches is read-only and returns every
candidate's title, issue/epic, exact IDs, state, age, last successful boundary,
and next safe action. Any corrupt durable source also makes generic detection
non-mutating. It never chooses by recency, title, or filesystem order.

`audit` classifies every valid or corrupt entry as one of:

- active and resumable;
- awaiting native action;
- confirmed but incompletely cleaned;
- confirmed and fully cleaned;
- superseded;
- stale and requiring operator adjudication;
- inconsistent or corrupt.

Age can produce the stale classification but cannot delete, abandon, or
supersede continuity state.

## Authoritative reconciliation

`reconcile-exact` consumes an operator-captured JSON snapshot bound to the exact
registry key. The snapshot contains:

- `source`: exact predecessor ID, archive state, and archive receipt path;
- `replacement`: existence, exact replacement ID, and native title;
- `title_receipt`: the exact replacement task ID plus adapter support and exact
  readback receipt, or an honest unsupported-adapter fallback receipt;
- `confirmation`: exact replacement ID and durable confirmation proof;
- `heartbeat`: exact automation ID, cleanup authorization, retirement state,
  and retirement receipt;
- `captured_at` and durable `evidence_paths`.

Reconciliation never infers creation, archival, confirmation, or heartbeat
retirement from a title, task absence, local process absence, or elapsed time.
It is read-only unless `--apply` is supplied. Apply writes a deterministic
receipt under the exact registry record and refuses inconsistent snapshots.

## Maintenance

The safe commands are `resume-exact`, `reconcile-exact`,
`finish-cleanup-exact`, `supersede-exact`, and `abandon-exact`. Cleanup,
supersession, and abandonment are two-step `--plan` / `--apply` operations.
Apply validates the immutable plan's digest, action, and exact key before any
mutation and writes an apply intent plus durable receipt.

Supersession or abandonment proof must assert all of the following and include
durable evidence paths:

- the packet is not confirmed active;
- no valid replacement owns the lineage;
- no native create is unrecorded;
- no active heartbeat depends on the packet;
- the selected agent, lineage, and rollover IDs match throughout.

Cleanup additionally requires the exact confirmed successor, exact predecessor
archive proof, explicit heartbeat-retirement authorization, and exact heartbeat
retirement proof. One lineage's proof never authorizes another lineage's
cleanup.

## Migration

Migration scans versioned lease files and immutable task-family plans. Planning
is read-only. Apply refuses corrupt inputs, preserves historical proof paths and
receipts, appends a migration event, and writes a migration receipt. It never
rewrites or deletes legacy history.
