# Archived thread cleanup

This runbook operates the deterministic cleanup for old Codex archived threads. It does not run a
model, submit a prompt, or use a Codex automation. A per-user macOS `launchd` job runs the same Python
command every week.

## Safety policy

The cleanup uses a 30-day retention period. A thread is only a deletion candidate when it is archived,
older than the retention cutoff, unpinned, inactive, and free of protected lifecycle references. The
cleanup engine revalidates eligibility before deletion.

Apply mode does not delete a newly eligible candidate on first sight. It records the first weekly
observation. The same candidate must remain eligible with an unchanged safety fingerprint on a second
weekly run at least seven days later before it can be deleted. A changed or newly protected thread does
not pass the second observation.

Permanent deletion goes through the supported Codex CLI operation, equivalent to:

```bash
codex delete --force <thread-uuid>
```

The cleanup does not unlink session files or edit Codex's state database directly.

## Manual dry run

Run from the merged primary checkout with its project virtual environment:

```bash
.venv/bin/python scripts/orchestration/archived_thread_cleanup.py
```

The default performs no deletion, but it does persist observation state and a receipt. Review the JSON
result and its receipt before enabling or invoking apply mode. To test another retention boundary
explicitly:

```bash
.venv/bin/python scripts/orchestration/archived_thread_cleanup.py --retention-days 30
```

## Manual apply

Apply the policy once with:

```bash
.venv/bin/python scripts/orchestration/archived_thread_cleanup.py --apply --repo-root "$PWD"
```

The first qualifying run records observations; only a later qualifying run at least seven days after
the first observation can delete an unchanged candidate. The command remains non-interactive.

Runtime state is stored at `~/.codex/thread-cleanup/state-v1.json`; versioned receipts are written under
`~/.codex/thread-cleanup/receipts/v1/`. Standard output and standard error from scheduled runs are
written to:

```text
~/.codex/thread-cleanup/logs/stdout.log
~/.codex/thread-cleanup/logs/stderr.log
```

Keep the receipts for both initial weekly observations. They are the audit record for why a thread was
retained, advanced to its second observation, skipped, or deleted.

## Inspect the launch agent without installing it

Render the plist without disk writes or `launchctl` calls:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py render \
  --repo-root "$PWD" \
  --weekday sunday \
  --hour 3
```

`install --dry-render` is an equivalent test-only path. Both forms are safe on non-macOS hosts and are
useful for inspecting `ProgramArguments` in tests.

## Install the weekly job

Install only from the merged primary checkout. The absolute checkout path is persisted in the plist,
so do not install from a disposable worktree. The default schedule is Sunday at 03:00 in the Mac's
local time:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py install \
  --repo-root "$PWD"
```

The installer atomically writes:

```text
~/Library/LaunchAgents/com.learn-ukrainian.codex-archived-thread-cleanup.plist
```

Its `ProgramArguments` use the checkout's explicit `.venv/bin/python` to run
`scripts/orchestration/archived_thread_cleanup.py --apply --repo-root <checkout> --retention-days 30
--observation-interval-days 7`. The installer also resolves the supported Codex CLI to an absolute,
executable path and persists it through `--codex-binary`; the scheduled job does not depend on
`launchd`'s minimal `PATH`. Installation is idempotent: an unchanged loaded job is left in place; a
changed job is unloaded, rewritten, loaded, and verified through `launchctl print`.

If `codex` is not on the interactive shell's `PATH`, provide its absolute path explicitly:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py install \
  --repo-root "$PWD" \
  --codex-binary "$HOME/.local/bin/codex"
```

To choose another weekly local schedule, pass a lowercase weekday name and an hour from 0 through 23:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py install \
  --repo-root "$PWD" \
  --weekday wednesday \
  --hour 4
```

## Verify status and observe the first two runs

Check both the plist and launchd's live service state:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py status
```

The command exits successfully only when the expected plist is installed, parses with the correct
label, and the service is loaded. For lower-level readback:

```bash
launchctl print "gui/$(id -u)/com.learn-ukrainian.codex-archived-thread-cleanup"
```

After each of the first two scheduled runs:

1. Run the status command and confirm the service remains loaded.
2. Inspect `~/.codex/thread-cleanup/logs/stderr.log`; it should contain no unhandled error.
3. Inspect the new receipt under `~/.codex/thread-cleanup/receipts/v1/` and reconcile its counts with the
   JSON line in `stdout.log`.
4. Confirm the first run only recorded observations. On the second run, confirm that only candidates
   observed unchanged at least seven days apart were eligible for deletion.

If the Mac is asleep at the scheduled time, `launchd` normally coalesces the missed calendar event and
runs it after wake. The cleanup engine's minimum seven-day observation interval remains the controlling
deletion gate.

## Uninstall

Unload the service and remove its plist:

```bash
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py uninstall
```

Uninstall is idempotent. It intentionally preserves `~/.codex/thread-cleanup/`, including receipts and
logs, so removing the schedule does not destroy its audit trail.

## Residual race window

The cleanup takes a fresh protected-state snapshot and revalidates each candidate immediately before it
invokes `codex delete --force`. There is still an unavoidable time-of-check/time-of-use window: another
process could pin, activate, restore, or otherwise reference the thread after the last validation but
before the Codex CLI completes deletion. The two-observation gate and last-moment revalidation reduce
that risk but cannot make multiple independent processes transactional. Uninstall the launch agent
before performing bulk thread lifecycle changes, then run a fresh dry run before reinstalling it.
