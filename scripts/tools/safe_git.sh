#!/usr/bin/env bash
# safe_git.sh — retries git commands that fail on index.lock
# Root cause: parallel Codex sessions share the same repo checkout and
# create brief index.lock holds during git operations. This wrapper
# retries up to 5 times with a short sleep between attempts.
set -euo pipefail
MAX_RETRIES=5
RETRY_DELAY=1

for attempt in $(seq 1 $MAX_RETRIES); do
    # Clear stale lock if it's older than 10 seconds (definitely stale)
    lock_file="$(git rev-parse --git-dir 2>/dev/null)/index.lock"
    if [ -f "$lock_file" ]; then
        lock_age=$(( $(date +%s) - $(stat -f %m "$lock_file" 2>/dev/null || echo 0) ))
        if [ "$lock_age" -gt 10 ]; then
            rm -f "$lock_file"
        fi
    fi
    
    if git "$@" 2>/dev/null; then
        exit 0
    fi
    
    # Check if it was a lock error
    if git "$@" 2>&1 | grep -q "index.lock"; then
        if [ "$attempt" -lt "$MAX_RETRIES" ]; then
            sleep "$RETRY_DELAY"
            rm -f "$lock_file"
            continue
        fi
    fi
    
    # Non-lock error or final attempt — run normally to show the real error
    git "$@"
done
