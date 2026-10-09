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

Fresh native threads use the same envelope with `origin: "fresh"`, the exact
current native `task_id`, and `lifecycle_state: "active"`. They omit
`predecessor_task_id`, `replacement_task_id`, `lineage_id`, and `generation`
entirely. They do not resume or rename a replacement, claim a lease, or assert
rollover ancestry. The schema rejects mixed fresh/rollover envelopes, blank or
whitespace-containing fresh task IDs, legacy fallback, and an unknown terminal
goal. Rollover envelopes retain their existing required fields and constraints;
null or blank lineage, a missing predecessor, and generation zero remain invalid.

Initialize a fresh driver's ledger through the supported closeout CLI. Supply
the native harness's actual current thread ID as `NATIVE_TASK_ID`; the issue,
stream epic, role, and task family must match the driver's assignment:

```bash
.venv/bin/python -m scripts.orchestration.task_closeout init \
  --fresh-task-id "$NATIVE_TASK_ID" \
  --repository org/repo --stream-epic 10 --issue 42 \
  --semantic-title "Enforce task closeout" \
  --task-family infrastructure --role driver --terminal-goal merge \
  --ac-policy ac-policy.json --author-family codex \
  --required-check "CI Gate"
```

Use the task-prescribed interpreter in linked worktrees. The AC policy maps
the issue's stable criterion IDs to their due states and required evidence
types, as specified in `task-lifecycle-closeout.md`. Initialization reads live
issue criteria and verifies registered stream membership before writing the
ledger; it does not mutate GitHub. The JSON result contains `state_file` and
the complete identity carrier. `--identity-file identity.json` remains supported
for both schema-valid forms. `--reuse` preserves an existing ledger and its
evidence, but a fresh identity must match that ledger's full persisted identity;
it cannot adopt another thread's ledger even for the same issue.

Pass the returned `state_file` as `--lifecycle-file` to the existing dispatch
command. Read the carrier or reconcile observations with:

```bash
.venv/bin/python -m scripts.orchestration.task_closeout carrier --state-file "$LEDGER"
.venv/bin/python -m scripts.orchestration.task_closeout reconcile --state-file "$LEDGER"
```

Carriers retain the exact fresh `task_id`. Reconciliation reads GitHub/Git
authority and appends a local receipt; it does not authorize remote mutations
or supply independent review, CI, or delivery proof.

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
