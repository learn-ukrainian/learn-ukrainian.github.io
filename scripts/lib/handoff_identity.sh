#!/usr/bin/env bash
# Map interactive launcher selections to their cold-start handoff identity
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

# handoff_epic_from_argv "$@"
# Echo the value of `--epic <v>` / `--epic=<v>` from an argv list, or nothing.
# `--epic` is a LAUNCHER flag, not a claude CLI flag: the caller must ALSO
# strip it from the argv it forwards (see strip_epic_from_argv). Accepts both
# `atlas` and `atlas.epic` spellings; a `.epic` suffix is dropped.
# First occurrence wins.
handoff_epic_from_argv() {
  local prev='' arg='' value=''
  for arg in "$@"; do
    case "$arg" in
      --epic=*)
        value="${arg#--epic=}"
        printf '%s' "${value%.epic}"
        return 0
        ;;
    esac
    if [ "$prev" = "--epic" ]; then
      printf '%s' "${arg%.epic}"
      return 0
    fi
    prev="$arg"
  done
}

# strip_epic_from_argv "$@"
# Print the argv list minus `--epic <v>` / `--epic=<v>`, NUL-delimited so args
# containing spaces or even newlines survive the round-trip (consume with:
# while IFS= read -r -d '' a; do argv+=("$a"); done < <(strip_epic_from_argv "$@")).
# Needed because the claude CLI does not know `--epic` and would reject it.
strip_epic_from_argv() {
  local skip_next=0 arg=''
  for arg in "$@"; do
    if [ "$skip_next" = "1" ]; then
      skip_next=0
      continue
    fi
    case "$arg" in
      --epic) skip_next=1; continue ;;
      --epic=*) continue ;;
    esac
    printf '%s\0' "$arg"
  done
}

# epic_flag_present "$@"
# Succeed when any `--epic` / `--epic=...` token appears in argv, regardless of
# whether a usable value follows. Needed because handoff_epic_from_argv returns
# empty BOTH for "flag absent" and "flag present with empty/dangling value" —
# and the latter must fail the launch loudly instead of leaking the
# launcher-private flag into the claude CLI argv (grok review of #5074).
epic_flag_present() {
  local arg=''
  for arg in "$@"; do
    case "$arg" in
      --epic|--epic=*) return 0 ;;
    esac
  done
  return 1
}

# epic_name_valid "<epic-name>"
# Succeed only for sane epic names: lowercase alnum + inner hyphens (atlas,
# hramatka, lit-war). Anything else — path chars, spaces, uppercase — is
# refused so a malformed --epic can never traverse into the handoff-slot path
# (.agent/claude-<epic>-thread-handoff.md) or the .claude/<epic>-epic/ pointer.
epic_name_valid() {
  # LC_ALL=C: under macOS system bash 3.2 the [a-z] range is locale-collated
  # and matches uppercase too — pin the C locale so the class is literal.
  local LC_ALL=C
  case "${1:-}" in
    ''|*[!a-z0-9-]*|-*|*-) return 1 ;;
    *) return 0 ;;
  esac
}

# handoff_identity_for_epic "<epic-name>"
# Echo the per-epic SESSION_HANDOFF_AGENT slot, or nothing when no epic is given.
# Default: claude-<epic>. An explicit epic BEATS the agent-type mapping so two
# sessions of the same agent type on different epics never share a handoff slot
# (root cause of the 2026-07-13 atlas/hramatka/main lane collision).
#
# Canonical-slot aliases: some epics are NOT free-standing lanes — they already
# have a durable handoff identity elsewhere. Mapping them to a phantom
# claude-<epic> slot hides live packets and causes silent cold starts (#5201).
# harness (infra & fleet reliability / --epic harness) → claude-infra, the same
# slot as --agent infra-orchestrator (lineage dir, session-state, inbox).
handoff_identity_for_epic() {
  local epic="${1:-}"
  [ -n "$epic" ] || return 0
  case "$epic" in
    harness|infra) printf '%s' 'claude-infra' ;;
    *) printf 'claude-%s' "$epic" ;;
  esac
}

# handoff_identity_for_codex_epic "<epic-name>"
# Echo the per-epic Codex rollover slot. Codex needs the same lane separation
# as Claude, but its namespaces must remain provider-specific so a Codex launch
# never adopts a Claude packet. The infra alias mirrors the canonical
# claude-infra convention and avoids inventing parallel harness/infra slots.
handoff_identity_for_codex_epic() {
  local epic="${1:-}"
  [ -n "$epic" ] || return 0
  case "$epic" in
    harness|infra) printf '%s' 'codex-infra' ;;
    *) printf 'codex-%s' "$epic" ;;
  esac
}

# handoff_identity_for_kimi_epic "<epic-name>"
# Echo the per-epic Kimi Code orchestrator rollover slot. Provider-specific so
# a Kimi seat never adopts Claude/Codex/Grok packets. harness/infra → kimi-infra.
handoff_identity_for_kimi_epic() {
  local epic="${1:-}"
  [ -n "$epic" ] || return 0
  case "$epic" in
    harness|infra) printf '%s' 'kimi-infra' ;;
    *) printf 'kimi-%s' "$epic" ;;
  esac
}
