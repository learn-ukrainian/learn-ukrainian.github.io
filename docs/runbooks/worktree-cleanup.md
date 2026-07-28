# Worktree cleanup

This runbook covers immediate post-merge cleanup and the local macOS safety
backstop for both Learn Ukrainian repositories.

## Safety contract

Cleanup is fail-closed. A worktree is preserved when any of these is true:

- its pull request is open;
- its pull-request head does not exactly match the worktree HEAD;
- its task is active or non-terminal;
- a live process has a working directory inside it;
- it is dirty, locked, outside the repository's `.worktrees/` subtree, or its
  state cannot be verified.

The scheduled job never commits work on the operator's behalf and never uses
`git worktree remove --force`. Unregistered directories with broken `.git`
pointers are reported as recovery candidates and are never deleted
automatically.

## Immediate cleanup after merge

The merge owner removes the exact worktree as soon as GitHub reports the PR
`MERGED`. Run this from a separate shell after every agent, editor, server, and
terminal has left the target worktree:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
cd "$PRIMARY_REPO"

.venv/bin/python scripts/orchestration/reap_worktrees.py \
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

Each run fetches and prunes `origin`, probes process working directories, runs
the exact-merged-PR reaper for both repository roots, reports orphaned worktree
directories, and writes an immutable JSON receipt under:

```text
~/.codex/worktree-cleanup/receipts/v1/
```

An unavailable fetch or process-activity probe blocks apply for that
repository. Standard output contains the same summary as the receipt.

## Inspect the LaunchAgent

Render the plist without writing system configuration:

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py render
```

The job runs at load and every 15 minutes. It uses the public checkout's exact
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
