#!/bin/bash
# Hook: PreToolUse (Bash) — Enforce .venv/bin/python usage.
# Rejects bare `python3` or `python` commands with one copyable replacement.
# It never rewrites a command behind the caller's back.

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

  PYTHON_VERSION_FILE="${CANONICAL_ROOT:+$CANONICAL_ROOT/}.python-version"
  if [ ! -f "$PYTHON_VERSION_FILE" ]; then
    printf 'Unqualified interpreter blocked: project Python pin is missing at %s\n' \
      "$PYTHON_VERSION_FILE" >&2
    exit 2
  fi
  EXPECTED_PYTHON_VERSION=$(head -1 "$PYTHON_VERSION_FILE" | tr -d '[:space:]')
  ACTUAL_PYTHON_VERSION=$("$PYTHON_BIN" --version 2>&1)
  if [ -z "$EXPECTED_PYTHON_VERSION" ] \
    || [ "$ACTUAL_PYTHON_VERSION" != "Python $EXPECTED_PYTHON_VERSION" ]; then
    printf 'Unqualified interpreter blocked: expected Python %s, got %s\n' \
      "${EXPECTED_PYTHON_VERSION:-<missing pin>}" "${ACTUAL_PYTHON_VERSION:-<unavailable>}" >&2
    exit 2
  fi

  printf -v QUOTED_PYTHON '%q' "$PYTHON_BIN"
  case "$COMMAND" in
    python3*) FIXED="${QUOTED_PYTHON}${COMMAND#python3}" ;;
    python*) FIXED="${QUOTED_PYTHON}${COMMAND#python}" ;;
  esac

  printf 'Unqualified interpreter blocked. Run this command instead:\n  %s\n' "$FIXED" >&2
  exit 2
fi

# Qualified commands pass through unchanged.
exit 0
