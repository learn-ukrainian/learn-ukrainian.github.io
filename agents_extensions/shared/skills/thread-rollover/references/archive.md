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
