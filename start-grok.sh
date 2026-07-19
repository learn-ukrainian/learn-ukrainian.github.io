#!/usr/bin/env bash
# Learn Ukrainian — Grok Build TUI launcher (peer of start-claude.sh).
#
# Launcher-only flags (stripped before exec — grok CLI does not know them):
#   --epic <name> | --epic=<name>     Pin lane (atlas, hramatka, harness, …)
#   --stream <id> | --stream=<id>     Explicit session-stream id (e.g. epic:4387)
#   --handoff-agent <id>              Override SESSION_HANDOFF_AGENT
#   --no-always-approve               Do not pass --always-approve to grok
#   --help-launcher                   This help (does not start grok)
#
# Defaults if not already on the command line:
#   --model grok-4.5
#   --effort high
#   --always-approve  (orchestrator-friendly; disable with --no-always-approve)
#   --cwd <repo root>
#
# Environment exported for hooks / dual-write / session streams:
#   SESSION_EPIC              from --epic
#   SESSION_HANDOFF_AGENT     grok-<epic> (or override / harness→grok-infra)
#   SESSION_STREAM_ID         epic:<n> from --stream or epic→number map
#   LEARN_UKRAINIAN_GROK_LAUNCH=1
#
# Cold-start: with --epic and no free-text PROMPT, the launcher injects an
# auto-continue prompt (Grok has no SessionStart hook like Claude). Pass an
# explicit PROMPT to override. Use --no-always-approve to require tool confirms.
#
# Examples:
#   ./start-grok.sh --epic atlas
#   ./start-grok.sh --epic atlas --stream epic:4387 --effort high
#   ./start-grok.sh --epic harness "continue the infra queue"
#   ./start-grok.sh --model grok-4.5 --effort high -c

set -euo pipefail

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:${HOME}/.grok/bin:${PATH:-}"
hash -r 2>/dev/null || true

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the main worktree root when this script is run from a git worktree copy.
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _git_common="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "${_git_common:-}" ] && [ -d "$(dirname "$_git_common")" ]; then
    _main_wt="$(dirname "$_git_common")"
    if [ -f "$_main_wt/start-grok.sh" ] || [ -f "$_main_wt/AGENTS.md" ]; then
      PROJECT_DIR="$_main_wt"
    fi
  fi
  unset _git_common _main_wt
fi

usage_launcher() {
  sed -n '2,35p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# --- locate grok binary ---
GROK_BIN=""
for cand in \
  "${HOME}/.grok/bin/grok" \
  "$(command -v grok 2>/dev/null || true)" \
  /opt/homebrew/bin/grok
do
  if [ -n "$cand" ] && [ -x "$cand" ]; then
    GROK_BIN="$cand"
    break
  fi
done
if [ -z "$GROK_BIN" ]; then
  echo "Error: grok CLI not found. Install Grok Build TUI (expected ~/.grok/bin/grok)." >&2
  exit 1
fi

echo "Starting Grok in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"
echo "Grok: $("$GROK_BIN" --version 2>/dev/null || echo "$GROK_BIN")"

cd "$PROJECT_DIR"

if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Current branch: $(git branch --show-current 2>/dev/null || echo '?')"
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "Uncommitted changes detected (primary checkout is orientation-only; write via worktrees)"
  fi
fi

# Optional deploy of shared extensions (fail-open — grok does not require .claude/ the same way).
if [ -f "$PROJECT_DIR/scripts/lib/deploy_extensions.sh" ]; then
  # shellcheck source=scripts/lib/deploy_extensions.sh
  source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
  deploy_agent_extensions "$PROJECT_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure (see banner above)."
fi

# --- parse launcher-only flags; build forward argv ---
_forward=()
_selected_epic=""
_selected_stream=""
_handoff_override=""
_always_approve=1
_has_model=0
_has_effort=0
_has_cwd=0
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
    --no-always-approve)
      _always_approve=0
      continue
      ;;
    --model|--model=*)
      _has_model=1
      ;;
    --effort|--effort=*)
      _has_effort=1
      ;;
    --cwd|--cwd=*)
      _has_cwd=1
      ;;
  esac

  # detect --model value form split
  if [ "$_prev" = "--model" ]; then _has_model=1; fi
  if [ "$_prev" = "--effort" ]; then _has_effort=1; fi
  if [ "$_prev" = "--cwd" ]; then _has_cwd=1; fi

  case "$arg" in
    --model|--effort|--cwd) _prev="$arg" ;;
    *) _prev="" ;;
  esac

  _forward+=("$arg")
done

if [ "$_prev" = "--epic" ] || [ "$_prev" = "--stream" ] || [ "$_prev" = "--handoff-agent" ]; then
  echo "Error: dangling launcher flag '$_prev' without a value." >&2
  exit 1
fi

# Validate epic via shared helper when present
if [ -f "$PROJECT_DIR/scripts/lib/handoff_identity.sh" ]; then
  # shellcheck source=scripts/lib/handoff_identity.sh
  source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
  if [ -n "$_selected_epic" ]; then
    if ! epic_name_valid "$_selected_epic"; then
      echo "Error: invalid --epic name '${_selected_epic}' (lowercase alnum + inner hyphens)." >&2
      exit 1
    fi
  fi
fi

# Epic → default stream id (override with --stream)
_stream_for_epic() {
  case "${1:-}" in
    atlas|practice|practice-hub) printf '%s' 'epic:4387' ;;
    harness|infra) printf '%s' 'epic:4707' ;;
    hramatka) printf '%s' 'epic:4542' ;;
    folk|seminars-folk) printf '%s' 'epic:2836' ;;
    bio|seminars-bio) printf '%s' 'epic:4431' ;;
    *) ;;
  esac
}

if [ -n "$_selected_epic" ]; then
  export SESSION_EPIC="$_selected_epic"
  echo "Epic assignment: ${SESSION_EPIC}.epic"
  if [ -z "$_selected_stream" ]; then
    _selected_stream="$(_stream_for_epic "$_selected_epic")"
  fi
  # Grok-specific handoff slot (not claude-<epic>)
  if [ -z "${SESSION_HANDOFF_AGENT:-}" ] && [ -z "$_handoff_override" ]; then
    case "$_selected_epic" in
      harness|infra) export SESSION_HANDOFF_AGENT='grok-infra' ;;
      *) export SESSION_HANDOFF_AGENT="grok-${_selected_epic}" ;;
    esac
  fi
fi

if [ -n "$_handoff_override" ]; then
  export SESSION_HANDOFF_AGENT="$_handoff_override"
fi

if [ -n "$_selected_stream" ]; then
  export SESSION_STREAM_ID="$_selected_stream"
  echo "Session stream: $SESSION_STREAM_ID"
fi

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  echo "Handoff identity: $SESSION_HANDOFF_AGENT"
fi

export LEARN_UKRAINIAN_GROK_LAUNCH=1
export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"

# Defaults for grok CLI
_defaults=()
if [ "$_has_cwd" -eq 0 ]; then
  _defaults+=(--cwd "$PROJECT_DIR")
fi
if [ "$_has_model" -eq 0 ]; then
  _defaults+=(--model grok-4.5)
fi
if [ "$_has_effort" -eq 0 ]; then
  _defaults+=(--effort high)
fi
if [ "$_always_approve" -eq 1 ]; then
  # Only add if not already present in forward args
  _has_aa=0
  for a in "${_forward[@]+"${_forward[@]}"}"; do
    case "$a" in --always-approve) _has_aa=1 ;; esac
  done
  if [ "$_has_aa" -eq 0 ]; then
    _defaults+=(--always-approve)
  fi
fi

# Lane cold-start hint (printed always when epic is set)
if [ -n "${SESSION_EPIC:-}" ]; then
  echo ""
  echo "Lane: ${SESSION_EPIC} (you are NOT the main orchestrator)."
  case "${SESSION_EPIC}" in
    atlas)
      echo "  Stream SSOT: epic:4387  (session_streams tail --stream epic:4387)"
      echo "  File dual-write: .claude/atlas-epic/INTERIM-DRIVER-HANDOFF.md (or CLAUDE-DRIVER-HANDOFF.md read-only)"
      echo "  TAKEOVER: .claude/atlas-epic/TAKEOVER-PROMPT.md"
      ;;
    harness|infra)
      echo "  Stream: ${SESSION_STREAM_ID:-epic:4707}"
      echo "  Infra handoff: docs/session-state/ + .agent/claude-infra-thread-handoff.md (read; write your own grok slot)"
      ;;
    *)
      echo "  Open stream if known: SESSION_STREAM_ID=${SESSION_STREAM_ID:-unset}"
      echo "  Epic dir (if any): .claude/${SESSION_EPIC}-epic/"
      ;;
  esac
  echo "  Primary checkout is READ-ONLY for writes → worktrees via scripts/delegate.py"
  echo ""
fi

# Auto-continue the epic stream when --epic is set and the user did not pass a PROMPT.
# Grok has no SessionStart hook (Claude does) — without an initial prompt the TUI idles
# even though SESSION_EPIC / SESSION_STREAM_ID are exported. Root cause of the 2026-07-19
# "start-grok.sh --epic=atlas did not auto-continue" failure.
_has_prompt=0
_expect_value=0
for a in "${_forward[@]+"${_forward[@]}"}"; do
  if [ "$_expect_value" -eq 1 ]; then
    _expect_value=0
    continue
  fi
  case "$a" in
    --)
      # everything after -- is prompt material; treat next non-empty as prompt
      _expect_value=0
      ;;
    --*=*)
      ;;
    --model|--effort|--cwd|--agent|--agents|--allow|--deny|--disallowed-tools|--debug-file|--json-schema|--leader-socket|--max-turns|--session-id|--resume|--worktree|--output-format|--permission-mode)
      _expect_value=1
      ;;
    -c|--continue|--always-approve|--debug|--disable-web-search|--experimental-memory|--fork-session|--fullscreen|--minimal|--no-alt-screen|--no-memory|--no-plan|--no-subagents|--check|--help|-h)
      ;;
    -*)
      # unknown flag: next token may be its value; do not treat as prompt
      ;;
    *)
      _has_prompt=1
      ;;
  esac
done

if [ -n "${SESSION_EPIC:-}" ] && [ "$_has_prompt" -eq 0 ]; then
  case "${SESSION_EPIC}" in
    atlas|practice|practice-hub)
      _cold_prompt="You are the interim ATLAS lane driver (stream epic:4387). Immediately read and execute .claude/atlas-epic/TAKEOVER-PROMPT.md: tail the session stream, open or resume your lease, reconcile the board against gh/git/worktrees/task files, update INTERIM-DRIVER-HANDOFF.md as dual-write, and drive the next unblocked action without asking for a menu. Primary checkout is read-only — all writes via worktrees."
      ;;
    harness|infra)
      _cold_prompt="You are the INFRA / harness lane driver (stream ${SESSION_STREAM_ID:-epic:4707}). Cold-start from the infra handoff and stream tail; reconcile in-flight work; drive the next unblocked infra action. Do not claim curriculum content lanes. Primary checkout is read-only — writes via worktrees."
      ;;
    hramatka)
      _cold_prompt="You are the hramatka lane driver (stream ${SESSION_STREAM_ID:-epic:4542}). Cold-start from the epic handoff and stream if present; reconcile and drive the next unblocked action. Primary checkout is read-only — writes via worktrees."
      ;;
    *)
      _cold_prompt="You are the ${SESSION_EPIC} lane driver (SESSION_STREAM_ID=${SESSION_STREAM_ID:-unset}). You are NOT the main orchestrator. Cold-start: load the epic handoff under .claude/${SESSION_EPIC}-epic/ (or stream tail if SESSION_STREAM_ID is set), reconcile reality, and drive the next unblocked action without a menu. Primary checkout is read-only — writes via worktrees."
      ;;
  esac
  echo "Cold-start: injecting epic auto-continue prompt (no user PROMPT given)."
  _forward+=("$_cold_prompt")
  unset _cold_prompt
fi
unset _has_prompt _expect_value

echo "Launching Grok Build TUI..."
exec "$GROK_BIN" "${_defaults[@]}" "${_forward[@]+"${_forward[@]}"}"
