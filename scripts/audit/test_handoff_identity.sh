#!/usr/bin/env bash
# Fixtures for scripts/lib/handoff_identity.sh — the launcher-side derivation of
# SESSION_HANDOFF_AGENT from a Claude Code `--agent` selection. Wired into the
# required pytest gate via tests/test_handoff_identity.py so the agent→slot
# mapping that prevents the infra/folk cold-start collision stays load-bearing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/handoff_identity.sh
source "$REPO_ROOT/scripts/lib/handoff_identity.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

eq() {
  # eq <actual> <expected> <label>
  if [[ "$1" != "$2" ]]; then
    fail "$3: expected [$2], got [$1]"
  fi
}

# --- argv extraction: spaced + equals forms, position-independent, non-consuming ---
eq "$(handoff_agent_from_argv --chrome --agent infra-orchestrator --foo bar)" "infra-orchestrator" "spaced --agent"
eq "$(handoff_agent_from_argv --agent=infra-orchestrator)" "infra-orchestrator" "equals --agent"
eq "$(handoff_agent_from_argv --permission-mode bypassPermissions --agent curriculum-orchestrator)" "curriculum-orchestrator" "trailing --agent"
eq "$(handoff_agent_from_argv --chrome --permission-mode bypassPermissions)" "" "no --agent flag"
eq "$(handoff_agent_from_argv)" "" "empty argv"

# --- agent → SESSION_HANDOFF_AGENT slot mapping ---
eq "$(handoff_identity_for_agent infra-orchestrator)" "claude-infra" "infra maps to claude-infra"
eq "$(handoff_identity_for_agent curriculum-orchestrator)" "" "curriculum keeps default claude slot"
eq "$(handoff_identity_for_agent)" "" "unset keeps default claude slot"
eq "$(handoff_identity_for_agent some-future-agent)" "" "unknown keeps default claude slot"

# --- end-to-end: the infra agent selection resolves to the claude-infra slot ---
agent="$(handoff_agent_from_argv --chrome --permission-mode bypassPermissions --agent infra-orchestrator)"
eq "$(handoff_identity_for_agent "$agent")" "claude-infra" "e2e: --agent infra-orchestrator → claude-infra"

# --- end-to-end: a folk/curriculum launch resolves to the default (empty) slot ---
agent="$(handoff_agent_from_argv --chrome --agent curriculum-orchestrator)"
eq "$(handoff_identity_for_agent "$agent")" "" "e2e: --agent curriculum-orchestrator → default claude"

printf 'ok - handoff identity fixtures passed\n'
