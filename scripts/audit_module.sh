#!/usr/bin/env bash
#
# audit_module.sh - Audit module and save log
#
# Usage:
#   scripts/audit_module.sh curriculum/l2-uk-en/{level}/{num}-{slug}.md [--skip-activities]
#
# What it does:
#   1. Runs audit_module.py on the specified file
#   2. Saves audit log to curriculum/l2-uk-en/{level}/audit/{slug}-audit.log
#   3. Returns audit exit code (0 = pass, 1 = fail)
#
# Options:
#   --skip-activities   Content-only audit: defer activity/vocab gates (internal: prose-only loop)
#   --skip-review       Validate content+activities, defer review gate only (#606)
#   --no-rag-verify     Skip RAG word verification (runs by default)
#
# Examples:
#   scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md
#   scripts/audit_module.sh curriculum/l2-uk-en/hist/15-holodomor-timeline.md
#   scripts/audit_module.sh --skip-activities curriculum/l2-uk-en/a1/this-is-i-am.md

set -euo pipefail

# Parse arguments
SKIP_ACTIVITIES=""
SKIP_REVIEW=""
RAG_VERIFY="1"
MODULE_PATH=""

for arg in "$@"; do
    case "$arg" in
        --skip-activities)
            SKIP_ACTIVITIES="--skip-activities"
            ;;
        --skip-review)
            SKIP_REVIEW="--skip-review"
            ;;
        --no-rag-verify)
            RAG_VERIFY=""
            ;;
        *)
            MODULE_PATH="$arg"
            ;;
    esac
done

# Check arguments
if [ -z "$MODULE_PATH" ]; then
    echo "Usage: $0 [--skip-activities] [--skip-review] [--no-rag-verify] <module-path>"
    echo "Example: $0 curriculum/l2-uk-en/b1/09-aspect-future.md"
    exit 1
fi

# Validate file exists
if [ ! -f "$MODULE_PATH" ]; then
    echo "Error: File not found: $MODULE_PATH"
    exit 1
fi

# Extract level and slug from path
# Path format: curriculum/l2-uk-en/{level}/{num}-{slug}.md (relative or absolute)
# Strip everything up to and including "curriculum/l2-uk-en/" to normalize
REL_PATH=$(echo "$MODULE_PATH" | sed 's|.*/curriculum/l2-uk-en/|curriculum/l2-uk-en/|; s|^curriculum/l2-uk-en/||')
LEVEL=$(echo "$REL_PATH" | cut -d'/' -f1)
FILENAME=$(basename "$MODULE_PATH" .md)

# Extract slug (everything after first dash)
# e.g., "09-aspect-future" → "aspect-future"
SLUG=$(echo "$FILENAME" | sed 's/^[0-9]*-//')

# Create audit directory if it doesn't exist
AUDIT_DIR="curriculum/l2-uk-en/$LEVEL/audit"
mkdir -p "$AUDIT_DIR"

# Audit log path
LOG_PATH="$AUDIT_DIR/${SLUG}-audit.log"

# Run audit and save to log file
# Use tee to both display and save output
echo "Auditing: $MODULE_PATH"
if [ -n "$SKIP_ACTIVITIES" ]; then
    echo "Mode: content-only (activities deferred)"
fi
echo "Saving log to: $LOG_PATH"
echo ""

# Run audit_module.py with tee to save output
# Capture exit code separately
set +e
.venv/bin/python scripts/audit_module.py $SKIP_ACTIVITIES $SKIP_REVIEW "$MODULE_PATH" 2>&1 | tee "$LOG_PATH"
AUDIT_EXIT_CODE=${PIPESTATUS[0]}
set -e

# Add metadata to log file
echo "" >> "$LOG_PATH"
echo "---" >> "$LOG_PATH"
echo "Audit Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")" >> "$LOG_PATH"
echo "Module Path: $MODULE_PATH" >> "$LOG_PATH"
echo "Exit Code: $AUDIT_EXIT_CODE" >> "$LOG_PATH"

# Print result
echo ""
if [ $AUDIT_EXIT_CODE -eq 0 ]; then
    echo "✅ AUDIT PASSED"
else
    echo "❌ AUDIT FAILED (see $LOG_PATH for details)"
fi

# RAG word verification (non-blocking — Qdrant may be offline)
if [ -n "$RAG_VERIFY" ]; then
    echo ""
    echo "Running RAG word verification..."
    RAG_EXTRA_FLAGS=""
    if [ -n "$SKIP_ACTIVITIES" ]; then
        RAG_EXTRA_FLAGS="--skip-activities"
    fi
    set +e
    .venv/bin/python scripts/rag_batch_verify.py $RAG_EXTRA_FLAGS "$MODULE_PATH" 2>&1
    RAG_EXIT=$?
    set -e
    if [ $RAG_EXIT -ne 0 ]; then
        echo "⚠️  RAG verification found unverified words (see audit report)"
    else
        echo "✅ RAG verification: all words verified"
    fi
fi

# Exit with audit exit code (RAG verify is informational, not blocking)
exit $AUDIT_EXIT_CODE
