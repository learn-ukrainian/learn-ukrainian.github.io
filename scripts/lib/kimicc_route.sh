#!/usr/bin/env bash
# Shared KimiCC route resolution for the interactive launcher and headless runtime.
#
# Inputs are the caller-owned ENDPOINT, MODEL_ALIAS, and ISOLATE_CONFIG globals.
# On success this function exports the Claude Code route environment and leaves
# the resolved, non-secret route metadata in globals consumed by the caller:
# LEAD_MODEL, PROFILE_ID, BASE_URL, AUTH_SOURCE, AUTH_VIA_OAUTH, and AUTH_NOTE.
#
# KIMICC_HEADLESS=1 deliberately disables the interactive apiKeyHelper path.
# Headless Claude Code uses --bare, so it resolves a fresh OAuth token at spawn
# and must be relaunched for calls longer than the roughly 15-minute token life.

kimicc_default_base_url() {
  case "$1" in
    platform) printf '%s\n' 'https://api.moonshot.ai/anthropic' ;;
    coding) printf '%s\n' 'https://api.kimi.com/coding' ;;
    *) return 1 ;;
  esac
}

# Resolve an explicit auth input into globals without command substitution so
# AUTH_SOURCE survives in the sourcing shell. OAuth is handled by the caller.
kimicc_resolve_explicit_auth_token() {
  _resolved_auth=""
  AUTH_SOURCE=""
  if [ -n "${KIMICC_AUTH_TOKEN:-}" ]; then
    _resolved_auth="$KIMICC_AUTH_TOKEN"
    AUTH_SOURCE="KIMICC_AUTH_TOKEN"
    return 0
  fi
  if [ -n "${MOONSHOT_API_KEY:-}" ]; then
    _resolved_auth="$MOONSHOT_API_KEY"
    AUTH_SOURCE="MOONSHOT_API_KEY"
    return 0
  fi
  if [ -n "${KIMI_API_KEY:-}" ]; then
    _resolved_auth="$KIMI_API_KEY"
    AUTH_SOURCE="KIMI_API_KEY"
    return 0
  fi
  # Deliberately do not fall back to ANTHROPIC_AUTH_TOKEN. An Anthropic-named
  # ambient credential is foreign to Kimi even when the coding endpoint is
  # selected; callers must supply a Kimi credential or use Kimi OAuth.
  return 1
}

kimicc_route_python() {
  local project_dir="$1"
  local git_common

  if [ -n "${KIMICC_ROUTE_PYTHON:-}" ] && [ -x "${KIMICC_ROUTE_PYTHON}" ]; then
    printf '%s\n' "$KIMICC_ROUTE_PYTHON"
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

kimicc_install_api_key_helper() {
  local python_bin="$1"
  local oauth_helper="$2"
  local helper_cmd settings_path

  helper_cmd="$python_bin $oauth_helper token"
  settings_path="$CLAUDE_CONFIG_DIR/settings.json"
  if ! KIMICC_SETTINGS_PATH="$settings_path" KIMICC_API_KEY_HELPER="$helper_cmd" \
      "$python_bin" - <<'PY'
import json
import os
import sys

path = os.environ["KIMICC_SETTINGS_PATH"]
helper = os.environ["KIMICC_API_KEY_HELPER"]
data = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"Error: {path} is not valid JSON ({exc}); refusing to modify it.", file=sys.stderr)
            sys.exit(1)
    if not isinstance(data, dict):
        print(f"Error: {path} is not a JSON object; refusing to modify it.", file=sys.stderr)
        sys.exit(1)
data["apiKeyHelper"] = helper
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
PY
  then
    echo "Error: could not install apiKeyHelper into $settings_path" >&2
    return 1
  fi
}

# Configure an Anthropic-compatible Kimi route in this shell.
#
# Args:
#   $1 project root that owns the route helper and profiles.
#   $2 optional catalog root (interactive worktree launchers preserve their
#      historical behavior by resolving the catalog from their own script dir).
kimicc_configure_route() {
  local project_dir="$1"
  local catalog_dir="${2:-$project_dir}"
  local durable_helper_dir="${3:-$project_dir}"
  local python_bin oauth_helper route platform_model coding_model default_base_url

  if ! python_bin="$(kimicc_route_python "$catalog_dir")"; then
    echo "Error: Python binary not found for the KimiCC route." >&2
    return 1
  fi
  if ! route="$("$python_bin" "$catalog_dir/scripts/review/model_catalog.py" \
      --resolve-kimi-model "$MODEL_ALIAS" --format kimicc 2>/dev/null)"; then
    echo "Error: unsupported model '$MODEL_ALIAS' (use k3, k2.7, k2.7-highspeed)." >&2
    return 2
  fi
  IFS=$'\t' read -r MODEL_ALIAS platform_model coding_model PROFILE_ID <<< "$route"
  if [ -z "$MODEL_ALIAS" ] || [ -z "$platform_model" ] || [ -z "$coding_model" ] || [ -z "$PROFILE_ID" ]; then
    echo "Error: invalid Kimi route in scripts/config/model_catalog.yaml." >&2
    return 1
  fi

  case "$ENDPOINT" in
    platform|coding) ;;
    *)
      echo "Error: unsupported endpoint '$ENDPOINT' (use platform or coding)." >&2
      return 2
      ;;
  esac
  case "$ISOLATE_CONFIG" in
    0|1) ;;
    *)
      echo "Error: KIMICC_ISOLATE_CONFIG must be 0 or 1 (got '$ISOLATE_CONFIG')." >&2
      return 2
      ;;
  esac

  if [ "$ENDPOINT" = "platform" ]; then
    LEAD_MODEL="$platform_model"
  else
    LEAD_MODEL="$coding_model"
  fi
  default_base_url="$(kimicc_default_base_url "$ENDPOINT")"
  BASE_URL="${KIMICC_BASE_URL:-$default_base_url}"
  BASE_URL="${BASE_URL%/}"
  if [ "$BASE_URL" != "$default_base_url" ]; then
    echo "Error: KIMICC_BASE_URL override is not an approved endpoint." >&2
    return 2
  fi

  # shellcheck source=scripts/lib/claude_route_guard.sh
  source "$project_dir/scripts/lib/claude_route_guard.sh"
  CLAUDE_ROUTE_GUARD_PYTHON="$python_bin"
  export CLAUDE_ROUTE_GUARD_PYTHON
  if [ "$ISOLATE_CONFIG" = "1" ] && [ "${KIMICC_HEADLESS:-0}" != "1" ] && [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
    export CLAUDE_CONFIG_DIR="${HOME}/.claude-kimicc"
    mkdir -p "$CLAUDE_CONFIG_DIR"
    echo "Isolated Claude config: $CLAUDE_CONFIG_DIR (original ~/.claude untouched)"
  fi
  if ! assert_claude_settings_route_clean "KimiCC" "$project_dir"; then
    return 1
  fi

  # Catalog/session resolution stays on the invoked worktree. Only Kimi's
  # OAuth helper can be durable, so isolated apiKeyHelper paths survive a
  # short-lived dispatch worktree without making the session itself durable.
  oauth_helper="$durable_helper_dir/scripts/lib/kimi_coding_oauth.py"
  AUTH_VIA_OAUTH=0
  if ! kimicc_resolve_explicit_auth_token; then
    if [ "$ENDPOINT" = "coding" ] && [ -f "$oauth_helper" ] && [ -x "$python_bin" ]; then
      if _resolved_auth="$("$python_bin" "$oauth_helper" token 2>/dev/null)" && [ -n "$_resolved_auth" ]; then
        AUTH_VIA_OAUTH=1
        AUTH_SOURCE="oauth(kimi login)"
      fi
    fi
  fi
  if [ -z "$_resolved_auth" ]; then
    if [ "${KIMICC_DRY_RUN:-0}" = "1" ]; then
      AUTH_NOTE="UNSET (dry-run only)"
    else
      echo "Error: no Kimi API credential found for the kimicc route." >&2
      echo "  Platform (pay-as-you-go): set MOONSHOT_API_KEY, KIMI_API_KEY, or KIMICC_AUTH_TOKEN" >&2
      echo "  Platform keys: https://platform.kimi.ai/console/api-keys" >&2
      echo "  Subscription: run \`kimi login\`, then use --endpoint coding (OAuth is picked up automatically)." >&2
      return 3
    fi
  fi

  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$project_dir/scripts/lib/profile_resolver.sh"
  CLAUDE_PROFILE_RESOLVER_PYTHON="$python_bin"
  export CLAUDE_PROFILE_RESOLVER_PYTHON
  if ! resolve_context_profile "$PROFILE_ID" "$LEAD_MODEL"; then
    echo "Error: could not resolve kimicc profile '$PROFILE_ID' for model '$LEAD_MODEL'." >&2
    return 1
  fi
  if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != "$PROFILE_ID" ]; then
    echo "Error: kimicc profile did not resolve to a trusted contract ($LEARN_UKRAINIAN_RESOLUTION_REASON)." >&2
    return 1
  fi

  export LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="$PROFILE_ID"
  export LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH=1
  export LEARN_UKRAINIAN_TRANSPORT=kimicc
  export ANTHROPIC_BASE_URL="$BASE_URL"
  unset ANTHROPIC_API_KEY

  if [ -n "$_resolved_auth" ]; then
    if [ "$AUTH_VIA_OAUTH" = "1" ] && [ "$ISOLATE_CONFIG" = "1" ] && [ "${KIMICC_HEADLESS:-0}" != "1" ]; then
      if ! kimicc_install_api_key_helper "$python_bin" "$oauth_helper"; then
        return 1
      fi
      export CLAUDE_CODE_API_KEY_HELPER_TTL_MS="${KIMICC_API_KEY_HELPER_TTL_MS:-300000}"
      unset ANTHROPIC_AUTH_TOKEN
      AUTH_NOTE="oauth(kimi login) via apiKeyHelper (auto-refresh, ttl=${CLAUDE_CODE_API_KEY_HELPER_TTL_MS}ms)"
    else
      export ANTHROPIC_AUTH_TOKEN="$_resolved_auth"
      if [ "$AUTH_VIA_OAUTH" = "1" ]; then
        if [ "${KIMICC_HEADLESS:-0}" = "1" ]; then
          AUTH_NOTE="oauth(kimi login) — fresh token exported at headless spawn; relaunch before ~15 min"
        else
          AUTH_NOTE="oauth(kimi login) — short-lived token (~15 min); for long sessions relaunch with --isolate-config"
        fi
      else
        AUTH_NOTE="$AUTH_SOURCE"
      fi
    fi
  fi
  unset _resolved_auth

  export ANTHROPIC_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="$LEAD_MODEL"
  export ANTHROPIC_DEFAULT_FABLE_MODEL="$LEAD_MODEL"
  export CLAUDE_CODE_SUBAGENT_MODEL="$LEAD_MODEL"
  export ENABLE_TOOL_SEARCH=false
  export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
  export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"

  if [ "$MODEL_ALIAS" = "k3" ]; then
    export CLAUDE_CODE_EFFORT_LEVEL="${KIMICC_EFFORT_LEVEL:-max}"
  elif [ -n "${KIMICC_EFFORT_LEVEL:-}" ]; then
    export CLAUDE_CODE_EFFORT_LEVEL="$KIMICC_EFFORT_LEVEL"
  fi
  # The interactive launcher reads this non-secret resolution note after the
  # helper returns; exporting also makes the shared helper's contract explicit.
  export AUTH_NOTE
}
