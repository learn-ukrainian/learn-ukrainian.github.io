# Systemd unit templates (loopback services & scheduled maintenance)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled via `loginctl enable-linger $USER`) or
`/etc/systemd/system/`, replace `@REPO_ROOT@` / `@PRIVATE_ROOT@`, run
`systemctl --user daemon-reload`, then enable/start.

## Loopback Services

Services bind `127.0.0.1` only. Reach them from another machine with an SSH
tunnel; set `MONITOR_INSTANCE_ID` in the environment so `/api/health`
distinguishes hosts. For `GET /api/occupancy`, an empty map makes the API
process fill the production glance row `host-teacher` in-process (plus
observer-only `mac-operator`). Optional `MONITOR_OCCUPANCY_HOST_IDS` adds
`canonical=opaque-id` pairs (opaque values only). Optional local seats:
`ATLAS_JOB_SELF_HOST` or `MONITOR_OCCUPANCY_DRIVER_HOST_ID` attaches
session-stream driver leases; `MONITOR_OCCUPANCY_MARKERS` publishes
Foundry/compiler heartbeats. Do not put addresses or SSH hostnames in the
occupancy JSON. `host-job` is not a default glance row.

Units are **Linux-native `Type=simple`** processes. Do not wrap
`./services.sh start` in `Type=oneshot RemainAfterExit=yes`: that is
launchd-shaped and does not supervise the listener on Linux. macOS still
uses `./services.sh supervise api` / launchd.

Public fixtures use opaque ids `host-teacher` (and mapped `host-job` only when needed).

Available service templates:
- `learn-ukrainian-api.service`: Monitor API service (`scripts/api/main.py`).
- `learn-ukrainian-astro.service`: Astro frontend UI.
- `learn-ukrainian-sources.service`: Sources lookup service.
- `learn-ukrainian-work.service`: Work projection adapter.
- `learn-ukrainian-loopback.target`: Target grouping loopback services.

## Scheduled Maintenance Timers

User timers run background reconciliation, garbage collection, and state
reporting. Target hosts: **any host with a checkout + `batch_state/`** (worker,
runner, and orchestrator hosts).

### 1. Reconciliation Sweep (`learn-ukrainian-reconcile.service` + `.timer`)

- **Frequency**: Hourly (`OnCalendar=hourly`, `RandomizedDelaySec=300`, `Persistent=true`).
- **What it does**: Runs `scripts/orchestration/reconcile_sweep.py` which:
  1. Releases write-ownership claims for inactive tasks via `dispatch_settle release-stale`.
  2. Marks running-with-dead-PID task records as `crashed` via the existing lazy heal path (`scripts/delegate.py status`).
  3. Logs a one-line summary count (`scanned_tasks`, `zombies`, `stale_claims`) to stdout/journal.
- **Default mode**: Report-only (dry-run). It inspects and reports what would be settled without mutating state or database records.
- **Dry-run → Apply promotion**: After verifying observability in the journal, edit `~/.config/systemd/user/learn-ukrainian-reconcile.service` to pass `--apply`:
  ```ini
  ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.orchestration.reconcile_sweep --apply
  ```
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-reconcile.timer
  ```

### 2. Worktree Garbage Collection (`learn-ukrainian-worktree-gc.service` + `.timer`)

- **Frequency**: Daily (`OnCalendar=daily`, `RandomizedDelaySec=1800`, `Persistent=true`).
- **What it does**: Runs `scripts/orchestration/run_scheduled_worktree_cleanup.sh` to prune stale worktree registrations, clean up merged/closed PR branches, and run automatic git maintenance with receipt logging.
- **Default mode**: Report-only (dry-run). The underlying script defaults to dry-run unless `--apply` is explicitly passed.
- **Dry-run → Apply promotion**: To enable active pruning, edit `~/.config/systemd/user/learn-ukrainian-worktree-gc.service` to append `--apply`:
  ```ini
  ExecStart=/usr/bin/env bash @REPO_ROOT@/scripts/orchestration/run_scheduled_worktree_cleanup.sh --repo-root @REPO_ROOT@ --apply
  ```
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-worktree-gc.timer
  ```

### 3. Project State Reporter (`learn-ukrainian-project-state-reporter.service` + `.timer`)

- **Frequency**: Every 5 minutes (`OnUnitActiveSec=5min`, `OnBootSec=2min`).
- **What it does**: Runs `scripts/orchestration/run_project_state_reporter.sh` to report periodic host project state.
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-project-state-reporter.timer
  ```
