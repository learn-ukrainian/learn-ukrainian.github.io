#!/bin/bash
# Backup all JSONL data files and dictionaries to Google Drive
# Run: ./scripts/backup-data.sh

set -euo pipefail

GDRIVE="/Users/krisztiankoos/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
SRC="/Users/krisztiankoos/projects/learn-ukrainian/data"

echo "=== Backing up data to Google Drive ==="
echo "Source: $SRC"
echo "Target: $GDRIVE"

mkdir -p "$GDRIVE"

# Literary texts (202 JSONL files — primary sources)
echo ""
echo "📚 Literary texts..."
mkdir -p "$GDRIVE/literary_texts"
rsync -av --include='*.jsonl' --exclude='*' "$SRC/literary_texts/" "$GDRIVE/literary_texts/"

# Dictionaries
for dict in antonenko-davydovych grinchenko sum11 balla-en-uk frazeolohichnyi wiktionary; do
    if [ -d "$SRC/$dict" ]; then
        echo ""
        echo "📖 $dict..."
        mkdir -p "$GDRIVE/$dict"
        rsync -av --include='*.jsonl' --include='*.json' --include='*.zip' --exclude='Formats' --exclude='json_raw' "$SRC/$dict/" "$GDRIVE/$dict/"
    fi
done

# VESUM database
echo ""
echo "📖 VESUM..."
cp -v "$SRC/vesum.db" "$GDRIVE/vesum.db"

# Textbook chunks
echo ""
echo "📚 Textbook chunks..."
mkdir -p "$GDRIVE/textbook_chunks"
rsync -av --include='*.jsonl' --exclude='*' "$SRC/textbook_chunks/" "$GDRIVE/textbook_chunks/" 2>/dev/null || echo "  (no files)"

# Show totals
echo ""
echo "=== Backup complete ==="
du -sh "$GDRIVE"
echo ""
echo "Files backed up:"
find "$GDRIVE" -name '*.jsonl' | wc -l | xargs echo "  JSONL files:"
find "$GDRIVE" -name '*.db' | wc -l | xargs echo "  SQLite DBs:"
