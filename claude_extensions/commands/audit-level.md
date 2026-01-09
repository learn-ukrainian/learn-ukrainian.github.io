#!/bin/bash
# /audit-level [level] - Deep audit of specific curriculum level

if [ -z "$1" ]; then
  echo "Usage: /audit-level [level]"
  echo ""
  echo "Available levels: a1, a2, b1, b2, c1, c2"
  echo ""
  echo "Example:"
  echo "  /audit-level b2"
  exit 1
fi

LEVEL="$1"
LEVEL_UPPER=$(echo "$LEVEL" | tr '[:lower:]' '[:upper:]')

echo "════════════════════════════════════════════════════════════════"
echo "  ${LEVEL_UPPER} Curriculum Deep Audit"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if level directory exists
if [ ! -d "curriculum/l2-uk-en/${LEVEL}" ]; then
  echo "❌ Level directory not found: curriculum/l2-uk-en/${LEVEL}"
  exit 1
fi

# Count modules
MODULE_COUNT=$(find "curriculum/l2-uk-en/${LEVEL}" -maxdepth 1 -name "[0-9]*-*.md" | wc -l)
echo "📊 Found ${MODULE_COUNT} modules in ${LEVEL_UPPER}"
echo ""

# Run level status check
if [ -f "scripts/check_${LEVEL}_status.py" ]; then
  echo "🔍 Running status check..."
  .venv/bin/python "scripts/check_${LEVEL}_status.py"
  echo ""
fi

# Audit all modules
FAILED_MODULES=()
PASSED_COUNT=0

echo "🧪 Auditing all ${LEVEL_UPPER} modules..."
echo ""

for module_file in curriculum/l2-uk-en/${LEVEL}/[0-9]*-*.md; do
  if [ -f "$module_file" ]; then
    MODULE_NUM=$(basename "$module_file" | grep -oP '^[0-9]+')

    echo -n "   Module ${MODULE_NUM}: "

    if .venv/bin/python scripts/audit_module.py "$module_file" > /dev/null 2>&1; then
      echo "✅"
      ((PASSED_COUNT++))
    else
      echo "❌"
      FAILED_MODULES+=("${MODULE_NUM}")
    fi
  fi
done

echo ""

# Vocabulary audit
echo "📚 Running global vocabulary audit for ${LEVEL_UPPER}..."
if .venv/bin/python scripts/global_vocab_audit.py --level "$LEVEL"; then
  echo "   ✅ Vocabulary audit passed"
else
  echo "   ⚠️  Vocabulary issues found"
fi
echo ""

# MDX generation test
echo "🔨 Testing MDX generation..."
if npm run generate l2-uk-en "$LEVEL" > /dev/null 2>&1; then
  echo "   ✅ MDX generation successful"
else
  echo "   ⚠️  MDX generation failed"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "  Audit Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Total modules: ${MODULE_COUNT}"
echo "Passed: ${PASSED_COUNT}"
echo "Failed: ${#FAILED_MODULES[@]}"
echo ""

if [ ${#FAILED_MODULES[@]} -gt 0 ]; then
  echo "Failed modules: ${FAILED_MODULES[*]}"
  echo ""
  echo "To audit specific module:"
  echo "  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${LEVEL}/[NUM]-*.md"
  exit 1
else
  echo "✅ All ${LEVEL_UPPER} modules passed audit!"
  exit 0
fi
