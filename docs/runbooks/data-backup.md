# Data Backup and Recovery

`scripts/backup-data.sh` creates encrypted, versioned restic snapshots of the
project's recovery-critical local state through an rclone remote. It does not
write through the cloud provider's desktop sync mount, overwrite the previous backup,
or restore directly over live project data. Snapshot pruning exists only as
the operator-approved weekly `retention` command described below.

The nightly reads one allowlist, `scripts/config/backup-allowlist.json`, and
backs up every kept path in one run. On Linux a clean run writes a bounded
number of restic snapshots that does not grow by one per database: one base
snapshot, `ceil(N / K)` database-batch snapshots, and two receipt snapshots
(pending, then completion). `N` is the number of databases in the run. `K` is
how many copies of the largest database fit in
`LU_BACKUP_DB_BATCH_MAX_BYTES` (`max(1, floor(budget / largest))`). A database
larger than the budget is its own batch. `data/lexicon/cache/ulif_raw.sqlite`
is one consistent SQLite snapshot inside a database batch, not its own restic
run. A dirty worktree adds one `lu-part-patch` snapshot. `BACKUP-RECEIPT.json`
is the receipt those final snapshots carry. A path that is not in the
allowlist is not backed up: the script does not walk it, does not stage it,
and does not fail because it exists. Drop rows are documentation of that
boundary. They are not exclude rules, so the kept file
`data/lexicon/cache/ulif_raw.sqlite` is still snapshotted even though
`data/lexicon/cache` is dropped.

`data/lexicon/runner-mirror` is an optional keep so the existing gate receipt
can compare that tree with the snapshot. A host with no mirror logs one line
and continues. Do not remove it while the gate receipt still names this path.

Required paths abort the run when they are missing. Optional paths log
`Optional backup path is absent: <path>` once and continue.

| Class | Paths |
| --- | --- |
| Required | `.claude/*-epic` (also when the glob matches nothing), `.agent`, `batch_state/fleet-comms`, `batch_state/review-receipts`, `data/sources.db` |
| Optional | every other KEEP row |

A non-ignored untracked file inside an allowlisted tree that the selection
does not cover still fails the run. An untracked file outside the allowlist
does not.

`data/lexicon/*.json` selects every regular file whose name ends in `.json`
and whose parent is `data/lexicon`. There is no size cutoff. Nested
directories are not included. Measured read-only on 2026-10-13T15:31:18Z:
8 files, 10675420 bytes.

To add a path, edit `scripts/config/backup-allowlist.json` and the KEEP table
below in the same change. Do not add a path by editing `scripts/backup-data.sh`.
Set `required` only when a missing path must abort the nightly. A supervised
run on the backup host is what shows that a nightly finishes; this page only
records the scope.

<!-- backup-allowlist-keep -->

| Path | Required | Reason |
| --- | --- | --- |
| `.claude/*-epic` | yes | Driver plans and handoffs are the only copy of in-flight epic state. |
| `.agent` | yes | Agent recovery state is local and is not in Git. |
| `data/sources.db` | yes | The corpus database is the source of truth for dictionary text. |
| `data/sum20_slovnyk_staging.db` | no | SUM-20 slovnyk staging is costly to rebuild. |
| `data/sum20_staging.db` | no | SUM-20 staging is costly to rebuild. |
| `data/lexicon/slovnyk_cache` | no | The slovnyk cache is costly to rebuild. |
| `data/lexicon/source-inventory` | no | Source inventory is the lexicon intake record. |
| `data/lexicon/side` | no | Side lexicon inputs are not regenerated from Git. |
| `data/lexicon/intake` | no | Lexicon intake is not regenerated from Git. |
| `data/lexicon/parked` | no | Parked lexicon inputs are not regenerated from Git. |
| `data/lexicon/*.json` | no | Every regular JSON file directly under data/lexicon. No size cutoff; nested directories are not included. |
| `data/lexicon/runner-mirror` | no | The gate receipt proves this tree matches the snapshot before a wipe. |
| `data/movaua.db` | no | The movaua corpus is costly to rebuild. |
| `data/movne_pytannya.db` | no | The language-question corpus is costly to rebuild. |
| `data/grac_frequency.db` | no | The GRAC frequency database is costly to rebuild. |
| `data/atlas.db` | no | The atlas database is costly to rebuild. |
| `data/wiki_*.db` | no | Wiki databases matched by this non-recursive glob. |
| `data/lexicon/cache/ulif_raw.sqlite` | no | ULIF raw cache is one SQLite snapshot in the same nightly. |
| `data/textbook_chunks` | no | Textbook chunks are costly to rebuild. |
| `data/projects` | no | Project data is not regenerated from Git. |
| `data/mphdict` | no | mphdict inputs are costly to rebuild. |
| `data/native-reviewer-lessons` | no | Native-reviewer lessons are not regenerated from Git. |
| `data/ua-gec` | no | UA-GEC inputs are costly to rebuild. |
| `data/ubertext-freq` | no | UberText frequencies are costly to rebuild. |
| `data/processed` | no | Processed inputs are costly to rebuild. |
| `data/datasets` | no | Datasets are costly to rebuild. |
| `batch_state/fleet-comms` | yes | Fleet Comms is the durable message and job store. |
| `batch_state/review-receipts` | yes | Review receipts are the record of independent review. |
| `batch_state/branch-archive` | no | Branch archive is the local copy of superseded branch state. |
| `batch_state/tasks` | no | Task records and archive only; lock files and snapshot directories are excluded. |
| `batch_state/open-model-data` | no | Open-model data stays until the data lane says it is regenerable. |
| `batch_state/open-model-data-20261007` | no | This open-model snapshot stays until the data lane says it is regenerable. |

<!-- backup-allowlist-drop -->

| Path | Reason |
| --- | --- |
| `batch_state/codex-atlas` | Atlas worker checkouts are regenerable. |
| `batch_state/preserved` | Preserved SQLite evidence is outside the nightly. |
| `batch_state/devops-*` | Devops scratch is regenerable. |
| `batch_state/briefs` | Briefs are regenerable. |
| `batch_state/github-client` | GitHub client cache is regenerable. |
| `batch_state/backups/archives` | Packed archives are not a nightly root. |
| `batch_state/reports` | Reports are regenerable. |
| `batch_state/bakeoff-*` | Bakeoff output is regenerable. |
| `batch_state/telemetry` | Telemetry is regenerable. |
| `batch_state/manifests` | Generated manifests are regenerable. |
| `data/backups` | Local backup copies are not a nightly root. |
| `data/vesum.db` | VESUM is rebuilt from its source, not recovered from this nightly. |
| `data/vesum_shadow_v680.db` | VESUM shadow is rebuilt, not recovered from this nightly. |
| `data/vesum.db.bak.*` | VESUM backups are outside the nightly. |
| `data/lexicon/cache` | Lexicon cache is dropped except the allowlisted ulif_raw.sqlite file. |

The old `learn-ukrainian-data` Drive folder is a read-only legacy recovery
source. Do not use it as the new restic repository path; the script rejects a
restic rclone path with that final directory name.

## Safety model

- `init`, `backup`, `retention`, and `restore` are previews unless `--execute`
  is explicit.
- On macOS, a backup executes from a private copy-on-write staging tree outside
  the checkout. The staging capacity check covers selected recovery trees,
  SQLite overhead, and a 2 GiB reserve.
- On macOS, source and staging must be on the same volume before APFS
  copy-on-write staging; a cross-volume staging location fails closed.
- On Linux, restic reads non-database files directly from the live recovery
  roots. Each SQLite database is copied one at a time with SQLite's online
  `.backup` command into a private staging batch and checked with
  `PRAGMA integrity_check`; a database that fails either step is never
  uploaded. The batch is uploaded as one `lu-part-db` restic snapshot and
  cleared once the next database copy would push it past
  `LU_BACKUP_DB_BATCH_MAX_BYTES` (default 1 GiB; a larger database goes
  alone), and at the end of the phase. Each copy is measured before it joins
  the batch, because it includes committed WAL content and can be larger than
  the source's main file. Each restic run pays a fixed repository
  open, index load, and lock cost, so one upload per database made runs with
  thousands of small databases take hours. The snapshot count for a clean run
  is one base snapshot, plus `ceil(N / K)` database batches, plus the pending
  receipt and the completion receipt. `K` is `max(1, floor(batch budget /
  largest database))`. The ULIF file is one consistent SQLite snapshot inside
  a batch. Before each database, the script
  checks staging free space against its DB plus WAL size and a 2 GiB reserve;
  if that fails while a batch is pending, it uploads the batch and checks
  again. No reflink or full-tree copy is required, so peak extra disk is at
  most about the batch budget plus one database copy, never the sum.
  Non-database files can
  change while restic reads them; coordinate writers for application-level
  consistency and inspect recovery-critical manifests during a restore drill.
- On Linux, `LU_BACKUP_TMPDIR` may point at the designated staging parent
  `<project>/data/.backup-staging` (the value the backup systemd unit sets).
  That keeps staging on the same filesystem as `data/`, so staging follows
  `data/` onto a future dedicated volume and the free-space preflight measures
  the data filesystem. The directory is gitignored and excluded from every
  scan and restic phase; any other staging location inside the checkout still
  fails closed.
- Every `*.db` and `*.sqlite*` under selected roots (including `.agent/`)
  is rebuilt with SQLite's online backup command.
- SQLite WAL/SHM/journal sidecars for selected databases,
  plus `__pycache__`, `.DS_Store`, and retired `qdrant/` data, are excluded.
- A selected SQLite database with more than one directory entry stops the
  backup before any snapshot is written, whatever its filename. The extra
  name does not carry the WAL, SHM, or journal of the path SQLite opened.
- All exclude patterns go to restic through a private `--exclude-file`, never
  as one `--exclude` flag per path, so thousands of databases cannot overflow
  the kernel argument limit. Literal paths are escaped for restic's pattern
  syntax, including `$` and spaces, which exclude files would otherwise expand
  or trim.
- On Linux, databases under a pytest base temp directory (any `pytest-*`
  path component below the project, such as `pytest-of-<user>` or a
  `--basetemp` like `pytest-RC`) are per-run test scratch: they are neither
  uploaded nor kept in the file phase, and the receipt counts them.
- The default archive directory `batch_state/backups/archives` is outside
  the allowlist, so the nightly does not read it and does not warn about it.
  Preserved SQLite evidence can still be packed into `NAME.tar.zst` with a
  `NAME.tar.zst.manifest` (`# archive_bytes:` and `# files:` headers, then one
  `size<TAB>mtime<TAB>project-relative path` line per database) when
  `LU_BACKUP_DB_ARCHIVE_DIR` points at a directory inside an allowlisted tree.
  The file phase uploads that archive; a listed database whose size and mtime
  still match is excluded as a loose file. A database that changed after
  archiving is backed up loose with a warning, and a manifest whose archive is
  missing or a different size is ignored with a warning. Verify the archive
  (listing, count and per-file hashes) before writing its manifest; the
  originals are never deleted by the backup.
- The backup logs `SQLite databases backed up: N of M (...)`; `last-run.json`
  records `databases_backed_up`, and the change-only failure and recovery
  alerts include it.
- Scoped `*-home/` directories under allowlisted `batch_state/` trees, and
  `home/` directories in `batch_state/review-receipts/`, are excluded. Review
  homes are ephemeral and may contain credential links. Absolute or escaping
  symlinks under an allowlisted `batch_state/` tree are skipped with a
  warning. The same links under any other allowlisted tree stop the backup.
- The legacy `data/textbooks` and `data/vesum` symlinks are excluded only when
  they resolve inside the old Drive backup. Other absolute or escaping
  symlinks stop the backup.
- `.agent/` must be a real directory. Broken, absolute, or escaping symlinks
  below it, and unsupported special files, stop the backup before restic runs.
- Restore accepts only an absolute empty or nonexistent directory outside the
  project, cloud mounts, and the legacy backup.
- The only snapshot deletion is `retention [--execute]`. It lists this backup
  family's snapshots (`--tag "$BACKUP_TAG"`), groups them into runs by the
  `lu-run-<id>` tag each snapshot carries, applies
  `--keep-daily 7 --keep-weekly 4 --keep-monthly 6` to completed runs (those
  with a `lu-part-complete` snapshot; a run with only its pending
  `lu-part-receipt` snapshot is incomplete), and forgets by explicit snapshot ID only the
  snapshots of runs outside the keep set. A retained receipt therefore never
  loses a snapshot it references, and a partial newer run can never displace
  one: runs newer than the newest completed run are always kept. `prune` runs
  as a separate explicit step. Other snapshot families in the same repository
  are never selected. It is a preview unless `--execute` is supplied and is
  scheduled weekly, not on every backup.
- Restic commits snapshots atomically. A failed upload does not replace an
  earlier recovery point. On Linux, a run is published in two phases. The
  receipt is first uploaded as a pending `lu-part-receipt` snapshot with a
  fixed `--time`. Then every step that can fail runs: the repository check
  (which covers every snapshot of the run, including the pending receipt), the
  upload-summary checks, the runner-mirror comparison, and staging of the local
  gate receipt. Only then are the same receipt bytes uploaded again, at the
  same time, tagged `lu-part-complete`. That upload reuses the checked tree
  and adds only a snapshot file, and it is the run's last repository write.
  `restore latest` selects only completed runs, so a run that fails or is
  killed before that upload is never selected. No snapshot is ever retagged
  or removed by a backup (`restic tag` rewrites snapshots and deletes the
  originals, and reports per-snapshot failures with exit 0).
- The repository check runs before the completion upload, so it cannot see
  that snapshot file. If the file is later damaged, restic skips it when
  listing snapshots. `restore latest` then selects the previous completed run.
  The damaged run can still be restored by its pending `lu-part-receipt`
  snapshot ID. The next backup's repository check fails, as do `verify` and
  retention, so the damage is reported rather than silently trusted.

Restic documents the [rclone backend][restic-rclone], [backup dry runs][restic-backup],
[restore dry runs][restic-restore], and [repository integrity checks][restic-check].
SQLite documents why its [online backup API produces a consistent snapshot][sqlite-backup].

[restic-rclone]: https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#rclone
[restic-backup]: https://restic.readthedocs.io/en/stable/040_backup.html#dry-runs
[restic-restore]: https://restic.readthedocs.io/en/stable/050_restore.html#dry-runs
[restic-check]: https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-integrity-and-consistency
[sqlite-backup]: https://www.sqlite.org/backup.html

## Open dependency: Cloud backup provider OAuth configuration

**Tracked:** [#6093](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6093) — *do not close until proven fixed.*

The scheduled backup job (`learn-ukrainian-backup` → `~/.local/bin/learn-ukrainian-backup`) requires
an operator-configured OAuth client and periodic authorization refresh:

- Config lives outside git (`~/.secrets/learn-ukrainian-backup.env` via `LU_BACKUP_ENV_FILE`, dedicated rclone config).
- Do **not** put client secrets, tokens, or password files in the repo, issues, or receipts.
- Procedure: configure dedicated OAuth credentials,
  then re-auth the remote and prove `backup-data.sh doctor`, one `backup --execute`,
  `snapshots`, `verify`, and a green scheduled run (acceptance on #6093).

Until #6093 is closed, treat this as a **time-bounded operational prerequisite**, not noise.

---

## One-time setup

Install current restic and rclone releases:

```bash
brew install restic rclone
restic version
rclone version
```

Configure a dedicated rclone remote. The examples use `<backup-remote>`; another
name is fine as long as the environment below matches it.

```bash
rclone config
rclone lsd <backup-remote>:
```

Create a unique restic password file:

```bash
mkdir -p "$HOME/.config/restic"
umask 077
openssl rand -base64 48 > "$HOME/.config/restic/learn-ukrainian.password"
chmod 600 "$HOME/.config/restic/learn-ukrainian.password"
```

Store the password separately in a password manager or offline recovery kit.
Losing it makes every restic snapshot unrecoverable. Do not commit it and do
not keep the only copy in the same cloud account as the repository.

Set the repository and password-file locations in the shell environment:

```bash
export LU_BACKUP_REPOSITORY='rclone:<backup-remote>:<path/to/backup-repo>'
export RESTIC_PASSWORD_FILE="$HOME/.config/restic/learn-ukrainian.password"
```

Preview repository initialization, confirm the remote path, and then execute
it once:

```bash
./scripts/backup-data.sh init
./scripts/backup-data.sh init --execute
./scripts/backup-data.sh doctor
```

`doctor` reports `NOT READY` before initialization; that is expected.

## Create a backup

First run the non-mutating preview:

```bash
./scripts/backup-data.sh backup
```

Review the selected root list, byte/file counts, excluded legacy symlinks,
known missing paths, SQLite list, and the restic change list. The Linux preview
shows the live non-database selection; it does not stage databases. Then create
the backup:

```bash
./scripts/backup-data.sh backup --execute
```

The execute path checks repository metadata after the snapshots. It does not
prune old versions. A per-user `flock` under `XDG_RUNTIME_DIR` (or `/run/user/$UID`,
then `/tmp`) serializes backup, retention, init, and restore execution. It waits
up to one hour; a timeout fails visibly. The kernel releases the lock after a
crash, and the next lock holder clears stale private staging before running.
The `flock` command is required on the backup host (`brew install flock` on macOS).

Each successful run contains `BACKUP-RECEIPT.json` with:

- UTC creation time, stable host label, Git SHA, and receipt preparation status;
- the selected root labels with file and byte counts;
- whether a tracked-worktree patch was needed;
- the count of untracked non-ignored files not included (normally zero);
- exclusions, known missing paths, and the restore command.

On macOS, path counts are calculated from the staged tree after exclusions.
On Linux, they are calculated from the live source inventory after exclusions;
concurrent non-database writes can change the actual uploaded byte counts.

The Linux receipt also lists each database's relative path, snapshot ID, and
mode, the live-file snapshot ID, and an optional patch snapshot ID. Databases
uploaded in one batch share a snapshot ID, and the Linux receipt carries
`schema_version: 3` to mark that layout (macOS receipts stay schema 1).
Restore any run with the current repository script. Older scripts refuse a
schema 3 receipt before restoring anything. The current script also restores
both schema 2 layouts: runs written by the batching build (shared database
snapshots) and historical runs with one snapshot per database. All parts share
one run ID, and the final receipt snapshot is tagged `lu-part-complete`.
`restore latest` uses that completed receipt to reassemble the tree, restoring
each database snapshot once; `--path` of one database restores only that file
from its snapshot. `--path` may contain glob characters (`*`, `?`, `[`, `\`)
only when it names a database path recorded in the receipt; that file is then
matched literally. Any other `--path` with glob characters is refused before
anything is written. The remote repository itself is encrypted. The final
process exit code belongs to the operator log; the in-snapshot receipt does
not record it.

When `data/lexicon/runner-mirror/` exists, a successful `backup --execute`
also writes its local `RESTIC-GATE-RECEIPT.json` after the repository
check. This is distinct from the in-snapshot `BACKUP-RECEIPT.json`: it binds
each current runner-mirror `manifest.json` checksum to the completed restic
snapshot so the pre-wipe gate works without credentials or network access.

A run is selectable if and only if its data snapshots are complete and
verified. `restore latest` selects a run only when its `lu-part-complete`
snapshot exists, and that snapshot is uploaded only after the repository
check, the upload-summary checks, and the runner-mirror comparison have
passed. The gate receipt is a separate artifact. Its absence keeps the
pre-wipe gate closed. It does not decide whether the run is selectable.

On Linux, the script compares the runner-mirror file list with the live
mirror and its manifest after the repository check. The compared snapshots are
the base snapshot plus every database batch that holds files in that tree: a
SQLite file in the mirror is uploaded in a database batch, not the base
snapshot. Ordinary files are compared by SHA-256. A SQLite file is compared by
`sqlite3 .dump`, because the online backup is not byte-identical to the live
file. A missing, extra, or changed file still fails the run. An absent mirror
logs one line and the run continues. The script writes the gate receipt to
`RESTIC-GATE-RECEIPT.json.tmp` in the same
directory as its destination, and only if the live mirror still has those
hashes. Any failure before the completion snapshot publishes nothing and
removes the staged file. After the completion snapshot is saved, the script
renames the staged file into place with same-directory `mv -T`, then checks
that the destination is a readable regular file. Nothing else that can fail
runs after that snapshot. The receipt is not renamed first: that order could
open the pre-wipe gate for a run whose data snapshots were not finished.

The pre-wipe gate (`_require_restic_gate_receipt` in
`scripts/lexicon/runner/durable_mirror.py`) checks the receipt's base
snapshot ID, its freshness, and the manifest fingerprints. It does not check
the completion tag. Selectability is the completed, verified data snapshots,
not the gate receipt. A mirror change after staging (while the completion
snapshot uploads) leaves a receipt for the verified manifest only, so the
gate refuses the changed mirror.

**Accepted commit-follower window.** If the process is killed after the
completion snapshot is saved, or the final rename fails, the data snapshots
are complete and verified, so the run stays selectable and restorable. The
command exits non-zero and no gate receipt is published, so the pre-wipe gate
stays closed until a later backup writes one. A kill can also leave the
staged `.tmp` file, which the gate ignores and the next run overwrites.
See [the Atlas runner durability runbook](atlas-20k-runner-durability.md) for
the required snapshot → backup → gate → wipe order.

List snapshots and perform periodic integrity checks:

```bash
./scripts/backup-data.sh snapshots
./scripts/backup-data.sh verify
./scripts/backup-data.sh verify --read-data
```

`verify` checks the repository rather than one snapshot: restic does not
support a positional snapshot ID for `check`. `--read-data` downloads and
verifies repository data and may be slow.
Use it for a periodic restore drill, not necessarily after every backup.

## Restore drill

Choose a recovery filesystem with enough free space. The target must be
absolute and empty (or not yet exist), and must not be under the repository or
a cloud mount.

```bash
mkdir -p /absolute/path/to/recovery-parent
./scripts/backup-data.sh restore latest \
  --to /absolute/path/to/recovery-parent/restore-test
./scripts/backup-data.sh restore latest \
  --to /absolute/path/to/recovery-parent/restore-test \
  --execute
```

The restored tree contains the allowlisted paths that were present in that
snapshot, plus the JSON receipt. It does not contain every live `batch_state/`
or `data/` directory. `restore --execute` removes any `-wal`, `-shm`, or
`-journal` file paired with a receipt-listed database after every snapshot
is written, including when `--path` restores a directory and the file-phase
snapshot follows the database batch. It then checks `PRAGMA integrity_check`
by opening each restored database read-only, so the check sees a leftover
sidecar the same way a normal reader would, and fails if any check is not
`ok`. Inspect the receipt and expected data before any live import:

```bash
jq . /absolute/path/to/recovery-parent/restore-test/BACKUP-RECEIPT.json
sqlite3 /absolute/path/to/recovery-parent/restore-test/data/sources.db \
  'PRAGMA integrity_check;'
find /absolute/path/to/recovery-parent/restore-test/data -type f | wc -l
```

After a wipe and clean reclone, restore the dual-write state without deleting
anything already present:

```bash
RECOVERY_DIR=/absolute/path/to/recovery-parent/restore-test
PROJECT_DIR=/absolute/path/to/clean/learn-ukrainian
rsync -a "$RECOVERY_DIR/.claude/" "$PROJECT_DIR/.claude/"
rsync -a "$RECOVERY_DIR/batch_state/" "$PROJECT_DIR/batch_state/"
```

Before any selective `.agent/` import, stop every `.agent` writer. Never
overwrite the live `.agent/` root as a whole, and never use `rsync --delete`.
Review and import only the required recovery files after validating their
databases and schema compatibility. Do not blindly reactivate stale locks,
wake state, caches, deployed mirrors, hooks, or executables from a snapshot.

If `GIT-WORKTREE.patch` exists, inspect it and run a check before deciding to
apply it:

```bash
git -C "$PROJECT_DIR" apply --check "$RECOVERY_DIR/GIT-WORKTREE.patch"
```

Copy `data/` back only after validating the specific recovery target and
stopping its writers.

For an incident:

1. Stop processes that write the affected live database or directory.
2. Preserve the damaged live item as forensic evidence on a different disk
   when space permits.
3. Restore into the staging target and validate checksums, database integrity,
   and expected row/file counts.
4. Copy back only the confirmed files. The backup script intentionally does
   not perform this overwrite.
5. Keep the staged restore until services and application checks pass.

Never point `restore --to` at `data/`, the project root, `_quarantine`, the old
Drive backup, or another directory containing files.

## What is not backed up

Anything that is not a KEEP row above is not backed up, including every DROP
row. In particular the nightly does not walk the rest of `batch_state/` or
`data/`. `batch_state/tasks/*.lock` files and `batch_state/tasks/*.snapshots/`
directories are not backed up even though `batch_state/tasks` is kept.
`batch_state/backups/last-run.json` is a scheduling record, not a backup root.

- `.git/objects`: committed history belongs on the Git remote.
- `.venv/`, `node_modules/`, and generated `site/public/atlas/`: rebuild them
  from committed configuration and release artifacts.
- `_quarantine/`: incident evidence remains separately managed.
- `data/qdrant/`: retired and rebuildable under ADR-005/006.
- SQLite WAL/SHM/journal sidecars for selected databases: transient
  state incorporated into each staged online database backup.
- Ephemeral scoped homes in `batch_state/`, including review-receipt homes.
- SQLite databases under pytest base temp directories (`pytest-*`).
- Loose copies of databases covered by a verified archive manifest; the
  archive itself is backed up.
- `data/textbooks` and `data/vesum` when they are legacy Drive symlinks. Their
  targets remain in the legacy backup until a separate migration is planned.

Run `doctor` after changing any source symlink. A new external or broken
symlink is a hard failure rather than a silent omission or recursive copy.

## Scheduling

On the data host, the systemd **user** units in `packaging/systemd/`
(`learn-ukrainian-backup.service` + `.timer`, and
`learn-ukrainian-backup-retention.service` + `.timer`) run the backup daily at
03:30 UTC (`Persistent=true`, 15-minute randomized delay) and the
operator-approved retention policy weekly. Install them from the primary
checkout (preview by default; writes only with `--apply`):

```bash
.venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root "$PWD"
.venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root "$PWD" --apply --enable
```

The units configure `LU_BACKUP_ENV_FILE=%h/.secrets/learn-ukrainian-backup.env` (as defined in `packaging/systemd/learn-ukrainian-backup.service`), which the wrapper validates (regular file, mode 0600, safe permissions) and sources.
Validation errors name the variable and condition without its value. The
scheduled wrapper replaces either configured repository value, its remote
path, and the password-file path in backup and retention output
before sending it to the journal. `scripts/orchestration/run_scheduled_backup.sh`
writes `batch_state/backups/last-run.json` after an attempted backup (UTC
start/end, exit status, restic run id, snapshot count, bytes added). A failed
run exits non-zero, and so does a failed log capture or a failed
`last-run.json` write, so `systemctl --user list-timers` and
`journalctl --user -u learn-ukrainian-backup.service` show it; there is no
separate alerting system.
Before each scheduled run's preflight, the wrapper removes the previous receipt;
an early failure therefore leaves no receipt. If systemd times out or kills the
wrapper before this point, `last-run.json` may still show the previous run; use
its timestamp together with the unit status. The user manager has no reliable
network-ready target, so a boot catch-up may fail visibly before network access
is available. Existing snapshots remain available; the next scheduled backup
or retention run retries at its usual daily or weekly interval.

Elsewhere, the script remains suitable for launchd or cron after the one-time
environment is available to that process. `backup --execute` returns nonzero
for missing critical roots, unsafe symlinks, uncovered untracked files,
corrupt SQLite databases, failed uploads, or failed repository checks. Send
stdout and stderr to an operator-controlled log outside the repository and
alert on every nonzero exit.

Schedule retention only through the weekly `retention` command above; do not
add ad-hoc `restic forget` or prune invocations.
