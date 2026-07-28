#!/usr/bin/env bash
# Headless Claude Code execution on the KimiCC route.
#
# This wrapper is invoked only by KimiccHarness through agent_runtime. It resolves
# auth immediately before exec so an OAuth access token is fresh for the new
# Claude process. It intentionally never writes CLAUDE_CONFIG_DIR or installs an
# apiKeyHelper: --bare is stateless, so runs that exceed the roughly 15-minute
# OAuth lifetime must be relaunched.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/kimicc_route.sh
source "$PROJECT_DIR/scripts/lib/kimicc_route.sh"

MODEL_ALIAS="${KIMICC_MODEL:-k3}"
ENDPOINT="${KIMICC_ENDPOINT:-coding}"
ISOLATE_CONFIG=0
MODE="read-only"
PROMPT=""
FORWARD_ARGS=()

usage() {
  echo "Usage: kimicc_headless.sh --model ALIAS --mode MODE --prompt TEXT [Claude Code options]" >&2
}

while (($#)); do
  case "$1" in
    --model)
      MODEL_ALIAS="${2:?--model requires a value}"
      shift 2
      ;;
    --mode)
      MODE="${2:?--mode requires a value}"
      shift 2
      ;;
    --prompt)
      PROMPT="${2:?--prompt requires a value}"
      shift 2
      ;;
    --mcp-config|--allowedTools|--agent|--max-budget-usd|--effort)
      FORWARD_ARGS+=("$1" "${2:?$1 requires a value}")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unsupported KimiCC headless argument '$1'." >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "$PROMPT" ]; then
  echo "Error: --prompt is required for headless KimiCC." >&2
  usage
  exit 2
fi
case "$MODE" in
  read-only|workspace-write|danger) ;;
  *)
    echo "Error: unsupported KimiCC headless mode '$MODE'." >&2
    exit 2
    ;;
esac

export KIMICC_HEADLESS=1
if kimicc_configure_route "$PROJECT_DIR"; then
  :
else
  exit $?
fi

CLAUDE_BIN="${KIMICC_CLAUDE_BIN:-claude}"
CMD=("$CLAUDE_BIN" -p --bare --model "$LEAD_MODEL" --output-format stream-json --verbose)
if [ "$MODE" = "danger" ]; then
  CMD+=(--dangerously-skip-permissions)
fi
CMD+=("${FORWARD_ARGS[@]}" -- "$PROMPT")
exec "${CMD[@]}"
