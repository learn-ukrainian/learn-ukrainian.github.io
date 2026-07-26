#!/bin/bash
# Hook: PostToolUse / PostToolUseFailure — record proven pytest success for #M-7.

set -u

SOURCE_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$SOURCE_ROOT" != "/" ] && [ ! -f "$SOURCE_ROOT/package.json" ]; do
  SOURCE_ROOT="$(dirname "$SOURCE_ROOT")"
done
[ -f "$SOURCE_ROOT/package.json" ] || exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$SOURCE_ROOT}"
PYTHON="$PROJECT_ROOT/.venv/bin/python"
HELPER="$PROJECT_ROOT/.githooks/pytest_stamp.py"

if [ ! -x "$PYTHON" ]; then
  COMMON_DIR=$(git -C "$SOURCE_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0
  PRIMARY_ROOT="$(dirname "$COMMON_DIR")"
  PYTHON="$PRIMARY_ROOT/.venv/bin/python"
fi

# Do not fall back to python/python3 from PATH. Repository commands require the
# project venv, and a system interpreter can belong to another checkout or lack
# pinned dependencies (#5134). Stamping is observational: no proven project
# interpreter means no marker, and the later pre-push guard remains fail-closed.
[ -x "$PYTHON" ] || exit 0
[ -f "$HELPER" ] || HELPER="$SOURCE_ROOT/.githooks/pytest_stamp.py"
[ -f "$HELPER" ] || exit 0

exec "$PYTHON" "$HELPER"
