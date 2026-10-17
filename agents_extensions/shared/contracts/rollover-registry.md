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

Launcher and SessionStart detection exclude a `pending_start` packet prepared
before its lane's latest durable handoff. Candidates come from the stream
inventory and the agent's role handoff. Comparison uses whole UTC seconds:
clean tracked handoffs use their latest commit time, while local handoff edits
use modification time. Equal timestamps remain eligible. This is a read-only
auto-binding filter, reported as `skipped_stale`; the packet, lease and registry
are preserved for exact inspection or maintenance. Resumed packets still
require an explicit receipted disposition.

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
`finish-cleanup-exact`, `supersede-exact`, `abandon-exact`, and
`dispose-exited-successor-exact`. Cleanup,
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

### Exited successor disposition

`dispose-exited-successor-exact` is the runtime-backed maintenance exception for an
exited resumed or confirmed successor. It records `ABANDONED_WITH_PROOF`,
retains the last successful boundary and all packet and lease files, and uses
the existing immutable plan, lineage lock, apply intent and receipt. The
supersede and abandon commands still refuse confirmed successors.

The proof must contain exactly the selected `agent`, `lineage_id`,
`rollover_id`, UTC `captured_at`, nonempty `reason`, `assertions`,
`evidence_paths`, and `successor_exit`. Assertions must contain exactly
`selected_exact_ids_match`, `no_unrecorded_native_create`, and
`no_active_heartbeat_dependency`, all true. These retain the existing
maintenance guards; they do not independently establish successor exit.
`successor_exit` contains exactly `run_id`, `replacement_thread_id`, and
`runtime_digest`. The successor ID must match the registry binding.

Only the existing launcher's canonical
`.agent/claudex-supervisors/<run-id>/runtime.json` is admitted as exit evidence.
`evidence_paths` must contain only that relative path. The supervisor's runtime
validator must accept it, its `session_id` and `handoff_agent` must match the
bound successor and registry agent, its state must be `exited`, and its exit
code must be an integer. Its update timestamp must follow the recorded resume
or confirmation boundary and be no later than `captured_at`. `runtime_digest`
is SHA-256 of its canonical JSON using sorted keys, compact separators and
unescaped Unicode. Symlinked evidence is refused.

Planning never changes the selected record. Apply revalidates the durable
runtime, pinned proof digest and record digest under the lineage lock. The
intent pins the resulting record digest before publication; the receipt pins
that same digest. Identical retries return the same receipt. Crash recovery
can finish receipt publication only for the exact applied record. Changed
records or evidence require reconciliation rather than receipt replay.

Synthetic tests cover active or unknown exits, mismatched exact IDs, changed
evidence, record and receipt replay, interrupted publication, arbitrary evidence
paths, preserved lease bytes, and launcher cold start after disposition. They
also exercise the heartbeat and unrecorded-create guards and refusal of legacy
confirmed dispositions. Boundaries not tested are live provider exit, remote
supervisor storage, hostile writers with write access to canonical launcher or
registry state, and kernel power-loss durability. Other launchers without this
canonical durable runtime fail closed; process absence and copied snapshots
are not substitutes.

### Operator disposition of a legacy resumed successor

`dispose-legacy-resumed-exact` admits only an exact Codex `RESUMED` record
whose native creation is `legacy_or_unrecorded` and whose successor has no
supervisor runtime. This is an attributed operator disposition, not proof of
native exit. `dispose-exited-successor-exact` still refuses missing, active or
non-exited runtime evidence.

The proof contains exactly `agent`, `lineage_id`, `rollover_id`, UTC
`captured_at`, a nonempty operator `reason`, `assertions`, `evidence_paths`
and `operator_disposition`. Assertions contain only
`selected_exact_ids_match: true`. Evidence paths contain only the selected
record's preserved rollover lease path. `operator_disposition` contains exactly
`authority` (`operator` or `cto`), nonempty `actor_agent` and `actor_host_id`,
and the exact `replacement_thread_id`. Actor and host attribution follow the
launcher's attributed operator force-release convention. They remain in local
registry evidence, not public reports.

Planning and apply, including retries, refuse a live Codex process naming that
exact successor in an argument or an `--option=value` argument. They also refuse
a positive `heartbeat_at` for that successor's `owner_thread_id` in the lane's
canonical thread lease, regardless of its age. The registry's stored
`active_or_unknown` is not positive heartbeat evidence. Unavailable process
inspection and malformed or symlinked evidence refuse the operation. A
supervisor runtime for that successor, in any state, excludes this legacy path.

The operation uses the existing immutable plan, lineage lock, apply intent,
record digest and receipt mechanism to record `ABANDONED_WITH_PROOF`. It
preserves the `RESUMED` boundary, lease bytes and packet files. Detection then
excludes that exact terminal record. It neither deletes nor releases a lease.

## Migration

Migration scans versioned lease files and immutable task-family plans. Planning
is read-only. Apply refuses corrupt inputs, preserves historical proof paths and
receipts, appends a migration event, and writes a migration receipt. It never
rewrites or deletes legacy history.
