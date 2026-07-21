#!/usr/bin/env bash
# Learn Ukrainian — Kimi Code CLI launcher (peer of start-grok.sh).
#
# Launcher-only flags (the kimi CLI does not know them):
#   --epic <name> | --epic=<name>     Pin lane (atlas, hramatka, harness, …)
#   --stream <id> | --stream=<id>     Explicit session-stream id (e.g. epic:4387)
#   --handoff-agent <id>              Override SESSION_HANDOFF_AGENT
#   --model <id>                      Kimi model (default: k2.7-coding)
#   --help-launcher                   This help (does not start kimi)
#
# Environment exported for hooks / dual-write / session streams:
#   SESSION_EPIC              from --epic
#   SESSION_HANDOFF_AGENT     kimi-<epic> (or override / harness→kimi-infra)
#   SESSION_STREAM_*          from the common session supervisor (scripts.session_supervisor)
#   LEARN_UKRAINE_KIMI_LAUNCH=1
#
# Cold-start: with --epic and no free-text PROMPT, the launcher claims the
# stream lease through the common supervisor, writes a capsule, and injects an
# auto-continue prompt. Pass an explicit PROMPT to override.
#
# Examples:
#   ./start-kimi.sh --epic atlas
#   ./start-kimi.sh --epic atlas --stream epic:4387 --model k3
#   ./start-kimi.sh --epic harness "continue the infra queue"
#   ./start-kimi.sh --model k2.7-coding "review the open PR"

set -euo pipefail

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:${HOME}/.kimi-code/bin:${PATH:-}"
hash -r 2>/dev/null || true

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the main worktree root when this script is run from a git worktree copy.
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _git_common="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "${_git_common:-}" ] && [ -d "$(dirname "$_git_common")" ]; then
    _main_wt="$(dirname "$_git_common")"
    if [ -f "$_main_wt/start-kimi.sh" ] || [ -f "$_main_wt/AGENTS.md" ]; then
      PROJECT_DIR="$_main_wt"
    fi
  fi
  unset _git_common _main_wt
fi

usage_launcher() {
  sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# --- locate kimi binary ---
KIMI_BIN="${LEARN_UK_KIMI_BIN:-}"
if [ -z "$KIMI_BIN" ] || [ ! -x "$KIMI_BIN" ]; then
  KIMI_BIN=""
  for cand in \
    "$(command -v kimi 2>/dev/null || true)" \
    "${HOME}/.kimi-code/bin/kimi"
  do
    if [ -n "$cand" ] && [ -x "$cand" ]; then
      KIMI_BIN="$cand"
      break
    fi
  done
fi
if [ -z "$KIMI_BIN" ]; then
  echo "Error: Kimi Code CLI not found. Install it or set LEARN_UK_KIMI_BIN." >&2
  exit 1
fi

echo "Starting Kimi Code in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"
echo "Kimi: $("$KIMI_BIN" --version 2>/dev/null || echo "$KIMI_BIN")"

cd "$PROJECT_DIR"

if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Current branch: $(git branch --show-current 2>/dev/null || echo '?')"
  # Heal detached/wrong-branch primary so agents never start on a raw SHA (#4857).
  if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
      && [ -f "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" ]; then
    if ! "$PROJECT_DIR/.venv/bin/python" \
        "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" \
        --cwd "$PROJECT_DIR" --heal; then
      echo "Error: primary checkout is not on main and auto-heal failed." >&2
      exit 1
    fi
  fi
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "Uncommitted changes detected (primary checkout is orientation-only; write via worktrees)"
  fi
fi

# Optional deploy of shared extensions (fail-open).
if [ -f "$PROJECT_DIR/scripts/lib/deploy_extensions.sh" ]; then
  # shellcheck source=scripts/lib/deploy_extensions.sh
  source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
  deploy_agent_extensions "$PROJECT_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure (see banner above)."
fi

# --- parse launcher-only flags; build forward argv and prompt ---
_forward=()
_selected_epic=""
_selected_stream=""
_handoff_override=""
_selected_model=""
_has_model=0
_prev=""

for arg in "$@"; do
  if [ "$_prev" = "--epic" ]; then
    _selected_epic="${arg%.epic}"
    _prev=""
    continue
  fi
  if [ "$_prev" = "--stream" ]; then
    _selected_stream="$arg"
    _prev=""
    continue
  fi
  if [ "$_prev" = "--handoff-agent" ]; then
    _handoff_override="$arg"
    _prev=""
    continue
  fi
  if [ "$_prev" = "--model" ]; then
    _selected_model="$arg"
    _has_model=1
    _prev=""
    continue
  fi

  case "$arg" in
    --help-launcher|-hl)
      usage_launcher
      ;;
    --epic)
      _prev=--epic
      continue
      ;;
    --epic=*)
      _selected_epic="${arg#--epic=}"
      _selected_epic="${_selected_epic%.epic}"
      continue
      ;;
    --stream)
      _prev=--stream
      continue
      ;;
    --stream=*)
      _selected_stream="${arg#--stream=}"
      continue
      ;;
    --handoff-agent)
      _prev=--handoff-agent
      continue
      ;;
    --handoff-agent=*)
      _handoff_override="${arg#--handoff-agent=}"
      continue
      ;;
    --model)
      _prev=--model
      continue
      ;;
    --model=*)
      _selected_model="${arg#--model=}"
      _has_model=1
      continue
      ;;
  esac

  _prev=""
  _forward+=("$arg")
done

if [ "$_prev" = "--epic" ] || [ "$_prev" = "--stream" ] || [ "$_prev" = "--handoff-agent" ] || [ "$_prev" = "--model" ]; then
  echo "Error: dangling launcher flag '$_prev' without a value." >&2
  exit 1
fi

# Load shared helpers.
if [ -f "$PROJECT_DIR/scripts/lib/handoff_identity.sh" ]; then
  # shellcheck source=scripts/lib/handoff_identity.sh
  source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
fi
if [ -f "$PROJECT_DIR/scripts/lib/session_supervisor.sh" ]; then
  # shellcheck source=scripts/lib/session_supervisor.sh
  source "$PROJECT_DIR/scripts/lib/session_supervisor.sh"
fi

# Validate epic name when the helper is present.
if command -v epic_name_valid >/dev/null 2>&1 && [ -n "$_selected_epic" ]; then
  if ! epic_name_valid "$_selected_epic"; then
    echo "Error: invalid --epic name '${_selected_epic}' (lowercase alnum + inner hyphens)." >&2
    exit 1
  fi
fi

if [ -n "$_selected_epic" ]; then
  export SESSION_EPIC="$_selected_epic"
  echo "Epic assignment: ${SESSION_EPIC}.epic"
  # Kimi-specific handoff slot (not claude-<epic>)
  if [ -z "${SESSION_HANDOFF_AGENT:-}" ] && [ -z "$_handoff_override" ]; then
    case "$_selected_epic" in
      harness|infra) export SESSION_HANDOFF_AGENT='kimi-infra' ;;
      *) export SESSION_HANDOFF_AGENT="kimi-${_selected_epic}" ;;
    esac
  fi
fi

if [ -n "$_handoff_override" ]; then
  export SESSION_HANDOFF_AGENT="$_handoff_override"
fi

# Claim/resume the stream lease through the common supervisor when an epic is pinned.
if [ -n "$_selected_epic" ]; then
  if [ -z "$_selected_stream" ]; then
    _selected_stream="$(stream_id_for_epic "$_selected_epic")"
  fi
  if [ -z "$_selected_stream" ]; then
    echo "Error: cannot resolve stream id for epic '${_selected_epic}'." >&2
    exit 1
  fi

  _launcher_task_id="${SESSION_TASK_ID:-${LEARN_UK_LAUNCHER_TASK_ID:-5512-pr-j1-launchers}}"
  _launcher_instance_id="${SESSION_INSTANCE_ID:-kimi-$$}"
  claim_session_supervisor_env \
    "$_selected_stream" \
    "kimi" \
    "kimi-code" \
    "$_launcher_task_id" \
    "$_launcher_instance_id" \
    "$PROJECT_DIR" \
    "start-kimi.sh" \
    "$_selected_epic"
  unset _launcher_task_id _launcher_instance_id
fi

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  echo "Handoff identity: $SESSION_HANDOFF_AGENT"
fi

export LEARN_UKRAINE_KIMI_LAUNCH=1
export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"

# Defaults for kimi CLI
if [ "$_has_model" -eq 0 ]; then
  _selected_model="k2.7-coding"
fi

# Lane cold-start hint (printed always when epic is set)
if [ -n "${SESSION_EPIC:-}" ]; then
  echo ""
  echo "Lane: ${SESSION_EPIC} (you are NOT the main orchestrator)."
  case "${SESSION_EPIC}" in
    atlas)
      echo "  Stream SSOT: ${SESSION_STREAM_ID:-epic:4387}  (session_streams tail --stream ${SESSION_STREAM_ID:-epic:4387})"
      echo "  File dual-write: .claude/atlas-epic/INTERIM-DRIVER-HANDOFF.md (or CLAUDE-DRIVER-HANDOFF.md read-only)"
      echo "  TAKEOVER: .claude/atlas-epic/TAKEOVER-PROMPT.md"
      ;;
    harness|infra)
      echo "  Stream: ${SESSION_STREAM_ID:-epic:4707}"
      echo "  Infra handoff: docs/session-state/ + .agent/claude-infra-thread-handoff.md (read; write your own kimi slot)"
      ;;
    *)
      echo "  Open stream: SESSION_STREAM_ID=${SESSION_STREAM_ID:-unset}"
      echo "  Epic dir (if any): .claude/${SESSION_EPIC}-epic/"
      ;;
  esac
  echo "  Primary checkout is READ-ONLY for writes → worktrees via scripts/delegate.py"
  echo "  Kimi orchestrator runbook: docs/runbooks/kimi-orchestrator.md"
  echo ""
fi

# Auto-continue the epic stream when --epic is set and the user did not pass a PROMPT.
if [ -n "${SESSION_EPIC:-}" ] && [ "${#_forward[@]}" -eq 0 ]; then
  case "${SESSION_EPIC}" in
    atlas|practice|practice-hub)
      _cold_prompt="You are the interim ATLAS lane driver (stream ${SESSION_STREAM_ID:-epic:4387}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Immediately: (1) read/execute .claude/atlas-epic/TAKEOVER-PROMPT.md — tail stream, reconcile board, dual-write INTERIM-DRIVER-HANDOFF.md; (2) load the session stream digest and mint a canary if one is required. Drive the next unblocked action without a menu. End on canary FAIL-HANDOFF (<8/10). Primary checkout is read-only — writes via worktrees."
      ;;
    harness|infra)
      _cold_prompt="You are the INFRA / harness lane driver (stream ${SESSION_STREAM_ID:-epic:4707}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start from the infra handoff and stream tail; reconcile in-flight work; drive the next unblocked infra action. End on canary FAIL-HANDOFF. Do not claim curriculum content lanes. Primary checkout is read-only — writes via worktrees."
      ;;
    hramatka)
      _cold_prompt="You are the hramatka lane driver (stream ${SESSION_STREAM_ID:-epic:4542}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start from the epic handoff and stream if present; reconcile and drive the next unblocked action. End on canary FAIL-HANDOFF. Primary checkout is read-only — writes via worktrees."
      ;;
    *)
      _cold_prompt="You are the ${SESSION_EPIC} lane driver (SESSION_STREAM_ID=${SESSION_STREAM_ID:-unset}). You are NOT the main orchestrator. The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start: load the epic handoff under .claude/${SESSION_EPIC}-epic/ (or stream tail if SESSION_STREAM_ID is set), reconcile reality, and drive the next unblocked action without a menu. End on canary FAIL-HANDOFF. Primary checkout is read-only — writes via worktrees."
      ;;
  esac
  echo "Cold-start: injecting epic auto-continue prompt (no user PROMPT given)."
  _forward=("$_cold_prompt")
  unset _cold_prompt
fi

echo "Launching Kimi Code..."
exec "$KIMI_BIN" -p "${_forward[*]}" -m "$_selected_model" --output-format stream-json
