#!/bin/bash
# Retired A2 plan-enrichment runner; use the AGY pipeline
# Run: ./scripts/enrich_a2_plans_gemini.sh
set -euo pipefail

# Frozen Gemini CLI runner; no admitted transport for new execution (#9316).
printf '%s\n' "Refused: legacy Gemini CLI plan enrichment; use the AGY pipeline." >&2
exit 2
