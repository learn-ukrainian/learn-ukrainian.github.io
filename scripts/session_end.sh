#!/bin/bash
# Session End — what changed, what's next
# Usage: scripts/session_end.sh
#
# Shows:
#   1. Git changes this session (uncommitted work)
#   2. Current project state (delta vs where we started)
#   3. Active builds still running
#   4. New failures to investigate
#   5. Memory save reminder
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

echo ""
echo -e "${BOLD}==============================================${NC}"
echo -e "${BOLD}  Session End — $(date '+%Y-%m-%d %H:%M')${NC}"
echo -e "${BOLD}==============================================${NC}"
echo ""

# ---------------------------------------------------------------------------
# 1. Git changes
# ---------------------------------------------------------------------------
echo -e "${BOLD}GIT CHANGES${NC}"

staged=$(git diff --cached --stat 2>/dev/null | tail -1)
unstaged=$(git diff --stat 2>/dev/null | tail -1)
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

if [ -n "$staged" ]; then
    echo -e "  Staged:    ${GREEN}$staged${NC}"
else
    echo -e "  Staged:    ${DIM}none${NC}"
fi

if [ -n "$unstaged" ]; then
    echo -e "  Unstaged:  ${YELLOW}$unstaged${NC}"
else
    echo -e "  Unstaged:  ${DIM}none${NC}"
fi

echo -e "  Untracked: $untracked files"

# Recent commits this session (last 2 hours)
recent=$(git log --oneline --since="2 hours ago" 2>/dev/null | head -5)
if [ -n "$recent" ]; then
    echo ""
    echo -e "  ${DIM}Recent commits:${NC}"
    echo "$recent" | while read -r line; do
        echo -e "    $line"
    done
fi
echo ""

# ---------------------------------------------------------------------------
# 2. Project state
# ---------------------------------------------------------------------------
if curl -s --max-time 2 "$API/api/state/summary" > /dev/null 2>&1; then
    SUMMARY=$(curl -s "$API/api/state/summary")

    total=$(echo "$SUMMARY" | jq '.totals.total')
    research=$(echo "$SUMMARY" | jq '.totals.research_done')
    content=$(echo "$SUMMARY" | jq '.totals.content_done')
    audit=$(echo "$SUMMARY" | jq '.totals.audit_passing')
    review=$(echo "$SUMMARY" | jq '.totals.final_review_done')

    echo -e "${BOLD}PROJECT STATE${NC}"
    echo -e "  Research:     ${YELLOW}$research${NC}/$total  ($((research * 100 / total))%)"
    echo -e "  Content:      ${BLUE}$content${NC}/$total  ($((content * 100 / total))%)"
    echo -e "  Audit pass:   ${GREEN}$audit${NC}/$total  ($((audit * 100 / total))%)"
    echo -e "  Final review: ${PURPLE}$review${NC}/$total  ($((review * 100 / total))%)"
    echo ""

    # Active builds
    ACTIVE=$(curl -s "$API/api/batch/active")
    active_count=$(echo "$ACTIVE" | jq 'length')
    if [ "$active_count" -gt 0 ]; then
        echo -e "${BOLD}STILL RUNNING${NC}  ${YELLOW}$active_count builds${NC}"
        echo "$ACTIVE" | jq -r '
            [.[].track] | group_by(.) | map({track: .[0], count: length}) |
            sort_by(-.count) | .[] | "  \(.track): \(.count)"'
        echo ""
    fi

    # Failures
    FAILING=$(curl -s "$API/api/state/failing")
    fail_count=$(echo "$FAILING" | jq '.count')
    if [ "$fail_count" -gt 0 ]; then
        echo -e "${BOLD}FAILING${NC}  ${RED}$fail_count modules${NC}"
        echo "$FAILING" | jq -r '.modules[:5][] |
            "  \(.track)/\(.slug) — audit:\(.audit_status) phases:\(.failed_phases | join(","))"'
        if [ "$fail_count" -gt 5 ]; then
            echo -e "  ${DIM}... and $((fail_count - 5)) more${NC}"
        fi
        echo ""
    fi
else
    echo -e "${DIM}Monitoring API not running — skipping state check${NC}"
    echo ""
fi

# ---------------------------------------------------------------------------
# 3. Memory save reminder
# ---------------------------------------------------------------------------
echo -e "${BOLD}REMEMBER${NC}"
echo -e "  ${CYAN}Save session progress to memory before closing:${NC}"
echo -e "  ${DIM}mcp__memory__add_observations(observations=[{${NC}"
echo -e "  ${DIM}    \"entityName\": \"current-session\",${NC}"
echo -e "  ${DIM}    \"contents\": [\"Did: ... In progress: ... Next: ...\"]${NC}"
echo -e "  ${DIM}}])${NC}"
echo ""
