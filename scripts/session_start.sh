#!/bin/bash
# Session Start — project state at a glance
# Usage: scripts/session_start.sh
#
# Pulls from monitoring API (localhost:8765) to show:
#   1. Project totals
#   2. Per-track progress (research → content → audit → review)
#   3. Active builds
#   4. Failing modules
#   5. Active-manifest learner state
#   6. Gemini inbox check
#
# Issue: #595

set -euo pipefail

API="http://localhost:8765"
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Check API is running
# ---------------------------------------------------------------------------
if ! curl -s --max-time 2 "$API/api/state/summary" > /dev/null 2>&1; then
    echo -e "${RED}Monitoring API not running at $API${NC}"
    echo "Start it:  .venv/bin/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --reload &"
    exit 1
fi

echo ""
echo -e "${BOLD}==============================================${NC}"
echo -e "${BOLD}  Session Start — $(date '+%Y-%m-%d %H:%M')${NC}"
echo -e "${BOLD}==============================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# 0. Worktree hygiene — auto-reap finished dispatch/build worktrees
#    The disk-bleed backstop: dispatch worktrees are each a full ~700MB
#    checkout, and delegate.py only reaps them on the happy path (danger
#    mode + status=done + clean). Everything else (needs_finalize, crashed,
#    dirty, review mode) leaked forever → 11GB before this was wired in.
#    reap_worktrees.py is safe-by-default: it ONLY reaps worktrees whose PR
#    is MERGED/CLOSED or whose HEAD matches origin/<branch>, prunes merged
#    branches, and preserves dirty ones (surfaced below, never auto-touched).
#    Guarded with set +e + timeout so it can never abort session start.
# ---------------------------------------------------------------------------
if [ -x .venv/bin/python ] && [ -f scripts/orchestration/reap_worktrees.py ]; then
    if command -v timeout > /dev/null 2>&1; then TIMEOUT_CMD="timeout 90"
    elif command -v gtimeout > /dev/null 2>&1; then TIMEOUT_CMD="gtimeout 90"
    else TIMEOUT_CMD=""; fi
    set +e
    REAP_OUT=$($TIMEOUT_CMD .venv/bin/python scripts/orchestration/reap_worktrees.py \
        --apply --prune-merged-branches 2>/dev/null)
    reaped=$(printf '%s\n' "$REAP_OUT" | grep -cE '^(REMOVED|PRESERVED_THEN_REMOVED) ')
    dirty_q=$(printf '%s\n' "$REAP_OUT" | grep -c 'dirty; qualifies for reap')
    wt_disk=$(du -sh .worktrees 2>/dev/null | cut -f1)
    set -e
    if [ "${reaped:-0}" -gt 0 ]; then
        echo -e "${BOLD}WORKTREE HYGIENE${NC}  ${GREEN}reaped ${reaped}${NC} finished worktree(s); .worktrees now ${wt_disk:-?}"
    else
        echo -e "${BOLD}WORKTREE HYGIENE${NC}  ${DIM}nothing to reap; .worktrees ${wt_disk:-?}${NC}"
    fi
    if [ "${dirty_q:-0}" -gt 0 ]; then
        echo -e "  ${YELLOW}${dirty_q} dirty worktree(s) qualify but are preserved${NC} — save work + reclaim with:"
        echo -e "  ${DIM}.venv/bin/python scripts/orchestration/reap_worktrees.py --apply --prune-merged-branches --preserve-then-reap${NC}"
    fi
    echo ""
fi

# ---------------------------------------------------------------------------
# 1. Project totals
# ---------------------------------------------------------------------------
SUMMARY=$(curl -s "$API/api/state/summary")

total=$(echo "$SUMMARY" | jq '.totals.total')
research=$(echo "$SUMMARY" | jq '.totals.research_done')
content=$(echo "$SUMMARY" | jq '.totals.content_done')
audit=$(echo "$SUMMARY" | jq '.totals.audit_passing')
review=$(echo "$SUMMARY" | jq '.totals.final_review_done')

research_pct=$((research * 100 / total))
content_pct=$((content * 100 / total))
audit_pct=$((audit * 100 / total))
review_pct=$((review * 100 / total))

echo -e "${BOLD}PROJECT TOTALS${NC}  ($total modules)"
echo -e "  Research:     ${YELLOW}$research${NC}/$total  (${research_pct}%)"
echo -e "  Content:      ${BLUE}$content${NC}/$total  (${content_pct}%)"
echo -e "  Audit pass:   ${GREEN}$audit${NC}/$total  (${audit_pct}%)"
echo -e "  Final review: ${PURPLE}$review${NC}/$total  (${review_pct}%)"
echo ""

# ---------------------------------------------------------------------------
# 2. Per-track progress table
# ---------------------------------------------------------------------------
echo -e "${BOLD}PER-TRACK PROGRESS${NC}"
printf "  ${DIM}%-14s %5s  %5s  %5s  %5s  %5s  %s${NC}\n" \
    "Track" "Total" "Res" "Cont" "Audit" "Rev" "Profile"
echo -e "  ${DIM}$(printf '%.0s-' {1..65})${NC}"

# Sort tracks: core first, then seminar, then pro
echo "$SUMMARY" | jq -r '
  .tracks | to_entries | sort_by(
    if .value.profile == "core" then "0" + .key
    elif .value.profile == "seminar" then "1" + .key
    else "2" + .key end
  ) | .[] | [.key, .value.total, .value.research_done, .value.content_done,
              .value.audit_passing, .value.final_review_done, .value.profile] | @tsv
' | while IFS=$'\t' read -r track t r c a rv prof; do
    # Color the track name by profile
    case "$prof" in
        core)    track_color="$CYAN" ;;
        seminar) track_color="$YELLOW" ;;
        pro)     track_color="$PURPLE" ;;
        *)       track_color="$NC" ;;
    esac

    # Highlight fully-researched tracks
    if [ "$r" = "$t" ]; then
        r_disp="${GREEN}${r}${NC}"
    elif [ "$r" = "0" ]; then
        r_disp="${RED}${r}${NC}"
    else
        r_disp="${YELLOW}${r}${NC}"
    fi

    printf "  ${track_color}%-14s${NC} %5s  %5s  %5s  %5s  %5s  ${DIM}%s${NC}\n" \
        "$track" "$t" "$r" "$c" "$a" "$rv" "$prof"
done
echo ""

# ---------------------------------------------------------------------------
# 3. Active builds
# ---------------------------------------------------------------------------
ACTIVE=$(curl -s "$API/api/batch/active")
active_count=$(echo "$ACTIVE" | jq 'length')

if [ "$active_count" -gt 0 ]; then
    echo -e "${BOLD}ACTIVE BUILDS${NC}  ($active_count running)"
    echo "$ACTIVE" | jq -r '.[] | "  \(.track)/\(.slug) — \(.seconds_ago)s ago"'
else
    echo -e "${BOLD}ACTIVE BUILDS${NC}  ${DIM}none${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Failing modules
# ---------------------------------------------------------------------------
FAILING=$(curl -s "$API/api/state/failing")
fail_count=$(echo "$FAILING" | jq '.count')

if [ "$fail_count" -gt 0 ]; then
    echo -e "${BOLD}FAILING MODULES${NC}  ${RED}$fail_count${NC}"
    echo "$FAILING" | jq -r '.modules[:10][] |
        "  \(.track)/\(.slug) — audit:\(.audit_status) phases:\(.failed_phases | join(","))"'
    if [ "$fail_count" -gt 10 ]; then
        echo -e "  ${DIM}... and $((fail_count - 10)) more${NC}"
    fi
else
    echo -e "${BOLD}FAILING MODULES${NC}  ${GREEN}none${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# 5. Active-manifest learner state
# ---------------------------------------------------------------------------
PREPARATION=$(curl -s "$API/api/state/preparation")
echo "$PREPARATION" | jq -r '
    "\u001b[1mACTIVE MANIFEST\u001b[0m  \(.totals.manifest_active_tracks) tracks · \(.totals.manifest_active_modules) modules",
    "  learner bundles: \(.totals.module_state_counts.built) built · \(.totals.module_state_counts.partial) partial · \(.totals.module_state_counts.unbuilt) unbuilt",
    "  publication: \(.totals.publication_state_counts.published) published · \(.totals.publication_state_counts.generated) generated · \(.totals.publication_state_counts.absent) absent"'
echo ""

# ---------------------------------------------------------------------------
# 6. Gemini inbox
# ---------------------------------------------------------------------------
# Check via the message broker MCP — fall back gracefully if not available
INBOX_COUNT=""
if command -v curl > /dev/null 2>&1; then
    # Try the MCP endpoint via the bridge script
    INBOX_RESULT=$(.venv/bin/python -c "
import json, sys
sys.path.insert(0, 'scripts')
try:
    from ai_agent_bridge import check_inbox
    msgs = check_inbox('claude')
    print(json.dumps(msgs))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null || echo '{"error": "bridge unavailable"}')

    if echo "$INBOX_RESULT" | jq -e '.error' > /dev/null 2>&1; then
        echo -e "${BOLD}GEMINI INBOX${NC}  ${DIM}(check manually: mcp__message-broker__check_inbox)${NC}"
    else
        inbox_count=$(echo "$INBOX_RESULT" | jq 'if type == "array" then length else .unread // 0 end' 2>/dev/null || echo "?")
        if [ "$inbox_count" != "0" ] && [ "$inbox_count" != "?" ]; then
            echo -e "${BOLD}GEMINI INBOX${NC}  ${YELLOW}$inbox_count unread${NC}"
        else
            echo -e "${BOLD}GEMINI INBOX${NC}  ${DIM}empty${NC}"
        fi
    fi
fi

echo ""
echo -e "${DIM}Endpoints: $API/api/state/{preparation,summary,pipeline/{track},weak-points,failing}${NC}"
echo -e "${DIM}Dashboard: $API/ | Docs: $API/docs${NC}"
echo ""
