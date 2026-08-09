# Worktree cleanup

This runbook covers immediate post-merge cleanup and the local macOS Git
hygiene backstop for both Learn Ukrainian repositories.

## Shared Python environment

The primary checkout's `.venv` is the only project virtual environment.
Dispatch worktrees must never create, copy, symlink, activate, or use a local
`.venv`. From any linked worktree, derive and invoke the absolute primary
interpreter instead:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" -m pytest tests/test_delegate.py
```

Do not substitute `python`, `.venv/bin/python`, or `python -m venv .venv`.
The dispatch launcher records a warning when a local `.venv` is already present;
do not delete it while a task might be active. After the normal merged-PR guards
pass, the P0 reaper removes the entire disposable worktree, including ignored
environment residue.

## Safety contract

Cleanup is fail-closed. A worktree is preserved when any of these is true:

- its pull request is open;
- its pull-request head does not exactly match the worktree HEAD;
- its task is active or non-terminal;
- a live process has a working directory inside it;
- it is dirty, locked, outside the repository's `.worktrees/` subtree, or its
  state cannot be verified.

The scheduled job never commits work on the operator's behalf. It uses
`git worktree remove --force` only as the final deletion step after all P0
guards and their final TOCTOU checks have passed; this removes disposable
ignored residue such as a worker `.venv`, not a bypass for cleanliness, PR,
task, or live-process guards. Unregistered directories with broken `.git`
pointers are reported as recovery candidates and are never deleted
automatically.

P0 automatic reaping includes clean `.worktrees/` checkouts whose GitHub PR is
`MERGED` at the exact local head. The scheduled job also enables a separately
guarded terminal-dispatch class: only worktrees below `.worktrees/dispatch/`
whose task record is explicitly `done`, `failed`, or `no_deliverable`, whose PID
is dead, whose active-task and live-CWD probes are available and clear, and
whose GitHub query confirms no open PR. Set `LU_REAPER_TERMINAL_DISPATCHES=0`
to disable only this optional scheduled class during an incident; merged-clean
reaping remains enabled. Before removal the reaper writes an
append-only local journal, reserves the path as reap-pending, and creates a
`refs/reaper-rescue/...` ref. Set `LU_REAPER_DISABLED=1` to stop automatic
reaps immediately. The first seven days are capped by
`LU_REAPER_MAX_REAPS_PER_DAY` (default 10); an approved policy lift uses
`LU_REAPER_LIFT_FIRST_CLASS_CAP=1`. Restore only to a new path under
`.worktrees/`:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" scripts/orchestration/reap_worktrees.py restore \
  --restore-ref refs/reaper-rescue/<timestamp>/<branch>-<sha> \
  --restore-branch <branch> \
  --restore-worktree .worktrees/dispatch/<agent>/<task>
```

For regular dispatch worktrees, `post_task_reap` delegates automatic removal
to this same P0 reaper rather than maintaining a second deletion path.

## Deletion ownership

`reap_worktrees._remove_worktree` is the single deletion hand for regular
dispatch worktrees. `post_task_reap`'s main path and `delegate`'s completed
worktree cleanup must call the P0 reaper; they must not invoke Git removal
directly.

The following narrowly bounded dual paths are allowed because they do not
represent ordinary merged-PR dispatch cleanup:

- `post_task_reap._remove_worktree` removes only task-state-bound ACP runtime
  paths below `.worktrees/dispatch/acp/`, after its own terminal, clean, and
  liveness checks; it always uses `--force` for ignored runtime residue.
- `_acp_execution.acp_execution_cwd` force-removes only the detached,
  no-checkout ACP workspace it created below `.worktrees/dispatch/acp/` during
  setup failure or context teardown.
- `delegate._release_stale_branch_holders` performs a non-force release after
  clean, synced, terminal-owner checks so a blocked dispatch may reattach its
  branch. Its normal completed-worktree cleanup still uses the P0 reaper.
- `task_family.git_safety.remove_worktree` remains the task-family bundle path:
  its executor repeats frozen-plan, merged-PR, bundle, and candidate checks
  immediately before deletion. Do not replace or remove that path here.

## Immediate cleanup after merge

The merge owner removes the exact worktree as soon as GitHub reports the PR
`MERGED`. Run this from a separate shell after every agent, editor, server, and
terminal has left the target worktree:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
cd "$PRIMARY_REPO"

"$PRIMARY_REPO/.venv/bin/python" scripts/orchestration/reap_worktrees.py \
  --repo-root "$PRIMARY_REPO" \
  --apply \
  --merged \
  --worktree "$EXACT_WORKTREE_PATH"
```

The command revalidates GitHub PR state, the exact PR-head SHA, local HEAD,
cleanliness, task state, and process activity. A skipped result is a blocker,
not permission to retry with `--force`.

The live-process check intentionally includes the invoking process tree. A
cleanup launched from inside the target worktree therefore self-protects and
must be retried from the primary checkout after that process exits. If `lsof`
cannot inspect process working directories, apply mode fails closed; resolve
the local macOS permission or tooling problem before retrying.

The canonical PR lifecycle trail already performs worktree-first cleanup after
merge. Other merge owners must invoke the exact command above before declaring
closeout complete.

Do not put networked worktree deletion in Git's `post-merge` hook. GitHub merges
do not run a local hook, and a later `git pull` is not reliable ownership
evidence for an arbitrary dispatch worktree.

## Manual dual-repository sweep

Dry run:

```bash
.venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py
```

Apply:

```bash
.venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py --apply
```

Each run performs the following in both repository roots:

1. fetches `origin` and prunes deleted remote refs;
2. prunes stale Git worktree registrations;
3. automatically removes only clean, inactive worktrees with exact merged-PR
   head evidence, plus the terminal-dispatch class described above; open or
   GitHub-unknown PR state remains a hard skip;
4. deletes local branches whose upstream is gone only when their exact head is
   proven merged or is already an ancestor of `origin/main`;
5. preserves and reports unproven gone branches and orphaned worktree
   directories;
6. runs `git gc --auto`;
7. writes an immutable JSON receipt.

Dirty worktrees, open PRs, active/non-terminal tasks, checked-out branches, and
unmerged branch heads remain untouched.

```text
~/.codex/worktree-cleanup/receipts/v2/
```

An unavailable fetch or process-activity probe blocks apply for that
repository. Standard output contains the same summary as the receipt.

## Inspect the LaunchAgent

Render the plist without writing system configuration:

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py render
```

The job runs at load and every 4 hours. It uses the public checkout's exact
`.venv/bin/python`, passes both repository roots explicitly, and persists logs
under:

```text
~/.codex/worktree-cleanup/logs/
```

## Install

Install only after the cleanup code is merged into the public primary checkout.
Both primary checkouts must be on `main`.

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py install
```

Installation is idempotent. It writes and loads:

```text
~/Library/LaunchAgents/com.learn-ukrainian.worktree-cleanup.plist
```

Verify the persisted plist and live service:

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py status
```

After installation, inspect the first receipt and confirm that protected
worktrees appear as `skipped`, not `removed`.

## Uninstall

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py uninstall
```

Uninstalling preserves receipts and logs for audit and recovery.
