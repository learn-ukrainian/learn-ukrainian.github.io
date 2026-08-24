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
`LU_REAPER_MAX_REAPS_PER_DAY` (default 25); when the eligible backlog of
fully safety-qualified worktrees exceeds the remaining daily budget, the cap
may expand up to a hard ceiling of 2x the configured base (journaled as
`cap-expansion` with the justifying backlog size; the ceiling is not
env-expandable). An approved policy lift uses
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

## Before re-firing a task id

A detached `delegate.py dispatch` launcher that is still grinding from a prior
attempt can finish after you re-fire the same task id, leaving two workers on
one worktree (the task record points at the newer pid; the older process is an
orphan). Before re-using a task id, kill any stale detached launcher for it:

```bash
/bin/ps -axo pid,etime,command | grep 'delegate.py dispatch .*--task-id <id>'
```

Confirm the match is the stale launcher, then terminate that pid before the
new dispatch.

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

Git closeout for **every** merge is exactly three things: worktree reaped,
remote branch gone, local branch gone. If GitHub did not delete the remote
head, delete it. Then delete the local branch. Host pulls, tunnels, occupancy
probes, service restarts, and similar proofs are **task remainder**, not this
list — name them for this task and finish them, but do not add them to standing
merge hygiene.

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
   head evidence (including same-tree squash siblings), plus the terminal-dispatch
   class described above; open or GitHub-unknown PR state remains a hard skip;
4. deletes origin heads whose GitHub PR is MERGED or CLOSED at the exact live
   origin SHA (`ls-remote` + `--force-with-lease`), or whose tip is already an
   ancestor of `origin/main`, and which are not checked out, have no open PR,
   and are not `entire/` refs;
5. deletes local branches whose upstream is gone, or that were never tracked,
   only when their exact head is proven merged/closed or is already an ancestor
   of `origin/main` (`entire/` refs are preserved; a `pr-N` name alone is not
   proof);
6. preserves and reports unproven gone branches and orphaned worktree
   directories;
7. runs `git gc --auto`;
8. writes an immutable JSON receipt.

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

The job runs at load and every 4 hours. launchd `Program` is `/bin/bash`
(Apple-signed, survives a `.venv` rebuild) plus
`scripts/orchestration/run_scheduled_worktree_cleanup.sh`, which execs the
public checkout's `.venv/bin/python`. Pointing `Program` at the venv
interpreter is what produced exit 78 (`Unable to get updated LWCR ... error
0x3`) after the 2026-08-15 venv rewrite. The wrapper passes both repository
roots explicitly and persists logs under:

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
worktrees appear as `skipped`, not `removed`. A venv rebuild does not require
reinstall anymore; `status` still verifies the plist still binds `Program` to
`/bin/bash`.

A red or missing scheduled run surfaces on the existing integrity canary
(`/api/orient` `health.worktree_cleanup_integrity_ok`, plus the dispatch
pre-flight warning). Probe:

```bash
.venv/bin/python scripts/audit/check_worktree_cleanup_integrity.py
```

## Uninstall

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py uninstall
```

Uninstalling preserves receipts and logs for audit and recovery.

## Ad-hoc `/tmp` leak sweep

Agents sometimes leave full clones under `/tmp` outside the formal review isolation
prefixes (`review-6621`, `pr6591-exact-*`, `lu-*`, local CI fixtures). Those trees do
not match `sweep_review_temp_orphans` and will refill the disk within hours.

```bash
# dry-run
.venv/bin/python -m scripts.orchestration.tmp_leak_sweep

# apply
.venv/bin/python -m scripts.orchestration.tmp_leak_sweep --apply
```

The scheduled git-hygiene runner (`scheduled_worktree_cleanup.py`) invokes the same
sweep after the review-temp reaper. Age gates: 2h normally, 30m when free space is
under 15 GiB. Live process paths are skipped.

