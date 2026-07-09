#!/bin/bash
# deploy_extensions.sh — fail-honest agent-extensions deploy for launchers.
#
# Both launchers (start-claude.sh, start-codex.sh) deploy
# agents_extensions/shared → .claude/.codex/.agents/... at startup. The old
# inline blocks ran `npm run <script> --silent 2>/dev/null || true` and then
# unconditionally printed a success line — so a failing deploy (orphan-path
# guard trip, prompt-lint violation, rsync error) launched the session
# against a silently STALE deploy target with zero signal. Same fail-silent
# bug class as the codexbar budget-guard blindness (#4823).
#
# This helper runs the deploy with output captured, prints one line on
# success, and on failure prints a loud banner plus the tail of the real
# output. It returns the npm exit code so callers can decide whether to
# abort; launchers deliberately continue (an interactive session with stale
# skills beats no session) but the operator now SEES the failure.
#
# Usage: deploy_agent_extensions <project_dir> <npm_script>
# Load-bearing tests: scripts/audit/test_deploy_extensions.sh (wrapped by
# tests/test_deploy_extensions.py in the required pytest gate).

deploy_agent_extensions() {
    local project_dir="$1"
    local npm_script="$2"

    if ! command -v npm >/dev/null 2>&1; then
        echo "⚠️  npm not found — skipping agent-extensions deploy (targets may be stale)"
        return 0
    fi
    if [ ! -f "$project_dir/package.json" ] \
        || ! grep -q "\"$npm_script\"" "$project_dir/package.json" 2>/dev/null; then
        echo "⚠️  npm script '$npm_script' not found in $project_dir/package.json — skipping deploy"
        return 0
    fi

    local log_file
    log_file="$(mktemp "${TMPDIR:-/tmp}/agents-deploy.XXXXXX")" || {
        echo "⚠️  mktemp failed — running deploy without output capture"
        (cd "$project_dir" && npm run --silent "$npm_script")
        return $?
    }

    local exit_code=0
    (cd "$project_dir" && npm run --silent "$npm_script" >"$log_file" 2>&1) || exit_code=$?

    if [ "$exit_code" -eq 0 ]; then
        echo "Agent extensions deployed ($npm_script)"
    else
        echo ""
        echo "⚠️⚠️  AGENT-EXTENSIONS DEPLOY FAILED (npm run $npm_script, exit $exit_code)  ⚠️⚠️"
        echo "⚠️   Deploy targets (.claude/.codex/.agents/...) may be STALE."
        echo "──── last 15 lines of deploy output ────"
        tail -15 "$log_file"
        echo "────────────────────────────────────────"
        echo "Reproduce with: npm run $npm_script"
    fi
    rm -f "$log_file"
    return "$exit_code"
}
