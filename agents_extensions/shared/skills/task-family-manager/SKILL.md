---
name: "task-family-manager"
description: "Inspect, rename, archive, finish, and clean up task families using exact inclusion and strict UI semantics."
---

# Task Family Manager

Use this skill to inspect, rename, archive, finish, and clean up task families. Never infer family from titles. Compose operations via the deterministic Python package.
Currently available Codex app tools for mutation/reading: `list_threads`, `read_thread`, `set_thread_title`, `set_thread_archived`, `handoff_thread`, `get_handoff_status`, `navigate_to_codex_page`. Use create/fork only when explicitly requested. Titles never prove membership.

## Provenance Evidence

Establish family membership using exact task IDs, structured fork/source responses, native spawn edges when present, and explicit typed manifest links. Note that `list_threads` excludes archived tasks and exposes no pin inventory.

## Minimal Manifest Example

Build and validate an explicit versioned manifest (`manifest.json`):

```json
{
  "version": "1.0",
  "project_cwd": "/path/to/project",
  "status_metadata": "active",
  "tasks": [
    {
      "id": "task_1",
      "role": "root",
      "evidence": "spawned from prompt"
    },
    {
      "id": "task_2",
      "role": "worker",
      "evidence": "forked from task_1"
    },
    {
      "id": "task_3",
      "role": "reviewer",
      "evidence": "spawn edge target from task_2"
    },
    {
      "id": "task_4",
      "role": "handoff",
      "evidence": "handoff thread from task_3"
    },
    {
      "id": "task_5",
      "role": "replacement",
      "evidence": "replacement for task_2"
    }
  ]
}
```

## Procedural Workflow

Follow this exact step sequencing:
1. Preview the operation using the CLI.
2. Display counts, mapping, and blockers to the user.
3. Apply per-task native tool mutation (e.g., `set_thread_title` or `set_thread_archived`).
4. Perform immediate read-only reconciliation and persist the result (receipt).
5. Stop on failure; retry idempotently.
6. Apply cleanup only after app targets verify.

### 1. Inspect Family

Preview family state, identities, blockers, and exact counts before mutation:

```bash
.venv/bin/python -m scripts.orchestration.task_family inspect --manifest manifest.json --json
```

### 2. Pinned State & Inclusion

Pinned state is unreadable via CLI. Mechanical enforcement is native-only. You must:
1. Require exact per-task inclusion in the manifest file.
2. Demand explicit operator affirmation that pin state is unknown using `--confirm-pin-unknown true`.

### 3. Rename Tasks

1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-rename --repo-root . --manifest manifest.json --operation-id op_123 --base-title "New Title" --select-task task_1 --actor agent --confirm-pin-unknown true --json
```
2. **Apply**: Call the native tool `set_thread_title` for each included task.
3. **Reconcile**: Perform a read-back to verify. Stop on partial failure, persist to a receipt file.
```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-title --repo-root . --family-id fam_123 --operation-id op_123 --plan-digest sha256:abc... --db auto --task-id task_1 --cwd /path --expected-title "New Title"
```

### 4. Archive Family

Separate archive-only (reversible, transcripts/Git retained) from finish-and-clean. Do not imply archive halts running tasks.

1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-archive --repo-root . --manifest manifest.json --operation-id op_123 --lineage-id lin_123 --base-title "Archiving" --db auto --select-task task_1 --actor agent --confirm-pin-unknown true --json
```
2. **Apply**: Call the native tool `set_thread_archived` for each included task.
3. **Reconcile**:
```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-archive --repo-root . --family-id fam_123 --operation-id op_123 --db auto --task-id task_1 --cwd /path --expected-title "Archiving"
```

### 5. Finish and Clean

Irreversible cleanup (proof-gated Git). Purge is not implemented. Never broad prune, remote-delete, force-remove worktrees, auto-commit/stash, delete locks, or call private DB writes.

1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-cleanup --repo-root . --manifest manifest.json --operation-id op_123 --lineage-id lin_123 --base-title "Cleanup" --db auto --select-task task_1 --actor agent --confirm-pin-unknown true --json
```
2. **Apply**: Execute the cleanup securely using the exact plan digest from preview.
```bash
.venv/bin/python -m scripts.orchestration.task_family apply-cleanup --repo-root . --family-id fam_123 --operation-id op_123 --lineage-id lin_123 --plan-digest sha256:abc... --json
```

### 6. Receipt and Restoration

Generate a receipt of the operation:
```bash
.venv/bin/python -m scripts.orchestration.task_family receipt --repo-root . --family-id fam_123 --operation-id op_123 --json
```

If restore is needed:
1. Call `set_thread_archived` (to unarchive).
2. Reconcile restore:
```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-restore --repo-root . --family-id fam_123 --operation-id op_123 --db auto --task-id task_1 --cwd /path --expected-title "Restored"
```
