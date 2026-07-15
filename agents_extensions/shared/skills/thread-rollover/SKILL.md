---
name: thread-rollover
description: Prepare, resume, validate, and confirm a durable Codex thread rollover with the repository's strict continuity packet. Use when a Codex task approaches context exhaustion, SessionStart reports a pending or resumed rollover, or a replacement task must prove continuity before predecessor cleanup.
---

# Thread Rollover

Use `--agent codex` for every Codex command. Never fork, continue, copy provider
history, or select a task by title. The repository owns the durable transition
plan and receipts; the app-capable agent owns the native create/title/archive
calls. Repo-local Python never writes Codex state directly.

## Health

Run this read-only command at a session boundary. It returns `status: none`, one
validated `pending_start`/`resumed` packet, or exit 2 with explicit corruption,
identity, path, or ambiguity evidence.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py detect --agent codex
```

For a known packet, inspect health without changing it.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py check --agent codex --lineage-id <lineage-id>
```

## Rollover

Prepare only from the active Codex thread; this reserves every packet path and
keeps cleanup false. Supply durable epic, goal, and phase metadata together when
known; `--next-phase` is optional.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent codex \
  --active-thread-id "$CODEX_THREAD_ID" \
  --epic-title "<durable epic label>" \
  --goal "<current goal>" \
  --phase "<current phase>" \
  --next-phase "<next phase>"
```

`prepare` returns `intended_title`, exact native lifecycle IDs, and a
`create_thread` action. The title is derived from the supplied metadata, for
example `Curriculum lifecycle — P5 CI unblock → P6`. If those fields are not
available, the fallback includes the durable lineage and generation. Never use
`Resume codex rollover` or another generic title.

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

If a native tool is absent or fails, use `record-native-result --failed
--error "..."` for the attempted action and stop. On retry, run
`native-action` first. It reconciles exact native state before authorizing a
mutation and will not repeat an acknowledged action while read-back is pending.

## Resume and confirm

In the fresh task, use the exact paths returned by `detect` or `resume`. First
bind the replacement thread, then read the handoff and write a truthful durable
semantic snapshot at the reserved `semantic_snapshot_path`. Its records must be
exactly 3 goals, 3 decisions/rationales, 2 negative constraints/prohibitions, and
2 next actions with real allowed `source_ref` values; never use Git, GitHub, or
Monitor facts and never pad anchors.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py resume --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> --replacement-thread-id "$CODEX_THREAD_ID"
.venv/bin/python scripts/context_canary.py mint --snapshot <semantic_snapshot_path> --out <strict_probe_path>
.venv/bin/python scripts/context_canary.py questions --probe <strict_probe_path> --out <strict_questions_path>
.venv/bin/python scripts/context_canary.py score --probe <strict_probe_path> --answers <strict_answers_path> --expected-lineage-id <lineage-id> --expected-rollover-id <rollover-id> --verdict <strict_verdict_path>
.venv/bin/python scripts/orchestration/thread_handoff_canary.py --rollover-id <rollover-id> --replacement-thread-id "$CODEX_THREAD_ID" --challenge <canary_challenge> --proof-file <canary_proof_path>
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent codex --lineage-id <lineage-id> --rollover-id <rollover-id> --new-thread-id "$CODEX_THREAD_ID" --canary-proof <canary_proof_path> --strict-probe <strict_probe_path> --strict-verdict <strict_verdict_path>
```

Create `strict_answers_path` only from the questions-only view after restoring
context. `confirm-started` unlocks cleanup only when the separate challenge proof
and strict verdict both bind to the exact reserved packet paths and pass 10/10.

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
