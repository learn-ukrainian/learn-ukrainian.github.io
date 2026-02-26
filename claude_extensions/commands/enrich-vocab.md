#!/bin/bash
# /enrich-vocab [level] [module] - Run vocabulary enrichment pipeline

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: /enrich-vocab [level] [module_num]"
  echo ""
  echo "Example:"
  echo "  /enrich-vocab b2 75"
  echo ""
  echo "What this does:"
  echo "  1. Adds grammatical metadata (gender, aspect)"
  echo "  2. Validates enriched entries"
  echo "  3. Optionally rebuilds vocabulary database"
  exit 1
fi

LEVEL="$1"
MODULE_NUM="$2"
LEVEL_UPPER=$(echo "$LEVEL" | tr '[:lower:]' '[:upper:]')

echo "════════════════════════════════════════════════════════════════"
echo "  Vocabulary Enrichment: ${LEVEL_UPPER} Module ${MODULE_NUM}"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if module exists
MODULE_FILE=$(find "curriculum/l2-uk-en/${LEVEL}" -name "${MODULE_NUM}-*.md" | head -1)

if [ -z "$MODULE_FILE" ]; then
  echo "❌ Module not found: ${LEVEL_UPPER} Module ${MODULE_NUM}"
  exit 1
fi

MODULE_SLUG=$(basename "$MODULE_FILE" .md)

echo "📄 Module: $MODULE_SLUG"
echo ""

# Determine vocabulary file location based on level
if [[ "$LEVEL" =~ ^(a1|a2|b1)$ ]]; then
  # A1-B1: Vocabulary embedded in module markdown
  echo "📋 Level ${LEVEL_UPPER}: Vocabulary is embedded in module file"
  echo "   Location: $MODULE_FILE"
  echo ""
  echo "⚠️  For A1-B1, vocabulary is in markdown tables."
  echo "   Enrichment happens during module audit."
  echo "   Run: .venv/bin/python scripts/audit_module.py $MODULE_FILE"
  exit 0
else
  # B2+: Separate vocabulary YAML
  VOCAB_FILE="curriculum/l2-uk-en/${LEVEL}/vocabulary/${MODULE_SLUG}.yaml"

  if [ ! -f "$VOCAB_FILE" ]; then
    echo "❌ Vocabulary file not found: $VOCAB_FILE"
    echo ""
    echo "Expected location for B2+: curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml"
    exit 1
  fi

  echo "📋 Vocabulary file: $VOCAB_FILE"
  echo ""
fi

# Run enrichment
echo "🔧 Running vocabulary enrichment..."
if .venv/bin/python scripts/enrich_yaml_vocab.py "$VOCAB_FILE"; then
  echo "   ✅ Enrichment completed"
else
  echo "   ❌ Enrichment failed"
  exit 1
fi
echo ""

# Validate enriched vocabulary
echo "🧪 Validating enriched vocabulary..."
if npm run validate:yaml "$VOCAB_FILE" > /dev/null 2>&1; then
  echo "   ✅ YAML validation passed"
else
  echo "   ❌ YAML validation failed"
  exit 1
fi
echo ""

# Ask about rebuilding database
echo "📚 Rebuild vocabulary database?"
echo "   This updates vocabulary.db with all enriched entries."
echo ""
read -p "Rebuild now? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "🏗️  Rebuilding vocabulary database..."
  if npm run vocab:rebuild; then
    echo "   ✅ Database rebuilt successfully"
  else
    echo "   ⚠️  Database rebuild had warnings"
  fi
else
  echo "⏭️  Skipping database rebuild"
  echo "   Run manually later: npm run vocab:rebuild"
fi
echo ""

# Global vocabulary audit
echo "📊 Running global vocabulary audit..."
if .venv/bin/python scripts/global_vocab_audit.py --level "$LEVEL"; then
  echo "   ✅ Vocabulary audit passed"
else
  echo "   ⚠️  Vocabulary issues found"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Vocabulary enrichment complete!"
echo "════════════════════════════════════════════════════════════════"
