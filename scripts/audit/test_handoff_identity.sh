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

# --- epic argv extraction: spaced + equals forms, .epic suffix normalized ---
eq "$(handoff_epic_from_argv --agent curriculum-orchestrator --epic atlas)" "atlas" "spaced --epic"
eq "$(handoff_epic_from_argv --epic=hramatka)" "hramatka" "equals --epic"
eq "$(handoff_epic_from_argv --epic atlas.epic)" "atlas" "spaced --epic with .epic suffix"
eq "$(handoff_epic_from_argv --epic=harness.epic)" "harness" "equals --epic with .epic suffix"
eq "$(handoff_epic_from_argv --agent curriculum-orchestrator)" "" "no --epic flag"
eq "$(handoff_epic_from_argv)" "" "empty argv (epic)"

# --- epic → slot mapping: epic beats agent-type; empty epic maps to nothing ---
eq "$(handoff_identity_for_epic atlas)" "claude-atlas" "epic atlas → claude-atlas"
eq "$(handoff_identity_for_epic hramatka)" "claude-hramatka" "epic hramatka → claude-hramatka"
eq "$(handoff_identity_for_epic)" "" "no epic → empty slot"

# --- strip: --epic (both forms) removed, everything else preserved in order ---
stripped="$(strip_epic_from_argv --chrome --epic atlas --agent curriculum-orchestrator | tr '\n' ' ')"
eq "$stripped" "--chrome --agent curriculum-orchestrator " "strip spaced --epic"
stripped="$(strip_epic_from_argv --epic=atlas --chrome | tr '\n' ' ')"
eq "$stripped" "--chrome " "strip equals --epic"
stripped="$(strip_epic_from_argv --chrome --agent curriculum-orchestrator | tr '\n' ' ')"
eq "$stripped" "--chrome --agent curriculum-orchestrator " "strip is no-op without --epic"

# --- e2e: two same-agent-type launches on different epics get DIFFERENT slots ---
epic_a="$(handoff_epic_from_argv --agent curriculum-orchestrator --epic atlas)"
epic_b="$(handoff_epic_from_argv --agent curriculum-orchestrator --epic hramatka)"
if [[ "$(handoff_identity_for_epic "$epic_a")" == "$(handoff_identity_for_epic "$epic_b")" ]]; then
  fail "same-agent different-epic launches must not share a handoff slot"
fi

printf 'ok - handoff identity fixtures passed\n'
