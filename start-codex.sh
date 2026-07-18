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

if [ "$(git -C "$PROJECT_DIR" branch --show-current)" != "main" ]; then
    printf 'Error: canonical checkout must be on main: %s\n' "$PROJECT_DIR" >&2
    exit 1
fi

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
    --enable multi_agent \
    -C "$PROJECT_DIR" \
    "$@"
