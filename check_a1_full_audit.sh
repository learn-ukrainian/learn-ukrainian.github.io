#!/bin/bash
echo "A1 Comprehensive Audit"
echo "======================"
slugs=$(yq ".levels.a1.modules[]" curriculum/l2-uk-en/curriculum.yaml | sed 's/ #.*//')
count=1
for slug in $slugs; do
  result=$(.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/$slug.md 2>&1)
  if echo "$result" | grep -q "AUDIT PASSED"; then
    echo "Module $count: ✅ $slug (Audit PASS)"
  else
    echo "Module $count: ❌ $slug (Audit FAIL)"
    echo "$result" | grep -E "Critical Failures|TEMPLATE COMPLIANCE|DUPLICATE_SYNONYMOUS_HEADERS"
  fi
  ((count++))
done
