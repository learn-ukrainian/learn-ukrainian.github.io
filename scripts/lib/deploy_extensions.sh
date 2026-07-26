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
# output. It returns the npm exit code so callers can choose whether to abort;
# start-claude.sh refuses to launch against stale definitions.
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

    # Durable status breadcrumb. Printing the banner to the terminal is NOT
    # enough: the launcher hands the terminal to the agent CLI, which clears
    # it on start, so the operator never sees the banner and the agent boots
    # with no idea its own config is stale. Persist the verdict where
    # session-setup.sh can read it back into the session capsule.
    # .agent is concurrent agent-owned state. The helper opens it with
    # O_NOFOLLOW|O_DIRECTORY and updates leaves by dir_fd; plain shell
    # redirection/cp/rm here would reintroduce deploy's path-swap escape.
    local scripts_dir helper_project_root status_helper
    scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    helper_project_root="$(cd "$scripts_dir/.." && pwd)"
    status_helper="$scripts_dir/deploy/update_agent_deploy_status.py"

    if [ "$exit_code" -eq 0 ]; then
        if ! "$helper_project_root/.venv/bin/python" "$status_helper" clear --agent-root "$project_dir/.agent"; then
            echo "Error: agent extensions deployed but deploy-status cleanup refused an unsafe .agent root." >&2
            rm -f "$log_file"
            return 1
        fi
        echo "Agent extensions deployed ($npm_script)"
    else
        echo ""
        echo "⚠️⚠️  AGENT-EXTENSIONS DEPLOY FAILED (npm run $npm_script, exit $exit_code)  ⚠️⚠️"
        echo "⚠️   Deploy targets (.claude/.codex/.agents/...) may be STALE."
        echo "──── last 15 lines of deploy output ────"
        tail -15 "$log_file"
        echo "────────────────────────────────────────"
        echo "Reproduce with: npm run $npm_script"
        if ! "$helper_project_root/.venv/bin/python" "$status_helper" record-failure \
            --agent-root "$project_dir/.agent" \
            --script "$npm_script" \
            --exit-code "$exit_code" \
            --failure-log "$log_file"; then
            echo "Error: deploy-status update refused an unsafe .agent root." >&2
        fi
    fi
    rm -f "$log_file"
    return "$exit_code"
}
