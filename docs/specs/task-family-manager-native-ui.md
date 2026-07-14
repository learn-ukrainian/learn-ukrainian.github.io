# Task Family Manager Native UI and API Specification

Status: target upstream contract; not implemented by the current Codex app.

Issue #5140 needs task-family lifecycle management that is safe at the app boundary. The repository implementation is the current fallback. This document defines the native inventory, mutation, accessibility, and receipt contract that would remove the fallback's dependence on a fragile read-only SQLite bridge.

## Current capability boundary

The current app can list visible tasks, read a task, rename one task, archive or restore one task, hand off a task, and report handoff status. It does not expose:

- an inventory that includes archived tasks;
- readable or mechanically enforceable pin state;
- typed parent, reviewer, handoff, replacement, and rollover relations;
- task versions or compare-and-swap batch operations;
- a native family preview, receipt, or restore operation;
- Git/worktree ownership and cleanup authority;
- an irreversible purge token.

The local fallback therefore uses exact task UUIDs and explicit typed manifest relations, performs native task mutations one at a time, and verifies each result through a bounded read-only SQLite bridge. The database is not a supported public interface. The fallback never writes it and must fail closed when its schema, identity, title, `cwd`, host, or archive state is ambiguous.

## Native domain model

### Identity and membership

Task UUID is the only identity key. Titles are mutable display text and must never establish family membership.

A family graph contains:

- exactly one root;
- typed `subagent_of`, `reviewer_for`, `handoff_of`, `replacement_of`, and `rollover_generation_of` edges;
- optional `issue_or_pr_member` annotations that are display-only unless explicitly promoted;
- per-edge provenance, source system, observed time, and version;
- active and archived members in the same inventory;
- explicit exclusion records for similar titles or shared issues outside the graph.

The service rejects unknown endpoints, conflicting parent-like relations, cycles, incompatible project roots, and zero or multiple roots.

### Task state

Each task record exposes:

- UUID, version/ETag, title, active/archive state, pin state, and run status;
- role and rollover generation derived from typed relations;
- project, worktree, branch, PR, model, harness, local/remote host, and `cwd` metadata;
- whether the task is running, waiting, completed, blocked, or unavailable;
- capabilities allowed for the current actor.

Pin state is tri-state only while migrating old data: `pinned`, `unpinned`, or `unknown`. Native operations protect `pinned` and `unknown` tasks by default. Unknown pin state requires an explicit task-specific confirmation; a family-wide Boolean override is invalid.

### Operations

The native model distinguishes:

1. Rename — reversible display mutation.
2. Archive — reversible visibility mutation; transcripts and Git resources remain.
3. Finish and clean — archive followed by exact proof-gated retirement of eligible local resources.
4. Purge — irreversible transcript deletion, unavailable until the upstream app provides a separately authenticated, short-lived purge token.

Archive does not cancel or halt an active task. The UI must say this directly and offer a separate supported stop/cancel action when one exists.

## Native API contract

All examples in this section are normative target APIs, not current endpoints.

### Read a family graph

`GET /api/v1/task-families/{family_id}?include_archived=true`

```json
{
  "family_id": "family-uuid",
  "version": "W/\"family-etag\"",
  "root_task_id": "task-uuid-1",
  "nodes": [
    {
      "task_id": "task-uuid-1",
      "version": "W/\"task-etag\"",
      "title": "Implement lifecycle",
      "archived": false,
      "pin_state": "unpinned",
      "status": "completed",
      "roles": ["Lead"],
      "generation": 0,
      "environment": {
        "project": "/absolute/project",
        "cwd": "/absolute/project",
        "worktree": null,
        "branch": "main",
        "pr": null,
        "model": "gpt-5.6-sol",
        "harness": "codex",
        "host": "local",
        "local": true
      },
      "capabilities": ["rename", "archive", "restore"]
    }
  ],
  "relations": [
    {
      "source_id": "task-uuid-2",
      "target_id": "task-uuid-1",
      "type": "subagent_of",
      "evidence": "native spawn edge",
      "source": "codex_app",
      "observed_at": "2026-07-14T00:00:00Z",
      "version": "W/\"edge-etag\""
    }
  ],
  "excluded": [
    {
      "task_id": "task-uuid-9",
      "reason": "outside exact-ID family graph"
    }
  ]
}
```

The response must not silently omit archived, pinned, remote, or temporarily unavailable members. Unavailable hosts are returned as explicit blockers.

### Preview an operation

`POST /api/v1/task-families/{family_id}/operation-previews`

```json
{
  "kind": "rename",
  "selected_task_ids": ["task-uuid-1", "task-uuid-2"],
  "base_title": "Lifecycle complete",
  "pin_unknown_confirmations": [],
  "expected_family_version": "W/\"family-etag\""
}
```

The response freezes exact inputs and returns:

```json
{
  "operation_id": "operation-uuid",
  "plan_digest": "64-lowercase-hex-digest",
  "expires_at": "2026-07-14T00:15:00Z",
  "counts": {
    "included": 2,
    "excluded": 1,
    "selected": 2,
    "blocked": 0
  },
  "rename_map": [
    {
      "task_id": "task-uuid-1",
      "expected_version": "W/\"task-etag\"",
      "old_title": "Implement lifecycle",
      "new_title": "Lifecycle complete [Lead]",
      "roles": ["Lead"]
    }
  ],
  "resource_decisions": [],
  "blockers": []
}
```

The preview must include every selected task, excluded task, title mapping, pin decision, and local resource decision. Standardized titles preserve role and generation information and fit the app's persisted title limit. A changed family/task/resource version invalidates the digest.

### Execute a preview

`POST /api/v1/task-families/{family_id}/operations`

Headers:

- `Idempotency-Key: <operation-uuid>`
- `If-Match: <plan-digest>`

```json
{
  "operation_id": "operation-uuid",
  "plan_digest": "64-lowercase-hex-digest",
  "actor": "actor-id",
  "confirmed_task_ids": ["task-uuid-1", "task-uuid-2"]
}
```

Native task-only rename/archive/restore batches should be transactional when all members live in one authority. When hosts or authorities prevent transactionality, execution is sequential, stops at the first failed mutation, and returns an exact partial receipt and resume token. Replaying the same idempotency key never repeats an already verified mutation.

The API uses these target failure classes:

- `409 Conflict` for family/task/resource version drift;
- `412 Precondition Failed` for a changed or expired digest;
- `422 Unprocessable Content` for graph, selection, pin, or proof blockers;
- `503 Service Unavailable` when an owning host cannot be verified.

### Read a receipt

`GET /api/v1/task-families/{family_id}/operations/{operation_id}`

```json
{
  "operation_id": "operation-uuid",
  "state": "partially_applied",
  "plan_digest": "64-lowercase-hex-digest",
  "planned": [],
  "actual": [],
  "skipped": [],
  "failures": [],
  "restoration": [],
  "retained_resources": [],
  "resume_token": "opaque-single-use-token",
  "events": []
}
```

Every action records task/resource ID, expected and observed versions, before/after state, actor, timestamp, reason, and recovery instruction. Receipts are durable and readable after tasks are archived.

### Restore

`POST /api/v1/task-families/{family_id}/operations/{operation_id}/restore`

Restore takes exact task IDs and current versions. It is idempotent, uses the same read-back rules, and appends restoration actions to the original receipt. Git resources removed by finish-and-clean are restored only from a verified retained snapshot and only when the receipt declares them restorable.

### Finish-and-clean proof

The app may delegate Git execution to a native privileged service, but the preview and receipt must expose each proof. A local branch is deletable only when all of the following remain true immediately before mutation:

- its PR is merged and has a merge SHA;
- the PR head matches the exact local branch head;
- the remote branch is absent;
- no worktree uses the branch;
- a verified recovery bundle contains the head and its digest matches;
- Git lock files are absent at both planning and mutation time;
- the primary checkout is on an up-to-date protected base;
- the exact branch is not protected or unknown.

Delete only that branch. Never invoke a post-merge hook, alias, broad gone-upstream pruner, remote branch deletion, forced worktree removal, auto-stash/commit, or lock deletion. A surviving remote branch, unknown protection, dirty worktree, active task, or changed proof blocks cleanup.

Purge requires a separate target endpoint and short-lived token scoped to exact task UUIDs. Until that authority exists, clients must omit purge controls entirely.

## Native user experience

### Family tree and badges

The task page offers `Current task`, `Task family`, and `Project` scopes. Family scope renders the exact graph as an accessible tree with:

- readable role and generation labels;
- status, model, harness, project, worktree, branch, PR, local/remote, archive, and pin badges;
- explicit edge labels for worker, reviewer, handoff, replacement, and rollover relations;
- an excluded-items disclosure explaining why similar tasks are outside the family.

The tree uses `role="tree"`, `role="treeitem"`, `aria-level`, `aria-expanded`, and `aria-selected`. Arrow keys navigate and expand/collapse; Home/End move to first/last visible node; Space toggles selection; Enter opens the task. Focus never moves because background status changed.

### Consolidated inbox

Family and project scopes include a consolidated inbox for approvals, failures, blocked tasks, review requests, and unavailable hosts. Items show task identity, role, age, owner, requested action, and next step. Filters and counts remain keyboard and screen-reader accessible.

### Selection and previews

Batch selection is explicit. The UI never selects hidden archived or pinned tasks implicitly. Selection controls and action buttons announce exact counts, for example `Archive 3 selected tasks`. Count changes use a polite live region.

Before mutation, a preview dialog shows:

- included, excluded, selected, and blocked counts;
- old-to-new title mappings;
- pin and running-state warnings;
- transcripts and Git resources retained or removed;
- irreversible steps and unavailable restore paths;
- a typed confirmation only for irreversible purge, if purge is supported.

Archive confirmation says that archiving hides tasks but does not halt active runs. Finish-and-clean confirmation separates reversible task archiving from proof-gated local resource deletion. A short toast or timed undo is never the sole safety mechanism.

### Progress, failure, and receipts

Execution displays one row per task/resource with pending, applied, verified, skipped, failed, or restored status. Partial failure leaves successful rows intact, stops further unsafe mutations, and offers `Retry verification`, `Resume remaining`, and `Restore verified changes` only when the receipt authorizes them.

The final receipt is reachable from the family, each affected task, and the consolidated inbox. It reports planned versus actual actions, exclusions, skipped resources and reasons, failures, recovery steps, restoration results, retained resources, and immutable operation identity.

## Local-to-native acceptance map

| Capability | Repository fallback | Required native behavior |
| --- | --- | --- |
| Exact inventory | Explicit manifest and exact UUID graph | Versioned graph including archived/pinned/remote tasks |
| Relations | Typed manifest evidence | Native typed provenance edges |
| Pin safety | Per-task unknown-state confirmation | Readable, mechanically enforced pin state |
| Preview | Immutable JSON plan and SHA-256 digest | Versioned server preview with CAS expiry |
| Rename/archive/restore | Native one-task action plus read-only DB reconciliation | Idempotent batch action plus native read-back |
| Partial failure | Stop, persist receipt, retry safely | Resume token and exact durable receipt |
| Cleanup | Local exact proof-gated executor | Native authority with the same or stronger proof |
| Purge | Not implemented | Token-scoped upstream-only operation |
| Accessibility | Skill/CLI output | Keyboard-accessible tree, counts, inbox, previews, and receipts |

Native acceptance requires tests for exact-ID discovery, archived/pinned inventory, role derivation, keyboard navigation, screen-reader names, selection counts, digest drift, partial failure, retry idempotency, restore, and every proof-gated cleanup blocker.
