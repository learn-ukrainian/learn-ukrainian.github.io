#!/bin/bash
# Single, deterministic entry point for Codex lifecycle hooks.
#
# Codex launches every matching command hook for an event concurrently. Keeping
# the Bash policy checks in one runner avoids redundant interpreter startup,
# makes their order deterministic, and prevents policy hooks from contending
# with each other for Git/GitHub state.

set -u

MODE="${1:-}"
PAYLOAD=$(cat)

SCRIPT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_DIR="$SCRIPT_ROOT/agents_extensions/shared/hooks"

payload_cwd=$(printf '%s' "$PAYLOAD" | jq -r '
  .tool_input.workdir
  // .tool_input.cwd
  // .tool_input.working_directory
  // .cwd
  // empty
' 2>/dev/null)
[ -n "$payload_cwd" ] || payload_cwd="$SCRIPT_ROOT"

COMMON_DIR=$(git -C "$payload_cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
  || COMMON_DIR=$(git -C "$SCRIPT_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
  || COMMON_DIR=""

if [ -n "$COMMON_DIR" ]; then
  CANONICAL_ROOT="$(dirname "$COMMON_DIR")"
else
  CANONICAL_ROOT="$SCRIPT_ROOT"
fi

PYTHON_BIN="$CANONICAL_ROOT/.venv/bin/python"

case "$MODE" in
  pre-tool-use)
    if [ ! -x "$PYTHON_BIN" ]; then
      printf 'Codex hook policy cannot run: project interpreter is missing at %s\n' \
        "$PYTHON_BIN" >&2
      exit 2
    fi

    printf '%s' "$PAYLOAD" \
      | "$PYTHON_BIN" "$SCRIPT_ROOT/scripts/agent_runtime/codex_hook_policy.py" \
        --python-bin "$PYTHON_BIN" \
        --hooks-dir "$HOOKS_DIR" \
        --canonical-root "$CANONICAL_ROOT"
    policy_rc=${PIPESTATUS[1]}
    [ "$policy_rc" -eq 0 ] || exit "$policy_rc"
    ;;

  post-tool-use)
    printf '%s' "$PAYLOAD" \
      | CLAUDE_PROJECT_DIR="$SCRIPT_ROOT" bash "$HOOKS_DIR/tool-timing.sh"
    printf '%s' "$PAYLOAD" \
      | CLAUDE_PROJECT_DIR="$SCRIPT_ROOT" bash "$HOOKS_DIR/stamp-pytest.sh"
    ;;

  user-prompt-submit)
    printf '%s' "$PAYLOAD" \
      | CLAUDE_PROJECT_DIR="$CANONICAL_ROOT" \
        LEARN_UK_HOOK_RECIPIENT=codex \
        bash "$HOOKS_DIR/check-gemini-inbox.sh"
    ;;

  *)
    printf 'Unknown Codex hook entry mode: %s\n' "$MODE" >&2
    exit 1
    ;;
esac
