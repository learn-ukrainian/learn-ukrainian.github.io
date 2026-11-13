#!/bin/bash
# Hook: Check for unread cross-agent messages on every prompt submit.
# Serves every agent seat (claude/codex/gemini/agy/grok/orchestrator) via
# LEARN_UK_HOOK_RECIPIENT; the Gemini CLI seat is retired, the name is not.
# Uses the live inbox CLI so fleet-comms remains the authority for messages.
#
# Fast path (#8529): a read-only, 1 s-bounded unread COUNT against the same
# broker DB the CLI reads skips the Python bridge startup entirely when the
# inbox is empty. Any probe uncertainty falls through to the live CLI so
# messages are never hidden.
#
# PIPELINE GUARD: Skips during build_module / ai_agent_bridge runs
# to prevent ping-pong between automated pipeline phases.

# Skip in pipeline/headless mode
if [ "${GEMINI_SESSION:-}" = "1" ] || [ "${LEARN_UKRAINIAN_PIPELINE:-}" = "1" ]; then
  exit 0
fi

HOOK_INPUT=$(cat)
# Generated from scripts/lib/project_interpreter.sh, as for native_hook_command.
# Collapse "." and ".." segments of an absolute path without following
# symlinks (a symlinked .git must stay visible to the checks below).
_project_interpreter_normalize() {
    local part
    local -a parts out=()
    IFS=/ read -r -a parts <<< "$1"
    for part in ${parts[@]+"${parts[@]}"}; do
        case "$part" in
            ''|.) ;;
            ..) [ "${#out[@]}" -gt 0 ] && unset "out[$((${#out[@]} - 1))]" ;;
            *) out+=("$part") ;;
        esac
    done
    printf '/%s' ${out[@]+"${out[@]}"}
    printf '\n'
}

# Prints the physical path of directory <dir>, or returns 1. The x sentinel keeps
# a trailing newline $(...) would strip, so a directory is never checked as its
# clean namesake; a physical path with a newline cannot be checked faithfully by
# these helpers (or exported intact), so it refuses (#100).
_project_physical_dir() {
    local dir
    dir="$(cd -P "$1" 2>/dev/null && pwd -P && printf x)" || return 1
    dir="${dir%$'\n'x}"
    [[ "$dir" != *$'\n'* ]] || return 1
    printf '%s\n' "$dir"
}

# Prints the primary checkout root for <root>; when the checkout's git metadata
# is untrusted prints the reason instead and returns 1 (the caller captures
# stdout, so a global would be lost in the subshell).
#
# A `.git` directory or no `.git` at all (release snapshot) resolves to <root>
# itself and never to any other directory. So a worktree whose gitfile was
# removed resolves to its own root: the launcher passes its own directory
# (LC_ROOT), whose code it is already running, so that grants nothing new
# (#9121; pinned by test_snapshot_resolves_only_to_the_launcher_root).
_project_interpreter_primary_root() {
    local root="$1"
    local git_path="$root/.git"
    local line gitdir worktrees_dir common_git

    if [ -L "$git_path" ]; then
        printf '%s\n' "$git_path is a symlink"
        return 1
    fi
    if [ -d "$git_path" ] || [ ! -e "$git_path" ]; then
        printf '%s\n' "$root"
        return 0
    fi
    if [ ! -f "$git_path" ]; then
        printf '%s\n' "$git_path is not a file or directory"
        return 1
    fi

    IFS= read -r line < "$git_path" || true
    case "$line" in
        gitdir:*) ;;
        *)
            printf '%s\n' "$git_path is not a gitdir: pointer"
            return 1
            ;;
    esac
    gitdir="${line#gitdir:}"
    gitdir="${gitdir#"${gitdir%%[![:space:]]*}"}"
    gitdir="${gitdir%"${gitdir##*[![:space:]]}"}"
    case "$gitdir" in
        /*) ;;
        *) gitdir="$root/$gitdir" ;;
    esac
    gitdir="$(_project_interpreter_normalize "$gitdir")"
    worktrees_dir="$(dirname "$gitdir")"
    if [ "$(basename "$worktrees_dir")" != "worktrees" ] || [ ! -d "$gitdir" ]; then
        printf '%s\n' "$git_path gitdir is not <primary>/.git/worktrees/<name>"
        return 1
    fi
    common_git="$(dirname "$worktrees_dir")"
    if [ "$(basename "$common_git")" != ".git" ] \
        || [ -L "$common_git" ] || [ ! -d "$common_git" ] \
        || [ -L "$worktrees_dir" ] || [ -L "$gitdir" ]; then
        printf '%s\n' "$git_path gitdir is not under a real <primary>/.git directory"
        return 1
    fi
    if ! _project_interpreter_points_back "$gitdir" "$root"; then
        printf '%s\n' "$gitdir/gitdir does not point back at $git_path"
        return 1
    fi
    dirname "$common_git"
}

# True when <admin-dir>/gitdir (written by `git worktree add`, absolute or,
# with worktree.useRelativePaths, relative to <admin-dir>) names <root>/.git.
# <root> is physical; the pointer's directory is compared physically too.
_project_interpreter_points_back() {
    local admin_dir="$1" root="$2" pointer="" pointed_root

    [ -f "$admin_dir/gitdir" ] && [ ! -L "$admin_dir/gitdir" ] || return 1
    IFS= read -r pointer < "$admin_dir/gitdir" || true
    pointer="${pointer#"${pointer%%[![:space:]]*}"}"
    pointer="${pointer%"${pointer##*[![:space:]]}"}"
    [ -n "$pointer" ] || return 1
    case "$pointer" in
        /*) ;;
        *) pointer="$admin_dir/$pointer" ;;
    esac
    [ "$(basename "$pointer")" = ".git" ] || return 1
    pointed_root="$(_project_physical_dir "$(dirname "$pointer")")" || return 1
    [ "$pointed_root" = "$root" ]
}

project_primary_root_resolve() {
    local root primary

    root="$(_project_physical_dir "${1:?project_primary_root_resolve: checkout root required}")" || {
        echo "Error: untrusted git metadata: checkout root $1 does not exist or its path has a newline" >&2
        return 1
    }
    if ! primary="$(_project_interpreter_primary_root "$root")"; then
        echo "Error: untrusted git metadata: $primary" >&2
        return 1
    fi
    printf '%s\n' "$primary"
}

project_interpreter_configured() {
    local configured="${LEARN_UKRAINIAN_PYTHON:-}"

    [ -n "$configured" ] || return 0
    case "$configured" in
        /*) ;;
        *)
            echo "Error: project interpreter not found: LEARN_UKRAINIAN_PYTHON must be an absolute path, got $configured" >&2
            return 1
            ;;
    esac
    if [ ! -f "$configured" ] || [ ! -x "$configured" ]; then
        echo "Error: project interpreter not found: LEARN_UKRAINIAN_PYTHON=$configured is not an executable file" >&2
        return 1
    fi
    printf '%s\n' "$configured"
}

project_interpreter_resolve() {
    local root primary primary_python tried configured

    configured="$(project_interpreter_configured)" || return 1
    if [ -n "$configured" ]; then
        printf '%s\n' "$configured"
        return 0
    fi
    root="$(_project_physical_dir "${1:?project_interpreter_resolve: checkout root required}")" || {
        echo "Error: project interpreter not found: checkout root $1 does not exist or its path has a newline" >&2
        return 1
    }
    if ! primary="$(_project_interpreter_primary_root "$root")"; then
        echo "Error: project interpreter not found: $root/.venv/bin/python not used ($primary)" >&2
        return 1
    fi
    primary_python="$primary/.venv/bin/python"
    if [ -f "$primary_python" ] && [ -x "$primary_python" ]; then
        printf '%s\n' "$primary_python"
        return 0
    fi
    tried="$primary_python"
    if [ "$primary" != "$root" ]; then
        tried="$tried (worktree-local $root/.venv/bin/python is not used)"
    fi
    echo "Error: project interpreter not found: $tried" >&2
    return 1
}

# _project_hook_git_layout <checkout>
#   true when <checkout>/.git passes Git's own repository test, as
#   repo_root._is_primary_git_layout applies it (stricter here: a symlinked HEAD
#   refuses): a real directory without commondir, with objects, refs and a valid
#   HEAD (`ref: refs/...` or a 40/64-hex object id). An empty or stray .git is not
#   a primary.
_project_hook_git_layout() {
    local git_dir="$1/.git" head=""
    [[ -d "$git_dir" && ! -L "$git_dir" ]] || return 1
    [[ ! -e "$git_dir/commondir" && ! -L "$git_dir/commondir" ]] || return 1
    [[ -d "$git_dir/objects" && -d "$git_dir/refs" ]] || return 1
    [[ -f "$git_dir/HEAD" && ! -L "$git_dir/HEAD" ]] || return 1
    IFS= read -r head < "$git_dir/HEAD" || true
    case "$head" in
        ref:*)
            head="${head#ref:}"
            [[ "${head#"${head%%[![:space:]]*}"}" = refs/* ]]
            ;;
        *) [[ "$head" =~ ^[0-9a-fA-F]{40}([0-9a-fA-F]{24})?$ ]] ;;
    esac
}

# project_hook_roots_resolve [<product-root>]
#   exports LU_PRODUCT_ROOT and LEARN_UKRAINIAN_PRIMARY_REPO_ROOT (exit 0), or
#   exports nothing (exit 1). The product is the argument when one is given,
#   else LU_PRODUCT_ROOT, else CLAUDE_PROJECT_DIR, else the nearest physical
#   ancestor of the working directory that has a .git entry; never this
#   library's location. The first candidate given is the only one considered.
#   The shared-state anchor is LEARN_UKRAINIAN_PRIMARY_REPO_ROOT when set, else
#   the product's validated primary. A product with a .git entry must resolve
#   to a primary, and the anchor must be one: both pass _project_hook_git_layout.
#   A set LEARN_UKRAINIAN_STATE_ROOT must name the anchor. A release snapshot
#   (no .git) therefore needs an explicit anchor.
project_hook_roots_resolve() {
    local root="${1-${LU_PRODUCT_ROOT:-${CLAUDE_PROJECT_DIR:-}}}"
    local primary state_root state_config invocation
    # Configured roots keep precedence, but cannot hide malformed invocation metadata.
    # Every directory below is checked by its exact physical path; one whose path has
    # a newline refuses (_project_physical_dir).
    invocation="$(_project_physical_dir .)" || return 1
    while [[ ! -e "$invocation/.git" && ! -L "$invocation/.git" && "$invocation" != / ]]; do
        invocation="${invocation%/*}"
        [[ -n "$invocation" ]] || invocation=/
    done
    if [[ -e "$invocation/.git" || -L "$invocation/.git" ]]; then
        primary="$(project_primary_root_resolve "$invocation")" || return 1
        _project_hook_git_layout "$primary" || return 1
    fi
    if [[ -z "$root" ]]; then
        root="$(pwd -P)" || return 1
        while [[ ! -e "$root/.git" && ! -L "$root/.git" ]]; do
            [[ "$root" != / ]] || return 1
            root="${root%/*}"
            [[ -n "$root" ]] || root=/
        done
    fi
    [[ "$root" = /* && -d "$root" ]] || return 1
    primary="$(project_primary_root_resolve "$root")" || return 1
    # A product with a .git entry must resolve to a real primary, whatever
    # anchor is configured: an empty or stray .git directory would otherwise
    # make the product its own primary and its .venv the interpreter.
    if [[ -e "$root/.git" || -L "$root/.git" ]]; then
        _project_hook_git_layout "$primary" || return 1
    fi
    state_root="${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-$primary}"
    [[ "$state_root" = /* ]] || return 1
    state_root="$(_project_physical_dir "$state_root")" && _project_hook_git_layout "$state_root" || return 1
    if [[ -n "${LEARN_UKRAINIAN_STATE_ROOT:-}" ]]; then
        [[ "$LEARN_UKRAINIAN_STATE_ROOT" = /* ]] || return 1
        state_config="$(_project_physical_dir "$LEARN_UKRAINIAN_STATE_ROOT")" || return 1
        [[ "$state_config" = "$state_root" ]] || return 1
    fi
    export LU_PRODUCT_ROOT="$root"
    export LEARN_UKRAINIAN_PRIMARY_REPO_ROOT="$state_root"
}

# project_hook_context_resolve [<product-root>]
#   needs a configured LEARN_UKRAINIAN_PRIMARY_REPO_ROOT; then
#   project_hook_roots_resolve, and exports LEARN_UKRAINIAN_PYTHON: the
#   configured absolute executable, else the configured primary's .venv python
#   (exit 0); exit 1 otherwise, before any interpreter starts. The product's own
#   Git metadata never names the primary or the interpreter: whoever works in a
#   checkout can rewrite it, and no local check tells it from a real primary
#   (#100).
project_hook_context_resolve() {
    local interpreter
    [[ -n "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-}" ]] || return 1
    project_hook_roots_resolve "$@" || return 1
    interpreter="$(project_interpreter_resolve "$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT")" || return 1
    export LEARN_UKRAINIAN_PYTHON="$interpreter"
}

project_hook_context_resolve 2>/dev/null || {
  echo "HOOK-BOOTSTRAP-FAILED: product root, shared state, interpreter or machinery unavailable." >&2
  exit 1
}
PROJECT_DIR="$LU_PRODUCT_ROOT"
INBOX_PYTHON="$LEARN_UKRAINIAN_PYTHON"
RECIPIENT="${LEARN_UK_HOOK_RECIPIENT:-claude}"

case "$RECIPIENT" in
  claude|codex|gemini|agy|grok|orchestrator) ;;
  *) exit 0 ;;
esac

RECIPIENT_LABEL=$(printf '%s' "$RECIPIENT" | tr '[:lower:]' '[:upper:]')

# Fast path: probe the same broker DB the bridge CLI reads
# (scripts/ai_agent_bridge/_config.py DB_PATH → _messaging.py check_inbox)
# with a read-only, 1 s-bounded unread count. Zero unread → exit silently
# without paying the Python bridge startup. DB missing/locked/error, schema
# drift, or an inconclusive result → fall through to the live CLI below.
DB_FILE="${AB_DB_PATH:-}"
if [ -z "$DB_FILE" ]; then
  GIT_COMMON_DIR=$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
  if [ -n "$GIT_COMMON_DIR" ]; then
    DB_FILE="$(dirname "$GIT_COMMON_DIR")/.mcp/servers/message-broker/messages.db"
  fi
fi

if [ -n "$DB_FILE" ] && [ -f "$DB_FILE" ]; then
  # Mirror check_inbox recipient resolution for the seats this hook serves:
  # resolve_recipient_alias is identity for registered seats, and
  # seat_read_aliases dual-reads only grok ↔ grok-build. RECIPIENT is already
  # whitelisted above, so interpolating it into SQL cannot inject.
  case "$RECIPIENT" in
    grok|grok-build) TO_LLM_SQL="'grok','grok-build'" ;;
    *) TO_LLM_SQL="'$RECIPIENT'" ;;
  esac
  # "unread" matches _message_consumption_state: neither acknowledged nor
  # consumed by a live driver (NULL is falsy in Python, 0 via COALESCE here).
  UNREAD_COUNT=""
  if command -v sqlite3 >/dev/null 2>&1; then
    UNREAD_COUNT=$(sqlite3 -readonly -cmd ".timeout 1000" "$DB_FILE" \
      "SELECT COUNT(*) FROM messages WHERE to_llm IN ($TO_LLM_SQL) AND COALESCE(acknowledged, 0) = 0 AND COALESCE(consumed_by_live_driver, 0) = 0;" \
      2>/dev/null || true)
  else
    # stdlib-only fallback for hosts without the sqlite3 CLI; prints nothing
    # on any error so the live CLI below stays the authority.
    UNREAD_COUNT=$("$INBOX_PYTHON" -I - "$DB_FILE" "$RECIPIENT" <<'PYEOF'
import sqlite3
import sys
from pathlib import Path

db, recipient = sys.argv[1], sys.argv[2]
recipients = ("grok", "grok-build") if recipient in ("grok", "grok-build") else (recipient,)
try:
    conn = sqlite3.connect(Path(db).resolve().as_uri() + "?mode=ro", uri=True, timeout=1.0)
    try:
        placeholders = ",".join("?" * len(recipients))
        row = conn.execute(
            f"SELECT COUNT(*) FROM messages WHERE to_llm IN ({placeholders}) "
            "AND COALESCE(acknowledged, 0) = 0 AND COALESCE(consumed_by_live_driver, 0) = 0",
            recipients,
        ).fetchone()
        print(row[0])
    finally:
        conn.close()
except Exception:
    pass
PYEOF
    )
  fi
  case "$UNREAD_COUNT" in
    ''|*[!0-9]*) ;;  # probe inconclusive → the live CLI decides below
    0) exit 0 ;;
  esac
fi

# Ask the live CLI for the recipient's inbox. Keep its existing output as the
# source of both the count and the bounded preview; the fast path above only
# ever short-circuits a proven-empty inbox, never replaces this listing.
INBOX_OUTPUT=$("$INBOX_PYTHON" -I -m lu_machinery.ai_agent_bridge inbox --for "$RECIPIENT" 2>/dev/null) || exit 0

# The legacy human listing emits `N unread`; the live channel listing emits a
# `pending: N` line. Accept both existing CLI shapes without creating a new
# output protocol for the hook.
COUNT=$(printf '%s\n' "$INBOX_OUTPUT" | sed -nE \
  -e 's/.*:[[:space:]]*([0-9]+)[[:space:]]+unread.*/\1/p' \
  -e 's/^[[:space:]]*pending:[[:space:]]*([0-9]+).*/\1/p' | head -n 1)

# Keep the pending IDs separate from previews: session-local dedupe state may
# never contain message content. The CLI's human listing places the state in
# the second bracket; `pending` covers the live channel listing if it exposes
# delivery IDs in the same row shape.
PENDING_IDS=$(printf '%s\n' "$INBOX_OUTPUT" | sed -nE \
  's/^[[:space:]]*\[([^]]+)\][[:space:]]*\[(unread|pending)\].*/\1/p')

case "$COUNT" in
  ''|*[!0-9]*)
    COUNT=$(printf '%s\n' "$PENDING_IDS" | sed '/^$/d' | wc -l | tr -d ' ')
    ;;
esac

if [ -z "$COUNT" ] || [ "$COUNT" -eq 0 ]; then
  exit 0
fi

# A structured count without IDs still deserves a notification. Use only the
# count as the body-free fallback dedupe key; human listings use their exact
# pending ID list.
if [ -z "$PENDING_IDS" ]; then
  PENDING_IDS="count:${COUNT}"
fi

# A UserPromptSubmit hook can fire repeatedly before another worker claims or
# acknowledges its message. Suppress only an identical recipient/session ID
# list. No session identity or unavailable state is deliberately fail-open.
SESSION_ID="${LEARN_UK_HOOK_SESSION_ID:-${LEARN_UKRAINIAN_SESSION_ID:-${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}}}"
if [ -z "$SESSION_ID" ]; then
  SESSION_ID=$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
fi
if [ -n "$SESSION_ID" ]; then
  STATE_DIR="$PROJECT_DIR/.agent/runtime"
  STATE_KEY=""
  if command -v shasum >/dev/null 2>&1; then
    STATE_KEY=$(printf '%s\n%s' "$RECIPIENT" "$SESSION_ID" | shasum -a 256 | awk '{print $1}')
  fi
  STATE_FILE="$STATE_DIR/inbox-${STATE_KEY}.ids"
  if [ -n "$STATE_KEY" ] && mkdir -p "$STATE_DIR" 2>/dev/null; then
    STATE_TMP=$(mktemp "$STATE_DIR/.inbox-${STATE_KEY}.XXXXXX" 2>/dev/null || true)
    if [ -n "$STATE_TMP" ]; then
      printf '%s\n' "$PENDING_IDS" > "$STATE_TMP"
      if [ -f "$STATE_FILE" ] && cmp -s "$STATE_TMP" "$STATE_FILE"; then
        rm -f "$STATE_TMP"
        exit 0
      fi
      if ! mv -f "$STATE_TMP" "$STATE_FILE" 2>/dev/null; then
        rm -f "$STATE_TMP"
      fi
    fi
  fi
fi

# Surface at most five rows from the CLI's own human listing. The following
# line is the CLI-provided preview, not a second read of message content.
PREVIEWS=$(printf '%s\n' "$INBOX_OUTPUT" | awk '
  /^[[:space:]]*\[[^]]+\][[:space:]]*\[(unread|pending)\]/ {
    if (shown >= 5) exit
    print
    if (getline > 0) print
    shown++
  }
')

# The live channel listing reports one bounded preview after this marker
# instead of exposing message IDs. Preserve that existing preview shape.
if [ -z "$PREVIEWS" ]; then
  PREVIEWS=$(printf '%s\n' "$INBOX_OUTPUT" | awk '
    /^[[:space:]]*oldest preview:[[:space:]]*$/ { capture = 1; next }
    capture && NF {
      print
      shown++
      if (shown >= 5) exit
    }
  ')
fi

CONTEXT="${RECIPIENT_LABEL} INBOX: ${COUNT} unread message(s) waiting.
---"

if [ -n "$PREVIEWS" ]; then
  CONTEXT="${CONTEXT}
${PREVIEWS}"
fi

INBOX_MODULE=lu_machinery.ai_agent_bridge
CONTEXT="${CONTEXT}
---
.venv/bin/python -m ${INBOX_MODULE} inbox --for ${RECIPIENT}"

jq -n --arg msg "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$msg}}'

exit 0
