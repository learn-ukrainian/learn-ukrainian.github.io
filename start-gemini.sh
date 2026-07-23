#!/usr/bin/env bash
# Learn Ukrainian — Gemini / AGY Build TUI launcher (peer of start-claude.sh / start-grok.sh).
#
# Launcher-only flags (stripped before exec — agy CLI does not know them):
#   --epic <name> | --epic=<name>     Pin lane (atlas, harness, hramatka, …)
#   --stream <id> | --stream=<id>     Explicit session-stream id (e.g. epic:4387)
#   --handoff-agent <id>              Override SESSION_HANDOFF_AGENT
#   --no-always-approve               Do not pass --dangerously-skip-permissions to agy
#   --help-launcher                   This help (does not start agy)
#
# Defaults if not already on the command line:
#   --model gemini-3.6-flash-high (or alias: pro -> gemini-3.1-pro-high)
#   --dangerously-skip-permissions  (orchestrator-friendly; disable with --no-always-approve)
#
# Environment exported for hooks / dual-write / session streams:
#   SESSION_EPIC              from --epic
#   SESSION_HANDOFF_AGENT     gemini-<epic> (or override / harness→gemini-infra)
#   SESSION_STREAM_*          from the common session supervisor (scripts.session_supervisor)
#   LEARN_UKRAINIAN_AGY_LAUNCH=1
#
# Cold-start: with --epic and no free-text PROMPT, the launcher claims the
# stream lease through the common supervisor, writes a capsule, and injects an
# auto-continue orchestrator prompt. Pass an explicit PROMPT to override.
#
# Examples:
#   ./start-gemini.sh --epic atlas
#   ./start-gemini.sh --epic harness --model pro
#   ./start-gemini.sh --epic atlas "check open PRs and stream status"
#   ./start-gemini.sh --model gemini-3.1-pro-high

set -euo pipefail

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:${HOME}/.gemini/bin:${PATH:-}"
hash -r 2>/dev/null || true

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the main worktree root when this script is run from a git worktree copy.
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _git_common="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "${_git_common:-}" ] && [ -d "$(dirname "$_git_common")" ]; then
    _main_wt="$(dirname "$_git_common")"
    if [ -f "$_main_wt/start-gemini.sh" ] || [ -f "$_main_wt/AGENTS.md" ]; then
      PROJECT_DIR="$_main_wt"
    fi
  fi
  unset _git_common _main_wt
fi

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage_launcher() {
  sed -n '2,29p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'
  exit 0
}

# --- locate agy binary ---
AGY_BIN=""
for cand in \
  "${HOME}/.local/bin/agy" \
  "$(command -v agy 2>/dev/null || true)" \
  /opt/homebrew/bin/agy
do
  if [ -n "$cand" ] && [ -x "$cand" ]; then
    AGY_BIN="$cand"
    break
  fi
done
if [ -z "$AGY_BIN" ]; then
  echo "Error: agy CLI not found. Install Antigravity CLI (expected ~/.local/bin/agy)." >&2
  exit 1
fi

echo "Starting Gemini (AGY) in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"
echo "AGY: $("$AGY_BIN" --version 2>/dev/null || echo "$AGY_BIN")"

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
  # Layout A: bare primary is a bug — heal before agents drive (#2842 / #5587).
  if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
      && [ -f "$PROJECT_DIR/scripts/audit/check_core_bare.py" ]; then
    "$PROJECT_DIR/.venv/bin/python" \
      "$PROJECT_DIR/scripts/audit/check_core_bare.py" --fix --repo "$PROJECT_DIR" \
      || echo "Warning: check_core_bare --fix failed (continuing launch)." >&2
  fi
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "Uncommitted changes detected (primary checkout is orientation-only; write via worktrees)"
  fi
fi

# Optional deploy of shared extensions.
if [ -f "$PROJECT_DIR/scripts/lib/deploy_extensions.sh" ]; then
  # shellcheck source=scripts/lib/deploy_extensions.sh
  source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
  deploy_agent_extensions "$PROJECT_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure."
fi

# --- parse launcher-only flags & model aliases ---
_forward=()
_selected_epic=""
_selected_stream=""
_handoff_override=""
_always_approve=1
_selected_model=""
_has_model=0
_has_effort=0
_has_print=0
_prev=""

resolve_gemini_model_alias() {
  case "$1" in
    pro|3.1-pro|gemini-3.1-pro|gemini-3.1-pro-high) printf '%s\n' 'gemini-3.1-pro-high' ;;
    pro-low|gemini-3.1-pro-low) printf '%s\n' 'gemini-3.1-pro-low' ;;
    flash|3.6-flash|gemini-3.6-flash|gemini-3.6-flash-high) printf '%s\n' 'gemini-3.6-flash-high' ;;
    flash-med|gemini-3.6-flash-medium) printf '%s\n' 'gemini-3.6-flash-medium' ;;
    flash35|3.5-flash|gemini-3.5-flash-high) printf '%s\n' 'gemini-3.5-flash-high' ;;
    *) printf '%s\n' "$1" ;;
  esac
}

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
    _selected_model="$(resolve_gemini_model_alias "$arg")"
    _has_model=1
    _forward+=( "$_selected_model" )
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
    --model)
      _prev=--model
      _forward+=("$arg")
      continue
      ;;
    --model=*)
      _raw_model="${arg#--model=}"
      _selected_model="$(resolve_gemini_model_alias "$_raw_model")"
      _has_model=1
      _forward+=("--model=$_selected_model")
      continue
      ;;
    --effort|--effort=*)
      _has_effort=1
      ;;
    -p|--print|--prompt)
      _has_print=1
      ;;
  esac

  if [ "$_prev" = "--effort" ]; then _has_effort=1; fi

  case "$arg" in
    --effort) _prev="$arg" ;;
    *) _prev="" ;;
  esac

  _forward+=("$arg")
done

if [ "$_prev" = "--epic" ] || [ "$_prev" = "--stream" ] || [ "$_prev" = "--handoff-agent" ]; then
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
if [ -f "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh" ]; then
  # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
  source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
fi

# Resolve the public selector exactly once, before deriving state or identities.
if [ -n "$_selected_epic" ]; then
  _requested_selector="$_selected_epic"
  if ! _canonical_lane="$(launcher_selector_lane "$_requested_selector")"; then
    echo "Error: unknown lane selector '${_requested_selector}'." >&2
    launcher_selector_help >&2
    exit 1
  fi
  case "$_requested_selector" in
    *.*|practice|practice-hub|seminars-folk|seminars-bio) _selected_epic="$_canonical_lane" ;;
  esac
  unset _requested_selector _canonical_lane
fi

if [ -n "$_selected_epic" ]; then
  export SESSION_EPIC="$_selected_epic"
  echo "Epic assignment: ${SESSION_EPIC}.epic"
  if [ -z "${SESSION_HANDOFF_AGENT:-}" ] && [ -z "$_handoff_override" ]; then
    if command -v handoff_identity_for_gemini_epic >/dev/null 2>&1; then
      export SESSION_HANDOFF_AGENT="$(handoff_identity_for_gemini_epic "$_selected_epic")"
    else
      case "$_selected_epic" in
        harness|infra|devops) export SESSION_HANDOFF_AGENT='gemini-infra' ;;
        *) export SESSION_HANDOFF_AGENT="gemini-${_selected_epic}" ;;
      esac
    fi
  fi
fi

if [ -n "$_handoff_override" ]; then
  export SESSION_HANDOFF_AGENT="$_handoff_override"
fi

# Fleet-comms plane mode + banner whenever epic is set (including explicit PROMPT paths).
if [ -n "${SESSION_EPIC:-}" ]; then
  if command -v fleet_comms_resolve_plane_mode >/dev/null 2>&1; then
    export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
  else
    export FLEET_COMMS_PLANE_MODE="off"
  fi
  if command -v fleet_comms_print_banner_line >/dev/null 2>&1; then
    fleet_comms_print_banner_line
  fi
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

  _launcher_task_id="${SESSION_TASK_ID:-${LEARN_UK_LAUNCHER_TASK_ID:-5512-pr-j1-gemini-launcher}}"
  _launcher_instance_id="${SESSION_INSTANCE_ID:-gemini-$$}"
  claim_session_supervisor_env \
    "$_selected_stream" \
    "gemini" \
    "agy" \
    "$_launcher_task_id" \
    "$_launcher_instance_id" \
    "$PROJECT_DIR" \
    "start-gemini.sh" \
    "$_selected_epic"
  unset _launcher_task_id _launcher_instance_id
fi

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  echo "Handoff identity: $SESSION_HANDOFF_AGENT"
fi

export LEARN_UKRAINIAN_AGY_LAUNCH=1
export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"

# Defaults for agy CLI
_defaults=()
if [ "$_has_model" -eq 0 ]; then
  # Default to gemini-3.6-flash-high for fast throughput, or use --model pro for complex orchestrations
  _defaults+=(--model gemini-3.6-flash-high)
fi
if [ "$_always_approve" -eq 1 ]; then
  _has_aa=0
  for a in "${_forward[@]+"${_forward[@]}"}"; do
    case "$a" in --dangerously-skip-permissions) _has_aa=1 ;; esac
  done
  if [ "$_has_aa" -eq 0 ]; then
    _defaults+=(--dangerously-skip-permissions)
  fi
fi

# Detect whether free-text user prompt or flags were provided
_has_prompt=0
_expect_value=0
_user_prompt=""

for a in "${_forward[@]+"${_forward[@]}"}"; do
  if [ "$_expect_value" -eq 1 ]; then
    _expect_value=0
    continue
  fi
  case "$a" in
    --)
      _expect_value=0
      ;;
    --*=*)
      ;;
    --model|--effort|--conversation|--log-file|--mode|--project|--print-timeout)
      _expect_value=1
      ;;
    -c|--continue|--dangerously-skip-permissions|-i|--prompt-interactive|-p|--print|--prompt|--sandbox|--help|-h)
      ;;
    -*)
      ;;
    *)
      _has_prompt=1
      _user_prompt="$a"
      ;;
  esac
done

if [ -n "${SESSION_EPIC:-}" ] && [ "$_has_prompt" -eq 0 ]; then
  _handoff_path=".agent/${SESSION_HANDOFF_AGENT:-gemini-${SESSION_EPIC}}-thread-handoff.md"
  if command -v fleet_comms_cold_clause >/dev/null 2>&1; then
    _fc="$(fleet_comms_cold_clause)"
  else
    _fc="Fleet-comms (#5512): obey agents_extensions/shared/rules/fleet-comms-coordination.md; plane-status + review-pr; file dual-write stays authoritative in every plane mode (dual_write=shadow/mirror)."
  fi
  _cold_prompt="You are the Gemini ${SESSION_EPIC} lane orchestrator (stream ${SESSION_STREAM_ID:-unset}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Immediately: (1) Check stream state in ${_handoff_path} or docs/session-state/; (2) Run 'codexbar usage' to monitor fleet quota/limits; (3) Assess tasks, pick the optimal model/agent from the capability matrix (AGENTS.md, model-assignment.md via /api/rules); (4) Dispatch worker sub-tasks via worktrees using 'scripts/delegate.py dispatch ...'; (5) Obey advisor approval gate (Fable / Sol) for architecture/process changes; (6) Enforce independent cross-family review via review-pr / publish-review-verdict before PR merges. ${_fc} Primary checkout is read-only — all edits belong in worktrees."
  # Wire the drive-epic playbook into the cold prompt (Sol review #5632 F005).
  _cold_prompt="${_cold_prompt} Your orchestration playbook is agents_extensions/shared/skills/drive-epic/SKILL.md (invoke \$drive-epic if your harness exposes skills) — load it before acting; it defines the topology→route→dispatch→cross-family-review→merge→handoff loop and the escalation triggers."
  echo "Cold-start: injecting epic orchestrator auto-continue prompt."
  if [ "$_has_print" -eq 1 ]; then
    _forward+=("$_cold_prompt")
  else
    _defaults+=("-i" "$_cold_prompt")
  fi
  unset _cold_prompt _fc
elif [ "$_has_prompt" -eq 1 ] && [ "$_has_print" -eq 0 ]; then
  # If a positional prompt is given for interactive mode, pass it via -i
  _forward_without_prompt=()
  for a in "${_forward[@]+"${_forward[@]}"}"; do
    if [ "$a" != "$_user_prompt" ]; then
      _forward_without_prompt+=("$a")
    fi
  done
  _forward=("${_forward_without_prompt[@]+"${_forward_without_prompt[@]}"}")
  _defaults+=("-i" "$_user_prompt")
  unset _forward_without_prompt
fi
unset _has_prompt _expect_value _user_prompt

echo "Launching Gemini AGY Build TUI..."
exec "$AGY_BIN" "${_defaults[@]+"${_defaults[@]}"}" "${_forward[@]+"${_forward[@]}"}"
