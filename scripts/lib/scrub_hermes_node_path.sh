#!/usr/bin/env bash
# Scrub Hermes-private Node from PATH.
#
# Hermes may keep a private runtime at ~/.hermes/node for its own agent.
# That tree must never shadow system Node (Homebrew) or user globals (~/.local).
# Long-lived orchestrator shells often still carry the old
#   export PATH="$HOME/.hermes/node/bin:$PATH"
# from before the detach — launchers must strip it on every start.
#
# Empty colon-delimited PATH fields are valid (they mean cwd). Rebuild PATH
# without dropping them; only remove entries exactly equal to the Hermes bin.
#
# Usage (from a repo-root start-*.sh):
#   # shellcheck source=scripts/lib/scrub_hermes_node_path.sh
#   source "$ROOT/scripts/lib/scrub_hermes_node_path.sh"
#   scrub_hermes_node_from_path

scrub_hermes_node_from_path() {
  local hermes_node_bin="${HOME}/.hermes/node/bin"
  local out="" sep="" rest="${PATH-}"
  local comp more=1

  # Split on ':' while preserving empty fields (unlike unquoted ${PATH} split).
  while [ "$more" -eq 1 ]; do
    case "$rest" in
      *:*)
        comp="${rest%%:*}"
        rest="${rest#*:}"
        ;;
      *)
        comp="$rest"
        more=0
        ;;
    esac
    if [ "$comp" = "$hermes_node_bin" ]; then
      continue
    fi
    out="${out}${sep}${comp}"
    sep=":"
  done

  export PATH="$out"
  hash -r 2>/dev/null || true
}
