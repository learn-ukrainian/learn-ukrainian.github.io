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

# Read the same compatibility map used by /api/work/v1/next. Print
# "<stream-key><TAB><lane>" and return 0 on a hit; return 1 for a selector that
# is not in the map (callers fall through to registry-key resolution); return 2
# when the map is missing or malformed so callers fail closed instead of
# silently resolving a compatibility alias like `atlas` as a raw registry key.
_launcher_compat_alias() {
  local selector="${1:-}"
  local aliases="$_HANDOFF_IDENTITY_DIR/../config/launcher_stream_aliases.tsv"
  [ -f "$aliases" ] || return 2
  awk -F '\t' -v wanted="$selector" '
    /^#/ || NF == 0 { next }
    NF != 3 { invalid = 1; next }
    $1 == wanted {
      if (found++) invalid = 1
      key = $2
      lane = $3
    }
    END {
      if (invalid) exit 2
      if (!found) exit 1
      printf "%s\t%s\n", key, lane
    }
  ' "$aliases"
}

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
# Unknown selectors return 1 and print nothing on stdout, so callers can fail closed.
# Retired selectors also explain the rejection on stderr.
launcher_selector_resolve() {
  local selector="${1:-}"
  local key=""
  local lane=""
  local epic=""
  local mapped=""
  local alias_rc=0

  # Retired selectors fail before alias and generic registry resolution.
  case "$selector" in
    eval-harness|a1-upgrade|infra.eval-harness|infra.a1-upgrade)
      printf 'retired lane selector: %s\n' "$selector" >&2
      return 1
      ;;
  esac

  mapped="$(_launcher_compat_alias "$selector")" && alias_rc=0 || alias_rc=$?
  case "$alias_rc" in
    0) IFS=$'\t' read -r key lane <<< "$mapped" ;;
    1)
      # Generic selectors are intentionally absent from the compatibility map:
      # a new registry row must work without a launcher edit.
      case "$selector" in
        infra.*) key="${selector#infra.}" ;;
        *) key="$selector" ;;
      esac
      lane="$key"
      ;;
    *)
      printf 'launcher alias map missing or malformed: scripts/config/launcher_stream_aliases.tsv\n' >&2
      return 1
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

# _handoff_slot_registry "<args for handoff_slot_registry.py>"
# Run the slot-registry helper with the durable interpreter.  The registry is
# scripts/config/area_assignments.yaml, read only through the bridge helpers
# that build the inbox `--for` choices (no second parser here).  Returns the
# helper's exit code (0 registered, 3 not registered, anything else means the
# check could not run); returns 2 when no interpreter is available so callers
# fail closed.
_handoff_slot_registry() {
  local repo_root="$_HANDOFF_IDENTITY_DIR/../.."
  local py="${LC_DURABLE_HELPER_ROOT:-$repo_root}/.venv/bin/python"
  [ -x "$py" ] || return 2
  (cd "$repo_root" && "$py" -m scripts.orchestration.handoff_slot_registry "$@")
}

# launcher_require_registered_slot "<provider>" "<selector>"
# Fail closed when "<provider>-<lane>" is not a registered handoff slot: an
# unregistered SESSION_HANDOFF_AGENT cannot receive inbox mail, fails the
# dispatch-lane self-test and lets rollover fall back to another lane's packet
# pool (#8303).  Prints one error naming the selector, the slot and the
# registered options; returns 1 (unresolvable/unregistered) or 2 (the check
# could not run).
launcher_require_registered_slot() {
  local provider="${1:-}" selector="${2:-}"
  local lane="" slot="" rc=0 options=""
  lane="$(launcher_selector_lane "$selector")" || return 1
  slot="$provider-$lane"
  _handoff_slot_registry --slot "$slot" 2>/dev/null && return 0 || rc=$?
  if [ "$rc" -eq 3 ]; then
    options="$(_handoff_slot_registry --list "$provider" 2>/dev/null | paste -sd ' ' - || true)"
    printf "selector '%s' resolves to handoff slot '%s', which is not registered in scripts/config/area_assignments.yaml; a session under it cannot receive inbox mail. Registered %s slots: %s\n" \
      "$selector" "$slot" "$provider" "${options:-none}" >&2
    return 1
  fi
  printf "cannot verify handoff slot '%s' for selector '%s': scripts/config/area_assignments.yaml is unreadable or the durable Python interpreter is missing; refusing to launch an unverified identity.\n" \
    "$slot" "$selector" >&2
  return 2
}

# launcher_selector_help
# Keep launcher diagnostics in one place so every entry point documents the
# exact same public selector surface.  Registry keys are listed only when the
# launcher would accept them, i.e. when the slot they mint is registered.
launcher_selector_help() {
  local key=""
  cat <<'EOF'
Valid lane selectors:
  Registry stream keys (and infra.<key>):
EOF
  while IFS= read -r key; do
    [ -n "$key" ] || continue
    # rc 3 = minted slot unregistered (launcher would refuse it); anything else =
    # cannot tell, so keep the key listed rather than hide a selector on a broken host.
    _handoff_slot_registry --slot "claude-$key" >/dev/null 2>&1 || [ "$?" -ne 3 ] || continue
    printf '    %s | infra.%s\n' "$key" "$key"
  done < <(_launcher_registry_stream_keys 2>/dev/null || true)
  cat <<'EOF'
  Compatibility aliases:
    infra | harness | infra.fleet-comms
    devops | infra.devops
    monitor | infra.monitor | ops-api | ops.api | operator-api
    atlas | practice | practice-hub | atlas.practice
    hramatka | hramatka.lessons
    folk | seminars-folk
    bio | seminars-bio
    corpus | corpus-channels
EOF
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
  printf 'claude-%s' "$lane"
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
  printf 'codex-%s' "$lane"
}

# handoff_identity_for_kimi_epic "<epic-name>"
# Echo the per-epic Kimi Code orchestrator rollover slot. Provider-specific so
# a Kimi seat never adopts Claude/Codex/Grok packets.
handoff_identity_for_kimi_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  printf 'kimi-%s' "$lane"
}

# handoff_identity_for_gemini_epic "<epic-name>"
# Echo the per-epic Gemini / Antigravity orchestrator rollover slot. Provider-specific so
# a Gemini seat never adopts Claude/Codex/Grok/Kimi packets.
handoff_identity_for_gemini_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  printf 'gemini-%s' "$lane"
}

# handoff_identity_for_grok_epic "<selector>"
# Grok uses the same canonical selector table as the other launchers.
handoff_identity_for_grok_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  printf 'grok-%s' "$lane"
}

# handoff_identity_for_cursor_epic "<selector>"
# Cursor TUI driver rollover slot. Provider-specific so a Cursor seat never
# adopts Claude/Codex/Grok/Gemini packets (#6956).
handoff_identity_for_cursor_epic() {
  local lane=''
  [ -n "${1:-}" ] || return 0
  lane="$(launcher_selector_lane "$1")" || return 1
  printf 'cursor-%s' "$lane"
}
