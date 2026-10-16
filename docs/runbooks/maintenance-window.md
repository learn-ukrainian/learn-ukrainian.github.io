# Host maintenance window: package upgrade and reboot

Use this runbook for a planned reboot of the host that runs the tmux driver
lanes (for example a pending kernel upgrade). A reboot kills the tmux server,
every lane, every `delegate.py wait`, in-flight workers and every transient
systemd unit. Enabled user units come back on their own when linger is on. The
lanes come back through `learn-ukrainian-lane-relaunch.service`, and the
context guard through `learn-ukrainian-context-guard.timer` (#10814).

Placeholders: `<primary-checkout>` is the primary checkout; run user-manager
commands with `XDG_RUNTIME_DIR=/run/user/$(id -u)` when the shell has no user
bus. Items marked **NOT CHECKED** were not verified when this runbook was
written; verify them before relying on them, or leave the mark.

## Lanes

The lane data lives in `scripts/config/driver_lanes.json`. The guard, the boot
relaunch, and keepers read the same file
(`.venv/bin/python -m scripts.ops.driver_lanes` prints it).

| tmux session | lane | CLI | launcher (repo-relative) |
| --- | --- | --- | --- |
| `infra-muse` | infra | Claude | `start-claude-driver.sh --epic infra` |
| `devops-muse` | devops | Claude | `start-claude-driver.sh --epic devops` |
| `harness` | harness | Codex | `start-codex-driver.sh --epic monitor` |
| `atlas` | atlas | Codex | `start-codex-driver.sh --epic atlas` |
| `open-model-data` | open-model-data | Codex | `start-codex-driver.sh --epic open-model-data` |
| `cto` | cto (lead, started last) | Claude | `start-claude-cto.sh --epic epics` |

Models and effort per lane are in the data file. Codex lanes run with
`scripts/agent_runtime/shims` first on `PATH`. The session names
`infra-muse` and `devops-muse` are historical; Claude runs in them now.

### Host-specific wrappers and accounts

Account selection and machine-specific launch wrappers live only in an
ignored local config, never in the repository:
`$LU_DRIVER_LANES_LOCAL`, default
`${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/driver-lanes.local.json`.
The file must be a regular file owned by the user and not group- or
world-writable (mode `0600`):

```json
{
  "lanes": {
    "cto": {"wrapper": "<cto launcher command>"},
    "infra-muse": {"wrapper": "<infra launcher command>"},
    "devops-muse": {"env": {"CLAUDE_CONFIG_DIR": "<claude account directory>"}},
    "harness": {"env": {"CODEX_HOME": "<codex home>"}}
  }
}
```

A `wrapper` replaces the generic launcher command; `env` adds variables to the
lane's tmux session. The CTO lane needs a wrapper on a host where the CTO role
prompt is a private file, because the generic command carries no role prompt.
`--dry-run` prints which source each lane uses and only the env keys, never
their values.

## 1. Before the reboot (go/no-go)

All items must pass before the upgrade starts.

- [ ] **Units installed.** `learn-ukrainian-context-guard.timer` is enabled
  and active, `learn-ukrainian-lane-relaunch.service` is enabled, and the
  transient guard timer it replaced is gone (see
  `packaging/systemd/README.md`). `.venv/bin/python -m scripts.ops.lane_relaunch --dry-run`
  prints six lanes, `cto` last, each with the intended source (`local-wrapper`
  or `generic`).
- [ ] **Every lane handed off.** Each of the six lanes wrote the top of its
  `DRIVER-STATE.md` and posted `HANDOFF-DONE`; its in-flight worker task ids and
  waits are in that handoff.
- [ ] **No task spawning.** `.venv/bin/python scripts/delegate.py status`
  shows no task in `spawning`.
- [ ] **No push in flight.** No pre-push gate holder or ticket under
  `<git-common-dir>/lu-pre-push-gate/` (`docs/runbooks/pre-push-gate.md`), and
  no transient push unit (`systemctl --user list-units --type=service`).
- [ ] **One-shot push chains noted.** A tmux session that runs a push script
  followed by a sleep is not a lane and is not relaunched. Note each one with
  its PR; re-run its push script after the boot if the PR is still unmerged.
- [ ] **Merge queue empty.** For each open PR that was enqueued,
  `.venv/bin/python scripts/gh_merge_queue_status.py <pr> --json` reports it is
  not queued. A single queue-wide listing command is **NOT CHECKED**.
- [ ] **Disk.** `df -h /` shows use below 85% and more than 40G free.
- [ ] **Recent backup.** `systemctl --user status learn-ukrainian-backup.service`
  and `jq . <primary-checkout>/batch_state/backups/last-run.json` show a clean
  run within the last day (`docs/runbooks/data-backup.md`).
- [ ] **Operator GO.** A present-tense operator GO for this window is recorded.

## 2. Upgrade and reboot

Run non-interactively so `dpkg` and `needrestart` cannot block on a prompt:

```bash
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a \
  apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
sync
sudo systemctl reboot
```

Service restarts by `needrestart` are superseded by the reboot. The host's
`needrestart` defaults are **NOT CHECKED**.

## 3. After the boot (parity smoke, in order)

1. **User manager.** `loginctl show-user "$USER" -p Linger` prints
   `Linger=yes`; `systemctl --user is-system-running` prints `running`.
2. **Disk.** `df -h /` still shows more than 40G free.
3. **Monitor API.** `curl -fsS http://127.0.0.1:8765/api/health` returns a
   version, and `curl -fsS http://127.0.0.1:8765/api/rules | head -c 200`
   returns rules text.
4. **Sources MCP.** `systemctl --user is-active learn-ukrainian-sources`
   prints `active`, and a `verify_word` call on `добрий` returns a VESUM hit.
5. **Storage.** `.venv/bin/python -m scripts.storage status` resolves
   `data/sources.db` and `data/vesum.db` (`docs/runbooks/storage-topology.md`).
6. **Work adapter.** `systemctl --user is-active learn-ukrainian-work` prints
   `active`; `curl -fsS http://127.0.0.1:8765/api/work/v1/health` answers
   through the Monitor API. The adapter's own health endpoint is **NOT CHECKED**.
7. **Astro.** `curl -fsSI http://127.0.0.1:4321/` returns 200.
8. **Timers.** `systemctl --user list-timers --all` shows a NEXT time for
   `learn-ukrainian-context-guard.timer`, the merge-queue keeper and the other
   enabled timers. Transient timers did not survive; recreating them is
   **NOT CHECKED** and belongs to their owners.
9. **Lanes.** `journalctl --user -u learn-ukrainian-lane-relaunch.service -b`
   shows one line per lane: `started`, `session exists, skipped`, or
   `launcher exited rc=N`. `tmux ls` lists all six sessions. For each Claude
   lane, `ps -ww eo args= -p <claude pid>` shows the intended `--model` and
   `--effort`, and the pane status line shows `ctx: …%`; Codex panes show
   `Context N% used`.
   - **Lease conflict.** A launcher that exits with a lease conflict fails
     closed; the relaunch logs it and moves on. Wait for the old lease's
     `expires_at`, then run `.venv/bin/python -m scripts.ops.lane_relaunch`
     again (existing sessions are skipped; kill only the failed lane's session
     first). Never force a lease.
10. **Guard.** After the lanes are up, run
    `.venv/bin/python -m scripts.ops.context_guard tick` once and check that
    `${XDG_STATE_HOME:-$HOME/.local/state}/learn-ukrainian/context-guard/guard.log`
    has a `watch ctx_pct=` line for every lane.
11. **Per lane.** Each lane drains its Fleet Comms inbox, re-arms its waits
    from the handoff, and runs `.venv/bin/python scripts/delegate.py status`.
    Reap dead tasks with
    `.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>` (dry-run
    first, then `--apply`). A per-lane dispatch dry run is **NOT CHECKED**.

## 4. Rollback

`uname -r` shows the running kernel. To boot the previous kernel, reboot and
choose it under the boot menu's advanced options, then repeat section 3. The
exact boot-menu entry and console access are **NOT CHECKED**.

## 5. Do not

- Mount, sync, move or evict bulk corpus mirrors, Drive objects or SMB shares
  (`docs/runbooks/storage-topology.md`).
- Read, edit or rotate credentials, account directories or SSH configuration.
- Force-release or bypass a pre-reboot stream lease.
