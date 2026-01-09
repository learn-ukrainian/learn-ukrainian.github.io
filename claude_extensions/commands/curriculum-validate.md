#!/bin/bash
# /curriculum-validate - Validate all curriculum levels

echo "════════════════════════════════════════════════════════════════"
echo "  Ukrainian Curriculum Validation"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
  echo "❌ Virtual environment not found. Run: python3 -m venv .venv"
  exit 1
fi

# Track overall status
FAILED_LEVELS=()

# Validate each level
for level in a1 a2 b1 b2 c1 c2; do
  LEVEL_UPPER=$(echo "$level" | tr '[:lower:]' '[:upper:]')

  if [ -f "scripts/check_${level}_status.py" ]; then
    echo "📋 Validating ${LEVEL_UPPER}..."

    if .venv/bin/python "scripts/check_${level}_status.py"; then
      echo "   ✅ ${LEVEL_UPPER} validation passed"
    else
      echo "   ⚠️  ${LEVEL_UPPER} has issues"
      FAILED_LEVELS+=("$LEVEL_UPPER")
    fi
    echo ""
  else
    echo "⏭️  Skipping ${LEVEL_UPPER} (no status checker)"
    echo ""
  fi
done

# Schema validation
echo "🧪 Running schema validation..."
if npm run test:schema > /dev/null 2>&1; then
  echo "   ✅ Schema validation passed"
else
  echo "   ⚠️  Schema validation failed"
  FAILED_LEVELS+=("SCHEMA")
fi
echo ""

# Vocabulary database check
echo "📚 Checking vocabulary database..."
if [ -f "curriculum/l2-uk-en/vocabulary.db" ]; then
  DB_SIZE=$(wc -c < "curriculum/l2-uk-en/vocabulary.db")
  if [ "$DB_SIZE" -gt 1000 ]; then
    echo "   ✅ Vocabulary database exists (${DB_SIZE} bytes)"
  else
    echo "   ⚠️  Vocabulary database is suspiciously small"
    FAILED_LEVELS+=("VOCAB_DB")
  fi
else
  echo "   ⚠️  Vocabulary database missing (run: npm run vocab:rebuild)"
  FAILED_LEVELS+=("VOCAB_DB")
fi
echo ""

# Docusaurus build check
echo "🏗️  Checking Docusaurus build..."
cd docusaurus
if npm run build > /dev/null 2>&1; then
  echo "   ✅ Docusaurus build successful"
else
  echo "   ⚠️  Docusaurus build failed"
  FAILED_LEVELS+=("DOCUSAURUS")
fi
cd ..
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
if [ ${#FAILED_LEVELS[@]} -eq 0 ]; then
  echo "  ✅ ALL VALIDATIONS PASSED"
  echo "════════════════════════════════════════════════════════════════"
  exit 0
else
  echo "  ⚠️  VALIDATION FAILURES: ${FAILED_LEVELS[*]}"
  echo "════════════════════════════════════════════════════════════════"
  exit 1
fi
