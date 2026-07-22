#!/bin/bash
# Launch interactive Codex from the repository's canonical main checkout.

set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:${PATH:-}"
# Avoid optional index refresh locks while the primary checkout is used for
# orientation. Task writes still belong in scoped dispatch worktrees.
export GIT_OPTIONAL_LOCKS=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_COMMON_DIR="$(git -C "$SCRIPT_DIR" rev-parse --path-format=absolute --git-common-dir)"
PROJECT_DIR="${CODEX_CANONICAL_REPO_ROOT:-}"

# Git cannot recover a primary working-tree path from a linked worktree when
# the repository was created with --separate-git-dir. Allow that uncommon
# layout to name the canonical checkout explicitly, but accept only the root
# of this same repository; the main-branch check below still applies.
if [ -n "$PROJECT_DIR" ]; then
    REQUESTED_PROJECT_DIR="$PROJECT_DIR"
    if ! PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd)"; then
        printf 'Error: CODEX_CANONICAL_REPO_ROOT is not a directory: %s\n' \
            "$REQUESTED_PROJECT_DIR" >&2
        exit 1
    fi
    if ! OVERRIDE_COMMON_DIR="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
        || [ "$OVERRIDE_COMMON_DIR" != "$GIT_COMMON_DIR" ] \
        || [ "$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null)" != "$PROJECT_DIR" ]; then
        printf 'Error: CODEX_CANONICAL_REPO_ROOT is not a checkout of Git common dir: %s\n' \
            "$GIT_COMMON_DIR" >&2
        exit 1
    fi
fi

if [ -z "$PROJECT_DIR" ]; then
    CURRENT_WORKTREE=""
    while IFS= read -r -d '' record; do
        case "$record" in
            worktree\ *)
                CURRENT_WORKTREE="${record#worktree }"
                ;;
            "branch refs/heads/main")
                if [ -d "$CURRENT_WORKTREE" ] \
                    && [ "$(git -C "$CURRENT_WORKTREE" rev-parse --show-toplevel 2>/dev/null)" = "$CURRENT_WORKTREE" ]; then
                    PROJECT_DIR="$CURRENT_WORKTREE"
                    break
                fi
                ;;
        esac
    done < <(git -C "$SCRIPT_DIR" worktree list --porcelain -z)
fi

if [ -z "$PROJECT_DIR" ] && [ "$(git -C "$SCRIPT_DIR" branch --show-current)" = "main" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
fi
if [ -z "$PROJECT_DIR" ]; then
    printf 'Error: could not resolve a canonical main checkout for Git common dir: %s\n' \
        "$GIT_COMMON_DIR" >&2
    exit 1
fi

# Primary must be *attached* to main (not detached SHA) — #4857.
if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
    && [ -f "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" ]; then
    if ! "$PROJECT_DIR/.venv/bin/python" \
        "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" \
        --cwd "$PROJECT_DIR" --heal; then
        printf 'Error: primary checkout must be on main (heal failed): %s\n' \
            "$PROJECT_DIR" >&2
        exit 1
    fi
elif [ "$(git -C "$PROJECT_DIR" branch --show-current)" != "main" ]; then
    printf 'Error: canonical checkout must be on main: %s\n' "$PROJECT_DIR" >&2
    exit 1
fi

# `--epic` is a launcher-only lane binding. Codex itself does not know this
# flag, so consume it before exec while preserving all other argv bytes and
# ordering. An explicit epic gets a provider-specific handoff namespace; this
# prevents unrelated Codex epic sessions from sharing one rollover queue.
FORWARD_ARGS=("$@")
FORWARD_ARG_COUNT=$#
HANDOFF_IDENTITY_SH="$PROJECT_DIR/scripts/lib/handoff_identity.sh"
if [ ! -f "$HANDOFF_IDENTITY_SH" ]; then
    printf 'Error: handoff identity helper is missing: %s\n' "$HANDOFF_IDENTITY_SH" >&2
    exit 1
fi
# shellcheck source=scripts/lib/handoff_identity.sh
source "$HANDOFF_IDENTITY_SH"

SELECTED_EPIC="$(handoff_epic_from_argv "$@")"
if [ -z "$SELECTED_EPIC" ] && epic_flag_present "$@"; then
    printf 'Error: --epic requires a non-empty value (for example: --epic hramatka).\n' >&2
    exit 1
fi
if [ -n "$SELECTED_EPIC" ]; then
    if ! epic_name_valid "$SELECTED_EPIC"; then
        printf "Error: invalid --epic name '%s' (use lowercase letters, digits, and inner hyphens).\n" \
            "$SELECTED_EPIC" >&2
        exit 1
    fi
    HANDOFF_SLOT="$(handoff_identity_for_codex_epic "$SELECTED_EPIC")"
    if [ -z "$HANDOFF_SLOT" ]; then
        printf "Error: could not derive a Codex handoff slot for epic '%s'.\n" "$SELECTED_EPIC" >&2
        exit 1
    fi
    export SESSION_EPIC="$SELECTED_EPIC"
    export SESSION_HANDOFF_AGENT="$HANDOFF_SLOT"
    FORWARD_ARGS=()
    FORWARD_ARG_COUNT=0
    while IFS= read -r -d '' FORWARD_ARG; do
        FORWARD_ARGS+=("$FORWARD_ARG")
        FORWARD_ARG_COUNT=$((FORWARD_ARG_COUNT + 1))
    done < <(strip_epic_from_argv "$@")
    unset FORWARD_ARG HANDOFF_SLOT
    printf 'Epic assignment: %s.epic\n' "$SESSION_EPIC"
    printf 'Handoff identity: %s\n' "$SESSION_HANDOFF_AGENT"
    # Fleet-comms dual-aware banner (Codex loads AGENTS.md + /api/rules for full doctrine).
    if [ -f "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh" ]; then
        # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
        source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
        if command -v fleet_comms_resolve_plane_mode >/dev/null 2>&1; then
            export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
        fi
        if command -v fleet_comms_print_banner_line >/dev/null 2>&1; then
            fleet_comms_print_banner_line
        fi
    fi
fi
unset HANDOFF_IDENTITY_SH SELECTED_EPIC

# macOS ships Bash 3.2, where expanding an empty indexed array under `set -u`
# fails even when the array was explicitly initialized. Move the filtered
# values back into the special positional-parameter array, whose empty
# expansion is nounset-safe, before any later loops or the final exec.
if [ "$FORWARD_ARG_COUNT" -gt 0 ]; then
    set -- "${FORWARD_ARGS[@]}"
else
    set --
fi
unset FORWARD_ARGS FORWARD_ARG_COUNT

# Keep generated Codex config and the canonical rollover state ready before
# replacing this wrapper process with the interactive CLI.
# PROJECT_DIR is resolved dynamically.
# shellcheck disable=SC1091
source "$PROJECT_DIR/scripts/lib/thread_rollover_link.sh"
bootstrap_codex_checkout "$PROJECT_DIR" "$PROJECT_DIR" continue

# Resolve the native Codex route before SessionStart so context-budget hooks
# receive an explicit, model-checked denominator. An explicit --model/-m is
# validated now; when Codex uses config.toml, SessionStart validates the model
# reported by the CLI before trusting the profile.
SELECTED_MODEL=""
PREVIOUS_ARG=""
for arg in "$@"; do
    case "$arg" in
        --model=*)
            SELECTED_MODEL="${arg#--model=}"
            ;;
    esac
    if [ "$PREVIOUS_ARG" = "--model" ] || [ "$PREVIOUS_ARG" = "-m" ]; then
        SELECTED_MODEL="$arg"
    fi
    PREVIOUS_ARG="$arg"
done

REQUESTED_PROFILE="native_codex"
# shellcheck disable=SC1091
source "$PROJECT_DIR/scripts/lib/profile_resolver.sh"
if ! resolve_context_profile "$REQUESTED_PROFILE" "$SELECTED_MODEL"; then
    printf 'Error: failed to resolve Codex context profile %s.\n' "$REQUESTED_PROFILE" >&2
    exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ]; then
    printf 'Warning: untrusted Codex route (%s); using compact fallback without a fabricated context window.\n' \
        "$LEARN_UKRAINIAN_RESOLUTION_REASON" >&2
fi

export CODEX_SESSION=1
export CODEX_CANONICAL_REPO_ROOT="$PROJECT_DIR"

printf 'Context profile: id=%s model=%s window=%s budget=%s reason=%s\n' \
    "$LEARN_UKRAINIAN_PROFILE_ID" \
    "$LEARN_UKRAINIAN_MAIN_MODEL_ID" \
    "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS" \
    "$LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS" \
    "$LEARN_UKRAINIAN_RESOLUTION_REASON"
printf 'Starting Codex in %s\n' "$PROJECT_DIR"
exec codex \
    --dangerously-bypass-approvals-and-sandbox \
    --search \
    --enable multi_agent_v2 \
    -c agents.max_concurrent_threads_per_session=3 \
    -c 'agents.default_subagent_model="gpt-5.6-terra"' \
    -c 'agents.default_subagent_reasoning_effort="medium"' \
    -c agents.interrupt_message=true \
    -c features.multi_agent_v2.hide_spawn_agent_metadata=false \
    -c 'tui.status_line=["model-with-reasoning","status","context-used","context-window-size","five-hour-limit","weekly-limit","git-branch","task-progress"]' \
    -C "$PROJECT_DIR" \
    "$@"
