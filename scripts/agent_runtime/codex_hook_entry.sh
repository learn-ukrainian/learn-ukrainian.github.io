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

# SCRIPT_ROOT is the machinery tree holding this file: it supplies the code
# (the hooks and the policy module), never the project (machinery #100 R70).
SCRIPT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_DIR="$SCRIPT_ROOT/agents_extensions/shared/hooks"

bootstrap_failed() {
  printf '%s\n' 'HOOK-BOOTSTRAP-FAILED: product root, shared state, interpreter or machinery unavailable.' >&2
  exit 2
}
# The product, shared-state anchor and interpreter come from the one hook rule,
# project_hook_context_resolve, before any child starts: LU_PRODUCT_ROOT, else
# CLAUDE_PROJECT_DIR, else the nearest checkout above the working directory.
# The interpreter and the canonical root come only from the configured
# shared-state anchor (LEARN_UKRAINIAN_PRIMARY_REPO_ROOT, validated and made
# physical by the rule); without it the hook refuses. The product's own Git
# metadata never names the primary: whoever works in a checkout can rewrite it.
# The payload's working directory stays policy input, never bootstrap authority.
# shellcheck source=scripts/lib/project_interpreter.sh
source "$SCRIPT_ROOT/scripts/lib/project_interpreter.sh" || bootstrap_failed
project_hook_context_resolve 2>/dev/null || bootstrap_failed
PYTHON_BIN="$LEARN_UKRAINIAN_PYTHON"
CANONICAL_ROOT="$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"

case "$MODE" in
  pre-tool-use)
    printf '%s' "$PAYLOAD" \
      | project_python_run "$PYTHON_BIN" -m scripts.agent_runtime.codex_hook_policy \
        --python-bin "$PYTHON_BIN" \
        --hooks-dir "$HOOKS_DIR" \
        --canonical-root "$CANONICAL_ROOT"
    policy_rc=${PIPESTATUS[1]}
    [ "$policy_rc" -eq 0 ] || exit "$policy_rc"
    ;;

  post-tool-use)
    printf '%s' "$PAYLOAD" \
      | CLAUDE_PROJECT_DIR="$CANONICAL_ROOT" bash "$HOOKS_DIR/tool-timing.sh"
    # stamp-pytest only inspects a Bash `command` (#8529); running it for
    # every other tool payload was pure interpreter-startup cost.
    TOOL_NAME=$(printf '%s' "$PAYLOAD" | jq -r '.tool_name // empty' 2>/dev/null || true)
    if [ "$TOOL_NAME" = "Bash" ]; then
      printf '%s' "$PAYLOAD" \
        | CLAUDE_PROJECT_DIR="$CANONICAL_ROOT" bash "$HOOKS_DIR/stamp-pytest.sh"
      # Primary-checkout dirt audit (#11253): exit 2 hands the attribution
      # report to the model; Codex runs PostToolUse for non-zero exits too.
      AUDIT_HOOK="$HOOKS_DIR/audit-primary-checkout-dirt.py"
      printf '%s' "$PAYLOAD" | "$PYTHON_BIN" -I "$AUDIT_HOOK"
      audit_rc=$?
      [ "$audit_rc" -eq 0 ] || exit "$audit_rc"
    fi
    ;;

  user-prompt-submit)
    printf '%s' "$PAYLOAD" \
      | CLAUDE_PROJECT_DIR="$CANONICAL_ROOT" \
        LEARN_UK_HOOK_RECIPIENT=codex \
        bash "$HOOKS_DIR/check-agent-inbox.sh"
    ;;

  *)
    printf 'Unknown Codex hook entry mode: %s\n' "$MODE" >&2
    exit 1
    ;;
esac
