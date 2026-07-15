#!/usr/bin/env bash
# Run Claude Code on GPT-5.6 Sol through CLIProxyAPI.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEAD_MODEL="gpt-5.6-sol"
SUBAGENT="${CLAUDEX_SUBAGENT:-sol}"
FORWARD_ARGS=()

usage() {
    cat <<'EOF'
Usage: ./start-claudex.sh [--subagent sol|terra|luna] [CLAUDE_ARGS...]

Launch Claude Code with GPT-5.6 Sol as the lead model and a configurable
GPT-5.6 subagent model. Other arguments are forwarded to start-claude.sh.

Options:
  --subagent MODEL  Subagent tier: sol (default), terra, or luna
  -h, --help        Show this help

Environment:
  CLAUDEX_SUBAGENT   Default subagent tier
  CLAUDEX_BASE_URL   CLIProxyAPI URL (default: http://127.0.0.1:8317)
  CLAUDEX_AUTH_TOKEN CLIProxyAPI token (default: sk-dummy)
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

if ! SUBAGENT_MODEL="$(resolve_model "$SUBAGENT")"; then
    echo "Error: unsupported subagent '$SUBAGENT' (choose sol, terra, or luna)." >&2
    exit 2
fi

export ANTHROPIC_BASE_URL="${CLAUDEX_BASE_URL:-http://127.0.0.1:8317}"
ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL%/}"
# CLIProxyAPI's documented public placeholder, not a repository credential.
export ANTHROPIC_AUTH_TOKEN="${CLAUDEX_AUTH_TOKEN:-sk-dummy}"
unset ANTHROPIC_API_KEY
export CLAUDE_CODE_SUBAGENT_MODEL="$SUBAGENT_MODEL"
export CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1
export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3
export ENABLE_TOOL_SEARCH=false

if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl is required to check CLIProxyAPI." >&2
    exit 1
fi

if ! curl --fail --silent --show-error --output /dev/null --header @- \
    --connect-timeout 1 --max-time 3 "$ANTHROPIC_BASE_URL/v1/models" \
    <<< "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN"; then
    echo "Error: CLIProxyAPI check failed at $ANTHROPIC_BASE_URL (unreachable or credential rejected)." >&2
    echo "   macOS: brew install cliproxyapi && brew services start cliproxyapi" >&2
    echo "   Connect: cliproxyapi --codex-login" >&2
    exit 1
fi

echo "Claudex: lead=$LEAD_MODEL subagent=$SUBAGENT_MODEL proxy=$ANTHROPIC_BASE_URL"
exec "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL" "${FORWARD_ARGS[@]}"
