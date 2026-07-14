# Task Family Manager Native UI & API Specification

This document specifies the target native UI and API contract for the Task Family Manager, implementing the R3 architecture approved for Issue #5140.

> **NOTE:** The Native APIs described below are currently **UNAVAILABLE**. They specify the target upstream native implementation. Local agents must use the fallback Skill implementations until the upstream APIs are deployed. Do not claim native implementation exists locally.

## 1. Native API Contract

### 1.1 Family Graph & Identity API

`GET /api/v1/task-families/{family_id}/graph`

**Response:**

```json
{
  "family_id": "string",
  "inventory": {
    "active": ["task_id", "..."],
    "archived": ["task_id", "..."],
    "pinned": ["task_id", "..."]
  },
  "provenance": {
    "reviewer_links": [{"source": "task_id", "target": "task_id", "type": "cross-family"}],
    "handoff_links": [],
    "replacement_links": [],
    "rollover_links": []
  },
  "environment": {
    "project": "string",
    "branch": "string",
    "pr": "string",
    "worktree": "string",
    "model": "string",
    "status": "string"
  }
}
```

### 1.2 Batch Operations (Preview & Execute)

Atomic batch APIs for rename, archive, restore, and finish enforce CAS (Compare-and-Swap) and idempotency.

**Preview Request:**

`POST /api/v1/task-families/{family_id}/preview`

```json
{
  "action": "archive",
  "tasks": ["task_1", "task_2"]
}
```

**Execute Request:**

`POST /api/v1/task-families/{family_id}/execute`

```json
{
  "action": "archive",
  "plan_digest": "sha256:...",
  "branch_proof": "exact_branch_name",
  "confirmation_token": "optional_token_for_purge"
}
```

**Response (Receipt):**

```json
{
  "status": "partial_success",
  "success_count": 1,
  "fail_count": 1,
  "results": [
    {"task_id": "task_1", "status": "success"},
    {"task_id": "task_2", "status": "failed", "error": "permission_denied"}
  ]
}
```

**Error Semantics:**

- `409 Conflict`: Digest mismatch (CAS failure).
- `428 Precondition Required`: Missing branch proof or confirmation token.
- `403 Forbidden`: Attempted broad upstream prune (not allowed).

## 2. Accessible Native UI

### 2.1 Navigation and Tree

- **Accessible Family Tree**: Tree structure mapping the family graph. Includes `role="tree"` and `role="treeitem"`.
- **Keyboard Behavior**: `Up/Down` navigates siblings, `Left/Right` collapse/expand nodes. Screen-readers announce tree hierarchy correctly.
- **Badges**: Status and Role badges (🟢 Active, 🔴 Failed), plus context badges (Branch, PR, Model, Local, Worktree).
- **Scope Selector**: Dropdown to shift focus between `Current Task`, `Task Family`, and `Project Scope`.
- **Title Templates**: Auto-formats incoming tasks as `[Verb] [Entity] - [Context]`.

### 2.2 Batch Actions & Inboxes

- **Consolidated Inbox**: Central pane aggregating all approval requests, blocked tasks, and error tasks across the active scope.
- **Explicit Counts**: Selection interfaces update dynamically (`aria-atomic="true"`). Batch action buttons explicitly state counts (e.g., "Archive 3 selected tasks").

### 2.3 Safety, Receipts, and Cleanup

- **Summarize-Before-Archive**: Modal lists aggregate stats (e.g., active tasks to be halted) before confirmation.
- **Blocker Preview**: Dry-run modal clearly itemizing blockers and data marked for deletion before execution.
- **Receipts/Restoration**: Destructive actions return a clear receipt of successes/failures, providing an explicit, recoverable restore path.
- **Destructive Safety**: Follows exact R3 contract. Short undo is NOT used as a safety mechanism for destructive actions. Cleanup relies strictly on exact-branch proof-gated cleanup. No broad gone-upstream pruner is implemented.

## 3. Local vs Native Acceptance Map

| Capability | Local CLI/Skill (Current) | Native API/UI (Target) |
| --- | --- | --- |
| **Inspection** | `python -m scripts.orchestration.task_family inspect` | `GET /api/v1/task-families/.../graph` |
| **Archiving** | Loop `set_thread_archived` with DB read-back | Atomic `POST /execute` (archive) |
| **Renaming** | Loop `set_thread_title` with DB read-back | Atomic `POST /execute` (rename) |
| **Receipts** | Skill persists JSON outcome locally | API returns partial-success receipt |
| **Cleanup** | Exact-branch proof CLI verification | Confirmation tokens + precise proof |
| **Pinned State** | Explicitly unknown, operator manual override | Typed pinned inventory |
