#!/bin/bash

# Audit all A2 modules and identify failures
echo "=== A2 Module Audit Report ==="
echo ""

FAIL_COUNT=0
PASS_COUNT=0
UNAUDITED_COUNT=0

FAIL_MODULES=()
UNAUDITED_MODULES=()

for file in curriculum/l2-uk-en/a2/gemini/[0-9]*.md; do
    if [ -f "$file" ]; then
        MODULE=$(basename "$file" | sed 's/-review\.md$//' | sed 's/\.md$//')
        MODULE_NUM=$(echo "$MODULE" | grep -oE '^[0-9]+')
        
        echo "Auditing $MODULE..."
        
        # Run audit and capture output
        AUDIT_OUTPUT=$(python3 scripts/audit_module.py "$file" 2>&1)
        AUDIT_EXIT=$?
        
        # Check for FAIL or PASS
        if echo "$AUDIT_OUTPUT" | grep -q "AUDIT FAILED"; then
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAIL_MODULES+=("$MODULE")
            echo "  ❌ FAILED"
            echo "$AUDIT_OUTPUT" | grep -E "(FAIL|ERROR|WARN)" | head -10
        elif echo "$AUDIT_OUTPUT" | grep -q "AUDIT PASSED"; then
            PASS_COUNT=$((PASS_COUNT + 1))
            echo "  ✅ PASSED"
        else
            UNAUDITED_COUNT=$((UNAUDITED_COUNT + 1))
            UNAUDITED_MODULES+=("$MODULE")
            echo "  ⚠️  UNAUDITED (no clear result)"
        fi
        echo ""
    fi
done

echo "=== SUMMARY ==="
echo "PASSED: $PASS_COUNT"
echo "FAILED: $FAIL_COUNT"
echo "UNAUDITED: $UNAUDITED_COUNT"
echo ""

if [ ${#FAIL_MODULES[@]} -gt 0 ]; then
    echo "=== FAILING MODULES ==="
    for mod in "${FAIL_MODULES[@]}"; do
        echo "  - $mod"
    done
    echo ""
fi

if [ ${#UNAUDITED_MODULES[@]} -gt 0 ]; then
    echo "=== UNAUDITED MODULES ==="
    for mod in "${UNAUDITED_MODULES[@]}"; do
        echo "  - $mod"
    done
fi
