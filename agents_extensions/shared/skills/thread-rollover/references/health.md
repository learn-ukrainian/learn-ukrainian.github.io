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
