## Resume and confirm

In the fresh task, use the exact paths returned by `detect` or `resume`. First
finish exact native title reconciliation or the honest unsupported-adapter
fallback. If that prerequisite is pending, read the title reconciliation and
unsupported-adapter procedures in [preparation](prepare.md) and finish only the
required action before resuming; never create another replacement merely to
resume. Then bind the replacement task, read the handoff, and write a truthful durable
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
