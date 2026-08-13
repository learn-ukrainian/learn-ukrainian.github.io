# launchd inventory

This runbook inventories the per-user macOS LaunchAgents the project owns,
their delete authority, and the log/receipt locations that must survive a
checkout loss. It is the reference for the post-incident reinstall step in
[Recovery after a local checkout or data loss](recovery.md) and for incident
forensics of the kind recorded in
[#6013](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6013).

List the installed jobs and inspect one live service with:

```bash
ls ~/Library/LaunchAgents/com.learn-ukrainian.*.plist
launchctl print "gui/$(id -u)/com.learn-ukrainian.<name>"
```

Every plist persists absolute paths into the primary checkout. Install or
reinstall only from the merged primary checkout on `main`, never from a
dispatch worktree.

## Jobs

### `com.learn-ukrainian.monitor-api`

- Purpose: keeps the Monitor API running under launchd supervision.
- Program: the primary checkout's `.venv/bin/python -m
  scripts.api.launchd_supervisor run --repo-root <primary checkout>`.
- Schedule: `RunAtLoad`; `KeepAlive.SuccessfulExit=false` restarts only
  unexpected exits; `ThrottleInterval=30` bounds crash-loop respawns.
- Delete authority: none. It starts and restarts the API only.
- Logs: `logs/api.launchd.stdout.log` and `logs/api.launchd.stderr.log`
  inside the checkout (gitignored runtime state, recreated on loss); the
  durable crash record is `.pids/api-last-crash.json`.
- Manage: `./services.sh supervise api install|status|uninstall`.
- Reference: [Local API server](../best-practices/local-api-server.md).

### `com.learn-ukrainian.backup`

- Purpose: nightly restic snapshot of recovery-critical local state.
- Program: the host-managed wrapper `~/.local/bin/learn-ukrainian-backup`,
  which sources its environment from `~/.secrets/` and runs
  `scripts/backup-data.sh backup --execute` in the primary checkout.
- Schedule: daily at 03:30 local (`StartCalendarInterval`).
- Delete authority: none. The backup script intentionally has no `forget`,
  `prune`, or snapshot-delete command; snapshots are additive.
- Logs: `~/Library/Logs/learn-ukrainian-backup/scheduled.out.log` and
  `scheduled.err.log` — outside the repository.
- Manage: installed host-side (plist plus wrapper); verify readiness with
  `./scripts/backup-data.sh doctor`.
- Reference: [Data backup and recovery](data-backup.md).

### `com.learn-ukrainian.worktree-cleanup`

- Purpose: Git hygiene backstop for both Learn Ukrainian repositories.
- Program: the primary checkout's `.venv/bin/python
  scripts/orchestration/scheduled_worktree_cleanup.py --apply` with both
  repository roots passed explicitly.
- Schedule: at load and every 4 hours (`StartInterval=14400`).
- Delete authority: removes only clean worktrees with exact merged-PR head
  evidence, the separately guarded terminal-dispatch class, and gone branches
  proven merged. Every removal is preceded by an append-only journal entry and
  a `refs/reaper-rescue/...` ref. Kill switches: `LU_REAPER_DISABLED=1` stops
  all reaps; `LU_REAPER_TERMINAL_DISPATCHES=0` disables only the
  terminal-dispatch class.
- Receipts and logs: `~/.codex/worktree-cleanup/receipts/v2/` and
  `~/.codex/worktree-cleanup/logs/` — outside the repository.
- Manage: `.venv/bin/python
  scripts/orchestration/install_worktree_cleanup_launchd.py
  render|install|status|uninstall`.
- Reference: [Worktree cleanup](worktree-cleanup.md).

### `com.learn-ukrainian.codex-archived-thread-cleanup`

- Purpose: deterministic cleanup of old archived Codex threads.
- Program: the primary checkout's `.venv/bin/python
  scripts/orchestration/archived_thread_cleanup.py --apply --retention-days 30
  --observation-interval-days 7` with an absolute `--codex-binary`.
- Schedule: Sundays at 03:00 local (`StartCalendarInterval`, weekday 0);
  `RunAtLoad` is false.
- Delete authority: `codex delete --force` through the supported Codex CLI,
  only for archived, unpinned, inactive threads older than 30 days that pass
  the two-observation gate at least seven days apart with an unchanged safety
  fingerprint. It never unlinks session files or edits Codex's state database
  directly.
- State, receipts, and logs: `~/.codex/thread-cleanup/` — outside the
  repository.
- Manage: `.venv/bin/python
  scripts/orchestration/install_archived_thread_cleanup_launchd.py
  render|install|status|uninstall`.
- Reference: [Archived thread cleanup](archived-thread-cleanup.md).

## Invariants

- Logs and receipts of scheduled jobs must live outside the repository so
  they survive a checkout loss and remain available for forensics.
  `worktree-cleanup` and `codex-archived-thread-cleanup` comply under
  `~/.codex/`; `backup` logs under `~/Library/Logs/learn-ukrainian-backup/`.
  The `monitor-api` service is the intentional exception: its launchd logs
  are gitignored runtime state inside the checkout and are recreated on
  restart, not audit receipts.
- Delete authority stays scoped and fail-closed as listed above. No project
  LaunchAgent may delete outside its documented guard set; the 2026-07-29
  forensics cleared `worktree-cleanup` and `codex-archived-thread-cleanup`
  for the checkout loss on exactly this evidence.
- Uninstalling a job preserves its receipts and logs for audit.
