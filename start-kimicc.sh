#!/usr/bin/env bash
# Interactive Claude Code UI routed to Kimi (K3 / K2.7) via Anthropic-compatible API.
#
# This is NOT the native Kimi Code TUI. For headless / native Kimi use:
#   kimi                       # interactive native Kimi Code CLI (OAuth)
#   delegate.py --agent kimi   # headless fleet lane (default)
#   ab ask-kimi                # bridge one-shot
#
# Design (parallel-safe with ./start-claude.sh):
# - Process-scoped env only (Moonshot Method 1). Never writes ~/.claude/settings.json.
# - Original Anthropic Claude config stays untouched; run native Claude in another terminal.
# - Refuses to launch if settings.json already pins route env keys (cc-switch hazard).
# - Compaction comes from scripts/config/context_profiles.yaml (1M for K3, 256K for K2.7).
# - Subscription auth: the `kimi login` OAuth credential (scripts/lib/kimi_coding_oauth.py)
#   is used for --endpoint coding when no API key is set; with --isolate-config an
#   apiKeyHelper is written into the isolated settings.json (never the operator's)
#   so the ~15-min access token is refreshed on Claude Code's schedule.
#
# Official references:
# - https://platform.kimi.ai/docs/guide/claude-code-kimi
# - https://github.com/farion1231/cc-switch  (do NOT use it to rewrite project Claude config)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$PROJECT_DIR"
# Prefer the main worktree root when launched from a git worktree copy, so the
# apiKeyHelper path baked into the isolated Claude config survives worktree
# cleanup (same pattern as start-kimi.sh). Ambient GIT_DIR/GIT_WORK_TREE (e.g.
# from a pre-commit hook) must not leak into these lookups.
if env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _git_common="$(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "${_git_common:-}" ] && [ -d "$(dirname "$_git_common")" ]; then
    _main_wt="$(dirname "$_git_common")"
    if [ -f "$_main_wt/start-kimicc.sh" ]; then
      PROJECT_DIR="$_main_wt"
    fi
  fi
  unset _git_common _main_wt
fi
export PATH="${HOME}/.local/bin:${PATH:-}"
hash -r 2>/dev/null || true

# Default: Kimi Open Platform Anthropic endpoint (pay-as-you-go API key).
# Defaults: Kimi Code subscription endpoint (OAuth via kimi login), isolated
# Claude config (apiKeyHelper auto-refresh), infra-lane agent. The pay-as-you-go
# platform endpoint stays available via --endpoint platform.
ENDPOINT="${KIMICC_ENDPOINT:-coding}"
MODEL_ALIAS="${KIMICC_MODEL:-k3}"
FORWARD_ARGS=()
ISOLATE_CONFIG="${KIMICC_ISOLATE_CONFIG:-1}"
# Default session agent (kimicc is the infra-lane UI). An explicit --agent on
# the command line always wins; set KIMICC_AGENT="" to inherit the project's
# settings.json default (curriculum-orchestrator) instead.
DEFAULT_AGENT="${KIMICC_AGENT-infra-orchestrator}"

usage() {
  cat <<'EOF'
Usage: ./start-kimicc.sh [options] [CLAUDE_ARGS...]

Launch Claude Code with Kimi as the lead model (interactive only).
Does not rewrite ~/.claude/settings.json — original Claude config stays intact.

Options:
  --model ALIAS     k3 (default) | k2.7 | k2.7-highspeed
                    Also accepts full IDs: kimi-k3[1m], kimi-k2.7-code, …
  --endpoint NAME   coding (default; Kimi Code subscription, api.kimi.com/coding)
                    platform (pay-as-you-go, api.moonshot.ai/anthropic)
  --isolate-config  Use CLAUDE_CONFIG_DIR=$HOME/.claude-kimicc (DEFAULT; separate
                    sessions, apiKeyHelper auto-refresh for OAuth)
  --no-isolate-config
                    Use the operator's live ~/.claude config instead
  --agent NAME      Session agent (forwarded to Claude Code). Default:
                    infra-orchestrator when no --epic is given (an epic already
                    implies the lane identity); explicit --agent wins
  -h, --help        Show this help
  -- [CLAUDE_ARGS...]
                    Everything after -- is forwarded verbatim to Claude Code,
                    even args that collide with launcher flags above
                    (e.g. -- --help shows Claude Code's help, not this one).
                    Unrecognized args BEFORE -- are already forwarded too;
                    -- exists for the colliding ones. A forwarded --model is
                    still rejected: KimiCC owns the lead model.

Environment:
  KIMICC_MODEL / KIMICC_ENDPOINT     Defaults for --model / --endpoint
  KIMICC_AGENT                     Default agent (default infra-orchestrator;
                                   empty string = inherit project settings.json default)
  KIMICC_ISOLATE_CONFIG=0          Same as --no-isolate-config
  MOONSHOT_API_KEY / KIMI_API_KEY    Platform API key (preferred for platform)
  KIMICC_AUTH_TOKEN                  Explicit auth token override
  KIMICC_BASE_URL                    Override Anthropic-compatible base URL
  KIMICC_DRY_RUN=1                   Resolve route + auth, print summary, exit before launch
  KIMICC_API_KEY_HELPER_TTL_MS       apiKeyHelper re-invoke interval (default 300000)
  CLAUDE_CONFIG_DIR                  Isolated Claude config directory
  CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1
                                     Bypass settings.json env conflict check (emergency)

Subscription auth (no API key needed):
  Run `kimi login` once. With --endpoint coding the launcher picks up the
  OAuth credential automatically and refreshes it. Access tokens live ~15 min:
  without --isolate-config the token is fixed at launch (short sessions);
  with --isolate-config an apiKeyHelper is installed that auto-refreshes
  (long sessions).

Examples:
  ./start-kimicc.sh
  ./start-kimicc.sh --model k2.7
  ./start-kimicc.sh --model k2.7-highspeed --epic harness
  MOONSHOT_API_KEY=<your-key> ./start-kimicc.sh --model k3
  ./start-kimicc.sh --endpoint coding --isolate-config   # subscription, long session
  ./start-kimicc.sh -- --verbose --help                  # flags for Claude Code itself

Headless / native Kimi (not this launcher):
  scripts/delegate.py dispatch --agent kimi --model k3 …
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-kimi …
EOF
}

default_base_url() {
  case "$1" in
    platform) printf '%s\n' 'https://api.moonshot.ai/anthropic' ;;
    coding) printf '%s\n' 'https://api.kimi.com/coding' ;;
    *) return 1 ;;
  esac
}

# Resolve the auth credential into globals (no command substitution, so
# AUTH_SOURCE survives in the caller's shell).
_resolved_auth=""
AUTH_SOURCE=""
resolve_auth_token() {
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
  if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ] && [ "${ENDPOINT}" = "coding" ]; then
    # Allow an already-exported coding token when operator sets it intentionally.
    _resolved_auth="$ANTHROPIC_AUTH_TOKEN"
    AUTH_SOURCE="ANTHROPIC_AUTH_TOKEN"
    return 0
  fi
  return 1
}

while (($#)); do
  case "$1" in
    --)
      # Explicit passthrough: forward the rest verbatim (still subject to the
      # forwarded --model rejection below — KimiCC owns the lead model).
      shift
      while (($#)); do
        FORWARD_ARGS+=("$1")
        shift
      done
      ;;
    --model)
      if (($# < 2)); then
        echo "Error: --model requires k3, k2.7, or k2.7-highspeed." >&2
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
        echo "Error: --endpoint requires platform or coding." >&2
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

if ! _kimicc_route="$("$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/scripts/review/model_catalog.py" \
    --resolve-kimi-model "$MODEL_ALIAS" --format kimicc 2>/dev/null)"; then
  echo "Error: unsupported model '$MODEL_ALIAS' (use k3, k2.7, k2.7-highspeed)." >&2
  exit 2
fi
IFS=$'\t' read -r MODEL_ALIAS _platform_model _coding_model PROFILE_ID <<< "$_kimicc_route"
if [ -z "$MODEL_ALIAS" ] || [ -z "$_platform_model" ] || [ -z "$_coding_model" ] || [ -z "$PROFILE_ID" ]; then
  echo "Error: invalid Kimi route in scripts/config/model_catalog.yaml." >&2
  exit 1
fi
unset _kimicc_route

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
    echo "Error: KIMICC_ISOLATE_CONFIG must be 0 or 1 (got '$ISOLATE_CONFIG')." >&2
    exit 2
    ;;
esac

if [ "$ENDPOINT" = "platform" ]; then
  LEAD_MODEL="$_platform_model"
else
  LEAD_MODEL="$_coding_model"
fi
unset _platform_model _coding_model
BASE_URL="${KIMICC_BASE_URL:-$(default_base_url "$ENDPOINT")}"
BASE_URL="${BASE_URL%/}"

# shellcheck source=scripts/lib/claude_route_guard.sh
source "$PROJECT_DIR/scripts/lib/claude_route_guard.sh"

if [ "$ISOLATE_CONFIG" = "1" ] && [ -z "${CLAUDE_CONFIG_DIR:-}" ]; then
  export CLAUDE_CONFIG_DIR="${HOME}/.claude-kimicc"
  mkdir -p "$CLAUDE_CONFIG_DIR"
  echo "Isolated Claude config: $CLAUDE_CONFIG_DIR (original ~/.claude untouched)"
fi

if ! assert_claude_settings_route_clean "KimiCC"; then
  exit 1
fi

# Explicit credentials win. For --endpoint coding, fall back to the
# `kimi login` OAuth credential (subscription route): the helper prints a
# fresh access token, refreshing it via the refresh_token grant when needed.
KIMI_OAUTH_PY="$PROJECT_DIR/.venv/bin/python"
KIMI_OAUTH_HELPER="$PROJECT_DIR/scripts/lib/kimi_coding_oauth.py"
AUTH_VIA_OAUTH=0
if ! resolve_auth_token; then
  if [ "$ENDPOINT" = "coding" ] && [ -f "$KIMI_OAUTH_HELPER" ] && [ -x "$KIMI_OAUTH_PY" ]; then
    if _resolved_auth="$("$KIMI_OAUTH_PY" "$KIMI_OAUTH_HELPER" token 2>/dev/null)" \
        && [ -n "$_resolved_auth" ]; then
      AUTH_VIA_OAUTH=1
      AUTH_SOURCE="oauth(kimi login)"
    fi
  fi
fi
if [ -z "$_resolved_auth" ]; then
  echo "Error: no Kimi API credential found for the kimicc route." >&2
  echo "  Platform (pay-as-you-go): set MOONSHOT_API_KEY, KIMI_API_KEY, or KIMICC_AUTH_TOKEN" >&2
  echo "  Platform keys: https://platform.kimi.ai/console/api-keys" >&2
  echo "  Subscription: run \`kimi login\`, then use --endpoint coding (OAuth is picked up automatically)." >&2
  exit 1
fi

# shellcheck source=scripts/lib/profile_resolver.sh
source "$PROJECT_DIR/scripts/lib/profile_resolver.sh"
if ! resolve_context_profile "$PROFILE_ID" "$LEAD_MODEL"; then
  echo "Error: could not resolve kimicc profile '$PROFILE_ID' for model '$LEAD_MODEL'." >&2
  exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != "$PROFILE_ID" ]; then
  echo "Error: kimicc profile did not resolve to a trusted contract ($LEARN_UKRAINIAN_RESOLUTION_REASON)." >&2
  exit 1
fi

export LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="$PROFILE_ID"
export LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH=1
export LEARN_UKRAINIAN_TRANSPORT=kimicc

# Moonshot Anthropic-compatible routing (process-scoped only).
export ANTHROPIC_BASE_URL="$BASE_URL"
unset ANTHROPIC_API_KEY

# OAuth (`kimi login`) access tokens expire after ~15 minutes. With an
# isolated config we install an apiKeyHelper that re-mints the token on Claude
# Code's schedule (long-session mode); without isolation the current token can
# only be exported into the process env, which is fixed at launch.
if [ "$AUTH_VIA_OAUTH" = "1" ] && [ "$ISOLATE_CONFIG" = "1" ]; then
  _helper_cmd="$KIMI_OAUTH_PY $KIMI_OAUTH_HELPER token"
  if ! KIMICC_SETTINGS_PATH="$CLAUDE_CONFIG_DIR/settings.json" KIMICC_API_KEY_HELPER="$_helper_cmd" \
      "$KIMI_OAUTH_PY" - <<'PY'
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
    echo "Error: could not install apiKeyHelper into $CLAUDE_CONFIG_DIR/settings.json" >&2
    exit 1
  fi
  unset _helper_cmd
  # Re-invoke the helper well inside the ~15 min token lifetime.
  export CLAUDE_CODE_API_KEY_HELPER_TTL_MS="${KIMICC_API_KEY_HELPER_TTL_MS:-300000}"
  unset ANTHROPIC_AUTH_TOKEN
  AUTH_NOTE="oauth(kimi login) via apiKeyHelper (auto-refresh, ttl=${CLAUDE_CODE_API_KEY_HELPER_TTL_MS}ms)"
else
  export ANTHROPIC_AUTH_TOKEN="$_resolved_auth"
  if [ "$AUTH_VIA_OAUTH" = "1" ]; then
    AUTH_NOTE="oauth(kimi login) — short-lived token (~15 min); for long sessions relaunch with --isolate-config"
  else
    AUTH_NOTE="$AUTH_SOURCE"
  fi
fi
unset _resolved_auth

export ANTHROPIC_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$LEAD_MODEL"
export ANTHROPIC_DEFAULT_FABLE_MODEL="$LEAD_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$LEAD_MODEL"

# Kimi endpoint does not support Claude Code tool-search yet (official guide).
export ENABLE_TOOL_SEARCH=false

# Compaction: certified profile capacity (below true window; emergency rollover first).
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"

# K3 defaults to max effort on the platform guide; k2.7 always-thinks (Tab thinking in UI).
if [ "$MODEL_ALIAS" = "k3" ]; then
  export CLAUDE_CODE_EFFORT_LEVEL="${KIMICC_EFFORT_LEVEL:-max}"
else
  # Leave effort unset for k2.7 unless operator overrides; thinking must stay on in the TUI.
  if [ -n "${KIMICC_EFFORT_LEVEL:-}" ]; then
    export CLAUDE_CODE_EFFORT_LEVEL="$KIMICC_EFFORT_LEVEL"
  fi
fi

echo "KimiCC: model=$LEAD_MODEL alias=$MODEL_ALIAS endpoint=$ENDPOINT profile=$PROFILE_ID"
echo "        window=$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS compact=$CLAUDE_CODE_AUTO_COMPACT_WINDOW"
echo "        base=$ANTHROPIC_BASE_URL (env-only; ~/.claude/settings.json not modified)"
echo "        auth=$AUTH_NOTE"
echo "        tip: keep ./start-claude.sh in another terminal for native Anthropic Claude"
if [ "$MODEL_ALIAS" != "k3" ]; then
  echo "        note: k2.7 requires Thinking ON in the TUI (Tab) or requests are rejected"
fi

# Strip any ambient --model from forwarded args; lead model is owned by this launcher.
_cleaned=()
_prev=""
for arg in "${FORWARD_ARGS[@]+"${FORWARD_ARGS[@]}"}"; do
  if [ "$_prev" = "--model" ]; then
    _prev=""
    continue
  fi
  case "$arg" in
    --model|--model=*)
      echo "Error: KimiCC owns the lead model ($LEAD_MODEL); drop --model from the command line." >&2
      exit 2
      ;;
  esac
  _cleaned+=("$arg")
  _prev="$arg"
done

# Default the session agent to the infra lane (kimicc is the infra UI), but
# only when no epic lane is pinned: an epic already implies the lane identity,
# and an infra persona on e.g. the atlas lane would be a mismatch. An explicit
# --agent on the command line always wins.
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
  echo "        agent=$DEFAULT_AGENT (default; override with --agent)"
elif [ "$_has_agent" -eq 0 ] && [ "$_has_epic" -eq 1 ]; then
  echo "        agent=(epic lane set; identity derives from --epic, no default agent)"
fi
unset _has_agent _has_epic

if [ "${KIMICC_DRY_RUN:-0}" = "1" ]; then
  echo "KIMICC_DRY_RUN=1: would exec $PROJECT_DIR/start-claude.sh --model $LEAD_MODEL ${_cleaned[*]+"${_cleaned[*]}"}"
  exit 0
fi

if ((${#_cleaned[@]})); then
  exec "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL" "${_cleaned[@]}"
else
  exec "$PROJECT_DIR/start-claude.sh" --model "$LEAD_MODEL"
fi
