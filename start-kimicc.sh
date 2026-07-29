#!/usr/bin/env bash
# Compatibility wrapper: Claude Code UI routed to Kimi (K3 / K2.7).
#
# Canonical entry after the launcher cutover (#5958):
#   ./start-kimi.sh --harness claude-code
#
# This wrapper restores the historical `./start-kimicc.sh` name. It does not
# invent a second route — it forwards to the shared kimi adapter with the
# Claude-Code harness pinned. Isolation, credential selection, and route
# guards remain in scripts/lib/kimicc_route.sh + launcher_core.sh.
#
# Official reference: https://platform.kimi.ai/docs/guide/claude-code-kimi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pin the compatibility route: a later --harness would otherwise override the
# leading default and silently drop into native kimi-code.
for _arg in "$@"; do
  case "$_arg" in
    --harness|--harness=*)
      echo "Error: start-kimicc.sh always uses Claude Code; omit --harness," >&2
      echo "  or call ./start-kimi.sh --harness kimi-code for the native TUI." >&2
      exit 2
      ;;
  esac
done
unset _arg

exec "$ROOT/start-kimi.sh" --harness claude-code "$@"
