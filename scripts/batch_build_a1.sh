#!/bin/bash
# Batch build A1 modules M08-M55 (48 modules)
# Writer: gemini-tools (Gemini with MCP/VESUM access)
# Reviewer: Claude (cross-agent)
# Usage: ./scripts/batch_build_a1.sh [start_module]
#   start_module: optional, resume from this module number (default: 8)

set -euo pipefail
cd "$(dirname "$0")/.."

START=${1:-8}
END=55
WRITER="gemini-tools"
LOG_DIR="logs/batch-a1-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"

echo "============================================================"
echo "  A1 Batch Build: M${START}-M${END} (writer: ${WRITER})"
echo "  Log dir: ${LOG_DIR}"
echo "  Started: $(date)"
echo "============================================================"

PASS=0
FAIL=0
SKIP=0

for i in $(seq "$START" "$END"); do
    slug=$(.venv/bin/python -c "
import yaml
with open('curriculum/l2-uk-en/curriculum.yaml') as f:
    data = yaml.safe_load(f)
print(data['levels']['a1']['modules'][$i - 1])
")

    # Skip if already built
    if [ -f "curriculum/l2-uk-en/a1/${slug}.md" ]; then
        echo "  ⏭️  M${i} ${slug} — already built, skipping"
        SKIP=$((SKIP + 1))
        continue
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Building M${i}/${END}: ${slug} ($(date +%H:%M:%S))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if .venv/bin/python scripts/build/v6_build.py a1 "$i" --writer "$WRITER" --step all \
        > "${LOG_DIR}/${slug}.log" 2>&1; then
        # Check if review passed
        if grep -q "Review PASSED\|Build COMPLETE" "${LOG_DIR}/${slug}.log"; then
            score=$(grep -oP 'Weighted score.*?(\d+\.\d+)' "${LOG_DIR}/${slug}.log" | tail -1 | grep -oP '\d+\.\d+')
            echo "  ✅ M${i} ${slug} — ${score:-?}/10"
            PASS=$((PASS + 1))
        else
            echo "  ⚠️  M${i} ${slug} — completed but review may have failed"
            FAIL=$((FAIL + 1))
        fi
    else
        echo "  ❌ M${i} ${slug} — build failed (see ${LOG_DIR}/${slug}.log)"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "============================================================"
echo "  A1 Batch Build COMPLETE"
echo "  Passed: ${PASS}  Failed: ${FAIL}  Skipped: ${SKIP}"
echo "  Finished: $(date)"
echo "  Logs: ${LOG_DIR}"
echo "============================================================"
