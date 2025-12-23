#!/bin/bash

# Get detailed audit reports for failing A2 modules
FAILING_MODULES=(31 32 33 36 37 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55)

echo "=== DETAILED AUDIT REPORTS FOR FAILING A2 MODULES ===" > a2_failing_details.txt
echo "" >> a2_failing_details.txt

for i in "${FAILING_MODULES[@]}"; do
    file="curriculum/l2-uk-en/a2/${i}-*.md"
    
    if ls $file 2>/dev/null | head -1 >/dev/null; then
        actual_file=$(ls $file 2>/dev/null | head -1)
        MODULE=$(basename "$actual_file" .md)
        
        echo "========================================" >> a2_failing_details.txt
        echo "MODULE M${i}: $MODULE" >> a2_failing_details.txt
        echo "========================================" >> a2_failing_details.txt
        
        python3 scripts/audit_module.py "$actual_file" 2>&1 >> a2_failing_details.txt
        
        echo "" >> a2_failing_details.txt
        echo "" >> a2_failing_details.txt
    fi
done

echo "Detailed audit reports saved to a2_failing_details.txt"
