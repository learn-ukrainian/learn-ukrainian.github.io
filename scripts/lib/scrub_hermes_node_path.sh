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
# without dropping them. Compare non-empty components to Hermes by physical
# path (pwd -P) so ../ and symlink spellings are also removed.
#
# Usage (from a repo-root start-*.sh):
#   # shellcheck source=scripts/lib/scrub_hermes_node_path.sh
#   source "$ROOT/scripts/lib/scrub_hermes_node_path.sh"
#   scrub_hermes_node_from_path

scrub_hermes_node_from_path() {
  local hermes_node_bin="${HOME}/.hermes/node/bin"
  local hermes_phys out="" sep="" rest="${PATH-}"
  local comp more=1 phys

  hermes_phys="$(cd "$hermes_node_bin" 2>/dev/null && pwd -P)" || hermes_phys=""

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

    # Drop Hermes-private bin (lexical or physical equivalence).
    if [ -n "$comp" ]; then
      if [ "$comp" = "$hermes_node_bin" ]; then
        continue
      fi
      if [ -n "$hermes_phys" ] && { [ -d "$comp" ] || [ -L "$comp" ]; }; then
        phys="$(cd "$comp" 2>/dev/null && pwd -P)" || phys=""
        if [ -n "$phys" ] && [ "$phys" = "$hermes_phys" ]; then
          continue
        fi
      fi
    fi

    out="${out}${sep}${comp}"
    sep=":"
  done

  export PATH="$out"
  hash -r 2>/dev/null || true
}
