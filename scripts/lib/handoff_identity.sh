#!/usr/bin/env bash
# Map a Claude Code `--agent` selection to its cold-start handoff identity
# (SESSION_HANDOFF_AGENT).
#
# WHY: every Claude session launched as plain `claude` defaults to agent
# `claude`, so the SessionStart hook (agents_extensions/shared/hooks/session-setup.sh)
# routes ALL of them to the single `.agent/claude-thread-handoff.md` slot. The
# folk driver and the infra/code lane then clobber each other's handoff and a
# cold-start adopts the wrong lane (root cause of the 2026-06-22 infra→folk
# mis-identification). The hook already honors an explicit SESSION_HANDOFF_AGENT;
# this helper lets ONE launcher (start-claude.sh) derive that value from the
# selected --agent, so each lane reads/writes its OWN slot and we don't maintain
# a per-lane wrapper script.
#
# Add a new lane by adding ONE case arm to handoff_identity_for_agent below.
# Unknown / absent agents fall back to the default `claude` slot (echo nothing).

# handoff_agent_from_argv "$@"
# Echo the value of `--agent <v>` / `--agent=<v>` from an argv list, or nothing.
# Does NOT consume the argument — the caller still forwards "$@" to claude
# unchanged. First occurrence wins.
handoff_agent_from_argv() {
  local prev='' arg=''
  for arg in "$@"; do
    case "$arg" in
      --agent=*)
        printf '%s' "${arg#--agent=}"
        return 0
        ;;
    esac
    if [ "$prev" = "--agent" ]; then
      printf '%s' "$arg"
      return 0
    fi
    prev="$arg"
  done
}

# handoff_identity_for_agent "<agent-name>"
# Echo the SESSION_HANDOFF_AGENT slot for an --agent name, or nothing for the
# default `claude` lane (the hook already defaults to it).
handoff_identity_for_agent() {
  case "${1:-}" in
    infra-orchestrator) printf '%s' 'claude-infra' ;;
    # curriculum-orchestrator / track-orchestrators / unset → default `claude`.
    *) ;;
  esac
}
