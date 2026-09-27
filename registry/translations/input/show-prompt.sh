#!/bin/bash
# Show Gemini prompt for a batch
# Usage: ./show-prompt.sh batch-ab

BATCH_FILE=$1

if [ -z "$BATCH_FILE" ]; then
    echo "Usage: ./show-prompt.sh batch-ab"
    echo ""
    echo "Available batches:"
    ls -1 batch-* 2>/dev/null
    exit 1
fi

if [ ! -f "$BATCH_FILE" ]; then
    echo "Error: File $BATCH_FILE not found"
    exit 1
fi

cat << 'EOF'
Translate these Ukrainian words to English. Return ONLY a JSON object with format:
{
  "ukrainian_word": "english_translation"
}

Rules:
- Provide the most common English translation
- For adjectives, translate as adjective (e.g., "новий" → "new")
- For verbs in infinitive, translate with "to" (e.g., "говорити" → "to speak")
- For nouns, provide the basic English equivalent
- For proper nouns (names, places), transliterate or provide English equivalent
- For diminutives, include "little" or "dear" in translation
- Skip words that are clearly fragments or corrupted (just omit from JSON)
- Return ONLY the JSON object, no other text

Words:

EOF

cat "$BATCH_FILE"

echo ""
echo "Return the JSON object now."
