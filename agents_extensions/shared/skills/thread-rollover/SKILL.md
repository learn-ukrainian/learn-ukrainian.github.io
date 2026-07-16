---
name: thread-rollover
description: Prepare, name, resume, validate, and confirm a durable fleet-wide task rollover with the shared task-identity envelope and strict continuity packet. Use when any supported agent or harness approaches context exhaustion, reports pending or resumed rollover state, must reconcile a replacement title, or must prove continuity before predecessor cleanup.
---

# Thread Rollover

Use the exact deployed `--agent` and `--harness` for the active runtime. Never
fork, continue, copy provider history, or select a task by title. The repository
owns the fleet-wide `task-identity.v1` envelope, transition plan, and receipts.
An app-capable adapter owns native create/title/archive calls; an unsupported
adapter records the shared carrier fallback and never claims a native rename.
Repo-local Python never writes provider state directly.

## Health

Run this read-only command at a session boundary. It returns `status: none`, one
validated `pending_start`/`resumed` packet, or exit 2 with explicit corruption,
identity, path, or structured ambiguity evidence. Multiple candidates include
semantic title, issue, lineage/generation, rollover and task IDs, timestamps,
confirmation states, and a safe exact-ID resolution; never choose one by order.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py detect --agent codex
```

For a known packet, inspect health without changing it.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py check --agent codex --lineage-id <lineage-id>
```

When more than one unrelated packet is pending, generic detection stays
read-only and returns actionable candidates. Select the intended packet by
exact ID; selectors are ANDed and titles never select a packet.

```bash
.venv/bin/python scripts/orchestration/rollover_registry_cli.py detect \
  --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id>
.venv/bin/python scripts/orchestration/rollover_registry_cli.py detect \
  --agent codex --source-thread-id <predecessor-task-id>
```

Audit all agents without mutation:

```bash
.venv/bin/python scripts/orchestration/rollover_registry_cli.py audit
```

Use `reconcile-exact --snapshot <authoritative-json>` before acting on an
unrecorded native successor or confusing cleanup state. Reconciliation requires
exact native IDs, title/readback receipts, confirmation proof, and automation
facts; a title or missing local process is never proof of creation or cleanup.
It is read-only unless `--apply` is explicit.

## Rollover

Prepare only from the active task; this reserves every packet path and keeps
cleanup false. New callers supply the one stream epic, scoped issue when
applicable, semantic title, family, role, terminal goal, and actual harness.
Legacy epic/goal/phase flags remain migration inputs, not the canonical title.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent <agent> --harness <harness> \
  --active-thread-id "<exact-active-task-id>" \
  --stream-epic <epic-number> \
  --issue-number <issue-number> \
  --semantic-title "<specific semantic task title>" \
  --task-family <task-family> \
  --role "<role>" \
  --terminal-goal <merge|deploy|certify>
```

`prepare` returns the complete identity envelope, title transition, identity
receipt path, and the next exact adapter action. Issue-backed visible titles are
`#<issue> — <semantic title>`; otherwise they are
`<task family> — <semantic title>`. UUIDs, lineage, rollover, and generation
remain metadata. Blank, generic, or identifier-only titles fail before prepare.
Legacy packets without identity receive a deterministic semantic fallback with
migration provenance and `terminal_goal: unknown`; explicit callers cannot use
that legacy-only value. The visible title never exposes raw runtime IDs.

In an app-capable task:

1. Ask the receipt whether native creation is authorized:

   ```bash
   .venv/bin/python scripts/orchestration/thread_handoff.py native-action \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --action create
   ```

2. Only when it returns `needs_native_action: true`, call native
   `create_thread` once with the returned bootstrap prompt and the local project
   environment. A queued `clientThreadId` is not an exact task identity; wait
   for a real `threadId` or record a failure and stop. Immediately persist the
   successful result before binding, so a crash cannot authorize a duplicate:

   ```bash
   .venv/bin/python scripts/orchestration/thread_handoff.py record-native-result \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --action create --succeeded \
     --evidence "create_thread returned threadId <exact-thread-id>"
   ```

3. Bind that exact replacement to the exact predecessor and persist both typed
   relations:

   ```bash
   .venv/bin/python scripts/orchestration/thread_handoff.py register-created \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --replacement-thread-id <exact-thread-id> \
     --evidence "native create_thread result <exact-thread-id>"
   ```

4. Ask the receipt for the exact title mutation:

   ```bash
   .venv/bin/python scripts/orchestration/thread_handoff.py native-action \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --action title
   ```

   Only when it returns `needs_native_action: true`, call native
   `set_thread_title` with its exact `arguments`. Persist the native result
   before read-back, then reconcile it:

   ```bash
   .venv/bin/python scripts/orchestration/thread_handoff.py record-native-result \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --action title --succeeded --evidence "set_thread_title acknowledged"
   .venv/bin/python scripts/orchestration/thread_handoff.py reconcile-native \
     --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
     --action title
   ```

If a supported native adapter is absent or fails, use
`record-native-result --failed --error "..."` for the attempted action and
stop. On retry, run
`native-action` first. It reconciles exact native state before authorizing a
mutation and will not repeat an acknowledged action while read-back is pending.
Readback compares raw strings without whitespace normalization. An
acknowledgement without exact task-ID and title readback never unlocks resume or
confirmation, and a late failed retry cannot regress a durable success.

For a harness that declares no native title mutation/readback support, create
or bind its exact replacement through that harness, then record the honest
fallback before resume:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py bind-replacement \
  --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> \
  --replacement-task-id <exact-task-id> \
  --evidence "<exact dispatch/harness binding receipt>"
```

The receipt must say mutation support is false and `attempted: false`. Carry
the exact visible title in the dispatch record, brief, ledger, inbox, monitor
API, and final receipt. Do not call `register-created`, `native-action --action
title`, or `reconcile-native`, and do not fabricate success for a missing
adapter.

Each prepared packet has its own deterministic native operation ID, even when
an explicit `prepare --force-new-replacement` stays in the same generation.
Forced preparation may supersede only an untouched predecessor intent: no
binding, create authorization, acknowledgement, actual action, or failure may
exist. The old immutable plan remains in place; an exact supersession document,
blocked receipt, and successor reference make retries fail closed. Never edit,
delete, or reuse an immutable receipt to resolve a collision.

For a legacy lease whose current packet references a pristine immutable plan
for a different rollover ID, do not create or fork a task. Repair the exact
receipt collision with app/operator evidence that `create_thread` was never
called:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py repair-native-intent \
  --agent codex --lineage-id <lineage-id> --rollover-id <current-rollover-id> \
  --evidence "App stopped before create_thread; exact receipt and binding are pristine."
```

The command persists the packet-specific transition first, marks only the exact
legacy intent `superseded_before_native_create`, and updates the lease last. It
is idempotent for the same exact successor and refuses ambiguous, partial, or
already-authorized native state. After success, begin again at `native-action
--action create`; the repair command itself performs no native mutation.

## Resume and confirm

In the fresh task, use the exact paths returned by `detect` or `resume`. First
finish exact native title reconciliation or the honest unsupported-adapter
fallback, then bind the replacement task, read the handoff, and write a truthful durable
semantic snapshot at the reserved `semantic_snapshot_path`. Its records must be
exactly 3 goals, 3 decisions/rationales, 2 negative constraints/prohibitions, and
2 next actions with real allowed `source_ref` values; never use Git, GitHub, or
Monitor facts and never pad anchors.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py resume --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> --replacement-thread-id <exact-replacement-task-id>
.venv/bin/python scripts/context_canary.py mint --snapshot <semantic_snapshot_path> --out <strict_probe_path>
.venv/bin/python scripts/context_canary.py questions --probe <strict_probe_path> --out <strict_questions_path>
.venv/bin/python scripts/context_canary.py score --probe <strict_probe_path> --answers <strict_answers_path> --expected-lineage-id <lineage-id> --expected-rollover-id <rollover-id> --verdict <strict_verdict_path>
.venv/bin/python scripts/orchestration/thread_handoff_canary.py --rollover-id <rollover-id> --replacement-thread-id <exact-replacement-task-id> --challenge <canary_challenge> --proof-file <canary_proof_path>
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> --new-thread-id <exact-replacement-task-id> --canary-proof <canary_proof_path> --strict-probe <strict_probe_path> --strict-verdict <strict_verdict_path>
```

Create `strict_answers_path` only from the questions-only view after restoring
context. `confirm-started` unlocks cleanup only when the separate challenge proof
and strict verdict both bind to the exact reserved packet paths and pass 10/10.
Repeated exact resume and confirmation are idempotent; a different replacement
ID fails closed.

## Archive the confirmed predecessor

After `confirm-started` succeeds, read the exact `predecessor_thread_id` through
the native app. Archive only if authoritative app state proves that exact task
is idle and unpinned. Never infer pin state from its absence: use `unknown` and
preserve the predecessor when the app does not expose it.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py native-action \
  --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> \
  --action archive --source-status idle --pin-state unpinned \
  --evidence "native read_thread/app state for exact predecessor UUID"
```

Only a response with `needs_native_action: true` authorizes native
`set_thread_archived` with the returned exact arguments. Then persist and
reconcile exactly as for title, using `--action archive`. Any missing proof,
unconfirmed replacement, title mismatch, ambiguous identity, running status,
pinned/unknown pin state, app/API absence, or partial failure leaves the exact
predecessor visible and records a retryable blocker. Unrelated tasks are never
archive candidates.

This archive step does not replace or weaken the existing automation cleanup
gate. Delete or pause an old heartbeat only after `confirm-started` reports
`old_automation_ready_to_delete: true`.

For stale or duplicate-looking packets, never delete the lease. Use the exact
registry maintenance commands. `finish-cleanup-exact`, `supersede-exact`, and
`abandon-exact` require immutable proof and separate `--plan` then `--apply`
invocations. Apply validates the selected agent/lineage/rollover, plan digest,
and action before mutation and writes a durable receipt. Age alone can warn but
cannot authorize a disposition. The complete proof contract is
`agents_extensions/shared/contracts/rollover-registry.md`.
