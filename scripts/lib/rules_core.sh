#!/usr/bin/env bash
# Rules core for launchers. Reads the core from this checkout through
# scripts/lib/rules_core.py (offline; never the Monitor API) and hands provider
# adapters the text in the form their harness accepts:
#   claude-code  --append-system-prompt "$LC_RULES_CORE"
#   codex        -c developer_instructions=<rules_core_toml>
#   grok         --rules "$LC_RULES_CORE"
#   kimi-code    --agent-file <rules_core_kimi_agent_file>   (keeps ${base_prompt})
#   agy, cursor-agent, opencode, hermes: the core leads the initial prompt
# Fail-open: a missing core or interpreter warns and the launch continues without it.

rules_core_warn() {
  printf 'WARNING: rules core not loaded (%s); launching without it.\n' "$*" >&2
}

# rules_core_load PYTHON ROOT LANE PROVIDER
# Sets LC_RULES_SEAT, LC_RULES_CORE, LC_RULES_CORE_BYTES and exports LU_RULES_SEAT
# so delegate.py and ACP calls made from the session inherit the seat.
rules_core_load() {
  local py="$1" root="$2" lane="${3:-}" provider="${4:-claude}"
  local script="$root/scripts/lib/rules_core.py"
  local -a lane_args=()
  LC_RULES_SEAT=""
  LC_RULES_CORE=""
  LC_RULES_CORE_BYTES=0
  if [ ! -x "$py" ] || [ ! -f "$script" ]; then
    rules_core_warn "loader unavailable: $script"
    return 0
  fi
  if [ -n "$lane" ]; then
    lane_args=(--lane "$lane" --provider "$provider")
  fi
  if ! LC_RULES_SEAT="$("$py" "$script" --root "$root" ${lane_args[@]+"${lane_args[@]}"} --format seat)"; then
    LC_RULES_SEAT=""
    rules_core_warn "seat resolution failed"
    return 0
  fi
  if ! LC_RULES_CORE="$("$py" "$script" --root "$root" --seat "$LC_RULES_SEAT" --format block)"; then
    LC_RULES_CORE=""
    rules_core_warn "core source missing for seat $LC_RULES_SEAT"
    return 0
  fi
  # shellcheck disable=SC2034  # read by launcher_core.sh (dry-run report, argv placeholder)
  LC_RULES_CORE_BYTES="$(printf '%s' "$LC_RULES_CORE" | wc -c | tr -d ' ')"
  export LU_RULES_SEAT="$LC_RULES_SEAT"
}

# rules_core_prefix TEXT — the core, a blank line, then TEXT (the ack when empty).
rules_core_prefix() {
  local text="${1:-}"
  if [ -z "$text" ]; then
    text="The rules core above is loaded for this session. Reply only 'Rules core loaded.' and wait for instructions."
  fi
  if [ -z "${LC_RULES_CORE:-}" ]; then
    printf '%s' "$text"
    return 0
  fi
  printf '%s\n\n%s' "$LC_RULES_CORE" "$text"
}

# rules_core_toml PYTHON ROOT — the framed core as one TOML basic string.
rules_core_toml() {
  "$1" "$2/scripts/lib/rules_core.py" --root "$2" --seat "$LC_RULES_SEAT" --format toml
}

# rules_core_kimi_agent_file PYTHON ROOT — writes a content-addressed Kimi agent
# file under the user's temp directory and prints its path.
rules_core_kimi_agent_file() {
  local py="$1" root="$2" dir digest path
  dir="${TMPDIR:-/tmp}/lu-rules-core-$(id -u)"
  { mkdir -p "$dir" && chmod 700 "$dir"; } || return 1
  digest="$(printf '%s' "$LC_RULES_CORE" | sha256sum | cut -c1-16)"
  path="$dir/kimi-agent-${LC_RULES_SEAT}-${digest}.md"
  "$py" "$root/scripts/lib/rules_core.py" --root "$root" --seat "$LC_RULES_SEAT" \
    --format kimi-agent-file --output "$path" || return 1
  printf '%s\n' "$path"
}
