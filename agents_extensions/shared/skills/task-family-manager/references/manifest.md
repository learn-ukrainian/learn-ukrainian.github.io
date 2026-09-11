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

Inspect the native pinned inventory before planning and preserve pin evidence.
The current local planner does not ingest native pin evidence: its
`--confirm-pin-unknown` requirement is a local precondition, not a claim that the
app cannot read pins. Every affected task must still be selected explicitly
with one `--select-task <TASK_UUID>` and separately acknowledged with one
`--confirm-pin-unknown <TASK_UUID>`. Never pass a Boolean in place of a task UUID
or bypass this precondition because a native inventory was readable.
