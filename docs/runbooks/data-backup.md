# Data Backup and Recovery

`scripts/backup-data.sh` creates encrypted, versioned restic snapshots of the
project's recovery-critical local state through an rclone remote. It does not
write through the Google Drive Desktop mount, overwrite the previous backup,
prune snapshots, or restore directly over live project data.

Every snapshot contains these roots, in priority order:

- every `.claude/*-epic/` directory, including driver plans and handoffs;
- `batch_state/`;
- `data/`, including SQLite databases, embeddings, and private inputs;
- `GIT-WORKTREE.patch` when tracked changes have not been committed; and
- `BACKUP-RECEIPT.json`.

The script fails closed when `.claude/atlas-epic`, `batch_state`, `data`, or
the destination configuration is missing. It also fails when a non-ignored
untracked Git path is outside the declared recovery roots. This prevents a
partial backup from appearing successful.

The old `learn-ukrainian-data` Drive folder is a read-only legacy recovery
source. Do not use it as the new restic repository path; the script rejects a
restic rclone path with that final directory name.

## Safety model

- `init`, `backup`, and `restore` are previews unless `--execute` is explicit.
- A backup executes from a private copy-on-write staging tree outside the
  checkout.
- Staging capacity is checked against every selected recovery tree, SQLite
  snapshot overhead, and a 2 GiB reserve before an execute path starts.
- On macOS, source and staging must be on the same volume before APFS
  copy-on-write staging; a cross-volume staging location fails closed.
- On Linux filesystems without reflink support, only a bounded source tree of
  at most 64 MiB may fall back to a normal copy; larger trees fail closed.
- Every `*.db`, `*.sqlite`, and `*.sqlite3` under the selected roots is rebuilt
  in staging with SQLite's online backup command and must pass
  `PRAGMA quick_check` before upload.
- SQLite WAL/SHM files, `__pycache__`, `.DS_Store`, and retired `qdrant/` data
  are excluded.
- The legacy `data/textbooks` and `data/vesum` symlinks are excluded only when
  they resolve inside the old Drive backup. Other absolute or escaping
  symlinks stop the backup.
- Restore accepts only an absolute empty or nonexistent directory outside the
  project, cloud mounts, and the legacy backup.
- There is intentionally no `forget`, `prune`, or snapshot-delete command.
- Restic commits snapshots atomically. A failed upload does not replace an
  earlier recovery point.

Restic documents the [rclone backend][restic-rclone], [backup dry runs][restic-backup],
[restore dry runs][restic-restore], and [repository integrity checks][restic-check].
SQLite documents why its [online backup API produces a consistent snapshot][sqlite-backup].

[restic-rclone]: https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#rclone
[restic-backup]: https://restic.readthedocs.io/en/stable/040_backup.html#dry-runs
[restic-restore]: https://restic.readthedocs.io/en/stable/050_restore.html#dry-runs
[restic-check]: https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-integrity-and-consistency
[sqlite-backup]: https://www.sqlite.org/backup.html

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
known missing paths, and the restic change list. Then create the snapshot:

```bash
./scripts/backup-data.sh backup --execute
```

The execute path checks repository metadata after the snapshot. It does not
prune old versions. Normal exits and handled interruptions clean the private
staging directory and local operation lock. After a power loss, inspect any
stale path reported by the next run before removing it.

Each successful snapshot contains `BACKUP-RECEIPT.json` with:

- UTC creation time, stable host label, Git SHA, and receipt preparation status;
- the selected root labels with file and byte counts;
- whether a tracked-worktree patch was needed;
- the count of untracked non-ignored files not included (normally zero);
- exclusions, known missing paths, and the restore command.

Path counts are calculated after exclusions are removed from the private
staging tree, so they describe recoverable snapshot files rather than raw
source-tree contents.

The receipt intentionally records only top-level recovery labels, not private
inner path names. The remote repository itself is encrypted. The final process
exit code belongs to the operator log: an in-snapshot file cannot truthfully
contain the outcome of the repository check that runs after the snapshot is
committed.

When `data/lexicon/runner-mirror/` exists, a successful `backup --execute`
also writes its local `RESTIC-GATE-RECEIPT.json` **after** the repository
check. This is distinct from the in-snapshot `BACKUP-RECEIPT.json`: it binds
each current runner-mirror `manifest.json` checksum to the completed restic
snapshot so the pre-wipe gate works without credentials or network access.
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

The restored tree contains `.claude/`, `batch_state/`, `data/`, and the JSON
receipt. Validate the receipt and databases before any live import:

```bash
jq . /absolute/path/to/recovery-parent/restore-test/BACKUP-RECEIPT.json
sqlite3 /absolute/path/to/recovery-parent/restore-test/data/sources.db \
  'PRAGMA quick_check;'
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

If `GIT-WORKTREE.patch` exists, inspect it and run a check before deciding to
apply it:

```bash
git -C "$PROJECT_DIR" apply --check "$RECOVERY_DIR/GIT-WORKTREE.patch"
```

Do not use `rsync --delete`. Copy `data/` back only after validating the
specific recovery target and stopping its writers.

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
- SQLite `*.db-wal` and `*.db-shm`: transient state incorporated into each
  staged online database backup.
- `data/textbooks` and `data/vesum` when they are legacy Drive symlinks. Their
  targets remain in the legacy backup until a separate migration is planned.

Run `doctor` after changing any source symlink. A new external or broken
symlink is a hard failure rather than a silent omission or recursive copy.

## Scheduling

The script is suitable for launchd or cron after the one-time environment is
available to that process. `backup --execute` returns nonzero for missing
critical roots, unsafe symlinks, uncovered untracked files, corrupt SQLite
databases, failed uploads, or failed repository checks. Send stdout and stderr
to an operator-controlled log outside the repository and alert on every
nonzero exit.

Do not schedule retention or pruning until an operator approves a policy and
multiple restore drills have succeeded.
