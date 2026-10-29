# Dispatch v2

`scripts/dispatch.py` delegates to `scripts.dispatcher.cli:main`; its `--help`
and each subcommand's `--help` are the command reference. This page records
what `--help` cannot: how dispatch worktrees end and how to see them.

## Worktree lifecycle

`dispatch` creates one linked worktree per task under `.worktrees/dispatch/`,
unless the task borrows an existing one with `--cwd`. When the task ends, its
supervisor publishes the terminal record and then settles the worktree
(`worker._reap_settled`, `git.settle_worktree`). Removal always goes through
the guarded chokepoint `worktree_claims.remove_unclaimed_worktree`, which
copies untracked files into the task's preserved archive first. The record
gets `worktree_disposition` (`removed`, `retained` or `error`) with a
`worktree_disposition_reason` and, when there is one, a
`worktree_disposition_detail`. The reasons are listed in
[Worktree cleanup](../runbooks/worktree-cleanup.md).

A retained tree whose reason can clear later (`worker.RETRY_REASONS`, which
covers every reason except `borrowed_worktree`) is settled again by
`worker.settle_left_worktrees`. This happens each time a dispatch starts and
each time a task settles, just before that task's record turns terminal, so the
supervisor exits as soon as its own tree is settled and a tree the task borrowed
is retried on the next pass. A retry
uses the same proofs as the first settlement, so a tree that still holds
uncommitted or unpublished work, or a nested repository with unpushed commits,
stays. A retry never forces a removal.

The chokepoint refuses while an unfinished task record claims the tree, and
it refuses when a candidate record cannot be read or parsed. A file in the
task-record directory that parses as JSON but is not an object, such as a
worker's proof list, is no task record and never blocks a removal.

## Seeing worktrees

```bash
.venv/bin/python scripts/dispatch.py worktrees            # hot task records
.venv/bin/python scripts/dispatch.py worktrees --all      # also archived records
.venv/bin/python scripts/dispatch.py worktrees --repo public
```

The command is read-only. For every linked worktree registered with the
repository, it prints one JSON object:

| Field | Meaning |
| --- | --- |
| `path` | The registered worktree path |
| `task_id` | The owning task: the record that created the tree, else the newest record naming it |
| `borrowers` | Other tasks whose records name the tree (dispatched there with `--cwd`) |
| `status` | The owner's recorded status, as stored, without liveness reconciliation |
| `worktree_disposition`, `worktree_disposition_reason` | The owner's last settlement result; `null` while it runs |
| `age_s` | Seconds since the worktree's `.git` file was written |
| `size_bytes` | Disk use of the tree on its own filesystem, or `null` if it cannot be measured |
| `no_task_record` | `true` when no task record names the tree |

A tree with `no_task_record: true` was not created by this dispatcher, or its
record was moved away; remove it only after its content is confirmed
published, through the guarded remover (`scripts.orchestration.worktree_claims`).
