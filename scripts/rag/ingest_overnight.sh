#!/bin/bash
# Robust overnight image ingestion — processes one JSONL at a time.
# If one file fails, logs the error and moves to the next.
#
# Usage:
#   ./scripts/rag/ingest_overnight.sh                    # all grades
#   ./scripts/rag/ingest_overnight.sh --grade 6 7 8 9 10 11  # specific grades
#
# Features:
#   - Processes files sequentially (one Python process at a time)
#   - Skips files with 0 images
#   - Logs progress to /tmp/rag-overnight.log
#   - If a file fails, continues with the next one
#   - Small batch size (4) to minimize memory usage
#   - Forces CPU + fp16 (no MPS) for stability

set -euo pipefail
cd "$(dirname "$0")/../.."

LOG="/tmp/rag-overnight.log"
BATCH_SIZE=4

echo "[$(date)] Starting overnight ingestion" | tee "$LOG"
echo "[$(date)] Batch size: $BATCH_SIZE" | tee -a "$LOG"

GRADE_FILTER=""
if [[ "${1:-}" == "--grade" ]]; then
    shift
    GRADE_FILTER="$*"
    echo "[$(date)] Grade filter: $GRADE_FILTER" | tee -a "$LOG"
fi

# Find all image JSONL files
JSONL_FILES=()
for grade_dir in data/textbook_images/grade-*/; do
    grade_num=$(basename "$grade_dir" | sed 's/grade-0*//')

    # Apply grade filter if specified
    if [[ -n "$GRADE_FILTER" ]]; then
        skip=true
        for g in $GRADE_FILTER; do
            if [[ "$grade_num" == "$g" ]]; then
                skip=false
                break
            fi
        done
        if $skip; then
            continue
        fi
    fi

    for f in "$grade_dir"*-images.jsonl; do
        [[ -f "$f" ]] || continue
        # Skip empty files
        if [[ ! -s "$f" ]]; then
            echo "[$(date)] SKIP (empty): $f" | tee -a "$LOG"
            continue
        fi
        JSONL_FILES+=("$f")
    done
done

TOTAL=${#JSONL_FILES[@]}
echo "[$(date)] Found $TOTAL JSONL files to process" | tee -a "$LOG"

SUCCESS=0
FAILED=0
SKIPPED=0

for i in "${!JSONL_FILES[@]}"; do
    f="${JSONL_FILES[$i]}"
    n=$((i + 1))
    echo "" | tee -a "$LOG"
    echo "[$(date)] [$n/$TOTAL] Processing: $(basename "$f")" | tee -a "$LOG"

    # Run ingestion for this single file
    # Use timeout of 30 minutes per file as safety net
    if timeout 1800 .venv/bin/python scripts/rag/ingest.py \
        --images "$f" \
        --batch-size "$BATCH_SIZE" \
        >> "$LOG" 2>&1; then
        echo "[$(date)] [$n/$TOTAL] OK: $(basename "$f")" | tee -a "$LOG"
        SUCCESS=$((SUCCESS + 1))
    else
        EXIT_CODE=$?
        if [[ $EXIT_CODE -eq 124 ]]; then
            echo "[$(date)] [$n/$TOTAL] TIMEOUT (30min): $(basename "$f")" | tee -a "$LOG"
        else
            echo "[$(date)] [$n/$TOTAL] FAILED (exit $EXIT_CODE): $(basename "$f")" | tee -a "$LOG"
        fi
        FAILED=$((FAILED + 1))
    fi

    # Brief pause between files for GC
    sleep 2
done

echo "" | tee -a "$LOG"
echo "[$(date)] =============================" | tee -a "$LOG"
echo "[$(date)] DONE: $SUCCESS ok, $FAILED failed, $SKIPPED skipped out of $TOTAL" | tee -a "$LOG"
echo "[$(date)] Final collection stats:" | tee -a "$LOG"
.venv/bin/python -c "
from qdrant_client import QdrantClient
c = QdrantClient(host='localhost', port=6333, timeout=10)
info = c.get_collection('textbook_images')
print(f'  textbook_images: {info.points_count} points')
" >> "$LOG" 2>&1
cat "$LOG" | tail -5
