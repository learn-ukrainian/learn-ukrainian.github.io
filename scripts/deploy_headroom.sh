#!/usr/bin/env bash
#
# deploy_headroom.sh — Upgrade the Headroom proxy (pipx `headroom-ai`) to a target
# version, restart the persistent proxy service, optionally re-apply the durable
# agent integrations, and cycle the Claude / Codex agent sessions so everything
# picks up the new build.
#
# +-- RUN ONLY WHEN NO AGENT IS ACTIVELY WORKING ----------------------------+
# | This STOPS the Headroom proxy and KILLS running Claude / Codex sessions. |
# | Run it from a PLAIN terminal (NOT from inside a Claude or Codex session) |
# | — otherwise it will kill the very session you launched it from.          |
# | When it finishes, relaunch your agents with the commands it prints.      |
# +-------------------------------------------------------------------------+
#
# Usage:
#   ./scripts/deploy_headroom.sh                 # interactive: confirms before killing agents
#   ./scripts/deploy_headroom.sh --yes           # non-interactive: kill agents without prompting
#   ./scripts/deploy_headroom.sh --reinit        # also re-run `headroom init claude|codex`
#   ./scripts/deploy_headroom.sh --no-agents     # upgrade + restart proxy only; leave agents alone
#   HEADROOM_VERSION=0.27.1 ./scripts/deploy_headroom.sh   # pin a specific version
#   HEADROOM_VERSION=latest ./scripts/deploy_headroom.sh   # upgrade to the newest on PyPI
#
# Verified against this machine 2026-06-22:
#   - pipx install spec : headroom-ai[proxy]   (~/.local/pipx/venvs/headroom-ai)
#   - deployment        : profile=default preset=persistent-service port=8787 backend=anthropic
#   - service           : launchd ~/Library/LaunchAgents/com.headroom.default.plist
#                         (managed by `headroom install` — never pkill it directly)
#
set -euo pipefail

# ---- config ---------------------------------------------------------------
# Resolve the repo root (this script lives in scripts/) and the project venv
# interpreter — the project convention is .venv/bin/python, never bare python3
# (enforced by the no-bare-python pre-commit hook).
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PROJECT_DIR}/.venv/bin/python"

TARGET_VERSION="${HEADROOM_VERSION:-0.27.0}"
PKG_BASE="headroom-ai"
PKG_SPEC="headroom-ai[proxy]"          # keep the [proxy] extra (matches existing install)
PROFILE="default"
PORT="8787"
BACKEND="anthropic"
HEALTH_URL="http://127.0.0.1:${PORT}/health"
CLAUDE_BIN="${HOME}/.local/bin/claude"
CODEX_BIN="${HOME}/.local/bin/codex"

ASSUME_YES=0
DO_REINIT=0
TOUCH_AGENTS=1

for arg in "$@"; do
  case "$arg" in
    --yes|-y)    ASSUME_YES=1 ;;
    --reinit)    DO_REINIT=1 ;;
    --no-agents) TOUCH_AGENTS=0 ;;
    -h|--help)   sed -n '2,33p' "$0" | sed 's/^#\{0,1\} \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

# ---- pretty helpers -------------------------------------------------------
c_bold(){ printf '\033[1m%s\033[0m\n' "$*"; }
c_ok(){   printf '\033[32m  ok:\033[0m %s\n' "$*"; }
c_warn(){ printf '\033[33m  !!:\033[0m %s\n' "$*"; }
die(){    printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

proxy_version(){
  curl -fsS --max-time 4 "$HEALTH_URL" 2>/dev/null \
    | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("version",""))' 2>/dev/null || true
}

confirm(){ # $1 = prompt; honored unless --yes
  [ "$ASSUME_YES" = "1" ] && return 0
  printf '%s [y/N] ' "$1"
  local reply=""
  read -r reply </dev/tty 2>/dev/null || reply=""
  case "$reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# Newline-separated PID lists (bash-3.2 safe: no mapfile / no arrays).
# Never returns our own PID or parent (so running it from a shell is safe).
_self="$$"; _parent="${PPID:-0}"
_filter_self(){ awk -v a="$_self" -v b="$_parent" '$1!=a && $1!=b {print}'; }

claude_pids(){ pgrep -f "$CLAUDE_BIN" 2>/dev/null | _filter_self || true; }

codex_pids(){
  # Match the codex CLI but skip the Computer-Use helper app and codex's own
  # `codex mcp` children — only the interactive/exec agent processes.
  pgrep -f "$CODEX_BIN" 2>/dev/null | while read -r pid; do
    cmd="$(ps -o command= -p "$pid" 2>/dev/null || true)"
    case "$cmd" in
      *computer-use*|*SkyComputerUseClient*|*"codex mcp"*) : ;;
      *) echo "$pid" ;;
    esac
  done | _filter_self || true
}

mcp_serve_pids(){ pgrep -f 'headroom mcp serve' 2>/dev/null | _filter_self || true; }

show_pids(){ # $@ = pids
  for p in "$@"; do
    [ -n "$p" ] || continue
    printf '      [%s] %s\n' "$p" "$(ps -o command= -p "$p" 2>/dev/null | cut -c1-90)"
  done
}

term_pids(){ # $@ = pids — SIGTERM, wait, SIGKILL stragglers
  local p
  for p in "$@"; do [ -n "$p" ] && kill -TERM "$p" 2>/dev/null || true; done
  sleep 2
  for p in "$@"; do [ -n "$p" ] && kill -0 "$p" 2>/dev/null && kill -KILL "$p" 2>/dev/null || true; done
}

# ---- preflight ------------------------------------------------------------
command -v pipx     >/dev/null 2>&1 || die "pipx not found on PATH"
command -v headroom >/dev/null 2>&1 || die "headroom not found on PATH"
[ -x "$PY" ] || die "project venv interpreter not found at $PY (run from the repo; needed to read /health)"

c_bold "== Headroom deploy =="
echo "  installed CLI  : $(headroom --version 2>/dev/null || echo '?')"
echo "  running proxy  : $(proxy_version || echo 'not responding')"
echo "  target version : ${TARGET_VERSION}"
echo "  reinit hooks   : $([ "$DO_REINIT" = 1 ] && echo yes || echo 'no (use --reinit)')"
echo "  cycle agents   : $([ "$TOUCH_AGENTS" = 1 ] && echo yes || echo 'no (--no-agents)')"
echo
if ! confirm "Proceed with the upgrade + restart?"; then echo "aborted."; exit 0; fi

# ---- 1. stop running agents ----------------------------------------------
if [ "$TOUCH_AGENTS" = 1 ]; then
  c_bold "== 1/6  Stop running Claude / Codex agents =="
  CPIDS="$(claude_pids)"; XPIDS="$(codex_pids)"
  if [ -z "$CPIDS$XPIDS" ]; then
    c_ok "no agent sessions running"
  else
    [ -n "$CPIDS" ] && { echo "    Claude:"; show_pids $CPIDS; }
    [ -n "$XPIDS" ] && { echo "    Codex:";  show_pids $XPIDS; }
    if confirm "  Kill these agent sessions?"; then
      # shellcheck disable=SC2086
      term_pids $CPIDS $XPIDS
      c_ok "agents stopped"
    else
      die "agents left running — aborting (run when idle, or pass --no-agents)"
    fi
  fi
else
  c_bold "== 1/6  Stop agents — SKIPPED (--no-agents) =="
fi

# ---- 2. stop the proxy service + stray MCP children -----------------------
c_bold "== 2/6  Stop the Headroom proxy service =="
headroom install stop --profile "$PROFILE" >/dev/null 2>&1 \
  || headroom install stop >/dev/null 2>&1 || true
MPIDS="$(mcp_serve_pids)"
if [ -n "$MPIDS" ]; then
  c_warn "killing stray 'headroom mcp serve' children: $(echo $MPIDS | tr '\n' ' ')"
  # shellcheck disable=SC2086
  term_pids $MPIDS
fi
c_ok "service stopped"

# ---- 3. upgrade the pipx package -----------------------------------------
c_bold "== 3/6  Upgrade ${PKG_SPEC} -> ${TARGET_VERSION} =="
if [ "$TARGET_VERSION" = "latest" ]; then
  pipx upgrade "$PKG_BASE" || pipx install --force "$PKG_SPEC"
else
  pipx install --force "${PKG_SPEC}==${TARGET_VERSION}"
fi
NEWCLI="$(headroom --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
echo "    headroom CLI now: ${NEWCLI:-unknown}"
if [ "$TARGET_VERSION" != "latest" ] && [ "$NEWCLI" != "$TARGET_VERSION" ]; then
  die "CLI reports ${NEWCLI:-?} after upgrade, expected ${TARGET_VERSION}"
fi
c_ok "package upgraded"

# ---- 4. (optional) re-apply durable agent integrations --------------------
if [ "$DO_REINIT" = 1 ]; then
  c_bold "== 4/6  Re-apply durable agent integrations (headroom init) =="
  c_warn "this rewrites ~/.claude and ~/.codex Headroom hooks/routing"
  headroom init claude --global --port "$PORT" --backend "$BACKEND" || c_warn "init claude failed"
  headroom init codex  --global --port "$PORT" --backend "$BACKEND" || c_warn "init codex failed"
  c_ok "integrations re-applied"
else
  c_bold "== 4/6  Re-apply integrations — SKIPPED (pass --reinit if 0.27 changed agent hooks) =="
fi

# ---- 5. start the proxy service ------------------------------------------
c_bold "== 5/6  Start the Headroom proxy service =="
headroom install start --profile "$PROFILE"
c_ok "service start issued"

# ---- 6. verify ------------------------------------------------------------
c_bold "== 6/6  Verify =="
RUNVER=""
for _ in 1 2 3 4 5; do
  sleep 2
  RUNVER="$(proxy_version)"
  [ -n "$RUNVER" ] && break
done
[ -n "$RUNVER" ] || die "proxy not responding at $HEALTH_URL after restart — check: headroom install status"
echo "    proxy /health version: $RUNVER"
case "$RUNVER" in
  "$TARGET_VERSION") c_ok "Headroom $RUNVER is live" ;;
  0.27.*)            c_ok "Headroom $RUNVER is live" ;;
  *) [ "$TARGET_VERSION" = "latest" ] && c_ok "Headroom $RUNVER is live (latest)" \
       || die "proxy reports $RUNVER, expected $TARGET_VERSION" ;;
esac

# Prove (not assume) the feature state the operator cares about: memory + compression.
curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null | "$PY" -c '
import sys, json
d = json.load(sys.stdin)
mem = (d.get("checks") or {}).get("memory") or {}
rt  = d.get("runtime") or {}
comp_on = "compression_executor" in rt or any("compress" in k for k in rt)
print("    memory      :", "ENABLED" if mem.get("enabled") else "disabled",
      "(native_tool=%s bridge=%s)" % (mem.get("native_tool"), mem.get("bridge_enabled")))
print("    compression :", "ON" if comp_on else "OFF/unknown")
' 2>/dev/null || c_warn "could not parse memory/compression from /health"

# 0.27 ships `headroom doctor` — run it as an advisory post-deploy sanity check.
if headroom doctor --help >/dev/null 2>&1; then
  c_bold "== headroom doctor (advisory) =="
  headroom doctor 2>&1 | sed 's/^/    /' || c_warn "headroom doctor reported issues (review above)"
fi

# ---- next steps -----------------------------------------------------------
echo
c_bold "== Done. Relaunch your agents in their own terminals: =="
cat <<EOF
  Claude (infra lane) :  ./start-claude.sh --agent infra-orchestrator
  Claude (folk lane)  :  ./start-claude.sh --agent curriculum-track-orchestrator
  Codex               :  ./start-codex.sh

  Health check        :  curl -s ${HEALTH_URL} | "$PY" -m json.tool
  Service status      :  headroom install status
EOF
