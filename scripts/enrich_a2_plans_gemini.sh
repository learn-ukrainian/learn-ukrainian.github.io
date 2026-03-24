#!/bin/bash
# Enrich A2 plan skeletons via Gemini in batches of 3
# Run: ./scripts/enrich_a2_plans_gemini.sh
set -euo pipefail

PLANS_DIR="curriculum/l2-uk-en/plans/a2"
OUTPUT_DIR="/tmp/a2-enriched"
mkdir -p "$OUTPUT_DIR"

PROMPT_HEADER='Enrich these A2 Ukrainian language plan YAMLs. Each is a skeleton — your job:

1. Ukrainian subtitle (replace TODO)
2. 4-5 specific learning objectives
3. Ukrainian section titles (topic-specific, not generic)
4. Detailed section points with grammar rules, examples, textbook refs
5. Vocabulary hints with English translations (required: 8-12, recommended: 5-8)
6. Specific activity focus descriptions
7. Textbook references (Заболотний, Авраменко)

Output ONLY the enriched YAML blocks separated by ---. No explanations.'

# Get all slugs
SLUGS=($(.venv/bin/python -c "
import yaml
data = yaml.safe_load(open('curriculum/l2-uk-en/curriculum.yaml'))
for s in data['levels']['a2']['modules']:
    print(s)
"))

TOTAL=${#SLUGS[@]}
BATCH_SIZE=3
BATCH_NUM=0

for ((i=0; i<TOTAL; i+=BATCH_SIZE)); do
    BATCH_NUM=$((BATCH_NUM + 1))
    BATCH_SLUGS=("${SLUGS[@]:i:BATCH_SIZE}")

    echo ""
    echo "========== Batch $BATCH_NUM (${BATCH_SLUGS[*]}) =========="

    # Check if already enriched
    OUTPUT_FILE="$OUTPUT_DIR/batch-${BATCH_NUM}.md"
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "  Already done — skipping"
        continue
    fi

    # Build prompt
    PROMPT="$PROMPT_HEADER"
    for slug in "${BATCH_SLUGS[@]}"; do
        PROMPT="$PROMPT

---
\`\`\`yaml
$(cat "$PLANS_DIR/${slug}.yaml")
\`\`\`"
    done

    # Send to Gemini
    echo "$PROMPT" | gemini -m gemini-3.1-pro-preview 2>/dev/null > "$OUTPUT_FILE"

    SIZE=$(wc -c < "$OUTPUT_FILE")
    echo "  ✅ Response: ${SIZE} bytes → $OUTPUT_FILE"

    # Brief delay to avoid rate limiting
    sleep 2
done

echo ""
echo "========== All batches complete =========="
echo "Output: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR/"
