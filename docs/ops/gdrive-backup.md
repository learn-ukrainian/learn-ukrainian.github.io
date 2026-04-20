# Google Drive DB Backup

This runbook sets up daily Google Drive backups for the expensive local
retrieval state:

- `data/sources.db` — corpus FTS5 index (~1.4G)
- `data/vesum.db` — morphology dictionary (~0.9G)
- `data/embeddings/` — MLX-encoded dense retrieval shards + manifest.db (~0.4G)
  - Regenerating these costs ~3h of MLX encoding
    (`scripts/wiki/cold_encode.py --all-corpora`), so they're worth
    shipping to Drive. `rclone copy --checksum` is incremental:
    only new/changed shards transfer on repeat runs.

The backup job uploads those to
`learn-ukrainian-backups/YYYY-MM-DD/` on Google Drive. DBs at the root,
embeddings under `embeddings/` to mirror the local layout.

## Prerequisites

Install `rclone` on macOS:

```bash
brew install rclone
rclone version
```

## First-Time `rclone` Setup

This repo cannot complete the Google OAuth flow non-interactively. Run this
once yourself before enabling cron:

```bash
rclone config
```

Recommended choices:

1. Choose `n` for a new remote.
2. Name it `gdrive`.
3. Choose `drive` as the storage type.
4. Follow the normal Google OAuth prompts in the browser.
5. Verify the remote works:

```bash
rclone lsd gdrive:
```

If you already use a different Google Drive remote name, the scripts will try
to auto-detect remotes named like `learn-ukrainian`, `gdrive`, or
`google-drive`. If your remote uses another name, export it explicitly:

```bash
export RCLONE_REMOTE=your-remote-name
```

You can also set `RCLONE_BACKUP_ROOT` if you want a different Google Drive
folder than the default `learn-ukrainian-backups`.

## Backup Script

Run the daily backup manually:

```bash
bash scripts/ops/backup_dbs.sh
```

Behavior:

- Copies `data/sources.db`, `data/vesum.db`, and the `data/embeddings/` tree
- Uses `rclone copy --checksum` — incremental, so repeat runs only transfer
  new/changed shards (typical daily delta: 0 bytes unless cold_encode re-ran)
- Writes logs to `logs/gdrive-backup.log`
- Exits nonzero on failure so cron can surface problems

If `data/sources.db-wal`, `data/vesum.db-wal`, or
`data/embeddings/manifest.db-wal` exists, the script logs a warning and
still uploads only the checkpointed `.db` file. If you need the latest
uncheckpointed SQLite changes captured, checkpoint that database before
running the backup.

If `data/embeddings/` is missing or empty (e.g. on a fresh clone that hasn't
run `cold_encode.py` yet), the script logs a warning, skips the embeddings
copy, and still ships the DBs. This is non-fatal.

## Prune Script

Run the retention cleanup manually:

```bash
bash scripts/ops/prune_gdrive_backups.sh
```

Retention policy:

- Keep the last 7 daily backups
- Keep the last 4 weekly backups taken on Sunday

## Cron Install

Install the jobs with `crontab -e`, then paste:

```cron
# Daily backup at 03:00 local
0 3 * * * /Users/krisztiankoos/projects/learn-ukrainian/scripts/ops/backup_dbs.sh

# Weekly prune at 04:00 local on Sunday
0 4 * * 0 /Users/krisztiankoos/projects/learn-ukrainian/scripts/ops/prune_gdrive_backups.sh
```

Save and exit the editor. Cron will use your local timezone.

## Verification

After the first successful manual run, confirm the dated folder is visible on
Google Drive:

```bash
rclone lsf gdrive:learn-ukrainian-backups/$(date +%Y-%m-%d)
```

If you use a remote name other than `gdrive`, replace it in the command above
or set `RCLONE_REMOTE` first.
