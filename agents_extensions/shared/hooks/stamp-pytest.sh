#!/bin/bash
# Hook: PostToolUse - stamp recent pytest runs for the #M-7 push guard.

set -u

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(</dev/stdin)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -n "$COMMAND" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PYTHON="$PROJECT_DIR/.venv/bin/python"

HAS_PYTEST=1
if [ -x "$PYTHON" ]; then
  printf '%s' "$COMMAND" | "$PYTHON" -c '
from __future__ import annotations

import shlex
import sys

command = sys.stdin.read()
try:
    tokens = shlex.split(command, posix=True)
except ValueError:
    sys.exit(1)

segments = []
current = []
for tok in tokens:
    if tok in ("&&", "||", ";", "|"):
        if current:
            segments.append(current)
            current = []
    else:
        current.append(tok)
if current:
    segments.append(current)

wrappers = {"sudo", "time", "env", "nohup"}
for seg in segments:
    i = 0
    while i < len(seg) and seg[i] in wrappers:
        i += 1
    if i >= len(seg):
        continue
    if seg[i] in {".venv/bin/python", "./.venv/bin/python"} and seg[i + 1 : i + 3] == ["-m", "pytest"]:
        sys.exit(0)
    if seg[i] == "pytest":
        sys.exit(0)
    if seg[i : i + 3] == ["dagger", "call", "pytest"]:
        sys.exit(0)
sys.exit(1)
'
  HAS_PYTEST=$?
else
  if [[ "$COMMAND" =~ (^|[[:space:];|&])(\./)?\.venv/bin/python[[:space:]]+-m[[:space:]]+pytest($|[[:space:]]) ]] || \
     [[ "$COMMAND" =~ (^|[[:space:];|&])pytest($|[[:space:]]) ]] || \
     [[ "$COMMAND" =~ (^|[[:space:];|&])dagger[[:space:]]+call[[:space:]]+pytest($|[[:space:]]) ]]; then
    HAS_PYTEST=0
  fi
fi

[ "$HAS_PYTEST" -eq 0 ] || exit 0

BRANCH=$(git branch --show-current 2>/dev/null) || exit 0
[ -n "$BRANCH" ] || exit 0

STAMP="${TMPDIR:-/tmp}/learn-uk-pytest.${BRANCH}.stamp"
mkdir -p "$(dirname "$STAMP")" 2>/dev/null || exit 0
touch "$STAMP" 2>/dev/null || true

exit 0
