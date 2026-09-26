# Data Backup and Recovery

`scripts/backup-data.sh` creates encrypted, versioned restic snapshots of the
project's recovery-critical local state through an rclone remote. It does not
write through the Google Drive Desktop mount, overwrite the previous backup,
or restore directly over live project data. Snapshot pruning exists only as
the operator-approved weekly `retention` command described below.

Every completed backup run contains these roots, in priority order:

- every `.claude/*-epic/` directory, including driver plans and handoffs;
- `.agent/`, including local agent recovery state and session-stream databases;
- `batch_state/`;
- `data/`, including SQLite databases, embeddings, and private inputs;
- `GIT-WORKTREE.patch` when tracked changes have not been committed; and
- `BACKUP-RECEIPT.json`.

The script fails closed when `.claude/atlas-epic`, `.agent`, `batch_state`, `data`, or
the destination configuration is missing. It also fails when a non-ignored
untracked Git path is outside the declared recovery roots. This prevents a
partial backup from appearing successful.

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
  roots. SQLite databases are backed up one at a time with SQLite's online
  `.backup` command, checked with `PRAGMA integrity_check`, uploaded, and
  removed from private staging before the next database. Before each database,
  the script checks staging free space against its DB plus WAL size and a 2 GiB
  reserve. No reflink or full-tree copy is required, so peak extra disk is
  about the largest single database, never the sum. Non-database files can
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
- Scoped `*-home/` directories in `batch_state/` and `home/` directories in
  `batch_state/review-receipts/` are excluded. Review homes are ephemeral and
  may contain credential links. Absolute symlinks elsewhere still stop backup.
- The legacy `data/textbooks` and `data/vesum` symlinks are excluded only when
  they resolve inside the old Drive backup. Other absolute or escaping
  symlinks stop the backup.
- `.agent/` must be a real directory. Broken, absolute, or escaping symlinks
  below it, and unsupported special files, stop the backup before restic runs.
- Restore accepts only an absolute empty or nonexistent directory outside the
  project, cloud mounts, and the legacy backup.
- The only snapshot deletion is `retention [--execute]`, which runs
  `restic forget --prune --keep-daily 7 --keep-weekly 4 --keep-monthly 6`
  scoped to this backup family's tag (`--tag "$BACKUP_TAG"`). Other snapshot
  families in the same repository are never selected. It is a preview unless
  `--execute` is supplied and is scheduled weekly, not on every backup.
- Restic commits snapshots atomically. A failed upload does not replace an
  earlier recovery point. On Linux, a final receipt snapshot marks the run
  complete; `restore latest` selects only completed runs.

Restic documents the [rclone backend][restic-rclone], [backup dry runs][restic-backup],
[restore dry runs][restic-restore], and [repository integrity checks][restic-check].
SQLite documents why its [online backup API produces a consistent snapshot][sqlite-backup].

[restic-rclone]: https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#rclone
[restic-backup]: https://restic.readthedocs.io/en/stable/040_backup.html#dry-runs
[restic-restore]: https://restic.readthedocs.io/en/stable/050_restore.html#dry-runs
[restic-check]: https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-integrity-and-consistency
[sqlite-backup]: https://www.sqlite.org/backup.html

## Open dependency: Google Drive OAuth client ID (2026)

**Tracked:** [#6093](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6093) — *do not close until proven fixed.*

The scheduled job (`com.learn-ukrainian.backup` → `~/.local/bin/learn-ukrainian-backup`) still
succeeds, but rclone logs a **NOTICE** that the **shared** Google Drive `client_id` is being
**retired during 2026**. When Google cuts it off, **new restic snapshots stop** until the
`lu-gdrive` remote uses an **operator-owned** OAuth client and is re-authorized.

- Config lives outside git (`~/.secrets/learn-ukrainian-backup.env`, dedicated rclone config).
- Do **not** put client secrets, tokens, or password files in the repo, issues, or receipts.
- Procedure: [rclone — making your own client_id](https://rclone.org/drive/#making-your-own-client-id),
  then re-auth the remote and prove `backup-data.sh doctor`, one `backup --execute`,
  `snapshots`, `verify`, and a green scheduled run (acceptance on #6093).

Until #6093 is closed, treat this as a **time-bounded production risk**, not noise.

---

## One-time setup

Install current restic and rclone releases:

```bash
brew install restic rclone
restic version
rclone version
```

Configure a dedicated rclone remote. The examples use `lu-gdrive`; another
name is fine as long as the environment below matches it.

```bash
rclone config
rclone lsd lu-gdrive:
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
export LU_BACKUP_REPOSITORY='rclone:lu-gdrive:Projects/learn-ukrainian-restic'
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
prune old versions. Normal exits and handled interruptions clean the private
staging directory and local operation lock. After a power loss, inspect any
stale path reported by the next run before removing it.

Each successful run contains `BACKUP-RECEIPT.json` with:

- UTC creation time, stable host label, Git SHA, and receipt preparation status;
- the selected root labels with file and byte counts;
- whether a tracked-worktree patch was needed;
- the count of untracked non-ignored files not included (normally zero);
- exclusions, known missing paths, and the restore command.

On macOS, path counts are calculated from the staged tree after exclusions.
On Linux, they are calculated from the live source inventory after exclusions;
concurrent non-database writes can change the actual uploaded byte counts.

The Linux receipt also lists each database's relative path and snapshot ID,
the live-file snapshot ID, and an optional patch snapshot ID. All parts share
one run ID, and the final receipt snapshot is tagged `lu-part-complete`.
`restore latest` uses that completed receipt to reassemble the tree. The
remote repository itself is encrypted. The final process
exit code belongs to the operator log: an in-snapshot file cannot truthfully
contain the outcome of the repository check that runs after the snapshot is
committed.

When `data/lexicon/runner-mirror/` exists, a successful `backup --execute`
also writes its local `RESTIC-GATE-RECEIPT.json` **after** the repository
check. This is distinct from the in-snapshot `BACKUP-RECEIPT.json`: it binds
each current runner-mirror `manifest.json` checksum to the completed restic
snapshot so the pre-wipe gate works without credentials or network access. On
Linux, the script compares the runner-mirror file list and SHA-256 hashes in
the live-file snapshot with the live mirror before writing that local gate
receipt.
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

The restored tree contains `.claude/`, `.agent/`, `batch_state/`, `data/`, and the JSON
receipt. `restore --execute` checks `PRAGMA integrity_check` on every restored
database and fails if any check is not `ok`. Inspect the receipt and expected
data before any live import:

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

- `.git/objects`: committed history belongs on the Git remote.
- `.venv/`, `node_modules/`, and generated `site/public/atlas/`: rebuild them
  from committed configuration and release artifacts.
- `_quarantine/`: incident evidence remains separately managed.
- `data/qdrant/`: retired and rebuildable under ADR-005/006.
- SQLite WAL/SHM/journal sidecars for selected databases: transient
  state incorporated into each staged online database backup.
- Ephemeral scoped homes in `batch_state/`, including review-receipt homes.
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

The units read `~/.secrets/learn-ukrainian-backup.env` via `EnvironmentFile=`
and never log secret values. `scripts/orchestration/run_scheduled_backup.sh`
writes `batch_state/backups/last-run.json` on success and on failure (UTC
start/end, exit status, restic run id, snapshot count, bytes added). A failed
run exits non-zero, so `systemctl --user list-timers` and
`journalctl --user -u learn-ukrainian-backup.service` show it; there is no
separate alerting system.

Elsewhere, the script remains suitable for launchd or cron after the one-time
environment is available to that process. `backup --execute` returns nonzero
for missing critical roots, unsafe symlinks, uncovered untracked files,
corrupt SQLite databases, failed uploads, or failed repository checks. Send
stdout and stderr to an operator-controlled log outside the repository and
alert on every nonzero exit.

Schedule retention only through the weekly `retention` command above; do not
add ad-hoc `restic forget` or prune invocations.
