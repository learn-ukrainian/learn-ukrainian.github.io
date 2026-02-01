#!/usr/bin/env bash
#
# audit_module.sh - Audit module and save log
#
# Usage:
#   scripts/audit_module.sh curriculum/l2-uk-en/{level}/{num}-{slug}.md
#
# What it does:
#   1. Runs audit_module.py on the specified file
#   2. Saves audit log to curriculum/l2-uk-en/{level}/audit/{slug}-audit.log
#   3. Returns audit exit code (0 = pass, 1 = fail)
#
# Examples:
#   scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md
#   scripts/audit_module.sh curriculum/l2-uk-en/b2-hist/15-holodomor-timeline.md

set -euo pipefail

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 <module-path>"
    echo "Example: $0 curriculum/l2-uk-en/b1/09-aspect-future.md"
    exit 1
fi

MODULE_PATH="$1"

# Validate file exists
if [ ! -f "$MODULE_PATH" ]; then
    echo "Error: File not found: $MODULE_PATH"
    exit 1
fi

# Extract level and slug from path
# Path format: curriculum/l2-uk-en/{level}/{num}-{slug}.md
LEVEL=$(echo "$MODULE_PATH" | cut -d'/' -f3)
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
echo "Saving log to: $LOG_PATH"
echo ""

# Run audit_module.py with tee to save output
# Capture exit code separately
set +e
.venv/bin/python scripts/audit_module.py "$MODULE_PATH" 2>&1 | tee "$LOG_PATH"
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

# Exit with audit exit code
exit $AUDIT_EXIT_CODE
