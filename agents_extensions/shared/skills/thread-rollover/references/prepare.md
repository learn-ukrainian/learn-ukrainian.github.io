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
