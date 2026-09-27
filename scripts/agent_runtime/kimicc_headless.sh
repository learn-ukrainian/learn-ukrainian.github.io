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
READ_ONLY_REVIEW=0
PROMPT=""
FORWARD_ARGS=()

usage() {
  echo "Usage: kimicc_headless.sh --model ALIAS --mode MODE --prompt TEXT [--read-only-review] [Claude Code options]" >&2
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
    --read-only-review)
      READ_ONLY_REVIEW=1
      shift
      ;;
    --mcp-config|--allowedTools|--tools|--agent|--max-budget-usd|--effort)
      FORWARD_ARGS+=("$1" "${2:?$1 requires a value}")
      shift 2
      ;;
    --setting-sources)
      # An explicit empty value is the isolation profile's way to suppress
      # ambient user/project settings, so distinguish an empty argument from
      # an omitted one here.
      FORWARD_ARGS+=("$1" "${2?--setting-sources requires a value}")
      shift 2
      ;;
    --strict-mcp-config)
      FORWARD_ARGS+=("$1")
      shift
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
if [ "$READ_ONLY_REVIEW" -eq 1 ] && [ "$MODE" != "read-only" ]; then
  echo "Error: --read-only-review requires --mode read-only." >&2
  exit 2
fi
if [ "$READ_ONLY_REVIEW" -eq 1 ]; then
  # The adapter only emits the review flag with the trusted strict MCP config;
  # without --strict-mcp-config, dontAsk could pre-approve tools from servers
  # the checkout or user config adds.
  has_strict=0
  for arg in "${FORWARD_ARGS[@]}"; do
    if [ "$arg" = "--strict-mcp-config" ]; then
      has_strict=1
    fi
  done
  if [ "$has_strict" -eq 0 ]; then
    echo "Error: --read-only-review requires --strict-mcp-config." >&2
    exit 2
  fi
fi

export KIMICC_HEADLESS=1
if kimicc_configure_route "$PROJECT_DIR"; then
  :
else
  _route_rc=$?
  # The consolidated route helper standardized environment failures on exit 3,
  # but this wrapper's PUBLIC contract (tests + the delegate adapter) pins
  # credential-missing at exit 1 — map it back at the boundary (#5958 CI fix).
  if [ "$_route_rc" -eq 3 ]; then exit 1; fi
  exit "$_route_rc"
fi

CLAUDE_BIN="${KIMICC_CLAUDE_BIN:-claude}"
CMD=("$CLAUDE_BIN" -p --bare --model "$LEAD_MODEL" --output-format stream-json --verbose)
if [ "$MODE" = "danger" ]; then
  CMD+=(--dangerously-skip-permissions)
elif [ "$MODE" = "read-only" ]; then
  if [ "$READ_ONLY_REVIEW" -eq 1 ]; then
    # Review dispatches carry the sources MCP grant, and plan mode refuses
    # every MCP call (#8652). dontAsk denies whatever --allowedTools did not
    # pre-approve; the built-in set below has no writer or shell, and the
    # explicit deny list keeps writes refused even if that set grows.
    CMD+=(--permission-mode dontAsk --disallowedTools "Write,Edit,NotebookEdit,Bash")
  else
    # Claude Code plan mode is the CLI's read-only permission mode.
    CMD+=(--permission-mode plan)
  fi
  # An explicit --tools profile from the adapter (trail isolation) wins over
  # the default read/search set so a caller allowlist is not doubled.
  has_tools=0
  for arg in "${FORWARD_ARGS[@]}"; do
    if [ "$arg" = "--tools" ]; then
      has_tools=1
    fi
  done
  if [ "$has_tools" -eq 0 ]; then
    CMD+=(--tools "Read,Grep,Glob,LS")
  fi
fi
CMD+=("${FORWARD_ARGS[@]}" -- "$PROMPT")
exec "${CMD[@]}"
