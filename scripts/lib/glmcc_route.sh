#!/usr/bin/env bash
# GLM Claude-Code route. It accepts only explicitly named GLM credentials.

glmcc_default_base_url() {
  case "$1" in
    coding|platform) printf '%s\n' 'https://api.z.ai/api/anthropic' ;;
    *) return 1 ;;
  esac
}

glmcc_resolve_explicit_auth_token() {
  _glmcc_auth=''
  GLMCC_AUTH_SOURCE=''
  if [ -n "${GLMCC_AUTH_TOKEN:-}" ]; then _glmcc_auth="$GLMCC_AUTH_TOKEN"; GLMCC_AUTH_SOURCE=GLMCC_AUTH_TOKEN
  elif [ -n "${ZAI_API_KEY:-}" ]; then _glmcc_auth="$ZAI_API_KEY"; GLMCC_AUTH_SOURCE=ZAI_API_KEY
  elif [ -n "${ZHIPU_API_KEY:-}" ]; then _glmcc_auth="$ZHIPU_API_KEY"; GLMCC_AUTH_SOURCE=ZHIPU_API_KEY
  elif [ -n "${GLM_API_KEY:-}" ]; then _glmcc_auth="$GLM_API_KEY"; GLMCC_AUTH_SOURCE=GLM_API_KEY
  else return 1
  fi
}

glmcc_configure_route() {
  local project_dir="$1" route platform_model coding_model profile default_base
  if ! route="$("$project_dir/.venv/bin/python" "$project_dir/scripts/review/model_catalog.py" --resolve-glm-model "$MODEL_ALIAS" --format glmcc 2>/dev/null)"; then
    echo "Error: unsupported GLM model '$MODEL_ALIAS' (use glm-5.2)." >&2
    return 2
  fi
  IFS=$'\t' read -r MODEL_ALIAS platform_model coding_model profile <<EOF
$route
EOF
  case "$ENDPOINT" in coding|platform) ;; *) echo "Error: unsupported endpoint '$ENDPOINT' (use coding or platform)." >&2; return 2 ;; esac
  case "$ISOLATE_CONFIG" in 0|1) ;; *) echo "Error: LAUNCHER_ISOLATE_CONFIG must be 0 or 1 (got '$ISOLATE_CONFIG')." >&2; return 2 ;; esac
  if [ "$ENDPOINT" = platform ]; then LEAD_MODEL="$platform_model"; else LEAD_MODEL="$coding_model"; fi
  default_base="$(glmcc_default_base_url "$ENDPOINT")"
  BASE_URL="${GLMCC_BASE_URL:-$default_base}"
  BASE_URL="${BASE_URL%/}"
  if [ "$BASE_URL" != "$default_base" ]; then
    echo 'Error: GLMCC_BASE_URL override is not an approved endpoint.' >&2
    return 2
  fi
  if ! glmcc_resolve_explicit_auth_token; then
    echo 'Error: no explicit GLM credential found (set GLMCC_AUTH_TOKEN, ZAI_API_KEY, ZHIPU_API_KEY, or GLM_API_KEY).' >&2
    return 3
  fi

  # An alternate Claude route must not inherit operator-owned route pins from
  # the live config. Isolation makes a disposable config explicit; otherwise
  # fail closed rather than silently allowing settings.json to override this
  # process-scoped allowlisted route.
  # shellcheck source=scripts/lib/claude_route_guard.sh
  source "$project_dir/scripts/lib/claude_route_guard.sh"
  CLAUDE_ROUTE_GUARD_PYTHON="$project_dir/.venv/bin/python"
  export CLAUDE_ROUTE_GUARD_PYTHON
  if [ "$ISOLATE_CONFIG" = 1 ] && [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
    export CLAUDE_CONFIG_DIR="$HOME/.claude-glmcc"
    mkdir -p "$CLAUDE_CONFIG_DIR"
  fi
  if ! assert_claude_settings_route_clean "GLM"; then
    return 1
  fi

  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$project_dir/scripts/lib/profile_resolver.sh"
  CLAUDE_PROFILE_RESOLVER_PYTHON="$project_dir/.venv/bin/python"
  export CLAUDE_PROFILE_RESOLVER_PYTHON
  if ! resolve_context_profile "$profile" "$LEAD_MODEL"; then
    echo "Error: could not resolve GLM profile '$profile' for model '$LEAD_MODEL'." >&2
    return 1
  fi
  if [ "$LEARN_UKRAINIAN_TRUSTED" != 1 ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != "$profile" ]; then
    echo "Error: GLM profile did not resolve to a trusted contract ($LEARN_UKRAINIAN_RESOLUTION_REASON)." >&2
    return 1
  fi
  export LEARN_UKRAINIAN_TRANSPORT=glmcc
  export LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="$profile"
  export API_TIMEOUT_MS="${GLMCC_API_TIMEOUT_MS:-3000000}"
  export ANTHROPIC_BASE_URL="$BASE_URL"
  export ANTHROPIC_AUTH_TOKEN="$_glmcc_auth"
  unset ANTHROPIC_API_KEY _glmcc_auth
  export ANTHROPIC_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_FABLE_MODEL="$LEAD_MODEL"
  export CLAUDE_CODE_SUBAGENT_MODEL="$LEAD_MODEL"
  export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
  export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"
  export ENABLE_TOOL_SEARCH=false
  export GLMCC_AUTH_SOURCE
}
