#!/usr/bin/env bash
# Scrub Hermes-private Node from PATH.
#
# Hermes may keep a private runtime at ~/.hermes/node for its own agent.
# That tree must never shadow system Node (Homebrew) or user globals (~/.local).
# Long-lived orchestrator shells often still carry the old
#   export PATH="$HOME/.hermes/node/bin:$PATH"
# from before the detach — launchers must strip it on every start.
#
# Usage (from a repo-root start-*.sh):
#   # shellcheck source=scripts/lib/scrub_hermes_node_path.sh
#   source "$ROOT/scripts/lib/scrub_hermes_node_path.sh"
#   scrub_hermes_node_from_path

scrub_hermes_node_from_path() {
  local hermes_node_bin="${HOME}/.hermes/node/bin"
  local scrubbed="" p
  local _old_ifs="$IFS"
  local -a parts=()

  IFS=':'
  # shellcheck disable=SC2206  # intentional word-split on PATH
  parts=(${PATH:-})
  IFS="$_old_ifs"

  for p in "${parts[@]+"${parts[@]}"}"; do
    [ -n "$p" ] || continue
    if [ "$p" = "$hermes_node_bin" ]; then
      continue
    fi
    if [ -n "$scrubbed" ]; then
      scrubbed="${scrubbed}:${p}"
    else
      scrubbed="$p"
    fi
  done

  export PATH="$scrubbed"
  hash -r 2>/dev/null || true
}
