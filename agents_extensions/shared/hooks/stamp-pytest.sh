#!/bin/bash
# Hook: PostToolUse / PostToolUseFailure - stamp recent pytest runs for the #M-7 push guard.

set -u

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(</dev/stdin)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -n "$COMMAND" ] || exit 0

# Resolve project root robustly by walking up until package.json is found
DIR="$(cd "$(dirname "$0")" && pwd)"
while [ "$DIR" != "/" ] && [ ! -f "$DIR/package.json" ]; do
  DIR="$(dirname "$DIR")"
done
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$DIR}"
PYTHON="$PROJECT_DIR/.venv/bin/python"

HAS_PYTEST=1
if [ -x "$PYTHON" ]; then
  # Pass the entire JSON input to python to parse tool_output/tool_response if needed
  printf '%s' "$INPUT" | "$PYTHON" -c '
from __future__ import annotations

import json
import re
import shlex
import sys
from typing import Any

payload_str = sys.stdin.read()
command = ""
payload = {}
try:
    payload = json.loads(payload_str)
    if isinstance(payload, dict):
        command = (payload.get("tool_input") or {}).get("command") or payload.get("command") or ""
except Exception:
    command = payload_str

if not command:
    command = payload_str

if not isinstance(command, str) or not command.strip():
    sys.exit(1)

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
has_pytest = False
for seg in segments:
    i = 0
    while i < len(seg) and seg[i] in wrappers:
        i += 1
    if i >= len(seg):
        continue
    # Support absolute path python pytest runs (e.g. /abs/path/.venv/bin/python)
    is_python = seg[i] == ".venv/bin/python" or seg[i].endswith("/.venv/bin/python")
    if is_python and seg[i + 1 : i + 3] == ["-m", "pytest"]:
        has_pytest = True
        break
    if seg[i] == "pytest":
        has_pytest = True
        break
    if seg[i : i + 3] == ["dagger", "call", "pytest"]:
        has_pytest = True
        break

if not has_pytest:
    sys.exit(1)

# If the overall command succeeded (PostToolUse) or event name is empty (tests/fallback),
# we can touch the stamp immediately.
event_name = (payload.get("hook_event_name") if isinstance(payload, dict) else "") or ""
if event_name in ("PostToolUse", ""):
    sys.exit(0)

# If the overall command failed (PostToolUseFailure), we check if the pytest segment
# itself succeeded by parsing the tool output/stdout for a passing pytest summary.
# This prevents compound command failures (e.g. pytest && failing-cmd) from blocking pushes.
def _find_command_output(val: Any) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        for key in ("tool_output", "output", "result", "stdout", "stderr"):
            o = val.get(key)
            if isinstance(o, str) and o:
                return o
        for key in ("tool_response", "tool_input", "tool_result"):
            o = _find_command_output(val.get(key))
            if o:
                return o
        parts = []
        for v in val.values():
            o = _find_command_output(v)
            if o:
                parts.append(o)
        return "\n".join(parts)
    if isinstance(val, list):
        parts = []
        for item in val:
            o = _find_command_output(item)
            if o:
                parts.append(o)
        return "\n".join(parts)
    return ""

output_str = _find_command_output(payload)
pytest_summary_pattern = re.compile(
    r"(?:={2,}\s+)?(?:(?P<counts>[0-9a-zA-Z\s,]+)\s+in\s+(?P<duration>[0-9.]+)s)(?:\s+=+)?"
)
matches = list(pytest_summary_pattern.finditer(output_str))
if matches:
    last_match = matches[-1]
    counts = last_match.group("counts")
    if "failed" not in counts and "error" not in counts:
        sys.exit(0)

sys.exit(1)
'
  HAS_PYTEST=$?
else
  # Bash fallback if python is not available (only matches command on success event or empty event)
  EVENT_NAME=$(printf '%s' "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
  if [ -z "$EVENT_NAME" ] || [ "$EVENT_NAME" = "PostToolUse" ]; then
    if [[ "$COMMAND" =~ (^|[[:space:];|&])[^[:space:]]*\.venv/bin/python[[:space:]]+-m[[:space:]]+pytest($|[[:space:]]) ]] || \
       [[ "$COMMAND" =~ (^|[[:space:];|&])pytest($|[[:space:]]) ]] || \
       [[ "$COMMAND" =~ (^|[[:space:];|&])dagger[[:space:]]+call[[:space:]]+pytest($|[[:space:]]) ]]; then
      HAS_PYTEST=0
    fi
  fi
fi

[ "$HAS_PYTEST" -eq 0 ] || exit 0

BRANCH=$(git branch --show-current 2>/dev/null) || exit 0
[ -n "$BRANCH" ] || exit 0

STAMP="${TMPDIR:-/tmp}/learn-uk-pytest.${BRANCH}.stamp"
mkdir -p "$(dirname "$STAMP")" 2>/dev/null || exit 0
touch "$STAMP" 2>/dev/null || true

exit 0
