#!/bin/bash
# Installed only by the interactive Claude launcher (#10265).
# Refuse unconditionally; prepared evidence selects only the handoff message.
# Independent of Python, evidence, parsing, and the evidence helper's status.
# Unexpected shell/helper exits also refuse; no raw diagnostic is published.
trap 'printf "%s\n" "Claude driver compaction refused: use thread-rollover (scripts/orchestration/thread_handoff.py prepare); if already prepared, print HANDOFF-DONE <path> and exit for a fresh launcher restart." >&2; exit 2' EXIT
set -Eeuo pipefail

# Bound the entire evidence path (including source, Git, stdin and the runtime)
# below the registration deadline. Never trust partial output after a timeout.
command -v timeout >/dev/null 2>&1 || exit 2
command -v jq >/dev/null 2>&1 || exit 2
# shellcheck disable=SC2016  # Expand variables in the bounded child, not this shell.
RESULT=$(timeout --kill-after=1 3 bash -Eeuo pipefail -c '
  source "$1/context-rollover-lib.sh"
  PROJECT_DIR="$2"
  CANONICAL_ROOT=$(context_canonical_root "$PROJECT_DIR")
  BOUNDED_PYTHON="${THREAD_ROLLOVER_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"
  BOUNDED_RUNNER="${SESSION_BOUNDED_RUNNER:-$PROJECT_DIR/scripts/agent_runtime/bounded_command.py}"
  [ -x "$BOUNDED_PYTHON" ] && [ -f "$BOUNDED_RUNNER" ] || exit 1
  cd "$PROJECT_DIR"
  # The existing proof checker accepts auto only. Normalize manual solely for
  # that read-only evidence check; both triggers receive the same refusal.
  jq '\''if .hook_event_name == "PreCompact" and .trigger == "manual" then .trigger = "auto" else . end'\'' \
    | "$BOUNDED_PYTHON" "$BOUNDED_RUNNER" --timeout 2 -- \
      "$BOUNDED_PYTHON" -m scripts.orchestration.precompact_handoff_check \
      --state-root "$CANONICAL_ROOT" --agent "${SESSION_HANDOFF_AGENT:-claude}"
' -- "$(dirname "${BASH_SOURCE[0]}")" "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}" 2>/dev/null) || exit 2
[ "$RESULT" = "prepared" ] || exit 2
trap - EXIT
printf '%s\n' 'Claude driver compaction refused: thread-rollover handoff is prepared; print HANDOFF-DONE <path> using its exact handoff path and exit for a fresh launcher restart.' >&2
exit 2
