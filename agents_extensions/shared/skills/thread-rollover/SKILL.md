---
name: thread-rollover
description: Prepare, resume, validate, and confirm a durable Codex thread rollover with the repository's strict continuity packet. Use when a Codex task approaches context exhaustion, SessionStart reports a pending or resumed rollover, or a replacement task must prove continuity before predecessor cleanup.
---

# Thread Rollover

Use `--agent codex` for every Codex orchestrator command. Never fork, continue,
copy provider history, or select an ambiguous task. Use the Codex app to create a
fresh task titled `Rollover <lineage-id> <rollover-id>` after `prepare` prints both IDs.

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
keeps cleanup false.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent codex --active-thread-id "$CODEX_THREAD_ID"
```

Read the resulting `handoff_file`, then create the fresh Codex app task with the
unique title above. Do not use a fork, copied provider history, or an ambiguous
existing task.

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
