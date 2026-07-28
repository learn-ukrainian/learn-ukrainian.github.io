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
_LU_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$_LU_ROOT/scripts/lib/scrub_hermes_node_path.sh" ]; then
  # shellcheck source=scripts/lib/scrub_hermes_node_path.sh
  source "$_LU_ROOT/scripts/lib/scrub_hermes_node_path.sh"
  scrub_hermes_node_from_path
fi
unset _LU_ROOT
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

# shellcheck source=scripts/lib/kimicc_route.sh
source "$SCRIPT_DIR/scripts/lib/kimicc_route.sh"
KIMICC_ROUTE_PYTHON="$SCRIPT_DIR/.venv/bin/python"
export KIMICC_ROUTE_PYTHON
if kimicc_configure_route "$PROJECT_DIR" "$SCRIPT_DIR"; then
  unset KIMICC_ROUTE_PYTHON
else
  _kimicc_route_rc=$?
  unset KIMICC_ROUTE_PYTHON
  exit "$_kimicc_route_rc"
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
