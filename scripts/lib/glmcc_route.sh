#!/usr/bin/env bash
# GLM Claude-Code route. Accepts only explicitly named GLM credentials or the
# owner-only file ~/.secret/zai.key. Ambient ANTHROPIC_AUTH_TOKEN is rejected.
#
# Isolation contract:
# - Process-scoped env only (never writes ~/.claude/settings.json).
# - File-backed keys are loaded into a local then moved to ANTHROPIC_AUTH_TOKEN;
#   they are never exported as ZAI_API_KEY and never printed.
# - Default CLAUDE_CONFIG_DIR=$HOME/.claude-glmcc keeps native Claude untouched.

glmcc_default_base_url() {
  case "$1" in
    coding|platform) printf '%s\n' 'https://api.z.ai/api/anthropic' ;;
    *) return 1 ;;
  esac
}

glmcc_route_python() {
  local project_dir="$1"
  local git_common

  if [ -n "${GLMCC_ROUTE_PYTHON:-}" ] && [ -x "${GLMCC_ROUTE_PYTHON}" ]; then
    printf '%s\n' "$GLMCC_ROUTE_PYTHON"
    return 0
  fi
  if [ -x "$project_dir/.venv/bin/python" ]; then
    printf '%s\n' "$project_dir/.venv/bin/python"
    return 0
  fi
  git_common="$(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR \
    git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$git_common" ] && [ -x "$(dirname "$git_common")/.venv/bin/python" ]; then
    printf '%s\n' "$(dirname "$git_common")/.venv/bin/python"
    return 0
  fi
  return 1
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

# Load ~/.secret/zai.key (or GLMCC_SECRET_FILE) via the audited credential
# helper. The value stays in _glmcc_auth only — never exported under a ZAI_*
# name — so a later `env` dump does not reveal a file-sourced key twice.
glmcc_load_secret_file_auth() {
  local project_dir="$1"
  local python_bin secret_path display_path

  secret_path="${GLMCC_SECRET_FILE:-$HOME/.secret/zai.key}"
  if [ ! -e "$secret_path" ]; then
    return 1
  fi
  if ! python_bin="$(glmcc_route_python "$project_dir")"; then
    echo 'Error: Python binary not found to load the GLM credential file.' >&2
    return 1
  fi
  display_path="$secret_path"
  # Intentional: credential_source shows a home-relative display path with a
  # literal tilde prefix (not an expandable assignment). SC2088 does not apply.
  # shellcheck disable=SC2088
  case "$display_path" in
    "$HOME"/*) display_path="~/${display_path#"$HOME"/}" ;;
  esac

  # load_credential errors include the path only — never the secret contents.
  # stdout is captured into the local holder; stderr stays on the tty.
  # The key is never placed on argv or exported as ZAI_*.
  if ! _glmcc_auth="$(
    LEARN_UKRAINIAN_ROOT="$project_dir" GLMCC_SECRET_PATH="$secret_path" \
      "$python_bin" - <<'PY'
import os
import sys
from pathlib import Path

root = Path(os.environ["LEARN_UKRAINIAN_ROOT"]).resolve()
sys.path.insert(0, str(root))
from scripts.ocr._credentials import CredentialError, load_credential

try:
    sys.stdout.write(load_credential(os.environ["GLMCC_SECRET_PATH"]))
except CredentialError as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)
PY
  )" || [ -z "${_glmcc_auth:-}" ]; then
    echo "Error: could not load GLM credential from $display_path." >&2
    return 1
  fi
  GLMCC_AUTH_SOURCE="file:$display_path"
  return 0
}

glmcc_configure_route() {
  local project_dir="$1" route platform_model coding_model profile default_base python_bin
  if ! python_bin="$(glmcc_route_python "$project_dir")"; then
    echo 'Error: Python binary not found for the GLM Claude-Code route.' >&2
    return 1
  fi
  if ! route="$("$python_bin" "$project_dir/scripts/review/model_catalog.py" --resolve-glm-model "$MODEL_ALIAS" --format glmcc 2>/dev/null)"; then
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
    if ! glmcc_load_secret_file_auth "$project_dir"; then
      echo 'Error: no explicit GLM credential found.' >&2
      echo '  Set GLMCC_AUTH_TOKEN, ZAI_API_KEY, ZHIPU_API_KEY, or GLM_API_KEY,' >&2
      echo '  or install owner-only ~/.secret/zai.key (mode 0600/0400).' >&2
      echo '  Ambient ANTHROPIC_AUTH_TOKEN is deliberately rejected.' >&2
      return 3
    fi
  fi

  # An alternate Claude route must not inherit operator-owned route pins from
  # the live config. Isolation makes a disposable config explicit; otherwise
  # fail closed rather than silently allowing settings.json to override this
  # process-scoped allowlisted route.
  # shellcheck source=scripts/lib/claude_route_guard.sh
  source "$project_dir/scripts/lib/claude_route_guard.sh"
  CLAUDE_ROUTE_GUARD_PYTHON="$python_bin"
  export CLAUDE_ROUTE_GUARD_PYTHON
  if [ "$ISOLATE_CONFIG" = 1 ] && [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
    export CLAUDE_CONFIG_DIR="$HOME/.claude-glmcc"
    mkdir -p "$CLAUDE_CONFIG_DIR"
  fi
  if ! assert_claude_settings_route_clean "GLM" "$project_dir"; then
    return 1
  fi

  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$project_dir/scripts/lib/profile_resolver.sh"
  CLAUDE_PROFILE_RESOLVER_PYTHON="$python_bin"
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
  # Drop the transient holder and any inherited Anthropic API key. File-sourced
  # keys were never exported as ZAI_*; env-sourced ZAI_*/GLM_* names stay as the
  # operator set them, but the Claude route itself only sees ANTHROPIC_*.
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
