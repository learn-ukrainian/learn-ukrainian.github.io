#!/usr/bin/env bash
set -euo pipefail

PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PROFILE="${HEADROOM_PROFILE:-default}"
PYPI_URL="${HEADROOM_PYPI_URL:-https://pypi.org/pypi/headroom-ai/json}"
HEALTH_URL="${HEADROOM_HEALTH_URL:-http://127.0.0.1:8787/health}"
LOG_DIR="${HEADROOM_UPDATE_LOG_DIR:-$HOME/.headroom/logs}"
LOCK_DIR="${HEADROOM_UPDATE_LOCK_DIR:-$HOME/.headroom/headroom-update.lock}"

mkdir -p "$LOG_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
}

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    log "missing required command: $name"
    exit 127
  fi
}

cleanup_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

restart_headroom() {
  if headroom install restart --profile "$PROFILE"; then
    return 0
  fi

  log "managed restart failed; using launchd bootout/bootstrap fallback"

  local label="com.headroom.$PROFILE"
  local domain="gui/$(id -u)"
  local plist="$HOME/Library/LaunchAgents/$label.plist"

  if [[ ! -f "$plist" ]]; then
    log "missing launchd plist: $plist"
    return 1
  fi

  launchctl bootout "$domain/$label" 2>/dev/null || true
  launchctl bootout "$domain" "$plist" 2>/dev/null || true
  sleep 2
  launchctl bootstrap "$domain" "$plist"
}

require_cmd curl
require_cmd headroom
require_cmd jq
require_cmd launchctl
require_cmd pipx

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "another headroom update check is already running"
  exit 0
fi
trap cleanup_lock EXIT

current="$(headroom --version | awk '{print $3}')"
latest="$(curl -fsS --retry 2 --connect-timeout 10 "$PYPI_URL" | jq -r '.info.version')"

if [[ -z "$current" || -z "$latest" || "$latest" == "null" ]]; then
  log "could not resolve current/latest version: current=$current latest=$latest"
  exit 1
fi

if [[ "$current" == "$latest" ]]; then
  log "headroom-ai current: $current"
  exit 0
fi

log "upgrading headroom-ai $current -> $latest"
pipx upgrade headroom-ai

log "restarting headroom profile: $PROFILE"
restart_headroom

curl -fsS --retry 5 --retry-delay 2 --connect-timeout 5 "$HEALTH_URL" >/dev/null
log "headroom healthy after upgrade to $latest"
