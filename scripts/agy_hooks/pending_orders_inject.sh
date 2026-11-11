#!/usr/bin/env bash
# Read-only AGY PreInvocation announcement. Never persist stdin or probe output.
# The product, shared-state anchor and interpreter come from the one hook rule,
# project_hook_context_resolve (lib/project_interpreter.sh), before the child
# starts. Without that context the hook denies with the bootstrap diagnostic;
# "unknown" is kept for a child that ran and could not read its stores.
fleet_module=scripts.fleet_comms
fallback='{"injectSteps":[{"ephemeralMessage":"PENDING ORDERS: unknown; legacy: ai_agent_bridge inbox for the registered handoff slot; authority: project interpreter -m '"$fleet_module"' deliveries --help"}]}'
bootstrap_failed() {
    cat >/dev/null 2>&1
    printf '%s\n' 'HOOK-BOOTSTRAP-FAILED: product root, shared state, interpreter or machinery unavailable.' >&2
    printf '%s\n' '{"decision":"deny","reason":"HOOK-BOOTSTRAP-FAILED: hook context unavailable."}'
    exit 0
}
code=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd) || bootstrap_failed
# shellcheck disable=SC1091
source "$code/scripts/lib/project_interpreter.sh" || bootstrap_failed
project_hook_context_resolve 2>/dev/null || bootstrap_failed
py="$LEARN_UKRAINIAN_PYTHON"
# The child drains stdin; on early import/exec failure the parent drains the rest.
project_python_command "$py" || bootstrap_failed
if output=$(cd "$LU_PRODUCT_ROOT" && "${PROJECT_PYTHON_COMMAND[@]}" -m scripts.inbox_pending --agy-hook 2>/dev/null); then
    child_ok=1
else
    child_ok=0
fi
cat >/dev/null
if [ "$child_ok" = 1 ] && validated=$(printf '%s' "$output" | "$py" -I -c '
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
