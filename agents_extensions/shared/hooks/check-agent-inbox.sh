#!/bin/bash
# Metadata-only authority inbox announcement. Readers never claim or read bodies.
if [ "${GEMINI_SESSION:-}" = "1" ] || [ "${LEARN_UKRAINIAN_PIPELINE:-}" = "1" ]; then
  exit 0
fi
cat >/dev/null
fallback='{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"AUTHORITY INBOX: unknown; oldest unknown; .venv/bin/python -m scripts.fleet_comms deliveries --help"}}'
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || common=
primary="${common%/.git}"
py="${LU_DRIVER_STATE_PYTHON:-$primary/.venv/bin/python}"
recipient="${SESSION_HANDOFF_AGENT:-${LEARN_UK_HOOK_RECIPIENT:-claude}}"
if [ ! -x "$py" ]; then
  printf '%s\n' "$fallback"
  exit 0
fi
if command -v timeout >/dev/null 2>&1; then
  output=$(cd "$root" && timeout 3s "$py" -m scripts.inbox_pending --native-hook --recipient "$recipient" 2>/dev/null) || output=
else
  output=$(cd "$root" && "$py" -m scripts.inbox_pending --native-hook --recipient "$recipient" 2>/dev/null) || output=
fi
if [ -n "$output" ] && validated=$(printf '%s' "$output" | "$py" -c '
import json, sys
value = json.load(sys.stdin)
assert set(value) == {"hookSpecificOutput"}
context = value["hookSpecificOutput"]
assert set(context) == {"hookEventName", "additionalContext"}
assert context["hookEventName"] == "UserPromptSubmit"
line = context["additionalContext"]
assert isinstance(line, str) and line.startswith("AUTHORITY INBOX: ")
assert len(line) <= 500 and line.isascii() and all(32 <= ord(c) < 127 for c in line)
print(json.dumps(value, separators=(",", ":")))
' 2>/dev/null); then
  printf '%s\n' "$validated"
else
  printf '%s\n' "$fallback"
fi
exit 0
