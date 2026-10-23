# Recover preserved historical task evidence

Use `scripts.orchestration.task_closeout recover-local` after a merged task's
dispatch worktree has been removed. Recovery appends a local observation to the
existing lifecycle ledger. It preserves the original task, identity, acceptance
snapshot and evidence files.

Supply the original task JSON, preservation manifest and push receipt. Recovery
verifies the complete preserved inventory, its digests and task/run/worktree
binding, then checks the commit ancestry. A helper's later report or checkout
head cannot replace the original implementation's evidence.

The supported push formats are:

- `head`, `remote_head`, `cwd`, `status: pushed_exact_head`, and a successful
  `push` step with integer `exit_code: 0`.
- Historical `local_head`, `remote_head`, `cwd`, `branch` and integer
  `push_exit_code: 0`. The exact receipt must be listed in the verified original
  task/run's preservation inventory. Mixed formats, conflicting identity fields,
  failed pushes and unequal heads are refused.

If the original task lacks `worktree_reap_proof`, supply `--closeout-record`
with the JSON output of the existing applied common `merge_closeout` command.
The record must report success, no errors, a merged PR with the exact branch and
head, and removal of both branch refs. Recovery reads that PR from the ledger's
repository on GitHub and binds its number, URL, head, branch and merge SHA.
The source task head must be an ancestor of the PR head, and the merge commit
must be an ancestor of `origin/main`. Failed or dry-run cleanup cannot supply
this proof. Recovery itself performs no cleanup or GitHub mutation.

```sh
.venv/bin/python -m scripts.orchestration.task_closeout recover-local \
  --state-file ledger.json \
  --task-record original-task.json \
  --preserved-manifest batch_state/preserved/task/attempt.manifest.json \
  --push-record batch_state/preserved/task/attempt/push.json \
  --closeout-record common-closeout.json
```

Recovery receipts retain hashed source locators and recheck their bytes when
used. Repeating the command with the same sources returns the existing receipt.
Child association still requires the original merged cohort proof; a closeout
record does not establish an earlier carrier's child membership.

Record original independent review through the existing `add-evidence` path.
Keep review approval separate from behavioral proof: historical prose or a
single execution surface does not establish missing canonical behavior facts.
Do not wrap an older artifact in a fabricated review receipt or re-review an
unchanged approved head to change its format. Missing facts remain blockers.
This adapter does not amend author families or acceptance snapshots and does
not change the trusted publication destination used by dispatch finalization.
