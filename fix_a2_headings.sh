#!/bin/bash

# Fix heading levels for all failing A2 modules
# Changes ## Summary, ## Activities, ## Vocabulary to # (H1)

FAILING_MODULES=(31 32 33 36 37 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57)

echo "Fixing heading levels for 21 failing A2 modules..."

for i in "${FAILING_MODULES[@]}"; do
    file=$(ls curriculum/l2-uk-en/a2/${i}-*.md 2>/dev/null | head -1)
    
    if [ -f "$file" ]; then
        MODULE=$(basename "$file" .md)
        echo "Fixing M${i}: $MODULE"
        
        # Fix heading levels using proper macOS sed syntax
        sed -i.bak 's/^## Summary$/# Summary/' "$file"
        sed -i.bak 's/^## Activities$/# Activities/' "$file"
        sed -i.bak 's/^## Vocabulary$/# Vocabulary/' "$file"
        
        # Remove backup files
        rm -f "${file}.bak"
        
        echo "  ✓ Fixed heading levels"
    fi
done

echo ""
echo "✅ Heading level fixes complete!"
