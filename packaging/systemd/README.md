# Systemd unit templates (loopback services & scheduled maintenance)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled via `loginctl enable-linger $USER`) or
`/etc/systemd/system/`, replace `@REPO_ROOT@` / `@PRIVATE_ROOT@`, run
`systemctl --user daemon-reload`, then follow the unit-specific instructions
below. The retired backup and retention timers must remain disabled.

## Dispatch worker slice (`lu-dispatch.slice`)

One slice for every detached worker `scripts/delegate.py` launches (#8645). The
driver stays outside it. A runaway worker is killed inside the slice; the driver
and the host services are not in that cgroup.

`MemoryHigh=` is the throttling line and `MemoryMax=` is the last line of
defense, as `systemd.resource-control(5)` recommends. `MemoryMax=` does not cap
swap, so `MemorySwapMax=` is set as well. The unit file in this directory
carries no values: all three are set per deployment, sized for that host, in a
limits drop-in installed next to the unit
(`~/.config/systemd/user/lu-dispatch.slice.d/10-limits.conf`). The same holds
for `lu.slice`. There is no environment override.

Running without the slice is supported. Dispatch then prints one warning and
starts the worker with plain `Popen`, and the task record's `launch_mode` is
`popen-fallback`. `LU_DISPATCH_ISOLATION=fallback` forces that path.

### Prerequisites

All of these have to hold or dispatch will not use the slice:

- Linger is on: `loginctl show-user "$USER" -p Linger` prints `Linger=yes`.
  Without linger the user manager, and every scoped worker, die when the
  session ends (`loginctl enable-linger "$USER"`).
- `/sys/fs/cgroup` is cgroup v2: `stat -f -c %T /sys/fs/cgroup` prints `cgroup2fs`.
- The user manager has the memory controller:
  `/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.subtree_control`
  contains `memory`.
- After install, `systemctl --user show -p MemoryHigh,MemoryMax,MemorySwapMax,DropInPaths lu-dispatch.slice`
  prints finite values and lists the limits drop-in. A slice without the
  drop-in, or a slice name systemd synthesized, reports `MemoryMax=infinity`
  and does not count.

### Install

Order matters, so the limits never lapse: first the deployment installs the
limits drop-in and verifies with `systemctl --user show` that the effective
values are the intended ones; only then is the value-free unit installed from
the updated checkout, followed by `systemctl --user daemon-reload` before more
workers are dispatched. `dispatch_isolation.py` reads the effective `MemoryMax`
and `MemorySwapMax` at runtime and uses the slice only when both are finite;
otherwise dispatch falls back to plain `Popen` without the slice memory cap.

Do not commit a machine path. From a checkout:

```bash
mkdir -p ~/.config/systemd/user
cp packaging/systemd/lu-dispatch.slice ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user show -p LoadState,MemoryHigh,MemoryMax,MemorySwapMax lu-dispatch.slice
```

No `enable` is required. The slice is started when a worker scope is placed in
it. Confirm a live worker with `systemctl --user status <launch_unit>.scope`
or `/proc/<pid>/cgroup`. `--collect` drops the scope unit after the worker
exits.

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
- `learn-ukrainian-api.service`: Monitor API service (`scripts/api/main.py`). A refused API startup makes every endpoint unavailable until the cause is fixed; the unit retries every five seconds.
- `learn-ukrainian-astro.service`: Astro frontend UI.
- `learn-ukrainian-sources.service`: Sources lookup service.
- `learn-ukrainian-work.service`: Work projection adapter.
- `learn-ukrainian-loopback.target`: Target grouping loopback services.

### Word-card release drop-in (`learn-ukrainian-sources.service.d/word-cards.conf`)

Sets `LU_WORD_CARDS_DIR` for the Sources MCP `word_card` tool (#11084). The
variable must be an absolute local directory holding `cards/*.json` plus the
optional `ledger.json` and `build-manifest.json`; unset means `not_configured`,
and relative, empty or `file:` values are refused. The drop-in points at
`data/datasets/word-cards/releases/current-assembly`, a relative symlink to the
current versioned assembly directory (gitignored). `install_data_volume_dropins.py`
only installs `data-volume.conf`, so this file is installed by hand.

Install, from the primary checkout:

```bash
repo_root=$(pwd -P)
unit_dir="$HOME/.config/systemd/user/learn-ukrainian-sources.service.d"
mkdir -p "$unit_dir"
sed -e "s|@REPO_ROOT@|$repo_root|g" \
  packaging/systemd/dropins/learn-ukrainian-sources.service.d/word-cards.conf \
  > "$unit_dir/word-cards.conf"
systemctl --user daemon-reload
systemctl --user restart learn-ukrainian-sources.service
systemctl --user show -p Environment learn-ukrainian-sources.service
```

Roll a new card version: build the new versioned directory next to the old one
under `data/datasets/word-cards/releases/` (directories `0555`, files `0444`),
then flip the pointer and restart. The relative link keeps the drop-in unchanged:

```bash
cd data/datasets/word-cards/releases
ln -sfn <new-version-dir> current-assembly
systemctl --user restart learn-ukrainian-sources.service
```

## Scheduled Maintenance Timers

User timers run background reconciliation, garbage collection, and state
reporting. Target hosts: **any host with a checkout + `batch_state/`** (worker,
runner, and orchestrator hosts).

### 1. Reconciliation Sweep (`learn-ukrainian-reconcile.service` + `.timer`)

- **Frequency**: Every 5 minutes (`OnBootSec=2min`, `OnUnitActiveSec=5min`, `AccuracySec=30s`), so a worker killed by the OOM killer or SIGKILL stops reading `running` within one interval (#8645). Dispatch admission also sweeps dead pids before it counts write workers.
- **What it does**: Runs `scripts/orchestration/reconcile_sweep.py --apply` which:
  1. Releases write-ownership claims for inactive tasks via `dispatch_settle release-stale` (the same reconciliation every dispatch runs at admission).
  2. Marks running/spawning task records whose pid is dead as `crashed` via the existing lazy heal path (`scripts/delegate.py status`). The mark re-checks status, pid, run nonce and liveness under the task's writer lock, so it cannot overwrite a worker's own terminal write; a pid owned by another user, or reused, counts as alive.
  3. Logs a one-line summary count (`scanned_tasks`, `zombies_crashed`, `stale_claims_released`) to stdout/journal.
- **Default mode**: Apply. Run `.venv/bin/python -m scripts.orchestration.reconcile_sweep` by hand (no `--apply`) for a report-only dry run. To make the timer report-only, drop `--apply` from `~/.config/systemd/user/learn-ukrainian-reconcile.service`.
- **Enable or update** (the unit files are templates; install them with `@REPO_ROOT@` replaced):
  ```bash
  systemctl --user daemon-reload
  systemctl --user enable --now learn-ukrainian-reconcile.timer
  ```

### 2. Worktree Garbage Collection (`learn-ukrainian-worktree-gc.service` + `.timer`)

- **Install**: The collector sweeps both registered repository roots. Replace `@REPO_ROOT@` and `@PRIVATE_ROOT@` with those roots before installing it. Templates do not install or enable themselves.
- **Frequency**: Hourly (`OnCalendar=hourly`, `RandomizedDelaySec=0`, `Persistent=true`), with the existing `OnBootSec=15min` startup trigger. The macOS launchd default remains separate.
- **What it does**: Runs `scripts/orchestration/run_scheduled_worktree_cleanup.sh` once with both roots. The existing runner invokes the canonical worktree reaper, eligible branch cleanup, named scratch cleanup, and automatic Git maintenance. Existing retention thresholds and safety proofs stay unchanged.
- **Receipts**: Immutable private receipts bind timestamps and repository slots to roots. Public summaries expose counts for worktrees, branch candidates, and named temp helpers per slot; missing probes report `not_observed`, never zero. Shared host temp observations are not unique per-repository inventory. See `docs/runbooks/worktree-cleanup.md` for comparison limits and the two actual observations required after approved deployment.
- **Default mode**: Apply. The shipped unit passes `--apply`, matching macOS launchd. The reaper stays fail-closed for OPEN PRs, live working directories, dirty worktrees, and unreadable GitHub state — this denser cadence does not loosen any of those guards, it only shrinks the backlog between runs.
- **Disable automatic reaping**: Set `LU_REAPER_DISABLED=1` in the user unit environment to stop automatic reaps, or `LU_REAPER_TERMINAL_DISPATCHES=0` to disable only the optional terminal-dispatch class. Reload systemd after changing the unit:
  ```bash
  systemctl --user daemon-reload
  ```
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-worktree-gc.timer
  ```

### 2b. Clean, Fully Pushed Worktree Reaper (`learn-ukrainian-worktree-reaper.service` + `.timer`)

- **Install**: Use the manual install recipe in `docs/runbooks/worktree-cleanup.md`. It checks that the sibling `learn-ukrainian-infra-private` checkout exists and requires a successful both-root dry run before writing units. It replaces both `@REPO_ROOT@` and `@PRIVATE_ROOT@` in the service template and its data-volume drop-in, then verifies the units before reloading and enabling the timer.
- **Frequency**: every 30 minutes (`OnCalendar=*:00/30`, `Persistent=false`); `TimeoutStartSec=1200`.
- **What it does**: runs `reap_worktrees --clean-pushed --repo-root @REPO_ROOT@ --repo-root @PRIVATE_ROOT@ --apply` with both placeholders replaced, which removes only `.worktrees/dispatch/<agent>/<task>/` checkouts that are clean, have no untracked files, have every commit on origin, are used by no process or live task, and were idle for 60 minutes (#10778). It never forces and never deletes branches. A oneshot unit never overlaps itself, and the reaper lock makes any other concurrent run a no-op. Its only network use is one bounded `git fetch --prune origin` and one bounded `git ls-remote --heads --tags origin` census before the run; if either fails, the run does nothing.
- **Install, verify and disable**: `docs/runbooks/worktree-cleanup.md` § "Clean, fully pushed, idle dispatch worktrees". The templates do not install or enable themselves.

### 3. Project State Reporter (`learn-ukrainian-project-state-reporter.service` + `.timer`)

- **Frequency**: Every 5 minutes (`OnUnitActiveSec=5min`, `OnBootSec=2min`).
- **What it does**: Runs `scripts/orchestration/run_project_state_reporter.sh` to report periodic host project state.
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-project-state-reporter.timer
  ```

### 4. Retired backup and retention timers

`learn-ukrainian-backup.timer` and
`learn-ukrainian-backup-retention.timer` are retired and must remain disabled.
The active offsite job owns scheduled capture; its secondary copy covers the
same completed snapshots. Consult the private operations runbook for current
operating procedures.

The existing service, timer and failure-alert templates remain installed for
manual maintenance. The installer previews without changing installed units or
calling systemctl. With `--apply`, it writes owner-only units, reloads the user
manager, then disables and stops both timers using checked
`systemctl --user disable --now`. It never removes backup data or unit files.
`--enable`, including `--apply --enable`, is refused before any write or
systemctl action; direct Python `apply(..., enable=True)` is also refused.
Stopping the timers does not cancel an already-running service.

After deployment is separately authorized, run from the primary checkout:

```bash
.venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary
.venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary --apply
```

Keep the retired schedules disabled; do not move them to another scheduler.
See [Data backup and recovery](../../docs/runbooks/data-backup.md) for manual
backup, verification, restore and explicit retention commands. The legacy
`last-run.json` receipt and failure-alert template describe legacy service runs;
they do not establish current offsite coverage.

### 5. OpenCode Session Retention (`learn-ukrainian-opencode-retention.service` + `.timer`)

- **Frequency**: daily at 04:15 UTC, with up to 15 minutes of jitter and a persistent catch-up run. Target host: the user account that owns the OpenCode session database.
- **What it does**: deletes a root session and its descendants only when every session in that family was last updated strictly more than seven days ago. `opencode session list --format json` is project-scoped and excludes child sessions, so the job uses a read-only `opencode db` query to list all session IDs, parent IDs, and timestamps in the database, then `opencode session delete` for each selected ID. Children are deleted before parents. A family with an old session and a recent member is skipped and logged with its root ID and newest member's age; unrelated old families are still deleted. It checks that every selected ID is gone and every preserved ID remains. It skips the run when any `opencode` process is active. It logs every deleted ID, checkpoints the WAL through `opencode db`, and logs the main DB and WAL bytes plus SQLite freelist/page counts before and after. It does not issue SQL writes to session tables. Deletion puts pages on SQLite's freelist for later inserts: a successful delete and checkpoint can leave the main DB at its working-set high-water mark while preventing renewed growth from retained old sessions. `VACUUM` is intentionally not run.
- **Preview**: from the primary checkout on the target host, run `"$(pwd -P)/.venv/bin/python" scripts/orchestration/opencode_session_retention.py --dry-run`. Use `--days N` to change the retention window. This preview reads the database through OpenCode's CLI; development tests must use an isolated scratch data directory.
- **Data-volume guard**: install the matching `data-volume.conf` with the unit so the timer checks the configured data volume before retention runs. A failed guard exits 78 and prevents restart.
- **Install, only after operator approval**: from the primary checkout on the target host, render the two templates into the user unit directory, replacing `@REPO_ROOT@` with the absolute checkout path and `@PYTHON@` with that checkout's absolute project interpreter. Verify the rendered units before enabling:
  ```bash
  repo_root=$(pwd -P)
  unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/learn-ukrainian-opencode-retention.service > "$unit_dir/learn-ukrainian-opencode-retention.service"
  cp packaging/systemd/learn-ukrainian-opencode-retention.timer "$unit_dir/"
  mkdir -p "$unit_dir/learn-ukrainian-opencode-retention.service.d"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/dropins/learn-ukrainian-opencode-retention.service.d/data-volume.conf \
    > "$unit_dir/learn-ukrainian-opencode-retention.service.d/data-volume.conf"
  systemd-analyze verify "$unit_dir/learn-ukrainian-opencode-retention.service" "$unit_dir/learn-ukrainian-opencode-retention.timer"
  systemctl --user daemon-reload
  systemctl --user enable --now learn-ukrainian-opencode-retention.timer
  journalctl --user -u learn-ukrainian-opencode-retention.service -n 30
  ```
  The templates do not install or enable themselves.

## Daily issue quality report

`learn-ukrainian-issue-quality-report.service` runs a counts-only fleet census
and publishes its persisted payload to Fleet Comms. Its independent daily timer
runs at 07:00 UTC with up to five minutes of jitter and catches missed runs.
It does not use the five-minute project-state reporter. Private repositories
contribute counts only and explicit unknown membership. A failed publication
fails the service; retry reuses the day's ignored `batch_state/reports/` payload
and idempotency key.

Preview and verify with
`.venv/bin/python -m scripts.orchestration.install_issue_quality_report_timer --check`.
After landing and approval, use `--apply`, or `--apply --enable` to start the
timer. The installer uses `safe_unit_install` and refuses symlinked destinations.
The data-volume drop-in is installed through the existing drop-in installer.
No unit is installed or enabled by tests or by preparing this source candidate.

## Driver lanes: context guard and boot relaunch

Both read the one lane data file, `scripts/config/driver_lanes.json`, and
address every lane by tmux session name (`=<session>:`), never by pane id.
Host-specific launch wrappers and account directories come from the ignored
local config described in `docs/runbooks/maintenance-window.md`.

- `learn-ukrainian-context-guard.service` + `.timer`: every 5 minutes
  (`OnCalendar=*:0/5`) runs `scripts.ops.context_guard tick`. Claude lanes
  hand off at 70% context; Codex lanes after three compactions. A lane that
  prints or posts `HANDOFF-DONE` before the prompt is exited without waiting
  for the threshold. In the handoff phase the guard re-sends `HANDOFF NOW`
  every 15 minutes, retries `/exit` or `/quit` every 10 minutes, logs
  `ctx_pct` on every tick, and types nothing while a human typed into that
  session within two minutes. Unknown state never acts: failed, timed-out
  or unparseable pane, process or client telemetry makes the tick log and
  retry, and a different agent process in a lane resets that lane to the
  watch phase before any further input. The guard respawns or types only on
  one consistent snapshot of the pane and the process table, re-taken right
  before `respawn-pane -k`, the exit-dialog answer and `/exit` or `/quit`;
  the one residual (owner: Infra) is a pane replaced after that re-check and
  before the tmux call, since tmux has no compare-and-swap. State and log live under
  `${XDG_STATE_HOME:-$HOME/.local/state}/learn-ukrainian/context-guard/`.
  Keep-alive tools must skip the sessions printed by
  `.venv/bin/python -m scripts.ops.context_guard handoff-sessions`. The
  service has a data-volume drop-in like the other timer services, installed
  with the rest by `scripts/storage/install_data_volume_dropins.py`.
- `learn-ukrainian-lane-relaunch.service`: a oneshot wanted by
  `default.target`. At boot it recreates each missing lane session in the
  repository root and starts its launcher, CTO last. Existing sessions are
  skipped, so a second run is a no-op, and it never types into a session. A
  launcher that exits within 20 seconds (for example on a lease conflict) is
  logged and the relaunch moves on; the unit then exits 3, as it does when a
  lane's local config entry is refused (that lane is not started) or a new
  pane cannot be read back. `--server-scope`
  starts a missing tmux server in its own user scope so it outlives the
  oneshot. Preview with `.venv/bin/python -m scripts.ops.lane_relaunch --dry-run`.

Install from the primary checkout after review. Stop the transient guard timer
first so two guards never act on the same lane, then render, verify and enable:

```bash
repo_root=$(pwd -P)
unit_dir="$HOME/.config/systemd/user"
systemctl --user stop lu-codex-context-guard.timer || true  # the transient guard it replaces
for unit in learn-ukrainian-context-guard.service learn-ukrainian-context-guard.timer \
    learn-ukrainian-lane-relaunch.service; do
  sed -e "s|@REPO_ROOT@|$repo_root|g" "packaging/systemd/$unit" > "$unit_dir/$unit"
done
systemd-analyze --user verify "$unit_dir"/learn-ukrainian-context-guard.* \
  "$unit_dir/learn-ukrainian-lane-relaunch.service"
systemctl --user daemon-reload
systemctl --user enable --now learn-ukrainian-context-guard.timer
systemctl --user enable learn-ukrainian-lane-relaunch.service
```

Enable the relaunch without `--now`: on a running host every lane session
exists, so starting it would only log skips. The guard starts with fresh state,
so Codex compaction counts restart from zero.

### 6. Sources MCP Watchdog (`learn-ukrainian-sources-watchdog.service` + `.timer`)

- **Why**: a hung sources server stays `active/running` in systemd, so `Restart=` never fires (#10674).
- **Frequency**: every 15 seconds (`OnUnitActiveSec=15s`, `AccuracySec=1s`).
- **What it does**: runs `scripts/orchestration/sources_watchdog.py run-once --apply`. It probes `http://127.0.0.1:8766/health` with a 5 s timeout. After three consecutive failures of the same main process of a running unit (about 45 s) it:
  1. writes an incident directory under `batch_state/sources-dumps/` (or `$LU_SOURCES_DUMP_DIR`): a `/proc` snapshot of thread states, wait channels, socket states on the port and the accept backlog; `py-spy dump --native` when py-spy is installed and allowed to attach; and the server's all-thread Python stacks, which it asks for with `SIGUSR1` (the server registers a `faulthandler` dump at startup, so this needs no py-spy and works while every thread is blocked);
  2. probes `/health` once more and re-reads the unit's main process (pid and start time). If the server recovered during the dump, or the unit now runs another process or is no longer active, it does not restart and records `restart aborted: recovered` or `restart aborted: changed`;
  3. otherwise sends `SIGKILL` to the unit (a process blocked on the GIL never runs its `SIGTERM` handler) and starts it again, then waits up to 90 s for `/health`;
  4. posts one report to the Fleet Comms `cto` channel per incident (`--sender sre-timers`, the publisher `backup_failure_alert.py` uses). An incident closes after 10 minutes of health following its last restart.
- **No restart loop**: at most three restarts per rolling hour, counted from a restart history in `watchdog-state.json` that closing an incident does not clear; beyond that it does not dump or restart, and an incident that opens with the budget spent is still reported once. It acts only on `learn-ukrainian-sources.service`: `--unit` accepts no other name, and the restart code refuses any other unit too. A unit that is not active is never touched, so an operator stop or a crash stays with systemd. The newest 20 incidents are kept.
- **Preview and drills**: `.venv/bin/python -m scripts.orchestration.sources_watchdog run-once` (no `--apply`) reports what it would do. `... sources_watchdog dump --pid <MainPID>` captures an incident dump of a live process without restarting it.
- **Install** (the driver, after review and merge, from the primary checkout):
  ```bash
  repo_root=$(pwd -P)
  unit_dir="$HOME/.config/systemd/user"
  for unit in learn-ukrainian-sources-watchdog.service learn-ukrainian-sources-watchdog.timer; do
    sed -e "s|@REPO_ROOT@|$repo_root|g" "packaging/systemd/$unit" > "$unit_dir/$unit"
  done
  mkdir -p "$unit_dir/learn-ukrainian-sources-watchdog.service.d"
  sed -e "s|@REPO_ROOT@|$repo_root|g" \
    packaging/systemd/dropins/learn-ukrainian-sources-watchdog.service.d/data-volume.conf \
    > "$unit_dir/learn-ukrainian-sources-watchdog.service.d/data-volume.conf"
  systemd-analyze verify "$unit_dir/learn-ukrainian-sources-watchdog.service" "$unit_dir/learn-ukrainian-sources-watchdog.timer"
  systemctl --user daemon-reload
  .venv/bin/python -m scripts.orchestration.sources_watchdog run-once   # preview: expect "healthy"
  systemctl --user restart learn-ukrainian-sources.service              # loads the SIGUSR1 dump handler
  systemctl --user enable --now learn-ukrainian-sources-watchdog.timer
  journalctl --user -u learn-ukrainian-sources-watchdog.service -n 20
  ```
  `py-spy` is optional; installing it is a separate reviewed host step.
- **Inside the server** (`scripts/rag/call_governor.py`): at most 12 tool calls hold a slot at once and the rest queue for up to 30 s; a call with no result after 120 s is answered `Tool call failed: <tool> (call_timeout: ...)`, a call that cannot get a slot `(... server_busy: ...)`. A timed-out call keeps its slot until its worker thread actually finishes (Python cannot kill the thread), so timeouts never let more than 12 calls' work run at once; while every slot is held by such work, new and queued calls are refused at once with `(... server_overloaded: ...)`. The calls' worker threads come from the server's own pool of the slot count plus 4, not Python's default pool (`min(32, CPUs + 4)` threads), so all 12 slots can run on any host and no call's timeout is spent waiting for a thread. Each call logs `call_start`/`call_end` lines (id, tool, in-flight, queued and abandoned counts, outcome, duration; never argument values) to the service log, and a timed-out call a `call_released` line when its work ends. A call still running after 60 s writes `slow-call-*.txt` (all-thread stacks) into the dump directory, which the watchdog rotates. Override with `LU_SOURCES_MAX_CONCURRENT_CALLS`, `LU_SOURCES_QUEUE_TIMEOUT_S`, `LU_SOURCES_CALL_TIMEOUT_S` and `LU_SOURCES_SLOW_CALL_DUMP_S`.
