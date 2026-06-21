#!/usr/bin/env bash
set -euo pipefail

PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PROFILE="${HEADROOM_PROFILE:-default}"
PYPI_URL="${HEADROOM_PYPI_URL:-https://pypi.org/pypi/headroom-ai/json}"
HEALTH_URL="${HEADROOM_HEALTH_URL:-http://127.0.0.1:8787/health}"
LOG_DIR="${HEADROOM_UPDATE_LOG_DIR:-$HOME/.headroom/logs}"
LOCK_DIR="${HEADROOM_UPDATE_LOCK_DIR:-$HOME/.headroom/headroom-update.lock}"
LOCK_TIMEOUT_SECONDS="${HEADROOM_UPDATE_LOCK_TIMEOUT_SECONDS:-21600}"
LOCK_PID_FILE="$LOCK_DIR/pid"

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
  rm -f "$LOCK_PID_FILE" 2>/dev/null || true
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

lock_mtime_epoch() {
  stat -f %m "$LOCK_DIR" 2>/dev/null || stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0
}

lock_is_stale() {
  local pid=""
  local mtime="0"
  local now="0"

  if [[ -r "$LOCK_PID_FILE" ]]; then
    pid="$(tr -cd '0-9' < "$LOCK_PID_FILE")"
  fi

  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    return 1
  fi

  if [[ -n "$pid" ]]; then
    log "removing stale headroom update lock for exited pid $pid"
    return 0
  fi

  mtime="$(lock_mtime_epoch)"
  now="$(date '+%s')"
  if (( mtime > 0 && now - mtime > LOCK_TIMEOUT_SECONDS )); then
    log "removing stale headroom update lock without pid file"
    return 0
  fi

  return 1
}

acquire_lock() {
  mkdir -p "$(dirname "$LOCK_DIR")"

  if mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" > "$LOCK_PID_FILE"
    trap cleanup_lock EXIT
    return 0
  fi

  if lock_is_stale; then
    rm -f "$LOCK_PID_FILE" 2>/dev/null || true
    rmdir "$LOCK_DIR" 2>/dev/null || {
      log "stale lock directory is not empty: $LOCK_DIR"
      exit 1
    }
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      printf '%s\n' "$$" > "$LOCK_PID_FILE"
      trap cleanup_lock EXIT
      return 0
    fi
  fi

  log "another headroom update check is already running"
  exit 0
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

acquire_lock

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
