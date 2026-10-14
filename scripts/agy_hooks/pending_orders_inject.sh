#!/bin/sh
# Read-only AGY PreInvocation announcement. Never persist stdin or probe output.
fallback='{"injectSteps":[{"ephemeralMessage":"PENDING ORDERS: unknown; legacy: ai_agent_bridge inbox for the registered handoff slot; authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"}]}'
root=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || { cat >/dev/null; printf '%s\n' "$fallback"; exit 0; }
# Resolve the shared interpreter for linked worktrees without a worktree venv.
primary=$root
if [ -f "$root/.git" ]; then
    common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || common=
    [ -z "$common" ] || primary=$(dirname "$common")
fi
py="${LU_DRIVER_STATE_PYTHON:-$primary/.venv/bin/python}"
if [ ! -x "$py" ]; then
    cat >/dev/null
    printf '%s\n' "$fallback"
    exit 0
fi
# The child drains stdin; on early import/exec failure the parent drains the rest.
if output=$(cd "$root" && "$py" -m scripts.inbox_pending --agy-hook 2>/dev/null); then
    child_ok=1
else
    child_ok=0
fi
cat >/dev/null
if [ "$child_ok" = 1 ] && validated=$(printf '%s' "$output" | "$py" -c '
import json, sys
value = json.load(sys.stdin)
if value != {}:
    assert set(value) == {"injectSteps"}
    steps = value["injectSteps"]
    assert isinstance(steps, list) and len(steps) == 1
    assert set(steps[0]) == {"ephemeralMessage"}
    line = steps[0]["ephemeralMessage"]
    assert isinstance(line, str) and line.startswith("PENDING ORDERS: ")
    assert len(line) <= 200 and line.isascii() and all(32 <= ord(c) < 127 for c in line)
print(json.dumps(value, separators=(",", ":")))
' 2>/dev/null); then
    printf '%s\n' "$validated"
else
    printf '%s\n' "$fallback"
fi
exit 0
