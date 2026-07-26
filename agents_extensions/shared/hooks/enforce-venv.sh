#!/bin/bash
# Hook: PreToolUse (Bash) — Enforce .venv/bin/python usage
# Rewrites bare `python3` or `python` commands to the canonical project venv.
# Prevents accidentally using system Python instead of project venv.

# Read tool input from stdin
INPUT=$(cat)

# Extract the command from JSON
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Check if the command starts with an unqualified interpreter name.
# Match: "python3 ...", "python ...", but NOT ".venv/bin/python ..." or "/path/to/python ..."
if echo "$COMMAND" | grep -qE '^python3?[[:space:]]'; then
  # Already using venv? Skip.
  if echo "$COMMAND" | grep -qE '^\./\.venv/|^\.venv/|^/.*\.venv/'; then
    exit 0
  fi

  CANONICAL_ROOT="${LEARN_UK_CANONICAL_ROOT:-}"
  if [ -z "$CANONICAL_ROOT" ]; then
    TOOL_CWD=$(printf '%s' "$INPUT" | jq -r '
      .tool_input.workdir
      // .tool_input.cwd
      // .tool_input.working_directory
      // .cwd
      // empty
    ')
    [ -n "$TOOL_CWD" ] || TOOL_CWD="$PWD"
    COMMON_DIR=$(git -C "$TOOL_CWD" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
      || COMMON_DIR=""
    [ -z "$COMMON_DIR" ] || CANONICAL_ROOT="$(dirname "$COMMON_DIR")"
  fi

  PYTHON_BIN="${CANONICAL_ROOT:+$CANONICAL_ROOT/}.venv/bin/python"
  if [ ! -x "$PYTHON_BIN" ]; then
    printf 'Unqualified interpreter blocked: project venv is missing at %s\n' "$PYTHON_BIN" >&2
    exit 2
  fi

  case "$COMMAND" in
    python3*) FIXED="${PYTHON_BIN}${COMMAND#python3}" ;;
    python*) FIXED="${PYTHON_BIN}${COMMAND#python}" ;;
  esac

  if [ "${LEARN_UK_HOOK_PROVIDER:-claude}" = "codex" ]; then
    jq -n --arg command "$FIXED" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        updatedInput: {command: $command}
      }
    }'
  else
    jq -n --arg command "$FIXED" '{modifiedInput: {command: $command}}'
  fi
  exit 0
fi

# No modification needed
exit 0
