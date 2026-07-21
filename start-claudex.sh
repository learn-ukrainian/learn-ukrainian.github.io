#!/usr/bin/env bash
# Interactive Claude Code UI on GPT-5.6 Sol through CLIProxyAPI.
#
# Interactive only — headless GPT/Codex work stays on ./start-codex.sh or the
# bridge. Process-scoped env only: never rewrites ~/.claude/settings.json, so
# ./start-claude.sh (native Anthropic) remains available in parallel.
#
# Compaction: sol_lead profile = 272k window, 258.4k auto-compact capacity
# (scripts/config/context_profiles.yaml). Do not raise English immersion policy
# via this launcher — it only changes the model route.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEAD_MODEL="gpt-5.6-sol"
SUBAGENT="${CLAUDEX_SUBAGENT:-terra}"
STATUS_SETTINGS="$PROJECT_DIR/agents_extensions/shared/statusline/claudex-settings.json"
FORWARD_ARGS=()

usage() {
    cat <<'EOF'
Usage: ./start-claudex.sh [--subagent sol|terra|luna] [CLAUDE_ARGS...]

Interactive Claude Code with GPT-5.6 Sol lead (272k context / 258.4k compact),
a configurable GPT-5.6 subagent, and live main/subagent status rows. Does not
rewrite ~/.claude/settings.json.

Options:
  --subagent MODEL  Subagent tier: terra (default), sol, or luna
  -h, --help        Show this help

Environment:
  CLAUDEX_SUBAGENT   Default subagent tier
  CLAUDEX_BASE_URL   CLIProxyAPI URL (default: http://127.0.0.1:8317)
  CLAUDEX_AUTH_TOKEN CLIProxyAPI token (default: sk-dummy)

Parallel native Claude: ./start-claude.sh in another terminal (original config).
Headless GPT: ./start-codex.sh or ab ask-codex — not this launcher.
EOF
}

resolve_model() {
    case "$1" in
        sol|gpt-5.6-sol) printf '%s\n' 'gpt-5.6-sol' ;;
        terra|gpt-5.6-terra) printf '%s\n' 'gpt-5.6-terra' ;;
        luna|gpt-5.6-luna) printf '%s\n' 'gpt-5.6-luna' ;;
        *) return 1 ;;
    esac
}

while (($#)); do
    case "$1" in
        --subagent)
            if (($# < 2)); then
                echo "Error: --subagent requires sol, terra, or luna." >&2
                exit 2
            fi
            SUBAGENT="$2"
            shift 2
            ;;
        --subagent=*)
            SUBAGENT="${1#*=}"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --model|--model=*)
            echo "Error: Claudex keeps the lead model on $LEAD_MODEL; configure only --subagent." >&2
            exit 2
            ;;
        *)
            FORWARD_ARGS+=("$1")
            shift
            ;;
    esac
done

# shellcheck source=scripts/lib/claude_route_guard.sh
source "$PROJECT_DIR/scripts/lib/claude_route_guard.sh"
if ! assert_claude_settings_route_clean "Claudex"; then
    exit 1
fi

# Resolve the Sol lead contract before delegated-model selection. The delegated
# model must not influence any main-session capacity or cold-start field.
# shellcheck source=scripts/lib/profile_resolver.sh
source "$PROJECT_DIR/scripts/lib/profile_resolver.sh"
if ! resolve_context_profile "sol_lead" "$LEAD_MODEL"; then
    echo "Error: could not resolve the certified Sol lead profile." >&2
    exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != "sol_lead" ]; then
    echo "Error: the Sol lead route did not resolve to its certified profile." >&2
    exit 1
fi
export LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="sol_lead"
# The nested start-claude.sh exports the certified assumed window and compact
# capacity from this profile. Keep the value here for the preflight diagnostic.
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"

if ! SUBAGENT_MODEL="$(resolve_model "$SUBAGENT")"; then
    echo "Error: unsupported subagent '$SUBAGENT' (choose sol, terra, or luna)." >&2
    exit 2
fi

if [ ! -f "$STATUS_SETTINGS" ]; then
    echo "Error: Claudex status settings are missing: $STATUS_SETTINGS" >&2
    exit 1
fi

export ANTHROPIC_BASE_URL="${CLAUDEX_BASE_URL:-http://127.0.0.1:8317}"
ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL%/}"
# CLIProxyAPI's documented public placeholder, not a repository credential.
export ANTHROPIC_AUTH_TOKEN="${CLAUDEX_AUTH_TOKEN:-sk-dummy}"
unset ANTHROPIC_API_KEY
export CLAUDE_CODE_SUBAGENT_MODEL="$SUBAGENT_MODEL"
export CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1
export CLAUDE_CODE_EFFORT_LEVEL=high
export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3
# Defer MCP schemas so the Sol route does not preload every tool definition.
export ENABLE_TOOL_SEARCH=true

if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl is required to check CLIProxyAPI." >&2
    exit 1
fi

if ! curl --fail --silent --show-error --output /dev/null --header @- \
    --connect-timeout 1 --max-time 3 "$ANTHROPIC_BASE_URL/v1/models" \
    <<< "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN"; then
    echo "Error: CLIProxyAPI check failed (unreachable or credential rejected)." >&2
    echo "   macOS: brew install cliproxyapi && brew services start cliproxyapi" >&2
    echo "   Connect: cliproxyapi --codex-login" >&2
    exit 1
fi

echo "Claudex: lead=$LEAD_MODEL subagent=$SUBAGENT_MODEL profile=$LEARN_UKRAINIAN_PROFILE_ID"
echo "         window=$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS compact=$CLAUDE_CODE_AUTO_COMPACT_WINDOW effort=$CLAUDE_CODE_EFFORT_LEVEL (process-scoped; user settings untouched)"
exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/orchestration/claudex_supervisor.py" "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL" --settings "$STATUS_SETTINGS" "${FORWARD_ARGS[@]}"
