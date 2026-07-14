---
name: task-family-manager
description: Inspect, rename, archive, finish, and clean up task families using exact inclusion and strict UI semantics.
---

# Task Family Manager

Use this skill to inspect, rename, archive, finish, and clean up task families. Never infer family from titles. Compose operations via the deterministic Python package.

## 1. Inspect Family

Preview family state, identities, blockers, and exact counts before mutation:

```bash
.venv/bin/python -m scripts.orchestration.task_family inspect --family-id <family-id>
```

Use `list/read/create/fork context`, `handoff status`, and navigation tools by their exact IDs as appropriate to supplement the inspection.

## 2. Pinned State & Inclusion

Pinned state is unreadable. You must:
1. Require exact per-task inclusion in a manifest file.
2. Demand explicit operator affirmation that pin state is unknown.
3. **No automatic bulk selection.**

## 3. Rename Tasks

1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-rename --family-id <family-id> --manifest <manifest-path>
```
2. **Apply**: Call the native tool `set_thread_title` for each included task.
3. **Reconcile**: Perform a DB read-back to verify. Stop on partial failure, persist the per-item outcome to a receipt file, and present the operator with retry and restore steps.

## 4. Archive Family

Separate archive-only from finish-and-clean.
1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-archive --family-id <family-id> --manifest <manifest-path>
```
2. **Apply**: Call the native tool `set_thread_archived` for each included task.
3. **Reconcile**: Perform a DB read-back. On partial failure, stop immediately, persist the receipt, and document recovery steps.

## 5. Finish and Clean

Never implement purge, halt active tasks implicitly, trigger repo-wide pruning, or use short undo as destructive safety.
1. **Preview**:
```bash
.venv/bin/python -m scripts.orchestration.task_family preview-cleanup --family-id <family-id> --branch <branch> --manifest <manifest-path>
```
2. **Apply**: Provide the exact plan digest returned by preview and explicit manifest. Execute the cleanup securely.
```bash
.venv/bin/python -m scripts.orchestration.task_family apply-cleanup --family-id <family-id> --digest <digest> --manifest <manifest-path>
```
