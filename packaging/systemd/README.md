# Systemd unit templates (loopback services & scheduled maintenance)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled via `loginctl enable-linger $USER`) or
`/etc/systemd/system/`, replace `@REPO_ROOT@` / `@PRIVATE_ROOT@`, run
`systemctl --user daemon-reload`, then enable/start.

## Dispatch worker slice (`lu-dispatch.slice`)

One slice for every detached worker `scripts/delegate.py` launches (#8645). The
driver stays outside it. A runaway worker is killed inside the slice; the driver
and the host services are not in that cgroup.

`MemoryHigh=10G` is the throttling line and `MemoryMax=11G` is the last line of
defense. `systemd.resource-control(5)` (this host's systemd 259 man page) says to
use `MemoryHigh=` as the main control and `MemoryMax=` only as the last line of
defense, so `MemoryHigh` sits just under `MemoryMax` (10GiB / 11GiB). `MemoryMax=`
does not cap swap — the 2026-09-24 scope used 6.3GiB of swap — so the unit also
sets `MemorySwapMax=1G`. The limits are the unit file. There is no environment
override.

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
- After install, `systemctl --user show -p MemoryMax,MemorySwapMax lu-dispatch.slice`
  prints `MemoryMax=11811160064` and `MemorySwapMax=1073741824` (11GiB and 1GiB,
  base 1024). A slice name systemd synthesized with `MemoryMax=infinity` does
  not count.

### Install

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

- **Frequency**: Every 4 hours (`OnBootSec=15min`, `OnUnitActiveSec=4h`, `RandomizedDelaySec=1800`, `Persistent=true`) — matches the macOS launchd cadence.
- **What it does**: Runs `scripts/orchestration/run_scheduled_worktree_cleanup.sh` to prune stale worktree registrations, clean up merged/closed PR branches, and run automatic git maintenance with receipt logging.
- **Default mode**: Apply. The shipped unit passes `--apply`, matching macOS launchd. The reaper stays fail-closed for OPEN PRs, live working directories, dirty worktrees, and unreadable GitHub state — this denser cadence does not loosen any of those guards, it only shrinks the backlog between runs.
- **Disable automatic reaping**: Set `LU_REAPER_DISABLED=1` in the user unit environment to stop automatic reaps, or `LU_REAPER_TERMINAL_DISPATCHES=0` to disable only the optional terminal-dispatch class. Reload systemd after changing the unit:
  ```bash
  systemctl --user daemon-reload
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

### 4. Data Backup (`learn-ukrainian-backup.service` + `.timer`) and Retention (`learn-ukrainian-backup-retention.service` + `.timer`)

- **Frequency**: backup daily at 03:30 UTC (`OnCalendar=*-*-* 03:30:00 UTC`, `Persistent=true`, `RandomizedDelaySec=15min`); retention weekly on Sunday at 05:15 UTC, after that day's backup. Target host: the data host whose checkout holds the live `data/` tree.
- **What it does**: the backup service runs `scripts/orchestration/run_scheduled_backup.sh`, which executes `scripts/backup-data.sh backup --execute` (restic via the rclone remote) and records the outcome in `batch_state/backups/last-run.json`. The retention service uses the same wrapper's `retention` mode to run `scripts/backup-data.sh retention --execute`, applying the operator-approved `--keep-daily 7 --keep-weekly 4 --keep-monthly 6` policy run-aware to the `learn-ukrainian-data` tag only: completed runs are kept or dropped as a unit and snapshots are forgotten by explicit snapshot ID, so a retained receipt never loses a snapshot it references. Other snapshot families in the repository are untouched.
- **Secrets**: both services read `EnvironmentFile=%h/.secrets/learn-ukrainian-backup.env` (repository + password-file path). Validation errors name the variable and condition without its value. The wrapper redacts the configured repository, its rclone spec without the `rclone:` prefix, and the password-file path from both services' output before it reaches the journal. The unit fails visibly when the file is missing.
- **Disk safety**: `LU_BACKUP_TMPDIR=@REPO_ROOT@/data/.backup-staging` keeps SQLite staging on the same filesystem as `data/` (gitignored; see `scripts/backup-data.sh` — databases are staged sequentially and each staged copy is deleted before the next). `Nice=15` + `IOSchedulingClass=idle` keep the run off the fast path; `TimeoutStartSec=10800` allows one hour of lock wait plus two hours for backup or retention.
- **Data-volume guard**: the two backup services have drop-ins among the twelve in `packaging/systemd/dropins/`. Each checks the configured data volume before executing the redacting `run_scheduled_backup.sh` wrapper; a failed guard exits 78 and does not restart. Install the drop-ins as described in `docs/runbooks/storage-topology.md` before enabling the timers on a migrated data host.
- **Failure visibility**: a failed run exits non-zero, and a failed log capture or `last-run.json` write fails the backup service even when the backup succeeded, so `systemctl --user list-timers` and `journalctl --user -u learn-ukrainian-backup.service` show it; `last-run.json` carries start/end, exit status, run id, snapshot count, and bytes added. A systemd timeout or SIGTERM may leave the previous receipt in place; check its timestamp alongside the unit status.
- **Install** (preview by default; writes only with `--apply`):
  ```bash
  .venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary
  .venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary --apply --enable
  ```

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

### 6. jevgrep auto-update (`learn-ukrainian-jevgrep-update.service` + `.timer`)

- **Frequency**: every 6 hours (`OnCalendar=*-*-* 00/6:00:00`, `RandomizedDelaySec=20min`, `Persistent=true`). Target host: any host whose agents use `jg` (#9134).
- **What it does**: runs `scripts/tools/jevgrep_update.py --json`, which keeps `@dzhng/jevgrep` (`~/.local/bin/jg`) at npm `latest`. Each run holds an exclusive lock (`~/.local/state/learn-ukrainian/jevgrep-update.lock`); a run that finds it held changes nothing and exits 0. Each run first rewrites `~/.claude/skills/jevgrep/SKILL.md` and `~/.agents/skills/jevgrep/SKILL.md` (tracked overlay + the upstream skill body of the package `~/.local/bin/jg` resolves to), so a CLI/skill mismatch left by a failed restore heals within one timer interval. It installs a new release only when the `registry.npmjs.org` metadata shows npm provenance attestations, no install scripts, `bin.jg`, only plain semver dependency ranges and no bundled dependencies, and a `registry.npmjs.org` tarball with a sha512 `dist.integrity`. Metadata and tarball requests follow no redirects and are size-capped. It verifies the tarball against `dist.integrity` and installs the local file with `--ignore-scripts --no-package-lock --registry=https://registry.npmjs.org/` into its own prefix under `~/.local/share/learn-ukrainian/jevgrep/`; npm gets no inherited `npm_config_*` variables and empty user and global config files. Every other package npm placed in the prefix must show a `https://registry.npmjs.org/` `resolved` URL and an `integrity` in the staged `node_modules/.package-lock.json`, or the prefix is deleted (`dependency_source_refused`). The staged `jg --version` and `jg doctor` must pass, and its upstream skill file must exist, before the `~/.local/bin/jg` symlink is switched atomically. A failed switch check or skill write restores the previous link and skill files without a download and checks them again. The active and previous prefixes are kept; the older `npm -g` install is left in place. Each run appends one JSON line (exit codes and fixed failure classifications, never child output) to `~/.local/state/learn-ukrainian/jevgrep-update.jsonl`.
- **Prerequisite**: the operator has run `jg auth` once on the host (see `agents_extensions/shared/skills/jevgrep/UPSTREAM.md`); without it `jg doctor` fails and new releases are never switched in.
- **Hold a version**: `systemctl --user edit learn-ukrainian-jevgrep-update.service`, add `Environment=JEVGREP_HOLD_VERSION=<x.y.z>` under `[Service]`; remove it to return to `latest`.
- **Data-volume guard**: install the matching `data-volume.conf` drop-in with the unit, as for the other timers.
- **Install (driver host maintenance; no operator approval gate — only `jg auth` is operator-only)**: preview first with `"$(pwd -P)/.venv/bin/python" scripts/tools/jevgrep_update.py --dry-run --json`, then from the primary checkout:
  ```bash
  repo_root=$(pwd -P)
  unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir/learn-ukrainian-jevgrep-update.service.d"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/learn-ukrainian-jevgrep-update.service > "$unit_dir/learn-ukrainian-jevgrep-update.service"
  cp packaging/systemd/learn-ukrainian-jevgrep-update.timer "$unit_dir/"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/dropins/learn-ukrainian-jevgrep-update.service.d/data-volume.conf \
    > "$unit_dir/learn-ukrainian-jevgrep-update.service.d/data-volume.conf"
  systemd-analyze verify "$unit_dir/learn-ukrainian-jevgrep-update.service" "$unit_dir/learn-ukrainian-jevgrep-update.timer"
  systemctl --user daemon-reload
  systemctl --user enable --now learn-ukrainian-jevgrep-update.timer
  journalctl --user -u learn-ukrainian-jevgrep-update.service -n 30
  ```
