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
#   SESSION_STREAM_*          from the common session supervisor (scripts.session_supervisor)
#   LEARN_UKRAINIAN_GROK_LAUNCH=1
#   FLEET_COMMS_PLANE_MODE    resolved at launch (off|shadow|dual_write); fail-open off
#
# Fleet-comms (#5512) — dual-aware mid-cutover (not pure rot):
#   Wired already: session-stream lease claim via claim_session_supervisor_env,
#   canary mint, stream dual-write diary. Message-plane default is still off
#   until parity receipt + operator/advisor GO — launchers must prefer plane
#   surfaces when mode != off and fall back to file dual-write while off.
#   Cold-prompts point at fleet_comms + review-pr / publish-review-verdict,
#   not file-handoff folklore alone.
#
# Cold-start: with --epic and no free-text PROMPT, the launcher claims the
# stream lease through the common supervisor, writes a capsule, and injects an
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
  sed -n '2,42p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# Shared dual-aware fleet-comms helpers (SSOT rule: fleet-comms-coordination.md).
if [ -f "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh" ]; then
  # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
  source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
fi

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

cd "$PROJECT_DIR"

# Quiet success path for preflight heals (errors still print on stderr).
if git rev-parse --git-dir >/dev/null 2>&1; then
  # Heal detached/wrong-branch primary so agents never start on a raw SHA (#4857).
  if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
      && [ -f "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" ]; then
    if ! "$PROJECT_DIR/.venv/bin/python" \
        "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" \
        --cwd "$PROJECT_DIR" --heal >/dev/null; then
      echo "Error: primary checkout is not on main and auto-heal failed." >&2
      exit 1
    fi
  fi
  # Layout A: bare primary is a bug — heal before agents drive (#2842 / #5587).
  # Grok has no SessionStart hook (Claude uses heal-core-bare PreToolUse).
  if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
      && [ -f "$PROJECT_DIR/scripts/audit/check_core_bare.py" ]; then
    if ! "$PROJECT_DIR/.venv/bin/python" \
        "$PROJECT_DIR/scripts/audit/check_core_bare.py" --fix --repo "$PROJECT_DIR" \
        >/dev/null; then
      echo "Warning: check_core_bare --fix failed (continuing launch)." >&2
    fi
  fi
fi

# Optional deploy of shared extensions (fail-open; quiet on success).
if [ -f "$PROJECT_DIR/scripts/lib/deploy_extensions.sh" ]; then
  # shellcheck source=scripts/lib/deploy_extensions.sh
  source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
  _deploy_out=""
  _deploy_rc=0
  _deploy_out="$(deploy_agent_extensions "$PROJECT_DIR" agents:deploy 2>&1)" || _deploy_rc=$?
  if [ "$_deploy_rc" -ne 0 ]; then
    printf '%s\n' "$_deploy_out" >&2
    echo "Continuing launch despite deploy failure." >&2
  fi
  unset _deploy_out _deploy_rc
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
    _selected_epic="$arg"
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

# Load shared helpers.
if [ -f "$PROJECT_DIR/scripts/lib/handoff_identity.sh" ]; then
  # shellcheck source=scripts/lib/handoff_identity.sh
  source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
fi
if [ -f "$PROJECT_DIR/scripts/lib/session_supervisor.sh" ]; then
  # shellcheck source=scripts/lib/session_supervisor.sh
  source "$PROJECT_DIR/scripts/lib/session_supervisor.sh"
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
    *.*) _selected_epic="$_canonical_lane" ;;
  esac
  unset _requested_selector _canonical_lane
fi

if [ -n "$_selected_epic" ]; then
  export SESSION_EPIC="$_selected_epic"
  # Grok-specific handoff slot (not claude-<epic>)
  if [ -z "${SESSION_HANDOFF_AGENT:-}" ] && [ -z "$_handoff_override" ]; then
    export SESSION_HANDOFF_AGENT="$(handoff_identity_for_grok_epic "$_selected_epic")"
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
  _launcher_instance_id="${SESSION_INSTANCE_ID:-grok-$$}"
  claim_session_supervisor_env \
    "$_selected_stream" \
    "grok" \
    "grok-tui" \
    "$_launcher_task_id" \
    "$_launcher_instance_id" \
    "$PROJECT_DIR" \
    "start-grok.sh" \
    "$_selected_epic"
  unset _launcher_task_id _launcher_instance_id
fi

export LEARN_UKRAINIAN_GROK_LAUNCH=1
export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"
if command -v fleet_comms_resolve_plane_mode >/dev/null 2>&1; then
  export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
else
  export FLEET_COMMS_PLANE_MODE="off"
fi

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

# Compact launch banner (one line + short lane block when epic set).
_grok_ver="$("$GROK_BIN" --version 2>/dev/null | head -1 || echo grok)"
_branch=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  _branch="$(git branch --show-current 2>/dev/null || true)"
fi
if [ -n "${SESSION_EPIC:-}" ]; then
  echo "Grok ${_grok_ver} · epic=${SESSION_EPIC} stream=${SESSION_STREAM_ID:-unset} handoff=${SESSION_HANDOFF_AGENT:-unset} plane=${FLEET_COMMS_PLANE_MODE}${_branch:+ · ${_branch}}"
  if command -v fleet_comms_print_banner_line >/dev/null 2>&1; then
    fleet_comms_print_banner_line
  else
    echo "  fleet-comms: plane=${FLEET_COMMS_PLANE_MODE} (shared helper missing — treat dual-aware)"
  fi
  case "${SESSION_EPIC}" in
    atlas)
      echo "  canary: .venv/bin/python -m scripts.session_canary.grok_lane mint --epic atlas"
      echo "  board:  .claude/atlas-epic/TAKEOVER-PROMPT.md + INTERIM-DRIVER-HANDOFF.md (diary authoritative every plane mode)"
      ;;
    harness|infra)
      echo "  canary: .venv/bin/python -m scripts.session_canary.grok_lane mint --epic harness"
      echo "  board:  .claude/harness-epic/*-DRIVER-HANDOFF.md + docs/session-state/ (diary authoritative every plane mode)"
      ;;
    *)
      echo "  canary: .venv/bin/python -m scripts.session_canary.grok_lane mint --epic ${SESSION_EPIC}"
      echo "  board:  .claude/${SESSION_EPIC}-epic/ (diary authoritative every plane mode)"
      ;;
  esac
  echo "  writes: worktrees only · end on canary FAIL-HANDOFF (docs/runbooks/grok-session-canary.md)"
else
  # Preserve handoff confirmation when --handoff-agent is used without --epic (CF F001).
  echo "Grok ${_grok_ver}${_branch:+ · ${_branch}}${SESSION_HANDOFF_AGENT:+ · handoff=${SESSION_HANDOFF_AGENT}} · no --epic (stream lease not claimed)"
fi
unset _grok_ver _branch

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
  if command -v fleet_comms_cold_clause >/dev/null 2>&1; then
    _fc="$(fleet_comms_cold_clause)"
  else
    _fc="Fleet-comms (#5512) mid-cutover: obey agents_extensions/shared/rules/fleet-comms-coordination.md; plane-status then review-pr; file dual-write stays authoritative in every plane mode (dual_write=shadow/mirror)."
  fi
  case "${SESSION_EPIC}" in
    atlas|practice|practice-hub)
      _cold_prompt="You are the interim ATLAS lane driver (stream ${SESSION_STREAM_ID:-epic:4387}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Immediately: (1) read/execute .claude/atlas-epic/TAKEOVER-PROMPT.md — tail stream, reconcile board, dual-write INTERIM-DRIVER-HANDOFF.md in every plane mode; (2) mint the session canary: .venv/bin/python -m scripts.session_canary.grok_lane mint --epic atlas --stream ${SESSION_STREAM_ID:-epic:4387} (docs/runbooks/grok-session-canary.md). ${_fc} Drive the next unblocked action without a menu. End session on canary FAIL-HANDOFF (<8/10), not on compact count; after any auto-compact re-score from memory then AUTO-HYDRATE on PASS — never ask the operator to restart. Primary checkout is read-only — writes via worktrees."
      ;;
    harness|infra)
      _cold_prompt="You are the INFRA / harness lane driver (stream ${SESSION_STREAM_ID:-epic:4707}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start from the infra handoff dual-write (.claude/harness-epic/*-DRIVER-HANDOFF.md) and stream tail; mint canary (.venv/bin/python -m scripts.session_canary.grok_lane mint --epic harness); reconcile in-flight work; drive the next unblocked infra action. ${_fc} End on canary FAIL-HANDOFF not compact count (docs/runbooks/grok-session-canary.md). After auto-compact you own recovery: score canary FROM MEMORY then read the AUTO-HYDRATE capsule score prints on PASS — never ask the operator to restart or re-load the diary. Do not claim curriculum content lanes. Primary checkout is read-only — writes via worktrees."
      ;;
    hramatka)
      _cold_prompt="You are the hramatka lane driver (stream ${SESSION_STREAM_ID:-epic:4542}). The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start from the epic handoff dual-write and stream if present; mint canary (.venv/bin/python -m scripts.session_canary.grok_lane mint --epic hramatka); reconcile and drive the next unblocked action. ${_fc} End on canary FAIL-HANDOFF (docs/runbooks/grok-session-canary.md). After auto-compact you own recovery: score FROM MEMORY then AUTO-HYDRATE from score PASS output — never ask the operator to restart/hydrate/diary. Primary checkout is read-only — writes via worktrees."
      ;;
    *)
      _cold_prompt="You are the ${SESSION_EPIC} lane driver (SESSION_STREAM_ID=${SESSION_STREAM_ID:-unset}). You are NOT the main orchestrator. The launcher has already claimed the stream lease; do NOT open or resume it yourself. Cold-start: load the epic handoff dual-write under .claude/${SESSION_EPIC}-epic/ (or stream tail if SESSION_STREAM_ID is set), mint canary via .venv/bin/python -m scripts.session_canary.grok_lane mint --epic ${SESSION_EPIC}, reconcile reality, and drive the next unblocked action without a menu. ${_fc} End on canary FAIL-HANDOFF not compact count (docs/runbooks/grok-session-canary.md). Primary checkout is read-only — writes via worktrees."
      ;;
  esac
  # Wire the drive-epic playbook into every epic's cold prompt (Sol review #5632 F005).
  _cold_prompt="${_cold_prompt} Your orchestration playbook is agents_extensions/shared/skills/drive-epic/SKILL.md (invoke \$drive-epic if your harness exposes skills) — load it before acting; it defines the topology→route→dispatch→cross-family-review→merge→handoff loop and the escalation triggers."
  _forward+=("$_cold_prompt")
  unset _cold_prompt _fc
fi
unset _has_prompt _expect_value

exec "$GROK_BIN" "${_defaults[@]}" "${_forward[@]+"${_forward[@]}"}"
