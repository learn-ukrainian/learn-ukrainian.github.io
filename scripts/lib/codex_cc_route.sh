#!/usr/bin/env bash
# Codex-through-Claude-Code route. The proxy endpoint is intentionally local
# and process-scoped; no foreign inherited route survives launcher_core.

codex_cc_configure_route() {
  local model="$1"
  local base="${CODEX_CC_BASE_URL:-http://127.0.0.1:8317}"
  base="${base%/}"
  case "$base" in
    http://127.0.0.1:8317|http://localhost:8317) ;;
    *) echo 'Error: CODEX_CC_BASE_URL must be the approved local CLIProxyAPI endpoint.' >&2; return 2 ;;
  esac
  export ANTHROPIC_BASE_URL="$base"
  export ANTHROPIC_AUTH_TOKEN="${CODEX_CC_AUTH_TOKEN:-sk-dummy}"
  unset ANTHROPIC_API_KEY
  export ANTHROPIC_MODEL="$model"
  export CLAUDE_CODE_SUBAGENT_MODEL="$model"
  export LEARN_UKRAINIAN_TRANSPORT="codex-claude-code"
  CODEX_CC_AUTH_SOURCE="${CODEX_CC_AUTH_TOKEN:+CODEX_CC_AUTH_TOKEN}"
  CODEX_CC_AUTH_SOURCE="${CODEX_CC_AUTH_SOURCE:-local-proxy-placeholder}"
  export CODEX_CC_AUTH_SOURCE
}
