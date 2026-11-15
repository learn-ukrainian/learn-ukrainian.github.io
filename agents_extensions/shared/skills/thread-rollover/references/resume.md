## Resume and confirm

In the fresh task, use the exact paths returned by `detect` or `resume`. First
finish exact native title reconciliation or the honest unsupported-adapter
fallback. If that prerequisite is pending, read the title reconciliation and
unsupported-adapter procedures in [preparation](prepare.md) and finish only the
required action before resuming; never create another replacement merely to
resume. Then bind the replacement task, read the durable handoff, and confirm
the exact replacement.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py resume --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> --replacement-thread-id <exact-replacement-task-id>
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> --new-thread-id <exact-replacement-task-id>
```

Repeated exact resume and confirmation are idempotent; a different replacement
ID fails closed.
