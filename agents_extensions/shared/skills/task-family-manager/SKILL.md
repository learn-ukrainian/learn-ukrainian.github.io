---
name: "task-family-manager"
description: "Inspect, rename, archive, restore, or proof-gated-clean an exact Codex task family with native app mutations, previews, reconciliation, and receipts."
---

# Task Family Manager

Use this skill when a user wants to inspect or operate on a Codex task family. Identity always comes from exact task UUIDs and typed relations; titles are display text only.

The repository package plans and verifies operations. Codex app tools perform task mutations. Never write Codex SQLite directly, call private app APIs, infer membership from similar titles, or treat archive as cancellation.

## Native boundary

Use the available Codex app tools for their supported actions:

- `list_threads` and `read_thread` for visible task state;
- `set_thread_title` for one exact rename;
- `set_thread_archived` for one exact archive or restore;
- `handoff_thread` and `get_handoff_status` only when handoff work is requested;
- `navigate_to_codex_page` only when the user asks to open a task.

The app currently lacks an include-archived inventory, readable pin state, typed family graph, atomic batch mutation, and native receipt API. The local bridge therefore performs bounded, read-only SQLite reconciliation after each native mutation. `--db auto` discovers a compatible local database fail-closed; an explicit database path is also accepted.

Runtime packets, rollover leases, and automations are preservation-only locally. For finish-and-clean, record a tool-backed terminal task `status`. Any selected rollover endpoint also needs `rollover_cleanup_eligible: "true"` plus `rollover_cleanup_proof`; any `automation_id` needs `automation_cleanup_eligible: "true"` plus `automation_cleanup_proof`. Missing proof blocks cleanup. Even with proof, the local executor records retirement as deferred and preserves the evidence because no native retirement API exists.

## Build the manifest

Create a versioned manifest from tool-backed exact IDs. Prefer structured fork responses or persisted spawn edges. Add reviewer, handoff, replacement, and rollover relations only when explicit evidence exists. `issue_or_pr_member` may be display-only by setting `family_defining` to `false`.

```json
{
  "schema_version": 1,
  "family_id": "issue-5140-family",
  "seed_task_id": "00000000-0000-4000-8000-000000000001",
  "nodes": [
    {
      "task_id": "00000000-0000-4000-8000-000000000001",
      "title": "Plan lifecycle",
      "project_root": "/absolute/project",
      "worktree": null,
      "branch": null,
      "pr_id": null,
      "metadata": {"cwd": "/absolute/project", "status": "completed"}
    },
    {
      "task_id": "00000000-0000-4000-8000-000000000002",
      "title": "Implement lifecycle",
      "project_root": "/absolute/project",
      "worktree": "/absolute/project/.worktrees/dispatch/codex/example",
      "branch": "codex/example",
      "pr_id": "123",
      "metadata": {"cwd": "/absolute/project", "status": "completed"}
    }
  ],
  "relations": [
    {
      "source_id": "00000000-0000-4000-8000-000000000002",
      "target_id": "00000000-0000-4000-8000-000000000001",
      "relation_type": "subagent_of",
      "evidence": "codex_app fork response sourceThreadId",
      "family_defining": true
    }
  ]
}
```

Supported typed relations are `root`, `subagent_of`, `reviewer_for`, `handoff_of`, `replacement_of`, `rollover_generation_of`, and `issue_or_pr_member`.

## Inspect before mutation

```bash
.venv/bin/python -m scripts.orchestration.task_family inspect \
  --manifest /absolute/manifest.json --json
```

Show the exact included and excluded task IDs, derived roles, relation count, resources, and blockers. Stop if the graph has unknown endpoints, conflicting parents, cycles, incompatible project roots, or anything other than one root.

Pinned state is currently unreadable. Every affected task must be selected explicitly with one `--select-task <TASK_UUID>` argument and separately acknowledged with one `--confirm-pin-unknown <TASK_UUID>` argument. Never pass a Boolean in place of a task UUID.

## Rename

Use a fresh UUID for each operation. The preview persists an immutable exact rename map and digest. Generated titles keep role/generation suffixes and respect Codex's 60-character persisted-title limit.

```bash
.venv/bin/python -m scripts.orchestration.task_family preview-rename \
  --repo-root /absolute/project \
  --manifest /absolute/manifest.json \
  --operation-id 00000000-0000-4000-8000-000000000010 \
  --base-title "Lifecycle complete" \
  --select-task 00000000-0000-4000-8000-000000000001 \
  --select-task 00000000-0000-4000-8000-000000000002 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000001 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000002 \
  --actor codex/operator --json
```

Family rename requires every included task. Repeat both selection arguments for every included UUID. After the user has seen the preview, call `set_thread_title` once per selected task using that task's exact `new_title`. Immediately reconcile each result:

```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-title \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000010 \
  --plan-digest <64-lowercase-hex-digest> \
  --db auto \
  --task-id 00000000-0000-4000-8000-000000000001 \
  --cwd /absolute/project \
  --expected-title "Lifecycle complete [Lead]"
```

Proceed sequentially and stop on the first mismatch. A retry is read-back-only when that exact action already succeeded.

## Archive or finish and clean

Choose the operation explicitly:

- `preview-archive` is reversible and retains transcripts, worktrees, branches, and runtime resources.
- `preview-cleanup` archives tasks and may remove only exact, verified, family-owned resources. Purge is not implemented.

```bash
.venv/bin/python -m scripts.orchestration.task_family preview-archive \
  --repo-root /absolute/project \
  --manifest /absolute/manifest.json \
  --operation-id 00000000-0000-4000-8000-000000000020 \
  --lineage-id 00000000-0000-4000-8000-000000000021 \
  --base-title "Lifecycle complete" --db auto \
  --select-task 00000000-0000-4000-8000-000000000001 \
  --select-task 00000000-0000-4000-8000-000000000002 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000001 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000002 \
  --actor codex/operator --json
```

For cleanup, replace `preview-archive` with `preview-cleanup`. Display its exact resource decisions and blockers before any mutation.

Call `set_thread_archived` with `archived: true` once per selected task, then reconcile immediately with its current exact title:

```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-archive \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 \
  --db auto \
  --task-id 00000000-0000-4000-8000-000000000001 \
  --cwd /absolute/project \
  --expected-title "Lifecycle complete [Lead]"
```

Only after every selected task verifies, execute the persisted plan:

```bash
.venv/bin/python -m scripts.orchestration.task_family apply-cleanup \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 \
  --lineage-id 00000000-0000-4000-8000-000000000021 \
  --plan-digest <64-lowercase-hex-digest> --json
```

Cleanup must never call `.git/hooks/post-merge`, `alias.cleanup-gone`, a broad gone-upstream pruner, remote branch deletion, forced worktree removal, auto-stash/commit, or lock deletion. A local branch is eligible only under the executor's exact PR/head/remote/worktree/snapshot/protected-base proof.

## Restore and receipts

To restore, call `set_thread_archived` with `archived: false`, then reconcile the same selected task:

```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-restore \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 \
  --db auto \
  --task-id 00000000-0000-4000-8000-000000000001 \
  --cwd /absolute/project \
  --expected-title "Lifecycle complete [Lead]"
```

Render the durable receipt at any point:

```bash
.venv/bin/python -m scripts.orchestration.task_family receipt \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 --json
```

Report planned versus actual actions, skipped resources and reasons, failures with recovery instructions, restoration information, final retained resources, and the receipt path under `.agent/task-families/<family>/operations/<operation>/`.
