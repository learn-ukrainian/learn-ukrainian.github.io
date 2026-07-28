#!/usr/bin/env bash
# Interactive Claude Code UI routed to Zhipu GLM (GLM-5.2) via Anthropic-compatible API.
#
# Design (parallel-safe with ./start-claude.sh):
# - Process-scoped env only. Never writes ~/.claude/settings.json.
# - Original Anthropic Claude config stays untouched; run native Claude in another terminal.
# - Refuses to launch if settings.json already pins route env keys (cc-switch hazard).
# - Compaction comes from scripts/config/context_profiles.yaml (1M for GLM-5.2).
# - Static Z.AI API key authentication (GLMCC_AUTH_TOKEN, ZAI_API_KEY, ZHIPU_API_KEY, GLM_API_KEY,
#   or ANTHROPIC_AUTH_TOKEN). Static keys require no OAuth helper or apiKeyHelper auto-refresh,
#   unlike KimiCC subscription tokens.
#
# Official references:
# - https://docs.z.ai/scenario-example/develop-tools/claude
# - https://z.ai/blog/glm-5.2

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$PROJECT_DIR"
# NOTE (r2 review): unlike start-kimicc.sh, this launcher does NOT redirect
# PROJECT_DIR to the main worktree. Kimicc's redirect exists solely so the
# apiKeyHelper path baked into its isolated Claude config survives worktree
# cleanup; glmcc uses a static key with no helper, so the redirect would only
# root a feature-worktree launch at the wrong branch. The invoking checkout IS
# the project context.
_LU_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$_LU_ROOT/scripts/lib/scrub_hermes_node_path.sh" ]; then
  # shellcheck source=scripts/lib/scrub_hermes_node_path.sh
  source "$_LU_ROOT/scripts/lib/scrub_hermes_node_path.sh"
  scrub_hermes_node_from_path
fi
unset _LU_ROOT
export PATH="${HOME}/.local/bin:${PATH:-}"
hash -r 2>/dev/null || true

ENDPOINT="${GLMCC_ENDPOINT:-coding}"
MODEL_ALIAS="${GLMCC_MODEL:-glm-5.2}"
FORWARD_ARGS=()
ISOLATE_CONFIG="${GLMCC_ISOLATE_CONFIG:-1}"
DEFAULT_AGENT="${GLMCC_AGENT-infra-orchestrator}"

usage() {
  cat <<'EOF'
Usage: ./start-glmcc.sh [options] [CLAUDE_ARGS...]

Launch Claude Code with GLM as the lead model (interactive only).
Does not rewrite ~/.claude/settings.json — original Claude config stays intact.

Options:
  --model ALIAS     glm-5.2 (default) | glm | glm52
  --endpoint NAME   coding (default) | platform
                    Both map to Z.AI Anthropic endpoint https://api.z.ai/api/anthropic
  --isolate-config  Use CLAUDE_CONFIG_DIR=$HOME/.claude-glmcc (DEFAULT; separate sessions)
  --no-isolate-config
                    Use the operator's live ~/.claude config instead
  --agent NAME      Session agent (forwarded to Claude Code). Default:
                    infra-orchestrator when no --epic is given; explicit --agent wins
  -h, --help        Show this help
  -- [CLAUDE_ARGS...]
                    Everything after -- is forwarded verbatim to Claude Code,
                    even args that collide with launcher flags above.
                    A forwarded --model is still rejected: GLMCC owns the lead model.

Environment:
  GLMCC_MODEL / GLMCC_ENDPOINT      Defaults for --model / --endpoint
  GLMCC_AGENT                       Default agent (default infra-orchestrator;
                                    empty string = inherit project settings.json default)
  GLMCC_ISOLATE_CONFIG=0            Same as --no-isolate-config
  ZAI_API_KEY / ZHIPU_API_KEY /      Z.AI API key (preferred)
  GLM_API_KEY / GLMCC_AUTH_TOKEN
  GLMCC_BASE_URL                    Override Anthropic-compatible base URL
                                    (default: https://api.z.ai/api/anthropic)
  GLMCC_API_TIMEOUT_MS              API timeout override (default: 3000000)
  GLMCC_DRY_RUN=1                   Resolve route + auth, print summary, exit before launch
  CLAUDE_CONFIG_DIR                 Isolated Claude config directory
  CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1
                                    Bypass settings.json env conflict check (emergency)

Examples:
  ZAI_API_KEY=<your-key> ./start-glmcc.sh
  ./start-glmcc.sh --model glm-5.2
  ./start-glmcc.sh --epic harness
  ./start-glmcc.sh -- --verbose --help
EOF
}

default_base_url() {
  case "$1" in
    coding|platform) printf '%s\n' 'https://api.z.ai/api/anthropic' ;;
    *) return 1 ;;
  esac
}

_resolved_auth=""
AUTH_SOURCE=""
resolve_auth_token() {
  _resolved_auth=""
  AUTH_SOURCE=""
  if [ -n "${GLMCC_AUTH_TOKEN:-}" ]; then
    _resolved_auth="$GLMCC_AUTH_TOKEN"
    AUTH_SOURCE="GLMCC_AUTH_TOKEN"
    return 0
  fi
  if [ -n "${ZAI_API_KEY:-}" ]; then
    _resolved_auth="$ZAI_API_KEY"
    AUTH_SOURCE="ZAI_API_KEY"
    return 0
  fi
  if [ -n "${ZHIPU_API_KEY:-}" ]; then
    _resolved_auth="$ZHIPU_API_KEY"
    AUTH_SOURCE="ZHIPU_API_KEY"
    return 0
  fi
  if [ -n "${GLM_API_KEY:-}" ]; then
    _resolved_auth="$GLM_API_KEY"
    AUTH_SOURCE="GLM_API_KEY"
    return 0
  fi
  # r3 security review: NO ambient ANTHROPIC_AUTH_TOKEN fallback — a credential
  # intended for Anthropic must never be transmitted to the Z.AI endpoint.
  # GLM credentials are explicit only: GLMCC_AUTH_TOKEN / ZAI_API_KEY /
  # ZHIPU_API_KEY / GLM_API_KEY.
  return 1
}

while (($#)); do
  case "$1" in
    --)
      shift
      while (($#)); do
        FORWARD_ARGS+=("$1")
        shift
      done
      ;;
    --model)
      if (($# < 2)); then
        echo "Error: --model requires glm-5.2, glm52, or glm." >&2
        exit 2
      fi
      MODEL_ALIAS="$2"
      shift 2
      ;;
    --model=*)
      MODEL_ALIAS="${1#*=}"
      shift
      ;;
    --endpoint)
      if (($# < 2)); then
        echo "Error: --endpoint requires coding or platform." >&2
        exit 2
      fi
      ENDPOINT="$2"
      shift 2
      ;;
    --endpoint=*)
      ENDPOINT="${1#*=}"
      shift
      ;;
    --isolate-config)
      ISOLATE_CONFIG=1
      shift
      ;;
    --no-isolate-config)
      ISOLATE_CONFIG=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

if ! _glmcc_route="$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/review/model_catalog.py" \
    --resolve-glm-model "$MODEL_ALIAS" --format glmcc 2>/dev/null)"; then
  echo "Error: unsupported model '$MODEL_ALIAS' (use glm-5.2)." >&2
  exit 2
fi
IFS=$'\t' read -r MODEL_ALIAS _platform_model _coding_model PROFILE_ID <<< "$_glmcc_route"
if [ -z "$MODEL_ALIAS" ] || [ -z "$_platform_model" ] || [ -z "$_coding_model" ] || [ -z "$PROFILE_ID" ]; then
  echo "Error: invalid GLM route in scripts/config/model_catalog.yaml." >&2
  exit 1
fi
unset _glmcc_route

case "$ENDPOINT" in
  platform|coding) ;;
  *)
    echo "Error: unsupported endpoint '$ENDPOINT' (use platform or coding)." >&2
    exit 2
    ;;
esac

case "$ISOLATE_CONFIG" in
  0|1) ;;
  *)
    echo "Error: GLMCC_ISOLATE_CONFIG must be 0 or 1 (got '$ISOLATE_CONFIG')." >&2
    exit 2
    ;;
esac

if [ "$ENDPOINT" = "platform" ]; then
  LEAD_MODEL="$_platform_model"
else
  LEAD_MODEL="$_coding_model"
fi
unset _platform_model _coding_model
BASE_URL="${GLMCC_BASE_URL:-$(default_base_url "$ENDPOINT")}"
BASE_URL="${BASE_URL%/}"

# shellcheck source=scripts/lib/claude_route_guard.sh
source "$PROJECT_DIR/scripts/lib/claude_route_guard.sh"

if [ "$ISOLATE_CONFIG" = "1" ] && [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
  export CLAUDE_CONFIG_DIR="${HOME}/.claude-glmcc"
  mkdir -p "$CLAUDE_CONFIG_DIR"
  echo "Isolated Claude config: $CLAUDE_CONFIG_DIR (original ~/.claude untouched)"
fi

if ! assert_claude_settings_route_clean "GLMCC"; then
  exit 1
fi

if ! resolve_auth_token; then
  echo "Error: no GLM API credential found for the glmcc route." >&2
  echo "  Set ZAI_API_KEY, ZHIPU_API_KEY, GLM_API_KEY, or GLMCC_AUTH_TOKEN" >&2
  echo "  Get API keys at: https://z.ai / https://open.bigmodel.cn" >&2
  exit 1
fi

# shellcheck source=scripts/lib/profile_resolver.sh
source "$PROJECT_DIR/scripts/lib/profile_resolver.sh"
if ! resolve_context_profile "$PROFILE_ID" "$LEAD_MODEL"; then
  echo "Error: could not resolve glmcc profile '$PROFILE_ID' for model '$LEAD_MODEL'." >&2
  exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != "$PROFILE_ID" ]; then
  echo "Error: glmcc profile did not resolve to a trusted contract ($LEARN_UKRAINIAN_RESOLUTION_REASON)." >&2
  exit 1
fi

export LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="$PROFILE_ID"
export LEARN_UKRAINIAN_GLMCC_MANAGED_LAUNCH=1
export LEARN_UKRAINIAN_TRANSPORT=glmcc

# Export Anthropic-compatible routing (process-scoped only).
export API_TIMEOUT_MS="${GLMCC_API_TIMEOUT_MS:-3000000}"
export ANTHROPIC_BASE_URL="$BASE_URL"
unset ANTHROPIC_API_KEY

# Z.AI authentication uses static API keys (NO OAuth helper / apiKeyHelper needed).
export ANTHROPIC_AUTH_TOKEN="$_resolved_auth"
AUTH_NOTE="$AUTH_SOURCE"
unset _resolved_auth

export ANTHROPIC_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_FABLE_MODEL="$LEAD_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$LEAD_MODEL"

# GLM endpoint tool-search support is unverified — conservative default.
export ENABLE_TOOL_SEARCH=false

# Compaction: certified profile capacity (below true window; emergency rollover first).
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"

if [ -n "${GLMCC_EFFORT_LEVEL:-}" ]; then
  export CLAUDE_CODE_EFFORT_LEVEL="$GLMCC_EFFORT_LEVEL"
fi

echo "GLMCC: model=$LEAD_MODEL alias=$MODEL_ALIAS endpoint=$ENDPOINT profile=$PROFILE_ID"
echo "       window=$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS compact=$CLAUDE_CODE_AUTO_COMPACT_WINDOW"
echo "       base=$ANTHROPIC_BASE_URL (env-only; ~/.claude/settings.json not modified)"
echo "       auth=$AUTH_NOTE"
echo "       tip: keep ./start-claude.sh in another terminal for native Anthropic Claude"

_cleaned=()
_prev=""
for arg in "${FORWARD_ARGS[@]+"${FORWARD_ARGS[@]}"}"; do
  if [ "$_prev" = "--model" ]; then
    _prev=""
    continue
  fi
  case "$arg" in
    --model|--model=*)
      echo "Error: GLMCC owns the lead model ($LEAD_MODEL); drop --model from the command line." >&2
      exit 2
      ;;
  esac
  _cleaned+=("$arg")
  _prev="$arg"
done

_has_agent=0
_has_epic=0
for arg in ${_cleaned[@]+"${_cleaned[@]}"}; do
  case "$arg" in
    --agent|--agent=*)
      _has_agent=1
      ;;
    --epic|--epic=*)
      _has_epic=1
      ;;
  esac
done
if [ "$_has_agent" -eq 0 ] && [ "$_has_epic" -eq 0 ] && [ -n "$DEFAULT_AGENT" ]; then
  _cleaned+=(--agent "$DEFAULT_AGENT")
  echo "       agent=$DEFAULT_AGENT (default; override with --agent)"
elif [ "$_has_agent" -eq 0 ] && [ "$_has_epic" -eq 1 ]; then
  echo "       agent=(epic lane set; identity derives from --epic, no default agent)"
fi
unset _has_agent _has_epic

if [ "${GLMCC_DRY_RUN:-0}" = "1" ]; then
  echo "GLMCC_DRY_RUN=1: would exec $PROJECT_DIR/start-claude.sh --model $LEAD_MODEL ${_cleaned[*]+"${_cleaned[*]}"}"
  exit 0
fi

if ((${#_cleaned[@]})); then
  exec "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL" "${_cleaned[@]}"
else
  exec "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL"
fi
