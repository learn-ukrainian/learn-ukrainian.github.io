#!/bin/bash
# Learn Ukrainian - Claude Code Wrapper
# Ensures skills are deployed and starts Claude

set -e

# Ensure ~/.local/bin is in PATH (where claude installs by default)
export PATH="$HOME/.local/bin:$PATH"
hash -r 2>/dev/null || true  # Clear command cache

# Get script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

launcher_usage() {
    cat <<'EOF'
Usage: ./start-claude.sh [Claude flags] [--epic <lane-or-lane.topic>]

`--epic` is launcher-only and is removed before Claude starts.
Valid lane selectors:
  infra | harness | infra.fleet-comms | infra.devops
  atlas | practice | atlas.practice
  hramatka | hramatka.lessons
  folk | seminars-folk
  bio | seminars-bio
EOF
}

case "${1:-}" in
    --help|--help-launcher|-h)
        launcher_usage
        exit 0
        ;;
esac

# Parse launcher-private epic selection before expensive launch preflight.  This
# gives typos the same fail-closed diagnostic whether or not Claude is installed.
# shellcheck source=scripts/lib/handoff_identity.sh
source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
if epic_flag_present "$@"; then
    _early_selector="$(handoff_epic_from_argv "$@")"
    if [ -z "$_early_selector" ]; then
        echo "Error: --epic flag present but no usable value." >&2
        launcher_selector_help >&2
        exit 1
    fi
    if ! launcher_selector_resolve "$_early_selector" >/dev/null; then
        echo "Error: unknown lane selector '$_early_selector'." >&2
        launcher_selector_help >&2
        exit 1
    fi
    unset _early_selector
fi

echo "Starting Claude in Learn Ukrainian project..."
echo "Project: $PROJECT_DIR"

# Preflight check: Verify required tools
echo "Preflight check..."
MISSING_TOOLS=""
for tool in git gh node npm; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Warning: Optional tools not found:$MISSING_TOOLS"
    echo "   (These are recommended but not required to start)"
fi

# Locate the Claude Code NATIVE install (preferred). The npx route is broken as of
# 2026-06-12: the npx-cached binary exits 194 ("native binary not installed").
CLAUDE_BIN="$HOME/.local/bin/claude"
if [ ! -x "$CLAUDE_BIN" ]; then
    echo "Error: Claude Code native install not found at $CLAUDE_BIN"
    echo "   Install/repair it, e.g.:  curl -fsSL https://claude.ai/install.sh | bash"
    exit 1
fi
echo "Claude native install: $("$CLAUDE_BIN" --version 2>/dev/null) ($CLAUDE_BIN)"

# Change to project directory
cd "$PROJECT_DIR"

# Show current branch
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected"
    fi
fi

# Deploy agent extensions (always run to ensure up-to-date). Fail-honest: a
# failing deploy prints a loud banner + the real output instead of the old
# silent `|| true` that claimed "Skills deployed" over a stale .claude/.
# shellcheck source=scripts/lib/deploy_extensions.sh
source "$PROJECT_DIR/scripts/lib/deploy_extensions.sh"
deploy_agent_extensions "$PROJECT_DIR" agents:deploy \
    || echo "Continuing launch despite deploy failure (see banner above)."

# Show project status
echo ""
echo "LEARN UKRAINIAN - Ukrainian Language Learning"

# Show completion status from CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    echo "   Completion Status:"
    # Extract completion status (lines between "### Completion Status" and next "###")
    sed -n '/^### Completion Status/,/^###/p' CLAUDE.md 2>/dev/null | \
        grep -E "^- \*\*[ABC][12]" | \
        sed 's/^- /       /' | \
        head -4
fi

# Count modules per level
echo ""
echo "   Module counts:"
for level in a1 a2 b1 b2 c1 c2; do
    if [ -d "curriculum/l2-uk-en/$level" ]; then
        COUNT=$(ls -1 curriculum/l2-uk-en/$level/*.md 2>/dev/null | wc -l | xargs)
        LEVEL_UPPER=$(echo "$level" | tr 'a-z' 'A-Z')
        echo "       $LEVEL_UPPER: $COUNT modules"
    fi
done

# List available skills dynamically
echo ""
if [ -d ".claude/skills" ]; then
    SKILL_COUNT=$(ls -1d .claude/skills/*/ 2>/dev/null | wc -l | xargs)
    echo "   Skills ($SKILL_COUNT available):"
    ls -1 .claude/skills/ 2>/dev/null | head -5 | sed 's/^/       /'
    if [ "$SKILL_COUNT" -gt 5 ]; then
        echo "       ... and $((SKILL_COUNT - 5)) more"
    fi
fi

# List available commands dynamically
echo ""
if [ -d ".claude/commands" ]; then
    CMD_COUNT=$(ls -1 .claude/commands/*.md 2>/dev/null | wc -l | xargs)
    echo "   Commands ($CMD_COUNT available):"
    ls -1 .claude/commands/*.md 2>/dev/null | \
        sed 's|.claude/commands/||' | \
        sed 's|.md$||' | \
        sed 's/^/       \//' | \
        head -4
    if [ "$CMD_COUNT" -gt 4 ]; then
        echo "       ... and $((CMD_COUNT - 4)) more"
    fi
fi

echo ""
echo "   Quick reference: npm run generate, npm run vocab:enrich, npm run pipeline"

echo ""

# Resolve and validate the main-session route independently of delegated models.
_selected_model=""
_prev=""
for arg in "$@"; do
    case "$arg" in
        --model=*)
            _selected_model="${arg#--model=}"
            ;;
    esac
    if [ "$_prev" = "--model" ]; then
        _selected_model="$arg"
    fi
    _prev="$arg"
done

# Direct use of this certified wrapper is the native-Claude route. Claudex and
# KimiCC mark only the process they own; markers are consumed here so a later
# nested native launch cannot inherit an alternate route by ambient state.
_claudex_managed_launch="${LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH:-0}"
_kimicc_managed_launch="${LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH:-0}"
unset LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH
unset LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH
if [ "$_claudex_managed_launch" != "1" ] && [ "${LEARN_UKRAINIAN_TRANSPORT:-}" = "claudex" ]; then
    unset LEARN_UKRAINIAN_REQUESTED_PROFILE_ID
fi
if [ "$_kimicc_managed_launch" != "1" ] && [ "${LEARN_UKRAINIAN_TRANSPORT:-}" = "kimicc" ]; then
    unset LEARN_UKRAINIAN_REQUESTED_PROFILE_ID
fi
_requested_profile="${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-native_claude}"
# shellcheck source=scripts/lib/profile_resolver.sh
source "$PROJECT_DIR/scripts/lib/profile_resolver.sh"
if ! resolve_context_profile "$_requested_profile" "$_selected_model"; then
    echo "Error: failed to resolve main-session context profile '$_requested_profile'." >&2
    exit 1
fi

if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ]; then
    echo "Warning: untrusted main-session route ($LEARN_UKRAINIAN_RESOLUTION_REASON); using compact fallback without a fabricated context window." >&2
    if [ "$LEARN_UKRAINIAN_MODEL_MISMATCH" = "1" ]; then
        echo "Warning: observed model '${_selected_model:-unknown}' does not match profile '${LEARN_UKRAINIAN_EXPECTED_PROFILE_ID:-unknown}'." >&2
    fi
fi

# The certified native route must not inherit Claudex/KimiCC proxy, delegation,
# deferred-tool, effort, context-capacity, or supervisor identity state.
if [ "$LEARN_UKRAINIAN_TRANSPORT" = "native" ]; then
    unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_SUBAGENT_MODEL
    unset ANTHROPIC_MODEL ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL
    unset ANTHROPIC_DEFAULT_HAIKU_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL
    unset ENABLE_TOOL_SEARCH CLAUDE_CODE_EFFORT_LEVEL
    unset CLAUDE_CODE_MAX_CONTEXT_TOKENS
    unset LEARN_UKRAINIAN_CLAUDEX_RUN_ID
    unset LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION
fi

# Only a trusted non-native gateway contract may override Claude Code's assumed
# context window and compaction point. The assumed window is required for
# unrecognized gateway model IDs; the compact capacity is capped against it.
if [ "$LEARN_UKRAINIAN_TRUSTED" = "1" ] && [ "$LEARN_UKRAINIAN_TRANSPORT" != "native" ] && [ "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS" -gt 0 ]; then
    export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
else
    unset CLAUDE_CODE_MAX_CONTEXT_TOKENS
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" = "1" ] && [ "$LEARN_UKRAINIAN_TRANSPORT" != "native" ] && [ -n "$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS" ]; then
    export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"
else
    unset CLAUDE_CODE_AUTO_COMPACT_WINDOW
fi

# One concise diagnostic; no endpoint, authorization, or forwarded arguments.
echo "Context profile: id=$LEARN_UKRAINIAN_PROFILE_ID model=$LEARN_UKRAINIAN_MAIN_MODEL_ID window=$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS budget=$LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS compact=${LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS:-native} reason=$LEARN_UKRAINIAN_RESOLUTION_REASON"
unset _claudex_managed_launch _kimicc_managed_launch _requested_profile _prev

export LEARN_UKRAINIAN_TELEMETRY_FOOTER="${LEARN_UKRAINIAN_TELEMETRY_FOOTER:-1}"

# Launch the NATIVE install directly. (Previously launched via
# `npx @anthropic-ai/claude-code@latest`, but that route broke 2026-06-12 — the
# npx-cached binary exits 194. The native install at ~/.local/bin/claude auto-updates
# via `claude update`, so npx is no longer needed to stay current.)
# Derive the cold-start handoff identity from the selected `--agent`, so ONE
# launcher serves every lane: the SessionStart hook keys the thread handoff off
# SESSION_HANDOFF_AGENT, and each lane reads/writes its OWN
# .agent/<id>-thread-handoff.md slot (no per-lane wrapper scripts). Folk /
# curriculum default to the `claude` slot; `--agent infra-orchestrator` →
# `claude-infra`. An explicit SESSION_HANDOFF_AGENT in the environment wins.
# Mapping + argv parsing live in scripts/lib/handoff_identity.sh (unit-tested).
#
# EPIC ASSIGNMENT (`--epic <name>` / `--epic=<name>`, e.g. `--epic atlas`):
# a LAUNCHER-ONLY flag (stripped before exec — the claude CLI does not know it).
# It pins the session to one epic lane: SESSION_EPIC is exported for the
# SessionStart hook to print a binding assignment banner, and the handoff slot
# becomes the canonical claude-<lane> slot (for example all infra selectors map
# to claude-infra) so two sessions on different lanes never share (or clobber) a thread
# handoff. Without --epic the hook tells the session to ASK the user instead of
# defaulting to a lane — the 2026-07-13 atlas/hramatka/main lane collision is
# the reason this exists.
#
# PR-J2: common session supervisor claims/resumes the stream lease when --epic
# is set (mirror start-grok.sh / start-kimi.sh). SessionStart binds the native
# Claude session id to the already-open lease and never opens a second lease.
_forward_args=("$@")
if [ -f "$PROJECT_DIR/scripts/lib/handoff_identity.sh" ]; then
    # shellcheck source=scripts/lib/handoff_identity.sh
    source "$PROJECT_DIR/scripts/lib/handoff_identity.sh"
fi
if [ -f "$PROJECT_DIR/scripts/lib/session_supervisor.sh" ]; then
    # shellcheck source=scripts/lib/session_supervisor.sh
    source "$PROJECT_DIR/scripts/lib/session_supervisor.sh"
fi

_selected_epic=""
if command -v handoff_epic_from_argv >/dev/null 2>&1; then
    _selected_epic="$(handoff_epic_from_argv "$@")"
    if [ -z "$_selected_epic" ] && command -v epic_flag_present >/dev/null 2>&1 && epic_flag_present "$@"; then
        echo "Error: --epic flag present but no usable value (dangling --epic, --epic=, or empty value)."
        echo "   Refusing to launch — pass --epic <name> (e.g. --epic atlas) or drop the flag."
        exit 1
    fi
    if [ -n "$_selected_epic" ]; then
        _requested_selector="$_selected_epic"
        if ! _canonical_lane="$(launcher_selector_lane "$_requested_selector")"; then
            echo "Error: unknown lane selector '$_requested_selector'." >&2
            launcher_selector_help >&2
            exit 1
        fi
        case "$_requested_selector" in
            *.*|practice|practice-hub|seminars-folk|seminars-bio) _selected_epic="$_canonical_lane" ;;
        esac
        unset _requested_selector _canonical_lane
        export SESSION_EPIC="$_selected_epic"
        if command -v strip_epic_from_argv >/dev/null 2>&1; then
            _forward_args=()
            while IFS= read -r -d '' _fwd_arg; do
                _forward_args+=("$_fwd_arg")
            done < <(strip_epic_from_argv "$@")
            unset _fwd_arg
        fi
        echo "Epic assignment: ${SESSION_EPIC}.epic"
    fi

    if [ -z "${SESSION_HANDOFF_AGENT:-}" ]; then
        _selected_agent=""
        if command -v handoff_agent_from_argv >/dev/null 2>&1; then
            _selected_agent="$(handoff_agent_from_argv "$@")"
        fi
        _handoff_slot=""
        if command -v handoff_identity_for_epic >/dev/null 2>&1; then
            _handoff_slot="$(handoff_identity_for_epic "${_selected_epic:-}")"
        fi
        if [ -z "$_handoff_slot" ] && command -v handoff_identity_for_agent >/dev/null 2>&1; then
            _handoff_slot="$(handoff_identity_for_agent "$_selected_agent")"
        fi
        if [ -n "$_handoff_slot" ]; then
            export SESSION_HANDOFF_AGENT="$_handoff_slot"
            echo "Handoff identity: $SESSION_HANDOFF_AGENT (from --epic '${_selected_epic:-}' / --agent '${_selected_agent:-}')"
        fi
        unset _selected_agent _handoff_slot
    fi
fi

# Claim/resume the stream lease through the common supervisor when an epic is pinned.
# Skip when a lease envelope is already exported (nested launchers / tests).
# Soft-fail when LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH=1 or CLAUDEX_TEST_CAPTURE is set
# (start-claudex nested path); hard-fail for normal interactive epic launches.
if [ -n "${_selected_epic:-}" ] && command -v claim_session_supervisor_env >/dev/null 2>&1; then
    if [ -n "${SESSION_STREAM_ID:-}" ] && [ -n "${SESSION_STREAM_SESSION_ID:-}" ] && [ -n "${SESSION_STREAM_LEASE_ID:-}" ]; then
        echo "Session supervisor: using pre-exported lease ${SESSION_STREAM_ID} (${SESSION_STREAM_SESSION_ID})"
    else
        _selected_stream="$(stream_id_for_epic "$_selected_epic")"
        if [ -z "$_selected_stream" ]; then
            echo "Error: cannot resolve stream id for epic '${_selected_epic}'." >&2
            exit 1
        fi
        _launcher_task_id="${SESSION_TASK_ID:-${LEARN_UK_LAUNCHER_TASK_ID:-5512-pr-j2-sessionstart}}"
        _launcher_instance_id="${SESSION_INSTANCE_ID:-claude-$$}"
        if claim_session_supervisor_env             "$_selected_stream"             "claude"             "claude-code"             "$_launcher_task_id"             "$_launcher_instance_id"             "$PROJECT_DIR"             "start-claude.sh"             "$_selected_epic"; then
            :
        else
            if [ -n "${LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH:-}" ] || [ -n "${CLAUDEX_TEST_CAPTURE:-}" ]; then
                echo "Warning: session supervisor claim failed for ${_selected_stream} (managed/nested launch continues)." >&2
            else
                echo "Error: session supervisor claim failed for ${_selected_stream}." >&2
                exit 1
            fi
        fi
        unset _launcher_task_id _launcher_instance_id _selected_stream
    fi
fi

# Fleet-comms dual-aware banner (Claude loads /api/rules for full doctrine; cold-prompt is SessionStart).
if [ -n "${SESSION_EPIC:-}" ] && [ -f "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh" ]; then
    # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
    source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
    if command -v fleet_comms_resolve_plane_mode >/dev/null 2>&1; then
        export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
    fi
    if command -v fleet_comms_print_banner_line >/dev/null 2>&1; then
        fleet_comms_print_banner_line
    fi
fi
unset _selected_epic

echo "Launching Claude Code (native install)..."
exec "$CLAUDE_BIN" --chrome --permission-mode bypassPermissions "${_forward_args[@]}"
