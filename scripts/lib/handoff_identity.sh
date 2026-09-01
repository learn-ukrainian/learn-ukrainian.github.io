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
# Launcher selectors resolve against the issue-stream registry, with the
# compatibility aliases below layered over it.  Do not derive a slot or stream
# id from arbitrary user input: that creates phantom handoff files and can
# silently attach a session to the wrong stream.
#
# The infra stream id is the issue-stream registry anchor (infra-harness), not
# a literal epic number. The next succession must not require a launcher edit.
# Tests may point HANDOFF_ISSUE_STREAMS_YAML at a fixture registry.

_HANDOFF_IDENTITY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# _launcher_stream_anchor_epic "<stream-key>"
# Print the first epic number listed for that key in issue_streams.yaml.
# Fail closed (print nothing, return 1) when the registry is missing or the
# stream has no numeric epic. Handles both `epics: [N]` and block-list forms.
_launcher_stream_anchor_epic() {
  local key="${1:-}"
  local registry="${HANDOFF_ISSUE_STREAMS_YAML:-$_HANDOFF_IDENTITY_DIR/../config/issue_streams.yaml}"
  local epic=""
  case "$key" in
    ''|*[!A-Za-z0-9._-]*) return 1 ;;
  esac
  [ -f "$registry" ] || return 1
  epic="$(
    awk -v key="$key" '
      $0 ~ /^streams:[[:space:]]*(#.*)?$/ {
        in_streams = 1
        next
      }
      !in_streams { next }
      {
        candidate = $1
        if ($0 !~ /^  [^[:space:]]/ || candidate !~ /^[A-Za-z0-9][A-Za-z0-9._-]*:$/) {
          candidate = ""
        } else {
          sub(/:$/, "", candidate)
        }
        if (candidate != "") {
          if (candidate in seen) invalid = 1
          seen[candidate] = 1
          if (found && !finished) finished = 1
          if (!finished && candidate == key) found = 1
          next
        }
      }
      found && !finished && $0 ~ /^[[:space:]]+epics:[[:space:]]*\[[[:space:]]*[1-9][0-9]*([[:space:]]*,[[:space:]]*[1-9][0-9]*)*[[:space:]]*\][[:space:]]*(#.*)?$/ {
        match($0, /[1-9][0-9]*/)
        epic = substr($0, RSTART, RLENGTH)
        finished = 1
        next
      }
      found && !finished && $0 ~ /^[[:space:]]+epics:[[:space:]]*$/ {
        list = 1
        next
      }
      found && !finished && list {
        if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[[:space:]]*#/) next
        if ($0 ~ /^[[:space:]]*-[[:space:]]*[1-9][0-9]*[[:space:]]*(#.*)?$/) {
          match($0, /[1-9][0-9]*/)
          epic = substr($0, RSTART, RLENGTH)
        }
        finished = 1
        next
      }
      END {
        if (!in_streams || invalid || epic == "") exit 1
        print epic
      }
    ' "$registry"
  )"
  [ -n "$epic" ] || return 1
  printf '%s' "$epic"
}

# _launcher_registry_stream_keys
# Print the top-level stream keys in the configured registry.  Keep this parser
# deliberately narrower than a general YAML parser: launchers only need the
# registry's two-space stream keys and their first numeric epic.
_launcher_registry_stream_keys() {
  local registry="${HANDOFF_ISSUE_STREAMS_YAML:-$_HANDOFF_IDENTITY_DIR/../config/issue_streams.yaml}"
  [ -f "$registry" ] || return 1
  awk '
    $0 ~ /^streams:[[:space:]]*(#.*)?$/ { in_streams = 1; next }
    in_streams && $0 ~ /^  [^[:space:]]/ && $1 ~ /^[A-Za-z0-9][A-Za-z0-9._-]*:$/ {
      key = $1
      sub(/:$/, "", key)
      print key
    }
    END {
      if (!in_streams) exit 1
    }
  ' "$registry"
}

# _launcher_infra_stream_id
# Print epic:<anchor> for the infra-harness registry stream.
_launcher_infra_stream_id() {
  local epic=""
  epic="$(_launcher_stream_anchor_epic infra-harness)" || return 1
  printf 'epic:%s' "$epic"
}

# launcher_selector_resolve "<lane-or-lane.topic>"
# Print the canonical lane and stream id, separated by a tab.  This is the
# single selector table shared by handoff identities and session supervision.
# Unknown selectors return 1 and print nothing, so callers can fail closed.
launcher_selector_resolve() {
  local selector="${1:-}"
  local key=""
  local lane=""
  local epic=""

  # Compatibility aliases preserve the pre-registry lane identity while their
  # stream anchor still comes from the registry.  Generic selectors below are
  # intentionally not added here: a new registry row must work without a
  # launcher edit.
  case "$selector" in
    infra|harness|infra.fleet-comms)
      key="infra-harness"
      lane="infra"
      ;;
    devops|infra.devops)
      key="devops"
      lane="devops"
      ;;
    monitor|infra.monitor)
      key="monitor"
      lane="monitor"
      ;;
    atlas|practice|practice-hub|atlas.practice)
      key="atlas-practice"
      lane="atlas"
      ;;
    hramatka|hramatka.lessons)
      key="hramatka"
      lane="hramatka"
      ;;
    folk|seminars-folk)
      key="seminars-folk"
      lane="folk"
      ;;
    bio|seminars-bio)
      key="seminars-bio"
      lane="bio"
      ;;
    corpus|corpus-channels)
      key="corpus-channels"
      lane="corpus"
      ;;
    infra.*)
      key="${selector#infra.}"
      lane="$key"
      ;;
    *)
      key="$selector"
      lane="$key"
      ;;
  esac

  epic="$(_launcher_stream_anchor_epic "$key")" || return 1
  case "$epic" in
    [1-9][0-9]*) ;;
    *) return 1 ;;
  esac
  printf '%s\tepic:%s\n' "$lane" "$epic"
}

# launcher_selector_lane "<selector>"
# Print the canonical lane for a selector.
launcher_selector_lane() {
  local resolved=''
  resolved="$(launcher_selector_resolve "${1:-}")" || return 1
  printf '%s' "${resolved%%$'\t'*}"
}

# launcher_selector_stream "<selector>"
# Print the canonical stream id for a selector.
launcher_selector_stream() {
  local resolved=''
  resolved="$(launcher_selector_resolve "${1:-}")" || return 1
  printf '%s' "${resolved#*$'\t'}"
}

# launcher_selector_help
# Keep launcher diagnostics in one place so every entry point documents the
# exact same public selector surface.
launcher_selector_help() {
  local key=""
  cat <<'EOF'
Valid lane selectors:
  Registry stream keys (and infra.<key>):
EOF
  while IFS= read -r key; do
    [ -n "$key" ] || continue
    printf '    %s | infra.%s\n' "$key" "$key"
  done < <(_launcher_registry_stream_keys 2>/dev/null || true)
  cat <<'EOF'
  Compatibility aliases:
    infra | harness | infra.fleet-comms
    devops | infra.devops
    monitor | infra.monitor
    atlas | practice | practice-hub | atlas.practice
    hramatka | hramatka.lessons
    folk | seminars-folk
    bio | seminars-bio
    corpus | corpus-channels
EOF
}

# _launcher_area_slots_empty "<lane>"
# Succeed only when area_assignments.yaml registers an area named exactly like
# the lane AND that area's slots roster is empty (monitor, open-model-data,
# core). Any other case — registry missing, area missing, roster non-empty —
# returns 1 so callers keep the legacy per-lane slot form. Tests may point
# HANDOFF_AREA_ASSIGNMENTS_YAML at a fixture registry.
_launcher_area_slots_empty() {
  local area="${1:-}"
  local registry="${HANDOFF_AREA_ASSIGNMENTS_YAML:-$_HANDOFF_IDENTITY_DIR/../config/area_assignments.yaml}"
  case "$area" in
    ''|*[!A-Za-z0-9._-]*) return 1 ;;
  esac
  [ -f "$registry" ] || return 1
  awk -v area="$area" '
    $0 ~ /^assignments:[[:space:]]*(#.*)?$/ { in_assignments = 1; next }
    !in_assignments { next }
    # Area keys are exactly two-space indented (`  open-model-data:`); slot
    # list items are deeper and start with a dash, so they never match here.
    $0 ~ /^  [^[:space:]]/ && $1 ~ /^[A-Za-z0-9][A-Za-z0-9._-]*:$/ {
      if (found) finished = 1
      if (!finished && $1 == area ":") { found = 1; empty = 1 }
      next
    }
    found && !finished {
      if ($0 ~ /^[[:space:]]+-[[:space:]]+[^[:space:]]/) empty = 0
      next
    }
    END {
      if (!in_assignments || !found || !empty) exit 1
    }
  ' "$registry"
}

# _launcher_handoff_slot_for_lane <provider> <lane>
# Print the SESSION_HANDOFF_AGENT slot for a provider+lane pair. An area whose
# area_assignments.yaml slots roster is EMPTY mints no per-lane roster slot:
# emit the bare provider identity (inbox --for accepts it) instead of a
# phantom `{provider}-{lane}` that argparse rejects (#7597). Registry miss or
# non-empty roster keeps the legacy per-lane form.
_launcher_handoff_slot_for_lane() {
  local provider="${1:-}" lane="${2:-}"
  if _launcher_area_slots_empty "$lane"; then
    printf '%s' "$provider"
  else
    printf '%s-%s' "$provider" "$lane"
  fi
}

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
# strip it from the argv it forwards (see strip_epic_from_argv).  The legacy
# `.epic` display suffix is removed before launchers resolve the selector.
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
# Echo the allowlisted per-lane SESSION_HANDOFF_AGENT slot, or nothing when no
# selector is given. An explicit selector beats the agent-type mapping so two
# sessions on different lanes never share a handoff slot.
handoff_identity_for_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane claude "$lane"
}

# handoff_identity_for_codex_epic "<epic-name>"
# Echo the per-epic Codex rollover slot. Codex needs the same lane separation
# as Claude, but its namespaces must remain provider-specific so a Codex launch
# never adopts a Claude packet. Infra aliases share the canonical infra slot;
# DevOps has its own slot because it owns an independent stream lease.
handoff_identity_for_codex_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane codex "$lane"
}

# handoff_identity_for_kimi_epic "<epic-name>"
# Echo the per-epic Kimi Code orchestrator rollover slot. Provider-specific so
# a Kimi seat never adopts Claude/Codex/Grok packets.
handoff_identity_for_kimi_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane kimi "$lane"
}

# handoff_identity_for_gemini_epic "<epic-name>"
# Echo the per-epic Gemini / Antigravity orchestrator rollover slot. Provider-specific so
# a Gemini seat never adopts Claude/Codex/Grok/Kimi packets.
handoff_identity_for_gemini_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane gemini "$lane"
}

# handoff_identity_for_grok_epic "<selector>"
# Grok uses the same canonical selector table as the other launchers.
handoff_identity_for_grok_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane grok "$lane"
}

# handoff_identity_for_cursor_epic "<selector>"
# Cursor TUI driver rollover slot. Provider-specific so a Cursor seat never
# adopts Claude/Codex/Grok/Gemini packets (#6956).
handoff_identity_for_cursor_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  _launcher_handoff_slot_for_lane cursor "$lane"
}
