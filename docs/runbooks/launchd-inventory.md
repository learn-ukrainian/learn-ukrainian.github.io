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
- Program: `/bin/bash --noprofile --norc
  scripts/api/run_monitor_api_supervisor.sh run --repo-root <primary
  checkout>`. The wrapper execs the primary `.venv/bin/python -m
  scripts.api.launchd_supervisor`. `Program` must stay `/bin/bash` so a
  venv rebuild cannot invalidate launchd LWCR (exit 78; #6937, #6941).
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
- Program: `/bin/bash --noprofile --norc
  scripts/orchestration/run_scheduled_worktree_cleanup.sh --apply` with both
  repository roots passed explicitly. The wrapper execs the primary
  `.venv/bin/python`. `Program` must stay `/bin/bash` so a venv rebuild
  cannot invalidate launchd LWCR (exit 78; #6937).
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
- Program: `/bin/bash --noprofile --norc
  scripts/orchestration/run_archived_thread_cleanup.sh --apply` with both
  `--repo-root` and an absolute `--codex-binary`. The wrapper execs the
  primary `.venv/bin/python`. `Program` must stay `/bin/bash` so a venv
  rebuild cannot invalidate launchd LWCR (exit 78; #6937, #6941).
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

### `com.learn-ukrainian.mac-observer-heartbeat`

- Purpose: Heartbeats live Mac GUI sessions (Cursor IDE and Codex UI) to
  `POST /api/observer/presence` over the loopback Monitor tunnel so
  occupancy shows supervision seats under opaque `mac-operator` without
  claiming stream leases (#7104). The same bounded heartbeat sweeps local
  SessionStart markers for Claude/Codex/Cursor sessions and carries local
  context counters when available (#7189).
- Program: `/bin/bash --noprofile --norc
  scripts/orchestration/run_mac_observer_heartbeat.sh --repo-root <primary
  checkout>`. The wrapper execs the primary `.venv/bin/python` with
  `scripts/orchestration/observer_heartbeat.py --mac-gui`. `Program` must stay
  `/bin/bash` so a venv rebuild cannot invalidate launchd LWCR (exit 78; #6937, #6941).
- Schedule: at load and every 5 minutes (`StartInterval=300`), well within
  the 15-minute presence TTL.
- Delete authority: only malformed, dead-PID, or older-than-24-hour marker
  files in the observer's own runtime marker directory; it has no repository
  or checkout deletion authority.
- Logs: `~/.codex/mac-observer/logs/` — outside the repository.
- Manage: `.venv/bin/python
  scripts/orchestration/install_mac_observer_launchd.py
  render|install|status|uninstall`.
- Reference: [Cursor driver](cursor-driver.md) and #7104.

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
