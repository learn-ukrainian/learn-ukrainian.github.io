# Host maintenance window: package upgrade and reboot

Use this guide for an operator-approved package upgrade and reboot. A reboot
terminates interactive sessions, workers, waits and transient services. Keep
the deployment inventory, service names, account configuration, resource
thresholds and raw operational evidence in the private runbook.

Run project commands from the checkout with the configured project
interpreter. Run host commands only under the authorization for the window.

## Lanes

Inventory every active lane and its in-flight tasks before maintenance. Use
the tracked lane configuration and the private deployment inventory to
compare expected and observed sessions. Do not assume a historical session
name still identifies the same runtime.

```bash
.venv/bin/python scripts/dispatch.py status
.venv/bin/python -m scripts.ops.lane_relaunch --dry-run
```

### Host-specific wrappers and accounts

Local wrappers and identity bindings are private operational configuration.
Have the operator verify them without exposing their paths or values. A
refused wrapper or account binding blocks that lane's relaunch. Do not edit
credentials or substitute an identity during maintenance.

A generic wrapper is one executable path or a list of command words. Each word
may contain only letters, digits and `_@%+=:,./-`. The launcher passes those
words as arguments, without shell parsing. Spaces, shell separators, command
substitution, redirections and newlines are refused. The lane is logged and
not started; `--dry-run` reports it as `refused`. Environment diagnostics show
only key names, never values. The ignored local configuration may supply a
wrapper or environment overrides; its path, identity bindings and actual
values stay in private operational configuration.

## 1. Before the reboot (go/no-go)

All checks must pass before the upgrade starts:

- Verify that the required persistent services and timers are installed and
  enabled. Compare the relaunch preview with the complete private inventory.
- Obtain a handoff for every lane, including each in-flight task and wait.
- Confirm that no task is spawning and no push or pre-push gate is active.
- Record one-shot jobs that the lane relauncher will not restore.
- Confirm that the merge queue is empty using each queued PR's status.
- Check disk headroom against the approved private maintenance thresholds.
- Verify a recent successful backup and its recovery evidence.
- Record present-tense operator approval for this maintenance window.

```bash
.venv/bin/python scripts/gh_merge_queue_status.py '<pr-number>' --json
./scripts/backup-data.sh doctor
```

## 2. Upgrade and reboot

The authorized host administrator applies the approved package upgrade,
records its result privately and reboots through the host's maintenance
procedure. Use the private runbook for platform-specific commands and console
access. An incomplete upgrade or lost recovery access blocks the reboot.

## 3. After the boot (parity smoke, in order)

1. Verify the user service manager and required persistent services.
2. Recheck disk headroom against the approved thresholds.
3. Verify the Monitor health and rules endpoints through the configured
   private endpoint, then verify Sources access.
4. Inspect storage resolution without moving or copying data:

   ```bash
   .venv/bin/python -m scripts.storage status
   ```

5. Verify the work adapter, site response and every required timer against
   the private inventory. Recreate transient jobs only through their owners.
6. Compare every relaunched lane with its handoff. A lease conflict fails
   closed; wait for normal expiry or an authorized release, never force it.
7. Verify the context guard's sanitized result for every lane:

   ```bash
   .venv/bin/python -m scripts.ops.context_guard tick
   ```

8. Each lane drains its inbox and re-arms the waits recorded in its handoff.
   Each worker settles its own task. Use the existing worktree removal proofs
   for tasks that died during the reboot; never remove a tree on appearance
   alone.

See [Storage topology](storage-topology.md) for local database constraints and
[Data backup and recovery](data-backup.md) for backup verification.

## 4. Rollback

If post-boot checks fail, preserve the diagnostics and use the approved
console procedure to boot the previous known-good kernel or restore the
failed component. Repeat every post-boot check before resuming work. Do not
assume a boot-menu entry or remote access path is available without checking.

## 5. Do not

- Mount, sync, move or evict bulk corpus mirrors as part of host maintenance.
- Read, edit or rotate credentials, account directories or access settings.
- Force-release or bypass a pre-reboot stream lease.
- Resume writers while storage identity, backups or service health are unknown.

Operational details are in the private infra repository's `runbooks/maintenance-window.md`.
