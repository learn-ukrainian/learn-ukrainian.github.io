---
name: "task-family-manager"
description: Inspect, rename, archive, restore, or clean an exact Codex task family using native tools and verified resource proofs.
---

# Task Family Manager

Use this skill when a user wants to inspect or operate on a Codex task family. Identity always comes from exact task UUIDs and typed relations; titles are display text only.

The repository package plans and verifies operations. Codex app tools perform task mutations. Never write Codex SQLite directly, call private app APIs, infer membership from similar titles, or treat archive as cancellation.

## Native boundary

Use the available Codex app tools for their supported actions:

- `list_threads` and `read_thread` for visible task state and the pinned inventory;
- `list_archived_threads` for paginated archived inventory when exposed by the live schema;
- `set_thread_title` for one exact rename;
- `set_thread_archived` for one exact archive or restore;
- `handoff_thread` and `get_handoff_status` only when handoff work is requested;
- `navigate_to_codex_page` only when the user asks to open a task.

Check the live tool schema before making capability claims. `list_threads`
exposes `pinnedThreads`, and `list_archived_threads` exposes archived inventory;
page as required and use exact returned IDs. Neither titles nor pin/archive
inventory establish typed family membership or an atomic batch receipt. The
local bridge still performs bounded, read-only SQLite reconciliation after each
native mutation. `--db auto` discovers a compatible database fail-closed; an
explicit database path is also accepted. If a tool is unavailable, report that
specific capability as unknown and preserve affected resources.

Runtime packets, rollover leases, and automations are preservation-only locally. For finish-and-clean, record a tool-backed terminal task `status`. Any selected rollover endpoint also needs `rollover_cleanup_eligible: "true"` plus `rollover_cleanup_proof`; any `automation_id` needs `automation_cleanup_eligible: "true"` plus `automation_cleanup_proof`. Missing proof blocks cleanup. Even with proof, the local executor records retirement as deferred and preserves the evidence because this local executor does not implement native retirement. Check live tool support separately; it does not bypass these proof gates.

## Choose the operation

First read [manifest and inspection](references/manifest.md) for exact family
identity and planner preconditions. Then read only the requested operation:

- [Rename](references/rename.md): immutable preview, exact names, sequential readback.
- [Archive or finish-and-clean](references/archive-cleanup.md): reversible archive
  or proof-gated removal of exact family resources; these are distinct operations.
- [Restore and receipts](references/restore-receipts.md): exact restoration and
  reporting of persisted operations; also read this for the final receipt.

Use repository-root command paths. Show the concrete preview before mutation.
Existing user authorization remains valid; unresolved identity, scope, or proof
stops only the dependent action. Stop on the first reconciliation mismatch.
Archive never means cancellation or proof of task completion. Never remove
resources without the executor's exact ownership, lifecycle, and cleanup proof.
