#!/bin/bash
#
# Backup all of data/ to Google Drive.
#
#   Usage:    ./scripts/backup-data.sh
#   When:     manually, whenever you want a fresh snapshot.
#             Typical triggers: after rebuilding sources.db / vesum.db,
#             or after running scripts/wiki/cold_encode.py.
#   Where:    rsyncs to the Google Drive for Desktop mount, so files
#             sync to Drive in the background. No rclone, no OAuth,
#             no cron. Drive keeps its own per-file version history
#             for rollback.
#   Covers:   everything in data/ (sources.db, vesum.db, wiki_cache.db,
#             data/embeddings/ dense shards, any JSONL, agent bridge
#             DBs). Excludes only SQLite WAL/SHM files (transient) +
#             __pycache__ + .DS_Store.
#   Notes:    data/embeddings/ costs ~3h of MLX encoding to regenerate
#             (scripts/wiki/cold_encode.py --all-corpora), so it's
#             worth shipping.
#
# Single canonical backup script. If this file is missing, that is the
# backup path. There are no other backup scripts.

set -euo pipefail

GDRIVE="/Users/krisztiankoos/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
SRC="/Users/krisztiankoos/projects/learn-ukrainian/data"

echo "=== Backing up data to Google Drive ==="
echo "Source: $SRC"
echo "Target: $GDRIVE"
echo ""

if [[ ! -d "$(dirname "$GDRIVE")" ]]; then
  echo "ERROR: Google Drive for Desktop mount not found at:" >&2
  echo "  $(dirname "$GDRIVE")" >&2
  echo "Make sure Google Drive for Desktop is running and your account is signed in." >&2
  exit 1
fi

mkdir -p "$GDRIVE"

rsync -av \
  --exclude='*.db-shm' \
  --exclude='*.db-wal' \
  --exclude='__pycache__/' \
  --exclude='.DS_Store' \
  "$SRC/" "$GDRIVE/"

echo ""
echo "=== Backup complete ==="
du -sh "$GDRIVE"
echo ""
echo "Files backed up:"
find "$GDRIVE" -type f | wc -l | xargs echo "  Total files:"
find "$GDRIVE" -name '*.jsonl' | wc -l | xargs echo "  JSONL files:"
find "$GDRIVE" -name '*.db' | wc -l | xargs echo "  SQLite DBs:"
if [[ -d "$GDRIVE/embeddings" ]]; then
  find "$GDRIVE/embeddings" -type f -name 'shard-*.npy' | wc -l \
    | xargs echo "  Dense shards:"
  du -sh "$GDRIVE/embeddings" | awk '{print "  Embeddings size:", $1}'
fi
echo ""
echo "Drive will sync these to the cloud in the background."
echo "Confirm sync completion in the Google Drive menu bar icon before shutting down."
