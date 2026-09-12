## Archive or finish and clean

Choose the operation explicitly:

- `preview-archive` is reversible and retains transcripts, worktrees, branches, and runtime resources.
- `preview-cleanup` archives tasks and may remove only exact, verified, family-owned resources. Purge is not implemented.

When the family belongs to non-trivial GitHub implementation work, task-family
cleanup is only the final local/native part of the shared closeout contract. Load
the exact `task-lifecycle.v1` ledger from its `task-identity.v1` repository/issue
before previewing cleanup:

```bash
.venv/bin/python -m scripts.orchestration.task_closeout locate \
  --identity-file /absolute/task-identity.json
.venv/bin/python -m scripts.orchestration.task_closeout reconcile \
  --state-file /absolute/.agent/task-lifecycle/.../issue-N.json \
  --branch codex/N-topic --worktree /absolute/.worktrees/dispatch/codex/N-topic
```

Do not treat archived tasks, a completed worker, a merged PR, or a `Fixes #N`
keyword as terminal proof. The lifecycle receipt must verify the explicit
merge/deploy/certify goal, actual issue closure, and exact branch/worktree
cleanup. A `BLOCKED_WITH_RECEIPT` disposition stops `preview-cleanup` until its
owner, reason, evidence, and next action are resolved.

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
