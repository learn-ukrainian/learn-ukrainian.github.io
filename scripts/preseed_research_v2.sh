#!/bin/bash
# Pre-seed Phase A research — v2
# Resumes from where v1 left off. Skips modules with research already done.
#
# Completed in v1: istorio (136/136), b2-pro (40/40)
# Partial in v1:   c1-pro (49/50), c2 (68/101), oes (30/100), ruth (23/100)
# Failed in v1:    lit* (4/387) — plan file naming bug (fixed below)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LOGDIR="logs/research-preseed"
mkdir -p "$LOGDIR"
TIMESTAMP=$(date +%Y%m%d-%H%M)

# ─── Step 1: Fix lit* plan file naming ────────────────────────────────
# Plan files have numbered prefixes (03-eneida-feast.yaml) but
# get_module_paths() expects bare slugs (eneida-feast.yaml).
# Rename to bare slugs. Safe: no collisions verified.

echo "============================================="
echo "  Phase A Pre-Seed v2 — $TIMESTAMP"
echo "============================================="
echo ""

fix_count=0
for track in lit lit-essay lit-fantastika lit-hist-fic lit-humor lit-juvenile lit-war; do
  plan_dir="curriculum/l2-uk-en/plans/$track"
  [ -d "$plan_dir" ] || continue
  for f in "$plan_dir"/*.yaml; do
    base=$(basename "$f")
    # Only rename files with leading number prefix (1-3 digits followed by dash)
    if [[ "$base" =~ ^[0-9]{1,3}- ]]; then
      bare=$(echo "$base" | sed 's/^[0-9]*-//')
      if [ ! -f "$plan_dir/$bare" ]; then
        mv "$f" "$plan_dir/$bare"
        ((fix_count++))
      fi
    fi
  done
done
echo "Fixed $fix_count plan file names (stripped numeric prefixes)"
echo ""

# ─── Step 2: Determine what to run ────────────────────────────────────

# Tracks and their expected counts (for display only — --all handles skipping)
# Gemini tracks (use gemini-cli for Phase A)
#   lit: 214, oes: 70, ruth: 77 → ~361 modules
GEMINI_TRACKS="lit oes ruth"
# Claude tracks (use --use-claude A for Phase A)
#   c1-pro: 1, c2: 33, lit-*: ~170 → ~204 modules
CLAUDE_TRACKS="c1-pro c2 lit-essay lit-fantastika lit-hist-fic lit-humor lit-juvenile lit-war"

# Count remaining work per track
echo "Remaining work (modules without research):"
for track in $GEMINI_TRACKS $CLAUDE_TRACKS; do
  total=$(.venv/bin/python -c "
import yaml, sys
sys.path.insert(0, 'scripts')
from batch_gemini_config import get_module_index
idx = get_module_index('$track')
print(idx['total'])
" 2>/dev/null || echo "?")

  research_dir="curriculum/l2-uk-en/$track/research"
  done=0
  [ -d "$research_dir" ] && done=$(ls "$research_dir"/*-research.md 2>/dev/null | wc -l | tr -d ' ')
  remaining=$((total - done))
  echo "  $track: $remaining remaining ($done/$total done)"
done
echo ""

# ─── Step 3: Launch builds ────────────────────────────────────────────

# Max parallel per engine to avoid rate limits
MAX_GEMINI=2
MAX_CLAUDE=4

pids=()
track_pids=()

launch() {
  local track=$1 engine=$2
  local logfile="$LOGDIR/${track}-${TIMESTAMP}.log"

  if [ "$engine" = "claude" ]; then
    .venv/bin/python scripts/build_module_v3.py "$track" --all --research-only --use-claude A \
      > "$logfile" 2>&1 &
  else
    .venv/bin/python scripts/build_module_v3.py "$track" --all --research-only \
      > "$logfile" 2>&1 &
  fi
  local pid=$!
  pids+=("$pid")
  track_pids+=("$track:$pid")
  echo "  [$engine] $track → PID $pid (log: $logfile)"
}

echo "Launching Gemini tracks (max $MAX_GEMINI parallel)..."
g_count=0
for track in $GEMINI_TRACKS; do
  launch "$track" "gemini"
  ((g_count++))
  # Stagger starts to avoid thundering herd
  sleep 5
done

echo ""
echo "Launching Claude tracks (max $MAX_CLAUDE parallel)..."
c_count=0
for track in $CLAUDE_TRACKS; do
  launch "$track" "claude"
  ((c_count++))
  sleep 5
done

total_tracks=$((g_count + c_count))
echo ""
echo "$total_tracks tracks launched ($g_count Gemini + $c_count Claude)."
echo "Monitor: tail -f $LOGDIR/*-$TIMESTAMP.log"
echo ""

# ─── Step 4: Wait and report ──────────────────────────────────────────

# Monitor loop: print progress every 5 minutes
while true; do
  # Check if any are still running
  alive=0
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      ((alive++))
    fi
  done

  if [ "$alive" -eq 0 ]; then
    break
  fi

  echo "[$(date +%H:%M)] $alive/$total_tracks tracks still running..."
  sleep 300
done

echo ""
echo "============================================="
echo "  ALL DONE — $(date)"
echo "============================================="
echo ""

# Summary
for entry in "${track_pids[@]}"; do
  track="${entry%%:*}"
  logfile="$LOGDIR/${track}-${TIMESTAMP}.log"
  passed=$(grep -c "VERDICT: PASS" "$logfile" 2>/dev/null || echo "0")
  failed=$(grep -c "VERDICT: FAIL\|FAILED\|ERROR:" "$logfile" 2>/dev/null || echo "0")
  printf "  %-20s passed=%-4s failed=%-4s\n" "$track" "$passed" "$failed"
done
