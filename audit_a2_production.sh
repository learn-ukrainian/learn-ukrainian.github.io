#!/bin/bash

# Audit all A2 production modules and identify failures
echo "=== A2 Production Module Audit Report ==="
echo ""

FAIL_COUNT=0
PASS_COUNT=0
ERROR_COUNT=0

FAIL_MODULES=()
ERROR_MODULES=()

for i in {01..55}; do
    file="curriculum/l2-uk-en/a2/${i}-*.md"
    
    # Check if file exists (use first match)
    if ls $file 2>/dev/null | head -1 >/dev/null; then
        actual_file=$(ls $file 2>/dev/null | head -1)
        MODULE=$(basename "$actual_file" .md)
        
        echo "Auditing M${i}: $MODULE..."
        
        # Run audit and capture output
        AUDIT_OUTPUT=$(python3 scripts/audit_module.py "$actual_file" 2>&1)
        
        # Check for errors first
        if echo "$AUDIT_OUTPUT" | grep -q "Error:"; then
            ERROR_COUNT=$((ERROR_COUNT + 1))
            ERROR_MODULES+=("M${i}: $MODULE")
            echo "  ⚠️  ERROR"
            echo "$AUDIT_OUTPUT" | grep "Error:" | head -5
        # Check for failures
        elif echo "$AUDIT_OUTPUT" | grep -qE "(FAIL|CRITICAL|MAJOR)"; then
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAIL_MODULES+=("M${i}: $MODULE")
            echo "  ❌ FAILED"
            echo "$AUDIT_OUTPUT" | grep -E "(FAIL|CRITICAL|MAJOR)" | head -10
        else
            PASS_COUNT=$((PASS_COUNT + 1))
            echo "  ✅ PASSED"
        fi
        echo ""
    else
        echo "M${i}: NOT FOUND"
        echo ""
    fi
done

echo "========================================"
echo "=== SUMMARY ==="
echo "PASSED: $PASS_COUNT"
echo "FAILED: $FAIL_COUNT"
echo "ERRORS: $ERROR_COUNT"
echo ""

if [ ${#FAIL_MODULES[@]} -gt 0 ]; then
    echo "=== FAILING MODULES ==="
    for mod in "${FAIL_MODULES[@]}"; do
        echo "  - $mod"
    done
    echo ""
fi

if [ ${#ERROR_MODULES[@]} -gt 0 ]; then
    echo "=== ERROR MODULES (need investigation) ==="
    for mod in "${ERROR_MODULES[@]}"; do
        echo "  - $mod"
    done
fi
